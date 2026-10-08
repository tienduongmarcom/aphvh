"""Tồn kho theo tài khoản × địa điểm, đối chiếu sổ cái (0.4.18). Có giá trị: chỉ cho kế toán."""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from lab9x.ton_kho_tk_rules import dia_diem, tai_khoan, tong_hop


def execute(filters=None):
    f = frappe._dict(filters or {})
    if not f.company:
        frappe.throw(_("Chọn công ty"))
    f.den_ngay = f.den_ngay or nowdate()
    cols = [
        {"label": _("Tài khoản kho"), "fieldname": "tk", "fieldtype": "Data", "width": 260},
        {"label": _("Địa điểm"), "fieldname": "dia_diem", "fieldtype": "Data", "width": 200},
        {"label": _("Giá trị tồn kho"), "fieldname": "gia_tri", "fieldtype": "Currency", "width": 160},
        {"label": _("Số dư sổ cái"), "fieldname": "so_cai", "fieldtype": "Currency", "width": 160},
        {"label": _("Chênh lệch"), "fieldname": "chenh_lech", "fieldtype": "Currency", "width": 140},
        {"label": "", "fieldname": "kieu", "fieldtype": "Data", "hidden": 1},
    ]
    return cols, _data(f)


def _data(f):
    ws = frappe.get_all("Warehouse", {"company": f.company}, ["name", "parent_warehouse", "is_group"])
    cha = {w.name: w.parent_warehouse for w in ws}
    goc = {w.name for w in ws if not w.parent_warehouse}

    mac_dinh_ct = frappe.db.get_value("Company", f.company, "default_inventory_account")
    item_def = dict(frappe.db.sql("select parent, default_inventory_account from `tabItem Default` where company=%s "
                                  "and ifnull(default_inventory_account,'')!='' and parenttype='Item'", f.company))
    grp_def = dict(frappe.db.sql("select parent, default_inventory_account from `tabItem Default` where company=%s "
                                 "and ifnull(default_inventory_account,'')!='' and parenttype='Item Group'", f.company))
    nhom = dict(frappe.db.sql("select name, item_group from tabItem"))

    rows = frappe.db.sql(
        """select item_code, warehouse, sum(stock_value_difference) gt from `tabStock Ledger Entry`
           where company=%s and is_cancelled=0 and posting_date<=%s group by item_code, warehouse""",
        (f.company, f.den_ngay), as_dict=True)
    ten = {}
    dong = []
    for r in rows:
        if not flt(r.gt):
            continue
        tk = tai_khoan(item_def.get(r.item_code), grp_def.get(nhom.get(r.item_code)), mac_dinh_ct)
        dd = dia_diem(r.warehouse, cha, goc)
        ten[dd] = dd.rsplit(" - ", 1)[0]
        dong.append({"tk": tk, "dia_diem": dd, "gia_tri": flt(r.gt)})

    tks = frappe.get_all("Account", {"company": f.company, "account_type": "Stock", "is_group": 0}, pluck="name")
    so_cai = {}
    for tk in tks:
        v = frappe.db.sql("select sum(debit-credit) from `tabGL Entry` where company=%s and account=%s and is_cancelled=0 "
                          "and posting_date<=%s", (f.company, tk, f.den_ngay))[0][0]
        so_cai[tk] = flt(v)
    if f.chi_tk:
        dong = [d for d in dong if d["tk"] == f.chi_tk]
        so_cai = {k: v for k, v in so_cai.items() if k == f.chi_tk}
    return tong_hop(dong, so_cai, lambda x: ten.get(x, x))
