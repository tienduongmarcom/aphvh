"""Chống lặp thu quầy trên chính Payment Entry, không tạo sổ thu thứ hai."""
import hashlib
import json
import re

import frappe

KEY = "kh_aph_luot_thu_quay"
HASH = "kh_aph_noi_dung_thu_quay"


def fields():
    return [{"fieldname": name, "label": label, "fieldtype": "Data", "read_only": 1,
             "hidden": 1, "no_copy": 1, "print_hide": 1, "search_index": int(name == KEY)}
            for name, label in ((KEY, "Mã lượt thu quầy"), (HASH, "Dấu nội dung lượt thu quầy"))]


def begin(request_id, payload):
    from kh_aph import cash_custody
    if not cash_custody.enabled():
        return None, None, None
    if not isinstance(request_id, str) or not re.fullmatch(r"[a-zA-Z0-9-]{16,64}", request_id):
        frappe.throw("Thiếu mã lượt thu hợp lệ; mở lại cửa sổ thu tiền")
    frappe.get_doc("Company", payload["company"]).check_permission("read")
    frappe.get_doc("Customer", payload["customer"]).check_permission("read")
    key = hashlib.sha256((frappe.session.user + ":" + payload["company"] + ":" + request_id).encode()).hexdigest()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    # Khóa company trước khi tìm: hai lần đồng thời vẫn thấy kết quả đã commit.
    # Khóa giữ đến hết RPC, kể cả lúc lập hai PE tiền mặt/chuyển khoản.
    frappe.db.sql("select name from `tabCompany` where name=%s for update", payload["company"])
    rows = frappe.db.sql(f"select name, `{HASH}` as digest, docstatus from `tabPayment Entry` "
                         f"where `{KEY}`=%s order by creation, name for update", key, as_dict=True)
    if not rows:
        return key, digest, None
    for row in rows:
        frappe.get_doc("Payment Entry", row.name, for_update=True).check_permission("read")
        if row.digest != digest:
            frappe.throw("Lượt thu này đã ghi với nội dung khác; kiểm tra phiếu đã có trước khi lập lượt mới")
        if row.docstatus != 1:
            frappe.throw("Lượt thu đã có phiếu bị hủy hoặc chưa ghi sổ; kiểm tra phiếu cũ, không ghi thu lại")
    return key, digest, {"phieu_thu": [row.name for row in rows]}


def protect(doc, method=None):
    from kh_aph import cash_custody
    if not cash_custody.enabled():
        return
    old = doc.get_doc_before_save()
    before = tuple(old.get(f) or "" for f in (KEY, HASH)) if old else ("", "")
    after = tuple(doc.get(f) or "" for f in (KEY, HASH))
    allowed = getattr(frappe.flags, "kh_aph_cashier_request", None)
    if after != before and not (not old and after == allowed):
        frappe.throw("Mã lượt thu do hệ thống ghi; không sửa hoặc sao chép trực tiếp")
    if method == "on_trash" and any(after):
        frappe.throw("Giữ phiếu thu quầy để đối chiếu và chống ghi thu trùng")
