"""Thông tin giao nhận gắn phiếu nguồn, dùng cờ Trung tâm Bán hàng hiện có."""
import frappe
from frappe.utils import cint, now_datetime
from kh_aph.delivery_info_rules import normalize, PICKUP_METHODS, EXTRA_LABELS

METHOD = "kh_aph_cach_giao"
RECIPIENT = "kh_aph_nguoi_nhan_tai_kho"
PHONE = "kh_aph_dien_thoai_nhan"
DISPATCHER = "kh_aph_nguoi_thuc_giao"
HANDED_AT = "kh_aph_ban_giao_luc"
HANDED_BY = "kh_aph_ban_giao_boi"
MAPPING = {"delivery_method": METHOD, "recipient": RECIPIENT, "phone": PHONE,
           "driver_name": "driver_name", "vehicle_no": "vehicle_no", "shipping_address_name": "shipping_address_name"}
EXTRA_MAPPING = {"carrier": "kh_aph_nha_xe_dot", "carrier_phone": "kh_aph_sdt_nha_xe_dot",
                 "authorization": "kh_aph_chi_dinh_nhan", "customer_signature": "kh_aph_can_ky_khach"}
VERSION = "kh_aph_mau_giao_nhan"


def enabled():
    return cint(frappe.conf.get("kh_aph_trung_tam_ban"))


def fields():
    return [
        {"fieldname": METHOD, "label": "Cách giao đợt này", "fieldtype": "Select", "options": "\nVận chuyển\nKhách đến lấy\nXe khách đến lấy",
         "insert_after": "customer", "no_copy": 1},
        {"fieldname": RECIPIENT, "label": "Người thực nhận hàng tại kho", "fieldtype": "Data", "insert_after": METHOD, "no_copy": 1},
        {"fieldname": PHONE, "label": "Điện thoại người nhận", "fieldtype": "Data", "insert_after": RECIPIENT, "no_copy": 1},
        {"fieldname": DISPATCHER, "label": "Người thực giao hàng tại kho", "fieldtype": "Data", "insert_after": PHONE, "no_copy": 1,
         "description": "Kho ghi họ tên người trực tiếp giao, khác tài khoản nhập/xác nhận trên phần mềm."},
        {"fieldname": HANDED_AT, "label": "Thời điểm xác nhận xuất tại kho", "fieldtype": "Datetime", "insert_after": DISPATCHER,
         "read_only": 1, "no_copy": 1},
        {"fieldname": HANDED_BY, "label": "Người xác nhận xuất trên hệ thống", "fieldtype": "Link", "options": "User",
         "insert_after": HANDED_AT, "read_only": 1, "no_copy": 1},
    ] + [
        {"fieldname": VERSION, "label": "Phiên bản thông tin giao nhận", "fieldtype": "Int", "default": "0",
         "read_only": 1, "hidden": 1, "no_copy": 1},
    ] + [
        {"fieldname": EXTRA_MAPPING[key], "label": label, "fieldtype": "Select" if key == "customer_signature" else "Data",
         **({"options": "\nCó\nKhông"} if key == "customer_signature" else {}), "no_copy": 1,
         "insert_after": RECIPIENT}
        for key, label in EXTRA_LABELS.items()
    ] + [
        {"fieldname": "kh_aph_nguon_bao_nhan", "label": "Nguồn báo khách nhận", "fieldtype": "Select",
         "options": "\nKhách báo\nNhà xe báo", "allow_on_submit": 1, "read_only": 1, "no_copy": 1},
        {"fieldname": "kh_aph_ngay_khach_nhan", "label": "Ngày khách nhận thực tế", "fieldtype": "Date",
         "allow_on_submit": 1, "read_only": 1, "no_copy": 1},
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
    if not values:
        return
    for key, value in values.items():
        if key == "shipping_address_name" and not value:
            continue  # Khi lập đợt, để trống nghĩa là giữ địa chỉ đã có từ từng SO nguồn.
        doc.set((MAPPING | EXTRA_MAPPING)[key], value)
    if any(key in values for key in EXTRA_MAPPING):
        doc.set(VERSION, 1)
    from frappe.contacts.doctype.address.address import get_address_display
    name = doc.get("shipping_address_name")
    doc.shipping_address = get_address_display(name) if name else ""


def validate(doc, method=None):
    if not enabled() or cint(doc.is_return) or not doc.meta.has_field(METHOD):
        return
    old = doc.get_doc_before_save()
    if any(str(doc.get(f) or "") != str((old.get(f) if old else None) or "") for f in (HANDED_AT, HANDED_BY)):
        frappe.throw("Thời điểm và người xác nhận xuất do hệ thống ghi; không sửa trực tiếp")
    if old and old.get(METHOD) and not doc.get(METHOD):
        frappe.throw("Không xóa cách giao của phiếu đã có thông tin giao nhận")
    if not doc.get(METHOD):
        return  # Phiếu cũ và lối lập chuẩn chưa có thông tin đợt: giữ nguyên hành vi trước nâng cấp.
    if cint(doc.docstatus) == 0 and any(doc.get(f) for f in EXTRA_MAPPING.values()):
        doc.set(VERSION, 1)
    try:
        mapping = MAPPING | EXTRA_MAPPING if cint(doc.get(VERSION)) else MAPPING
        values = normalize({key: doc.get(field) for key, field in mapping.items()})
    except ValueError as exc:
        frappe.throw(str(exc))
    if not old or cint(old.docstatus) == 0 or doc.get("shipping_address_name") != old.get("shipping_address_name"):
        check_address(doc.customer, values["shipping_address_name"])
    if old and cint(old.docstatus) == 1:
        if any((doc.get(f) or "") != (old.get(f) or "") for f in (*MAPPING.values(), *EXTRA_MAPPING.values(), VERSION, DISPATCHER)):
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
    if pickup != (doc.get(METHOD) in PICKUP_METHODS):
        frappe.throw("Thao tác xác nhận không khớp cách giao trên phiếu; kiểm lại Vận chuyển/Khách đến lấy")

    doc.set(HANDED_AT, now_datetime())
    doc.set(HANDED_BY, frappe.session.user)


@frappe.whitelist()
def recent_carriers():
    """Chỉ gợi ý nhà xe từ các phiếu người gọi có quyền đọc, không truy danh mục chung bỏ qua phạm vi."""
    if not enabled():
        frappe.throw("Thông tin giao nhận chưa được bật")
    rows = frappe.get_list("Delivery Note", filters={"docstatus": ["!=", 2], "is_return": 0,
        EXTRA_MAPPING["carrier"]: ["is", "set"]}, fields=[EXTRA_MAPPING["carrier"], EXTRA_MAPPING["carrier_phone"]],
        order_by="modified desc", limit_page_length=100)
    result, seen = [], set()
    for row in rows:
        name, phone = row.get(EXTRA_MAPPING["carrier"]), row.get(EXTRA_MAPPING["carrier_phone"])
        if name not in seen:
            result.append({"carrier": name, "carrier_phone": phone or ""})
            seen.add(name)
    return result
