"""Opt-in delivery states; native DN submission owns stock and receivable."""
import frappe
from frappe.utils import cint, now_datetime
from kh_aph.delivery_receivable import enabled

STATE = 'kh_aph_delivery_state'
ACTOR = 'kh_aph_delivery_actor'
TIME = 'kh_aph_delivery_at'
WAITING = 'Chờ xuất'
TRANSIT = 'Đang giao'
RECEIVED = 'Khách đã nhận'
FIELDS = (STATE, ACTOR, TIME)


def stamp(doc, state):
    doc.set(STATE, state)
    doc.set(ACTOR, frappe.session.user)
    doc.set(TIME, now_datetime())


def validate(doc, method=None):
    if not enabled() or cint(doc.is_return):
        return
    old = doc.get_doc_before_save()
    if not old:
        if doc.get(STATE) not in (None, '', WAITING) or doc.get(ACTOR) or doc.get(TIME):
            frappe.throw('Trạng thái giao hàng phải được xác nhận bằng thao tác giao/nhận')
        stamp(doc, WAITING)
    elif not doc.flags.kh_aph_delivery_transition:
        if any(str(doc.get(f) or '') != str(old.get(f) or '') for f in FIELDS):
            frappe.throw('Không được sửa trực tiếp trạng thái hoặc lịch sử giao hàng')


def before_submit(doc, method=None):
    if enabled() and not cint(doc.is_return):
        stamp(doc, RECEIVED if doc.flags.kh_aph_pickup else TRANSIT)


def before_update_after_submit(doc, method=None):
    validate(doc, method)


@frappe.whitelist(methods=['POST'])
def confirm(name, action):
    if not enabled():
        frappe.throw('Quy trình giao hàng chưa được bật')
    if action not in ('handoff', 'pickup', 'receive'):
        frappe.throw('Thao tác giao hàng không hợp lệ')
    frappe.db.sql('SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE', name)
    doc = frappe.get_doc('Delivery Note', name)
    doc.check_permission('write')
    if cint(doc.is_return) or cint(doc.docstatus) == 2:
        frappe.throw('Không xác nhận giao hàng trên phiếu trả lại hoặc phiếu đã hủy')
    current = doc.get(STATE)
    if action == 'receive':
        if cint(doc.docstatus) != 1 or current not in (TRANSIT, RECEIVED):
            frappe.throw('Chỉ xác nhận nhận hàng sau khi xuất hàng')
        if current == RECEIVED:
            return doc.as_dict()
        doc.flags.kh_aph_delivery_transition = True
        stamp(doc, RECEIVED)
        doc.save()
    else:
        target = RECEIVED if action == 'pickup' else TRANSIT
        if cint(doc.docstatus) == 1 and current == target:
            return doc.as_dict()
        if cint(doc.docstatus) != 0 or current != WAITING:
            frappe.throw('Phiếu không còn ở trạng thái chờ xuất')
        doc.check_permission('submit')
        doc.flags.kh_aph_pickup = action == 'pickup'
        doc.submit()
    # Frappe commits the request only after all native stock/credit hooks succeed.
    return doc.as_dict()
