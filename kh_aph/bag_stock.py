"""Opt-in physical bag ledger, atomic with native stock vouchers."""
import frappe
from frappe.utils import cint, flt
from kh_aph.quantity_rules import bag_conversion
FLAG = "kh_aph_quantity_valuation_mvp"


def enabled():
    return cint(frappe.conf.get(FLAG))


def validate(doc, method=None):
    if not enabled():
        return
    for row in doc.get("items") or []:
        if not row.get("item_code"):
            continue  # dòng không mã hàng (hóa đơn đầu kỳ của Opening Invoice Creation Tool, dòng dịch vụ tự do)
        item = frappe.get_cached_doc("Item", row.item_code)
        weight = flt(item.get("kh_aph_kg_per_bag"))
        if not weight:
            continue
        if item.stock_uom != "Kg":
            frappe.throw("Mã quản lý bao phải có đơn vị tồn kho Kg")
        if doc.doctype == "Stock Reconciliation":
            frappe.throw("Mã quản lý bao: điều chỉnh bằng phiếu kho có số bao")
        if doc.doctype in ("Sales Invoice", "Purchase Invoice") and not doc.get("update_stock"):
            continue
        # Mapping and amendment preserve the original package snapshot.
        saved = weight
        if row.name and frappe.db.exists(row.doctype, row.name):
            saved = flt(frappe.db.get_value(row.doctype, row.name, "kh_aph_kg_per_bag")) or weight
        for field, dt in (("so_detail", "Sales Order Item"), ("sales_order_item", "Sales Order Item"),
                          ("purchase_receipt_item", "Purchase Receipt Item"), ("dn_detail", "Delivery Note Item")):
            if row.get(field):
                source = frappe.db.get_value(dt, row.get(field), ["item_code", "kh_aph_kg_per_bag"], as_dict=True)
                if not source or source.item_code != row.item_code:
                    frappe.throw("Dòng chứng từ gốc không đúng mã hàng: " + row.item_code)
                saved = flt(source.kh_aph_kg_per_bag) or saved
        try:
            result = bag_conversion(row.get("kh_aph_bags"), saved,
                row.get("rate") if doc.doctype in ("Sales Order", "APH Shared Sales Order") else None)
        except ValueError as exc:
            frappe.throw(str(exc) + ": " + row.item_code)
        if row.get("uom") not in (None, "", "Kg"):
            frappe.throw("Phiếu bao dùng Kg; số bao và kg/bao có cột riêng")
        if abs(flt(row.qty) - float(result["qty"])) > 0.000001:
            frappe.throw("Số kg không khớp số bao × kg/bao: " + row.item_code)
        row.kh_aph_kg_per_bag = saved
        row.kh_aph_bag_rate = float(result.get("rate_per_bag", 0))


def validate_item(doc, method=None):
    if enabled() and doc.get("kh_aph_kg_per_bag"):
        if flt(doc.kh_aph_kg_per_bag) <= 0 or doc.stock_uom != "Kg" or not doc.is_stock_item:
            frappe.throw("Quy cách bao cần kg/bao dương và hàng tồn kho Kg")
    if enabled() and not doc.is_new():
        old = doc.get_doc_before_save()
        if old and flt(old.get("kh_aph_kg_per_bag")) != flt(doc.get("kh_aph_kg_per_bag")):
            if (frappe.db.exists("APH Bag Movement", {"item_code": doc.name, "inactive": 0}) or
                    frappe.db.exists("APH Pending Receipt Item", {"item_code": doc.name, "docstatus": ["!=", 2]})):
                frappe.throw("Mã đã có sổ bao: không đổi/xóa quy cách; dùng mã quy cách khác")


def validate_valued_receipt(doc, method=None):
    if not enabled():
        return
    if doc.doctype == "Stock Entry" and doc.get("kh_aph_loss_type") == "Hao hụt bất thường":
        if not doc.get("kh_aph_loss_reason") or doc.purpose != "Material Issue":
            frappe.throw("Hao hụt bất thường: dùng phiếu xuất chi phí riêng và lưu lý do")
        for row in doc.get("items") or []:
            account = frappe.db.get_value("Account", row.get("expense_account"),
                ["root_type", "company", "is_group"], as_dict=True) if row.get("expense_account") else None
            if not account or account.root_type != "Expense" or account.company != doc.company or account.is_group:
                frappe.throw("Hao hụt bất thường cần tài khoản chi phí chi tiết đúng Company")
    if doc.doctype == "Purchase Invoice" and not doc.get("update_stock"):
        return
    for row in doc.get("items") or []:
        item = frappe.get_cached_doc("Item", row.item_code)
        if not item.is_stock_item or item.stock_uom != "Kg":
            continue
        incoming = row.get("t_warehouse") and not row.get("s_warehouse") if doc.doctype == "Stock Entry" else not doc.get("is_return")
        rate = row.get("valuation_rate") if doc.doctype == "Stock Entry" else row.get("rate")
        if incoming and flt(rate) <= 0:
            frappe.throw("Hàng chưa chốt giá: dùng phiếu chờ định giá, không nhập tồn giá 0")


def balance(item, warehouse):
    return flt(frappe.db.sql("""SELECT COALESCE(SUM(bags),0) FROM `tabAPH Bag Movement`
        WHERE item_code=%s AND warehouse=%s AND inactive=0""", (item, warehouse))[0][0])


def _moves(doc):
    if doc.doctype in ("Sales Invoice", "Purchase Invoice") and not doc.get("update_stock"):
        return []
    moves = []
    for row in doc.items:
        bags = flt(row.get("kh_aph_bags"))
        if not bags:
            continue
        if doc.doctype == "Stock Entry":
            for field, sign in (("s_warehouse", -1), ("t_warehouse", 1)):
                if row.get(field):
                    moves.append((row, row.get(field), sign * bags))
        else:
            sign = -1 if doc.doctype in ("Delivery Note", "Sales Invoice") else 1
            moves.append((row, row.warehouse, sign * bags))
    return moves


def post(doc, method=None):
    if not enabled():
        return
    for row, warehouse, bags in _moves(doc):
        # Native stock creates/locks Bin before on_submit; share that lock.
        frappe.db.sql("SELECT name FROM `tabBin` WHERE item_code=%s AND warehouse=%s FOR UPDATE",
                      (row.item_code, warehouse))
        key = {"voucher_type": doc.doctype, "voucher_no": doc.name,
               "voucher_detail": row.name, "warehouse": warehouse}
        if frappe.db.exists("APH Bag Movement", key):
            frappe.throw("Sổ bao đã có dòng; không ghi trùng")
        if balance(row.item_code, warehouse) + bags < -0.000001:
            frappe.throw("Không đủ số bao thực tế: " + row.item_code)
        movement = frappe.get_doc({"doctype": "APH Bag Movement", **key,
            "company": doc.company, "item_code": row.item_code, "bags": bags,
            "kg": bags * flt(row.kh_aph_kg_per_bag), "kg_per_bag": row.kh_aph_kg_per_bag,
            "posting_date": doc.posting_date, "inactive": 0})
        frappe.flags.bag_internal_process = True
        try:
            movement.insert(ignore_permissions=True)
        finally:
            frappe.flags.bag_internal_process = False


def reverse(doc, method=None):
    if not enabled():
        return
    rows = frappe.get_all("APH Bag Movement", filters={"voucher_type": doc.doctype,
        "voucher_no": doc.name, "inactive": 0}, fields=["name", "item_code", "warehouse"])
    for row in rows:
        frappe.db.sql("SELECT name FROM `tabBin` WHERE item_code=%s AND warehouse=%s FOR UPDATE",
                      (row.item_code, row.warehouse))
    for row in rows:
        frappe.db.set_value("APH Bag Movement", row.name, "inactive", 1)
    for row in rows:
        if balance(row.item_code, row.warehouse) < -0.000001:
            frappe.throw("Không thể hủy: số bao đã được dùng ở phiếu sau")


def protect(doc, method=None):
    if not frappe.flags.bag_internal_process:
        frappe.throw("Sổ bao chỉ được ghi qua chứng từ kho")


def boot_session(bootinfo):
    bootinfo.setdefault("kh_aph", {})["quantity_valuation_mvp"] = enabled()
    bootinfo.kh_aph["funds_workflow"] = cint(frappe.conf.get("kh_aph_funds_workflow"))
    bootinfo.kh_aph["source_change"] = cint(frappe.conf.get("kh_aph_source_change"))
    for _co in ("factory_costing", "factory_cash", "sales_adjust", "data_review", "kho_chuan", "sales_p1", "quan_tri", "du_lieu", "dau_ky", "kho_van_hanh", "gia_san"):  # 0.11.1–0.13
        bootinfo.kh_aph[_co] = cint(frappe.conf.get("kh_aph_" + _co))

