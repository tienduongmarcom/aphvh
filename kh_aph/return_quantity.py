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


def refund_after_credit(credit, outstanding_after):
    """Khoản thực hoàn tối đa sau khi hóa đơn giảm đã đối chiếu vào hóa đơn gốc.

    Nợ dương còn phải thu, nợ âm là còn phải trả khách. Không hoàn lại số
    đã dùng giảm nợ, cũng không lấy số dư có cũ để tăng tiền hoàn lượt này.
    """
    credit, outstanding_after = map(number, (credit, outstanding_after))
    if credit <= 0:
        raise ValueError("Giá trị hàng trả phải dương")
    return min(credit, max(number(0), -outstanding_after))


def credit_budget(original_total, returned, reductions, proposed):
    """Giới hạn toàn khoản gốc; chưa thay thế phân bổ thỏa thuận theo từng dòng."""
    original_total, returned, reductions, proposed = map(number, (original_total, returned, reductions, proposed))
    if original_total <= 0 or returned < 0 or reductions < 0 or proposed <= 0:
        raise ValueError("Giá trị đối chiếu trả/giảm không hợp lệ")
    remaining = max(number(0), original_total - returned - reductions)
    if proposed > remaining + number('0.5'):
        raise ValueError("Giá trị trả vượt phần còn được xử lý sau các khoản đã trả/giảm; kế toán đối chiếu thỏa thuận và giá trên phiếu trả")
    return remaining
