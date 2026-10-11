"""Bộ tài khoản chuẩn cho từng đơn vị (0.4.21) — app tự kiểm và tự tạo phần còn thiếu, không xóa, không đổi tên tài khoản có sẵn.

Hệ thống tài khoản lấy từ thông tư (APH: TT133, VH: TT99, hộ kinh doanh Minh Khang và TL: bộ tài khoản gọn của app).
App chỉ bổ sung tài khoản RIÊNG mà nghiệp vụ của app cần, hiện có một tài khoản:
  "Tiền thu hộ đơn vị khác" (APH, VH): nằm dưới 3388 (hoặc cùng nhóm với 3388 nếu 3388 đã có số phát sinh),
  số hiệu bắt đầu bằng 3388. Bút toán thu hộ chỉ nhận đúng tài khoản này.
Chạy lại an toàn. Chạy tự động sau mỗi lần migrate; chạy tay:
  bench --site <site> execute kh_aph.tai_khoan_chuan.setup_all
"""

TEN_TK_THU_HO = "Tiền thu hộ đơn vị khác"
SO_TK_THU_HO_UNG_VIEN = tuple(str(n) for n in range(33880, 33890))

# Số hiệu tài khoản (hoặc tài khoản con của nó) mà các nghiệp vụ của app dựa vào.
CAN = {
    "aph": ["1111", "1121", "131", "1331", "152", "153", "154", "155", "156", "242", "331", "3331", "3381", "3388",
            "5111", "632", "6421", "6422", "711", "811", "1381", "1388"],  # TT133: không có 621/622/627/641; chi phí bán hàng, quản lý là 6421, 6422
    "vh": ["1111", "1121", "131", "1331", "153", "1561", "242", "331", "3331", "3381", "3388",
           "5111", "632", "641", "642", "711", "811", "1381", "1388"],
    "mk": ["1111", "1121", "131", "1561", "331", "3339", "5111", "711", "632", "642"],
    "tl": ["1111", "131", "1561", "331", "5111", "632"],
}
# Tên và loại gốc của tài khoản chuẩn (theo TT133/TT99) để app tự tạo khi thiếu: số hiệu -> (tên, loại gốc, loại tài khoản)
TEN_CHUAN = {
    "153": ("Công cụ, dụng cụ", "Asset", "Stock"),
    "242": ("Chi phí trả trước", "Asset", ""),
    "1381": ("Tài sản thiếu chờ xử lý", "Asset", ""),
    "3381": ("Tài sản thừa chờ giải quyết", "Liability", ""),
    "641": ("Chi phí bán hàng", "Expense", ""),  # TT99
    "6421": ("Chi phí bán hàng", "Expense", ""),  # TT133
    "6422": ("Chi phí quản lý doanh nghiệp", "Expense", ""),  # TT133
    "642": ("Chi phí quản lý doanh nghiệp", "Expense", ""),
    "627": ("Chi phí sản xuất chung", "Expense", ""),
    "632": ("Giá vốn hàng bán", "Expense", "Cost of Goods Sold"),
    "711": ("Thu nhập khác", "Income", ""),
    "811": ("Chi phí khác", "Expense", ""),
    "1388": ("Phải thu khác", "Asset", ""),
    "3388": ("Phải trả, phải nộp khác", "Liability", ""),
}
CO_THU_HO = ("aph", "vh")
LOAI = {"APH": "aph", "VH": "vh", "VHT": "vh", "MK": "mk", "MKT": "mk", "TL": "tl", "TLT": "tl"}


def loai_don_vi(abbr):
    """Loại đơn vị theo viết tắt. Khách mới khai trong cấu hình (site_config 'kh_aph_loai': {viết tắt: loại}) thì ưu tiên."""
    a = (abbr or "").upper()
    try:
        import frappe

        extra = (frappe.conf or {}).get("kh_aph_loai") or {}
        if a in extra:
            return extra[a]
    except Exception:
        pass
    return LOAI.get(a)


def thieu(so_hieu_co: set, can: list) -> list:
    """Số hiệu cần mà chưa có tài khoản nào trùng hoặc bắt đầu bằng số hiệu đó (thuần)."""
    return [c for c in can if not any(s == c or s.startswith(c) for s in so_hieu_co)]


def chon_cha(so_moi: str, ds: list, root_type: str):
    """Tài khoản nhóm có số hiệu dài nhất là tiền tố của so_moi; không có thì tài khoản gốc cùng loại. ds: list dict (name, account_number, is_group, parent_account, root_type) (thuần)."""
    ung = [d for d in ds if d.get("is_group") and d.get("account_number") and so_moi.startswith(d["account_number"]) and d["account_number"] != so_moi]
    if ung:
        return max(ung, key=lambda d: len(d["account_number"]))["name"]
    goc = [d for d in ds if d.get("is_group") and not d.get("parent_account") and d.get("root_type") == root_type]
    return goc[0]["name"] if goc else None


def chon_so_thu_ho(so_hieu_co: set):
    """Số hiệu còn trống đầu tiên trong 33880–33889 cho tài khoản thu hộ; None nếu hết."""
    for n in SO_TK_THU_HO_UNG_VIEN:
        if n not in so_hieu_co:
            return n
    return None


def setup(company: str) -> dict:
    import frappe

    abbr = frappe.db.get_value("Company", company, "abbr")
    loai = loai_don_vi(abbr)
    kq = {"cong_ty": company, "loai": loai, "thieu": [], "viec": [], "canh_bao": []}
    if not loai:
        kq["canh_bao"].append(f"Chưa biết đơn vị {abbr}: bỏ qua")
        return kq
    campos = ["name", "account_number", "account_name", "parent_account", "is_group", "root_type"]
    ds = frappe.get_all("Account", {"company": company}, campos)
    so = {d.account_number for d in ds if d.account_number}
    for c in thieu(so, CAN[loai]):
        if c not in TEN_CHUAN:
            continue
        ten, rt, at = TEN_CHUAN[c]
        cha = chon_cha(c, [dict(d) for d in ds], rt)
        if not cha:
            kq["canh_bao"].append(f"Không thấy nhóm cha cho {c}")
            continue
        try:
            v = {"doctype": "Account", "account_name": ten, "account_number": c, "company": company,
                 "parent_account": cha, "root_type": rt, "is_group": 0}
            if at:
                v["account_type"] = at
            frappe.get_doc(v).insert(ignore_permissions=True)
            frappe.db.commit()
            kq["viec"].append(f"tạo {c} - {ten}")
        except Exception as e:
            frappe.db.rollback()
            kq["canh_bao"].append(f"Không tạo được {c}: {str(e)[:120]}")
    ds = frappe.get_all("Account", {"company": company}, campos)
    so = {d.account_number for d in ds if d.account_number}
    kq["thieu"] = thieu(so, CAN[loai])
    if loai not in CO_THU_HO:
        return kq
    if any(d.account_name == TEN_TK_THU_HO for d in ds):
        return kq
    goc = next((d for d in ds if d.account_number == "3388"), None) or next(
        (d for d in ds if (d.account_number or "").startswith("3388") and d.is_group), None)
    if not goc:
        cha = next((d for d in ds if d.account_number and d.account_number.startswith("3388")), None)
        if not cha:
            kq["canh_bao"].append("Không thấy tài khoản 3388: chưa tạo được tài khoản thu hộ")
            return kq
        goc = cha
    so_moi = chon_so_thu_ho(so)
    if not so_moi:
        kq["canh_bao"].append("Hết số hiệu 33880–33889: tạo tay tài khoản 'Tiền thu hộ đơn vị khác' dưới 3388")
        return kq
    cha_ten = goc.name if goc.is_group else goc.parent_account
    try:
        d = frappe.get_doc({"doctype": "Account", "account_name": TEN_TK_THU_HO, "account_number": so_moi, "company": company,
                            "parent_account": cha_ten, "root_type": "Liability", "is_group": 0})
        d.insert(ignore_permissions=True)
        frappe.db.commit()
        kq["viec"].append(f"tạo {d.name}")
    except Exception as e:  # không làm hỏng migrate
        frappe.db.rollback()
        kq["canh_bao"].append(f"Không tạo được tài khoản thu hộ: {str(e)[:120]}")
    return kq


def setup_all() -> list:
    import frappe

    return [setup(c) for c in frappe.get_all("Company", pluck="name")]
