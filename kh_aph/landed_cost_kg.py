"""Allocate trip expenses by receipt stock kg, using native LCV reposting."""
import frappe
from frappe.utils import flt
from kh_aph.quantity_rules import weighted_cost
from kh_aph.bag_stock import enabled


class LandedCostKg:
    def set_applicable_charges_on_item(self):
        if not enabled() or not self.get("kh_aph_by_kg"):
            return super().set_applicable_charges_on_item()
        if self.distribute_charges_based_on != "Distribute Manually":
            frappe.throw("Phân bổ kg dùng chế độ Distribute Manually của ERPNext")
        weights = []
        for row in self.items:
            if row.receipt_document_type not in ("Purchase Receipt", "Purchase Invoice"):
                frappe.throw("Chi phí chuyến theo kg: dùng phiếu nhập mua đã ghi sổ")
            detail = frappe.get_doc(row.receipt_document_type + " Item", row.purchase_receipt_item)
            if detail.parent != row.receipt_document or detail.item_code != row.item_code:
                frappe.throw("Dòng chi phí không khớp dòng nhập")
            if detail.stock_uom != "Kg" or flt(detail.stock_qty) <= 0:
                frappe.throw("Phân bổ chi phí cần số kg nhập dương")
            weights.append(detail.stock_qty)
        try:
            charges = weighted_cost(self.total_taxes_and_charges, weights)
        except ValueError as exc:
            frappe.throw(str(exc))
        for row, charge in zip(self.items, charges, strict=True):
            row.applicable_charges = float(charge)
