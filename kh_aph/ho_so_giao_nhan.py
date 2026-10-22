"""Hồ sơ bản ký trên phiếu giao nguồn; không tạo sổ hoặc trạng thái giao hàng thứ hai."""
import json

import frappe
from frappe.utils import cint, now_datetime

HISTORY = "kh_aph_lich_su_ban_ky"
FILE = "kh_aph_ban_ky"
NOTE = "kh_aph_ghi_chu_ban_ky"
ACTOR = "kh_aph_doi_chieu_boi"
TIME = "kh_aph_doi_chieu_luc"
ORIGINAL_BY = "kh_aph_nhan_goc_boi"
ORIGINAL_AT = "kh_aph_nhan_goc_luc"
ORIGINAL_LOCATION = "kh_aph_vi_tri_goc"
ORIGINAL_FIELDS = (ORIGINAL_BY, ORIGINAL_AT, ORIGINAL_LOCATION)


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
        {"fieldname": HISTORY, "label": "Lịch sử hồ sơ bản ký", "fieldtype": "Long Text",
         "insert_after": TIME, "allow_on_submit": 1, "read_only": 1, "hidden": 1,
         "no_copy": 1, "depends_on": condition},
    ] + [
        {"insert_after": HISTORY, "fieldname": ORIGINAL_BY, "label": "Người nhận giấy gốc", "fieldtype": "Link", "options": "User",
         "allow_on_submit": 1, "read_only": 1, "no_copy": 1, "depends_on": condition},
        {"insert_after": ORIGINAL_BY, "fieldname": ORIGINAL_AT, "label": "Thời điểm nhận giấy gốc", "fieldtype": "Datetime",
         "allow_on_submit": 1, "read_only": 1, "no_copy": 1, "depends_on": condition},
        {"insert_after": ORIGINAL_AT, "fieldname": ORIGINAL_LOCATION, "label": "Vị trí lưu giấy gốc", "fieldtype": "Data",
         "allow_on_submit": 1, "read_only": 1, "no_copy": 1, "depends_on": condition},
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
    if doc.meta.has_field(HISTORY) and (doc.get(HISTORY) or '') != ((old.get(HISTORY) if old else None) or ''):
        frappe.throw("Không sửa lịch sử hồ sơ bản ký; tải bản mới trên phiếu để giữ dấu thay đổi")
    original_update = frappe.flags.get("kh_aph_nhan_goc") == doc.name
    if not original_update and any(str(doc.get(f) or "") != str((old.get(f) if old else None) or "") for f in ORIGINAL_FIELDS):
        frappe.throw("Dùng thao tác Nhận giấy gốc để ghi người, thời điểm và vị trí lưu")
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
    _record_history(doc, old)


def _record_history(doc, old):
    if not doc.meta.has_field(HISTORY):
        return
    keys = (FILE, NOTE, ACTOR, TIME, *ORIGINAL_FIELDS)
    def state(source):
        return {key: str((source.get(key) if source else None) or '') for key in keys}
    before, after = state(old), state(doc)
    if before == after:
        return
    raw = old.get(HISTORY) if old else None
    history = json.loads(raw) if raw else {'files': [], 'events': []}
    if not isinstance(history, dict) or set(history) != {'files', 'events'}:
        frappe.throw('Lịch sử bản ký cần quản trị kiểm tra, không tự ghi đè')
    files = history['files']
    for value in (before[FILE], after[FILE]):
        if value and value not in files:
            files.append(value)
    history['events'].append({'by': frappe.session.user, 'at': str(now_datetime()), 'before': before, 'after': after})
    doc.set(HISTORY, json.dumps(history, ensure_ascii=False, sort_keys=True))


def _file_in_use(url):
    # Giữ cả bản trên phiếu đã hủy và phiên bản đã thay; không xóa blob rồi trông vào rollback DB.
    if frappe.db.exists('Delivery Note', {FILE: url}):
        return True
    if not frappe.get_meta('Delivery Note').has_field(HISTORY):
        return False
    return bool(frappe.db.sql(f"""SELECT name FROM `tabDelivery Note`
        WHERE IF(JSON_VALID(`{HISTORY}`), JSON_CONTAINS(`{HISTORY}`, %s, '$.files'), 0) LIMIT 1""",
        (json.dumps(url),)))


def prevent_delete(doc, method=None):
    if enabled() and (doc.get(FILE) or doc.get(HISTORY) or doc.get(ORIGINAL_BY)):
        frappe.throw('Giữ phiếu có hồ sơ ký hoặc giấy gốc để truy nguyên, kể cả sau hủy')


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
    warehouse_handoff = (cint(doc.get("kh_aph_mau_giao_nhan")) and doc.get("kh_aph_cach_giao") == "Vận chuyển"
                         and doc.get("kh_aph_delivery_state") == "Đang giao")
    if cint(doc.docstatus) != 1 or cint(doc.is_return) or (doc.get("kh_aph_delivery_state") != "Khách đã nhận" and not warehouse_handoff):
        frappe.throw("Chỉ đối chiếu bản ký sau khi xuất hàng; phiếu cũ cần khách đã nhận")
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
    """Không xóa tệp hiện tại hoặc phiên bản cũ đã được chọn làm hồ sơ."""
    if not enabled() or not doc.file_url or not frappe.get_meta("Delivery Note").has_field(FILE):
        return
    if _file_in_use(doc.file_url):
        frappe.throw("Tệp thuộc hồ sơ bản ký của phiếu giao; giữ cả bản cũ để truy nguyên")


def protect_file_update(doc, method=None):
    """Giữ quyền riêng tư/liên kết/nội dung của tệp đã được chọn trên phiếu."""
    if not enabled() or not frappe.get_meta("Delivery Note").has_field(FILE):
        return
    old = doc.get_doc_before_save()
    if not old or not old.file_url:
        return
    if not _file_in_use(old.file_url):
        return
    if any(doc.get(f) != old.get(f) for f in ("file_url", "is_private", "attached_to_doctype", "attached_to_name")) or doc.get("content"):
        frappe.throw("Tệp đang là bản ký. Tải tệp mới và thay trên phiếu để đối chiếu lại")


class HoSoFileMixin:
    def on_trash(self):
        # File.on_trash xóa blob trước doc_events; phải kiểm trước super(),
        # vì rollback CSDL không khôi phục được nội dung đã xóa trên đĩa.
        protect_file(self)
        return super().on_trash()


@frappe.whitelist(methods=["POST"])
def nhan_giay_goc(name, modified, location):
    """Giấy và ảnh độc lập: đã nhận giấy không đòi tải ảnh trước hoặc ghi thêm sổ."""
    if not enabled():
        frappe.throw("Hồ sơ giao nhận chưa được bật")
    if not isinstance(location, str) or not location.strip() or len(location.strip()) > 140 or any(ord(c) < 32 for c in location):
        frappe.throw("Ghi vị trí lưu giấy gốc, tối đa140ký tự")
    frappe.db.sql("SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE", name)
    doc = frappe.get_doc("Delivery Note", name, for_update=True)
    doc.check_permission("read")
    doc.check_permission("write")
    if cint(doc.docstatus) != 1 or cint(doc.is_return):
        frappe.throw("Nhận giấy gốc trên phiếu xuất đã ghi sổ")
    if doc.get(ORIGINAL_BY):
        if doc.get(ORIGINAL_LOCATION) != location.strip():
            frappe.throw("Phiếu đã nhận giấy gốc ở vị trí khác; đối soát trước khi chuyển tập")
        return {"name": doc.name, "location": doc.get(ORIGINAL_LOCATION), "received_by": doc.get(ORIGINAL_BY), "received_at": doc.get(ORIGINAL_AT)}
    if str(doc.modified) != str(modified):
        frappe.throw("Phiếu đã thay đổi; tải lại trước khi nhận giấy gốc", frappe.TimestampMismatchError)
    previous = frappe.flags.get("kh_aph_nhan_goc")
    frappe.flags.kh_aph_nhan_goc = doc.name
    try:
        doc.set(ORIGINAL_BY, frappe.session.user)
        doc.set(ORIGINAL_AT, now_datetime())
        doc.set(ORIGINAL_LOCATION, location.strip())
        doc.save()
        from frappe.utils import escape_html
        doc.add_comment("Comment", "Đã nhận giấy gốc, vị trí lưu: " + escape_html(location.strip()))
    finally:
        frappe.flags.kh_aph_nhan_goc = previous
    return {"name": doc.name, "location": doc.get(ORIGINAL_LOCATION), "received_by": doc.get(ORIGINAL_BY), "received_at": doc.get(ORIGINAL_AT)}
