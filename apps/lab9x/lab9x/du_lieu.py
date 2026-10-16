"""Quy tắc kiểm dữ liệu danh mục và đối chiếu số dư đầu kỳ (lõi 9xLab, dùng cho mọi khách). Phần thuần, không import frappe.

- Trung tâm dữ liệu (0.12.0): kiểm từng dòng đề nghị cập nhật số liệu, MST, kg tịnh, sản lượng lệch định mức.
- Số dư đầu kỳ (0.12.1): xếp trạng thái từng loại số dư khi so bảng nguồn với sổ.
"""
import re

LOI = "lỗi"          # lỗi cấu trúc: không cho gửi
CANH_BAO = "cảnh báo"  # lỗi số liệu: cho gửi, hiện cạnh dòng

MST_RE = re.compile(r"^\d{10}(-\d{3})?$")
SAI_SO_KG = 0.005       # 0,5%
NGUONG_LECH_SAN_LUONG = 0.20

LOAI_DAU_KY = ("Tồn kho", "Tiền mặt và ngân hàng", "Công nợ khách", "Công nợ nhà cung cấp")
CHUA_NAP, LECH, KHOP = "Chưa nạp", "Lệch", "Khớp"


def _so(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def kiem_mst(mst):
    """None nếu hợp lệ (hoặc để trống), ngược lại là câu báo."""
    if not mst:
        return None
    s = str(mst).strip().replace(" ", "")
    return None if MST_RE.match(s) else f"MST \"{mst}\" phải là 10 số hoặc 13 số dạng 10-3"


def nhom_trung_mst(dong):
    """dong: [(ten, cong_ty, mst)] -> [(cong_ty, mst, [ten...])] các MST xuất hiện ở hơn một đối tượng trong cùng công ty."""
    gom = {}
    for ten, cty, mst in dong:
        s = (mst or "").strip().replace(" ", "")
        if s:
            gom.setdefault((cty or "", s), []).append(ten)
    return [(c, m, sorted(t)) for (c, m), t in sorted(gom.items()) if len(t) > 1]


def kiem_kg_tinh(kg, so_goi=None, gram_moi_goi=None):
    """kg tịnh mỗi đơn vị > 0; nếu có số gói và gram mỗi gói thì kg = số gói × gram / 1000 (sai số 0,5%)."""
    v = _so(kg)
    if v is None or v <= 0:
        return LOI, "Kg tịnh phải là số lớn hơn 0"
    g, gr = _so(so_goi) or 0, _so(gram_moi_goi) or 0  # ô số để trống được lưu là 0: coi như không khai
    if g or gr:
        if g <= 0 or gr <= 0:
            return LOI, "Nhập cả số gói và gram mỗi gói (lớn hơn 0), hoặc để trống cả hai"
        dung = g * gr / 1000
        if abs(v - dung) > dung * SAI_SO_KG:
            return LOI, f"Kg tịnh {v:g} khác số gói × gram mỗi gói = {dung:g}"
    return None


def kiem_gia_tri(truong, gia_tri, so_goi=None, gram_moi_goi=None):
    """Kiểm một dòng đề nghị. Trả None hoặc (mức, câu báo)."""
    if truong == "kg_tinh":
        return kiem_kg_tinh(gia_tri, so_goi, gram_moi_goi)
    v = _so(gia_tri)
    if truong == "san_luong_me":
        return None if v is not None and v > 0 else (LOI, "Sản lượng mỗi mẻ phải lớn hơn 0")
    if truong == "hao_hut":
        if v is None or v < 0:
            return LOI, "Tỷ lệ hao hụt phải ≥ 0"
        return (CANH_BAO, "Hao hụt cho phép trên 10%: kiểm lại") if v > 10 else None
    if truong == "dinh_muc_mac_dinh":
        return None if str(gia_tri).strip() in ("1", "Có", "có") else (LOI, "Giá trị phải là 1 (đặt làm định mức mặc định)")
    return LOI, f"Trường \"{truong}\" không được sửa qua đề nghị"


def lech_san_luong(dinh_muc, thuc_te, nguong=NGUONG_LECH_SAN_LUONG):
    """Sản lượng thực tế bình quân lệch định mức quá ngưỡng (mặc định 20%)."""
    d, t = _so(dinh_muc), _so(thuc_te)
    if not d or d <= 0 or t is None:
        return False
    return abs(t - d) / d > nguong


def trang_thai_dau_ky(so_nguon, so_so, da_nhap_nguon=True, sai_so=1.0):
    """So số theo bảng nguồn với số trên sổ cho một loại số dư đầu kỳ."""
    if not so_so and not so_nguon:
        return CHUA_NAP
    if not da_nhap_nguon:
        return LECH if so_so else CHUA_NAP
    return KHOP if abs((so_nguon or 0) - (so_so or 0)) <= sai_so else LECH


def can_bang_tk_tam(so_du_tk_tam, tong_da_nap):
    """Tài khoản tạm đối ứng (dư Nợ dương) cộng tổng số dư đã nạp (Nợ dương) phải bằng 0: phần còn lại là phần chưa nạp."""
    return round((so_du_tk_tam or 0) + (tong_da_nap or 0), 2)
