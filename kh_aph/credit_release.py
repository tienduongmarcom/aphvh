"""Opt-in high-risk shipment guard and chief-accountant audit approvals."""
import frappe
from frappe.utils import cint,now_datetime
from kh_aph.global_credit import balance_for
from kh_aph.credit_release_rules import credit_increase,shipment_fingerprint
HIGH_RISK='kh_aph_credit_high_risk'
APPROVAL='APH Credit Release'

def _enabled():
    return cint(frappe.conf.get('kh_aph_high_risk_credit_guard'))

def _chief():
    if frappe.session.user != 'Administrator' and 'Accounts Manager' not in frappe.get_roles():
        frappe.throw('Chỉ Kế toán trưởng được duyệt bán chịu cho khách rủi ro cao',frappe.PermissionError)

def validate_customer(doc,method=None):
    if not _enabled():return
    old=doc.get_doc_before_save()
    for field in (HIGH_RISK, 'kh_aph_global_credit_limit'):
        if float(doc.get(field) or 0) != float(old.get(field) or 0 if old else 0):
            _chief()

def validate_release(doc,method=None):
    _chief()
    if not _enabled():frappe.throw('Phê duyệt rủi ro chưa được bật')
    if not doc.is_new():frappe.throw('Phiếu duyệt là dấu vết bất biến; tạo phiếu mới khi nội dung giao thay đổi')
    dn=frappe.get_doc('Delivery Note',doc.delivery_note);dn.check_permission('read')
    if dn.docstatus!=0 or dn.is_return:frappe.throw('Chỉ duyệt phiếu giao bán ở bản nháp')
    if not doc.reason or not doc.reason.strip():frappe.throw('Cần lý do phê duyệt')
    doc.customer=dn.customer;doc.company=dn.company
    doc.fingerprint=shipment_fingerprint(dn.as_dict())
    doc.amount=dn.grand_total;doc.approved_by=frappe.session.user;doc.approved_at=now_datetime()

@frappe.whitelist(methods=['POST'])
def approve(delivery_note,reason):
    _chief()
    if not _enabled():frappe.throw('Phê duyệt rủi ro chưa được bật')
    release=frappe.get_doc({'doctype':APPROVAL,'delivery_note':delivery_note,'reason':reason}).insert()
    return {'name':release.name,'approved_by':release.approved_by,'approved_at':release.approved_at,
            'fingerprint':release.fingerprint}

def before_submit_delivery(doc,method=None):
    if not _enabled() or doc.is_return:return
    # Serialize dispatch decisions for the same customer; request owns commit.
    frappe.db.sql('SELECT name FROM `tabCustomer` WHERE name=%s FOR UPDATE',doc.customer)
    if not cint(frappe.db.get_value('Customer',doc.customer,HIGH_RISK)):return
    if credit_increase(balance_for(doc.customer),doc.grand_total)<=0:return
    fingerprint=shipment_fingerprint(doc.as_dict())
    matched=frappe.db.sql('''SELECT name FROM `tabAPH Credit Release`
        WHERE delivery_note=%s AND customer=%s AND company=%s
          AND fingerprint=%s AND revoked_at IS NULL FOR UPDATE''',
        (doc.name,doc.customer,doc.company,fingerprint))
    if not matched:
        frappe.throw('Khách rủi ro cao: cần Kế toán trưởng phê duyệt đúng nội dung phiếu giao trước khi bán chịu',title='Chặn bán chịu')


@frappe.whitelist(methods=['POST'])
def revoke(approval, reason):
    _chief()
    if not _enabled():frappe.throw('Phê duyệt rủi ro chưa được bật')
    if not reason or not reason.strip():frappe.throw('Cần lý do thu hồi')
    release=frappe.get_doc(APPROVAL,approval);release.check_permission('read')
    # Lock in the same order as the dispatch guard, preventing a revoke race.
    frappe.db.sql('SELECT name FROM `tabCustomer` WHERE name=%s FOR UPDATE',release.customer)
    frappe.db.sql('SELECT name FROM `tabAPH Credit Release` WHERE name=%s FOR UPDATE',release.name)
    release.reload()
    if frappe.db.get_value('Delivery Note',release.delivery_note,'docstatus') != 0:
        frappe.throw('Chỉ thu hồi phê duyệt trước khi xác nhận giao; không tự đảo chứng từ đã giao')
    if release.get('revoked_at'):
        return {'name':release.name,'revoked_by':release.revoked_by,'revoked_at':release.revoked_at}
    when=now_datetime()
    frappe.db.set_value(APPROVAL,release.name,{
        'revoked_by':frappe.session.user,'revoked_at':when,'revocation_reason':reason.strip()})
    return {'name':release.name,'revoked_by':frappe.session.user,'revoked_at':when}


def before_submit_invoice(doc, method=None):
    """Direct invoices must not bypass a high-risk shipment approval.

    Generated invoices retain the approved DN path. Covered prepaid shipments
    and credit notes do not increase net debt, so need no extra credit release.
    """
    if not _enabled() or float(doc.grand_total or 0) <= 0:return
    frappe.db.sql('SELECT name FROM `tabCustomer` WHERE name=%s FOR UPDATE',doc.customer)
    if not cint(frappe.db.get_value('Customer',doc.customer,HIGH_RISK)):return
    if credit_increase(balance_for(doc.customer),doc.grand_total)<=0:return
    sources={row.delivery_note for row in doc.items if row.delivery_note}
    if not sources or any(not row.delivery_note for row in doc.items):
        frappe.throw('Khách rủi ro cao: hóa đơn tăng công nợ phải gắn phiếu giao đã được duyệt; không tạo trực tiếp để bỏ qua phê duyệt',title='Chặn bán chịu')
    for name in sources:
        dn=frappe.get_doc('Delivery Note',name)
        if dn.docstatus!=1 or dn.customer!=doc.customer or dn.company!=doc.company:
            frappe.throw('Khách rủi ro cao: phiếu giao trên hóa đơn không khớp khách/company hoặc chưa xác nhận')
        matched=frappe.db.sql("""SELECT name FROM `tabAPH Credit Release`
            WHERE delivery_note=%s AND customer=%s AND company=%s
              AND fingerprint=%s AND revoked_at IS NULL FOR UPDATE""",
            (name,doc.customer,doc.company,shipment_fingerprint(dn.as_dict())))
        if not matched:
            frappe.throw('Khách rủi ro cao: hóa đơn chưa có phê duyệt còn hiệu lực cho phiếu giao')
