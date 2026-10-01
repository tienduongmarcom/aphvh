"""Quy tắc kiểm soát 0.3.4 — thuần Python để kiểm thử không cần Frappe.

Sinh ra từ đợt kiểm thử 8086 (01/10/2026): K21, I01, H05, J16, J24, J26, J28.
Phần đọc dữ liệu và chặn/cảnh báo nằm ở controls.py.
"""

from datetime import date

from aphvh.vn_words import so_vn

# Thu/chi tiền mặt từ mức này trở lên thì cảnh báo (nên chuyển khoản; điều kiện khấu trừ thuế bên mua).
CASH_WARN_LIMIT = 20_000_000

# Chứng từ có ngày ghi sổ cần chặn ngày tương lai.
POSTING_DATE_DOCTYPES = (
    "Sales Invoice",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",
    "Delivery Note",
    "Purchase Receipt",
    "Stock Entry",
    "Stock Reconciliation",
)

# Vai trò được phép làm việc ngoại lệ (ngày tương lai).
OVERRIDE_ROLES = ("Accounts Manager", "System Manager")


def _get(row, key):
    return row.get(key) if hasattr(row, "get") else getattr(row, key, None)


def stock_account_rows(rows, account_type_of) -> list:
    """Dòng bút toán ghi vào tài khoản loại Kho. account_type_of: hàm tên TK -> loại TK."""
    out = []
    for r in rows or []:
        acc = _get(r, "account")
        if acc and account_type_of(acc) == "Stock":
            out.append((_get(r, "idx"), acc))
    return out


def stock_account_message(bad) -> str:
    rows = ", ".join(f"dòng {i} ({a})" for i, a in bad)
    return (
        f"Không ghi bút toán tay vào tài khoản kho: {rows}. Sổ cái sẽ lệch sổ kho. "
        "Hàng thừa/thiếu dùng Phiếu kiểm kê; giá vốn sai dùng Phiếu kho hoặc chứng từ điều chỉnh."
    )


def is_future(posting_date, today) -> bool:
    if not posting_date:
        return False
    if isinstance(posting_date, str):
        posting_date = date.fromisoformat(posting_date[:10])
    if isinstance(today, str):
        today = date.fromisoformat(today[:10])
    return posting_date > today


def can_override(roles) -> bool:
    return bool(set(roles or ()) & set(OVERRIDE_ROLES))


def cash_warning(amount) -> str | None:
    amount = float(amount or 0)
    if amount < CASH_WARN_LIMIT:
        return None
    return (
        f"Thu/chi tiền mặt {so_vn(amount, 0)} đ (từ {so_vn(CASH_WARN_LIMIT, 0)} đ trở lên). "
        "Nên chuyển khoản: hóa đơn từ 20 triệu trả tiền mặt thì bên mua không được khấu trừ thuế GTGT đầu vào."
    )


def walk_in_problem(is_walk_in: bool, pay_account, is_return: bool) -> str | None:
    """Khách vãng lai chung chỉ được bán thu tiền ngay (J28)."""
    if not is_walk_in or is_return:
        return None
    if not pay_account:
        return (
            "Khách vãng lai chung chỉ được bán thu tiền ngay: chọn ô 'Thu tiền ngay vào tài khoản' (tiền mặt hoặc ngân hàng). "
            "Khách mua nợ phải tạo mã khách riêng (theo số điện thoại)."
        )
    return None


def deposit_warning(has_references: bool, overdue_total) -> str | None:
    """Thu tiền trả trước không gắn đơn khi khách đang có nợ quá hạn (J24)."""
    overdue_total = float(overdue_total or 0)
    if has_references or overdue_total <= 0:
        return None
    return (
        f"Khách đang nợ quá hạn {so_vn(overdue_total, 0)} đ. Nếu đây là tiền cọc cho đơn mới, "
        "hãy chọn Đơn bán hàng ở bảng tham chiếu để tiền cọc không bị trừ nhầm vào nợ cũ."
    )
