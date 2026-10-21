"""Thông tin nhận diện khách chỉ đọc, kể cả Address/Contact nhập riêng qua import.

Chỉ nối các hồ sơ được get_list cho phép, liên kết đúng Customer. Không sửa ô
tóm tắt của Customer, không chọn địa chỉ giao trên đơn và không ghi snapshot cũ.
"""
import re

import frappe
from frappe.utils import strip_html

CUSTOMER_FIELDS = ['name', 'customer_name', 'mobile_no', 'primary_address',
                   'customer_primary_address', 'customer_primary_contact']


def _plain(value):
    value = re.sub(r'<br\s*/?>', ', ', str(value or ''), flags=re.I)
    return ' '.join(strip_html(value).split())


def _linked(doctype, customers, fields, preferred):
    """Một truy vấn theo nhóm; quyền parent và điều kiện child cùng truy vấn."""
    if not customers:
        return {}
    try:
        rows = frappe.get_list(doctype, filters=[
            ['Dynamic Link', 'parenttype', '=', doctype],
            ['Dynamic Link', 'link_doctype', '=', 'Customer'],
            ['Dynamic Link', 'link_name', 'in', customers],
            *([[doctype, 'disabled', '=', 0]] if doctype == 'Address' else []),
        ], fields=['name', *fields, '`tabDynamic Link`.link_name as linked_customer'],
            order_by=f'{preferred} desc, creation asc, name asc' +
                     (', `tabContact Phone`.idx asc' if doctype == 'Contact' else ''), limit_page_length=0)
    except frappe.PermissionError:
        return None
    result = {}
    for row in rows:
        # Phòng thủ ở ranh giới dữ liệu, không dùng Link của Supplier/khách ngoài yêu cầu.
        if row.get('linked_customer') in customers:
            result.setdefault(row.linked_customer, []).append(row)
    return result


def _preferred(rows, name):
    return next((r for r in rows if r.name == name), rows[0] if rows else None)


def details(customers):
    """Đầu vào là Customer đã lọc quyền; trả đúng bốn trường nhận diện cho UI."""
    result = {c.name: {'name': c.name, 'customer_name': c.customer_name,
                      'mobile_no': c.get('mobile_no') or '',
                      'primary_address': _plain(c.get('primary_address'))} for c in customers}
    names = [c.name for c in customers]
    addresses = _linked('Address', names,
        ['address_title', 'address_type', 'address_line1', 'address_line2', 'city', 'county',
         'state', 'pincode', 'country', 'email_id', 'phone', 'fax', 'is_primary_address'], 'is_primary_address')
    contacts = _linked('Contact', names, ['mobile_no', 'phone', 'is_primary_contact',
        '`tabContact Phone`.phone as listed_phone'], 'is_primary_contact')
    for c in customers:
        value = result[c.name]
        address = _preferred((addresses or {}).get(c.name, []), c.get('customer_primary_address'))
        contact_rows = (contacts or {}).get(c.name, [])
        contact = _preferred(contact_rows, c.get('customer_primary_contact'))
        # Hồ sơ liên kết là nguồn hiện tại: cache Customer có thể còn số/địa chỉ cũ.
        if address:
            from frappe.contacts.doctype.address.address import get_address_display
            value['primary_address'] = _plain(get_address_display(dict(address)))
        elif addresses is None:
            value['primary_address'] = 'Không có quyền xem địa chỉ liên kết'
        elif c.get('customer_primary_address'):
            value['primary_address'] = ''
        if contact:
            # Contact rỗng không che số đang có trên liên hệ khác của cùng khách.
            ordered = [contact, *(r for r in contact_rows if r is not contact)]
            value['mobile_no'] = next((r.get('mobile_no') or r.get('phone') or r.get('listed_phone')
                                       for r in ordered if r.get('mobile_no') or r.get('phone') or r.get('listed_phone')), '')
        elif contacts is None or c.get('customer_primary_contact'):
            value['mobile_no'] = ''
        # Giữ SĐT khai trực tiếp trên Customer nếu không có Contact thay thế.
        # Khi Contact đã xóa số, không làm sống lại cache cũ.
        if not value['mobile_no']:
            value['mobile_no'] = (address or {}).get('phone') or ''
        if not value['mobile_no'] and (contacts is None or addresses is None):
            value['mobile_no'] = 'Không có quyền xem số điện thoại liên kết'
    return result
