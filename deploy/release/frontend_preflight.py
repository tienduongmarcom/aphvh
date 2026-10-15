"""Standalone frontend inventory. No installation, writes or secret export.

Run with backend env/bin/python, stdin, cwd frappe-bench/sites.
The report is inventory evidence, not business acceptance.
"""
import importlib
import json
import frappe

SITE = "frontend"
ROOT = "/home/frappe/frappe-bench/sites"
FLAGS = ("kh_aph_server_cost_guard", "kh_aph_post_receivable_on_delivery",
    "kh_aph_shared_sales_order", "kh_aph_global_credit_warning",
    "kh_aph_high_risk_credit_guard", "kh_aph_quantity_valuation_mvp",
    "kh_aph_funds_workflow", "kh_aph_source_change",
         "kh_aph_factory_costing", "kh_aph_factory_cash", "kh_aph_sales_adjust", "kh_aph_data_review",
         "kh_aph_kho_chuan", "kh_aph_sales_p1", "kh_aph_quan_tri",
         "kh_aph_du_lieu", "kh_aph_dau_ky", "kh_aph_kho_van_hanh", "kh_aph_gia_san",
         "kh_aph_trung_tam_ban", "kh_aph_tien_vay")
DOCTYPES = ("User", "Customer", "Supplier", "Item", "Warehouse", "Sales Order",
    "Delivery Note", "Sales Invoice", "Purchase Receipt", "Purchase Invoice",
    "Payment Entry", "Journal Entry", "Stock Entry", "GL Entry", "Stock Ledger Entry",
    "Payment Ledger Entry", "BOM", "Work Order", "APH Funds Route", "APH Funds Receipt",
    "APH Funds Action", "APH Source Change", "APH Pending Receipt", "APH Bag Movement")

frappe.init(site=SITE, sites_path=ROOT)
try:
    frappe.connect()
    frappe.set_user("Administrator")
    frappe.db.rollback()
    frappe.db.sql("START TRANSACTION READ ONLY")
    apps = frappe.get_installed_apps()
    item_fields = ["name", "stock_uom", "valuation_method"]
    if frappe.db.has_column("Item", "kh_aph_kg_per_bag"):
        item_fields.append("kh_aph_kg_per_bag")
    users = []
    for user in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"},
            fields=["name", "first_name", "last_name"]):
        users.append({**user, "roles": frappe.get_roles(user.name)})
    report = {"site": SITE, "read_only": True, "acceptance": "NOT_TESTED",
        "versions": {a: str(getattr(importlib.import_module(a), "__version__", "unknown")) for a in apps},
        "installed_apps": apps,
        "companies": frappe.get_all("Company", fields=["name", "abbr", "default_currency"]),
        "warehouses": frappe.get_all("Warehouse", fields=["name", "company", "is_group", "disabled", "parent_warehouse"]),
        "stock_items": frappe.get_all("Item", filters={"is_stock_item": 1}, fields=item_fields),
        "users": users, "flags": {f: frappe.conf.get(f) for f in FLAGS},
        "counts": {d: frappe.db.count(d) if frappe.db.exists("DocType", d) else None for d in DOCTYPES},
        "account_candidates": frappe.get_all("Account", filters={"is_group": 0, "disabled": 0,
            "root_type": ["in", ["Asset", "Liability"]]},
            fields=["name", "company", "root_type", "account_type", "account_currency", "account_number"])}
    print(json.dumps(report, ensure_ascii=False, default=str))
finally:
    if getattr(frappe.local, "db", None):
        frappe.db.rollback()
    frappe.destroy()
