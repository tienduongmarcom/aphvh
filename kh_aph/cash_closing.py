"""Xác minh số bắt đầu và chốt ca; không tạo bút toán hay bàn giao tiền."""
import json

import frappe
from frappe.utils import cint, now_datetime, getdate

from kh_aph import cash_custody as custody
from kh_aph.cash_closing_rules import anchor, balance, money, position, unchanged
from kh_aph.cash_transaction import retry_rpc

FLAG = "kh_aph_cash_closing"
OPENING = "APH Xac minh quy"
SHIFT = "APH Chot ca tien"
MANAGERS = {"Accounts Manager", "System Manager"}


def roles_for(user=None):
    # Frappe trả MỌI role cho Administrator, gồm cả profile cấm vốn tự động.
    # Đây không phải người dùng bị gán profile NoCost; kiểm actor tự thân vẫn áp dụng.
    user = user or frappe.session.user
    return {"System Manager"} if user == "Administrator" else set(frappe.get_roles(user))


def enabled():
    return cint(frappe.conf.get(FLAG))


def guard(manager=False):
    if not enabled() or not custody.enabled():
        frappe.throw("Cần bật xác minh/chốt ca và người giữ tiền trước khi sử dụng")
    roles = roles_for()
    if roles & {"APH Không xem giá vốn", "Kế toán nhà máy"} or not roles & (MANAGERS if manager else MANAGERS | {"Accounts User"}):
        frappe.throw("Chưa có quyền xác minh/chốt ca tiền", frappe.PermissionError)


def scope(company, account):
    guard()
    co = frappe.get_doc("Company", company)
    co.check_permission("read")
    acc = frappe.get_doc("Account", account)
    acc.check_permission("read")
    if co.default_currency != "VND" or acc.company != company or acc.account_type != "Cash" or acc.is_group or acc.disabled or acc.account_currency != "VND":
        frappe.throw("Chọn tài khoản tiền mặt VND đang hoạt động đúng đơn vị")
    if not frappe.has_permission("GL Entry", "read"):
        frappe.throw("Cần quyền đọc sổ quỹ để đối chiếu", frappe.PermissionError)
    # Mọi thao tác cùng quỹ dùng một khóa. Đọc GL bên dưới là current read,
    # không dùng snapshot đã có trước lúc đợi khóa ở mức REPEATABLE READ.
    frappe.db.sql("select name from `tabAccount` where company=%s and account_type='Cash' order by name for update", (company,))


def lock_ledger(doc, method=None):
    """Đồng bộ với ghi/hủy sổ native; cờ tắt không truy vấn hoặc tác động."""
    if not enabled():
        return
    company = doc.get("company")
    if not company:
        return
    # Khóa toàn bộ quỹ của company theo thứ tự, kể cả chứng từ ghi nhiều quỹ.
    # Hook GL bao phủ cả nguồn khác và dòng đảo do engine tạo.
    frappe.db.sql("select name from `tabAccount` where company=%s and account_type='Cash' order by name for update", (company,))


def ledger(company, account):
    # scope() đã kiểm quyền GL, Company và Account. SQL current read cố ý lấy
    # đủ cả dòng hủy, chỉ một quỹ; không trả toàn bộ sổ qua API.
    rows = frappe.db.sql("""select * from `tabGL Entry`
        where company=%s and account=%s order by name limit 10001 for update""", (company, account), as_dict=True)
    if len(rows) > 10000:
        frappe.throw("Quỹ vượt 10.000 dòng sổ; chưa hỗ trợ chốt trên tập này, không cắt bớt dữ liệu")
    sources = {}
    for row in rows:
        # Kiểm trên đủ field của current read, kể cả Accounting Dimension tùy
        # chỉnh. Không chỉ kiểm quyền loại GL rồi bỏ qua User Permission từng dòng.
        frappe.get_doc({"doctype": "GL Entry", **row}).check_permission("read")
        key = (row.voucher_type, row.voucher_no)
        if key not in sources:
            source = None
            if row.voucher_type in custody.SOURCES:
                source = frappe.get_doc(*key, for_update=True)
                source.check_permission("read")
                if source.company != company:
                    frappe.throw("Nguồn sổ khác đơn vị")
            sources[key] = source
        source = sources[key]
        row["holder"] = (custody._source_holder(source, account) if source else None) or ""
    return rows


def latest(dt, company, account, holder=None):
    # Truy vấn nội bộ sau scope; khóa quỹ đã tuần tự hóa mọi bản submit.
    conditions = " and holder=%s" if holder else ""
    args = (company, account, holder) if holder else (company, account)
    rows = frappe.db.sql(f"select name from `tab{dt}` where company=%s and account=%s and docstatus=1{conditions} order by closed_at desc, name desc limit 1 for update", args)
    return frappe.get_doc(dt, rows[0][0], for_update=True) if rows else None


def _money(value):
    try:
        return money(value)
    except ValueError as exc:
        frappe.throw(str(exc))


def _state(company, account, holder, *, ledger_reader=None):
    opening = latest(OPENING, company, account)
    if not opening:
        frappe.throw("Quỹ chưa có xác minh số bắt đầu")
    # Facade tiền cá nhân có scope riêng và chỉ đọc cột Cash/metadata.
    # Không thay quyền GL hoặc nguồn của luồng chốt ca native.
    rows = (ledger_reader or ledger)(company, account)
    allocations = {r.holder: r.amount for r in opening.allocations}
    allocations[""] = opening.unverified_amount
    try:
        totals = position(allocations, opening.source_rows, rows)
    except ValueError as exc:
        frappe.throw(str(exc))
    from kh_aph import cash_handover
    changes, _ = cash_handover.transfer_state(company, account, opening.name)
    for user, amount in changes.items():
        totals[user] = totals.get(user, money(0)) + amount
    previous = latest(SHIFT, company, account, holder)
    if previous and previous.verification == opening.name:
        if not unchanged(previous.source_rows, rows):
            frappe.throw("Sổ trước ca đã chốt đã đổi; cần xác minh lại quỹ, không sửa số ca cũ")
        old = json.loads(previous.source_rows)
        if any(r.name not in old and getdate(r.posting_date) < getdate(previous.closed_at) for r in rows):
            frappe.throw("Có sổ mới ghi lùi ngày sau chốt; cần xác minh lại quỹ")
    return opening, previous, rows, totals


def validate(doc):
    from kh_aph import personal_cash as P
    P.shift_origin(doc)
    personal = P.shift_allowed(doc)
    if personal:
        P._shift_scope(doc.company, doc.account)
    else:
        guard(manager=doc.doctype == OPENING)
        scope(doc.company, doc.account)
    check_evidence(doc)

    if doc.doctype == SHIFT:
        custody._person(doc.holder, doc.company)
        if not doc.holder or doc.holder != frappe.session.user:
            frappe.throw("Người giữ phải tự đăng nhập chốt ca của mình", frappe.PermissionError)
    _validate_snapshot(doc, ledger_reader=P._ledger if personal else None)


def check_evidence(doc):
    if doc.get("evidence"):
        found = frappe.db.sql("""select name from `tabFile` where file_url=%s
            and attached_to_doctype=%s and attached_to_name=%s and is_private=1 for update""",
            (doc.evidence, doc.doctype, doc.name))
        if not doc.evidence.startswith("/private/files/") or not found:
            frappe.throw("Tệp kiểm đếm phải riêng tư và gắn đúng hồ sơ này")


def _validate_snapshot(doc, *, ledger_reader=None):
    if doc.get_doc_before_save() and cint(doc.get_doc_before_save().docstatus) == 1:
        frappe.throw("Hồ sơ đã xác nhận giữ nguyên; lập bản xác minh mới có lý do thay vì sửa lịch sử")
    rows = (ledger_reader or ledger)(doc.company, doc.account)
    encoded, digest = anchor(rows)
    if doc._action == "submit" and doc.source_hash != digest:
        frappe.throw("Sổ đã đổi từ lúc lưu nháp; lưu lại, kiểm số phải có rồi xác nhận")
    if doc.doctype == OPENING:
        from kh_aph import cash_handover
        cash_handover.before_verification(doc.company, doc.account)
        previous = latest(OPENING, doc.company, doc.account)
        if doc._action == "submit" and (doc.previous_verification or "") != (previous.name if previous else ""):
            frappe.throw("Đã có xác minh khác; lưu và kiểm lại bản nháp")
        doc.previous_verification = previous.name if previous else None
        amount = balance(rows)
        if amount < 0:
            frappe.throw("Sổ quỹ đang âm; cần đối chiếu chứng từ trước khi xác minh")
        users = set()
        allocated = _money(0)
        for row in doc.allocations:
            if not row.holder or row.holder in users:
                frappe.throw("Mỗi người giữ chỉ có một dòng phân bổ và không được để trống")
            users.add(row.holder)
            custody._person(row.holder, doc.company)
            row.amount = _money(row.amount)
            if row.amount < 0:
                frappe.throw("Phân bổ không được âm")
            allocated += row.amount
        doc.unverified_amount = _money(doc.unverified_amount)
        if doc.unverified_amount < 0:
            frappe.throw("Phần chưa xác minh không được âm")
        doc.gl_balance = amount
        if doc._action == "submit" and allocated + doc.unverified_amount != amount:
            frappe.throw("Tổng phân bổ và chưa xác minh phải bằng đúng số dư sổ quỹ")
    else:
        opening, previous, rows, totals = _state(doc.company, doc.account, doc.holder, ledger_reader=ledger_reader) if ledger_reader else _state(doc.company, doc.account, doc.holder)
        from kh_aph import cash_handover
        _, transfer_hash = cash_handover.transfer_state(doc.company, doc.account, opening.name)
        if doc._action == "submit" and (doc.transfer_hash or "") != transfer_hash:
            frappe.throw("Trách nhiệm tiền đã đổi sau lưu nháp; lưu và kiểm lại ca")
        doc.transfer_hash = transfer_hash
        if doc._action == "submit" and (doc.previous_shift or "") != (previous.name if previous else ""):
            frappe.throw("Ca khác đã chốt; lưu và kiểm lại ca này")
        if doc._action == "submit" and doc.verification != opening.name:
            frappe.throw("Mốc xác minh đã đổi; lưu và kiểm lại ca")
        doc.verification = opening.name
        doc.previous_shift = previous.name if previous else None
        doc.started_at = previous.closed_at if previous and previous.verification == opening.name else opening.closed_at
        doc.expected_amount = totals.get(doc.holder, _money(0))
        doc.counted_amount = _money(doc.counted_amount)
        if doc.counted_amount < 0:
            frappe.throw("Số thực đếm không được âm")
        doc.difference = doc.counted_amount - doc.expected_amount
        doc.status = "Có chênh lệch" if doc.difference else "Khớp"
        doc.issue_state = "Chờ xử lý" if doc.difference else None
        doc.issue_resolution = None
        if doc.difference and doc._action == "submit":
            if not doc.reason or not doc.assignee or not doc.due_date:
                frappe.throw("Ca lệch phải có lý do, người xử lý và hạn xử lý")
            custody._person(doc.assignee, doc.company)
            if getdate(doc.due_date) < getdate():
                frappe.throw("Hạn xử lý không được trước hôm nay")
    doc.source_rows, doc.source_hash = encoded, digest
    doc.closed_by = None
    doc.closed_at = None


def before_submit(doc):
    # validate() đã kiểm current read dưới khóa; mốc do server đặt, không nhận client.
    doc.closed_by = frappe.session.user
    doc.closed_at = now_datetime()


def prevent_change(doc, method=None):
    frappe.throw("Giữ nguyên hồ sơ đã xác nhận; lập xác minh mới có căn cứ và liên kết bản trước")


@frappe.whitelist(methods=["POST"])
@retry_rpc
def close(name):
    """Retry theo tên hồ sơ: cùng ca chỉ được submit một lần."""
    guard()
    doc = frappe.get_doc(SHIFT, name, for_update=True)
    doc.check_permission("read")
    scope(doc.company, doc.account)
    if doc.holder != frappe.session.user:
        frappe.throw("Chỉ người giữ được chốt ca của mình", frappe.PermissionError)
    if doc.docstatus != 1:
        doc.check_permission("submit")
        doc.submit()
    return {"name": doc.name, "status": doc.status, "expected_amount": doc.expected_amount,
            "counted_amount": doc.counted_amount, "difference": doc.difference}


@frappe.whitelist()
@retry_rpc
def current(company, account):
    """Chỉ trả phần tiền của người đang đăng nhập; không lộ các nguồn hoặc người khác."""
    scope(company, account)
    opening, previous, rows, totals = _state(company, account, frappe.session.user)
    from kh_aph import cash_handover
    extra = cash_handover.wallet(company, account) if cash_handover.enabled() else {}
    return {"verification": opening.name, "previous_shift": previous.name if previous else "", **extra,
            "expected_amount": totals.get(frappe.session.user, 0), "checked_at": now_datetime()}


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if not enabled():
        return False
    roles = roles_for(user)
    if roles & {"APH Không xem giá vốn", "Kế toán nhà máy"}:
        return False
    if roles & MANAGERS:
        return True
    return doc.doctype == SHIFT and "Accounts User" in roles and doc.holder == user


def query_conditions(user=None):
    user = user or frappe.session.user
    roles = roles_for(user)
    if not enabled() or roles & {"APH Không xem giá vốn", "Kế toán nhà máy"}:
        return "1=0"
    if roles & MANAGERS:
        return ""
    return "`tabAPH Chot ca tien`.holder=" + frappe.db.escape(user)


def opening_query_conditions(user=None):
    user = user or frappe.session.user
    roles = roles_for(user)
    if not enabled() or roles & {"APH Không xem giá vốn", "Kế toán nhà máy"} or not roles & MANAGERS:
        return "1=0"
    return ""


def protect_file(doc, method=None):
    """Bảo vệ blob trước File.on_trash; rollback CSDL không khôi phục tệp đã xóa."""
    if not enabled():
        return
    old = doc.get_doc_before_save() or doc
    url = old.get("file_url")
    if not url:
        return
    types = (OPENING, SHIFT, "APH Ban giao tien", "APH Doi chieu lech tien") if cint(frappe.conf.get("kh_aph_cash_handover")) else (OPENING, SHIFT)
    for dt in types:
        if frappe.db.sql(f"select name from `tab{dt}` where docstatus in (1,2) and evidence=%s limit 1 for update", (url,)):
            if method != "on_trash" and _same_private_upload(doc):
                return
            if method == "on_trash" or doc.get("content") or any(doc.get(f) != old.get(f) for f in ("file_url", "is_private", "attached_to_doctype", "attached_to_name")):
                frappe.throw("Tệp thuộc hồ sơ tiền đã xác nhận; giữ nguyên bằng chứng lịch sử")


def _same_private_upload(doc):
    """File.before_insert đã chuẩn hóa nội dung/dedupe; chỉ thêm File mới.

    Không tin content_hash từ client, không cho nhánh này sửa File đã tồn tại.
    So byte sau xử lý native (kể cả EXIF), giữ URL/riêng tư và blob cũ.
    """
    if not doc.is_new() or not cint(doc.get("is_private")) or frappe.db.exists("File", doc.name):
        return False
    rows = frappe.db.sql("""select name from `tabFile` where file_url=%s
        and is_private=1 and name!=%s order by name limit 1 for update""", (doc.file_url, doc.name))
    if not rows:
        return False
    original = frappe.get_doc("File", rows[0][0])
    original.check_permission("read")
    incoming = getattr(doc, "_content", None)
    if incoming is None:
        incoming = doc.get_content(encodings=[])
    existing = original.get_content(encodings=[])
    def raw(value):
        return value.encode("utf-8") if isinstance(value, str) else value
    return raw(incoming) == raw(existing)


class CashClosingFileMixin:
    def on_trash(self):
        protect_file(self, "on_trash")
        return super().on_trash()


def schema():
    if not enabled():
        return
    if not custody.enabled():
        frappe.throw("Chốt ca cần bật kh_aph_cash_custody")
    for dt in ("APH Phan bo quy", OPENING, SHIFT):
        frappe.reload_doc("kh_aph", "doctype", frappe.scrub(dt))
