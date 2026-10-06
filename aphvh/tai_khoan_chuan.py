"""Bộ tài khoản chuẩn cho từng đơn vị (0.4.21) — app tự kiểm và tự tạo phần còn thiếu, không xóa, không đổi tên tài khoản có sẵn.

Hệ thống tài khoản lấy từ thông tư (APH: TT133, VH: TT99, hộ kinh doanh Minh Khang và TL: bộ tài khoản gọn của app).
App chỉ bổ sung tài khoản RIÊNG mà nghiệp vụ của app cần, hiện có một tài khoản:
  "Tiền thu hộ đơn vị khác" (APH, VH): nằm dưới 3388 (hoặc cùng nhóm với 3388 nếu 3388 đã có số phát sinh),
  số hiệu bắt đầu bằng 3388. Bút toán thu hộ chỉ nhận đúng tài khoản này.
Chạy lại an toàn. Chạy tự động sau mỗi lần migrate; chạy tay:
  bench --site <site> execute aphvh.tai_khoan_chuan.setup_all
"""

TEN_TK_THU_HO = "Tiền thu hộ đơn vị khác"
SO_TK_THU_HO_UNG_VIEN = tuple(str(n) for n in range(33880, 33890))

# Số hiệu tài khoản (hoặc tài khoản con của nó) mà các nghiệp vụ của app dựa vào.
CAN = {
    "aph": ["1111", "1121", "131", "1331", "152", "153", "154", "155", "156", "242", "331", "3331", "3381", "3388",
            "5111", "627", "632", "641", "642", "711", "811", "1381", "1388"],
    "vh": ["1111", "1121", "131", "1331", "153", "1561", "242", "331", "3331", "3381", "3388",
           "5111", "632", "641", "642", "711", "811", "1381", "1388"],
    "mk": ["1111", "1121", "131", "1561", "331", "3339", "5111", "711", "632", "642"],
    "tl": ["1111", "131", "1561", "331", "5111", "632"],
}
CO_THU_HO = ("aph", "vh")
LOAI = {"APH": "aph", "VH": "vh", "VHT": "vh", "MK": "mk", "MKT": "mk", "TL": "tl", "TLT": "tl"}


def loai_don_vi(abbr):
    return LOAI.get((abbr or "").upper())


def thieu(so_hieu_co: set, can: list) -> list:
    """Số hiệu cần mà chưa có tài khoản nào trùng hoặc bắt đầu bằng số hiệu đó (thuần)."""
    return [c for c in can if not any(s == c or s.startswith(c) for s in so_hieu_co)]


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
    ds = frappe.get_all("Account", {"company": company}, ["name", "account_number", "account_name", "parent_account", "is_group"])
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
