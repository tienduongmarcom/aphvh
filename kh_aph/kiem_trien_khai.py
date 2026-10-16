"""Bộ kiểm sau triển khai (0.6.0): chạy bằng một lệnh theo file cấu hình khách, xuất bảng ĐẠT / KHÔNG ĐẠT.

  bench --site <site> execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/path/khach.json", "ra": "/tmp/kq.json"}'
Chỉ đọc (không tạo, không xóa). Mã thoát: in dòng 'TỔNG ... KHÔNG ĐẠT: n'.
"""

import json

from kh_aph import cai_ban_trang as C
from kh_aph import khach_hang as K
from lab9x.bang_tai_khoan import bang
from kh_aph.tai_khoan_chuan import CAN


def kiem_cong_ty(c: dict, ok):
    """c: cấu hình một công ty; ok(ma, dat, ghi) ghi kết quả. Cần Frappe."""
    import frappe

    ab, loai = c["abbr"], K.loai_cua(c)
    co = frappe.db.get_value("Company", {"abbr": ab}, "name")
    ok(f"{ab} có công ty", bool(co), co)
    if not co:
        return
    chuan = C.bang_cua(loai)
    hkd = loai in C.HKD
    ten_tt = "nội bộ (bộ gọn)" if loai == "tl" else f"thông tư {c['thong_tu']}"
    so = {d.account_number: d for d in frappe.get_all("Account", {"company": co, "account_number": ["is", "set"]}, ["name", "account_number"])}
    ok(f"{ab}: đủ tài khoản chuẩn {ten_tt}", all(d["so"] in so for d in chuan), [d["so"] for d in chuan if d["so"] not in so][:10])
    khong_so = [d.name for d in frappe.get_all("Account", {"company": co, "parent_account": ["is", "set"]}, ["name", "account_number"]) if not d.account_number]
    ok(f"{ab}: không còn tài khoản mẫu không số hiệu", not khong_so, khong_so[:8])
    # 0.11.1: tài khoản do bộ cài tính năng giá thành tạo cho công ty TT133 (1548x, 6323) là chi tiết hợp lệ.
    from lab9x.gia_thanh import TK_KHONG_PHAN_BO, TK_YEU_TO_154
    tinh_nang = {t for t, _ in TK_YEU_TO_154} | {TK_KHONG_PHAN_BO[1]} if loai == "aph" else set()
    if frappe.conf.get("kh_aph_tien_vay"):
        # 0.14: chi tiết lãi vay (6351, 3352) và tài khoản từng ngân hàng (1121xx / 1122xx) do app dựng
        from kh_aph.tien_vay import TK_LAI
        tinh_nang = tinh_nang | set(TK_LAI) | {x for x in so if len(x) == 6 and x[:4] in ("1121", "1122")}
    thua = sorted(set(so) - {d["so"] for d in chuan} - {C.TK_TAM[0]} - set(CAN[loai]) - tinh_nang)
    ok(f"{ab}: không có tài khoản ngoài bảng chuẩn", not thua, thua[:10])
    cam = ["621", "622", "623", "627", "641", "3389"] if loai == "aph" else ["3389", "3385"] if loai == "vh" else ["33311", "1331"]
    ok(f"{ab}: không có tài khoản cấm theo thông tư", not [k for k in cam if k in so], [k for k in cam if k in so])
    mdk = {k: s for k, s in C.mac_dinh(loai).items() if frappe.get_meta("Company").has_field(k)}
    md = frappe.db.get_value("Company", co, list(mdk), as_dict=True)
    sai = {k: (md.get(k), so[s].name) for k, s in mdk.items() if s in so and md.get(k) != so[s].name}
    ok(f"{ab}: tài khoản mặc định đúng", not sai, sai)
    ok(f"{ab}: tồn kho vĩnh viễn + theo mặt hàng", bool(frappe.db.get_value("Company", co, "enable_perpetual_inventory")) and bool(frappe.db.get_value("Company", co, "enable_item_wise_inventory_account")))
    kho = {w.warehouse_name for w in frappe.get_all("Warehouse", {"company": co, "disabled": 0}, ["warehouse_name"])}
    mau = {f"{t} - {ab}" for t in C.KHO_MAC_DINH_ERPNEXT}
    con = [w for w in mau if frappe.db.exists("Warehouse", w)]
    ok(f"{ab}: không còn kho mẫu ERPNext (kể cả kho đã ngừng dùng)", not con, con)
    tro = sorted({r.default_warehouse for r in frappe.get_all("Item Default", {"company": co, "default_warehouse": ["is", "set"]}, ["default_warehouse"])
                  if frappe.db.get_value("Warehouse", r.default_warehouse, "disabled") or frappe.db.get_value("Warehouse", r.default_warehouse, "company") != co})
    ok(f"{ab}: kho mặc định của nhóm hàng / mã hàng không trỏ vào kho ngừng dùng hoặc của công ty khác", not tro, tro)
    nhom = [(n["ten"], n.get("tk")) for n in c["nhom_hang"]] if c.get("nhom_hang") else C.nhom_theo_loai_hinh(loai, c.get("loai_hinh"))
    sai = []
    for ten, s in nhom:
        g = frappe.db.get_value("Item Default", {"parent": ten, "company": co}, "default_inventory_account")
        if (s and g != (so[s].name if s in so else None)) or (not s and g):
            sai.append(ten)
    ok(f"{ab}: nhóm hàng gắn đúng tài khoản kho", not sai, sai)
    ok(f"{ab}: không còn nhóm hàng mẫu ERPNext", not [g for g in C.NHOM_MAC_DINH_ERPNEXT if frappe.db.exists("Item Group", g)], "")
    if hkd:
        return  # hộ kinh doanh / đơn vị nội bộ: không có thu hộ 3388, không có thuế GTGT khấu trừ
    ok(f"{ab}: có tài khoản thu hộ dưới 3388", bool(frappe.db.exists("Account", {"company": co, "account_name": "Tiền thu hộ đơn vị khác"})))
    from lab9x import vat_rules as V

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

    import kh_aph

    ok("Đã cài app kh_aph", "kh_aph" in frappe.get_installed_apps(), kh_aph.__version__)
    ok("Bước thiết lập ban đầu xong", frappe.is_setup_complete())
    kmd = frappe.db.get_single_value("Stock Settings", "default_warehouse")
    ok("Cài đặt kho: kho mặc định trống hoặc là kho đang dùng", not kmd or not frappe.db.get_value("Warehouse", kmd, "disabled"), kmd or "")
    hong = [f"{d.defkey}={d.defvalue}" for d in frappe.get_all("DefaultValue", {"defkey": ["like", "%warehouse%"]}, ["defkey", "defvalue"])
            if d.defvalue and (not frappe.db.exists("Warehouse", d.defvalue) or frappe.db.get_value("Warehouse", d.defvalue, "disabled"))]
    ok("Giá trị mặc định hệ thống không trỏ vào kho đã xóa / ngừng dùng", not hong, hong)
    ok("Không tự thêm dòng thuế theo mẫu thuế mặt hàng (tránh tính thuế hai lần)", not frappe.db.get_single_value("Accounts Settings", "add_taxes_from_item_tax_template"))
    for c in cfg["cong_ty"]:
        kiem_cong_ty(c, ok)
    from kh_aph import kho_chuan
    if kho_chuan.enabled() and cfg.get("cay_kho") and frappe.get_meta("Warehouse").has_field(kho_chuan.F_LOAI):
        # 0.11.2: sau khi chạy kh_aph.kho_chuan.dung, cây kho phải đủ (kho ngoài cây chỉ là cảnh báo, không tính lỗi).
        ke, tao, canh_bao, _co = kho_chuan.ke_hoach_site(cfg)
        ok(f"Cây kho chuẩn đủ ({len(ke)} kho)", not tao,
           [f"{k['ten']} - {k['abbr']}" for k in tao][:10] or ("cảnh báo: " + "; ".join(canh_bao[:5]) if canh_bao else ""))
    if ra:
        json.dump(R, open(ra, "w"), ensure_ascii=False, indent=1)
    print("TỔNG", len(R), "dòng, KHÔNG ĐẠT:", sum(1 for r in R if r[1] != "ĐẠT"))
    return R
