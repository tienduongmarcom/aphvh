"""Dữ liệu cần rà soát & điều chỉnh dần (0.11.1, cờ kh_aph_data_review). Đặc tả docs/dac-ta-0.11.1.md mục 3.6.

Không chặn, không sửa dữ liệu: liệt kê dòng có dấu hiệu lệch để kế toán sửa dần (Asset, Stock Reconciliation, Purchase Invoice,
Repost Item Valuation chuẩn). Quy tắc phân loại thuần ở kh_aph.data_review_rules.
"""

from lab9x.vn_words import so_vn
import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

from kh_aph import data_review_rules as R


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not cint(frappe.conf.get("kh_aph_data_review")):
        frappe.throw("Báo cáo rà soát dữ liệu chưa được bật")
    cols = [
        {"fieldname": "nhom", "label": "Nhóm", "fieldtype": "Data", "width": 90},
        {"fieldname": "ma", "label": "Mã kiểm", "fieldtype": "Data", "width": 60},
        {"fieldname": "loai", "label": "Loại chứng từ", "fieldtype": "Data", "width": 130},
        {"fieldname": "ten", "label": "Chứng từ", "fieldtype": "Dynamic Link", "options": "loai", "width": 180},
        {"fieldname": "mo_ta", "label": "Dấu hiệu", "fieldtype": "Data", "width": 420},
        {"fieldname": "gia_tri", "label": "Giá trị liên quan", "fieldtype": "Float", "width": 140},
    ]
    rows = []
    for nhom, ham in (("Tài sản", _tai_san), ("Giá tạm", _gia_tam), ("Tồn kho", _ton_kho), ("Kho bồn", _kho_bon)):
        if not filters.nhom or filters.nhom == nhom:
            rows += [{"nhom": nhom, **r} for r in ham(filters.company)]
    return cols, rows


def _co(company):
    return {"company": company} if company else {}


def _tai_san(company):
    if not frappe.db.exists("DocType", "Asset"):
        return []
    xuong = {}
    if frappe.get_meta("Cost Center").has_field("kh_aph_loai_ttcp"):
        xuong = {c.name: c for c in frappe.get_all("Cost Center", {"kh_aph_loai_ttcp": ["is", "set"], **_co(company)},
                                                   ["name", "cost_center_name", "kh_aph_loai_ttcp"])}
    ten_ttcp = {c.cost_center_name: c.name for c in xuong.values()}
    out = []
    ng = "net_purchase_amount" if frappe.get_meta("Asset").has_field("net_purchase_amount") else "gross_purchase_amount"
    for a in frappe.get_all("Asset", {"docstatus": ["<", 2], **_co(company)},
                            ["name", "company", f"{ng} as nguyen_gia", "opening_accumulated_depreciation",
                             "opening_number_of_booked_depreciations", "location", "cost_center", "asset_category"]):
        fb = frappe.get_all("Asset Finance Book", {"parent": a.name}, ["total_number_of_depreciations",
                            "frequency_of_depreciation"], order_by="idx", limit=1)
        tong_ky = cint(fb[0].total_number_of_depreciations) if fb else 0
        tan_suat = cint(fb[0].frequency_of_depreciation) if fb else 1
        tk_kh = frappe.db.get_value("Asset Category Account", {"parent": a.asset_category, "company_name": a.company},
                                    "depreciation_expense_account") if a.asset_category else None
        so_tk = frappe.get_cached_value("Account", tk_kh, "account_number") if tk_kh else None
        loai_ttcp = xuong[a.cost_center].kh_aph_loai_ttcp if a.cost_center in xuong else None
        ttcp_cua_vi_tri = ten_ttcp.get(a.location)
        for ma, mo_ta in R.kiem_tai_san(flt(a.nguyen_gia), flt(a.opening_accumulated_depreciation),
                                        tong_ky, cint(a.opening_number_of_booked_depreciations), tan_suat,
                                        a.cost_center, ttcp_cua_vi_tri, loai_ttcp, so_tk):
            out.append({"ma": ma, "loai": "Asset", "ten": a.name, "mo_ta": mo_ta, "gia_tri": flt(a.nguyen_gia)})
    return out


def _gia_tam(company):
    out = []
    if frappe.get_meta("Purchase Receipt").has_field("kh_aph_gia_tam"):
        for pr in frappe.db.sql("""SELECT pr.name, pr.base_net_total FROM `tabPurchase Receipt` pr
                WHERE pr.docstatus=1 AND pr.kh_aph_gia_tam=1 {co} AND NOT EXISTS (
                  SELECT 1 FROM `tabPurchase Invoice Item` pii JOIN `tabPurchase Invoice` pi ON pi.name=pii.parent
                  WHERE pii.purchase_receipt=pr.name AND pi.docstatus=1)""".format(
                co="AND pr.company=%(c)s" if company else ""), {"c": company}, as_dict=True):
            out.append({"ma": "b", "loai": "Purchase Receipt", "ten": pr.name, "gia_tri": flt(pr.base_net_total),
                        "mo_ta": "Phiếu nhập giá tạm chưa có hóa đơn mua chốt giá"})
    if frappe.get_meta("Stock Reconciliation").has_field("kh_aph_gia_tam"):
        for r in frappe.db.sql("""SELECT sr.name, i.item_code, i.warehouse, i.valuation_rate, sr.posting_date
                FROM `tabStock Reconciliation` sr JOIN `tabStock Reconciliation Item` i ON i.parent=sr.name
                WHERE sr.docstatus=1 AND sr.kh_aph_gia_tam=1 {co} AND NOT EXISTS (
                  SELECT 1 FROM `tabStock Reconciliation` s2 JOIN `tabStock Reconciliation Item` i2 ON i2.parent=s2.name
                  WHERE s2.docstatus=1 AND IFNULL(s2.kh_aph_gia_tam,0)=0 AND i2.item_code=i.item_code
                    AND i2.warehouse=i.warehouse AND s2.posting_date>=sr.posting_date)""".format(
                co="AND sr.company=%(c)s" if company else ""), {"c": company}, as_dict=True):
            out.append({"ma": "b", "loai": "Stock Reconciliation", "ten": r.name, "gia_tri": flt(r.valuation_rate),
                        "mo_ta": f"Tồn {r.item_code} tại {r.warehouse} đang giá tạm {so_vn(flt(r.valuation_rate), 0)}"})
    return out


def _ton_kho(company):
    out = []
    kho_cty = {w.name: w for w in frappe.get_all("Warehouse", {"is_group": 0, **_co(company)}, ["name", "account"])}
    tk_nhom = {}
    for b in frappe.get_all("Bin", {"warehouse": ["in", list(kho_cty) or [""]]},
                            ["item_code", "warehouse", "actual_qty", "stock_value"]):
        for ma, mo_ta in R.kiem_ton(flt(b.actual_qty), flt(b.stock_value)):
            out.append({"ma": ma, "loai": "Item", "ten": b.item_code, "gia_tri": flt(b.stock_value),
                        "mo_ta": f"{b.warehouse}: {mo_ta}"})
        tk_kho = kho_cty[b.warehouse].account
        if not tk_kho or not flt(b.actual_qty):
            continue
        nhom = frappe.get_cached_value("Item", b.item_code, "item_group")
        key = (nhom, frappe.get_cached_value("Warehouse", b.warehouse, "company"))
        if key not in tk_nhom:
            from frappe.utils.nestedset import get_ancestors_of
            tk_nhom[key] = None
            for g in [nhom, *(get_ancestors_of("Item Group", nhom) or [])]:
                v = frappe.db.get_value("Item Default", {"parent": g, "parenttype": "Item Group", "company": key[1]},
                                        "default_inventory_account")
                if v:
                    tk_nhom[key] = v
                    break
        if tk_nhom[key] and tk_nhom[key] != tk_kho:
            out.append({"ma": "d", "loai": "Item", "ten": b.item_code, "gia_tri": flt(b.actual_qty),
                        "mo_ta": f"Nằm ở {b.warehouse} (kho gắn {tk_kho}) nhưng nhóm hàng ghi sổ vào {tk_nhom[key]}"})
    return out


def _kho_bon(company):
    if not frappe.get_meta("Warehouse").has_field("kh_aph_kho_bon"):
        return []
    out = []
    moc = add_days(getdate(nowdate()), -R.NGAY_BON_TOI_DA)
    for w in frappe.get_all("Warehouse", {"kh_aph_kho_bon": 1, **_co(company)}, pluck="name"):
        ton = flt(frappe.db.sql("SELECT SUM(actual_qty) FROM `tabBin` WHERE warehouse=%s", w)[0][0])
        if ton <= 0:
            continue
        lan_ve_0 = frappe.db.sql("""SELECT MAX(posting_date) FROM `tabStock Entry`
            WHERE kh_aph_vet_bon=%s AND docstatus=1""", w)[0][0] if frappe.get_meta("Stock Entry").has_field(
            "kh_aph_vet_bon") else None
        if not lan_ve_0 or getdate(lan_ve_0) < moc:
            out.append({"ma": "e", "loai": "Warehouse", "ten": w, "gia_tri": ton,
                        "mo_ta": f"Bồn còn {so_vn(ton, 0)} trên sổ, chưa vét về 0 trong {R.NGAY_BON_TOI_DA} ngày"})
    return out
