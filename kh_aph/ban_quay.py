"""Giá sàn và quầy bán hàng của kế toán bán hàng (lượt 0.13, cờ `kh_aph_gia_san`, mặc định tắt).
Đặc tả docs/dac-ta-0.13.md mục 7–8; rà soát pháp lý dòng 19.

- Giá sàn (DocType "APH Gia san"): dòng giá dưới sàn chặn xác nhận đơn bán / hóa đơn bán lẻ đến khi có người duyệt; người
  không có quyền duyệt chỉ thấy "dưới giá sàn", không thấy con số. Người duyệt và mức theo bảng trong Thiết lập bán hàng
  (kế toán bán hàng có thể tự duyệt đơn mình lập trong mức).
- Thu tiền nhanh: một hộp thoại tiền mặt + chuyển khoản (mã giao dịch chống ghi trùng), phân bổ vào đúng hóa đơn chọn.
- In phiếu xuất kho kiêm biên bản bàn giao 2 liên; biên bản đối soát công nợ (mẫu in trên Khách).
- Thu hồi nợ: ghi cuộc gọi + hẹn trả trên Khách; báo cáo "Khach can goi hom nay".
Quy tắc thuần ở lab9x.van_hanh.
"""
import frappe
from kh_aph.cash_transaction import retry_rpc
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate
from lab9x import van_hanh as V

FLAG = "kh_aph_gia_san"
DT_SAN = "APH Gia san"
DT_DUYET = "APH Nguoi duyet gia san"
ROLE_KTBH = "Kế toán bán hàng"
VAI_TRO_QUAY = {ROLE_KTBH, "Accounts User", "Accounts Manager", "System Manager"}
F_DUOI = "kh_aph_duoi_san"
F_BOI = "kh_aph_duyet_san_boi"
F_MUC = "kh_aph_duyet_san_muc"
F_LY_DO = "kh_aph_duyet_san_ly_do"
F_BANG = "kh_aph_nguoi_duyet_gia_san"
F_HEN = "kh_aph_hen_tra"
F_GOI_LUC = "kh_aph_lan_goi_cuoi"
F_GOI_KQ = "kh_aph_ket_qua_goi"
MAU_DOI_SOAT = "Biên bản đối soát công nợ"
MAU_PHIEU_GIAO = "Phiếu xuất kho bán hàng"


def _duyet_fields(after):
    return [
        {"fieldname": F_DUOI, "label": "Có dòng dưới giá sàn", "fieldtype": "Check", "insert_after": after,
         "read_only": 1, "no_copy": 1, "hidden": 1},
        {"fieldname": F_BOI, "label": "Duyệt giá dưới sàn bởi", "fieldtype": "Link", "options": "User",
         "insert_after": F_DUOI, "read_only": 1, "no_copy": 1, "depends_on": F_BOI},
        {"fieldname": F_MUC, "label": "Mức dưới sàn đã duyệt (%)", "fieldtype": "Percent", "insert_after": F_BOI,
         "read_only": 1, "no_copy": 1, "hidden": 1},
        {"fieldname": F_LY_DO, "label": "Lý do duyệt dưới sàn", "fieldtype": "Small Text", "insert_after": F_MUC,
         "read_only": 1, "no_copy": 1, "depends_on": F_BOI}]


FIELDS = {
    "Sales Order": _duyet_fields("customer"),
    "Sales Invoice": _duyet_fields("customer"),
    "Selling Settings": [
        {"fieldname": F_BANG, "label": "Người duyệt giá dưới sàn", "fieldtype": "Table", "options": DT_DUYET,
         "insert_after": "kh_aph_so_ngay_xac_nhan_cong_no",
         "description": "Mức trống = không giới hạn. Đơn vị trống = mọi đơn vị. Tự duyệt: được duyệt đơn do chính mình lập."}],
    "Customer": [
        {"fieldname": F_HEN, "label": "Hẹn trả nợ ngày", "fieldtype": "Date", "insert_after": "kh_aph_so_du_da_xac_nhan",
         "no_copy": 1},
        {"fieldname": F_GOI_LUC, "label": "Lần gọi thu nợ cuối", "fieldtype": "Datetime", "insert_after": F_HEN,
         "read_only": 1, "no_copy": 1},
        {"fieldname": F_GOI_KQ, "label": "Kết quả cuộc gọi cuối", "fieldtype": "Small Text", "insert_after": F_GOI_LUC,
         "read_only": 1, "no_copy": 1}],
}


def enabled():
    return cint(frappe.conf.get(FLAG))


def _can_bat():
    if not enabled():
        frappe.throw("Giá sàn / quầy bán hàng 0.13 chưa được bật")


def _vai_tro(vai_tro=VAI_TRO_QUAY):
    from kh_aph.constants import ROLE_NO_COST
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and (not (roles & set(vai_tro)) or ROLE_NO_COST in roles):
        frappe.throw("Cần quyền kế toán bán hàng", frappe.PermissionError)


def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_gia_san trước khi cài")
    for dt in (DT_DUYET, DT_SAN):
        frappe.reload_doc("kh_aph", "doctype", frappe.scrub(dt))
    if not frappe.db.exists("Role", ROLE_KTBH):
        frappe.get_doc({"doctype": "Role", "role_name": ROLE_KTBH, "desk_access": 1}).insert(ignore_permissions=True)
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    _quyen_ktbh()
    return {"fields": sum(len(v) for v in FIELDS.values()), "role": ROLE_KTBH}


# Quyền chuẩn cho vai trò Kế toán bán hàng (ERPNext tự kiểm quyền Payment Entry bên trong khi lập phiếu thu).
QUYEN_KTBH = {
    "Payment Entry": ("read", "write", "create", "submit", "print", "email"),
    "Sales Order": ("read", "write", "create", "submit", "print", "email"),
    "Delivery Note": ("read", "print"),
    "Sales Invoice": ("read", "print"),
    "Customer": ("read", "write", "create", "print"),
    "Account": ("read",),
}


def _quyen_ktbh():
    """Idempotent: thêm Custom DocPerm cấp 0 cho vai trò Kế toán bán hàng (không hủy, không xóa)."""
    from frappe.permissions import add_permission, update_permission_property
    for dt, quyen in QUYEN_KTBH.items():
        add_permission(dt, ROLE_KTBH, 0)
        for q in quyen:
            update_permission_property(dt, ROLE_KTBH, 0, q, 1, validate=False)


# ---------------------------------------------------------------- giá sàn

def gia_san(company, item_code):
    v = frappe.db.get_value(DT_SAN, {"company": company, "item_code": item_code}, "gia_san")
    if v is None:
        v = frappe.db.get_value(DT_SAN, {"company": ["in", ["", None]], "item_code": item_code}, "gia_san")
    return flt(v)


def _ap_dung(doc):
    if doc.doctype == "Sales Order":
        return not doc.get("kh_aph_shared_order")  # đơn chung: duyệt ở lượt sau
    if cint(doc.get("is_return")):
        return False
    # hóa đơn lập từ đơn / phiếu giao: giá đã qua kiểm ở đơn bán
    return not any(d.get("sales_order") or d.get("delivery_note") for d in doc.items)


def dong_duoi_san(doc):
    """[(idx, item, % dưới sàn)] của các dòng dưới giá sàn (giá theo đơn vị tồn kho)."""
    out = []
    for d in doc.get("items") or []:
        if not d.get("item_code"):
            continue
        san = gia_san(doc.company, d.item_code)
        pt = V.phan_tram_duoi_san(flt(d.rate) / (flt(d.get("conversion_factor")) or 1), san)
        if pt > 0:
            out.append((d.idx, d.item_code, pt))
    return out


def validate(doc, method=None):
    """Sales Order / Sales Invoice validate: đánh dấu dưới sàn; giá giảm thêm sau khi duyệt thì mất duyệt."""
    if not enabled() or not doc.meta.has_field(F_DUOI) or not _ap_dung(doc):
        return
    dong = dong_duoi_san(doc)
    doc.set(F_DUOI, 1 if dong else 0)
    muc = max((p for _i, _m, p in dong), default=0)
    if doc.get(F_BOI) and (not dong or muc > flt(doc.get(F_MUC)) + 1e-6):
        doc.set(F_BOI, None)
        doc.set(F_MUC, 0)
        doc.set(F_LY_DO, None)


def before_submit(doc, method=None):
    if not enabled() or not doc.meta.has_field(F_DUOI) or not _ap_dung(doc):
        return
    dong = dong_duoi_san(doc)
    if dong and not doc.get(F_BOI):
        frappe.throw("Dòng " + ", ".join(str(i) for i, _m, _p in dong) + " dưới giá sàn, cần người có quyền duyệt "
                     "(bấm \"Duyệt giá dưới sàn\").", title="Giá dưới sàn")


def _bang_duyet():
    return [{"user": r.user, "muc": flt(r.muc) or None, "cong_ty": r.company, "tu_duyet": cint(r.tu_duyet)}
            for r in frappe.get_all(DT_DUYET, {"parent": "Selling Settings"}, ["user", "muc", "company", "tu_duyet"])]


@frappe.whitelist()
def xem_duoi_san(doctype, name):
    """Cho người duyệt: các dòng dưới sàn và %; người khác chỉ nhận số dòng (không lộ giá sàn)."""
    _can_bat()
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    dong = dong_duoi_san(doc)
    duoc, _ly = V.quyen_duyet(frappe.session.user, doc.owner, doc.company, max((p for *_x, p in dong), default=0),
                              _bang_duyet())
    if frappe.session.user == "Administrator" or duoc:
        return {"duoc_duyet": True, "dong": [{"idx": i, "item_code": m, "phan_tram": p} for i, m, p in dong]}
    return {"duoc_duyet": False, "dong": [{"idx": i, "item_code": m} for i, m, _p in dong]}


@frappe.whitelist(methods=["POST"])
def duyet_gia_san(doctype, name, ly_do):
    _can_bat()
    if doctype not in ("Sales Order", "Sales Invoice"):
        frappe.throw("Chỉ duyệt đơn bán / hóa đơn bán")
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do duyệt giá dưới sàn")
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    if doc.docstatus != 0:
        frappe.throw("Chỉ duyệt chứng từ đang nháp")
    dong = dong_duoi_san(doc)
    if not dong:
        return {"duyet": False, "ly_do": "Không có dòng dưới giá sàn"}
    muc = max(p for *_x, p in dong)
    if frappe.session.user != "Administrator":
        duoc, ly = V.quyen_duyet(frappe.session.user, doc.owner, doc.company, muc, _bang_duyet())
        if not duoc:
            frappe.throw(ly, frappe.PermissionError)
    doc.db_set({F_DUOI: 1, F_BOI: frappe.session.user, F_MUC: muc, F_LY_DO: ly_do.strip()})
    doc.add_comment("Comment", f"Duyệt giá dưới sàn {muc:g}% bởi {frappe.session.user}. Lý do: {ly_do.strip()}")
    return {"duyet": True, "muc": muc}


# ---------------------------------------------------------------- thu tiền nhanh

def _tk_ngan_hang_hop_le(company, tk):
    a = frappe.db.get_value("Account", tk, ["company", "account_type", "is_group"], as_dict=True)
    if not a or a.company != company or a.account_type not in ("Bank", "Cash") or cint(a.is_group):
        frappe.throw("Chọn tài khoản ngân hàng chi tiết của đúng đơn vị")


@frappe.whitelist(methods=["POST"])
@retry_rpc
def thu_tien(company, customer, tien_mat=0, chuyen_khoan=0, tk_ngan_hang=None, ma_gd=None, hoa_don=None, ghi_chu=None, nguoi_giu_tien=None, request_id=None):
    """Lập và ghi sổ phiếu thu (mỗi hình thức một phiếu). hoa_don: danh sách hóa đơn được chọn (JSON), phân bổ theo thứ tự
    chọn; phần dư để trả trước, kế toán phân bổ theo kế hoạch (không FIFO)."""
    _can_bat()
    _vai_tro()
    try:
        cac_phan = V.tach_thu(flt(tien_mat), flt(chuyen_khoan), ma_gd)
    except ValueError as e:
        frappe.throw(str(e))
    from kh_aph import cashier_request
    from kh_aph.funds_rules import money
    try:
        cash_amount, bank_amount = (money(v or 0) for v in (tien_mat, chuyen_khoan))
    except ValueError as exc:
        frappe.throw(str(exc))
    hd = frappe.parse_json(hoa_don) if isinstance(hoa_don, str) else (hoa_don or [])
    if not isinstance(hd, list) or any(not isinstance(v, str) for v in hd) or len(set(hd)) != len(hd):
        frappe.throw("Danh sách hóa đơn không hợp lệ hoặc bị lặp")
    ma_gd = (ma_gd or "").strip()
    key, digest, previous = cashier_request.begin(request_id, {
        "company": company, "customer": customer, "cash": format(cash_amount, ".2f"), "bank": format(bank_amount, ".2f"),
        "account": tk_ngan_hang or "", "reference": ma_gd, "invoices": hd,
        "note": ghi_chu or "", "holder": nguoi_giu_tien or ""})
    if previous is not None:
        return previous
    if flt(chuyen_khoan):
        if not tk_ngan_hang:
            frappe.throw("Chọn tài khoản ngân hàng nhận chuyển khoản")
        _tk_ngan_hang_hop_le(company, tk_ngan_hang)
        # chống ghi trùng chung với 0.14: phiếu thu / chi, bút toán, phiếu thực thu 0.10 trên cùng tài khoản
        from kh_aph.tien_vay import ma_da_ghi
        trung = ma_da_ghi(tk_ngan_hang, ma_gd)
        if trung:
            frappe.throw(f"Mã giao dịch {ma_gd} đã ghi ở phiếu thu {trung}")
    from erpnext.accounts.party import get_party_account
    phai_thu = get_party_account("Customer", customer, company)
    quy = frappe.get_cached_value("Company", company, "default_cash_account")
    no = []
    for ten in hd:
        si = frappe.db.get_value("Sales Invoice", ten, ["customer", "company", "docstatus", "outstanding_amount"], as_dict=True)
        if not si or si.customer != customer or si.company != company or si.docstatus != 1:
            frappe.throw(f"Hóa đơn {ten} không thuộc khách / đơn vị này")
        no.append((ten, flt(si.outstanding_amount)))
    phieu = []
    for hinh_thuc, tien in cac_phan:
        tk = quy if hinh_thuc == "Tiền mặt" else tk_ngan_hang
        if not tk:
            frappe.throw(f"{company} chưa có tài khoản tiền mặt mặc định")
        pb, _du = V.phan_bo(tien, no)
        da = dict(pb)
        no = [(t, round(n - da.get(t, 0), 2)) for t, n in no]
        pe = frappe.get_doc({
            "doctype": "Payment Entry", "payment_type": "Receive", "company": company, "posting_date": nowdate(),
            "party_type": "Customer", "party": customer, "paid_from": phai_thu, "paid_to": tk,
            "paid_amount": tien, "received_amount": tien, "source_exchange_rate": 1, "target_exchange_rate": 1,
            "reference_no": ma_gd if hinh_thuc == "Chuyển khoản" else None,
            "reference_date": nowdate() if hinh_thuc == "Chuyển khoản" else None,
            "remarks": (ghi_chu or f"Thu {hinh_thuc.lower()} của khách {customer}"),
            "references": [{"reference_doctype": "Sales Invoice", "reference_name": t, "allocated_amount": a} for t, a in pb]})
        from kh_aph import cash_custody
        if cash_custody.enabled() and hinh_thuc == "Tiền mặt":
            pe.set(cash_custody.HOLDER, nguoi_giu_tien)
        pe.flags.ignore_permissions = True  # quyền đã kiểm: kế toán bán hàng / kế toán
        previous_request = getattr(frappe.flags, "kh_aph_cashier_request", None)
        try:
            if key:
                pe.set(cashier_request.KEY, key)
                pe.set(cashier_request.HASH, digest)
                frappe.flags.kh_aph_cashier_request = (key, digest)
            pe.insert()
            pe.submit()
        finally:
            frappe.flags.kh_aph_cashier_request = previous_request
        phieu.append(pe.name)
    return {"phieu_thu": phieu}


# ---------------------------------------------------------------- in

@frappe.whitelist()
def in_hai_lien(delivery_note):
    """HTML phiếu xuất kho kiêm biên bản bàn giao, 2 liên trên một lần in."""
    _can_bat()
    doc = frappe.get_doc("Delivery Note", delivery_note)
    doc.check_permission("print")
    mau = MAU_PHIEU_GIAO if frappe.db.exists("Print Format", MAU_PHIEU_GIAO) else None
    mot = frappe.get_print("Delivery Note", delivery_note, print_format=mau)
    return mot + '<div style="page-break-before: always"></div>' + mot


def doi_soat(customer, ngay=None):
    """Số liệu biên bản đối soát: theo từng đơn vị, nợ đầu ngày + phát sinh tăng − đã thu/giảm = còn nợ (sổ công nợ)."""
    ngay = str(getdate(ngay or nowdate()))
    rows = frappe.db.sql("""SELECT company,
            SUM(CASE WHEN posting_date < %(d)s THEN amount ELSE 0 END) AS no_dau,
            SUM(CASE WHEN posting_date = %(d)s AND amount > 0 THEN amount ELSE 0 END) AS tang,
            SUM(CASE WHEN posting_date = %(d)s AND amount < 0 THEN -amount ELSE 0 END) AS giam
        FROM `tabPayment Ledger Entry` WHERE party_type='Customer' AND party=%(p)s AND delinked=0 AND posting_date<=%(d)s
        GROUP BY company""", {"p": customer, "d": ngay}, as_dict=True)
    for r in rows:
        r.con_no = flt(r.no_dau) + flt(r.tang) - flt(r.giam)
    tong = {k: sum(flt(r[k]) for r in rows) for k in ("no_dau", "tang", "giam", "con_no")}
    return {"ngay": ngay, "dong": rows, "tong": tong}


# ---------------------------------------------------------------- thu hồi nợ

@frappe.whitelist(methods=["POST"])
def ghi_cuoc_goi(customer, ket_qua, hen_tra=None):
    _can_bat()
    _vai_tro()
    if not (ket_qua or "").strip():
        frappe.throw("Ghi kết quả cuộc gọi")
    kh = frappe.get_doc("Customer", customer)
    kh.check_permission("read")
    kh.db_set({F_GOI_LUC: now_datetime(), F_GOI_KQ: ket_qua.strip(), F_HEN: getdate(hen_tra) if hen_tra else None})
    kh.add_comment("Comment", f"Gọi thu nợ: {ket_qua.strip()}" + (f". Hẹn trả {hen_tra}" if hen_tra else ""))
    return {"ok": True}


def khach_can_goi(company=None, ngay=None):
    hom_nay = getdate(ngay or nowdate())
    so_ngay = cint(frappe.db.get_single_value("Selling Settings", "kh_aph_so_ngay_xac_nhan_cong_no") or 30) \
        if frappe.get_meta("Selling Settings").has_field("kh_aph_so_ngay_xac_nhan_cong_no") else 30
    dk = "AND company=%(c)s" if company else ""
    du = frappe.db.sql(f"""SELECT party, SUM(amount) AS no,
            SUM(CASE WHEN due_date < %(h)s THEN amount ELSE 0 END) AS qua_han,
            SUM(CASE WHEN due_date BETWEEN %(h)s AND %(h3)s THEN amount ELSE 0 END) AS den_han
        FROM `tabPayment Ledger Entry` WHERE party_type='Customer' AND delinked=0 {dk}
        GROUP BY party HAVING SUM(amount) > 0.5""", {"c": company, "h": hom_nay, "h3": add_days(hom_nay, 3)}, as_dict=True)
    meta = frappe.get_meta("Customer")
    cot = ["name", "customer_name", "mobile_no"] + [f for f in (F_HEN, F_GOI_LUC, F_GOI_KQ, "kh_aph_xac_nhan_cong_no_ngay")
                                                   if meta.has_field(f)]
    out = []
    for r in du:
        kh = frappe.db.get_value("Customer", r.party, cot, as_dict=True) or {}
        hen = getdate(kh.get(F_HEN)) if kh.get(F_HEN) else None
        xn = getdate(kh.get("kh_aph_xac_nhan_cong_no_ngay")) if kh.get("kh_aph_xac_nhan_cong_no_ngay") else None
        ly_do = V.can_goi(flt(r.no), flt(r.qua_han), flt(r.den_han), hen, hom_nay, xn, so_ngay)
        if ly_do:
            out.append({"customer": r.party, "ten": kh.get("customer_name"), "dien_thoai": kh.get("mobile_no"),
                        "con_no": flt(r.no), "qua_han": flt(r.qua_han), "hen_tra": hen, "ly_do": ", ".join(ly_do),
                        "goi_cuoi": kh.get(F_GOI_LUC), "ket_qua": kh.get(F_GOI_KQ)})
    return sorted(out, key=lambda x: (-x["qua_han"], -x["con_no"]))


def has_permission(doc, ptype=None, user=None):
    """Frappe 16: chỉ True / False. Giá sàn: cờ tắt hoặc hồ sơ không xem giá vốn (Dũng) thì chặn."""
    if not enabled():
        return False
    from kh_aph.constants import ROLE_NO_COST
    return ROLE_NO_COST not in frappe.get_roles(user)
