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
    tam = phieu_gia_tam(company, ngay)
    dong.append({"loai": f"Phiếu tồn đầu kỳ còn giá tạm: {len(tam)} phiếu", "so_so": sum(t.gia_tri for t in tam),
                 "trang_thai": "Còn giá tạm — chưa chốt được" if tam else ""})
    lech_kho = round(s["so_kho"] - s["so_cai_kho"], 2)
    dong.append({"loai": "Kiểm: sổ kho − sổ cái tài khoản kho", "so_nguon": s["so_kho"], "so_so": s["so_cai_kho"],
                 "chenh": lech_kho, "trang_thai": D.KHOP if abs(lech_kho) < 1 else D.LECH})
    return dong


def phieu_gia_tam(company, ngay):
    """Phiếu tồn đầu kỳ (Stock Reconciliation mục đích Opening Stock) tại ngày đầu kỳ còn đánh dấu Giá tạm (rà soát dòng 15)."""
    if not frappe.get_meta("Stock Reconciliation").has_field("kh_aph_gia_tam"):
        return []
    return frappe.db.sql("""SELECT sr.name, SUM(i.amount) AS gia_tri FROM `tabStock Reconciliation` sr
        JOIN `tabStock Reconciliation Item` i ON i.parent=sr.name
        WHERE sr.company=%s AND sr.docstatus=1 AND sr.purpose='Opening Stock' AND sr.posting_date=%s AND sr.kh_aph_gia_tam=1
        GROUP BY sr.name""", (company, str(getdate(ngay))), as_dict=True)


@frappe.whitelist()
def ngay_dau_ky():
    """Ngày đầu kỳ cho bộ lọc báo cáo (site_config kh_aph_ngay_dau_ky hoặc khach.json)."""
    can_quyen()
    return ngay_mac_dinh()


@frappe.whitelist(methods=["POST"])
def chot_dau_ky(company, ngay, ly_do):
    """Bốn loại phải Khớp, không còn phiếu tồn giá tạm; rồi khóa từ đầu tháng đến HẾT NGÀY đầu kỳ (Accounting Period chuẩn).
    Chứng từ sau ngày đầu kỳ (kể cả cùng tháng) vẫn ghi được."""
    can_quyen()
    from kh_aph.constants import ROLE_NO_COST
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and ("Accounts Manager" not in roles or ROLE_NO_COST in roles):
        frappe.throw("Chỉ kế toán trưởng được chốt số dư đầu kỳ", frappe.PermissionError)
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do chốt")
    chua = [f"{d['loai']}: {d['trang_thai']}" for d in doi_chieu(company, ngay)
            if d["loai"] in D.LOAI_DAU_KY and d["trang_thai"] != D.KHOP]
    tam = phieu_gia_tam(company, ngay)
    if tam:
        chua.append("phiếu tồn còn giá tạm: " + ", ".join(t.name for t in tam[:5]))
    if chua:
        frappe.throw("Chưa chốt được, còn: " + "; ".join(chua))
    return {"chot": True, **khoa_den_ngay(company, ngay, f"Chốt số dư đầu kỳ {ngay}. {ly_do.strip()}")}


def khoa_den_ngay(company, ngay, ly_do):
    """Accounting Period từ đầu tháng đến ngày đầu kỳ, khóa mọi loại chứng từ ghi sổ (như khóa kỳ 0.11.4)."""
    cuoi = getdate(ngay)
    dau = cuoi.replace(day=1)
    # Kỳ đã có chồng lên khoảng này (khóa tháng 0.11.4 hoặc lần chốt trước): nới kỳ đó thay vì tạo kỳ chồng (ERPNext cấm).
    co = frappe.db.sql("""SELECT name FROM `tabAccounting Period` WHERE company=%s AND start_date<=%s AND end_date>=%s
        ORDER BY start_date LIMIT 1""", (company, cuoi, dau))
    if co:
        ap = frappe.get_doc("Accounting Period", co[0][0])
        ap.start_date = min(getdate(ap.start_date), dau)
        ap.end_date = max(getdate(ap.end_date), cuoi)
        ap.disabled = 0
        ap.save(ignore_permissions=True)
    else:
        loai = list(dict.fromkeys(frappe.get_hooks("period_closing_doctypes") or []))
        ap = frappe.get_doc({"doctype": "Accounting Period", "period_name": f"Chốt đầu kỳ {cuoi}", "company": company,
                             "start_date": dau, "end_date": cuoi,
                             "closed_documents": [{"document_type": dt, "closed": 1} for dt in loai]})
        ap.insert(ignore_permissions=True)  # quyền đã kiểm: kế toán trưởng
    ap.add_comment("Comment", f"{ly_do} — bởi {frappe.session.user}")
    return {"ky": ap.name, "da_khoa": True, "tu": str(getdate(ap.start_date)), "den": str(getdate(ap.end_date))}


def khach_chua_co_cong_no(company, ngay):
    """Khách có đơn / giao / hóa đơn / phiếu thu SAU ngày đầu kỳ mà chưa có hóa đơn đầu kỳ (is_opening) của công ty."""
    ngay = str(getdate(ngay))
    return frappe.db.sql("""SELECT k.customer, COUNT(*) AS so_ct, SUM(k.ban) AS tong_ban, SUM(k.thu) AS tong_thu,
            MAX(k.ngay) AS lan_cuoi FROM (
          SELECT customer, grand_total AS ban, 0 AS thu, posting_date AS ngay FROM `tabSales Invoice`
            WHERE company=%(c)s AND docstatus=1 AND posting_date>%(d)s AND IFNULL(is_opening,'No')='No'
          UNION ALL SELECT customer, 0, 0, posting_date FROM `tabDelivery Note`
            WHERE company=%(c)s AND docstatus=1 AND posting_date>%(d)s
          UNION ALL SELECT customer, 0, 0, transaction_date FROM `tabSales Order`
            WHERE company=%(c)s AND docstatus=1 AND transaction_date>%(d)s
          UNION ALL SELECT party, 0, paid_amount, posting_date FROM `tabPayment Entry`
            WHERE company=%(c)s AND docstatus=1 AND party_type='Customer' AND posting_date>%(d)s
        ) k WHERE NOT EXISTS (SELECT 1 FROM `tabSales Invoice` o WHERE o.customer=k.customer AND o.company=%(c)s
            AND o.docstatus=1 AND o.is_opening='Yes')
        GROUP BY k.customer ORDER BY tong_ban DESC""", {"c": company, "d": ngay}, as_dict=True)


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
