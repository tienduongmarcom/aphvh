#!/usr/bin/env python3
"""Bộ kiểm NocoBase 0.4.1 — Factory MES Lite (dữ liệu giả, tiền tố T41-). Bổ sung, không thay các bộ kiểm cũ.
Bao phủ bảng kịch bản mục 10 đặc tả 0.4.1; mỗi ca kiểm số dư kho / giá trị trước–sau, không chỉ mã trả về.

    python3 kiem_041.py --email <quản trị> --password <mật khẩu>
"""
import argparse
import json
import sys
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
    k = "T41-" + uuid.uuid4().hex[:5]
    nhom = lambda t: print(f"\n==== {t}")
    rid = lambda: uuid.uuid4().hex
    ad.lam("cau_hinh:nangCap")
    for kh_, gt in (("giu_khi_duyet", "co"), ("pham_vi_mac_dinh", "tu_choi")):
        ad.lam("cau_hinh:dat", None, {"khoa": kh_, "gia_tri": gt})

    pw = "Thu" + uuid.uuid4().hex[:10]
    VT = {"nha_may": ["nha_may", "khong_xem_gia"], "ke_toan": ["ke_toan"], "kho": ["kho"]}
    uid = {}
    for ten, roles in VT.items():
        em = f"t041-{ten}@aphvh.local"
        u = ad.ds("users", {"email": em})
        if u:
            ad.call("users:update", {"password": pw, "roles": roles}, q=f"?filterByTk={u[0]['id']}")
            uid[ten] = u[0]["id"]
        else:
            uid[ten] = ad.tao("users", {"email": em, "nickname": "T041 " + ten, "password": pw, "roles": roles})["id"]
    for x in ad.ds("pham_vi", {"nguoi_dung_id": {"$in": list(uid.values())}}):
        ad.call("pham_vi:destroy", {}, q=f"?filterByTk={x['id']}")
    dv = {x["ma"]: x for x in ad.ds("don_vi", {})}
    K = {n: ad.tao("kho", {"ma": f"{k}-{n}", "ten": f"{n} {k}", "loai_kho": "nha_may"}) for n in ("NL", "VT", "TP")}
    K["HG"] = ad.tao("kho", {"ma": f"{k}-HG", "ten": f"Hàng gửi VH {k}", "loai_kho": "hang_gui"})
    K["HN"] = ad.tao("kho", {"ma": f"{k}-HN", "ten": f"HN {k}"})
    for n in ("NL", "VT", "TP", "HG"):
        ad.tao("pham_vi", {"nguoi_dung_id": uid["nha_may"], "kho_id": K[n]["id"]})
    ad.tao("pham_vi", {"nguoi_dung_id": uid["kho"], "kho_id": K["HN"]["id"]})
    time.sleep(1)
    U = {t: API(o.url, f"t041-{t}@aphvh.local", pw, VT[t][0]) for t in VT}
    nm, kt = U["nha_may"], U["ke_toan"]

    def mh(m, ten, **x):
        return ad.tao("mat_hang", {"ma": f"{k}-{m}", "ten": ten, **x})
    M = {"DO": mh("DO", "Đỗ xanh hạt"), "DOTV": mh("DOTV", "Đỗ tách vỏ", kg_bao=25, gia_ban=50000), "TAM": mh("TAM", "Tấm đỗ", loai_hang="phu_pham"),
         "CAM": mh("CAM", "Cám đỗ", loai_hang="phu_pham"), "BAO": mh("BAO", "Bao 25kg", dvt_ton="cai", loai_hang="bao_bi"),
         "CUI": mh("CUI", "Củi đốt (kg)"), "BOT": mh("BOT", "Bột năng xá"),
         "THUNG": mh("THUNG", "Bột năng thùng 20 gói × 500g", dvt_ton="thung", kg_moi_dvt=10, kg_dvt_can_cu="20 gói × 0,5 kg (cân mẫu)"),
         "VOT": mh("VOT", "Vỏ thùng carton", dvt_ton="cai", loai_hang="bao_bi"), "TUI": mh("TUI", "Túi 500g", dvt_ton="cai", loai_hang="bao_bi"),
         "DAU": mh("DAU", "Dầu đậu nành bồn", dvt_ton="lit", kg_moi_dvt=0.92, kg_dvt_can_cu="Khối lượng riêng 0,92 kg/l (phiếu kiểm NCC)"),
         "CHAI": mh("CHAI", "Dầu chai 1L", dvt_ton="cai", kg_moi_dvt=0.92, kg_dvt_can_cu="1 lít × 0,92"),
         "DAU2": mh("DAU2", "Dầu bồn chưa có khối lượng riêng", dvt_ton="lit"),
         "BANH": mh("BANH", "Bột phồng tôm"), "NUOC": mh("NUOC", "Nước pha"), "PT": mh("PT", "Phồng tôm thành phẩm"),
         "X": mh("X", "Thành phẩm X")}

    def ton(kk, mm):
        r = ad.ds("ton_kho", {"kho_id": K[kk]["id"], "mat_hang_id": M[mm]["id"]})
        return r[0]["so_kg"] if r else 0

    def gv(kk, mm):
        r = ad.ds("gia_von", {"kho_id": K[kk]["id"], "mat_hang_id": M[mm]["id"]})
        return r[0] if r else {"so_kg": 0, "gia_tri": 0}

    def nhap(kk, mm, sl, gia):
        pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K[kk]["id"], "dong": [{"mat_hang_id": M[mm]["id"], "so_kg": sl, "don_gia": gia}]})
        kt.lam("phieu_kho:ghiSo", pk["id"])
    for kk, mm, sl, gia in (("NL", "DO", 10000, 20000), ("VT", "BAO", 2000, 3000), ("NL", "CUI", 1000, 1500), ("NL", "BOT", 5000, 15000),
                            ("VT", "VOT", 1000, 4000), ("VT", "TUI", 10000, 200), ("NL", "DAU", 1000, 40000), ("NL", "DAU2", 100, 40000),
                            ("NL", "BANH", 1000, 30000), ("NL", "NUOC", 1000, 1)):
        nhap(kk, mm, sl, gia)

    def mau(ma, loai, dong, pp="kg", nguong=None):
        m = kt.tao("mau_sx", {"ma": f"{k}-{ma}", "ten": ma, "loai_cn": loai, "xuong": ma, "pp_gia_thanh": pp})
        pb = kt.tao("mau_sx_phien_ban", {"mau_sx_id": m["id"], "nguong_chenh_pct": nguong, "can_cu": "Thực nghiệm 3 mẻ tháng 10",
                                         "dong": [{**d, "mat_hang_id": M[d["mat_hang_id"]]["id"]} for d in dong]})
        s, r = kt.lam("mau_sx_phien_ban:duyet", pb["id"])
        return m, pb
    nhom("1. Thư viện mẫu 4 công nghệ, định mức có phiên bản")
    mDo, pbDo = mau("DO", "GRADING", [
        {"vai_tro": "nvl", "mat_hang_id": "DO", "co_so": "nvl", "dinh_muc": 1, "nguong_hao_pct": 3},
        {"vai_tro": "tp", "mat_hang_id": "DOTV", "co_so": "nvl", "dinh_muc": 0.82, "he_so_gia": 1},
        {"vai_tro": "phu_pham", "mat_hang_id": "TAM", "co_so": "nvl", "dinh_muc": 0.10, "gia_tham_chieu": 8000, "nguon_gia_tc": "Giá bán tấm T9"},
        {"vai_tro": "phu_pham", "mat_hang_id": "CAM", "co_so": "nvl", "dinh_muc": 0.05, "gia_tham_chieu": 3000, "nguon_gia_tc": "Giá bán cám T9"},
        {"vai_tro": "bao_bi", "mat_hang_id": "BAO", "co_so": "tp", "dinh_muc": 0.04},
        {"vai_tro": "nhien_lieu", "mat_hang_id": "CUI", "co_so": "nvl", "dinh_muc": 0.05}])
    mBot, _ = mau("BOT", "REPACKING", [
        {"vai_tro": "tp", "mat_hang_id": "THUNG", "co_so": "tp", "dinh_muc": 1},
        {"vai_tro": "nvl", "mat_hang_id": "BOT", "co_so": "tp", "dinh_muc": 10},
        {"vai_tro": "bao_bi", "mat_hang_id": "VOT", "co_so": "tp", "dinh_muc": 1},
        {"vai_tro": "bao_bi", "mat_hang_id": "TUI", "co_so": "tp", "dinh_muc": 20}])
    mDau, _ = mau("DAU", "LIQUID_FILLING", [
        {"vai_tro": "tp", "mat_hang_id": "CHAI", "co_so": "tp", "dinh_muc": 1}, {"vai_tro": "nvl", "mat_hang_id": "DAU", "co_so": "tp", "dinh_muc": 1}])
    mDau2, _ = mau("DAU2", "LIQUID_FILLING", [
        {"vai_tro": "tp", "mat_hang_id": "CHAI", "co_so": "tp", "dinh_muc": 1}, {"vai_tro": "nvl", "mat_hang_id": "DAU2", "co_so": "tp", "dinh_muc": 1}])
    mPt, _ = mau("PT", "BLENDING_COOKING", [
        {"vai_tro": "nvl", "mat_hang_id": "BANH", "co_so": "nvl", "dinh_muc": 1, "nguong_hao_pct": 5},
        {"vai_tro": "nuoc", "mat_hang_id": "NUOC", "co_so": "nvl", "dinh_muc": 0.3}, {"vai_tro": "tp", "mat_hang_id": "PT", "co_so": "nvl", "dinh_muc": 0.97}])
    mX, _ = mau("X", "GRADING", [{"vai_tro": "nvl", "mat_hang_id": "DO", "co_so": "nvl", "dinh_muc": 1},
                                 {"vai_tro": "tp", "mat_hang_id": "X", "co_so": "nvl", "dinh_muc": 1}])
    ok("Tạo 4 loại mẫu (đỗ / đóng gói / dầu / phồng tôm), phiên bản đã duyệt", ad.lay("mau_sx_phien_ban", pbDo["id"])["trang_thai"] == "da_duyet")
    s, r = nm.tao("mau_sx_phien_ban", {"mau_sx_id": mDo["id"], "dong": [{"vai_tro": "tp", "mat_hang_id": M["DOTV"]["id"], "co_so": "nvl", "dinh_muc": 0.9}]}), None
    ok("Nhà máy đề xuất định mức mới: trạng thái 'đề xuất', chưa dùng được", s["trang_thai"] == "de_xuat")
    s2, r2 = nm.lam("mau_sx_phien_ban:duyet", s["id"], {"can_cu": "x"})
    ok("Nhà máy không tự duyệt định mức", s2 in (400, 403))
    s2, r2 = kt.call("mau_sx_dong:update", {"dinh_muc": 0.5}, q=f"?filterByTk={ad.ds('mau_sx_dong', {'mau_sx_phien_ban_id': pbDo['id']})[0]['id']}")
    ok("Sửa dòng định mức đã duyệt: bị chặn (phải tạo phiên bản mới)", s2 == 400, r2)

    nhom("2. Mở mẻ từ mẫu xưởng đỗ: tự điền định mức, KHÔNG ghi kho")
    do0, tp0 = ton("NL", "DO"), ton("TP", "DOTV")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mDo["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"], "request_id": f"{k}-M1"})
    me1 = r["data"]["id"]
    s, r = nm.lam("me_sx:goiY", me1, {"nvl_kg": 1000})
    gy = {x["ma"].split("-")[-1]: x["du_kien"] for x in r["data"]["goi_y"]}
    ok("Gợi ý: 1.000 kg đỗ → 820 tách vỏ, 100 tấm, 50 cám, 32,8 bao, 50 kg củi", gy == {"DO": 1000, "DOTV": 820, "TAM": 100, "CAM": 50, "BAO": 32.8, "CUI": 50}, gy)
    ok("Mở mẻ + gợi ý: tồn không đổi", ton("NL", "DO") == do0 and ton("TP", "DOTV") == tp0)
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mDo["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"], "request_id": f"{k}-M1"})
    ok("Mở lại cùng mã yêu cầu: không tạo mẻ thứ hai", r["data"].get("da_mo_truoc") and r["data"]["id"] == me1)

    nhom("3. Thay định mức sau khi mẻ đã bắt đầu → mẻ giữ snapshot cũ")
    pb2 = kt.tao("mau_sx_phien_ban", {"mau_sx_id": mDo["id"], "can_cu": "Đổi nguyên liệu nhập khẩu", "dong": [
        {"vai_tro": "nvl", "mat_hang_id": M["DO"]["id"], "co_so": "nvl", "dinh_muc": 1, "nguong_hao_pct": 3},
        {"vai_tro": "tp", "mat_hang_id": M["DOTV"]["id"], "co_so": "nvl", "dinh_muc": 0.85, "he_so_gia": 1}]})
    kt.lam("mau_sx_phien_ban:duyet", pb2["id"])
    s, r = nm.lam("me_sx:goiY", me1, {"nvl_kg": 1000})
    ok("Mẻ cũ vẫn gợi ý 820 (định mức v1)", [x["du_kien"] for x in r["data"]["goi_y"] if x["vai_tro"] == "tp"] == [820])
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mDo["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"], "nvl_kg": 1000})
    ok("Mẻ mở sau dùng định mức mới (850)", [x["du_kien"] for x in r["data"]["goi_y"] if x["vai_tro"] == "tp"] == [850], r)
    me_moi = r["data"]["id"]
    s, r = kt.lam("me_sx:chot", me_moi, {"chap_nhan_chenh": True, "ly_do_chenh": "Không được bỏ qua kết thúc"})
    ok("Mẻ đang sản xuất: chấp nhận chênh không thay thế kết thúc mẻ", s == 400, r)

    nhom("3b. Chênh ÂM: đầu ra lớn hơn đầu vào, giải trình có dấu")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mX["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    me_am = r["data"]["id"]
    s, r = nm.lam("me_sx:ghiThucTe", me_am, {"request_id": rid(),
        "nvl": [{"mat_hang_id": M["DO"]["id"], "so_luong": 100}],
        "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 110}], "ket_thuc": True})
    ok("Cân âm 10kg khi đầu ra 110kg > đầu vào 100kg", s == 200 and r["data"]["con_lai"] == -10, r)
    s, r = nm.lam("me_sx:giaiTrinh", me_am, {"so_kg": 10, "phan_loai": "hao_bat_thuong", "ly_do": "Không hợp lý"})
    ok("Không cho ghi hao bất thường với chênh thừa", s == 400, r)
    s, r = nm.lam("me_sx:giaiTrinh", me_am, {"so_kg": 10, "phan_loai": "do_sai", "ly_do": "Cân đầu ra cần đối chiếu"})
    g_am = r.get("data", {}).get("id")
    ok("Giải trình chênh thừa lưu số kg mang dấu âm", s == 200 and float(ad.lay("sx_giai_trinh", g_am)["so_kg"]) == -10, r)
    s, r = kt.lam("sx_giai_trinh:duyet", g_am)
    ok("Duyệt giải trình chênh âm đưa số còn lại về 0", s == 200 and r["data"]["con_lai"] == 0, r)

    nhom("4. NVL 1.000 kg, sản lượng 970 kg → báo chênh 30, KHÔNG tự ghi hao hụt")
    rq1 = rid()
    v1 = {"request_id": rq1, "nvl": [{"mat_hang_id": M["DO"]["id"], "so_luong": 1000, "so_lo": "LO-NL-01"}],
          "tp": [{"mat_hang_id": M["DOTV"]["id"], "so_luong": 820, "so_bao": 33, "so_lo": "LO-TP-01"}],
          "phu_pham": [{"mat_hang_id": M["TAM"]["id"], "so_luong": 100}, {"mat_hang_id": M["CAM"]["id"], "so_luong": 50}],
          "bao_bi": [{"mat_hang_id": M["BAO"]["id"], "so_luong": 33}], "nhien_lieu": [{"mat_hang_id": M["CUI"]["id"], "so_luong": 50}]}
    s, r = nm.lam("me_sx:ghiThucTe", me1, v1)
    ok("Bao bì dùng 33 khác định mức 32,8 không ghi nguyên nhân: bị chặn", s == 400 and "nguyên nhân" in json.dumps(r, ensure_ascii=False), r)
    v1["bao_bi"][0]["ly_do"] = "Làm tròn bao nguyên"
    s, r = nm.lam("me_sx:ghiThucTe", me1, v1)
    d = r.get("data", {})
    ok("Ghi thực tế: chênh 30 kg, kết quả 'còn chênh', hao hụt ghi sổ = 0", s == 200 and d["chenh"] == 30 and d["ket_qua"] == "co_chenh" and d["kg_hao"] == 0, d)
    ok("Củi 50 kg (ĐVT kg) KHÔNG vào khối lượng nguyên liệu (kg vào = 1.000)", d["kg_vao"] == 1000)
    ok("Kho: đỗ −1.000, tách vỏ +820, bao −33, củi −50", ton("NL", "DO") == do0 - 1000 and ton("TP", "DOTV") == tp0 + 820 and ton("VT", "BAO") == 2000 - 33
       and ton("NL", "CUI") == 950)
    s, r = nm.lam("me_sx:ghiThucTe", me1, v1)
    ok("Gửi lại cùng mã yêu cầu: không ghi kho lần hai", r["data"].get("da_ghi_truoc") and ton("NL", "DO") == do0 - 1000)
    hao = [x for x in ad.ds("phieu_kho_dong", {"huong": "hao_hut"}) if x.get("phieu_kho_id") in [p["id"] for p in ad.ds("phieu_kho", {"me_sx_id": me1})]]
    ok("Không có dòng hao hụt tự sinh", not hao)

    nhom("5. Ghi hao hụt đã đo 20 kg → còn 10 kg cần giải trình")
    s, r = nm.lam("me_sx:ghiThucTe", me1, {"request_id": rid(), "hao": [{"so_kg": 20}], "ket_thuc": True})
    d = r.get("data", {})
    ok("Hao xác nhận 20, còn chênh 10, mẻ 'chờ cân đối'", d.get("kg_hao") == 20 and d.get("con_lai") == 10 and d.get("tt_van_hanh") == "cho_can_doi", d)
    s, r = kt.lam("me_sx:chot", me1)
    ok("Chốt giá thành khi còn chênh chưa giải trình: bị chặn", s == 400, r)
    s, r = nm.lam("me_sx:ghiThucTe", me1, {"request_id": rid(), "hao": [{"so_kg": 5, "loai_hao": "bat_thuong"}]})
    ok("Nhà máy không tự ghi hao bất thường", s == 400)
    s, r = nm.lam("me_sx:giaiTrinh", me1, {"so_kg": 15, "phan_loai": "do_sai", "ly_do": "x"})
    ok("Giải trình vượt phần còn lại: bị chặn", s == 400)
    s, r = nm.lam("me_sx:giaiTrinh", me1, {"so_kg": 6, "phan_loai": "hao_bat_thuong", "ly_do": "Đổ vỡ khi bốc"})
    g1 = r["data"]["id"]
    s, r = nm.lam("me_sx:giaiTrinh", me1, {"so_kg": 4, "phan_loai": "do_sai", "ly_do": "Cân bàn lệch 4 kg (đã hiệu chỉnh)"})
    g2 = r["data"]["id"]
    s, r = nm.lam("sx_giai_trinh:duyet", g1)
    ok("Nhà máy không duyệt giải trình", s in (400, 403))
    kt.lam("sx_giai_trinh:duyet", g1)
    s, r = kt.lam("sx_giai_trinh:duyet", g2)
    me = ad.lay("me_sx", me1)
    ok("Kế toán duyệt: hao bất thường 6 kg thành chứng từ, còn chênh 0, mẻ 'hoàn thành thực tế'", r["data"]["con_lai"] == 0 and me["tt_van_hanh"] == "hoan_thanh"
       and me["kg_hao_bat_thuong"] == 6, [r["data"], me["tt_van_hanh"]])
    s, r = kt.lam("me_sx:chot", me1)
    d = r.get("data", {})
    # Chi phí: 1.000 × 20.000 + 33 bao × 3.000 + 50 kg củi × 1.500 = 20.174.000; phụ phẩm theo giá tham chiếu: 100×8.000 + 50×3.000 = 950.000
    ok("Chốt theo phương pháp của mẫu, phụ phẩm theo giá tham chiếu đã duyệt (950.000)", s == 200 and ad.lay("me_sx", me1)["gia_tri_phu_pham"] == 950000, [s, d.get("tong_phan_bo")])

    nhom("6. Sản xuất qua hai ngày: dở dang không tính hai lần")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mX["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    me2 = r["data"]["id"]
    s, r = nm.lam("me_sx:ghiThucTe", me2, {"request_id": rid(), "nvl": [{"mat_hang_id": M["DO"]["id"], "so_luong": 500}],
                                            "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 200}], "wip_cuoi": 300})
    ok("Ngày 1: vào 500, ra 200, dở dang 300 → cân", r["data"]["ket_qua"] == "can" and r["data"]["chenh"] == 0, r["data"])
    s, r = nm.lam("me_sx:ghiThucTe", me2, {"request_id": rid(), "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 295}], "hao": [{"so_kg": 5}],
                                            "wip_cuoi": 0, "ket_thuc": True})
    ok("Ngày 2: ra thêm 295 + hao 5, dở dang 0 → kg vào vẫn 500, cân, hoàn thành", r["data"]["kg_vao"] == 500 and r["data"]["ket_qua"] == "can"
       and r["data"]["tt_van_hanh"] == "hoan_thanh", r["data"])

    nhom("7. Phồng tôm: thêm nước, sấy — không báo hao giả, thiếu số đo nước → chưa đủ căn cứ")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mPt["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    me3 = r["data"]["id"]
    s, r = nm.lam("me_sx:ghiThucTe", me3, {"request_id": rid(), "nvl": [{"mat_hang_id": M["BANH"]["id"], "so_luong": 100}],
                                            "tp": [{"mat_hang_id": M["PT"]["id"], "so_luong": 97}], "nuoc_vao": 30, "ket_thuc": True})
    ok("Chưa đo nước bay hơi: 'Chưa đủ căn cứ cân đối' (không coi 30 kg là hao)", r["data"]["ket_qua"] == "chua_du" and r["data"]["kg_hao"] == 0, r["data"])
    s, r = nm.lam("me_sx:ghiThucTe", me3, {"request_id": rid(), "nuoc_bay_hoi": 30, "hao": [{"so_kg": 3}], "ket_thuc": True})
    ok("Ghi nước bay hơi 30 + hao 3: cân (100 + 30 = 97 + 30 + 3)", r["data"]["ket_qua"] == "can" and r["data"]["tt_van_hanh"] == "hoan_thanh", r["data"])

    nhom("8. Đóng gói 200 thùng × 20 gói × 500 g: gợi ý 2.000 kg + bao bì; ghi thực, vỏ hỏng có lý do")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mBot["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"], "sl_ke_hoach": 200})
    me4 = r["data"]["id"]
    gy = {x["ma"].split("-")[-1]: x["du_kien"] for x in r["data"]["goi_y"]}
    ok("Gợi ý: 200 thùng, 2.000 kg bột, 200 vỏ thùng, 4.000 túi", gy == {"THUNG": 200, "BOT": 2000, "VOT": 200, "TUI": 4000}, gy)
    s, r = nm.lam("me_sx:ghiThucTe", me4, {"request_id": rid(), "nvl": [{"mat_hang_id": M["BOT"]["id"], "so_luong": 2000}],
        "tp": [{"mat_hang_id": M["THUNG"]["id"], "so_luong": 200}], "bao_bi": [{"mat_hang_id": M["VOT"]["id"], "so_luong": 200, "so_hong": 5}], "ket_thuc": True})
    ok("5 vỏ hỏng không ghi lý do: bị chặn", s == 400)
    vot0, tui0 = ton("VT", "VOT"), ton("VT", "TUI")
    s, r = nm.lam("me_sx:ghiThucTe", me4, {"request_id": rid(), "nvl": [{"mat_hang_id": M["BOT"]["id"], "so_luong": 2000}],
        "tp": [{"mat_hang_id": M["THUNG"]["id"], "so_luong": 200}],
        "bao_bi": [{"mat_hang_id": M["VOT"]["id"], "so_luong": 200, "so_hong": 5, "ly_do": "5 vỏ rách khi gấp", "kho_id": K["VT"]["id"]},
                   {"mat_hang_id": M["TUI"]["id"], "so_luong": 4010, "ly_do": "10 túi hàn hỏng thay", "kho_id": K["VT"]["id"]}], "ket_thuc": True})
    d = r.get("data", {})
    ok("Thùng quy kg theo quy cách (200 × 10 = 2.000): cân", s == 200 and d["kg_tp"] == 2000 and d["ket_qua"] == "can", d)
    ok("Vỏ thùng trừ 205 (200 dùng + 5 hỏng), túi trừ 4.010 — không ép theo công thức", ton("VT", "VOT") == vot0 - 205 and ton("VT", "TUI") == tui0 - 4010)
    bb = {x["mat_hang_id"]: x for x in d.get("bao_bi", [])}
    ok("Lưu chênh bao bì so định mức + nguyên nhân", bb[M["VOT"]["id"]]["hong"] == 5 and bb[M["TUI"]["id"]]["dinh_muc"] == 4000 and bb[M["TUI"]["id"]]["ly_do"])

    nhom("9. Dầu ăn Lít / chai: quy đổi khối lượng có căn cứ")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mDau["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    me5 = r["data"]["id"]
    s, r = nm.lam("me_sx:ghiThucTe", me5, {"request_id": rid(), "nvl": [{"mat_hang_id": M["DAU"]["id"], "so_luong": 100}],
                                            "tp": [{"mat_hang_id": M["CHAI"]["id"], "so_luong": 99}], "hao": [{"so_kg": 0.92}], "ket_thuc": True})
    ok("100 lít × 0,92 = 92 kg vào; 99 chai = 91,08 kg + hao 0,92 → cân", r["data"]["kg_vao"] == 92 and r["data"]["ket_qua"] == "can", r["data"])
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mDau2["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    s, r = nm.lam("me_sx:ghiThucTe", r["data"]["id"], {"request_id": rid(), "nvl": [{"mat_hang_id": M["DAU2"]["id"], "so_luong": 10}],
                                                      "tp": [{"mat_hang_id": M["CHAI"]["id"], "so_luong": 10}], "ket_thuc": True})
    ok("Dầu chưa khai khối lượng riêng: 'chưa đủ căn cứ', không dùng hệ số tùy tiện", r["data"]["ket_qua"] == "chua_du"
       and any("quy đổi kg" in x for x in r["data"]["van_de"]), r["data"])

    nhom("10. Chỉ có thành phẩm, thiếu phiếu cấp nguyên liệu → không chốt giá thành chính thức")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mX["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    me6 = r["data"]["id"]
    s, r = nm.lam("me_sx:ghiThucTe", me6, {"request_id": rid(), "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 50}], "ket_thuc": True})
    ok("Cân đối: 'chưa đủ căn cứ' (chưa có nguyên liệu vào)", r["data"]["ket_qua"] == "chua_du")
    kt.tao("me_sx_chi_phi", {"me_sx_id": me6, "loai": "nhan_cong", "so_tien": 100000, "so_chung_tu": f"BL-{k}"})
    s, r = kt.lam("me_sx:chot", me6, {"chap_nhan_chenh": True, "ly_do_chenh": "thử"})
    ok("Chốt bị chặn kể cả khi kế toán chấp nhận chênh", s == 400 and "thiếu phiếu cấp" in json.dumps(r, ensure_ascii=False), r)

    nhom("11. Hàng gửi VH để APH gia công: không tự thành sở hữu APH")
    hs = kt.tao("sx_ho_so_gia_cong", {"ben_gui_id": dv["VH"]["id"], "ben_nhan_id": dv["APH"]["id"], "kho_id": K["HG"]["id"], "can_cu": "BB giao nhận 24/10"})
    s, r = kt.call("sx_ho_so_gia_cong:create", {"ben_gui_id": dv["VH"]["id"], "ben_nhan_id": dv["APH"]["id"], "kho_id": K["NL"]["id"]})
    ok("Hồ sơ gắn kho thường: bị chặn (phải kho hàng gửi riêng)", s == 400)
    nl_gt0 = gv("NL", "DO")["gia_tri"]
    s, r = kt.lam("sx_ho_so_gia_cong:nhanHang", hs["id"], {"request_id": f"{k}-GC1", "dong": [{"mat_hang_id": M["DO"]["id"], "so_kg": 1000}]})
    s, r2 = kt.lam("sx_ho_so_gia_cong:nhanHang", hs["id"], {"request_id": f"{k}-GC1", "dong": [{"mat_hang_id": M["DO"]["id"], "so_kg": 1000}]})
    ok("Nhận 1.000 kg hàng gửi (gửi lại không nhân đôi): kho hàng gửi 1.000, giá trị sở hữu 0", ton("HG", "DO") == 1000 and gv("HG", "DO")["gia_tri"] == 0
       and r2["data"].get("da_nhan_truoc"))
    ok("Giá trị tồn đỗ của bên nhận (kho NL) không đổi", gv("NL", "DO")["gia_tri"] == nl_gt0)
    ok("Chủ sở hữu chưa xác nhận (không tự gán APH)", ad.lay("sx_ho_so_gia_cong", hs["id"])["chu_so_huu_id"] is None)
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["HG"]["id"], "dong": [{"mat_hang_id": M["DO"]["id"], "so_kg": 10, "don_gia": 1}]})
    s, r = kt.lam("phieu_kho:ghiSo", pk["id"])
    ok("Nhập thường vào kho hàng gửi: bị chặn", s == 400, r)
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mX["id"], "ho_so_gia_cong_id": hs["id"]})
    me7 = r["data"]["id"]
    s, r = nm.lam("me_sx:ghiThucTe", me7, {"request_id": rid(), "nvl": [{"mat_hang_id": M["DO"]["id"], "so_luong": 400}],
                                            "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 395}], "hao": [{"so_kg": 5}], "ket_thuc": True})
    ok("Mẻ gia công lấy và trả về kho hàng gửi: HG đỗ 600, X 395", s == 200 and ton("HG", "DO") == 600 and ton("HG", "X") == 395, r)
    b = kt.tao("don_ban", {"khach_id": ad.ds("khach_hang", {})[0]["id"], "don_vi_ban_id": dv["APH"]["id"],
                           "dong": [{"mat_hang_id": M["X"]["id"], "kho_id": K["HG"]["id"], "so_kg": 10, "don_gia": 1000}]})
    kt.lam("don_ban:chotDon", b["id"])
    s, r = kt.lam("luot_giao:taoLuot", None, {"don_ban_id": b["id"], "dong": [{"don_ban_dong_id": ad.lay("don_ban", b["id"], "dong")["dong"][0]["id"], "so_kg": 10}]})
    ok("Bán hàng từ kho hàng gửi: bị chặn", s == 400, r)
    ad.lam("don_ban:huy", b["id"], {"ly_do": "thử"})
    s, r = kt.lam("sx_ho_so_gia_cong:baoCao", hs["id"])
    hg = {x["ma"].split("-")[-1]: x for x in r["data"]["hang"]}
    ok("Báo cáo hồ sơ: nhận 1.000, đã dùng 400, ra 395, đang giữ 600 / 395", hg["DO"]["da_nhan"] == 1000 and hg["DO"]["da_dung"] == 400 and hg["X"]["da_ra"] == 395
       and hg["DO"]["dang_giu"] == 600, hg)
    s, r = kt.lam("sx_ho_so_gia_cong:xacNhanSoHuu", hs["id"], {"chu_so_huu_id": dv["VH"]["id"], "can_cu": "HĐ gia công 01/2026"})
    ok("Xác nhận chủ sở hữu chỉ qua thao tác có căn cứ", s == 200 and ad.lay("sx_ho_so_gia_cong", hs["id"])["chu_so_huu_id"] == dv["VH"]["id"])

    nhom("12. Quyền: nhà máy không thấy giá (API, quan hệ, xuất, giá tham chiếu, snapshot giá)")
    s, r = nm.call("gia_von:list")
    ok("gia_von:list → 403", s == 403)
    s, r = nm.call("me_sx:get", q=f"?filterByTk={me1}")
    ok("Mẻ không có giá thành / snapshot giá", s == 200 and "gia_thanh" not in r["data"] and "snapshot_gia" not in r["data"], list(r.get("data", {}))[:50])
    s, r = nm.call("mau_sx_dong:list", q="?pageSize=200")
    ok("Định mức không lộ giá tham chiếu phụ phẩm", s == 200 and "gia_tham_chieu" not in json.dumps(r) and "nguon_gia_tc" not in json.dumps(r))
    s, r = nm.call("me_sx:get", q=f"?filterByTk={me1}&appends=phieu.dong")
    ok("Nhúng phiếu → dòng không lộ đơn giá", s == 200 and '"don_gia"' not in json.dumps(r))
    s, r = nm.call("me_sx:export", {})
    ok("Xuất dữ liệu: bị chặn", s in (400, 403))
    s, r = nm.lam("me_sx:chot", me2)
    ok("Nhà máy không chốt giá thành", s in (400, 403))

    nhom("13. Mẻ A bán hết, mẻ B nhập mới rồi chốt lại A: không đội giá trị tồn mẻ B")
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mX["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    mA = r["data"]["id"]
    x0 = ton("TP", "X")
    nm.lam("me_sx:ghiThucTe", mA, {"request_id": rid(), "nvl": [{"mat_hang_id": M["DO"]["id"], "so_luong": 100}], "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 100}], "ket_thuc": True})
    kt.lam("me_sx:chot", me2)
    kt.lam("me_sx:chot", mA)
    tonx = ton("TP", "X")
    b = kt.tao("don_ban", {"khach_id": ad.ds("khach_hang", {})[0]["id"], "don_vi_ban_id": dv["APH"]["id"],
                           "dong": [{"mat_hang_id": M["X"]["id"], "kho_id": K["TP"]["id"], "so_kg": tonx, "don_gia": 30000}]})
    kt.lam("don_ban:chotDon", b["id"])
    l_ = kt.lam("luot_giao:taoLuot", None, {"don_ban_id": b["id"], "dong": [{"don_ban_dong_id": ad.lay("don_ban", b["id"], "dong")["dong"][0]["id"], "so_kg": tonx}]})[1]["data"]
    kt.lam("luot_giao:khachNhan", l_["id"])
    ok("Bán hết thành phẩm X ở kho TP", ton("TP", "X") == 0)
    s, r = nm.lam("me_sx:moTuMau", None, {"mau_sx_id": mX["id"], "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"]})
    mB = r["data"]["id"]
    nm.lam("me_sx:ghiThucTe", mB, {"request_id": rid(), "nvl": [{"mat_hang_id": M["DO"]["id"], "so_luong": 100}], "tp": [{"mat_hang_id": M["X"]["id"], "so_luong": 100}], "ket_thuc": True})
    kt.lam("me_sx:chot", mB)
    gB = gv("TP", "X")["gia_tri"]
    kt.tao("me_sx_chi_phi", {"me_sx_id": mA, "loai": "dien", "so_tien": 300000, "so_chung_tu": f"DIEN-{k}"})
    s, r = kt.lam("me_sx:chot", mA)
    ok("Chốt lại A +300.000: toàn bộ vào giá vốn, giá trị tồn mẻ B giữ nguyên", s == 200 and r["data"]["vao_gia_von"] == 300000 and gv("TP", "X")["gia_tri"] == gB,
       [r.get("data", {}).get("vao_gia_von"), gB, gv("TP", "X")["gia_tri"]])

    nhom("14. Hủy / điều chỉnh mẻ đã ghi: chứng từ đảo, giữ lịch sử")
    pks = ad.ds("phieu_kho", {"me_sx_id": mB, "loai": "thu_hoi"})
    tp1 = ton("TP", "X")
    s, r = nm.lam("phieu_kho:huy", pks[0]["id"], {"ly_do": "Ghi nhầm"})
    ok("Nhà máy không tự hủy phiếu đã ghi của mẻ", s in (400, 403))
    s, r = kt.lam("phieu_kho:huy", pks[0]["id"], {"ly_do": "Ghi nhầm sản lượng, ghi lại"})
    so = ad.lay("phieu_kho", pks[0]["id"])["so"]
    ok("Kế toán hủy phiếu thu hồi: tồn X −100, dòng sổ gốc + dòng đảo đều còn", s == 200 and ton("TP", "X") == tp1 - 100
       and len(ad.ds("so_kho", {"chung_tu": so})) == 2 and ad.lay("me_sx", mB)["trang_thai"] in ("can_chot_lai", "mo"), r)

    nhom("15. Đề xuất mã hàng mới từ nhà máy")
    dx = nm.tao("de_xuat_mat_hang", {"ten": "Đỗ 3 sao tranh ảnh", "dvt": "kg", "quy_cach": "25 kg/bao", "gap_o_phieu": "SB-1510"})
    ok("Nhà máy tạo đề xuất (chờ duyệt)", dx["trang_thai"] == "cho_duyet")
    s, r = nm.lam("de_xuat_mat_hang:duyet", dx["id"], {"ma": f"{k}-DO3S"})
    ok("Nhà máy không tự duyệt mã", s in (400, 403))
    s, r = kt.lam("de_xuat_mat_hang:duyet", dx["id"], {"ma": f"{k}-DO3S", "kg_bao": 25})
    ok("Kế toán duyệt: tạo mã chính thức", s == 200 and ad.ds("mat_hang", {"ma": f"{k}-DO3S"}))

    nhom("16. Nhập lại phiếu nhà máy từ file cũ: không tạo trùng")
    ph = {"so_phieu": f"SX-{k}", "ngay": "2026-10-20", "xuong": "Đậu", "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"], "nguon": "nguon:nha_may",
          "nvl": [{"mat_hang_id": M["DO"]["id"], "so_kg": 100}], "tp": [{"mat_hang_id": M["X"]["id"], "so_kg": 100}]}
    d0 = ton("NL", "DO")
    s, r = nm.lam("me_sx:nhapNhanh", None, ph)
    s, r2 = nm.lam("me_sx:nhapNhanh", None, ph)
    ok("Cùng phiếu nhập hai lần: một mẻ, kho trừ một lần", r2["data"].get("da_tao_truoc") and ton("NL", "DO") == d0 - 100)

    nhom("Báo cáo hiệu suất & đối chiếu")
    s, r = kt.lam("me_sx:hieuSuat", None, {"tu": "2026-01-01"})
    ok("Báo cáo hiệu suất có mẻ 0.4.1", s == 200 and any(x["id"] == me1 for x in r["data"]))
    ok("Đối chiếu bảo toàn toàn hệ thống: CÂN", ad.lam("gia_von:doiChieu")[1]["data"]["can"])
    loi = [t for t, d in KQ if not d]
    print(f"\nTỔNG {len(KQ)} ca, LỖI {len(loi)}")
    for t in loi:
        print("  LỖI:", t)
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
