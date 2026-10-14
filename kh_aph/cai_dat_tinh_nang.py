"""Bộ cài tính năng ứng viên (đơn chung, công nợ lúc giao, bao/kg, quỹ/cọc, đổi nguồn, chặn xem giá vốn)
cho một site production đã kiểm kê — từ bản 0.10.0.

Không chạy tự động (không gắn after_install/after_migrate). Chạy tay, theo thứ tự trong
deploy/release/RELEASE_GATES.md:

    bench --site frontend set-config <từng cờ trong FLAGS> 1
    bench --site frontend execute kh_aph.cai_dat_tinh_nang.cai --kwargs '{"xac_nhan_site": "frontend"}'
    bench --site frontend execute kh_aph.cai_dat_tinh_nang.kiem --kwargs '{"xac_nhan_site": "frontend"}'

Dùng CHÍNH phần schema đã kiểm trên UAT (uat_candidate_setup.schema và các hàm schema() con), chỉ khác
lớp khóa: phải là Administrator, gõ đúng tên site đích, đủ 15 cờ, và site chưa có dữ liệu nghiệp vụ
(site đã có dữ liệu phải đi quy trình bản sao + đối chiếu sổ riêng, bộ cài này từ chối).
Dấu vân schema/số liệu để so sánh: deploy/release/dau_van_site.py (chạy được trên mọi phiên bản).
"""
import frappe
from frappe.utils import cint

FLAGS = (
    "kh_aph_server_cost_guard", "kh_aph_post_receivable_on_delivery",
    "kh_aph_shared_sales_order", "kh_aph_global_credit_warning",
    "kh_aph_high_risk_credit_guard", "kh_aph_quantity_valuation_mvp",
    "kh_aph_funds_workflow", "kh_aph_source_change",
    # 0.11.1
    "kh_aph_factory_costing", "kh_aph_factory_cash", "kh_aph_sales_adjust", "kh_aph_data_review",
    # 0.11.2–0.11.4
    "kh_aph_kho_chuan", "kh_aph_sales_p1", "kh_aph_quan_tri",
)
CAM_SITE = ("erpnext.local",)


def _kiem_dau_vao(xac_nhan_site):
    if frappe.session.user != "Administrator":
        frappe.throw("Chỉ Administrator được chạy bộ cài tính năng", frappe.PermissionError)
    if not xac_nhan_site or xac_nhan_site != frappe.local.site:
        frappe.throw(f"Gõ đúng tên site đích để xác nhận: xac_nhan_site = \"{frappe.local.site}\"")
    if frappe.local.site in CAM_SITE:
        frappe.throw("Không dùng site erpnext.local")
    thieu = [f for f in FLAGS if not cint(frappe.conf.get(f))]
    if thieu:
        frappe.throw("Chưa bật đủ cờ trên site: " + ", ".join(thieu))


def cai(xac_nhan_site=None):
    """Cài schema tính năng (idempotent), rồi kiểm ngay. Trả về kết quả kiểm."""
    _kiem_dau_vao(xac_nhan_site)
    from kh_aph.uat_candidate_setup import schema
    schema()
    return kiem(xac_nhan_site)


def kiem(xac_nhan_site=None):
    """Kiểm sau cài: chạy lại bộ cài phải không đổi gì; field, DocType, hook, quyền đúng như UAT."""
    _kiem_dau_vao(xac_nhan_site)
    from kh_aph.uat_candidate_setup import schema
    from kh_aph.uat_fresh_verify import kiem_schema
    kq = kiem_schema(schema)
    return {"trang_thai": "ĐẠT", "site": frappe.local.site, "idempotent": True,
            "co": {f: cint(frappe.conf.get(f)) for f in FLAGS},
            **kq,
            "nghiem_thu_nghiep_vu": "NOT_TESTED"}
