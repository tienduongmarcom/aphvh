"""Phân bổ giảm theo lượng trên JE chuẩn, nối phần trả trên DN chuẩn; không sổ riêng."""
from contextvars import ContextVar
import json
import frappe
from frappe.utils import flt
from kh_aph.quantity_rules import number
from kh_aph.quality_parts import balances, select

ALLOCATION = 'kh_aph_phan_bo_giam'
RETURN_PARTS = 'kh_aph_phan_nhan_tra'
_BUILD = ContextVar('quality_allocation_build', default=None)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def parse(raw):
    try:
        rows = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(rows, list) or not rows or any(not isinstance(r, dict) for r in rows):
            raise ValueError()
        return rows
    except (ValueError, TypeError):
        frappe.throw('Phân bổ giảm/nhận trả chưa hợp lệ; đối chiếu lại chứng từ gốc')


def agreements(invoice, lock=False):
    if not frappe.get_meta('Journal Entry').has_field(ALLOCATION):
        return []  # Trước bộ cài tường minh, đường cũ không truy vấn cột chưa có.
    from kh_aph.sales_p1 import F_JE_HD
    return frappe.db.sql(f'''SELECT name, docstatus, {ALLOCATION} AS allocation FROM `tabJournal Entry`
        WHERE {F_JE_HD}=%s AND docstatus<2 ORDER BY name''' + (' FOR UPDATE' if lock else ''), invoice, as_dict=True)


def simple_taxes(doc):
    taxes=doc.get('taxes') or []
    if len(taxes)>1 or any(row.charge_type!='On Net Total' for row in taxes):
        frappe.throw('Khoản có thuế/chi phí kiểu khác; kế toán đối chiếu chứng từ chuẩn trước khi chia phần hàng')


def prepare_return_prices(doc):
    # Giá phần hàng là giá thuần đã tính từ nguồn, không trừ chiết khấu cũ lần nữa.
    simple_taxes(doc)
    doc.discount_amount=0
    doc.additional_discount_percentage=0
    for tax in doc.get('taxes') or []:
        tax.included_in_print_rate=0


def prepare(si, raw, total, exclude=None, allow_unclassified=False):
    """Chỉ đường nhập mới có lựa chọn rõ lượng; API cũ chưa phân bổ giữ luồng cũ."""
    if not frappe.get_meta('Journal Entry').has_field(ALLOCATION):
        frappe.throw('Chưa cài phân bổ phần hàng; quản trị viên chạy bộ cài tính năng trước')
    simple_taxes(si)
    if si.currency != 'VND' or si.party_account_currency != 'VND':
        frappe.throw('Phân bổ giảm theo lượng hiện dùng cho khoản VND')
    from kh_aph.sales_p1 import _thue_suat
    from lab9x.ban_hang import chia_giam_gia
    chosen, seen, output, chia = parse(raw), set(), [], []
    prior = [row for row in agreements(si.name, lock=True) if row.name != exclude]
    for row in prior:
        frappe.get_doc('Journal Entry',row.name).check_permission('read')
    if not allow_unclassified and any(not row.allocation for row in prior):
        frappe.throw('Khoản cũ chưa có phân bổ lượng; kế toán đối chiếu trước khi lập phần giảm mới')
    for choice in chosen:
        key = choice.get('invoice_row')
        if key in seen:
            frappe.throw('Không chọn trùng dòng hóa đơn')
        seen.add(key)
        source = next((row for row in si.items if row.name == key), None)
        if not source or source.uom != 'Kg' or flt(source.conversion_factor) != 1:
            frappe.throw('Chọn đúng dòng hàng Kg của khoản gốc')
        # Không đoán phần chưa giảm sau một phiếu trả cũ chưa phân loại.
        if source.dn_detail and frappe.db.sql('''SELECT r.name FROM `tabDelivery Note Item` r
            JOIN `tabDelivery Note` p ON p.name=r.parent WHERE r.dn_detail=%s AND p.is_return=1
            AND p.docstatus<2 LIMIT 1''', source.dn_detail):
            frappe.throw('Dòng đã có nhận trả; đối chiếu phần lượng trước khi lập giảm mới')
        allocated = sum((number(row['qty']) for je in prior if je.allocation for row in parse(je.allocation)
                         if row['invoice_row'] == key), number(0))
        qty, amount = number(choice.get('qty')), number(choice.get('amount'))
        if qty <= 0 or qty + allocated > number(source.qty):
            frappe.throw('Lượng giảm chồng phần đã giảm/đang đề nghị hoặc vượt lượng gốc')
        tax, _ = _thue_suat(si, source)
        split = chia_giam_gia(float(amount), [(key, float(qty * number(source.net_rate)), tax)],
                              precision=si.precision('base_grand_total') or 0)[0]
        chia.append(split)
        output.append({'invoice_row':key, 'qty':str(qty), 'net_discount':str(split[1]), 'tax_discount':str(split[2])})
    if abs(sum(number(row['net_discount']) + number(row['tax_discount']) for row in output) - number(total)) > number('0.5'):
        frappe.throw('Tổng tiền giảm phải khớp chi tiết từng phần hàng')
    return output, chia


def insert(je):
    token = _BUILD.set(id(je))
    try:
        je.insert()
    finally:
        _BUILD.reset(token)


def protect(doc, old):
    current, previous = doc.get(ALLOCATION) or '', (old.get(ALLOCATION) if old else '') or ''
    if not current and not previous and not doc.get('amended_from'):
        return
    if old and current != previous and not (_BUILD.get() == id(doc) and not previous):
        frappe.throw('Không sửa/xóa phân bổ lượng đã lưu; bỏ đề nghị nháp và lập lại nếu cần')
    inherited = False
    if not old and doc.get('amended_from') and _BUILD.get() != id(doc):
        source = frappe.get_doc('Journal Entry', doc.amended_from)
        source.check_permission('read')
        if source.docstatus != 2:
            frappe.throw('Chỉ sửa đổi từ đề nghị giảm đã hủy')
        previous_source = source.get(ALLOCATION) or ''
        if current and current != previous_source:
            frappe.throw('Phân bổ của bản sửa đổi phải giữ đúng nguồn đã hủy')
        if previous_source:
            doc.set(ALLOCATION, previous_source)
            current, inherited = previous_source, True
    if not old and current and _BUILD.get() != id(doc) and not inherited:
        frappe.throw('Dùng thao tác Giảm giá theo phần hàng để giữ đúng nguồn và lượng')
    if current:
        parse(current)


def guard_credit(doc, amount, source):
    raw = doc.get(ALLOCATION)
    if raw:
        expected = sum(number(r['net_discount']) + number(r['tax_discount']) for r in parse(raw))
        if abs(expected - number(amount)) > number('0.5'):
            frappe.throw('Số tiền bút toán không khớp phân bổ lượng; lập lại đề nghị nếu thỏa thuận đổi')
        choices = [{'invoice_row':row['invoice_row'],'qty':row['qty'],
                    'amount':str(number(row['net_discount'])+number(row['tax_discount']))} for row in parse(raw)]
        prepare(source, choices, expected, exclude=doc.name)
        check_posted_debits(doc,source,parse(raw))



def _read_return_basis(source, dn):
    """Facade theo DN: chỉ phần giá bán đã duyệt, không mở quyền đọc toàn SI/JE.

    Nhân viên có quyền nhận trả DN vẫn phải qua phạm vi native của nguồn tài chính.
    Không cấp DocPerm mới hoặc trả tài khoản, GL, giá vốn từ nguồn này.
    """
    if source.company != dn.company:
        frappe.throw('Nguồn phân loại khác đơn vị phiếu giao')
    if frappe.has_permission(source.doctype,'read',doc=source):
        source.check_permission('read')
        return
    from frappe.permissions import has_user_permission
    dn.check_permission('read')
    if not frappe.has_permission('Delivery Note','create') or not has_user_permission(source,user=frappe.session.user,ptype='read'):
        frappe.throw('Nguồn phân loại ngoài phạm vi nhận trả được cấp',frappe.PermissionError)


def parts_for_dn(dn, exclude=None, lock=False):
    """Trả None cho luồng cũ; không suy phân bổ từ tổng tiền JE lịch sử."""
    links = frappe.db.sql('''SELECT DISTINCT s.parent FROM `tabSales Invoice Item` s
        JOIN `tabSales Invoice` p ON p.name=s.parent
        WHERE s.delivery_note=%s AND p.docstatus=1 AND p.is_return=0''', dn.name, as_dict=True)
    if len(links) != 1:
        return None
    invoice = links[0].parent
    if lock:
        frappe.db.sql('SELECT name FROM `tabSales Invoice` WHERE name=%s FOR UPDATE', invoice)
    values = agreements(invoice, lock=lock)
    if not any(row.allocation for row in values):
        return None
    if not frappe.get_meta('Delivery Note Item').has_field(RETURN_PARTS):
        frappe.throw('Chưa cài phần nhận trả theo lượng; quản trị viên hoàn tất bộ cài trước')
    si = frappe.get_doc('Sales Invoice', invoice, for_update=lock)
    _read_return_basis(si,dn)
    simple_taxes(si)
    simple_taxes(dn)
    if si.docstatus != 1 or si.company != dn.company or si.customer != dn.customer:
        frappe.throw('Khoản gốc vừa đổi trạng thái hoặc phạm vi; tải lại phiếu trước khi nhận trả')
    if si.currency != 'VND' or any(not row.allocation for row in values):
        frappe.throw('Khoản có phần giảm chưa phân loại; kế toán đối chiếu trước khi nhận trả')
    # Đề nghị giảm nháp giữ lượng; chưa được dùng mức giá chưa xác nhận để hoàn.
    if any(row.docstatus == 0 for row in values):
        frappe.throw('Còn đề nghị giảm nháp; hoàn tất hoặc bỏ đề nghị trước khi nhận trả')
    for row in values:
        _read_return_basis(frappe.get_doc('Journal Entry',row.name),dn)
    used = frappe.db.sql(f'''SELECT r.dn_detail, r.{RETURN_PARTS} AS parts FROM `tabDelivery Note Item` r
        JOIN `tabDelivery Note` p ON p.name=r.parent WHERE p.return_against=%s AND p.is_return=1
        AND p.docstatus<2 AND p.name!=%s ORDER BY p.name, r.idx''' + (' FOR UPDATE' if lock else ''),
        (dn.name, exclude or ''), as_dict=True)
    result = {}
    for source in dn.items:
        si_rows = [row for row in si.items if row.dn_detail == source.name]
        if len(si_rows) != 1:
            frappe.throw('Chưa xác định duy nhất dòng giá gốc cho phần nhận trả')
        original = si_rows[0]
        if abs(flt(original.qty)-flt(source.qty)) > 0.000001 or abs(flt(original.net_rate)-flt(source.net_rate)) > 0.000001:
            frappe.throw('Giá/lượng hóa đơn và phiếu giao khác nhau; kế toán đối chiếu trước khi chia phần trả')
        portions = [{'key':je.name, 'qty':row['qty'], 'net_discount':row['net_discount']}
                    for je in values for row in parse(je.allocation) if row['invoice_row']==original.name]
        reservations = []
        for returned in used:
            if returned.dn_detail == source.name:
                if not returned.parts:
                    frappe.throw('Có phiếu trả cũ chưa phân loại phần hàng; kế toán đối chiếu trước khi tiếp tục')
                reservations.extend(parse(returned.parts))
        try:
            result[source.name] = balances(source.qty, source.net_rate, portions, reservations)
        except (ValueError, KeyError) as exc:
            frappe.throw(str(exc))
    return result


def price(parts, choices):
    try:
        result = select(parts, choices)
        total = sum(row['net_amount'] for row in result)
        qty = sum(row['qty'] for row in result)
    except (ValueError, KeyError, TypeError) as exc:
        frappe.throw(str(exc))
    return result, float(qty), float(total / qty)


def prevent_cancel(doc):
    """Không đổi ý nghĩa tiền đã nhận trả bằng cách hủy thỏa thuận làm nguồn."""
    from kh_aph.sales_p1 import enabled
    if not enabled() or not doc.get(ALLOCATION):
        return
    sources = [row['invoice_row'] for row in parse(doc.get(ALLOCATION))]
    rows = frappe.db.sql(f'''SELECT r.{RETURN_PARTS} AS parts FROM `tabDelivery Note Item` r
        JOIN `tabDelivery Note` p ON p.name=r.parent
        JOIN `tabSales Invoice Item` s ON s.dn_detail=r.dn_detail
        WHERE s.parent=%s AND s.name IN %s AND p.docstatus<2 AND p.is_return=1''',
        (doc.kh_aph_giam_gia_hd, tuple(sources)), as_dict=True)
    if any(row.parts for row in rows):
        frappe.throw('Phần giảm đã được dùng trong phiếu nhận trả; xử lý phiếu trả trước khi hủy giảm')


def validate_return(doc, dn):
    parts = parts_for_dn(dn, exclude=doc.name, lock=True)
    if parts is None:
        if any(row.get(RETURN_PARTS) for row in doc.items):
            frappe.throw('Chưa có nguồn giảm đã phân bổ cho phần nhận trả này')
        return False
    amended = None
    if doc.get('amended_from'):
        amended = frappe.get_doc('Delivery Note', doc.amended_from)
        amended.check_permission('read')
        if amended.docstatus != 2 or amended.return_against != dn.name:
            frappe.throw('Bản sửa đổi phải theo đúng phiếu trả đã hủy và nguồn giao gốc')
    for row in doc.items:
        if not row.get(RETURN_PARTS) and amended:
            previous = next((r for r in amended.items if r.dn_detail == row.dn_detail), None)
            if previous:
                row.set(RETURN_PARTS, previous.get(RETURN_PARTS))
        chosen, qty, rate = price(parts[row.dn_detail], parse(row.get(RETURN_PARTS)))
        precision = row.precision('net_rate') if callable(getattr(row,'precision',None)) else 6
        expected_rate = flt(rate,precision)
        expected_amount=sum(piece['net_amount'] for piece in chosen)
        if abs(abs(flt(row.qty))-qty)>0.000001 or abs(flt(row.net_rate)-expected_rate)>0.000001:
            frappe.throw('Giá/lượng nhận trả phải khớp từng phần đã giảm hoặc chưa giảm')
        if abs(abs(number(row.net_amount))-expected_amount)>number('0.5'):
            frappe.throw('Sai lệch làm tròn tiền phần trả vượt0,5đ; kế toán đối chiếu cách ghi chứng từ chuẩn')
        if getattr(row, 'set', None):
            from lab9x.vn_words import so_vn
            detail = []
            for piece in chosen:
                label = 'Đã giảm (' + piece['key'] + ')' if piece['key'] else 'Chưa giảm'
                detail.append(label + ': ' + so_vn(piece['qty'],6) + ' kg × ' + so_vn(piece['net_rate'],2) + ' VND/kg (chưa thuế)')
            row.set('kh_aph_chi_tiet_phan_tra', '\n'.join(detail))
    return True


def check_posted_debits(je, source, allocation):
    """Phân loại lịch sử không được đổi cách chia tiền/thuế đã ghi trong GL."""
    from kh_aph.sales_p1 import _so_hieu_la, _thue_suat
    from lab9x import ban_hang as B
    code = B.tk_giam_tru(_so_hieu_la(source.company))
    reduction = frappe.db.get_value('Account', {'company':source.company,'account_number':code,'is_group':0}, 'name') if code else None
    expected = {}
    for choice in allocation:
        row = next(r for r in source.items if r.name == choice['invoice_row'])
        _, tax_account = _thue_suat(source,row)
        for account, value in ((reduction or row.income_account,number(choice['net_discount'])),
                               (tax_account,number(choice['tax_discount']))):
            if value:
                key=(account,row.cost_center or '')
                expected[key]=expected.get(key,number(0))+value
    actual={}
    for row in je.accounts:
        party_row=(row.account==source.debit_to and row.party_type=='Customer' and row.party==source.customer
                   and row.reference_type=='Sales Invoice' and row.reference_name==source.name)
        if party_row:
            if flt(row.debit_in_account_currency):
                frappe.throw('Khoản giảm cũ có phát sinh Nợ khác; kế toán đối chiếu chứng từ chuẩn')
            continue
        if flt(row.credit_in_account_currency) or row.party_type:
            frappe.throw('Bút toán cũ có đối ứng khác; không tự phân loại phần hàng')
        key=(row.account,row.cost_center or '')
        actual[key]=actual.get(key,number(0))+number(row.debit_in_account_currency or 0)
    if any(abs(expected.get(k,number(0))-actual.get(k,number(0)))>number('0.5') for k in expected.keys()|actual.keys()):
        frappe.throw('Phân bổ chưa khớp tiền hàng/thuế/tài khoản đã ghi; không sửa số bút toán cũ để vượt kiểm tra')


def summary(source, allocation):
    from lab9x.vn_words import so_vn
    items={row.name:row for row in source.items} if source else {}
    lines=[]
    for record in allocation:
        row=items.get(record['invoice_row'])
        label=(row.get('item_code') if row else None) or record['invoice_row']
        gross=number(record['net_discount'])+number(record['tax_discount'])
        lines.append(str(label)+': '+so_vn(record['qty'],6)+' kg; giảm '+so_vn(gross,2)+
                     ' VND (thuế '+so_vn(record['tax_discount'],2)+' VND)')
    return 'Phần hàng được giảm: '+ '; '.join(lines)


def save_existing(je, allocation, reason, source=None):
    from html import escape
    before=encode({'company':je.company,'posting_date':str(je.posting_date),
                   'accounts':[{k:v for k,v in row.as_dict().items() if k not in ('modified','modified_by')} for row in je.accounts]})
    je.set(ALLOCATION,encode(allocation))
    token=_BUILD.set(id(je))
    try:
        je.save()
    finally:
        _BUILD.reset(token)
    after=encode({'company':je.company,'posting_date':str(je.posting_date),
                  'accounts':[{k:v for k,v in row.as_dict().items() if k not in ('modified','modified_by')} for row in je.accounts]})
    if before!=after:
        frappe.throw('Thông tin tài chính vừa đổi; chưa lưu phân loại, cần đối chiếu lại nguồn')
    je.add_comment('Comment','Bổ sung phân loại phần hàng đã giảm; không ghi giảm thêm: '+escape(reason)+'<br>'+escape(summary(source,allocation)))


def same_selection(allocation, raw):
    try:
        actual = sorted((r['invoice_row'],number(r['qty']),number(r['amount'])) for r in parse(raw))
        expected = sorted((r['invoice_row'],number(r['qty']),number(r['net_discount'])+number(r['tax_discount'])) for r in allocation)
        return actual == expected
    except (KeyError,ValueError,TypeError):
        return False
