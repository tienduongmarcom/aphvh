#!/usr/bin/env python3
"""Bộ kiểm NocoBase 0.4.0 — Unified Operations (dữ liệu giả, tiền tố T4-). Bổ sung, KHÔNG thay bộ kiểm 0.3.2.

Bao phủ 17 nhóm điều kiện đóng phiên bản (mục 13 đặc tả) + truy vết xuyên suốt 1 kg nguyên liệu → mẻ → chuyển Hà Nội → đơn gộp → tiền vào tài khoản APH.
Mỗi nhóm kiểm số dư TRƯỚC / SAU (tồn, giá trị, quỹ, công nợ), không chỉ mã trả về.

    python3 kiem_040.py --email <quản trị> --password <mật khẩu>
"""
import argparse
import base64
import json
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
    k = "T4-" + uuid.uuid4().hex[:5]
    nhom = lambda t: print(f"\n==== {t}")

    nhom("Nâng cấp dữ liệu 0.4.0 (chạy lại an toàn)")
    s, r = ad.lam("cau_hinh:nangCap")
    ok("Nâng cấp chạy được", s == 200 and r["data"]["phien_ban"] == "0.4.0", r)
    s, r2 = ad.lam("cau_hinh:nangCap")
    ok("Chạy lại nâng cấp: không ghi thêm phiên bản, không cấp thêm phạm vi", s == 200 and r2["data"]["da_nang_truoc"] and not r2["data"]["cap_pham_vi"], r2)
    for kh_, gt in (("giu_khi_duyet", "co"), ("vuot_han_muc_khach_thuong", "canh_bao"), ("pham_vi_mac_dinh", "tu_choi"), ("ck_can_xac_minh", "khong"),
                    ("dung_sai_can_pct", "2"), ("nguong_lech_sx_pct", "0.5")):
        ad.lam("cau_hinh:dat", None, {"khoa": kh_, "gia_tri": gt})

    # ---------- Người dùng ----------
    pw = "Thu" + uuid.uuid4().hex[:10]
    VT = {"ban_hang": ["ban_hang"], "ban_hang2": ["ban_hang"], "kho_hn": ["kho"], "kho_trong": ["kho"], "nha_may": ["nha_may", "khong_xem_gia"],
          "thu_chi": ["thu_chi"], "ke_toan": ["ke_toan"], "pos": ["pos"]}
    uid = {}
    for ten, roles in VT.items():
        em = f"t040-{ten}@aphvh.local"
        u = ad.ds("users", {"email": em})
        if u:
            ad.call("users:update", {"password": pw, "roles": roles}, q=f"?filterByTk={u[0]['id']}")
            uid[ten] = u[0]["id"]
        else:
            uid[ten] = ad.tao("users", {"email": em, "nickname": "T040 " + ten, "password": pw, "roles": roles})["id"]
    for x in ad.ds("pham_vi", {"nguoi_dung_id": {"$in": list(uid.values())}}):
        ad.call("pham_vi:destroy", {}, q=f"?filterByTk={x['id']}")
    time.sleep(2)
    U = {t: API(o.url, f"t040-{t}@aphvh.local", pw, VT[t][0]) for t in VT}

    dv = {x["ma"]: x for x in ad.ds("don_vi", {})}
    APH, VH, TL, MK = dv["APH"], dv["VH"], dv["TL"], dv["MK"]
    q = lambda m, t_, d, l: ad.tao("quy", {"ma": f"{k}-{m}", "ten": t_, "don_vi_id": d["id"], "loai": l})
    Q = {"APH_TM": q("APH-TM", "TM APH T4", APH, "tien_mat"), "APH_NH": q("APH-NH", "MB APH T4", APH, "ngan_hang"),
         "TL_TM": q("TL-TM", "TM TL T4", TL, "tien_mat"), "VH_TM": q("VH-TM", "TM VH T4", VH, "tien_mat"), "POS": q("POS", "Quầy HN T4", APH, "tien_mat")}
    K = {"NL": ad.tao("kho", {"ma": f"{k}-NL", "ten": f"NL nhà máy {k}", "loai_kho": "nha_may"}),
         "TP": ad.tao("kho", {"ma": f"{k}-TP", "ten": f"TP nhà máy {k}", "loai_kho": "nha_may"}),
         "TG": ad.tao("kho", {"ma": f"{k}-TG", "ten": f"Đang vận chuyển {k}", "trung_chuyen": True, "loai_kho": "cho_xu_ly"}),
         "HN": ad.tao("kho", {"ma": f"{k}-HN", "ten": f"Kho HN {k}"}), "HN2": ad.tao("kho", {"ma": f"{k}-HN2", "ten": f"Kho HN2 {k}"})}
    M = {"NL": ad.tao("mat_hang", {"ma": f"{k}-NL", "ten": "Đỗ hạt NL T4", "loai_hang": "nguyen_lieu"}),
         "TP": ad.tao("mat_hang", {"ma": f"{k}-TP", "ten": "Đỗ tách vỏ T4", "kg_bao": 25, "gia_ban": 50000, "gia_san": 45000, "tinh_tien_theo": "quy_cach",
                                   "dung_sai_pct": 2, "thue_suat": 5}),
         "TP2": ad.tao("mat_hang", {"ma": f"{k}-TP2", "ten": "Đỗ mảnh T4", "gia_ban": 40000}),
         "HH": ad.tao("mat_hang", {"ma": f"{k}-HH", "ten": "Lạc nhân T4", "gia_ban": 60000, "tinh_tien_theo": "thuc_can"}),
         "PP": ad.tao("mat_hang", {"ma": f"{k}-PP", "ten": "Vỏ đỗ T4", "loai_hang": "phu_pham"}),
         "BAO": ad.tao("mat_hang", {"ma": f"{k}-BAO", "ten": "Bao 25kg T4", "dvt_ton": "cai", "loai_hang": "bao_bi"}),
         "TP3": ad.tao("mat_hang", {"ma": f"{k}-TP3", "ten": "Đỗ phiếu bổ sung T4"}),
         "Z": ad.tao("mat_hang", {"ma": f"{k}-Z", "ten": "Hàng kiểm kê giá 0 T4"}),
         "GOI": ad.tao("mat_hang", {"ma": f"{k}-GOI", "ten": "Bột năng gói T4", "dvt_ton": "goi", "gia_ban": 12000, "ma_vach": f"89{uuid.uuid4().int % 10**10:010d}"})}
    ad.tao("quy_doi_dvt", {"mat_hang_id": M["GOI"]["id"], "dvt": "thung", "he_so": 20})
    if not ad.ds("khach_hang", {"ma": "KHACH-LE"}):
        ad.tao("khach_hang", {"ma": "KHACH-LE", "ten": "Khách lẻ"})
    KH = {"thuong": ad.tao("khach_hang", {"ma": f"{k}-KH", "ten": "Khách sỉ T4", "han_muc": 100000000, "nhom_gia": "si", "so_ngay_no": 30}),
          "nho": ad.tao("khach_hang", {"ma": f"{k}-KHN", "ten": "Khách hạn mức nhỏ T4", "han_muc": 1000000}),
          "rui_ro": ad.tao("khach_hang", {"ma": f"{k}-KHR", "ten": "Khách rủi ro T4", "han_muc": 5000000, "rui_ro": True}),
          "le": ad.ds("khach_hang", {"ma": "KHACH-LE"})[0]}
    pv = lambda u, **x: ad.tao("pham_vi", {"nguoi_dung_id": uid[u], **x})
    for kk in ("NL", "TP", "TG"): pv("nha_may", kho_id=K[kk]["id"])
    for kk in ("HN", "HN2", "TG"): pv("kho_hn", kho_id=K[kk]["id"])
    for u in ("ban_hang", "ban_hang2"): pv(u, tat_ca_kho=True)
    pv("thu_chi", tat_ca_quy=True); pv("thu_chi", tat_ca_kho=True)
    pv("pos", kho_id=K["HN"]["id"]); pv("pos", quy_id=Q["POS"]["id"]); pv("pos", quy_id=Q["APH_NH"]["id"])
    time.sleep(1)

    def ton(kk, mm):
        r = ad.ds("ton_kho", {"kho_id": K[kk]["id"], "mat_hang_id": M[mm]["id"]})
        return r[0] if r else {"so_kg": 0, "so_giu": 0, "so_cho_gia": 0}

    def gv(kk, mm):
        r = ad.ds("gia_von", {"kho_id": K[kk]["id"], "mat_hang_id": M[mm]["id"]})
        return r[0] if r else {"so_kg": 0, "gia_tri": 0, "gia_bq": 0}

    def du(qq):
        return sum(x["so_tien"] for x in ad.ds("so_quy", {"quy_id": Q[qq]["id"]}))

    atp = lambda kk, mm: (lambda x: round(x["so_kg"] - x["so_giu"] - x["so_cho_gia"], 3))(ton(kk, mm))
    kt = U["ke_toan"]
    doi_chieu = lambda: ad.lam("gia_von:doiChieu")[1]["data"]["can"]

    # ======================= 1. NHÀ MÁY =======================
    nhom("1. Nhà máy: nhập NVL, nhập nhanh phiếu SX, rà soát, không chốt giá 0")
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["NL"]["id"], "dong": [{"mat_hang_id": M["NL"]["id"], "so_kg": 10000, "don_gia": 20000}]})
    kt.lam("phieu_kho:ghiSo", pk["id"])
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["NL"]["id"], "dong": [{"mat_hang_id": M["BAO"]["id"], "so_kg": 500, "don_gia": 3000}]})
    kt.lam("phieu_kho:ghiSo", pk["id"])
    ok("NVL 10.000 kg × 20.000 vào kho NL", ton("NL", "NL")["so_kg"] == 10000 and gv("NL", "NL")["gia_tri"] == 200000000)
    nm = U["nha_may"]
    sp = f"SX-{k}"
    phieu = {"so_phieu": sp, "ngay": "2026-10-20", "xuong": "Đậu bóc vỏ", "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"],
             "nvl": [{"mat_hang_id": M["NL"]["id"], "so_kg": 1000}, {"mat_hang_id": M["BAO"]["id"], "so_kg": 32}],
             "tp": [{"mat_hang_id": M["TP"]["id"], "so_kg": 800, "so_bao": 32}],
             "phu_pham": [{"mat_hang_id": M["PP"]["id"], "so_kg": 150, "don_gia": 0}], "hao": [{"mat_hang_id": M["NL"]["id"], "so_kg": 50, "loai_hao": "tu_nhien"}]}
    thieu = {**phieu, "so_phieu": sp + "-THIEU", "nvl": [{"ten_nguon": "ĐỖ 3 SAO TRANH ẢNH", "so_kg": 1000}], "tp": [{"mat_hang_id": M["TP3"]["id"], "so_kg": 800}]}
    s, r = nm.lam("me_sx:nhapNhanh", None, thieu)
    ok("Phiếu SX thiếu mã NVL → vào hàng đợi rà soát, KHÔNG ghi sổ, không tự sinh đầu vào",
       s == 200 and r["data"].get("ra_soat") and ton("NL", "NL")["so_kg"] == 10000 and ton("TP", "TP")["so_kg"] == 0, r)
    rs_id = r["data"]["id"]
    lech = {**phieu, "so_phieu": sp + "-LECH", "tp": [{"mat_hang_id": M["TP"]["id"], "so_kg": 700}]}
    s, r = nm.lam("me_sx:nhapNhanh", None, lech)
    ok("Phiếu SX lệch cân bằng 100 kg (10% > 0,5%) → rà soát", s == 200 and r["data"].get("ra_soat") and any("Lệch" in x for x in r["data"]["van_de"]), r)
    s, r = nm.lam("me_sx:nhapNhanh", None, phieu)
    ok("Phiếu SX đủ: tạo mẻ + cấp NVL + thu hồi trong một giao dịch", s == 200 and r["data"].get("ok"), r)
    me1 = r["data"]["me_sx_id"]
    s, r2 = nm.lam("me_sx:nhapNhanh", None, phieu)
    ok("Gửi lại cùng phiếu SX (mạng chập chờn): không tạo mẻ thứ hai", r2["data"].get("da_tao_truoc") and r2["data"]["me_sx_id"] == me1)
    ok("Sau mẻ: NVL 9.000 (1.000 cấp; hao 50 nằm trong 1.000), bao bì 468 Cái, TP 800 kg, PP 150 kg",
       ton("NL", "NL")["so_kg"] == 9000 and ton("NL", "BAO")["so_kg"] == 468 and ton("TP", "TP")["so_kg"] == 800 and ton("TP", "PP")["so_kg"] == 150,
       [ton("NL", "NL")["so_kg"], ton("NL", "BAO")["so_kg"], ton("TP", "TP")["so_kg"]])
    s, r = nm.lam("sx_ra_soat:boSung", rs_id, {"nvl": [{"mat_hang_id": M["NL"]["id"], "so_kg": 1000}], "so_phieu": sp + "-THIEU"})
    ok("Bổ sung mã cho phiếu rà soát rồi tạo lại → thành mẻ", s == 200 and r["data"].get("ok"), r)
    me_bs = r["data"].get("me_sx_id")
    # Kho có hàng giá 0 (kiểm kê thừa, chưa có giá) → mẻ dùng NVL giá 0 không được chốt giá thành 0
    kk0 = kt.tao("phieu_kho", {"loai": "kiem_ke", "kho_id": K["NL"]["id"], "ghi_chu": "Kiểm kê thừa", "dong": [{"mat_hang_id": M["Z"]["id"], "so_kg": 100}]})
    kt.lam("phieu_kho:ghiSo", kk0["id"])
    s, r = nm.lam("me_sx:nhapNhanh", None, {"so_phieu": sp + "-0", "ngay": "2026-10-20", "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"],
                                            "nvl": [{"mat_hang_id": M["Z"]["id"], "so_kg": 100}], "tp": [{"mat_hang_id": M["Z"]["id"], "so_kg": 100}]})
    me0 = r["data"]["me_sx_id"]
    s, r = kt.lam("me_sx:chot", me0)
    ok("Mẻ có tổng chi phí 0 (NVL giá 0): KHÔNG chốt giá thành bằng 0", s == 400, r)
    s, r = kt.lam("me_sx:chot", me1)
    ok("Chốt mẻ 1: giá thành = (1.000×20.000 + 32×3.000) / 800 = 25.120", s == 200 and r["data"]["gia_thanh"] == 25120, r)
    ok("Giá trị TP nhà máy = 800 × 25.120", gv("TP", "TP")["gia_tri"] == 20096000, gv("TP", "TP"))
    s, r = kt.lam("me_sx:hieuSuat", None, {"tu": "2026-10-01"})
    hs = [x for x in r["data"] if x["id"] == me1]
    ok("Báo cáo hiệu suất: tỷ lệ thu hồi 80%, phụ phẩm 15%, hao 5%, lệch cân bằng 0",
       hs and hs[0]["ty_le_thu_hoi"] == 80 and hs[0]["ty_le_phu_pham"] == 15 and hs[0]["ty_le_hao"] == 5 and hs[0]["lech_can_bang"] == 0, hs)

    nhom("Quyền NoCost (nhà máy) — API, quan hệ, xuất, in")
    s, r = nm.call("gia_von:list")
    ok("NoCost: gia_von:list → 403", s == 403)
    s, r = nm.call("me_sx:get", q=f"?filterByTk={me1}")
    ok("NoCost: mẻ không có giá thành / giá trị NVL", s == 200 and "gia_thanh" not in r["data"] and "gia_tri_nvl" not in r["data"], list(r.get("data", {}).keys())[:40])
    s, r = nm.call("me_sx:get", q=f"?filterByTk={me1}&appends=phieu.dong")
    vet = json.dumps(r.get("data"))
    ok("NoCost: nhúng phiếu → dòng phiếu không lộ đơn giá / giá trị", s == 200 and '"don_gia"' not in vet and '"gia_tri"' not in vet, vet[:300])
    s, r = nm.call("so_kho:list", q="?appends=gia_von")
    ok("NoCost: yêu cầu nhúng quan hệ giá vốn → bị chặn hoặc bị lược, không lộ giá", s in (400, 403) or ("gia_von" not in json.dumps(r) and "gia_bq" not in json.dumps(r)),
       (s, str(r)[:200]))
    s, r = nm.call("ton_kho:export", {})
    ok("NoCost: xuất dữ liệu → bị chặn", s in (400, 403))
    s, r = nm.call("luot_giao:truyVet", {}, q="?filterByTk=1")
    ok("NoCost: truy vết (có giá vốn) → không có quyền", s in (400, 403))

    # ======================= 2. CHUYỂN KHO HAI ĐẦU =======================
    nhom("2. Chuyển hàng Phú Thọ → Hà Nội: hai đầu, thử lại không nhân đôi, chênh lệch chờ xử lý")
    ch = nm.tao("chuyen_hang", {"kho_di_id": K["TP"]["id"], "kho_den_id": K["HN"]["id"], "kho_tg_id": K["TG"]["id"], "xe": "29C-T4", "request_id": f"{k}-CH1",
                                "dong": [{"mat_hang_id": M["TP"]["id"], "so_kg": 600, "so_bao": 24}]})
    s, r = nm.call("chuyen_hang:create", {"kho_di_id": K["TP"]["id"], "kho_den_id": K["HN"]["id"], "request_id": f"{k}-CH1"})
    ok("Tạo trùng chuyến cùng mã yêu cầu: bị chặn", s == 400)
    nm.lam("chuyen_hang:xacNhanXuat", ch["id"])
    s, r = nm.lam("chuyen_hang:xacNhanXuat", ch["id"])
    ok("Xác nhận xuất lần 2 (thử lại API): không trừ lần hai", r["data"].get("da_xuat_truoc") and ton("TP", "TP")["so_kg"] == 200 and ton("TG", "TP")["so_kg"] == 600)
    ok("Giá trị theo hàng đi đường = 600 × 25.120", gv("TG", "TP")["gia_tri"] == 15072000, gv("TG", "TP"))
    s, r = nm.lam("chuyen_hang:xacNhanNhan", ch["id"], {"nhan": {}})
    ok("Nhà máy không xác nhận nhận ở kho Hà Nội (ngoài phạm vi)", s == 400)
    kh_ = U["kho_hn"]
    dong_ch = ad.lay("chuyen_hang", ch["id"], "dong")["dong"][0]["id"]
    s, r = kh_.lam("chuyen_hang:xacNhanNhan", ch["id"], {"nhan": {str(dong_ch): {"so_kg": 598, "so_bao": 24}}})
    ok("Nhận thiếu 2 kg không ghi lý do: bị chặn", s == 400)
    res = []
    th = [threading.Thread(target=lambda: res.append(kh_.lam("chuyen_hang:xacNhanNhan", ch["id"], {"nhan": {str(dong_ch): {"so_kg": 598, "so_bao": 24}}, "ly_do": "Cân HN thiếu 2kg"})))
          for _ in range(3)]
    [x.start() for x in th]; [x.join() for x in th]
    ok("Ba lần xác nhận nhận đồng thời: HN chỉ +598, kho đi đường còn 2", ton("HN", "TP")["so_kg"] == 598 and ton("TG", "TP")["so_kg"] == 2, [ton("HN", "TP"), ton("TG", "TP")])
    cl = ad.ds("chenh_lech_giao_nhan", {"chuyen_hang_id": ch["id"]})
    ok("Chênh lệch −2 kg CHỜ XỬ LÝ (không tự hao hụt)", len(cl) == 1 and cl[0]["so_kg"] == -2 and cl[0]["trang_thai"] == "cho_xu_ly", cl)
    s, r = kh_.lam("chenh_lech_giao_nhan:xuLy", cl[0]["id"], {"cach_xu_ly": "hao_hut", "ly_do": "BB-01"})
    ok("Thủ kho không tự duyệt hao hụt", s in (400, 403))
    s, r = kt.lam("chenh_lech_giao_nhan:xuLy", cl[0]["id"], {"cach_xu_ly": "hao_hut", "ly_do": "Biên bản BB-01"})
    ok("Kế toán duyệt hao hụt: kho đi đường về 0, chuyến 'Đã nhận'", s == 200 and ton("TG", "TP")["so_kg"] == 0 and ad.lay("chuyen_hang", ch["id"])["trang_thai"] == "da_nhan")
    ok("Đối chiếu bảo toàn sau chuyển hàng: CÂN", doi_chieu())
    ch_h = nm.tao("chuyen_hang", {"kho_di_id": K["TP"]["id"], "kho_den_id": K["HN"]["id"], "kho_tg_id": K["TG"]["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "so_kg": 10}]})
    nm.lam("chuyen_hang:xacNhanXuat", ch_h["id"])
    s, r = nm.lam("chuyen_hang:huy", ch_h["id"], {"ly_do": "xuất nhầm"})
    ok("Nhà máy không tự hủy chuyến đã xuất", s in (400, 403))
    s, r = kt.lam("chuyen_hang:huy", ch_h["id"], {"ly_do": "Xuất nhầm, xe chưa chạy"})
    ok("Kế toán hủy chuyến đã xuất: đảo sổ, TP NM về 200, đi đường 0", s == 200 and ton("TP", "TP")["so_kg"] == 200 and ton("TG", "TP")["so_kg"] == 0, [ton("TP", "TP"), ton("TG", "TP")])

    # ======================= 3. BẢNG GIÁ, VAT, UOM =======================
    nhom("3. Bảng giá / giá sàn / VAT theo dòng / quy đổi ĐVT")
    ad.tao("bang_gia", {"ma": f"{k}-SI", "ten": "Giá sỉ T4", "nhom_gia": "si", "kenh": "si", "tu_ngay": "2026-01-01", "uu_tien": 1,
                        "dong": [{"mat_hang_id": M["TP"]["id"], "don_gia": 48000, "gia_san": 46000}]})
    ad.tao("bang_gia", {"ma": f"{k}-SI-CU", "ten": "Giá sỉ hết hạn", "nhom_gia": "si", "kenh": "si", "tu_ngay": "2025-01-01", "den_ngay": "2025-12-31", "uu_tien": 9,
                        "dong": [{"mat_hang_id": M["TP"]["id"], "don_gia": 99000, "gia_san": 90000}]})
    ad.tao("bang_gia", {"ma": f"{k}-SL", "ten": "Giá sỉ ≥ 500", "nhom_gia": "si", "kenh": "si", "uu_tien": 1,
                        "dong": [{"mat_hang_id": M["TP"]["id"], "sl_toi_thieu": 500, "don_gia": 47000, "gia_san": 46000}]})
    ad.tao("bang_gia", {"ma": f"{k}-LE", "ten": "Giá lẻ POS", "kenh": "pos", "gia_gom_vat": True,
                        "dong": [{"mat_hang_id": M["GOI"]["id"], "don_gia": 15000, "gia_san": 13000}, {"mat_hang_id": M["TP"]["id"], "don_gia": 55000, "gia_san": 50000}]})
    bh = U["ban_hang"]
    d1 = bh.tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "xuat_hoa_don": True,
                            "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"], "so_kg": 100}]})
    dd = ad.lay("don_ban", d1["id"], "dong")["dong"][0]
    ok("Khách nhóm sỉ: giá bảng giá còn hiệu lực 48.000 (không lấy bảng hết hạn 99.000)", dd["don_gia"] == 48000 and "SI" in (dd["nguon_gia"] or ""), dd.get("nguon_gia"))
    ok("VAT 5% trên giá chưa VAT: trước thuế 4.800.000, thuế 240.000, phải thu 5.040.000",
       dd["tien_truoc_thue"] == 4800000 and dd["tien_thue"] == 240000 and dd["thanh_tien"] == 5040000, [dd["tien_truoc_thue"], dd["tien_thue"], dd["thanh_tien"]])
    d2 = bh.tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"], "so_kg": 500}]})
    ok("Bậc số lượng ≥ 500: 47.000", ad.lay("don_ban", d2["id"], "dong")["dong"][0]["don_gia"] == 47000)
    bh.call("don_ban:destroy", {}, q=f"?filterByTk={d2['id']}")
    d3 = bh.tao("don_ban", {"khach_id": KH["nho"]["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"], "so_kg": 10}]})
    ok("Khách không thuộc nhóm sỉ: giá danh mục 50.000", ad.lay("don_ban", d3["id"], "dong")["dong"][0]["don_gia"] == 50000)
    bh.call("don_ban:destroy", {}, q=f"?filterByTk={d3['id']}")
    d4 = bh.tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"], "so_kg": 10, "don_gia": 47500}]})
    s, r = bh.lam("don_ban:chotDon", d4["id"])
    ok("Bán dưới giá niêm yết không ghi lý do: bị chặn", s == 400, r)
    d4b = bh.tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"], "so_kg": 10, "don_gia": 44000,
                                                                                                 "ly_do_sua_gia": "Khách lấy đều"}]})
    s, r = bh.lam("don_ban:chotDon", d4b["id"])
    ok("Dưới giá sàn bảng giá (46.000): chờ duyệt", ad.lay("don_ban", d4b["id"])["trang_thai"] == "cho_duyet", r)
    for d_ in (d4, d4b):
        ad.lam("don_ban:huy", d_["id"], {"ly_do": "thử"})
    dg_u = bh.tao("don_gop", {"khach_id": KH["thuong"]["id"], "dong": [{"mat_hang_id": M["GOI"]["id"], "don_vi_ban_id": MK["id"], "kho_id": K["HN"]["id"],
                                                                       "dvt_nhap": "thung", "sl_nhap": 2}]})
    ok("UOM: 2 thùng × 20 gói = 40 gói (không cộng nhầm sang kg)", ad.lay("don_gop", dg_u["id"], "dong")["dong"][0]["so_kg"] == 40)
    bh.call("don_gop:destroy", {}, q=f"?filterByTk={dg_u['id']}")

    # ======================= 4. ĐƠN GỘP =======================
    nhom("4. Đơn gộp APH + VH + TL, cùng mặt hàng / cùng kho, không trừ tồn đôi")
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["HN"]["id"], "dong": [{"mat_hang_id": M["HH"]["id"], "so_kg": 1000, "don_gia": 50000}]})
    kt.lam("phieu_kho:ghiSo", pk["id"])
    tr_hn = ton("HN", "TP")["so_kg"]
    dg = bh.tao("don_gop", {"khach_id": KH["thuong"]["id"], "request_id": f"{k}-DG1", "cach_giao": "van_chuyen", "dong": [
        {"mat_hang_id": M["TP"]["id"], "don_vi_ban_id": APH["id"], "kho_id": K["HN"]["id"], "so_kg": 200, "so_bao": 8, "vat_ap_dung": True},
        {"mat_hang_id": M["TP"]["id"], "don_vi_ban_id": VH["id"], "kho_id": K["HN"]["id"], "so_kg": 100, "so_bao": 4, "vat_ap_dung": True},
        {"mat_hang_id": M["HH"]["id"], "don_vi_ban_id": TL["id"], "kho_id": K["HN"]["id"], "so_kg": 500}]})
    s, r = bh.lam("don_gop:chot", dg["id"])
    ok("Chốt đơn gộp → 3 đơn con theo bên bán", s == 200 and len(r["data"]["don_con"]) == 3, r)
    s, r2 = bh.lam("don_gop:chot", dg["id"])
    con = ad.ds("don_ban", {"don_gop_id": dg["id"]})
    ok("Chốt lại (thử lại): không tạo thêm đơn con", r2["data"].get("da_chot_truoc") and len(con) == 3)
    ben = sorted(ad.lay("don_vi", c["don_vi_ban_id"])["ma"] for c in con)
    ok("Đơn con đúng bên bán APH / TL / VH", ben == ["APH", "TL", "VH"], ben)
    ok("Giữ tồn ngay khi duyệt: TP HN giữ 300 (một số dư, không cộng đôi), HH giữ 500",
       ton("HN", "TP")["so_giu"] == 300 and ton("HN", "HH")["so_giu"] == 500 and ton("HN", "TP")["so_kg"] == tr_hn, [ton("HN", "TP"), ton("HN", "HH")])
    g_ = ad.lay("don_gop", dg["id"])
    ok("Trạng thái đơn gộp: duyệt / giao / thanh toán / hóa đơn tách riêng", g_["tt_duyet"] == "da_duyet" and g_["tt_giao"] == "da_giu" and g_["tt_thanh_toan"] == "chua_thu", g_)
    ok("Tổng đơn gộp = Σ đơn con", g_["tong_tien"] == sum(c["tong_tien"] for c in con))

    nhom("Giữ hàng đồng thời: hai người duyệt cùng lúc không giữ vượt ATP")
    con_atp = atp("HN", "TP")
    don_a = U["ban_hang"].tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"],
                                                                                                              "so_kg": con_atp - 50}]})
    don_b = U["ban_hang2"].tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": VH["id"], "dong": [{"mat_hang_id": M["TP"]["id"], "kho_id": K["HN"]["id"],
                                                                                                              "so_kg": con_atp - 50}]})
    th = [threading.Thread(target=lambda u, d: u.lam("don_ban:chotDon", d["id"]), args=(U["ban_hang"], don_a)),
          threading.Thread(target=lambda u, d: u.lam("don_ban:chotDon", d["id"]), args=(U["ban_hang2"], don_b))]
    [x.start() for x in th]; [x.join() for x in th]
    t_ = ton("HN", "TP")
    ga = ad.lay("don_ban", don_a["id"], "dong")["dong"][0]["giu_don"]; gb = ad.lay("don_ban", don_b["id"], "dong")["dong"][0]["giu_don"]
    ok(f"ATP {con_atp}, hai đơn mỗi đơn {con_atp - 50}: tổng giữ mới = {con_atp} (một đơn giữ thiếu), không âm",
       round(ga + gb, 3) == con_atp and t_["so_giu"] <= t_["so_kg"] and atp("HN", "TP") == 0, [ga, gb, t_])
    for d_ in (don_a, don_b):
        ad.lam("don_ban:huy", d_["id"], {"ly_do": "thử giữ"})
    ok("Hủy hai đơn: nhả đúng phần giữ", ton("HN", "TP")["so_giu"] == 300, ton("HN", "TP"))

    nhom("Giao gộp theo cân thực, quy cách bao nguyên")
    gdong = ad.lay("don_gop", dg["id"], "dong")["dong"]
    gid = {(x["don_vi_ban_id"], x["mat_hang_id"]): x["id"] for x in gdong}
    s, r = U["kho_hn"].lam("don_gop:taoGiao", dg["id"], {"request_id": f"{k}-GN1", "dong": [
        {"don_gop_dong_id": gid[(APH["id"], M["TP"]["id"])], "so_kg": 200, "so_bao": 8},
        {"don_gop_dong_id": gid[(VH["id"], M["TP"]["id"])], "so_kg": 100, "so_bao": 4},
        {"don_gop_dong_id": gid[(TL["id"], M["HH"]["id"])], "so_kg": 500}]})
    if s != 200:
        s, r = ad.lam("don_gop:taoGiao", dg["id"], {"request_id": f"{k}-GN1", "dong": [
            {"don_gop_dong_id": gid[(APH["id"], M["TP"]["id"])], "so_kg": 200, "so_bao": 8},
            {"don_gop_dong_id": gid[(VH["id"], M["TP"]["id"])], "so_kg": 100, "so_bao": 4},
            {"don_gop_dong_id": gid[(TL["id"], M["HH"]["id"])], "so_kg": 500}]})
    ok("Một chuyến giao gồm 3 lượt (3 đơn con)", s == 200 and len(r["data"]["luot"]) == 3, r)
    gg_id = r["data"]["id"]
    ok("Giữ chuyển từ đơn sang lượt không cộng trùng: TP giữ vẫn 300", ton("HN", "TP")["so_giu"] == 300, ton("HN", "TP"))
    ldong = {}
    for l_ in ad.ds("giao_gop_luot", {"giao_gop_id": gg_id}):
        for x in ad.lay("luot_giao", l_["luot_giao_id"], "dong")["dong"]:
            ldong[(ad.lay("luot_giao", l_["luot_giao_id"])["don_ban_id"], x["mat_hang_id"])] = x["id"]
    don_aph = [c for c in con if c["don_vi_ban_id"] == APH["id"]][0]
    don_vh = [c for c in con if c["don_vi_ban_id"] == VH["id"]][0]
    don_tl = [c for c in con if c["don_vi_ban_id"] == TL["id"]][0]
    thuc = {str(ldong[(don_aph["id"], M["TP"]["id"])]): {"so_kg": 194, "so_bao": 8}, str(ldong[(don_tl["id"], M["HH"]["id"])]): {"so_kg": 485}}
    s, r = ad.lam("giao_gop:xacNhan", gg_id, {"thuc": thuc})
    ok("Cân 194 kg / 8 bao (lệch 3% > dung sai 2%) không lý do: bị chặn", s == 400, r)
    thuc[str(ldong[(don_aph["id"], M["TP"]["id"])])]["ly_do"] = "Bao hụt ẩm"
    hn_tp0, hn_hh0 = ton("HN", "TP")["so_kg"], ton("HN", "HH")["so_kg"]
    s, r = ad.lam("giao_gop:xacNhan", gg_id, {"thuc": thuc})
    s2, r2 = ad.lam("giao_gop:xacNhan", gg_id, {"thuc": thuc})
    ok("Xác nhận chuyến gộp (2 lần): mỗi lượt xuất đúng 1 lần", s == 200 and r2["data"].get("da_xuat_truoc"))
    ok("Kho TP HN giảm theo cân thực 194 + 100 = 294 (một kho chung, hai bên bán, không trừ đôi)", round(hn_tp0 - ton("HN", "TP")["so_kg"], 3) == 294,
       [hn_tp0, ton("HN", "TP")["so_kg"]])
    l_aph = ad.ds("luot_giao_dong", {"id": ldong[(don_aph["id"], M["TP"]["id"])]})[0]
    ok("Quy cách bao nguyên: APH tính tiền 8 × 25 = 200 kg dù cân 194", l_aph["sl_tinh_tien"] == 200 and l_aph["so_kg_thuc"] == 194 and l_aph["chenh_can"] == -6, l_aph)
    da = ad.lay("don_ban", don_aph["id"], "dong")
    ok("Đơn APH: đã giao 200 (đủ), phải thu = 200 × 48.000 × 1,05", da["dong"][0]["da_giao"] == 200 and da["phai_thu"] == 10080000, [da["dong"][0]["da_giao"], da["phai_thu"]])
    dt = ad.lay("don_ban", don_tl["id"], "dong")
    nhom("Đặt 500 kg, xuất thực 485 kg (hàng tính theo cân thực)")
    ok("Kho HH giảm đúng 485", round(hn_hh0 - ton("HN", "HH")["so_kg"], 3) == 485)
    ok("Đơn TL: đã giao 485, chưa giao 15, phải thu 485 × 60.000", dt["dong"][0]["da_giao"] == 485 and dt["phai_thu"] == 29100000 and dt["trang_thai"] == "dang_giao",
       [dt["dong"][0]["da_giao"], dt["phai_thu"], dt["trang_thai"]])
    ok("Giao thiếu không chọn giữ lại: nhả giữ 15 kg (không treo giữ ảo)", ton("HN", "HH")["so_giu"] == 0 and dt["dong"][0]["giu_don"] == 0, ton("HN", "HH"))
    g_ = ad.lay("don_gop", dg["id"])
    ok("Đơn gộp: giao một phần (TL còn 15 kg)", g_["tt_giao"] == "mot_phan", g_["tt_giao"])
    ok("Đối chiếu bảo toàn sau giao: CÂN", doi_chieu())

    # ======================= 5. HÀNG ĐỢI HÓA ĐƠN MISA =======================
    nhom("5. Hàng đợi hóa đơn MISA theo bên bán")
    hq = ad.ds("hoa_don_cho_xuat", {"don_ban_id": {"$in": [c["id"] for c in con]}})
    ok("Đơn gộp → hàng đợi đúng bên bán có yêu cầu HĐ (APH, VH), không có TL", sorted(ad.lay("don_vi", x["don_vi_id"])["ma"] for x in hq) == ["APH", "VH"], hq)
    h_aph = [x for x in hq if x["don_vi_id"] == APH["id"]][0]
    h_vh = [x for x in hq if x["don_vi_id"] == VH["id"]][0]
    ok("Hàng đợi APH: tổng 10.080.000, thuế 480.000", h_aph["tong"] == 10080000 and h_aph["tien_thue"] == 480000, h_aph)
    s, r = bh.lam("hoa_don_cho_xuat:nhan", h_aph["id"])
    ok("Bán hàng không xử lý hàng đợi hóa đơn", s in (400, 403))
    kt.lam("hoa_don_cho_xuat:nhan", h_aph["id"])
    so_hd = str(uuid.uuid4().int % 10**7).zfill(7)
    s, r = kt.lam("hoa_don_cho_xuat:ghiSo", h_aph["id"], {"ky_hieu": "1C26TAA", "so_hd": so_hd})
    ok("Ghi ký hiệu + số HĐ đã xuất trên MISA", s == 200 and ad.lay("don_ban", don_aph["id"])["trang_thai_hd"] == "da_xuat")
    s, r = kt.lam("hoa_don_cho_xuat:ghiSo", h_aph["id"], {"ky_hieu": "1C26TAA", "so_hd": so_hd})
    ok("Ghi lại cùng dòng: không ghi đôi", r["data"].get("da_ghi_truoc"))
    s, r = kt.lam("hoa_don_cho_xuat:ghiSo", h_vh["id"], {"ky_hieu": "1C26TAA", "so_hd": so_hd})
    ok("Cùng ký hiệu + số cho bên bán KHÁC (VH) được (hai pháp nhân hai dãy số)", s == 200, r)
    h2 = kt.tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "xuat_hoa_don": True, "dong": [{"mat_hang_id": M["HH"]["id"], "kho_id": K["HN"]["id"],
                                                                                                                    "so_kg": 1, "don_gia": 60000}]})
    kt.lam("don_ban:chotDon", h2["id"])
    l2 = kt.lam("luot_giao:taoLuot", None, {"don_ban_id": h2["id"], "dong": [{"don_ban_dong_id": ad.lay("don_ban", h2["id"], "dong")["dong"][0]["id"], "so_kg": 1}]})[1]["data"]
    kt.lam("luot_giao:khachNhan", l2["id"])
    hq2 = ad.ds("hoa_don_cho_xuat", {"don_ban_id": h2["id"]})[0]
    s, r = kt.lam("hoa_don_cho_xuat:ghiSo", hq2["id"], {"ky_hieu": "1C26TAA", "so_hd": so_hd})
    ok("Cùng bên bán APH dùng lại số HĐ đã ghi: bị chặn (không xuất trùng)", s == 400, r)

    nhom("Hủy chuyến giao: giữ quay về cấp đơn; hủy đơn gộp: nhả giữ")
    giu0 = ton("HN", "HH")["so_giu"]
    dg3 = bh.tao("don_gop", {"khach_id": KH["thuong"]["id"], "dong": [{"mat_hang_id": M["HH"]["id"], "don_vi_ban_id": APH["id"], "kho_id": K["HN"]["id"], "so_kg": 10}]})
    bh.lam("don_gop:chot", dg3["id"])
    gd3 = ad.lay("don_gop", dg3["id"], "dong")["dong"][0]
    gg3 = ad.lam("don_gop:taoGiao", dg3["id"], {"dong": [{"don_gop_dong_id": gd3["id"], "so_kg": 10}]})[1]["data"]
    ok("Chốt + lập chuyến: giữ 10 (không cộng đôi)", ton("HN", "HH")["so_giu"] == giu0 + 10, ton("HN", "HH"))
    ad.lam("giao_gop:huy", gg3["id"], {"ly_do": "Xe hỏng"})
    dc3 = ad.ds("don_ban", {"don_gop_id": dg3["id"]})[0]
    ok("Hủy chuyến: giữ trở lại cấp đơn (giu_don 10), tồn giữ không đổi", ton("HN", "HH")["so_giu"] == giu0 + 10 and ad.lay("don_ban", dc3["id"], "dong")["dong"][0]["giu_don"] == 10)
    s, r = bh.lam("don_gop:huy", dg3["id"], {"ly_do": "Khách hủy"})
    ok("Hủy đơn gộp: nhả giữ, đơn con đã hủy", s == 200 and ton("HN", "HH")["so_giu"] == giu0 and ad.lay("don_ban", dc3["id"])["trang_thai"] == "da_huy", r)

    # ======================= 6. TÍN DỤNG =======================
    nhom("6. Tín dụng: phơi nhiễm = nợ + cam kết chưa giao; khách rủi ro chờ duyệt")
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["HN2"]["id"], "dong": [{"mat_hang_id": M["HH"]["id"], "so_kg": 1000, "don_gia": 50000}]})
    kt.lam("phieu_kho:ghiSo", pk["id"])
    mk = lambda kh, sl, dv_=APH: bh.tao("don_ban", {"khach_id": KH[kh]["id"], "don_vi_ban_id": dv_["id"], "dong": [{"mat_hang_id": M["HH"]["id"], "kho_id": K["HN2"]["id"], "so_kg": sl}]})
    r1 = mk("rui_ro", 100)  # 6 triệu > hạn mức 5 triệu
    s, r = bh.lam("don_ban:chotDon", r1["id"])
    ok("Khách rủi ro vượt hạn mức: chờ duyệt", ad.lay("don_ban", r1["id"])["trang_thai"] == "cho_duyet", r)
    s, r = bh.lam("don_ban:duyetGia", r1["id"], {"ly_do": "ok"})
    ok("Nhân viên bán hàng không duyệt tín dụng", s in (400, 403))
    s, r = kt.lam("don_ban:duyetGia", r1["id"], {"ly_do": "Giám đốc đồng ý bằng tin nhắn 24/10"})
    ok("Kế toán trưởng duyệt: đơn chờ xuất + lịch sử duyệt", s == 200 and ad.lay("don_ban", r1["id"])["trang_thai"] == "cho_xuat"
       and ad.ds("lich_su_duyet_gia", {"don_ban_id": r1["id"]}))
    n1 = mk("nho", 10)  # 600k
    bh.lam("don_ban:chotDon", n1["id"])
    n2 = mk("nho", 7, VH)  # 420k: nợ 0 + cam kết 600k + 420k > 1tr
    s, r = bh.lam("don_ban:chotDon", n2["id"])
    x = ad.lay("don_ban", n2["id"])
    ok("Khách thường: cam kết chưa giao (bên APH) + đơn mới (bên VH) vượt hạn mức → CẢNH BÁO theo chính sách, vẫn bán",
       x["trang_thai"] == "cho_xuat" and "hạn mức" in (x.get("canh_bao_tin_dung") or "") and "cam kết" in (x.get("canh_bao_tin_dung") or ""), x.get("canh_bao_tin_dung"))
    ad.lam("cau_hinh:dat", None, {"khoa": "vuot_han_muc_khach_thuong", "gia_tri": "duyet"})
    n3 = mk("nho", 1)
    bh.lam("don_ban:chotDon", n3["id"])
    ok("Đổi chính sách 'duyệt': khách thường vượt hạn mức chờ duyệt", ad.lay("don_ban", n3["id"])["trang_thai"] == "cho_duyet")
    ad.lam("cau_hinh:dat", None, {"khoa": "vuot_han_muc_khach_thuong", "gia_tri": "canh_bao"})
    l_ = kt.lam("luot_giao:taoLuot", None, {"don_ban_id": n1["id"], "dong": [{"don_ban_dong_id": ad.lay("don_ban", n1["id"], "dong")["dong"][0]["id"], "so_kg": 10}]})[1]["data"]
    kt.lam("luot_giao:khachNhan", l_["id"])
    n4 = mk("nho", 0.001)
    bh.lam("don_ban:chotDon", n4["id"])
    cb = ad.lay("don_ban", n4["id"]).get("canh_bao_tin_dung") or ""
    ok("Sau khi giao đơn 600k: phơi nhiễm không cộng trùng (nợ 600k thay cho cam kết 600k)", "nợ 600.000" in cb and "cam kết chưa giao 420.000" in cb, cb)
    for d_ in (n2, n3, n4, r1):
        ad.lam("don_ban:huy", d_["id"], {"ly_do": "dọn thử"})

    # ======================= 7. THU HỘ =======================
    nhom("7. Thu hộ: APH nhận tiền cho đơn con TL")
    no_tl0 = ad.lay("don_ban", don_tl["id"])["con_no"]
    pt = U["thu_chi"].tao("phieu_thu", {"khach_id": KH["thuong"]["id"], "don_vi_id": APH["id"], "hinh_thuc": "tien_mat", "so_tien": 20000000, "quy_id": Q["APH_TM"]["id"]})
    U["thu_chi"].lam("phieu_thu:ghi", pt["id"])
    s, r = U["thu_chi"].lam("phieu_thu:phanBoThuHo", pt["id"], {"phan_bo": [{"don_ban_id": don_tl["id"], "so_tien": 15000000}], "ghi_chu": "x"})
    ok("Thu ngân không tự phân bổ thu hộ liên pháp nhân", s in (400, 403))
    s, r = kt.lam("phieu_thu:phanBo", pt["id"], {"phan_bo": [{"don_ban_id": don_tl["id"], "so_tien": 15000000}]})
    ok("Phân bổ thường sang đơn của pháp nhân khác: bị chặn", s == 400, r)
    s, r = kt.lam("phieu_thu:phanBoThuHo", pt["id"], {"phan_bo": [{"don_ban_id": don_tl["id"], "so_tien": 15000000}], "ghi_chu": "Khách xác nhận trả TL qua APH (Zalo 24/10)"})
    ok("Kế toán phân bổ thu hộ có căn cứ", s == 200, r)
    ok("Nợ TL giảm đúng 15.000.000; APH còn 5.000.000 chưa phân bổ; quỹ TL không đổi",
       ad.lay("don_ban", don_tl["id"])["con_no"] == no_tl0 - 15000000 and ad.lay("phieu_thu", pt["id"])["chua_phan_bo"] == 5000000 and du("TL_TM") == 0)
    thh = ad.ds("thu_ho", {"phieu_thu_id": pt["id"]})
    ok("Nghĩa vụ thu hộ APH → TL theo dõi riêng (đang giữ hộ)", len(thh) == 1 and thh[0]["trang_thai"] == "dang_giu_ho" and thh[0]["so_tien"] == 15000000)

    # ======================= 8. POS =======================
    nhom("8. Bán nhanh: nhiều phương thức thanh toán, không cộng tiền hai lần")
    pos = U["pos"]
    s, r = pos.lam("ca_pos:mo", None, {"quy_id": Q["APH_TM"]["id"], "kho_id": K["HN"]["id"]})
    ok("Thu ngân không mở ca trên quỹ ngoài phạm vi", s == 400)
    s, r = pos.lam("ca_pos:mo", None, {"quy_id": Q["POS"]["id"], "kho_id": K["HN"]["id"], "tien_dau_ca": 0})
    ca = r["data"]["id"]
    ok("Mở ca", s == 200)
    tm0, nh0 = du("POS"), du("APH_NH")
    hn_goi0 = ton("HN", "GOI")["so_kg"]
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["HN"]["id"], "dong": [{"mat_hang_id": M["GOI"]["id"], "so_kg": 200, "don_gia": 9000}]})
    kt.lam("phieu_kho:ghiSo", pk["id"])
    rq = f"{k}-POS1"
    ban = {"ca_pos_id": ca, "request_id": rq, "dong": [{"mat_hang_id": M["GOI"]["id"], "dvt_nhap": "thung", "sl_nhap": 1}, {"mat_hang_id": M["GOI"]["id"], "so_kg": 5}],
           "thanh_toan": [{"hinh_thuc": "tien_mat", "so_tien": 300000}, {"hinh_thuc": "chuyen_khoan", "so_tien": 100000, "quy_id": Q["APH_NH"]["id"], "ma_gd": f"FT{k}"}]}
    s, r = pos.lam("ca_pos:ban", ca, ban)
    ok("Bán 25 gói × 15.000 (giá lẻ đã gồm VAT) = 375.000: TM 300k + CK 100k", s == 200 and r["data"]["phai_thu"] == 375000, r)
    pr = r["data"]
    ok("Tiền mặt chỉ thu 275.000 (thối 25.000), CK 100.000 chờ xác minh", pr["tien_mat"] == 275000 and pr["tien_thoi"] == 25000 and pr["chuyen_khoan_cho_xac_minh"] == 100000, pr)
    s, r2 = pos.lam("ca_pos:ban", ca, ban)
    ok("Bấm lại (cùng mã yêu cầu): không tạo đơn / tiền mới", r2["data"].get("da_ban_truoc") and du("POS") - tm0 == 275000 and du("APH_NH") == nh0)
    ok("Kho giảm 25 gói một lần", ton("HN", "GOI")["so_kg"] == hn_goi0 + 200 - 25)
    dpos = ad.ds("don_ban", {"request_id": rq})[0]
    ok("Đơn POS: nợ còn 100.000 tới khi CK được xác minh (CK không phải tiền thực nhận)", dpos["kenh"] == "pos" and dpos["con_no"] == 100000, dpos["con_no"])
    s, r = pos.lam("ca_pos:ban", ca, {"ca_pos_id": ca, "request_id": rq + "b", "dong": [{"mat_hang_id": M["GOI"]["id"], "so_kg": 2}],
                                      "thanh_toan": [{"hinh_thuc": "tien_mat", "so_tien": 10000}]})
    ok("Khách lẻ trả thiếu: bị chặn, không ghi nợ khách lẻ", s == 400 and not ad.ds("don_ban", {"request_id": rq + "b"}), r)
    s, r = pos.lam("ca_pos:ban", ca, {"ca_pos_id": ca, "request_id": rq + "c", "khach_id": KH["thuong"]["id"], "dong": [{"mat_hang_id": M["GOI"]["id"], "so_kg": 2}],
                                      "thanh_toan": [{"hinh_thuc": "tien_mat", "so_tien": 10000}, {"hinh_thuc": "ghi_no", "so_tien": 20000}]})
    ok("Khách có mã: tiền mặt + ghi nợ phần còn lại", s == 200 and r["data"]["ghi_no"] == 20000, r)
    s, r = pos.lam("ca_pos:chot", ca, {"thuc_dem": 280000})
    ok("Chốt ca: phải có 285.000, đếm 280.000 không lý do → bị chặn", s == 400, r)
    s, r = pos.lam("ca_pos:chot", ca, {"thuc_dem": 285000})
    ok("Chốt ca khớp, báo 1 CK chờ xác minh", s == 200 and r["data"]["chenh_lech"] == 0 and r["data"]["ck_cho_xac_minh"]["so_phieu"] == 1, r)

    # ======================= 9. NGÂN HÀNG =======================
    nhom("9. Sao kê: nạp hai lần không tạo thêm tiền; khớp CK chờ xác minh")
    csv = ("Ngày giao dịch,Số tham chiếu,Nội dung,Ghi nợ,Ghi có\n"
           f"24/10/2026,FT{k},KHACH LE CK FT{k},,100.000\n"
           f"24/10/2026,FT{k}X,NGUYEN VAN A chuyen tien hang,,2.500.000\n"
           f"24/10/2026,FT{k}P,Phi dich vu,11.000,\n")
    b64 = base64.b64encode(csv.encode()).decode()
    s, r = kt.lam("sao_ke:nap", None, {"quy_id": Q["APH_NH"]["id"], "ten_tep": "sk1.csv", "base64": b64})
    ok("Nạp sao kê: 3 dòng, gợi ý khớp phiếu CK của POS", s == 200 and r["data"]["so_moi"] == 3 and r["data"]["goi_y"], r)
    goi_y = r["data"]["goi_y"][0]
    s, r = kt.lam("sao_ke:nap", None, {"quy_id": Q["APH_NH"]["id"], "ten_tep": "sk1.csv", "base64": b64})
    ok("Nạp lại cùng tệp: không thêm dòng", r["data"].get("da_nap_truoc"))
    csv2 = csv + f"25/10/2026,FT{k}Y,TRAN THI B,,1.000.000\n"
    s, r = kt.lam("sao_ke:nap", None, {"quy_id": Q["APH_NH"]["id"], "ten_tep": "sk2.csv", "base64": base64.b64encode(csv2.encode()).decode()})
    ok("Tệp sao kê mới chồng ngày cũ: chỉ thêm 1 dòng mới, 3 dòng đã có", r["data"]["so_moi"] == 1 and r["data"]["so_trung"] == 3, r)
    nh1 = du("APH_NH")
    s, r = kt.lam("sao_ke_dong:khop", goi_y["sao_ke_dong_id"], {"phieu_thu_id": goi_y["phieu_thu_id"]})
    s2, r2 = kt.lam("sao_ke_dong:khop", goi_y["sao_ke_dong_id"], {"phieu_thu_id": goi_y["phieu_thu_id"]})
    ok("Khớp sao kê → CK được xác minh, tài khoản +100.000 một lần", s == 200 and r2["data"].get("da_khop_truoc") and du("APH_NH") - nh1 == 100000)
    ok("Đơn POS hết nợ sau xác minh", ad.lay("don_ban", dpos["id"])["con_no"] == 0)
    sk_x = [x for x in ad.ds("sao_ke_dong", {"quy_id": Q["APH_NH"]["id"]}) if x["ma_gd"] == f"FT{k}X"][0]
    s, r = kt.lam("sao_ke_dong:taoThu", sk_x["id"], {})
    ok("Dòng chưa rõ người nộp → phiếu thu 'chưa rõ', +2.500.000 vào tài khoản", s == 200 and du("APH_NH") - nh1 == 2600000)
    s, r = kt.lam("sao_ke_dong:taoThu", sk_x["id"], {})
    ok("Tạo thu lần 2 từ cùng dòng: bị chặn", s == 400)

    nhom("Chuyển khoản thủ quỹ ghi khi cấu hình 'chờ đối soát'")
    ad.lam("cau_hinh:dat", None, {"khoa": "ck_can_xac_minh", "gia_tri": "co"})
    nh2 = du("APH_NH")
    pt_ck = U["thu_chi"].tao("phieu_thu", {"khach_id": KH["thuong"]["id"], "don_vi_id": APH["id"], "hinh_thuc": "chuyen_khoan", "so_tien": 777000, "quy_id": Q["APH_NH"]["id"],
                                           "ma_gd": f"FT{k}CK"})
    s, r = U["thu_chi"].lam("phieu_thu:ghi", pt_ck["id"])
    ok("Thủ quỹ ghi CK → CHỜ XÁC MINH, tài khoản chưa tăng", s == 200 and ad.lay("phieu_thu", pt_ck["id"])["trang_thai"] == "cho_xac_minh" and du("APH_NH") == nh2, r)
    s, r = U["thu_chi"].lam("phieu_thu:xacMinh", pt_ck["id"], {"ma_gd": f"FT{k}CK"})
    ok("Thủ quỹ không tự xác minh", s in (400, 403))
    s, r = kt.lam("phieu_thu:xacMinh", pt_ck["id"], {"ma_gd": f"FT{k}CK"})
    ok("Kế toán xác minh: vào tài khoản đúng 777.000", s == 200 and du("APH_NH") - nh2 == 777000 and ad.lay("phieu_thu", pt_ck["id"])["trang_thai"] == "da_ghi", r)
    ad.lam("cau_hinh:dat", None, {"khoa": "ck_can_xac_minh", "gia_tri": "khong"})

    # ======================= 10. PHẢI HOÀN =======================
    nhom("10. Trả hàng sau khi đã thu đủ → khoản phải hoàn, không công nợ âm, không tự cấn")
    pt2 = U["thu_chi"].tao("phieu_thu", {"khach_id": KH["thuong"]["id"], "don_vi_id": APH["id"], "hinh_thuc": "tien_mat", "so_tien": 10080000, "quy_id": Q["APH_TM"]["id"],
                                         "phan_bo": [{"don_ban_id": don_aph["id"], "so_tien": 10080000}]})
    U["thu_chi"].lam("phieu_thu:ghi", pt2["id"])
    ok("Đơn APH đã thu đủ", ad.lay("don_ban", don_aph["id"])["con_no"] == 0)
    th_ = ad.tao("tra_hang", {"don_ban_id": don_aph["id"], "kho_nhan_id": K["HN"]["id"], "ly_do": "Khách trả 1 bao ẩm",
                              "dong": [{"don_ban_dong_id": ad.lay("don_ban", don_aph["id"], "dong")["dong"][0]["id"], "so_kg": 25}]})
    ad.lam("tra_hang:ghi", th_["id"])
    x = ad.lay("don_ban", don_aph["id"])
    ok("Phải hoàn 1.260.000, còn nợ 0 (không âm)", x["phai_hoan"] == 1260000 and x["con_no"] == 0 and x["tt_thanh_toan"] == "phai_hoan", [x["phai_hoan"], x["con_no"]])
    ok("Hóa đơn đã xuất chuyển 'Cần điều chỉnh' (không tự xuất)", ad.ds("hoa_don_cho_xuat", {"don_ban_id": don_aph["id"]})[0]["trang_thai"] == "can_dieu_chinh")
    tm1 = du("APH_TM")
    s, r = kt.lam("don_ban:xuLyHoan", don_aph["id"], {"cach": "hoan", "ly_do": "Hoàn tiền mặt", "quy_id": Q["APH_TM"]["id"]})
    ok("Hoàn tiền bằng phiếu chi từ quỹ APH: quỹ −1.260.000, phải hoàn về 0", s == 200 and du("APH_TM") - tm1 == -1260000 and ad.lay("don_ban", don_aph["id"])["phai_hoan"] == 0, r)
    ok("Phiếu thu không 'còn tiền' ảo sau hoàn", ad.lay("phieu_thu", pt2["id"])["chua_phan_bo"] == 0)
    nhom("Giảm giá sau thanh toán → phải hoàn → giữ làm tiền chưa phân bổ (không tự cấn đơn khác)")
    no_vh = ad.lay("don_ban", don_vh["id"])["con_no"]
    pt4 = U["thu_chi"].tao("phieu_thu", {"khach_id": KH["thuong"]["id"], "don_vi_id": VH["id"], "hinh_thuc": "tien_mat", "so_tien": no_vh, "quy_id": Q["VH_TM"]["id"],
                                         "phan_bo": [{"don_ban_id": don_vh["id"], "so_tien": no_vh}]})
    U["thu_chi"].lam("phieu_thu:ghi", pt4["id"])
    gg = ad.tao("dieu_chinh_gia", {"don_ban_id": don_vh["id"], "so_tien": 300000, "ly_do": "Chiết khấu sau bán"})
    ad.lam("dieu_chinh_gia:ghi", gg["id"])
    x = ad.lay("don_ban", don_vh["id"])
    ok("Giảm giá 300.000 sau khi thu đủ: phải hoàn 300.000, nợ 0", x["phai_hoan"] == 300000 and x["con_no"] == 0, [x["phai_hoan"], x["con_no"]])
    vh0 = du("VH_TM")
    s, r = kt.lam("don_ban:xuLyHoan", don_vh["id"], {"cach": "giu", "ly_do": "Khách để lại trừ đơn sau"})
    ok("Giữ làm tiền chưa phân bổ: phiếu thu VH còn 300.000 chưa phân bổ, quỹ không đổi, đơn hết phải hoàn",
       s == 200 and ad.lay("phieu_thu", pt4["id"])["chua_phan_bo"] == 300000 and du("VH_TM") == vh0 and ad.lay("don_ban", don_vh["id"])["phai_hoan"] == 0, r)

    # ======================= 11. GIÁ VỐN =======================
    nhom("11. Giá vốn: mẻ cũ điều chỉnh sau khi bán hết không đội giá trị lô mới")
    s, r = nm.lam("me_sx:nhapNhanh", None, {"so_phieu": sp + "-M2", "ngay": "2026-10-21", "kho_id": K["NL"]["id"], "kho_tp_id": K["TP"]["id"],
                                            "nvl": [{"mat_hang_id": M["NL"]["id"], "so_kg": 100}], "tp": [{"mat_hang_id": M["TP2"]["id"], "so_kg": 100}]})
    me2 = r["data"]["me_sx_id"]
    kt.lam("me_sx:chot", me2)
    ok("Mẻ 2: 100 kg TP2 giá thành 20.000", gv("TP", "TP2")["gia_tri"] == 2000000, gv("TP", "TP2"))
    db_ = kt.tao("don_ban", {"khach_id": KH["thuong"]["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": M["TP2"]["id"], "kho_id": K["TP"]["id"], "so_kg": 100, "don_gia": 40000}]})
    kt.lam("don_ban:chotDon", db_["id"])
    l_ = kt.lam("luot_giao:taoLuot", None, {"don_ban_id": db_["id"], "dong": [{"don_ban_dong_id": ad.lay("don_ban", db_["id"], "dong")["dong"][0]["id"], "so_kg": 100}]})
    if l_[0] != 200:
        print("  (kho TP nhà máy là kho nhà máy — chuyển sang HN2 để bán)")
    ok("Bán hết 100 kg TP2", l_[0] == 200 and kt.lam("luot_giao:khachNhan", l_[1]["data"]["id"])[0] == 200 and ton("TP", "TP2")["so_kg"] == 0, l_)
    pk = kt.tao("phieu_kho", {"loai": "nhap", "kho_id": K["TP"]["id"], "dong": [{"mat_hang_id": M["TP2"]["id"], "so_kg": 100, "don_gia": 30000}]})
    kt.lam("phieu_kho:ghiSo", pk["id"])
    kt.tao("me_sx_chi_phi", {"me_sx_id": me2, "loai": "nhan_cong", "so_tien": 500000, "so_chung_tu": f"BL-{k}"})
    s, r = kt.lam("me_sx:chot", me2)
    ok("Chốt lại mẻ 2 (+500.000): toàn bộ vào giá vốn (hàng đã bán), lô mới giữ 3.000.000",
       s == 200 and r["data"]["vao_gia_von"] == 500000 and gv("TP", "TP2")["gia_tri"] == 3000000, [r.get("data", {}).get("vao_gia_von"), gv("TP", "TP2")])
    nhom("Giá vốn: chuyển nhiều kho rồi chốt lại mẻ 1 → chênh lệch đi theo vết bình quân")
    hn_v0, tp_v0 = gv("HN", "TP")["gia_tri"], gv("TP", "TP")["gia_tri"]
    kt.tao("me_sx_chi_phi", {"me_sx_id": me1, "loai": "dien", "so_tien": 800000, "so_chung_tu": f"DIEN-{k}"})
    s, r = kt.lam("me_sx:chot", me1)
    dc = r.get("data", {})
    dct = ad.ds("dieu_chinh_gia_tri", {"chung_tu": ad.lay("me_sx", me1)["so"]})
    last = dct[-1] if dct else {}
    ok("Chênh 800.000 = vào tồn (TP NM + HN) + vào giá vốn (đã bán / hao hụt); làm tròn 0",
       s == 200 and last.get("chenh_lech") == 800000 and last.get("vao_ton", 0) + last.get("vao_gia_von", 0) + (last.get("vao_me") or 0) == 800000 and last.get("lam_tron") == 0, last)
    ok("Phần còn ở TP nhà máy (200/800 kg sau khi xuất) nhận 200.000", gv("TP", "TP")["gia_tri"] - tp_v0 == 200000, gv("TP", "TP")["gia_tri"] - tp_v0)
    ok("Phần theo sang HN (600 kg) chia theo vết: kho HN tăng > 0, không vượt 600.000", 0 < gv("HN", "TP")["gia_tri"] - hn_v0 <= 600000, gv("HN", "TP")["gia_tri"] - hn_v0)
    ok("Đối chiếu bảo toàn sau điều chỉnh: CÂN", doi_chieu())

    # ======================= 12. PHẠM VI MẶC ĐỊNH TỪ CHỐI =======================
    nhom("12. Phạm vi kho / quỹ chưa cấp → từ chối mặc định")
    s, r = U["kho_trong"].call("ton_kho:list", q="?pageSize=50")
    ok("Thủ kho chưa được cấp phạm vi: không thấy tồn kho nào", s == 200 and not r.get("data"), (s, len(r.get("data") or [])))
    ch2 = kt.tao("chuyen_hang", {"kho_di_id": K["HN"]["id"], "kho_den_id": K["HN2"]["id"], "kho_tg_id": K["TG"]["id"], "dong": [{"mat_hang_id": M["HH"]["id"], "so_kg": 1}]})
    s, r = U["kho_trong"].lam("chuyen_hang:xacNhanXuat", ch2["id"])
    ok("Thủ kho chưa được cấp phạm vi: không xác nhận xuất", s == 400, r)

    # ======================= 13. IMPORT HAI NGUỒN =======================
    nhom("13. Trung tâm dữ liệu: hai sheet mô tả MỘT chuyến → một chứng từ")
    ten_nm, ten_bh = f"Kho TP nhà máy NG {k}", f"Kho nhà máy {k}"
    nm_txt = ("## Sheet name: Chuyển kho\n"
              "Ngày,Số phiếu,Từ kho,Đến kho,Mã hàng,Tên hàng (tự hiện),ĐVT,Số lượng,Số kg,Lô,Xe / biển số,Ghi chú,Đã lên ERP\n"
              f"22/10/2026,CK-{k}-01,{ten_nm},Hàng đang vận chuyển {k},{k}-TP,Đỗ tách vỏ,kg,\"50,0\",\"50,0\",,,Xe Kiên,FALSE\n"
              f"22/10/2026,CK-{k}-02,{ten_nm},Hàng đang vận chuyển {k},,,kg,\"10,0\",\"10,0\",,,Gốc: ĐỖ 3 SAO — mã chưa có,FALSE\n"
              f"10/10/2026,CK-{k}-00,{ten_nm},Hàng đang vận chuyển {k},{k}-TP,Đỗ tách vỏ,kg,\"5,0\",\"5,0\",,,trước mốc,FALSE\n")
    bh_txt = ("## Sheet name: Chuyển kho – xuất khác\n"
              "CHUYỂN KHO VÀ XUẤT KHÁC\n\nKế toán ghi,,Kho ghi\n"
              "Ngày,Số phiếu,Từ kho,Đến kho,Loại (xuất khác),Mặt hàng (chọn),Số lượng,Ghi chú,Mã hàng,Tên hàng,ĐVT\n"
              f"23/10/2026,,{ten_bh},Kho cửa hàng {k},,{k}-TP | Đỗ tách vỏ,\"50,\",xe kiên,{k}-TP,Đỗ tách vỏ,Kg\n"
              f"23/10/2026,,Kho cửa hàng {k},Kho bác K {k},,{k}-HH | Lạc,\"3,\",,{k}-HH,Lạc,Kg\n"
              f"23/10/2026,HỦY-1,Kho cửa hàng {k},Kho bác K {k},,{k}-HH | Lạc,\"4,\",ĐÃ HỦY,{k}-HH,Lạc,Kg\n")
    s, r = kt.lam("nguon_tep:nap", None, {"he_thong": "nha_may", "ten_tep": "nm.txt", "van_ban": nm_txt})
    ok("Nạp sheet nhà máy (3 dòng)", s == 200 and r["data"]["so_moi"] == 3, r)
    tep_nm = r["data"]["id"]
    s, r = kt.lam("nguon_tep:nap", None, {"he_thong": "nha_may", "ten_tep": "nm.txt", "van_ban": nm_txt})
    ok("Nạp lại cùng tệp: nhận ra đã nạp", r["data"].get("da_nap_truoc"))
    s, r = kt.lam("nguon_tep:nap", None, {"he_thong": "ban_hang", "ten_tep": "bh.txt", "van_ban": bh_txt})
    ok("Nạp sổ bán hàng (tiêu đề ở dòng 4)", s == 200 and r["data"]["so_moi"] == 3, r)
    tep_bh = r["data"]["id"]
    # Ánh xạ: kho NM + kho BH "Kho nhà máy" → cùng kho TP nhà máy; đang vận chuyển → TG; cửa hàng → HN; bác K → HN2
    dat = {ten_nm: K["TP"], f"Hàng đang vận chuyển {k}": K["TG"], ten_bh: K["TP"], f"Kho cửa hàng {k}": K["HN"], f"Kho bác K {k}": K["HN2"]}
    for x in ad.ds("anh_xa_ma", {"ma_nguon": {"$in": list(dat)}}):
        kt.lam("anh_xa_ma:dat", x["id"], {"dich_id": dat[x["ma_nguon"]]["id"]})
    for x in ad.ds("anh_xa_ma", {"loai": "mat_hang", "ma_nguon": {"$in": [f"{k}-TP", f"{k}-HH"]}}):
        ok(f"Mã hàng {x['ma_nguon']} tự khớp", x["dich_id"] == (M["TP"] if x["ma_nguon"].endswith("TP") else M["HH"])["id"])
    s, r = kt.lam("nguon_tep:phanLoai", None, {"moc": "2026-10-18", "tep_ids": [tep_nm, tep_bh]})
    bc = r["data"]["bao_cao"]
    ok("Phân loại: 2 dòng ghép chuyến 'Có thể trùng', 1 'Chưa đủ' (thiếu mã), 1 'Trước mốc', 1 'Bị chặn' (HỦY), 1 'Nhập được'",
       bc.get("chuyen_kho", {}) == {"co_the_trung": 2, "chua_du": 1, "truoc_moc": 1, "bi_chan": 1, "nhap_duoc": 1}, bc)
    ok("Tìm trùng: đề xuất 1 cặp NM → HN", r["data"]["ghep"]["de_xuat"] >= 1, r["data"]["ghep"])
    cap = [c for c in ad.ds("khop_chung_tu", {"trang_thai": "de_xuat"}) if f"CK-{k}-01" in json.dumps(ad.lay("nguon_ban_ghi", c["ban_ghi_a_id"]))]
    ok("Cặp đề xuất đúng chuyến CK-…-01", len(cap) == 1, cap)
    kt.lam("khop_chung_tu:xacNhan", cap[0]["id"])
    tp0, hn0, tg0 = ton("TP", "TP")["so_kg"], ton("HN", "TP")["so_kg"], ton("TG", "TP")["so_kg"]
    ch_truoc = len(ad.ds("chuyen_hang", {"kho_di_id": K["TP"]["id"]}))
    s, r = kt.lam("nguon_tep:ghiSo", None, {"loai_nv": ["chuyen_ghep", "chuyen_kho"], "tep_ids": [tep_nm, tep_bh]})
    ok("Ghi sổ: 1 chuyến ghép + 1 chuyển nội bộ, không lỗi", s == 200 and r["data"]["ket_qua"].get("chuyen_ghep", {}).get("ok") == 1
       and r["data"]["ket_qua"].get("chuyen_kho", {}).get("ok") == 1, r)
    s, r2 = kt.lam("nguon_tep:ghiSo", None, {"loai_nv": ["chuyen_ghep", "chuyen_kho"], "tep_ids": [tep_nm, tep_bh]})
    ok("Ghi sổ lần 2: không tạo thêm chứng từ", s == 200 and not r2["data"]["ket_qua"], r2)
    ok("Hai sheet một chuyến → đúng MỘT chuyến chuyển hàng; NM −50, HN +50, đi đường không đổi",
       len(ad.ds("chuyen_hang", {"kho_di_id": K["TP"]["id"]})) == ch_truoc + 1 and ton("TP", "TP")["so_kg"] == tp0 - 50 and ton("HN", "TP")["so_kg"] == hn0 + 50
       and ton("TG", "TP")["so_kg"] == tg0, [ton("TP", "TP")["so_kg"], ton("HN", "TP")["so_kg"], ton("TG", "TP")["so_kg"]])
    ng = ad.ds("nguon_ban_ghi", {"tep_id": tep_nm})
    ok("Bản ghi nguồn giữ vết: số dòng, khóa, chứng từ đích", all(x["dong"] and x["khoa"] for x in ng) and any(x["chung_tu_dich"] for x in ng))
    s, r = kt.lam("nguon_tep:baoCao", None, {})
    ok("Báo cáo Trung tâm dữ liệu có phân loại + vấn đề thường gặp", s == 200 and r["data"]["phan_loai"] and r["data"]["van_de_thuong_gap"], r)
    nm_sua = nm_txt.replace('"50,0","50,0",,,Xe Kiên', '"51,0","51,0",,,Xe Kiên')
    s, r = kt.lam("nguon_tep:nap", None, {"he_thong": "nha_may", "ten_tep": "nm-sua.txt", "van_ban": nm_sua})
    tep_sua = r["data"]["id"]
    s, r = kt.lam("nguon_tep:phanLoai", None, {"moc": "2026-10-18", "tep_ids": [tep_sua]})
    sua = [x for x in ad.ds("nguon_ban_ghi", {"tep_id": tep_sua}) if f"CK-{k}-01" in (x["so_ct"] or "")]
    ok("Nạp lại bản SỬA của chuyến đã ghi: bản mới 'Có thể trùng — đã ghi sổ', không tự ghi lần hai",
       sua and sua[0]["ket_qua"] == "co_the_trung" and "ĐÃ GHI SỔ" in (sua[0]["van_de"] or ""), sua)
    s, r = kt.lam("nguon_tep:ghiSo", None, {"tep_ids": [tep_sua]})
    ok("Ghi sổ tệp sửa: không phát sinh chuyến mới", len(ad.ds("chuyen_hang", {"kho_di_id": K["TP"]["id"]})) == ch_truoc + 1)
    s, r = kt.lam("nguon_ban_ghi:boQua", sua[0]["id"], {"ly_do": "Bản sửa trùng chuyến đã ghi"})
    ok("Bỏ qua bản trùng có lý do", s == 200 and ad.lay("nguon_ban_ghi", sua[0]["id"])["ket_qua"] == "bo_qua")
    ok("Đối chiếu bảo toàn sau import: CÂN", doi_chieu())

    # ======================= 14. TRUY VẾT XUYÊN SUỐT =======================
    nhom("14. Truy vết: NVL nhà máy → mẻ → chuyển HN → đơn gộp → tiền vào tài khoản APH")
    dg2 = bh.tao("don_gop", {"khach_id": KH["thuong"]["id"], "request_id": f"{k}-DG2", "dong": [
        {"mat_hang_id": M["TP"]["id"], "don_vi_ban_id": APH["id"], "kho_id": K["HN"]["id"], "so_kg": 25, "so_bao": 1}]})
    bh.lam("don_gop:chot", dg2["id"])
    gd = ad.lay("don_gop", dg2["id"], "dong")["dong"][0]
    s, r = ad.lam("don_gop:taoGiao", dg2["id"], {"request_id": f"{k}-GN2", "dong": [{"don_gop_dong_id": gd["id"], "so_kg": 25, "so_bao": 1}]})
    ad.lam("giao_gop:xacNhan", r["data"]["id"], {"thuc": {}})
    con2 = ad.ds("don_ban", {"don_gop_id": dg2["id"]})[0]
    pt3 = U["thu_chi"].tao("phieu_thu", {"khach_id": KH["thuong"]["id"], "don_vi_id": APH["id"], "hinh_thuc": "chuyen_khoan", "so_tien": con2["con_no"],
                                         "quy_id": Q["APH_NH"]["id"], "ma_gd": f"FT{k}Z", "phan_bo": [{"don_ban_id": con2["id"], "so_tien": con2["con_no"]}]})
    U["thu_chi"].lam("phieu_thu:ghi", pt3["id"])
    lg = ad.ds("luot_giao", {"don_ban_id": con2["id"]})[0]
    s, r = kt.lam("luot_giao:truyVet", lg["id"])
    tv = r.get("data", {})
    vet = json.dumps(tv, ensure_ascii=False)
    h0 = (tv.get("hang") or [{}])[0]
    ok("Một dòng sổ kho xuất duy nhất, trừ đúng 25 kg", h0.get("so_dong_so_kho_xuat") == 1 and h0.get("tong_tru_kho") == 25, h0)
    ok("Nguồn kho HN ← chuyến từ TP nhà máy ← mẻ sản xuất ← NVL ← phiếu nhập", "tu_kho" in vet and '"me_sx"' in vet and '"nvl"' in vet and '"nhap"' in vet, vet[:800])
    ok("Xuôi: đơn con APH thuộc đơn gộp, thanh toán vào tài khoản APH, hết nợ",
       tv.get("ben_ban") == "APH" and tv.get("don_gop") and tv.get("con_no") == 0 and any(x["quy"] == "MB APH T4" and x["don_vi_nhan"] == "APH" for x in tv.get("thanh_toan", [])), tv)
    s, r = kt.lam("don_gop:tongQuan")
    ok("Báo cáo tổng quan vận hành chạy được (đơn gộp thiếu, công nợ theo bên bán, thu hộ, WIP, chênh lệch…)",
       s == 200 and all(x in r["data"] for x in ("don_gop_thieu", "cong_no_ben_ban", "thu_ho_dang_giu", "wip", "hang_doi_hoa_don")), r)

    nhom("Đối chiếu cuối")
    ok("Đối chiếu bảo toàn toàn hệ thống: CÂN", doi_chieu())
    loi = [t for t, d in KQ if not d]
    print(f"\nTỔNG {len(KQ)} ca, LỖI {len(loi)}")
    for t in loi:
        print("  LỖI:", t)
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
