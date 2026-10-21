"""Trả lẻ kg: tách khối lượng hàng và số bao vật lý; không phụ thuộc Frappe."""
from kh_aph.quantity_rules import number

LOOSE = "kh_aph_tra_le_kg"


def loose_return(qty, bags, weight, original_qty, original_bags):
    qty, bags, weight, original_qty, original_bags = map(number,
        (qty, bags or 0, weight, original_qty, original_bags or 0))
    if qty >= 0 or original_qty <= 0 or -qty > original_qty:
        raise ValueError("Lượng trả phải âm và không vượt lượng trên dòng giao gốc")
    if weight <= 0:
        raise ValueError("Dòng giao gốc chưa có quy cách bao hợp lệ")
    if bags > 0 or bags != bags.to_integral_value() or -bags > original_bags:
        raise ValueError("Số bao nhận lại phải nguyên, không âm và không vượt số bao đã giao")
    # Số bao mang dấu như chứng từ trả, nhưng kg không được suy từ số bao/vỏ đã mở.
    return {"qty": qty, "bags": bags, "kg_per_bag": weight}
