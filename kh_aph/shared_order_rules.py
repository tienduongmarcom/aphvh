"""Pure company routing for the agreed one-order, many-owner workflow."""
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
import hashlib
import json


def plan_orders(rows, warehouses):
    if not rows:
        raise ValueError("Đơn bán phải có ít nhất một dòng hàng")
    groups = OrderedDict()
    identifiers = set()
    for source in rows:
        row = dict(source)
        line = str(row.get("line_id") or "")
        if not line or line in identifiers:
            raise ValueError("Mỗi dòng phải có định danh duy nhất")
        identifiers.add(line)
        warehouse = warehouses.get(row.get("warehouse"))
        if not warehouse or warehouse.get("is_group") or warehouse.get("disabled"):
            raise ValueError("Kho nguồn phải là kho lá đang hoạt động")
        company = warehouse.get("company")
        if not company or warehouse.get("abbr") not in {"APH", "VH", "MK", "TL"}:
            raise ValueError("Kho nguồn phải thuộc APH/VH/MK/TL")
        if row.get("company") and row["company"] != company:
            raise ValueError("Company dòng hàng không khớp chủ sở hữu kho")
        try:
            qty = Decimal(str(row["qty"]))
            rate = Decimal(str(row["rate"]))
        except (KeyError, InvalidOperation, TypeError):
            raise ValueError("Số lượng và giá bán không hợp lệ") from None
        if not qty.is_finite() or not rate.is_finite() or qty <= 0 or rate <= 0:
            raise ValueError("Số lượng và giá bán phải lớn hơn 0")
        if not row.get("item_code"):
            raise ValueError("Thiếu mã hàng")
        row.update(company=company, qty=str(qty), rate=str(rate), amount=str(qty * rate))
        groups.setdefault(company, []).append(row)
    canonical = json.dumps(list(groups.items()), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"companies": groups,
            "net_total": str(sum((Decimal(r["amount"]) for rows in groups.values() for r in rows), Decimal(0))),
            "fingerprint": hashlib.sha256(canonical.encode()).hexdigest()}
