"""Chia giá thành phẩm theo kg cho phiếu kho loại "Đóng gói theo kg".

Gắn vào ERPNext qua hook `extend_doctype_class` (Frappe v16): lớp dưới đây đứng TRƯỚC
lớp StockEntry chuẩn trong MRO, nên chỉ can thiệp đúng hai điểm và gọi super() cho phần
còn lại.

1. `validate_repack_entry`: ERPNext chuẩn bắt phiếu Repack có nhiều thành phẩm phải nhập
   giá tay. Với loại phiếu "Đóng gói theo kg", app thay kiểm tra đó bằng kiểm tra riêng,
   đồng thời LƯU lên phiếu mã quy tắc (kg-v1) và số kg của từng dòng.
2. `set_basic_rate`: sau khi ERPNext tính giá đầu vào, app chia tổng giá đầu vào cho các
   dòng thành phẩm theo số kg đã lưu. Các bước sau (chi phí cộng thêm, giá tồn kho, tổng
   phiếu) do ERPNext tính tiếp như bình thường.

Khi tính lại giá (repost), ERPNext nạp lại phiếu qua cùng lớp đã mở rộng và gọi
`calculate_rate_and_amount` → `set_basic_rate`, nên giá thành phẩm tự cập nhật. Repost
KHÔNG gọi validate, vì vậy nó dùng mã quy tắc và số kg đã lưu trên phiếu, không đọc lại
trọng lượng hiện tại trên mã hàng.
"""

import frappe
from frappe import _
from frappe.utils import flt

from aphvh.constants import KG_ENTRY_TYPE, KG_UOM, RULE_KG_V1
from aphvh.costing_rules import split_by_weight


class StockEntryKgCosting:
    """Lớp mở rộng cho DocType Stock Entry (khai báo trong hooks.extend_doctype_class)."""

    def validate_repack_entry(self):
        if self.purpose == "Repack" and self.stock_entry_type == KG_ENTRY_TYPE:
            self.aphvh_costing_rule = RULE_KG_V1
            snapshot_kg(self)
            validate_kg_entry(self)
            return

        # Phiếu không thuộc loại "Đóng gói theo kg": giữ nguyên hành vi chuẩn của ERPNext.
        if self.get("aphvh_costing_rule"):
            self.aphvh_costing_rule = None
        return super().validate_repack_entry()

    def set_basic_rate(self, reset_outgoing_rate=True, raise_error_if_no_rate=True):
        super().set_basic_rate(reset_outgoing_rate, raise_error_if_no_rate)
        if uses_kg_rule(self):
            allocate_finished_cost_by_kg(self)


def uses_kg_rule(doc):
    """Phiếu có dùng quy tắc chia theo kg không — đọc mã quy tắc ĐÃ LƯU trên phiếu."""
    return doc.purpose == "Repack" and doc.get("aphvh_costing_rule") == RULE_KG_V1


def finished_rows(doc):
    return [d for d in doc.get("items") if d.is_finished_item and d.t_warehouse and not d.s_warehouse]


def input_rows(doc):
    return [d for d in doc.get("items") if d.s_warehouse and not d.t_warehouse]


def kg_per_stock_uom(item_code, stock_uom):
    """Số kg của 1 đơn vị tồn kho. Trả 0 nếu mã hàng chưa khai báo trọng lượng."""
    if (stock_uom or "").strip().lower() == KG_UOM.lower():
        return 1.0

    weight, weight_uom = frappe.get_cached_value("Item", item_code, ["weight_per_unit", "weight_uom"])
    weight = flt(weight)
    if not weight or not weight_uom:
        return 0.0
    if weight_uom.strip().lower() == KG_UOM.lower():
        return weight

    factor = uom_factor_to_kg(weight_uom)
    return weight * factor if factor else 0.0


def uom_factor_to_kg(uom):
    """Hệ số quy 1 `uom` ra Kg, lấy từ bảng UOM Conversion Factor chuẩn của ERPNext."""
    value = frappe.db.get_value("UOM Conversion Factor", {"from_uom": uom, "to_uom": KG_UOM}, "value")
    if flt(value):
        return flt(value)
    value = frappe.db.get_value("UOM Conversion Factor", {"from_uom": KG_UOM, "to_uom": uom}, "value")
    return 1.0 / flt(value) if flt(value) else 0.0


def snapshot_kg(doc):
    """Lưu hệ số kg/ĐVT tồn kho và số kg lên từng dòng (chỉ chạy lúc lưu/gửi phiếu)."""
    for d in doc.get("items"):
        factor = kg_per_stock_uom(d.item_code, d.stock_uom)
        d.aphvh_kg_per_unit = factor
        d.aphvh_kg = flt(flt(d.transfer_qty) * factor, 6)


def validate_kg_entry(doc):
    """Kiểm tra phiếu "Đóng gói theo kg" (bản 0.1: một quy tắc duy nhất, chia hết theo kg)."""
    if not input_rows(doc):
        frappe.throw(
            _("Phiếu {0} cần ít nhất một dòng đầu vào (có Kho nguồn, không có Kho đích).").format(
                KG_ENTRY_TYPE
            ),
            title=_("Thiếu đầu vào"),
        )

    mixed = [d.idx for d in doc.get("items") if d.s_warehouse and d.t_warehouse]
    if mixed:
        frappe.throw(
            _("Dòng {0}: phiếu {1} không dùng dòng vừa có Kho nguồn vừa có Kho đích.").format(
                ", ".join(str(i) for i in mixed), KG_ENTRY_TYPE
            ),
            title=_("Dòng không hợp lệ"),
        )

    secondary = [d.idx for d in doc.get("items") if d.get("secondary_item_type") or d.get("valuation_type")]
    if secondary:
        frappe.throw(
            _("Dòng {0}: bản hiện tại chưa hỗ trợ phụ phẩm định giá riêng trên phiếu {1}.").format(
                ", ".join(str(i) for i in secondary), KG_ENTRY_TYPE
            ),
            title=_("Chưa hỗ trợ"),
        )

    if doc.get("additional_costs"):
        frappe.throw(
            _("Bản hiện tại chưa hỗ trợ chi phí cộng thêm trên phiếu {0}.").format(KG_ENTRY_TYPE),
            title=_("Chưa hỗ trợ"),
        )

    missing = [d for d in finished_rows(doc) if flt(d.aphvh_kg) <= 0]
    if missing:
        items = ", ".join(sorted({d.item_code for d in missing}))
        frappe.throw(
            _(
                "Chưa tính được số kg cho thành phẩm: {0}. Với mã không tính tồn kho bằng {1}, "
                "khai báo Trọng lượng/đơn vị và Đơn vị trọng lượng = {1} trên mã hàng."
            ).format(items, KG_UOM),
            title=_("Thiếu trọng lượng"),
        )

    # Giá thành phẩm do app chia theo kg, không nhận giá tay.
    for d in finished_rows(doc):
        d.set_basic_rate_manually = 0


def allocate_finished_cost_by_kg(doc):
    """Chia tổng giá đầu vào cho các dòng thành phẩm theo số kg đã lưu trên dòng."""
    fg = finished_rows(doc)
    weights = [flt(d.aphvh_kg) for d in fg]
    if not fg or sum(weights) <= 0:
        return

    pool = sum(flt(d.basic_amount) for d in input_rows(doc))
    # Giá trị các dòng định giá riêng (chưa dùng ở bản 0.1) được trừ trước khi chia.
    costed_out = getattr(doc, "get_costed_out_items_cost", None)
    if costed_out:
        pool -= flt(costed_out())

    precision = fg[0].precision("basic_amount")
    amounts = split_by_weight(pool, weights, precision, rounder=flt)
    for d, amount in zip(fg, amounts, strict=True):
        d.basic_amount = amount
        # Không làm tròn đơn giá, giống ERPNext, để tránh mất chính xác.
        d.basic_rate = amount / flt(d.transfer_qty) if flt(d.transfer_qty) else 0.0
