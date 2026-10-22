"""Giấy khách ký tại đích khi có yêu cầu; độc lập bản ký giao nhà xe, không ghi sổ."""
from contextvars import ContextVar

import frappe
from frappe.utils import cint, now_datetime

FILE = 'kh_aph_ban_ky_khach'
NOTE = 'kh_aph_ghi_chu_ky_khach'
ACTOR = 'kh_aph_kiem_ky_khach_boi'
TIME = 'kh_aph_kiem_ky_khach_luc'
ORIGINAL_BY = 'kh_aph_nhan_goc_khach_boi'
ORIGINAL_AT = 'kh_aph_nhan_goc_khach_luc'
LOCATION = 'kh_aph_vi_tri_goc_khach'
KEYS = (FILE, NOTE, ACTOR, TIME, ORIGINAL_BY, ORIGINAL_AT, LOCATION)
_INTERNAL = ContextVar('customer_delivery_proof', default=None)


def required(doc):
    return (cint(doc.get('kh_aph_mau_giao_nhan')) == 1 and not cint(doc.get('is_return'))
            and doc.get('kh_aph_cach_giao') == 'Vận chuyển' and doc.get('kh_aph_can_ky_khach') == 'Có')


def fields():
    condition = 'eval:doc.docstatus==1 && !doc.is_return && doc.kh_aph_mau_giao_nhan==1 && doc.kh_aph_cach_giao=="Vận chuyển" && doc.kh_aph_can_ky_khach=="Có"'
    result = []
    previous = 'kh_aph_vi_tri_goc'
    for name, label, kind in ((FILE, 'Bản khách ký tại đích', 'Attach'), (NOTE, 'Ghi chú bản khách ký', 'Small Text'),
            (ACTOR, 'Người kiểm bản khách ký', 'Link'), (TIME, 'Thời điểm kiểm bản khách ký', 'Datetime'),
            (ORIGINAL_BY, 'Người nhận gốc khách ký', 'Link'), (ORIGINAL_AT, 'Thời điểm nhận gốc khách ký', 'Datetime'),
            (LOCATION, 'Vị trí gốc khách ký', 'Data')):
        result.append({'fieldname': name, 'label': label, 'fieldtype': kind, 'insert_after': previous,
            'depends_on': condition, 'allow_on_submit': 1, 'no_copy': 1,
            'read_only': int(name not in (FILE, NOTE)), **({'options': 'User'} if kind == 'Link' else {})})
        previous = name
    return result


def validate(doc, old):
    if not doc.meta.has_field(FILE):
        return
    internal = _INTERNAL.get() == id(doc)
    changed = lambda key: str(doc.get(key) or '') != str((old.get(key) if old else None) or '')
    if not internal and any(changed(key) for key in (ACTOR, TIME, ORIGINAL_BY, ORIGINAL_AT, LOCATION)):
        frappe.throw('Dùng thao tác Nhận hồ sơ khách ký để giữ người, thời điểm và giấy gốc')
    if any(changed(key) for key in KEYS):
        if cint(doc.docstatus) != 1 or not required(doc):
            frappe.throw('Hồ sơ khách ký tại đích chỉ dùng cho chuyến đã xuất có yêu cầu khách ký')
        if doc.get(FILE):
            from kh_aph.ho_so_giao_nhan import _file
            _file(doc, FILE)
        if not internal and (changed(FILE) or changed(NOTE)):
            doc.set(ACTOR, None); doc.set(TIME, None)


@frappe.whitelist(methods=['POST'])
def receive(name, modified, file_url=None, location=None, received_on=None):
    from kh_aph.ho_so_giao_nhan import enabled, _file
    if not enabled():
        frappe.throw('Hồ sơ giao nhận chưa được bật')
    if any(value is not None and not isinstance(value, str) for value in (file_url, location)):
        frappe.throw('Thông tin hồ sơ khách ký không hợp lệ')
    location = (location or '').strip()
    if len(location) > 140 or any(ord(c) < 32 or c in '<>' for c in location):
        frappe.throw('Ghi vị trí giấy gốc bằng chữ thông thường, tối đa140ký tự')
    frappe.db.sql('SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE', name)
    doc = frappe.get_doc('Delivery Note', name, for_update=True)
    doc.check_permission('read'); doc.check_permission('write')
    if cint(doc.docstatus) != 1 or not required(doc):
        frappe.throw('Chọn chuyến đã xuất có yêu cầu khách ký tại đích')
    selected = file_url or doc.get(FILE)
    if not selected and not location and not doc.get(ORIGINAL_BY):
        frappe.throw('Chọn tệp khách ký hoặc ghi vị trí đã nhận giấy gốc; ảnh có thể bổ sung sau')
    if (doc.get(ACTOR) and doc.get('kh_aph_delivery_state') == 'Khách đã nhận'
            and (not file_url or doc.get(FILE) == file_url) and (not location or doc.get(LOCATION) == location)):
        return {'name': doc.name, 'received_by': doc.get(ACTOR), 'original_at': doc.get(ORIGINAL_AT)}
    if str(doc.modified) != str(modified):
        frappe.throw('Phiếu đã thay đổi; tải lại trước khi nhận hồ sơ khách ký', frappe.TimestampMismatchError)
    if doc.get('kh_aph_delivery_state') != 'Khách đã nhận':
        from kh_aph.delivery_status import confirm
        confirm(name, 'receive', reported_by='Khách báo', received_on=received_on)
        doc = frappe.get_doc('Delivery Note', name, for_update=True)
    previous_file = doc.get(FILE)
    token = _INTERNAL.set(id(doc))
    try:
        if selected:
            doc.set(FILE, selected)
            _file(doc, FILE)
        if location:
            doc.set(LOCATION, location)
            if not doc.get(ORIGINAL_BY):
                doc.set(ORIGINAL_BY, frappe.session.user); doc.set(ORIGINAL_AT, now_datetime())
        if not doc.get(ACTOR) or (file_url and doc.get(FILE) != previous_file):
            doc.set(ACTOR, frappe.session.user); doc.set(TIME, now_datetime())
        doc.save()
    finally:
        _INTERNAL.reset(token)
    return {'name': doc.name, 'received_by': doc.get(ACTOR), 'original_at': doc.get(ORIGINAL_AT)}
