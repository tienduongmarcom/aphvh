"""Thuế GTGT theo loại khách (0.3.5) — quy tắc thuần Python, kiểm thử không cần Frappe.

Căn cứ NĐ 181/2025 sửa bởi NĐ 359/2025 (hiệu lực 01/01/2026): sản phẩm trồng trọt chưa chế biến
hoặc chỉ sơ chế thông thường, ở khâu kinh doanh thương mại:
- bán cho doanh nghiệp, hợp tác xã: không phải kê khai, tính nộp thuế GTGT (vẫn khấu trừ đầu vào);
- bán cho hộ kinh doanh, cá nhân: thuế suất 5% (phương pháp khấu trừ).
Hàng đã chế biến (tinh bột, đường, dầu, miến…) theo thuế suất riêng — kế toán trưởng chốt từng mặt hàng.

ERPNext chọn mẫu thuế mặt hàng theo "Loại thuế" (Tax Category) của chứng từ, lấy từ hồ sơ khách.
App tự phân loại khách chưa có loại thuế theo MST và tên; kế toán sửa tay được, app không ghi đè.
"""

import re
import unicodedata

CAT_DN = "Doanh nghiệp/HTX"
CAT_HKD = "Hộ KD/cá nhân"
CATEGORIES = (CAT_DN, CAT_HKD)

# Mẫu thuế mặt hàng (tên mẫu = "<tiêu đề> - <viết tắt công ty>"), ghi vào TK 33311.
T_KKKTN = "Không kê khai tính nộp"
T_KCT = "Không chịu thuế GTGT"
T_5, T_8, T_10 = "GTGT 5%", "GTGT 8%", "GTGT 10%"
VAT_TEMPLATES = ((T_KKKTN, 0.0), (T_KCT, 0.0), (T_5, 5.0), (T_8, 8.0), (T_10, 10.0))
SALES_TAX_TEMPLATE = "Thuế GTGT bán ra"  # mẫu thuế bán hàng (Sales Taxes and Charges Template)
VAT_ACCOUNT_NUMBER = "33311"

# Nông sản chưa chế biến / sơ chế thông thường (mặc định của app).
DEFAULT_BY_CATEGORY = {CAT_DN: T_KKKTN, CAT_HKD: T_5}

# Nhãn trong tệp "Thuế GTGT ngoại lệ" của kế toán trưởng -> tiêu đề mẫu.
_LABELS = {
    "mac dinh": None,
    "khong ke khai tinh nop": T_KKKTN,
    "khong chiu thue": T_KCT,
    "khong chiu thue gtgt": T_KCT,
    "5%": T_5,
    "8%": T_8,
    "10%": T_10,
}


def _plain(s) -> str:
    s = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def title_for_label(label) -> str | None:
    """Một nhãn -> tiêu đề mẫu thuế; "Mặc định" hoặc trống -> None."""
    if label is None or not str(label).strip():
        return None
    key = _plain(label).replace(" %", "%")
    if key not in _LABELS:
        raise ValueError(f"Nhãn thuế không hiểu: {label!r}")
    return _LABELS[key]


def templates_for_row(row: dict) -> dict | None:
    """Dòng quy tắc -> {loại khách: tiêu đề mẫu}.

    Hai cột riêng "dn" / "hkd" (tệp ngoại lệ của kế toán trưởng) thì lấy theo từng cột;
    một cột "nhan" thì theo templates_for_label. None = theo mặc định nhóm.
    """
    if "dn" in row or "hkd" in row:
        m = {}
        for cat, key in ((CAT_DN, "dn"), (CAT_HKD, "hkd")):
            t = title_for_label(row.get(key))
            if t == T_KKKTN and cat == CAT_HKD:
                raise ValueError("Bán hộ KD/cá nhân không thuộc diện 'Không kê khai tính nộp' (thuế suất 5%)")
            if t:
                m[cat] = t
        return m or None
    return templates_for_label(row.get("nhan"))


def templates_for_label(label) -> dict | None:
    """Nhãn thuế của một mặt hàng/nhóm -> {loại khách: tiêu đề mẫu}. None = theo mặc định nhóm.

    "Không kê khai tính nộp" chỉ áp với khách doanh nghiệp; bán hộ KD/cá nhân vẫn 5%.
    Các thuế suất khác (hàng đã chế biến, hàng không chịu thuế) áp như nhau cho mọi loại khách.
    """
    key = _plain(label).replace(" %", "%")
    if key not in _LABELS:
        raise ValueError(f"Nhãn thuế không hiểu: {label!r}")
    title = _LABELS[key]
    if title is None:
        return None
    if title == T_KKKTN:
        return dict(DEFAULT_BY_CATEGORY)
    return {c: title for c in CATEGORIES}


# --- Phân loại khách ------------------------------------------------------------------------

_DN_WORDS = re.compile(
    r"\b(cong ty|c\.? ?ty|cty|tnhh|co phan|ctcp|jsc|htx|hop tac xa|dntn|doanh nghiep tu nhan|"
    r"tong cong ty|chi nhanh cong ty|limited|company|corporation|co\.,? ?ltd)\b"
)
_ORG_WORDS = re.compile(
    r"\b(truong (dai hoc|cao dang|trung cap|thpt|thcs|tieu hoc|mam non|mau giao|pho thong|day nghe|quoc te)|"
    r"dai hoc|hoc vien|vien [a-z]|benh vien|nha may|xi nghiep|ban quan ly|uy ban|ubnd|"
    r"bo tham muu|quan khu|su doan|trung doan|lu doan|buu dien|ngan hang)\b"
)
_HKD_WORDS = re.compile(r"\b(ho kinh doanh|hkd|co so|cua hang|tap hoa|dai ly|nha phan phoi)\b")


def tax_id_digits(tax_id) -> str:
    """MST bỏ phần chi nhánh (-001) và ký tự lạ."""
    return re.sub(r"\D", "", str(tax_id or "").split("-")[0])


def classify_customer(name, tax_id) -> tuple[str, str]:
    """(loại thuế, lý do). Thứ tự: MST cá nhân/CCCD trước, rồi tên."""
    mst = tax_id_digits(tax_id)
    n = _plain(name)
    if len(mst) == 12:
        return CAT_HKD, "MST 12 số (số định danh cá nhân)"
    if len(mst) == 10 and mst.startswith("8"):
        return CAT_HKD, "MST cá nhân (bắt đầu bằng 8)"
    if _DN_WORDS.search(n):
        return CAT_DN, "Tên có Công ty/TNHH/Cổ phần/HTX/DNTN"
    if _HKD_WORDS.search(n):
        return CAT_HKD, "Tên hộ kinh doanh/cơ sở/cửa hàng"
    if _ORG_WORDS.search(n):
        return CAT_DN, "Tổ chức (trường, nhà máy, viện…)"
    if not mst:
        return CAT_HKD, "Không có MST → khách lẻ"
    return CAT_HKD, "Tên người, có MST riêng → cá nhân kinh doanh"


def choose_category(doc_choice, customer_category) -> str | None:
    """Loại thuế áp cho chứng từ: kế toán chọn trên chứng từ thắng; trống thì lấy theo hồ sơ khách."""
    return (doc_choice or "").strip() or (customer_category or "").strip() or None
