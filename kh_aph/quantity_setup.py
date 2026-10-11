"""Explicit blank-site UAT schema setup; never an automatic production migration."""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from kh_aph.bag_stock import FLAG


def setup():
    if frappe.local.site != 'aphvh-web-uat' or frappe.session.user != 'Administrator':
        frappe.throw('Thiết lập số lượng chỉ trên site UAT trắng')
    if not frappe.conf.get(FLAG):
        frappe.throw('Cần bật flag quantity/valuation trên UAT')
    for slug in ('aph_bag_movement', 'aph_pending_receipt_item', 'aph_pending_receipt'):
        frappe.reload_doc('kh_aph', 'doctype', slug)
    fields = {'Item': [{'fieldname': 'kh_aph_kg_per_bag', 'label': 'Quy cách kg/bao',
        'fieldtype': 'Float', 'insert_after': 'stock_uom', 'description': '0: hàng không quản lý theo bao'}]}
    for dt in ('Stock Entry Detail', 'Purchase Receipt Item', 'Purchase Invoice Item',
               'Sales Order Item', 'Delivery Note Item', 'Sales Invoice Item', 'APH Shared Sales Order Item'):
        fields[dt] = [
            {'fieldname':'kh_aph_bags','label':'Số bao thực tế','fieldtype':'Float','insert_after':'qty','in_list_view':1},
            {'fieldname':'kh_aph_kg_per_bag','label':'Kg/bao đã lưu','fieldtype':'Float','read_only':1,'insert_after':'kh_aph_bags'},
            {'fieldname':'kh_aph_bag_rate','label':'Giá bán/bao','fieldtype':'Currency','read_only':1,'insert_after':'kh_aph_kg_per_bag'}]
    fields['Purchase Receipt'] = [{'fieldname':'kh_aph_pending_receipt','label':'Phiếu chờ định giá',
        'fieldtype':'Link','options':'APH Pending Receipt','read_only':1,'unique':1,'no_copy':1,'insert_after':'supplier'}]
    fields['Landed Cost Voucher'] = [{'fieldname':'kh_aph_by_kg','label':'Phân bổ theo kg thực nhập',
        'fieldtype':'Check','insert_after':'distribute_charges_based_on'}]
    create_custom_fields(fields)
