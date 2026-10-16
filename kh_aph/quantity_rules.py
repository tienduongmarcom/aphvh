"""Exact kg/bag arithmetic; kg remains the inventory and price base."""
from decimal import Decimal, InvalidOperation


def number(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError("Số lượng/giá không hợp lệ") from None
    if not result.is_finite():
        raise ValueError("Số lượng/giá phải hữu hạn")
    return result


def bag_conversion(bags, kg_per_bag, rate_per_kg=None):
    bags, weight = number(bags), number(kg_per_bag)
    if bags == 0 or bags != bags.to_integral_value() or weight <= 0:
        raise ValueError("Số bao phải nguyên, khác 0; kg/bao phải lớn hơn 0")
    result = {"qty": bags * weight, "bags": bags, "kg_per_bag": weight}
    if rate_per_kg is not None:
        rate = number(rate_per_kg)
        if rate <= 0:
            raise ValueError("Giá/kg phải lớn hơn 0")
        result.update(rate_per_bag=rate * weight, amount=rate * bags * weight)
    return result


def weighted_cost(total, weights):
    total = number(total)
    weights = [number(w) for w in weights]
    if total < 0 or not weights or any(w <= 0 for w in weights):
        raise ValueError("Chi phí không âm và trọng lượng phải lớn hơn 0")
    amounts = [(total*w/sum(weights)).quantize(Decimal("0.01")) for w in weights]
    amounts[max(range(len(weights)), key=lambda i: weights[i])] += total-sum(amounts)
    return amounts
