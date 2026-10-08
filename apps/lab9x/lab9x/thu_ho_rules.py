"""Bút toán thu hộ (0.4.20) — quy tắc thuần, kiểm thử không cần Frappe.

Khách lấy hàng của đơn vị chuyển tiếp (TL) nhưng chuyển tiền vào tài khoản VH hoặc APH:
- Kế toán lập bút toán thu hộ: Nợ tiền gửi (tiền mặt) / Có 3388 (tiền thu hộ), tích "Thu hộ", ghi khách, chủ hàng.
- Bút toán ở trạng thái "Cần xử lý" cho tới khi kế toán xử lý các nghiệp vụ phía sau (trên MISA) và ghi số chứng từ / ghi chú.
- App chỉ nhắc và liệt kê khoản chưa xử lý; không tự ghi sổ bên TL, không cân đối hóa đơn.
"""

TT_CAN_XU_LY = "Cần xử lý"
TT_DA_XU_LY = "Đã xử lý"
TRANG_THAI = (TT_CAN_XU_LY, TT_DA_XU_LY)
TEN_TK_THU_HO = "Tiền thu hộ đơn vị khác"  # tài khoản riêng dưới 3388, app tự tạo (tai_khoan_chuan)


def la_tk_thu_ho(so_tk, ten_tk) -> bool:
    """Chỉ nhận tài khoản riêng 'Tiền thu hộ đơn vị khác' (số hiệu bắt đầu 3388). Các tài khoản 3388 khác không tính."""
    return str(so_tk or "").strip().startswith("3388") and str(ten_tk or "").strip() == TEN_TK_THU_HO


def so_tien_thu_ho(dong) -> float:
    """dong: [{"so_tk","ten_tk","debit","credit"}] -> tổng (Có - Nợ) trên các tài khoản thu hộ."""
    return round(sum(float(d.get("credit") or 0) - float(d.get("debit") or 0)
                     for d in dong if la_tk_thu_ho(d.get("so_tk"), d.get("ten_tk"))), 2)


def kiem_tra(thu_ho, khach, chu_hang, so_tien, trang_thai, ghi_chu_xu_ly) -> dict:
    """-> {"loi": [..] (chặn lưu), "trang_thai": str | None}."""
    if not thu_ho:
        return {"loi": [], "trang_thai": None}
    loi = []
    if not khach:
        loi.append("Chọn khách hàng đã chuyển tiền.")
    if not (chu_hang or "").strip():
        loi.append("Ghi chủ hàng (đơn vị có hàng, ví dụ TL).")
    if float(so_tien or 0) <= 0:
        loi.append(f"Bút toán thu hộ phải có dòng Có tài khoản '{TEN_TK_THU_HO}' (dưới 3388).")
    tt = trang_thai if trang_thai in TRANG_THAI else TT_CAN_XU_LY
    if tt == TT_DA_XU_LY and not (ghi_chu_xu_ly or "").strip():
        loi.append("Ghi số chứng từ MISA hoặc ghi chú đã xử lý trước khi chuyển sang 'Đã xử lý'.")
    return {"loi": loi, "trang_thai": tt}


def so_ngay_cho(ngay, hom_nay) -> int:
    """Số ngày từ ngày ghi sổ tới hôm nay (không âm)."""
    return max((hom_nay - ngay).days, 0)
