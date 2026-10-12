"""Opt-in received funds; native Journal Entries own every GL/PLE mutation.

Routes are explicitly approved account mappings. No chart creation, bank swap,
automatic old-debt allocation, FIFO, commit, or MISA call is performed here.
"""
import hashlib
import html
import json
import frappe
from frappe.model.document import Document
from frappe.utils import cint, now
from kh_aph.funds_rules import money, position, check_action, order_figures

FLAG = "kh_aph_funds_workflow"
KINDS = ("Giữ cọc", "Chuyển cọc", "Giải phóng cọc", "Cấn hóa đơn", "Hoàn tiền", "Trả tiền thu hộ")


def require(manager=False):
    if not cint(frappe.conf.get(FLAG)):
        frappe.throw("Luồng tiền/cọc chưa được bật")
    roles = set(frappe.get_roles())
    allowed = {"Accounts Manager"} if manager else {"Accounts Manager", "Accounts User"}
    if frappe.session.user != "Administrator" and ("APH Không xem giá vốn" in roles or not roles & allowed):
        frappe.throw("Cần quyền kế toán phù hợp", frappe.PermissionError)


def has_permission(doc, user=None, permission_type=None):
    roles = set(frappe.get_roles(user or frappe.session.user))
    if (user or frappe.session.user) == "Administrator":
        return None
    if "APH Không xem giá vốn" in roles or not roles & {"Accounts User", "Accounts Manager"}:
        return False
    return None  # Preserve native role and Company User Permission checks.


def query_conditions(user=None):
    roles = set(frappe.get_roles(user or frappe.session.user))
    if (user or frappe.session.user) != "Administrator" and (
        "APH Không xem giá vốn" in roles or not roles & {"Accounts User", "Accounts Manager"}):
        return "1=0"
    return ""


def company(name):
    doc = frappe.get_doc("Company", name)
    doc.check_permission("read")
    if doc.abbr not in ("APH", "VH", "MK", "TL") or doc.default_currency != "VND":
        frappe.throw("Chỉ dùng APH/VH/MK/TL và VND")
    return doc


def account(name, co, root, bank=False):
    doc = frappe.get_doc("Account", name)
    doc.check_permission("read")
    if doc.company != co or doc.is_group or doc.disabled or doc.root_type != root or doc.account_currency != "VND":
        frappe.throw("Tài khoản cần chi tiết, hoạt động, VND và đúng đơn vị/loại sổ")
    if bank != (doc.account_type in ("Bank", "Cash")):
        frappe.throw("Tài khoản ngân hàng/quỹ và tài khoản giữ tiền cần chọn riêng")
    if not bank and doc.account_type in ("Receivable", "Payable"):
        frappe.throw("Tài khoản giữ/đối ứng không được là công nợ khách/nhà cung cấp")
    return doc


def checked(dt, name, permission="read"):
    doc = frappe.get_doc(dt, name)
    doc.check_permission(permission)
    return doc


def locked_receipt(name):
    frappe.db.sql("SELECT name FROM `tabAPH Funds Receipt` WHERE name=%s FOR UPDATE", name)
    receipt = checked("APH Funds Receipt", name)
    if receipt.docstatus != 1:
        frappe.throw("Tiền thực nhận chưa được ghi sổ")
    return receipt


def actions(receipt, exclude=None):
    filters = {"receipt": receipt, "docstatus": 1}
    if exclude:
        filters["name"] = ["!=", exclude]
    return frappe.get_all("APH Funds Action", filters=filters,
        fields=["name", "action_type", "amount", "source_reservation", "shared_order", "source_company", "invoice"])


def native_journal(receipt, rows, action=None, owner=None):
    values = {"doctype": "Journal Entry", "voucher_type": "Journal Entry",
              "company": receipt.company, "posting_date": receipt.posting_date,
              "user_remark": "Tiền/cọc theo kế hoạch: " + (action.reason if action else receipt.reason),
              "kh_aph_funds_receipt": receipt.name, "accounts": rows}
    if action:
        values.update(company=action.invoice_company if action.action_type == "Cấn hóa đơn" else receipt.company,
                      posting_date=action.posting_date, kh_aph_funds_action=action.name)
    if owner:
        values["company"] = owner
    frappe.flags.funds_internal = True
    try:
        doc = frappe.get_doc(values).insert()
        doc.submit()
        return doc.name
    finally:
        frappe.flags.funds_internal = False


def reverse_journal(name):
    frappe.flags.funds_internal = True
    try:
        checked("Journal Entry", name, "cancel").cancel()
    finally:
        frappe.flags.funds_internal = False


def protect_journal(doc, method=None):
    if doc.get("kh_aph_funds_receipt") or doc.get("kh_aph_funds_action"):
        if not frappe.flags.funds_internal:
            frappe.throw("Chứng từ tiền/cọc phải xử lý qua phiếu kế hoạch, không sửa/hủy riêng")


class FundsRoute(Document):
    def validate(self):
        require(True)
        company(self.receiving_company)
        account(self.holding_account, self.receiving_company, "Liability")
        if self.owner_company:
            company(self.owner_company)
            if self.owner_company != self.receiving_company:
                if not self.due_from_account:
                    frappe.throw("Cần tài khoản phải thu nội bộ của đơn vị chủ hàng để duyệt tuyến")
                account(self.due_from_account, self.owner_company, "Asset")
            elif self.due_from_account:
                frappe.throw("Tuyến cùng đơn vị không dùng tài khoản đối ứng liên company")
        elif self.due_from_account:
            frappe.throw("Chưa chọn đơn vị chủ hàng thì không có tài khoản đối ứng")

    def before_submit(self):
        self.validate()
        self.approved_by, self.approved_at = frappe.session.user, now()

    def before_update_after_submit(self):
        frappe.throw("Tuyến đã duyệt bất biến; lập tuyến mới khi thay đổi")

    def before_cancel(self):
        require(True)
        if frappe.db.exists("APH Funds Receipt", {"route": self.name, "docstatus": 1}) or frappe.db.exists("APH Funds Action", {"route": self.name, "docstatus": 1}):
            frappe.throw("Tuyến đã được dùng; cần xử lý chứng từ tiền/cọc trước")


class FundsReceipt(Document):
    def validate(self):
        require()
        company(self.company)
        account(self.bank_account, self.company, "Asset", bank=True)
        route = checked("APH Funds Route", self.route)
        if route.docstatus != 1 or route.receiving_company != self.company:
            frappe.throw("Chọn tuyến giữ tiền đã duyệt đúng đơn vị thực nhận")
        self.holding_account = route.holding_account
        account(self.holding_account, self.company, "Liability")
        if money(self.amount) <= 0 or not (self.external_reference or "").strip() or not (self.reason or "").strip():
            frappe.throw("Cần số tiền dương, tham chiếu giao dịch thực nhận và lý do")
        self.external_reference = self.external_reference.strip()
        self.external_key = hashlib.sha256((self.bank_account + "\0" + self.external_reference).encode()).hexdigest()
        if self.customer:
            checked("Customer", self.customer)
        if self.is_new() and self.journal_entry:
            frappe.throw("Không gắn thủ công chứng từ tiền")

    def on_submit(self):
        require()
        self.db_set("journal_entry", native_journal(self, [
            {"account": self.bank_account, "debit_in_account_currency": float(money(self.amount))},
            {"account": self.holding_account, "credit_in_account_currency": float(money(self.amount))},
        ]))
        if self.customer:
            frappe.db.set_value(self.doctype, self.name, {"identified_by": frappe.session.user, "identified_at": now()})

    def before_update_after_submit(self):
        frappe.throw("Phiếu thực thu đã ghi sổ bất biến; xác minh khách bằng thao tác riêng")

    def before_cancel(self):
        require(True)
        frappe.db.sql("SELECT name FROM `tabAPH Funds Receipt` WHERE name=%s FOR UPDATE", self.name)
        if actions(self.name):
            frappe.throw("Cần đảo các kế hoạch cọc/phân bổ/hoàn trước khi hủy thực thu")
        if self.journal_entry:
            reverse_journal(self.journal_entry)


class FundsAction(Document):
    def validate(self):
        require()
        receipt = checked("APH Funds Receipt", self.receipt)
        if receipt.docstatus != 1:
            frappe.throw("Chỉ xử lý tiền đã thực nhận")
        if not receipt.customer:
            frappe.throw("Cần xác minh khách trước khi giữ/phân bổ/hoàn tiền")
        self.customer, self.receiving_company = receipt.customer, receipt.company
        if self.action_type not in KINDS or money(self.amount) <= 0 or not (self.reason or "").strip():
            frappe.throw("Cần loại thao tác, số tiền dương và lý do/thỏa thuận")
        if self.is_new() and (self.journal_entry or self.owner_journal_entry):
            frappe.throw("Không gắn thủ công chứng từ kế hoạch")
        if self.source_reservation:
            source = checked("APH Funds Action", self.source_reservation)
            if source.receipt != receipt.name or source.docstatus != 1 or source.action_type not in ("Giữ cọc", "Chuyển cọc"):
                frappe.throw("Cọc nguồn không thuộc khoản thực thu hoặc không còn hiệu lực")
        if self.action_type == "Giữ cọc" and self.source_reservation:
            frappe.throw("Đổi cọc đã giữ cần thao tác Transfer, không tạo cọc giả mới")
        if self.action_type == "Trả tiền thu hộ" and self.source_reservation:
            frappe.throw("Thanh toán thu hộ cần chọn khoản đã cấn nợ chủ hàng, không dùng cọc mới")
        owner = checked("APH Funds Route", receipt.route).owner_company
        if self.action_type in ("Giữ cọc", "Chuyển cọc"):
            if not self.shared_order:
                frappe.throw("Chọn đơn cần giữ/chuyển cọc")
            order = checked("APH Shared Sales Order", self.shared_order)
            if order.docstatus != 1 or order.customer != receipt.customer:
                frappe.throw("Chọn đơn chung đã xác nhận của đúng khách")
            if self.source_company:
                company(self.source_company)
                if not frappe.db.exists("Sales Order", {"kh_aph_shared_order": order.name, "company": self.source_company, "docstatus": 1}):
                    frappe.throw("Nguồn cọc cần có phần hàng đang hiệu lực trong đơn")
            if owner and self.source_company != owner:
                frappe.throw("Tiền đã thuộc một chủ hàng; không đổi chủ tùy tiện")
        elif self.action_type == "Giải phóng cọc":
            if not self.source_reservation:
                frappe.throw("Chọn cọc cần giải phóng; tiền chỉ về chưa phân bổ, không vào nợ cũ")
        elif self.action_type == "Cấn hóa đơn":
            if not self.invoice:
                frappe.throw("Chọn hóa đơn ERP cần cấn")
            inv = checked("Sales Invoice", self.invoice)
            if inv.docstatus != 1 or inv.customer != receipt.customer or inv.is_return or inv.currency != "VND":
                frappe.throw("Chọn hóa đơn ERP đã ghi sổ VND của đúng khách")
            self.invoice_company = inv.company
            company(inv.company)
            if owner and inv.company != owner:
                frappe.throw("Tiền đã thuộc một chủ hàng; cần đúng chủ khi phân bổ")
            if money(self.amount) > money(inv.outstanding_amount):
                frappe.throw("Phân bổ vượt công nợ hóa đơn còn lại")
            linked = invoice_orders(inv)
            if self.source_reservation:
                if source.shared_order not in linked or (source.source_company and source.source_company != inv.company):
                    frappe.throw("Cọc giữ cho đơn/nguồn khác; cần duyệt chuyển hoặc giải phóng trước")
            if inv.company != receipt.company:
                if not self.route:
                    frappe.throw("Phân bổ liên company cần chọn tuyến đối ứng đã duyệt")
                route = checked("APH Funds Route", self.route)
                if (route.docstatus != 1 or route.receiving_company != receipt.company
                    or route.owner_company != inv.company or route.holding_account != receipt.holding_account):
                    frappe.throw("Phân bổ liên company cần tuyến đối ứng đã duyệt đúng tiền thực nhận/chủ hàng")
                account(route.due_from_account, inv.company, "Asset")
        elif self.action_type == "Trả tiền thu hộ":
            if not self.source_allocation:
                frappe.throw("Chọn khoản đã cấn nợ chủ hàng để trả thu hộ")
            allocation = checked("APH Funds Action", self.source_allocation)
            if allocation.docstatus != 1 or allocation.receipt != receipt.name or allocation.action_type != "Cấn hóa đơn" or allocation.invoice_company == receipt.company:
                frappe.throw("Chọn khoản đã phân bổ liên company của đúng thực thu")
            self.invoice_company, self.route = allocation.invoice_company, allocation.route
            account(self.bank_account, receipt.company, "Asset", bank=True)
            account(self.owner_bank_account, self.invoice_company, "Asset", bank=True)
            if not (self.external_reference or "").strip() or not (self.owner_external_reference or "").strip():
                frappe.throw("Cần tham chiếu thực chi và thực nhận của chủ hàng")
            used = frappe.db.sql("SELECT COALESCE(SUM(amount),0) FROM `tabAPH Funds Action` WHERE source_allocation=%s AND action_type='Trả tiền thu hộ' AND docstatus=1 AND name!=%s", (allocation.name, self.name))[0][0]
            if money(self.amount) + money(used) > money(allocation.amount):
                frappe.throw("Vượt tiền thu hộ còn phải trả cho chủ hàng")
            self.external_reference = self.external_reference.strip()
            self.owner_external_reference = self.owner_external_reference.strip()
            self.external_key = hashlib.sha256((self.bank_account + "\0" + self.external_reference).encode()).hexdigest()
            self.owner_external_key = hashlib.sha256((self.owner_bank_account + "\0" + self.owner_external_reference).encode()).hexdigest()
        elif self.action_type == "Hoàn tiền":
            account(self.bank_account, receipt.company, "Asset", bank=True)
            if not (self.external_reference or "").strip():
                frappe.throw("Hoàn tiền cần tham chiếu thực chi; không tự chuyển ngân hàng")
            self.external_reference = self.external_reference.strip()
            self.external_key = hashlib.sha256((self.bank_account + "\0" + self.external_reference).encode()).hexdigest()
        else:
            self.external_key = None

    def before_submit(self):
        require(True)
        receipt = locked_receipt(self.receipt)
        if self.action_type in ("Hoàn tiền", "Trả tiền thu hộ"):
            for bank in sorted({self.bank_account, self.owner_bank_account} - {None, ""}):
                frappe.db.sql("SELECT name FROM `tabAccount` WHERE name=%s FOR UPDATE", bank)
        if self.action_type == "Cấn hóa đơn":
            frappe.db.sql("SELECT name FROM `tabSales Invoice` WHERE name=%s FOR UPDATE", self.invoice)
        self.validate()
        try:
            check_action(receipt.amount, actions(receipt.name, self.name), self.as_dict())
        except ValueError as exc:
            frappe.throw(str(exc))
        self.approved_by, self.approved_at = frappe.session.user, now()

    def on_submit(self):
        receipt = locked_receipt(self.receipt)
        amount = float(money(self.amount))
        if self.action_type == "Cấn hóa đơn":
            inv = checked("Sales Invoice", self.invoice)
            debit = receipt.holding_account if inv.company == receipt.company else checked("APH Funds Route", self.route).due_from_account
            rows = [{"account": debit, "debit_in_account_currency": amount},
                    {"account": inv.debit_to, "credit_in_account_currency": amount,
                     "party_type": "Customer", "party": receipt.customer,
                     "reference_type": "Sales Invoice", "reference_name": inv.name}]
            # Cross-company allocation records owner receivable from the actual
            # receiver; receiver bank and held liability remain untouched.
            self.db_set("journal_entry", native_journal(receipt, rows, self))
        elif self.action_type == "Hoàn tiền":
            self.db_set("journal_entry", native_journal(receipt, [
                {"account": receipt.holding_account, "debit_in_account_currency": amount},
                {"account": self.bank_account, "credit_in_account_currency": amount},
            ], self))
        elif self.action_type == "Trả tiền thu hộ":
            route = checked("APH Funds Route", self.route)
            self.db_set("journal_entry", native_journal(receipt, [
                {"account": receipt.holding_account, "debit_in_account_currency": amount},
                {"account": self.bank_account, "credit_in_account_currency": amount},
            ], self))
            self.db_set("owner_journal_entry", native_journal(receipt, [
                {"account": self.owner_bank_account, "debit_in_account_currency": amount},
                {"account": route.due_from_account, "credit_in_account_currency": amount},
            ], self, owner=self.invoice_company))

    def before_update_after_submit(self):
        frappe.throw("Kế hoạch đã duyệt bất biến; đảo rồi lập lại, không sửa lịch sử")

    def before_cancel(self):
        require(True)
        locked_receipt(self.receipt)
        if frappe.db.exists("APH Funds Action", {"source_reservation": self.name, "docstatus": 1}):
            frappe.throw("Cọc đã được dùng/chuyển; cần đảo thao tác sau trước")
        if frappe.db.exists("APH Funds Action", {"source_allocation": self.name, "docstatus": 1}):
            frappe.throw("Tiền thu hộ đã trả chủ hàng; cần đảo thực chi/thực nhận trước")
        receipt = checked("APH Funds Receipt", self.receipt)
        try:
            position(receipt.amount, actions(receipt.name, self.name))
        except ValueError as exc:
            frappe.throw("Không thể đảo vì tiền đã dùng sau đó: " + str(exc))
        if self.owner_journal_entry:
            reverse_journal(self.owner_journal_entry)
        if self.journal_entry:
            reverse_journal(self.journal_entry)


def invoice_orders(inv):
    return set(frappe.db.get_value("Sales Order", row.sales_order, "kh_aph_shared_order")
               for row in inv.items if row.sales_order) - {None, ""}


@frappe.whitelist()
def identify_receipt(name, customer, reason):
    require(True)
    if not (reason or "").strip():
        frappe.throw("Cần lý do/xác minh khách")
    receipt = locked_receipt(name)
    receipt.check_permission("write")
    checked("Customer", customer)
    if receipt.customer:
        if receipt.customer != customer:
            frappe.throw("Khách đã xác minh; không chuyển tiền sang khách khác")
        return {"name": name, "customer": customer, "already_identified": True}
    frappe.db.set_value(receipt.doctype, receipt.name,
        {"customer": customer, "identified_by": frappe.session.user, "identified_at": now(), "identification_reason": reason})
    receipt.add_comment("Info", "Xác minh tiền thực nhận cho " + html.escape(customer) + ": " + html.escape(reason))
    return {"name": name, "customer": customer}


def unapplied_verified(customer):
    total = money(0)
    for receipt in frappe.get_all("APH Funds Receipt", filters={"docstatus": 1, "customer": customer}, fields=["name", "amount"]):
        total += position(receipt.amount, actions(receipt.name))["unspent"]
    return total


@frappe.whitelist()
def receipt_position(name):
    require()
    receipt = checked("APH Funds Receipt", name)
    return {k: str(v) if k != "reservations" else {n: str(a) for n, a in v.items()}
            for k, v in position(receipt.amount, actions(name)).items()}


@frappe.whitelist()
def create_action(values):
    """Approve a new plan atomically; normal saved drafts remain separately usable."""
    require(True)
    values = json.loads(values) if isinstance(values, str) else values
    fields = ("receipt", "action_type", "amount", "posting_date", "reason", "source_reservation",
              "source_allocation", "shared_order", "source_company", "invoice", "route",
              "bank_account", "owner_bank_account", "external_reference", "owner_external_reference")
    doc = frappe.get_doc({"doctype": "APH Funds Action", **{f: values.get(f) for f in fields}}).insert()
    doc.submit()
    return doc.as_dict()


@frappe.whitelist()
def reconcile_rows(company_name, bank_account, rows):
    """Import/reconcile JSON bank rows; does not write cash or auto-allocate."""
    require()
    company(company_name)
    account(bank_account, company_name, "Asset", bank=True)
    rows = json.loads(rows) if isinstance(rows, str) else rows
    result, seen = [], set()
    for row in rows:
        ref = str(row.get("external_reference") or "").strip()
        if not ref:
            frappe.throw("Dòng sao kê cần mã giao dịch ổn định")
        key = hashlib.sha256((bank_account + "\0" + ref).encode()).hexdigest()
        if key in seen:
            frappe.throw("Sao kê có mã giao dịch trùng: " + ref)
        seen.add(key)
        receipt = frappe.db.get_value("APH Funds Receipt", {"external_key": key}, ["name", "amount", "posting_date", "docstatus"], as_dict=True)
        status = "Chưa ghi thực thu"
        if receipt:
            checked("APH Funds Receipt", receipt.name)
            status = "Khớp" if (receipt.docstatus == 1 and money(row["amount"]) == money(receipt.amount)
                and str(row["posting_date"]) == str(receipt.posting_date)) else "Cần đối soát"
        result.append({"external_reference": ref, "status": status, "receipt": receipt.name if receipt else None})
    return result


def guard_native_order_advance(doc, method=None):
    if not cint(frappe.conf.get(FLAG)):
        return
    for row in doc.get("references") or []:
        if row.reference_doctype == "Sales Order" and frappe.db.get_value("Sales Order", row.reference_name, "kh_aph_shared_order"):
            frappe.throw("Cọc đơn chung cần ghi thực thu và kế hoạch giữ/phân bổ riêng; không tự cấn advance")


@frappe.whitelist()
def shared_financials(name):
    if not cint(frappe.conf.get(FLAG)):
        frappe.throw("Luồng tiền/cọc chưa bật")
    from kh_aph.price_visibility import is_price_restricted
    if is_price_restricted():
        frappe.throw("Không có quyền xem số tiền", frappe.PermissionError)
    order = checked("APH Shared Sales Order", name)
    orders = frappe.get_all("Sales Order", filters={"kh_aph_shared_order": name, "docstatus": 1}, pluck="name")
    for so in orders:
        checked("Sales Order", so)
    invoices = set(frappe.get_all("Sales Invoice Item", filters={"sales_order": ["in", orders]}, pluck="parent")) if orders else set()
    delivered, debt = money(0), money(0)
    for inv_name in invoices:
        inv = checked("Sales Invoice", inv_name)
        if inv.docstatus != 1:
            continue
        if inv.customer != order.customer or invoice_orders(inv) != {name}:
            frappe.throw("Hóa đơn gộp nhiều đơn cần tách số công nợ theo nguồn trước")
        delivered += money(inv.grand_total)
        debt += money(inv.outstanding_amount)
    reserved = money(0)
    for r in frappe.get_all("APH Funds Action", filters={"docstatus": 1, "shared_order": name,
        "action_type": ["in", ["Giữ cọc", "Chuyển cọc"]]}, fields=["name", "receipt"]):
        receipt = frappe.get_doc("APH Funds Receipt", r.receipt)
        if receipt.docstatus != 1 or receipt.customer != order.customer:
            frappe.throw("Cọc và đơn không khớp khách/trạng thái")
        reserved += position(receipt.amount, actions(receipt.name))["reservations"].get(r.name, money(0))
    try:
        return {k: str(v) for k, v in order_figures(order.net_total, delivered, debt, reserved).items()}
    except ValueError as exc:
        frappe.throw(str(exc))
