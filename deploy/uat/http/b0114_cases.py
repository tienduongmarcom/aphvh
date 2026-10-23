"""Các ca HTTP của bản 0.11.4 (docs/dac-ta-0.11.4.md mục 3). Gọi từ b0114.py (CI, site UAT dùng một lần).

Gọi API thật qua HTTP bằng đúng người dùng (kế toán trưởng, kế toán, nhân viên bán hàng, Dũng); không sửa assertion để che lỗi.
"""
import datetime
import json
import urllib.error


def chay(admin, phien, f, emit):
    ktt, ktt2, ban, dung = phien(f["ktt"]), phien(f["ktt2"]), phien(f["ban"]), phien(f["dung"])
    d = f["date"]
    ngay = datetime.date.fromisoformat(d)
    thang = d[:7]
    cuoi_truoc = ngay.replace(day=1) - datetime.timedelta(days=1)  # ERPNext chỉ cho khóa tháng đã kết thúc
    thang_truoc = f"{cuoi_truoc:%Y-%m}"

    def rpc(method, args=None, caller=None):
        return (caller or admin)("/api/method/" + method, args)["message"]

    def raw(method, args=None, caller=None):
        return (caller or admin)("/api/method/" + method, args)

    def get(dt, name, caller=None):
        return rpc("frappe.client.get", {"doctype": dt, "name": name}, caller)

    def insert(doc, caller=None):
        return rpc("frappe.client.insert", {"doc": json.dumps(doc)}, caller)

    def submit(doc, caller=None):
        return rpc("frappe.client.submit", {"doc": json.dumps(doc)}, caller)

    def lst(dt, filters, fields, caller=None):
        return rpc("frappe.client.get_list", {"doctype": dt, "filters": json.dumps(filters), "fields": json.dumps(fields),
                                              "limit_page_length": 0}, caller)

    def denied(fn, kinds=("ValidationError", "PermissionError"), text=None):
        try:
            fn()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            data = json.loads(body) if body.startswith("{") else {}
            assert data.get("exc_type") in kinds, (exc.code, body[:600])
            if text:
                assert text in body, body[:600]
            return data
        raise AssertionError("Không bị chặn")

    def near(a, b, tol=1.0):
        assert abs(float(a) - float(b)) <= tol, (a, b)

    def don_doc(company, customer, qty, rate, kho, tax):
        return {"doctype": "Sales Order", "company": company, "customer": customer, "transaction_date": d, "delivery_date": d,
                "selling_price_list": f["pl"], "currency": "VND", "conversion_rate": 1,
                "items": [{"item_code": f["A"], "qty": qty, "uom": "Kg", "conversion_factor": 1, "rate": rate,
                           "warehouse": kho, "delivery_date": d, "item_tax_template": tax}]}

    def ban_hang(company, customer, qty, rate, kho, tax):
        so = submit(insert(don_doc(company, customer, qty, rate, kho, tax), ktt), ktt)
        dn = rpc("erpnext.selling.doctype.sales_order.sales_order.make_delivery_note", {"source_name": so["name"]}, ktt)
        dn = submit(insert(dn, ktt), ktt)
        hd = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", dn["name"]], ["docstatus", "=", 1]], ["name"])
        return so, dn, get("Sales Invoice", hd[0]["name"])

    def bao_cao(ten, flt, caller=ktt):
        return rpc("frappe.desk.query_report.run", {"report_name": ten, "filters": json.dumps(flt)}, caller)

    def lai_gop(theo="Công ty"):
        bc = bao_cao("Lai gop quan tri", {"tu_ngay": d, "den_ngay": d, "theo": theo})
        return {x["khoa"]: x for x in bc["result"] if isinstance(x, dict) and x.get("khoa")}

    # 1. Lãi gộp cộng ngang 4 đơn vị: có trả hàng, giảm giá sau giao, chi phí trực tiếp của đơn
    so_a, dn_a, _hd_a = ban_hang(f["aph"], f["kh0"], 10, 30000, f["kho"], f["t_aph"])
    ret = rpc("erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return", {"source_name": dn_a["name"]}, ktt)
    for r in ret["items"]:
        r["qty"] = -2
    ret["kh_aph_loai_dieu_chinh"] = "Khách trả hàng (R025)"
    submit(insert(ret, ktt), ktt)
    _so_v, _dn_v, hd_v = ban_hang(f["vh"], f["kh0"], 10, 40000, f["khov"], f["t_vh"])
    gg = rpc("kh_aph.sales_p1.giam_gia_sau_giao", {"sales_invoice": hd_v["name"], "so_tien": 110000, "ly_do": "UAT"}, ktt)
    submit(get("Journal Entry", gg["but_toan"], ktt), ktt)
    submit(insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": d, "accounts": [
        {"account": f["acc"]["cp"], "debit_in_account_currency": 10000, "kh_aph_don_ban": so_a["name"]},
        {"account": f["acc"]["tien"], "credit_in_account_currency": 10000}]}, ktt), ktt)
    # Lọc theo khách của ca (site UAT có thể có dữ liệu khác trong ngày): một dòng, các cột từng đơn vị + cộng ngang.
    kh = lai_gop("Khách")[f["kh0"]]
    near(kh["APH_dt"], 240000)
    near(kh["APH_gv"], 160000)
    near(kh["APH_lg"], 80000)
    near(kh["VH_dt"], 300000)
    near(kh["VH_lg"], 100000)
    near(kh["lg"], 180000)
    near(kh["APH_lg"] + kh["VH_lg"], kh["lg"])
    near(kh["cp"], 10000)
    near(kh["lai_sau_cp"], 170000)
    don = lai_gop("Đơn")[so_a["name"]]
    near(don["cp"], 10000)
    near(don["lg"], 80000)
    ceo = phien(f["ceo"])
    ceo_report = bao_cao("Lai gop quan tri", {"tu_ngay": d, "den_ngay": d, "theo": "Khách"}, ceo)
    ceo_row = next(row for row in ceo_report["result"] if isinstance(row, dict) and row.get("khoa") == f["kh0"])
    near(ceo_row["APH_gv"], 160000)
    near(ceo_row["lai_sau_cp"], 170000)
    bao_cao("Dong tien 7 30 ngay", {"ngay": d}, ceo)
    denied(lambda: rpc("kh_aph.quan_tri.khoa_ky", {"company": f["aph"], "thang": thang_truoc, "ly_do": "CEO chỉ xem"}, ceo), ("PermissionError",))
    denied(lambda: raw("frappe.client.set_value", {"doctype":"Sales Invoice", "name":_hd_a["name"], "fieldname":"remarks", "value":"Không có quyền sửa"}, ceo), ("PermissionError",))
    denied(lambda: bao_cao("Lai gop quan tri", {"tu_ngay": d, "den_ngay": d}, phien(f["ceo_cost_denied"])), ("PermissionError",))
    a = kh
    emit("HTTP_0114_LAI_GOP_CONG_NGANG", "PASS", {"APH": kh["APH_lg"], "VH": kh["VH_lg"], "cong_ngang": kh["lg"],
                                                  "lai_sau_cp": kh["lai_sau_cp"]})

    # 2. Lãi tạm tính khi chưa khóa kỳ
    assert "chưa khóa kỳ" in a["tam_tinh"], a["tam_tinh"]
    emit("HTTP_0114_LAI_TAM_TINH", "PASS", {"ly_do": a["tam_tinh"]})

    # 3. Khóa kỳ (R105): chỉ kế toán trưởng; chặn ghi sổ trong kỳ; mở khóa bắt buộc lý do
    denied(lambda: rpc("kh_aph.quan_tri.khoa_ky", {"company": f["aph"], "thang": thang_truoc, "ly_do": "x"}, ktt2),
           ("PermissionError",))
    denied(lambda: rpc("kh_aph.quan_tri.khoa_ky", {"company": f["aph"], "thang": thang, "ly_do": "Tháng chưa hết"}, ktt))
    k = rpc("kh_aph.quan_tri.khoa_ky", {"company": f["aph"], "thang": thang_truoc, "ly_do": "Khóa sổ tháng UAT"}, ktt)
    je = {"doctype": "Journal Entry", "company": f["aph"], "posting_date": cuoi_truoc.isoformat(), "accounts": [
        {"account": f["acc"]["cp"], "debit_in_account_currency": 1000},
        {"account": f["acc"]["tien"], "credit_in_account_currency": 1000}]}
    denied(lambda: insert(je, ktt), ("ClosedAccountingPeriod", "ValidationError"), text="Accounting Period")
    denied(lambda: rpc("kh_aph.quan_tri.mo_khoa_ky", {"company": f["aph"], "thang": thang_truoc, "ly_do": ""}, ktt))
    rpc("kh_aph.quan_tri.mo_khoa_ky", {"company": f["aph"], "thang": thang_truoc, "ly_do": "Bổ sung chứng từ"}, ktt)
    submit(insert(je, ktt), ktt)
    k2 = rpc("kh_aph.quan_tri.khoa_ky", {"company": f["aph"], "thang": thang_truoc, "ly_do": "Khóa lại"}, ktt)
    assert k2["ky"] == k["ky"], (k, k2)
    emit("HTTP_0114_KHOA_KY", "PASS", {"ky": k["ky"], "chan_ghi_so": True, "mo_khoa_co_ly_do": True})

    # 4. Dòng tiền 7 / 30 ngày: hạn 5 ngày vào cửa sổ 7, hạn 20 ngày chỉ vào cửa sổ 30, nội bộ bị loại
    def dong_tien():
        return {x["don_vi"].split(" — ")[0]: x for x in bao_cao("Dong tien 7 30 ngay", {"ngay": d})["result"]
                if isinstance(x, dict)}
    truoc = dong_tien()  # so chênh trước / sau để không phụ thuộc dữ liệu khác trên site
    _s1, _d1, hd5 = ban_hang(f["aph"], f["kh1"], 5, 30000, f["kho"], f["t_aph"])
    _s2, _d2, hd20 = ban_hang(f["aph"], f["kh2"], 5, 30000, f["kho"], f["t_aph"])
    _s3, _d3, hd_nb = ban_hang(f["aph"], f["noi_bo"], 5, 30000, f["kho"], f["t_aph"])
    assert hd5["due_date"] == (ngay + datetime.timedelta(days=5)).isoformat(), hd5["due_date"]
    assert hd20["due_date"] == (ngay + datetime.timedelta(days=20)).isoformat(), hd20["due_date"]
    dt = dong_tien()
    aph, aph0 = dt["APH"], truoc["APH"]
    near(aph["thu_7"] - aph0["thu_7"], float(hd5["outstanding_amount"]), 2)
    near(aph["thu_30"] - aph0["thu_30"], float(hd5["outstanding_amount"]) + float(hd20["outstanding_amount"]), 2)
    near(dt["Cộng ngang"]["thu_30"], sum(float(x["thu_30"]) for k2, x in dt.items() if k2 != "Cộng ngang"), 2)
    emit("HTTP_0114_DONG_TIEN", "PASS", {"thu_7": aph["thu_7"], "thu_30": aph["thu_30"], "noi_bo_loai": hd_nb["name"]})

    # 5. Xác nhận công nợ (R039): cảnh báo mềm, ghi nhận có chênh lệch và nhật ký, báo cáo danh sách
    r = raw("frappe.client.insert", {"doc": json.dumps(don_doc(f["aph"], f["kh0"], 1, 30000, f["kho"], f["t_aph"]))}, ktt)
    assert r["message"]["name"] and "chưa xác nhận công nợ" in json.dumps(r.get("_server_messages") or "", ensure_ascii=False)
    ds = {x["customer"] for x in bao_cao("Khach chua xac nhan cong no", {})["result"] if isinstance(x, dict)}
    assert f["kh0"] in ds and f["kh1"] in ds, ds
    so_du = sum(float(x["amount"]) for x in lst("Payment Ledger Entry", {"party": f["kh0"], "delinked": 0}, ["amount"]))
    xn = rpc("kh_aph.quan_tri.ghi_nhan_xac_nhan", {"customer": f["kh0"], "ngay": d, "so_du_xac_nhan": so_du - 1000,
                                                    "ghi_chu": "Biên bản UAT"}, ktt2)
    near(xn["chenh_lech"], -1000)
    assert get("Customer", f["kh0"])["kh_aph_xac_nhan_cong_no_ngay"] == d
    r2 = raw("frappe.client.insert", {"doc": json.dumps(don_doc(f["aph"], f["kh0"], 1, 30000, f["kho"], f["t_aph"]))}, ktt)
    assert "chưa xác nhận công nợ" not in json.dumps(r2.get("_server_messages") or "", ensure_ascii=False)
    ds2 = {x["customer"] for x in bao_cao("Khach chua xac nhan cong no", {})["result"] if isinstance(x, dict)}
    assert f["kh0"] not in ds2 and f["kh1"] in ds2, ds2
    emit("HTTP_0114_XAC_NHAN_CONG_NO", "PASS", {"canh_bao_mem": True, "chenh_lech": xn["chenh_lech"]})

    scoped = phien(f["scope_aph"])
    scoped_profit = bao_cao("Lai gop quan tri", {"tu_ngay": d, "den_ngay": d, "theo": "Công ty"}, scoped)
    assert scoped_profit["result"] and all(x["khoa"] == f["aph"] for x in scoped_profit["result"]), scoped_profit["result"]
    assert not any(c.get("fieldname", "").startswith("VH_") for c in scoped_profit["columns"])
    denied(lambda: bao_cao("Lai gop quan tri", {"tu_ngay": d, "den_ngay": d, "company": f["vh"]}, scoped), ("PermissionError",))
    scoped_cash = bao_cao("Dong tien 7 30 ngay", {"ngay": d}, scoped)["result"]
    assert len(scoped_cash) == 2 and scoped_cash[0]["don_vi"].startswith("APH —"), scoped_cash
    near(scoped_cash[0]["so_du"], scoped_cash[1]["so_du"])
    scoped_debt = bao_cao("Khach chua xac nhan cong no", {}, scoped)
    assert all(r.get("so_du_xn") is None and r.get("chenh") is None for r in scoped_debt["result"])
    denied(lambda: rpc("kh_aph.quan_tri.ghi_nhan_xac_nhan", {"customer": f["kh0"], "ngay": d,
        "so_du_xac_nhan": 1, "ghi_chu": "Không ghi số dư một đơn vị thành xác nhận toàn khách"}, scoped), ("PermissionError",))
    emit("HTTP_0114_COMPANY_SCOPE", "PASS", {"profit": "APH only", "cash": "APH only", "outside_filter": "denied"})

    # 6. Dũng và nhân viên bán hàng không xem được báo cáo quản trị
    for nguoi in (dung, ban):
        for ten in ("Lai gop quan tri", "Dong tien 7 30 ngay", "Khach chua xac nhan cong no"):
            denied(lambda ten=ten, nguoi=nguoi: bao_cao(ten, {}, nguoi), ("PermissionError",))
    emit("HTTP_0114_QUYEN", "PASS", {"dung": "chặn", "ban_hang": "chặn"})
