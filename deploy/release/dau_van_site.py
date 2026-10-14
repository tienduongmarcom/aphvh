"""Dấu vân một site: số bản ghi, tổng sổ (GL/SLE/Bin/PLE), schema tùy biến, giá trị Settings, cờ tính năng. CHỈ ĐỌC.

Độc lập với app (chạy được trên 0.9.1 lẫn bản mới) để so trước nâng cấp / sau quay lui / site dựng mới.
Chạy bằng python của bench, cwd = frappe-bench/sites, mã qua stdin, tham số là tên site:

    docker exec -i -w /home/frappe/frappe-bench/sites <backend> /home/frappe/frappe-bench/env/bin/python - frontend < dau_van_site.py

Giao dịch READ ONLY rồi rollback. Không in site_config, mật khẩu, khóa. In một dòng JSON.
"""
import hashlib
import importlib
import json
import sys

import frappe

SITE = sys.argv[1] if len(sys.argv) > 1 else "frontend"
FLAGS = ("kh_aph_server_cost_guard", "kh_aph_post_receivable_on_delivery", "kh_aph_shared_sales_order",
         "kh_aph_global_credit_warning", "kh_aph_high_risk_credit_guard", "kh_aph_quantity_valuation_mvp",
         "kh_aph_funds_workflow", "kh_aph_source_change",
         "kh_aph_factory_costing", "kh_aph_factory_cash", "kh_aph_sales_adjust", "kh_aph_data_review")
DEM = ("User", "Company", "Account", "Warehouse", "Item Group", "Customer", "Supplier", "Item", "Item Price",
       "Sales Order", "Delivery Note", "Sales Invoice", "Purchase Order", "Purchase Receipt", "Purchase Invoice",
       "Payment Entry", "Journal Entry", "Stock Entry", "Stock Reconciliation", "Landed Cost Voucher",
       "GL Entry", "Stock Ledger Entry", "Payment Ledger Entry", "Bin", "BOM", "Work Order", "File",
       "APH Shared Sales Order", "APH Pending Receipt", "APH Bag Movement", "APH Credit Release",
       "APH Funds Route", "APH Funds Receipt", "APH Funds Action", "APH Source Change")
# Giá trị các trang Settings (tabSingles), bỏ trường mật khẩu/tệp và trường hệ thống. So riêng bằng --phan cai_dat.
SETTINGS = ("Stock Settings", "Accounts Settings", "Selling Settings", "Buying Settings", "Manufacturing Settings",
            "System Settings", "Print Settings")
BO_TRUONG = {"modified", "creation", "modified_by", "owner", "name", "idx", "docstatus"}
QUYEN = ("read", "write", "create", "submit", "cancel", "amend", "delete", "report", "export", "print",
         "email", "share", "select")


def _so(x):
    return str(round(float(x or 0), 6))


def _schema():
    muc = []
    for r in frappe.get_all("Custom Field", fields=["dt", "fieldname", "fieldtype", "options", "permlevel",
                                                     "insert_after", "read_only", "hidden", "reqd", "allow_on_submit"]):
        muc.append("CF|" + "|".join("" if r[k] is None else str(r[k]) for k in
                                    ("dt", "fieldname", "fieldtype", "options", "permlevel", "insert_after",
                                     "read_only", "hidden", "reqd", "allow_on_submit")))
    for r in frappe.get_all("Property Setter", fields=["doc_type", "field_name", "property", "value"]):
        muc.append(f"PS|{r.doc_type}|{r.field_name or ''}|{r.property}|{r.value}")
    for r in frappe.get_all("Custom DocPerm", fields=["parent", "role", "permlevel", "if_owner", *QUYEN]):
        muc.append("DP|" + "|".join(str(r[k]) for k in ("parent", "role", "permlevel", "if_owner", *QUYEN)))
    for r in frappe.get_all("DocType", filters={"module": ["in", ["Kh Aph", "Lab9X", "Lab9x"]]},
                            fields=["name", "custom", "istable"]):
        muc.append(f"DT|{r.name}|{r.custom}|{r.istable}")
    for r in frappe.get_all("DocType", filters={"custom": 1}, fields=["name", "istable"]):
        muc.append(f"DTC|{r.name}|{r.istable}")
    for r in frappe.get_all("Role", filters={"is_custom": 0}, pluck="name"):
        muc.append(f"RO|{r}")
    muc = sorted(set(muc))
    return {"so_muc": len(muc), "sha256": hashlib.sha256("\n".join(muc).encode()).hexdigest(), "muc": muc}


def _cai_dat():
    out = {}
    for dt in SETTINGS:
        if not frappe.db.exists("DocType", dt):
            continue
        bo = {df.fieldname for df in frappe.get_meta(dt).fields
              if df.fieldtype in ("Password", "Attach", "Attach Image", "Code")}
        for f, v in frappe.db.sql("select field, value from `tabSingles` where doctype=%s", dt):
            if f in bo or f in BO_TRUONG:
                continue
            out[f"{dt}.{f}"] = v
    return out


def _tong():
    q = frappe.db.sql
    t = {}
    gl = q("select count(*), sum(debit), sum(credit) from `tabGL Entry` where is_cancelled=0")[0]
    t["gl"] = [int(gl[0]), _so(gl[1]), _so(gl[2])]
    sle = q("select count(*), sum(actual_qty), sum(stock_value_difference) from `tabStock Ledger Entry` "
            "where is_cancelled=0")[0]
    t["sle"] = [int(sle[0]), _so(sle[1]), _so(sle[2])]
    b = q("select count(*), sum(actual_qty), sum(stock_value) from `tabBin`")[0]
    t["bin"] = [int(b[0]), _so(b[1]), _so(b[2])]
    ple = q("select count(*), sum(amount) from `tabPayment Ledger Entry` where delinked=0")[0]
    t["ple"] = [int(ple[0]), _so(ple[1])]
    return t


frappe.init(site=SITE, sites_path=".")
try:
    frappe.connect()
    frappe.set_user("Administrator")
    frappe.db.rollback()
    frappe.db.sql("START TRANSACTION READ ONLY")
    apps = frappe.get_installed_apps()
    kq = {
        "site": SITE, "read_only": True,
        "versions": {a: str(getattr(importlib.import_module(a), "__version__", "unknown")) for a in apps},
        "co": {f: int(str(frappe.conf.get(f) or 0).strip() or 0) for f in FLAGS},
        "dem": {d: frappe.db.count(d) if frappe.db.exists("DocType", d) else None for d in DEM},
        "tong": _tong(),
        "schema": _schema(),
        "cai_dat": _cai_dat(),
    }
    print("DAU_VAN " + json.dumps(kq, ensure_ascii=False, default=str))
finally:
    if getattr(frappe.local, "db", None):
        frappe.db.rollback()
    frappe.destroy()
