"""Đơn tổng APH (0.3.9): một đơn của khách, nhiều đơn vị bán, dòng có / không xuất hóa đơn.

Xác nhận: tách thành Đơn bán hàng chuẩn — mỗi (đơn vị × có/không hóa đơn) một đơn, gắn ô aphvh_don_tong
(ô này đi theo sang phiếu giao, hóa đơn khi lập từ đơn). Hủy: hủy các đơn con chưa giao, chưa lập hóa đơn.
Tình hình (tinh_hinh): tiền đơn, đã lập hóa đơn, đã thu, còn phải thu — từng đơn con và cả đơn.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt

from aphvh import don_tong_rules as R
from aphvh.vn_words import so_vn

F_DON_TONG = "aphvh_don_tong"  # Sales Order / Delivery Note / Sales Invoice / Payment Entry


class DonTongAPH(Document):
    def validate(self):
        for r in self.items:
            if not r.xuat_hoa_don and self.xuat_hd_mac_dinh:
                r.xuat_hoa_don = self.xuat_hd_mac_dinh
            r.amount = flt(r.qty) * flt(r.rate)
            if r.warehouse and frappe.get_cached_value("Warehouse", r.warehouse, "company") != r.cong_ty:
                frappe.throw(f"Dòng {r.idx}: kho {frappe.bold(r.warehouse)} không thuộc đơn vị {frappe.bold(r.cong_ty)}.")
        self.tong_tien_hang = sum(flt(r.amount) for r in self.items)
        if not self.ap_thue and self.customer:
            self.ap_thue = frappe.get_cached_value("Customer", self.customer, "tax_category")
        loi = R.row_problems(self.items)
        if loi:
            frappe.throw("<br>".join(loi), title="Đơn tổng chưa đủ thông tin")

    def on_submit(self):
        made = []
        for (cong_ty, xuat_hd), rows in R.group_rows(self.items):
            so = frappe.get_doc(
                {
                    "doctype": "Sales Order",
                    "company": cong_ty,
                    "customer": self.customer,
                    "transaction_date": self.transaction_date,
                    "delivery_date": self.delivery_date,
                    "aphvh_xuat_hoa_don": xuat_hd,
                    "aphvh_ap_thue": self.ap_thue if xuat_hd == "Có" else None,
                    F_DON_TONG: self.name,
                    "items": [
                        {
                            "item_code": r.item_code,
                            "qty": r.qty,
                            "uom": r.uom,
                            "rate": r.rate,
                            "warehouse": r.warehouse,
                            "delivery_date": self.delivery_date,
                        }
                        for r in rows
                    ],
                }
            )
            if self.ghi_chu and so.meta.has_field("terms"):
                so.terms = self.ghi_chu
            so.insert()
            so.submit()
            for r in rows:
                r.db_set("sales_order", so.name, update_modified=False)
            made.append(so.name)
        frappe.msgprint(
            "Đã tách thành đơn bán hàng: " + ", ".join(frappe.bold(n) for n in made),
            title="Đơn tổng đã xác nhận",
            indicator="green",
        )

    def on_cancel(self):
        names = sorted({r.sales_order for r in self.items if r.sales_order})
        for n in names:
            so = frappe.get_doc("Sales Order", n)
            if so.docstatus != 1:
                continue
            if flt(so.per_delivered) or flt(so.per_billed):
                frappe.throw(
                    f"Đơn bán {frappe.bold(n)} đã giao hoặc đã lập hóa đơn. Hủy phiếu giao / hóa đơn trước, rồi hủy đơn tổng.",
                    title="Không hủy được đơn tổng",
                )
            so.cancel()

    def onload(self):
        if self.docstatus > 0:
            self.set_onload("tinh_hinh", tinh_hinh(self.name))


def _so_names(don_tong: str) -> list:
    return frappe.get_all("Sales Order", {F_DON_TONG: don_tong, "docstatus": 1}, pluck="name", order_by="company, name")


@frappe.whitelist()
def tinh_hinh(name: str) -> dict:
    """Tình hình đơn tổng: từng đơn con (đơn vị × có/không HĐ) và tổng."""
    frappe.has_permission("Don Tong APH", "read", name, throw=True)
    rows = []
    for so_name in _so_names(name):
        so = frappe.db.get_value(
            "Sales Order",
            so_name,
            ["name", "company", "aphvh_xuat_hoa_don", "grand_total", "rounded_total", "per_delivered", "per_billed", "status", "transaction_date"],
            as_dict=True,
        )
        sis = frappe.db.sql(
            """select distinct si.name, si.grand_total, si.rounded_total, si.outstanding_amount, si.docstatus
               from `tabSales Invoice` si join `tabSales Invoice Item` i on i.parent = si.name
               where i.sales_order = %s and si.docstatus < 2 and si.is_return = 0""",
            so_name,
            as_dict=True,
        )
        lap = sum(flt(s.rounded_total or s.grand_total) for s in sis if s.docstatus == 1)
        refs = [so_name] + [s.name for s in sis if s.docstatus == 1]
        thu = _da_thu(refs)
        tong = flt(so.rounded_total or so.grand_total)
        rows.append(
            {
                "don_ban": so.name,
                "cong_ty": frappe.get_cached_value("Company", so.company, "abbr") or so.company,
                "xuat_hd": cstr(so.aphvh_xuat_hoa_don),
                "tong": tong,
                "da_giao_pt": flt(so.per_delivered),
                "hoa_don": [s.name + ("" if s.docstatus == 1 else " (nháp)") for s in sis],
                "da_lap_hd": lap,
                "da_thu": thu,
                "con_phai_thu": tong - thu,
                "si_con_no": sum(flt(x.outstanding_amount) for x in sis if x.docstatus == 1),
                "hoa_don_mo": [
                    {"ten": x.name, "con_lai": flt(x.outstanding_amount)} for x in sis if x.docstatus == 1 and flt(x.outstanding_amount) > 0
                ],
                "ngay": str(so.transaction_date),
            }
        )
    return {"don_con": rows, "tong": R.tong_hop(rows)}


def _da_thu(refs: list) -> float:
    """Tiền đã thu gắn với đơn bán / hóa đơn: phiếu thu (Payment Entry) và chứng từ ghi có 131 của khách
    có tham chiếu (phần thu hộ của đơn vị khác — phiếu thu gộp)."""
    if not refs:
        return 0.0
    pe = frappe.db.sql(
        """select ifnull(sum(r.allocated_amount), 0) from `tabPayment Entry Reference` r
           join `tabPayment Entry` p on p.name = r.parent
           where p.docstatus = 1 and r.reference_name in %s""",
        (tuple(refs),),
    )[0][0]
    je = frappe.db.sql(
        """select ifnull(sum(a.credit_in_account_currency - a.debit_in_account_currency), 0)
           from `tabJournal Entry Account` a join `tabJournal Entry` j on j.name = a.parent
           where j.docstatus = 1 and a.party_type = 'Customer' and a.reference_name in %s""",
        (tuple(refs),),
    )[0][0]
    return flt(pe) + flt(je)


# --- Phiếu thu gộp (0.4.0) ---------------------------------------------------------------------


def _cho_thu(name: str) -> list:
    """Khoản còn phải thu của đơn tổng: hóa đơn còn nợ, và phần đơn bán chưa lập hóa đơn chưa thu."""
    out = []
    for d in tinh_hinh(name)["don_con"]:
        for h in d["hoa_don_mo"]:
            out.append({"cong_ty": d["cong_ty"], "loai": "SI", "ten": h["ten"], "con_lai": h["con_lai"], "ngay": d["ngay"]})
        so_con = flt(d["con_phai_thu"]) - flt(d["si_con_no"])
        if so_con > 0.5:
            out.append({"cong_ty": d["cong_ty"], "loai": "SO", "ten": d["don_ban"], "con_lai": so_con, "ngay": d["ngay"]})
    return out


def _abbr(company: str) -> str:
    return frappe.get_cached_value("Company", company, "abbr")


def _company_of(abbr: str) -> str:
    return frappe.db.get_value("Company", {"abbr": abbr}, "name")


def _acc(company: str, number: str) -> str:
    acc = frappe.db.get_value("Account", {"company": company, "account_number": number, "is_group": 0}, "name")
    if not acc:
        frappe.throw(
            f"Công ty {frappe.bold(company)} chưa có tài khoản {frappe.bold(number)} (công nợ nội bộ). "
            "Kế toán trưởng tạo tài khoản trước khi thu gộp.",
            title="Thiếu tài khoản nội bộ",
        )
    return acc


@frappe.whitelist()
def xem_thu_gop(name: str, so_tien: float, tk_nhan: str) -> dict:
    """Xem trước cách chia tiền (không ghi sổ)."""
    frappe.has_permission("Don Tong APH", "read", name, throw=True)
    nhan = frappe.get_cached_value("Account", tk_nhan, "company")
    plan = R.phan_bo_thu_gop(flt(so_tien), _abbr(nhan), _cho_thu(name))
    plan["don_vi_nhan"] = _abbr(nhan)
    return plan


@frappe.whitelist()
def thu_gop(name: str, so_tien: float, tk_nhan: str, ngay: str, tham_chieu: str | None = None, nguoi_nop: str | None = None) -> dict:
    """Thu tiền một lần cho cả đơn tổng.

    Đơn vị nhận tiền R: một phiếu thu đủ số tiền khách đưa — trừ hóa đơn / đơn của R, phần của đơn vị khác C
    trừ vào chứng từ giữ hộ (Nợ 131 khách / Có 3388x phải trả C), phần thừa là khách trả trước tại R.
    Đơn vị C: chứng từ Nợ 1388x phải thu R / Có 131 khách, trừ thẳng vào hóa đơn (đơn) của C.
    """
    dt = frappe.get_doc("Don Tong APH", name)
    dt.check_permission("read")
    if dt.docstatus != 1:
        frappe.throw("Đơn tổng chưa xác nhận.")
    t_nhan = frappe.get_cached_value("Account", tk_nhan, "account_type")
    if t_nhan not in ("Cash", "Bank"):
        frappe.throw("Tài khoản nhận tiền phải là tiền mặt hoặc ngân hàng.")
    if t_nhan == "Bank" and not tham_chieu:
        frappe.throw("Thu qua ngân hàng: nhập số tham chiếu (số giao dịch).")
    R_co = frappe.get_cached_value("Account", tk_nhan, "company")
    R_ab = _abbr(R_co)
    plan = R.phan_bo_thu_gop(flt(so_tien), R_ab, _cho_thu(name))
    khac: dict = {}
    for d in plan["dong"]:
        if d["cong_ty"] != R_ab:
            khac.setdefault(d["cong_ty"], []).append(d)

    giu_ho = {}
    for C_ab, rows in khac.items():
        tien = sum(flt(x["so_tien"]) for x in rows)
        _, phai_tra = R.tk_noi_bo(R_ab, C_ab)
        je = frappe.get_doc(
            {
                "doctype": "Journal Entry",
                "company": R_co,
                "posting_date": ngay,
                "user_remark": f"Đơn tổng {name}: khách trả gộp tại {R_ab}, phần của {C_ab} {so_vn(tien, 0)} — {R_ab} giữ hộ",
                "accounts": [
                    {"account": frappe.get_cached_value("Company", R_co, "default_receivable_account"),
                     "party_type": "Customer", "party": dt.customer, "debit_in_account_currency": tien},
                    {"account": _acc(R_co, phai_tra), "credit_in_account_currency": tien},
                ],
            }
        )
        je.insert()
        je.submit()
        giu_ho[C_ab] = (je.name, tien)

    pe = frappe.new_doc("Payment Entry")
    pe.update(
        {
            "payment_type": "Receive",
            "company": R_co,
            "posting_date": ngay,
            "party_type": "Customer",
            "party": dt.customer,
            "paid_from": frappe.get_cached_value("Company", R_co, "default_receivable_account"),
            "paid_to": tk_nhan,
            "paid_amount": flt(so_tien),
            "received_amount": flt(so_tien),
            "reference_no": tham_chieu or name,
            "reference_date": ngay,
            "aphvh_don_tong": name,
            "aphvh_nguoi_nop_nhan": nguoi_nop,
            "custom_remarks": 1,
        }
    )
    for d in plan["dong"]:
        if d["cong_ty"] == R_ab:
            pe.append("references", {"reference_doctype": "Sales Invoice" if d["loai"] == "SI" else "Sales Order",
                                     "reference_name": d["ten"], "allocated_amount": d["so_tien"]})
    for C_ab, (je_name, tien) in giu_ho.items():
        pe.append("references", {"reference_doctype": "Journal Entry", "reference_name": je_name, "allocated_amount": tien})
    phan = [
        f"{d['cong_ty']}{'' if d['cong_ty'] == R_ab else ' (giữ hộ)'} {'hóa đơn' if d['loai'] == 'SI' else 'đơn'} {d['ten']} {so_vn(d['so_tien'], 0)}"
        for d in plan["dong"]
    ]
    if plan["tra_truoc"]:
        phan.append(f"trả trước {so_vn(plan['tra_truoc'], 0)}")
    pe.remarks = f"Thu tiền đơn tổng {name} (thu gộp): " + "; ".join(phan)
    pe.setup_party_account_field()
    pe.set_missing_values()
    pe.set_missing_ref_details(force=True)
    pe.insert()
    pe.submit()

    don_vi = []
    for C_ab, rows in khac.items():
        C_co = _company_of(C_ab)
        phai_thu, _ = R.tk_noi_bo(C_ab, R_ab)
        tien = sum(flt(x["so_tien"]) for x in rows)
        accs = [{"account": _acc(C_co, phai_thu), "debit_in_account_currency": tien}]
        for x in rows:
            accs.append(
                {
                    "account": frappe.get_cached_value("Company", C_co, "default_receivable_account"),
                    "party_type": "Customer",
                    "party": dt.customer,
                    "credit_in_account_currency": x["so_tien"],
                    "reference_type": "Sales Invoice" if x["loai"] == "SI" else "Sales Order",
                    "reference_name": x["ten"],
                    "is_advance": "No" if x["loai"] == "SI" else "Yes",
                }
            )
        je = frappe.get_doc(
            {
                "doctype": "Journal Entry",
                "company": C_co,
                "posting_date": ngay,
                "user_remark": f"Đơn tổng {name}: khách trả gộp vào {R_ab} (phiếu thu {pe.name}), {R_ab} giữ hộ {so_vn(tien, 0)}",
                "accounts": accs,
            }
        )
        je.insert()
        je.submit()
        don_vi.append(je.name)

    return {
        "phieu_thu": pe.name,
        "giu_ho": [v[0] for v in giu_ho.values()],
        "chung_tu_don_vi": don_vi,
        "phan_bo": plan,
    }
