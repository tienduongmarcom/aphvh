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
                                       opt("san_xuat", "Sản xuất (một bước)"), opt("dong_goi", "Đóng gói / đổi bao"),
                                       opt("cap_nvl", "Cấp nguyên liệu cho mẻ"), opt("thu_hoi", "Thu hồi thành phẩm từ mẻ")], "nhap"),
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
        select("huong", "Vào / ra", [opt("vao", "Nguyên liệu / bao bì vào"), opt("ra", "Thành phẩm ra"), opt("phu_pham", "Phụ phẩm ra"),
                                     opt("hao_hut", "Hao hụt")]),
        number("don_gia", "Đơn giá (đ/kg)", 0),
        select("trang_thai_gia", "Tình trạng giá", [opt("co_gia", "Có giá"), opt("cho_gia", "Chờ định giá"), opt("tam", "Giá tạm được duyệt")]),
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
        select("trang_thai", "Trạng thái", [opt("nhap", "Nháp", "default"), opt("cho_xac_minh", "Chờ xác minh (chưa vào quỹ)", "gold"), opt("da_ghi", "Đã ghi", "green"), opt("da_huy", "Đã hủy", "red")], "nhap"), input_("ghi_boi", "Người ghi"),
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

# ---------------- 0.3.1: Go-Live & số dư đầu kỳ, tài sản, mẻ sản xuất ----------------
TT_LO = [opt("nhap", "Mới dán", "default"), opt("da_kiem", "Đã kiểm tra", "blue"), opt("da_duyet", "Đã duyệt", "purple"),
         opt("da_ghi", "Đã ghi sổ", "green"), opt("da_huy", "Đã hủy", "red")]
LOAI_LO = [opt("mat_hang", "Danh mục mặt hàng"), opt("khach_hang", "Danh mục khách hàng"), opt("nha_cung_cap", "Danh mục nhà cung cấp"),
           opt("kho", "Danh mục kho"), opt("quy", "Danh mục quỹ / tài khoản"), opt("ton_dau_ky", "Tồn kho đầu kỳ"),
           opt("no_khach", "Công nợ khách đầu kỳ"), opt("no_ncc", "Công nợ nhà cung cấp đầu kỳ"), opt("quy_dau_ky", "Số dư quỹ / ngân hàng đầu kỳ"),
           opt("tien_chua_pb", "Tiền cọc / chưa phân bổ đầu kỳ"), opt("thu_ho_dau_ky", "Thu hộ còn giữ đầu kỳ"),
           opt("don_chuyen_tiep", "Đơn chưa giao / đang vận chuyển"), opt("tai_san", "Danh mục tài sản / CCDC"),
           opt("quy_doi_dvt", "Quy đổi đơn vị tính"), opt("do_dang_dau_ky", "Dở dang sản xuất đầu kỳ")]
TT_GIA = [opt("co_gia", "Có giá"), opt("cho_gia", "Chờ định giá"), opt("tam", "Giá tạm được duyệt")]
BANG += [
    {"name": "ky_mo_so", "title": "Kỳ mở sổ", "titleField": "ma", "fields": [
        input_("ma", "Mã kỳ", required=True, unique=True), date("ngay_chot", "Ngày chốt số dư"),
        select("trang_thai", "Trạng thái", [opt("mo", "Đang mở sổ", "blue"), opt("da_khoa", "Đã khóa", "green")], "mo"),
        input_("khoa_boi", "Người khóa"), text("ghi_chu", "Ghi chú")]},
    {"name": "nhap_lo", "title": "Lô nhập dữ liệu", "titleField": "so", "fields": [
        so_ct("NL", 10), select("loai", "Loại dữ liệu", LOAI_LO), m2o("ky_mo_so", "Kỳ mở sổ", "ky_mo_so", label="ma"),
        input_("nguon", "Nguồn (tên file / link Google Sheet / tab)"), text("du_lieu_goc", "Dữ liệu gốc đã dán"),
        select("trang_thai", "Trạng thái", TT_LO, "nhap"), select("che_do", "Mã đã có", [opt("bo_qua", "Bỏ qua, không ghi đè"),
        opt("cap_nhat", "Cập nhật theo file")], "bo_qua"),
        number("so_dong", "Số dòng", 0, read_only=True), number("so_hop_le", "Hợp lệ", 0, read_only=True),
        number("so_loi", "Lỗi", 0, read_only=True), number("so_trung", "Trùng", 0, read_only=True),
        text("tong_kiem", "Tổng đối chiếu (trước / sau)"), input_("nguoi_nhap", "Người nhập"), input_("nguoi_duyet", "Người duyệt"),
        input_("ghi_boi", "Người ghi sổ"), text("ghi_chu", "Ghi chú")]},
    {"name": "nhap_dong", "title": "Dòng nhập dữ liệu", "fields": [
        m2o("nhap_lo", "Lô", "nhap_lo", label="so"), number("stt", "Dòng", 0), text("du_lieu", "Dữ liệu (JSON)"),
        input_("khoa_trung", "Khóa chống trùng"), select("trang_thai", "Trạng thái", [opt("hop_le", "Hợp lệ", "blue"), opt("loi", "Lỗi", "red"),
        opt("trung", "Trùng / đã có", "orange"), opt("da_ghi", "Đã ghi", "green"), opt("bo_qua", "Bỏ qua", "default")], "hop_le"),
        text("loi", "Lỗi / cảnh báo"), input_("ket_qua", "Chứng từ đã tạo")]},
    {"name": "mo_so_khoa", "title": "Khóa chống ghi trùng số dư", "fields": [
        input_("khoa", "Khóa", unique=True), m2o("nhap_lo", "Lô", "nhap_lo", label="so"), input_("ket_qua", "Chứng từ")]},
    {"name": "no_ncc_dau_ky", "title": "Công nợ NCC đầu kỳ", "titleField": "so", "fields": [
        so_ct("NO", 11), m2o("nha_cung_cap", "Nhà cung cấp", "nha_cung_cap", required=True), m2o("don_vi", "Đơn vị nợ", "don_vi", required=True),
        input_("chung_tu_goc", "Chứng từ gốc"), date("ngay_ct", "Ngày phát sinh"), date("han_tt", "Hạn thanh toán"),
        number("so_tien", "Số dư đầu kỳ", 0), number("da_tra", "Đã trả", 0, read_only=True),
        select("doi_chieu", "Đối chiếu", [opt("da", "Đã đối chiếu", "green"), opt("cho", "Chờ đối chiếu", "orange")], "cho"),
        select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "da_ghi"), m2o("nhap_lo", "Lô nhập", "nhap_lo", label="so"),
        input_("ly_do_huy", "Lý do hủy"), text("ghi_chu", "Ghi chú")]},
    {"name": "don_ban", "fields": [
        input_("chung_tu_goc", "Chứng từ gốc (nợ đầu kỳ)"), date("han_tt", "Hạn thanh toán"),
        select("doi_chieu", "Đối chiếu nợ đầu kỳ", [opt("da", "Đã đối chiếu", "green"), opt("cho", "Chờ đối chiếu", "orange")]),
        m2o("nhap_lo", "Lô nhập", "nhap_lo", label="so"), input_("so_don_cu", "Số đơn hệ thống cũ")]},
    {"name": "phieu_chi", "fields": [m2o("no_ncc_dau_ky", "Trả nợ NCC đầu kỳ", "no_ncc_dau_ky", label="so")]},
    {"name": "phieu_thu", "fields": [check("dau_ky", "Số dư đầu kỳ (tiền đã nằm trong số dư quỹ)"), m2o("nhap_lo", "Lô nhập", "nhap_lo", label="so"),
                                     input_("ma_tham_chieu", "Mã tham chiếu đầu kỳ")]},
    {"name": "thu_ho", "fields": [check("dau_ky", "Số dư đầu kỳ"), input_("ma_tham_chieu", "Mã tham chiếu")]},
    {"name": "phieu_kho", "fields": [
        select("loai", "Loại phiếu", [opt("nhap", "Nhập kho"), opt("xuat", "Xuất kho khác"), opt("chuyen", "Chuyển kho"),
                                       opt("dau_ky", "Tồn đầu kỳ"), opt("kiem_ke", "Điều chỉnh kiểm kê"),
                                       opt("san_xuat", "Sản xuất (một bước)"), opt("dong_goi", "Đóng gói / đổi bao"),
                                       opt("cap_nvl", "Cấp nguyên liệu cho mẻ"), opt("thu_hoi", "Thu hồi thành phẩm từ mẻ")], "nhap"),
        m2o("nhap_lo", "Lô nhập", "nhap_lo", label="so")]},
    {"name": "phieu_kho_dong", "fields": [
        select("trang_thai_gia", "Tình trạng giá", TT_GIA),
        select("huong", "Vào / ra", [opt("vao", "Nguyên liệu / bao bì vào"), opt("ra", "Thành phẩm ra"), opt("phu_pham", "Phụ phẩm ra"),
                                     opt("hao_hut", "Hao hụt")]),
        select("loai_hao", "Loại hao hụt", [opt("tu_nhien", "Tự nhiên (tính vào giá thành)"), opt("bat_thuong", "Bất thường (không tính vào giá thành)")]),
        number("he_so", "Hệ số phân bổ", 3), select("tinh_trang_hang", "Tình trạng hàng", [opt("ban_duoc", "Bán được"), opt("cho_xu_ly", "Chờ xử lý"),
                                                                                         opt("dang_van_chuyen", "Đang vận chuyển")])]},
    # Tài sản vận hành (MISA vẫn hạch toán, khấu hao chính thức)
    {"name": "tai_san", "title": "Tài sản / công cụ dụng cụ", "titleField": "nhan", "fields": [
        input_("ma", "Mã tài sản", required=True, unique=True), input_("ten", "Tên", required=True), input_("nhan", "Mã – tên"),
        select("loai", "Loại", [opt("tscd", "Tài sản cố định"), opt("ccdc", "Công cụ dụng cụ"), opt("van_phong", "Thiết bị văn phòng")], "tscd"),
        input_("serial", "Số serial"), input_("dia_diem", "Địa điểm"), input_("nguoi_quan_ly", "Người quản lý / đang giữ"), input_("bo_phan", "Bộ phận"),
        select("tinh_trang", "Tình trạng", [opt("dang_dung", "Đang dùng", "green"), opt("trong_kho", "Trong kho", "blue"), opt("hong", "Hỏng / chờ sửa", "orange"),
               opt("cho_thanh_ly", "Chờ thanh lý", "purple"), opt("da_thanh_ly", "Đã thanh lý", "default"), opt("mat", "Mất", "red")], "dang_dung"),
        date("ngay_mua", "Ngày mua"), number("nguyen_gia", "Nguyên giá tham khảo", 0), number("so_thang_sd", "Thời gian dùng ước tính (tháng)", 0),
        number("so_luong", "Số lượng (CCDC)", 0), m2o("don_vi_so_huu", "Đơn vị đứng tên chứng từ mua (nếu rõ)", "don_vi"),
        input_("chung_tu_mua", "Chứng từ mua"), check("dung_cho_san_xuat", "Dùng cho sản xuất (ước tính chi phí giá thành)"),
        date("ngay_bao_tri", "Ngày bảo trì kế tiếp"), text("ghi_chu", "Ghi chú")]},
    {"name": "tai_san_su_kien", "title": "Sự kiện tài sản", "titleField": "so", "fields": [
        so_ct("TS", 12), m2o("tai_san", "Tài sản", "tai_san", required=True), date("ngay", "Ngày"),
        select("loai", "Nghiệp vụ", [opt("ban_giao", "Bàn giao người giữ"), opt("dieu_chuyen", "Điều chuyển địa điểm"), opt("cap_phat", "Cấp phát CCDC"),
               opt("thu_hoi", "Thu hồi về kho"), opt("bao_tri", "Bảo trì"), opt("sua_chua", "Sửa chữa"), opt("bao_hong", "Báo hỏng"),
               opt("de_nghi_thanh_ly", "Đề nghị thanh lý"), opt("thanh_ly", "Thanh lý (đã duyệt)"), opt("bao_mat", "Báo mất")]),
        input_("nguoi_nhan", "Người nhận / người giữ mới"), input_("dia_diem_moi", "Địa điểm mới"), number("so_luong", "Số lượng", 0),
        number("chi_phi", "Chi phí (sửa chữa / bảo trì)", 0), date("ngay_bao_tri_tiep", "Hẹn bảo trì kế tiếp"), text("ghi_chu", "Ghi chú"),
        select("trang_thai", "Trạng thái", TRANG_THAI_PHIEU, "nhap"), input_("ghi_boi", "Người ghi"), input_("ly_do_huy", "Lý do hủy")]},
    # Mẻ sản xuất: chỉ tập hợp chi phí & phân bổ; số lượng / giá trị kho vẫn qua sổ kho.
    {"name": "me_sx", "title": "Mẻ sản xuất", "titleField": "so", "fields": [
        so_ct("ME", 13), date("ngay_mo", "Ngày mở mẻ"), input_("xuong", "Xưởng / tổ"), text("san_pham_du_kien", "Sản phẩm dự kiến"),
        m2o("kho", "Kho nhà máy", "kho", required=True), m2o("kho_tp", "Kho thành phẩm (trống = kho nhà máy)", "kho"),
        select("phuong_phap", "Phân bổ giá thành", [opt("kg", "Theo kg tương đương"), opt("he_so", "Theo hệ số định mức"),
               opt("gia_tri", "Theo giá trị tương đối (giá bán)")], "kg"),
        select("trang_thai", "Trạng thái", [opt("mo", "Đang sản xuất", "blue"), opt("tam_hoan_thanh", "Tạm hoàn thành (chờ chi phí)", "cyan"),
               opt("da_chot", "Đã chốt giá thành", "green"), opt("can_chot_lai", "Cần điều chỉnh", "orange"), opt("da_khoa", "Đã khóa kỳ", "default"),
               opt("da_huy", "Đã hủy", "red")], "mo"),
        number("gia_tri_nvl", "Giá trị NVL tiêu hao", 0, read_only=True), number("gia_tri_bao_bi", "Giá trị bao bì / vật tư (Cái…)", 0, read_only=True),
        number("kg_nvl", "Kg nguyên liệu cấp", 3, read_only=True), number("kg_tp", "Kg thành phẩm thu hồi", 3, read_only=True),
        number("kg_phu_pham", "Kg phụ phẩm", 3, read_only=True), number("kg_hao_tu_nhien", "Hao hụt tự nhiên (kg)", 3, read_only=True),
        number("kg_hao_bat_thuong", "Hao hụt bất thường (kg)", 3, read_only=True),
        number("chi_phi", "Chi phí tập hợp", 0, read_only=True), number("gia_tri_phu_pham", "Giá trị phụ phẩm", 0, read_only=True),
        number("do_dang_cuoi", "Dở dang cuối (giá trị còn lại trên chuyền)", 0), number("kg_do_dang", "Dở dang cuối (kg)", 3),
        number("hao_bat_thuong_gt", "Chi phí hao hụt bất thường (không vào giá thành)", 0, read_only=True),
        number("tong_phan_bo", "Tổng giá trị phân bổ cho thành phẩm", 0, read_only=True), number("da_vao_kho", "Giá trị đã ghi vào kho", 0, read_only=True),
        number("gia_thanh", "Giá thành bình quân (đ/kg)", 2, read_only=True), number("phien_ban", "Phiên bản giá thành", 0, read_only=True),
        input_("chot_boi", "Người chốt"), text("ghi_chu", "Ghi chú")]},
    {"name": "me_sx_chi_phi", "title": "Chi phí mẻ sản xuất", "fields": [
        m2o("me_sx", "Mẻ", "me_sx", label="so", required=True), date("ngay", "Ngày"),
        select("loai", "Khoản chi phí", [opt("nhan_cong", "Nhân công trực tiếp"), opt("dien", "Điện / nước"), opt("bao_bi", "Bao bì ngoài phiếu"),
               opt("van_chuyen", "Vận chuyển / thu mua"), opt("khau_hao", "Khấu hao / chi phí tài sản (ước tính)"), opt("chung", "Chi phí sản xuất chung"),
               opt("do_dang_dau_ky", "Dở dang đầu kỳ / chuyển từ mẻ trước"), opt("dieu_chinh_nvl", "Điều chỉnh giá trị NVL đã cấp")]),
        number("so_tien", "Số tiền", 0), input_("ky", "Kỳ (vd 2026-10)"), text("ghi_chu", "Căn cứ / ghi chú"), input_("nguoi_ghi", "Người ghi")]},
    {"name": "me_sx_phien_ban", "title": "Phiên bản giá thành mẻ", "fields": [
        m2o("me_sx", "Mẻ", "me_sx", label="so"), number("phien_ban", "Phiên bản", 0), date("ngay", "Ngày chốt"),
        number("tong_chi_phi", "NVL + bao bì + chi phí", 0), number("phu_pham", "Phụ phẩm", 0), number("do_dang_cuoi", "Dở dang cuối", 0),
        number("hao_bat_thuong", "Hao hụt bất thường", 0), number("tong_phan_bo", "Phân bổ thành phẩm", 0), number("dieu_chinh", "Điều chỉnh vào kho", 0),
        text("chi_tiet", "Chi tiết phân bổ (JSON)"), input_("nguoi", "Người chốt")]},
]

# ---------------- 0.3.2: toàn vẹn dữ liệu, phạm vi, điều chỉnh giá trị, CCDC theo người giữ, quy đổi ĐVT ----------------
BANG += [
    {"name": "dieu_chinh_gia_tri", "title": "Điều chỉnh giá trị (valuation adjustment)", "fields": [
        date("ngay", "Ngày"), input_("nguon", "Nguồn (mẻ / phiếu nhập / tồn về 0)"), input_("chung_tu", "Chứng từ"),
        m2o("mat_hang", "Mặt hàng", "mat_hang"), m2o("kho", "Kho nguồn", "kho"),
        number("so_luong_goc", "Số lượng gốc chịu điều chỉnh", 3), number("so_luong_con", "Còn tồn tại kho nguồn", 3),
        number("chenh_lech", "Chênh lệch phải phân bổ", 0), number("vao_ton", "Vào giá trị tồn (kho nguồn + kho nhận)", 0),
        number("vao_gia_von", "Vào giá vốn / chi phí kỳ (hàng đã xuất)", 0), number("lam_tron", "Sai số làm tròn", 0),
        text("chi_tiet", "Chi tiết (JSON)"), input_("ly_do", "Lý do")]},
    {"name": "pham_vi", "title": "Phạm vi kho / quỹ của người dùng", "fields": [
        m2o("nguoi_dung", "Người dùng", "users", label="nickname", required=True), m2o("kho", "Kho được thao tác", "kho"),
        m2o("quy", "Quỹ / tài khoản được thao tác", "quy"), text("ghi_chu", "Ghi chú")]},
    {"name": "quy_doi_dvt", "title": "Quy đổi đơn vị tính", "fields": [
        m2o("mat_hang", "Mặt hàng", "mat_hang", required=True),
        select("dvt", "Đơn vị giao dịch", [opt("bao", "Bao"), opt("thung", "Thùng"), opt("goi", "Gói"), opt("cai", "Cái"), opt("kg", "Kg")]),
        number("he_so", "= bao nhiêu ĐVT tồn", 4), check("mac_dinh", "Mặc định khi bán")]},
    {"name": "tai_san_giu", "title": "Số lượng tài sản / CCDC theo người giữ", "fields": [
        m2o("tai_san", "Tài sản", "tai_san"), input_("nguoi_giu", "Người / tổ giữ"), number("so_luong", "Số lượng đang giữ", 0)]},
    {"name": "nhap_lo", "fields": [
        text("tep_goc", "Tệp gốc (base64)"), input_("ten_tep", "Tên tệp"), input_("checksum", "SHA-256 tệp / dữ liệu"),
        input_("thoi_diem_lay", "Thời điểm lấy dữ liệu"), input_("ma_nguon", "Mã nguồn (ID Google Sheet / tệp)"), input_("trang_tinh", "Trang tính"),
        number("nguoi_nhap_id", "Mã người nhập", 0), text("ngoai_le", "Lý do ngoại lệ đã duyệt"), input_("ngoai_le_boi", "Người duyệt ngoại lệ")]},
    {"name": "ky_mo_so", "fields": [check("tach_nguoi_duyet", "Người duyệt phải khác người nhập (tiền, công nợ)", True)]},
    {"name": "luot_giao", "fields": [select("tt_gia_von", "Giá vốn", [opt("co", "Đã có"), opt("chua_xac_dinh", "Chưa xác định")], "co")]},
    {"name": "thu_ho", "fields": [number("da_tat_toan", "Đã tất toán", 0), text("chung_tu_tat_toan", "Chứng từ tất toán")]},
    {"name": "don_ban", "fields": [number("so_doi_tac_xac_nhan", "Số đối tác xác nhận (đối chiếu)", 0)]},
    {"name": "no_ncc_dau_ky", "fields": [number("so_doi_tac_xac_nhan", "Số NCC xác nhận (đối chiếu)", 0)]},
    {"name": "don_ban_dong", "fields": [input_("dvt_nhap", "ĐVT nhập"), number("sl_nhap", "Số lượng theo ĐVT nhập", 3)]},
    {"name": "phieu_kho_dong", "fields": [input_("dvt_nhap", "ĐVT nhập"), number("sl_nhap", "Số lượng theo ĐVT nhập", 3)]},
    {"name": "tai_san", "fields": [date("ngay_su_dung", "Ngày đưa vào sử dụng"), input_("bo_phan_chi_phi", "Bộ phận chịu chi phí")]},
    {"name": "tai_san_su_kien", "fields": [input_("nguoi_tra", "Người / tổ trả (thu hồi)"), input_("so_chung_tu", "Số chứng từ (sửa chữa / thanh lý)")]},
    {"name": "me_sx", "fields": [number("kg_do_dang_dau", "Dở dang đầu kỳ (kg)", 3),
        select("trang_thai", "Trạng thái", [opt("mo", "Đang sản xuất", "blue"), opt("tam_hoan_thanh", "Tạm hoàn thành (chờ chi phí)", "cyan"),
               opt("da_chot", "Đã chốt giá thành", "green"), opt("can_chot_lai", "Cần điều chỉnh", "orange"), opt("da_khoa", "Đã khóa kỳ", "default"),
               opt("da_huy", "Đã hủy", "red")], "mo")]},
    {"name": "me_sx_chi_phi", "fields": [input_("so_chung_tu", "Số chứng từ (hóa đơn / bảng lương)"), m2o("phieu_chi", "Phiếu chi", "phieu_chi", label="so")]},
]

# ---------------- 0.4.0 Unified Operations ----------------
TT_PT = [opt("nhap", "Nháp", "default"), opt("cho_xac_minh", "Chờ xác minh (chưa vào quỹ)", "gold"), opt("da_ghi", "Đã ghi", "green"), opt("da_huy", "Đã hủy", "red")]
VAT = [opt("chiu_thue", "Chịu thuế"), opt("khong_chiu", "Không chịu thuế"), opt("kkknt", "Không kê khai tính nộp"), opt("khong_hd", "Không xuất hóa đơn")]
DVT_GD = [opt("kg", "Kg"), opt("bao", "Bao"), opt("thung", "Thùng"), opt("goi", "Gói"), opt("cai", "Cái")]
BANG += [
    {"name": "cau_hinh", "title": "Cấu hình", "titleField": "khoa", "fields": [
        input_("khoa", "Khóa", unique=True), text("gia_tri", "Giá trị"), text("mo_ta", "Ý nghĩa")]},
    {"name": "phien_ban_schema", "title": "Phiên bản dữ liệu", "fields": [
        input_("phien_ban", "Phiên bản", unique=True), input_("ngay", "Thời điểm"), text("ghi_chu", "Nội dung nâng cấp")]},
    {"name": "dat_giu_ton", "title": "Nhật ký giữ tồn", "fields": [
        m2o("kho", "Kho", "kho"), m2o("mat_hang", "Mặt hàng", "mat_hang"), m2o("don_ban_dong", "Dòng đơn", "don_ban_dong"),
        number("so_luong", "Số lượng (+ giữ / − nhả)", 3), select("loai", "Nghiệp vụ", [opt("giu_don", "Giữ khi duyệt đơn"), opt("sang_luot", "Chuyển giữ sang lượt"),
        opt("ve_don", "Lượt hủy: trả giữ về đơn"), opt("xuat", "Xuất thực tế"), opt("nha", "Giải phóng")]), input_("chung_tu", "Chứng từ")]},
    {"name": "mat_hang", "fields": [
        select("tinh_tien_theo", "Tính tiền khi cân lệch", [opt("quy_cach", "Theo quy cách (bao nguyên)"), opt("thuc_can", "Theo số cân thực")], "quy_cach"),
        number("dung_sai_pct", "Dung sai cân cho phép (%)", 2), number("thue_suat", "Thuế suất VAT mặc định (%)", 2),
        select("loai_vat", "Loại VAT mặc định", VAT), input_("ma_vach", "Mã vạch (EAN / nội bộ)"), check("theo_lo", "Theo dõi số lô / hạn dùng")]},
    {"name": "khach_hang", "fields": [
        input_("nhom_gia", "Nhóm giá (sỉ / lẻ / đại lý…)"), check("rui_ro", "Khách rủi ro (vượt hạn mức phải duyệt)"),
        number("so_ngay_no", "Số ngày được nợ", 0)]},
    {"name": "bang_gia", "title": "Bảng giá", "titleField": "ma", "fields": [
        input_("ma", "Mã bảng giá", required=True, unique=True), input_("ten", "Tên"), input_("nhom_gia", "Nhóm giá khách (trống = mọi khách)"),
        select("kenh", "Kênh", [opt("si", "Bán sỉ"), opt("pos", "Bán lẻ / POS")]), date("tu_ngay", "Hiệu lực từ"), date("den_ngay", "Hiệu lực đến"),
        check("gia_gom_vat", "Giá đã gồm VAT"), number("uu_tien", "Ưu tiên (lớn hơn thắng)", 0), check("ngung", "Ngừng dùng")]},
    {"name": "bang_gia_dong", "title": "Dòng bảng giá", "fields": [
        m2o("mat_hang", "Mặt hàng", "mat_hang", required=True), select("dvt", "ĐVT giá", DVT_GD, "kg"),
        number("sl_toi_thieu", "Từ số lượng (ĐVT tồn)", 3), number("don_gia", "Đơn giá / ĐVT tồn", 0), number("gia_san", "Giá sàn / ĐVT tồn", 0)]},
    {"name": "lich_su_duyet_gia", "title": "Lịch sử duyệt giá / tín dụng", "fields": [
        m2o("don_ban", "Đơn", "don_ban", label="so"), input_("loai", "Loại (giá / tín dụng)"), text("noi_dung", "Nội dung"), input_("nguoi", "Người duyệt"),
        input_("ly_do", "Lý do"), input_("thoi_diem", "Thời điểm")]},
    {"name": "don_gop", "title": "Đơn gộp", "titleField": "so", "fields": [
        so_ct("DG", 14), m2o("khach", "Khách hàng", "khach_hang", required=True), date("ngay", "Ngày đặt"), date("ngay_giao", "Ngày giao"),
        select("cach_giao", "Cách giao", [opt("khach_den_lay", "Khách đến lấy"), opt("van_chuyen", "Vận chuyển")], "khach_den_lay"),
        input_("nguoi_nhan", "Người nhận"), input_("sdt", "SĐT"), text("dia_chi_giao", "Địa chỉ giao"), text("ghi_chu", "Ghi chú"),
        select("tt_duyet", "Duyệt", [opt("nhap", "Nháp"), opt("cho_duyet", "Chờ duyệt"), opt("da_duyet", "Đã duyệt"), opt("tu_choi", "Từ chối"), opt("da_huy", "Đã hủy")], "nhap"),
        select("tt_giao", "Giao", [opt("chua_giu", "Chưa giữ hàng"), opt("da_giu", "Đã giữ hàng"), opt("thieu_giu", "Giữ thiếu"), opt("cho_xuat", "Chờ xuất"), opt("dang_giao", "Đang giao"),
               opt("mot_phan", "Đã giao một phần"), opt("du", "Đã giao đủ"), opt("dong", "Đóng phần chưa giao")], "chua_giu"),
        select("tt_thanh_toan", "Thanh toán", [opt("chua_thu", "Chưa thu"), opt("mot_phan", "Thu một phần"), opt("du", "Đã thu đủ"), opt("phai_hoan", "Có khoản phải hoàn")], "chua_thu"),
        select("tt_hoa_don", "Hóa đơn", [opt("khong", "Không yêu cầu"), opt("cho_xu_ly", "Chờ xử lý"), opt("dang_lap", "Đang lập nháp"), opt("da_xuat", "Đã xuất"), opt("can_dieu_chinh", "Cần điều chỉnh")], "khong"),
        number("tong_tien", "Tổng tiền (gồm VAT)", 0), number("phai_thu", "Phải thu (đã giao)", 0), number("da_thu", "Đã thu", 0), number("con_no", "Còn nợ", 0),
        input_("ly_do_duyet", "Cần duyệt vì"), input_("duyet_boi", "Người duyệt"), input_("request_id", "Mã yêu cầu", unique=True)]},
    {"name": "don_gop_dong", "title": "Dòng đơn gộp", "fields": [
        m2o("mat_hang", "Mặt hàng", "mat_hang", required=True), m2o("don_vi_ban", "Bên bán", "don_vi", required=True), m2o("kho", "Kho xuất", "kho"),
        input_("dvt_nhap", "ĐVT"), number("sl_nhap", "SL theo ĐVT", 3), number("so_kg", "SL ĐVT tồn", 3), number("so_bao", "Số bao", 2),
        number("don_gia", "Đơn giá / ĐVT tồn (nhập tay, trống = bảng giá)", 0), check("vat_ap_dung", "Xuất hóa đơn VAT"), number("thue_suat", "Thuế suất %", 2),
        check("gia_gom_vat", "Giá đã gồm VAT"), text("ghi_chu", "Ghi chú"), number("don_ban_dong_id", "Dòng đơn con", 0)]},
    {"name": "don_ban", "fields": [
        select("kenh", "Kênh", [opt("si", "Bán sỉ"), opt("pos", "POS / bán lẻ")], "si"), number("phai_hoan", "Phải hoàn cho khách", 0),
        select("tt_thanh_toan", "Thanh toán", [opt("chua_thu", "Chưa thu"), opt("mot_phan", "Thu một phần"), opt("du", "Đã thu đủ"), opt("phai_hoan", "Có khoản phải hoàn")], "chua_thu"),
        text("canh_bao_tin_dung", "Cảnh báo tín dụng"), number("tien_thue", "Tiền thuế", 0)]},
    {"name": "don_ban_dong", "fields": [
        number("gia_niem_yet", "Giá niêm yết (bảng giá)", 0), input_("nguon_gia", "Nguồn giá"), input_("ly_do_sua_gia", "Lý do sửa giá"),
        check("vat_ap_dung", "Có VAT"), select("loai_vat", "Loại VAT", VAT), number("thue_suat", "Thuế suất %", 2), check("gia_gom_vat", "Giá đã gồm VAT"),
        number("tien_truoc_thue", "Tiền trước thuế", 0), number("tien_thue", "Tiền thuế", 0), number("don_gia_tt", "Đơn giá thanh toán (gồm VAT)", 4),
        number("giu_don", "Đang giữ cấp đơn", 3), number("he_so_qd", "Hệ số quy đổi lúc đặt", 4), input_("price_basis", "Cơ sở giá (gồm / chưa gồm VAT)"),
        number("gia_san_ap", "Giá sàn áp dụng", 0)]},
    {"name": "luot_giao_dong", "fields": [
        number("so_kg_thuc", "Số lượng thực xuất (cân / đếm)", 3), number("so_bao_thuc", "Số bao thực", 2), number("sl_tinh_tien", "Số lượng tính tiền", 3),
        number("chenh_can", "Chênh cân (thực − tính tiền)", 3), input_("ly_do_chenh", "Lý do chênh"), number("tien_thue", "Tiền thuế", 0),
        input_("so_lo", "Số lô"), date("han_dung", "Hạn dùng")]},
    {"name": "giao_gop", "title": "Chuyến giao gộp", "titleField": "so", "fields": [
        so_ct("GN", 15), date("ngay", "Ngày"), select("cach_giao", "Cách giao", [opt("khach_den_lay", "Khách đến lấy"), opt("van_chuyen", "Vận chuyển")], "khach_den_lay"),
        input_("nguoi_nhan", "Người nhận / lái xe"), input_("bien_so", "Biển số"), input_("request_id", "Mã yêu cầu", unique=True),
        select("trang_thai", "Trạng thái", [opt("cho_xuat", "Chờ xuất"), opt("da_xuat", "Đã xuất"), opt("da_huy", "Đã hủy")], "cho_xuat")]},
    {"name": "giao_gop_luot", "title": "Lượt trong chuyến gộp", "fields": [m2o("luot_giao", "Lượt giao", "luot_giao", label="so")]},
    {"name": "hoa_don_cho_xuat", "title": "Hàng đợi hóa đơn MISA", "titleField": "so", "fields": [
        so_ct("HQ", 16), m2o("don_ban", "Đơn con", "don_ban", label="so"), m2o("don_vi", "Bên bán (bên xuất HĐ)", "don_vi"), m2o("khach", "Khách", "khach_hang"),
        number("lan", "Lần", 0), input_("khoa_trung", "Khóa", unique=True), number("tien_truoc_thue", "Tiền trước thuế", 0), number("tien_thue", "Tiền thuế", 0),
        number("tong", "Tổng", 0), select("trang_thai", "Trạng thái", [opt("cho_xu_ly", "Chờ xử lý"), opt("dang_lap", "Đang lập nháp"), opt("da_xuat", "Đã xuất"),
        opt("can_dieu_chinh", "Cần điều chỉnh"), opt("huy", "Hủy")], "cho_xu_ly"), input_("nguoi_xu_ly", "Người xử lý"), input_("ky_hieu", "Ký hiệu"),
        input_("so_hd", "Số HĐ"), date("ngay_hd", "Ngày HĐ"), text("ghi_chu", "Ghi chú")]},
    {"name": "chuyen_hang", "title": "Chuyến chuyển hàng (2 đầu)", "titleField": "so", "fields": [
        so_ct("CH", 17), date("ngay", "Ngày"), m2o("kho_di", "Kho đi", "kho", required=True), m2o("kho_den", "Kho đến", "kho", required=True),
        m2o("kho_tg", "Kho hàng đang vận chuyển", "kho"), input_("xe", "Xe / biển số"), input_("nguoi_giao", "Người giao"), input_("nguoi_nhan", "Người nhận"),
        select("trang_thai", "Trạng thái", [opt("nhap", "Nháp"), opt("da_xuat", "Đã xuất — đang đi đường"), opt("da_nhan", "Đã nhận đủ"),
               opt("co_chenh_lech", "Đã nhận — có chênh lệch chờ xử lý"), opt("da_huy", "Đã hủy")], "nhap"),
        input_("xuat_boi", "Người xác nhận xuất"), input_("nhan_boi", "Người xác nhận nhận"), input_("request_id", "Mã yêu cầu", unique=True),
        input_("nguon", "Nguồn (nhập liệu / import)"), text("ghi_chu", "Ghi chú")]},
    {"name": "chuyen_hang_dong", "title": "Dòng chuyến chuyển", "fields": [
        m2o("mat_hang", "Mặt hàng", "mat_hang", required=True), number("so_kg", "SL xuất", 3), number("so_bao", "Bao xuất", 2),
        number("so_kg_nhan", "SL thực nhận", 3), number("so_bao_nhan", "Bao nhận", 2), input_("so_lo", "Số lô"), text("ghi_chu", "Ghi chú")]},
    {"name": "chenh_lech_giao_nhan", "title": "Chênh lệch giao – nhận", "fields": [
        m2o("chuyen_hang", "Chuyến", "chuyen_hang", label="so"), m2o("mat_hang", "Mặt hàng", "mat_hang"), number("so_kg", "Chênh (− thiếu / + thừa)", 3),
        select("trang_thai", "Trạng thái", [opt("cho_xu_ly", "Chờ xử lý", "orange"), opt("da_xu_ly", "Đã xử lý", "green")], "cho_xu_ly"),
        select("cach_xu_ly", "Cách xử lý", [opt("hao_hut", "Hao hụt (duyệt)"), opt("nhan_bo_sung", "Tìm thấy — nhận bổ sung"), opt("tra_ve", "Trả về kho đi"), opt("boi_thuong", "Bồi thường")]),
        text("ly_do", "Lý do / biên bản"), input_("nguoi_duyet", "Người duyệt")]},
    {"name": "ca_pos", "title": "Ca bán nhanh", "titleField": "so", "fields": [
        so_ct("CA", 18), m2o("quy", "Quỹ tiền mặt của ca", "quy", required=True), m2o("kho", "Kho bán", "kho", required=True), m2o("don_vi", "Bên bán mặc định", "don_vi"),
        input_("thu_ngan", "Thu ngân"), number("thu_ngan_id", "Mã người dùng", 0), input_("mo_luc", "Mở lúc"), input_("dong_luc", "Chốt lúc"),
        number("tien_dau_ca", "Tiền đầu ca", 0), number("thu_tien_mat", "Thu tiền mặt", 0), number("thu_ck", "Chuyển khoản (chờ xác minh)", 0), number("ghi_no", "Ghi nợ", 0),
        number("so_don", "Số đơn", 0), number("thuc_dem", "Thực đếm cuối ca", 0), number("chenh_lech", "Chênh lệch", 0), text("ly_do", "Lý do chênh"),
        select("trang_thai", "Trạng thái", [opt("mo", "Đang mở", "green"), opt("da_chot", "Đã chốt", "default")], "mo")]},
    {"name": "phieu_thu", "fields": [select("trang_thai", "Trạng thái", TT_PT, "nhap"), input_("xac_minh_boi", "Người xác minh")]},
    {"name": "phieu_chi", "fields": [number("hoan_cho_don_id", "Hoàn tiền cho đơn", 0)]},
    {"name": "sao_ke", "title": "Sao kê ngân hàng", "titleField": "so", "fields": [
        so_ct("SK", 19), m2o("quy", "Tài khoản ngân hàng", "quy", required=True), input_("ten_tep", "Tệp"), input_("checksum", "SHA-256"),
        number("so_dong", "Số dòng", 0), number("so_moi", "Dòng mới", 0), number("so_trung", "Dòng đã có", 0), input_("nguoi_nap", "Người nạp")]},
    {"name": "sao_ke_dong", "title": "Dòng sao kê", "fields": [
        m2o("quy", "Tài khoản", "quy"), date("ngay", "Ngày"), number("so_tien", "Số tiền (+ vào / − ra)", 0), text("noi_dung", "Nội dung"),
        input_("ma_gd", "Mã giao dịch NH"), input_("khoa_trung", "Khóa chống trùng", unique=True),
        select("trang_thai", "Trạng thái", [opt("chua_khop", "Chưa khớp", "orange"), opt("da_khop", "Đã khớp", "green"), opt("bo_qua", "Bỏ qua (không phải thu)", "default")], "chua_khop"),
        m2o("phieu_thu", "Phiếu thu đã khớp", "phieu_thu", label="so"), input_("khop_boi", "Người khớp")]},
    {"name": "sx_ra_soat", "title": "Sản xuất cần rà soát", "titleField": "so_phieu", "fields": [
        input_("nguon", "Nguồn"), input_("so_phieu", "Số phiếu"), date("ngay", "Ngày"), input_("xuong", "Dây chuyền / xưởng"), text("du_lieu", "Dòng phiếu (JSON)"),
        text("van_de", "Vấn đề"), select("trang_thai", "Trạng thái", [opt("cho_bo_sung", "Chờ bổ sung", "orange"), opt("du_dieu_kien", "Đủ điều kiện", "blue"),
        opt("da_tao", "Đã tạo mẻ", "green"), opt("bo_qua", "Bỏ qua", "default")], "cho_bo_sung"), m2o("me_sx", "Mẻ đã tạo", "me_sx", label="so"),
        input_("khoa_trung", "Khóa", unique=True)]},
    {"name": "nguon_tep", "title": "Tệp nguồn đã nạp", "titleField": "ten_tep", "fields": [
        select("he_thong", "Nguồn", [opt("nha_may", "Sheet nhà máy Phú Thọ"), opt("ban_hang", "Sổ bán hàng – kho – công nợ"), opt("misa", "MISA"), opt("erpnext", "ERPNext")]),
        input_("ten_tep", "Tên tệp"), input_("checksum", "SHA-256", unique=True), input_("thoi_diem", "Thời điểm nạp"), number("so_ban_ghi", "Số bản ghi", 0),
        input_("nguoi_nap", "Người nạp"), text("ghi_chu", "Ghi chú")]},
    {"name": "nguon_ban_ghi", "title": "Bản ghi nguồn (staging)", "fields": [
        m2o("tep", "Tệp", "nguon_tep", label="ten_tep"), input_("he_thong", "Nguồn"), input_("trang_tinh", "Trang tính"), number("dong", "Dòng", 0),
        input_("khoa", "Khóa nguồn (hệ thống|trang|nội dung)", unique=True), input_("loai_nv", "Loại nghiệp vụ"), date("ngay", "Ngày"), input_("so_ct", "Số chứng từ nguồn"),
        text("du_lieu", "Dữ liệu gốc (JSON)"), text("chuan_hoa", "Dữ liệu chuẩn hóa (JSON)"),
        select("ket_qua", "Phân loại", [opt("nhap_duoc", "Nhập được", "green"), opt("chua_du", "Chưa đủ căn cứ", "orange"), opt("co_the_trung", "Có thể trùng", "purple"),
               opt("bi_chan", "Bị chặn", "red"), opt("truoc_moc", "Trước mốc / nằm trong số dư", "default"), opt("da_ghi", "Đã ghi sổ", "blue"), opt("bo_qua", "Bỏ qua", "default")]),
        text("van_de", "Vấn đề"), input_("chung_tu_dich", "Chứng từ đã tạo")]},
    {"name": "anh_xa_ma", "title": "Ánh xạ mã nguồn", "fields": [
        input_("he_thong", "Nguồn"), select("loai", "Loại", [opt("kho", "Kho"), opt("mat_hang", "Mặt hàng"), opt("khach_hang", "Khách"), opt("nha_cung_cap", "NCC"), opt("don_vi", "Đơn vị"), opt("quy", "Quỹ / tài khoản")]),
        input_("ma_nguon", "Mã / tên ở nguồn"), input_("ten_nguon", "Tên ở nguồn"), number("dich_id", "Mã đích (id)", 0), input_("dich_ma", "Mã đích"),
        input_("khoa", "Khóa", unique=True), text("ghi_chu", "Ghi chú")]},
    {"name": "dieu_chinh_gia_tri", "fields": [number("vao_me", "Vào chi phí mẻ tiêu thụ (NVL đã cấp)", 0)]},
    {"name": "pham_vi", "fields": [check("tat_ca_kho", "Được mọi kho"), check("tat_ca_quy", "Được mọi quỹ")]},
    {"name": "khop_chung_tu", "title": "Ghép chứng từ hai nguồn", "fields": [
        m2o("ban_ghi_a", "Bản ghi nguồn A", "nguon_ban_ghi"), m2o("ban_ghi_b", "Bản ghi nguồn B", "nguon_ban_ghi"), number("diem", "Điểm khớp", 2), text("ly_do", "Căn cứ"),
        select("trang_thai", "Trạng thái", [opt("de_xuat", "Đề xuất"), opt("xac_nhan", "Đã xác nhận là một chuyến"), opt("bac_bo", "Không phải một chuyến")], "de_xuat"),
        input_("nguoi", "Người xác nhận"), input_("khoa", "Khóa", unique=True)]},
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
    ("nhap_lo", o2m("dong", "Các dòng", "nhap_dong", "nhap_lo_id")),
    ("tai_san", o2m("su_kien", "Lịch sử", "tai_san_su_kien", "tai_san_id")),
    ("me_sx", m2o("me_goc", "Mẻ gốc (tái chế / sản xuất lại)", "me_sx", label="so")),
    ("tai_san", o2m("dang_giu", "Đang giữ", "tai_san_giu", "tai_san_id")),
    ("mat_hang", o2m("quy_doi", "Quy đổi ĐVT", "quy_doi_dvt", "mat_hang_id")),
    ("bang_gia", o2m("dong", "Dòng giá", "bang_gia_dong", "bang_gia_id")),
    ("don_gop", o2m("dong", "Dòng hàng", "don_gop_dong", "don_gop_id")),
    ("don_ban", m2o("don_gop", "Đơn gộp", "don_gop", label="so")),
    ("don_gop", o2m("don_con", "Đơn con", "don_ban", "don_gop_id", label="so")),
    ("giao_gop", o2m("luot_ds", "Các lượt", "giao_gop_luot", "giao_gop_id")),
    ("giao_gop", m2o("don_gop", "Đơn gộp", "don_gop", label="so")),
    ("chuyen_hang", o2m("dong", "Hàng", "chuyen_hang_dong", "chuyen_hang_id")),
    ("don_ban", m2o("ca_pos", "Ca bán", "ca_pos", label="so")),
    ("phieu_thu", m2o("ca_pos", "Ca bán", "ca_pos", label="so")),
    ("sao_ke", o2m("dong", "Dòng", "sao_ke_dong", "sao_ke_id")),
    ("phieu_kho", m2o("me_sx", "Mẻ sản xuất", "me_sx", label="so")),
    ("me_sx", o2m("chi_phi_ds", "Chi phí", "me_sx_chi_phi", "me_sx_id")),
    ("me_sx", o2m("phieu", "Phiếu kho", "phieu_kho", "me_sx_id", label="so")),
    ("me_sx", o2m("phien_ban_ds", "Phiên bản giá thành", "me_sx_phien_ban", "me_sx_id")),
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
        co[b["name"]] = {"fields": [dict(f) for f in b["fields"]]}
    co = {c["name"]: c for c in api.call("collections:list", params="?paginate=false&appends=fields")["data"]}
    for bang, f in QUAN_HE:
        if f["name"] not in {x["name"] for x in co[bang].get("fields") or []}:
            api.call(f"collections/{bang}/fields:create", f)
            print(f"+ quan hệ {bang}.{f['name']}")
    print("Xong.")


if __name__ == "__main__":
    main()
