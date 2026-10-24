#!/usr/bin/env python3
"""Bộ kiểm nghiệp vụ NocoBase 0.3.0 (dữ liệu giả, tiền tố KT-). Bao phủ bảng "bộ kiểm thử bắt buộc" của bản rà soát 24/10/2026.

    python3 kiem_030.py --email <quản trị> --password <mật khẩu>
"""
import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

KQ = []


def ok(ten, dk, ct=""):
    KQ.append((ten, bool(dk)))
    print(("ĐẠT " if dk else "LỖI ") + ten + (f" — {ct}" if ct != "" and not dk else ""))


class API:
    def __init__(self, url, email, pw, role=None):
        self.url, self.token, self.role = url.rstrip("/"), None, role
        s, r = self.call("auth:signIn", {"account": email, "password": pw}, h={"X-Authenticator": "basic"})
        if s != 200:
            raise SystemExit(f"Đăng nhập {email} lỗi: {r}")
        self.token = r["data"]["token"]

    def call(self, action, body=None, q="", h=None):
        hd = {"Content-Type": "application/json", **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
              **({"X-Role": self.role} if self.role else {}), **(h or {})}
        req = urllib.request.Request(f"{self.url}/api/{action}{q}", method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None, headers=hd)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b"{}")
            except Exception:
                return e.code, {}

    def tao(self, bang, v):
        q = "".join(f"&updateAssociationValues[]={x}" for x, y in v.items() if isinstance(y, list))
        s, r = self.call(f"{bang}:create", v, q="?" + q[1:] if q else "")
        if s != 200:
            raise SystemExit(f"Tạo {bang} lỗi {s}: {r}")
        return r["data"]

    def lam(self, act, id_=None, v=None):
        return self.call(act, v or {}, q=f"?filterByTk={id_}" if id_ is not None else "")

    def lay(self, bang, id_, appends=""):
        return self.call(f"{bang}:get", q=f"?filterByTk={id_}" + (f"&appends={appends}" if appends else ""))[1].get("data")

    def ds(self, bang, f):
        return self.call(f"{bang}:list", q="?pageSize=1000&filter=" + urllib.parse.quote(json.dumps(f)))[1].get("data") or []


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="http://localhost:13000")
    a.add_argument("--email", required=True)
    a.add_argument("--password", required=True)
    o = a.parse_args()
    ad = API(o.url, o.email, o.password)
    k = "KT-" + uuid.uuid4().hex[:5]

    # Người dùng thử theo nhóm
    pw = "Thu" + uuid.uuid4().hex[:10]
    for role in ["ban_hang", "kho", "nha_may", "thu_chi", "ke_toan"]:
        em = f"thu-{role}@aphvh.local"
        u = ad.ds("users", {"email": em})
        if u:
            ad.call("users:update", {"password": pw, "roles": [role]}, q=f"?filterByTk={u[0]['id']}")
        else:
            ad.tao("users", {"email": em, "nickname": "Thử " + role, "password": pw, "roles": [role]})
    time.sleep(2)
    U = {r: API(o.url, f"thu-{r}@aphvh.local", pw, r) for r in ["ban_hang", "kho", "nha_may", "thu_chi", "ke_toan"]}

    dv = {x["ma"]: x for x in ad.ds("don_vi", {})}
    APH, TL = dv["APH"], dv["TL"]
    q_aph_tm = ad.tao("quy", {"ma": k + "-APH-TM", "ten": "TM APH thử", "don_vi_id": APH["id"], "loai": "tien_mat"})
    q_aph_nh = ad.tao("quy", {"ma": k + "-APH-NH", "ten": "MB APH thử", "don_vi_id": APH["id"], "loai": "ngan_hang"})
    q_tl_tm = ad.tao("quy", {"ma": k + "-TL-TM", "ten": "TM TL thử", "don_vi_id": TL["id"], "loai": "tien_mat"})
    kho1 = ad.tao("kho", {"ma": k + "-K1", "ten": "Cửa hàng thử"})
    kho2 = ad.tao("kho", {"ma": k + "-K2", "ten": "Nhà máy thử", "loai_kho": "nha_may"})
    khoxl = ad.tao("kho", {"ma": k + "-XL", "ten": "Chờ xử lý thử", "loai_kho": "cho_xu_ly"})
    dx = ad.tao("mat_hang", {"ma": k + "-DX", "ten": "Đỗ xanh thử", "kg_bao": 25, "gia_ban": 40000, "gia_san": 36000})
    nl = ad.tao("mat_hang", {"ma": k + "-NL", "ten": "Đỗ nguyên liệu thử", "loai_hang": "nguyen_lieu"})
    pp = ad.tao("mat_hang", {"ma": k + "-PP", "ten": "Vỏ đỗ thử", "loai_hang": "phu_pham"})
    thung = ad.tao("mat_hang", {"ma": k + "-TH", "ten": "Vỏ thùng carton thử", "dvt_ton": "cai", "loai_hang": "bao_bi"})
    tpd = ad.tao("mat_hang", {"ma": k + "-TPD", "ten": "Đỗ đóng thùng thử", "loai_hang": "thanh_pham"})
    kh = ad.tao("khach_hang", {"ma": k + "-KH", "ten": "Khách thử", "sdt": "0911000000", "dia_chi": "Hà Nội"})
    kh2 = ad.tao("khach_hang", {"ma": k + "-KH2", "ten": "Khách hạn mức", "han_muc": 1000000})
    ncc = ad.tao("nha_cung_cap", {"ma": k + "-NCC", "ten": "NCC thử"})

    def ton(kho, mh):
        r = ad.ds("ton_kho", {"kho_id": kho["id"], "mat_hang_id": mh["id"]})
        return r[0] if r else {"so_kg": 0, "so_giu": 0, "so_cho_gia": 0}

    def gv(kho, mh):
        r = ad.ds("gia_von", {"kho_id": kho["id"], "mat_hang_id": mh["id"]})
        return r[0] if r else {}

    def du(q):
        return sum(x["so_tien"] for x in ad.ds("so_quy", {"quy_id": q["id"]}))

    # ---- Nhập có giá (kế toán) và nhập chờ giá (kho) ----
    pk = ad.tao("phieu_kho", {"loai": "nhap", "kho_id": kho1["id"], "nha_cung_cap_id": ncc["id"],
                              "dong": [{"mat_hang_id": dx["id"], "so_bao": 40, "don_gia": 30000}]})
    ad.lam("phieu_kho:ghiSo", pk["id"])
    ok("Nhập 40 bao × 25 kg có giá 30.000: tồn 1.000 kg, giá BQ 30.000, phải trả NCC 30 triệu",
       ton(kho1, dx)["so_kg"] == 1000 and gv(kho1, dx).get("gia_bq") == 30000 and ad.lay("phieu_kho", pk["id"])["phai_tra"] == 30000000)
    pk2 = U["kho"].tao("phieu_kho", {"loai": "nhap", "kho_id": kho1["id"], "dong": [{"mat_hang_id": dx["id"], "so_kg": 400, "don_gia": 99999}]})
    U["kho"].lam("phieu_kho:ghiSo", pk2["id"])
    t = ton(kho1, dx)
    ok("Thủ kho nhập (kể cả gõ giá): thành CHỜ ĐỊNH GIÁ, tồn 1.400 nhưng không vào giá trị",
       t["so_kg"] == 1400 and t["so_cho_gia"] == 400 and gv(kho1, dx).get("so_kg") == 1000, t)
    s, r = U["kho"].lam("phieu_kho:dinhGia", pk2["id"], {"gia": {}})
    ok("Thủ kho không định giá được", s in (400, 403))

    # ---- Bán: chốt, giữ hàng, giao nhiều đợt ----
    don = U["ban_hang"].tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": APH["id"], "request_id": k + "-D1",
                                        "dong": [{"mat_hang_id": dx["id"], "kho_id": kho1["id"], "so_kg": 1000, "don_gia": 40000}]})
    s, r = U["ban_hang"].call("don_ban:create", {"khach_id": kh["id"], "don_vi_ban_id": APH["id"], "request_id": k + "-D1"})
    ok("Tạo trùng đơn (mạng chập chờn, cùng mã yêu cầu): chỉ một đơn", s == 400 and len(ad.ds("don_ban", {"request_id": k + "-D1"})) == 1, r)
    U["ban_hang"].lam("don_ban:chotDon", don["id"])
    dong_id = ad.lay("don_ban", don["id"], "dong")["dong"][0]["id"]
    s, r = U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don["id"], "request_id": k + "-L1", "dong": [{"don_ban_dong_id": dong_id, "so_kg": 1100}]})
    ok("Lượt giao vượt lượng đặt: bị chặn", s == 400, r)
    s, r = U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don["id"], "request_id": k + "-L1", "dong": [{"don_ban_dong_id": dong_id, "so_kg": 600}]})
    l1 = r["data"]["id"]
    s, r2 = U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don["id"], "request_id": k + "-L1", "dong": [{"don_ban_dong_id": dong_id, "so_kg": 600}]})
    ok("Thử lại tạo lượt cùng mã yêu cầu: trả lại đúng lượt cũ, không giữ thêm", r2["data"]["id"] == l1 and ton(kho1, dx)["so_giu"] == 600)
    ok("Chờ giá 400 + giữ 600: khả dụng còn 400", (lambda x: x["so_kg"] - x["so_giu"] - x["so_cho_gia"])(ton(kho1, dx)) == 400)
    # Hai lượt cùng lúc tranh 400 kg khả dụng (đơn khác)
    don_b = ad.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": TL["id"], "dong": [{"mat_hang_id": dx["id"], "kho_id": kho1["id"], "so_kg": 600, "don_gia": 40000}]})
    ad.lam("don_ban:chotDon", don_b["id"])
    db_id = ad.lay("don_ban", don_b["id"], "dong")["dong"][0]["id"]
    kq = []
    th = [threading.Thread(target=lambda: kq.append(U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don_b["id"],
          "dong": [{"don_ban_dong_id": db_id, "so_kg": 300}]})[0])) for _ in range(2)]
    [x.start() for x in th]
    [x.join() for x in th]
    ok("Hai nhân viên cùng giữ 300 kg khi khả dụng 400: một được, một bị chặn", sorted(kq) == [200, 400], kq)
    luot_b = [x for x in ad.ds("luot_giao", {"don_ban_id": don_b["id"]}) if x["trang_thai"] == "cho_xuat"][0]

    s, r = U["kho"].lam("luot_giao:khachNhan", l1, {"nguoi_nhan": "Anh A"})
    U["kho"].lam("luot_giao:khachNhan", l1)
    d = ad.lay("don_ban", don["id"])
    t = ton(kho1, dx)
    ok("Giao đợt 1 600 kg (bấm 2 lần): tồn 800, giữ 300 (đơn TL), đơn Giao một phần, phải thu 24 triệu",
       t["so_kg"] == 800 and t["so_giu"] == 300 and d["trang_thai"] == "dang_giao" and d["phai_thu"] == 24000000, (t, d["trang_thai"], d["phai_thu"]))
    ok("Giá vốn lượt 1 = 600 × 30.000 (chỉ kế toán xem)", d["gia_von"] == 18000000, d.get("gia_von"))
    db_ban = U["ban_hang"].lay("don_ban", don["id"])
    ok("Nhân viên bán đọc đơn: không thấy giá vốn", "gia_von" not in db_ban and db_ban.get("phai_thu") == 24000000, db_ban)
    s, r = ad.lam("don_ban:huy", don["id"], {"ly_do": "thử"})
    ok("Hủy đơn đã giao: bị chặn, kho không đổi", s == 400 and ton(kho1, dx)["so_kg"] == 800, r)

    # Định giá hàng chờ → khả dụng thêm 200
    s, r = ad.lam("phieu_kho:dinhGia", pk2["id"], {"gia": {str(ad.lay("phieu_kho", pk2["id"], "dong")["dong"][0]["id"]): 33000}})
    t = ton(kho1, dx)
    ok("Kế toán định giá 400 kg chờ giá @33.000: hết chờ giá; giá trị kho có giá đúng",
       t["so_cho_gia"] == 0 and gv(kho1, dx)["so_kg"] == 800 and gv(kho1, dx)["gia_tri"] == 400 * 30000 + 400 * 33000, (t, gv(kho1, dx)))

    # Đợt 2 vận chuyển: bàn giao xe rồi khách nhận
    s, r = U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don["id"], "cach_giao": "van_chuyen", "dong": [{"don_ban_dong_id": dong_id, "so_kg": 250}]})
    l2 = r["data"]["id"]
    U["kho"].lam("luot_giao:banGiaoXe", l2, {"nguoi_nhan": "Nhà xe B", "bien_so": "29C-1"})
    t_sau_xe = ton(kho1, dx)["so_kg"]
    U["ban_hang"].lam("luot_giao:khachNhan", l2)
    ok("Bàn giao xe trừ kho; khách nhận sau không trừ lần hai", t_sau_xe == 550 and ton(kho1, dx)["so_kg"] == 550)
    s, r = U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don["id"], "dong": [{"don_ban_dong_id": dong_id, "so_kg": 150}]})
    ok("Tạo lượt 3 (150 kg)", s == 200, r)
    U["kho"].lam("luot_giao:khachNhan", r["data"]["id"])
    d = ad.lay("don_ban", don["id"])
    ok("Ba đợt 600 + 250 + 150 = 1.000: đơn Đã giao đủ, không giao thêm được", d["trang_thai"] == "da_giao" and
       U["ban_hang"].lam("luot_giao:taoLuot", None, {"don_ban_id": don["id"], "dong": [{"don_ban_dong_id": dong_id, "so_kg": 1}]})[0] == 400)

    # Đơn TL giao lượt đang giữ
    U["kho"].lam("luot_giao:khachNhan", luot_b["id"])
    ok("Đơn TL và đơn APH cùng kho: 1.400 − 1.000 − 300 còn 100 kg; công nợ tách đơn vị",
       ton(kho1, dx)["so_kg"] == 100 and ad.lay("don_ban", don_b["id"])["phai_thu"] == 12000000)

    # ---- Trả hàng 5 kg từ bao 25 kg; giảm giá ----
    th_ = U["kho"].tao("tra_hang", {"don_ban_id": don["id"], "kho_nhan_id": khoxl["id"], "ly_do": "5 kg hỏng",
                                    "dong": [{"don_ban_dong_id": dong_id, "so_kg": 5}]})
    U["kho"].lam("tra_hang:ghi", th_["id"])
    U["kho"].lam("tra_hang:ghi", th_["id"])
    d = ad.lay("don_ban", don["id"])
    ok("Trả 5 kg hỏng: nhập đúng 5 kg vào kho chờ xử lý, phải thu giảm 200.000", ton(khoxl, dx)["so_kg"] == 5 and d["phai_thu"] == 40000000 - 200000,
       (ton(khoxl, dx), d["phai_thu"]))
    th2 = U["kho"].tao("tra_hang", {"don_ban_id": don["id"], "kho_nhan_id": khoxl["id"], "ly_do": "thử vượt", "dong": [{"don_ban_dong_id": dong_id, "so_kg": 996}]})
    ok("Trả quá lượng đã giao − đã trả: bị chặn", U["kho"].lam("tra_hang:ghi", th2["id"])[0] == 400)
    gg = U["ban_hang"].tao("dieu_chinh_gia", {"don_ban_id": don["id"], "so_tien": 300000, "ly_do": "Hàng hơi ẩm, khách giữ hàng"})
    ok("Nhân viên bán chỉ lập phiếu giảm giá, không tự ghi", U["ban_hang"].lam("dieu_chinh_gia:ghi", gg["id"])[0] == 403)
    ad.lam("dieu_chinh_gia:ghi", gg["id"])
    ok("Giảm giá 300.000 không nhập kho, phải thu giảm", ad.lay("don_ban", don["id"])["phai_thu"] == 39500000 and ton(kho1, dx)["so_kg"] == 100)

    # ---- Tiền: thu nợ, chưa rõ khách, cọc, thu hộ ----
    pt = U["thu_chi"].tao("phieu_thu", {"khach_id": kh["id"], "don_vi_id": APH["id"], "quy_id": q_aph_nh["id"], "hinh_thuc": "chuyen_khoan",
                                        "ma_gd": "FT1", "so_tien": 30000000, "phan_bo": [{"don_ban_id": don["id"], "so_tien": 25000000}]})
    U["thu_chi"].lam("phieu_thu:ghi", pt["id"])
    U["thu_chi"].lam("phieu_thu:ghi", pt["id"])
    ok("Thu CK 30 triệu vào MB APH, trả đơn APH 25 triệu, 5 triệu chưa phân bổ (bấm 2 lần chỉ ghi 1)",
       du(q_aph_nh) == 30000000 and ad.lay("phieu_thu", pt["id"])["chua_phan_bo"] == 5000000 and ad.lay("don_ban", don["id"])["con_no"] == 14500000)
    s, r = U["thu_chi"].lam("phieu_thu:phanBo", pt["id"], {"phan_bo": [{"don_ban_id": don_b["id"], "so_tien": 5000000}]})
    ok("Tiền APH không tự trả nợ đơn TL (phân bổ thường bị chặn)", s == 400, r)
    s, r = U["thu_chi"].lam("phieu_thu:phanBoThuHo", pt["id"], {"ghi_chu": "khách nhầm TK", "phan_bo": [{"don_ban_id": don_b["id"], "so_tien": 5000000}]})
    ok("Thủ quỹ không được phân bổ thu hộ", s in (400, 403), s)
    s, r = U["ke_toan"].lam("phieu_thu:phanBoThuHo", pt["id"], {"ghi_chu": "Khách xác nhận chuyển nhầm TK APH", "phan_bo": [{"don_ban_id": don_b["id"], "so_tien": 5000000}]})
    th_ho = ad.ds("thu_ho", {"phieu_thu_id": pt["id"]})
    ok("Kế toán phân bổ thu hộ: nợ TL giảm 5 triệu, tiền vẫn ở MB APH, ghi khoản APH giữ hộ TL",
       s == 200 and ad.lay("don_ban", don_b["id"])["con_no"] == 7000000 and du(q_aph_nh) == 30000000 and len(th_ho) == 1
       and th_ho[0]["don_vi_nhan_id"] == APH["id"] and th_ho[0]["don_vi_chu_no_id"] == TL["id"], r)
    cr = U["thu_chi"].tao("phieu_thu", {"loai_thu": "chua_ro", "don_vi_id": APH["id"], "quy_id": q_aph_nh["id"], "hinh_thuc": "chuyen_khoan",
                                        "ma_gd": "FT2", "so_tien": 2000000})
    U["thu_chi"].lam("phieu_thu:ghi", cr["id"])
    ok("Tiền chưa rõ người nộp: vào đúng tài khoản, nằm ở chưa phân bổ",
       du(q_aph_nh) == 32000000 and ad.lay("phieu_thu", cr["id"])["chua_phan_bo"] == 2000000)
    ok("Chưa nhận diện thì không phân bổ được", U["thu_chi"].lam("phieu_thu:phanBo", cr["id"], {"phan_bo": [{"don_ban_id": don["id"], "so_tien": 1}]})[0] == 400)
    U["thu_chi"].lam("phieu_thu:nhanDien", cr["id"], {"khach_id": kh["id"]})
    U["thu_chi"].lam("phieu_thu:phanBo", cr["id"], {"phan_bo": [{"don_ban_id": don["id"], "so_tien": 2000000}]})
    ok("Nhận diện khách rồi phân bổ 2 triệu", ad.lay("don_ban", don["id"])["con_no"] == 12500000)
    coc = U["thu_chi"].tao("phieu_thu", {"loai_thu": "coc", "khach_id": kh["id"], "don_vi_id": APH["id"], "quy_id": q_aph_tm["id"],
                                         "so_tien": 1000000, "muc_dich_coc": "Giữ 1 tấn đỗ tháng 11"})
    U["thu_chi"].lam("phieu_thu:ghi", coc["id"])
    ok("Tiền cọc: vào quỹ, không tự trừ nợ cũ", du(q_aph_tm) == 1000000 and ad.lay("don_ban", don["id"])["con_no"] == 12500000)

    # ---- Hạn mức, giá sàn ----
    d3 = ad.tao("don_ban", {"khach_id": kh2["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": dx["id"], "kho_id": kho1["id"], "so_kg": 50, "don_gia": 40000}]})
    s, r = ad.lam("don_ban:chotDon", d3["id"])
    ok("Đơn 2 triệu vượt hạn mức 1 triệu: chờ duyệt", r.get("data", {}).get("cho_duyet") is True, r)
    d4 = ad.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": APH["id"], "dong": [{"mat_hang_id": dx["id"], "kho_id": kho1["id"], "so_kg": 10, "don_gia": 35000}]})
    s, r = ad.lam("don_ban:chotDon", d4["id"])
    ok("Bán dưới giá sàn: chờ duyệt; bán hàng không tự duyệt",
       r.get("data", {}).get("cho_duyet") is True and U["ban_hang"].lam("don_ban:duyetGia", d4["id"], {"ly_do": "x"})[0] == 403)

    # ---- Chuyển kho mang giá trị; nhà máy sản xuất 1.000 → 820 + 150 + hao 30; đóng gói bao bì Cái ----
    pkn = ad.tao("phieu_kho", {"loai": "nhap", "kho_id": kho2["id"], "dong": [{"mat_hang_id": nl["id"], "so_kg": 1000, "don_gia": 20000},
                                                                             {"mat_hang_id": thung["id"], "so_kg": 200, "don_gia": 5000}]})
    ad.lam("phieu_kho:ghiSo", pkn["id"])
    sx = U["nha_may"].tao("phieu_kho", {"loai": "san_xuat", "kho_id": kho2["id"], "chi_phi_sx": 1800000, "dong": [
        {"mat_hang_id": nl["id"], "huong": "vao", "so_kg": 1000}, {"mat_hang_id": dx["id"], "huong": "ra", "so_kg": 820},
        {"mat_hang_id": pp["id"], "huong": "phu_pham", "so_kg": 150, "don_gia": 2000}]})
    s, r = U["nha_may"].lam("phieu_kho:ghiSo", sx["id"])
    ok("Sản xuất hao 30 kg không ghi lý do: bị chặn", s == 400)
    U["nha_may"].call("phieu_kho:update", {"ghi_chu": "Hao hụt sàng, phơi"}, q=f"?filterByTk={sx['id']}")
    s, r = U["nha_may"].lam("phieu_kho:ghiSo", sx["id"])
    ok("Nhà máy ghi sản xuất: phản hồi KHÔNG có giá thành / giá trị", s == 200 and "gia_thanh" not in r["data"] and "gia_tri_nvl" not in r["data"], r)
    p_sx = ad.lay("phieu_kho", sx["id"])
    ok("Giá thành = (20 triệu + 1,8 triệu − 300.000 phụ phẩm) / 820 = 26.219,51 đ/kg",
       p_sx["gia_thanh"] == 26219.51 and p_sx["kg_vao"] == 1000 and p_sx["kg_ra"] == 970, p_sx)
    ok("Nhà máy đọc phiếu: không thấy giá thành, giá trị, đơn giá dòng",
       all(x not in U["nha_may"].lay("phieu_kho", sx["id"], "dong") for x in ("gia_thanh", "gia_tri_nvl", "chi_phi_sx"))
       and all("don_gia" not in x for x in U["nha_may"].lay("phieu_kho", sx["id"], "dong")["dong"]))
    for role in ("nha_may", "kho", "ban_hang", "thu_chi"):
        ok(f"{role} gọi API giá vốn / sổ giá trị: bị chặn",
           U[role].call("gia_von:list")[0] == 403 and U[role].call("so_gia_von:list")[0] == 403)
    ok("Nhà máy xuất dữ liệu (export): bị chặn", U["nha_may"].call("phieu_kho:export", {})[0] in (403, 404))
    dg = U["nha_may"].tao("phieu_kho", {"loai": "dong_goi", "kho_id": kho2["id"], "dong": [
        {"mat_hang_id": dx["id"], "huong": "vao", "so_kg": 500}, {"mat_hang_id": thung["id"], "huong": "vao", "so_kg": 100},
        {"mat_hang_id": tpd["id"], "huong": "ra", "so_kg": 500}]})
    s, r = U["nha_may"].lam("phieu_kho:ghiSo", dg["id"])
    ok("Đóng gói 500 kg + 100 vỏ thùng (Cái): kg cân, giảm đúng 100 Cái, thành phẩm 500 kg",
       s == 200 and ton(kho2, thung)["so_kg"] == 100 and ton(kho2, tpd)["so_kg"] == 500 and ton(kho2, dx)["so_kg"] == 320, r)
    ok("Giá thành thành phẩm đóng thùng gồm vỏ thùng: (500 × 26.219,51 + 100 × 5.000) / 500",
       abs(ad.lay("phieu_kho", dg["id"])["gia_thanh"] - (500 * 26219.51 + 500000) / 500) < 1, ad.lay("phieu_kho", dg["id"]).get("gia_thanh"))
    ck = ad.tao("phieu_kho", {"loai": "chuyen", "kho_id": kho2["id"], "kho_dich_id": kho1["id"], "dong": [{"mat_hang_id": dx["id"], "so_kg": 100}]})
    gt_truoc = gv(kho1, dx)
    ad.lam("phieu_kho:ghiSo", ck["id"])
    gt_sau = gv(kho1, dx)
    ok("Chuyển 100 kg nhà máy → cửa hàng mang giá trị xuất thực tế (giá theo kho)",
       abs(gt_sau["gia_tri"] - gt_truoc["gia_tri"] - 100 * 26219.51) < 5, (gt_truoc, gt_sau))

    # ---- NCC, phiếu chi, quỹ, chốt ca ----
    pc = ad.tao("phieu_chi", {"don_vi_id": APH["id"], "quy_id": q_aph_nh["id"], "nguoi_nhan": "NCC thử", "so_tien": 40000000, "ly_do": "Trả NCC",
                              "ma_gd": "CK1", "nha_cung_cap_id": ncc["id"], "phieu_kho_id": pk["id"]})
    ok("Trả NCC quá phải trả của phiếu nhập: bị chặn", ad.lam("phieu_chi:ghi", pc["id"])[0] == 400)
    pc = ad.tao("phieu_chi", {"don_vi_id": APH["id"], "quy_id": q_aph_nh["id"], "nguoi_nhan": "NCC thử", "so_tien": 10000000, "ly_do": "Trả NCC",
                              "ma_gd": "CK1", "nha_cung_cap_id": ncc["id"], "phieu_kho_id": pk["id"]})
    ad.lam("phieu_chi:ghi", pc["id"])
    ok("Trả NCC 10 triệu: phiếu nhập còn phải trả 20 triệu, ngân hàng giảm", ad.lay("phieu_kho", pk["id"])["da_tra"] == 10000000 and du(q_aph_nh) == 22000000)
    pcx = ad.tao("phieu_chi", {"don_vi_id": APH["id"], "quy_id": q_aph_tm["id"], "nguoi_nhan": "x", "so_tien": 5000000, "ly_do": "x"})
    ok("Chi tiền mặt quá quỹ: bị chặn", ad.lam("phieu_chi:ghi", pcx["id"])[0] == 400)
    ct = ad.tao("chuyen_tien", {"tu_quy_id": q_aph_tm["id"], "den_quy_id": q_tl_tm["id"], "so_tien": 100000})
    ok("Không chuyển tiền giữa hai đơn vị", ad.lam("chuyen_tien:ghi", ct["id"])[0] == 400)
    s, r = U["thu_chi"].lam("chot_ca:chot", None, {"quy_id": q_aph_tm["id"], "thuc_dem": 900000, "ly_do": "Thiếu 100.000 đang kiểm"})
    ok("Chốt ca: sổ 1 triệu, đếm 900.000, lệch −100.000 có lý do", s == 200 and r["data"]["chenh_lech"] == -100000, r)

    # ---- Hủy phiếu thu hoàn công nợ; báo cáo ----
    ok("Thủ quỹ không tự hủy phiếu thu đã ghi", U["thu_chi"].lam("phieu_thu:huy", pt["id"], {"ly_do": "x"})[0] == 403)
    U["ke_toan"].lam("phieu_thu:huy", pt["id"], {"ly_do": "Thử hủy"})
    ok("Hủy phiếu thu: nợ APH và nợ TL trả lại, khoản thu hộ hủy, tiền ngân hàng trừ lại",
       ad.lay("don_ban", don["id"])["con_no"] == 37500000 and ad.lay("don_ban", don_b["id"])["con_no"] == 12000000
       and ad.ds("thu_ho", {"phieu_thu_id": pt["id"]})[0]["trang_thai"] == "da_huy" and du(q_aph_nh) == -8000000,
       (ad.lay("don_ban", don["id"])["con_no"], ad.lay("don_ban", don_b["id"])["con_no"], ad.ds("thu_ho", {"phieu_thu_id": pt["id"]}), du(q_aph_nh)))
    s, r = ad.call("don_ban:baoCao", {"theo": "don_vi"})
    ok("Báo cáo lãi gộp theo đơn vị (kế toán)", s == 200 and any(x["nhom"] == APH["ten"] for x in r["data"]), r)
    ok("Nhân viên bán không xem báo cáo lãi gộp", U["ban_hang"].call("don_ban:baoCao", {"theo": "don_vi"})[0] in (400, 403))
    s, _ = ad.call("so_kho:create", {"kho_id": kho1["id"], "so_kg": 999})
    ok("Không ghi tay sổ kho / tồn / sổ quỹ", s >= 400 and ad.call("ton_kho:update", {"so_kg": 1}, q=f"?filterByTk=1")[0] >= 400)

    loi = [x for x in KQ if not x[1]]
    print(f"\nTỔNG {len(KQ)} ca, LỖI {len(loi)}")
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
