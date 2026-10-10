"""Process-local candidate test, hard pinned to aphvh-uat. Never installs app files."""
import hashlib
import importlib.util
import json
import os
import sys
import traceback
import types
import uuid

import frappe
from frappe.utils import add_days, flt, today

SITE = "aphvh-uat"
SITES = "/home/frappe/frappe-bench/sites"
TRACKED = ["User", "Customer", "Item", "Item Group", "Item Tax Template", "Warehouse", "Bin",
           "Sales Order", "Delivery Note", "Sales Invoice", "Stock Entry", "GL Entry",
           "Stock Ledger Entry", "Property Setter", "Custom DocPerm", "Payment Ledger Entry"]
results = []
affected = set()
original_commit = None


def record(case, status, detail):
    results.append({"case": case, "status": status, "detail": detail})
    print(json.dumps(results[-1], ensure_ascii=False, default=str), flush=True)


def test(case, fn):
    frappe.db.savepoint("p0_case")
    try:
        detail = fn()
        record(case, "PASS", detail)
    except AssertionError as exc:
        frappe.db.rollback(save_point="p0_case")
        record(case, "FAIL", str(exc))
    except Exception as exc:
        frappe.db.rollback(save_point="p0_case")
        record(case, "BLOCKED", {"type": type(exc).__name__, "error": str(exc)[:1200]})


try:
    os.chdir(SITES)
    frappe.init(site=SITE, sites_path=SITES)
    if frappe.local.site != SITE:
        raise RuntimeError("UAT site mismatch")
    frappe.connect()
    frappe.set_user("Administrator")
    before = {dt: frappe.db.count(dt) for dt in TRACKED}
    before_series = frappe.db.sql("SELECT name,current FROM `tabSeries` ORDER BY name")
    original_commit = frappe.db.commit
    def no_commit(*args, **kwargs):
        raise RuntimeError("Runner forbids commit: all candidate data must roll back")
    frappe.db.commit = no_commit
    frappe.flags.in_test = True
    frappe.conf.mute_emails = True
    frappe.conf.kh_aph_server_cost_guard = 1
    frappe.conf.kh_aph_post_receivable_on_delivery = 1

    # PATCH_SOURCES is embedded in the generated standalone file. No disk app replacement.
    import kh_aph
    for name, source in PATCH_SOURCES.items():
        candidate = types.ModuleType(name)
        candidate.__file__ = "<candidate:" + name + ">"
        candidate.__package__ = "kh_aph"
        sys.modules[name] = candidate
        setattr(kh_aph, name.rsplit(".", 1)[1], candidate)
        exec(compile(source, candidate.__file__, "exec"), candidate.__dict__)

    from kh_aph.server_cost_guard import CostReadGuard, apply_query_field_permissions
    from kh_aph.constants import INV_FLAG, INV_NO, ROLE_FACTORY
    changed = apply_query_field_permissions()
    record("SETUP_COST_FIELDS", "DONE", {"field_count": len(changed)})
    from frappe.model.base_document import get_controller
    # Never cache transaction-local candidate Documents in shared Redis. This also
    # prevents phantom fixture documents surviving SQL rollback. Reads still use
    # native DB/controller behaviour; only document-cache writes are skipped here.
    import frappe.model.document as document_module
    def no_document_cache_write(key, doc):
        return None
    document_module._set_document_in_cache = no_document_cache_write
    frappe._set_document_in_cache = no_document_cache_write
    for dt in ("Stock Entry", "Purchase Receipt", "Purchase Order", "Serial and Batch Bundle",
               "Item", "Sales Order", "Delivery Note"):
        base = get_controller(dt)
        frappe.controllers[SITE][dt] = type("UatCostGuard" + base.__name__, (CostReadGuard, base), {})
        affected.add(dt)

    co = frappe.get_doc("Company", frappe.db.get_value("Company", {"abbr": "APH"}, "name"))
    p = "UAT-P0-" + uuid.uuid4().hex[:8]
    wh = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p, "company": co.name,
                        "is_group": 0, "parent_warehouse": frappe.db.get_value("Warehouse", {
                            "company": co.name, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name"),
                        "account": co.default_inventory_account}).insert().name
    group = frappe.get_doc({"doctype": "Item Group", "item_group_name": p,
                           "parent_item_group": "HH - Hàng hóa", "is_group": 0}).insert().name
    customer = frappe.get_doc({"doctype": "Customer", "customer_name": p, "customer_type": "Company",
                               "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
                               "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
                               INV_FLAG: INV_NO}).insert()
    vat_account = frappe.db.get_value("Account", {"company": co.name, "account_number": "33311", "is_group": 0}, "name")
    tax = frappe.get_doc({"doctype": "Item Tax Template", "title": p + "-TEST10", "company": co.name,
                         "taxes": [{"tax_type": vat_account, "tax_rate": 10}]}).insert()
    item = frappe.get_doc({"doctype": "Item", "item_code": p, "item_name": p, "item_group": group,
                          "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average",
                          "taxes": [{"item_tax_template": tax.name, "tax_category": customer.tax_category}],
                          "item_defaults": [{"company": co.name, "default_warehouse": wh,
                                             "income_account": co.default_income_account,
                                             "expense_account": co.default_expense_account,
                                             "buying_cost_center": co.cost_center,
                                             "selling_cost_center": co.cost_center}]}).insert()
    se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": co.name,
                        "posting_date": today(), "items": [{"item_code": item.name, "qty": 100,
                            "uom": "Kg", "stock_uom": "Kg", "conversion_factor": 1, "t_warehouse": wh,
                            "basic_rate": 10000, "set_basic_rate_manually": 1,
                            "expense_account": co.stock_adjustment_account, "cost_center": co.cost_center}]}).insert()
    se.submit()
    user = frappe.get_doc({"doctype": "User", "email": p.lower() + "@example.invalid", "first_name": p,
                          "enabled": 1, "user_type": "System User", "send_welcome_email": 0,
                          "roles": [{"role": ROLE_FACTORY}]})
    user.flags.no_welcome_mail = True
    user.insert()

    def restricted_document_reads():
        from frappe.client import get
        from frappe.api.v2 import read_doc
        frappe.set_user(user.name)
        try:
            for api in (get, read_doc):
                data = api("Stock Entry", se.name)
                assert data["items"][0]["qty"] == 100, "Quantity must remain visible"
                for row in data["items"]:
                    for field in ("basic_rate", "basic_amount", "valuation_rate", "amount"):
                        assert row.get(field) in (None, "", 0), "Cost exposed: " + field
            return "client.get and api.v2.read_doc masked cost; quantity preserved"
        finally:
            frappe.set_user("Administrator")
    test("P0_COST_DOCUMENT", restricted_document_reads)

    def restricted_child_query():
        from frappe.client import get_list
        frappe.set_user(user.name)
        try:
            try:
                rows = get_list("Stock Entry Detail", parent="Stock Entry",
                                filters={"parent": se.name}, fields=["qty", "basic_rate"])
            except frappe.PermissionError:
                return "Cost query rejected by native field permissions"
            for row in rows:
                assert row.get("basic_rate") in (None, "", 0), "Child query exposed basic_rate"
            return "Child query did not return cost"
        finally:
            frappe.set_user("Administrator")
    test("P0_COST_CHILD_QUERY", restricted_child_query)

    def admin_cost_read():
        from frappe.client import get
        data = get("Stock Entry", se.name)
        assert flt(data["items"][0]["basic_rate"]) == 10000, "Admin lost cost access"
        return "Admin cost remains 10000"
    test("P0_COST_ADMIN", admin_cost_read)

    so = frappe.get_doc({"doctype": "Sales Order", "company": co.name, "customer": customer.name,
                        "transaction_date": today(), "delivery_date": add_days(today(), 1),
                        "selling_price_list": frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name"),
                        "currency": "VND", "conversion_rate": 1, "order_type": "Sales", INV_FLAG: INV_NO,
                        "items": [{"item_code": item.name, "qty": 10, "uom": "Kg", "conversion_factor": 1,
                                   "rate": 20000, "warehouse": wh, "item_tax_template": tax.name,
                                   "delivery_date": add_days(today(), 1)}]}).insert()
    so.submit()
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
    from kh_aph.delivery_receivable import post_receivable
    dn = make_delivery_note(so.name)
    dn.posting_date = today()
    dn.set(INV_FLAG, INV_NO)
    for row in dn.items:
        row.qty = 4
    dn.insert()
    dn.submit()
    def dispatch_debt():
        debt = flt(frappe.db.sql("SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry` "
                                "WHERE party_type='Customer' AND party=%s AND company=%s AND is_cancelled=0",
                                (customer.name, co.name))[0][0])
        qty = flt(frappe.db.get_value("Bin", {"item_code": item.name, "warehouse": wh}, "actual_qty"))
        assert abs(debt-flt(dn.grand_total)) < .01, f"Expected debt {dn.grand_total}; got {debt}"
        assert qty == 96, f"Expected 96 kg; got {qty}"
        return {"expected_debt": dn.grand_total, "actual_debt": debt, "stock_kg": qty}
    test("P0_DISPATCH_DEBT", dispatch_debt)
    def repeat_hook():
        count = frappe.db.count("Sales Invoice")
        post_receivable(frappe.get_doc("Delivery Note", dn.name))
        assert frappe.db.count("Sales Invoice") == count, "Duplicate invoice on repeated hook"
        return "Repeated hook creates no additional SI"
    test("P0_DISPATCH_REPEAT", repeat_hook)

    def posting_failure():
        from unittest.mock import patch
        from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
        fail_dn = make_delivery_note(so.name)
        fail_dn.posting_date = today()
        for row in fail_dn.items:
            row.qty = 1
        fail_dn.insert()
        frappe.db.savepoint("dispatch_failure")
        baseline_qty = flt(frappe.db.get_value("Bin", {"item_code": item.name, "warehouse": wh}, "actual_qty"))
        marker = "UAT intentional SI posting failure"
        try:
            with patch.object(SalesInvoice, "submit", side_effect=RuntimeError(marker)):
                try:
                    fail_dn.submit()
                except RuntimeError as exc:
                    assert marker in str(exc), "Unexpected failure"
                else:
                    raise AssertionError("Dispatch swallowed invoice posting failure")
        finally:
            frappe.db.rollback(save_point="dispatch_failure")
        actual_qty = flt(frappe.db.get_value("Bin", {"item_code": item.name, "warehouse": wh}, "actual_qty"))
        assert actual_qty == baseline_qty, "Failed dispatch changed stock after transaction rollback"
        return "Failure propagated; dispatch stock rolled back"
    test("P0_DISPATCH_FAILURE", posting_failure)

except Exception as exc:
    record("RUNNER", "BLOCKED", {"type": type(exc).__name__, "error": str(exc)[:1600]})
    print(traceback.format_exc())
finally:
    if getattr(frappe.local, "db", None):
        frappe.set_user("Administrator")
        frappe.db.rollback()
        if original_commit:
            frappe.db.commit = original_commit
        if "before" in locals():
            after = {dt: frappe.db.count(dt) for dt in TRACKED}
            series_after = frappe.db.sql("SELECT name,current FROM `tabSeries` ORDER BY name")
            record("ROLLBACK_COUNTS_AND_SERIES", "PASS" if before == after and before_series == series_after else "FAIL",
                   {"before": before, "after": after, "series_restored": before_series == series_after})
        frappe.clear_cache()
    frappe.destroy()
    print("Candidate loaded in this process only; no shared app files replaced.")
    if any(row["status"] in ("FAIL", "BLOCKED") for row in results):
        sys.exit(1)
