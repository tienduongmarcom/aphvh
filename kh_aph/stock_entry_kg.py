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

from kh_aph.constants import IG_FIXED_RATE, KG_ENTRY_TYPE, KG_UOM, RULE_KG_V1, RULE_KG_V2, SED_FIXED_RATE
from lab9x.costing_rules import split_by_weight, split_with_fixed


class StockEntryKgCosting:
    """Lớp mở rộng cho DocType Stock Entry (khai báo trong hooks.extend_doctype_class)."""

    def validate_repack_entry(self):
        if ((self.purpose == "Repack" and self.stock_entry_type == KG_ENTRY_TYPE)
                or (self.purpose == "Manufacture" and self.stock_entry_type == "Sản xuất theo kg")):
            from kh_aph.bag_stock import enabled
            self.kh_aph_costing_rule = "kg-v3" if enabled() else RULE_KG_V2
            snapshot_kg(self)
            validate_kg_entry(self)
            return

        # Phiếu không thuộc loại "Đóng gói theo kg": giữ nguyên hành vi chuẩn của ERPNext.
        if self.get("kh_aph_costing_rule"):
            self.kh_aph_costing_rule = None
        return super().validate_repack_entry()

    def set_basic_rate(self, reset_outgoing_rate=True, raise_error_if_no_rate=True):
        super().set_basic_rate(reset_outgoing_rate, raise_error_if_no_rate)
        if uses_kg_rule(self):
            allocate_finished_cost_by_kg(self)

    def get_additional_cost_allocation(self):
        if self.get("kh_aph_costing_rule") == "kg-v3":
            rows = kg_rows(self)
            return rows, "kh_aph_kg", sum(flt(d.kh_aph_kg) for d in rows)
        return super().get_additional_cost_allocation()

    def distribute_additional_costs(self):
        super().distribute_additional_costs()
        if self.get("kh_aph_costing_rule") != "kg-v3":
            return
        rows = kg_rows(self)
        if not rows:
            return
        amounts = split_by_weight(self.total_additional_costs,
            [flt(r.kh_aph_kg) for r in rows], rows[0].precision("additional_cost"), rounder=flt)
        for row in self.items:
            row.additional_cost = 0
        for row, amount in zip(rows, amounts, strict=True):
            row.additional_cost = amount


def uses_kg_rule(doc):
    """Phiếu có dùng quy tắc chia theo kg không — đọc mã quy tắc ĐÃ LƯU trên phiếu."""
    return doc.purpose in ("Repack", "Manufacture") and doc.get("kh_aph_costing_rule") in (RULE_KG_V1, RULE_KG_V2, "kg-v3")


def is_fixed_rate_row(doc, d):
    """Dòng giá cố định (kg-v2): đọc cờ ĐÃ LƯU trên dòng, chỉ với phiếu quy tắc kg-v2."""
    return doc.get("kh_aph_costing_rule") in (RULE_KG_V2, "kg-v3") and bool(d.get(SED_FIXED_RATE)) and d.t_warehouse and not d.s_warehouse


def fixed_rows(doc):
    return [d for d in doc.get("items") if is_fixed_rate_row(doc, d)]


def kg_rows(doc):
    """Thành phẩm chia giá theo kg (trừ dòng giá cố định)."""
    return [d for d in finished_rows(doc) if not is_fixed_rate_row(doc, d)]


def group_is_fixed_rate(item_group):
    """Nhóm hàng (hoặc một nhóm cha) có tích "Giá cố định trên phiếu chia theo kg"."""
    from frappe.utils.nestedset import get_ancestors_of

    if not item_group or not frappe.get_meta("Item Group").has_field(IG_FIXED_RATE):
        return False
    for g in [item_group, *(get_ancestors_of("Item Group", item_group) or [])]:
        if frappe.get_cached_value("Item Group", g, IG_FIXED_RATE):
            return True
    return False


def finished_rows(doc):
    return [d for d in doc.get("items") if (d.is_finished_item or
            (doc.get("kh_aph_costing_rule") == "kg-v3" and d.get("secondary_item_type")))
            and d.t_warehouse and not d.s_warehouse]


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
        d.kh_aph_kg_per_unit = factor
        d.kh_aph_kg = flt(flt(d.transfer_qty) * factor, 6)
        if d.meta.has_field(SED_FIXED_RATE):
            target_only = d.t_warehouse and not d.s_warehouse
            group = frappe.get_cached_value("Item", d.item_code, "item_group") if target_only else None
            d.set(SED_FIXED_RATE, 1 if target_only and group_is_fixed_rate(group) else 0)


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
    if secondary and doc.get("kh_aph_costing_rule") != "kg-v3":
        frappe.throw(
            _("Dòng {0}: bản hiện tại chưa hỗ trợ phụ phẩm định giá riêng trên phiếu {1}.").format(
                ", ".join(str(i) for i in secondary), KG_ENTRY_TYPE
            ),
            title=_("Chưa hỗ trợ"),
        )

    if doc.get("additional_costs") and doc.get("kh_aph_costing_rule") != "kg-v3":
        frappe.throw(
            _("Bản hiện tại chưa hỗ trợ chi phí cộng thêm trên phiếu {0}.").format(KG_ENTRY_TYPE),
            title=_("Chưa hỗ trợ"),
        )

    if doc.get("kh_aph_costing_rule") == "kg-v3":
        if any(flt(row.amount) < 0 for row in doc.get("additional_costs") or []):
            frappe.throw("Chi phí sản xuất cộng thêm không được âm")
        loss = flt(sum(flt(d.kh_aph_kg) for d in input_rows(doc)) -
                   sum(flt(d.kh_aph_kg) for d in finished_rows(doc)), 6)
        doc.kh_aph_process_loss_kg = loss
        if loss > 0:
            if doc.get("kh_aph_loss_type") != "Hao hụt tự nhiên" or not doc.get("kh_aph_loss_reason"):
                frappe.throw("Hao hụt: cần loại tự nhiên và lý do; bất thường phải xuất chi phí riêng trước sản xuất")

    for d in fixed_rows(doc):
        if flt(d.basic_rate) <= 0:
            frappe.throw(
                _("Dòng {0} ({1}): dòng giá cố định (phế, dở dang) cần nhập Đơn giá cơ bản.").format(
                    d.idx, d.item_code
                ),
                title=_("Thiếu giá cố định"),
            )
        d.set_basic_rate_manually = 1

    if not kg_rows(doc):
        frappe.throw(
            _("Phiếu {0} cần ít nhất một thành phẩm chia giá theo kg.").format(KG_ENTRY_TYPE),
            title=_("Thiếu thành phẩm"),
        )

    missing = [d for d in kg_rows(doc) if flt(d.kh_aph_kg) <= 0]
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
    for d in kg_rows(doc):
        d.set_basic_rate_manually = 0


def allocate_finished_cost_by_kg(doc):
    """Chia tổng giá đầu vào cho các dòng thành phẩm theo số kg đã lưu trên dòng.

    kg-v2: trước khi chia, trừ giá trị các dòng giá cố định (số lượng × đơn giá nhập tay).
    """
    fg = kg_rows(doc)
    weights = [flt(d.kh_aph_kg) for d in fg]
    if not fg or sum(weights) <= 0:
        return

    pool = sum(flt(d.basic_amount) for d in input_rows(doc))
    # Giá trị các dòng định giá riêng chuẩn của ERPNext (không dùng trên phiếu này) được trừ trước.
    costed_out = getattr(doc, "get_costed_out_items_cost", None)
    if costed_out and doc.get("kh_aph_costing_rule") != "kg-v3":
        pool -= flt(costed_out())

    precision = fg[0].precision("basic_amount")
    fixed_amounts = []
    for d in fixed_rows(doc):
        d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), precision)
        fixed_amounts.append(d.basic_amount)
    try:
        amounts = split_with_fixed(pool, fixed_amounts, weights, precision, rounder=flt)
    except ValueError as e:
        frappe.throw(_("Phiếu {0}: {1}.").format(doc.name or KG_ENTRY_TYPE, e), title=_("Giá cố định quá lớn"))
    for d, amount in zip(fg, amounts, strict=True):
        d.basic_amount = amount
        # Không làm tròn đơn giá, giống ERPNext, để tránh mất chính xác.
        d.basic_rate = amount / flt(d.transfer_qty) if flt(d.transfer_qty) else 0.0
