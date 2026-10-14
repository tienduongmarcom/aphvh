"""Số dư đầu kỳ (0.12.1, cờ `kh_aph_dau_ky`, mặc định tắt). Đặc tả docs/dac-ta-0.12.0-0.12.1.md mục 3.

Nạp bằng công cụ chuẩn ERPNext (Stock Reconciliation mục đích Opening Stock, Opening Invoice Creation Tool,
Journal Entry loại Opening Entry), đối ứng tài khoản tạm 9990. App không tự ghi chứng từ đầu kỳ; chỉ:
- lưu số theo bảng nguồn (APH So du dau ky nguon) để đối chiếu,
- báo cáo "Doi chieu so du dau ky": từng loại, số dư tài khoản tạm, sổ kho so với sổ cái,
- nút "Chốt số dư đầu kỳ": khi bốn loại đã khớp thì khóa tháng đầu kỳ bằng khóa kỳ của 0.11.4.
Lượt này 4 loại (tồn kho, tiền, công nợ khách, công nợ NCC); TSCĐ, CCDC, vay, vốn để lượt sau (dòng "Khác").
"""
import json
import os

import frappe
from frappe.utils import cint, flt, getdate
from lab9x import du_lieu as D

FLAG = "kh_aph_dau_ky"
DT_NGUON = "APH So du dau ky nguon"
TK_TAM_MAC_DINH = "9990"
KHAC = "Khác (TSCĐ, CCDC, vay, vốn… — lượt sau)"


def enabled():
    return cint(frappe.conf.get(FLAG))


def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_dau_ky trước khi cài")
    frappe.reload_doc("kh_aph", "doctype", frappe.scrub(DT_NGUON))
    return {"doctype": DT_NGUON}


def can_quyen():
    if not enabled():
        frappe.throw("Số dư đầu kỳ 0.12.1 chưa được bật")
    from kh_aph.constants import ROLE_NO_COST
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles())
    if not (roles & {"Accounts Manager", "Accounts User", "System Manager"}) or ROLE_NO_COST in roles:
        frappe.throw("Cần quyền kế toán", frappe.PermissionError)


def ngay_mac_dinh():
    """Ngày đầu kỳ: site_config kh_aph_ngay_dau_ky, nếu không thì ngay_chot trong khach.json của app."""
    if frappe.conf.get("kh_aph_ngay_dau_ky"):
        return str(getdate(frappe.conf.get("kh_aph_ngay_dau_ky")))
    try:
        p = os.path.join(frappe.get_app_path("kh_aph"), "..", "khach", "aph-vh", "khach.json")
        with open(p, encoding="utf-8") as f:
            return str(getdate(json.load(f)["ngay_chot"]))
    except Exception:
        return None


def tk_tam(company):
    so = str(frappe.conf.get("kh_aph_tk_doi_ung_dau_ky") or TK_TAM_MAC_DINH)
    ten = frappe.db.get_value("Account", {"company": company, "account_number": so, "is_group": 0}, "name")
    if not ten:
        frappe.throw(f"{company} chưa có tài khoản {so} (tài khoản tạm nhập số dư đầu kỳ)")
    return ten


def validate_nguon(doc, method=None):
    can_quyen()
    trung = frappe.db.get_value(DT_NGUON, {"company": doc.company, "ngay": doc.ngay, "loai": doc.loai,
                                           "name": ["!=", doc.name]}, "name")
    if trung:
        frappe.throw(f"Đã có số nguồn \"{doc.loai}\" của {doc.company} ngày {doc.ngay}: sửa bản {trung}")


def so_lieu(company, ngay):
    """Số trên sổ theo loại (dư Nợ dương; công nợ NCC đổi dấu thành số dương) và các số kiểm."""
    tam = tk_tam(company)
    ngay = str(getdate(ngay))
    dong = frappe.db.sql("""SELECT g.voucher_type, g.account, a.account_type, SUM(g.debit-g.credit) AS so
        FROM `tabGL Entry` g JOIN `tabAccount` a ON a.name=g.account
        WHERE g.company=%(c)s AND g.is_cancelled=0 AND g.posting_date<=%(d)s AND g.account!=%(t)s
          AND (g.voucher_type, g.voucher_no) IN (SELECT voucher_type, voucher_no FROM `tabGL Entry`
                WHERE company=%(c)s AND account=%(t)s AND is_cancelled=0 AND posting_date<=%(d)s)
        GROUP BY g.voucher_type, g.account, a.account_type""", {"c": company, "d": ngay, "t": tam}, as_dict=True)
    so = {loai: 0.0 for loai in (*D.LOAI_DAU_KY, KHAC)}
    for r in dong:
        v = flt(r.so)
        if r.voucher_type == "Stock Reconciliation":
            so["Tồn kho"] += v
        elif r.voucher_type == "Sales Invoice":
            so["Công nợ khách"] += v
        elif r.voucher_type == "Purchase Invoice":
            so["Công nợ nhà cung cấp"] -= v
        elif r.voucher_type == "Journal Entry" and r.account_type in ("Cash", "Bank"):
            so["Tiền mặt và ngân hàng"] += v
        else:
            so[KHAC] += v
    du_tam = flt(frappe.db.sql("""SELECT SUM(debit-credit) FROM `tabGL Entry` WHERE company=%s AND account=%s
        AND is_cancelled=0 AND posting_date<=%s""", (company, tam, ngay))[0][0])
    so_kho = flt(frappe.db.sql("""SELECT SUM(sle.stock_value_difference) FROM `tabStock Ledger Entry` sle
        WHERE sle.company=%s AND sle.is_cancelled=0 AND sle.posting_date<=%s""", (company, ngay))[0][0])
    so_cai_kho = flt(frappe.db.sql("""SELECT SUM(g.debit-g.credit) FROM `tabGL Entry` g JOIN `tabAccount` a ON a.name=g.account
        WHERE g.company=%s AND g.is_cancelled=0 AND g.posting_date<=%s AND a.account_type='Stock'""", (company, ngay))[0][0])
    return {"so": {k: round(v, 2) for k, v in so.items()}, "tk_tam": tam, "du_tam": round(du_tam, 2),
            "so_kho": round(so_kho, 2), "so_cai_kho": round(so_cai_kho, 2)}


def doi_chieu(company, ngay):
    can_quyen()
    s = so_lieu(company, ngay)
    nguon = {}
    for r in frappe.get_all(DT_NGUON, {"company": company, "ngay": getdate(ngay)}, ["loai", "so_tien"]):
        nguon[r.loai] = flt(r.so_tien)
    dong = []
    for loai in D.LOAI_DAU_KY:
        so_so = s["so"][loai]
        dong.append({"loai": loai, "so_nguon": nguon.get(loai), "so_so": so_so,
                     "chenh": (so_so - nguon[loai]) if loai in nguon else None,
                     "trang_thai": D.trang_thai_dau_ky(nguon.get(loai, 0), so_so, loai in nguon)})
    dong.append({"loai": KHAC, "so_so": s["so"][KHAC], "trang_thai": "Lượt sau" if s["so"][KHAC] else ""})
    tong = sum(s["so"].values()) - 2 * s["so"]["Công nợ nhà cung cấp"]  # công nợ NCC đã đổi dấu: đổi lại về dư Nợ
    dong.append({"loai": f"Số dư tài khoản tạm {s['tk_tam']}", "so_so": s["du_tam"],
                 "chenh": D.can_bang_tk_tam(s["du_tam"], tong),
                 "trang_thai": "Về 0" if abs(s["du_tam"]) < 1 else "Còn số dư = phần chưa nạp"})
    lech_kho = round(s["so_kho"] - s["so_cai_kho"], 2)
    dong.append({"loai": "Kiểm: sổ kho − sổ cái tài khoản kho", "so_nguon": s["so_kho"], "so_so": s["so_cai_kho"],
                 "chenh": lech_kho, "trang_thai": D.KHOP if abs(lech_kho) < 1 else D.LECH})
    return dong


@frappe.whitelist(methods=["POST"])
def chot_dau_ky(company, ngay, ly_do):
    """Bốn loại phải Khớp; rồi khóa tháng chứa ngày đầu kỳ (Accounting Period chuẩn, qua kh_aph.quan_tri.khoa_ky)."""
    can_quyen()
    from kh_aph.constants import ROLE_NO_COST
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and ("Accounts Manager" not in roles or ROLE_NO_COST in roles):
        frappe.throw("Chỉ kế toán trưởng được chốt số dư đầu kỳ", frappe.PermissionError)
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do chốt")
    chua = [f"{d['loai']}: {d['trang_thai']}" for d in doi_chieu(company, ngay)
            if d["loai"] in D.LOAI_DAU_KY and d["trang_thai"] != D.KHOP]
    if chua:
        frappe.throw("Chưa chốt được, còn: " + "; ".join(chua))
    from kh_aph.quan_tri import khoa_ky
    kq = khoa_ky(company, str(getdate(ngay))[:7], f"Chốt số dư đầu kỳ {ngay}. {ly_do.strip()}")
    return {"chot": True, **kq}


def has_permission(doc, ptype=None, user=None):
    """Frappe 16: chỉ trả True (không ý kiến) hoặc False (chặn). Hồ sơ không xem giá vốn (Dũng) bị chặn."""
    if not enabled():
        return False
    from kh_aph.constants import ROLE_NO_COST
    return ROLE_NO_COST not in frappe.get_roles(user)


def query_conditions(user=None):
    """Danh sách số nguồn: chặn hồ sơ không xem giá vốn (Dũng) và khi cờ tắt."""
    from kh_aph.constants import ROLE_NO_COST
    if not enabled() or ROLE_NO_COST in frappe.get_roles(user):
        return "1=0"
    return ""
