"""Gợi ý gom hàng theo lượng đơn chưa lập phiếu; chuyển thực tế dùng Stock Entry chuẩn."""
import frappe
from frappe.utils import cint
from kh_aph.quantity_rules import number


@frappe.whitelist()
def preview(shared_order):
    from kh_aph import factory_transfer as transfer
    from kh_aph.ban_nhanh import _order, _rows
    transfer.guard()
    if not cint(frappe.conf.get('kh_aph_shared_sales_order')):
        frappe.throw('Chưa bật đơn bán chung')
    if not frappe.has_permission('Stock Entry', 'create'):
        frappe.throw('Cần quyền chuẩn bị phiếu chuyển kho', frappe.PermissionError)
    order = _order(shared_order)
    groups = {}
    for row in _rows(order):
        qty = number(row['remaining_qty'])
        if qty <= 0:
            continue
        key = (row['company'], row['warehouse'])
        group = groups.setdefault(key, {})
        item = group.setdefault(row['item_code'], {'item_code': row['item_code'],
            'item_name': row['item_name'], 'qty': number(0), 'kg_per_bag': number(row['kg_per_bag'])})
        if item['kg_per_bag'] != number(row['kg_per_bag']):
            frappe.throw('Quy cách cùng mã trên đơn khác nhau; đối chiếu trước khi gom')
        item['qty'] += qty
    if len(groups) > 100 or any(len(items) > 100 for items in groups.values()):
        frappe.throw('Đơn vượt100nhóm hoặc100mã một nhóm; dùng phiếu chuyển kho chuẩn')
    result = []
    for (company, destination), items in sorted(groups.items()):
        transfer._destination(destination, company, None)
        values = []
        for item in items.values():
            weight = item['kg_per_bag']
            bags = item['qty'] / weight if weight > 0 else number(0)
            values.append({**item, 'qty': float(item['qty']), 'kg_per_bag': float(weight),
                'bags': int(bags) if bags == bags.to_integral_value() else 0})
        result.append({'company': company, 'destination': destination, 'items': values})
    return {'shared_order': order.name, 'groups': result}
