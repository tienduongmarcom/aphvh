"""Đơn vị theo dõi nội bộ (0.4.13) — vd TL: hàng mua / bán không hóa đơn trong giai đoạn chuyển tiếp,
dự kiến chuyển dần về hộ kinh doanh Minh Khang trong 6–12 tháng.

- Công ty riêng trong ERPNext, không mã số thuế, đánh dấu "Đơn vị theo dõi nội bộ".
- Hệ thống tài khoản gọn như hộ kinh doanh (aphvh.hkd_accounts): tiền, công nợ, hàng hóa, doanh thu, giá vốn, chi phí.
- Không có TK 33311 nên app không gắn mẫu thuế GTGT nào; phiếu in không ghi mẫu số thông tư.
- Kho riêng: tồn, giá vốn, lãi lỗ tính riêng; khi đóng đơn vị thì chuyển tồn và công nợ còn lại sang hộ kinh doanh.

Chạy: bench --site <site> execute aphvh.don_vi_noi_bo.setup --kwargs '{"ten": "TL", "abbr": "TL", "kho": ["Kho TL"]}'
Chạy lại an toàn.
"""


def setup(ten: str, abbr: str, kho=None) -> dict:
    import frappe

    from aphvh import hkd_accounts

    kho = kho or [f"Kho {abbr}"]
    out = {"viec": []}
    if not frappe.db.exists("Company", ten):
        frappe.get_doc({"doctype": "Company", "company_name": ten, "abbr": abbr, "default_currency": "VND",
                        "country": "Vietnam", "create_chart_of_accounts_based_on": "Standard Template",
                        "chart_of_accounts": "Standard"}).insert(ignore_permissions=True)
        out["viec"].append(f"tạo công ty {ten} ({abbr})")
    if frappe.get_meta("Company").has_field("aphvh_noi_bo"):
        frappe.db.set_value("Company", ten, "aphvh_noi_bo", 1)
    out["viec"] += hkd_accounts.setup(ten)["viec"]
    abbr = frappe.db.get_value("Company", ten, "abbr")
    goc = frappe.db.get_value("Warehouse", {"company": ten, "is_group": 1, "parent_warehouse": ["in", ("", None)]}, "name")
    for k in kho:
        if not frappe.db.exists("Warehouse", f"{k} - {abbr}"):
            frappe.get_doc({"doctype": "Warehouse", "warehouse_name": k, "company": ten, "parent_warehouse": goc}).insert(ignore_permissions=True)
            out["viec"].append(f"tạo kho {k}")
    frappe.db.set_value("Company", ten, "default_warehouse_for_sales_return", f"{kho[0]} - {abbr}") if frappe.get_meta("Company").has_field("default_warehouse_for_sales_return") else None
    frappe.db.commit()
    out["kho"] = frappe.get_all("Warehouse", {"company": ten, "is_group": 0}, pluck="name")
    return out
