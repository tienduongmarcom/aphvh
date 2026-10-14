"""Read-only inventory for handoff; deliberately does not certify acceptance."""
import importlib
import frappe
from frappe.utils import cint

FLAGS = (
    "kh_aph_server_cost_guard", "kh_aph_post_receivable_on_delivery",
    "kh_aph_shared_sales_order", "kh_aph_global_credit_warning",
    "kh_aph_high_risk_credit_guard", "kh_aph_quantity_valuation_mvp", "kh_aph_funds_workflow", "kh_aph_source_change",
    "kh_aph_factory_costing", "kh_aph_factory_cash", "kh_aph_sales_adjust", "kh_aph_data_review",
    "kh_aph_kho_chuan", "kh_aph_sales_p1", "kh_aph_quan_tri",
    "kh_aph_du_lieu", "kh_aph_dau_ky",
)
COUNTS = (
    "User", "Customer", "Supplier", "Item", "Warehouse", "Sales Order",
    "Delivery Note", "Sales Invoice", "Payment Entry", "Stock Entry",
    "GL Entry", "Stock Ledger Entry", "Payment Ledger Entry", "BOM", "Work Order",
    "APH Shared Sales Order", "APH Pending Receipt", "APH Bag Movement", "APH Credit Release",
    "APH Funds Route", "APH Funds Receipt", "APH Funds Action", "APH Source Change",
)


def inspect(dung_user=None):
    """Invoke with bench execute; no HTTP endpoint, changes or secret configuration."""
    if frappe.local.site not in ("frontend", "aphvh-web-uat", "aphvh-uat"):
        frappe.throw("Chỉ kiểm kê site dự án mới; không dùng erpnext.local")
    if frappe.session.user != "Administrator":
        frappe.throw("Cần Administrator để đọc đầy đủ kiểm kê", frappe.PermissionError)
    # The DB itself rejects writes throughout this inventory transaction.
    frappe.db.rollback()
    frappe.db.sql("START TRANSACTION READ ONLY")
    try:
        installed = frappe.get_installed_apps()
        versions = {app: str(getattr(importlib.import_module(app), "__version__", "unknown")) for app in installed}
        companies = frappe.get_all("Company", fields=["name", "abbr", "default_currency"])
        warehouses = frappe.get_all("Warehouse", filters={"is_group": 0, "disabled": 0}, fields=["name", "company"])
        items = frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0}, fields=["name", "stock_uom", "valuation_method"])
        result = {
            "site": frappe.local.site, "read_only": True, "acceptance": "NOT_TESTED",
            "versions": versions, "installed_apps": installed, "companies": companies,
            "leaf_warehouses": warehouses, "stock_items": items,
            "flags": {flag: cint(frappe.conf.get(flag)) for flag in FLAGS},
            "counts": {dt: frappe.db.count(dt) if frappe.db.exists("DocType", dt) else None for dt in COUNTS},
            "dung_identity": {"status": "NOT_PROVIDED"},
            "release_gates": ["Native Desk business acceptance", "Opening physical bag counts",
                "Planned receipts/deposits/intercompany allocation", "Original 202 decision reconciliation",
                "Versioned release image and migration/rollback rehearsal"],
        }
        if dung_user:
            if not frappe.db.exists("User", dung_user):
                result["dung_identity"] = {"status": "NOT_FOUND"}
            else:
                roles = frappe.get_roles(dung_user)
                result["dung_identity"] = {"status": "IDENTITY_READ_ONLY_NOT_TESTED",
                    "enabled": cint(frappe.db.get_value("User", dung_user, "enabled")),
                    "roles": roles, "explicit_no_cost_role": "APH Không xem giá vốn" in roles}
        return result
    finally:
        frappe.db.rollback()
