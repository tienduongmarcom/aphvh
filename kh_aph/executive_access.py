"""Quyền xem điều hành, tách khỏi quyền khóa kỳ và sửa chứng từ."""
import frappe
from frappe.utils import cint

ROLE = 'Xem báo cáo điều hành'
REPORTS = ('Lai gop quan tri', 'Dong tien 7 30 ngay')
READ_DOCTYPES = ('Company', 'Customer', 'Supplier', 'Item', 'Item Group', 'Warehouse',
                 'Sales Order', 'Sales Invoice', 'Account', 'Cost Center', 'GL Entry', 'APH Khe uoc vay')


def guard():
    from kh_aph import quan_tri as K
    K.can_quyen(K.VAI_TRO_XEM | {ROLE})
    if frappe.session.user != 'Administrator' and ROLE in frappe.get_roles():
        # Báo cáo hiện tổng hợp theo Company. Không giả vờ áp được giới hạn dòng
        # Customer/Item/Warehouse vào SQL tổng hợp; hồ sơ hẹp phải dùng báo cáo khác.
        permissions = frappe.get_all('User Permission', filters={'user': frappe.session.user},
                                     fields=['allow'])
        if any(row.allow != 'Company' for row in permissions):
            frappe.throw('Hồ sơ có giới hạn chi tiết; cần đối chiếu phạm vi trước khi xem báo cáo điều hành',
                         frappe.PermissionError)


def schema():
    """Bộ cài tường minh; không gán vai trò cho người dùng và không tự chạy migrate."""
    if not cint(frappe.conf.get('kh_aph_quan_tri')):
        return
    if frappe.session.user != 'Administrator':
        frappe.throw('Quản trị thực hiện cài quyền điều hành', frappe.PermissionError)
    from frappe.permissions import add_permission, update_permission_property
    if not frappe.db.exists('Role', ROLE):
        frappe.get_doc({'doctype':'Role','role_name':ROLE,'desk_access':1}).insert()
    for dt in READ_DOCTYPES:
        add_permission(dt, ROLE, 0)
        for permission in ('read', 'report'):
            update_permission_property(dt, ROLE, 0, permission, 1, validate=False)
    # Report chuẩn không được save ngoài import/developer mode ở Frappe16.52.
    # Cài đúng hai Report của app, giữ mọi vai trò cũ và khôi phục context ngay.
    from frappe.core.doctype.custom_role.custom_role import get_custom_allowed_roles
    for name in REPORTS:
        custom = get_custom_allowed_roles('report', name)
        if custom and ROLE not in custom:
            frappe.throw('Báo cáo có quyền tùy chỉnh riêng cần đối chiếu: ' + name)
        report = frappe.get_doc('Report', name)
        if report.module != 'Kh Aph' or report.report_type != 'Script Report':
            frappe.throw('Sai nguồn báo cáo điều hành: ' + name)
        if not any(row.role == ROLE for row in report.roles):
            report.append('roles', {'role': ROLE})
            previous = frappe.flags.get('in_import')
            try:
                frappe.flags.in_import = True
                report.save()
            finally:
                frappe.flags.in_import = previous
