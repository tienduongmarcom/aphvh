"""In khoản thực nhận bằng mẫu thu đang dùng; chỉ tạo dữ liệu trình bày, không tạo PE/JE."""
import frappe
from kh_aph.funds_rules import money


def receipt_html(receipt):
    from kh_aph.funds import require, company
    require()
    receipt.check_permission('read')
    receipt.check_permission('print')
    company(receipt.company)
    if receipt.docstatus != 1 or not receipt.journal_entry or money(receipt.amount)<=0:
        frappe.throw('Chọn khoản thực nhận đã ghi sổ để in phiếu thu')
    for name in (receipt.bank_account, receipt.holding_account):
        account=frappe.get_doc('Account',name)
        account.check_permission('read')
        if account.company!=receipt.company or account.is_group or account.account_currency!='VND':
            frappe.throw('Tài khoản thực nhận/giữ tiền chưa khớp đơn vị và VND')
    journal=frappe.get_doc('Journal Entry',receipt.journal_entry)
    journal.check_permission('read')
    if journal.docstatus!=1 or journal.company!=receipt.company or journal.get('kh_aph_funds_receipt')!=receipt.name:
        frappe.throw('Khoản thực nhận chưa khớp chứng từ ghi tiền gốc')
    totals={receipt.bank_account:money(0),receipt.holding_account:money(0)}
    for row in journal.accounts:
        value=money(row.debit_in_account_currency)-money(row.credit_in_account_currency)
        if row.account not in totals and value:
            frappe.throw('Chứng từ thực nhận có đối ứng khác; kế toán đối chiếu trước khi in')
        if row.account in totals:
            totals[row.account]+=value
    if (totals[receipt.bank_account]!=money(receipt.amount)
            or totals[receipt.holding_account]!=-money(receipt.amount)):
        frappe.throw('Số tiền thực nhận không khớp bút toán đã ghi; không in số tự suy')
    customer=None
    if receipt.customer:
        customer=frappe.get_doc('Customer',receipt.customer)
        customer.check_permission('read')
    # Đây là view-model của khoản thực nhận R, KHÔNG giả lập/chèn Payment Entry.
    view=frappe._dict(doctype=receipt.doctype,name=receipt.name,company=receipt.company,docstatus=1,
        owner=receipt.owner,posting_date=receipt.posting_date,payment_type='Receive',party_type='Customer',
        party=receipt.customer or '',party_name=customer.customer_name if customer else '',
        paid_from=receipt.holding_account,paid_to=receipt.bank_account,paid_amount=receipt.amount,
        received_amount=receipt.amount,paid_from_account_currency='VND',paid_to_account_currency='VND',
        source_exchange_rate=1,target_exchange_rate=1,references=[],custom_remarks=1,
        remarks=receipt.reason,reference_no=receipt.external_reference)
    from kh_aph.print_utils import kh_aph_no_co
    template=frappe.get_doc('Print Format','Phiếu thu chi')
    # Nợ/Có lấy từ JE gốc, không query GL bằng tên khoản thực nhận hoặc in toàn bộ JE.
    return frappe.render_template('<style>'+template.css+'</style>'+template.html,
        {'doc':view,'kh_aph_no_co':lambda doc:kh_aph_no_co(journal)})


@frappe.whitelist()
def print_receipt(receipt):
    from kh_aph.funds import require
    require()
    return {'html':receipt_html(frappe.get_doc('APH Funds Receipt',receipt))}
