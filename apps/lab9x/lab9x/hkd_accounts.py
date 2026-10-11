"""Hệ thống tài khoản cho hộ kinh doanh nộp thuế theo thu nhập (TT152/2025, doanh thu > 3 tỷ) — 0.4.9.

TT152 không ban hành hệ thống tài khoản cho hộ kinh doanh (ghi sổ S2c–S2e). ERPNext cần tài khoản để ghi sổ,
nên app dùng số hiệu quen thuộc theo TT133 và tách chi phí theo các khoản thường gặp của sổ S2c, để kế toán
lọc "chi phí hợp lý" theo từng loại. Kế toán trưởng sửa tên / thêm bớt được trong ERPNext.

Chạy: bench --site <site> execute lab9x.hkd_accounts.setup --kwargs '{"company": "HKD Minh Khang"}'
Chạy lại an toàn: tài khoản đã có (theo số hiệu) thì chỉ sửa tên/nhóm, không tạo trùng, không xóa.
"""

# frappe nhập trong hàm: plan() kiểm thử được không cần Frappe.

# (số hiệu, tên, root_type, account_type, nhóm cha theo số hiệu hoặc None = gốc của root_type, là nhóm)
GROUP_CP = "642"
ACCOUNTS = [
    ("1111", "Tiền mặt", "Asset", "Cash", None, 0),
    ("1121", "Tiền gửi ngân hàng", "Asset", "Bank", None, 0),
    ("131", "Phải thu khách hàng", "Asset", "Receivable", None, 0),
    ("1561", "Hàng hóa", "Asset", "Stock", None, 0),
    ("331", "Phải trả người bán", "Liability", "Payable", None, 0),
    ("3339", "Thuế GTGT, TNCN phải nộp", "Liability", "Tax", None, 0),
    ("5111", "Doanh thu bán hàng hóa", "Income", "Income Account", None, 0),
    ("711", "Thu nhập khác", "Income", "Income Account", None, 0),
    ("632", "Giá vốn hàng bán", "Expense", "Cost of Goods Sold", None, 0),
    (GROUP_CP, "Chi phí kinh doanh", "Expense", "", None, 1),
    ("6421", "Chi phí nhân công (tiền lương, tiền công)", "Expense", "Expense Account", GROUP_CP, 0),
    ("6422", "Chi phí vận chuyển, bốc xếp", "Expense", "Expense Account", GROUP_CP, 0),
    ("6423", "Chi phí thuê mặt bằng, kho bãi", "Expense", "Expense Account", GROUP_CP, 0),
    ("6424", "Chi phí điện, nước, điện thoại, internet", "Expense", "Expense Account", GROUP_CP, 0),
    ("6425", "Chi phí khấu hao tài sản, công cụ dụng cụ", "Expense", "Expense Account", GROUP_CP, 0),
    ("6426", "Chi phí lãi vay", "Expense", "Expense Account", GROUP_CP, 0),
    ("6427", "Thuế, phí, lệ phí (trừ thuế TNCN)", "Expense", "Expense Account", GROUP_CP, 0),
    ("6428", "Chi phí khác", "Expense", "Expense Account", GROUP_CP, 0),
]

# Tài khoản cũ cần đổi số hiệu trước khi tạo mới (số cũ, tên cũ chứa, số mới): giữ nguyên bút toán đã ghi.
RENUMBER = [("6422", "chỉ quản trị", "6428")]

DEFAULTS = {
    "default_receivable_account": "131",
    "default_payable_account": "331",
    "default_income_account": "5111",
    "default_expense_account": "632",  # giá vốn khi bán hàng (ERPNext lấy TK chi phí mặc định làm TK giá vốn)
    "default_cash_account": "1111",
    "default_bank_account": "1121",
    "default_inventory_account": "1561",
    "stock_adjustment_account": "632",
}


def plan(existing: dict) -> list:
    """existing: {số hiệu: {"name", "account_name", "parent_number", "is_group"}} -> danh sách việc (thuần, để kiểm thử).

    Việc: ("doi_so", số cũ, số mới) | ("tao", số) | ("sua", số, {trường: giá trị mới}).
    """
    ex = {k: dict(v) for k, v in existing.items()}
    jobs = []
    for old, contains, new in RENUMBER:
        a = ex.get(old)
        if a and contains in (a.get("account_name") or "") and new not in ex:
            jobs.append(("doi_so", old, new))
            ex[new] = ex.pop(old)
    for no, name, _root, _typ, parent, is_group in ACCOUNTS:
        a = ex.get(no)
        if not a:
            jobs.append(("tao", no))
            continue
        diff = {}
        if a.get("account_name") != name:
            diff["account_name"] = name
        if parent and a.get("parent_number") != parent:
            diff["parent_number"] = parent
        if diff:
            jobs.append(("sua", no, diff))
    return jobs


def _existing(company):
    import frappe

    rows = frappe.get_all("Account", {"company": company}, ["name", "account_name", "account_number", "parent_account", "is_group"])
    num = {r.name: r.account_number for r in rows}
    return {r.account_number: {"name": r.name, "account_name": r.account_name, "is_group": r.is_group,
                               "parent_number": num.get(r.parent_account)} for r in rows if r.account_number}


def _root(company, root_type):
    import frappe

    return frappe.db.get_value("Account", {"company": company, "root_type": root_type, "is_group": 1,
                                            "parent_account": ["in", ("", None)]}, "name")


def setup(company: str) -> dict:
    import frappe
    from erpnext.accounts.doctype.account.account import update_account_number

    if not frappe.db.exists("Company", company):
        frappe.throw(f"Không có công ty {company}")
    spec = {a[0]: a for a in ACCOUNTS}
    jobs = plan(_existing(company))
    done = []
    for job in jobs:
        ex = _existing(company)
        if job[0] == "doi_so":
            _, old, new = job
            update_account_number(ex[old]["name"], spec[new][1], account_number=new)
            done.append(f"đổi {old} → {new} {spec[new][1]}")
        elif job[0] == "tao":
            no = job[1]
            _, name, root, typ, parent, is_group = spec[no]
            par = ex[parent]["name"] if parent else _root(company, root)
            frappe.get_doc({"doctype": "Account", "company": company, "account_name": name, "account_number": no,
                            "parent_account": par, "account_type": typ, "is_group": is_group,
                            "account_currency": "VND"}).insert(ignore_permissions=True)
            done.append(f"tạo {no} {name}")
        else:
            _, no, diff = job
            doc = frappe.get_doc("Account", ex[no]["name"])
            if "parent_number" in diff:
                doc.parent_account = ex[diff["parent_number"]]["name"]
            doc.save(ignore_permissions=True)
            if "account_name" in diff:
                update_account_number(doc.name, diff["account_name"], account_number=no)
            done.append(f"sửa {no}: {', '.join(diff)}")
    ex = _existing(company)
    meta = frappe.get_meta("Company")
    for f, no in DEFAULTS.items():
        if meta.has_field(f) and no in ex and not ex[no]["is_group"]:
            frappe.db.set_value("Company", company, f, ex[no]["name"])
    frappe.db.commit()
    return {"viec": done, "tai_khoan": sorted(ex)}
