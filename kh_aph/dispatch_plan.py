"""Kiểm lượng giao được chọn; thuần Python để agent khác kiểm độc lập."""
from decimal import Decimal, InvalidOperation


def number(value):
    try:
        result = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        raise ValueError("Số lượng không hợp lệ") from None
    if not result.is_finite():
        raise ValueError("Số lượng phải hữu hạn")
    return result


def plan(rows, selected):
    """Dòng theo Sales Order Item; lượng Kg, bao nguyên theo snapshot đã chốt."""
    if not isinstance(selected, list) or not selected or len(selected) > 200:
        raise ValueError("Chọn từ 1 đến 200 dòng giao hàng")
    available = {r["source_row"]: r for r in rows}
    seen, result = set(), []
    for choice in selected:
        if not isinstance(choice, dict) or choice.get("source_row") not in available:
            raise ValueError("Dòng giao không thuộc nguồn đang hiệu lực")
        key = choice["source_row"]
        if key in seen:
            raise ValueError("Không chọn trùng dòng giao")
        seen.add(key)
        row = available[key]
        qty = number(choice.get("qty"))
        remaining = number(row["ordered_qty"]) - number(row["delivered_qty"]) - number(row["draft_qty"])
        if qty <= 0 or qty > remaining:
            raise ValueError("Lượng giao phải dương và không vượt lượng còn lập phiếu: " + key)
        weight = number(row.get("kg_per_bag"))
        bags = qty / weight if weight > 0 else Decimal(0)
        if weight > 0 and bags != bags.to_integral_value():
            raise ValueError("Lượng giao phải đủ bao theo quy cách đã lưu: " + key)
        result.append({**row, "qty": float(qty), "bags": int(bags) if weight > 0 else 0})
    return result
