"""Bộ kiểm sau triển khai (0.6.0): chạy bằng một lệnh theo file cấu hình khách, xuất bảng ĐẠT / KHÔNG ĐẠT.

  bench --site <site> execute aphvh.kiem_trien_khai.chay --kwargs '{"duong_dan": "/path/khach.json", "ra": "/tmp/kq.json"}'
Chỉ đọc (không tạo, không xóa). Mã thoát: in dòng 'TỔNG ... KHÔNG ĐẠT: n'.
"""

import json

from aphvh import cai_ban_trang as C
from aphvh import khach_hang as K
from aphvh.bang_tai_khoan import bang
from aphvh.tai_khoan_chuan import CAN


def kiem_cong_ty(c: dict, ok):
    """c: cấu hình một công ty; ok(ma, dat, ghi) ghi kết quả. Cần Frappe."""
    import frappe

    ab, loai = c["abbr"], K.loai_cua(c)
    co = frappe.db.get_value("Company", {"abbr": ab}, "name")
    ok(f"{ab} có công ty", bool(co), co)
    if not co:
        return
    chuan = bang(loai)
    so = {d.account_number: d for d in frappe.get_all("Account", {"company": co, "account_number": ["is", "set"]}, ["name", "account_number"])}
    ok(f"{ab}: đủ tài khoản chuẩn thông tư {c['thong_tu']}", all(d["so"] in so for d in chuan), [d["so"] for d in chuan if d["so"] not in so][:10])
    khong_so = [d.name for d in frappe.get_all("Account", {"company": co, "parent_account": ["is", "set"]}, ["name", "account_number"]) if not d.account_number]
    ok(f"{ab}: không còn tài khoản mẫu không số hiệu", not khong_so, khong_so[:8])
    thua = sorted(set(so) - {d["so"] for d in chuan} - {C.TK_TAM[0]} - set(CAN[loai]))
    ok(f"{ab}: không có tài khoản ngoài bảng chuẩn", not thua, thua[:10])
    cam = ["621", "622", "623", "627", "641", "3389"] if loai == "aph" else ["3389", "3385"]
    ok(f"{ab}: không có tài khoản cấm theo thông tư", not [k for k in cam if k in so], [k for k in cam if k in so])
    mdk = {k: s for k, s in C.mac_dinh(loai).items() if frappe.get_meta("Company").has_field(k)}
    md = frappe.db.get_value("Company", co, list(mdk), as_dict=True)
    sai = {k: (md.get(k), so[s].name) for k, s in mdk.items() if s in so and md.get(k) != so[s].name}
    ok(f"{ab}: tài khoản mặc định đúng", not sai, sai)
    ok(f"{ab}: tồn kho vĩnh viễn + theo mặt hàng", bool(frappe.db.get_value("Company", co, "enable_perpetual_inventory")) and bool(frappe.db.get_value("Company", co, "enable_item_wise_inventory_account")))
    kho = {w.warehouse_name for w in frappe.get_all("Warehouse", {"company": co, "disabled": 0}, ["warehouse_name"])}
    ok(f"{ab}: có kho địa điểm + Hàng đang vận chuyển", {"Hà Nội", "Kho bán hàng Hà Nội", "Kho Đà Nẵng", "Kho Hồ Chí Minh", "Hàng đang vận chuyển"} <= kho)
    if c.get("nha_may"):
        can = {t for t, _, _ in C.cay_nha_may(c.get("ten_nha_may") or C.TEN_NHA_MAY_MAC_DINH, c.get("kho_them"))}
        ok(f"{ab}: đủ kho nhà máy theo cấu hình ({len(can)} kho/nhóm)", can <= kho, sorted(can - kho)[:8])
    else:
        ok(f"{ab}: không có kho nhà máy", not (kho & {t for t, _, _ in C.cay_nha_may()}), "")
    ok(f"{ab}: không còn kho mẫu ERPNext", not (kho & set(C.KHO_MAC_DINH_ERPNEXT)), kho & set(C.KHO_MAC_DINH_ERPNEXT))
    nhom = [(n["ten"], n.get("tk")) for n in c["nhom_hang"]] if c.get("nhom_hang") else C.NHOM_HANG[loai]
    sai = []
    for ten, s in nhom:
        g = frappe.db.get_value("Item Default", {"parent": ten, "company": co}, "default_inventory_account")
        if (s and g != (so[s].name if s in so else None)) or (not s and g):
            sai.append(ten)
    ok(f"{ab}: nhóm hàng gắn đúng tài khoản kho", not sai, sai)
    ok(f"{ab}: không còn nhóm hàng mẫu ERPNext", not [g for g in C.NHOM_MAC_DINH_ERPNEXT if frappe.db.exists("Item Group", g)], "")
    ok(f"{ab}: có tài khoản thu hộ dưới 3388", bool(frappe.db.exists("Account", {"company": co, "account_name": "Tiền thu hộ đơn vị khác"})))
    from aphvh import vat_rules as V

    ok(f"{ab}: có mẫu thuế GTGT theo thuế suất", all(frappe.db.exists("Item Tax Template", f"{ti} - {ab}") for ti, _ in V.VAT_TEMPLATES)
       and bool(frappe.db.exists("Sales Taxes and Charges Template", f"{V.SALES_TAX_TEMPLATE} - {ab}")))


def chay(duong_dan: str = None, ra: str = None, cfg: dict = None) -> list:
    import frappe

    if cfg is None:
        cfg = K.doc_cau_hinh(duong_dan)
    R = []

    def ok(ma, dat, ghi=""):
        R.append((ma, "ĐẠT" if dat else "KHÔNG ĐẠT", str(ghi)))
        print(ma, "ĐẠT" if dat else "KHÔNG ĐẠT", ghi)

    import aphvh

    ok("Đã cài app aphvh", "aphvh" in frappe.get_installed_apps(), aphvh.__version__)
    ok("Bước thiết lập ban đầu xong", frappe.is_setup_complete())
    for c in cfg["cong_ty"]:
        kiem_cong_ty(c, ok)
    if ra:
        json.dump(R, open(ra, "w"), ensure_ascii=False, indent=1)
    print("TỔNG", len(R), "dòng, KHÔNG ĐẠT:", sum(1 for r in R if r[1] != "ĐẠT"))
    return R
