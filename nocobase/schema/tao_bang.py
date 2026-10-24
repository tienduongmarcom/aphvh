#!/usr/bin/env python3
"""Tạo (hoặc bổ sung) các bảng dữ liệu NocoBase cho APH-VH qua API quản lý bảng.

Bảng tạo bằng API nên vẫn hiện và sửa được trong "Quản lý dữ liệu" của NocoBase.
Chạy lại an toàn: bảng/trường đã có thì bỏ qua (không xóa, không đổi).

    python3 tao_bang.py --url http://localhost:13000 --email admin@... --password ...
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


def opt(value, label, color=None):
    o = {"value": value, "label": label}
    if color:
        o["color"] = color
    return o


def input_(name, title, required=False, unique=False):
    f = {"name": name, "interface": "input", "type": "string",
         "uiSchema": {"type": "string", "title": title, "x-component": "Input"}}
    if required:
        f["uiSchema"]["required"] = True
    if unique:
        f["unique"] = True
    return f


def text(name, title):
    return {"name": name, "interface": "textarea", "type": "text",
            "uiSchema": {"type": "string", "title": title, "x-component": "Input.TextArea"}}


def number(name, title, precision=2, read_only=False):
    f = {"name": name, "interface": "number", "type": "double",
         "uiSchema": {"type": "number", "title": title, "x-component": "InputNumber",
                      "x-component-props": {"step": "1", "stringMode": True, "precision": precision}}}
    if read_only:
        f["uiSchema"]["x-read-pretty"] = True
    return f


def date(name, title):
    return {"name": name, "interface": "date", "type": "dateOnly",
            "uiSchema": {"type": "string", "title": title, "x-component": "DatePicker",
                         "x-component-props": {"dateOnly": True, "dateFormat": "DD/MM/YYYY"}}}


def check(name, title, default=False):
    return {"name": name, "interface": "checkbox", "type": "boolean", "defaultValue": default,
            "uiSchema": {"type": "boolean", "title": title, "x-component": "Checkbox"}}


def select(name, title, options, default=None):
    f = {"name": name, "interface": "select", "type": "string",
         "uiSchema": {"type": "string", "title": title, "x-component": "Select", "enum": options}}
    if default is not None:
        f["defaultValue"] = default
    return f


def m2o(name, title, target, label="nhan", required=False):
    f = {"name": name, "interface": "m2o", "type": "belongsTo", "target": target, "foreignKey": f"{name}_id",
         "onDelete": "RESTRICT",
         "uiSchema": {"title": title, "x-component": "AssociationField",
                      "x-component-props": {"multiple": False, "fieldNames": {"label": label, "value": "id"}}}}
    if required:
        f["uiSchema"]["required"] = True
    return f


def o2m(name, title, target, fk, label="id"):
    return {"name": name, "interface": "o2m", "type": "hasMany", "target": target, "foreignKey": fk,
            "onDelete": "CASCADE", "sortBy": "id",
            "uiSchema": {"title": title, "x-component": "AssociationField",
                         "x-component-props": {"multiple": True, "fieldNames": {"label": label, "value": "id"}}}}


def so_ct(prefix, key):
    """Số chứng từ tự tăng theo năm: <prefix>-YYYY-00001. Prefix không dùng 'APH' (quy ước chủ dự án)."""
    return {"name": "so", "interface": "sequence", "type": "sequence", "unique": True,
            "patterns": [{"type": "string", "options": {"value": f"{prefix}-"}},
                         {"type": "date", "options": {"format": "YYYY"}},
                         {"type": "string", "options": {"value": "-"}},
                         {"type": "integer", "options": {"digits": 5, "start": 1, "key": key, "cycle": "0 0 1 1 *"}}],
            "uiSchema": {"type": "string", "title": "Số", "x-component": "Input", "x-read-pretty": True}}


TRANG_THAI_PHIEU = [opt("nhap", "Nháp", "default"), opt("da_ghi", "Đã ghi", "green"), opt("da_huy", "Đã hủy", "red")]

BANG = [
    {"name": "don_vi", "title": "Đơn vị", "titleField": "nhan", "fields": [
        input_("ma", "Mã đơn vị", required=True, unique=True), input_("ten", "Tên đơn vị", required=True),
        input_("nhan", "Tên hiển thị"), input_("mst", "Mã số thuế"), text("dia_chi", "Địa chỉ"),
        input_("dien_thoai", "Điện thoại")]},
    {"name": "kho", "title": "Kho", "titleField": "nhan", "fields": [
        input_("ma", "Mã kho", required=True, unique=True), input_("ten", "Tên kho", required=True),
        input_("nhan", "Tên hiển thị"), check("trung_chuyen", "Kho hàng đang vận chuyển"),
        select("loai_kho", "Loại kho", [opt("ban_duoc", "Kho bán được"), opt("nha_may", "Kho nhà máy"), opt("cho_xu_ly", "Kho chờ xử lý (không bán)")], "ban_duoc"),
        input_("dia_diem", "Địa điểm"),
        check("ngung_dung", "Ngừng dùng"), text("ghi_chu", "Ghi chú")]},
    {"name": "mat_hang", "title": "Mặt hàng", "titleField": "nhan", "fields": [
        input_("ma", "Mã hàng", required=True, unique=True), input_("ten", "Tên hàng", required=True),
        input_("nhan", "Mã – tên"), input_("dvt", "Đơn vị tính"), number("kg_bao", "Kg/bao", 3),
        number("gia_ban", "Giá bán (đ/ĐVT)", 0), number("gia_san", "Giá sàn (đ/ĐVT)", 0), check("ngung_dung", "Ngừng dùng"),
        select("dvt_ton", "ĐVT tồn kho", [opt("kg", "Kg"), opt("cai", "Cái"), opt("goi", "Gói"), opt("bao", "Bao"), opt("thung", "Thùng")], "kg"),
        select("loai_hang", "Loại hàng", [opt("hang_hoa", "Hàng hóa"), opt("nguyen_lieu", "Nguyên liệu"), opt("thanh_pham", "Thành phẩm"),
                                          opt("phu_pham", "Phụ phẩm"), opt("bao_bi", "Bao bì / vật tư")], "hang_hoa")]},
    {"name": "khach_hang", "title": "Khách hàng", "titleField": "nhan", "fields": [
        input_("ma", "Mã khách", required=True, unique=True), input_("ten", "Tên khách", required=True),
        input_("nhan", "Tên – SĐT"), input_("sdt", "Điện thoại"), text("dia_chi", "Địa chỉ"),
        input_("mst", "Mã số thuế"), text("ghi_chu", "Ghi chú"), number("han_muc", "Hạn mức công nợ chung (đ, 0 = không giới hạn)", 0)]},
    {"name": "nha_cung_cap", "title": "Nhà cung cấp", "titleField": "nhan", "fields": [
        input_("ma", "Mã NCC", required=True, unique=True), input_("ten", "Tên nhà cung cấp", required=True),
        input_("nhan", "Tên – SĐT"), input_("sdt", "Điện thoại"), text("dia_chi", "Địa chỉ"), input_("mst", "Mã số thuế"), text("ghi_chu", "Ghi chú")]},
    {"name": "phieu_kho", "title": "Phiếu kho", "titleField": "so", "fields": [
        so_ct("PK", 1),
        select("loai", "Loại phiếu", [opt("nhap", "Nhập kho"), opt("xuat", "Xuất kho khác"), opt("chuyen", "Chuyển kho"),
                                       opt("dau_ky", "Tồn đầu kỳ"), opt("kiem_ke", "Điều chỉnh kiểm kê"),
                                       opt("san_xuat", "Sản xuất"), opt("dong_goi", "Đóng gói / đổi bao")], "nhap"),
        date("ngay", "Ngày"), m2o("kho", "Kho", "kho", required=True), m2o("kho_dich", "Kho nhận (chuyển kho)", "kho"),
        input_("nguoi_giao_nhan", "Người giao / nhận"), text("ghi_chu", "Ghi chú"),
        select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"),
        input_("ghi_boi", "Người ghi sổ"), input_("ly_do_huy", "Lý do hủy"),
        number("chi_phi_sx", "Chi phí sản xuất (nhân công, điện, bao bì…)", 0), input_("xuong", "Xưởng / tổ"),
        number("gia_tri_nvl", "Giá trị nguyên liệu", 0, read_only=True), number("kg_vao", "Kg nguyên liệu", 3, read_only=True),
        number("kg_ra", "Kg thành phẩm", 3, read_only=True), number("gia_thanh", "Giá thành (đ/kg)", 0, read_only=True),
        m2o("nha_cung_cap", "Nhà cung cấp", "nha_cung_cap"), input_("chung_tu_ncc", "Số hóa đơn / phiếu của NCC"),
        number("phai_tra", "Phải trả NCC", 0, read_only=True), number("da_tra", "Đã trả NCC", 0, read_only=True),
        input_("request_id", "Mã yêu cầu", unique=True)]},
    {"name": "phieu_kho_dong", "title": "Dòng phiếu kho", "fields": [
        m2o("mat_hang", "Mặt hàng", "mat_hang", required=True), input_("ten_hang", "Tên hàng"),
        number("so_bao", "Số bao", 2), number("so_kg", "Số kg (âm = giảm khi kiểm kê)", 3), text("ghi_chu", "Ghi chú"),
        select("huong", "Vào / ra (sản xuất)", [opt("vao", "Nguyên liệu vào"), opt("ra", "Thành phẩm ra"), opt("phu_pham", "Phụ phẩm ra")]),
        number("don_gia", "Đơn giá (đ/kg)", 0),
        select("trang_thai_gia", "Tình trạng giá", [opt("co_gia", "Đã có giá"), opt("cho_gia", "Chờ định giá")]),
        input_("dinh_gia_boi", "Người định giá")]},
    {"name": "so_kho", "title": "Sổ kho", "titleField": "chung_tu", "fields": [
        date("ngay", "Ngày"), m2o("kho", "Kho", "kho"), m2o("mat_hang", "Mặt hàng", "mat_hang"),
        number("so_kg", "Số kg (+ nhập / − xuất)", 3), number("so_bao", "Số bao (+/−)", 2),
        input_("loai", "Nghiệp vụ"), input_("chung_tu", "Chứng từ"), input_("nguon", "Bảng nguồn"),
        {"name": "nguon_id", "interface": "integer", "type": "bigInt",
         "uiSchema": {"type": "number", "title": "Mã dòng nguồn", "x-component": "InputNumber"}}]},
    {"name": "ton_kho", "title": "Tồn kho", "fields": [
        m2o("kho", "Kho", "kho"), m2o("mat_hang", "Mặt hàng", "mat_hang"),
        number("so_kg", "Tồn vật lý", 3, read_only=True), number("so_bao", "Tồn (bao)", 2, read_only=True),
        number("so_giu", "Đang giữ cho lượt giao", 3, read_only=True), number("so_cho_gia", "Chờ định giá", 3, read_only=True)]},
    {"name": "don_ban", "title": "Đơn bán", "titleField": "so", "fields": [
        so_ct("DB", 2),
        select("loai", "Loại", [opt("ban", "Bán hàng"), opt("dau_ky", "Công nợ đầu kỳ")], "ban"),
        date("ngay", "Ngày đặt"), date("ngay_giao", "Ngày giao dự kiến"),
        m2o("khach", "Khách hàng", "khach_hang", required=True), input_("sdt", "Điện thoại khách"),
        text("dia_chi_giao", "Địa chỉ giao"), m2o("don_vi_ban", "Đơn vị bán", "don_vi", required=True),
        select("cach_giao", "Cách giao", [opt("khach_den_lay", "Khách đến lấy"), opt("van_chuyen", "Vận chuyển")],
               "khach_den_lay"),
        input_("nguoi_nhan", "Người nhận / lái xe"), input_("bien_so", "Biển số xe"),
        select("trang_thai", "Trạng thái", [opt("nhap", "Nháp", "default"), opt("cho_duyet", "Chờ duyệt", "purple"), opt("cho_xuat", "Đã chốt – chờ giao", "orange"),
                                            opt("dang_giao", "Giao một phần", "blue"), opt("da_giao", "Đã giao đủ", "green"), opt("da_dong", "Đóng phần chưa giao", "cyan"),
                                            opt("da_huy", "Đã hủy", "red")], "nhap"),
        number("tong_tien", "Tổng tiền", 0, read_only=True), number("da_thu", "Đã thu", 0, read_only=True),
        number("con_no", "Còn nợ", 0, read_only=True), input_("giao_boi", "Người xác nhận giao"),
        input_("ly_do_huy", "Lý do hủy"), text("ghi_chu", "Ghi chú"),
        input_("duyet_boi", "Người duyệt giá"), input_("ly_do_gia", "Lý do bán dưới giá sàn"),
        number("gia_von", "Giá vốn hàng bán", 0, read_only=True),
        number("phai_thu", "Phải thu (đã giao − trả − giảm)", 0, read_only=True), number("gia_tri_giao", "Giá trị đã giao", 0, read_only=True),
        number("gia_tri_tra", "Giá trị hàng trả", 0, read_only=True), number("giam_gia", "Giảm giá sau bán", 0, read_only=True),
        input_("ly_do_duyet", "Cần duyệt vì"), check("xuat_hoa_don", "Xuất hóa đơn GTGT (MISA)"),
        select("trang_thai_hd", "Hóa đơn", [opt("khong", "Không xuất"), opt("cho_xuat", "Chờ xuất HĐ"), opt("da_xuat", "Đã xuất HĐ")], "khong"),
        input_("so_hoa_don", "Số hóa đơn"), input_("ky_hieu_hd", "Ký hiệu HĐ"), date("ngay_hd", "Ngày hóa đơn"),
        input_("request_id", "Mã yêu cầu", unique=True)]},
    {"name": "don_ban_dong", "title": "Dòng đơn bán", "fields": [
        m2o("mat_hang", "Mã hàng", "mat_hang", label="ma", required=True), input_("ten_hang", "Tên hàng"),
        m2o("kho", "Kho xuất", "kho", required=True), number("so_bao", "Số bao", 2), number("so_kg", "Số kg", 3),
        number("don_gia", "Đơn giá (đ/kg)", 0), number("thanh_tien", "Thành tiền", 0, read_only=True),
        number("da_giao", "Đã giao", 3, read_only=True), number("da_tra", "Đã trả lại", 3, read_only=True),
        number("dang_giu", "Đang giữ (lượt chưa giao)", 3, read_only=True), number("gia_von_da_giao", "Giá vốn đã giao", 0, read_only=True)]},
    {"name": "phieu_thu", "title": "Phiếu thu", "titleField": "so", "fields": [
        so_ct("PT", 3), date("ngay", "Ngày thu"), m2o("khach", "Khách hàng (trống = chưa rõ người nộp)", "khach_hang"),
        m2o("don_vi", "Đơn vị nhận tiền", "don_vi", required=True),
        select("hinh_thuc", "Hình thức", [opt("tien_mat", "Tiền mặt"), opt("chuyen_khoan", "Chuyển khoản")], "tien_mat"),
        number("so_tien", "Số tiền thực nhận", 0), input_("ma_gd", "Mã giao dịch / nội dung CK"),
        input_("nguoi_nop", "Người nộp"), number("chua_phan_bo", "Chưa phân bổ", 0, read_only=True),
        m2o("quy", "Quỹ / tài khoản nhận", "quy"),
        select("loai_thu", "Loại tiền", [opt("thu_no", "Khách trả nợ / trả đơn"), opt("coc", "Đặt cọc"), opt("chua_ro", "Chưa rõ người nộp")], "thu_no"),
        input_("muc_dich_coc", "Mục đích cọc"), input_("request_id", "Mã yêu cầu", unique=True),
        select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"), input_("ghi_boi", "Người ghi"),
        input_("ly_do_huy", "Lý do hủy"), text("ghi_chu", "Ghi chú")]},
    {"name": "phieu_thu_phan_bo", "title": "Phân bổ phiếu thu", "fields": [
        m2o("don_ban", "Đơn bán", "don_ban", label="so", required=True), number("so_tien", "Số tiền trả cho đơn", 0),
        check("thu_ho", "Thu hộ đơn vị khác"), input_("phan_bo_boi", "Người phân bổ"), date("ngay_phan_bo", "Ngày phân bổ")]},
]

BANG += [
    {"name": "quy", "title": "Quỹ / tài khoản tiền", "titleField": "nhan", "fields": [
        input_("ma", "Mã quỹ", required=True, unique=True), input_("ten", "Tên quỹ / tài khoản", required=True),
        input_("nhan", "Tên hiển thị"), m2o("don_vi", "Đơn vị", "don_vi", required=True),
        select("loai", "Loại", [opt("tien_mat", "Tiền mặt"), opt("ngan_hang", "Ngân hàng")], "tien_mat"),
        input_("nguoi_giu", "Người giữ quỹ"), check("ngung_dung", "Ngừng dùng")]},
    {"name": "so_quy", "title": "Sổ quỹ", "titleField": "chung_tu", "fields": [
        date("ngay", "Ngày"), m2o("quy", "Quỹ", "quy"), number("so_tien", "Số tiền (+ thu / − chi)", 0),
        input_("loai", "Nghiệp vụ"), input_("chung_tu", "Chứng từ"), text("dien_giai", "Diễn giải")]},
    {"name": "phieu_chi", "title": "Phiếu chi", "titleField": "so", "fields": [
        so_ct("PC", 4), date("ngay", "Ngày chi"), m2o("don_vi", "Đơn vị chi", "don_vi", required=True),
        m2o("quy", "Chi từ quỹ / tài khoản", "quy", required=True),
        select("loai_chi", "Loại chi", [opt("mua_hang", "Trả tiền mua hàng"), opt("van_chuyen", "Vận chuyển"), opt("san_xuat", "Chi phí sản xuất"),
                                        opt("luong", "Lương / công"), opt("hoan_khach", "Hoàn tiền khách"), opt("khac", "Chi khác")], "khac"),
        input_("nguoi_nhan", "Người nhận tiền", required=True), number("so_tien", "Số tiền", 0), text("ly_do", "Lý do chi"),
        input_("ma_gd", "Mã giao dịch (nếu chuyển khoản)"), select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"),
        input_("ghi_boi", "Người ghi"), input_("ly_do_huy", "Lý do hủy"),
        m2o("nha_cung_cap", "Nhà cung cấp", "nha_cung_cap"), m2o("phieu_kho", "Trả cho phiếu nhập", "phieu_kho", label="so"),
        input_("request_id", "Mã yêu cầu", unique=True)]},
    {"name": "chuyen_tien", "title": "Chuyển / bàn giao tiền", "titleField": "so", "fields": [
        so_ct("CT", 5), date("ngay", "Ngày"), m2o("tu_quy", "Từ quỹ", "quy", required=True), m2o("den_quy", "Đến quỹ", "quy", required=True),
        number("so_tien", "Số tiền", 0), input_("nguoi_giao", "Người giao"), input_("nguoi_nhan", "Người nhận"), text("ghi_chu", "Ghi chú"),
        select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"), input_("ghi_boi", "Người ghi"), input_("ly_do_huy", "Lý do hủy")]},
    {"name": "chot_ca", "title": "Chốt ca tiền", "titleField": "so", "fields": [
        so_ct("CC", 6), date("ngay", "Ngày"), m2o("quy", "Quỹ tiền mặt", "quy", required=True),
        number("so_sach", "Số theo sổ", 0, read_only=True), number("thuc_dem", "Tiền thực đếm", 0),
        number("chenh_lech", "Chênh lệch (đếm − sổ)", 0, read_only=True), text("ly_do", "Lý do chênh lệch"),
        input_("nguoi_chot", "Người chốt")]},
    {"name": "gia_von", "title": "Giá vốn bình quân", "fields": [
        m2o("mat_hang", "Mặt hàng", "mat_hang"), m2o("kho", "Kho", "kho"), number("so_kg", "Tồn có giá", 3, read_only=True),
        number("gia_tri", "Tổng giá trị", 0, read_only=True), number("gia_bq", "Giá bình quân (đ/kg)", 2, read_only=True)]},
    {"name": "so_gia_von", "title": "Sổ giá trị kho", "titleField": "chung_tu", "fields": [
        date("ngay", "Ngày"), m2o("mat_hang", "Mặt hàng", "mat_hang"), m2o("kho", "Kho", "kho"), number("so_kg", "Số lượng", 3), number("gia_tri", "Giá trị (+/−)", 0),
        number("gia_bq_sau", "Giá BQ sau", 2), input_("loai", "Nghiệp vụ"), input_("chung_tu", "Chứng từ")]},
]

TT_LUOT = [opt("cho_xuat", "Chờ xuất (đang giữ hàng)", "orange"), opt("da_ban_giao_xe", "Đã bàn giao xe", "blue"),
           opt("khach_da_nhan", "Khách đã nhận", "green"), opt("da_huy", "Đã hủy", "red")]
BANG += [
    {"name": "luot_giao", "title": "Lượt giao", "titleField": "so", "fields": [
        so_ct("LG", 7), m2o("don_ban", "Đơn bán", "don_ban", label="so", required=True), date("ngay", "Ngày"),
        select("cach_giao", "Cách giao", [opt("khach_den_lay", "Khách đến lấy"), opt("van_chuyen", "Vận chuyển")], "khach_den_lay"),
        input_("nguoi_nhan", "Người nhận / lái xe"), input_("bien_so", "Biển số xe"), input_("ben_van_chuyen", "Bên vận chuyển"),
        select("trang_thai", "Trạng thái", TT_LUOT, "cho_xuat"), number("gia_tri", "Giá trị lượt", 0, read_only=True),
        number("gia_von", "Giá vốn lượt", 0, read_only=True), input_("xuat_boi", "Người xác nhận xuất"), input_("nhan_xac_nhan_boi", "Người xác nhận khách nhận"),
        input_("ly_do_huy", "Lý do hủy"), input_("request_id", "Mã yêu cầu", unique=True)]},
    {"name": "luot_giao_dong", "title": "Dòng lượt giao", "fields": [
        m2o("don_ban_dong", "Dòng đơn", "don_ban_dong"), m2o("mat_hang", "Mặt hàng", "mat_hang"), m2o("kho", "Kho xuất", "kho"),
        number("so_kg", "Số lượng", 3), number("so_bao", "Số bao", 2), number("don_gia", "Đơn giá", 0), number("thanh_tien", "Thành tiền", 0),
        number("gia_von", "Giá vốn", 0)]},
    {"name": "tra_hang", "title": "Trả hàng", "titleField": "so", "fields": [
        so_ct("TH", 8), m2o("don_ban", "Đơn bán", "don_ban", label="so", required=True), date("ngay", "Ngày"),
        m2o("kho_nhan", "Kho nhận hàng trả", "kho", required=True), text("ly_do", "Lý do trả"),
        select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"), number("gia_tri", "Giá trị hàng trả", 0, read_only=True),
        input_("ghi_boi", "Người ghi"), input_("ly_do_huy", "Lý do hủy")]},
    {"name": "tra_hang_dong", "title": "Dòng trả hàng", "fields": [
        m2o("don_ban_dong", "Dòng đơn", "don_ban_dong"), m2o("mat_hang", "Mặt hàng", "mat_hang"), number("so_kg", "Số lượng trả", 3),
        number("don_gia", "Đơn giá", 0), number("thanh_tien", "Thành tiền", 0)]},
    {"name": "dieu_chinh_gia", "title": "Giảm giá sau bán", "titleField": "so", "fields": [
        so_ct("GG", 9), m2o("don_ban", "Đơn bán", "don_ban", label="so", required=True), date("ngay", "Ngày"),
        number("so_tien", "Số tiền giảm", 0), text("ly_do", "Lý do"), select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"),
        input_("ghi_boi", "Người ghi"), input_("ly_do_huy", "Lý do hủy")]},
    {"name": "thu_ho", "title": "Thu hộ giữa đơn vị", "fields": [
        m2o("phieu_thu", "Phiếu thu", "phieu_thu", label="so"), m2o("don_vi_nhan", "Đơn vị thực nhận tiền", "don_vi"),
        m2o("don_vi_chu_no", "Đơn vị có khoản phải thu", "don_vi"), m2o("don_ban", "Đơn được trả", "don_ban", label="so"),
        number("so_tien", "Số tiền", 0), select("trang_thai", "Trạng thái", [opt("dang_giu_ho", "Đang giữ hộ", "orange"), opt("da_tat_toan", "Đã tất toán", "green"),
        opt("da_huy", "Đã hủy", "red")], "dang_giu_ho"), input_("nguoi_phan_bo", "Người phân bổ"), text("ghi_chu", "Ghi chú")]},
]

# Quan hệ cha – con thêm sau khi các bảng đã có.
QUAN_HE = [
    ("phieu_kho", o2m("dong", "Hàng", "phieu_kho_dong", "phieu_kho_id")),
    ("phieu_kho_dong", m2o("phieu_kho", "Phiếu kho", "phieu_kho", label="so")),
    ("don_ban", o2m("dong", "Hàng bán", "don_ban_dong", "don_ban_id")),
    ("don_ban_dong", m2o("don_ban", "Đơn bán", "don_ban", label="so")),
    ("phieu_thu", o2m("phan_bo", "Trả cho đơn nào", "phieu_thu_phan_bo", "phieu_thu_id")),
    ("phieu_thu_phan_bo", m2o("phieu_thu", "Phiếu thu", "phieu_thu", label="so")),
    ("luot_giao", o2m("dong", "Hàng giao", "luot_giao_dong", "luot_giao_id")),
    ("luot_giao_dong", m2o("luot_giao", "Lượt giao", "luot_giao", label="so")),
    ("tra_hang", o2m("dong", "Hàng trả", "tra_hang_dong", "tra_hang_id")),
    ("tra_hang_dong", m2o("tra_hang", "Phiếu trả", "tra_hang", label="so")),
    ("don_ban", o2m("luot", "Các lượt giao", "luot_giao", "don_ban_id", label="so")),
]


class API:
    def __init__(self, url, email, password):
        self.url = url.rstrip("/")
        self.token = None
        r = self.call("auth:signIn", {"account": email, "password": password}, headers={"X-Authenticator": "basic"})
        self.token = r["data"]["token"]

    def call(self, action, body=None, params="", headers=None):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        h.update(headers or {})
        req = urllib.request.Request(f"{self.url}/api/{action}{params}", method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            raise SystemExit(f"Lỗi {action}: {e.code} {e.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:13000")
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    a = ap.parse_args()
    api = API(a.url, a.email, a.password)
    co = {c["name"]: c for c in api.call("collections:list", params="?paginate=false&appends=fields")["data"]}
    for b in BANG:
        if b["name"] in co:
            ten_truong = {f["name"] for f in co[b["name"]].get("fields") or []}
            co_truong = {f["name"]: f for f in co[b["name"]].get("fields") or []}
            for f in b["fields"]:
                if f["name"] not in ten_truong:
                    api.call(f"collections/{b['name']}/fields:create", f)
                    print(f"+ trường {b['name']}.{f['name']}")
                elif f.get("interface") == "select":
                    cu = (co_truong[f["name"]].get("uiSchema") or {}).get("enum") or []
                    if [o["value"] for o in cu] != [o["value"] for o in f["uiSchema"]["enum"]]:
                        api.call(f"collections/{b['name']}/fields:update", {"uiSchema": f["uiSchema"]},
                                 params=f"?filterByTk={f['name']}")
                        print(f"~ lựa chọn {b['name']}.{f['name']}")
            continue
        body = {"name": b["name"], "title": b["title"], "logging": True, "autoGenId": True, "createdBy": True,
                "updatedBy": True, "createdAt": True, "updatedAt": True, "sortable": True, "template": "general",
                "fields": b["fields"]}
        if b.get("titleField"):
            body["titleField"] = b["titleField"]
        api.call("collections:create", body)
        print(f"+ bảng {b['name']}")
    co = {c["name"]: c for c in api.call("collections:list", params="?paginate=false&appends=fields")["data"]}
    for bang, f in QUAN_HE:
        if f["name"] not in {x["name"] for x in co[bang].get("fields") or []}:
            api.call(f"collections/{bang}/fields:create", f)
            print(f"+ quan hệ {bang}.{f['name']}")
    print("Xong.")


if __name__ == "__main__":
    main()
