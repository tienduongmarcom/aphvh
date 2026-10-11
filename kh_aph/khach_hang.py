"""Cấu hình khách hàng và bộ nạp (0.6.0): một file JSON mô tả khách, một lệnh dựng toàn bộ hệ thống trên site trắng.

Lệnh:  bench --site <site> execute kh_aph.khach_hang.ap_dung --kwargs '{"duong_dan": "/path/khach.json"}'
Chạy lại an toàn (chỉ bổ sung phần thiếu). Mẫu cấu hình: deploy/khach/mau-aph-vh.json.
"""

import json
import re

THONG_TU = {"133": "aph", "99": "vh", "152": "mk"}  # TT133 -> bộ tài khoản 'aph'; TT99 -> 'vh'; TT152 (hộ kinh doanh) -> 'mk'
# Đơn vị theo dõi nội bộ (không MST, không VAT, vd TL): khai "noi_bo": true thay cho "thong_tu" -> bộ tài khoản 'tl'.
ABBR_RE = re.compile(r"^[A-Z0-9]{2,6}$")
NAM_TC_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
# Cách đưa dữ liệu vào hệ thống của khách:
#   tu_nhap          khách tự nhập toàn bộ (mình không chạm dữ liệu thật)
#   import_mot_phan  khách gửi file mẫu; mình import danh mục + số dư đầu kỳ, khách nhập phiếu từ ngày chốt
CHE_DO_DU_LIEU = ("tu_nhap", "import_mot_phan")


def kiem_cau_hinh(cfg: dict) -> list:
    """Thuần: trả danh sách lỗi (rỗng = hợp lệ)."""
    loi = []
    if not cfg.get("khach_hang"):
        loi.append("thiếu 'khach_hang' (tên khách)")
    if not NAM_TC_RE.match(str(cfg.get("nam_tai_chinh_bat_dau", "01-01"))):
        loi.append("'nam_tai_chinh_bat_dau' phải dạng MM-DD (ví dụ 01-01)")
    che_do = cfg.get("che_do_du_lieu", "tu_nhap")
    if che_do not in CHE_DO_DU_LIEU:
        loi.append("'che_do_du_lieu' phải là " + " hoặc ".join(CHE_DO_DU_LIEU))
    chot = cfg.get("ngay_chot")
    if chot is not None:
        import datetime

        try:
            datetime.date.fromisoformat(str(chot))
        except ValueError:
            loi.append("'ngay_chot' phải dạng YYYY-MM-DD hợp lệ")
    elif che_do == "import_mot_phan":
        loi.append("chế độ 'import_mot_phan' bắt buộc có 'ngay_chot' (ngày chốt số dư đầu kỳ)")
    cts = cfg.get("cong_ty") or []
    if not cts:
        loi.append("cần ít nhất một công ty trong 'cong_ty'")
    thay_ten, thay_abbr = set(), set()
    for i, c in enumerate(cts, 1):
        t = c.get("ten")
        if not t:
            loi.append(f"công ty #{i}: thiếu 'ten'")
        elif t in thay_ten:
            loi.append(f"công ty #{i}: trùng tên {t}")
        thay_ten.add(t)
        ab = c.get("abbr", "")
        if not ABBR_RE.match(ab):
            loi.append(f"công ty #{i}: 'abbr' phải 2–6 ký tự chữ hoa/số")
        elif ab in thay_abbr:
            loi.append(f"công ty #{i}: trùng viết tắt {ab}")
        thay_abbr.add(ab)
        if c.get("loai_hinh") and c["loai_hinh"] not in ("thuong_mai", "san_xuat"):
            loi.append(f"công ty #{i}: 'loai_hinh' phải là thuong_mai hoặc san_xuat")
        if c.get("noi_bo"):
            if c.get("thong_tu") or c.get("mst"):
                loi.append(f"công ty #{i}: đơn vị nội bộ không khai 'thong_tu' và 'mst'")
        elif str(c.get("thong_tu")) not in THONG_TU:
            loi.append(f"công ty #{i}: 'thong_tu' phải là 133, 99 hoặc 152 (hoặc khai \"noi_bo\": true)")
        if any(k in c for k in ("nha_may", "kho_them", "ten_nha_may")):
            loi.append(f"công ty #{i}: từ 0.8.0 không khai kho trong cấu hình (khách tự tạo kho trên giao diện)")
    return loi


def loai_cua(c: dict) -> str:
    return "tl" if c.get("noi_bo") else THONG_TU[str(c["thong_tu"])]


def doc_cau_hinh(duong_dan: str) -> dict:
    with open(duong_dan, encoding="utf-8") as f:
        cfg = json.load(f)
    loi = kiem_cau_hinh(cfg)
    if loi:
        raise ValueError("Cấu hình khách không hợp lệ: " + "; ".join(loi))
    return cfg


def _wizard(cfg: dict):
    import datetime

    import frappe
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    c = cfg["cong_ty"][0]
    nam = datetime.date.today().year
    mm, dd = str(cfg.get("nam_tai_chinh_bat_dau", "01-01")).split("-")
    bd = datetime.date(nam, int(mm), int(dd))
    kt = datetime.date(nam + 1, int(mm), int(dd)) - datetime.timedelta(days=1) if (mm, dd) != ("01", "01") else datetime.date(nam, 12, 31)
    setup_complete({"language": "vi", "country": "Vietnam", "timezone": "Asia/Ho_Chi_Minh", "currency": "VND", "full_name": "Quản trị",
                    "company_name": c["ten"], "company_abbr": c["abbr"], "chart_of_accounts": "Standard",
                    "fy_start_date": bd.isoformat(), "fy_end_date": kt.isoformat(), "company_tagline": cfg["khach_hang"],
                    "bank_account": "Tiền gửi ngân hàng"})
    frappe.db.commit()


def ap_dung(duong_dan: str = None, cfg: dict = None) -> list:
    import frappe
    from frappe.installer import update_site_config

    from kh_aph import cai_ban_trang as C

    if cfg is None:
        cfg = doc_cau_hinh(duong_dan)
    else:
        loi = kiem_cau_hinh(cfg)
        if loi:
            raise ValueError("Cấu hình khách không hợp lệ: " + "; ".join(loi))
    # khai loại đơn vị theo viết tắt để các chức năng khác của app nhận ra công ty
    extra = dict(frappe.conf.get("kh_aph_loai") or {})
    extra.update({c["abbr"]: loai_cua(c) for c in cfg["cong_ty"]})
    update_site_config("kh_aph_loai", extra)
    frappe.conf["kh_aph_loai"] = extra
    if not frappe.is_setup_complete():
        _wizard(cfg)
    ket_qua = []
    for c in cfg["cong_ty"]:
        ten = frappe.db.get_value("Company", {"abbr": c["abbr"]}, "name")
        if not ten:
            frappe.get_doc({"doctype": "Company", "company_name": c["ten"], "abbr": c["abbr"], "default_currency": "VND", "country": "Vietnam",
                            "create_chart_of_accounts_based_on": "Standard Template", "chart_of_accounts": "Standard"}).insert(ignore_permissions=True)
            frappe.db.commit()
            ten = c["ten"]
        if c.get("mst"):
            frappe.db.set_value("Company", ten, "tax_id", c["mst"])
        if c.get("noi_bo") and frappe.get_meta("Company").has_field("kh_aph_noi_bo"):
            frappe.db.set_value("Company", ten, "kh_aph_noi_bo", 1)  # đơn vị theo dõi nội bộ: không VAT, ô "Khách lấy hóa đơn" luôn Không
        nhom = [(n["ten"], n.get("tk")) for n in c["nhom_hang"]] if c.get("nhom_hang") else C.nhom_theo_loai_hinh(loai_cua(c), c.get("loai_hinh"))
        # nhóm hàng khai theo tài khoản số hiệu: chuyển tk (số hiệu) giữ nguyên, bộ cài tra tài khoản theo số hiệu
        ket_qua.append(C.cai(ten, loai_cua(c), nhom))
    frappe.db.commit()
    return ket_qua
