"""Số liệu chụp tại mốc đối chiếu; không suy số dư lịch sử hoặc cấn chéo đơn vị."""
from decimal import Decimal, InvalidOperation


def amount(value):
    try:
        result = Decimal(str(value or 0))
    except InvalidOperation as exc:
        raise ValueError('Số công nợ không hợp lệ') from exc
    if not result.is_finite():
        raise ValueError('Số công nợ cần hữu hạn')
    return result


def snapshot(companies, entries, selected):
    """selected là tập voucher đã kiểm quyền; khoản khác là tại CÙNG mốc, không nợ đầu ngày."""
    companies = list(companies)
    if not companies or len(set(companies)) != len(companies):
        raise ValueError('Chọn phạm vi đơn vị không trùng')
    selected = set(selected)
    positions = {company: {'company': company, 'current': Decimal(0), 'increase': Decimal(0),
                           'decrease': Decimal(0), 'other': Decimal(0)} for company in companies}
    movements = {}
    for row in entries:
        company = row['company']
        if company not in positions:
            raise ValueError('Sổ công nợ nằm ngoài phạm vi đối chiếu')
        value = amount(row['amount'])
        positions[company]['current'] += value
        key = (row['voucher_type'], row['voucher_no'])
        if key in selected:
            full_key = (company, *key)
            movements[full_key] = movements.get(full_key, Decimal(0)) + value
    for (company, _type, _name), value in movements.items():
        positions[company]['increase'] += max(value, Decimal(0))
        positions[company]['decrease'] += max(-value, Decimal(0))
    for row in positions.values():
        row['other'] = row['current'] - row['increase'] + row['decrease']
    # Tổng phải thu và dư có giữ riêng; không dùng dư có ở một Company để giảm phải thu Company khác.
    receivable = sum((max(row['current'], Decimal(0)) for row in positions.values()), Decimal(0))
    credit = sum((max(-row['current'], Decimal(0)) for row in positions.values()), Decimal(0))
    return {'positions': [{k: str(v) if isinstance(v, Decimal) else v for k, v in row.items()}
                          for row in positions.values()],
            'movements': [{'company': co, 'doctype': dt, 'name': name, 'amount': str(value)}
                          for (co, dt, name), value in sorted(movements.items())],
            'receivable': str(receivable), 'credit': str(credit)}
