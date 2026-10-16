"""Phần thuần của kh_aph.sales_adjust (0.11.1) — không import frappe, để unit test."""

from lab9x.vn_words import so_vn

DC_TRA_HANG = "Khách trả hàng (R025)"
DC_CHO_VE = "Giao thiếu - hàng chở về kho (R022/R024)"
DC_MAT = "Giao thiếu - mất trên đường (R024)"
DC_SUA_SL = "Sửa sai số lượng (R024)"
LOAI_DIEU_CHINH = (DC_TRA_HANG, DC_CHO_VE, DC_MAT, DC_SUA_SL)
GIAO_THIEU = (DC_CHO_VE, DC_MAT)  # loại được trừ khi in "lượng thực nhận"


def kiem_dieu_chinh(doctype, is_return, update_stock, loai, theo_phieu_tra=False):
    """Trả thông báo lỗi hoặc None. Chứng từ trả lại/giảm phải có loại; loại phải hợp với việc có nhập kho hay không.

    theo_phieu_tra: hóa đơn giảm lập từ phiếu giao trả lại (kho đã nhập qua phiếu đó)."""
    if not is_return:
        return None
    if loai not in LOAI_DIEU_CHINH:
        return "Chọn loại điều chỉnh cho chứng từ trả lại / giảm"
    nhap_kho = doctype == "Delivery Note" or bool(update_stock) or bool(theo_phieu_tra)
    if loai == DC_MAT and nhap_kho:
        return "Hàng mất trên đường không nhập lại kho: lập hóa đơn giảm (không cập nhật kho)"
    if loai == DC_CHO_VE and not nhap_kho:
        return "Hàng chở về kho phải nhập lại kho: lập phiếu giao trả lại theo lượng thực chở về"
    return None


def canh_bao_gia_von(dong):
    """dong: [(idx, mã, giá bán theo ĐVT tồn kho, giá vốn bình quân)]. Chỉ gọi cho người được xem giá vốn."""
    return [f"Dòng {idx} ({ma}): giá bán {so_vn(float(gia), 0)} thấp hơn giá vốn bình quân hiện tại {so_vn(float(von), 0)}"
            for idx, ma, gia, von in dong if von and float(gia or 0) < float(von)]


def so_gon(x):
    return so_vn(float(x or 0))


def hien_thi_sl(qty, uom, stock_qty=None, stock_uom=None, bags=None):
    """R053/Q199: hàng có bao in "x bao (y kg)"; hàng bán theo thùng/hộp in kèm quy đổi ra đơn vị tồn kho."""
    qty = abs(float(qty or 0))
    if bags:
        return f"{so_gon(abs(float(bags)))} bao ({so_gon(qty)} {uom})"
    if stock_uom and uom and stock_uom != uom and stock_qty:
        return f"{so_gon(qty)} {uom} (= {so_gon(abs(float(stock_qty)))} {stock_uom})"
    return f"{so_gon(qty)} {uom or ''}".strip()
