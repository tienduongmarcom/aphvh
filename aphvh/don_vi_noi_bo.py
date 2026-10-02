"""Đơn vị chuyển tiếp (0.4.13, 0.4.14) — vd TL: hàng mua / bán không hóa đơn trong giai đoạn chuyển tiếp,
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


# --- 0.4.15: ô "Khách lấy hóa đơn" ---------------------------------------------------------------------------
# APH, VH, Minh Khang phát hành hóa đơn (trên MISA) cho mọi lần bán; ô chỉ cho biết khách có lấy hóa đơn không:
#   Có  -> đơn giá chưa thuế, cộng thêm VAT, in tách thuế;
#   Không -> đơn giá đã gồm VAT (giá báo khách), hệ thống tách ngược, in giá đã gồm VAT, MISA ghi "người mua không lấy hóa đơn".
# Đơn vị chuyển tiếp (TL): không VAT, ô luôn "Không".
def co_xuat_hoa_don(chuyen_tiep: bool, chon_tren_chung_tu: str, mac_dinh_khach: str, co="Có", khong="Không"):
    """-> (giá trị ô Khách lấy hóa đơn, lỗi | None). Quy tắc thuần, kiểm thử không cần Frappe."""
    if chuyen_tiep:
        return khong, None
    return (chon_tren_chung_tu or mac_dinh_khach or ""), None


def gia_gom_thue(chuyen_tiep: bool, khach_lay_hd: str, khong="Không") -> bool:
    """Đơn giá nhập vào đã gồm VAT? (khách không lấy hóa đơn của pháp nhân)."""
    return (not chuyen_tiep) and khach_lay_hd == khong
