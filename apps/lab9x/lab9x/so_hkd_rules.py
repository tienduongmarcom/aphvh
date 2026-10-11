"""Sổ doanh thu hộ kinh doanh theo Thông tư 152/2025/TT-BTC (0.4.5) — quy tắc thuần, kiểm thử không cần Frappe.

- S1a-HKD: hộ không phải nộp thuế — ngày, diễn giải, số tiền; dòng tổng.
- S2a-HKD: nộp GTGT và TNCN theo tỷ lệ % doanh thu — chi tiết theo nhóm ngành nghề cùng tỷ lệ;
  mỗi ngành: cộng doanh thu, thuế GTGT, thuế TNCN; cuối sổ: tổng thuế GTGT, tổng thuế TNCN phải nộp.
- S2b-HKD: GTGT theo tỷ lệ %, TNCN theo thu nhập — như S2a nhưng chỉ dòng thuế GTGT.

Tỷ lệ theo Nghị định 68/2026/NĐ-CP (kế toán trưởng xác nhận). Thuế TNCN theo tỷ lệ chỉ tính trên phần doanh thu năm
vượt 500 triệu đồng: sổ ghi số TNCN theo tỷ lệ trên doanh thu trong kỳ để tham khảo, kế toán trừ phần ngưỡng khi kê khai.
"""

NGANH_MAC_DINH = "Phân phối, cung cấp hàng hóa"
# (tên ngành, tỷ lệ GTGT %, tỷ lệ TNCN %)
NGANH = (
    (NGANH_MAC_DINH, 1.0, 0.5),
    ("Sản xuất, vận tải, dịch vụ có gắn với hàng hóa, xây dựng có bao thầu nguyên vật liệu", 3.0, 1.5),
    ("Dịch vụ, xây dựng không bao thầu nguyên vật liệu", 5.0, 2.0),
    ("Hoạt động kinh doanh khác", 2.0, 1.0),
)
TY_LE = {n: (g, t) for n, g, t in NGANH}
NGUONG_TNCN_NAM = 500_000_000
MAU = {
    "S1a-HKD": "SỔ DOANH THU BÁN HÀNG HÓA, DỊCH VỤ",
    "S2a-HKD": "SỔ DOANH THU BÁN HÀNG HÓA, DỊCH VỤ",
    "S2b-HKD": "SỔ DOANH THU BÁN HÀNG HÓA, DỊCH VỤ",
}


def _r(x):
    return round(float(x or 0))


def dong_so(mau: str, dong: list) -> list:
    """dong: [{"ngay", "so", "dien_giai", "nganh", "so_tien"}] (đã theo thứ tự ngày) -> các dòng sổ.

    Mỗi dòng ra: {"kieu": "ct" | "nganh" | "cong" | "gtgt" | "tncn" | "tong" | "tong_gtgt" | "tong_tncn", ...}.
    """
    if mau not in MAU:
        raise ValueError(f"Mẫu sổ không hỗ trợ: {mau}")
    out = []
    if mau == "S1a-HKD":
        tong = 0.0
        for d in dong or []:
            out.append({"kieu": "ct", "ngay": d.get("ngay"), "so": d.get("so"), "dien_giai": d.get("dien_giai"), "so_tien": _r(d.get("so_tien"))})
            tong += float(d.get("so_tien") or 0)
        out.append({"kieu": "tong", "dien_giai": "Tổng cộng", "so_tien": _r(tong)})
        return out

    theo_nganh: dict = {}
    for d in dong or []:
        theo_nganh.setdefault(d.get("nganh") or NGANH_MAC_DINH, []).append(d)
    thu_tu = [n for n, _, _ in NGANH if n in theo_nganh] + [n for n in theo_nganh if n not in TY_LE]
    tong_gtgt = tong_tncn = 0.0
    for i, n in enumerate(thu_tu, 1):
        g, t = TY_LE.get(n, (0.0, 0.0))
        out.append({"kieu": "nganh", "dien_giai": f"{i}. Ngành nghề: {n}", "ty_le_gtgt": g, "ty_le_tncn": t})
        cong = 0.0
        for d in theo_nganh[n]:
            out.append({"kieu": "ct", "ngay": d.get("ngay"), "so": d.get("so"), "dien_giai": d.get("dien_giai"), "so_tien": _r(d.get("so_tien"))})
            cong += float(d.get("so_tien") or 0)
        thue_g = cong * g / 100
        out.append({"kieu": "cong", "dien_giai": "Tổng cộng (1)", "so_tien": _r(cong)})
        out.append({"kieu": "gtgt", "dien_giai": f"Thuế GTGT ({_pt(g)} × (1))", "so_tien": _r(thue_g)})
        tong_gtgt += thue_g
        if mau == "S2a-HKD":
            thue_t = cong * t / 100
            out.append({"kieu": "tncn", "dien_giai": f"Thuế TNCN ({_pt(t)} × (1), trước khi trừ ngưỡng 500 triệu/năm)", "so_tien": _r(thue_t)})
            tong_tncn += thue_t
    out.append({"kieu": "tong_gtgt", "dien_giai": "Tổng số thuế GTGT phải nộp", "so_tien": _r(tong_gtgt)})
    if mau == "S2a-HKD":
        out.append({"kieu": "tong_tncn", "dien_giai": "Tổng số thuế TNCN phải nộp (tham khảo, chưa trừ ngưỡng)", "so_tien": _r(tong_tncn)})
    return out


def _pt(x) -> str:
    x = float(x)
    return (f"{int(x)}%" if x == int(x) else f"{x:g}%").replace(".", ",")


def tncn_sau_nguong(doanh_thu_nam: float, thue_ty_le: float) -> float:
    """TNCN theo tỷ lệ cả năm sau khi trừ ngưỡng: thuế × (DT năm − 500 tr) / DT năm (chia đều theo tỷ trọng)."""
    dt = float(doanh_thu_nam or 0)
    if dt <= NGUONG_TNCN_NAM:
        return 0.0
    return float(thue_ty_le or 0) * (dt - NGUONG_TNCN_NAM) / dt


# --- 0.4.6: hộ kinh doanh nộp thuế theo thu nhập (doanh thu > 3 tỷ; > 50 tỷ: TNCN 20%) — S2c, S2d, S2e ------------

THUE_SUAT_TNCN_MAC_DINH = 20.0  # doanh thu năm trên 50 tỷ (NĐ 68/2026); kế toán trưởng xác nhận


def dong_s2c(doanh_thu: list, chi_phi: list, thue_suat=THUE_SUAT_TNCN_MAC_DINH) -> list:
    """S2c-HKD. doanh_thu / chi_phi: [{"so", "ngay", "dien_giai", "so_tien"}].

    0.4.8: chi phí có "khong_hop_ly" (kế toán tích trên chứng từ) không vào mục (2), không trừ khi tính thuế;
    liệt kê riêng sau dòng thuế (kiểu "khl_*") để đối chiếu — bản in chính thức bỏ các dòng này.
    """
    out = [{"kieu": "muc", "dien_giai": "(1) Doanh thu bán hàng hóa, dịch vụ"}]
    dt = 0.0
    for d in doanh_thu or []:
        out.append(dict(d, kieu="ct", so_tien=_r(d.get("so_tien"))))
        dt += float(d.get("so_tien") or 0)
    out.append({"kieu": "cong", "dien_giai": "Cộng doanh thu (1)", "so_tien": _r(dt)})
    out.append({"kieu": "muc", "dien_giai": "(2) Chi phí hợp lý"})
    cp = 0.0
    loai = []
    for d in chi_phi or []:
        if d.get("khong_hop_ly"):
            loai.append(d)
            continue
        out.append(dict(d, kieu="ct", so_tien=_r(d.get("so_tien"))))
        cp += float(d.get("so_tien") or 0)
    out.append({"kieu": "cong", "dien_giai": "Cộng chi phí hợp lý (2)", "so_tien": _r(cp)})
    cl = dt - cp
    out.append({"kieu": "tong", "dien_giai": "(3) Chênh lệch = (1) − (2)", "so_tien": _r(cl)})
    out.append({"kieu": "tong", "dien_giai": f"(4) Thuế TNCN phải nộp = (3) × {_pt(thue_suat)}", "so_tien": _r(max(cl, 0) * float(thue_suat) / 100)})
    if loai:
        out.append({"kieu": "khl_muc", "dien_giai": "Chi phí không hợp lý — đã ghi sổ, không trừ khi tính thuế (đối chiếu)"})
        tong = 0.0
        for d in loai:
            ly_do = (d.get("ly_do") or "").strip()
            out.append(dict(d, kieu="khl_ct", so_tien=_r(d.get("so_tien")),
                            dien_giai=(d.get("dien_giai") or "") + (f" [Lý do: {ly_do}]" if ly_do else "")))
            tong += float(d.get("so_tien") or 0)
        out.append({"kieu": "khl_cong", "dien_giai": "Cộng chi phí không hợp lý", "so_tien": _r(tong)})
    return out


def dong_s2d(mat_hang: list) -> list:
    """S2d-HKD. mat_hang: [{"ma", "ten", "dvt", "ton_sl", "ton_tt", "ps": [{"so", "ngay", "dien_giai", "don_gia",
    "nhap_sl", "nhap_tt", "xuat_sl", "xuat_tt"}]}] -> từng mặt hàng: dòng tên, tồn đầu kỳ, phát sinh (tồn chạy), cộng."""
    out = []
    for m in mat_hang or []:
        sl, tt = float(m.get("ton_sl") or 0), float(m.get("ton_tt") or 0)
        ps = m.get("ps") or []
        if not ps and not sl and not tt:
            continue
        out.append({"kieu": "muc", "dien_giai": f"{m['ma']} – {m.get('ten') or ''}", "dvt": m.get("dvt")})
        out.append({"kieu": "dau_ky", "dien_giai": "Số dư đầu kỳ", "dvt": m.get("dvt"), "ton_sl": sl, "ton_tt": _r(tt)})
        c = {"nhap_sl": 0.0, "nhap_tt": 0.0, "xuat_sl": 0.0, "xuat_tt": 0.0}
        for p in ps:
            for k in c:
                c[k] += float(p.get(k) or 0)
            sl += float(p.get("nhap_sl") or 0) - float(p.get("xuat_sl") or 0)
            tt += float(p.get("nhap_tt") or 0) - float(p.get("xuat_tt") or 0)
            out.append(dict(p, kieu="ct", dvt=m.get("dvt"), nhap_tt=_r(p.get("nhap_tt")), xuat_tt=_r(p.get("xuat_tt")),
                            ton_sl=round(sl, 3), ton_tt=_r(tt)))
        out.append({"kieu": "cong", "dien_giai": "Cộng phát sinh / tồn cuối kỳ", "dvt": m.get("dvt"),
                    "nhap_sl": round(c["nhap_sl"], 3), "nhap_tt": _r(c["nhap_tt"]), "xuat_sl": round(c["xuat_sl"], 3),
                    "xuat_tt": _r(c["xuat_tt"]), "ton_sl": round(sl, 3), "ton_tt": _r(tt)})
    return out


def dong_s2e(tai_khoan: list) -> list:
    """S2e-HKD. tai_khoan: [{"ten", "dau_ky", "ps": [{"so", "ngay", "dien_giai", "thu", "chi"}]}] -> mỗi tài khoản tiền
    (tiền mặt, từng tài khoản ngân hàng): số dư đầu kỳ, thu, chi, tồn chạy, cộng và số dư cuối kỳ."""
    out = []
    for a in tai_khoan or []:
        du = float(a.get("dau_ky") or 0)
        ps = a.get("ps") or []
        if not ps and not du:
            continue
        out.append({"kieu": "muc", "dien_giai": a["ten"]})
        out.append({"kieu": "dau_ky", "dien_giai": "Số dư đầu kỳ", "ton": _r(du)})
        thu = chi = 0.0
        for p in ps:
            t, c = float(p.get("thu") or 0), float(p.get("chi") or 0)
            thu += t
            chi += c
            du += t - c
            out.append(dict(p, kieu="ct", thu=_r(t), chi=_r(c), ton=_r(du)))
        out.append({"kieu": "cong", "dien_giai": "Cộng phát sinh trong kỳ", "thu": _r(thu), "chi": _r(chi)})
        out.append({"kieu": "cuoi_ky", "dien_giai": "Số dư cuối kỳ", "ton": _r(du)})
    return out
