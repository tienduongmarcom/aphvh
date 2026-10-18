"""Rà nguồn Cash có/chưa có người giữ; không suy đây là tiền còn giữ hiện tại."""
from kh_aph.cash_custody import review


def execute(filters=None):
    f = filters or {}
    columns = [
        {"fieldname": "posting_date", "label": "Ngày", "fieldtype": "Date", "width": 100},
        {"fieldname": "account", "label": "Quỹ tiền mặt", "fieldtype": "Link", "options": "Account", "width": 200},
        {"fieldname": "voucher_type", "label": "Loại nguồn", "fieldtype": "Link", "options": "DocType", "width": 150},
        {"fieldname": "voucher_no", "label": "Chứng từ nguồn", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
        {"fieldname": "debit", "label": "Tăng tiền mặt", "fieldtype": "Currency", "width": 140},
        {"fieldname": "credit", "label": "Giảm tiền mặt", "fieldtype": "Currency", "width": 140},
        {"fieldname": "holder", "label": "Người giữ ghi trên nguồn", "fieldtype": "Link", "options": "User", "width": 220},
        {"fieldname": "status", "label": "Tình trạng nguồn", "fieldtype": "Data", "width": 240},
    ]
    return columns, review(f.get("company"), f.get("from_date"), f.get("to_date")), \
        "Đây là phát sinh trên sổ theo chứng từ nguồn, chưa phải số tiền mỗi người đang giữ. Chưa bao gồm chốt ca và bàn giao mới."
