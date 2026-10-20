"""Locked and idempotent conversion into a native valued Purchase Receipt."""
import frappe
from frappe.utils import flt, today, now_datetime
from kh_aph.quantity_rules import number
from kh_aph.bag_stock import enabled
from kh_aph.cash_transaction import retry_rpc


@frappe.whitelist(methods=["POST"])
@retry_rpc
def finalize(name, rates, reason):
    if not enabled():
        frappe.throw("Chưa bật nhập chờ định giá")
    if frappe.session.user != "Administrator" and "Accounts Manager" not in frappe.get_roles():
        frappe.throw("Kế toán trưởng mới được chốt giá", frappe.PermissionError)
    from kh_aph.price_visibility import is_cost_restricted
    if is_cost_restricted():
        frappe.throw("Hồ sơ không xem giá vốn không được chốt giá nhập", frappe.PermissionError)
    doc = frappe.get_doc("APH Pending Receipt", name)
    doc.check_permission("write")
    order = doc.get('kh_aph_receiving_purchase_order')
    if order:
        from kh_aph import factory_receiving as receiving
        from kh_aph.pending_order import lock_orders
        receiving.guard()
        lock_orders(doc.company, [order])
    doc = frappe.get_doc("APH Pending Receipt", name, for_update=True)
    doc.check_permission("write")
    if doc.docstatus != 1:
        frappe.throw("Cần xác nhận phiếu nhận hàng trước khi định giá")
    if doc.purchase_receipt:
        receipt = frappe.get_doc("Purchase Receipt", doc.purchase_receipt)
        receipt.check_permission("read")
        if receipt.docstatus != 1:
            frappe.throw("Phiếu nhập liên kết đã thay đổi; cần đối soát")
        return receipt.name
    rates = frappe.parse_json(rates)
    if not isinstance(rates, dict) or set(rates) != {r.name for r in doc.items} or not str(reason or "").strip():
        frappe.throw("Cần giá/kg cho đúng từng dòng và lý do chốt giá")
    co = frappe.get_doc("Company", doc.company)
    rows = []
    for row in doc.items:
        try:
            rate = number(rates[row.name])
            if rate <= 0:
                raise ValueError("Giá/kg phải lớn hơn 0; không nhập giá 0")
        except ValueError as exc:
            frappe.throw(str(exc))
        rows.append({"item_code": row.item_code, "warehouse": row.warehouse,
            "qty": row.qty, "rate": float(rate), "uom": "Kg", "conversion_factor": 1,
            "kh_aph_bags": row.kh_aph_bags, "kh_aph_kg_per_bag": row.kh_aph_kg_per_bag,
            "cost_center": co.cost_center})
    receipt = frappe.get_doc({"doctype": "Purchase Receipt", "company": doc.company,
        "supplier": doc.supplier, "posting_date": today(), "currency": "VND", "conversion_rate": 1,
        "kh_aph_pending_receipt": doc.name, "items": rows})
    token = None
    receiving_token = None
    if order:
        from kh_aph import factory_receiving as receiving
        from kh_aph.pending_order import FINALIZING, pending_transition, ROW_FIELD
        from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
        source = receiving._source(order, lock=True)
        pending_transition(doc)
        selected = {r.get(ROW_FIELD): r for r in doc.items}
        if len(selected) != len(doc.items):
            frappe.throw('Mỗi dòng chờ giá phải giữ đúng một dòng đơn mua')
        for source_row, row in selected.items():
            original = next((r for r in source.items if r.name == source_row), None)
            if not original or number(original.rate) != number(rates[row.name]):
                frappe.throw('Cập nhật giá trên đơn mua bằng thao tác chuẩn trước, rồi chốt đúng giá hiện hành')
            receiving._item(original)
        receipt = make_purchase_receipt(order, args={'filtered_children': list(selected)})
        if {r.purchase_order_item for r in receipt.items} != set(selected):
            frappe.throw('Nguồn đơn mua đã đổi; đối chiếu phiếu chờ trước khi chốt giá')
        for row in receipt.items:
            pending_row = selected[row.purchase_order_item]
            row.qty = row.received_qty = pending_row.qty
            row.rejected_qty = 0
            row.warehouse = pending_row.warehouse
            row.kh_aph_bags = pending_row.kh_aph_bags
            row.kh_aph_receiving_quality_qty = pending_row.get('kh_aph_receiving_quality_qty') or 0
        receipt.posting_date = today()
        receipt.set_posting_time = 1
        receipt.kh_aph_pending_receipt = doc.name
        receipt.kh_aph_gia_tam = source.get('kh_aph_gia_tam')
        for field in receiving.STAMP:
            receipt.set(receiving.PREFIX+field, doc.get(receiving.PREFIX+field))
        token = FINALIZING.set(doc.name)
        receiving_token = receiving._INTERNAL.set((frappe.session.user,
            receipt.get(receiving.PREFIX+'request'), receipt.get(receiving.PREFIX+'payload')))
    previous_internal = frappe.flags.pending_internal_process
    frappe.flags.pending_internal_process = True
    try:
        receipt.insert()
        receipt.submit()
    finally:
        frappe.flags.pending_internal_process = previous_internal
        if order:
            receiving._INTERNAL.reset(receiving_token)
            FINALIZING.reset(token)
    doc.db_set({"purchase_receipt": receipt.name, "status": "Đã định giá",
        "valued_by": frappe.session.user, "valued_at": now_datetime(), "valuation_reason": reason},
        update_modified=True)
    return receipt.name


def validate_link(doc, method=None):
    if enabled() and doc.get("kh_aph_pending_receipt") and not frappe.flags.pending_internal_process:
        frappe.throw("Phiếu chờ định giá phải được chốt qua thao tác định giá; không gán liên kết tay")
