"""Các ca HTTP của lượt 0.12 (docs/dac-ta-0.12.0-0.12.1.md mục 4). Gọi từ b012.py (CI, site UAT dùng một lần).

Gọi API thật qua HTTP bằng đúng người dùng (kế toán trưởng, kế toán, nhân viên bán hàng, Dũng); không sửa assertion để che lỗi.
"""
import datetime
import json
import urllib.error

LOAI = ("Tồn kho", "Tiền mặt và ngân hàng", "Công nợ khách", "Công nợ nhà cung cấp")


def chay(admin, phien, f, emit):
    ktt, ktt2, ban, dung = phien(f["ktt"]), phien(f["ktt2"]), phien(f["ban"]), phien(f["dung"])
    ngay = datetime.date.fromisoformat(f["date"])
    # cuối tháng trước: khóa kỳ chỉ cho tháng đã kết thúc (chạy thử cục bộ có thể đặt f["dau_ky"] riêng)
    dau_ky = f.get("dau_ky") or str(ngay.replace(day=1) - datetime.timedelta(days=1))

    def rpc(method, args=None, caller=None):
        return (caller or admin)("/api/method/" + method, args)["message"]

    def get(dt, name, caller=None):
        return rpc("frappe.client.get", {"doctype": dt, "name": name}, caller)

    def insert(doc, caller=None):
        return rpc("frappe.client.insert", {"doc": json.dumps(doc)}, caller)

    def submit(doc, caller=None):
        return rpc("frappe.client.submit", {"doc": json.dumps(doc)}, caller)

    def bao_cao(ten, filters, caller=None):
        return rpc("frappe.desk.query_report.run", {"report_name": ten, "filters": json.dumps(filters)}, caller)["result"]

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

    def de_nghi(dong, caller):
        return insert({"doctype": "APH De nghi so lieu", "tieu_de": f["p"], "dong": dong}, caller)

    # 1. Kg tịnh sai công thức không lưu được (lỗi cấu trúc).
    denied(lambda: de_nghi([{"truong": "kg_tinh", "mat_hang": f["TP"], "gia_tri_moi": "18.5", "so_goi": 72,
                             "gram_moi_goi": 250}], dung), text="Kg t")
    emit("HTTP_012_KG_SAI_CHAN", "PASS", "18,5 kg ≠ 72 × 250 g")

    # 2. Dũng lập + gửi; Dũng (dù có Accounts Manager) không duyệt; kế toán trưởng duyệt → mã hàng đổi, định mức bản mới.
    dn = de_nghi([{"truong": "kg_tinh", "mat_hang": f["TP"], "gia_tri_moi": "18", "so_goi": 72, "gram_moi_goi": 250},
                  {"truong": "san_luong_me", "dinh_muc": f["bom"], "gia_tri_moi": "95"},
                  {"truong": "hao_hut", "dinh_muc": f["bom"], "gia_tri_moi": "12", "ly_do": "thử"}], dung)
    assert dn["dong"][2]["canh_bao"], dn["dong"]
    rpc("kh_aph.du_lieu.gui", {"name": dn["name"]}, dung)
    denied(lambda: rpc("kh_aph.du_lieu.duyet", {"name": dn["name"]}, dung), ("PermissionError",))
    kq = rpc("kh_aph.du_lieu.duyet", {"name": dn["name"]}, ktt)
    moi = kq["ket_qua"][1]
    assert moi == kq["ket_qua"][2] and moi != f["bom"], kq
    assert float(get("Item", f["TP"])["weight_per_unit"]) == 18
    bm, cu = get("BOM", moi), get("BOM", f["bom"])
    assert float(bm["quantity"]) == 95 and float(bm["kh_aph_hao_hut_cho_phep"]) == 12 and bm["docstatus"] == 1, bm["quantity"]
    assert float(cu["quantity"]) == 100 and cu["docstatus"] == 1
    assert get("Item", f["TP"])["default_bom"] == moi
    assert get("APH De nghi so lieu", dn["name"])["trang_thai"] == "Đã áp dụng"
    denied(lambda: rpc("kh_aph.du_lieu.duyet", {"name": dn["name"]}, ktt))
    emit("HTTP_012_DE_NGHI_DUYET", "PASS", {"de_nghi": dn["name"], "dinh_muc_moi": moi, "dinh_muc_cu_giu": 100})

    # 3. Trả lại phải có lý do; nhân viên bán hàng không lập đề nghị.
    dn2 = de_nghi([{"truong": "kg_tinh", "mat_hang": f["NL"], "gia_tri_moi": "1"}], dung)
    rpc("kh_aph.du_lieu.gui", {"name": dn2["name"]}, dung)
    denied(lambda: rpc("kh_aph.du_lieu.tra_lai", {"name": dn2["name"], "ly_do": " "}, ktt))
    rpc("kh_aph.du_lieu.tra_lai", {"name": dn2["name"], "ly_do": "sai mã"}, ktt)
    assert get("APH De nghi so lieu", dn2["name"])["trang_thai"] == "Trả lại"
    denied(lambda: de_nghi([{"truong": "kg_tinh", "mat_hang": f["NL"], "gia_tri_moi": "1"}], ban))
    emit("HTTP_012_TRA_LAI_QUYEN", "PASS", "trả lại có lý do; nhân viên bán hàng bị chặn")

    # 3b (0.14.3). Hai lần bấm duyệt CÙNG LÚC một đề nghị: đúng một lần áp dụng, chỉ thêm MỘT bản định mức.
    import threading
    dem_bom = lambda: rpc("frappe.client.get_count", {"doctype": "BOM", "filters": json.dumps({"item": f["TP"]})})
    truoc = dem_bom()
    dn3 = de_nghi([{"truong": "san_luong_me", "dinh_muc": moi, "gia_tri_moi": "90"}], dung)
    rpc("kh_aph.du_lieu.gui", {"name": dn3["name"]}, dung)
    kq3 = []

    def bam():
        try:
            kq3.append(("ok", rpc("kh_aph.du_lieu.duyet", {"name": dn3["name"]}, ktt)))
        except urllib.error.HTTPError as exc:
            kq3.append(("chan", exc.read().decode(errors="replace")[:300]))

    luong = [threading.Thread(target=bam) for _ in range(2)]
    for t in luong:
        t.start()
    for t in luong:
        t.join(120)
    assert sorted(k for k, _ in kq3) == ["chan", "ok"], kq3
    assert dem_bom() == truoc + 1, (truoc, dem_bom())
    assert get("APH De nghi so lieu", dn3["name"])["trang_thai"] == "Đã áp dụng"
    emit("HTTP_012_DUYET_DONG_THOI", "PASS", {"de_nghi": dn3["name"], "ket_qua": [k for k, _ in kq3], "bom_them": 1})

    # 4. Danh sách rà soát nhóm Danh mục: hai khách trùng MST.
    rows = bao_cao("Du lieu can ra soat", {"nhom": "Danh mục"}, ktt)
    trung = {r["ten"] for r in rows if r.get("loai") == "Customer" and "Trùng MST" in (r.get("mo_ta") or "")}
    assert {f["kh1"], f["kh2"]} <= trung and f["kh3"] not in trung, rows[:5]
    emit("HTTP_012_RA_SOAT_DANH_MUC", "PASS", sorted(trung))

    # 5. Nạp đầu kỳ bằng công cụ chuẩn (kế toán trưởng, qua HTTP), đối ứng 9990.
    tam, tien = f["acc"]["tam"], f["acc"]["tien"]
    submit(insert({"doctype": "Stock Reconciliation", "company": f["aph"], "purpose": "Opening Stock", "posting_date": dau_ky,
                   "set_posting_time": 1, "posting_time": "23:00:00", "expense_account": tam,
                   "items": [{"item_code": f["NL"], "warehouse": f["kho"], "qty": 100, "valuation_rate": 20000}]}, ktt), ktt)
    submit(insert({"doctype": "Journal Entry", "voucher_type": "Opening Entry", "is_opening": "Yes", "company": f["aph"],
                   "posting_date": dau_ky, "accounts": [{"account": tien, "debit_in_account_currency": 5000000},
                                                        {"account": tam, "credit_in_account_currency": 5000000}]}, ktt), ktt)
    for loai, pt, party, so in (("Sales", "Customer", f["kh3"], 3000000), ("Purchase", "Supplier", f["ncc"], 1000000)):
        tool = {"doctype": "Opening Invoice Creation Tool", "name": "Opening Invoice Creation Tool", "company": f["aph"],
                "invoice_type": loai, "create_missing_party": 0, "temporary_opening_account": tam,
                "invoices": [{"doctype": "Opening Invoice Creation Tool Item", "party_type": pt, "party": party,
                              "posting_date": dau_ky, "due_date": f["date"], "outstanding_amount": so, "qty": 1,
                              "temporary_opening_account": tam}]}
        # Opening Invoice Creation Tool chuẩn chỉ cấp cho System Manager: người nạp là quản trị (anh Tiến).
        tool["modified"] = get("Opening Invoice Creation Tool", "Opening Invoice Creation Tool").get("modified")
        admin("/api/method/run_doc_method", {"docs": json.dumps(tool), "method": "make_invoices"})
    dong = {r["loai"]: r for r in bao_cao("Doi chieu so du dau ky", {"company": f["aph"], "ngay": dau_ky}, ktt)}
    so = {k: float(dong[k]["so_so"]) for k in LOAI}
    assert so == {"Tồn kho": 2000000, "Tiền mặt và ngân hàng": 5000000, "Công nợ khách": 3000000,
                  "Công nợ nhà cung cấp": 1000000}, so
    tam_dong = next(r for k, r in dong.items() if k.startswith("Số dư tài khoản tạm"))
    assert float(tam_dong["so_so"]) == -9000000 and float(tam_dong["chenh"]) == 0, tam_dong
    assert next(r for k, r in dong.items() if k.startswith("Kiểm"))["trang_thai"] == "Khớp"
    denied(lambda: rpc("kh_aph.dau_ky.chot_dau_ky", {"company": f["aph"], "ngay": dau_ky, "ly_do": "thử"}, ktt), text="Ch")
    emit("HTTP_012_DAU_KY_NAP", "PASS", {"ngay": dau_ky, **so, "tk_tam": float(tam_dong["so_so"])})

    # 6. Số nguồn: một lệch → báo Lệch; sửa đúng → Khớp; trùng loại bị chặn.
    nguon = {}
    for loai, v in zip(LOAI, (2000000, 5000000, 3000000, 900000)):
        nguon[loai] = insert({"doctype": "APH So du dau ky nguon", "company": f["aph"], "ngay": dau_ky, "loai": loai,
                              "so_tien": v}, ktt)
    denied(lambda: insert({"doctype": "APH So du dau ky nguon", "company": f["aph"], "ngay": dau_ky, "loai": "Tồn kho",
                           "so_tien": 1}, ktt), text="Đã có")
    dong = {r["loai"]: r for r in bao_cao("Doi chieu so du dau ky", {"company": f["aph"], "ngay": dau_ky}, ktt)}
    assert dong["Công nợ nhà cung cấp"]["trang_thai"] == "Lệch" and float(dong["Công nợ nhà cung cấp"]["chenh"]) == 100000
    assert all(dong[k]["trang_thai"] == "Khớp" for k in LOAI[:3])
    n = nguon["Công nợ nhà cung cấp"]
    n["so_tien"] = 1000000
    rpc("frappe.client.save", {"doc": json.dumps(n)}, ktt)
    dong = {r["loai"]: r for r in bao_cao("Doi chieu so du dau ky", {"company": f["aph"], "ngay": dau_ky}, ktt)}
    assert all(dong[k]["trang_thai"] == "Khớp" for k in LOAI), dong
    emit("HTTP_012_DOI_CHIEU", "PASS", {k: dong[k]["trang_thai"] for k in LOAI})

    # 7. Dũng và kế toán thường: không xem / không chốt; kế toán trưởng chốt → chứng từ trong kỳ bị chặn.
    denied(lambda: bao_cao("Doi chieu so du dau ky", {"company": f["aph"], "ngay": dau_ky}, dung))
    assert rpc("frappe.client.get_list", {"doctype": "APH So du dau ky nguon", "fields": json.dumps(["name"])}, dung) == []
    denied(lambda: get("APH So du dau ky nguon", nguon["Tồn kho"]["name"], dung))
    denied(lambda: rpc("kh_aph.dau_ky.chot_dau_ky", {"company": f["aph"], "ngay": dau_ky, "ly_do": "thử"}, ktt2),
           ("PermissionError",))
    kq = rpc("kh_aph.dau_ky.chot_dau_ky", {"company": f["aph"], "ngay": dau_ky, "ly_do": "khớp đủ 4 loại"}, ktt)
    assert kq["chot"] and kq["da_khoa"], kq
    denied(lambda: insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": dau_ky,
                           "accounts": [{"account": tien, "debit_in_account_currency": 1},
                                        {"account": tam, "credit_in_account_currency": 1}]}, ktt),
           ("ValidationError", "ClosedAccountingPeriod"))
    emit("HTTP_012_CHOT_KHOA", "PASS", kq)
