"""Các ca HTTP của bản 0.11.2 (docs/dac-ta-0.11.2.md mục 8). Gọi từ b0112.py (CI, site UAT dùng một lần).

Mỗi ca gọi API thật qua HTTP bằng đúng người dùng (kế toán trưởng, nhân viên bán hàng, Dũng); không sửa assertion để che lỗi.
"""
import json
import urllib.error


def chay(admin, phien, f, emit):
    """admin: phiên Administrator; phien(user) -> phiên của user; f: dữ liệu fixture; emit(ca, trạng thái, chi tiết)."""
    ktt, ban, dung = phien(f["ktt"]), phien(f["ban"]), phien(f["dung"])
    it, co, vh = f["items"], f["company"], f["vh"]

    def K(t, ab="APH"):
        return f"{t} - {ab}"

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

    def gl(account, vouchers, cost_center=None):
        flt = {"account": account, "is_cancelled": 0, "voucher_no": ["in", list(vouchers)]}
        if cost_center:
            flt["cost_center"] = cost_center
        rows = rpc("frappe.client.get_list", {"doctype": "GL Entry", "filters": json.dumps(flt),
                                               "fields": json.dumps(["debit", "credit"]), "limit_page_length": 0})
        return sum(float(r["debit"]) - float(r["credit"]) for r in rows)

    def bin_qty(item, wh):
        rows = rpc("frappe.client.get_list", {"doctype": "Bin", "filters": json.dumps({"item_code": item, "warehouse": wh}),
                                               "fields": json.dumps(["actual_qty"])})
        return float(rows[0]["actual_qty"]) if rows else 0.0

    def se(caller=ktt, company=None, **kw):
        return submit(insert({"doctype": "Stock Entry", "company": company or co, **kw}, caller), caller)

    def rows(doc):
        return {r["item_code"]: r for r in doc["items"]}

    # 1. Cây kho chuẩn: dựng hai lần không trùng, kho cũ ngoài cây chỉ báo (K1, mục 2.3)
    assert f["lan1"]["tao"] > 0 and f["lan2"]["tao"] == 0, (f["lan1"]["tao"], f["lan2"]["tao"])
    assert any(f["kho_cu"] in c for c in f["lan2"]["canh_bao"]), f["lan2"]["canh_bao"][:5]
    assert get("Warehouse", f["kho_cu"])["disabled"] == 0
    assert f["kho_pt"]["kh_aph_loai_kho"] == "Dở dang dây chuyền" and f["kho_pt"]["kh_aph_day_chuyen"] == "Phồng tôm", f["kho_pt"]
    assert f["kho_vc"]["warehouse_type"] == "Transit" and f["transit_mac_dinh"] == K("Hàng đang vận chuyển"), f
    emit("HTTP_0112_CAY_KHO", "PASS", {"lan_1_tao": f["lan1"]["tao"], "lan_2_tao": 0, "kho_cu": "chỉ báo",
                                       "van_chuyen_mac_dinh": f["transit_mac_dinh"]})

    # 2. Đơn bán không chọn được kho không bán (mục 2.4)
    def don(wh, caller=ban):
        return insert({"doctype": "Sales Order", "company": co, "customer": f["customer"], "transaction_date": f["date"],
                       "delivery_date": f["date"], "currency": "VND", "conversion_rate": 1,
                       "items": [{"item_code": it["goi"], "qty": 1, "rate": 30000, "warehouse": wh, "delivery_date": f["date"],
                                  "item_tax_template": f["tax"]}]}, caller)
    denied(lambda: don(K("Kho chờ đóng gói")), text="Không bán từ kho")
    denied(lambda: don(K("Dở dang dây chuyền phồng tôm")), text="Không bán từ kho")
    denied(lambda: don(K("Hàng đang vận chuyển")), text="Không bán từ kho")
    duoc = don(K("Kho thành phẩm nhà máy"))
    emit("HTTP_0112_CHAN_BAN_KHO", "PASS", {"cho_dong_goi": "chặn", "do_dang": "chặn", "van_chuyen": "chặn", "thanh_pham": duoc["name"]})

    # 3–4. Phồng tôm: cấp 2 mẻ (320 kg bột), ra 1,8 mẻ (324 kg bánh khô), ghi tiêu hao 280 → quyết toán theo định mức
    wip = K("Dở dang dây chuyền phồng tôm")

    def chu_ky(ten):
        se(stock_entry_type="Material Transfer", items=[{"item_code": it["bot"], "qty": 320, "uom": "Kg", "conversion_factor": 1,
                                                         "s_warehouse": K("Kho nguyên liệu"), "t_warehouse": wip}])
        r = raw("frappe.client.insert", {"doc": json.dumps({
            "doctype": "Stock Entry", "company": co, "stock_entry_type": "Sản xuất theo kg", "kh_aph_xuong": f["cc_pt"],
            "items": [{"item_code": it["bot"], "qty": 280, "uom": "Kg", "conversion_factor": 1, "s_warehouse": wip},
                      {"item_code": it["banh"], "qty": 324, "uom": "Kg", "conversion_factor": 1,
                       "t_warehouse": K("Kho chờ đóng gói"), "is_finished_item": 1}]})}, ktt)
        canh_bao = json.dumps(r.get("_server_messages") or "", ensure_ascii=False)
        submit(r["message"], ktt)
        denied(lambda: rpc("kh_aph.factory_costing.quyet_toan_do_dang", {"kho": wip, "xuong": f["cc_pt"], "ly_do": "x"}, dung),
               ("PermissionError",))
        kq = rpc("kh_aph.factory_costing.quyet_toan_do_dang", {"kho": wip, "xuong": f["cc_pt"], "ly_do": f"dừng chuyền {ten}"}, ktt)
        lai = rpc("kh_aph.factory_costing.quyet_toan_do_dang", {"kho": wip, "xuong": f["cc_pt"], "ly_do": f"dừng chuyền {ten}"}, ktt)
        assert kq["che_do"] == "dinh_muc" and lai.get("da_co") and sorted(lai["phieu"]) == sorted(kq["phieu"]), (kq, lai)
        for n in kq["phieu"]:
            submit(get("Stock Entry", n, ktt), ktt)
        c = kq["chi_tiet"][0]
        return kq, c, canh_bao

    kq, c, canh_bao = chu_ky("0%")
    assert "Lệch định mức" in canh_bao, canh_bao[:600]
    near(c["dinh_muc"], 288, 0.001)
    near(c["tu_nhien"], 8, 0.001)
    near(c["bat_thuong"], 32, 0.001)
    near(gl(f["acc"]["15488"], kq["phieu"], f["cc_pt"]), 8 * 20000)
    near(gl(f["acc"]["6322"], kq["phieu"]), 32 * 20000)
    assert bin_qty(it["bot"], wip) == 0
    emit("HTTP_0112_PHONG_TOM_DINH_MUC", "PASS", {"dinh_muc": 288, "tu_nhien_15488": 8, "vuot_6322": 32, "ton_sau": 0,
                                                  "canh_bao_R073": True, "dung": "chặn", "chay_lai_khong_trung": True})

    rpc("frappe.client.set_value", {"doctype": "BOM", "name": f["bom"], "fieldname": "kh_aph_hao_hut_cho_phep", "value": 2})
    kq2, c2, _ = chu_ky("2%")
    near(c2["muc_cho_phep"], 293.76, 0.001)
    near(c2["tu_nhien"], 13.76, 0.001)
    near(c2["bat_thuong"], 26.24, 0.001)
    assert kq2["ky"]["so_phieu_san_xuat"] == 1, kq2["ky"]
    emit("HTTP_0112_PHONG_TOM_TY_LE_CHO_PHEP", "PASS", {"ty_le": "2%", "tu_nhien": 13.76, "vuot": 26.24, "ky_moi": True})

    # 5. Đậu: không có định mức → kế toán chọn tự nhiên / bất thường (như 0.11.1)
    wipd = K("Dở dang dây chuyền đậu")
    se(stock_entry_type="Material Transfer", items=[{"item_code": it["dau"], "qty": 100, "uom": "Kg", "conversion_factor": 1,
                                                     "s_warehouse": K("Kho nguyên liệu"), "t_warehouse": wipd}])
    se(stock_entry_type="Sản xuất theo kg", kh_aph_xuong=f["cc_dau"], kh_aph_loss_type="Hao hụt tự nhiên",
       kh_aph_loss_reason="UAT giảm ẩm", items=[
           {"item_code": it["dau"], "qty": 90, "uom": "Kg", "conversion_factor": 1, "s_warehouse": wipd},
           {"item_code": it["dausach"], "qty": 85, "uom": "Kg", "conversion_factor": 1, "t_warehouse": K("Kho chờ đóng gói"),
            "is_finished_item": 1}])
    hoi = rpc("kh_aph.factory_costing.quyet_toan_do_dang", {"kho": wipd, "xuong": f["cc_dau"], "ly_do": "dừng đậu"}, ktt)
    assert hoi.get("can_chon"), hoi
    kd = rpc("kh_aph.factory_costing.quyet_toan_do_dang", {"kho": wipd, "xuong": f["cc_dau"], "ly_do": "dừng đậu",
                                                           "loai_hao_hut": "Hao hụt bất thường"}, ktt)
    submit(get("Stock Entry", kd["phieu"], ktt), ktt)
    near(gl(f["acc"]["6322"], [kd["phieu"]]), 10 * 30000)
    assert bin_qty(it["dau"], wipd) == 0
    emit("HTTP_0112_DAU_KE_TOAN_CHON", "PASS", {"hoi_lai": True, "6322": 300000})

    # 6. Đóng gói thành phẩm: 36 kg bánh + 0,4 kg túi PP + 2 vỏ → 2 thùng 18 kg; túi không làm lệch kg; giá = đầu vào
    dg = se(stock_entry_type="Đóng gói thành phẩm", items=[
        {"item_code": it["banh"], "qty": 36, "uom": "Kg", "conversion_factor": 1, "s_warehouse": K("Kho chờ đóng gói")},
        {"item_code": it["tui"], "qty": 0.4, "uom": "Kg", "conversion_factor": 1, "s_warehouse": K("Kho vật tư - bao bì - phụ tùng")},
        {"item_code": it["vo"], "qty": 2, "uom": "Nos", "conversion_factor": 1, "s_warehouse": K("Kho vật tư - bao bì - phụ tùng")},
        {"item_code": it["thung"], "qty": 2, "uom": "Thùng", "conversion_factor": 1, "t_warehouse": K("Kho thành phẩm nhà máy")}])
    r = rows(dg)
    assert dg["kh_aph_costing_rule"] == "kg-v4" and abs(float(dg["kh_aph_process_loss_kg"] or 0)) < 0.001, dg["kh_aph_process_loss_kg"]
    assert float(r[it["tui"]]["kh_aph_kg"]) == 0, r[it["tui"]]["kh_aph_kg"]
    dau_vao = sum(float(r[i]["basic_amount"]) for i in (it["banh"], it["tui"], it["vo"]))
    near(float(r[it["thung"]]["basic_amount"]), dau_vao, 1)
    emit("HTTP_0112_DONG_GOI_THANH_PHAM", "PASS", {"lech_kg": 0, "kg_tui": 0, "gia_thung": r[it["thung"]]["basic_amount"],
                                                   "dau_vao": dau_vao})

    # 7. Chia nhỏ 50 kg hàng thương mại thành 100 gói 500 g (cộng túi vào giá gốc hàng hóa)
    cn = se(stock_entry_type="Đóng gói thành phẩm", items=[
        {"item_code": it["xa"], "qty": 50, "uom": "Kg", "conversion_factor": 1, "s_warehouse": K("Kho chờ đóng gói")},
        {"item_code": it["tuinho"], "qty": 100, "uom": "Nos", "conversion_factor": 1, "s_warehouse": K("Kho vật tư - bao bì - phụ tùng")},
        {"item_code": it["goi"], "qty": 100, "uom": "Gói", "conversion_factor": 1, "t_warehouse": K("Kho thành phẩm nhà máy")}])
    near(float(rows(cn)[it["goi"]]["basic_rate"]), (50 * 40000 + 100 * 300) / 100, 0.01)
    assert abs(float(cn["kh_aph_process_loss_kg"] or 0)) < 0.001
    emit("HTTP_0112_CHIA_NHO", "PASS", {"gia_goi": rows(cn)[it["goi"]]["basic_rate"], "lech_kg": 0})

    # 8. Hàng VH đóng gói tại nhà máy: ghi trên sổ VH, kho Gửi tại nhà máy
    gui = K("Gửi tại Nhà máy Phú Thọ", "VH")
    v = se(company=vh, stock_entry_type="Đóng gói thành phẩm", items=[
        {"item_code": it["xa"], "qty": 50, "uom": "Kg", "conversion_factor": 1, "s_warehouse": gui},
        {"item_code": it["goi"], "qty": 100, "uom": "Gói", "conversion_factor": 1, "t_warehouse": gui}])
    assert v["company"] == vh and bin_qty(it["goi"], gui) == 100
    emit("HTTP_0112_VH_DONG_GOI_GUI", "PASS", {"phieu": v["name"], "so": vh, "kho": gui})

    # 9. Kiểm kê có mốc: vượt ngưỡng cần lý do; thiếu Nợ 1381; thừa vào kho Chờ xử lý, Có 3381; không bán được từ kho đó
    rpc("frappe.client.set_value", {"doctype": "Stock Settings", "name": "Stock Settings",
                                    "fieldname": "kh_aph_nguong_kiem_ke", "value": 5})
    knl, kvt = K("Kho nguyên liệu"), K("Kho vật tư - bao bì - phụ tùng")
    so = {x["item_code"]: x["sl_so"] for x in rpc("kh_aph.kho_chuan.so_sach", {"kho": knl}, ktt)}
    dong = json.dumps([{"item_code": it["bot"], "sl_thuc_te": so[it["bot"]] - 30}])
    denied(lambda: rpc("kh_aph.kho_chuan.ghi_kiem_ke", {"kho": knl, "dong": dong}, ktt), text="vượt ngưỡng")
    kk = rpc("kh_aph.kho_chuan.ghi_kiem_ke", {"kho": knl, "dong": dong, "ly_do": "UAT chuột cắn bao"}, ktt)
    for n in kk["phieu"]:
        submit(get("Stock Entry", n, ktt), ktt)
    near(gl(f["acc"]["1381"], kk["phieu"]), 30 * 20000)
    assert bin_qty(it["bot"], knl) == so[it["bot"]] - 30
    so2 = {x["item_code"]: x["sl_so"] for x in rpc("kh_aph.kho_chuan.so_sach", {"kho": kvt}, ktt)}
    dong2 = json.dumps([{"item_code": it["vo"], "sl_thuc_te": so2[it["vo"]] + 1}])
    kk2 = rpc("kh_aph.kho_chuan.ghi_kiem_ke", {"kho": kvt, "dong": dong2}, ktt)
    for n in kk2["phieu"]:
        submit(get("Stock Entry", n, ktt), ktt)
    cho = K("Hàng chờ xử lý Nhà máy Phú Thọ")
    assert bin_qty(it["vo"], cho) == 1 and get("Warehouse", cho)["kh_aph_loai_kho"] == "Chờ xử lý"
    near(gl(f["acc"]["3381"], kk2["phieu"]), -5000)
    bb = get("Stock Entry", kk2["phieu"][0], ktt)["kh_aph_kiem_ke"]
    lai = rpc("kh_aph.kho_chuan.ghi_kiem_ke", {"kho": kvt, "dong": dong2, "bien_ban": bb}, ktt)
    assert lai.get("da_co"), lai
    denied(lambda: don(cho), text="Không bán từ kho")
    emit("HTTP_0112_KIEM_KE_MOC", "PASS", {"vuot_nguong": "đòi lý do", "thieu_1381": 600000, "thua_3381": -5000,
                                           "kho_cho_xu_ly": cho, "khong_ban": True, "chay_lai_khong_trung": True})

    # 10. Báo cáo Tiêu hao so với định mức (kỳ đã đóng gần nhất)
    bc = rpc("frappe.desk.query_report.run", {"report_name": "Tieu hao so voi dinh muc",
                                               "filters": json.dumps({"kho": wip})}, ktt)
    moc = rpc("frappe.client.get_list", {"doctype": "Stock Entry", "filters": json.dumps({"kh_aph_vet_bon": wip, "docstatus": 1}),
                                          "fields": json.dumps(["posting_date", "posting_time"]),
                                          "order_by": "posting_date desc, posting_time desc", "limit_page_length": 1}, ktt)[0]
    bc2 = rpc("frappe.desk.query_report.run", {"report_name": "Tieu hao so voi dinh muc", "filters": json.dumps(
        {"kho": wip, "moc": f"{moc['posting_date']} {moc['posting_time']}"})}, ktt)
    dong_bot = [x for x in bc2["result"] if isinstance(x, dict) and x.get("item_code") == it["bot"]]
    assert dong_bot and abs(float(dong_bot[0]["thuc_te"]) - 320) < 0.001 and abs(float(dong_bot[0]["dinh_muc"]) - 288) < 0.001, bc2
    denied(lambda: rpc("frappe.desk.query_report.run", {"report_name": "Tieu hao so voi dinh muc",
                                                         "filters": json.dumps({"kho": wip})}, ban), ("PermissionError",))
    emit("HTTP_0112_BAO_CAO_TIEU_HAO", "PASS", {"ky_mo": len(bc["result"]), "thuc_te": 320, "dinh_muc": 288, "ban_hang": "chặn"})

    # 11. Rà soát dữ liệu: một mã bao bì mang hai quy cách (mục 5)
    rs = rpc("frappe.desk.query_report.run", {"report_name": "Du lieu can ra soat",
                                               "filters": json.dumps({"company": co, "nhom": "Bao bì"})}, ktt)
    ma = {(x.get("ma"), x.get("ten")) for x in rs["result"] if isinstance(x, dict)}
    assert ("f", it["tui"]) in ma, sorted(ma)[:10]
    emit("HTTP_0112_RA_SOAT_BAO_BI", "PASS", {"ma": it["tui"]})

    # 12. Đổi loại kho đang có tồn bị chặn; ô "Kho bồn dở dang" của 0.11.1 đã gỡ
    w = get("Warehouse", K("Kho thành phẩm nhà máy"))
    w["kh_aph_loai_kho"] = "Bán hàng"
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(w)}), text="đang có tồn")
    assert not rpc("frappe.client.get_list", {"doctype": "Custom Field", "filters": json.dumps(
        {"dt": "Warehouse", "fieldname": "kh_aph_kho_bon"}), "fields": json.dumps(["name"])})
    emit("HTTP_0112_LOAI_KHO", "PASS", {"doi_loai_khi_co_ton": "chặn", "o_kho_bon": "đã gỡ"})
