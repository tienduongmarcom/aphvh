"""Quy tắc cảnh báo của đơn bán hàng (0.3) — thuần Python để kiểm thử không cần Frappe.

Phần đọc dữ liệu (hạn mức, công nợ, nợ quá hạn) nằm ở sales_warnings.py; ở đây chỉ so sánh và
viết câu cảnh báo. Không có quy tắc nào chặn lưu hay chặn xác nhận đơn.
"""

from aphvh.vn_words import so_vn

# Giá VND là số nguyên; chênh dưới mức này coi như bằng nhau (làm tròn khi đổi ĐVT).
PRICE_TOLERANCE = 0.001


def _get(row, key):
    return row.get(key) if hasattr(row, "get") else getattr(row, key, None)


def _dong(amount) -> str:
    return f"{so_vn(amount, 0)} đ"


def below_price_rows(rows) -> list[dict]:
    """Dòng có giá bán thấp hơn giá trong bảng giá. Dòng chưa có giá trong bảng giá thì bỏ qua."""
    out = []
    for r in rows or []:
        plr = float(_get(r, "price_list_rate") or 0)
        rate = float(_get(r, "rate") or 0)
        if plr > 0 and rate < plr - PRICE_TOLERANCE:
            out.append(
                {
                    "idx": _get(r, "idx"),
                    "item_code": _get(r, "item_code"),
                    "item_name": _get(r, "item_name") or "",
                    "rate": rate,
                    "price_list_rate": plr,
                    "pct": (plr - rate) / plr * 100,
                }
            )
    return out


def price_lines(rows) -> list[str]:
    lines = []
    for r in below_price_rows(rows):
        name = f" {r['item_name']}" if r["item_name"] and r["item_name"] != r["item_code"] else ""
        lines.append(
            f"Dòng {r['idx']} – {r['item_code']}{name}: giá {so_vn(r['rate'], 0)} thấp hơn bảng giá "
            f"{so_vn(r['price_list_rate'], 0)} ({so_vn(r['pct'], 1)}%)."
        )
    return lines


def pick_limit(customer_limit, group_limits) -> tuple[float, str | None]:
    """Hạn mức cảnh báo áp dụng: của riêng khách nếu có, không thì của nhóm gần nhất có đặt.

    group_limits: [(tên nhóm, hạn mức)] từ nhóm của khách lên các nhóm cha.
    Trả về (hạn mức, nguồn); (0, None) nếu không đặt ở đâu.
    """
    if float(customer_limit or 0) > 0:
        return float(customer_limit), "riêng của khách"
    for group, limit in group_limits or []:
        if float(limit or 0) > 0:
            return float(limit), f"nhóm khách {group}"
    return 0.0, None


def credit_lines(limit, source, outstanding, order_amount, overdue) -> tuple[bool, list[str]]:
    """(có vượt hạn mức hoặc có nợ quá hạn không, các câu cảnh báo)."""
    lines = []
    total = float(outstanding or 0) + float(order_amount or 0)
    if float(limit or 0) > 0 and total > float(limit):
        lines.append(
            f"Công nợ của khách tính cả đơn này là {_dong(total)} (đang nợ và đơn chưa lập hóa đơn "
            f"{_dong(outstanding)} + đơn này {_dong(order_amount)}), vượt hạn mức cảnh báo "
            f"{_dong(limit)} ({source}) {_dong(total - float(limit))}."
        )
    if float(overdue or 0) > 0:
        lines.append(f"Khách đang có {_dong(overdue)} nợ quá hạn thanh toán.")
    return bool(lines), lines
