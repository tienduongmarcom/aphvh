"""0.2.1: bản 0.2.0 tạo quyền cho vai trò nhà máy nhưng để giá trị mặc định read=1, export=1
(xuất Excel, đọc cả Tài khoản/Trung tâm chi phí/Dự án). Đặt lại đúng bảng quyền trong install.py.

Chỉ sửa các dòng quyền của vai trò "Kế toán nhà máy APH" đã có; dòng chưa có sẽ do after_migrate tạo.
"""

import frappe

from aphvh.constants import ROLE_FACTORY
from aphvh.install import ROLE_FACTORY_PERMS, set_factory_role_rights


def execute():
    for doctype, rights in ROLE_FACTORY_PERMS.items():
        if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": ROLE_FACTORY, "permlevel": 0}):
            set_factory_role_rights(doctype, rights)
