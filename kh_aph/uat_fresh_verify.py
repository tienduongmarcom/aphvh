"""Run only inside a newly created GitHub Actions UAT site."""
import json
import frappe
from kh_aph.uat_candidate_setup import FIELDS, setup_uat

def verify():
    assert frappe.local.site == "aphvh-web-uat"
    assert frappe.session.user == "Administrator"
    expected = {"APH", "VH", "MK", "TL"}
    assert set(frappe.get_all("Company", pluck="abbr")) == expected
    before = {dt: frappe.db.count(dt) for dt in
              ("Custom Field", "Custom DocPerm", "Property Setter")}
    setup_uat()
    after = {dt: frappe.db.count(dt) for dt in before}
    assert before == after, ("Setup is not idempotent", before, after)
    for dt, fields in FIELDS.items():
        meta = frappe.get_meta(dt)
        for field in fields:
            actual = meta.get_field(field["fieldname"])
            assert actual and actual.fieldtype == field["fieldtype"], (dt, field)
    assert frappe.get_meta("APH Credit Release").has_field("revoked_at")
    from frappe.model.base_document import get_controller
    for dt in ("Item", "Stock Entry", "Sales Order", "Delivery Note"):
        mro = [c.__name__ for c in get_controller(dt).__mro__]
        assert "CostReadGuard" in mro, (dt, mro)
    assert "StockEntryKgCosting" in [c.__name__ for c in get_controller("Stock Entry").__mro__]
    hooks = frappe.get_hooks("doc_events")
    assert "kh_aph.credit_release.before_submit_invoice" in hooks["Sales Invoice"]["before_submit"]
    assert "kh_aph.credit_release.before_submit_delivery" in hooks["Delivery Note"]["before_submit"]
    overrides = frappe.get_hooks("override_whitelisted_methods")
    assert overrides["frappe.client.get_value"][-1] == "kh_aph.cost_query_api.get_value"
    filters = {"parent": "Delivery Note", "role": "Accounts Manager", "permlevel": 0, "if_owner": 0}
    assert frappe.db.get_value("Custom DocPerm", filters, "read") == 1
    blank = {dt: frappe.db.count(dt) for dt in
             ("Customer", "Item", "Sales Order", "Delivery Note", "Sales Invoice",
              "Payment Entry", "Stock Entry", "GL Entry", "Stock Ledger Entry",
              "APH Shared Sales Order", "APH Credit Release")}
    assert not any(blank.values()), blank
    print(json.dumps({"case": "FRESH_IMAGE_SETUP", "status": "PASS",
                      "idempotent": True, "companies": sorted(expected),
                      "blank_counts": blank, "schema_counts": after}, ensure_ascii=False))
