"""Phép chia giá thuần (không phụ thuộc Frappe) để kiểm thử độc lập.

Mọi quy tắc tính giá của app đặt ở đây dưới dạng hàm thuần; phần gắn vào ERPNext nằm ở
stock_entry_kg.py. Thêm quy tắc mới = thêm hàm mới + mã quy tắc mới, không sửa hàm cũ.
"""


def split_by_weight(total, weights, precision=0, rounder=None):
    """Chia `total` theo tỷ lệ `weights`, làm tròn tới `precision` chữ số thập phân.

    Phần lẻ do làm tròn dồn vào dòng có trọng số lớn nhất (dòng đầu tiên nếu bằng nhau),
    nên tổng các phần luôn bằng đúng `total` đã làm tròn.

    >>> split_by_weight(10_800_000, [40, 20])
    [7200000.0, 3600000.0]
    >>> split_by_weight(100, [1, 1, 1])
    [34.0, 33.0, 33.0]
    """
    rnd = rounder or (lambda v, p: round(v, p))
    weights = [float(w or 0) for w in weights]
    if not weights:
        return []

    total = rnd(float(total or 0), precision)
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("Tổng trọng số phải lớn hơn 0")
    if any(w < 0 for w in weights):
        raise ValueError("Trọng số không được âm")

    amounts = [rnd(total * w / total_weight, precision) for w in weights]
    residual = rnd(total - sum(amounts), precision)
    if residual:
        largest = max(range(len(weights)), key=lambda i: (weights[i], -i))
        amounts[largest] = rnd(amounts[largest] + residual, precision)
    return amounts


def split_with_fixed(total, fixed_amounts, weights, precision=0, rounder=None):
    """Quy tắc kg-v2: trừ giá trị các dòng giá cố định khỏi `total`, phần còn lại chia theo kg.

    Trả về danh sách số tiền cho các dòng chia theo kg (cùng thứ tự `weights`).
    Báo lỗi nếu phần còn lại âm (giá cố định lớn hơn tổng đầu vào).

    >>> split_with_fixed(1_000_000, [100_000], [30, 60])
    [300000.0, 600000.0]
    """
    rnd = rounder or (lambda v, p: round(v, p))
    rest = rnd(float(total or 0) - sum(float(a or 0) for a in fixed_amounts), precision)
    if rest < 0:
        raise ValueError(f"Giá trị các dòng giá cố định lớn hơn tổng đầu vào {rnd(-rest, precision)}")
    return split_by_weight(rest, weights, precision, rounder=rnd)
