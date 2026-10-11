"""Opt-in global customer warnings. Never changes payments or MISA."""
import frappe
from frappe.utils import cint
from kh_aph.global_credit_rules import measure_credit

LIMIT_FIELD = 'kh_aph_global_credit_limit'
FLAG_FIELD = 'kh_aph_global_credit_over'

def balance_for(customer):
    # Receivable GL includes verified-customer unallocated receipts once, already
    # in debit-credit. Never subtract Payment Entry again or use anonymous money.
    return frappe.db.sql('''
        SELECT COALESCE(SUM(gl.debit-gl.credit),0)
        FROM `tabGL Entry` gl
        JOIN `tabCompany` co ON co.name=gl.company
        JOIN `tabAccount` a ON a.name=gl.account AND a.company=gl.company
        WHERE gl.party_type='Customer' AND gl.party=%s
          AND gl.is_cancelled=0 AND co.abbr IN ('APH','VH','MK','TL')
          AND a.account_type='Receivable'
    ''', customer)[0][0]

def evaluate(customer, additional):
    limit = frappe.db.get_value('Customer', customer, LIMIT_FIELD) or 0
    return measure_credit(balance_for(customer), additional, limit)

def warn(doc, additional):
    if not cint(frappe.conf.get('kh_aph_global_credit_warning')):
        return None
    result = evaluate(doc.customer, additional)
    if doc.meta.has_field(FLAG_FIELD):
        doc.set(FLAG_FIELD, int(result['over_limit']))
    if result['over_limit']:
        frappe.msgprint('Khách vượt hạn mức công nợ chung APH/VH/MK/TL; kế toán cần xem xét.',
                        title='Hạn mức chung', indicator='orange')
    return result

def validate_shared(doc):
    return warn(doc, doc.net_total)

def validate_delivery(doc, method=None):
    if not doc.customer or doc.is_return or cint(doc.docstatus)==2:
        return
    # Avoid counting a previously posted shipment again when updating it.
    submitted = doc.name and frappe.db.get_value('Delivery Note', doc.name, 'docstatus') == 1
    return warn(doc, 0 if submitted else doc.grand_total)
