"""Tồn kho theo SỐ LƯỢNG (không có giá, giá trị) — cho kế toán nhà máy, nhân viên bán hàng, thủ kho Hà Nội.

Báo cáo gốc có giá trị (Stock Balance, Stock Ledger…) không mở cho vai trò nhà máy.
"""

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Mã hàng"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 170},
        {"label": _("Tên hàng"), "fieldname": "item_name", "fieldtype": "Data", "width": 260},
        {"label": _("Nhóm hàng"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 160},
        {"label": _("Kho"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
        {"label": _("ĐVT"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 70},
        {"label": _("Tồn thực tế"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Đặt mua chưa nhận"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 140},
        {"label": _("Số bao thực tế"), "fieldname": "actual_bags", "fieldtype": "Float", "width": 120},
        {"label": _("Kg chờ định giá (chưa khả dụng)"), "fieldname": "pending_kg", "fieldtype": "Float", "width": 170},
    ]


def get_data(filters):
    # Query Builder does not apply user permissions automatically.
    warehouses = frappe.get_list("Warehouse", pluck="name", limit_page_length=0)
    items = frappe.get_list("Item", pluck="name", limit_page_length=0)
    if not warehouses or not items:
        return []
    b = frappe.qb.DocType("Bin")
    i = frappe.qb.DocType("Item")
    w = frappe.qb.DocType("Warehouse")

    q = (
        frappe.qb.from_(b)
        .join(i)
        .on(i.name == b.item_code)
        .join(w)
        .on(w.name == b.warehouse)
        .select(b.item_code, i.item_name, i.item_group, b.warehouse, b.stock_uom, b.actual_qty, b.ordered_qty)
        .orderby(i.item_group)
        .orderby(b.item_code)
        .orderby(b.warehouse)
    )

    q = q.where(w.name.isin(warehouses)).where(i.name.isin(items))

    if filters.company:
        q = q.where(w.company == filters.company)
    if filters.warehouse:
        lft, rgt = frappe.db.get_value("Warehouse", filters.warehouse, ["lft", "rgt"])
        q = q.where((w.lft >= lft) & (w.rgt <= rgt))
    if filters.item_group:
        groups = [filters.item_group, *(frappe.db.get_descendants("Item Group", filters.item_group) or [])]
        q = q.where(i.item_group.isin(groups))
    if filters.item_code:
        q = q.where(b.item_code == filters.item_code)
    if not filters.show_zero:
        q = q.where((b.actual_qty != 0) | (b.ordered_qty != 0))

    rows = q.run(as_dict=True)
    from kh_aph.bag_stock import enabled, balance
    if not enabled():
        return rows
    indexed = {(r.item_code, r.warehouse): r for r in rows}
    for row in rows:
        row.actual_bags = balance(row.item_code, row.warehouse)
        row.pending_kg = 0
    if frappe.has_permission("APH Pending Receipt", "read"):
        pending = frappe.get_list("APH Pending Receipt", filters={"docstatus": 1,
            "status": "Chờ định giá"}, pluck="name", limit_page_length=0)
        for name in pending:
            doc = frappe.get_doc("APH Pending Receipt", name)
            for line in doc.items:
                if line.warehouse not in warehouses or line.item_code not in items:
                    continue
                if filters.company and doc.company != filters.company:
                    continue
                if filters.item_code and line.item_code != filters.item_code:
                    continue
                item = frappe.get_cached_doc("Item", line.item_code)
                if filters.item_group and item.item_group not in groups:
                    continue
                if filters.warehouse:
                    bounds = frappe.db.get_value("Warehouse", line.warehouse, ["lft", "rgt"])
                    if not (lft <= bounds[0] and bounds[1] <= rgt):
                        continue
                key = (line.item_code, line.warehouse)
                if key not in indexed:
                    row = frappe._dict(item_code=line.item_code, warehouse=line.warehouse,
                        item_name=item.item_name, item_group=item.item_group, stock_uom="Kg",
                        actual_qty=0, ordered_qty=0, actual_bags=0, pending_kg=0)
                    rows.append(row)
                    indexed[key] = row
                indexed[key].pending_kg += line.qty
    return rows
