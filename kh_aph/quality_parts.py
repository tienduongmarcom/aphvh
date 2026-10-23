"""Lượng giảm giá tách biệt theo thỏa thuận; không ghi sổ và không bình quân cả mã."""
from kh_aph.quantity_rules import number


def _key(value):
    if not isinstance(value, str) or len(value) > 140 or any(ord(c) < 32 for c in value):
        raise ValueError('Mã phần hàng không hợp lệ')
    return value


def balances(original_qty, net_rate, agreements, used):
    """Một dòng giao gốc; khóa rỗng là phần chưa giảm, khóa khác là thỏa thuận riêng.

    agreements: key, qty, net_discount (tiền giảm chưa thuế trên đúng lượng).
    used gồm cả phiếu trả nháp và đã ghi, bỏ phiếu hủy ở adapter. Không FIFO.
    Caller phải đối chiếu các thỏa thuận với chứng từ gốc và khóa trước khi ghi.
    """
    original_qty, net_rate = number(original_qty), number(net_rate)
    if original_qty <= 0 or net_rate < 0:
        raise ValueError('Lượng và giá dòng giao gốc không hợp lệ')
    parts, allocated = {}, number(0)
    for agreement in agreements:
        key = _key(agreement['key'])
        qty, discount = number(agreement['qty']), number(agreement['net_discount'])
        if not key or key in parts or qty <= 0 or discount <= 0 or discount > qty * net_rate:
            raise ValueError('Phần giảm giá trùng nguồn hoặc vượt giá trị lượng được giảm')
        parts[key] = {'key': key, 'qty': qty, 'remaining': qty,
                      'net_rate': net_rate - discount / qty}
        allocated += qty
    if allocated > original_qty:
        raise ValueError('Các phần giảm giá chồng lấn hoặc vượt lượng giao gốc')
    normal = original_qty - allocated
    parts[''] = {'key': '', 'qty': normal, 'remaining': normal, 'net_rate': net_rate}
    for row in used:
        key, qty = _key(row['key']), number(row['qty'])
        if key not in parts or qty <= 0 or qty > parts[key]['remaining']:
            raise ValueError('Lượng đã trả/chờ trả vượt đúng phần hàng; đối chiếu nguồn trước khi tiếp tục')
        parts[key]['remaining'] -= qty
    return list(parts.values())


def select(parts, selections):
    """Tính riêng từng phần được trả. Không tự chọn hoặc chuyển lượng sang phần khác."""
    if not isinstance(selections, list) or not selections:
        raise ValueError('Chọn phần hàng và lượng nhận trả')
    available = {row['key']: row for row in parts}
    chosen, seen = [], set()
    for row in selections:
        key, qty = _key(row['key']), number(row['qty'])
        if key in seen or key not in available or qty <= 0 or qty > number(available[key]['remaining']):
            raise ValueError('Lượng trả vượt phần đã chọn hoặc phần nhận trả bị trùng')
        seen.add(key)
        rate = number(available[key]['net_rate'])
        if rate < 0:
            raise ValueError('Giá của phần hàng không được âm')
        chosen.append({'key': key, 'qty': qty, 'net_rate': rate, 'net_amount': qty * rate})
    return chosen
