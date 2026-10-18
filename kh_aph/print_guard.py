"""Chặn các lối in / xem trước của Frappe bỏ qua bước xóa giá của app (0.11.0).

App xóa giá trên bản in bằng hook `before_print` và che giá trên chứng từ bằng `apply_fieldlevel_read_permissions`
(CostReadGuard). Các endpoint dưới đây trả nội dung chứng từ mà KHÔNG đi qua hai bước đó, nên với người bị ẩn giá
(vai trò "APH Không xem giá vốn", nhà máy, bán hàng, thủ kho không có vai trò xem giá) phải chặn:

- `frappe.utils.weasyprint.download_pdf` (có từ Frappe 16.35): in PDF bằng bộ dựng mẫu in, không gọi before_print.
- `frappe.utils.weasyprint_legacy.download_pdf` (Frappe 16.51): như trên.
- `frappe.utils.print_format_generator.*` (Frappe 16.51): `get_formatted_field_values` trả giá trị định dạng mọi trường kể
  cả dòng con; `check_conditions` cho dò giá bằng biểu thức đúng/sai; xem trước bộ dựng.
- `frappe.desk.doc_preview.get_preview` (Frappe 16.51) trên **dòng con**: dòng con không có lớp che của chứng từ cha.

`print_format_generator.download_pdf` không chặn: mẫu in kiểu mới chạy `run_before_print` (có hook của app), mẫu Jinja đi
lối in cũ. In bằng các lối chuẩn (printview, download_pdf cũ) vẫn dùng được và đã có ca UAT `HTTP_DUNG_PRINT`.

Không phụ thuộc cờ: ẩn giá nhà máy/bán hàng có từ 0.2–0.3, không bật tắt. Chặn theo tên lệnh trước khi Frappe chạy hàm,
nên endpoint chưa có ở bản Frappe đang chạy cũng bị trả 403 như nhau.
"""

CHAN_HAN = frozenset({
    "frappe.utils.weasyprint.download_pdf",
    "frappe.utils.weasyprint_legacy.download_pdf",
    "frappe.utils.print_format_generator.get_formatted_field_values",
    "frappe.utils.print_format_generator.check_conditions",
    "frappe.utils.print_format_generator.render_builder_preview",
    "frappe.utils.print_format_generator.download_builder_preview_pdf",
    "frappe.utils.print_format_generator.render_jinja_template",
})
XEM_TRUOC = "frappe.desk.doc_preview.get_preview"
THONG_BAO = "Tài khoản bị ẩn giá: dùng mẫu in của hệ thống (Print) thay cho lối in/xem trước này."


def lay_lenh(cmd: str | None, duong_dan: str | None) -> str:
    """Tên hàm được gọi: tham số cmd, hoặc phần sau /api/method/ hay /api/v2/method/ của đường dẫn (thuần)."""
    if cmd:
        return cmd.strip()
    duong_dan = duong_dan or ""
    for tien_to in ("/api/v2/method/", "/api/method/"):
        if tien_to in duong_dan:
            return duong_dan.split(tien_to, 1)[1].split("?", 1)[0].strip("/")
    return ""


def can_chan(lenh: str, bi_an_gia: bool, la_bang_con: bool = False) -> bool:
    """Có chặn lời gọi này không (thuần)."""
    if not bi_an_gia or not lenh:
        return False
    if lenh in CHAN_HAN:
        return True
    return lenh == XEM_TRUOC and la_bang_con


def before_request():
    import frappe

    lenh = lay_lenh(frappe.form_dict.get("cmd"), getattr(frappe.request, "path", ""))
    if lenh not in CHAN_HAN and lenh != XEM_TRUOC:
        return  # đa số request: không tốn truy vấn vai trò
    from kh_aph.price_visibility import is_cost_restricted, is_price_restricted

    bi_an_gia = is_price_restricted() or is_cost_restricted()
    la_bang_con = False
    if lenh == XEM_TRUOC and bi_an_gia:
        dt = frappe.form_dict.get("doctype")
        la_bang_con = bool(dt) and bool(frappe.get_meta(dt).istable)
    if can_chan(lenh, bi_an_gia, la_bang_con):
        frappe.throw(THONG_BAO, frappe.PermissionError)
