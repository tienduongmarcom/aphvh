"""Cài bản trắng (0.5.0): dựng hệ thống tài khoản chuẩn cho công ty mới, bỏ tài khoản mẫu không thuộc thông tư, đặt tài khoản mặc định.

APH theo TT133, VH theo TT99 (bảng ở bang_tai_khoan). Chạy lại an toàn: chỉ tạo phần còn thiếu, không đổi tên,
không xóa tài khoản đã có số phát sinh. Sau khi cài, doanh nghiệp tự thêm/sửa tài khoản chi tiết trong ERPNext.
Chạy tay:  bench --site <site> execute aphvh.cai_ban_trang.cai_tat_ca
"""

from aphvh.bang_tai_khoan import bang
from aphvh.tai_khoan_chuan import loai_don_vi

# Tài khoản tạm để nhập số dư đầu kỳ; không thuộc thông tư, số dư phải về 0 sau khi nhập xong (không dùng 3389).
TK_TAM = ("9990", "Tài khoản tạm nhập số dư đầu kỳ", "Asset", "Temporary")

# trường mặc định của Company -> số hiệu tài khoản (đều phải là tài khoản chi tiết trong bảng chuẩn)
MAC_DINH_CHUNG = {
    "default_receivable_account": "131", "default_payable_account": "3311", "default_income_account": "5111",
    "default_expense_account": "6321", "default_cash_account": "1111", "default_bank_account": "1121",
    "stock_received_but_not_billed": "3318", "stock_adjustment_account": "6322",
    "exchange_gain_loss_account": "6359", "default_payroll_payable_account": "334",
    "write_off_account": "811", "round_off_account": "811",
}
MAC_DINH_KHO = {"aph": "156", "vh": "1561"}


def mac_dinh(loai: str) -> dict:
    """Trường mặc định công ty -> số hiệu (thuần). Tồn kho mặc định: APH 156, VH 1561 (hàng cụ thể lấy theo nhóm hàng)."""
    d = dict(MAC_DINH_CHUNG)
    d["default_inventory_account"] = MAC_DINH_KHO[loai]
    return d


def kiem_mac_dinh(loai: str) -> list:
    """Thuần: mọi số hiệu mặc định phải có trong bảng chuẩn và là tài khoản chi tiết."""
    ds = {x["so"]: x for x in bang(loai)}
    loi = []
    for truong, so in mac_dinh(loai).items():
        if so not in ds:
            loi.append(f"{truong}: {so} không có trong bảng {loai}")
        elif ds[so]["nhom"]:
            loi.append(f"{truong}: {so} là tài khoản nhóm")
    return loi


def cai(company: str) -> dict:
    import frappe

    abbr = frappe.db.get_value("Company", company, "abbr")
    loai = loai_don_vi(abbr)
    kq = {"company": company, "loai": loai, "tao": 0, "bo": 0, "canh_bao": []}
    if loai not in ("aph", "vh"):
        return kq
    co = {d.account_number: d.name for d in frappe.get_all("Account", {"company": company, "account_number": ["is", "set"]},
                                                           ["name", "account_number"])}
    goc = {d.root_type: d.name for d in frappe.get_all("Account", {"company": company, "parent_account": ["is", "not set"]},
                                                      ["name", "root_type"])}
    chuan = bang(loai) + [{"so": TK_TAM[0], "ten": TK_TAM[1], "cha": None, "nhom": 0, "root": TK_TAM[2], "loai_tk": TK_TAM[3]}]
    # 1) bỏ tài khoản mẫu không thuộc bảng chuẩn (chỉ khi chưa có số phát sinh, chưa có số hiệu, không phải gốc)
    if not co:
        for truong in MAC_DINH_CHUNG:
            if frappe.get_meta("Company").has_field(truong):
                frappe.db.set_value("Company", company, truong, None)
        mau = frappe.get_all("Account", {"company": company, "parent_account": ["is", "set"]}, ["name", "is_group", "lft"], order_by="lft desc")
        for a in mau:  # lft giảm dần: con trước cha
            if frappe.db.exists("GL Entry", {"account": a.name}):
                continue
            frappe.db.savepoint("xoa_tk")
            try:
                frappe.delete_doc("Account", a.name, ignore_permissions=True, force=0)
                kq["bo"] += 1
            except Exception:
                frappe.db.rollback(save_point="xoa_tk")
                kq["canh_bao"].append(f"Giữ lại {a.name} (đang được dùng)")
    # 2) tạo tài khoản chuẩn còn thiếu
    for d in chuan:
        if d["so"] in co:
            continue
        cha = co.get(d["cha"]) if d["cha"] else goc.get(d["root"])
        if not cha:
            kq["canh_bao"].append(f"Chưa tạo {d['so']}: thiếu tài khoản cha")
            continue
        try:
            a = frappe.get_doc({"doctype": "Account", "account_name": d["ten"], "account_number": d["so"], "company": company,
                                "parent_account": cha, "root_type": d["root"], "is_group": d["nhom"],
                                "account_type": d["loai_tk"] or None}).insert(ignore_permissions=True)
            co[d["so"]] = a.name
            kq["tao"] += 1
        except Exception as e:
            frappe.db.rollback()
            kq["canh_bao"].append(f"Không tạo được {d['so']}: {str(e)[:120]}")
    # 3) tài khoản mặc định (chỉ đặt khi đang trống)
    cur = frappe.db.get_value("Company", company, list(mac_dinh(loai)), as_dict=True) or {}
    for truong, so in mac_dinh(loai).items():
        if not cur.get(truong) and so in co and frappe.get_meta("Company").has_field(truong):
            frappe.db.set_value("Company", company, truong, co[so])
    frappe.db.commit()
    return kq


def cai_tat_ca() -> list:
    import frappe

    return [cai(c) for c in frappe.get_all("Company", pluck="name")]
