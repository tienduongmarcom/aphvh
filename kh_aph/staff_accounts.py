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


def profiles():
    from kh_aph.constants import ROLE_SALES, ROLE_HN_STOCK, ROLE_FACTORY, ROLE_NO_COST
    from kh_aph.staff_scope import FULL_CUSTOMER_DEBT_ROLE
    sales=['Kế toán bán hàng','Sales User',ROLE_SALES]
    return {
        'huong': {'roles':sales,'workspace':'Bán hàng'},
        'hanh': {'roles':sales+['Stock User',ROLE_HN_STOCK,FULL_CUSTOMER_DEBT_ROLE], 'workspace':'Kho vận','warehouses':'cua_hang'},
        'dungktt': {'roles':['Accounts Manager','Accounts User','Purchase Manager','Purchase User','Stock Manager','Stock User','Sales User','Item Manager'],'workspace':'Tiền và kế toán'},
        'lan': {'roles':['Accounts User'],'workspace':'Tiền và kế toán'},
        'ha': {'roles':['Accounts User'],'workspace':'Tiền và kế toán'},
        'trang': {'roles':sales+['Duyệt khách rủi ro','Nhận bàn giao tiền'],'workspace':'Bán hàng'},
        'ninh': {'roles':['Xem báo cáo điều hành','Nhận bàn giao tiền'],'workspace':'Tiền và kế toán'},
        'anh': {'roles':['Nhận bàn giao tiền'],'workspace':'Tiền và kế toán'},
        'dungnm': {'roles':[ROLE_FACTORY,ROLE_NO_COST,'Stock User'],'workspace':'Nhà máy','warehouses':'nha_may'},
    }


def chuan_bi(duong_dan, xac_nhan_site=None, chay_that=0):
    """Mặc định xem kế hoạch. Ghi thật chỉ chuẩn bị User VÔ HIỆU, chưa cho đăng nhập.

    Không đổi quyền tài khoản sẵn có, không đặt mật khẩu/gửi email hoặc bật cơ chế
    đăng nhập toàn hệ thống. Quản trị thiết lập mật khẩu và kích hoạt sau nghiệm thu.
    """
    import frappe
    from frappe.utils import cint
    from kh_aph.khach_hang import doc_cau_hinh
    from kh_aph.staff_scope import STOCK_SCOPE_DOCTYPES, warehouse_plan
    from kh_aph.ux_task import enabled
    if not enabled() or frappe.session.user != 'Administrator':
        frappe.throw('Quản trị chuẩn bị tài khoản sau khi bật giao diện theo công việc', frappe.PermissionError)
    write=bool(cint(chay_that))
    if write and xac_nhan_site != frappe.local.site:
        frappe.throw('Cần xác nhận đúng tên site trước khi chuẩn bị nhân sự')
    config=doc_cau_hinh(duong_dan)
    companies={row['abbr']:frappe.db.get_value('Company',{'abbr':row['abbr']},'name') for row in config['cong_ty']}
    if not all(companies.values()):frappe.throw('Chưa có đủ đơn vị trong cấu hình nhân sự')
    company_abbr={name:abbr for abbr,name in companies.items()}
    warehouses=frappe.get_all('Warehouse',filters={'company':['in',list(company_abbr)]},
        fields=['name','company','parent_warehouse','is_group','disabled','warehouse_type'])
    warehouse_rows=[{**row,'company_abbr':company_abbr[row['company']]} for row in warehouses]
    stock=warehouse_plan(config,warehouse_rows)
    if stock['chua_phan_loai']:
        frappe.throw('Cần phân loại địa điểm kho trước khi áp nhân sự: '+', '.join(stock['chua_phan_loai']))
    by_name={row['name']:row for row in warehouses}
    existing=frappe.get_all('User',fields=['name','email','username'],limit_page_length=0)
    entries=plan(existing);settings=profiles();prepared=[]
    marker='Chuẩn bị nhân sự dùng thử 23/10/2026'
    for entry in entries:
        profile=settings[entry['username']]
        missing=[role for role in profile['roles'] if not frappe.db.exists('Role',role)]
        if missing:frappe.throw('Chưa cài đủ vai trò: '+', '.join(missing))
        if not frappe.db.exists('Workspace',profile['workspace']):frappe.throw('Chưa có khu làm việc: '+profile['workspace'])
        whs=stock[profile['warehouses']] if profile.get('warehouses') else []
        if profile.get('warehouses') and not whs:frappe.throw('Chưa có phạm vi kho cho '+entry['username'])
        allowed_companies=sorted({by_name[name]['company'] for name in whs}) if entry['username']=='dungnm' else sorted(company_abbr)
        permissions=[{'allow':'Company','for_value':company,'apply_to_all_doctypes':1,'applicable_for':''} for company in allowed_companies]
        permissions += [{'allow':'Warehouse','for_value':name,'apply_to_all_doctypes':0,'applicable_for':dt}
                        for name in whs for dt in sorted(STOCK_SCOPE_DOCTYPES)]
        reuse=False
        if entry['existing']:
            if entry['existing']!=[entry['email']]:frappe.throw('Mã tài khoản đã có, cần đối chiếu thủ công: '+entry['username'])
            user=frappe.get_doc('User',entry['email'])
            current_roles={row.role for row in user.roles}
            own_batch=frappe.db.exists('Comment',{'reference_doctype':'User','reference_name':user.name,'comment_type':'Comment','content':marker})
            current_permissions=frappe.get_all('User Permission',filters={'user':user.name},
                fields=['allow','for_value','apply_to_all_doctypes','applicable_for'])
            key=lambda row:(row['allow'],row['for_value'],int(row['apply_to_all_doctypes']),row.get('applicable_for') or '')
            if (not own_batch or user.enabled or user.username!=entry['username'] or user.first_name!=entry['full_name'] or
                user.user_type!='System User' or current_roles!=set(profile['roles']) or user.default_workspace!=profile['workspace'] or
                sorted(map(key,current_permissions))!=sorted(map(key,permissions))):
                frappe.throw('Tài khoản đã đổi hoặc không thuộc lượt chuẩn bị; giữ nguyên để đối chiếu: '+entry['username'])
            reuse=True
        prepared.append({**entry,'roles':sorted(profile['roles']),'workspace':profile['workspace'],
                         'permissions':permissions,'enabled':0,'reused':reuse})
    if not write:
        return {'chay_thu':True,'nhan_su':prepared,'kho':stock,'dat_mat_khau':False,'kich_hoat':False,
                'dang_nhap_bang_ma_hien_tai':bool(cint(frappe.db.get_single_value('System Settings','allow_login_using_user_name')))}
    # Chuẩn bị cả lượt nguyên khối; lỗi không để lại một phần tài khoản/quyền.
    frappe.db.savepoint('chuan_bi_nhan_su')
    try:
        for row in prepared:
            if row['reused']:continue
            user=frappe.get_doc({'doctype':'User','email':row['email'],'username':row['username'],
                'first_name':row['full_name'],'enabled':0,'user_type':'System User','send_welcome_email':0,
                'language':'vi','default_workspace':row['workspace'],'roles':[{'role':role} for role in row['roles']]})
            user.flags.no_welcome_mail=True
            user.insert()
            if user.username!=row['username']:frappe.throw('Mã đăng nhập vừa bị trùng; hủy lượt chuẩn bị')
            user.add_comment('Comment',marker)
            for permission in row['permissions']:
                frappe.get_doc({'doctype':'User Permission','user':user.name,**permission}).insert()
        frappe.db.commit()
    except Exception:
        frappe.db.rollback(save_point='chuan_bi_nhan_su')
        raise
    return {'chay_thu':False,'nhan_su':[{'username':row['username'],'user':row['email'],'enabled':0,'reused':row['reused']} for row in prepared],
            'dat_mat_khau':False,'kich_hoat':False,'gui_email':False}
