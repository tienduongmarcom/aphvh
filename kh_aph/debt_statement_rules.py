"""Số liệu chụp tại mốc đối chiếu; không suy số dư lịch sử hoặc cấn chéo đơn vị."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


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


def base_unallocated(payment_type, value, source_rate, target_rate):
    """Như Payment Entry16.51.1: thu dùng tỷ giá phía khách (source), chi dùng target."""
    if payment_type not in ('Receive', 'Pay'):
        raise ValueError('Chỉ quy đổi khoản thu hoặc chi khách hàng')
    rate = amount(source_rate if payment_type == 'Receive' else target_rate)
    value = amount(value)
    if rate <= 0 or value < 0:
        raise ValueError('Kiểm tỷ giá và khoản tiền chưa phân bổ trên phiếu gốc')
    return (value * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def deposit_snapshot(receipt, actions):
    """Cọc còn giữ theo đúng nguồn, không bình quân/FIFO hoặc trừ vào nợ lần nữa."""
    from kh_aph.funds_rules import position
    state = position(receipt['amount'], actions)
    by_name = {row['name']: row for row in actions}
    details = []
    for key, remaining in sorted(state['reservations'].items()):
        if remaining <= 0:
            continue
        source = by_name[key]
        if not source.get('shared_order'):
            raise ValueError('Cọc đang giữ thiếu đơn nguồn; cần đối chiếu trước khi cấp biên bản')
        details.append({'company': receipt['company'], 'receipt': receipt['name'], 'reservation': key,
            'shared_order': source['shared_order'], 'source_company': source.get('source_company') or '',
            'reserved': str(remaining)})
    return state, details
