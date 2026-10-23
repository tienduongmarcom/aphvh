"""Đầu nhận xem lượng của đúng chuyến gửi đến kho mình; không mở phiếu kho nguồn."""
import frappe
from frappe.utils import cint


def expected_receiver(doc):
    from kh_aph import factory_transfer as T
    T.guard()
    if (doc.docstatus!=1 or doc.purpose!='Material Transfer' or not cint(doc.add_to_transit)
            or doc.get('outgoing_stock_entry') or not doc.get(T.DESTINATION)):
        frappe.throw('Chuyến chưa có kho nhận được chỉ định',frappe.PermissionError)
    if not (frappe.has_permission('Stock Entry','create') and frappe.has_permission('Stock Entry','submit')):
        frappe.throw('Cần quyền lập và xác nhận nhận kho',frappe.PermissionError)
    frappe.get_doc('Company',doc.company).check_permission('read')
    # Chỉ quyền thao tác tại kho dự kiến mới mở projection lượng của chuyến.
    T._destination(doc.get(T.DESTINATION),doc.company,None)


def make_incoming(source):
    """Tái dùng mapping của core16.51.1, bỏ qua CHỈ quyền đọc nguồn đã ràng buộc.

    Mapper core không có tham số quyền ở wrapper make_stock_in_entry. Target vẫn
    kiểm create/submit/UserPermission bình thường; không có RPC trả nguồn hoặc giá.
    Chỉ áp Kg/hệ số1/khônglô-sêri do _item kiểm trước khi gọi.
    """
    expected_receiver(source)
    from frappe.model.mapper import get_mapped_doc
    from kh_aph import factory_transfer as T
    def item(source_row,target_row,parent):
        target_row.t_warehouse=''
        target_row.s_warehouse=source_row.t_warehouse
        target_row.qty=float(T._number(source_row.transfer_qty)-T._number(source_row.transferred_qty or 0))
    def missing(source_doc,target):
        target.stock_entry_type='Material Transfer'
        target.from_warehouse=None;target.to_warehouse=None
        target.set_missing_values()
    entry=get_mapped_doc('Stock Entry',source.name,{
        'Stock Entry':{'doctype':'Stock Entry','field_map':{'name':'outgoing_stock_entry'},'validation':{'docstatus':['=',1]}},
        'Stock Entry Detail':{'doctype':'Stock Entry Detail','field_map':{'name':'ste_detail','parent':'against_stock_entry'},
            'postprocess':item,'condition':lambda row:T._number(row.transfer_qty)>T._number(row.transferred_qty or 0)}
    },postprocess=missing,ignore_permissions=True)
    entry.flags.ignore_permissions=False
    entry.check_permission('create')
    return entry
