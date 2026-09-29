"""Đọc số tiền bằng chữ tiếng Việt (dùng cho mẫu in). Thuần Python, kiểm thử không cần Frappe.

Quy ước theo cách đọc phổ biến trên chứng từ kế toán:
- 105 = một trăm linh năm; 1.005.000 = một triệu không trăm linh năm nghìn
- 15 = mười lăm; 25 = hai mươi lăm; 21 = hai mươi mốt; 24 = hai mươi tư; 11 = mười một; 14 = mười bốn
- Nhóm hàng tỷ lặp lại: 10^12 = một nghìn tỷ, 10^18 = một tỷ tỷ
"""

_DIGITS = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")
_UNITS = ("", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ", "tỷ tỷ")


def _read_triplet(n: int, full: bool) -> list[str]:
    """Đọc một nhóm 3 chữ số (0-999). full=True khi không phải nhóm đầu tiên (phải đọc 'không trăm')."""
    hundreds, rest = divmod(n, 100)
    tens, units = divmod(rest, 10)
    words: list[str] = []

    if hundreds or full:
        words += [_DIGITS[hundreds], "trăm"]

    if tens == 0:
        if units:
            if hundreds or full:
                words.append("linh")
            words.append(_DIGITS[units])
        return words

    if tens == 1:
        words.append("mười")
        if units == 5:
            words.append("lăm")
        elif units:
            words.append(_DIGITS[units])
        return words

    words += [_DIGITS[tens], "mươi"]
    if units == 1:
        words.append("mốt")
    elif units == 4:
        words.append("tư")
    elif units == 5:
        words.append("lăm")
    elif units:
        words.append(_DIGITS[units])
    return words


def so_thanh_chu(n: int) -> str:
    """Số nguyên không âm thành chữ, chữ thường. 0 -> 'không'."""
    n = int(n)
    if n < 0:
        raise ValueError("Chỉ đọc số không âm")
    if n == 0:
        return "không"

    groups: list[int] = []
    while n:
        n, g = divmod(n, 1000)
        groups.append(g)
    if len(groups) > len(_UNITS):
        raise ValueError("Số quá lớn")

    words: list[str] = []
    top = len(groups) - 1
    for idx in range(top, -1, -1):
        g = groups[idx]
        if g == 0:
            continue
        words += _read_triplet(g, full=idx != top)
        if _UNITS[idx]:
            words.append(_UNITS[idx])
    return " ".join(words)


def so_tien_bang_chu(amount, currency_word: str = "đồng") -> str:
    """Số tiền (làm tròn đến đồng) thành chữ, viết hoa chữ đầu, có đơn vị tiền. Âm đọc là 'Âm ...'."""
    value = round(float(amount or 0))
    prefix = ""
    if value < 0:
        prefix, value = "âm ", -value
    text = f"{prefix}{so_thanh_chu(value)} {currency_word}".strip()
    return text[:1].upper() + text[1:]


def so_vn(value, precision: int = 3) -> str:
    """Định dạng số kiểu Việt Nam: 1.234.567,5 — bỏ số 0 thừa sau dấu phẩy. None/'' -> ''."""
    if value is None or value == "":
        return ""
    text = f"{float(value):,.{int(precision)}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("-0", ""):
        text = "0"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
