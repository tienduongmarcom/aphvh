"""0.7.0: bỏ chữ "APH" khỏi tên vai trò, mẫu in, báo cáo để dùng chung cho nhiều khách (lõi 9xLab).

Chạy TRƯỚC khi đồng bộ model (pre_model_sync): đổi tên bản ghi cũ sang tên mới để lúc đồng bộ file, Frappe cập
nhật đúng bản ghi đó thay vì tạo bản trùng. Đổi tên bằng rename_doc nên mọi liên kết (người dùng có vai trò, quyền
DocPerm / Custom DocPerm, vai trò của báo cáo, liên kết workspace) đi theo. Các giá trị lưu dạng chữ (mẫu in mặc định
trong Property Setter) đổi bằng tay. Chạy lại an toàn: đã có tên mới thì gộp (vai trò) hoặc bỏ bản cũ (mẫu in, báo cáo).
"""

import frappe

VAI_TRO = {
    "Kế toán nhà máy APH": "Kế toán nhà máy",
    "Nhân viên bán hàng APH": "Nhân viên bán hàng",
    "Thủ kho Hà Nội APH": "Thủ kho bán hàng",
}
MAU_IN = {
    "Phiếu nhập kho APH": "Phiếu nhập kho",
    "Phiếu kho APH": "Phiếu kho",
    "Phiếu xuất kho bán hàng APH": "Phiếu xuất kho bán hàng",
    "Biên bản giao nhận APH": "Biên bản giao nhận",
    "Phiếu thu chi APH": "Phiếu thu chi",
    "Phiếu bán hàng APH": "Phiếu bán hàng",
}
BAO_CAO = {
    "Ton kho so luong APH": "Ton kho so luong",
    "Ban hang co hoa don APH": "Ban hang co hoa don",
    "Tong hop ban hang theo khach APH": "Tong hop ban hang theo khach",
}


def _doi(doctype, cu, moi, gop=False):
    if not frappe.db.exists(doctype, cu):
        return "không có"
    if frappe.db.exists(doctype, moi):
        if gop:
            frappe.rename_doc(doctype, cu, moi, merge=True, force=True)
            return "gộp"
        frappe.delete_doc(doctype, cu, force=True)
        return "bỏ bản cũ"
    frappe.rename_doc(doctype, cu, moi, force=True)
    return "đổi tên"


def execute():
    for cu, moi in VAI_TRO.items():
        kq = _doi("Role", cu, moi, gop=True)
        if frappe.db.exists("Role", moi):
            frappe.db.set_value("Role", moi, "role_name", moi, update_modified=False)
        print(f"Vai trò {cu} -> {moi}: {kq}")
    for cu, moi in MAU_IN.items():
        kq = _doi("Print Format", cu, moi)
        frappe.db.sql("update `tabProperty Setter` set value=%s where property='default_print_format' and value=%s", (moi, cu))
        print(f"Mẫu in {cu} -> {moi}: {kq}")
    for cu, moi in BAO_CAO.items():
        kq = _doi("Report", cu, moi)
        if frappe.db.exists("Report", moi):
            frappe.db.set_value("Report", moi, "report_name", moi, update_modified=False)
        print(f"Báo cáo {cu} -> {moi}: {kq}")
    frappe.clear_cache()
