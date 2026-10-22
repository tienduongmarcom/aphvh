"""Lưu giấy dự phòng ngay trên chứng từ nhập bổ sung; không ghi sổ hoặc đồng bộ offline."""
import hashlib
import re

import frappe
from frappe.utils import cint, get_datetime, now_datetime

FLAG = 'kh_aph_tu_giay_tay'
NUMBER = 'kh_aph_so_giay_tay'
ACTUAL = 'kh_aph_thuc_te_luc'
LOCATION = 'kh_aph_noi_luu_giay_tay'
FILE = 'kh_aph_anh_giay_tay'
KEY = 'kh_aph_khoa_giay_tay'
SOURCES = {'Delivery Note': 'kh_aph_kho_van_hanh', 'Stock Entry': 'kh_aph_kho_van_hanh',
           'Payment Entry': 'kh_aph_cash_custody'}
IDENTITY = (FLAG, NUMBER, ACTUAL, 'company')


def enabled(doctype):
    return doctype in SOURCES and cint(frappe.conf.get(SOURCES[doctype]))


def paper_number(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 140 or re.search(r'[<>\x00-\x1f]', value):
        raise ValueError('Ghi số giấy kèm điểm giao/quyển/tờ, tối đa 140 ký tự')
    return ' '.join(value.split()).upper()


def paper_key(company, number):
    return hashlib.sha256((company + '\n' + paper_number(number)).encode()).hexdigest()


def fields():
    result = [
        {'fieldname': 'kh_aph_giay_tay_section', 'label': 'Giấy dự phòng khi mất mạng',
         'fieldtype': 'Section Break', 'collapsible': 1, 'insert_after': 'amended_from', 'print_hide': 1},
        {'fieldname': FLAG, 'label': 'Nhập bổ sung từ giấy tay', 'fieldtype': 'Check',
         'default': '0', 'no_copy': 1, 'allow_on_submit': 1, 'print_hide': 1,
         'read_only_depends_on': 'eval:doc.docstatus==1 && doc.' + FLAG,
         'description': 'Nhập chứng từ chuẩn như bình thường, đính kèm giấy để đối chiếu. Không tự xuất hoặc thu thêm lần nữa.'},
        {'fieldname': NUMBER, 'label': 'Số giấy (điểm giao / quyển / tờ)', 'fieldtype': 'Data',
         'no_copy': 1, 'allow_on_submit': 1, 'print_hide': 1, 'depends_on': 'eval:doc.' + FLAG},
        {'fieldname': ACTUAL, 'label': 'Thời điểm giao / thu thực tế trên giấy', 'fieldtype': 'Datetime',
         'no_copy': 1, 'allow_on_submit': 1, 'print_hide': 1, 'depends_on': 'eval:doc.' + FLAG,
         'description': 'Ngày hạch toán vẫn theo chứng từ và kỳ được phép. Ô này chỉ lưu sự kiện thực tế.'},
        {'fieldname': LOCATION, 'label': 'Nơi giữ giấy gốc', 'fieldtype': 'Data',
         'no_copy': 1, 'allow_on_submit': 1, 'print_hide': 1, 'depends_on': 'eval:doc.' + FLAG},
        {'fieldname': FILE, 'label': 'Ảnh / PDF giấy tay', 'fieldtype': 'Attach',
         'no_copy': 1, 'allow_on_submit': 1, 'print_hide': 1, 'depends_on': 'eval:doc.' + FLAG,
         'description': 'Có thể bổ sung sau khi lưu phiếu. Tệp riêng tư đính kèm đúng phiếu; bản gốc vẫn lưu tại nơi ghi trên.'},
        {'fieldname': KEY, 'label': 'Khóa giấy nhập bổ sung', 'fieldtype': 'Data',
         'unique': 1, 'hidden': 1, 'read_only': 1, 'no_copy': 1, 'allow_on_submit': 1, 'print_hide': 1},
    ]
    for previous, field in zip(result, result[1:]):
        field['insert_after'] = previous['fieldname']
    return result


def schema():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    data = {dt: fields() for dt in SOURCES if enabled(dt)}
    if data:
        create_custom_fields(data)


def _file(doc):
    url = doc.get(FILE)
    if not url:
        return
    targets = [doc.name]
    if doc.get('amended_from'):
        source = frappe.get_doc(doc.doctype, doc.amended_from)
        source.check_permission('read')
        if source.get(FILE) == url:
            targets.append(source.name)
    if not isinstance(url, str) or not url.startswith('/private/files/') or not frappe.db.exists('File',
            {'file_url': url, 'attached_to_doctype': doc.doctype, 'attached_to_name': ['in', targets], 'is_private': 1}):
        frappe.throw('Ảnh giấy tay phải là tệp riêng tư đính kèm đúng phiếu đã lưu')


def validate(doc, method=None):
    if not enabled(doc.doctype) or not doc.meta.has_field(FLAG):
        return
    old = doc.get_doc_before_save()
    if doc.is_new() and doc.get('amended_from'):
        original = frappe.get_doc(doc.doctype, doc.amended_from)
        original.check_permission('read')
        if cint(original.get(FLAG)):
            for field in (FLAG, NUMBER, ACTUAL, LOCATION, FILE):
                if doc.get(field) and str(doc.get(field)) != str(original.get(field)):
                    frappe.throw('Phiếu sửa đổi giữ nguyên giấy nguồn; không đổi giấy thành nghiệp vụ khác')
                doc.set(field, original.get(field))
    if old and cint(old.get(FLAG)) and cint(old.docstatus) != 0:
        for field in IDENTITY:
            before, after = old.get(field), doc.get(field)
            if field == ACTUAL:
                before, after = get_datetime(before), get_datetime(after)
            if before != after:
                frappe.throw('Không đổi hoặc xóa số giấy, đơn vị và thời điểm thực tế sau khi phiếu đã ghi sổ')
        for field in (FILE,):
            if old.get(field) and doc.get(field) != old.get(field):
                frappe.throw('Giữ bản giấy nguồn đã lưu; bổ sung giải thích và tệp mới trong đính kèm, không thay dấu cũ')
    if not cint(doc.get(FLAG)):
        if old and cint(old.get(FLAG)) and cint(old.docstatus) == 0:
            for field in (NUMBER, ACTUAL, LOCATION, FILE, KEY):
                doc.set(field, None)
            return
        if any(doc.get(f) for f in (NUMBER, ACTUAL, LOCATION, FILE, KEY)):
            frappe.throw('Chọn Nhập bổ sung từ giấy tay khi lưu thông tin giấy nguồn')
        return
    frappe.get_doc('Company', doc.company).check_permission('read')
    try:
        number = paper_number(doc.get(NUMBER))
        if not doc.get(ACTUAL) or get_datetime(doc.get(ACTUAL)) > now_datetime():
            raise ValueError('Ghi thời điểm thực tế trên giấy, không chọn thời điểm tương lai')
    except (ValueError, TypeError) as exc:
        frappe.throw(str(exc))
    if not doc.get(LOCATION) or len(doc.get(LOCATION)) > 140 or re.search(r'[<>\x00-\x1f]', doc.get(LOCATION)):
        frappe.throw('Ghi nơi đang giữ giấy gốc, tối đa 140 ký tự')
    if doc.is_new() and not doc.get('amended_from'):
        # SQL chỉ tra dấu trùng sau khi kiểm Company; không trả tên/chứng từ ngoài quyền.
        if frappe.db.exists(doc.doctype, {NUMBER: number, 'company': doc.company, 'docstatus': 2}):
            frappe.throw('Giấy này đã có phiếu hủy. Mở phiếu cũ và dùng Sửa đổi để giữ liên kết lịch sử')
    doc.set(NUMBER, number)
    doc.set(KEY, None if cint(doc.docstatus) == 2 else paper_key(doc.company, number))
    _file(doc)


def _in_use(url):
    return any(enabled(dt) and frappe.get_meta(dt).has_field(FILE)
               and frappe.db.exists(dt, {FILE: url}) for dt in SOURCES)


def protect_file_update(doc, method=None):
    old = doc.get_doc_before_save()
    if old and old.file_url and _in_use(old.file_url) and (doc.get('content') or any(
            doc.get(f) != old.get(f) for f in ('file_url', 'is_private', 'attached_to_doctype', 'attached_to_name'))):
        frappe.throw('Tệp đang lưu giấy tay nguồn; không đổi nội dung, quyền riêng tư hoặc nơi đính kèm')


class PaperFileMixin:
    def on_trash(self):
        if self.file_url and _in_use(self.file_url):
            frappe.throw('Giữ tệp giấy tay nguồn của phiếu để truy lại khi đối chiếu')
        return super().on_trash()
