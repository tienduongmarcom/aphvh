"""Quy tắc cho mẫu in tiếng Việt (0.3.7) — thuần Python, kiểm thử không cần Frappe.

- Căn cứ mẫu chứng từ theo chế độ kế toán của từng công ty: APH theo TT133/2016, VH theo TT99/2025.
  Hộ kinh doanh (TT152/2025) không ghi căn cứ mẫu.
- Phiếu thu (01-TT) / phiếu chi (02-TT) từ Payment Entry: xác định thu hay chi theo phía tài khoản tiền mặt;
  tiền gửi ngân hàng in "chứng từ thu/chi ngân hàng" (không phải mẫu phiếu thu chi tiền mặt).
- Lý do thu/chi viết tiếng Việt (ERPNext tự sinh diễn giải tiếng Anh).
- Tên loại phiếu kho tiếng Việt (ERPNext lưu tên chuẩn tiếng Anh: Manufacture, Material Issue…).
"""

THONG_TU = {
    "APH": ("133/2016/TT-BTC", "26/08/2016", "Ban hành theo"),
    "VHT": ("99/2025/TT-BTC", "27/10/2025", "Kèm theo"),
}


def can_cu_mau(abbr) -> str:
    """Dòng căn cứ dưới "Mẫu số …" theo công ty; "" nếu không ghi (hộ kinh doanh, công ty lạ)."""
    t = THONG_TU.get((abbr or "").strip())
    if not t:
        return ""
    so, ngay, dong = t
    return f"({dong} Thông tư số {so} ngày {ngay} của Bộ Tài chính)"


# --- Thu / chi ------------------------------------------------------------------------------

def loai_thu_chi(payment_type, from_type, to_type) -> dict:
    """Payment Entry -> {"kieu": "thu" | "chi" | "chuyen", "tien_mat": bool}.

    from_type/to_type: loại tài khoản (Cash, Bank, Receivable…) của paid_from / paid_to.
    """
    if payment_type == "Receive":
        return {"kieu": "thu", "tien_mat": to_type == "Cash"}
    if payment_type == "Pay":
        return {"kieu": "chi", "tien_mat": from_type == "Cash"}
    # Internal Transfer: phía tiền mặt quyết định
    if to_type == "Cash" and from_type != "Cash":
        return {"kieu": "thu", "tien_mat": True}
    if from_type == "Cash" and to_type != "Cash":
        return {"kieu": "chi", "tien_mat": True}
    return {"kieu": "chuyen", "tien_mat": from_type == "Cash"}


def tieu_de_thu_chi(kieu: str, tien_mat: bool) -> tuple[str, str]:
    """(tiêu đề, mẫu số)."""
    if kieu == "thu":
        return ("PHIẾU THU", "01-TT") if tien_mat else ("CHỨNG TỪ THU NGÂN HÀNG", "")
    if kieu == "chi":
        return ("PHIẾU CHI", "02-TT") if tien_mat else ("CHỨNG TỪ CHI NGÂN HÀNG", "")
    return ("CHỨNG TỪ CHUYỂN TIỀN NỘI BỘ", "")


_REF = {
    "Sales Invoice": "hóa đơn",
    "Sales Order": "đơn hàng",
    "Purchase Invoice": "hóa đơn mua",
    "Purchase Order": "đơn mua hàng",
    "Journal Entry": "chứng từ",
    "Expense Claim": "đề nghị thanh toán",
    "Employee Advance": "đề nghị tạm ứng",
}


def _refs_text(refs) -> str:
    """refs: [(doctype, name)] -> "hóa đơn A, B; đơn hàng C"."""
    groups: dict[str, list] = {}
    for dt, name in refs or []:
        if name:
            groups.setdefault(_REF.get(dt, "chứng từ"), [])
            if name not in groups[_REF.get(dt, "chứng từ")]:
                groups[_REF.get(dt, "chứng từ")].append(name)
    return "; ".join(f"{k} {', '.join(v)}" for k, v in groups.items())


def ly_do(payment_type, party_type, refs, from_type=None, to_type=None, ghi_chu=None) -> str:
    """Lý do thu/chi tiếng Việt. ghi_chu: diễn giải người lập tự ghi (ưu tiên)."""
    if ghi_chu and str(ghi_chu).strip():
        return str(ghi_chu).strip()
    r = _refs_text(refs)
    theo = f" theo {r}" if r else ""
    dts = {dt for dt, _ in refs or []}
    if payment_type == "Internal Transfer":
        if from_type == "Bank" and to_type == "Cash":
            return "Rút tiền gửi ngân hàng nhập quỹ tiền mặt"
        if from_type == "Cash" and to_type == "Bank":
            return "Nộp tiền mặt vào tài khoản ngân hàng"
        return "Chuyển tiền giữa các tài khoản"
    if payment_type == "Receive":
        if party_type == "Customer":
            if dts and dts <= {"Sales Order"}:
                return f"Thu tiền đặt cọc{theo}"
            return f"Thu tiền hàng{theo}" if r else "Thu tiền khách hàng trả trước"
        if party_type == "Supplier":
            return f"Thu tiền nhà cung cấp hoàn trả{theo}"
        if party_type == "Employee":
            return f"Thu hoàn tạm ứng{theo}"
        return f"Thu tiền{theo}"
    if payment_type == "Pay":
        if party_type == "Supplier":
            if dts and dts <= {"Purchase Order"}:
                return f"Chi đặt cọc{theo}"
            return f"Chi trả tiền hàng{theo}" if r else "Chi trả trước cho nhà cung cấp"
        if party_type == "Customer":
            return f"Chi trả lại tiền cho khách hàng{theo}"
        if party_type == "Employee":
            return f"Chi tạm ứng, thanh toán cho nhân viên{theo}"
        return f"Chi tiền{theo}"
    return ""


TIEN_TE = {"VND": "đồng", "USD": "đô la Mỹ", "EUR": "euro", "CNY": "nhân dân tệ"}


def chu_tien_te(currency) -> str:
    return TIEN_TE.get((currency or "VND").upper(), currency or "")


# --- Phiếu kho --------------------------------------------------------------------------------

LOAI_PHIEU_KHO = {
    "Material Issue": "Xuất kho",
    "Material Receipt": "Nhập kho",
    "Material Transfer": "Chuyển kho",
    "Material Transfer for Manufacture": "Xuất nguyên liệu cho sản xuất",
    "Material Consumption for Manufacture": "Xuất dùng cho sản xuất",
    "Manufacture": "Sản xuất",
    "Repack": "Đóng gói / đổi mã",
    "Send to Subcontractor": "Xuất gia công",
    "Disassemble": "Tháo dỡ",
    "Receive from Customer": "Nhận hàng của khách",
}


def ten_loai_phieu_kho(name) -> str:
    """Tên loại phiếu kho tiếng Việt; loại tự đặt (đã tiếng Việt) giữ nguyên."""
    return LOAI_PHIEU_KHO.get(name or "", name or "")


# --- Thuế suất trên phiếu bán hàng -------------------------------------------------------------

def nhan_thue_suat(template_title, rate=None) -> str:
    """Nhãn cột thuế suất: KKKNT (không kê khai, tính nộp), KCT (không chịu thuế), hoặc "5%"."""
    t = (template_title or "").lower()
    if "không kê khai" in t:
        return "KKKNT"
    if "không chịu thuế" in t:
        return "KCT"
    if rate is None:
        return ""
    r = float(rate)
    return f"{int(r)}%" if r == int(r) else f"{r:g}%".replace(".", ",")


# Mẫu in mặc định ERPNext tự đặt lúc cài (không phải người dùng chọn). Tên đổi theo phiên bản:
# ERPNext ≤ 16.36 dùng with Item Image, 16.50 Modern with Images, 16.51.1 Classic.
# Chỉ nhận đúng tên của chính DocType; mẫu người dùng tự chọn khác vẫn được giữ.
MAU_MAC_DINH_ERPNEXT = ("{dt} with Item Image", "{dt} Modern with Images", "{dt} Classic")


def la_mau_mac_dinh_erpnext(doctype: str, ten_mau: str | None) -> bool:
    """True nếu mẫu in mặc định hiện tại là mẫu ERPNext tự đặt (coi như chưa ai chọn) hoặc chưa có (thuần)."""
    if not ten_mau:
        return True
    return ten_mau in {m.format(dt=doctype) for m in MAU_MAC_DINH_ERPNEXT}
