"""Quản trị (0.11.4, cờ `kh_aph_quan_tri`, mặc định tắt). Đặc tả docs/dac-ta-0.11.4.md.

- R099–R101, R104: báo cáo "Lai gop quan tri" cộng ngang 4 đơn vị (không phải hợp nhất), cờ lãi tạm tính.
- R102–R103: báo cáo "Dong tien 7 30 ngay", loại đối tác nội bộ.
- R105: khóa / mở khóa kỳ theo tháng bằng Accounting Period chuẩn ERPNext (bắt buộc lý do, nhật ký).
- R039: ghi nhận khách xác nhận công nợ, cảnh báo mềm khi đơn bán của khách quá hạn xác nhận.
Chỉ đọc sổ; không tự ghi chứng từ.
"""
import calendar
import datetime

import frappe
from frappe.utils import cint, flt, getdate, nowdate
from lab9x import quan_tri as Q
from lab9x.vn_words import so_vn

FLAG = "kh_aph_quan_tri"
F_XN_NGAY = "kh_aph_xac_nhan_cong_no_ngay"
F_XN_BOI = "kh_aph_xac_nhan_cong_no_boi"
F_XN_SO_DU = "kh_aph_so_du_da_xac_nhan"
F_SO_NGAY = "kh_aph_so_ngay_xac_nhan_cong_no"
F_DON_BAN = "kh_aph_don_ban"
AP_TIEN_TO = "Khóa kỳ"
VAI_TRO_XEM = {"Accounts Manager", "System Manager"}

FIELDS = {
    "Customer": [
        {"fieldname": F_XN_NGAY, "label": "Đã xác nhận công nợ đến ngày (R039)", "fieldtype": "Date",
         "insert_after": "payment_terms", "read_only": 1, "no_copy": 1},
        {"fieldname": F_XN_BOI, "label": "Người ghi nhận xác nhận", "fieldtype": "Link", "options": "User",
         "insert_after": F_XN_NGAY, "read_only": 1, "no_copy": 1},
        {"fieldname": F_XN_SO_DU, "label": "Số dư khách xác nhận", "fieldtype": "Currency", "options": "VND",
         "insert_after": F_XN_BOI, "read_only": 1, "no_copy": 1}],
    "Selling Settings": [
        {"fieldname": F_SO_NGAY, "label": "Cảnh báo khi khách chưa xác nhận công nợ quá (ngày)", "fieldtype": "Int",
         "default": "30", "insert_after": "cust_master_name", "non_negative": 1}],
    "Journal Entry Account": [
        {"fieldname": F_DON_BAN, "label": "Đơn bán (chi phí trực tiếp của đơn)", "fieldtype": "Link",
         "options": "Sales Order", "insert_after": "cost_center",
         "description": "R099: chiết khấu / hoa hồng / chi phí gắn đúng một đơn bán; báo cáo lãi quản trị trừ vào đơn đó."}],
}


def enabled():
    return cint(frappe.conf.get(FLAG))


def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_quan_tri trước khi cài")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    if frappe.db.get_single_value("Selling Settings", F_SO_NGAY) in (None, ""):
        frappe.db.set_single_value("Selling Settings", F_SO_NGAY, 30)
    return {"fields": sum(len(v) for v in FIELDS.values())}


def can_quyen(vai_tro=VAI_TRO_XEM):
    if not enabled():
        frappe.throw("Tính năng quản trị 0.11.4 chưa được bật")
    if frappe.session.user != "Administrator" and not (set(frappe.get_roles()) & set(vai_tro)):
        frappe.throw("Cần quyền kế toán trưởng", frappe.PermissionError)


def cac_cong_ty():
    """[(abbr, tên)] theo thứ tự tạo."""
    return [(c.abbr, c.name) for c in frappe.get_all("Company", fields=["name", "abbr"], order_by="creation")]


# ---------------------------------------------------------------- R105 khóa kỳ

def _thang(thang):
    dau = getdate(f"{thang}-01")
    return dau, dau.replace(day=calendar.monthrange(dau.year, dau.month)[1])


def _ky(company, thang):
    """(period_name, tên bản ghi nếu đã có). ERPNext tự thêm " - <viết tắt>" vào cả tên và period_name: tìm theo ngày."""
    dau, cuoi = _thang(thang)
    return f"{AP_TIEN_TO} {thang}", frappe.db.get_value(
        "Accounting Period", {"company": company, "start_date": dau, "end_date": cuoi}, "name")


@frappe.whitelist(methods=["POST"])
def khoa_ky(company, thang, ly_do):
    """Khóa tháng `thang` (YYYY-MM) của `company`: Accounting Period chuẩn, khóa mọi loại chứng từ ghi sổ."""
    can_quyen({"Accounts Manager"})
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do khóa kỳ")
    dau, cuoi = _thang(thang)
    ten, co = _ky(company, thang)
    if co:
        ap = frappe.get_doc("Accounting Period", co)
        if not cint(ap.disabled):
            return {"ky": co, "da_khoa": True}
        ap.disabled = 0
        ap.save(ignore_permissions=True)
    else:
        # Mọi loại chứng từ ghi sổ khai trong hook period_closing_doctypes của các app (như nút chuẩn của ERPNext).
        loai = list(dict.fromkeys(frappe.get_hooks("period_closing_doctypes") or []))
        ap = frappe.get_doc({"doctype": "Accounting Period", "period_name": ten, "company": company,
                             "start_date": dau, "end_date": cuoi,
                             "closed_documents": [{"document_type": dt, "closed": 1} for dt in loai]})
        ap.insert(ignore_permissions=True)  # quyền đã kiểm: Accounts Manager
    ap.add_comment("Comment", f"Khóa kỳ {thang} bởi {frappe.session.user}. Lý do: {ly_do.strip()}")
    return {"ky": ap.name, "da_khoa": True, "so_loai_chung_tu": len(ap.closed_documents)}


@frappe.whitelist(methods=["POST"])
def mo_khoa_ky(company, thang, ly_do):
    can_quyen({"Accounts Manager"})
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do mở khóa kỳ")
    _ten, co = _ky(company, thang)
    if not co:
        frappe.throw(f"Kỳ {thang} của {company} chưa khóa")
    ap = frappe.get_doc("Accounting Period", co)
    ap.disabled = 1
    ap.save(ignore_permissions=True)
    ap.add_comment("Comment", f"Mở khóa kỳ {thang} bởi {frappe.session.user}. Lý do: {ly_do.strip()}")
    return {"ky": co, "da_khoa": False}


def da_khoa(company, dau, cuoi):
    """Có Accounting Period đang bật phủ trọn khoảng [dau, cuoi] của công ty."""
    return bool(frappe.db.sql("""SELECT name FROM `tabAccounting Period` WHERE company=%s AND disabled=0
        AND start_date<=%s AND end_date>=%s LIMIT 1""", (company, dau, cuoi)))


def ly_do_tam_tinh(company, thang):
    """Tập lý do lãi tạm tính của tháng `thang` (YYYY-MM)."""
    dau, cuoi = _thang(thang)
    can_pb = frappe.get_meta("Cost Center").has_field("kh_aph_loai_ttcp") and bool(frappe.db.exists(
        "Cost Center", {"company": company, "kh_aph_loai_ttcp": "Xưởng sản xuất"}))
    da_pb = False
    if can_pb and frappe.get_meta("Landed Cost Voucher").has_field("kh_aph_phan_bo_ky"):
        da_pb = bool(frappe.db.exists("Landed Cost Voucher", {"company": company, "docstatus": 1,
                                                               "kh_aph_phan_bo_ky": ["like", f"{thang}|%"]}))
    return Q.trang_thai_ky(da_khoa(company, dau, cuoi), can_pb, da_pb)


# ---------------------------------------------------------------- R039 xác nhận công nợ

def so_du_khach(customer, company=None, ngay=None):
    dk = "AND company=%(c)s" if company else ""
    return flt(frappe.db.sql(f"""SELECT SUM(amount) FROM `tabPayment Ledger Entry` WHERE party_type='Customer'
        AND party=%(p)s AND delinked=0 AND posting_date<=%(d)s {dk}""",
                             {"p": customer, "c": company, "d": ngay or nowdate()})[0][0])


@frappe.whitelist(methods=["POST"])
def ghi_nhan_xac_nhan(customer, ngay, so_du_xac_nhan, ghi_chu=None):
    can_quyen({"Accounts User", "Accounts Manager", "System Manager"})
    kh = frappe.get_doc("Customer", customer)
    kh.check_permission("read")
    ngay = getdate(ngay)
    so = so_du_khach(customer, ngay=ngay)
    lech = flt(so_du_xac_nhan) - so
    frappe.db.set_value("Customer", customer, {F_XN_NGAY: ngay, F_XN_BOI: frappe.session.user,
                                               F_XN_SO_DU: flt(so_du_xac_nhan)})
    kh.add_comment("Comment", f"Xác nhận công nợ đến {ngay:%d/%m/%Y}: khách xác nhận {so_vn(flt(so_du_xac_nhan), 0)}, "
                              f"sổ {so_vn(so, 0)}, chênh {so_vn(lech, 0)}." + (f" {ghi_chu}" if ghi_chu else ""))
    return {"so_du_so": so, "so_du_xac_nhan": flt(so_du_xac_nhan), "chenh_lech": lech}


def canh_bao_xac_nhan(doc, method=None):
    """Sales Order validate: cảnh báo mềm (không chặn) khi khách có số dư mà quá hạn xác nhận công nợ."""
    if not enabled() or not frappe.get_meta("Customer").has_field(F_XN_NGAY) or not doc.get("customer"):
        return
    so_ngay = cint(frappe.db.get_single_value("Selling Settings", F_SO_NGAY) or 30)
    so = so_du_khach(doc.customer)
    ngay_xn = frappe.db.get_value("Customer", doc.customer, F_XN_NGAY)
    if so > 0 and Q.qua_han_xac_nhan(ngay_xn, nowdate(), so_ngay):
        lan_cuoi = f"lần cuối {getdate(ngay_xn):%d/%m/%Y}" if ngay_xn else "chưa từng xác nhận"
        frappe.msgprint(f"Khách chưa xác nhận công nợ trong {so_ngay} ngày ({lan_cuoi}); số dư hiện tại {so_vn(so, 0)}.",
                        title="Khách chưa xác nhận công nợ (R039)", indicator="orange")


# ---------------------------------------------------------------- dữ liệu báo cáo

def dong_lai_gop(tu, den, company=None):
    """Dòng chi tiết cho báo cáo lãi gộp: mỗi dòng hóa đơn bán (kể cả trả lại), cộng giảm giá sau giao và chi phí trực tiếp."""
    tu, den = getdate(tu), getdate(den)
    dk = "AND si.company=%(c)s" if company else ""
    rows = frappe.db.sql(f"""SELECT si.name AS si, si.company, si.customer, si.posting_date, i.name AS dong,
            i.item_code, i.warehouse, i.sales_order, i.base_net_amount AS dt, i.stock_qty, i.dn_detail,
            si.update_stock
        FROM `tabSales Invoice` si JOIN `tabSales Invoice Item` i ON i.parent=si.name
        WHERE si.docstatus=1 AND si.posting_date BETWEEN %(tu)s AND %(den)s {dk}""",
                         {"tu": tu, "den": den, "c": company}, as_dict=True)
    # Giá vốn: giá trị xuất trên sổ kho của dòng phiếu giao (hoặc dòng hóa đơn xuất kho), theo tỷ lệ số lượng đã lập hóa đơn.
    ma_dong = [r.dn_detail for r in rows if r.dn_detail and not r.update_stock] + [r.dong for r in rows if r.update_stock]
    sle = {}
    if ma_dong:
        for s in frappe.db.sql("""SELECT voucher_detail_no, SUM(stock_value_difference) AS gt, SUM(actual_qty) AS sl
                FROM `tabStock Ledger Entry` WHERE is_cancelled=0 AND voucher_detail_no IN %s
                GROUP BY voucher_detail_no""", (tuple(ma_dong),), as_dict=True):
            sle[s.voucher_detail_no] = (flt(s.gt), flt(s.sl))
    giam = {}
    if frappe.get_meta("Journal Entry").has_field("kh_aph_giam_gia_hd") and rows:
        for g in frappe.db.sql("""SELECT je.kh_aph_giam_gia_hd AS si, SUM(a.debit) AS tien
                FROM `tabJournal Entry` je JOIN `tabJournal Entry Account` a ON a.parent=je.name
                JOIN `tabAccount` acc ON acc.name=a.account
                WHERE je.docstatus=1 AND IFNULL(je.kh_aph_giam_gia_hd,'')!='' AND acc.account_number NOT LIKE '333%%'
                  AND je.kh_aph_giam_gia_hd IN %s GROUP BY je.kh_aph_giam_gia_hd""",
                              (tuple({r.si for r in rows}),), as_dict=True):
            giam[g.si] = flt(g.tien)
    tong_si = {}
    for r in rows:
        tong_si[r.si] = tong_si.get(r.si, 0) + flt(r.dt)
    out = []
    for r in rows:
        key = r.dong if r.update_stock else r.dn_detail
        gv = 0.0
        if key in sle:
            gt, sl = sle[key]
            ty = abs(flt(r.stock_qty) / sl) if sl else 1.0
            gv = -gt * min(ty, 1.0)
        dt = flt(r.dt)
        if r.si in giam and tong_si[r.si]:
            dt -= giam[r.si] * flt(r.dt) / tong_si[r.si]
        out.append({**r, "doanh_thu": dt, "gia_von": gv, "cp_truc_tiep": 0.0})
    if frappe.get_meta("Journal Entry Account").has_field(F_DON_BAN):
        for c in frappe.db.sql(f"""SELECT a.{F_DON_BAN} AS so, je.company, SUM(a.debit - a.credit) AS tien
                FROM `tabJournal Entry` je JOIN `tabJournal Entry Account` a ON a.parent=je.name
                WHERE je.docstatus=1 AND je.posting_date BETWEEN %(tu)s AND %(den)s AND IFNULL(a.{F_DON_BAN},'')!=''
                  AND IFNULL(je.kh_aph_giam_gia_hd,'')='' {dk.replace('si.', 'je.')} GROUP BY a.{F_DON_BAN}, je.company""",
                               {"tu": tu, "den": den, "c": company}, as_dict=True):
            so = frappe.db.get_value("Sales Order", c.so, ["customer"], as_dict=True) or {}
            out.append({"si": None, "company": c.company, "customer": so.get("customer"), "posting_date": den,
                        "item_code": None, "warehouse": None, "sales_order": c.so, "doanh_thu": 0.0, "gia_von": 0.0,
                        "cp_truc_tiep": flt(c.tien)})
    return out


def dong_tien_cong_ty(company, ngay):
    ngay = getdate(ngay)
    ten_cty = [n for _a, n in cac_cong_ty()]
    so_du = flt(frappe.db.sql("""SELECT SUM(g.debit - g.credit) FROM `tabGL Entry` g JOIN `tabAccount` a ON a.name=g.account
        WHERE g.company=%s AND g.is_cancelled=0 AND g.posting_date<=%s AND a.account_type IN ('Cash','Bank')""",
                              (company, ngay))[0][0])
    thu, chi, ct_thu, ct_chi = [], [], [], []
    for r in frappe.db.sql("""SELECT si.name, si.customer, c.customer_name, c.is_internal_customer AS nb, si.due_date,
            si.outstanding_amount AS con FROM `tabSales Invoice` si JOIN `tabCustomer` c ON c.name=si.customer
            WHERE si.company=%s AND si.docstatus=1 AND si.outstanding_amount>0""", company, as_dict=True):
        if Q.la_noi_bo(r.customer_name, r.nb, ten_cty):
            continue
        thu.append((r.due_date, r.con))
        ct_thu.append(r)
    pi_out = "outstanding_amount"  # tiền tệ công ty là VND; hóa đơn ngoại tệ (nếu có) cần quy đổi ở bản sau
    for r in frappe.db.sql(f"""SELECT pi.name, pi.supplier, s.supplier_name, s.is_internal_supplier AS nb, pi.due_date,
            pi.{pi_out} AS con FROM `tabPurchase Invoice` pi JOIN `tabSupplier` s ON s.name=pi.supplier
            WHERE pi.company=%s AND pi.docstatus=1 AND pi.{pi_out}>0""", company, as_dict=True):
        if Q.la_noi_bo(r.supplier_name, r.nb, ten_cty):
            continue
        chi.append((r.due_date, r.con))
        ct_chi.append(r)
    # 0.14 (cờ kh_aph_tien_vay): gốc vay còn nợ + lãi chưa trả đến hạn theo khế ước
    from kh_aph.tien_vay import khoan_vay_den_han
    for han, con, k in khoan_vay_den_han(company, ngay):
        chi.append((han, con))
        ct_chi.append(frappe._dict(name=k["name"], supplier=None, supplier_name="Vay: " + (k["ben_cho_vay"] or ""),
                                   nb=0, due_date=han, con=con))
    return Q.dong_tien(so_du, thu, chi, ngay), ct_thu, ct_chi


def tu_ngay_den_ngay(filters):
    hom_nay = getdate(nowdate())
    tu = getdate(filters.get("tu_ngay") or hom_nay.replace(day=1))
    den = getdate(filters.get("den_ngay") or hom_nay)
    if tu > den:
        frappe.throw("Từ ngày phải trước đến ngày")
    return tu, den


def cac_thang(tu, den):
    t = datetime.date(tu.year, tu.month, 1)
    while t <= den:
        yield f"{t:%Y-%m}"
        t = (t.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

