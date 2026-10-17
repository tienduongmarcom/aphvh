"""Hồ sơ bản ký trên phiếu giao nguồn; không tạo sổ hoặc trạng thái giao hàng thứ hai."""
import frappe
from frappe.utils import cint, now_datetime

FILE = "kh_aph_ban_ky"
NOTE = "kh_aph_ghi_chu_ban_ky"
ACTOR = "kh_aph_doi_chieu_boi"
TIME = "kh_aph_doi_chieu_luc"


def enabled():
    return cint(frappe.conf.get("kh_aph_trung_tam_ban"))


def fields():
    condition = "eval:doc.docstatus==1 && !doc.is_return"
    return [
        {"fieldname": "kh_aph_ho_so_giao_nhan", "label": "Hồ sơ giao nhận", "fieldtype": "HTML", "options": "<strong>Hồ sơ giao nhận</strong>",
         "insert_after": "kh_aph_delivery_at", "depends_on": condition},
        {"fieldname": FILE, "label": "Bản phiếu đã ký", "fieldtype": "Attach",
         "insert_after": "kh_aph_ho_so_giao_nhan", "allow_on_submit": 1, "no_copy": 1, "depends_on": condition,
         "description": "Tải tệp riêng tư gắn với chính phiếu này. Có tệp chưa đồng nghĩa đã đối chiếu."},
        {"fieldname": NOTE, "label": "Ghi chú / chênh lệch trên bản ký", "fieldtype": "Small Text",
         "insert_after": FILE, "allow_on_submit": 1, "no_copy": 1, "depends_on": condition},
        {"fieldname": ACTOR, "label": "Người đã đối chiếu bản ký", "fieldtype": "Link", "options": "User",
         "insert_after": NOTE, "allow_on_submit": 1, "read_only": 1, "no_copy": 1, "depends_on": condition},
        {"fieldname": TIME, "label": "Thời điểm đối chiếu bản ký", "fieldtype": "Datetime",
         "insert_after": ACTOR, "allow_on_submit": 1, "read_only": 1, "no_copy": 1, "depends_on": condition},
    ]


def _file(doc):
    url = doc.get(FILE)
    if not url:
        frappe.throw("Cần tải bản phiếu đã ký trước khi đối chiếu")
    # URL công khai, URL ngoài hoặc tệp của phiếu khác không phải hồ sơ hợp lệ.
    records = frappe.get_all("File", filters={"file_url": url, "attached_to_doctype": "Delivery Note",
                            "attached_to_name": doc.name, "is_private": 1}, fields=["name"], limit_page_length=1)
    if not records or not url.startswith("/private/files/"):
        frappe.throw("Bản ký phải là tệp riêng tư đính kèm đúng phiếu giao này")


def validate(doc, method=None):
    if not enabled() or not doc.meta.has_field(FILE):
        return
    old = doc.get_doc_before_save()
    reviewed = frappe.flags.get("kh_aph_doi_chieu_ban_ky") == doc.name
    if not reviewed and any(str(doc.get(f) or "") != str((old.get(f) if old else None) or "") for f in (ACTOR, TIME)):
        frappe.throw("Dùng thao tác Đối chiếu bản ký để ghi người và thời điểm xác nhận")
    changed = any((doc.get(f) or "") != ((old.get(f) if old else None) or "") for f in (FILE, NOTE))
    if changed:
        if cint(doc.docstatus) != 1 or cint(doc.is_return):
            frappe.throw("Chỉ lưu hồ sơ bản ký trên phiếu giao đã xuất, không phải phiếu trả lại")
        if doc.get(FILE):
            _file(doc)
        # Thay tệp hoặc ghi chú làm mất xác nhận trước, không giữ dấu đối chiếu cũ.
        doc.set(ACTOR, None)
        doc.set(TIME, None)


@frappe.whitelist(methods=["POST"])
def doi_chieu(name, modified):
    if not enabled():
        frappe.throw("Hồ sơ giao nhận chưa được bật")
    frappe.db.sql("SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE", name)
    doc = frappe.get_doc("Delivery Note", name)
    doc.check_permission("read")
    doc.check_permission("write")
    if str(doc.modified) != str(modified):
        frappe.throw("Phiếu đã thay đổi. Tải lại và kiểm tra bản ký trước khi xác nhận", frappe.TimestampMismatchError)
    if cint(doc.docstatus) != 1 or cint(doc.is_return) or doc.get("kh_aph_delivery_state") != "Khách đã nhận":
        frappe.throw("Chỉ đối chiếu bản ký khi khách đã nhận hàng")
    _file(doc)
    if doc.get(ACTOR):
        return {"name": doc.name, "doi_chieu_boi": doc.get(ACTOR), "doi_chieu_luc": doc.get(TIME)}
    previous = frappe.flags.get("kh_aph_doi_chieu_ban_ky")
    frappe.flags.kh_aph_doi_chieu_ban_ky = doc.name
    try:
        doc.set(ACTOR, frappe.session.user)
        doc.set(TIME, now_datetime())
        doc.save()
        doc.add_comment("Comment", "Đã đối chiếu bản phiếu có chữ ký với phiếu giao và ghi chú chênh lệch.")
    finally:
        frappe.flags.kh_aph_doi_chieu_ban_ky = previous
    return {"name": doc.name, "doi_chieu_boi": doc.get(ACTOR), "doi_chieu_luc": doc.get(TIME)}


def protect_file(doc, method=None):
    """Không xóa tệp đang được dùng làm hồ sơ; gỡ/thay trên phiếu trước để mất dấu đối chiếu."""
    if not enabled() or not doc.file_url or not frappe.get_meta("Delivery Note").has_field(FILE):
        return
    if frappe.db.exists("Delivery Note", {FILE: doc.file_url, "docstatus": ["!=", 2]}):
        frappe.throw("Tệp đang là bản ký của phiếu giao. Gỡ hoặc thay bản ký trên phiếu trước khi xóa tệp")


def protect_file_update(doc, method=None):
    """Giữ quyền riêng tư/liên kết/nội dung của tệp đã được chọn trên phiếu."""
    if not enabled() or not frappe.get_meta("Delivery Note").has_field(FILE):
        return
    old = doc.get_doc_before_save()
    if not old or not old.file_url:
        return
    if not frappe.db.exists("Delivery Note", {FILE: old.file_url, "docstatus": ["!=", 2]}):
        return
    if any(doc.get(f) != old.get(f) for f in ("file_url", "is_private", "attached_to_doctype", "attached_to_name")) or doc.get("content"):
        frappe.throw("Tệp đang là bản ký. Tải tệp mới và thay trên phiếu để đối chiếu lại")


class HoSoFileMixin:
    def on_trash(self):
        # File.on_trash xóa blob trước doc_events; phải kiểm trước super(),
        # vì rollback CSDL không khôi phục được nội dung đã xóa trên đĩa.
        protect_file(self)
        return super().on_trash()
