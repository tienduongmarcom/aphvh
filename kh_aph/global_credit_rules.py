"""Global VND warning calculation; no allocations or blocking policy."""
from decimal import Decimal

def measure_credit(balance, additional, limit):
    values = [Decimal(str(v or 0)) for v in (balance, additional, limit)]
    if any(not v.is_finite() for v in values) or values[1] < 0 or values[2] < 0:
        raise ValueError('Invalid global credit inputs')
    balance, additional, limit = values
    projected = max(Decimal(0), balance + additional)
    return {'net_balance': str(balance), 'additional': str(additional),
            'projected': str(projected), 'limit': str(limit),
            'over_limit': bool(limit > 0 and projected > limit)}
