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
