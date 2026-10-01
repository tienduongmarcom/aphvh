"""Thuế GTGT theo loại khách (0.3.5). Quy tắc thuần ở vat_rules.py.

- Customer: chưa có Loại thuế thì app tự phân loại theo MST và tên (kế toán sửa được, không ghi đè).
- Đơn bán, phiếu giao, hóa đơn "Có" xuất hóa đơn: lấy Loại thuế của khách, chọn mẫu thuế từng mặt hàng
  theo loại khách (mặt hàng trước, rồi nhóm hàng và nhóm cha) — chạy trước validate của ERPNext.
- Cài đặt: Loại thuế, mẫu thuế mặt hàng và mẫu thuế bán hàng cho mọi công ty có TK 33311.
- load_rules: nạp quy tắc thuế theo nhóm hàng / mặt hàng (tệp của kế toán trưởng hoặc dữ liệu thử).
"""

import frappe
from frappe.utils import cstr, flt

from aphvh import vat_rules as V
from aphvh.constants import INV_FLAG, INV_YES

F_REASON = "aphvh_ly_do_loai_thue"  # Customer


# --- Khách ----------------------------------------------------------------------------------


def validate_customer(doc, method=None):
    if doc.get("tax_category"):
        return
    cat, why = V.classify_customer(doc.customer_name, doc.get("tax_id"))
    doc.tax_category = cat
    if doc.meta.has_field(F_REASON):
        doc.set(F_REASON, f"App tự phân loại: {why}")


def classify_missing_customers() -> dict:
    """Gán Loại thuế cho khách chưa có (không đụng khách kế toán đã đặt)."""
    ensure_tax_categories()
    has_reason = frappe.get_meta("Customer").has_field(F_REASON)
    out = {c: 0 for c in V.CATEGORIES}
    for c in frappe.get_all("Customer", {"tax_category": ["in", ("", None)]}, ["name", "customer_name", "tax_id"]):
        cat, why = V.classify_customer(c.customer_name, c.tax_id)
        vals = {"tax_category": cat}
        if has_reason:
            vals[F_REASON] = f"App tự phân loại: {why}"
        frappe.db.set_value("Customer", c.name, vals, update_modified=False)
        out[cat] += 1
    return out


# --- Chứng từ bán -----------------------------------------------------------------------------


def _flag(doc) -> str:
    if doc.get(INV_FLAG):
        return doc.get(INV_FLAG)
    return cstr(frappe.get_cached_value("Customer", doc.customer, INV_FLAG)) if doc.get("customer") else ""


def _sales_tax_template(company: str) -> str | None:
    abbr = frappe.get_cached_value("Company", company, "abbr")
    name = f"{V.SALES_TAX_TEMPLATE} - {abbr}"
    return name if frappe.db.exists("Sales Taxes and Charges Template", name) else None


def before_validate_sales(doc, method=None):
    """Sales Order / Delivery Note / Sales Invoice "Có": thuế theo loại khách, trước validate của ERPNext."""
    if not doc.get("customer") or not doc.meta.has_field(INV_FLAG):
        return
    if doc.get("is_internal_customer") or doc.get("is_opening") == "Yes" or doc.get("is_return"):
        return
    if _flag(doc) != INV_YES:
        return
    cat = frappe.get_cached_value("Customer", doc.customer, "tax_category")
    if cat:
        doc.tax_category = cat
    acc = _vat_account(doc.company)
    if not acc:
        return  # hộ kinh doanh: không có thuế GTGT khấu trừ trên hóa đơn
    has_vat_row = any(t.get("account_head") == acc for t in doc.get("taxes") or [])
    if not has_vat_row and doc.meta.has_field("taxes_and_charges"):
        tpl = _sales_tax_template(doc.company)
        if tpl:
            doc.set("taxes", [])
            doc.taxes_and_charges = tpl
            doc.append_taxes_from_master("Sales Taxes and Charges Template")
    if not doc.get("tax_category"):
        return
    from erpnext.stock.get_item_details import get_item_tax_map, get_item_tax_template

    date = doc.get("posting_date") or doc.get("transaction_date")
    for row in doc.get("items") or []:
        if not row.get("item_code"):
            continue
        ctx = frappe._dict(
            company=doc.company,
            tax_category=doc.tax_category,
            posting_date=date,
            transaction_date=date,
            item_code=row.item_code,
            base_net_rate=row.get("base_net_rate") or row.get("base_rate"),
            item_tax_template=None,
        )
        tpl = get_item_tax_template(ctx)
        if tpl and tpl != row.get("item_tax_template"):
            row.item_tax_template = tpl
            row.item_tax_rate = get_item_tax_map(doc=doc, tax_template=tpl, as_json=True)


def missing_category_message(doc) -> str | None:
    if doc.get("tax_category"):
        return None
    return (
        f"Khách {frappe.bold(doc.customer)} chưa có Loại thuế (Doanh nghiệp/HTX hay Hộ KD/cá nhân) "
        "nên chưa chọn được thuế suất. Kế toán đặt Loại thuế trên hồ sơ khách."
    )


# --- Cài đặt ----------------------------------------------------------------------------------


def ensure_tax_categories():
    for c in V.CATEGORIES:
        if not frappe.db.exists("Tax Category", c):
            frappe.get_doc({"doctype": "Tax Category", "title": c}).insert(ignore_permissions=True)


def _vat_account(company: str) -> str | None:
    if not company:
        return None
    return frappe.db.get_value(
        "Account", {"company": company, "account_number": V.VAT_ACCOUNT_NUMBER, "is_group": 0}, "name"
    )


def ensure_vat_templates() -> list:
    """Mẫu thuế mặt hàng và mẫu thuế bán hàng cho công ty có TK 33311 (hộ KD không có: bỏ qua)."""
    ensure_tax_categories()
    made = []
    for co, abbr in frappe.get_all("Company", fields=["name", "abbr"], as_list=True):
        acc = _vat_account(co)
        if not acc:
            continue
        for title, rate in V.VAT_TEMPLATES:
            if frappe.db.exists("Item Tax Template", f"{title} - {abbr}"):
                continue
            frappe.get_doc(
                {
                    "doctype": "Item Tax Template",
                    "title": title,
                    "company": co,
                    "taxes": [{"tax_type": acc, "tax_rate": rate}],
                }
            ).insert(ignore_permissions=True)
            made.append(f"{title} - {abbr}")
        name = f"{V.SALES_TAX_TEMPLATE} - {abbr}"
        if not frappe.db.exists("Sales Taxes and Charges Template", name):
            has_default = frappe.db.exists("Sales Taxes and Charges Template", {"company": co, "is_default": 1})
            frappe.get_doc(
                {
                    "doctype": "Sales Taxes and Charges Template",
                    "title": V.SALES_TAX_TEMPLATE,
                    "company": co,
                    "is_default": 0 if has_default else 1,
                    "taxes": [
                        {
                            "charge_type": "On Net Total",
                            "account_head": acc,
                            "description": "Thuế GTGT đầu ra",
                            "rate": 0,
                        }
                    ],
                }
            ).insert(ignore_permissions=True)
            made.append(name)
    return made


def _set_taxes(doc, mapping: dict) -> int:
    """mapping {loại khách: tiêu đề mẫu}: đặt dòng thuế của mặt hàng / nhóm hàng theo từng công ty.

    Ghi thẳng bảng con Item Tax (không lưu cả nhóm hàng: lưu nhóm gốc làm ERPNext tự gắn nhóm cha
    là chính nó và báo lỗi vòng lặp). Dòng cùng loại khách + cùng công ty thì sửa tại chỗ, thiếu thì thêm.
    Không xóa dòng nào.
    """
    have = frappe.get_all(
        "Item Tax",
        {"parenttype": doc.doctype, "parent": doc.name, "parentfield": "taxes"},
        ["name", "item_tax_template", "tax_category", "idx"],
        order_by="idx",
    )
    idx = max([h.idx for h in have] or [0])
    n = 0
    for co, abbr in frappe.get_all("Company", fields=["name", "abbr"], as_list=True):
        for cat, title in mapping.items():
            tpl = f"{title} - {abbr}"
            if not frappe.db.exists("Item Tax Template", tpl):
                continue
            same = [
                h for h in have
                if cstr(h.tax_category) == cat
                and frappe.get_cached_value("Item Tax Template", h.item_tax_template, "company") == co
            ]
            if same:
                if same[0].item_tax_template != tpl:
                    frappe.db.set_value("Item Tax", same[0].name, "item_tax_template", tpl, update_modified=False)
            else:
                idx += 1
                frappe.get_doc(
                    {
                        "doctype": "Item Tax",
                        "parenttype": doc.doctype,
                        "parentfield": "taxes",
                        "parent": doc.name,
                        "idx": idx,
                        "item_tax_template": tpl,
                        "tax_category": cat,
                    }
                ).db_insert()
            n += 1
    frappe.clear_document_cache(doc.doctype, doc.name)
    return n


def load_rules(rules: list) -> dict:
    """Nạp quy tắc thuế. Mỗi dòng: {"item_group" | "item_code": ...} và
    "nhan": "Không kê khai tính nộp" | "5%" | ... (áp cho cả hai loại khách), hoặc "dn" / "hkd" riêng từng loại.

    "Mặc định" thì bỏ qua (theo nhóm cha). Nhóm hàng gốc "All Item Groups" mang quy tắc mặc định của app.
    """
    ensure_vat_templates()
    out = {"nhom": 0, "ma": 0, "bo_qua": 0, "loi": []}
    for r in rules:
        try:
            mapping = V.templates_for_row(r)
        except ValueError as e:
            out["loi"].append(str(e))
            continue
        if not mapping:
            out["bo_qua"] += 1
            continue
        if r.get("item_code"):
            if not frappe.db.exists("Item", r["item_code"]):
                out["loi"].append(f"Không có mã {r['item_code']}")
                continue
            _set_taxes(frappe._dict(doctype="Item", name=r["item_code"]), mapping)
            out["ma"] += 1
        elif r.get("item_group"):
            if not frappe.db.exists("Item Group", r["item_group"]):
                out["loi"].append(f"Không có nhóm {r['item_group']}")
                continue
            _set_taxes(frappe._dict(doctype="Item Group", name=r["item_group"]), mapping)
            out["nhom"] += 1
    return out


def setup_defaults():
    """after_install / after_migrate: loại thuế, mẫu thuế, phân loại khách còn trống,
    quy tắc mặc định ở nhóm gốc nếu nhóm gốc chưa có dòng thuế nào.
    Lỗi ở đây không làm hỏng migrate: ghi Error Log để xem lại."""
    try:
        _setup_defaults()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title="aphvh: cài đặt thuế GTGT theo loại khách lỗi")


def _setup_defaults():
    ensure_vat_templates()
    classify_missing_customers()
    rules = default_root_rules()
    if rules and not frappe.get_all("Item Tax", {"parenttype": "Item Group", "parent": rules[0]["item_group"]}, limit=1):
        load_rules(rules)


def default_root_rules() -> list:
    """Quy tắc mặc định: gắn ở nhóm gốc — nông sản chưa chế biến / sơ chế thông thường."""
    root = frappe.db.get_value("Item Group", {"parent_item_group": ("is", "not set"), "is_group": 1}, "name")
    return [{"item_group": root, "nhan": V.T_KKKTN}] if root else []
