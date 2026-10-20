"""Projection tiền của chính người gọi; không cấp quyền GL hoặc trả nguồn giá vốn.

Chỉ đọc, dùng cùng mốc/fingerprint/công thức với chốt ca. SQL nội bộ cố ý
không kiểm quyền GL: quyền là capability xem số cá nhân, sau guard Company
và phạm vi Cash. Không có tham số holder hoặc đường ghi/chốt/nhận thay.
"""
import frappe
from frappe.utils import cint, now_datetime

from kh_aph import cash_closing as C, cash_custody as custody, cash_handover as H
from kh_aph.cash_closing_rules import money
from kh_aph.cash_transaction import retry_rpc

ROLES = C.MANAGERS | {"Accounts User", "Kế toán bán hàng", "Kế toán nhà máy"}
RESTRICTED = {"APH Không xem giá vốn", "Kế toán nhà máy"}


def _scope(company, account=None):
    if not C.enabled() or not custody.enabled():
        frappe.throw("Tiền cá nhân cần bật người giữ tiền và xác minh/chốt ca")
    if frappe.session.user == "Guest" or not C.roles_for() & ROLES:
        frappe.throw("Chưa có quyền xem tiền cá nhân", frappe.PermissionError)
    if not isinstance(company, str) or not company.strip():
        frappe.throw("Chọn đơn vị hợp lệ")
    custody._person(frappe.session.user, company)
    co = frappe.get_doc("Company", company)
    co.check_permission("read")
    if co.default_currency != "VND":
        frappe.throw("Tiền cá nhân chỉ hỗ trợ đơn vị dùng VND")
    restricted = bool(C.roles_for() & RESTRICTED)
    factory_account = co.get("kh_aph_quy_nha_may")
    if restricted and (not cint(frappe.conf.get("kh_aph_factory_cash")) or not factory_account):
        frappe.throw("Chưa được cấu hình phạm vi quỹ nhà máy", frappe.PermissionError)
    if account is None:
        return factory_account if restricted else None
    if restricted and account != factory_account:
        frappe.throw("Chỉ xem tiền cá nhân tại quỹ nhà máy được cấu hình", frappe.PermissionError)
    acc = frappe.get_doc("Account", account)
    if not restricted:
        acc.check_permission("read")
    else:
        from frappe.permissions import has_user_permission
        if not has_user_permission(acc, user=frappe.session.user, ptype="read"):
            frappe.throw("Quỹ nằm ngoài phạm vi tài khoản được cấp", frappe.PermissionError)
    if acc.company != company or acc.account_type != "Cash" or acc.is_group or acc.disabled or acc.account_currency != "VND":
        frappe.throw("Chọn quỹ tiền mặt VND đang hoạt động đúng đơn vị")
    # Cùng thứ tự khóa với ghi sổ/chốt ca/bàn giao, không đọc snapshot cũ
    # sau khi chờ giao dịch khác. Không khóa ngược theo phiếu nguồn.
    frappe.db.sql("select name from `tabAccount` where company=%s and account_type='Cash' order by name for update", (company,))


@frappe.whitelist()
def accounts(company):
    """Danh sách quỹ cho Dialog; không mở quyền tìm Account cho vai trò nhà máy."""
    factory = _scope(company)
    if factory:
        _scope(company, factory)
        return [factory]
    return frappe.get_list("Account", filters={"company": company, "account_type": "Cash", "is_group": 0,
        "disabled": 0, "account_currency": "VND"}, pluck="name", limit_page_length=0)


def _holder(voucher_type, voucher_no, company, account):
    """Chỉ metadata đã ghi, không tải chứng từ/chi phí hay suy từ owner."""
    if voucher_type not in custody.SOURCES:
        return ""
    fields = "company"
    if voucher_type == "Payment Entry":
        fields += f", paid_to, paid_from, `{custody.HOLDER}`, `{custody.PAYER}`"
    elif voucher_type != "Journal Entry":
        fields += f", `{custody.HOLDER}`"
    # Tên bảng từ allowlist server cố định; mọi giá trị truy vấn tham số hóa.
    sources = frappe.db.sql(f"select {fields} from `tab{voucher_type}` where name=%s for update", (voucher_no,), as_dict=True)
    if not sources:
        return ""
    source = sources[0]
    if source.company != company:
        frappe.throw("Nguồn tiền khác đơn vị; cần đối chiếu lại")
    if voucher_type == "Journal Entry":
        rows = frappe.db.sql(f"select `{custody.HOLDER}` from `tabJournal Entry Account` where parent=%s and parenttype='Journal Entry' and account=%s order by idx for update", (voucher_no, account), as_dict=True)
        users = {row.get(custody.HOLDER) or "" for row in rows}
        return next(iter(users)) if len(users) == 1 else ""
    if voucher_type == "Payment Entry":
        return (source.get(custody.HOLDER) if source.paid_to == account else source.get(custody.PAYER) if source.paid_from == account else None) or ""
    return source.get(custody.HOLDER) or ""


def _ledger(company, account):
    """Chỉ gọi sau _scope; đủ cột fingerprint, không select * hoặc đọc đối ứng."""
    rows = frappe.db.sql("""select name, posting_date, creation, debit, credit, is_cancelled, voucher_type, voucher_no
        from `tabGL Entry` where company=%s and account=%s order by name limit 10001 for update""", (company, account), as_dict=True)
    if len(rows) > 10000:
        frappe.throw("Quỹ vượt 10.000 dòng; cần đối chiếu trên tập đầy đủ")
    sources = {}
    for row in rows:
        key = (row.voucher_type, row.voucher_no)
        if key not in sources:
            sources[key] = _holder(*key, company, account)
        row["holder"] = sources[key]
    return rows


@frappe.whitelist()
@retry_rpc
def current(company, account):
    """Không nhận người dùng từ client; phản hồi luôn là số của session hiện tại."""
    if not isinstance(account, str) or not account.strip():
        frappe.throw("Chọn quỹ tiền mặt hợp lệ")
    _scope(company, account)
    _, _, _, totals = C._state(company, account, frappe.session.user, ledger_reader=_ledger)
    expected = totals.get(frappe.session.user, money(0))
    reserved = money(0)
    shifts = frappe.db.sql(f"select name from `tab{C.SHIFT}` where company=%s and account=%s and holder=%s and docstatus=1 and difference!=0 and coalesce(issue_state,'')!='Đã đối chiếu' limit 1 for update", (company, account, frappe.session.user))
    disputed = any(value < 0 for value in totals.values()) or bool(shifts)
    if H.enabled():
        reserved = sum((money(row.requested_amount) for row in H._query(company, account)
            if row.from_account == account and row.from_holder == frappe.session.user and row.status in H.PENDING), money(0))
        disputed = disputed or H._disputed(company, account, frappe.session.user)
    return {"expected_amount": expected, "reserved_amount": reserved,
        "available_amount": money(0) if disputed else max(money(0), expected - reserved),
        "disputed": bool(disputed), "checked_at": now_datetime()}


# Capability chốt tự thân: không mở quyền đọc native snapshot/GL cho nhà máy.
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json

_SHIFT_OPERATION = ContextVar('personal_shift_operation', default=None)


def shift_allowed(doc):
    current = _SHIFT_OPERATION.get()
    return bool(current and current == (frappe.session.user, doc.company, doc.account, doc.get('personal_request'))
        and doc.doctype == C.SHIFT and doc.holder == frappe.session.user)


def shift_origin(doc):
    if doc.get('personal_request') or doc.get('personal_payload'):
        if not shift_allowed(doc):
            frappe.throw('Dùng thao tác chốt ca cá nhân; không sửa dấu yêu cầu', frappe.PermissionError)
    elif doc.doctype == C.SHIFT:
        doc.set('personal_request', None)
        doc.set('personal_payload', None)


@contextmanager
def _shift_operation(doc):
    token = _SHIFT_OPERATION.set((frappe.session.user, doc.company, doc.account, doc.personal_request))
    try:
        doc.flags.ignore_permissions = True
        yield
    finally:
        _SHIFT_OPERATION.reset(token)


def _shift_result(doc):
    return {key: doc.get(key) for key in ('name', 'docstatus', 'expected_amount', 'counted_amount', 'difference', 'status')}


def _shift_scope(company, account):
    from kh_aph import factory_handover
    if not factory_handover.enabled():
        frappe.throw('Chốt ca cá nhân chưa được bật')
    factory_handover.guard()
    _scope(company, account)


@frappe.whitelist(methods=['POST'])
@retry_rpc
def prepare_shift(company, account, request_id, counted_amount, reason=None, assignee=None, due_date=None):
    _shift_scope(company, account)
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 100:
        frappe.throw('Cần mã lượt chốt ca')
    amount = C._money(counted_amount)
    if amount < 0:
        frappe.throw('Số thực đếm không được âm')
    reason = (reason or '').strip()
    payload = hashlib.sha256(json.dumps([str(amount.quantize(money("0.01"))), reason, assignee or '', due_date or '']).encode()).hexdigest()
    key = hashlib.sha256(json.dumps([frappe.session.user, company, account, request_id]).encode()).hexdigest()
    existing = frappe.db.sql(f'select name from `tab{C.SHIFT}` where personal_request=%s for update', (key,))
    if existing:
        doc = frappe.get_doc(C.SHIFT, existing[0][0], for_update=True)
        if doc.holder != frappe.session.user or doc.personal_payload != payload:
            frappe.throw('Mã lượt chốt đã dùng với nội dung khác; kiểm hồ sơ trước khi lập lượt mới')
        return _shift_result(doc)
    doc = frappe.get_doc({'doctype': C.SHIFT, 'company': company, 'account': account,
        'holder': frappe.session.user, 'counted_amount': amount, 'reason': reason,
        'assignee': assignee or None, 'due_date': due_date or None,
        'personal_request': key, 'personal_payload': payload})
    with _shift_operation(doc):
        doc.insert()
    return _shift_result(doc)


@frappe.whitelist(methods=['POST'])
@retry_rpc
def confirm_shift(name):
    # Đọc metadata trước để khóa Cash theo cùng thứ tự; không trả snapshot.
    preliminary = frappe.get_doc(C.SHIFT, name)
    _shift_scope(preliminary.company, preliminary.account)
    doc = frappe.get_doc(C.SHIFT, name, for_update=True)
    if ((doc.company, doc.account) != (preliminary.company, preliminary.account)
            or doc.holder != frappe.session.user or not doc.get('personal_request')):
        frappe.throw('Chỉ tự chốt ca cá nhân đúng hồ sơ', frappe.PermissionError)
    if doc.docstatus not in (0, 1):
        frappe.throw('Ca không còn hiệu lực')
    with _shift_operation(doc):
        if doc.docstatus == 0:
            doc.submit()
    return _shift_result(doc)
