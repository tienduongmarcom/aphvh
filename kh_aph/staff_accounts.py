"""Kế hoạch mã đăng nhập nội bộ; chỉ đối chiếu, không tạo User hoặc cấp quyền."""

ROSTER = (
    ('huong', 'Cô Hường', 'bán hàng'),
    ('hanh', 'Cô Hạnh', 'bán hàng và kho ngoài nhà máy'),
    ('dungktt', 'Dung', 'kế toán trưởng và mua trong nước'),
    ('lan', 'Lan', 'tổng hợp và thuế'),
    ('ha', 'Hà', 'tổng hợp và thuế'),
    ('trang', 'Trang', 'duyệt bán hàng và nhận tiền'),
    ('ninh', 'Ninh', 'xem điều hành và nhận tiền'),
    ('anh', 'Ánh', 'nhận tiền'),
    ('dungnm', 'Dũng', 'nhà máy, không xem giá vốn'),
)


def plan(existing):
    """Không nhận gần đúng theo họ tên; mã/email nội bộ có sẵn phải đối chiếu thủ công.

    .invalid là địa chỉ kỹ thuật cho trường email bắt buộc của User, không phải
    hộp thư thật. Không tái sử dụng tài khoản trùng, kể cả tài khoản đã vô hiệu.
    """
    existing = list(existing)
    result = []
    for username, full_name, duty in ROSTER:
        email = username + '@nhansu.invalid'
        matches = [row for row in existing if
                   str(row.get('username') or '').strip().casefold() == username or
                   str(row.get('name') or '').strip().casefold() == email or
                   str(row.get('email') or '').strip().casefold() == email]
        result.append({'username': username, 'email': email, 'full_name': full_name,
                       'duty': duty, 'send_welcome_email': 0,
                       'status': 'can_doi_chieu' if matches else 'chua_co',
                       'existing': [row.get('name') for row in matches]})
    return result


def xem_ke_hoach():
    """Chạy bằng bench hoặc console quản trị; không công khai API danh sách nhân sự."""
    import frappe
    from kh_aph.ux_task import enabled
    if not enabled():
        frappe.throw('Chưa bật giao diện theo công việc')
    if frappe.session.user != 'Administrator' and 'System Manager' not in frappe.get_roles():
        frappe.throw('Chỉ quản trị được đối chiếu tài khoản nhân sự', frappe.PermissionError)
    frappe.has_permission('User', ptype='read', throw=True)
    rows = frappe.get_all('User', fields=['name', 'email', 'username'], limit_page_length=0)
    return {'chay_thu': True, 'tao_tai_khoan': False, 'cap_quyen': False, 'nhan_su': plan(rows)}
