"""Đối chiếu có căn cứ trên nguồn; không tự điều chỉnh sổ hoặc số đếm lịch sử."""
from html import escape

import frappe
from frappe.utils import now_datetime, get_datetime

from kh_aph import cash_closing as C, cash_handover as H
from kh_aph.cash_closing_rules import anchor, money
from kh_aph.cash_transaction import retry_rpc

DT = 'APH Doi chieu lech tien'
CHILD = 'APH Can cu doi chieu quy'
PENDING = 'Chờ xử lý'
CLOSED = 'Đã đối chiếu'


def guard():
    H.guard()
    C.guard(manager=True)


def parties(source):
    if source.doctype == C.SHIFT:
        return [(source.account, source.holder)]
    result = [(source.from_account, source.from_holder)]
    if H.target(source.company, source.to_account).account_type == 'Cash':
        result.append((source.to_account, source.to_holder))
    return result


def source_for(doc):
    guard()
    if doc.source_type not in (C.SHIFT, H.DT):
        frappe.throw('Chọn nguồn là ca chốt hoặc bàn giao tiền')
    preliminary = frappe.get_doc(doc.source_type, doc.source_name)
    preliminary.check_permission('read')
    preliminary.check_permission('write')
    account = preliminary.account if doc.source_type == C.SHIFT else preliminary.from_account
    # Hoàn từ Bank vẫn có một phía Cash; mọi thao tác cùng company giữ cùng khóa.
    if doc.source_type == H.DT and not H.custody.cash(account):
        account = preliminary.to_account
    C.scope(preliminary.company, account)
    source = frappe.get_doc(doc.source_type, doc.source_name, for_update=True)
    source.check_permission('read')
    source.check_permission('write')
    if source.company != preliminary.company:
        frappe.throw('Nguồn vừa đổi đơn vị; tải lại')
    doc.company = source.company
    return source


def _active(source, exclude=None):
    return frappe.db.sql(f'''select name from `tab{DT}` where source_type=%s
        and source_name=%s and docstatus=1 and name!=%s limit 1 for update''',
        (source.doctype, source.name, exclude or ''))


def cancelled_links(doc, links):
    """Chỉ nguồn bàn giao đã hủy có quan sát được dùng làm tham chiếu lịch sử.

    Native vẫn kiểm mọi link không tồn tại và link hủy ở các trường khác/child.
    Không dùng ignore_links; quyền/phạm vi/khóa nguồn vẫn kiểm trước ngoại lệ.
    """
    if doc.source_type != H.DT or not any(row[0] == 'source_name' for row in links):
        return links
    source = source_for(doc)
    if source.docstatus == 2 and source.receive_hash and source.issue_state:
        return [row for row in links if row[0] != 'source_name']
    return links


def validate(doc):
    source = source_for(doc)
    old = doc.get_doc_before_save()
    if old and (old.source_type, old.source_name) != (doc.source_type, doc.source_name):
        frappe.throw('Không đổi nguồn của hồ sơ đối chiếu; lập bản khác')
    if source.doctype == C.SHIFT:
        eligible = source.docstatus == 1 and money(source.difference) != 0
        occurred = source.closed_at
    else:
        eligible = source.docstatus in (1, 2) and bool(source.receive_hash) and bool(source.issue_state)
        occurred = source.received_at
        if source.status in H.PENDING:
            frappe.throw('Nhận hoặc hủy đề nghị chưa chuyển trước khi đối chiếu kết quả')
    if not eligible or _active(source, doc.name):
        frappe.throw('Nguồn không có vụ lệch đang mở hoặc đã có đối chiếu khác')
    expected = parties(source)
    if not doc.get('proofs'):
        for account, holder in expected:
            doc.append('proofs', {'account': account, 'holder': holder})
    if [(r.account, r.holder) for r in doc.proofs] != expected:
        frappe.throw('Bảng căn cứ phải đúng quỹ/người của nguồn, không thêm hoặc đổi phía')
    doc.closed_by = doc.closed_at = None
    if doc._action != 'submit':
        return
    if not (doc.result or '').strip():
        frappe.throw('Ghi kết quả điều tra và đối chiếu')
    if not doc.evidence:
        frappe.throw('Đính kèm căn cứ riêng tư trước khi chốt đối chiếu')
    C.check_evidence(doc)
    for row in doc.proofs:
        C.scope(doc.company, row.account)
        opening, latest, rows, totals = C._state(doc.company, row.account, row.holder)
        if row.verification != opening.name or get_datetime(opening.closed_at) <= get_datetime(occurred):
            frappe.throw('Cần mốc xác minh mới sau vụ lệch và còn là mốc hiện tại')
        if not row.shift or not latest or row.shift != latest.name:
            frappe.throw('Chọn ca kiểm đếm mới nhất đúng người và quỹ')
        latest.check_permission('read')
        if latest.verification != opening.name or money(latest.difference) != 0 or get_datetime(latest.closed_at) < get_datetime(opening.closed_at):
            frappe.throw('Ca căn cứ phải khớp, thuộc mốc xác minh mới và đúng người')
        _, digest = anchor(rows)
        _, transfers = H.transfer_state(doc.company, row.account, opening.name)
        if digest != latest.source_hash or (latest.transfer_hash or '') != transfers:
            frappe.throw('Sổ hoặc trách nhiệm đã đổi sau kiểm đếm; chốt ca mới trước khi đối chiếu')


def before_submit(doc):
    doc.closed_by, doc.closed_at = frappe.session.user, now_datetime()


def _mark(doc, state):
    source = source_for(doc)
    source.db_set({'issue_state': state, 'issue_resolution': doc.name if state == CLOSED else None})
    source.add_comment('Comment', 'Đối chiếu lệch tiền — ' + escape(state) + ': ' + escape(doc.name) + '<br>' + escape(doc.result or ''))


def on_submit(doc):
    _mark(doc, CLOSED)


def before_cancel(doc):
    guard()
    # Cùng khóa quỹ/source với submit và giao tiền; mở lại không đổi số tiền.
    _mark(doc, PENDING)


def prevent_change(doc):
    frappe.throw('Giữ nguyên kết quả đã xác nhận; hủy hồ sơ đối chiếu để mở lại vụ lệch')


def prevent_delete(doc):
    if doc.docstatus != 0:
        frappe.throw('Giữ lịch sử đối chiếu đã xác nhận hoặc hủy; không xóa hồ sơ')


def _locked(name):
    guard()
    preliminary = frappe.get_doc(DT, name)
    preliminary.check_permission('read')
    source_for(preliminary)
    doc = frappe.get_doc(DT, name, for_update=True)
    doc.check_permission('read')
    return doc


@frappe.whitelist(methods=['POST'])
@retry_rpc
def confirm(name):
    doc = _locked(name)
    if doc.docstatus == 0:
        doc.check_permission('submit')
        doc.submit()
    if doc.docstatus != 1:
        frappe.throw('Hồ sơ đối chiếu đã hủy; lập hồ sơ mới khi cần chốt lại')
    return {'name': doc.name, 'docstatus': doc.docstatus}


@frappe.whitelist(methods=['POST'])
@retry_rpc
def reopen(name):
    doc = _locked(name)
    if doc.docstatus != 2:
        doc.check_permission('cancel')
        doc.cancel()
    return {'name': doc.name, 'docstatus': doc.docstatus}


def has_permission(doc, user=None, permission_type=None):
    roles = C.roles_for(user)
    return bool(H.enabled() and roles & C.MANAGERS and not roles & {'APH Không xem giá vốn', 'Kế toán nhà máy'})


def query_conditions(user=None):
    return '' if has_permission(None, user) else '1=0'


def schema():
    if H.enabled():
        for dt in (CHILD, DT):
            frappe.reload_doc('kh_aph', 'doctype', frappe.scrub(dt))
