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
    ]


def get_data(filters):
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

    return q.run(as_dict=True)
