"""Các ca HTTP của lượt 0.13 (docs/dac-ta-0.13.md mục 9). Gọi từ b013.py (CI, site UAT dùng một lần).

Gọi API thật qua HTTP bằng đúng người dùng (kế toán trưởng, kế toán, kế toán bán hàng, trưởng phòng bán hàng, Dũng);
không sửa assertion để che lỗi.
"""
import datetime
import json
import urllib.error

LOAI = ("Tồn kho", "Tiền mặt và ngân hàng", "Công nợ khách", "Công nợ nhà cung cấp")


def chay(admin, phien, f, emit):
    ktt, ktt2, ktbh, tp, dung = (phien(f[k]) for k in ("ktt", "ktt2", "ktbh", "tp", "dung"))
    d = f["date"]
    ngay = datetime.date.fromisoformat(d)
    cuoi_truoc = ngay.replace(day=1) - datetime.timedelta(days=1)
    # đầu kỳ giữa tháng trước (đã kết thúc): chứng từ sau ngày đầu kỳ cùng tháng vẫn phải ghi được sau khi chốt
    dau_ky = str(f.get("dau_ky") or cuoi_truoc.replace(day=15))
    sau_dk = str(datetime.date.fromisoformat(dau_ky) + datetime.timedelta(days=3))

    def rpc(method, args=None, caller=None):
        return (caller or admin)("/api/method/" + method, args)["message"]

    def get(dt, name, caller=None):
        return rpc("frappe.client.get", {"doctype": dt, "name": name}, caller)

    def insert(doc, caller=None):
        return rpc("frappe.client.insert", {"doc": json.dumps(doc)}, caller)

    def submit(doc, caller=None):
        return rpc("frappe.client.submit", {"doc": json.dumps(doc)}, caller)

    def lst(dt, filters, fields, caller=None):
        return rpc("frappe.client.get_list", {"doctype": dt, "filters": json.dumps(filters), "fields": json.dumps(fields),
                                              "limit_page_length": 0}, caller)

    def bao_cao(ten, filters, caller=None):
        return rpc("frappe.desk.query_report.run", {"report_name": ten, "filters": json.dumps(filters)}, caller)["result"]

    def denied(fn, kinds=("ValidationError", "PermissionError"), text=None, khong_co=None):
        try:
            fn()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            data = json.loads(body) if body.startswith("{") else {}
            assert data.get("exc_type") in kinds, (exc.code, body[:600])
            if text:
                assert text in body, body[:600]
            for x in khong_co or ():
                assert x not in body, ("lộ thông tin", x)
            return data
        raise AssertionError("Không bị chặn")

    def don(customer, qty, rate, item=None, caller=None, ngay_ct=None):
        return insert({"doctype": "Sales Order", "company": f["aph"], "customer": customer,
                       "transaction_date": ngay_ct or d, "delivery_date": ngay_ct or d,
                       "selling_price_list": f["pl"], "currency": "VND", "conversion_rate": 1,
                       "items": [{"item_code": item or f["A"], "qty": qty, "uom": "Kg", "conversion_factor": 1, "rate": rate,
                                  "warehouse": f["kho"], "delivery_date": ngay_ct or d}]}, caller or ktt)

    def giao(so, caller=None):
        dn = rpc("erpnext.selling.doctype.sales_order.sales_order.make_delivery_note", {"source_name": so["name"]}, caller or ktt)
        return submit(insert(dn, caller or ktt), caller or ktt)

    def hoa_don_cua(dn):
        hd = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", dn["name"]], ["docstatus", "=", 1]], ["name"])
        return hd[0]["name"] if hd else None

    # 1. Giá sàn: người không có quyền bị chặn, không lộ con số; kế toán bán hàng tự duyệt trong mức; vượt mức thì trưởng phòng.
    insert({"doctype": "APH Gia san", "item_code": f["A"], "company": f["aph"], "gia_san": 30000}, ktt)
    denied(lambda: get("APH Gia san", lst("APH Gia san", {"item_code": f["A"]}, ["name"], ktt)[0]["name"], dung))
    so1 = don(f["kh1"], 10, 25000, caller=ktt2)
    assert so1["kh_aph_duoi_san"] == 1
    denied(lambda: submit(get("Sales Order", so1["name"], ktt2), ktt2), text="giá sàn", khong_co=("30000", "30.000", "30,000"))
    xem = rpc("kh_aph.ban_quay.xem_duoi_san", {"doctype": "Sales Order", "name": so1["name"]}, ktt2)
    assert not xem["duoc_duyet"] and "phan_tram" not in xem["dong"][0], xem
    denied(lambda: rpc("kh_aph.ban_quay.duyet_gia_san", {"doctype": "Sales Order", "name": so1["name"], "ly_do": "x"}, ktt2),
           ("PermissionError",))
    so2 = don(f["kh1"], 10, 28000, caller=ktbh)  # 6,67% < 10%: tự duyệt
    rpc("kh_aph.ban_quay.duyet_gia_san", {"doctype": "Sales Order", "name": so2["name"], "ly_do": "khách lấy nhiều"}, ktbh)
    so2 = submit(get("Sales Order", so2["name"], ktbh), ktbh)
    so3 = don(f["kh1"], 10, 25000, caller=ktbh)  # 16,7% > 10%: vượt mức
    denied(lambda: rpc("kh_aph.ban_quay.duyet_gia_san", {"doctype": "Sales Order", "name": so3["name"], "ly_do": "x"}, ktbh),
           ("PermissionError",), text="vượt mức")
    rpc("kh_aph.ban_quay.duyet_gia_san", {"doctype": "Sales Order", "name": so3["name"], "ly_do": "giám đốc đồng ý"}, tp)
    submit(get("Sales Order", so3["name"], ktbh), ktbh)
    emit("HTTP_013_GIA_SAN", "PASS", {"chan_khong_lo_so": so1["name"], "tu_duyet": so2["name"], "truong_phong": so3["name"]})

    # 2. Thu tiền nhanh: tiền mặt + chuyển khoản một lần, phân bổ vào đúng hóa đơn; mã giao dịch trùng bị chặn.
    dn2 = giao(so2)
    hd2 = hoa_don_cua(dn2)
    assert hd2, "Không có hóa đơn ghi nợ lúc giao"
    tong = float(get("Sales Invoice", hd2)["outstanding_amount"])
    denied(lambda: rpc("kh_aph.ban_quay.thu_tien", {"company": f["aph"], "customer": f["kh1"], "chuyen_khoan": 1000,
                                                     "tk_ngan_hang": f["acc"]["bank"], "ma_gd": " "}, ktbh), text="mã giao dịch")
    kq = rpc("kh_aph.ban_quay.thu_tien", {"company": f["aph"], "customer": f["kh1"], "tien_mat": 50000, "chuyen_khoan": 30000,
                                          "tk_ngan_hang": f["acc"]["bank"], "ma_gd": f["p"] + "-FT1",
                                          "hoa_don": json.dumps([hd2])}, ktbh)
    assert len(kq["phieu_thu"]) == 2, kq
    assert abs(float(get("Sales Invoice", hd2)["outstanding_amount"]) - (tong - 80000)) < 1
    denied(lambda: rpc("kh_aph.ban_quay.thu_tien", {"company": f["aph"], "customer": f["kh1"], "chuyen_khoan": 1000,
                                                     "tk_ngan_hang": f["acc"]["bank"], "ma_gd": f["p"] + "-FT1"}, ktbh),
           text="đã ghi")
    denied(lambda: rpc("kh_aph.ban_quay.thu_tien", {"company": f["aph"], "customer": f["kh1"], "tien_mat": 1}, dung),
           ("PermissionError",))
    emit("HTTP_013_THU_TIEN", "PASS", {"phieu_thu": kq["phieu_thu"], "con_no": tong - 80000})

    # 3. In 2 liên + biên bản đối soát công nợ.
    html = rpc("kh_aph.ban_quay.in_hai_lien", {"delivery_note": dn2["name"]}, ktbh)
    assert html.count("page-break-before") == 1 and len(html) > 200
    ds = rpc("frappe.www.printview.get_html_and_style", {"doc": "Customer", "name": f["kh1"],
                                                         "print_format": "Biên bản đối soát công nợ"}, ktbh)
    assert "ĐỐI SOÁT CÔNG NỢ" in ds["html"] and f["p"] in ds["html"], ds["html"][:400]
    emit("HTTP_013_IN_DOI_SOAT", "PASS", "2 liên + biên bản đối soát")

    # 4. Thu hồi nợ: hẹn hôm nay thì lên danh sách; hẹn ngày sau thì không (chưa quá hạn).
    rpc("kh_aph.ban_quay.ghi_cuoc_goi", {"customer": f["kh1"], "ket_qua": "khách hẹn trả", "hen_tra": d}, ktbh)
    goi = {r["customer"]: r for r in bao_cao("Khach can goi hom nay", {"company": f["aph"]}, ktbh)}
    assert "Đến ngày hẹn trả" in goi[f["kh1"]]["ly_do"], goi.get(f["kh1"])
    rpc("kh_aph.ban_quay.ghi_cuoc_goi", {"customer": f["kh1"], "ket_qua": "hẹn tuần sau",
                                         "hen_tra": str(ngay + datetime.timedelta(days=7))}, ktbh)
    goi = {r["customer"]: r for r in bao_cao("Khach can goi hom nay", {"company": f["aph"]}, ktbh)}
    assert f["kh1"] not in goi, goi.get(f["kh1"])
    emit("HTTP_013_THU_HOI_NO", "PASS", "danh sách theo ngày hẹn")

    # 5. Sửa số lượng nhập sai: chưa thu → hủy hóa đơn + phiếu giao, lập bản sửa; đã thu → từ chối.
    so4 = submit(don(f["kh2"], 10, 35000), ktt)
    dn4 = giao(so4)
    hd4 = hoa_don_cua(dn4)
    kq = rpc("kh_aph.kho_van_hanh.sua_so_luong", {"delivery_note": dn4["name"], "ly_do": "nhập 10 thay vì 8",
                                                  "so_luong": json.dumps({dn4["items"][0]["name"]: 8})}, ktt)
    assert get("Delivery Note", dn4["name"])["docstatus"] == 2 and get("Sales Invoice", hd4)["docstatus"] == 2
    moi = get("Delivery Note", kq["phieu_moi"])
    assert moi["docstatus"] == 0 and float(moi["items"][0]["qty"]) == 8 and moi["amended_from"] == dn4["name"]
    denied(lambda: rpc("kh_aph.kho_van_hanh.sua_so_luong", {"delivery_note": dn2["name"], "ly_do": "x",
                                                            "so_luong": json.dumps({dn2["items"][0]["name"]: 5})}, ktt),
           text="đã thu")
    denied(lambda: rpc("kh_aph.kho_van_hanh.sua_so_luong", {"delivery_note": dn2["name"], "ly_do": "x",
                                                            "so_luong": "{}"}, ktt2), ("PermissionError",))
    emit("HTTP_013_SUA_SO_LUONG", "PASS", {"ban_sua": kq["phieu_moi"], "hoa_don_huy": kq["hoa_don_da_huy"]})

    # 6. Hàng không giao được → chuyển kho khác: phiếu trả nháp vào kho chọn.
    so5 = submit(don(f["kh2"], 5, 35000), ktt)
    dn5 = giao(so5)
    kq = rpc("kh_aph.kho_van_hanh.chuyen_kho_khac", {"delivery_note": dn5["name"], "warehouse": f["kho2"]}, ktt)
    tra = get("Delivery Note", kq["phieu_tra"])
    assert tra["is_return"] == 1 and all(r["warehouse"] == f["kho2"] for r in tra["items"]), tra["items"]
    emit("HTTP_013_CHUYEN_KHO_KHAC", "PASS", kq)

    # 7. Đề nghị bổ sung: dưới ngưỡng thì lên báo cáo; yêu cầu chuyển kho nhiều nguồn, không giữ hàng ở kho nguồn.
    it = get("Item", f["B"])
    it["reorder_levels"] = [{"warehouse": f["kho2"], "warehouse_reorder_level": 300, "warehouse_reorder_qty": 50,
                             "material_request_type": "Transfer"}]
    rpc("frappe.client.save", {"doc": json.dumps(it)}, ktt)
    dn_bc = {(r["item_code"], r["warehouse"]): r for r in bao_cao("De nghi bo sung hang", {"company": f["aph"]}, ktt)}
    r = dn_bc[(f["B"], f["kho2"])]
    assert float(r["de_nghi"]) == 300, r
    giu_truoc = lst("Bin", {"item_code": f["B"], "warehouse": f["kho"]}, ["reserved_qty", "reserved_stock"], ktt)
    kq = rpc("kh_aph.kho_van_hanh.tao_yeu_cau_chuyen", {"dong": json.dumps([
        {"item_code": f["B"], "warehouse": f["kho2"], "from_warehouse": f["kho"], "qty": 300}])}, ktt)
    mr = get("Material Request", kq["yeu_cau"][0])
    assert mr["material_request_type"] == "Material Transfer" and mr["items"][0]["from_warehouse"] == f["kho"]
    assert lst("Bin", {"item_code": f["B"], "warehouse": f["kho"]}, ["reserved_qty", "reserved_stock"], ktt) == giu_truoc
    emit("HTTP_013_BO_SUNG", "PASS", {"yeu_cau": kq["yeu_cau"], "de_nghi": r["de_nghi"]})

    # 8. Chênh lệch kiểm kê bước 2: xử lý theo vụ, vượt số còn lại bị chặn, ghi sổ xong vụ hết chờ.
    so_a = next(x["sl_so"] for x in rpc("kh_aph.kho_chuan.so_sach", {"kho": f["kho"]}, ktt) if x["item_code"] == f["A"])
    kk = rpc("kh_aph.kho_chuan.ghi_kiem_ke", {"kho": f["kho"], "dong": json.dumps([{"item_code": f["A"], "sl_thuc_te": so_a - 10}]),
                                               "ly_do": "UAT", "bien_ban": f["p"] + "-KK1"}, ktt)
    for name in kk["phieu"]:
        submit(get("Stock Entry", name, ktt), ktt)
    vu = {r["bien_ban"]: r for r in bao_cao("Chenh lech kiem ke cho xu ly", {"company": f["aph"]}, ktt)}[f["p"] + "-KK1"]
    thieu = float(vu["thieu"])
    assert thieu > 0, vu
    denied(lambda: rpc("kh_aph.kho_van_hanh.xu_ly_chenh_lech", {"bien_ban": f["p"] + "-KK1", "dong": json.dumps([
        {"phuong_an": "Thiếu: ghi giá vốn (hao hụt)", "so_tien": thieu + 1000}])}, ktt), text="vượt")
    xl = rpc("kh_aph.kho_van_hanh.xu_ly_chenh_lech", {"bien_ban": f["p"] + "-KK1", "dong": json.dumps([
        {"phuong_an": "Thiếu: ghi giá vốn (hao hụt)", "so_tien": thieu}])}, ktt)
    denied(lambda: rpc("kh_aph.kho_van_hanh.xu_ly_chenh_lech", {"bien_ban": f["p"] + "-KK1", "dong": json.dumps([
        {"phuong_an": "Thiếu: ghi giá vốn (hao hụt)", "so_tien": 1}])}, ktt), text="vượt")  # nháp đã chiếm hết
    submit(get("Journal Entry", xl["but_toan"], ktt), ktt)
    con = {r["bien_ban"] for r in bao_cao("Chenh lech kiem ke cho xu ly", {"company": f["aph"]}, ktt)}
    assert f["p"] + "-KK1" not in con
    emit("HTTP_013_KIEM_KE_BUOC_2", "PASS", {"vu": f["p"] + "-KK1", "thieu": thieu, "but_toan": xl["but_toan"]})

    # 9. Đầu kỳ: tồn giá tạm chặn chốt; sửa xong chốt chỉ khóa đến hết ngày đầu kỳ; khách chưa có công nợ đầu kỳ.
    tam, tien = f["acc"]["tam"], f["acc"]["tien"]
    sr = submit(insert({"doctype": "Stock Reconciliation", "company": f["aph"], "purpose": "Opening Stock",
                        "posting_date": dau_ky, "set_posting_time": 1, "posting_time": "23:00:00", "expense_account": tam,
                        "kh_aph_gia_tam": 1,
                        "items": [{"item_code": f["B"], "warehouse": f["kho2"], "qty": 10, "valuation_rate": 20000}]}, ktt), ktt)
    submit(insert({"doctype": "Journal Entry", "voucher_type": "Opening Entry", "is_opening": "Yes", "company": f["aph"],
                   "posting_date": dau_ky, "accounts": [{"account": tien, "debit_in_account_currency": 5000000},
                                                        {"account": tam, "credit_in_account_currency": 5000000}]}, ktt), ktt)
    for loai, pt, party, so in (("Sales", "Customer", f["kh3"], 3000000), ("Purchase", "Supplier", f["ncc"], 1000000)):
        tool = {"doctype": "Opening Invoice Creation Tool", "name": "Opening Invoice Creation Tool", "company": f["aph"],
                "invoice_type": loai, "create_missing_party": 0, "temporary_opening_account": tam,
                "invoices": [{"doctype": "Opening Invoice Creation Tool Item", "party_type": pt, "party": party,
                              "posting_date": dau_ky, "due_date": d, "outstanding_amount": so, "qty": 1,
                              "temporary_opening_account": tam}]}
        tool["modified"] = get("Opening Invoice Creation Tool", "Opening Invoice Creation Tool").get("modified")
        admin("/api/method/run_doc_method", {"docs": json.dumps(tool), "method": "make_invoices"})
    dong = {r["loai"]: r for r in bao_cao("Doi chieu so du dau ky", {"company": f["aph"], "ngay": dau_ky}, ktt)}
    for loai in LOAI:
        insert({"doctype": "APH So du dau ky nguon", "company": f["aph"], "ngay": dau_ky, "loai": loai,
                "so_tien": float(dong[loai]["so_so"])}, ktt)
    denied(lambda: rpc("kh_aph.dau_ky.chot_dau_ky", {"company": f["aph"], "ngay": dau_ky, "ly_do": "x"}, ktt), text="giá tạm")
    # sửa tồn đầu kỳ: hủy và sửa (Amend) phiếu đầu kỳ, bỏ đánh dấu giá tạm (không phiếu điều chỉnh ngày sau)
    rpc("frappe.client.cancel", {"doctype": "Stock Reconciliation", "name": sr["name"]}, ktt)
    sua = get("Stock Reconciliation", sr["name"], ktt)
    for k in ("name", "docstatus", "creation", "modified", "amended_from"):
        sua.pop(k, None)
    sua["amended_from"] = sr["name"]
    sua["kh_aph_gia_tam"] = 0
    for row in sua["items"]:
        row.pop("name", None)
    submit(insert(sua, ktt), ktt)
    kq = rpc("kh_aph.dau_ky.chot_dau_ky", {"company": f["aph"], "ngay": dau_ky, "ly_do": "đã sửa tồn"}, ktt)
    assert kq["den"] == dau_ky, kq
    denied(lambda: insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": dau_ky,
                           "accounts": [{"account": tien, "debit_in_account_currency": 1},
                                        {"account": tam, "credit_in_account_currency": 1}]}, ktt),
           ("ValidationError", "ClosedAccountingPeriod"))
    je = insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": sau_dk,
                 "accounts": [{"account": tien, "debit_in_account_currency": 1},
                              {"account": tam, "credit_in_account_currency": 1}]}, ktt)
    assert je["name"]
    ktt("/api/method/frappe.client.delete", {"doctype": "Journal Entry", "name": je["name"]})
    chua = {r["customer"] for r in bao_cao("Khach chua co cong no dau ky", {"company": f["aph"], "ngay": dau_ky}, ktt)}
    assert f["kh2"] in chua and f["kh3"] not in chua, chua
    emit("HTTP_013_DAU_KY", "PASS", {"ngay": dau_ky, "khoa_den": kq["den"], "khach_chua_co": sorted(chua)[:5]})
