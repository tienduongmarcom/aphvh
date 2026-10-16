"""Ca đặc hiệu nền 16.51.1; chỉ site CI trắng, dữ liệu giả, luôn rollback.

Chạy trong container UAT sau bộ cài, trước các bộ HTTP. Không sửa controller upstream.
"""
import json
import uuid

import frappe
from frappe.utils import add_days, today


def emit(case, detail):
    print(json.dumps({"case": case, "status": "PASS", "detail": detail}, ensure_ascii=False), flush=True)


def rejected(fn, kinds=(frappe.ValidationError,)):
    try:
        fn()
    except kinds:
        return
    raise AssertionError("Native guard không từ chối")


frappe.init(site="aphvh-web-uat", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")
tracked = ("Item", "Item Group", "Warehouse", "Bin", "Stock Entry", "Stock Ledger Entry", "GL Entry",
           "Stock Closing Entry", "Stock Closing Balance")
before = {dt: frappe.db.count(dt) for dt in tracked}
series = frappe.db.sql("SELECT name,current FROM `tabSeries` ORDER BY name")
try:
    assert not before["Item"] and not before["Stock Ledger Entry"], "Chỉ chạy site UAT trắng"
    import erpnext
    assert erpnext.__version__ == "16.51.1", erpnext.__version__
    from erpnext.stock.doctype.stock_closing_entry.stock_closing_entry import prepare_closing_stock_balance
    from erpnext.stock.report.stock_balance.stock_balance import execute

    p = "UAT-16511-" + uuid.uuid4().hex[:8]
    company = frappe.get_doc("Company", frappe.db.get_value("Company", {"abbr": "APH"}, "name"))
    parent = frappe.db.get_value("Warehouse", {"company": company.name, "is_group": 1}, "name")
    wh = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p, "company": company.name,
                        "parent_warehouse": parent, "account": company.default_inventory_account}).insert().name
    other_wh = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p + "-KHAC", "company": company.name,
                              "parent_warehouse": parent, "account": company.default_inventory_account}).insert().name
    group = frappe.get_doc({"doctype": "Item Group", "item_group_name": p, "parent_item_group": "HH - Hàng hóa",
                           "is_group": 0}).insert().name
    codes = []
    for suffix in ("A", "B"):
        codes.append(frappe.get_doc({"doctype": "Item", "item_code": p + suffix, "item_name": p + suffix,
                      "item_group": group, "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average"}).insert().name)
    entry = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": company.name,
                            "posting_date": add_days(today(), -10), "set_posting_time": 1,
                            "items": [{"item_code": codes[0], "qty": 100, "t_warehouse": wh, "basic_rate": 10000},
                                      {"item_code": codes[1], "qty": 200, "t_warehouse": other_wh, "basic_rate": 20000}]})
    entry.insert()
    entry.submit()
    rejected(lambda: frappe.get_doc({"doctype": "Stock Closing Entry", "company": company.name,
                                     "to_date": add_days(today(), 1)}).insert())
    missing = frappe.new_doc("Stock Closing Entry")
    missing.company = None  # Không để user default tự điền công ty và che mất ca thiếu dữ liệu.
    missing.to_date = add_days(today(), -5)
    rejected(missing._validate_mandatory, (frappe.MandatoryError,))
    draft = frappe.get_doc({"doctype": "Stock Closing Entry", "company": company.name,
                            "to_date": add_days(today(), -5)}).insert()
    rejected(draft.enqueue_job)
    prepare_closing_stock_balance(draft.name)
    assert not frappe.db.count("Stock Closing Balance"), "Nháp đã tạo số dư chốt"
    emit("NATIVE_16511_DRAFT_AND_DATE_GUARD", {"future_rejected": True, "company_required": True, "draft_balances": 0})

    draft.submit()
    prepare_closing_stock_balance(draft.name)
    assert frappe.db.get_value("Stock Closing Entry", draft.name, "status") == "Completed"
    filters = frappe._dict(company=company.name, from_date=add_days(today(), -4), to_date=today(),
                           item_code=[codes[0]], warehouse=[wh], show_stock_ageing_data=1)
    data = execute(filters)[1]
    selected = [r for r in data if r.get("item_code")]
    assert len(selected) == 1, selected
    row = selected[0]
    assert row["item_code"] == codes[0] and row["warehouse"] == wh, row
    assert abs(row["bal_qty"] - 100) < 1e-6 and abs(row["bal_val"] - 1000000) < 0.5, row
    assert abs(row["opening_qty"] - 100) < 1e-6 and abs(row["in_qty"]) < 1e-6, row
    without = execute(frappe._dict({**filters, "ignore_closing_balance": 1}))[1]
    baseline = next(r for r in without if r.get("item_code") == codes[0])
    assert abs(baseline["bal_qty"] - row["bal_qty"]) < 1e-6, (baseline, row)
    emit("NATIVE_16511_STOCK_BALANCE_FILTER", {"kg": row["bal_qty"], "value": row["bal_val"], "single_item_warehouse": True})

    later = frappe.get_doc({"doctype": "Stock Closing Entry", "company": company.name,
                            "to_date": add_days(today(), -2)}).insert()
    later.submit()
    prepare_closing_stock_balance(later.name)
    count = frappe.db.count("Stock Closing Balance", {"stock_closing_entry": draft.name})
    rejected(draft.regenerate_closing_balance)
    rejected(draft.cancel)
    assert frappe.db.count("Stock Closing Balance", {"stock_closing_entry": draft.name}) == count
    later.cancel()
    draft.reload()
    draft.cancel()
    prepare_closing_stock_balance(draft.name)
    assert not frappe.db.count("Stock Closing Balance", {"stock_closing_entry": draft.name})
    emit("NATIVE_16511_CANCEL_REGENERATE_GUARD", {"later_blocks_regenerate_cancel": True, "cancelled_balances": 0})
finally:
    frappe.db.rollback()
    after = {dt: frappe.db.count(dt) for dt in tracked}
    assert before == after, (before, after)
    assert series == frappe.db.sql("SELECT name,current FROM `tabSeries` ORDER BY name"), "Series không khôi phục"
    emit("NATIVE_16511_ROLLBACK", {"counts_unchanged": True, "series_unchanged": True})
    frappe.destroy()
