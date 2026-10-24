#!/usr/bin/env python3
"""Bộ kiểm 0.3.1: Go-Live & số dư đầu kỳ (6 điều kiện nghiệm thu), tài sản, mẻ sản xuất. Dữ liệu giả tiền tố GL-.
Chạy trên CSDL THỬ (tạo kỳ mở sổ thử rồi khóa).

    python3 kiem_golive.py --email <quản trị> --password <mật khẩu>
"""
import argparse
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
    k = "GL" + uuid.uuid4().hex[:4].upper()
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
    kt = U["ke_toan"]

    # Kỳ mở sổ thử (đóng kỳ cũ còn mở nếu có — chỉ trên CSDL thử)
    for x in ad.ds("ky_mo_so", {"trang_thai": "mo"}):
        ad.lam("ky_mo_so:khoa", x["id"], {"bo_qua_lo_dang_do": True})
    ky = kt.tao("ky_mo_so", {"ma": k, "ngay_chot": "2026-10-25"})
    ok("Không mở hai kỳ mở sổ cùng lúc", kt.call("ky_mo_so:create", {"ma": k + "x"})[0] >= 400)

    def lo(api, loai, bang, nguon="thử", che_do="bo_qua"):
        s, r = api.call("nhap_lo:create", {"loai": loai, "du_lieu_goc": bang, "nguon": nguon, "che_do": che_do})
        return s, (r.get("data") or {}).get("id"), r

    def chay(loai, bang, nguon="thử", che_do="bo_qua"):
        s, lid, r = lo(kt, loai, bang, nguon, che_do)
        assert s == 200, r
        s1, r1 = kt.lam("nhap_lo:kiem", lid)
        return lid, r1.get("data") or r1

    # ---- Quyền mở sổ ở máy chủ (điều kiện 5) ----
    ok("Thủ kho không tạo được lô nhập (API)", lo(U["kho"], "ton_dau_ky", "x\ty")[0] == 403)
    ok("Thủ quỹ không gọi được Kiểm tra / Ghi lô (API)", U["thu_chi"].lam("nhap_lo:ghi", 1)[0] in (400, 403))
    kh0 = ad.tao("khach_hang", {"ma": k + "-K0", "ten": "Khách GL 0"})
    dv = {x["ma"]: x for x in ad.ds("don_vi", {})}
    ok("Nhân viên bán tạo công nợ đầu kỳ qua API: bị chặn",
       U["ban_hang"].call("don_ban:create", {"loai": "dau_ky", "khach_id": kh0["id"], "don_vi_ban_id": dv["APH"]["id"], "tong_tien": 1000})[0] >= 400)
    ok("Quản trị cũng không tạo nợ đầu kỳ ngoài Go-Live",
       ad.call("don_ban:create", {"loai": "dau_ky", "khach_id": kh0["id"], "don_vi_ban_id": dv["APH"]["id"], "tong_tien": 1000})[0] >= 400)
    ok("Thủ quỹ tạo phiếu thu đầu kỳ qua API: bị chặn",
       U["thu_chi"].call("phieu_thu:create", {"dau_ky": True, "don_vi_id": dv["APH"]["id"], "so_tien": 1000})[0] >= 400)

    # ---- Danh mục: preview, không ghi đè mặc định, quỹ có mã đơn vị ----
    _, r = chay("kho", f"Mã kho\tTên kho\tLoại kho\tKho đang vận chuyển\n{k}-HN\tKho Hà Nội GL\tBán được\t\n{k}-PT\tNhà máy Phú Thọ GL\tNhà máy\t\n"
                       f"{k}-XL\tChờ xử lý GL\tChờ xử lý\t\n{k}-VC\tĐang vận chuyển GL\tBán được\tx")
    ok("Danh mục kho: kiểm tra 4 dòng hợp lệ (chưa ghi gì)", r.get("hop_le") == 4 and not ad.ds("kho", {"ma": k + "-HN"}), r)
    lid = ad.ds("nhap_lo", {"loai": "kho"})[-1]["id"]
    ok("Ghi khi chưa duyệt: bị chặn", kt.lam("nhap_lo:ghi", lid)[0] == 400)
    kt.lam("nhap_lo:duyet", lid)
    kt.lam("nhap_lo:ghi", lid)
    KHO = {x["ma"]: x for x in ad.ds("kho", {"ma": {"$startsWith": k}})}
    ok("Ghi lô danh mục kho: đủ 4 kho, kho đang vận chuyển đúng cờ", len(KHO) == 4 and KHO[k + "-VC"]["trung_chuyen"] is True)
    _, r = chay("mat_hang", f"Mã hàng\tTên hàng\tĐVT tồn\tKg/bao\tGiá bán\n{k}-DX\tĐỗ xanh GL\tKg\t25\t40000\n{k}-TH\tThùng carton GL\tCái\t\t\n"
                            f"{k}-NL\tĐỗ nguyên liệu GL\tKg\t50\t\n{k}-TP\tĐỗ thành phẩm GL\tKg\t\t42000\n{k}-PP\tVỏ đỗ GL\tKg\t\t")
    lid = ad.ds("nhap_lo", {"loai": "mat_hang"})[-1]["id"]
    kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    MH = {x["ma"]: x for x in ad.ds("mat_hang", {"ma": {"$startsWith": k}})}
    ok("Danh mục hàng: thùng ĐVT Cái", MH[k + "-TH"]["dvt_ton"] == "cai" and len(MH) == 5)
    _, r = chay("mat_hang", f"Mã hàng\tTên hàng\tGiá bán\n{k}-DX\tĐỗ xanh GL (tên mới)\t45000")
    ok("Dán lại mã đã có: mặc định KHÔNG ghi đè (báo trùng, chỉ ra trường khác)", r.get("trung") == 1 and r.get("hop_le") == 0)
    _, r = chay("quy", f"Mã quỹ\tTên quỹ\tĐơn vị\tLoại\n{k}-TM\tTiền mặt APH GL\tAPH\tTiền mặt\n{k}-NH\tMB APH GL\tAPH\tNgân hàng\n{k}-NG\tSai đơn vị\tXYZ\tTiền mặt")
    ok("Danh mục quỹ đọc mã đơn vị (APH); mã sai báo lỗi dòng", r.get("hop_le") == 2 and r.get("loi") == 1, r)
    lid = ad.ds("nhap_lo", {"loai": "quy"})[-1]["id"]
    ok("Còn dòng lỗi: không duyệt được", kt.lam("nhap_lo:duyet", lid)[0] == 400)
    kt.call("nhap_lo:update", {"du_lieu_goc": f"Mã quỹ\tTên quỹ\tĐơn vị\tLoại\n{k}-TM\tTiền mặt APH GL\tAPH\tTiền mặt\n{k}-NH\tMB APH GL\tAPH\tNgân hàng"}, q=f"?filterByTk={lid}")
    kt.lam("nhap_lo:kiem", lid); kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    Q = {x["ma"]: x for x in ad.ds("quy", {"ma": {"$startsWith": k}})}
    ok("Quỹ ghi đúng đơn vị APH", Q[k + "-NH"]["don_vi_id"] == dv["APH"]["id"] and Q[k + "-TM"]["loai"] == "tien_mat")
    _, r = chay("khach_hang", f"Mã khách\tTên khách\tĐiện thoại\n{k}-KA\tKhách A GL\t0901\n{k}-KB\tKhách B GL\t0902")
    lid = ad.ds("nhap_lo", {"loai": "khach_hang"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    _, r = chay("nha_cung_cap", f"Mã NCC\tTên NCC\n{k}-N1\tNCC GL 1")
    lid = ad.ds("nhap_lo", {"loai": "nha_cung_cap"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    KH = {x["ma"]: x for x in ad.ds("khach_hang", {"ma": {"$startsWith": k}})}
    NCC = ad.ds("nha_cung_cap", {"ma": k + "-N1"})[0]

    def ton(kho, mh):
        r = ad.ds("ton_kho", {"kho_id": KHO[kho]["id"], "mat_hang_id": MH[mh]["id"]})
        return r[0] if r else {"so_kg": 0, "so_cho_gia": 0}

    def gv(kho, mh):
        r = ad.ds("gia_von", {"kho_id": KHO[kho]["id"], "mat_hang_id": MH[mh]["id"]})
        return r[0] if r else {"so_kg": 0, "gia_tri": 0}

    # ---- Tồn đầu kỳ (điều kiện 1, 2) ----
    TON = (f"Mã kho\tMã hàng\tSố lượng\tSố bao\tGiá trị\tTình trạng giá\tTình trạng hàng\n"
           f"{k}-HN\t{k}-DX\t1.000\t40\t30.000.000\tĐã chốt\tBán được\n"
           f"{k}-PT\t{k}-NL\t2000\t40\t40.000.000\tTạm tính\tBán được\n"
           f"{k}-PT\t{k}-TH\t500\t\t2.500.000\tĐã chốt\t\n"
           f"{k}-HN\t{k}-TP\t20\t\t\tChưa xác định\tBán được\n"
           f"{k}-XL\t{k}-DX\t5\t\t100.000\tĐã chốt\tChờ xử lý\n"
           f"{k}-VC\t{k}-DX\t75\t3\t2.250.000\tĐã chốt\tĐang vận chuyển\n"
           f"{k}-HN\t{k}-PP\t10\t\t0\tĐã chốt\tBán được")
    lid, r = chay("ton_dau_ky", TON, "Kiểm kê 25-10.xlsx / tab Tồn")
    ok("Tồn đầu kỳ: dòng giá 0 'đã chốt' bị chặn (không dùng giá 0)", r.get("loi") == 1 and r.get("hop_le") == 6, r)
    TON = TON.rsplit("\n", 1)[0]
    kt.call("nhap_lo:update", {"du_lieu_goc": TON}, q=f"?filterByTk={lid}")
    s, r = kt.lam("nhap_lo:kiem", lid)
    if "data" not in r:
        print("KIEM LOI", s, str(r)[:800])
    tk = r["data"]["tong_kiem"]
    ok("Xem trước có tổng đối chiếu theo kho (file / hệ thống trước)", tk["file"][k + "-HN"]["so_luong"] == 1020 and tk["truoc"][k + "-HN"]["so_luong"] == 0, tk)
    kt.lam("nhap_lo:duyet", lid)
    s, r = kt.lam("nhap_lo:ghi", lid)
    ok("Ghi tồn đầu kỳ: 6 dòng, tổng sau = tổng file", s == 200 and r["data"]["tong_kiem"]["sau"][k + "-HN"]["so_luong"] == 1020, r)
    ok("Tồn & giá trị khớp bảng kiểm kê (theo kho × mã, không chia đơn vị)",
       ton(k + "-HN", k + "-DX")["so_kg"] == 1000 and gv(k + "-HN", k + "-DX")["gia_tri"] == 30000000
       and gv(k + "-PT", k + "-NL")["gia_tri"] == 40000000 and ton(k + "-PT", k + "-TH")["so_kg"] == 500)
    ok("Hàng chưa xác định giá: có tồn nhưng chờ định giá, không vào giá trị",
       ton(k + "-HN", k + "-TP")["so_cho_gia"] == 20 and gv(k + "-HN", k + "-TP").get("gia_tri", 0) == 0)
    dongNL = [x for x in ad.ds("phieu_kho_dong", {"mat_hang_id": MH[k + "-NL"]["id"]})]
    ok("Giá tạm được ghi trạng thái 'tạm' (không phải đã chốt)", dongNL and dongNL[0]["trang_thai_gia"] == "tam")
    lid2, r = chay("ton_dau_ky", TON, "dán lại lần 2")
    ok("ĐK1 — Dán lại cùng file: mọi dòng là TRÙNG, không có dòng ghi được", r.get("trung") == 6 and r.get("hop_le") == 0, r)
    ok("ĐK1 — Không duyệt được lô toàn dòng trùng", kt.lam("nhap_lo:duyet", lid2)[0] == 400)
    pk = ad.tao("phieu_kho", {"loai": "dau_ky", "kho_id": KHO[k + "-HN"]["id"], "dong": [{"mat_hang_id": MH[k + "-DX"]["id"], "so_kg": 1000, "don_gia": 30000}]})
    ok("ĐK1 — Lập tay phiếu tồn đầu kỳ trùng mã × kho: bị chặn", ad.lam("phieu_kho:ghiSo", pk["id"])[0] == 400 and ton(k + "-HN", k + "-DX")["so_kg"] == 1000)
    pk = U["kho"].tao("phieu_kho", {"loai": "dau_ky", "kho_id": KHO[k + "-HN"]["id"], "dong": [{"mat_hang_id": MH[k + "-NL"]["id"], "so_kg": 5}]})
    ok("ĐK5 — Thủ kho tự ghi phiếu tồn đầu kỳ: bị chặn", U["kho"].lam("phieu_kho:ghiSo", pk["id"])[0] == 400)
    ok("Tổng tồn sau mở sổ bằng tổng file (không nhân đôi)", ton(k + "-HN", k + "-DX")["so_kg"] == 1000 and ton(k + "-VC", k + "-DX")["so_kg"] == 75)

    # Giá tạm → giá chính thức
    pkNL = ad.lay("phieu_kho", dongNL[0]["phieu_kho_id"], "dong")
    kt.lam("phieu_kho:dinhGia", pkNL["id"], {"gia": {str(dongNL[0]["id"]): 20500}})
    ok("Giá tạm 20.000 → chốt 20.500: chỉ điều chỉnh giá trị (+1.000.000), số lượng giữ nguyên",
       gv(k + "-PT", k + "-NL")["gia_tri"] == 41000000 and ton(k + "-PT", k + "-NL")["so_kg"] == 2000)

    # ---- Công nợ đầu kỳ (ĐK3) ----
    NO = (f"Mã khách\tĐơn vị\tSố dư\tChứng từ gốc\tNgày phát sinh\tHạn thanh toán\tĐối chiếu\n"
          f"{k}-KA\tAPH\t12.000.000\tHĐ 101\t01/09/2026\t30/10/2026\tĐã đối chiếu\n"
          f"{k}-KA\tAPH\t3.000.000\tHĐ 102\t15/09/2026\t\tChờ đối chiếu\n"
          f"{k}-KA\tVH\t5.000.000\tHĐ VH-7\t20/09/2026\t\tChờ đối chiếu\n"
          f"{k}-KB\tTL\t8.000.000\t\t\t\t")
    lid, r = chay("no_khach", NO)
    kt.lam("nhap_lo:duyet", lid); s, r = kt.lam("nhap_lo:ghi", lid)
    if "data" not in r:
        print("GHI LOI", s, r)
    tk = r["data"]["tong_kiem"]
    ok("ĐK3 — Nợ khách theo đúng đơn vị: APH 15tr, VH 5tr, TL 8tr (kể cả khoản chờ đối chiếu)",
       tk["sau"]["APH"]["gia_tri"] - tk["truoc"]["APH"]["gia_tri"] == 15000000 and tk["sau"]["VH"]["gia_tri"] - tk["truoc"]["VH"]["gia_tri"] == 5000000
       and tk["sau"]["TL"]["gia_tri"] - tk["truoc"]["TL"]["gia_tri"] == 8000000, tk)
    noKA = ad.ds("don_ban", {"khach_id": KH[k + "-KA"]["id"], "loai": "dau_ky"})
    ok("Một khách nhiều khoản nợ, lưu chứng từ gốc / hạn / đối chiếu", len(noKA) == 3 and any(x["han_tt"] == "2026-10-30" and x["doi_chieu"] == "da" for x in noKA))
    lid2, r = chay("no_khach", NO)
    ok("ĐK1 — Dán lại nợ khách: toàn bộ trùng", r.get("trung") == 4 and r.get("hop_le") == 0)
    _, r = chay("no_ncc", f"Mã NCC\tĐơn vị\tSố dư\tChứng từ gốc\n{k}-N1\tAPH\t20.000.000\tPN cũ 55\n{k}-N1\tVH\t4.000.000\tPN cũ 56")
    lid = ad.ds("nhap_lo", {"loai": "no_ncc"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    noN = {x["don_vi_id"]: x for x in ad.ds("no_ncc_dau_ky", {"nha_cung_cap_id": NCC["id"]})}
    ok("ĐK3 — Nợ NCC đầu kỳ (không tạo phiếu nhập giả, kho không đổi)", len(noN) == 2 and not ad.ds("phieu_kho", {"nha_cung_cap_id": NCC["id"]}))
    ok("Không tạo tay nợ NCC đầu kỳ ngoài Go-Live", ad.call("no_ncc_dau_ky:create", {"nha_cung_cap_id": NCC["id"], "don_vi_id": dv["APH"]["id"], "so_tien": 1})[0] >= 400)

    # ---- Tiền đầu kỳ (ĐK4) ----
    _, r = chay("tien_chua_pb", f"Mã quỹ\tLoại\tSố tiền\tMã tham chiếu\tMã khách\n{k}-NH\tCọc\t10.000.000\tFT-C1\t{k}-KA")
    ok("Tiền chưa phân bổ khi quỹ chưa có số dư: cảnh báo đếm đôi", bool(r.get("tong_kiem", {}).get("canh_bao")), r.get("tong_kiem"))
    kt.lam("nhap_lo:huy", ad.ds("nhap_lo", {"loai": "tien_chua_pb"})[-1]["id"])
    _, r = chay("quy_dau_ky", f"Mã quỹ\tSố dư\tGhi chú\n{k}-NH\t300.000.000\tSao kê MB 25/10\n{k}-TM\t15.000.000\tBiên bản kiểm quỹ")
    lid = ad.ds("nhap_lo", {"loai": "quy_dau_ky"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    _, r = chay("tien_chua_pb", f"Mã quỹ\tLoại\tSố tiền\tMã tham chiếu\tMã khách\tMục đích cọc\n"
                                f"{k}-NH\tCọc\t10.000.000\tFT-C1\t{k}-KA\tGiữ 1 tấn tháng 11\n{k}-NH\tChưa rõ\t30.000.000\tFT-X9\t\t")
    lid = ad.ds("nhap_lo", {"loai": "tien_chua_pb"})[-1]["id"]
    ok("Quỹ đã có số dư: không cảnh báo", not r.get("tong_kiem", {}).get("canh_bao"), r.get("tong_kiem"))
    kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    du = lambda q: sum(x["so_tien"] for x in ad.ds("so_quy", {"quy_id": Q[q]["id"]}))
    ptdk = ad.ds("phieu_thu", {"quy_id": Q[k + "-NH"]["id"], "dau_ky": True})
    ok("ĐK4 — Số dư MB vẫn 300tr (cọc + chưa rõ 40tr KHÔNG cộng thêm), 40tr nằm ở chưa phân bổ",
       du(k + "-NH") == 300000000 and sum(x["chua_phan_bo"] for x in ptdk) == 40000000)
    _, r = chay("quy_dau_ky", f"Mã quỹ\tSố dư\n{k}-NH\t300.000.000")
    ok("ĐK1 — Dán lại số dư quỹ: trùng", r.get("trung") == 1 or r.get("loi") == 1)
    _, r = chay("thu_ho_dau_ky", f"Đơn vị giữ tiền\tĐơn vị được trả\tSố tiền\tMã tham chiếu\tGhi chú\nAPH\tTL\t6.000.000\tTH-OLD-1\tKhách chuyển nhầm tháng 9")
    lid = ad.ds("nhap_lo", {"loai": "thu_ho_dau_ky"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    ok("Thu hộ còn giữ đầu kỳ: khoản APH giữ hộ TL, không đụng số dư quỹ",
       any(x["so_tien"] == 6000000 and x["trang_thai"] == "dang_giu_ho" for x in ad.ds("thu_ho", {"ma_tham_chieu": "TH-OLD-1"})) and du(k + "-NH") == 300000000)

    # Dùng số dư đầu kỳ sau Go-Live
    cr = [x for x in ptdk if x["loai_thu"] == "chua_ro"][0]
    U["thu_chi"].lam("phieu_thu:nhanDien", cr["id"], {"khach_id": KH[k + "-KA"]["id"]})
    s, r = U["thu_chi"].lam("phieu_thu:phanBo", cr["id"], {"phan_bo": [{"don_ban_id": [x for x in noKA if x["chung_tu_goc"] == "HĐ 101"][0]["id"], "so_tien": 12000000}]})
    ok("Tiền chưa rõ đầu kỳ → nhận diện → trả khoản nợ đầu kỳ HĐ 101 (đúng đơn vị APH)", s == 200 and
       ad.ds("don_ban", {"chung_tu_goc": "HĐ 101", "khach_id": KH[k + "-KA"]["id"]})[0]["con_no"] == 0, r)
    s, r = U["thu_chi"].lam("phieu_thu:phanBo", cr["id"], {"phan_bo": [{"don_ban_id": [x for x in noKA if x["chung_tu_goc"] == "HĐ VH-7"][0]["id"], "so_tien": 1000}]})
    ok("Tiền APH không tự trả nợ đầu kỳ của VH", s == 400)
    pc = ad.tao("phieu_chi", {"don_vi_id": dv["APH"]["id"], "quy_id": Q[k + "-NH"]["id"], "nguoi_nhan": "NCC GL", "so_tien": 5000000, "ly_do": "Trả nợ cũ",
                              "ma_gd": "UNC1", "nha_cung_cap_id": NCC["id"], "no_ncc_dau_ky_id": noN[dv["VH"]["id"]]["id"]})
    ok("APH không trả hộ nợ NCC đầu kỳ của VH", ad.lam("phieu_chi:ghi", pc["id"])[0] == 400)
    pc = ad.tao("phieu_chi", {"don_vi_id": dv["APH"]["id"], "quy_id": Q[k + "-NH"]["id"], "nguoi_nhan": "NCC GL", "so_tien": 25000000, "ly_do": "Trả nợ cũ",
                              "ma_gd": "UNC2", "nha_cung_cap_id": NCC["id"], "no_ncc_dau_ky_id": noN[dv["APH"]["id"]]["id"]})
    ok("Trả quá nợ NCC đầu kỳ: bị chặn", ad.lam("phieu_chi:ghi", pc["id"])[0] == 400)
    pc = ad.tao("phieu_chi", {"don_vi_id": dv["APH"]["id"], "quy_id": Q[k + "-NH"]["id"], "nguoi_nhan": "NCC GL", "so_tien": 8000000, "ly_do": "Trả nợ cũ",
                              "ma_gd": "UNC3", "nha_cung_cap_id": NCC["id"], "no_ncc_dau_ky_id": noN[dv["APH"]["id"]]["id"]})
    ad.lam("phieu_chi:ghi", pc["id"])
    ok("Trả 8tr nợ NCC đầu kỳ: còn 12tr, MB còn 292tr",
       ad.lay("no_ncc_dau_ky", noN[dv["APH"]["id"]]["id"])["da_tra"] == 8000000 and du(k + "-NH") == 292000000)

    # ---- Đơn chuyển tiếp ----
    DON = (f"Số đơn cũ\tMã khách\tĐơn vị bán\tMã hàng\tMã kho\tSố lượng còn giao\tĐơn giá\tTình trạng\n"
           f"SO-OLD-1\t{k}-KA\tAPH\t{k}-DX\t{k}-HN\t300\t40000\tChưa giao\n"
           f"SO-OLD-2\t{k}-KB\tTL\t{k}-DX\t{k}-HN\t75\t41000\tĐang vận chuyển")
    _, r = chay("don_chuyen_tiep", DON)
    lid = ad.ds("nhap_lo", {"loai": "don_chuyen_tiep"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    d1 = ad.ds("don_ban", {"so_don_cu": "SO-OLD-1"})[0]
    d2 = ad.ds("don_ban", {"so_don_cu": "SO-OLD-2"})[0]
    ok("Đơn chưa giao chuyển sang: đã chốt, chưa trừ kho, chưa ghi nợ", d1["trang_thai"] == "cho_xuat" and d1["phai_thu"] == 0 and ton(k + "-HN", k + "-DX")["so_kg"] == 1000)
    ok("Đơn đang vận chuyển: lượt 'đã bàn giao xe', ghi nợ 3.075.000, KHÔNG trừ kho lần nữa",
       d2["phai_thu"] == 3075000 and ton(k + "-HN", k + "-DX")["so_kg"] == 1000 and ad.ds("luot_giao", {"don_ban_id": d2["id"]})[0]["trang_thai"] == "da_ban_giao_xe")
    l2 = ad.ds("luot_giao", {"don_ban_id": d2["id"]})[0]
    U["kho"].lam("luot_giao:khachNhan", l2["id"])
    ok("Khách nhận đơn đang vận chuyển: không trừ kho", ton(k + "-HN", k + "-DX")["so_kg"] == 1000)
    _, r = chay("don_chuyen_tiep", DON)
    ok("ĐK1 — Dán lại đơn chuyển tiếp: trùng", r.get("hop_le") == 0)
    dx = ad.tao("don_ban", {"khach_id": KH[k + "-KA"]["id"], "don_vi_ban_id": dv["APH"]["id"], "dong": [{"mat_hang_id": MH[k + "-DX"]["id"], "kho_id": KHO[k + "-XL"]["id"], "so_kg": 5, "don_gia": 1}]})
    ad.lam("don_ban:chotDon", dx["id"])
    dxd = ad.lay("don_ban", dx["id"], "dong")["dong"][0]["id"]
    ok("Không xuất bán từ kho chờ xử lý / đang vận chuyển",
       ad.lam("luot_giao:taoLuot", None, {"don_ban_id": dx["id"], "dong": [{"don_ban_dong_id": dxd, "so_kg": 5}]})[0] == 400)

    # ---- Khóa kỳ (ĐK5 tiếp) ----
    ok("Thủ quỹ không khóa được kỳ", U["thu_chi"].lam("ky_mo_so:khoa", ky["id"])[0] in (400, 403))
    kt.lam("ky_mo_so:khoa", ky["id"], {"bo_qua_lo_dang_do": True})
    _, lid, _ = lo(kt, "quy_dau_ky", f"Mã quỹ\tSố dư\n{k}-TM\t1")
    ok("Sau khóa kỳ: không kiểm / ghi số dư đầu kỳ được nữa", kt.lam("nhap_lo:kiem", lid)[0] == 400)
    pk = ad.tao("phieu_kho", {"loai": "dau_ky", "kho_id": KHO[k + "-HN"]["id"], "dong": [{"mat_hang_id": MH[k + "-NL"]["id"], "so_kg": 1, "don_gia": 1}]})
    ok("Sau khóa kỳ: quản trị cũng không ghi tồn đầu kỳ tay", ad.lam("phieu_kho:ghiSo", pk["id"])[0] == 400)
    l = ad.lay("nhap_lo", ad.ds("nhap_lo", {"loai": "ton_dau_ky", "trang_thai": "da_ghi"})[-1]["id"], "dong")
    ok("ĐK6 — Truy được nguồn: lô lưu tên file, dữ liệu gốc, người nhập / duyệt / ghi, từng dòng → chứng từ",
       l["nguon"] and l["du_lieu_goc"] and l["nguoi_duyet"] and l["ghi_boi"] and all(x["ket_qua"] for x in l["dong"] if x["trang_thai"] == "da_ghi"))
    ok("Người ngoài kế toán không đọc được lô nhập", U["kho"].call("nhap_lo:list")[0] == 403)

    # ---- TÀI SẢN ----
    _, r = chay("tai_san", f"Mã tài sản\tTên tài sản\tLoại\tĐịa điểm\tNgười quản lý\tNgày mua\tNguyên giá\tSố tháng sử dụng\tDùng cho sản xuất\tĐơn vị đứng tên\n"
                           f"{k}-MS\tMáy sàng GL\tTSCĐ\tNhà máy Phú Thọ\tAnh Tổ trưởng\t01/01/2026\t120.000.000\t60\tx\tAPH\n"
                           f"{k}-CAN\tCân 100kg GL\tCCDC\tKho HN\t\t\t3.000.000\t\t\t")
    lid = ad.ds("nhap_lo", {"loai": "tai_san"})[-1]["id"]; kt.lam("nhap_lo:duyet", lid); kt.lam("nhap_lo:ghi", lid)
    ts = ad.ds("tai_san", {"ma": k + "-MS"})[0]
    ok("Nhập danh mục tài sản (đơn vị đứng tên tùy chọn)", ts["don_vi_so_huu_id"] == dv["APH"]["id"] and ad.ds("tai_san", {"ma": k + "-CAN"})[0]["don_vi_so_huu_id"] is None)
    ok("Sửa tay người giữ tài sản: bị chặn (phải qua sự kiện)", ad.call("tai_san:update", {"nguoi_quan_ly": "X"}, q=f"?filterByTk={ts['id']}")[0] == 400)
    e = U["nha_may"].tao("tai_san_su_kien", {"tai_san_id": ts["id"], "loai": "ban_giao", "nguoi_nhan": "Chị Ca 2", "dia_diem_moi": "Xưởng 2"})
    U["nha_may"].lam("tai_san_su_kien:ghi", e["id"])
    ts2 = ad.lay("tai_san", ts["id"])
    ok("Nhà máy bàn giao máy: người giữ / địa điểm cập nhật, có lịch sử", ts2["nguoi_quan_ly"] == "Chị Ca 2" and ts2["dia_diem"] == "Xưởng 2")
    e = U["nha_may"].tao("tai_san_su_kien", {"tai_san_id": ts["id"], "loai": "thanh_ly"})
    ok("Thanh lý khi chưa có đề nghị / không phải kế toán: bị chặn", U["nha_may"].lam("tai_san_su_kien:ghi", e["id"])[0] == 400)
    e2 = U["nha_may"].tao("tai_san_su_kien", {"tai_san_id": ts["id"], "loai": "de_nghi_thanh_ly", "ghi_chu": "Hỏng mô tơ"})
    U["nha_may"].lam("tai_san_su_kien:ghi", e2["id"])
    ok("Nhà máy vẫn không tự thanh lý sau đề nghị", U["nha_may"].lam("tai_san_su_kien:ghi", e["id"])[0] == 400)
    e3 = kt.tao("tai_san_su_kien", {"tai_san_id": ts["id"], "loai": "thanh_ly", "ghi_chu": "Duyệt BB 12"})
    s, _ = kt.lam("tai_san_su_kien:ghi", e3["id"])
    ok("Kế toán duyệt thanh lý", s == 200 and ad.lay("tai_san", ts["id"])["tinh_trang"] == "da_thanh_ly")
    ok("Nhà máy không thấy nguyên giá", "nguyen_gia" not in U["nha_may"].lay("tai_san", ts["id"]))
    s, r = kt.call("tai_san:uocTinh", {"thang": "2026-10"})
    ok("Chi phí sử dụng tài sản ước tính (quản trị) theo tháng", s == 200 and isinstance(r["data"], list), r)

    # ---- MẺ SẢN XUẤT ----
    nm = U["nha_may"]
    me = nm.tao("me_sx", {"kho_id": KHO[k + "-PT"]["id"], "kho_tp_id": KHO[k + "-HN"]["id"], "xuong": "Tổ 1", "san_pham_du_kien": "Đỗ thành phẩm"})
    c1 = nm.tao("phieu_kho", {"loai": "cap_nvl", "kho_id": KHO[k + "-PT"]["id"], "me_sx_id": me["id"], "dong": [
        {"mat_hang_id": MH[k + "-NL"]["id"], "so_kg": 1000}, {"mat_hang_id": MH[k + "-TH"]["id"], "so_kg": 100}]})
    s, r = nm.lam("phieu_kho:ghiSo", c1["id"])
    ok("Nhà máy cấp 1.000 kg NVL + 100 thùng (Cái) cho mẻ", s == 200 and ton(k + "-PT", k + "-NL")["so_kg"] == 1000 and ton(k + "-PT", k + "-TH")["so_kg"] == 400, r)
    t1 = nm.tao("phieu_kho", {"loai": "thu_hoi", "kho_id": KHO[k + "-PT"]["id"], "me_sx_id": me["id"], "dong": [
        {"mat_hang_id": MH[k + "-TP"]["id"], "huong": "ra", "so_kg": 400}, {"mat_hang_id": MH[k + "-PP"]["id"], "huong": "phu_pham", "so_kg": 100, "don_gia": 2000}]})
    s, r = nm.lam("phieu_kho:ghiSo", t1["id"])
    ok("Ngày 1 thu hồi 400 kg (mẻ còn dở dang), vào kho thành phẩm với giá TẠM", s == 200 and ton(k + "-HN", k + "-TP")["so_kg"] == 420, r)
    t2 = nm.tao("phieu_kho", {"loai": "thu_hoi", "kho_id": KHO[k + "-PT"]["id"], "me_sx_id": me["id"], "dong": [
        {"mat_hang_id": MH[k + "-TP"]["id"], "huong": "ra", "so_kg": 420},
        {"mat_hang_id": MH[k + "-NL"]["id"], "huong": "hao_hut", "loai_hao": "tu_nhien", "so_kg": 20},
        {"mat_hang_id": MH[k + "-NL"]["id"], "huong": "hao_hut", "loai_hao": "bat_thuong", "so_kg": 60}]})
    ok("Hao hụt bất thường không ghi nguyên nhân: bị chặn", nm.lam("phieu_kho:ghiSo", t2["id"])[0] == 400)
    nm.call("phieu_kho:update", {"ghi_chu": "Mất điện, 60 kg hỏng"}, q=f"?filterByTk={t2['id']}")
    nm.lam("phieu_kho:ghiSo", t2["id"])
    ok("Nhà máy không ghi được chi phí mẻ", nm.call("me_sx_chi_phi:create", {"me_sx_id": me["id"], "loai": "dien", "so_tien": 1})[0] == 403)
    kt.tao("me_sx_chi_phi", {"me_sx_id": me["id"], "loai": "nhan_cong", "so_tien": 1200000, "ky": "2026-10"})
    kt.tao("me_sx_chi_phi", {"me_sx_id": me["id"], "loai": "dien", "so_tien": 600000, "ky": "2026-10"})
    mn = nm.lay("me_sx", me["id"])
    ok("Nhà máy đọc mẻ: thấy kg, không thấy giá trị / chi phí / giá thành",
       mn.get("kg_tp") == 820 and not any(x in mn for x in ("gia_tri_nvl", "chi_phi", "gia_thanh", "tong_phan_bo")), mn)
    ok("Nhà máy gọi API chốt giá thành: bị chặn", nm.lam("me_sx:chot", me["id"])[0] in (400, 403))
    s, r = kt.lam("me_sx:chot", me["id"], {"do_dang_cuoi": 0})
    nvl, bb, cp, pp = 41000000 / 2000 * 1000, 500000, 1800000, 200000
    goc = nvl + bb + cp - pp
    bt = round(goc * 60 / 880)
    pb = goc - bt
    ok(f"Chốt v1: (NVL 20,5tr + thùng 0,5tr + CP 1,8tr − PP 0,2tr) − hao bất thường {bt:,} = {pb:,.0f}", s == 200 and abs(r["data"]["tong_phan_bo"] - pb) <= 1, r)
    ok("Giá trị thành phẩm trong kho = phân bổ (giá tạm đã được điều chỉnh)", abs(gv(k + "-HN", k + "-TP")["gia_tri"] - pb) <= 1, gv(k + "-HN", k + "-TP"))
    kt.tao("me_sx_chi_phi", {"me_sx_id": me["id"], "loai": "chung", "so_tien": 880000, "ky": "2026-10", "ghi_chu": "Phân bổ chi phí chung cuối tháng"})
    ok("Chi phí đến sau → mẻ 'cần chốt lại'", ad.lay("me_sx", me["id"])["trang_thai"] == "can_chot_lai")
    s, r = kt.lam("me_sx:chot", me["id"], {"do_dang_cuoi": 500000, "kg_do_dang": 20})
    goc2 = goc + 880000 - 500000
    pb2 = goc2 - round(goc2 * 60 / 880)
    ok("Chốt v2 (thêm 880.000 chi phí, dở dang cuối 500.000): điều chỉnh đúng phần chênh, giữ phiên bản 1",
       s == 200 and r["data"]["phien_ban"] == 2 and abs(r["data"]["dieu_chinh"] - (pb2 - pb)) <= 2 and abs(gv(k + "-HN", k + "-TP")["gia_tri"] - pb2) <= 2
       and len(ad.ds("me_sx_phien_ban", {"me_sx_id": me["id"]})) == 2, r)
    s, r = kt.lam("me_sx:chot", me["id"], {"gia_phu_pham": {str([x for x in ad.lay("phieu_kho", t1["id"], "dong")["dong"] if x["huong"] == "phu_pham"][0]["id"]): 3000}})
    goc3 = goc2 - 100000
    pb3 = goc3 - round(goc3 * 60 / 880)
    ok("Chốt v3: chỉnh giá phụ phẩm 2.000 → 3.000 làm giảm giá thành tương ứng", s == 200 and abs(r["data"]["tong_phan_bo"] - pb3) <= 2, r)
    ok("Hủy mẻ đã có phiếu: bị chặn", kt.lam("me_sx:huy", me["id"])[0] == 400)

    loi = [x for x in KQ if not x[1]]
    print(f"\nTỔNG {len(KQ)} ca, LỖI {len(loi)}")
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
