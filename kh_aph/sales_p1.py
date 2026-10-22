"""Bán hàng P1 (0.11.3, cờ `kh_aph_sales_p1`, mặc định tắt). Đặc tả docs/dac-ta-0.11.3.md.

- R025: phiếu trả "Khách trả hàng" chọn hàng về đâu (bán lại được / cách ly) × xử lý tiền (bù trừ / hoàn tiền / đổi hàng).
- R026: giảm giá sau giao → bút toán NHÁP loại Credit Note, chia theo tỷ trọng dòng, tách thuế; TK giảm trừ 521 (TT99) hoặc
  TK doanh thu của dòng (TT133, HKD, nội bộ).
- Q166–Q168, R044–R045: hạn thanh toán chung của đơn, gia hạn có lịch sử. Q178/Q180: đổi địa chỉ khi đang giao. Q189/Q190:
  báo cáo đơn quá hạn giao.
- R093–R098, Q148: hồ sơ hóa đơn MISA (APH Hoa don ngoai) với hàng đợi và khóa người xử lý chống trùng.
Phiếu thu/chi được chuẩn bị NHÁP. Phiếu trả mới có thể đối trừ hóa đơn giảm với khoản gốc bằng dịch vụ native; không ghi thu/chi thêm.
"""
import json

import frappe
from frappe.utils import cint, flt, getdate, now_datetime
from lab9x import ban_hang as B

FLAG = "kh_aph_sales_p1"
F_HANG = "kh_aph_hang_tra_ve"
F_TIEN = "kh_aph_xu_ly_tien"
F_XU_LY = "kh_aph_chung_tu_xu_ly"
F_HAN = "kh_aph_han_thanh_toan"
F_LS = "kh_aph_lich_su_gia_han"
F_JE_HD = "kh_aph_giam_gia_hd"
DT_HD = "APH Hoa don ngoai"
VAI_TRO_KT = {"Accounts User", "Accounts Manager", "System Manager"}
HD_HIEU_LUC = ("Đang xử lý", "Đã xuất", "Bị điều chỉnh")  # hồ sơ Gốc/Thay thế còn giữ hóa đơn bán

FIELDS = {
    "Delivery Note": [
        {"fieldname": F_HANG, "label": "Hàng trả về", "fieldtype": "Select", "options": "\n" + "\n".join(B.HANG_TRA_VE),
         "insert_after": "kh_aph_loai_dieu_chinh", "depends_on": "eval:doc.is_return",
         "description": "R025: Cách ly → hàng vào kho \"Hàng cách ly <địa điểm>\", không bán được."},
        {"fieldname": F_TIEN, "label": "Xử lý tiền", "fieldtype": "Select", "options": "\n" + "\n".join(B.XU_LY_TIEN),
         "insert_after": F_HANG, "depends_on": "eval:doc.is_return",
         "description": "Bù trừ: đối chiếu khoản nợ gốc. Hoàn tiền: kiểm phiếu chi nháp trước khi chi. Đổi hàng: nhận trả rồi chọn mã hàng thay."},
        {"fieldname": F_XU_LY, "label": "Chứng từ xử lý tiền / đổi hàng", "fieldtype": "Data", "insert_after": F_TIEN,
         "read_only": 1, "allow_on_submit": 1, "no_copy": 1}],
    "Sales Order": [
        {"fieldname": F_HAN, "label": "Hạn thanh toán chung", "fieldtype": "Date", "insert_after": "delivery_date",
         "allow_on_submit": 1, "no_copy": 1, "read_only_depends_on": "eval:doc.docstatus==1",
         "description": "Q166: mọi đợt giao của đơn dùng chung hạn này. Sau khi xác nhận: dùng nút Gia hạn thanh toán."},
        {"fieldname": F_LS, "label": "Lịch sử gia hạn", "fieldtype": "Table", "options": "APH Lich su gia han",
         "insert_after": F_HAN, "read_only": 1, "allow_on_submit": 1, "no_copy": 1}],
    "Journal Entry": [
        {"fieldname": F_JE_HD, "label": "Giảm giá sau giao cho hóa đơn", "fieldtype": "Link", "options": "Sales Invoice",
         "insert_after": "voucher_type", "read_only": 1, "no_copy": 1}],
}


def enabled():
    return cint(frappe.conf.get(FLAG))


def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_sales_p1 trước khi cài")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    return {"fields": sum(len(v) for v in FIELDS.values())}


def _can_ke_toan():
    if not enabled():
        frappe.throw("Tính năng bán hàng 0.11.3 chưa được bật")
    if frappe.session.user != "Administrator" and not (set(frappe.get_roles()) & VAI_TRO_KT):
        frappe.throw("Cần quyền kế toán", frappe.PermissionError)


# ---------------------------------------------------------------- R025 trả hàng

def validate_tra_hang(doc, method=None):
    """Delivery Note validate."""
    if not enabled() or not doc.meta.has_field(F_HANG):
        return
    from kh_aph.sales_adjust_rules import DC_TRA_HANG
    tra_hang = cint(doc.is_return) and doc.get("kh_aph_loai_dieu_chinh") == DC_TRA_HANG
    if not tra_hang:
        doc.set(F_HANG, None)
        doc.set(F_TIEN, None)
        return
    # Không chọn thì giữ đúng cách làm trước 0.11.3: hàng về kho cũ bán lại được, hóa đơn giảm bù trừ công nợ.
    if not doc.get(F_HANG):
        doc.set(F_HANG, B.HANG_BAN_LAI)
    if not doc.get(F_TIEN):
        doc.set(F_TIEN, B.TIEN_BU_TRU)
    loi = B.kiem_tra_hang(True, doc.get(F_HANG), doc.get(F_TIEN))
    if loi:
        frappe.throw(loi, title="Trả hàng (R025)")
    if doc.get(F_HANG) == B.HANG_CACH_LY:
        from kh_aph import kho_chuan
        if not kho_chuan.enabled():
            frappe.throw("Cách ly cần bật cây kho chuẩn (kh_aph_kho_chuan)")
        from lab9x.cay_kho import CACH_LY
        for d in doc.items:
            if d.get("warehouse") and kho_chuan.loai_kho(d.warehouse) != CACH_LY:
                d.warehouse = kho_chuan.kho_tinh_trang(d.warehouse, CACH_LY)


def sau_ghi_tra_hang(doc, method=None):
    """Delivery Note on_submit (sau khi app sinh hóa đơn giảm): Đổi hàng → phiếu giao NHÁP mới từ đơn gốc."""
    if not enabled() or not cint(doc.is_return) or doc.get(F_TIEN) != B.TIEN_DOI_HANG:
        return
    from kh_aph.sales_return import REQUEST
    if doc.get(REQUEST):
        frappe.msgprint("Đã nhận trả. Dùng Lập đơn hàng thay để chọn mã và lượng hàng mới.", indicator="blue")
        return
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
    so = next((d.against_sales_order for d in doc.items if d.get("against_sales_order")), None)
    if not so:
        frappe.msgprint("Phiếu trả không gắn đơn bán: lập phiếu giao đổi hàng bằng tay.", indicator="orange")
        return
    can = {}
    for d in doc.items:
        if d.get("against_sales_order") == so:
            can[d.so_detail] = can.get(d.so_detail, 0) + abs(flt(d.qty))
    moi = make_delivery_note(so)
    moi.items = [r for r in moi.items if r.get("so_detail") in can]
    for r in moi.items:
        r.qty = min(flt(r.qty), can[r.so_detail])
    if not moi.items:
        frappe.msgprint("Đơn gốc không còn phần chờ giao để đổi: lập phiếu giao đổi hàng bằng tay.", indicator="orange")
        return
    moi.flags.ignore_permissions = True  # người ghi sổ phiếu trả là thủ kho; phiếu NHÁP, người có quyền xác nhận sau
    moi.insert()
    doc.db_set(F_XU_LY, moi.name)
    frappe.msgprint(f"Đã lập phiếu giao đổi hàng nháp {moi.name}.", indicator="blue")


def sau_ghi_hoa_don_giam(doc, method=None):
    """Sales Invoice on_submit: hóa đơn giảm của phiếu trả "Hoàn tiền" → Payment Entry NHÁP trả tiền cho khách."""
    if not enabled() or not cint(doc.is_return):
        return
    dn = next((d.delivery_note for d in doc.items if d.get("delivery_note")), None)
    if not dn:
        return
    settlement = frappe.db.get_value("Delivery Note", dn, F_TIEN)
    from kh_aph.sales_return import REQUEST
    modern = (frappe.get_meta("Delivery Note").has_field(REQUEST)
              and frappe.db.get_value("Delivery Note", dn, REQUEST))
    if not modern and settlement != B.TIEN_HOAN:
        return
    # Giữ chuẩn bị nháp của phiếu lịch sử. Phiếu mới phải đối chiếu số dư
    # native thực tế: ERPNext có thể giữ hóa đơn giảm riêng khi giá trị trả vượt khoản còn nợ.
    so_tien = abs(flt(doc.base_rounded_total or doc.base_grand_total))
    references = []
    if modern:
        # Phiếu trả mới đã ghi giảm vào đúng hóa đơn gốc. Chỉ phần số dư có
        # còn lại mới được chuẩn bị chi; hoàn tiền tất toán số dư này một lần.
        from kh_aph.return_quantity import refund_after_credit
        if not doc.return_against:
            frappe.throw("Cần xác định khoản phải thu gốc trước khi chuẩn bị hoàn tiền")
        frappe.db.sql("SELECT name FROM `tabSales Invoice` WHERE name=%s FOR UPDATE", doc.return_against)
        original = frappe.get_doc("Sales Invoice", doc.return_against, for_update=True)
        if original.company != doc.company or original.customer != doc.customer or original.docstatus != 1:
            frappe.throw("Khoản hoàn phải cùng khách và đơn vị với hóa đơn gốc còn hiệu lực")
        if original.currency != "VND" or original.party_account_currency != "VND":
            frappe.msgprint("Khoản hoàn khác VND: kế toán đối chiếu tỷ giá và lập phiếu chi riêng.", indicator="orange")
            return
        reference = original
        if cint(doc.get("update_outstanding_for_self")):
            credit = frappe.get_doc("Sales Invoice", doc.name, for_update=True)
            offset = min(max(0, flt(original.outstanding_amount)), max(0, -flt(credit.outstanding_amount)))
            if offset:
                if not (frappe.has_permission("Journal Entry", "create") and frappe.has_permission("Journal Entry", "submit")):
                    frappe.msgprint("Đã nhận trả; khoản giảm chờ kế toán đối trừ với khoản gốc trước khi chuẩn bị hoàn tiền.", indicator="orange")
                    return
                from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import reconcile_dr_cr_note
                from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions
                dimensions = get_dimensions(with_cost_center_and_project=True)[0]
                allocation = frappe._dict(voucher_type="Sales Invoice", voucher_no=credit.name,
                    against_voucher_type="Sales Invoice", against_voucher=original.name,
                    account=original.debit_to, currency=original.party_account_currency, party_type="Customer", party=original.customer,
                    dr_or_cr="credit_in_account_currency", unadjusted_amount=abs(flt(credit.outstanding_amount)),
                    allocated_amount=offset, difference_amount=0, exchange_rate=1,
                    cost_center=credit.cost_center or original.cost_center,
                    debit_or_credit_note_posting_date=doc.posting_date)
                for dimension in dimensions:
                    allocation[dimension.fieldname] = credit.get(dimension.fieldname)
                # Hai dòng cùng TK/khách/Company đối trừ hai hóa đơn. Không tăng doanh thu hoặc ghi tiền.
                reconcile_dr_cr_note([allocation], doc.company, dimensions)
                credit = frappe.get_doc("Sales Invoice", doc.name, for_update=True)
            reference = credit
        if settlement != B.TIEN_HOAN:
            return
        so_tien = float(refund_after_credit(so_tien, reference.outstanding_amount))
        if not so_tien:
            frappe.msgprint("Giá trị hàng trả đã giảm khoản còn nợ; không phát sinh tiền phải hoàn ở lượt này.", indicator="blue")
            return
        references = [{"reference_doctype": "Sales Invoice", "reference_name": reference.name,
                       "total_amount": reference.grand_total, "outstanding_amount": reference.outstanding_amount,
                       "allocated_amount": -so_tien}]
    quy = frappe.get_cached_value("Company", doc.company, "default_cash_account")
    try:
        if not quy:
            raise frappe.ValidationError("Công ty chưa có tài khoản tiền mặt mặc định")
        pe = frappe.get_doc({
            "doctype": "Payment Entry", "payment_type": "Pay", "party_type": "Customer", "party": doc.customer,
            "company": doc.company, "posting_date": doc.posting_date, "paid_from": quy, "paid_to": doc.debit_to,
            "paid_amount": so_tien, "received_amount": so_tien, "source_exchange_rate": 1, "target_exchange_rate": 1,
            "references": references,
            "remarks": f"Hoàn tiền hàng trả lại theo {dn} / {doc.name} (R025). Kế toán chọn quỹ / ngân hàng rồi ghi sổ."})
        pe.flags.ignore_permissions = True  # người ghi sổ phiếu trả có thể là thủ kho; phiếu NHÁP
        pe.insert()
    except Exception:
        doc.log_error(f"kh_aph: không lập được phiếu chi hoàn tiền cho {doc.name}")
        frappe.msgprint(f"Không tự lập được phiếu chi hoàn tiền cho {doc.name}: kế toán lập tay (Tạo → Thanh toán).",
                        indicator="orange")
        return
    frappe.db.set_value("Delivery Note", dn, F_XU_LY, pe.name, update_modified=False)
    frappe.msgprint(f"Đã lập phiếu chi hoàn tiền nháp {pe.name}.", indicator="blue")


# ---------------------------------------------------------------- R026 giảm giá sau giao

def protect_processing_reference(doc, method=None):
    """Ô chứng từ xử lý chỉ do các hook chuẩn bị nháp ghi, không nhận dữ liệu tự gán."""
    if not enabled():
        return
    old = doc.get_doc_before_save()
    if (doc.get(F_XU_LY) or '') != ((old.get(F_XU_LY) if old else None) or ''):
        frappe.throw('Không tự đổi chứng từ xử lý tiền / đổi hàng; mở phiếu đã được hệ thống liên kết')

def _so_hieu_la(company):
    return set(frappe.get_all("Account", {"company": company, "is_group": 0, "account_number": ["is", "set"]},
                              pluck="account_number"))


def _thue_suat(si, d):
    """% thuế của dòng theo các TK thuế có trên hóa đơn (hóa đơn không lấy hóa đơn đã bỏ thuế → 0)."""
    tk_thue = {t.account_head: flt(t.rate) for t in si.get("taxes") or [] if t.charge_type == "On Net Total"}
    if not tk_thue:
        return 0.0, None
    rates = json.loads(d.get("item_tax_rate") or "{}")
    tk = next(iter(tk_thue))
    if rates:
        return sum(flt(rates.get(a, 0)) for a in tk_thue), tk
    return sum(tk_thue.values()), tk


@frappe.whitelist(methods=["POST"])
def giam_gia_sau_giao(sales_invoice, so_tien, ly_do):
    """Bút toán NHÁP giảm giá sau giao cho một hóa đơn đã ghi sổ. Chạy lại khi còn nháp trả bút toán cũ."""
    _can_ke_toan()
    # Cùng khóa hóa đơn để hai người không lập hai đề nghị giảm nháp đồng thời.
    frappe.db.sql("SELECT name FROM `tabSales Invoice` WHERE name=%s FOR UPDATE", sales_invoice)
    si = frappe.get_doc("Sales Invoice", sales_invoice, for_update=True)
    si.check_permission("read")
    if si.docstatus != 1 or cint(si.is_return):
        frappe.throw("Chỉ dùng cho hóa đơn bán đã ghi sổ (không phải hóa đơn trả lại)")
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do giảm giá")
    pending = frappe.db.sql(f"SELECT name FROM `tabJournal Entry` WHERE {F_JE_HD}=%s AND docstatus=0 ORDER BY name FOR UPDATE",
                            si.name, as_dict=True)
    if len(pending) > 1:
        frappe.throw("Có nhiều đề nghị giảm nháp cho khoản này; kế toán đối soát trước khi lập thêm")
    if pending:
        # Mở lại để đối chiếu nội dung cũ, không hứa đã đổi sang số tiền mới của người gọi.
        existing = frappe.get_doc("Journal Entry", pending[0].name)
        existing.check_permission("read")
        return {"but_toan": existing.name, "da_co": True}
    so_tien = flt(so_tien)
    if so_tien > flt(si.outstanding_amount) + 0.5:
        frappe.throw(f"Số tiền giảm lớn hơn phần khách còn nợ của hóa đơn ({flt(si.outstanding_amount):,.0f})")
    tk_521 = B.tk_giam_tru(_so_hieu_la(si.company))
    if tk_521:
        tk_521 = frappe.db.get_value("Account", {"company": si.company, "account_number": tk_521, "is_group": 0}, "name")
    dong, thong_tin = [], {}
    for d in si.items:
        ts, tk_thue = _thue_suat(si, d)
        dong.append((d.name, flt(d.base_net_amount), ts))
        thong_tin[d.name] = (tk_521 or d.income_account, d.cost_center, tk_thue)
    try:
        chia = B.chia_giam_gia(so_tien, dong, precision=si.precision("base_grand_total") or 0)
    except ValueError as e:
        frappe.throw(str(e))
    no = {}
    for ten, chua, thue in chia:
        tk, cc, tk_thue = thong_tin[ten]
        no[(tk, cc)] = no.get((tk, cc), 0) + chua
        if thue:
            no[(tk_thue, cc)] = no.get((tk_thue, cc), 0) + thue
    tong = sum(no.values())
    je = frappe.get_doc({
        "doctype": "Journal Entry", "voucher_type": "Credit Note", "company": si.company, "posting_date": getdate(),
        F_JE_HD: si.name,
        "user_remark": f"Giảm giá sau giao hóa đơn {si.name} (R026): {ly_do.strip()}. "
                       + ("Ghi Nợ 521 (TT99)." if tk_521 else "Ghi giảm thẳng TK doanh thu (TT133 không dùng 521)."),
        "accounts": [{"account": tk, "cost_center": cc, "debit_in_account_currency": flt(v)} for (tk, cc), v in no.items()]
                    + [{"account": si.debit_to, "party_type": "Customer", "party": si.customer,
                        "credit_in_account_currency": flt(tong), "reference_type": "Sales Invoice",
                        "reference_name": si.name, "cost_center": si.items[0].cost_center}],
    })
    je.insert()  # quyền tạo bút toán chuẩn của kế toán
    return {"but_toan": je.name, "chia": chia, "tk_giam_tru": tk_521 or "TK doanh thu của dòng"}


# ---------------------------------------------------------------- Q166–Q168 hạn thanh toán chung

def _han_mac_dinh(so):
    from erpnext.accounts.party import get_due_date
    tpl = so.get("payment_terms_template") or frappe.db.get_value("Customer", so.customer, "payment_terms")
    if not tpl:
        return None
    return getdate(get_due_date(str(getdate(so.transaction_date)), "Customer", so.customer, so.company, template_name=tpl))


def validate_don(doc, method=None):
    """Sales Order validate: điền hạn chung trước khi xác nhận."""
    if not enabled() or not doc.meta.has_field(F_HAN) or doc.docstatus != 0:
        return
    if not doc.get(F_HAN):
        doc.set(F_HAN, _han_mac_dinh(doc))
    if doc.get(F_HAN) and getdate(doc.get(F_HAN)) < getdate(doc.transaction_date):
        frappe.throw("Hạn thanh toán chung không được trước ngày đơn")


def ap_han_hoa_don(si, ngay_giao):
    """Gọi từ sales_flow._build_invoice: hóa đơn của đợt giao lấy hạn chung của đơn (Q166)."""
    if not enabled() or not frappe.get_meta("Sales Order").has_field(F_HAN):
        return
    so = next((d.sales_order for d in si.items if d.get("sales_order")), None)
    han = frappe.db.get_value("Sales Order", so, F_HAN) if so else None
    due = B.han_hoa_don(han, getdate(ngay_giao)) if han else None
    if not due:
        return
    # Bỏ điều khoản (ERPNext sẽ tính lại lịch theo ngày giao) và đặt sẵn một dòng lịch 100% đúng hạn chung;
    # ERPNext tự điền số tiền của dòng theo tổng hóa đơn.
    si.payment_terms_template = None
    si.ignore_default_payment_terms_template = 1
    si.set("payment_schedule", [{"due_date": due, "invoice_portion": 100}])
    si.due_date = due


@frappe.whitelist(methods=["POST"])
def gia_han_thanh_toan(sales_order, han_moi, ly_do):
    _can_ke_toan()
    so = frappe.get_doc("Sales Order", sales_order)
    so.check_permission("read")
    if so.docstatus != 1:
        frappe.throw("Đơn chưa xác nhận: sửa thẳng ô Hạn thanh toán chung")
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do gia hạn")
    han_moi = getdate(han_moi)
    if han_moi < getdate(so.transaction_date):
        frappe.throw("Hạn mới không được trước ngày đơn")
    cu = so.get(F_HAN)
    so.append(F_LS, {"han_cu": cu, "han_moi": han_moi, "ly_do": ly_do.strip(), "nguoi": frappe.session.user,
                     "luc": now_datetime()})
    so.set(F_HAN, han_moi)
    so.flags.ignore_validate_update_after_submit = True
    so.save(ignore_permissions=True)  # quyền đã kiểm ở _can_ke_toan; chỉ đổi hạn và lịch sử
    hd = frappe.db.sql_list("""SELECT DISTINCT si.name FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` i ON i.parent=si.name
        WHERE i.sales_order=%s AND si.docstatus=1 AND si.is_return=0 AND si.outstanding_amount>0""", so.name)
    for n in hd:
        ngay = frappe.db.get_value("Sales Invoice", n, "posting_date")
        due = max(han_moi, getdate(ngay))
        frappe.db.set_value("Sales Invoice", n, "due_date", due, update_modified=False)
        frappe.db.sql("UPDATE `tabPayment Schedule` SET due_date=%s WHERE parenttype='Sales Invoice' AND parent=%s",
                      (due, n))
        frappe.db.sql("""UPDATE `tabPayment Ledger Entry` SET due_date=%s
            WHERE voucher_type='Sales Invoice' AND voucher_no=%s AND delinked=0""", (due, n))
    return {"han_moi": str(han_moi), "hoa_don_cap_nhat": hd}


# ---------------------------------------------------------------- Q178/Q180 đổi địa chỉ đang giao

@frappe.whitelist(methods=["POST"])
def doi_dia_chi_giao(delivery_note, dia_chi, ly_do):
    if not enabled():
        frappe.throw("Tính năng bán hàng 0.11.3 chưa được bật")
    dn = frappe.get_doc("Delivery Note", delivery_note)
    dn.check_permission("write")
    if dn.docstatus != 1 or cint(dn.is_return):
        frappe.throw("Chỉ đổi địa chỉ cho phiếu giao đã xuất kho")
    from kh_aph.delivery_status import STATE, TRANSIT
    if dn.meta.has_field(STATE) and dn.get(STATE) not in (None, "", TRANSIT):
        frappe.throw("Chỉ đổi địa chỉ khi phiếu đang giao")
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do đổi địa chỉ")
    if not frappe.db.exists("Dynamic Link", {"parenttype": "Address", "parent": dia_chi, "link_doctype": "Customer",
                                             "link_name": dn.customer}):
        frappe.throw("Địa chỉ không thuộc khách của phiếu")
    from frappe.contacts.doctype.address.address import get_address_display
    cu = dn.shipping_address_name or dn.customer_address
    dn.db_set({"shipping_address_name": dia_chi, "shipping_address": get_address_display(dia_chi)})
    dn.add_comment("Comment", f"Đổi địa chỉ giao từ {cu or '(trống)'} sang {dia_chi}. Lý do: {ly_do.strip()}")
    return {"dia_chi_cu": cu, "dia_chi_moi": dia_chi}


# ---------------------------------------------------------------- R093–R098 hồ sơ hóa đơn MISA

def _dang_giu(sales_invoice, tru=None):
    """Hồ sơ Gốc/Thay thế còn hiệu lực đang giữ hóa đơn bán (trừ hồ sơ `tru`)."""
    rows = frappe.db.sql("""SELECT h.name, h.nguoi_xu_ly FROM `tabAPH Hoa don ngoai` h
        JOIN `tabAPH Dong hoa don ngoai` d ON d.parent=h.name
        WHERE d.sales_invoice=%s AND h.docstatus<2 AND h.loai IN ('Gốc','Thay thế') AND h.trang_thai IN %s
          AND h.name!=%s""", (sales_invoice, HD_HIEU_LUC, tru or ""), as_dict=True)
    return rows[0] if rows else None


def validate_hoa_don_ngoai(doc):
    if not enabled():
        frappe.throw("Tính năng hồ sơ hóa đơn MISA chưa được bật")
    user = frappe.session.user
    if doc.is_new() and not doc.nguoi_xu_ly:
        doc.nguoi_xu_ly, doc.nhan_luc = user, now_datetime()
    elif doc.nguoi_xu_ly and doc.nguoi_xu_ly != user and user != "Administrator" \
            and "Accounts Manager" not in frappe.get_roles():
        frappe.throw(f"Hồ sơ đang do {doc.nguoi_xu_ly} xử lý", frappe.PermissionError)
    if doc.loai != "Gốc":
        if not doc.hoa_don_lien_quan:
            frappe.throw("Chọn hồ sơ hóa đơn bị điều chỉnh / thay thế / hủy")
        lq = frappe.db.get_value(DT_HD, doc.hoa_don_lien_quan, ["docstatus", "company", "customer"], as_dict=True)
        if not lq or lq.docstatus != 1 or lq.company != doc.company:
            frappe.throw("Hồ sơ liên quan phải đã ghi sổ và cùng đơn vị phát hành")
        if not doc.get("dong"):
            for d in frappe.get_all("APH Dong hoa don ngoai", {"parent": doc.hoa_don_lien_quan}, ["sales_invoice"],
                                    order_by="idx"):
                doc.append("dong", {"sales_invoice": d.sales_invoice})
        doc.customer = doc.customer or lq.customer
    tong_qt = 0
    for d in doc.get("dong") or []:
        si = frappe.db.get_value("Sales Invoice", d.sales_invoice,
                                 ["docstatus", "company", "customer", "posting_date", "base_grand_total"], as_dict=True)
        if not si or si.docstatus != 1 or si.company != doc.company:
            frappe.throw(f"Dòng {d.idx}: hóa đơn bán phải đã ghi sổ và thuộc {doc.company}")
        d.customer, d.posting_date, d.doanh_thu = si.customer, si.posting_date, si.base_grand_total
        tong_qt += flt(si.base_grand_total)
        if doc.loai in ("Gốc", "Thay thế"):
            giu = _dang_giu(d.sales_invoice, tru=doc.name if not doc.is_new() else None)
            if giu and not (doc.loai == "Thay thế" and giu.name == doc.hoa_don_lien_quan):
                frappe.throw(f"Hóa đơn {d.sales_invoice} đang thuộc hồ sơ {giu.name} ({giu.nguoi_xu_ly} xử lý)",
                             title="Chống xuất trùng")
        doc.customer = doc.customer or si.customer
    doc.tong = flt(doc.tien_truoc_thue) + flt(doc.tien_thue)
    doc.doanh_thu_quan_tri = tong_qt
    doc.chenh_lech = flt(doc.tong) - tong_qt  # Q148: chỉ hiển thị, không chặn


def _ghi_hd_ban(doc, xoa=False):
    from kh_aph.constants import SI_EINV_DATE, SI_EINV_NO, SI_EINV_SERIES
    gia_tri = {SI_EINV_SERIES: None, SI_EINV_NO: None, SI_EINV_DATE: None} if xoa else \
        {SI_EINV_SERIES: doc.ky_hieu, SI_EINV_NO: doc.so, SI_EINV_DATE: doc.ngay}
    for d in doc.get("dong") or []:
        frappe.db.set_value("Sales Invoice", d.sales_invoice, gia_tri, update_modified=False)


def submit_hoa_don_ngoai(doc):
    if doc.loai != "Hủy" and not (doc.ky_hieu and doc.so and doc.ngay):
        frappe.throw("Nhập ký hiệu, số và ngày hóa đơn đã xuất trên MISA trước khi ghi sổ")
    doc.db_set("trang_thai", "Đã xuất")
    if doc.loai == "Gốc":
        _ghi_hd_ban(doc)
        return
    lq = frappe.get_doc(DT_HD, doc.hoa_don_lien_quan)
    if doc.loai == "Thay thế":
        lq.db_set("trang_thai", "Bị thay thế")
        _ghi_hd_ban(doc)
    elif doc.loai == "Điều chỉnh":
        lq.db_set("trang_thai", "Bị điều chỉnh")
    else:  # Hủy: hóa đơn bán quay lại hàng đợi
        lq.db_set("trang_thai", "Đã hủy")
        _ghi_hd_ban(lq, xoa=True)


def cancel_hoa_don_ngoai(doc):
    doc.db_set("trang_thai", "Đã hủy")
    if doc.loai == "Gốc":
        _ghi_hd_ban(doc, xoa=True)
    elif doc.hoa_don_lien_quan:
        lq = frappe.get_doc(DT_HD, doc.hoa_don_lien_quan)
        lq.db_set("trang_thai", "Đã xuất")
        if doc.loai in ("Thay thế", "Hủy"):
            _ghi_hd_ban(lq)


@frappe.whitelist(methods=["POST"])
def nhan_xu_ly(sales_invoices):
    """Hàng đợi: nhận xử lý một hoặc nhiều hóa đơn bán cùng đơn vị → hồ sơ Gốc NHÁP đứng tên người bấm."""
    _can_ke_toan()
    ds = frappe.parse_json(sales_invoices) if isinstance(sales_invoices, str) else sales_invoices
    ds = list(dict.fromkeys(ds or []))
    if not ds:
        frappe.throw("Chọn hóa đơn bán")
    for n in ds:
        frappe.db.sql("SELECT name FROM `tabSales Invoice` WHERE name=%s FOR UPDATE", n)
        giu = _dang_giu(n)
        if giu:
            frappe.throw(f"Hóa đơn {n} đang thuộc hồ sơ {giu.name} ({giu.nguoi_xu_ly} xử lý)", title="Chống xuất trùng")
    company = frappe.db.get_value("Sales Invoice", ds[0], "company")
    doc = frappe.get_doc({"doctype": DT_HD, "loai": "Gốc", "company": company,
                          "dong": [{"sales_invoice": n} for n in ds]})
    doc.insert()
    return {"ho_so": doc.name}


def guard_quality_credit(doc, method=None):
    """Kiểm lại khi xác nhận đề nghị cũ; số còn nợ có thể đã giảm bởi trả hàng/thu tiền."""
    if not enabled():
        return
    protect_quality_source(doc)
    if not doc.get(F_JE_HD):
        return
    frappe.db.sql('SELECT name FROM `tabSales Invoice` WHERE name=%s FOR UPDATE', doc.get(F_JE_HD))
    source = frappe.get_doc('Sales Invoice', doc.get(F_JE_HD), for_update=True)
    source.check_permission('read')
    if source.docstatus != 1 or cint(source.is_return) or source.company != doc.company:
        frappe.throw('Bút toán giảm phải gắn hóa đơn bán gốc còn hiệu lực cùng đơn vị')
    references = [r for r in doc.accounts if r.get('reference_type') == 'Sales Invoice']
    if any(r.reference_name != source.name or r.party_type != 'Customer' or r.party != source.customer
           or r.account != source.debit_to for r in references):
        frappe.throw('Đề nghị giảm chỉ phân bổ vào đúng khoản gốc và khách đã chọn')
    amount = sum(flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency) for r in references)
    if amount <= 0 or amount > flt(source.outstanding_amount) + 0.5:
        frappe.throw('Khoản còn nợ đã thay đổi; đối chiếu và sửa đề nghị giảm trước khi xác nhận')


def protect_quality_source(doc, method=None):
    if not enabled():
        return
    old = doc.get_doc_before_save()
    if old and old.get(F_JE_HD) and old.get(F_JE_HD) != doc.get(F_JE_HD):
        frappe.throw('Không đổi hoặc xóa khoản gốc của đề nghị giảm đã lưu')
    if not doc.get(F_JE_HD) and doc.get('amended_from'):
        source = frappe.db.get_value('Journal Entry', doc.amended_from, F_JE_HD)
        if source:
            doc.set(F_JE_HD, source)
