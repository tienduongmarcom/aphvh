"""Giữ chỗ và nhận bàn giao; không ghi thu khách hoặc đối ứng công nợ."""
from contextlib import contextmanager
import hashlib
import json

import frappe
from frappe.utils import cint, now_datetime, getdate

from kh_aph import cash_closing as C, cash_custody as custody
from kh_aph.cash_closing_rules import money
from kh_aph.cash_transaction import retry_rpc

FLAG = "kh_aph_cash_handover"
DT = "APH Ban giao tien"
JE_LINK = "kh_aph_ban_giao_tien"
PENDING = ("Chờ nhận", "Vượt nguồn cần xử lý")


def enabled():
    return cint(frappe.conf.get(FLAG))


def guard():
    if not enabled():
        frappe.throw("Bàn giao tiền chưa được bật")
    C.guard()


def target(company, account):
    doc = frappe.get_doc("Account", account)
    doc.check_permission("read")
    if doc.company != company or doc.is_group or doc.disabled or doc.account_currency != "VND" or doc.account_type not in ("Cash", "Bank"):
        frappe.throw("Quỹ/ngân hàng nhận phải chi tiết, VND, đang hoạt động và cùng đơn vị")
    return doc


def _scope(doc):
    guard()
    C.scope(doc.company, doc.from_account)
    return target(doc.company, doc.to_account)


def _query(company, account):
    # Các caller đã kiểm scope và giữ khóa quỹ; đọc đủ hai phía để so trách nhiệm.
    rows = frappe.db.sql(f"""select * from `tab{DT}` where company=%s
        and (from_account=%s or to_account=%s) and docstatus=1
        order by name limit 10001 for update""", (company, account, account), as_dict=True)
    if len(rows) > 10000:
        frappe.throw("Quỹ vượt 10.000 hồ sơ bàn giao; không cắt dữ liệu khi đối chiếu")
    return rows


def transfer_state(company, account, verification):
    """Delta cùng quỹ kể từ xác minh; khác quỹ đã nằm trong GL nên không cộng lại."""
    if not enabled():
        return {}, ""
    changes, proof = {}, []
    for row in _query(company, account):
        if row.from_account == row.to_account and row.from_verification == verification and row.status in ("Đã nhận", "Có chênh lệch"):
            amount = money(row.received_amount)
            changes[row.from_holder] = changes.get(row.from_holder, money(0)) - amount
            changes[row.to_holder] = changes.get(row.to_holder, money(0)) + amount
            proof.append([row.name, row.receive_hash])
    return changes, hashlib.sha256(json.dumps(sorted(proof)).encode()).hexdigest()


def before_verification(company, account):
    if enabled() and any(r.status in PENDING for r in _query(company, account)):
        frappe.throw("Quỹ còn bàn giao chờ nhận; nhận hoặc hủy đề nghị trước khi đổi mốc xác minh")


def _disputed(company, account, holder):
    # Lát này chưa có nghiệp vụ đóng vụ lệch: giữ nguyên hồ sơ và chặn giao ra
    # trên ví có lệch chưa xử lý, không cộng lặp các khoản thiếu qua nhiều ca.
    shifts = frappe.db.sql(f"select name from `tab{C.SHIFT}` where company=%s and account=%s and holder=%s and docstatus=1 and difference!=0 limit 1 for update", (company, account, holder))
    handovers = any(r.status in ("Có chênh lệch", "Vượt nguồn cần xử lý") and
        ((r.from_account == account and r.from_holder == holder) or (r.to_account == account and r.to_holder == holder))
        for r in _query(company, account))
    return bool(shifts) or handovers


def available(company, account, holder, exclude=None):
    opening, previous, rows, totals = C._state(company, account, holder)
    reserved = sum((money(r.requested_amount) for r in _query(company, account)
        if r.from_account == account and r.from_holder == holder and r.status in PENDING and r.name != exclude), money(0))
    return opening, totals.get(holder, money(0)), reserved, _disputed(company, account, holder)


def validate(doc):
    guard()
    destination = _scope(doc)
    C.check_evidence(doc)
    if not doc.from_holder or not doc.to_holder or doc.from_holder == doc.to_holder:
        frappe.throw("Người giao và người nhận phải khác nhau, kể cả tài khoản quản lý")
    if doc.from_holder != frappe.session.user:
        frappe.throw("Người giữ phải tự đăng nhập gửi bàn giao", frappe.PermissionError)
    for user in (doc.from_holder, doc.to_holder):
        custody._person(user, doc.company)
        roles = C.roles_for(user)
        if roles & {"APH Không xem giá vốn", "Kế toán nhà máy"} or not roles & (C.MANAGERS | {"Accounts User"}):
            frappe.throw("Người giao/nhận chưa có quyền dùng luồng bàn giao này", frappe.PermissionError)
    old = doc.get_doc_before_save()
    if old and old.docstatus == 1:
        frappe.throw("Không sửa hồ sơ bàn giao đã gửi")
    doc.requested_amount = C._money(doc.requested_amount)
    if doc.requested_amount <= 0:
        frappe.throw("Số tiền bàn giao dự kiến phải lớn hơn 0")
    opening, expected, reserved, disputed = available(doc.company, doc.from_account, doc.from_holder)
    doc.from_verification = opening.name
    if destination.account_type == "Cash":
        C.scope(doc.company, doc.to_account)
        to_opening, _, _, _ = C._state(doc.company, doc.to_account, doc.to_holder)
        doc.to_verification = to_opening.name
    else:
        doc.to_verification = None
    for field in ("received_amount", "difference", "received_by", "received_at", "receive_hash", "journal_entry", "sent_by", "sent_at", "receive_reason", "assignee", "due_date"):
        doc.set(field, None)
    doc.status = "Nháp"
    if doc._action == "submit":
        if disputed:
            frappe.throw("Ví còn chênh lệch chưa xử lý; chưa gửi bàn giao mới")
        if doc.requested_amount > expected - reserved:
            frappe.throw("Tiền đã xác minh khả dụng không đủ hoặc đang được giữ chỗ")
        doc.status, doc.sent_by, doc.sent_at = "Chờ nhận", frappe.session.user, now_datetime()


def before_cancel(doc):
    _scope(doc)
    if doc.from_holder != frappe.session.user:
        frappe.throw("Chỉ người giao được hủy đề nghị của mình", frappe.PermissionError)
    if doc.status not in PENDING or doc.journal_entry:
        frappe.throw("Bàn giao đã nhận không được hủy; cần nghiệp vụ đảo có kiểm soát")
    doc.status = "Đã hủy"


def protect(doc):
    if frappe.flags.get("kh_aph_handover_update") != doc.name:
        frappe.throw("Dùng thao tác nhận bàn giao; không sửa hồ sơ đã gửi")


@contextmanager
def _updating(doc):
    old = frappe.flags.get("kh_aph_handover_update")
    frappe.flags.kh_aph_handover_update = doc.name
    try:
        yield
    finally:
        frappe.flags.kh_aph_handover_update = old


def _locked(name):
    guard()
    preliminary = frappe.get_doc(DT, name)
    preliminary.check_permission("read")
    _scope(preliminary)
    doc = frappe.get_doc(DT, name, for_update=True)
    doc.check_permission("read")
    if (doc.company, doc.from_account, doc.to_account) != (preliminary.company, preliminary.from_account, preliminary.to_account):
        frappe.throw("Hồ sơ vừa đổi; tải lại trước khi thao tác")
    return doc


def result(doc):
    return {key: doc.get(key) for key in ("name", "status", "requested_amount", "received_amount", "difference", "journal_entry")}


@frappe.whitelist(methods=["POST"])
@retry_rpc
def send(name):
    doc = _locked(name)
    if doc.from_holder != frappe.session.user:
        frappe.throw("Chỉ người giao được gửi đề nghị", frappe.PermissionError)
    if doc.docstatus == 0:
        doc.check_permission("submit")
        doc.submit()
    if doc.docstatus != 1:
        frappe.throw("Đề nghị không còn hiệu lực")
    return result(doc)


@frappe.whitelist(methods=["POST"])
@retry_rpc
def cancel(name):
    doc = _locked(name)
    if doc.from_holder != frappe.session.user:
        frappe.throw("Chỉ người giao được hủy đề nghị", frappe.PermissionError)
    if doc.docstatus != 2:
        doc.check_permission("cancel")
        doc.cancel()
    return result(doc)


def _journal(doc, amount):
    rows = [{"account": doc.from_account, "credit_in_account_currency": amount, custody.HOLDER: doc.from_holder},
            {"account": doc.to_account, "debit_in_account_currency": amount}]
    if custody.cash(doc.to_account):
        rows[1][custody.HOLDER] = doc.to_holder
    journal = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Cash Entry", "company": doc.company,
        "posting_date": str(getdate()), "cheque_no": doc.name, "cheque_date": str(getdate()),
        "user_remark": "Chuyển tiền bàn giao " + doc.name, JE_LINK: doc.name, "accounts": rows})
    # Quyền tạo/submit JE là quyền native của người nhận; không mở bypass.
    with _updating(doc):
        journal.insert()
        journal.submit()
    return journal.name


@frappe.whitelist(methods=["POST"])
@retry_rpc
def receive(name, amount, reason=None, assignee=None, due_date=None):
    doc = _locked(name)
    if doc.from_holder == doc.to_holder or frappe.session.user != doc.to_holder:
        frappe.throw("Chỉ đúng người nhận được xác nhận; không tự nhận hoặc nhận thay", frappe.PermissionError)
    if doc.docstatus != 1:
        frappe.throw("Đề nghị chưa được gửi hoặc đã hủy")
    amount = C._money(amount)
    if amount < 0:
        frappe.throw("Số thực nhận không được âm")
    reason = (reason or "").strip()
    payload = [str(amount.quantize(money("0.01"))), reason, assignee or "", str(due_date or "")]
    signature = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
    if doc.receive_hash:
        if doc.receive_hash != signature:
            frappe.throw("Yêu cầu nhận đã ghi với nội dung khác; không dùng lại hồ sơ để đổi kết quả")
        return result(doc)
    if doc.status != "Chờ nhận":
        frappe.throw("Đề nghị không còn chờ nhận")
    opening, expected, reserved, disputed = available(doc.company, doc.from_account, doc.from_holder, exclude=doc.name)
    if opening.name != doc.from_verification:
        frappe.throw("Mốc xác minh nguồn đã đổi; cần kiểm lại bàn giao")
    destination = target(doc.company, doc.to_account)
    if destination.account_type == "Cash":
        C.scope(doc.company, doc.to_account)
        target_opening, _, _, _ = C._state(doc.company, doc.to_account, doc.to_holder)
        if target_opening.name != doc.to_verification:
            frappe.throw("Mốc xác minh quỹ nhận đã đổi")
    difference = amount - C._money(doc.requested_amount)
    over = amount > expected - reserved or disputed
    if difference or over:
        if not reason or not assignee or not due_date:
            frappe.throw("Chênh lệch/vượt nguồn phải có lý do, người xử lý và hạn xử lý")
        custody._person(assignee, doc.company)
        if getdate(due_date) < getdate():
            frappe.throw("Hạn xử lý không được trước hôm nay")
    journal = None
    if not over and amount and doc.from_account != doc.to_account:
        journal = _journal(doc, amount)
    doc.received_amount, doc.difference = amount, difference
    doc.received_by, doc.received_at = frappe.session.user, now_datetime()
    doc.receive_hash, doc.receive_reason = signature, reason
    doc.assignee, doc.due_date, doc.journal_entry = assignee, due_date, journal
    doc.status = "Vượt nguồn cần xử lý" if over else "Có chênh lệch" if difference else "Đã nhận"
    with _updating(doc):
        doc.save()
    return result(doc)


def protect_journal(doc, method=None):
    if not enabled():
        return
    old = doc.get_doc_before_save()
    link = doc.get(JE_LINK) or (old.get(JE_LINK) if old else None)
    if not link:
        return
    if old and old.get(JE_LINK) != doc.get(JE_LINK):
        frappe.throw("Không gỡ hoặc đổi liên kết bút toán bàn giao")
    if method in ("before_cancel", "before_update_after_submit") or frappe.flags.get("kh_aph_handover_update") != doc.get(JE_LINK):
        frappe.throw("Bút toán bàn giao không được sửa/hủy hoặc lập tay ngoài hồ sơ nguồn")


def wallet(company, account):
    opening, expected, reserved, disputed = available(company, account, frappe.session.user)
    return {"reserved_amount": reserved, "available_amount": max(money(0), expected - reserved) if not disputed else money(0), "disputed": disputed}


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = C.roles_for(user)
    if not enabled() or roles & {"APH Không xem giá vốn", "Kế toán nhà máy"}:
        return False
    return bool(roles & C.MANAGERS or ("Accounts User" in roles and user in (doc.from_holder, doc.to_holder)))


def query_conditions(user=None):
    user = user or frappe.session.user
    roles = C.roles_for(user)
    if not enabled() or roles & {"APH Không xem giá vốn", "Kế toán nhà máy"}:
        return "1=0"
    if roles & C.MANAGERS:
        return ""
    escaped = frappe.db.escape(user)
    return f"(`tab{DT}`.from_holder={escaped} or `tab{DT}`.to_holder={escaped})"


def schema():
    if not enabled():
        return
    if not C.enabled() or not custody.enabled():
        frappe.throw("Bàn giao cần bật xác minh/chốt ca và người giữ tiền")
    frappe.reload_doc("kh_aph", "doctype", "aph_ban_giao_tien")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({"Journal Entry": [{"fieldname": JE_LINK, "label": "Hồ sơ bàn giao tiền", "fieldtype": "Link",
        "options": DT, "read_only": 1, "no_copy": 1, "insert_after": "user_remark"}]})
