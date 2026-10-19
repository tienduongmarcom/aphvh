"""Các ca HTTP của lượt 0.14 (docs/dac-ta-0.14.md mục 8). Gọi từ b014.py (CI, site UAT dùng một lần).

Gọi API thật qua HTTP bằng đúng người dùng (kế toán trưởng, kế toán, kế toán bán hàng, trưởng phòng / nhân viên bán hàng, Dũng);
không sửa assertion để che lỗi.
"""
import calendar
import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import urllib.error


def lai(du_no, ls, ngay):
    return float(round(du_no * ls / 100 * ngay / 365)) if ngay > 0 else 0.0


def chay(admin, phien, f, emit, factory_feature):
    ktt, ktt2, ktbh, tp, nvbh, dung = (phien(f[k]) for k in ("ktt", "ktt2", "ktbh", "tp", "nvbh", "dung"))
    d = f["date"]
    hom_nay = datetime.date.fromisoformat(d)
    acc = f["acc"]
    ma = {n: f"{f['p']}-FT{n}" for n in (1, 2, 8, 9)}  # mã giao dịch riêng mỗi lần chạy

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
        assert abs(float(a or 0) - float(b or 0)) <= tol, (a, b)

    # 1. Tài khoản ngân hàng theo khach.json: dưới nhóm 112, đúng loại tiền, thẻ Bank Account; chạy lại không trùng.
    nh1, nh2 = f["nh"]
    assert len(nh1["tao_tai_khoan"]) == 3 and len(nh1["tao_the"]) == 3, nh1
    assert not nh2["tao_tai_khoan"] and not nh2["tao_the"] and len(nh2["da_co"]) == 3, nh2
    usd = f["usd"]
    assert usd[1] == "USD" and usd[0].startswith("1122") and usd[2].startswith("112 "), usd
    ba = get("Bank Account", f["bank_account"], ktt)
    assert ba["mask"] == "1111" and ba["account"] == acc["bank"] and ba["is_company_account"] == 1 and not ba.get("bank_account_no")
    emit("HTTP_014_NGAN_HANG", "PASS", {"tao": nh1["tao_tai_khoan"], "chay_lai": "không trùng", "usd": usd[0]})

    # 2. Thu tiền (0.13) ghi vào tài khoản ngân hàng mới; chống trùng mã dùng chung; sổ tiền gửi tồn sau từng phiếu.
    kq = rpc("kh_aph.ban_quay.thu_tien", {"request_id": f["p"] + "-thu-quay-b014-cases-1", "company": f["aph"], "customer": f["kh1"], "chuyen_khoan": 3_000_000,
                                          "tk_ngan_hang": acc["bank"], "ma_gd": ma[1]}, ktbh)
    pe = kq["phieu_thu"][0]
    denied(lambda: rpc("kh_aph.ban_quay.thu_tien", {"request_id": f["p"] + "-thu-quay-b014-cases-2", "company": f["aph"], "customer": f["kh2"], "chuyen_khoan": 1_000_000,
                                                    "tk_ngan_hang": acc["bank"], "ma_gd": ma[1]}, ktbh), text=pe)
    # bút toán có số tham chiếu cũng tính là đã ghi
    je_ck = insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": d, "cheque_no": ma[2], "cheque_date": d,
                    "accounts": [{"account": acc["bank"], "credit_in_account_currency": 500_000},
                                 {"account": acc["cp"], "debit_in_account_currency": 500_000}]}, ktt)
    submit(je_ck, ktt)
    denied(lambda: rpc("kh_aph.ban_quay.thu_tien", {"request_id": f["p"] + "-thu-quay-b014-cases-3", "company": f["aph"], "customer": f["kh2"], "chuyen_khoan": 1_000_000,
                                                    "tk_ngan_hang": acc["bank"], "ma_gd": ma[2]}, ktbh), text=je_ck["name"])
    for reference in (ma[1], ma[2]):
        denied(lambda: insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": d,
            "cheque_no": reference, "cheque_date": d, "accounts": [
                {"account": acc["bank"], "credit_in_account_currency": 1},
                {"account": acc["cp"], "debit_in_account_currency": 1}]}, ktt), text="Mã giao dịch đã được dùng")
    # Hai phiên đồng thời không tạo được hai JE nháp với cùng mã trên cùng ngân hàng.
    race_doc = {"doctype": "Journal Entry", "company": f["aph"], "posting_date": d,
        "cheque_no": f["p"] + "-race-native", "cheque_date": d, "accounts": [
            {"account": acc["bank"], "credit_in_account_currency": 1}, {"account": acc["cp"], "debit_in_account_currency": 1}]}
    def raced(caller):
        try:
            return insert(race_doc, caller)["name"]
        except urllib.error.HTTPError as exc:
            error = json.loads(exc.read())
            assert error.get("exc_type") in ("ValidationError", "QueryDeadlockError"), error
            return None
    with ThreadPoolExecutor(2) as pool:
        race_results = list(pool.map(raced, [phien(f["ktt"]), phien(f["ktt"])]))
    winners = [name for name in race_results if name]
    assert len(winners) == 1, race_results
    denied(lambda: insert(race_doc, ktt), text="Mã giao dịch đã được dùng")
    ktt("/api/method/frappe.client.delete", {"doctype": "Journal Entry", "name": winners[0]})
    emit("HTTP_014_MA_GD_NATIVE", "PASS", {"cross_pe_je": True, "concurrent_single_draft": True})
    so = bao_cao("So quy va tien gui", {"company": f["aph"], "account": acc["bank"], "tu_ngay": d, "den_ngay": d}, ktt2)
    dong = [r for r in so if r.get("so")]
    assert [r["so"] for r in dong] == [pe, je_ck["name"]], dong
    dau_tk = so[0]["ton"]  # tồn đầu ngày (site UAT trắng: 0)
    assert so[0]["dien_giai"] == "Số tồn đầu kỳ" and [r["ton"] for r in dong] == [dau_tk + 3_000_000, dau_tk + 2_500_000], dong
    assert so[-1]["ton"] == dau_tk + 2_500_000 and so[-2]["thu"] == 3_000_000 and so[-2]["chi"] == 500_000
    denied(lambda: bao_cao("So quy va tien gui", {"company": f["aph"], "account": acc["bank"]}, dung), ("PermissionError",))
    emit("HTTP_014_SO_TIEN_GUI", "PASS", {"phieu": [pe, je_ck["name"]], "ton_cuoi": dau_tk + 2_500_000, "chong_trung": "PE + JE"})

    # 3. Thu / chi hộ qua tài khoản cá nhân giám đốc: bút toán nháp 1388 / 3388 đối tượng Nhân viên; công nợ với giám đốc.
    def ho(loai, tien, **kw):
        je = rpc("kh_aph.tien_vay.thu_chi_ho", {"company": f["aph"], "loai": loai, "nhan_vien": f["nv"], "so_tien": tien,
                                                 "noi_dung": loai, **kw}, ktt2)["journal_entry"]
        doc = get("Journal Entry", je, ktt)
        assert doc["docstatus"] == 0
        assert all(a["account"] != acc["bank"] for a in doc["accounts"]), "không ghi vào 112 của công ty"
        submit(doc, ktt)
        return doc
    j1 = ho("Giám đốc thu hộ tiền khách", 5_000_000, khach=f["kh2"])
    assert {a["party_type"] for a in j1["accounts"]} == {"Employee", "Customer"}
    ho("Giám đốc chi hộ chi phí", 2_000_000, tk_doi_ung=acc["cp"])
    ho("Giám đốc nộp lại tiền thu hộ", 1_000_000, tk_doi_ung=acc["tien"])
    denied(lambda: rpc("kh_aph.tien_vay.thu_chi_ho", {"company": f["aph"], "loai": "Giám đốc thu hộ tiền khách",
                                                      "nhan_vien": f["nv"], "so_tien": 1, "noi_dung": "x", "khach": f["kh1"]}, dung),
           ("PermissionError",))
    cn = [r for r in bao_cao("Cong no voi giam doc", {"company": f["aph"]}, ktt2) if r.get("nhan_vien") == f["nv"]]
    assert len(cn) == 1 and cn[0]["phai_thu"] == 4_000_000 and cn[0]["phai_tra"] == 2_000_000 and cn[0]["chenh"] == 2_000_000, cn
    emit("HTTP_014_THU_CHI_HO", "PASS", {"giu_thu_ho": 4_000_000, "con_no_chi_ho": 2_000_000, "chenh": 2_000_000})

    # 4. Khế ước vay: nhận vay → trả gốc → trích lãi tháng (dư nợ thực từng ngày) → dư nợ, lịch đến hạn, dòng tiền.
    dau = (hom_nay.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)  # đầu tháng trước
    cuoi = dau.replace(day=calendar.monthrange(dau.year, dau.month)[1])
    tra = dau.replace(day=16)
    han = hom_nay + datetime.timedelta(days=20)
    ku = insert({"doctype": "APH Khe uoc vay", "company": f["aph"], "so_khe_uoc": f["p"] + "-KU1", "loai_ben_cho_vay": "Ngân hàng",
                 "ben_cho_vay": "ACB", "so_tien": 100_000_000, "lai_suat": 12, "ngay_vay": str(dau), "ngay_den_han": str(han),
                 "tai_khoan": acc["vay"]}, ktt)
    assert ku["ky_han"] == "Ngắn hạn"
    denied(lambda: get("APH Khe uoc vay", ku["name"], dung))
    denied(lambda: insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": str(dau), "accounts": [
        {"account": acc["bank"], "debit_in_account_currency": 1}, {"account": acc["vay"], "credit_in_account_currency": 1}]}, ktt),
        text="khế ước")
    nhan = submit(insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": str(dau), "cheque_no": f["p"] + "-GN",
                          "cheque_date": str(dau), "accounts": [
        {"account": acc["bank"], "debit_in_account_currency": 100_000_000},
        {"account": acc["vay"], "credit_in_account_currency": 100_000_000, "kh_aph_khe_uoc": ku["name"]}]}, ktt), ktt)
    submit(insert({"doctype": "Journal Entry", "company": f["aph"], "posting_date": str(tra), "cheque_no": f["p"] + "-TG",
                   "cheque_date": str(tra), "accounts": [
        {"account": acc["vay"], "debit_in_account_currency": 40_000_000, "kh_aph_khe_uoc": ku["name"]},
        {"account": acc["bank"], "credit_in_account_currency": 40_000_000}]}, ktt), ktt)
    denied(lambda: rpc("kh_aph.tien_vay.trich_lai", {"company": f["aph"], "den_ngay": str(cuoi)}, ktbh), ("PermissionError",))
    tl = rpc("kh_aph.tien_vay.trich_lai", {"company": f["aph"], "den_ngay": str(cuoi)}, ktt)
    ky_vong = lai(100_000_000, 12, 15) + lai(60_000_000, 12, (cuoi - tra).days + 1)
    je_lai = get("Journal Entry", tl["journal_entry"], ktt)
    assert je_lai["docstatus"] == 0 and je_lai["posting_date"] == str(cuoi)
    no = {a["account"]: a for a in je_lai["accounts"]}
    near(no[acc["lai"]]["debit_in_account_currency"], ky_vong)
    near(no[acc["lai_tra"]]["credit_in_account_currency"], ky_vong)
    assert no[acc["lai"]]["kh_aph_khe_uoc"] == ku["name"]
    submit(je_lai, ktt)
    denied(lambda: rpc("kh_aph.tien_vay.trich_lai", {"company": f["aph"], "den_ngay": str(cuoi)}, ktt), text="đã có bút toán trích lãi")
    dn_vay = [r for r in bao_cao("Du no vay theo khe uoc", {"company": f["aph"]}, ktt2) if r.get("name") == ku["name"]]
    assert len(dn_vay) == 1, dn_vay
    r = dn_vay[0]
    assert r["goc_nhan"] == 100_000_000 and r["da_tra"] == 40_000_000 and r["du_no"] == 60_000_000, r
    near(r["lai_phai_tra"], ky_vong)
    assert r["nhom_han"] == "Trong 30 ngày", r["nhom_han"]
    dt = [x for x in bao_cao("Dong tien 7 30 ngay", {"ngay": d}, ktt) if str(x.get("don_vi", "")).startswith("APH")]
    assert dt and dt[0]["chi_30"] >= 60_000_000 + ky_vong - 1, dt
    emit("HTTP_014_KHE_UOC", "PASS", {"khe_uoc": ku["name"], "lai_trich": ky_vong, "du_no": 60_000_000, "dong_tien_chi_30": dt[0]["chi_30"]})

    # 5. Đối chiếu sao kê CSV: khớp (phiếu thu, bút toán), lệch số tiền, trùng mã trên sao kê, chưa ghi sổ. Chỉ đọc.
    dd = lambda x: x.strftime("%d/%m/%Y")
    csv = "\n".join([
        "SAO KÊ TÀI KHOẢN", "Ngày GD;Số tham chiếu;Diễn giải;Ghi nợ;Ghi có",
        f"{dd(dau)};{f['p']}-GN;Giải ngân;;100.000.000",
        f"{dd(tra)};{f['p']}-TG;Trả gốc;40.000.000;",
        f"{dd(hom_nay)};{ma[1]};KH1 chuyển khoản;;3.000.000",
        f"{dd(hom_nay)};{ma[2]};Chi phí;600.000;",
        f"{dd(hom_nay)};{ma[9]};Khách lạ;;7.000.000",
        f"{dd(hom_nay)};{ma[9]};Khách lạ;;7.000.000",
        f"{dd(hom_nay)};{ma[8]};Phí SMS;11.000;", ";;Cộng;40.611.000;117.000.000"]) + "\n"
    fl = insert({"doctype": "File", "file_name": f["p"] + "-saoke.csv", "content": csv, "is_private": 1}, ktt2)
    mau = {"dong_tieu_de": 2, "ngay": "Ngày GD", "ma": "Số tham chiếu", "noi_dung": "Diễn giải", "ghi_no": "Ghi nợ", "ghi_co": "Ghi có"}
    kq = rpc("kh_aph.tien_vay.doi_chieu_sao_ke", {"bank_account": f["bank_account"], "file_url": fl["file_url"],
                                                  "anh_xa": json.dumps(mau)}, ktt2)
    tt = {(r["ma"], r["trang_thai"]) for r in kq["dong"]}
    assert tt == {(f["p"] + "-GN", "Khớp"), (f["p"] + "-TG", "Khớp"), (ma[1], "Khớp"), (ma[2], "Lệch"),
                  (ma[9], "Trùng"), (ma[8], "Chưa ghi sổ")}, tt
    assert kq["tong"] == {"Khớp": 3, "Lệch": 1, "Trùng": 2, "Chưa ghi sổ": 1}, kq["tong"]
    khop = {r["ma"]: r["chung_tu"] for r in kq["dong"] if r["trang_thai"] == "Khớp"}
    assert khop[ma[1]] == pe and khop[f["p"] + "-GN"] == nhan["name"], khop
    denied(lambda: rpc("kh_aph.tien_vay.doi_chieu_sao_ke", {"bank_account": f["bank_account"], "file_url": fl["file_url"],
        "anh_xa": json.dumps(mau), "luu_mau": 1}, ktt2), ("PermissionError",))
    denied(lambda: rpc("kh_aph.tien_vay.doi_chieu_sao_ke", {"bank_account": f["bank_account"], "file_url": fl["file_url"],
        "anh_xa": json.dumps(mau)}, ktt), ("PermissionError",))
    own_file = insert({"doctype": "File", "file_name": f["p"] + "-saoke-manager.csv", "content": csv + "\n", "is_private": 1}, ktt)
    saved = rpc("kh_aph.tien_vay.doi_chieu_sao_ke", {"bank_account": f["bank_account"], "file_url": own_file["file_url"],
        "anh_xa": json.dumps(mau), "luu_mau": 1}, ktt)
    assert saved["tong"] == kq["tong"]
    scoped_bank = phien(f["scope_co"])
    # scope_co chỉ được APH; thêm Accounts Manager qua fixture để gọi các báo cáo tài chính.
    for report in ("Cong no voi giam doc", "Du no vay theo khe uoc"):
        view = bao_cao(report, {}, scoped_bank)
        assert all(r.get("company") == f["aph"] for r in view)
        denied(lambda report=report: bao_cao(report, {"company": f["vh"]}, scoped_bank), ("PermissionError",))
    assert f["bank_vh"], "Thiếu tài khoản ngân hàng VH đối chứng"
    denied(lambda: bao_cao("So quy va tien gui", {"company": f["vh"], "account": f["bank_vh"]}, scoped_bank), ("PermissionError",))
    emit("HTTP_014_SAO_KE_QUYEN", "PASS", {"file_private": True, "bank_mapping_write": True})
    # mẫu đã lưu cho ngân hàng: lần sau không cần khai cột
    kq2 = rpc("kh_aph.tien_vay.doi_chieu_sao_ke", {"bank_account": f["bank_account"], "file_url": fl["file_url"]}, ktt2)
    assert kq2["tong"] == kq["tong"]
    denied(lambda: rpc("kh_aph.tien_vay.doi_chieu_sao_ke", {"bank_account": f["bank_account"], "file_url": fl["file_url"]}, dung),
           ("PermissionError",))
    emit("HTTP_014_SAO_KE", "PASS", {"tong": kq["tong"], "mau_luu": True, "khong_ghi_so": True})

    # 6. Giá sàn trên đơn chung: chặn xác nhận, người lập không thấy %, trưởng phòng duyệt, đơn con mang dấu duyệt.
    insert({"doctype": "APH Gia san", "item_code": f["A"], "company": f["aph"], "gia_san": 30000}, ktt)
    dc = insert({"doctype": "APH Shared Sales Order", "customer": f["kh1"], "transaction_date": d, "delivery_date": d,
                 "selling_price_list": f["pl"], "currency": "VND",
                 "items": [{"item_code": f["A"], "warehouse": f["kho"], "qty": 10, "rate": 25000}]}, nvbh)
    assert dc["kh_aph_duoi_san"] == 1
    denied(lambda: submit(get("APH Shared Sales Order", dc["name"], nvbh), nvbh), text="giá sàn")
    xem = rpc("kh_aph.trung_tam_ban.xem_duoi_san_chung", {"name": dc["name"]}, nvbh)
    assert not xem["duoc_duyet"] and "phan_tram" not in xem["dong"][0], xem
    denied(lambda: rpc("kh_aph.trung_tam_ban.duyet_don_chung", {"name": dc["name"], "ly_do": "x"}, nvbh), ("PermissionError",))
    denied(lambda: rpc("kh_aph.trung_tam_ban.duyet_don_chung", {"name": dc["name"], "ly_do": " "}, tp), text="lý do")
    rpc("kh_aph.trung_tam_ban.duyet_don_chung", {"name": dc["name"], "ly_do": "Khách lấy số lượng lớn"}, tp)
    dc = submit(get("APH Shared Sales Order", dc["name"], nvbh), nvbh)
    con = lst("Sales Order", {"kh_aph_shared_order": dc["name"]}, ["name", "docstatus", "kh_aph_duyet_san_boi"], ktt)
    assert con and all(x["docstatus"] == 1 and x["kh_aph_duyet_san_boi"] == f["tp"] for x in con), con
    emit("HTTP_014_GIA_SAN_DON_CHUNG", "PASS", {"don_chung": dc["name"], "don_con": [x["name"] for x in con], "duyet": f["tp"]})

    # 7. In lại phiếu xuất kho kèm số hóa đơn MISA và "In lại lần n" (kế toán bán hàng).
    so1 = insert({"doctype": "Sales Order", "company": f["aph"], "customer": f["kh2"], "transaction_date": d, "delivery_date": d,
                  "selling_price_list": f["pl"], "currency": "VND", "conversion_rate": 1,
                  "items": [{"item_code": f["A"], "qty": 20, "uom": "Kg", "conversion_factor": 1, "rate": 35000,
                             "warehouse": f["kho"], "delivery_date": d, "item_tax_template": f["t_aph"]}]}, ktt)
    so1 = submit(so1, ktt)
    dn = rpc("erpnext.selling.doctype.sales_order.sales_order.make_delivery_note", {"source_name": so1["name"]}, ktt)
    dn = submit(insert(dn, ktt), ktt)
    hd = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", dn["name"]], ["docstatus", "=", 1]], ["name"], ktt)
    assert hd, "chưa có hóa đơn bán từ phiếu giao"
    r0 = rpc("kh_aph.trung_tam_ban.in_lai", {"delivery_note": dn["name"]}, ktbh)
    assert r0["lan"] == 1 and "In lại lần 1" in r0["html"] and "Hóa đơn ký hiệu" not in r0["html"]
    ho_so = rpc("kh_aph.sales_p1.nhan_xu_ly", {"sales_invoices": json.dumps([hd[0]["name"]])}, ktt)["ho_so"]
    h = get("APH Hoa don ngoai", ho_so, ktt)
    h.update(ky_hieu="1C26TAP", so="0000321", ngay=d)
    submit(h, ktt)
    r1 = rpc("kh_aph.trung_tam_ban.in_lai", {"delivery_note": dn["name"]}, ktbh)
    assert r1["lan"] == 2 and "In lại lần 2" in r1["html"] and "1C26TAP" in r1["html"] and "0000321" in r1["html"], r1["lan"]
    assert get("Delivery Note", dn["name"], ktt)["kh_aph_so_lan_in"] == 2
    emit("HTTP_014_IN_LAI", "PASS", {"phieu_giao": dn["name"], "so_hd": "1C26TAP 0000321", "lan": 2})

    from b014_ho_so_cases import chay as ho_so_cases
    ho_so_cases(rpc, get, insert, lst, denied, ktt, dn, emit)
    from b014_chenh_lech_cases import chay as chenh_lech_cases
    chenh_lech_cases(rpc, get, insert, submit, lst, denied, ktt, ktbh, f, dn, emit, phien)

    # 8. Hai màn hình điều hướng có đủ lối vào; bộ đếm in không cho sửa tay.
    tb = get("Workspace", "Trung tâm Bán hàng", ktt)
    tv = get("Workspace", "Tiền và vay", ktt)
    nhan_tb = {s["label"] for s in tb["shortcuts"]}
    for x in ("Đơn chờ duyệt dưới giá sàn", "Đơn chung chờ duyệt dưới giá sàn", "Hóa đơn còn nợ", "Khách cần gọi hôm nay",
              "Hóa đơn chờ xuất MISA", "Phiếu đã nhận thiếu bản ký", "Bản ký chờ đối chiếu", "Chênh lệch giao nhận cần xử lý"):
        assert x in nhan_tb, x
    nhan_tv = {s["label"] for s in tv["shortcuts"]}
    for x in ("Sổ quỹ và tiền gửi", "Khế ước vay", "Dư nợ vay theo khế ước",
              "Công nợ với giám đốc", "Tiền chưa rõ khách", "Phân bổ tiền và cọc còn nháp",
              "Bàn giao tiền nhà máy chờ nhận", "Bàn giao tiền có chênh lệch"):
        assert x in nhan_tv, x
    emit("HTTP_014_MAN_HINH", "PASS", {"trung_tam_ban": len(nhan_tb), "tien_va_vay": len(nhan_tv)})

    from b014_ban_nhanh_cases import chay as ban_nhanh_cases
    chain = ban_nhanh_cases(rpc, get, insert, submit, lst, denied, ktbh, dung, ktt, f, emit, phien)
    from b014_tien_giao_nhan_chain import chay as tien_chain
    tien_chain(rpc, get, insert, submit, lst, ktt, f, chain, emit)
    from b014_xuat_ngay_cases import chay as xuat_ngay_cases
    xuat_ngay_cases(rpc, get, insert, submit, lst, denied, ktt, dung, f, phien, emit)
    from b014_cash_custody import chay as cash_cases
    cash_cases(rpc, get, insert, submit, lst, denied, ktt, ktbh, dung, f, phien, emit)

    from b014_cash_closing import chay as closing_cases
    closing_cases(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit)

    from b014_cash_handover import chay as handover_cases
    handover_cases(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit)

    from b014_cash_issue_reverse import chay as issue_reverse_cases
    issue_reverse_cases(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit)

    from b014_cashier_request import chay as cashier_cases
    cashier_cases(rpc, get, insert, lst, denied, ktt, ktbh, f, phien, emit)

    from b014_personal_cash import chay as personal_cases
    personal_cases(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit)

    from b014_factory_handover import chay as factory_cases
    factory_cases(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit, factory_feature)
