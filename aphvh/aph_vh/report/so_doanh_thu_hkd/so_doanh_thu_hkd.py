"""Sổ doanh thu hộ kinh doanh (TT152/2025): S1a-HKD, S2a-HKD, S2b-HKD — lập từ hóa đơn bán hàng của đơn vị hộ kinh doanh."""

import frappe
from frappe.utils import flt

from aphvh.so_hkd_rules import NGANH_MAC_DINH, dong_so

F_NGANH = "aphvh_nganh_hkd"  # Item Group


def _nganh_cua_nhom(group, cache):
    """Ngành nghề HKD của nhóm hàng: lấy ở nhóm hoặc nhóm cha gần nhất; không có thì mặc định phân phối hàng hóa."""
    if group in cache:
        return cache[group]
    g, val = group, None
    while g and not val:
        val, g = frappe.db.get_value("Item Group", g, [F_NGANH, "parent_item_group"]) if frappe.db.exists("Item Group", g) else (None, None)
    cache[group] = val or NGANH_MAC_DINH
    return cache[group]


def _dong(f):
    cond, args = "", [f.company, f.from_date, f.to_date]
    if f.pham_vi == "Chỉ bán có hóa đơn":
        cond = " and si.aphvh_xuat_hoa_don = 'Có'"
    items = frappe.db.sql(
        f"""select si.name, si.posting_date, si.customer_name, si.is_return, si.aphvh_hd_so, i.item_name, i.item_group,
                   i.base_net_amount amt
            from `tabSales Invoice` si join `tabSales Invoice Item` i on i.parent = si.name
            where si.company = %s and si.docstatus = 1 and si.posting_date between %s and %s{cond}
            order by si.posting_date, si.name, i.idx""",
        args,
        as_dict=True,
    )
    cache, gom = {}, {}
    for r in items:
        nganh = _nganh_cua_nhom(r.item_group, cache)
        k = (r.name, nganh)
        if k not in gom:
            loai = "Hàng bán bị trả lại" if r.is_return else "Bán hàng"
            gom[k] = {"ngay": r.posting_date, "so": r.aphvh_hd_so or r.name, "chung_tu": r.name, "nganh": nganh,
                      "dien_giai": f"{loai} cho {r.customer_name}: ", "_ten": [], "so_tien": 0.0}
        gom[k]["so_tien"] += flt(r.amt)
        if len(gom[k]["_ten"]) < 3 and r.item_name not in gom[k]["_ten"]:
            gom[k]["_ten"].append(r.item_name)
    out = []
    for v in gom.values():
        v["dien_giai"] += ", ".join(v.pop("_ten"))
        out.append(v)
    return out


def execute(filters=None):
    f = frappe._dict(filters or {})
    f.mau_so = f.mau_so or "S2a-HKD"
    cols = [
        {"fieldname": "so", "label": "Số hiệu chứng từ", "fieldtype": "Data", "width": 170},
        {"fieldname": "ngay", "label": "Ngày tháng", "fieldtype": "Date", "width": 100},
        {"fieldname": "dien_giai", "label": "Diễn giải", "fieldtype": "Data", "width": 420},
        {"fieldname": "so_tien", "label": "Số tiền", "fieldtype": "Currency", "width": 140},
        {"fieldname": "kieu", "label": "Loại dòng", "fieldtype": "Data", "hidden": 1},
    ]
    if not (f.company and f.from_date and f.to_date):
        return cols, []
    rows = dong_so(f.mau_so, _dong(f))
    if rows:
        from aphvh.print_utils import aphvh_cong_ty

        c = aphvh_cong_ty(f.company)
        rows[-1].update(ten_ho=c.get("ten"), dia_chi=c.get("dia_chi"), mst=c.get("mst"))
    return cols, rows
