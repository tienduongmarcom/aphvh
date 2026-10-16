"""Quy tắc bán hàng dùng chung (thuần, không import frappe) — từ lab9x 0.2.4 / kh_aph 0.11.3.

- Giảm giá sau giao (R026, Q169–Q170): chia tổng tiền giảm theo tỷ trọng tiền dòng, tách phần thuế theo thuế suất dòng.
- Tài khoản ghi giảm trừ doanh thu: TT99 có 521; TT133 (và bộ HKD / nội bộ của 9xLab) không có 521 → ghi giảm thẳng 511.
- Hạn thanh toán chung của đơn (Q166–Q168).
- Trả hàng hai chiều (R025): hàng về đâu × xử lý tiền.
"""
import datetime

from lab9x.costing_rules import split_by_weight

HANG_BAN_LAI, HANG_CACH_LY = "Bán lại được", "Cách ly"
HANG_TRA_VE = (HANG_BAN_LAI, HANG_CACH_LY)
TIEN_BU_TRU, TIEN_HOAN, TIEN_DOI_HANG = "Bù trừ công nợ", "Hoàn tiền", "Đổi hàng"
XU_LY_TIEN = (TIEN_BU_TRU, TIEN_HOAN, TIEN_DOI_HANG)
TK_GIAM_TRU_TT99 = "521"


def chia_giam_gia(tong, dong, precision=0):
    """dong: [(khóa, tiền dòng chưa thuế, thuế suất %)]. `tong`: tổng tiền khách được giảm (gồm thuế của các dòng có thuế).

    Trả [(khóa, phần chưa thuế, phần thuế)], tổng đúng bằng `tong` đã làm tròn. Dòng tiền 0 không nhận phần nào.
    """
    tong = float(tong or 0)
    if tong <= 0:
        raise ValueError("Số tiền giảm phải lớn hơn 0")
    co = [(k, float(t or 0), float(ts or 0)) for k, t, ts in dong if float(t or 0) > 0]
    if not co:
        raise ValueError("Hóa đơn không có dòng nào để giảm")
    if any(ts < 0 for _k, _t, ts in co):
        raise ValueError("Thuế suất không được âm")
    gom_thue = [t * (1 + ts / 100) for _k, t, ts in co]
    if tong > sum(gom_thue) + 0.5:
        raise ValueError("Số tiền giảm lớn hơn tổng tiền hàng của hóa đơn")
    phan = split_by_weight(tong, gom_thue, precision)
    out = []
    for (k, _t, ts), p in zip(co, phan, strict=True):
        chua = round(p / (1 + ts / 100), precision)
        out.append((k, chua, round(p - chua, precision)))
    return out


def tk_giam_tru(so_hieu_la):
    """so_hieu_la: tập số hiệu tài khoản lá của công ty. Có 521 (TT99) → "521"; không có → None (ghi giảm TK doanh thu dòng)."""
    return TK_GIAM_TRU_TT99 if TK_GIAM_TRU_TT99 in set(so_hieu_la or ()) else None


def han_chung(ngay_don, so_ngay):
    """Hạn thanh toán chung = ngày xác nhận đơn + số ngày theo điều khoản; không có điều khoản → None."""
    if so_ngay is None:
        return None
    if isinstance(ngay_don, str):
        ngay_don = datetime.date.fromisoformat(ngay_don[:10])
    return ngay_don + datetime.timedelta(days=int(so_ngay))


def han_hoa_don(han_chung_don, ngay_giao):
    """Hóa đơn của một đợt giao lấy hạn chung; hạn chung sớm hơn ngày giao thì lấy ngày giao."""
    if han_chung_don is None:
        return None
    if isinstance(han_chung_don, str):
        han_chung_don = datetime.date.fromisoformat(han_chung_don[:10])
    if isinstance(ngay_giao, str):
        ngay_giao = datetime.date.fromisoformat(ngay_giao[:10])
    return max(han_chung_don, ngay_giao)


def kiem_tra_hang(loai_dieu_chinh_tra_hang, hang_tra_ve, xu_ly_tien):
    """Trả lỗi hoặc None. Chỉ phiếu trả loại "Khách trả hàng" mới cần hai ô."""
    if not loai_dieu_chinh_tra_hang:
        return None
    if hang_tra_ve not in HANG_TRA_VE:
        return "Chọn hàng trả về: " + " / ".join(HANG_TRA_VE)
    if xu_ly_tien not in XU_LY_TIEN:
        return "Chọn cách xử lý tiền: " + " / ".join(XU_LY_TIEN)
    return None
