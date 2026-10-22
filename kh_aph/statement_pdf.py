"""Đóng băng bộ PDF tại lần cấp; in lại đọc File riêng tư, không render số liệu mới."""
from io import BytesIO
import hashlib

import frappe


def make_bundle(statement, documents):
    from pypdf import PdfReader, PdfWriter
    from frappe.utils.pdf import get_pdf
    from frappe.utils.file_manager import save_file
    writer = PdfWriter()
    data = frappe.get_print(statement.doctype, statement.name, print_format='Biên bản đối soát theo lượt', as_pdf=True)
    writer.append(PdfReader(BytesIO(data)))
    for (doctype, name), source in sorted(documents.items()):
        source.check_permission('read')
        if doctype != 'Journal Entry':
            source.check_permission('print')
        if doctype == 'Delivery Note' and not source.is_return and source.get('kh_aph_mau_giao_nhan'):
            from kh_aph.ban_nhanh import _check_print_note, _render_notes, F_ORDER
            _check_print_note(source)
            html = _render_notes(source.get(F_ORDER) or '', [source])['html']
            data = get_pdf(html, options={'page-size': 'A5', 'orientation': 'Landscape',
                'margin-top': '6mm', 'margin-bottom': '6mm', 'margin-left': '7mm', 'margin-right': '7mm'})
        elif doctype == 'Delivery Note':
            data = frappe.get_print(doctype, name, print_format='Phiếu xuất kho bán hàng', as_pdf=True)
        elif doctype == 'Payment Entry':
            data = frappe.get_print(doctype, name, print_format='Phiếu thu chi', as_pdf=True)
        elif doctype == 'Sales Invoice':
            # Khi đã chọn DN, không in thêm hóa đơn vận hành của chính phiếu đó.
            if source.items and all(('Delivery Note', row.delivery_note) in documents for row in source.items):
                continue
            data = frappe.get_print(doctype, name, print_format='Phiếu bán hàng', as_pdf=True)
        else:
            # JE có thể chứa đối tượng khác: chỉ hiện phát sinh của khách trong biên bản,
            # không cấp toàn bộ bút toán nội bộ cho khách.
            continue
        writer.append(PdfReader(BytesIO(data)))
    output = BytesIO()
    writer.write(output)
    content = output.getvalue()
    if not content or not writer.pages:
        frappe.throw('Chưa tạo được đủ bộ giấy; thử lại lượt lập biên bản')
    file = save_file(statement.name + '.pdf', content, statement.doctype, statement.name, is_private=1)
    statement.add_comment('Comment', 'Đã lưu bộ giấy ' + str(len(writer.pages)) + ' trang; SHA256 ' + hashlib.sha256(content).hexdigest())
    return file.file_url
