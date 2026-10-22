"""Hồ sơ ký đối soát bất biến; chỉ đọc sổ chuẩn, không tạo khoản thu/chi hoặc công nợ."""
from contextvars import ContextVar
import hashlib
import json
import re

import frappe
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, today
from kh_aph.constants import ROLE_NO_COST
from kh_aph.debt_statement_rules import amount, snapshot

DT = 'Bien ban doi soat no'
FLAG = 'kh_aph_quan_tri'
ROLES = {'Kế toán bán hàng', 'Accounts User', 'Accounts Manager', 'System Manager'}
_INTERNAL = ContextVar('debt_statement_internal', default=None)
SOURCES = {'Delivery Note', 'Sales Invoice', 'Payment Entry', 'Journal Entry'}


def enabled():
    return cint(frappe.conf.get(FLAG))


def _allowed(user=None):
    user = user or frappe.session.user
    if not enabled() or user == 'Guest':
        return False
    roles = set(frappe.get_roles(user))
    return bool(ROLE_NO_COST not in roles
                and (user == 'Administrator' or roles & ROLES))


def _limited_dimensions(user=None):
    # API được giao quyền tổng hợp nợ theo Company/Customer, không mở dữ liệu tài chính
    # ngoài phạm vi tài khoản/trung tâm chi phí/dimension riêng của một người dùng.
    from frappe.permissions import get_user_permissions
    restrictions = get_user_permissions(user or frappe.session.user)
    dimensions = {'Account', 'Cost Center', 'Project'}
    dimensions.update(frappe.get_all('Accounting Dimension', pluck='document_type'))
    dimensions -= {'Company', 'Customer'}
    return any(key in dimensions and values for key, values in restrictions.items())


def _guard():
    if not _allowed():
        frappe.throw('Cần quyền kế toán được xem đối soát công nợ', frappe.PermissionError)
    if _limited_dimensions():
        frappe.throw('Phạm vi tài chính còn giới hạn theo tài khoản hoặc bộ phận; nhờ kế toán có đủ phạm vi lập bản đối soát', frappe.PermissionError)


def has_permission(doc=None, user=None, permission_type=None, ptype=None, **kwargs):
    user = user or frappe.session.user
    if not _allowed(user) or _limited_dimensions(user) or (ptype or permission_type) in ('delete', 'cancel', 'submit'):
        return False
    if not doc or doc.is_new():
        return True
    try:
        companies = json.loads(doc.scope)
    except (ValueError, TypeError):
        return False
    if not isinstance(companies, list) or not companies:
        return False
    return (frappe.has_permission('Customer', 'read', doc=frappe.get_doc('Customer', doc.customer), user=user)
            and all(frappe.has_permission('Company', 'read', doc=frappe.get_doc('Company', name), user=user)
                    for name in companies))


def query_conditions(user=None):
    if not _allowed(user) or _limited_dimensions(user) or (user and user != frappe.session.user):
        return '1=0'
    companies = frappe.get_list('Company', pluck='name', limit_page_length=0)
    if not companies:
        return '1=0'
    allowed = frappe.db.escape(json.dumps(companies))
    return f'JSON_VALID(`tab{DT}`.`scope`) AND JSON_CONTAINS({allowed}, `tab{DT}`.`scope`)'


class Statement(Document):
    def validate(self):
        if _INTERNAL.get() != id(self):
            frappe.throw('Dùng thao tác lập biên bản hoặc lưu bản ký để giữ đúng số đã cấp', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Giữ biên bản đã cấp và giấy ký; lập bản bổ sung khi số liệu thay đổi')

    def before_rename(self, *args, **kwargs):
        frappe.throw('Không đổi mã biên bản đã cấp')


def schema():
    if not enabled():
        return
    frappe.reload_doc('kh_aph', 'doctype', 'bien_ban_doi_soat_no')
    frappe.reload_doc('kh_aph', 'print_format', 'doi_soat_theo_luot')
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    current = frappe.get_meta(DT).get('default_print_format')
    if not current or current == 'Standard':
        make_property_setter(DT, None, 'default_print_format', 'Biên bản đối soát theo lượt', 'Data', for_doctype=True)
    from frappe.permissions import add_permission, update_permission_property
    if frappe.db.exists('Role', 'Kế toán bán hàng'):
        add_permission(DT, 'Kế toán bán hàng', 0)
        for permission in ('read', 'create', 'write', 'print', 'report'):
            update_permission_property(DT, 'Kế toán bán hàng', 0, permission, 1)


def _scope(customer, raw):
    customer_doc = frappe.get_doc('Customer', customer)
    customer_doc.check_permission('read')
    values = frappe.parse_json(raw) if isinstance(raw, str) else raw
    if not isinstance(values, list) or not 1 <= len(values) <= 10 or any(not isinstance(v, str) for v in values):
        frappe.throw('Chọn phạm vi đơn vị để đối soát')
    companies = sorted(set(values))
    allowed = set(frappe.get_list('Company', filters={'name': ['in', companies]}, pluck='name', limit_page_length=0))
    if allowed != set(companies):
        frappe.throw('Chưa được xem đủ các đơn vị đã chọn', frappe.PermissionError)
    for company in companies:
        co = frappe.get_doc('Company', company)
        co.check_permission('read')
        if co.default_currency != 'VND':
            frappe.throw('Biên bản này dùng các đơn vị hạch toán VND; ngoại tệ cần đối chiếu riêng')
    return customer_doc, companies


def _source_keys(raw):
    rows = frappe.parse_json(raw) if isinstance(raw, str) else raw
    if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
        frappe.throw('Chọn từ1 đến20 chứng từ đã ghi của lượt cần ký')
    keys = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'doctype', 'name'}
                or not isinstance(row['doctype'], str) or row['doctype'] not in SOURCES
                or not isinstance(row['name'], str) or not row['name'] or len(row['name']) > 140):
            frappe.throw('Nguồn đối soát không hợp lệ')
        keys.add((row['doctype'], row['name']))
    return sorted(keys)


def _sources(customer, companies, keys):
    selected, documents = set(), {}
    for key in keys:
        doc = frappe.get_doc(*key)
        doc.check_permission('read')
        if doc.docstatus != 1 or doc.company not in companies or getdate(doc.posting_date) > getdate(today()):
            frappe.throw('Chọn chứng từ đã ghi sổ, trong phạm vi và không ở ngày tương lai')
        if key[0] in ('Delivery Note', 'Sales Invoice'):
            valid_customer = doc.customer == customer
        elif key[0] == 'Payment Entry':
            valid_customer = doc.party_type == 'Customer' and doc.party == customer
        else:
            valid_customer = any(d.party_type == 'Customer' and d.party == customer for d in doc.accounts)
        if not valid_customer:
            frappe.throw('Mọi chứng từ của lượt phải đúng khách đang đối soát')
        documents[key] = doc
        if key[0] != 'Delivery Note':
            selected.add(key)
    delivery_notes = {name for dt, name in documents if dt == 'Delivery Note'}
    for name in sorted(delivery_notes):
        parents = frappe.get_all('Sales Invoice Item', filters={'delivery_note': name}, pluck='parent')
        invoices = [frappe.get_doc('Sales Invoice', parent) for parent in sorted(set(parents))]
        invoices = [doc for doc in invoices if doc.docstatus == 1]
        if not invoices:
            frappe.throw('Phiếu giao chưa có chứng từ ghi nợ còn hiệu lực; đối chiếu trước khi lập biên bản')
        for invoice in invoices:
            invoice.check_permission('read')
            if (invoice.company not in companies or invoice.customer != customer
                    or any(d.delivery_note not in delivery_notes for d in invoice.items)):
                frappe.throw('Hóa đơn gộp nhiều phiếu: chọn đầy đủ phiếu hoặc chọn trực tiếp hóa đơn để đối chiếu')
            selected.add(('Sales Invoice', invoice.name))
    return selected, documents


def _lock_sources(customer, companies, selected, documents):
    current = {}
    for key in sorted(set(selected) | set(documents)):
        source = frappe.get_doc(*key, for_update=True)
        source.check_permission('read')
        same_customer = (source.customer == customer if key[0] in ('Sales Invoice', 'Delivery Note') else
                         source.party_type == 'Customer' and source.party == customer if key[0] == 'Payment Entry' else
                         any(row.party_type == 'Customer' and row.party == customer for row in source.accounts))
        if source.docstatus != 1 or source.company not in companies or not same_customer:
            frappe.throw('Chứng từ nguồn vừa đổi hoặc hủy; tải lại lượt cần đối soát trước khi cấp bộ giấy')
        if key in documents:
            current[key] = source
    return current


def _figures(customer, companies, selected, documents):
    from kh_aph.cash_closing import enabled as closing_enabled, lock_ledger
    if not closing_enabled():
        frappe.throw('Chưa bật cấu hình đối chiếu tiền đồng thời; quản trị viên hoàn tất cấu hình trước khi lập biên bản')
    for company in companies:
        lock_ledger(frappe._dict(company=company))
    # Current read sau khóa sổ; không dùng bản nguồn từ read-view trước lúc chờ khóa.
    documents = _lock_sources(customer, companies, selected, documents)
    # Facade tổng hợp tối thiểu, đã kiểm vai trò/Customer/Company và phạm vi dimensions.
    rows = frappe.db.sql('''SELECT company, voucher_type, voucher_no, amount FROM `tabPayment Ledger Entry`
        WHERE party_type='Customer' AND party=%s AND company IN %s AND delinked=0 AND posting_date<=%s
        ORDER BY company, name LIMIT 10001 FOR UPDATE''', (customer, tuple(companies), today()), as_dict=True)
    if len(rows) > 10000:
        frappe.throw('Khách vượt10.000 dòng sổ; cần đối chiếu tập đầy đủ, không cắt bớt số liệu')
    result = snapshot(companies, rows, selected)
    from kh_aph.funds_rules import position
    funds = {co: {'company': co, 'reserved': amount(0), 'available': amount(0),
                  'unallocated_received': amount(0), 'unallocated_paid': amount(0)} for co in companies}
    receipts = frappe.db.sql('''SELECT name, company, amount FROM `tabAPH Funds Receipt`
        WHERE customer=%s AND company IN %s AND docstatus=1 ORDER BY name LIMIT 1001 FOR UPDATE''',
        (customer, tuple(companies)), as_dict=True)
    if len(receipts) > 1000:
        frappe.throw('Khách vượt1.000 khoản tiền giữ; cần đối chiếu tập đầy đủ')
    for receipt in receipts:
        history = frappe.db.sql('''SELECT name, action_type, amount, source_reservation
            FROM `tabAPH Funds Action` WHERE receipt=%s AND docstatus=1 ORDER BY name FOR UPDATE''',
            receipt.name, as_dict=True)
        state = position(receipt.amount, history)
        funds[receipt.company]['reserved'] += state['reserved']
        funds[receipt.company]['available'] += state['available']
    payments = frappe.db.sql('''SELECT company, payment_type, unallocated_amount FROM `tabPayment Entry`
        WHERE party_type='Customer' AND party=%s AND company IN %s AND docstatus=1 AND posting_date<=%s
        AND unallocated_amount>0 ORDER BY name FOR UPDATE''', (customer, tuple(companies), today()), as_dict=True)
    for payment in payments:
        if payment.payment_type in ('Receive', 'Pay'):
            key = 'unallocated_received' if payment.payment_type == 'Receive' else 'unallocated_paid'
            funds[payment.company][key] += amount(payment.unallocated_amount)
    result['funds'] = [{key: str(value) if key != 'company' else value for key, value in row.items()}
                       for row in funds.values()]
    return result, documents


@frappe.whitelist(methods=['POST'])
def create(customer, companies, vouchers, request_id, supersedes=None):
    _guard()
    if not isinstance(request_id, str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}', request_id):
        frappe.throw('Thiếu mã lượt lập biên bản; mở lại thao tác')
    customer_doc, scope = _scope(customer, companies)
    keys = _source_keys(vouchers)
    identity = json.dumps([customer, scope, keys, supersedes or ''], sort_keys=True)
    signature = hashlib.sha256(identity.encode()).hexdigest()
    existing = frappe.db.get_value(DT, {'request_id': request_id}, ['name', 'request_hash'], as_dict=True)
    if existing:
        doc = frappe.get_doc(DT, existing.name)
        doc.check_permission('read')
        if existing.request_hash != signature:
            frappe.throw('Mã lượt đã dùng cho nội dung khác; mở lại thao tác')
        return {'name': doc.name, 'file_url': doc.bundle_file, 'reused': True}
    selected, sources = _sources(customer, scope, keys)
    if supersedes:
        previous = frappe.get_doc(DT, supersedes)
        previous.check_permission('read')
        if previous.customer != customer or sorted(json.loads(previous.scope)) != scope:
            frappe.throw('Bản bổ sung cần cùng khách và phạm vi với bản trước')
    figures, sources = _figures(customer, scope, selected, sources)
    from kh_aph.customer_identity import details
    identity = details([customer_doc])[customer]
    figures.update(customer_name=customer_doc.customer_name, customer=customer,
                   prepared_by=frappe.utils.get_fullname(frappe.session.user),
                   tax_id=customer_doc.tax_id or '',
                   phone=identity['mobile_no'] if not identity['mobile_no'].startswith('Không có quyền') else '',
                   address=identity['primary_address'] if not identity['primary_address'].startswith('Không có quyền') else '',
                   sources=[{'doctype': dt, 'name': name} for dt, name in sorted(sources)])
    doc = frappe.get_doc({'doctype': DT, 'customer': customer, 'scope': json.dumps(scope),
        'payload': json.dumps(figures, ensure_ascii=False), 'snapshot_at': now_datetime(), 'status': 'Chờ ký',
        'request_id': request_id, 'request_hash': signature, 'supersedes': supersedes})
    token = _INTERNAL.set(id(doc))
    try:
        doc.insert()
        from kh_aph.statement_pdf import make_bundle
        doc.bundle_file = make_bundle(doc, sources)
        doc.save()
    finally:
        _INTERNAL.reset(token)
    return {'name': doc.name, 'file_url': doc.bundle_file, 'reused': False}


def print_data(doc):
    doc.check_permission('read')
    if not has_permission(doc):
        frappe.throw('Chưa đủ phạm vi xem bản đối soát này', frappe.PermissionError)
    return json.loads(doc.payload)


@frappe.whitelist(methods=['POST'])
def record_signature(name, modified, signer, authority, authorization=None, file_url=None, location=None):
    _guard()
    frappe.db.sql(f'SELECT name FROM `tab{DT}` WHERE name=%s FOR UPDATE', name)
    doc = frappe.get_doc(DT, name, for_update=True)
    doc.check_permission('read'); doc.check_permission('write')
    if not isinstance(signer, str) or not signer.strip() or len(signer) > 140 or re.search(r'[<>\x00-\x1f]', signer) or authority not in ('Khách hàng', 'Được ủy quyền ký nợ'):
        frappe.throw('Ghi người ký và đúng tư cách ký công nợ')
    if any(value is not None and not isinstance(value, str) for value in (authorization, file_url, location)):
        frappe.throw('Thông tin bản ký không hợp lệ')
    authorization, location = (authorization or '').strip(), (location or '').strip()
    if any(re.search(r'[<>]', value) for value in (authorization, location)) or re.search(r'[\x00-\x1f]', location):
        frappe.throw('Ghi căn cứ và vị trí lưu bằng chữ, không dùng thẻ hoặc ký tự điều khiển')
    if authority == 'Được ủy quyền ký nợ' and not (authorization or '').strip():
        frappe.throw('Ghi căn cứ khách giao riêng quyền ký công nợ; quyền lấy hàng không thay quyền ký nợ')
    if len(authorization) > 1000 or len(location) > 140:
        frappe.throw('Căn cứ ký hoặc vị trí lưu quá dài')
    if not file_url and not location:
        frappe.throw('Ghi vị trí giấy gốc đang có hoặc đính bản ký riêng tư')
    if file_url and (not file_url.startswith('/private/files/') or not frappe.db.exists('File',
            {'file_url': file_url, 'is_private': 1, 'attached_to_doctype': DT, 'attached_to_name': name})):
        frappe.throw('Bản ký phải là tệp riêng tư đính kèm đúng biên bản')
    if doc.signed_by and (doc.signer != signer.strip() or doc.signature_authority != authority
            or (doc.authorization or '') != (authorization or '').strip()
            or (doc.signed_file and file_url and doc.signed_file != file_url)):
        frappe.throw('Giữ bản ký và người ký đã lưu; lập bản bổ sung khi cần thay đổi')
    if (doc.signed_by and (not file_url or doc.signed_file == file_url)
            and (not location or doc.original_location == location.strip())):
        return {'name': doc.name, 'status': doc.status}
    if str(doc.modified) != str(modified):
        frappe.throw('Biên bản đã thay đổi; tải lại trước khi lưu bản ký', frappe.TimestampMismatchError)
    token = _INTERNAL.set(id(doc))
    try:
        doc.signer, doc.signature_authority = signer.strip(), authority
        doc.authorization = (authorization or '').strip()
        if not doc.signed_by:
            doc.signed_by, doc.signed_at = frappe.session.user, now_datetime()
        if file_url:
            doc.signed_file = file_url
        if location:
            doc.original_location = location.strip()
            if not doc.original_by:
                doc.original_by, doc.original_at = frappe.session.user, now_datetime()
        doc.status = 'Đã nhận giấy gốc' if doc.original_at else 'Đã nhận bản ký'
        doc.save()
    finally:
        _INTERNAL.reset(token)
    return {'name': doc.name, 'status': doc.status}


def file_in_use(url):
    return enabled() and frappe.db.exists('DocType', DT) and (frappe.db.exists(DT, {'bundle_file': url})
        or frappe.db.exists(DT, {'signed_file': url}))


def protect_file_update(doc, method=None):
    old = doc.get_doc_before_save()
    if old and old.file_url and file_in_use(old.file_url) and (doc.get('content') or any(
            doc.get(key) != old.get(key) for key in ('file_url', 'is_private', 'attached_to_doctype', 'attached_to_name'))):
        frappe.throw('Giữ nguyên tệp của bộ giấy hoặc bản ký đã lưu')


class StatementFileMixin:
    def on_trash(self):
        if self.file_url and file_in_use(self.file_url):
            frappe.throw('Tệp thuộc biên bản đã cấp; giữ để in lại và truy nguyên bản ký')
        return super().on_trash()
