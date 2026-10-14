"""Các ca HTTP của bản 0.11.3 (docs/dac-ta-0.11.3.md mục 6). Gọi từ b0113.py (CI, site UAT dùng một lần).

Mỗi ca gọi API thật qua HTTP bằng đúng người dùng (kế toán trưởng, kế toán, nhân viên bán hàng, Dũng); không sửa assertion để
che lỗi.
"""
import datetime
import json
import urllib.error


def chay(admin, phien, f, emit):
    ktt, ktt2, ban, dung = phien(f["ktt"]), phien(f["ktt2"]), phien(f["ban"]), phien(f["dung"])
    d = f["date"]
    ngay = datetime.date.fromisoformat(d)

    def rpc(method, args=None, caller=None):
        return (caller or admin)("/api/method/" + method, args)["message"]

    def get(dt, name, caller=None):
        return rpc("frappe.client.get", {"doctype": dt, "name": name}, caller)

    def insert(doc, caller=None):
        return rpc("frappe.client.insert", {"doc": json.dumps(doc)}, caller)

    def submit(doc, caller=None):
        return rpc("frappe.client.submit", {"doc": json.dumps(doc)}, caller)

    def save(doc, caller=None):
        return rpc("frappe.client.save", {"doc": json.dumps(doc)}, caller)

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

    def bin_qty(item, wh):
        r = lst("Bin", {"item_code": item, "warehouse": wh}, ["actual_qty"])
        return float(r[0]["actual_qty"]) if r else 0.0

    def don(company, customer, rows, caller=ktt, **kw):
        return submit(insert({"doctype": "Sales Order", "company": company, "customer": customer, "transaction_date": d,
                              "delivery_date": d, "selling_price_list": f["pl"], "currency": "VND", "conversion_rate": 1,
                              "items": [{"item_code": i, "qty": q, "uom": "Kg", "conversion_factor": 1, "rate": r,
                                         "warehouse": w, "delivery_date": kw.get("delivery_date", d), "item_tax_template": t}
                                        for i, q, r, w, t in rows], **kw}, caller), caller)

    def giao(so, qty=None, caller=ktt):
        dn = rpc("erpnext.selling.doctype.sales_order.sales_order.make_delivery_note", {"source_name": so}, caller)
        if qty is not None:
            for r in dn["items"]:
                r["qty"] = qty
        return submit(insert(dn, caller), caller)

    def hd_cua(dn_name):
        rows = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", dn_name], ["docstatus", "=", 1]], ["name"], admin)
        assert rows, f"phiếu {dn_name} chưa có hóa đơn đã ghi sổ"
        return get("Sales Invoice", rows[0]["name"])

    def tra(dn_name, qty, **kw):
        ret = rpc("erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return", {"source_name": dn_name}, ktt)
        for r in ret["items"]:
            r["qty"] = -qty
        ret.update({"kh_aph_loai_dieu_chinh": "Khách trả hàng (R025)", **kw})
        return ret

    # 1. Hạn thanh toán chung (Q166): 2 đợt giao cùng hạn = ngày đơn + 30
    so = don(f["aph"], f["kh1"], [(f["A"], 50, 30000, f["kho"], f["t10"])])
    han = (ngay + datetime.timedelta(days=30)).isoformat()
    assert so["kh_aph_han_thanh_toan"] == han, so["kh_aph_han_thanh_toan"]
    dn1, dn2 = giao(so["name"], 20), giao(so["name"], 10)
    hd1, hd2 = hd_cua(dn1["name"]), hd_cua(dn2["name"])
    assert hd1["due_date"] == han and hd2["due_date"] == han, (hd1["due_date"], hd2["due_date"])
    emit("HTTP_0113_HAN_CHUNG", "PASS", {"han": han, "hoa_don": [hd1["name"], hd2["name"]]})

    # 2. Gia hạn có lịch sử, cập nhật hóa đơn và sổ công nợ (Q167–Q168, R045)
    han2 = (ngay + datetime.timedelta(days=45)).isoformat()
    denied(lambda: rpc("kh_aph.sales_p1.gia_han_thanh_toan", {"sales_order": so["name"], "han_moi": han2, "ly_do": "x"}, ban),
           ("PermissionError",))
    denied(lambda: rpc("kh_aph.sales_p1.gia_han_thanh_toan", {"sales_order": so["name"], "han_moi": han2, "ly_do": ""}, ktt))
    gh = rpc("kh_aph.sales_p1.gia_han_thanh_toan", {"sales_order": so["name"], "han_moi": han2, "ly_do": "Khách xin lùi 15 ngày"}, ktt)
    assert set(gh["hoa_don_cap_nhat"]) == {hd1["name"], hd2["name"]}, gh
    assert get("Sales Invoice", hd1["name"])["due_date"] == han2
    ple = lst("Payment Ledger Entry", {"voucher_no": hd1["name"], "delinked": 0}, ["due_date"])
    assert ple and all(x["due_date"] == han2 for x in ple), ple
    so2 = get("Sales Order", so["name"], ktt)
    ls = so2["kh_aph_lich_su_gia_han"]
    assert len(ls) == 1 and ls[0]["han_cu"] == han and ls[0]["han_moi"] == han2 and ls[0]["nguoi"] == f["ktt"], ls
    emit("HTTP_0113_GIA_HAN", "PASS", {"han_moi": han2, "lich_su": 1, "ple": True, "ban_hang": "chặn"})

    # 3. Đổi địa chỉ khi đang giao (Q180)
    assert get("Delivery Note", dn1["name"])["kh_aph_delivery_state"] == "Đang giao"
    denied(lambda: rpc("kh_aph.sales_p1.doi_dia_chi_giao", {"delivery_note": dn1["name"], "dia_chi": f["dc_khac"], "ly_do": "x"}, ktt),
           text="không thuộc khách")
    rpc("kh_aph.sales_p1.doi_dia_chi_giao", {"delivery_note": dn1["name"], "dia_chi": f["dc2"], "ly_do": "Khách đổi kho nhận"}, ktt)
    assert get("Delivery Note", dn1["name"])["shipping_address_name"] == f["dc2"]
    cm = lst("Comment", {"reference_doctype": "Delivery Note", "reference_name": dn1["name"], "comment_type": "Comment"}, ["content"])
    assert any("Đổi địa chỉ giao" in c["content"] for c in cm), cm
    emit("HTTP_0113_DOI_DIA_CHI", "PASS", {"dia_chi": f["dc2"], "nhat_ky": True})

    # 4. Đơn quá hạn giao (Q189–Q190)
    qh = don(f["aph"], f["kh1"], [(f["A"], 5, 30000, f["kho"], f["t10"])],
             transaction_date=(ngay - datetime.timedelta(days=5)).isoformat(),
             delivery_date=(ngay - datetime.timedelta(days=3)).isoformat())
    bc = rpc("frappe.desk.query_report.run", {"report_name": "Don qua han giao", "filters": json.dumps({"company": f["aph"]})}, ktt)
    dong = [x for x in bc["result"] if isinstance(x, dict) and x.get("name") == qh["name"]]
    assert dong and dong[0]["tre"] == 3 and abs(float(dong[0]["con_lai"]) - 5) < 1e-6, bc["result"][:5]
    assert not [x for x in bc["result"] if isinstance(x, dict) and x.get("name") == so["name"]]
    emit("HTTP_0113_QUA_HAN_GIAO", "PASS", {"don": qh["name"], "tre": 3})

    # 5. Trả hàng cách ly + bù trừ (R025): thiếu lựa chọn bị chặn; hàng vào kho cách ly, không bán được từ đó
    r = tra(dn2["name"], 4)
    denied(lambda: insert(r, ktt), text="hàng trả về")
    r.update(kh_aph_hang_tra_ve="Cách ly", kh_aph_xu_ly_tien="Bù trừ công nợ")
    tr = submit(insert(r, ktt), ktt)
    cl = "Hàng cách ly Hà Nội - APH"
    assert all(x["warehouse"] == cl for x in tr["items"]) and bin_qty(f["A"], cl) == 4, tr["items"][0]["warehouse"]
    assert get("Warehouse", cl)["kh_aph_loai_kho"] == "Cách ly"
    denied(lambda: don(f["aph"], f["kh1"], [(f["A"], 1, 30000, cl, f["t10"])], caller=ban), text="Không bán từ kho")
    emit("HTTP_0113_TRA_CACH_LY", "PASS", {"phieu": tr["name"], "kho": cl, "kg": 4})

    # 6. Trả hàng bán lại được + hoàn tiền: phiếu chi nháp đúng số hóa đơn giảm
    ton = bin_qty(f["A"], f["kho"])
    th = submit(insert(tra(dn1["name"], 2, kh_aph_hang_tra_ve="Bán lại được", kh_aph_xu_ly_tien="Hoàn tiền"), ktt), ktt)
    assert bin_qty(f["A"], f["kho"]) == ton + 2
    th = get("Delivery Note", th["name"])
    pe = get("Payment Entry", th["kh_aph_chung_tu_xu_ly"])
    giam = hd_cua(th["name"])
    assert pe["docstatus"] == 0 and pe["payment_type"] == "Pay" and pe["party"] == f["kh1"], pe["payment_type"]
    near(pe["paid_amount"], abs(float(giam["grand_total"])))
    emit("HTTP_0113_TRA_HOAN_TIEN", "PASS", {"phieu_chi_nhap": pe["name"], "so_tien": pe["paid_amount"]})

    # 7. Đổi hàng: phiếu giao nháp mới từ đơn gốc
    dh = submit(insert(tra(dn1["name"], 1, kh_aph_hang_tra_ve="Bán lại được", kh_aph_xu_ly_tien="Đổi hàng"), ktt), ktt)
    moi = get("Delivery Note", get("Delivery Note", dh["name"])["kh_aph_chung_tu_xu_ly"])
    assert moi["docstatus"] == 0 and not moi["is_return"] and moi["items"][0]["item_code"] == f["A"] \
        and abs(float(moi["items"][0]["qty"]) - 1) < 1e-6, moi["items"]
    emit("HTTP_0113_DOI_HANG", "PASS", {"phieu_giao_nhap": moi["name"]})

    # 8–9. Giảm giá sau giao 2 dòng có thuế (R026): APH ghi giảm 511, VH ghi 521; công nợ hóa đơn giảm đúng
    def giam_gia(company, customer, rows, kho, tk_giam, tk_thue):
        s = don(company, customer, rows)
        hd = hd_cua(giao(s["name"])["name"])
        denied(lambda: rpc("kh_aph.sales_p1.giam_gia_sau_giao", {"sales_invoice": hd["name"], "so_tien": 1000, "ly_do": "x"}, ban),
               ("PermissionError",))
        kq = rpc("kh_aph.sales_p1.giam_gia_sau_giao", {"sales_invoice": hd["name"], "so_tien": 1_100_000,
                                                       "ly_do": "Chiết khấu sản lượng tháng"}, ktt)
        lai = rpc("kh_aph.sales_p1.giam_gia_sau_giao", {"sales_invoice": hd["name"], "so_tien": 1_100_000, "ly_do": "x"}, ktt)
        assert lai.get("da_co") and lai["but_toan"] == kq["but_toan"], lai
        je = get("Journal Entry", kq["but_toan"], ktt)
        no = {}
        for a in je["accounts"]:
            no[a["account"]] = no.get(a["account"], 0) + float(a["debit_in_account_currency"]) - float(a["credit_in_account_currency"])
        assert any(k in tk_giam for k in no if no[k] > 0), (no, tk_giam)
        near(sum(v for v in no.values() if v > 0), 1_100_000)
        submit(je, ktt)
        near(float(get("Sales Invoice", hd["name"])["outstanding_amount"]), float(hd["outstanding_amount"]) - 1_100_000)
        return je, no, tk_thue

    je, no, tk_thue = giam_gia(f["aph"], f["kh1"], [(f["A"], 100, 30000, f["kho"], f["t10"]), (f["B"], 100, 50000, f["kho"], f["t5"])],
                               f["kho"], f["acc"]["aph_511"], f["acc"]["aph_33311"])
    # tỷ trọng gồm thuế: A 3.300.000, B 5.250.000 → thuế = 1.100.000×3,3/8,55×10/110 + 1.100.000×5,25/8,55×5/105
    thue = 1_100_000 * 3_300_000 / 8_550_000 * 10 / 110 + 1_100_000 * 5_250_000 / 8_550_000 * 5 / 105
    near(no.get(tk_thue, 0), thue, 2)
    emit("HTTP_0113_GIAM_GIA_TT133", "PASS", {"but_toan": je["name"], "ghi_giam": "511", "thue": round(no.get(tk_thue, 0))})
    je2, no2, _ = giam_gia(f["vh"], f["kh2"], [(f["A"], 100, 30000, f["khov"], f["t10v"])], f["khov"], [f["acc"]["vh_521"]],
                           f["acc"]["vh_33311"])
    near(no2.get(f["acc"]["vh_521"], 0), 1_000_000)
    emit("HTTP_0113_GIAM_GIA_TT99", "PASS", {"but_toan": je2["name"], "ghi_giam": "521", "521": 1_000_000})

    # 10. Hồ sơ hóa đơn MISA: hàng đợi, nhận xử lý, chống trùng, Q148 không chặn chênh lệch
    def hang_doi(caller=ktt, **flt):
        bc = rpc("frappe.desk.query_report.run", {"report_name": "Hoa don cho xuat",
                                                   "filters": json.dumps({"company": f["aph"], **flt})}, caller)
        return {x["name"]: x for x in bc["result"] if isinstance(x, dict) and x.get("name")}
    assert hd1["name"] in hang_doi(), "hóa đơn chưa vào hàng đợi"
    ho = rpc("kh_aph.sales_p1.nhan_xu_ly", {"sales_invoices": json.dumps([hd1["name"]])}, ktt)["ho_so"]
    denied(lambda: rpc("kh_aph.sales_p1.nhan_xu_ly", {"sales_invoices": json.dumps([hd1["name"]])}, ktt2), text="đang thuộc")
    assert hd1["name"] not in hang_doi(chi_chua_nhan=1) and hang_doi(chi_chua_nhan=0)[hd1["name"]]["nguoi_xu_ly"] == f["ktt"]
    h = get("APH Hoa don ngoai", ho, ktt2)
    h.update(ky_hieu="1C26TAP", so="0000123", ngay=d)
    denied(lambda: save(h, ktt2), text="đang do")
    h = get("APH Hoa don ngoai", ho, ktt)
    h.update(ky_hieu="1C26TAP", so="0000123", ngay=d, tien_truoc_thue=500_000, tien_thue=50_000)
    h = submit(h, ktt)
    assert h["trang_thai"] == "Đã xuất" and float(h["chenh_lech"]) != 0, h["chenh_lech"]
    s1 = get("Sales Invoice", hd1["name"])
    assert s1["kh_aph_hd_so"] == "0000123" and s1["kh_aph_hd_ky_hieu"] == "1C26TAP", s1["kh_aph_hd_so"]
    assert hd1["name"] not in hang_doi(chi_chua_nhan=0)
    emit("HTTP_0113_HOA_DON_MISA", "PASS", {"ho_so": ho, "chong_trung": True, "chenh_lech_q148": h["chenh_lech"]})

    # 11. Thay thế rồi hủy: hồ sơ cũ đổi trạng thái; hủy thì hóa đơn bán quay lại hàng đợi
    tt = submit(insert({"doctype": "APH Hoa don ngoai", "loai": "Thay thế", "company": f["aph"], "hoa_don_lien_quan": ho,
                        "ky_hieu": "1C26TAP", "so": "0000124", "ngay": d}, ktt), ktt)
    assert get("APH Hoa don ngoai", ho)["trang_thai"] == "Bị thay thế" and get("Sales Invoice", hd1["name"])["kh_aph_hd_so"] == "0000124"
    huy = submit(insert({"doctype": "APH Hoa don ngoai", "loai": "Hủy", "company": f["aph"], "hoa_don_lien_quan": tt["name"]}, ktt), ktt)
    assert get("APH Hoa don ngoai", tt["name"])["trang_thai"] == "Đã hủy" and not get("Sales Invoice", hd1["name"])["kh_aph_hd_so"]
    assert hd1["name"] in hang_doi()
    emit("HTTP_0113_MISA_THAY_THE_HUY", "PASS", {"thay_the": tt["name"], "huy": huy["name"], "quay_lai_hang_doi": True})

    # 12. Dũng (không xem giá vốn) không xem được hồ sơ hóa đơn và hàng đợi
    denied(lambda: get("APH Hoa don ngoai", ho, dung), ("PermissionError",))
    denied(lambda: rpc("frappe.desk.query_report.run", {"report_name": "Hoa don cho xuat"}, dung), ("PermissionError",))
    emit("HTTP_0113_DUNG_KHONG_XEM", "PASS", {"ho_so": "chặn", "hang_doi": "chặn"})
