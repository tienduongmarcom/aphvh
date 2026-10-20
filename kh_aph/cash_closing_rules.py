"""Số tiền và dấu vết chốt quỹ; không phụ thuộc Frappe."""
from decimal import Decimal, InvalidOperation
import hashlib
import json


def money(value):
    try:
        number = Decimal(str(value if value is not None else 0))
    except (InvalidOperation, ValueError):
        raise ValueError("Số tiền không hợp lệ") from None
    if not number.is_finite() or abs(number) > Decimal("999999999999999") or number != number.quantize(Decimal("0.01")):
        raise ValueError("Số tiền phải hữu hạn, tối đa hai số lẻ và trong giới hạn cho phép")
    return number


def anchor(rows):
    """Kèm cả dòng hủy để nhận ra sửa/xóa/hủy/repost, không chỉ so tổng."""
    fields = ("name", "posting_date", "creation", "debit", "credit", "is_cancelled", "voucher_type", "voucher_no", "holder")
    records = {r["name"]: hashlib.sha256(json.dumps([str(r.get(f) or "") for f in fields], ensure_ascii=True).encode()).hexdigest() for r in rows}
    encoded = json.dumps(records, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return encoded, hashlib.sha256(encoded.encode()).hexdigest()


def unchanged(saved, rows):
    old = json.loads(saved)
    current = json.loads(anchor(rows)[0])
    return all(current.get(name) == value for name, value in old.items())


def balance(rows):
    return sum((money(r["debit"]) - money(r["credit"]) for r in rows if not r["is_cancelled"]), Decimal(0))


def position(allocations, saved, rows):
    """Phát sinh mới theo định danh GL; metadata chưa rõ luôn ở nhóm rỗng."""
    if not unchanged(saved, rows):
        raise ValueError("Sổ hoặc người giữ trên nguồn trước mốc đã đổi; cần xác minh lại quỹ")
    old = json.loads(saved)
    result = {user: money(amount) for user, amount in allocations.items()}
    result.setdefault("", Decimal(0))
    for row in rows:
        if row["name"] not in old and not row["is_cancelled"]:
            user = row.get("holder") or ""
            result[user] = result.get(user, Decimal(0)) + money(row["debit"]) - money(row["credit"])
    if sum(result.values()) != balance(rows):
        raise ValueError("Tổng trách nhiệm không khớp sổ quỹ; cần xác minh lại")
    return result
