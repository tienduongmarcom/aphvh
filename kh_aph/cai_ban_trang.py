"""Cài bản trắng (0.5.0): dựng hệ thống tài khoản chuẩn cho công ty mới, bỏ tài khoản mẫu không thuộc thông tư, đặt tài khoản mặc định.

APH theo TT133, VH theo TT99 (bảng ở bang_tai_khoan). Chạy lại an toàn: chỉ tạo phần còn thiếu, không đổi tên,
không xóa tài khoản đã có số phát sinh. Sau khi cài, doanh nghiệp tự thêm/sửa tài khoản chi tiết trong ERPNext.
Chạy tay:  bench --site <site> execute kh_aph.cai_ban_trang.cai_tat_ca
"""

from lab9x.bang_tai_khoan import bang
from kh_aph.tai_khoan_chuan import loai_don_vi

# Tài khoản tạm để nhập số dư đầu kỳ; không thuộc thông tư, số dư phải về 0 sau khi nhập xong (không dùng 3389).
TK_TAM = ("9990", "Tài khoản tạm nhập số dư đầu kỳ", "Asset", "Temporary")

# trường mặc định của Company -> số hiệu tài khoản (đều phải là tài khoản chi tiết trong bảng chuẩn)
MAC_DINH_CHUNG = {
    "default_receivable_account": "131", "default_payable_account": "3311", "default_income_account": "5111",
    "default_expense_account": "6321", "default_cash_account": "1111", "default_bank_account": "1121",
    "stock_received_but_not_billed": "3318", "stock_adjustment_account": "6322",
    "exchange_gain_loss_account": "6359",
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


# 0.8.0: không tạo cây kho. Khách tự tạo kho trên giao diện (dữ liệu trắng); app chỉ bỏ kho mẫu ERPNext chưa dùng.


KHO_MAC_DINH_ERPNEXT = ("Stores", "Work In Progress", "Finished Goods", "Goods In Transit")
NHOM_MAC_DINH_ERPNEXT = ("Products", "Raw Material", "Services", "Sub Assemblies", "Consumable")

# Nhóm hàng cấp 1 và tài khoản kho mặc định (số hiệu trong bảng chuẩn). None = không phải hàng tồn kho.
NHOM_HANG = {
    "aph": [("HH - Hàng hóa", "156"), ("TP - Thành phẩm", "1551"), ("NL - Nguyên liệu", "1521"), ("VT - Vật tư, bao bì", "1523"),
            ("DD - Sản phẩm dở dang", "15411"), ("PTSC - Phụ tùng, vật tư thay thế", "1524"), ("CCDC - Công cụ, dụng cụ", "153"),
            ("DV - Dịch vụ", None), ("TS - Tài sản cố định", None)],
    "vh": [("HH - Hàng hóa", "1561"), ("CCDC - Công cụ, dụng cụ", "153"), ("DV - Dịch vụ", None), ("TS - Tài sản cố định", None)],
}


def kiem_nhom_hang(loai: str) -> list:
    """Thuần: tài khoản kho của nhóm hàng phải là tài khoản chi tiết loại Stock trong bảng chuẩn."""
    ds = {x["so"]: x for x in bang(loai)}
    loi = []
    for ten, so in NHOM_HANG[loai]:
        if so and (so not in ds or ds[so]["nhom"] or ds[so]["loai_tk"] != "Stock"):
            loi.append(f"{ten}: {so} không phải tài khoản kho chi tiết")
    return loi


def cai_kho_nhom_hang(company: str, co: dict, loai: str, nhom_hang: list = None) -> dict:
    """Nhóm hàng cấp 1 gắn tài khoản kho, bật tồn kho theo mặt hàng, bỏ kho/nhóm mẫu ERPNext chưa dùng. Không tạo kho (khách tự tạo)."""
    import frappe

    kq = {"kho": 0, "nhom": 0, "canh_bao": []}
    abbr = frappe.db.get_value("Company", company, "abbr")
    for f in ("enable_perpetual_inventory", "enable_item_wise_inventory_account"):
        if frappe.get_meta("Company").has_field(f):
            frappe.db.set_value("Company", company, f, 1)
    for ten in KHO_MAC_DINH_ERPNEXT:  # kho mẫu của ERPNext, bỏ nếu chưa dùng
        n = f"{ten} - {abbr}"
        if frappe.db.exists("Warehouse", n):
            frappe.db.savepoint("xoa_kho")
            try:
                frappe.db.set_value("Company", company, "default_in_transit_warehouse", None) if n.startswith("Goods In") else None
                frappe.delete_doc("Warehouse", n, ignore_permissions=True)
            except Exception:
                frappe.db.rollback(save_point="xoa_kho")
                frappe.db.set_value("Warehouse", n, "disabled", 1)  # đã có liên kết: ngừng sử dụng thay vì xóa
    for ten in NHOM_MAC_DINH_ERPNEXT:
        if frappe.db.exists("Item Group", ten) and not frappe.db.exists("Item", {"item_group": ten}):
            frappe.db.savepoint("xoa_nhom")
            try:
                frappe.delete_doc("Item Group", ten, ignore_permissions=True)
            except Exception:
                frappe.db.rollback(save_point="xoa_nhom")
    for ten, so in (nhom_hang or NHOM_HANG[loai]):
        if not frappe.db.exists("Item Group", ten):
            frappe.get_doc({"doctype": "Item Group", "item_group_name": ten, "parent_item_group": "All Item Groups",
                            "is_group": 1}).insert(ignore_permissions=True)
            kq["nhom"] += 1
        if so and so in co:
            g = frappe.get_doc("Item Group", ten)
            if not any(r.company == company for r in g.get("item_group_defaults") or []):
                frappe.get_doc({"doctype": "Item Default", "parenttype": "Item Group", "parentfield": "item_group_defaults",
                                "parent": ten, "company": company, "default_inventory_account": co[so]}).insert(ignore_permissions=True)
    frappe.db.commit()
    return kq


def gan_tk_cho_nhom_con(company: str) -> int:
    """Sau khi nhập danh mục: nhóm hàng con chưa có tài khoản kho thì lấy của nhóm cha gần nhất. Chạy tay, chạy lại an toàn."""
    import frappe

    n = 0
    co = {d.name for d in frappe.get_all("Account", {"company": company})}
    for g in frappe.get_all("Item Group", fields=["name", "parent_item_group"], order_by="lft"):
        if frappe.db.exists("Item Default", {"parent": g.name, "company": company}):
            continue
        cha = g.parent_item_group
        while cha:
            m = frappe.db.get_value("Item Default", {"parent": cha, "company": company}, "default_inventory_account")
            if m:
                frappe.get_doc({"doctype": "Item Default", "parenttype": "Item Group", "parentfield": "item_group_defaults",
                                "parent": g.name, "company": company, "default_inventory_account": m}).insert(ignore_permissions=True)
                n += 1
                break
            cha = frappe.db.get_value("Item Group", cha, "parent_item_group")
    frappe.db.commit()
    return n


# Hình thức thanh toán mặc định -> số hiệu tài khoản chuẩn
HINH_THUC_TT = {"Cash": "1111", "Bank Draft": "1121", "Wire Transfer": "1121", "Credit Card": "1121", "Cheque": "1121"}


def _don_mau_thue_va_thanh_toan(company: str, co: dict):
    """Trước khi bỏ tài khoản mẫu: bỏ mẫu thuế 'Vietnam Tax' của ERPNext (dùng tài khoản VAT mẫu), chuyển hình thức thanh toán sang tài khoản chuẩn."""
    import frappe

    for dt in ("Sales Taxes and Charges Template", "Purchase Taxes and Charges Template", "Item Tax Template"):
        for n in frappe.get_all(dt, {"company": company, "title": "Vietnam Tax"}, pluck="name"):
            frappe.db.savepoint("xoa_thue")
            try:
                frappe.delete_doc(dt, n, ignore_permissions=True)
            except Exception:
                frappe.db.rollback(save_point="xoa_thue")
    for r in frappe.get_all("Mode of Payment Account", {"company": company}, ["name", "parent"]):
        so = HINH_THUC_TT.get(r.parent)
        if so and so in co:
            frappe.db.set_value("Mode of Payment Account", r.name, "default_account", co[so])


def cai(company: str, loai: str = None, nhom_hang: list = None) -> dict:
    """loai: 'aph' (TT133) hoặc 'vh' (TT99); bỏ trống thì suy từ viết tắt công ty."""
    import frappe

    abbr = frappe.db.get_value("Company", company, "abbr")
    loai = loai or loai_don_vi(abbr)
    kq = {"company": company, "loai": loai, "tao": 0, "bo": 0, "canh_bao": []}
    if loai not in ("aph", "vh"):
        return kq
    co = {d.account_number: d.name for d in frappe.get_all("Account", {"company": company, "account_number": ["is", "set"]},
                                                           ["name", "account_number"])}
    goc = {d.root_type: d.name for d in frappe.get_all("Account", {"company": company, "parent_account": ["is", "not set"]},
                                                      ["name", "root_type"])}
    chuan = bang(loai) + [{"so": TK_TAM[0], "ten": TK_TAM[1], "cha": None, "nhom": 0, "root": TK_TAM[2], "loai_tk": TK_TAM[3]}]
    # 1) tạo tài khoản chuẩn còn thiếu
    for d in chuan:
        if d["so"] in co:
            continue
        cha = co.get(d["cha"]) if d["cha"] else goc.get(d["root"])
        if not cha:
            kq["canh_bao"].append(f"Chưa tạo {d['so']}: thiếu tài khoản cha")
            continue
        frappe.db.savepoint("tao_tk")
        try:
            a = frappe.get_doc({"doctype": "Account", "account_name": d["ten"], "account_number": d["so"], "company": company,
                                "parent_account": cha, "root_type": d["root"], "is_group": d["nhom"],
                                "account_type": d["loai_tk"] or None}).insert(ignore_permissions=True)
            co[d["so"]] = a.name
            kq["tao"] += 1
        except Exception as e:
            frappe.db.rollback(save_point="tao_tk")
            kq["canh_bao"].append(f"Không tạo được {d['so']}: {str(e)[:120]}")
    # 2) bỏ tài khoản mẫu không thuộc bảng chuẩn: CHỈ khi công ty chưa có bút toán nào; tài khoản có số hiệu, có phát sinh hoặc đang được dùng thì giữ
    if not frappe.db.exists("GL Entry", {"company": company}):
        _don_mau_thue_va_thanh_toan(company, co)
        meta = frappe.get_meta("Company")
        for df in meta.fields:
            if df.fieldtype == "Link" and df.options == "Account":
                frappe.db.set_value("Company", company, df.fieldname, None)
        mau = frappe.get_all("Account", {"company": company, "parent_account": ["is", "set"]},
                             ["name", "account_number", "lft"], order_by="lft desc")
        for a in mau:  # lft giảm dần: con trước cha
            if a.account_number:
                continue
            frappe.db.savepoint("xoa_tk")
            try:
                frappe.delete_doc("Account", a.name, ignore_permissions=True)
                kq["bo"] += 1
            except frappe.QueueOverloaded:
                frappe.db.rollback(save_point="xoa_tk")
                kq["canh_bao"].append("Hàng đợi nền đang đầy: dừng bỏ tài khoản mẫu, chạy lại sau vài phút (chạy lại an toàn)")
                break
            except Exception:
                frappe.db.rollback(save_point="xoa_tk")
                kq["canh_bao"].append(f"Giữ lại {a.name} (đang được dùng)")
    # 3) tài khoản mặc định (chỉ đặt khi đang trống)
    md = {k: v for k, v in mac_dinh(loai).items() if frappe.get_meta("Company").has_field(k)}  # trường chỉ có khi cài app khác (vd. lương) thì bỏ
    cur = frappe.db.get_value("Company", company, list(md), as_dict=True) or {}
    for truong, so in md.items():
        if not cur.get(truong) and so in co:
            frappe.db.set_value("Company", company, truong, co[so])
    frappe.db.commit()
    kq["kho_nhom"] = cai_kho_nhom_hang(company, co, loai, nhom_hang)
    try:
        from kh_aph.vat import ensure_vat_templates

        kq["thue"] = len(ensure_vat_templates())  # mẫu thuế GTGT (33311) cho công ty có tài khoản thuế
    except Exception as e:
        kq["canh_bao"].append(f"mẫu thuế: {str(e)[:120]}")
    return kq


def cai_tat_ca() -> list:
    import frappe

    return [cai(c) for c in frappe.get_all("Company", pluck="name")]
