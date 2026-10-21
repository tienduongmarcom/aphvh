"""Bảng chốt ngày chỉ đọc từ nguồn chuẩn; không tạo sổ/chứng từ hoặc cấp duyệt mới."""
import frappe
from frappe.utils import getdate, now_datetime
from kh_aph import cash_closing as C, cash_handover as H, factory_handover as F
from kh_aph.cash_closing_rules import money

LIMIT = 5000


def rows(dt, filters, fields, **kwargs):
    values = frappe.get_list(dt, filters=filters, fields=fields, limit_page_length=LIMIT + 1, **kwargs)
    if len(values) > LIMIT:
        frappe.throw('Bảng chốt ngày vượt 5.000 dòng ' + dt + '; không cắt bớt số liệu')
    return values


def _row(group, status, **values):
    return {'group': group, 'status': status, **values}


def _position(company, account, holder):
    # C._state vẫn kiểm đầy đủ. Khi lỗi đối chiếu đã được biểu diễn thành
    # dòng trong báo cáo, chỉ bỏ message mới của lỗi ấy khỏi hàng đợi popup.
    # Không xóa message có trước, không nuốt PermissionError hoặc lỗi khác.
    messages = frappe.local.message_log
    start = len(messages)
    try:
        return C._state(company, account, holder)
    except frappe.ValidationError:
        del messages[start:]
        raise


def _cash(company):
    result = []
    accounts = rows('Account', {'company': company, 'account_type': 'Cash', 'is_group': 0, 'disabled': 0}, ['name'])
    if len(accounts) > 30:
        frappe.throw('Chọn đơn vị có tối đa30 quỹ để đối chiếu đầy đủ')
    for account in accounts:
        name = account.name
        C.scope(company, name)
        ledger = C.ledger(company, name)
        opening = C.latest(C.OPENING, company, name)
        if not opening:
            result.append(_row('Tiền mặt hiện tại', 'Chưa xác minh người giữ', account=name, amount=C.balance(ledger)))
            continue
        try:
            _, _, _, totals = _position(company, name, frappe.session.user)
        except frappe.ValidationError as exc:
            result.append(_row('Tiền mặt hiện tại', 'Cần xác minh lại: ' + str(exc), account=name, doctype=C.OPENING, document=opening.name))
            continue
        if len(totals) > 100:
            frappe.throw('Quỹ vượt100 nhóm trách nhiệm; cần đối chiếu trên tập đầy đủ')
        for holder, amount in sorted(totals.items()):
            if not holder:
                result.append(_row('Tiền mặt hiện tại', 'Chưa xác minh người giữ', account=name, amount=amount))
                continue
            try:
                _, previous, _, _ = _position(company, name, holder)
            except frappe.ValidationError as exc:
                result.append(_row('Tiền mặt hiện tại', 'Cần xác minh lại: ' + str(exc), account=name, holder=holder))
                continue
            reserved = sum((money(r.requested_amount) for r in H._query(company, name)
                if r.from_account == name and r.from_holder == holder and r.status in H.PENDING), money(0)) if H.enabled() else money(0)
            disputed = H._disputed(company, name, holder) if H.enabled() else False
            result.append(_row('Tiền mặt hiện tại', 'Cần đối chiếu' if disputed or any(v < 0 for v in totals.values()) else 'Theo mốc xác minh',
                account=name, holder=holder, amount=amount, reserved=reserved,
                available=0 if disputed or any(v < 0 for v in totals.values()) else max(money(0), amount-reserved),
                counted=previous.counted_amount if previous else None, difference=previous.difference if previous else None,
                checked_at=previous.closed_at if previous else None,
                doctype=C.SHIFT if previous else C.OPENING, document=previous.name if previous else opening.name))
    return result


def _cash_work(company):
    result = []
    for value in rows(H.DT, {'company': company, 'docstatus': ['in', [1, 2]]},
            ['name','status','from_account','from_holder','requested_amount','received_amount','difference','issue_state','assignee','due_date']):
        if value.status in H.PENDING or value.issue_state == 'Chờ xử lý':
            result.append(_row('Bàn giao / việc tồn', value.status, account=value.from_account, holder=value.from_holder,
                amount=value.requested_amount, counted=value.received_amount, difference=value.difference,
                assignee=value.assignee, due_date=value.due_date, doctype=H.DT, document=value.name))
    for value in rows(C.SHIFT, {'company': company, 'docstatus': 1, 'difference': ['!=', 0]},
            ['name','account','holder','counted_amount','difference','issue_state','assignee','due_date']):
        if value.issue_state != 'Đã đối chiếu':
            result.append(_row('Ca lệch / việc tồn', 'Chờ xử lý', account=value.account, holder=value.holder,
                counted=value.counted_amount, difference=value.difference, assignee=value.assignee, due_date=value.due_date,
                doctype=C.SHIFT, document=value.name))
    for value in rows('APH Phieu quy nha may', {'company': company, 'docstatus': 1, 'loai': 'Bàn giao tiền'},
            ['name','trang_thai','ban_giao_tien','tong_tien','kh_aph_nguoi_giu_tien']):
        if not value.ban_giao_tien and value.trang_thai == 'Chờ nhận':
            result.append(_row('Chuyển tiếp nhà máy', 'Người giữ cần chuyển tiếp và giữ chỗ', holder=value.kh_aph_nguoi_giu_tien,
                amount=value.tong_tien, doctype='APH Phieu quy nha may', document=value.name))
    return result


def _bank(company, day):
    result = []
    banks = rows('Bank Account', {'company': company, 'is_company_account': 1}, ['name','account'])
    names = [bank.name for bank in banks]
    if not names:
        return [_row('Ngân hàng', 'Chưa có thẻ tài khoản ngân hàng được cấp')]
    found = rows('Bank Transaction', {'company': company, 'bank_account': ['in', names], 'docstatus': 1, 'date': ['<=', day]},
        ['name','bank_account','date','deposit','withdrawal','unallocated_amount','party','status'])
    for value in found:
        frappe.get_doc('Bank Account', value.bank_account).check_permission('read')
        state = 'Đã khớp theo sao kê native' if not money(value.unallocated_amount) else 'Chưa xác định đối tượng' if not value.party else 'Chưa khớp hết'
        result.append(_row('Ngân hàng', state, account=next(b.account for b in banks if b.name == value.bank_account),
            amount=money(value.deposit)-money(value.withdrawal), available=value.unallocated_amount,
            doctype='Bank Transaction', document=value.name, checked_at=value.date))
    if not found:
        result.append(_row('Ngân hàng', 'Chưa có giao dịch sao kê native được lưu; đối chiếu tệp tại Tiền và vay'))
    return result


def _debt(company, day):
    values = rows('Payment Ledger Entry', {'company': company, 'party_type': 'Customer', 'delinked': 0, 'posting_date': ['<=', day]},
        ['name','party','posting_date','amount'])
    grouped = {}
    for value in values:
        bucket = grouped.setdefault(value.party, [money(0),money(0),money(0)])
        amount = money(value.amount)
        if getdate(value.posting_date) < getdate(day):
            bucket[0] += amount
        elif amount >= 0:
            bucket[1] += amount
        else:
            bucket[2] -= amount
    result = []
    for customer, (opening, increase, decrease) in sorted(grouped.items()):
        frappe.get_doc('Customer', customer).check_permission('read')
        result.append(_row('Công nợ khách', 'Trong phạm vi dữ liệu được cấp', party=customer,
            opening=opening, increase=increase, decrease=decrease, amount=opening+increase-decrease))
    from kh_aph.funds_rules import position
    for receipt in rows('APH Funds Receipt', {'company': company, 'docstatus': 1}, ['name','amount','customer']):
        actions = rows('APH Funds Action', {'receipt': receipt.name, 'docstatus': 1}, ['name','action_type','amount','source_reservation'])
        state = position(receipt.amount, actions)
        result.append(_row('Cọc / tiền chưa phân bổ hiện tại', 'Chưa xác định khách' if not receipt.customer else 'Theo nguồn thực nhận',
            party=receipt.customer, reserved=sum(state['reservations'].values(), money(0)), available=state['available'],
            doctype='APH Funds Receipt', document=receipt.name))
    return result


def _goods(company, day):
    from kh_aph import delivery_issue as I, ho_so_giao_nhan as S
    result = []
    fields = ['name','docstatus','is_return','posting_date','kh_aph_delivery_state', S.FILE, S.ACTOR, I.STATE, I.ASSIGNEE, I.DUE]
    originals = frappe.get_meta('Delivery Note').has_field(S.ORIGINAL_AT)
    if originals:
        fields += ['kh_aph_mau_giao_nhan', S.ORIGINAL_AT]
    values = rows('Delivery Note', {'company': company, 'docstatus': ['in', [1,2]], 'posting_date': ['<=', day]}, fields)
    for value in values:
        pending = value.get(I.STATE) in ('Cần xử lý', 'Đang xử lý')
        missing_original = originals and value.get('kh_aph_mau_giao_nhan') == 1 and not value.get(S.ORIGINAL_AT)
        missing = not value.get(S.FILE) or not value.get(S.ACTOR) or missing_original
        if getdate(value.posting_date) != getdate(day) and not pending and not (missing and value.docstatus == 1 and not value.is_return):
            continue
        state = 'Đã hủy' if value.docstatus == 2 else 'Trả hàng' if value.is_return else value.kh_aph_delivery_state or 'Đã xuất'
        if not value.is_return and value.docstatus == 1:
            state += ' / ' + ('Thiếu bản ký' if not value.get(S.FILE) else 'Có tệp chưa đối chiếu' if not value.get(S.ACTOR) else 'Đã đối chiếu bản ký')
            if originals and value.get('kh_aph_mau_giao_nhan') == 1:
                state += ' / ' + ('Thiếu giấy gốc' if missing_original else 'Đã nhận giấy gốc')
        if pending:
            state += ' / ' + value.get(I.STATE)
        doc = frappe.get_doc('Delivery Note', value.name)
        doc.check_permission('read')
        for item in doc.items:
            if item.warehouse:
                frappe.get_doc('Warehouse', item.warehouse).check_permission('read')
            result.append(_row('Hàng / hồ sơ', state, doctype='Delivery Note', document=value.name,
                item_code=item.item_code, warehouse=item.warehouse, quantity=item.stock_qty, uom=item.stock_uom,
                bags=item.get('kh_aph_bags'), assignee=value.get(I.ASSIGNEE), due_date=value.get(I.DUE)))
    return result


def _exceptions(company, day):
    result = []
    for dt in ('Payment Entry','Sales Invoice'):
        fields = ['name','docstatus','posting_date'] + (['payment_type','party_type'] if dt == 'Payment Entry' else ['is_return'])
        for value in rows(dt, {'company': company, 'posting_date': day, 'docstatus': ['in',[1,2]]}, fields):
            state = 'Hủy nguồn tiền/nợ' if value.docstatus == 2 else 'Hoàn tiền khách' if dt == 'Payment Entry' and value.payment_type == 'Pay' and value.party_type == 'Customer' else 'Hóa đơn trả/giảm' if dt == 'Sales Invoice' and value.is_return else None
            if state:
                result.append(_row('Ngoại lệ trong ngày', state, doctype=dt, document=value.name))
    return result


@frappe.whitelist()
def review(company, day):
    if not F.enabled():
        frappe.throw('Bảng chốt ngày chưa được bật')
    C.guard(manager=True)
    F.guard()
    frappe.get_doc('Company', company).check_permission('read')
    day = str(getdate(day))
    if getdate(day) > getdate():
        frappe.throw('Không chốt ngày trong tương lai')
    result = _cash(company) + _cash_work(company) + _bank(company, day) + _debt(company, day) + _goods(company, day) + _exceptions(company, day)
    if len(result) > LIMIT:
        frappe.throw('Bảng vượt5.000 dòng; không trả kết quả thiếu')
    for value in result:
        value['overdue'] = bool(value.get('due_date') and getdate(value['due_date']) < getdate() and value.get('status') != 'Đã đối chiếu')
    return {'checked_at': now_datetime(), 'rows': result}
