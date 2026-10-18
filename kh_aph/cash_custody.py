"""Người thực giữ tiền trên nguồn; báo cáo chỉ đọc GL, không tạo sổ tiền thứ hai.

Lát 2A chưa chốt ca/chuyển trách nhiệm: để trống là chưa xác minh, tuyệt đối
không suy từ owner. Một tài khoản Cash trên một JE chỉ có một người giữ.
"""
import frappe
from frappe.utils import cint, getdate

FLAG = "kh_aph_cash_custody"
HOLDER = "kh_aph_nguoi_giu_tien"
PAYER = "kh_aph_nguoi_giao_tien"
SOURCES = ("Payment Entry", "Journal Entry", "Sales Invoice", "Purchase Invoice", "POS Invoice")
HEADS = (*SOURCES, "APH Funds Receipt", "APH Funds Action", "APH Phieu quy nha may")


def enabled():
    return cint(frappe.conf.get(FLAG))


def schema():
    if not enabled():
        return
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    fields = {}
    for dt in HEADS:
        # JE ghi theo dòng tài khoản, không có ô đầu phiếu gây mơ hồ nhiều quỹ.
        if dt == "Journal Entry" or not frappe.db.exists("DocType", dt):
            continue
        after = {"Payment Entry": "paid_to", "Sales Invoice": "customer", "POS Invoice": "customer",
                 "Purchase Invoice": "cash_bank_account", "APH Funds Receipt": "bank_account",
                 "APH Funds Action": "owner_bank_account", "APH Phieu quy nha may": "company"}[dt]
        fields[dt] = [_field(HOLDER, "Người thực giữ/nhận tiền mặt", insert_after=after)]
        if dt in ("Payment Entry", "APH Funds Action"):
            fields[dt].append(_field(PAYER, "Người thực giao/chi tiền mặt", insert_after="paid_from" if dt == "Payment Entry" else "bank_account"))
    fields["Journal Entry Account"] = [_field(HOLDER, "Người thực giữ tiền mặt", in_list_view=1, insert_after="account")]
    create_custom_fields(fields)
    frappe.reload_doc("kh_aph", "report", "ra_nguoi_giu_tien_mat")


def _field(name, label, **extra):
    return {"fieldname": name, "label": label, "fieldtype": "Link", "options": "User",
            "no_copy": 1, "depends_on": "eval:frappe.boot.kh_aph && frappe.boot.kh_aph.cash_custody",
            "description": "Chỉ tiền mặt. Để trống là chưa xác minh; không mặc định người lập phiếu.", **extra}


def cash(account):
    return bool(account) and frappe.get_cached_value("Account", account, "account_type") == "Cash"


def _person(user, company):
    if not user:
        return
    data = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
    if user in ("Guest",) or not data or not data.enabled or data.user_type != "System User":
        frappe.throw("Người giữ tiền phải là tài khoản nội bộ đang hoạt động")
    co = frappe.get_doc("Company", company)
    co.check_permission("read")
    if not frappe.has_permission("Company", "read", doc=co, user=user):
        frappe.throw("Người giữ tiền chưa được cấp phạm vi đơn vị này", frappe.PermissionError)


def _values(doc):
    if doc.doctype == "Journal Entry":
        return [(r.name, r.account, r.get(HOLDER) or "") for r in doc.get("accounts") or []]
    return [(field, doc.get(field) or "") for field in (HOLDER, PAYER)]


def validate(doc, method=None):
    if not enabled():
        return
    old = doc.get_doc_before_save()
    if old and cint(old.docstatus) == 1:
        if _values(old) != _values(doc):
            frappe.throw("Không đổi người giữ tiền trên phiếu đã ghi sổ; giữ nguyên lịch sử nguồn")
        return
    if doc.doctype == "Journal Entry":
        accounts = {}
        for row in doc.get("accounts") or []:
            holder = row.get(HOLDER)
            if holder and not cash(row.account):
                frappe.throw("Chỉ chọn người giữ tiền trên dòng tài khoản tiền mặt")
            if cash(row.account):
                # GL có thể gộp các dòng cùng account: cấm hai người khác nhau
                # (kể cả một dòng chưa xác minh) để không gán sai số tiền.
                previous = accounts.setdefault(row.account, holder or "")
                if previous != (holder or ""):
                    frappe.throw("Cùng tài khoản tiền mặt trên một bút toán phải cùng người giữ; tách phiếu nếu khác người")
                _person(holder, doc.company)
    else:
        co = doc.get("company") or doc.get("receiving_company")
        for field in (HOLDER, PAYER):
            # Funds Action có company nhận/chủ khác nhau; kiểm phía thực nhận riêng.
            target = doc.get("invoice_company") if doc.doctype == "APH Funds Action" and field == HOLDER and doc.get("action_type") == "Trả tiền thu hộ" else co
            if doc.get(field):
                _person(doc.get(field), target)


def stamp_rows(rows, holders):
    """Chỉ truyền metadata vào JE sắp tạo, giữ nguyên tài khoản/số tiền."""
    if enabled():
        for row in rows:
            holder = holders.get(row.get("account"))
            if holder and cash(row.get("account")):
                row[HOLDER] = holder
    return rows


def _source_holder(doc, account):
    if doc.doctype == "Payment Entry":
        return doc.get(HOLDER) if doc.paid_to == account else doc.get(PAYER) if doc.paid_from == account else None
    if doc.doctype == "Journal Entry":
        users = {r.get(HOLDER) or "" for r in doc.accounts if r.account == account}
        return next(iter(users)) if len(users) == 1 else None
    return doc.get(HOLDER)


@frappe.whitelist()
def review(company, from_date, to_date):
    """Phát sinh Cash theo nguồn, không phải số tồn hiện tại theo người."""
    if not enabled():
        frappe.throw("Theo dõi người giữ tiền chưa được bật")
    if not isinstance(company, str) or not company.strip():
        frappe.throw("Chọn đơn vị hợp lệ")
    roles = set(frappe.get_roles())
    if "APH Không xem giá vốn" in roles or "Kế toán nhà máy" in roles or not roles & {"Accounts User", "Accounts Manager", "System Manager"}:
        frappe.throw("Cần quyền kế toán để rà người giữ tiền", frappe.PermissionError)
    co = frappe.get_doc("Company", company)
    co.check_permission("read")
    if co.default_currency != "VND":
        frappe.throw("Bảng rà hiện chỉ hỗ trợ đơn vị dùng VND")
    if not from_date or not to_date:
        frappe.throw("Chọn đủ ngày bắt đầu và kết thúc")
    start, end = getdate(from_date), getdate(to_date)
    if not 0 <= (end - start).days <= 30:
        frappe.throw("Chọn khoảng ngày hợp lệ, tối đa 31 ngày")
    accounts = frappe.get_list("Account", filters={"company": company, "account_type": "Cash", "is_group": 0}, pluck="name", limit_page_length=0)
    if not accounts:
        return []
    rows = frappe.get_list("GL Entry", filters={"company": company, "account": ["in", accounts],
        "posting_date": ["between", [str(start), str(end)]], "is_cancelled": 0},
        fields=["name", "posting_date", "account", "voucher_type", "voucher_no", "debit", "credit"],
        order_by="posting_date, creation, name", limit_page_length=5001)
    if len(rows) > 5000:
        frappe.throw("Có hơn 5.000 dòng; thu hẹp khoảng ngày để xem đủ dữ liệu")
    cache = {}
    result = []
    for row in rows:
        key = (row.voucher_type, row.voucher_no)
        if key not in cache:
            source = None
            if row.voucher_type in SOURCES and frappe.db.exists(row.voucher_type, row.voucher_no):
                candidate = frappe.get_doc(row.voucher_type, row.voucher_no)
                if candidate.has_permission("read") and candidate.company == company:
                    source = candidate
            cache[key] = source
        source = cache[key]
        holder = _source_holder(source, row.account) if source else None
        result.append({"gl_entry": row.name, "posting_date": row.posting_date, "account": row.account,
            "voucher_type": row.voucher_type, "voucher_no": row.voucher_no, "debit": row.debit, "credit": row.credit,
            "holder": holder or "", "status": "Đã ghi người giữ trên nguồn" if holder else "Chưa xác minh"})
    return result
