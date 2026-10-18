"""Explicit isolated-UAT setup. No production migration or automatic hooks.

Requires an opt-in blank aphvh-web-uat clone. Review before any release.
"""
import frappe
from kh_aph.server_cost_guard import apply_query_field_permissions
from kh_aph.shared_order_setup import schema as setup_shared

FIELDS = {'APH Credit Release': [{'fieldname': 'revocation_reason', 'label': 'Lý do thu hồi', 'fieldtype': 'Small Text', 'insert_after': 'revoked_at', 'read_only': 1, 'hidden': 0, 'no_copy': 0, 'permlevel': 0, 'reqd': 0}, {'fieldname': 'revoked_at', 'label': 'Thời điểm thu hồi', 'fieldtype': 'Datetime', 'insert_after': 'revoked_by', 'read_only': 1, 'hidden': 0, 'no_copy': 0, 'permlevel': 0, 'reqd': 0}, {'fieldname': 'revoked_by', 'label': 'Người thu hồi', 'fieldtype': 'Link', 'options': 'User', 'insert_after': 'approved_at', 'read_only': 1, 'hidden': 0, 'no_copy': 0, 'permlevel': 0, 'reqd': 0}], 'APH Shared Sales Order': [{'fieldname': 'kh_aph_global_credit_over', 'label': 'Vượt hạn mức chung', 'fieldtype': 'Check', 'insert_after': 'net_total', 'read_only': 1, 'hidden': 0, 'no_copy': 1, 'permlevel': 0, 'reqd': 0}], 'Customer': [{'fieldname': 'kh_aph_credit_high_risk', 'label': 'Rủi ro cao: cần duyệt bán chịu', 'fieldtype': 'Check', 'insert_after': 'kh_aph_global_credit_limit', 'read_only': 0, 'hidden': 0, 'no_copy': 0, 'permlevel': 9, 'reqd': 0}, {'fieldname': 'kh_aph_global_credit_limit', 'label': 'Hạn mức công nợ chung APH/VH/MK/TL', 'fieldtype': 'Currency', 'options': 'VND', 'insert_after': 'customer_name', 'read_only': 0, 'hidden': 0, 'no_copy': 0, 'permlevel': 9, 'reqd': 0, 'description': '0: chưa đặt hạn mức. Candidate chỉ cảnh báo, chưa chặn khách rủi ro cao.'}], 'Delivery Note': [{'fieldname': 'kh_aph_global_credit_over', 'label': 'Vượt hạn mức chung khi giao', 'fieldtype': 'Check', 'insert_after': 'customer', 'read_only': 1, 'hidden': 0, 'no_copy': 1, 'permlevel': 0, 'reqd': 0}], 'Sales Order Item': [{'fieldname': 'kh_aph_shared_line', 'label': 'Dòng đơn chung', 'fieldtype': 'Data', 'insert_after': 'item_code', 'read_only': 1, 'hidden': 1, 'no_copy': 1, 'permlevel': 0, 'reqd': 0}], 'Sales Order': [{'fieldname': 'kh_aph_shared_fingerprint', 'label': 'Dấu vết đơn chung', 'fieldtype': 'Data', 'insert_after': 'kh_aph_shared_order', 'read_only': 1, 'hidden': 1, 'no_copy': 1, 'permlevel': 0, 'reqd': 0}, {'fieldname': 'kh_aph_shared_order', 'label': 'Đơn bán chung', 'fieldtype': 'Link', 'options': 'APH Shared Sales Order', 'insert_after': 'company', 'read_only': 1, 'hidden': 0, 'no_copy': 1, 'permlevel': 0, 'reqd': 0}]}

APPROVAL_DOCTYPE = {'name': 'APH Credit Release', 'module': 'Kh Aph', 'custom': 1, 'autoname': 'hash', 'track_changes': 1, 'doctype': 'DocType', 'fields': [{'fieldname': 'delivery_note', 'label': 'Phiếu giao được duyệt', 'fieldtype': 'Link', 'options': 'Delivery Note', 'reqd': 1, 'read_only': 0}, {'fieldname': 'reason', 'label': 'Lý do duyệt', 'fieldtype': 'Small Text', 'reqd': 1, 'read_only': 0}, {'fieldname': 'customer', 'label': 'Khách', 'fieldtype': 'Link', 'options': 'Customer', 'reqd': 0, 'read_only': 1}, {'fieldname': 'company', 'label': 'Company', 'fieldtype': 'Link', 'options': 'Company', 'reqd': 0, 'read_only': 1}, {'fieldname': 'amount', 'label': 'Giá trị phiếu giao', 'fieldtype': 'Currency', 'options': 'VND', 'reqd': 0, 'read_only': 1}, {'fieldname': 'fingerprint', 'label': 'Dấu vết nội dung', 'fieldtype': 'Data', 'reqd': 0, 'read_only': 1}, {'fieldname': 'approved_by', 'label': 'Người duyệt', 'fieldtype': 'Link', 'options': 'User', 'reqd': 0, 'read_only': 1}, {'fieldname': 'approved_at', 'label': 'Thời điểm duyệt', 'fieldtype': 'Datetime', 'reqd': 0, 'read_only': 1}], 'permissions': [{'role': 'Accounts Manager', 'read': 1, 'create': 1, 'write': 1, 'submit': 0, 'cancel': 0, 'delete': 1, 'permlevel': 0, 'if_owner': 0}, {'role': 'System Manager', 'read': 1, 'create': 1, 'write': 1, 'submit': 0, 'cancel': 0, 'delete': 1, 'permlevel': 0, 'if_owner': 0}]}

def setup_uat():
    if frappe.local.site != "aphvh-web-uat" or frappe.session.user != "Administrator":
        frappe.throw("Candidate setup chỉ cho Administrator trên aphvh-web-uat")
    # Từ 0.11.5 ap_dung đặt ngôn ngữ hệ thống = vi; bộ UAT HTTP/Desk gọi bằng Administrator và đọc thông báo,
    # nhãn gốc tiếng Anh của ERPNext. Giữ Administrator ở tiếng Anh như trước; người dùng thử khác vẫn theo hệ thống.
    frappe.db.set_value("User", "Administrator", "language", "en")
    return schema()


def schema(cho_phep_du_lieu=False):
    """Phần schema dùng chung cho UAT và bộ cài production (kh_aph.cai_dat_tinh_nang).

    Không tự kiểm site; người gọi phải kiểm Administrator và site đích. Vẫn đòi đủ cờ và site
    chưa có dữ liệu nghiệp vụ, trừ khi `cho_phep_du_lieu` (0.14.2: site đã vận hành, chỉ gọi sau diễn tập bản sao).
    """
    flags = ("kh_aph_server_cost_guard", "kh_aph_post_receivable_on_delivery",
             "kh_aph_shared_sales_order", "kh_aph_global_credit_warning",
             "kh_aph_high_risk_credit_guard")
    if any(not frappe.conf.get(flag) for flag in flags):
        frappe.throw("Cần bật đủ flags candidate trên UAT trước khi setup")
    for dt in ("Customer", "Item", "Sales Order", "Delivery Note", "Sales Invoice",
               "Stock Entry", "Payment Entry", "GL Entry", "Stock Ledger Entry"):
        if not cho_phep_du_lieu and frappe.db.count(dt):
            frappe.throw("UAT phải là bản sao chưa có dữ liệu nghiệp vụ: " + dt)
    from kh_aph.constants import ROLE_NO_COST
    if not frappe.db.exists("Role", ROLE_NO_COST):
        frappe.get_doc({"doctype": "Role", "role_name": ROLE_NO_COST, "desk_access": 1}).insert()
    from kh_aph.quantity_setup import schema as setup_quantity
    setup_quantity()
    from kh_aph.funds_setup import schema as setup_funds
    setup_funds()
    apply_query_field_permissions()
    setup_shared()
    if not frappe.db.exists("DocType", "APH Credit Release"):
        frappe.get_doc(APPROVAL_DOCTYPE).insert()
    # 0.11.1: giá thành nhà máy, phiếu quỹ nhà máy, điều chỉnh bán hàng (mỗi hàm tự đòi cờ của mình).
    from kh_aph import factory_cash, factory_costing, sales_adjust
    factory_costing.schema()
    factory_cash.schema()
    sales_adjust.schema()
    if not frappe.conf.get("kh_aph_data_review"):
        frappe.throw("Cần bật cờ kh_aph_data_review")
    # 0.11.2: cây kho chuẩn / loại kho / đóng gói 2 công đoạn / kiểm kê có mốc (hàm tự đòi cờ kh_aph_kho_chuan).
    from kh_aph import kho_chuan
    kho_chuan.schema()
    # 0.11.3: bán hàng P1 (hàm tự đòi cờ kh_aph_sales_p1).
    from kh_aph import sales_p1
    sales_p1.schema()
    # 0.11.4: báo cáo quản trị, khóa kỳ, xác nhận công nợ (hàm tự đòi cờ kh_aph_quan_tri).
    from kh_aph import quan_tri
    quan_tri.schema()
    # 0.12.0–0.12.1: Trung tâm dữ liệu, số dư đầu kỳ (mỗi hàm tự đòi cờ của mình).
    from kh_aph import dau_ky, du_lieu
    du_lieu.schema()
    dau_ky.schema()
    # 0.13: kho vận hành, giá sàn / quầy bán hàng (mỗi hàm tự đòi cờ của mình).
    from kh_aph import ban_quay, kho_van_hanh
    kho_van_hanh.schema()
    ban_quay.schema()
    # 0.14: Trung tâm Bán hàng, tiền và vay (mỗi hàm tự đòi cờ của mình).
    from kh_aph import tien_vay, trung_tam_ban
    trung_tam_ban.schema()
    from kh_aph import cash_custody
    cash_custody.schema()
    from kh_aph import cash_closing
    cash_closing.schema()
    from kh_aph import cash_handover
    cash_handover.schema()
    tien_vay.schema()
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    create_custom_fields({'Delivery Note': [
        {'fieldname': 'kh_aph_delivery_state', 'label': 'Trạng thái giao hàng',
         'fieldtype': 'Select', 'options': 'Chờ xuất\nĐang giao\nKhách đã nhận',
         'insert_after': 'customer', 'read_only': 1, 'allow_on_submit': 1, 'no_copy': 1},
        {'fieldname': 'kh_aph_delivery_actor', 'label': 'Người xác nhận giao/nhận',
         'fieldtype': 'Link', 'options': 'User', 'insert_after': 'kh_aph_delivery_state',
         'read_only': 1, 'allow_on_submit': 1, 'no_copy': 1},
        {'fieldname': 'kh_aph_delivery_at', 'label': 'Thời điểm xác nhận giao/nhận',
         'fieldtype': 'Datetime', 'insert_after': 'kh_aph_delivery_actor',
         'read_only': 1, 'allow_on_submit': 1, 'no_copy': 1},
    ]})
    filters = {"parent": "Delivery Note", "role": "Accounts Manager",
               "permlevel": 0, "if_owner": 0}
    rows = frappe.get_all("Custom DocPerm", filters=filters, fields=["name"])
    if len(rows) > 1:
        frappe.throw("Trùng dòng quyền Accounts Manager; cần đối soát")
    if rows:
        frappe.db.set_value("Custom DocPerm", rows[0].name, "read", 1)
    else:
        if not frappe.db.exists("Custom DocPerm", {"parent": "Delivery Note"}):
            frappe.throw("Chưa có bảng quyền tùy chỉnh Delivery Note; không thay quyền chuẩn")
        frappe.get_doc({"doctype": "Custom DocPerm", "parenttype": "DocType",
                        "parentfield": "permissions", **filters, "read": 1}).insert()
    for dt,fields in FIELDS.items():
        meta = frappe.get_meta(dt)
        if any(not meta.has_field(field["fieldname"]) for field in fields):
            frappe.throw("Thiếu field candidate: " + dt)
    frappe.db.commit()
    frappe.clear_cache()
    return {"site": frappe.local.site, "custom_fields": sum(map(len, FIELDS.values())),
            "production_release": False}
