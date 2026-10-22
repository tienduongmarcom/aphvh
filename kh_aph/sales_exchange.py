"""Đơn hàng thay từ phiếu nhận trả: người bán chọn mã mới trên form đơn chuẩn."""
import frappe
from frappe.utils import cint, nowdate
from kh_aph.sales_return import REQUEST, enabled

SOURCE = 'kh_aph_phieu_tra_doi'
ACTIVE = 'kh_aph_luot_doi_dang_mo'
DT = 'APH Shared Sales Order'


def fields():
    return [
        {'fieldname': SOURCE, 'label': 'Phiếu nhận trả của lượt đổi', 'fieldtype': 'Link', 'options': 'Delivery Note',
         'read_only': 1, 'no_copy': 0, 'insert_after': 'customer', 'depends_on': 'eval:doc.kh_aph_phieu_tra_doi',
         'description': 'Chọn mã, lượng và giá hàng thay như đơn mới; chỉ xuất hàng mới khi xác nhận giao.'},
        {'fieldname': ACTIVE, 'label': 'Khóa lượt đổi đang mở', 'fieldtype': 'Data', 'unique': 1,
         'read_only': 1, 'hidden': 1, 'no_copy': 1},
    ]


def _return(name, lock=False):
    if not enabled() or not cint(frappe.conf.get('kh_aph_shared_sales_order')):
        frappe.throw('Chưa bật nghiệp vụ đổi hàng theo đơn bán')
    if lock:
        frappe.db.sql('SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE', name)
    source = frappe.get_doc('Delivery Note', name, for_update=lock)
    source.check_permission('read')
    frappe.get_doc('Company', source.company).check_permission('read')
    frappe.get_doc('Customer', source.customer).check_permission('read')
    if (source.docstatus != 1 or not cint(source.is_return) or not source.get(REQUEST)
            or source.get('kh_aph_xu_ly_tien') != 'Đổi hàng'):
        frappe.throw('Chọn phiếu nhận trả mới đã ghi sổ và chọn xử lý Đổi hàng')
    return source


def _active(name, exclude=None, lock=False):
    rows = frappe.db.sql(f'''SELECT name FROM `tab{DT}`
        WHERE {SOURCE}=%s AND docstatus<2 AND name!=%s ORDER BY name'''
        + (' FOR UPDATE' if lock else ''), (name, exclude or ''), as_dict=True)
    if len(rows) > 1:
        frappe.throw('Có nhiều đơn hàng thay cho cùng phiếu trả; cần đối soát trước khi tiếp tục')
    return rows[0].name if rows else None


@frappe.whitelist()
def prepare(return_note):
    """Chỉ đọc: mở lại đơn đã lưu, hoặc điền nguồn vào form đơn mới chưa lưu."""
    source = _return(return_note)
    existing = _active(source.name)
    if existing:
        frappe.get_doc(DT, existing).check_permission('read')
        return {'existing': existing}
    if not frappe.has_permission(DT, 'create'):
        frappe.throw('Cần quyền lập đơn bán để chọn hàng thay', frappe.PermissionError)
    original = frappe.get_doc('Delivery Note', source.return_against)
    original.check_permission('read')
    return {'defaults': {SOURCE: source.name, 'customer': source.customer, 'currency': 'VND',
            'transaction_date': nowdate(), 'delivery_date': nowdate(), 'selling_price_list': original.selling_price_list},
            'company': source.company}


def validate(doc, method=None):
    if not enabled():
        return
    old = doc.get_doc_before_save()
    if old and old.get(SOURCE) and old.get(SOURCE) != doc.get(SOURCE):
        frappe.throw('Không đổi hoặc xóa phiếu nhận trả nguồn trên đơn hàng thay đã lưu')
    if not doc.get(SOURCE):
        doc.set(ACTIVE, None)
        return
    source = _return(doc.get(SOURCE), lock=True)
    if doc.customer != source.customer:
        frappe.throw('Đơn hàng thay phải đúng khách của phiếu nhận trả')
    for row in doc.get('items') or []:
        wh = frappe.get_doc('Warehouse', row.warehouse)
        wh.check_permission('read')
        if wh.company != source.company:
            frappe.throw('Hàng thay phải cùng đơn vị bán với phiếu nhận trả; không tự cấn chéo đơn vị')
    if _active(source.name, exclude=doc.name, lock=True):
        frappe.throw('Đã có đơn hàng thay cho phiếu trả này; mở lại đơn hiện có để xử lý')
    doc.set(ACTIVE, source.name)


def before_cancel(doc, method=None):
    if not enabled():
        return
    old = doc.get_doc_before_save()
    if old and old.get(SOURCE) != doc.get(SOURCE):
        frappe.throw('Không đổi hoặc xóa nguồn đổi hàng khi hủy đơn')
    if not doc.get(SOURCE):
        doc.set(ACTIVE, None)
        return
    _return(doc.get(SOURCE), lock=True)
    # Giữ Link nguồn trong lịch sử; chỉ nhả khóa duy nhất để lập lại sau hủy.
    doc.set(ACTIVE, None)


def validate_source_change(doc, method=None):
    if not enabled() or not doc.get('shared_order'):
        return
    shared = frappe.get_doc(DT, doc.shared_order)
    shared.check_permission('read')
    if not shared.get(SOURCE):
        return
    source = _return(shared.get(SOURCE))
    if doc.target_company != source.company:
        frappe.throw('Đơn hàng thay không đổi nguồn sang đơn vị khác; xử lý giao dịch riêng, không cấn chéo')
