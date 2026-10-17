"""Thông tin giao nhận gắn phiếu nguồn, dùng cờ Trung tâm Bán hàng hiện có."""
import frappe
from frappe.utils import cint
from kh_aph.delivery_info_rules import normalize

METHOD = "kh_aph_cach_giao"
RECIPIENT = "kh_aph_nguoi_nhan_tai_kho"
PHONE = "kh_aph_dien_thoai_nhan"
DISPATCHER = "kh_aph_nguoi_thuc_giao"
MAPPING = {"delivery_method": METHOD, "recipient": RECIPIENT, "phone": PHONE,
           "driver_name": "driver_name", "vehicle_no": "vehicle_no", "shipping_address_name": "shipping_address_name"}


def enabled():
    return cint(frappe.conf.get("kh_aph_trung_tam_ban"))


def fields():
    return [
        {"fieldname": METHOD, "label": "Cách giao đợt này", "fieldtype": "Select", "options": "\nVận chuyển\nKhách đến lấy",
         "insert_after": "customer", "no_copy": 1},
        {"fieldname": RECIPIENT, "label": "Người thực nhận hàng tại kho", "fieldtype": "Data", "insert_after": METHOD, "no_copy": 1},
        {"fieldname": PHONE, "label": "Điện thoại người nhận", "fieldtype": "Data", "insert_after": RECIPIENT, "no_copy": 1},
        {"fieldname": DISPATCHER, "label": "Người thực giao hàng tại kho", "fieldtype": "Data", "insert_after": PHONE, "no_copy": 1,
         "description": "Kho ghi họ tên người trực tiếp giao, khác tài khoản nhập/xác nhận trên phần mềm."},
    ]


def check_address(customer, name):
    if not name:
        return
    address = frappe.get_doc("Address", name)
    address.check_permission("read")
    if address.disabled or not any(r.link_doctype == "Customer" and r.link_name == customer for r in address.links):
        frappe.throw("Địa chỉ giao phải đang sử dụng và liên kết đúng khách hàng của phiếu")


def parse(values, customer):
    try:
        result = normalize(frappe.parse_json(values) if isinstance(values, str) else values)
    except ValueError as exc:
        frappe.throw(str(exc))
    if result:
        check_address(customer, result["shipping_address_name"])
    return result


def apply(doc, values):
    for key, value in values.items():
        doc.set(MAPPING[key], value)
    if "shipping_address_name" in values:
        from frappe.contacts.doctype.address.address import get_address_display
        doc.shipping_address = get_address_display(values["shipping_address_name"]) if values["shipping_address_name"] else ""


def validate(doc, method=None):
    if not enabled() or cint(doc.is_return) or not doc.meta.has_field(METHOD):
        return
    old = doc.get_doc_before_save()
    if old and old.get(METHOD) and not doc.get(METHOD):
        frappe.throw("Không xóa cách giao của phiếu đã có thông tin giao nhận")
    if not doc.get(METHOD):
        return  # Phiếu cũ và lối lập chuẩn chưa có thông tin đợt: giữ nguyên hành vi trước nâng cấp.
    try:
        values = normalize({key: doc.get(field) for key, field in MAPPING.items()})
    except ValueError as exc:
        frappe.throw(str(exc))
    if not old or cint(old.docstatus) == 0 or doc.get("shipping_address_name") != old.get("shipping_address_name"):
        check_address(doc.customer, values["shipping_address_name"])
    if old and cint(old.docstatus) == 1:
        if any((doc.get(f) or "") != (old.get(f) or "") for f in (*MAPPING.values(), DISPATCHER)):
            frappe.throw("Phiếu đã xuất: không ghi đè thông tin giao nhận; dùng quy trình điều chỉnh có lưu lịch sử")
    dispatcher = doc.get(DISPATCHER) or ""
    if not isinstance(dispatcher, str) or len(dispatcher.strip()) > 140 or any(ord(c) < 32 for c in dispatcher):
        frappe.throw("Tên người thực giao không hợp lệ")
    if dispatcher != ((old.get(DISPATCHER) or "") if old else "") and not frappe.has_permission("Delivery Note", "submit", doc=doc):
        frappe.throw("Người có quyền xác nhận xuất kho mới được ghi người thực giao", frappe.PermissionError)
    if cint(doc.docstatus) == 0:
        apply(doc, values)
        doc.set(DISPATCHER, dispatcher.strip())


def before_submit(doc, method=None):
    if not enabled() or cint(doc.is_return) or not doc.get(METHOD):
        return
    if not (doc.get(DISPATCHER) or "").strip():
        frappe.throw("Kho ghi tên người trực tiếp giao hàng trước khi xác nhận xuất")
    pickup = frappe.flags.get("kh_aph_delivery_pickup") == doc.name
    if pickup != (doc.get(METHOD) == "Khách đến lấy"):
        frappe.throw("Thao tác xác nhận không khớp cách giao trên phiếu; kiểm lại Vận chuyển/Khách đến lấy")
