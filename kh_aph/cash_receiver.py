"""Người nhận chỉ xác nhận đúng bàn giao được gửi cho mình, không mở sổ quỹ.

Capability sống trong receive, gắn actor và tuple hồ sơ sau khóa quỹ. Dùng service
bàn giao chuẩn; không có đường tạo JE tự do, sửa nguồn hay gửi/hoàn thay người giữ.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import frappe
from kh_aph import cash_closing as C, cash_custody as custody
from kh_aph.cash_closing_rules import money

ROLE = 'Nhận bàn giao tiền'
ROLES = {ROLE, 'Kế toán bán hàng'}
_SOURCE = ContextVar('cash_receiver_source', default=None)


def active():
    source = _SOURCE.get()
    return source is not None and source[0] == frappe.session.user


def guard():
    from kh_aph import cash_handover as H
    roles = C.roles_for()
    if not H.enabled() or not C.enabled() or not custody.enabled():
        frappe.throw('Cần bật người giữ, chốt ca và bàn giao tiền')
    if not roles & ROLES or roles & {'APH Không xem giá vốn', 'Kế toán nhà máy'}:
        frappe.throw('Chưa được cấp quyền nhận bàn giao tiền', frappe.PermissionError)


def _tuple(doc):
    return (doc.name, doc.company, doc.from_account, doc.to_account,
            doc.from_holder, doc.to_holder, money(doc.requested_amount),
            doc.get('factory_source'), doc.get('reversal_of'), doc.docstatus)


def bound(doc):
    return active() and doc.doctype == 'APH Ban giao tien' and _tuple(doc) == _SOURCE.get()[1]


def check(doc, permission='read'):
    if not bound(doc) or permission not in ('read', 'write'):
        frappe.throw('Không có quyền trên hồ sơ bàn giao này', frappe.PermissionError)
    # Chỉ instance nguồn đã khóa, chỉ service receive gọi save dưới _updating.
    doc.flags.ignore_permissions = True


def target(company, account):
    if not active():
        frappe.throw('Thiếu phạm vi nhận bàn giao', frappe.PermissionError)
    source = _SOURCE.get()[1]
    if company != source[1] or account not in source[2:4]:
        frappe.throw('Tài khoản ngoài bàn giao được chỉ định', frappe.PermissionError)
    doc = frappe.get_doc('Account', account)
    doc.check_permission('read')
    if doc.company != company or doc.account_type not in ('Cash','Bank') or doc.is_group or doc.disabled or doc.account_currency != 'VND':
        frappe.throw('Chọn tài khoản tiền VND chi tiết đang hoạt động đúng đơn vị')
    return doc


def cash_scope(company, account):
    if target(company, account).account_type != 'Cash':
        frappe.throw('Nguồn phải là quỹ tiền mặt')


def scope(doc):
    guard()
    if not bound(doc):
        frappe.throw('Hồ sơ nhận vừa đổi hoặc ngoài phạm vi', frappe.PermissionError)
    co = frappe.get_doc('Company', doc.company)
    co.check_permission('read')
    if co.default_currency != 'VND':
        frappe.throw('Bàn giao chỉ hỗ trợ VND')
    cash_scope(doc.company, doc.from_account)
    return target(doc.company, doc.to_account)


def ledger(company, account):
    cash_scope(company, account)
    from kh_aph import personal_cash
    return personal_cash._ledger(company, account)


@contextmanager
def operation(doc):
    guard()
    if (doc.docstatus != 1 or doc.to_holder != frappe.session.user or
            doc.from_holder == doc.to_holder or doc.get('factory_source') or doc.get('reversal_of')):
        frappe.throw('Chỉ nhận đúng bàn giao thông thường đã gửi cho mình', frappe.PermissionError)
    token = _SOURCE.set((frappe.session.user, _tuple(doc)))
    try:
        scope(doc)
        yield
    finally:
        _SOURCE.reset(token)


def route(function):
    @wraps(function)
    def wrapped(name, *args, **kwargs):
        roles = C.roles_for()
        if not roles & ROLES or roles & (C.MANAGERS | {'Accounts User'}):
            return function(name, *args, **kwargs)
        guard()
        from kh_aph import cash_handover as H
        preliminary = frappe.get_doc(H.DT, name)
        preliminary.check_permission('read')
        if preliminary.get('factory_source'):
            # Nguồn nhà máy giữ adapter riêng và kiểm đúng người/nguồn như trước.
            return function(name, *args, **kwargs)
        if preliminary.to_holder != frappe.session.user or preliminary.from_holder == frappe.session.user:
            frappe.throw('Không được nhận thay hoặc tự nhận tiền mình giao', frappe.PermissionError)
        frappe.get_doc('Company', preliminary.company).check_permission('read')
        custody._person(frappe.session.user, preliminary.company)
        frappe.db.sql("select name from `tabAccount` where company=%s and account_type='Cash' order by name for update", (preliminary.company,))
        source = frappe.get_doc(H.DT, name, for_update=True)
        if _tuple(source) != _tuple(preliminary):
            frappe.throw('Bàn giao vừa đổi; tải lại để kiểm đếm')
        with operation(source):
            result = function(name, *args, **kwargs)
            return {key:value for key,value in result.items() if key != 'journal_entry'}
    return wrapped


def schema():
    from kh_aph import cash_handover as H
    if not H.enabled():
        return
    from frappe.permissions import add_permission, update_permission_property
    if not frappe.db.exists('Role', ROLE):
        frappe.get_doc({'doctype':'Role','role_name':ROLE,'desk_access':1}).insert()
    for dt in (H.DT, 'Company', 'Account'):
        add_permission(dt, ROLE, 0)
        update_permission_property(dt, ROLE, 0, 'read', 1, validate=False)

    # Bán hàng được gửi/hủy đề nghị của mình; hook giữ phạm vi actor và bất biến.
    for permission in ('read','write','create','submit','cancel','print'):
        add_permission(H.DT, 'Kế toán bán hàng', 0)
        update_permission_property(H.DT, 'Kế toán bán hàng', 0, permission, 1, validate=False)
