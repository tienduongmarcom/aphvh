"""Các ca HTTP của bản 0.11.1 (docs/dac-ta-0.11.1.md mục 4). Gọi từ b0111.py (CI, site UAT dùng một lần).

Mỗi ca gọi API thật qua HTTP bằng đúng người dùng (Dũng, kế toán trưởng, nhân viên bán hàng); không sửa assertion để che lỗi.
"""
import json
import urllib.error
import urllib.parse


def chay(admin, phien, f, emit):
    """admin: phiên Administrator; phien(user) -> phiên của user; f: dữ liệu fixture; emit(ca, trạng thái, chi tiết)."""
    dung, dung2, ktt, ban = phien(f["dung"]), phien(f["dung2"]), phien(f["ktt"]), phien(f["ban"])

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

    def gl(account, cost_center=None):
        flt = {"account": account, "is_cancelled": 0}
        if cost_center:
            flt["cost_center"] = cost_center
        rows = rpc("frappe.client.get_list", {"doctype": "GL Entry", "filters": json.dumps(flt),
                                               "fields": json.dumps(["debit", "credit"]), "limit_page_length": 0})
        return sum(float(r["debit"]) - float(r["credit"]) for r in rows)

    def bin_qty(item, wh):
        rows = rpc("frappe.client.get_list", {"doctype": "Bin", "filters": json.dumps({"item_code": item, "warehouse": wh}),
                                               "fields": json.dumps(["actual_qty"])})
        return float(rows[0]["actual_qty"]) if rows else 0.0

    it, co, d = f["items"], f["company"], f["date"]

    # 1. Giá tạm chỉ cho nhóm hàng nhà máy (R063/R064)
    pr = {"doctype": "Purchase Receipt", "supplier": f["supplier"], "company": co, "posting_date": d, "kh_aph_gia_tam": 1,
          "items": [{"item_code": it["trade"], "qty": 10, "rate": 1000, "uom": "Kg", "conversion_factor": 1,
                     "warehouse": f["wh_nvl"]}]}
    denied(lambda: insert(pr, ktt), text="không cho nhập giá tạm")
    pr["items"][0].update(item_code=it["raw"], rate=21000)
    pr_tam = submit(insert(pr, ktt), ktt)
    pr["items"][0]["rate"] = 0
    denied(lambda: insert(pr, ktt))
    # Hook quyền của hồ sơ Dũng không được chặn kế toán (Frappe 16: hook trả None = từ chối).
    assert get("Stock Reconciliation", f["sr_tam"], ktt)["kh_aph_gia_tam"] == 1
    denied(lambda: get("Stock Reconciliation", f["sr_tam"], dung), ("PermissionError",))
    emit("HTTP_0111_GIA_TAM_THEO_NHOM", "PASS", {"hang_thuong_mai": "chặn", "nguyen_lieu": pr_tam["name"], "gia_0": "chặn"})

    # 2. Hệ số phẩm cấp kg-v4 (R078)
    submit(insert({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "company": co, "posting_date": d,
                   "items": [{"item_code": it["raw"], "qty": 5000, "uom": "Kg", "conversion_factor": 1,
                              "s_warehouse": f["wh_nvl"], "t_warehouse": f["wh_bon"]}]}))
    sx = submit(insert({"doctype": "Stock Entry", "stock_entry_type": "Đóng gói theo kg", "company": co, "posting_date": d,
                        "kh_aph_xuong": f["cc_sc"], "kh_aph_loss_type": "Hao hụt tự nhiên", "kh_aph_loss_reason": "UAT giảm ẩm",
                        "items": [{"item_code": it["raw"], "qty": 3000, "uom": "Kg", "conversion_factor": 1, "s_warehouse": f["wh_bon"]},
                                  {"item_code": it["a"], "qty": 1500, "uom": "Kg", "conversion_factor": 1, "t_warehouse": f["wh_tp"]},
                                  {"item_code": it["b"], "qty": 1400, "uom": "Kg", "conversion_factor": 1, "t_warehouse": f["wh_tp"]}]}))
    assert sx["kh_aph_costing_rule"] == "kg-v4", sx["kh_aph_costing_rule"]
    rows = {r["item_code"]: r for r in sx["items"]}
    assert float(rows[it["b"]]["kh_aph_he_so"]) == 0.7 and rows[it["a"]]["cost_center"] == f["cc_sc"]
    ty_le = float(rows[it["a"]]["basic_amount"]) / float(rows[it["b"]]["basic_amount"])
    assert abs(ty_le - 1500 / 980) < 1e-4, ty_le
    near(float(rows[it["a"]]["basic_amount"]) + float(rows[it["b"]]["basic_amount"]), float(rows[it["raw"]]["basic_amount"]), 2)
    emit("HTTP_0111_HE_SO_PHAM_CAP", "PASS", {"rule": "kg-v4", "ty_le_a_b": round(ty_le, 4), "ky_vong": round(1500 / 980, 4)})

    # 3. Phân bổ chi phí sản xuất cuối tháng (R079, D1, D2)
    je = submit(insert({"doctype": "Journal Entry", "company": co, "posting_date": d, "accounts": [
        {"account": f["acc"]["15484"], "debit_in_account_currency": 12_480_000, "cost_center": f["cc_sc"]},
        {"account": f["acc"]["15484"], "debit_in_account_currency": 3_000_000, "cost_center": f["cc_chung"]},
        {"account": f["acc"]["3311"], "credit_in_account_currency": 15_480_000, "party_type": "Supplier",
         "party": f["supplier"]}]}))
    denied(lambda: rpc("kh_aph.factory_costing.phan_bo_thang", {"company": co, "thang": f["month"]}, dung), ("PermissionError",))
    kq = rpc("kh_aph.factory_costing.phan_bo_thang", {"company": co, "thang": f["month"]}, ktt)
    assert set(kq["lcv"]) == {f["cc_sc"]} and kq["but_toan_chung"], kq
    again = rpc("kh_aph.factory_costing.phan_bo_thang", {"company": co, "thang": f["month"]}, ktt)
    assert again["lcv"] == kq["lcv"] and again["but_toan_chung"] == kq["but_toan_chung"], again
    lcv = get("Landed Cost Voucher", kq["lcv"][f["cc_sc"]], ktt)
    submit(lcv, ktt)
    submit(get("Journal Entry", kq["but_toan_chung"], ktt), ktt)
    sx2 = {r["item_code"]: r for r in get("Stock Entry", sx["name"])["items"]}
    lc_a, lc_b = float(sx2[it["a"]]["landed_cost_voucher_amount"]), float(sx2[it["b"]]["landed_cost_voucher_amount"])
    near(lc_a + lc_b, 12_480_000, 1)
    assert abs(lc_a / lc_b - 1500 / 980) < 1e-3, (lc_a, lc_b)
    near(gl(f["acc"]["15484"], f["cc_sc"]), 0)
    near(gl(f["acc"]["15484"], f["cc_chung"]), 0)
    near(gl(f["acc"]["6323"], f["cc_chung"]), 3_000_000)
    emit("HTTP_0111_PHAN_BO_CUOI_THANG", "PASS", {"lcv": lcv["name"], "a": lc_a, "b": lc_b, "6323": 3_000_000,
                                                  "chay_lai_khong_trung": True, "dung_bi_chan": True, "je_chi_phi": je["name"]})

    # 4. Vét bồn về 0 (R076, R068)
    con = bin_qty(it["raw"], f["wh_bon"])
    assert con == 2000, con
    vb = rpc("kh_aph.factory_costing.vet_bon", {"kho": f["wh_bon"], "xuong": f["cc_sc"], "loai_hao_hut": "Hao hụt tự nhiên",
                                                "ly_do": "UAT vét bồn"}, ktt)
    phieu = submit(get("Stock Entry", vb["phieu"], ktt), ktt)
    assert bin_qty(it["raw"], f["wh_bon"]) == 0
    hh = gl(f["acc"]["15488"], f["cc_sc"])
    near(hh, float(phieu["total_outgoing_value"]), 1)
    emit("HTTP_0111_VET_BON", "PASS", {"kg": con, "15488": hh, "ton_sau": 0})

    # 5. Đổi bao bảo toàn kg (Q103)
    db = {"doctype": "Stock Entry", "stock_entry_type": "Đổi bao, đóng gói lại", "company": co, "posting_date": d,
          "items": [{"item_code": it["a"], "qty": 100, "uom": "Kg", "conversion_factor": 1, "s_warehouse": f["wh_tp"]},
                    {"item_code": it["b"], "qty": 98, "uom": "Kg", "conversion_factor": 1, "t_warehouse": f["wh_tp"]}]}
    denied(lambda: insert(db), text="lệch")
    db.update(kh_aph_xac_nhan_lech_kg=1, kh_aph_ly_do_lech_kg="UAT cân lại")
    doi = submit(insert(db))
    near(doi["kh_aph_process_loss_kg"], 2, 0.001)
    emit("HTTP_0111_DOI_BAO_LECH_KG", "PASS", {"khong_xac_nhan": "chặn", "lech_kg": 2})

    # 6. Phiếu quỹ nhà máy của Dũng (R046–R048, R085–R087)
    chi = submit(insert({"doctype": "APH Phieu quy nha may", "loai": "Chi phí nhỏ", "company": co, "posting_date": d,
                         "dong": [{"dien_giai": "Bốc xếp 3 xe", "khoan_muc": f["km"], "so_tien": 600000},
                                  {"dien_giai": "Bốc xếp thêm", "khoan_muc": f["km"], "so_tien": 150000}]}, dung), dung)
    thu = submit(insert({"doctype": "APH Phieu quy nha may", "loai": "Thu tiền khách", "company": co, "posting_date": d,
                         "customer": f["customer"], "dong": [{"dien_giai": "Khách trả tiền", "so_tien": 2_000_000}]}, dung), dung)
    bg = submit(insert({"doctype": "APH Phieu quy nha may", "loai": "Bàn giao tiền", "company": co, "posting_date": d,
                        "nguoi_nhan": f["ktt"], "dong": [{"dien_giai": "Nộp tiền về Hà Nội", "so_tien": 1_000_000}]}, dung), dung)
    chi, thu, bg = (get("APH Phieu quy nha may", x["name"], dung) for x in (chi, thu, bg))
    assert chi["trang_thai"] == "Đã ghi sổ" and chi["journal_entry"] and thu["journal_entry"], chi
    assert bg["trang_thai"] == "Chờ nhận" and not bg["journal_entry"], bg
    ds = rpc("frappe.desk.reportview.get", {"doctype": "APH Phieu quy nha may", "fields": json.dumps(["name"])}, dung)
    assert len(ds["values"]) == 3, ds
    ds2 = rpc("frappe.desk.reportview.get", {"doctype": "APH Phieu quy nha may", "fields": json.dumps(["name"])}, dung2)
    assert len((ds2 or {}).get("values") or []) == 0, ds2
    denied(lambda: get("APH Phieu quy nha may", chi["name"], dung2), ("PermissionError",))
    denied(lambda: get("Journal Entry", chi["journal_entry"], dung), ("PermissionError",))
    denied(lambda: rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": 1,
                                                              "tai_khoan_nhan": f["acc"]["1111"]}, dung2), ("PermissionError",))
    # Phạm vi Company vẫn áp dụng kể cả người gọi có Accounts Manager.
    scope = phien(f["scope_vh"])
    assert get("Company", f["vh"], scope)["name"] == f["vh"]
    before_guard = gl(f["quy"])
    denied(lambda: rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": 1,
                                                             "tai_khoan_nhan": f["acc"]["1111"]}, scope), ("PermissionError",))
    forged = {**get("APH Phieu quy nha may", bg["name"], ktt), "so_thuc_nhan": 1, "trang_thai": "Đã nhận"}
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(forged)}, ktt), text="không được sửa trực tiếp")
    fake_link = {"doctype": "APH Phieu quy nha may", "loai": "Bàn giao tiền", "company": co, "posting_date": d,
                 "nguoi_nhan": f["ktt"], "journal_entry": chi["journal_entry"],
                 "dong": [{"dien_giai": "Không được gắn bút toán có sẵn", "so_tien": 10}]}
    denied(lambda: insert(fake_link, ktt), text="Không sửa trực tiếp")
    for invalid in ("NaN", "Infinity", "1.001"):
        denied(lambda: rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": invalid,
                                                                 "tai_khoan_nhan": f["acc"]["1111"]}, ktt))
    denied(lambda: rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": 950000,
        "tai_khoan_nhan": f["acc"]["1111"]}, admin), text="không nhận thay")
    self_receive = {"doctype": "APH Phieu quy nha may", "loai": "Bàn giao tiền", "company": co,
        "posting_date": d, "nguoi_nhan": f["dung"], "dong": [{"dien_giai": "Tự nhận", "so_tien": 1}]}
    denied(lambda: insert(self_receive, dung), text="không được tự nhận")
    near(gl(f["quy"]), before_guard)
    assert get("APH Phieu quy nha may", bg["name"], ktt)["trang_thai"] == "Chờ nhận"
    emit("HTTP_0111_QUY_GUARDS", "PASS", {"company_scope": True, "forged_result": "denied", "nonfinite": "denied"})
    nhan = rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": 950000,
                                                       "tai_khoan_nhan": f["acc"]["1111"]}, ktt)
    assert nhan["trang_thai"] == "Chênh lệch chờ điều tra", nhan
    after_receive = gl(f["quy"])
    assert rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": "950000.00",
        "tai_khoan_nhan": f["acc"]["1111"]}, ktt) == nhan
    denied(lambda: rpc("kh_aph.factory_cash.xac_nhan_nhan", {"name": bg["name"], "so_thuc_nhan": 950001,
        "tai_khoan_nhan": f["acc"]["1111"]}, ktt), text="kết quả khác")
    near(gl(f["quy"]), after_receive)

    near(gl(f["quy"]), 2_000_000 - 750_000 - 950_000)
    near(gl(f["acc"]["15488"], f["cc_sc"]) - hh, 750_000)
    emit("HTTP_0111_QUY_NHA_MAY", "PASS", {"dung_thay": 3, "dung2_thay": 0, "je_dung": "chặn", "quy": 300000,
                                           "ban_giao": nhan["trang_thai"]})

    # 7. Khóa giá thành phẩm chính khi Dũng bán (R090, R091, Q138)
    def don(item, rate, caller):
        return insert({"doctype": "Sales Order", "company": co, "customer": f["customer"], "transaction_date": d,
                       "delivery_date": d, "selling_price_list": f["pl"], "currency": "VND", "conversion_rate": 1,
                       "items": [{"item_code": item, "qty": 10, "uom": "Kg", "conversion_factor": 1, "rate": rate,
                                  "warehouse": f["wh_tp"], "delivery_date": d, "item_tax_template": f["tax"]}]}, caller)
    denied(lambda: don(it["a"], 30000, dung), text="giá Hà Nội chốt")
    dung_dung = don(it["a"], 35000, dung)
    dung_pp = don(it["pp"], 1234, dung)
    kt_sua = don(it["a"], 30000, ktt)
    emit("HTTP_0111_KHOA_GIA_THANH_PHAM", "PASS", {"sai_gia": "chặn", "dung_gia": dung_dung["name"], "phu_pham": dung_pp["name"],
                                                    "ke_toan_sua_duoc": kt_sua["name"]})

    # 8. Cảnh báo dưới giá vốn chỉ kế toán thấy (R011, R084)
    def don_raw(caller):
        return raw("frappe.client.insert", {"doc": json.dumps({
            "doctype": "Sales Order", "company": co, "customer": f["customer"], "transaction_date": d, "delivery_date": d,
            "selling_price_list": f["pl"], "currency": "VND", "conversion_rate": 1,
            "items": [{"item_code": it["a"], "qty": 1, "uom": "Kg", "conversion_factor": 1, "rate": 1000,
                       "warehouse": f["wh_tp"], "delivery_date": d, "item_tax_template": f["tax"]}]})}, caller)
    kt_r, nv_r = don_raw(ktt), don_raw(ban)
    kt = json.dumps(kt_r.get("_server_messages") or "", ensure_ascii=False)
    nv = json.dumps(nv_r.get("_server_messages") or "", ensure_ascii=False)
    assert "giá vốn" in kt and "bảng giá" in kt, kt[:800]
    assert "giá vốn" not in nv and "bảng giá" in nv, nv[:800]
    for r in nv_r["message"]["items"]:
        assert r.get("valuation_rate") in (None, 0, 0.0) and r.get("gross_profit") in (None, 0, 0.0), r
    emit("HTTP_0111_GIA_VON_CHI_KE_TOAN", "PASS", {"ke_toan": "thấy", "nhan_vien_ban_hang": "không thấy, vẫn có cảnh báo bảng giá"})

    # 9. Mã khách (Q176, đổi ở 0.14 theo anh Tiến 15/10): không ghi mã thì cấp KH + 7 số; mã đưa vào giữ nguyên; trùng thì chặn
    import re
    kh = insert({"doctype": "Customer", "customer_name": f["p"] + "-moi", "customer_type": "Company"})
    assert re.fullmatch(r"KH\d{7}", kh["name"]) and kh["kh_aph_ma"] == kh["name"], kh["name"]
    ma = "KH" + f["p"][-6:].upper() + "-1"
    kh2 = insert({"doctype": "Customer", "customer_name": f["p"] + "-misa", "customer_type": "Company", "kh_aph_ma": " " + ma + " "})
    assert kh2["name"] == ma and kh2["kh_aph_ma"] == ma, kh2["name"]
    try:
        insert({"doctype": "Customer", "customer_name": f["p"] + "-trung", "customer_type": "Company", "kh_aph_ma": ma})
        raise AssertionError("Mã trùng không bị chặn")
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode(errors="replace"))
        assert body.get("exc_type") in ("DuplicateEntryError", "UniqueValidationError"), body.get("exc_type")
    emit("HTTP_0111_MA_KHACH_KH", "PASS", {"ma_cap": kh["name"], "ma_giu_nguyen": ma, "trung": "chặn"})

    # 10. Xe quay về (R016, R022, R024): ghi nợ lúc giao giữ nguyên; trả lại theo lượng thực chở về
    giao = rpc("kh_aph.delivery_status.confirm", {"name": f["dn"], "action": "handoff"})
    assert giao["kh_aph_delivery_state"] == "Đang giao", giao
    ton_truoc = bin_qty(it["a"], f["wh_tp"])
    tra = rpc("kh_aph.sales_adjust.xe_quay_ve", {"delivery_note": f["dn"]}, ktt)["phieu_tra"]
    doc = get("Delivery Note", tra, ktt)
    assert doc["kh_aph_loai_dieu_chinh"] == "Giao thiếu - hàng chở về kho (R022/R024)" and doc["docstatus"] == 0, doc["kh_aph_loai_dieu_chinh"]
    doc["items"][0]["qty"] = -40
    tra_doc = submit(doc, ktt)
    assert bin_qty(it["a"], f["wh_tp"]) == ton_truoc + 40
    giam = rpc("frappe.client.get_list", {"doctype": "Sales Invoice", "filters": json.dumps(
        {"is_return": 1, "docstatus": 1, "customer": f["customer"]}), "fields": json.dumps(["name", "kh_aph_loai_dieu_chinh", "grand_total"])})
    assert giam and giam[0]["kh_aph_loai_dieu_chinh"] == doc["kh_aph_loai_dieu_chinh"], giam
    emit("HTTP_0111_XE_QUAY_VE", "PASS", {"phieu_tra": tra_doc["name"], "nhap_lai_kg": 40, "hoa_don_giam": giam[0]["name"]})

    # 11. In biên bản giao nhận: mặc định không giá, có cột thực nhận (Q192, Q198)
    args = {"doc": "Delivery Note", "name": f["dn"], "print_format": "Biên bản giao nhận", "no_letterhead": 1}
    html = rpc("frappe.www.printview.get_html_and_style", args, ktt)["html"]
    assert "Đơn giá" not in html and "Thực nhận" in html, html[-1500:]
    rpc("frappe.client.set_value", {"doctype": "Delivery Note", "name": f["dn"], "fieldname": "kh_aph_in_gia", "value": 1})
    html2 = rpc("frappe.www.printview.get_html_and_style", args, ktt)["html"]
    assert "Đơn giá" in html2, html2[-1500:]
    emit("HTTP_0111_IN_BIEN_BAN", "PASS", {"mac_dinh": "không giá", "thuc_nhan": True, "tich_in_gia": "có giá"})

    # 12. Đóng phần chưa giao của đơn chung (Q181, Q182)
    chung = submit(insert({"doctype": "APH Shared Sales Order", "customer": f["customer2"], "transaction_date": d,
                           "delivery_date": d, "selling_price_list": f["pl"], "currency": "VND",
                           "items": [{"item_code": it["a"], "warehouse": f["wh_tp"], "qty": 50, "rate": 35000}]}))
    denied(lambda: rpc("kh_aph.sales_adjust.dong_phan_chua_giao", {"shared_order": chung["name"], "ly_do": "x"}, dung2),
           ("PermissionError",))
    dong = rpc("kh_aph.sales_adjust.dong_phan_chua_giao", {"shared_order": chung["name"], "ly_do": "Khách hủy phần còn lại"}, ktt)
    assert dong["don_da_dong"], dong
    for n in dong["don_da_dong"]:
        assert get("Sales Order", n)["status"] == "Closed"
    assert get("APH Shared Sales Order", chung["name"])["kh_aph_dong_boi"] == f["ktt"]
    emit("HTTP_0111_DONG_PHAN_CHUA_GIAO", "PASS", {"don": dong["don_da_dong"]})

    # 13. Báo cáo dữ liệu cần rà soát (BA mục 16)
    bc = rpc("frappe.desk.query_report.run", {"report_name": "Du lieu can ra soat", "filters": json.dumps({"company": co})}, ktt)
    ma = {(r.get("ma"), r.get("ten")) for r in bc["result"] if isinstance(r, dict)}
    assert ("b", pr_tam["name"]) in ma and ("b", f["sr_tam"]) in ma, sorted(ma)[:20]
    denied(lambda: rpc("frappe.desk.query_report.run", {"report_name": "Du lieu can ra soat"}, dung), ("PermissionError",))
    emit("HTTP_0111_RA_SOAT_DU_LIEU", "PASS", {"so_dong": len(bc["result"]), "gia_tam": 2, "dung": "chặn"})
