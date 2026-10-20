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
         "kh_aph_factory_costing", "kh_aph_factory_cash", "kh_aph_sales_adjust", "kh_aph_data_review",
         "kh_aph_kho_chuan", "kh_aph_sales_p1", "kh_aph_quan_tri",
         "kh_aph_du_lieu", "kh_aph_dau_ky", "kh_aph_kho_van_hanh", "kh_aph_gia_san",
         "kh_aph_trung_tam_ban", "kh_aph_tien_vay", "kh_aph_cash_custody", "kh_aph_cash_closing", "kh_aph_cash_handover", "kh_aph_factory_handover", "kh_aph_factory_receiving", "kh_aph_factory_production")
DEM = ("User", "Company", "Account", "Warehouse", "Item Group", "Customer", "Supplier", "Item", "Item Price",
       "Sales Order", "Delivery Note", "Sales Invoice", "Purchase Order", "Purchase Receipt", "Purchase Invoice",
       "Payment Entry", "Journal Entry", "Stock Entry", "Stock Reconciliation", "Landed Cost Voucher",
       "GL Entry", "Stock Ledger Entry", "Payment Ledger Entry", "Bin", "BOM", "Work Order", "File",
       "APH Shared Sales Order", "APH Pending Receipt", "APH Bag Movement", "APH Credit Release",
       "APH Funds Route", "APH Funds Receipt", "APH Funds Action", "APH Source Change", "APH Hoa don ngoai")
# Giá trị các trang Settings (tabSingles), bỏ trường mật khẩu/tệp và trường hệ thống. So riêng bằng --phan cai_dat.
SETTINGS = ("Stock Settings", "Accounts Settings", "Selling Settings", "Buying Settings", "Manufacturing Settings",
            "System Settings", "Print Settings")
BO_TRUONG = {"modified", "creation", "modified_by", "owner", "name", "idx", "docstatus"}
# 0.11.2: Property Setter do người dùng chỉnh cột danh sách trên giao diện (List View Settings / Customize Form) không
# phải schema của app; tách sang phần "giao_dien" để so production với CI chỉ báo lệch thật (docs/dac-ta-0.11.2.md mục 7).
PS_GIAO_DIEN = ("in_list_view", "columns", "in_preview")
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
        if r.property in PS_GIAO_DIEN:
            continue
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


def _giao_dien():
    return {f"{r.doc_type}|{r.field_name or ''}|{r.property}": r.value
            for r in frappe.get_all("Property Setter", filters={"property": ["in", PS_GIAO_DIEN]},
                                    fields=["doc_type", "field_name", "property", "value"])}


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


def _chi_tiet():
    """Sổ chi tiết theo nhóm (0.14.3): tổng khớp chưa đủ, phải khớp từng công ty / tài khoản / đối tượng, mã hàng / kho, số bao."""
    q = frappe.db.sql
    ct = {}
    ct["gl"] = {f"{r[0]}|{r[1]}|{r[2] or ''}|{r[3] or ''}": [int(r[4]), _so(r[5]), _so(r[6])] for r in q(
        "select company, account, party_type, party, count(*), sum(debit), sum(credit) from `tabGL Entry` "
        "where is_cancelled=0 group by company, account, party_type, party")}
    ct["sle"] = {f"{r[0]}|{r[1]}": [int(r[2]), _so(r[3]), _so(r[4])] for r in q(
        "select item_code, warehouse, count(*), sum(actual_qty), sum(stock_value_difference) from `tabStock Ledger Entry` "
        "where is_cancelled=0 group by item_code, warehouse")}
    ct["bin"] = {f"{r[0]}|{r[1]}": [_so(r[2]), _so(r[3])] for r in q(
        "select item_code, warehouse, sum(actual_qty), sum(stock_value) from `tabBin` group by item_code, warehouse")}
    ct["ple"] = {f"{r[0]}|{r[1]}|{r[2] or ''}|{r[3] or ''}": [int(r[4]), _so(r[5])] for r in q(
        "select company, account, party_type, party, count(*), sum(amount) from `tabPayment Ledger Entry` "
        "where delinked=0 group by company, account, party_type, party")}
    ct["chung_tu"] = {f"{r[0]}|{r[1]}": [int(r[2]), _so(r[3])] for r in q(
        "select voucher_type, company, count(distinct voucher_no), sum(debit) from `tabGL Entry` "
        "where is_cancelled=0 group by voucher_type, company")}
    if frappe.db.exists("DocType", "APH Bag Movement"):
        ct["bao"] = {f"{r[0]}|{r[1]}": [int(r[2]), _so(r[3]), _so(r[4])] for r in q(
            "select item_code, warehouse, count(*), sum(bags), sum(kg) from `tabAPH Bag Movement` "
            "where ifnull(inactive, 0)=0 group by item_code, warehouse")}
    return ct


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
        "chi_tiet": _chi_tiet(),
        "schema": _schema(),
        "cai_dat": _cai_dat(),
        "giao_dien": _giao_dien(),
    }
    print("DAU_VAN " + json.dumps(kq, ensure_ascii=False, default=str))
finally:
    if getattr(frappe.local, "db", None):
        frappe.db.rollback()
    frappe.destroy()
