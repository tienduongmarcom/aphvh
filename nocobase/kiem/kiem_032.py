#!/usr/bin/env python3
"""Bộ kiểm 0.3.2 — toàn vẹn dữ liệu (theo bảng "Bộ kiểm thử cần thêm trước khi chốt 0.3.2" của bản audit PR #43). Dữ liệu giả tiền tố TV-.

    python3 kiem_032.py --email <quản trị> --password <mật khẩu>
"""
import argparse
import base64
import io
import sys
import threading
import time
import uuid

from kiem_api import API, KQ, ok


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="http://localhost:13000")
    a.add_argument("--email", required=True)
    a.add_argument("--password", required=True)
    o = a.parse_args()
    ad = API(o.url, o.email, o.password)
    k = "TV" + uuid.uuid4().hex[:4].upper()
    pw = "Thu" + uuid.uuid4().hex[:10]
    NG = {"ban_hang": ["ban_hang"], "kho": ["kho"], "nha_may": ["nha_may"], "thu_chi": ["thu_chi"], "ke_toan": ["ke_toan"],
          "kho_hn": ["kho"], "nm_kiem": ["nha_may", "ke_toan", "khong_xem_gia"]}
    uid = {}
    for ten, roles in NG.items():
        em = f"tv-{ten}@aphvh.local"
        u = ad.ds("users", {"email": em})
        if u:
            ad.call("users:update", {"password": pw, "roles": roles}, q=f"?filterByTk={u[0]['id']}")
            uid[ten] = u[0]["id"]
        else:
            uid[ten] = ad.tao("users", {"email": em, "nickname": "TV " + ten, "password": pw, "roles": roles})["id"]
    time.sleep(2)
    U = {t: API(o.url, f"tv-{t}@aphvh.local", pw, NG[t][0]) for t in NG}
    U["nm_kt"] = API(o.url, "tv-nm_kiem@aphvh.local", pw, "ke_toan")  # cùng người, chọn vai trò kế toán
    kt = U["ke_toan"]
    dv = {x["ma"]: x for x in ad.ds("don_vi", {})}
    APH = dv["APH"]

    KHO = {x: ad.tao("kho", {"ma": f"{k}-{x}", "ten": f"Kho {x} {k}", "loai_kho": "nha_may" if x == "PT" else "ban_duoc"}) for x in ["PT", "HN", "DN", "HCM"]}
    MH = {x: ad.tao("mat_hang", {"ma": f"{k}-{x}", "ten": f"Hàng {x} {k}", "gia_ban": 40000, "loai_hang": "thanh_pham" if x == "TP" else "hang_hoa"})
          for x in ["NL", "TP", "HH", "PT"]}
    MH["THUNG"] = ad.tao("mat_hang", {"ma": f"{k}-THUNG", "ten": f"Phồng tôm thùng {k}", "gia_ban": 300000})
    kh = ad.tao("khach_hang", {"ma": f"{k}-KH", "ten": "Khách TV"})
    q_nh = ad.tao("quy", {"ma": f"{k}-NH", "ten": "MB APH TV", "don_vi_id": APH["id"], "loai": "ngan_hang"})
    q_tm = ad.tao("quy", {"ma": f"{k}-TM", "ten": "TM APH TV", "don_vi_id": APH["id"], "loai": "tien_mat"})

    def gv(kho, mh):
        r = ad.ds("gia_von", {"kho_id": KHO[kho]["id"], "mat_hang_id": MH[mh]["id"]})
        return r[0] if r else {"so_kg": 0, "gia_tri": 0}

    def ban(kho, mh, sl, gia=40000):
        d = ad.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": MH[mh]["id"], "kho_id": KHO[kho]["id"], "so_kg": sl, "don_gia": gia}]})
        ad.lam("don_ban:chotDon", d["id"])
        dd = ad.lay("don_ban", d["id"], "dong")["dong"][0]["id"]
        s, r = ad.lam("luot_giao:taoLuot", None, {"don_ban_id": d["id"], "dong": [{"don_ban_dong_id": dd, "so_kg": sl}]})
        ad.lam("luot_giao:khachNhan", r["data"]["id"])
        return d

    def can():
        s, r = ad.call("gia_von:doiChieu", {})
        return r["data"]["can"], r["data"]

    # ---------- 1 & 2. Chốt lại mẻ sau khi bán 60% / bán hết ----------
    pk = ad.tao("phieu_kho", {"loai": "nhap", "kho_id": KHO["PT"]["id"], "dong": [{"mat_hang_id": MH["NL"]["id"], "so_kg": 1000, "don_gia": 20000}]})
    ad.lam("phieu_kho:ghiSo", pk["id"])
    me = ad.tao("me_sx", {"kho_id": KHO["PT"]["id"], "kho_tp_id": KHO["HN"]["id"], "xuong": "Tổ TV"})
    c = ad.tao("phieu_kho", {"loai": "cap_nvl", "kho_id": KHO["PT"]["id"], "me_sx_id": me["id"], "dong": [{"mat_hang_id": MH["NL"]["id"], "so_kg": 1000}]})
    ad.lam("phieu_kho:ghiSo", c["id"])
    th = ad.tao("phieu_kho", {"loai": "thu_hoi", "kho_id": KHO["PT"]["id"], "me_sx_id": me["id"], "dong": [{"mat_hang_id": MH["TP"]["id"], "huong": "ra", "so_kg": 1000}]})
    ad.lam("phieu_kho:ghiSo", th["id"])
    ok("Thu hồi 1.000 kg giá tạm 20.000 → giá trị tồn TP 20 triệu", gv("HN", "TP")["gia_tri"] == 20000000, gv("HN", "TP"))
    ban("HN", "TP", 600)
    ok("Bán 600 kg trước khi chốt: tồn 400 kg / 8 triệu", gv("HN", "TP")["so_kg"] == 400 and gv("HN", "TP")["gia_tri"] == 8000000)
    kt.tao("me_sx_chi_phi", {"me_sx_id": me["id"], "loai": "nhan_cong", "so_tien": 1000000, "so_chung_tu": "BL-10"})
    s, r = kt.lam("me_sx:chot", me["id"])
    ok("Chốt sau khi bán 60%: chênh 1 triệu → 400.000 vào tồn, 600.000 vào giá vốn kỳ",
       s == 200 and r["data"]["vao_ton"] == 400000 and r["data"]["vao_gia_von"] == 600000 and gv("HN", "TP")["gia_tri"] == 8400000, r)
    ok("Giá bình quân tồn = 21.000 (không dồn cả 1 triệu vào 400 kg)", gv("HN", "TP")["gia_bq"] == 21000, gv("HN", "TP"))
    ok("Cùng chứng từ chi phí ghi hai lần vào mẻ: bị chặn", kt.call("me_sx_chi_phi:create", {"me_sx_id": me["id"], "loai": "nhan_cong", "so_tien": 5, "so_chung_tu": "BL-10"})[0] >= 400)
    ban("HN", "TP", 400)
    kt.tao("me_sx_chi_phi", {"me_sx_id": me["id"], "loai": "dien", "so_tien": 500000, "so_chung_tu": "HĐ điện 10"})
    s, r = kt.lam("me_sx:chot", me["id"])
    g = gv("HN", "TP")
    ok("Chốt lại sau khi bán hết: toàn bộ 500.000 vào giá vốn, tồn không có giá trị ảo", s == 200 and r["data"]["vao_gia_von"] == 500000 and g["so_kg"] == 0 and g["gia_tri"] == 0, (r, g))
    cn, d = can()
    ok("Sổ giá trị vẫn cân sau 2 lần chốt (Σ sổ = tồn, mọi điều chỉnh cân)", cn, d)

    # ---------- 3. Giá tạm tăng sau khi chuyển kho ----------
    pk = U["kho"].tao("phieu_kho", {"loai": "nhap", "kho_id": KHO["DN"]["id"], "dong": [{"mat_hang_id": MH["HH"]["id"], "so_kg": 100}]})
    U["kho"].lam("phieu_kho:ghiSo", pk["id"])
    dong = ad.lay("phieu_kho", pk["id"], "dong")["dong"][0]
    kt.lam("phieu_kho:dinhGia", pk["id"], {"gia": {str(dong["id"]): 10000}, "tam": True})
    ck = ad.tao("phieu_kho", {"loai": "chuyen", "kho_id": KHO["DN"]["id"], "kho_dich_id": KHO["HCM"]["id"], "dong": [{"mat_hang_id": MH["HH"]["id"], "so_kg": 60}]})
    ad.lam("phieu_kho:ghiSo", ck["id"])
    ok("Giá tạm 10.000: DN 40 kg / 400.000, HCM 60 kg / 600.000", gv("DN", "HH")["gia_tri"] == 400000 and gv("HCM", "HH")["gia_tri"] == 600000)
    kt.lam("phieu_kho:dinhGia", pk["id"], {"gia": {str(dong["id"]): 12000}})
    ok("Chốt giá 12.000 sau khi chuyển: +80.000 ở DN, +120.000 theo hàng sang kho nhận HCM",
       gv("DN", "HH")["gia_tri"] == 480000 and gv("HCM", "HH")["gia_tri"] == 720000, (gv("DN", "HH"), gv("HCM", "HH")))

    # ---------- Kỳ mở sổ thử (tách người duyệt) ----------
    for x in ad.ds("ky_mo_so", {"trang_thai": "mo"}):
        ad.lam("ky_mo_so:khoa", x["id"], {"bo_qua_lo_dang_do": True})
    ky = kt.tao("ky_mo_so", {"ma": k, "ngay_chot": "2026-10-25"})

    def lo(api, loai, bang, che_do="bo_qua"):
        s, r = api.call("nhap_lo:create", {"loai": loai, "du_lieu_goc": bang, "nguon": "kiểm 0.3.2", "che_do": che_do})
        lid = r["data"]["id"]
        s, r = api.lam("nhap_lo:kiem", lid)
        return lid, (r.get("data") or r)

    # ---------- 4. Tồn đầu kỳ cho mã–kho đã có phát sinh ----------
    lid, r = lo(kt, "ton_dau_ky", f"Mã kho\tMã hàng\tSố lượng\tGiá trị\tTình trạng giá\n{k}-DN\t{k}-HH\t10\t100000\tĐã chốt\n{k}-PT\t{k}-PT\t5\t50000\tĐã chốt")
    ok("Mở tồn cho mã × kho ĐÃ có phát sinh: lỗi dòng; mã × kho mới: hợp lệ", r.get("loi") == 1 and r.get("hop_le") == 1, r)

    # ---------- 5. Tiền chưa phân bổ > số dư quỹ: chặn; tách người duyệt ----------
    lid, r = lo(kt, "quy_dau_ky", f"Mã quỹ\tSố dư\n{k}-NH\t300.000.000")
    ok("Lô tiền: người nhập tự duyệt bị chặn (tách người duyệt)", kt.lam("nhap_lo:duyet", lid)[0] == 400)
    ok("Người khác (quản lý) duyệt được", ad.lam("nhap_lo:duyet", lid)[0] == 200)
    ok("Người nhập cũng không tự ghi sổ lô tiền", kt.lam("nhap_lo:ghi", lid)[0] == 400)
    ad.lam("nhap_lo:ghi", lid)
    lid, r = lo(kt, "tien_chua_pb", f"Mã quỹ\tLoại\tSố tiền\tMã tham chiếu\n{k}-NH\tChưa rõ\t350.000.000\t{k}-FT-350")
    ok("Tiền chưa phân bổ 350tr > quỹ 300tr: có cảnh báo", bool(r.get("tong_kiem", {}).get("canh_bao")))
    ok("… và KHÔNG duyệt được (chặn, không chỉ cảnh báo)", ad.lam("nhap_lo:duyet", lid)[0] == 400)
    ok("Kế toán không tự duyệt ngoại lệ", kt.lam("nhap_lo:duyetNgoaiLe", lid, {"ly_do": "Sao kê có khoản treo của ngân hàng"})[0] == 400)
    ok("Quản lý duyệt ngoại lệ cần căn cứ", ad.lam("nhap_lo:duyetNgoaiLe", lid, {"ly_do": "ngắn"})[0] == 400)
    ad.lam("nhap_lo:duyetNgoaiLe", lid, {"ly_do": "Biên bản đối chiếu ngân hàng số 12: khoản treo 50tr"})
    ok("Có ngoại lệ có căn cứ: duyệt được", ad.lam("nhap_lo:duyet", lid)[0] == 200)
    # ---------- 9. Hai người cùng ghi một lô ----------
    kq = []
    ts = [threading.Thread(target=lambda u=u: kq.append(u.lam("nhap_lo:ghi", lid)[1])) for u in (ad, ad)]
    [x.start() for x in ts]; [x.join() for x in ts]
    pts = ad.ds("phieu_thu", {"ma_tham_chieu": f"{k}-FT-350"})
    ok("Hai người cùng bấm Ghi sổ một lô: chỉ ghi một lần", len(pts) == 1 and any((x.get("data") or {}).get("da_ghi_truoc") for x in kq), (len(pts), [str(x)[:160] for x in kq]))

    # ---------- 6. Đơn đang vận chuyển chưa có giá vốn ----------
    lid, r = lo(kt, "don_chuyen_tiep", f"Số đơn cũ\tMã khách\tĐơn vị bán\tMã hàng\tMã kho\tSố lượng còn giao\tĐơn giá\tTình trạng\tĐã thu\tMã quỹ đã thu\n"
                                       f"{k}-D1\t{k}-KH\tAPH\t{k}-HH\t{k}-DN\t50\t50000\tĐang vận chuyển\t1.000.000\t{k}-NH\n"
                                       f"{k}-D2\t{k}-KH\tAPH\t{k}-HH\t{k}-DN\t10\t50000\tChưa giao\t\t")
    s1 = ad.lam("nhap_lo:duyet", lid); s2 = ad.lam("nhap_lo:ghi", lid)
    d1 = ad.ds("don_ban", {"so_don_cu": f"{k}-D1"})[0]
    l1 = ad.ds("luot_giao", {"don_ban_id": d1["id"]})[0]
    ok("Đơn vận chuyển không có giá vốn: lượt 'giá vốn chưa xác định'", l1["tt_gia_von"] == "chua_xac_dinh", (s1, s2, l1))
    ok("Đã thu 1 triệu trước Go-Live: còn nợ 1,5 triệu, sổ quỹ KHÔNG tăng", d1["con_no"] == 1500000 and sum(x["so_tien"] for x in ad.ds("so_quy", {"quy_id": q_nh["id"]})) == 300000000)
    s, rep = ad.call("don_ban:baoCao", {"theo": "mat_hang"})
    canh = [x for x in rep["data"] if x.get("chua_xac_dinh")]
    hang = [x for x in rep["data"] if x["nhom"].startswith(f"{k}-HH")]
    ok("Báo cáo: doanh số 2,5tr chưa có giá vốn tách riêng, KHÔNG vào lãi gộp mặt hàng", canh and canh[0]["doanh_so"] >= 2500000 and not hang, (canh, hang))
    ok("Kế toán nhập giá vốn chuyển tiếp cần căn cứ", ad.lam("luot_giao:nhapGiaVon", l1["id"], {"gia_von": 600000})[0] == 400)
    ad.lam("luot_giao:nhapGiaVon", l1["id"], {"gia_von": 600000, "ghi_chu": "Giá vốn MISA tháng 10"})
    s, rep = ad.call("don_ban:baoCao", {"theo": "mat_hang"})
    hang = [x for x in rep["data"] if x["nhom"].startswith(f"{k}-HH")]
    ok("Sau khi có giá vốn: vào lãi gộp (doanh số 2,5tr, giá vốn 0,6tr)", hang and hang[0]["doanh_so"] == 2500000 and hang[0]["gia_von"] == 600000, hang)

    # ---------- 7. Chốt mẻ A gửi hệ số dòng của mẻ B ----------
    meB = ad.tao("me_sx", {"kho_id": KHO["PT"]["id"], "kho_tp_id": KHO["HN"]["id"]})
    pkB = ad.tao("phieu_kho", {"loai": "nhap", "kho_id": KHO["PT"]["id"], "dong": [{"mat_hang_id": MH["NL"]["id"], "so_kg": 100, "don_gia": 20000}]})
    ad.lam("phieu_kho:ghiSo", pkB["id"])
    cB = ad.tao("phieu_kho", {"loai": "cap_nvl", "kho_id": KHO["PT"]["id"], "me_sx_id": meB["id"], "dong": [{"mat_hang_id": MH["NL"]["id"], "so_kg": 100}]})
    ad.lam("phieu_kho:ghiSo", cB["id"])
    tB = ad.tao("phieu_kho", {"loai": "thu_hoi", "kho_id": KHO["PT"]["id"], "me_sx_id": meB["id"], "dong": [{"mat_hang_id": MH["TP"]["id"], "huong": "ra", "so_kg": 90},
              {"mat_hang_id": MH["NL"]["id"], "huong": "hao_hut", "loai_hao": "tu_nhien", "so_kg": 10}]})
    ad.lam("phieu_kho:ghiSo", tB["id"])
    dongB = [x for x in ad.lay("phieu_kho", tB["id"], "dong")["dong"] if x["huong"] == "ra"][0]
    s, r = kt.lam("me_sx:chot", me["id"], {"he_so": {str(dongB["id"]): 5}})
    ok("Chốt mẻ A kèm hệ số dòng của mẻ B: máy chủ từ chối, hệ số mẻ B không đổi", s == 400 and ad.lay("phieu_kho_dong", dongB["id"]).get("he_so") in (None, 1), r)
    U["nha_may"].lam("me_sx:baoXong", meB["id"])
    kt.lam("me_sx:chot", meB["id"]); kt.lam("me_sx:khoa", meB["id"])
    tB2 = ad.tao("phieu_kho", {"loai": "thu_hoi", "kho_id": KHO["PT"]["id"], "me_sx_id": meB["id"], "dong": [{"mat_hang_id": MH["TP"]["id"], "huong": "ra", "so_kg": 1}]})
    ok("Mẻ đã khóa kỳ: không thu hồi thêm", ad.lam("phieu_kho:ghiSo", tB2["id"])[0] == 400)
    kt.tao("me_sx_chi_phi", {"me_sx_id": meB["id"], "loai": "chung", "so_tien": 90000, "so_chung_tu": "PB-11"})
    mB = ad.lay("me_sx", meB["id"])
    s, r = kt.lam("me_sx:chot", meB["id"], {"dieu_chinh_ky_sau": True})
    ok("Chi phí đến muộn cho mẻ đã khóa: 'Cần điều chỉnh', chốt thành phiên bản điều chỉnh mới (giữ bản cũ)",
       mB["trang_thai"] == "can_chot_lai" and s == 200 and r["data"]["phien_ban"] == 2, (mB["trang_thai"], r))

    # ---------- 10. CCDC theo người giữ ----------
    kt.call("tai_san:create", {"ma": f"{k}-CAN", "ten": "Cân điện tử TV", "loai": "ccdc", "so_luong": 10})
    ts_ = ad.ds("tai_san", {"ma": f"{k}-CAN"})[0]

    def sk(api, loai, **kw):
        e = api.tao("tai_san_su_kien", {"tai_san_id": ts_["id"], "loai": loai, **kw})
        return api.lam("tai_san_su_kien:ghi", e["id"])[0]
    sk(U["kho"], "cap_phat", nguoi_nhan="Tổ A", so_luong=3); sk(U["kho"], "cap_phat", nguoi_nhan="Tổ B", so_luong=2)
    giu = {x["nguoi_giu"]: x["so_luong"] for x in ad.ds("tai_san_giu", {"tai_san_id": ts_["id"]})}
    ok("Cấp 3 cho tổ A, 2 cho tổ B: kho 5, A 3, B 2, tổng 10", ad.lay("tai_san", ts_["id"])["so_luong"] == 5 and giu == {"Tổ A": 3, "Tổ B": 2}, giu)
    ok("Thu hồi 3 từ tổ B (đang giữ 2): bị chặn", sk(U["kho"], "thu_hoi", nguoi_tra="Tổ B", so_luong=3) == 400)
    ok("Cấp vượt tồn kho (6 > 5): bị chặn", sk(U["kho"], "cap_phat", nguoi_nhan="Tổ C", so_luong=6) == 400)
    sk(U["kho"], "thu_hoi", nguoi_tra="Tổ A", so_luong=2)
    giu = {x["nguoi_giu"]: x["so_luong"] for x in ad.ds("tai_san_giu", {"tai_san_id": ts_["id"]})}
    ok("Thu hồi 2 từ tổ A: kho 7, A 1, B 2 — tổng vẫn 10", ad.lay("tai_san", ts_["id"])["so_luong"] == 7 and giu == {"Tổ A": 1, "Tổ B": 2})

    # ---------- 11. CSV có dấu phẩy, ngoặc kép, xuống dòng trong ô ----------
    csv = (f'Mã khách,Tên khách,Địa chỉ,Ghi chú\n{k}-C1,"Công ty A, chi nhánh 2","Số 5, ngõ 10, Cầu Giấy, Hà Nội","Khách ""VIP""\ngiao sáng"\n'
           f'{k}-C2,Cửa hàng B,"Hải Phòng",\n')
    lid, r = lo(kt, "khach_hang", csv)
    ad.lam("nhap_lo:duyet", lid); ad.lam("nhap_lo:ghi", lid)
    c1 = ad.ds("khach_hang", {"ma": f"{k}-C1"})
    ok("CSV dấu phẩy / ngoặc kép / xuống dòng trong ô: đọc nguyên, không lệch cột",
       c1 and c1[0]["ten"] == "Công ty A, chi nhánh 2" and c1[0]["dia_chi"] == "Số 5, ngõ 10, Cầu Giấy, Hà Nội" and c1[0]["ghi_chu"] == 'Khách "VIP"\ngiao sáng', c1)

    # ---------- Tệp .xlsx thật + checksum ----------
    try:
        import openpyxl
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Ton"
        ws.append(["Mã kho", "Mã hàng", "Số lượng", "Giá trị", "Tình trạng giá"])
        ws.append([f"{k}-HCM", f"{k}-PT", 12.5, 250000, "Đã chốt"])
        wb.create_sheet("Khac").append(["x"])
        buf = io.BytesIO(); wb.save(buf)
        s, r = kt.call("nhap_lo:create", {"loai": "ton_dau_ky", "nguon": "Google Sheet / tải .xlsx"})
        lid = r["data"]["id"]
        s, r = kt.lam("nhap_lo:taiTep", lid, {"ten_tep": "Kiem-ke.xlsx", "base64": base64.b64encode(buf.getvalue()).decode(), "trang_tinh": "Ton", "ma_nguon": "1AbCSheetId"})
        s2, r2 = kt.lam("nhap_lo:kiem", lid)
        l = ad.lay("nhap_lo", lid)
        ok("Đọc tệp .xlsx thật (chọn trang tính), lưu tệp gốc + SHA-256 + thời điểm lấy + mã nguồn",
           s == 200 and r["data"]["trang_tinh"] == ["Ton", "Khac"] and r2["data"]["hop_le"] == 1 and len(l["checksum"]) == 64 and l["tep_goc"] and l["ma_nguon"] == "1AbCSheetId", (r, r2))
    except ImportError:
        ok("openpyxl có sẵn để tạo tệp thử", False)

    # ---------- Quy đổi ĐVT (phồng tôm thùng) ----------
    lid, r = lo(kt, "quy_doi_dvt", f"Mã hàng\tĐơn vị giao dịch\tHệ số\n{k}-THUNG\tThùng\t5\n{k}-THUNG\tGói\t0,2")
    ad.lam("nhap_lo:duyet", lid); ad.lam("nhap_lo:ghi", lid)
    d = ad.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": MH["THUNG"]["id"], "kho_id": KHO["HN"]["id"], "dvt_nhap": "thung", "sl_nhap": 3, "don_gia": 60000}]})
    dd = ad.lay("don_ban", d["id"], "dong")["dong"][0]
    ok("Bán 3 thùng (1 thùng = 5 kg): tồn / giá vốn tính theo 15 kg, ghi 3 thùng", dd["so_kg"] == 15 and dd["so_bao"] == 3, dd)
    ok("ĐVT chưa khai quy đổi: báo lỗi", ad.call("don_ban:create", {"khach_id": kh["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": MH["HH"]["id"], "kho_id": KHO["HN"]["id"], "dvt_nhap": "thung", "sl_nhap": 1}]},
       q="?updateAssociationValues[]=dong")[0] >= 400)

    # ---------- Dở dang đầu kỳ ----------
    lid, r = lo(kt, "do_dang_dau_ky", f"Mã dở dang\tMã kho nhà máy\tKg dở dang\tGiá trị\tXưởng / tổ\n{k}-W1\t{k}-PT\t200\t4.200.000\tTổ 2")
    ad.lam("nhap_lo:duyet", lid); ad.lam("nhap_lo:ghi", lid)
    mw = ad.ds("me_sx", {"xuong": "Tổ 2", "kho_id": KHO["PT"]["id"]})
    ok("Dở dang đầu kỳ: mẻ mở với 200 kg, chi phí dở dang 4,2tr", mw and mw[0]["kg_do_dang_dau"] == 200 and mw[0]["chi_phi"] == 4200000, mw)
    lid, r = lo(kt, "do_dang_dau_ky", f"Mã dở dang\tMã kho nhà máy\tKg dở dang\tGiá trị\n{k}-W1\t{k}-PT\t200\t4.200.000")
    ok("Dán lại dở dang đầu kỳ: trùng", r.get("trung") == 1)

    # ---------- Thu hộ tất toán một phần ----------
    pt = ad.tao("phieu_thu", {"khach_id": kh["id"], "don_vi_id": APH["id"], "quy_id": q_tm["id"], "so_tien": 900000})
    ad.lam("phieu_thu:ghi", pt["id"])
    dTL = ad.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": dv["TL"]["id"], "dong": [{"mat_hang_id": MH["HH"]["id"], "kho_id": KHO["DN"]["id"], "so_kg": 20, "don_gia": 50000}]})
    ad.lam("don_ban:chotDon", dTL["id"]); ddt = ad.lay("don_ban", dTL["id"], "dong")["dong"][0]["id"]
    s, r = ad.lam("luot_giao:taoLuot", None, {"don_ban_id": dTL["id"], "dong": [{"don_ban_dong_id": ddt, "so_kg": 20}]}); ad.lam("luot_giao:khachNhan", r["data"]["id"])
    ad.lam("phieu_thu:phanBoThuHo", pt["id"], {"ghi_chu": "Khách chuyển nhầm", "phan_bo": [{"don_ban_id": dTL["id"], "so_tien": 900000}]})
    th_ = ad.ds("thu_ho", {"phieu_thu_id": pt["id"]})[0]
    ad.lam("thu_ho:tatToan", th_["id"], {"so_tien": 400000, "ghi_chu": "UNC 001 APH → TL"})
    t1 = ad.lay("thu_ho", th_["id"])
    ok("Tất toán thu hộ một phần 400k/900k: còn giữ hộ 500k, có chứng từ", t1["da_tat_toan"] == 400000 and t1["trang_thai"] == "dang_giu_ho" and "UNC 001" in t1["chung_tu_tat_toan"])
    ok("Tất toán quá phần còn: bị chặn", ad.lam("thu_ho:tatToan", th_["id"], {"so_tien": 600000, "ghi_chu": "x"})[0] == 400)

    # ---------- 12. NoCost phủ quyết ----------
    nk = U["nm_kt"]
    ok("Người có vai trò kế toán + 'Không xem giá vốn': gọi giá vốn bị chặn", nk.call("gia_von:list")[0] == 403 and nk.call("so_gia_von:list")[0] == 403)
    ok("… không xem lãi gộp / chốt giá thành", nk.call("don_ban:baoCao", {"theo": "don_vi"})[0] in (400, 403))
    d0 = nk.lay("don_ban", d1["id"])
    ok("… đọc đơn không thấy giá vốn", d0 is not None and "gia_von" not in d0, d0)

    # ---------- Phạm vi kho / quỹ ----------
    for x in ad.ds("pham_vi", {"nguoi_dung_id": {"$in": [uid["kho_hn"], uid["thu_chi"]]}}):
        ad.call("pham_vi:destroy", {}, q=f"?filterByTk={x['id']}")
    ad.tao("pham_vi", {"nguoi_dung_id": uid["kho_hn"], "kho_id": KHO["HN"]["id"]})
    kh_hn = U["kho_hn"]
    p1 = kh_hn.tao("phieu_kho", {"loai": "xuat", "kho_id": KHO["DN"]["id"], "dong": [{"mat_hang_id": MH["HH"]["id"], "so_kg": 1}]})
    ok("Thủ kho Hà Nội ghi phiếu kho Đà Nẵng: bị chặn", kh_hn.lam("phieu_kho:ghiSo", p1["id"])[0] == 400)
    tk = kh_hn.ds("ton_kho", {})
    ok("Thủ kho Hà Nội chỉ đọc được tồn kho Hà Nội", tk and all(x["kho_id"] == KHO["HN"]["id"] for x in tk), [x["kho_id"] for x in tk][:5])
    ok("Mở phiếu kho Đà Nẵng (in phiếu) ngoài phạm vi: không thấy", kh_hn.call("phieu_kho:get", q=f"?filterByTk={p1['id']}")[1].get("data") is None)
    ad.tao("pham_vi", {"nguoi_dung_id": uid["thu_chi"], "quy_id": q_tm["id"]})
    pt2 = U["thu_chi"].tao("phieu_thu", {"khach_id": kh["id"], "don_vi_id": APH["id"], "quy_id": q_nh["id"], "hinh_thuc": "chuyen_khoan", "ma_gd": "X1", "so_tien": 1000})
    ok("Thủ quỹ được giao quỹ TM ghi thu vào tài khoản MB: bị chặn", U["thu_chi"].lam("phieu_thu:ghi", pt2["id"])[0] == 400)

    # ---------- Đối chiếu bảo toàn cuối ----------
    cn, d = can()
    ok("Đối chiếu bảo toàn toàn hệ thống: số lượng, giá trị, điều chỉnh đều cân", cn, d)
    loi = [x for x in KQ if not x[1]]
    print(f"\nTỔNG {len(KQ)} ca, LỖI {len(loi)}")
    for ten, _ in loi:
        print("  LỖI:", ten)
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
