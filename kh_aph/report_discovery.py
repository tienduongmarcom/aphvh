"""Danh sách biến thể báo cáo trống cho hồ sơ ẩn vốn; không đọc Report hoặc SQL báo cáo."""
import frappe
from kh_aph.constants import REPORT_QTY

METHOD = 'frappe.desk.reportview.get_list'


def is_quantity_lookup(values, cmd):
    if cmd != METHOD or values.get('doctype') != 'Report':
        return False
    if set(values) - {'cmd','doctype','fields','filters','order_by','limit','_'}:
        return False
    if values.get('cmd') not in (None, '', METHOD):
        return False
    if values.get('order_by') != 'report_name asc' or str(values.get('limit')) != '0':
        return False
    if '_' in values and not str(values['_']).isdigit():
        return False
    try:
        fields = frappe.parse_json(values.get('fields'))
        filters = frappe.parse_json(values.get('filters'))
    except (ValueError, TypeError):
        return False
    return (fields == ['name','report_name']
            and filters == {'reference_report': REPORT_QTY, 'report_type': 'Custom Report', 'disabled': 0})


@frappe.whitelist()
def get_list(**kwargs):
    from kh_aph.dung_cost_policy import restricted, DANH_SACH_DUOC_XEM
    if not restricted() or frappe.form_dict.get('doctype') in DANH_SACH_DUOC_XEM:
        from frappe.desk.reportview import get_list as native_get_list
        return native_get_list()
    if not is_quantity_lookup(frappe.form_dict, METHOD):
        frappe.throw('Hồ sơ không xem giá vốn không được đọc danh mục báo cáo tùy chỉnh', frappe.PermissionError)
    # Chính sách chỉ cho dùng báo cáo số lượng gốc, không có biến thể tùy chỉnh.
    # Trả rỗng ngay, không nới quyền Report, không chạm DB hoặc trả cấu hình/query.
    return []
