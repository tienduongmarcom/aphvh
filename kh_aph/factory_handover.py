"""Nối phiếu nhà máy vào đúng một bàn giao; capability chỉ sống trong một thao tác.

Không cấp GL/JE/DocPerm cho nhà máy. Context do server mở sau kiểm nguồn,
Company, actor và khóa quỹ; mọi hồ sơ bên trong phải khớp nguồn đã khóa.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

import frappe
from frappe.utils import cint
from kh_aph import cash_closing as C, cash_custody as custody
from kh_aph.cash_closing_rules import money
from kh_aph.cash_transaction import retry_rpc

_SOURCE = ContextVar('factory_handover_source', default=None)
SOURCE_FIELD = 'factory_source'
LINK = 'ban_giao_tien'
TARGET = 'tai_khoan_nhan'
SOURCE_ACCOUNT = 'quy_giao'
FLAG = 'kh_aph_factory_handover'

def enabled():
    return cint(frappe.conf.get(FLAG))


def _personal():
    from kh_aph import personal_cash
    return personal_cash


def active():
    value = _SOURCE.get()
    return value is not None and value[0] == frappe.session.user


def guard():
    from kh_aph import factory_cash as F, cash_handover as H
    if not enabled() or not F.enabled() or not H.enabled() or not C.enabled() or not custody.enabled():
        frappe.throw('Cần bật quỹ nhà máy, người giữ, chốt ca và bàn giao')
    if frappe.session.user == 'Guest' or not C.roles_for() & _personal().ROLES:
        frappe.throw('Chưa có quyền thao tác tiền nhà máy', frappe.PermissionError)


def _account(company, name):
    from frappe.permissions import has_user_permission
    if not isinstance(name, str) or not name:
        frappe.throw('Chọn quỹ/ngân hàng nhận trước khi gửi')
    doc = frappe.get_doc('Account', name)
    if C.roles_for() & _personal().RESTRICTED:
        if not has_user_permission(doc, user=frappe.session.user, ptype='read'):
            frappe.throw('Tài khoản ngoài phạm vi được cấp', frappe.PermissionError)
    else:
        doc.check_permission('read')
    if doc.company != company or doc.account_type not in ('Cash', 'Bank') or doc.is_group or doc.disabled or doc.account_currency != 'VND':
        frappe.throw('Chọn tài khoản tiền chi tiết VND đang hoạt động cùng đơn vị')
    return doc


def _load(name):
    from kh_aph import factory_cash as F
    guard()
    preliminary = frappe.get_doc(F.DT, name)
    # Khóa Company/Cash trước nguồn, cùng thứ tự với GL và service bàn giao.
    co = frappe.get_doc('Company', preliminary.company)
    co.check_permission('read')
    if co.default_currency != 'VND':
        frappe.throw('Bàn giao chỉ hỗ trợ VND')
    custody._person(frappe.session.user, preliminary.company)
    frappe.db.sql("select name from `tabAccount` where company=%s and account_type='Cash' order by name for update", (preliminary.company,))
    source = frappe.get_doc(F.DT, name, for_update=True)
    if source.company != preliminary.company or source.loai != F.LOAI_BAN_GIAO:
        frappe.throw('Chọn đúng phiếu bàn giao nhà máy; tải lại nếu đơn vị vừa đổi')
    if frappe.session.user not in (source.get(custody.HOLDER), source.nguoi_nhan):
        frappe.throw('Chỉ người giữ hoặc người nhận của phiếu được thao tác', frappe.PermissionError)
    return source


def _bound(doc):
    if not active():
        return False
    source = _SOURCE.get()[1]
    if doc.doctype != 'APH Ban giao tien':
        return False
    if doc.get('reversal_of'):
        if not source.get(LINK) or doc.reversal_of != source.get(LINK) or doc.get(SOURCE_FIELD):
            return False
        root = frappe.get_doc('APH Ban giao tien', source.get(LINK), for_update=True)
        return (doc.company, doc.from_account, doc.to_account, doc.from_holder, doc.to_holder, money(doc.requested_amount)) == (root.company, root.to_account, root.from_account, root.to_holder, root.from_holder, money(root.received_amount))
    return (doc.get(SOURCE_FIELD) == source.name and
        (doc.company, doc.from_account, doc.to_account, doc.from_holder, doc.to_holder, money(doc.requested_amount)) ==
        (source.company, source.get(SOURCE_ACCOUNT), source.get(TARGET), source.get(custody.HOLDER), source.nguoi_nhan, money(source.tong_tien)))


def check(doc, permission='read'):
    """Bypass native H chỉ cho đúng nguồn/tuple dưới capability đã kiểm actor."""
    if not _bound(doc):
        doc.check_permission(permission)
        return
    doc.flags.ignore_permissions = True


def _source_name(doc):
    if doc.get(SOURCE_FIELD):
        return doc.get(SOURCE_FIELD)
    if doc.get('reversal_of'):
        return frappe.db.get_value('APH Ban giao tien', doc.reversal_of, SOURCE_FIELD)
    return None


def validate_origin(doc):
    source = _source_name(doc)
    old = doc.get_doc_before_save()
    if old and old.get(SOURCE_FIELD) != doc.get(SOURCE_FIELD):
        frappe.throw('Không thêm, đổi hoặc gỡ nguồn quỹ nhà máy')
    if source and not _bound(doc):
        frappe.throw('Dùng thao tác trên phiếu quỹ nhà máy; không lập/sửa bàn giao nguồn này bằng tay', frappe.PermissionError)
    if not doc.get(SOURCE_FIELD):
        doc.set(SOURCE_FIELD, None)


def cash_scope(company, account):
    if not active():
        return C.scope(company, account)
    source = _SOURCE.get()[1]
    if company != source.company or account not in (source.get(SOURCE_ACCOUNT), source.get(TARGET)):
        frappe.throw('Quỹ ngoài nguồn bàn giao', frappe.PermissionError)
    doc = _account(company, account)
    if doc.account_type != 'Cash':
        frappe.throw('Chọn quỹ tiền mặt')


def target(company, account):
    if not active():
        from kh_aph import cash_handover as H
        return H.target(company, account)
    source = _SOURCE.get()[1]
    if company != source.company or account not in (source.get(SOURCE_ACCOUNT), source.get(TARGET)):
        frappe.throw('Tài khoản ngoài nguồn bàn giao', frappe.PermissionError)
    return _account(company, account)


def scope(doc):
    if not _bound(doc):
        frappe.throw('Không có capability đúng hồ sơ nhà máy', frappe.PermissionError)
    source = _SOURCE.get()[1]
    # Nhà máy chỉ có quyền trên quỹ cấu hình; thay cấu hình phải xử lý hồ sơ cũ
    # trước, không âm thầm chuyển trách nhiệm sang một quỹ mới.
    from kh_aph import factory_cash as F
    if source.get(SOURCE_ACCOUNT) != F._quy(source.company):
        frappe.throw('Quỹ nhà máy đã đổi; đối chiếu hồ sơ cũ trước khi tiếp tục')
    if C.roles_for() & _personal().RESTRICTED:
        _personal()._scope(source.company, source.get(SOURCE_ACCOUNT))
    for account in {doc.from_account, doc.to_account}:
        _account(doc.company, account)
    return target(doc.company, doc.to_account)


def ledger_reader():
    return _personal()._ledger if active() else None


@contextmanager
def operation(source):
    guard()
    token = _SOURCE.set((frappe.session.user, source))
    try:
        yield
    finally:
        _SOURCE.reset(token)


def _sync(source):
    from kh_aph import cash_handover as H, factory_cash as F
    root = frappe.get_doc(H.DT, source.get(LINK), for_update=True)
    if root.status == 'Đã hủy':
        state = F.TT_HUY
    elif root.status in ('Có chênh lệch', 'Vượt nguồn cần xử lý'):
        state = 'Chênh lệch đã đối chiếu' if root.issue_state == 'Đã đối chiếu' else 'Chênh lệch chờ điều tra'
    elif root.status == 'Đã nhận':
        state = 'Đã nhận'
    else:
        state = F.TT_CHO_NHAN
    source.db_set({'trang_thai': state, 'so_thuc_nhan': root.received_amount,
        'nhan_boi': root.received_by, 'nhan_luc': root.received_at, 'journal_entry': root.journal_entry, 'xu_ly_chenh_lech': root.issue_state})


def _result(value):
    if C.roles_for() & _personal().RESTRICTED:
        return {k: v for k, v in value.items() if k != 'journal_entry'}
    return value


def route(function):
    """Lối native và lối cũ đi qua cùng capability, khóa và service canonical."""
    @wraps(function)
    def wrapped(name, *args, **kwargs):
        if not enabled():
            return function(name, *args, **kwargs)
        if not active():
            from kh_aph import cash_handover as H
            preliminary = frappe.get_doc(H.DT, name)
            source_name = _source_name(preliminary)
            if source_name:
                source = _load(source_name)
                if source.docstatus != 1 or not source.get(LINK):
                    frappe.throw('Nguồn bàn giao chưa được gửi hoặc đã hủy')
                with operation(source):
                    result = function(name, *args, **kwargs)
                    _sync(source)
                    return _result(result)
        return function(name, *args, **kwargs)
    return wrapped


def send_source(source):
    """Gọi trong on_submit; toàn bộ nguồn/H/giữ chỗ cùng transaction."""
    from kh_aph import cash_handover as H, factory_cash as F
    guard()
    if source.get(custody.HOLDER) != frappe.session.user:
        frappe.throw('Người thực giữ phải tự gửi bàn giao nhà máy', frappe.PermissionError)
    source.quy_giao = F._quy(source.company)
    if not source.get(TARGET):
        frappe.throw('Chọn quỹ/ngân hàng nhận trước khi gửi bàn giao')
    for user, account in [(source.get(custody.HOLDER), source.quy_giao), (source.nguoi_nhan, source.get(TARGET))]:
        custody._person(user, source.company)
        roles = C.roles_for(user)
        if not roles & _personal().ROLES:
            frappe.throw('Người giao/nhận chưa có vai trò thao tác tiền', frappe.PermissionError)
        if roles & _personal().RESTRICTED and account != source.quy_giao:
            frappe.throw('Người nhà máy chỉ nhận vào quỹ nhà máy được cấu hình', frappe.PermissionError)
    with operation(source):
        existing = frappe.db.sql(f'select name from `tab{H.DT}` where factory_source=%s for update', (source.name,))
        if existing:
            root = frappe.get_doc(H.DT, existing[0][0], for_update=True)
            if not _bound(root) or root.docstatus != 1:
                frappe.throw('Nguồn đã có bàn giao khác hoặc đã hủy; giữ lịch sử và lập phiếu mới')
        else:
            root = frappe.get_doc({'doctype': H.DT, SOURCE_FIELD: source.name, 'company': source.company,
                'from_account': source.quy_giao, 'to_account': source.get(TARGET),
                'from_holder': source.get(custody.HOLDER), 'to_holder': source.nguoi_nhan,
                'requested_amount': source.tong_tien, 'reason': 'Bàn giao từ phiếu nhà máy ' + source.name})
            check(root, 'create')
            root.insert()
            root.submit()
        source.db_set({LINK: root.name, SOURCE_ACCOUNT: source.quy_giao, TARGET: source.get(TARGET)})
        _sync(source)
        return _result(H.result(root))


@frappe.whitelist(methods=['POST'])
@retry_rpc
def connect_pending(name, tai_khoan_nhan):
    """Chuyển tiếp phiếu cũ chờ nhận, đúng người giữ tự tạo giữ chỗ mới."""
    source = _load(name)
    if source.docstatus != 1 or source.journal_entry or source.trang_thai not in ('Chờ nhận', 'Chênh lệch chờ điều tra'):
        frappe.throw('Chỉ chuyển tiếp phiếu cũ chưa nhận/chưa ghi sổ')
    if source.get(TARGET) and source.get(TARGET) != tai_khoan_nhan:
        frappe.throw('Quỹ nhận đã chốt; không đổi khi gửi lại')
    source.tai_khoan_nhan = tai_khoan_nhan
    return send_source(source)


@frappe.whitelist(methods=['POST'])
@retry_rpc
def receive_source(name, so_thuc_nhan, tai_khoan_nhan, reason=None, assignee=None, due_date=None):
    from kh_aph import cash_handover as H
    source = _load(name)
    if not source.get(LINK):
        if source.journal_entry and source.trang_thai != 'Chờ nhận':
            from kh_aph import factory_cash as F
            return F._legacy_receive(name, so_thuc_nhan, tai_khoan_nhan)
        frappe.throw('Phiếu cũ chưa được giữ chỗ; người giữ cần chuyển tiếp trước khi nhận')
    if tai_khoan_nhan != source.get(TARGET):
        frappe.throw('Quỹ nhận khác quỹ đã chốt khi gửi')
    return H.receive(source.get(LINK), so_thuc_nhan, reason, assignee, due_date)


def cancel_source(source):
    from kh_aph import cash_handover as H
    source = _load(source.name)
    if not source.get(LINK):
        if source.journal_entry:
            frappe.throw('Giữ nguyên bàn giao cũ đã nhận; xử lý bằng nghiệp vụ có căn cứ')
        return
    with operation(source):
        H.cancel(source.get(LINK))
        _sync(source)


def schema():
    from kh_aph import cash_handover as H, factory_cash as F
    if enabled():
        guard()
        frappe.reload_doc('kh_aph', 'doctype', 'aph_phieu_quy_nha_may')
        frappe.reload_doc('kh_aph', 'report', 'chot_ngay_va_can_xu_ly')


@frappe.whitelist()
def destinations(company):
    from kh_aph import factory_cash as F
    guard()
    _personal()._scope(company, F._quy(company))
    if C.roles_for() & _personal().RESTRICTED:
        from frappe.permissions import has_user_permission
        values = frappe.db.sql("select name from `tabAccount` where company=%s and account_type in ('Cash','Bank') and is_group=0 and disabled=0 and account_currency='VND' order by name limit 501", (company,), as_dict=True)
        if len(values) > 500:
            frappe.throw('Danh sách tài khoản vượt500; cần cấu hình phạm vi hẹp hơn')
        return [row.name for row in values if has_user_permission(frappe.get_doc('Account', row.name), user=frappe.session.user, ptype='read')]
    return frappe.get_list('Account', filters={'company': company, 'account_type': ['in', ['Cash','Bank']], 'is_group': 0, 'disabled': 0, 'account_currency': 'VND'}, pluck='name', limit_page_length=0)


@frappe.whitelist()
def status(name):
    from kh_aph import cash_handover as H
    source = _load(name)
    if not source.get(LINK):
        return {}
    with operation(source):
        root = frappe.get_doc(H.DT, source.get(LINK), for_update=True)
        scope(root)
        value = {'root': root.name, 'status': root.status, 'issue_state': root.issue_state,
            'from_holder': root.from_holder, 'to_holder': root.to_holder,
            'requested_amount': root.requested_amount, 'received_amount': root.received_amount}
        if root.reversal_doc:
            reverse = frappe.get_doc(H.DT, root.reversal_doc, for_update=True)
            if not _bound(reverse):
                frappe.throw('Quan hệ hoàn không khớp nguồn')
            value['reverse'] = {'name': reverse.name, 'status': reverse.status, 'to_holder': reverse.to_holder, 'amount': reverse.requested_amount}
        return value


def sync_resolution(root):
    if not root.get(SOURCE_FIELD):
        return
    C.guard(manager=True)
    from kh_aph import factory_cash as F
    source = frappe.get_doc(F.DT, root.get(SOURCE_FIELD), for_update=True)
    with operation(source):
        if source.get(LINK) != root.name or not _bound(root):
            frappe.throw('Nguồn bàn giao không khớp phiếu nhà máy')
        _sync(source)
