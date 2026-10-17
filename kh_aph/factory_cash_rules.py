"""Phần thuần của kh_aph.factory_cash (không import frappe) để unit test."""

from lab9x.vn_words import so_vn
from kh_aph.funds_rules import money


LOAI_CHI = "Chi phí nhỏ"
LOAI_THU = "Thu tiền khách"
LOAI_BAN_GIAO = "Bàn giao tiền"
TT_GHI_SO, TT_CHO_NHAN, TT_DA_NHAN, TT_CHENH, TT_HUY = (
    "Đã ghi sổ", "Chờ nhận", "Đã nhận", "Chênh lệch chờ điều tra", "Đã hủy")
VAI_TRO_NHA_MAY = ("Kế toán nhà máy", "APH Không xem giá vốn")
VAI_TRO_KE_TOAN = ("Accounts User", "Accounts Manager", "System Manager", "Administrator")
SAI_SO_GIA = 0.5  # đồng


def kiem_phieu(loai, dong, customer=None, nguoi_nhan=None):
    """dong: [(diễn giải, khoản mục, số tiền)]. Trả danh sách lỗi (rỗng = hợp lệ)."""
    loi = []
    if loai not in (LOAI_CHI, LOAI_THU, LOAI_BAN_GIAO):
        loi.append("Loại phiếu không hợp lệ")
    if not dong:
        loi.append("Phiếu cần ít nhất một dòng")
    for i, (_dg, km, tien) in enumerate(dong, 1):
        try:
            if money(tien) <= 0:
                loi.append(f"Dòng {i}: số tiền phải lớn hơn 0")
        except ValueError:
            loi.append(f"Dòng {i}: số tiền không hợp lệ, cần hữu hạn và tối đa hai chữ số thập phân")
        if loai == LOAI_CHI and not km:
            loi.append(f"Dòng {i}: chọn khoản mục chi phí")
        if loai != LOAI_CHI and km:
            loi.append(f"Dòng {i}: khoản mục chỉ dùng cho phiếu chi phí nhỏ")
    if loai == LOAI_THU and not customer:
        loi.append("Thu tiền khách cần chọn khách")
    if loai == LOAI_BAN_GIAO and not nguoi_nhan:
        loi.append("Bàn giao tiền cần chọn người nhận")
    return loi


def trang_thai_nhan(tong, so_nhan):
    return TT_DA_NHAN if abs(float(tong or 0) - float(so_nhan or 0)) < 0.5 else TT_CHENH


def bi_khoa_gia(roles):
    roles = set(roles or ())
    return bool(roles & set(VAI_TRO_NHA_MAY)) and not roles & set(VAI_TRO_KE_TOAN)


def vi_pham_khoa_gia(dong):
    """dong: [(idx, mã, giá bán, giá bảng giá hoặc None, có khóa)]. Trả thông báo cho dòng sai."""
    loi = []
    for idx, ma, gia, gia_bang, khoa in dong:
        if not khoa:
            continue
        if gia_bang is None:
            loi.append(f"Dòng {idx} ({ma}): thành phẩm chính chưa có giá Hà Nội trên bảng giá; nhờ kế toán đặt giá")
        elif abs(float(gia or 0) - float(gia_bang)) > SAI_SO_GIA:
            loi.append(f"Dòng {idx} ({ma}): thành phẩm chính bán đúng giá Hà Nội chốt {so_vn(float(gia_bang), 0)}")
    return loi


