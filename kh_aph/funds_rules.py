"""Money already received: explicit reservation/allocation, never FIFO."""
from decimal import Decimal, InvalidOperation


def money(value):
    try:
        value = Decimal(str(value or 0))
    except InvalidOperation as exc:
        raise ValueError("Số tiền không hợp lệ") from exc
    if not value.is_finite() or value != value.quantize(Decimal("0.01")):
        raise ValueError("Số tiền cần hữu hạn, tối đa hai chữ số thập phân")
    return value


def position(received, actions):
    """Active immutable actions, excluding the candidate being validated."""
    received = money(received)
    if received <= 0:
        raise ValueError("Tiền thực nhận phải lớn hơn 0")
    by_name = {r["name"]: r for r in actions}
    if len(by_name) != len(actions):
        raise ValueError("Trùng dòng lịch sử")
    reserves = {r["name"]: money(r["amount"]) for r in actions
                if r["action_type"] in ("Giữ cọc", "Chuyển cọc")}
    spent = Decimal(0)
    for row in actions:
        amount = money(row["amount"])
        if amount <= 0:
            raise ValueError("Lịch sử có số tiền không dương")
        kind = row["action_type"]
        if kind not in ("Giữ cọc", "Chuyển cọc", "Giải phóng cọc", "Cấn hóa đơn", "Hoàn tiền", "Trả tiền thu hộ"):
            raise ValueError("Loại thao tác không hợp lệ")
        if kind in ("Cấn hóa đơn", "Hoàn tiền"):
            spent += amount
        source = row.get("source_reservation")
        if source:
            if source not in reserves or source == row["name"]:
                raise ValueError("Không tìm thấy cọc nguồn")
            reserves[source] -= amount
        elif kind in ("Chuyển cọc", "Giải phóng cọc"):
            raise ValueError("Chuyển/giải phóng cần chọn cọc nguồn")
    if any(v < 0 for v in reserves.values()):
        raise ValueError("Dùng quá cọc đã giữ")
    reserved = sum(reserves.values(), Decimal(0))
    unspent = received - spent
    if unspent < reserved or unspent < 0:
        raise ValueError("Dùng quá tiền thực nhận")
    return {"spent": spent, "reserved": reserved, "unspent": unspent,
            "available": unspent - reserved, "reservations": reserves}


def check_action(received, actions, candidate):
    previous = position(received, actions)
    amount = money(candidate["amount"])
    if amount <= 0:
        raise ValueError("Số tiền phải lớn hơn 0")
    source = candidate.get("source_reservation")
    if source:
        if amount > previous["reservations"].get(source, Decimal(0)):
            raise ValueError("Số tiền vượt cọc nguồn còn lại")
    elif candidate["action_type"] != "Trả tiền thu hộ" and amount > previous["available"]:
        raise ValueError("Số tiền vượt phần chưa giữ/chưa phân bổ")
    return position(received, [*actions, candidate])


def order_figures(order_total, delivered, outstanding, reserved):
    total, delivered, outstanding, reserved = map(money, (order_total, delivered, outstanding, reserved))
    if min(total, delivered, outstanding, reserved) < 0 or delivered > total or outstanding > delivered:
        raise ValueError("Số liệu đơn và công nợ cần đối soát")
    paid = delivered - outstanding
    return {"order_total": total, "remaining_to_pay": max(total - paid - reserved, Decimal(0)),
            "dispatched_debt": outstanding, "undelivered_value": total - delivered,
            "reserved_deposit": reserved, "paid_dispatched": paid}
