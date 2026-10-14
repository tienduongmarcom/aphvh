"""Tiêu hao so với định mức (0.11.2, cờ kh_aph_factory_costing). Đặc tả docs/dac-ta-0.11.2.md mục 3.

Một kho Dở dang dây chuyền, một kỳ quyết toán: (lần quyết toán về 0 trước mốc, mốc]. Chỉ số lượng, không có giá trị.
Định mức = sản lượng thành phẩm chính trong kỳ × BOM mặc định; mức cho phép = định mức × (1 + tỷ lệ hao hụt cho phép).
Thực tế = đã ghi tiêu hao trên phiếu sản xuất + phần xuất khi quyết toán (tự nhiên/bất thường) + phần còn trên sổ nếu kỳ chưa đóng.
"""

import frappe
from frappe.utils import cint, flt, get_datetime, now_datetime
from lab9x import gia_thanh as G


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not cint(frappe.conf.get("kh_aph_factory_costing")):
        frappe.throw("Tính năng giá thành nhà máy chưa được bật")
    from kh_aph import factory_costing as F
    wh = frappe.get_doc("Warehouse", filters.kho)
    wh.check_permission("read")
    if not F.la_do_dang(wh):
        frappe.throw(f"{filters.kho} không phải kho {F.DO_DANG}")
    moc = get_datetime(filters.moc) if filters.moc else now_datetime()
    ky = F.so_lieu_ky(filters.kho, moc)
    dm = F.dinh_muc(ky["san_luong"])
    sl_dm = {k: v for k, v in ky["san_luong"].items() if k in dm}
    can, _ = G.nhu_cau_dinh_muc(sl_dm, dm)
    muc, _ = G.nhu_cau_dinh_muc(sl_dm, dm, cong_ty_le=True)
    qt = {}
    dk_tu = "AND TIMESTAMP(se.posting_date, se.posting_time) > %(tu)s" if ky["tu"] else ""
    for r in frappe.db.sql(f"""SELECT d.item_code, se.kh_aph_loss_type AS loai, SUM(d.transfer_qty) AS sl
            FROM `tabStock Entry` se JOIN `tabStock Entry Detail` d ON d.parent=se.name
            WHERE se.docstatus=1 AND se.kh_aph_vet_bon=%(kho)s AND TIMESTAMP(se.posting_date, se.posting_time) <= %(moc)s
              {dk_tu} GROUP BY d.item_code, se.kh_aph_loss_type""",
                           {"kho": filters.kho, "moc": moc, "tu": ky["tu"]}, as_dict=True):
        q = qt.setdefault(r.item_code, {"tu_nhien": 0.0, "bat_thuong": 0.0})
        q["tu_nhien" if r.loai == "Hao hụt tự nhiên" else "bat_thuong"] += flt(r.sl)
    da_dong = bool(qt)
    ton = {} if da_dong else {i: flt(sl) for i, sl, _gt in F._ton_kho(filters.kho, moc.date(), moc.time()) if flt(sl)}
    cols = [
        {"fieldname": "item_code", "label": "Nguyên liệu", "fieldtype": "Link", "options": "Item", "width": 160},
        {"fieldname": "dinh_muc", "label": "Định mức", "fieldtype": "Float", "width": 110},
        {"fieldname": "muc", "label": "Mức cho phép", "fieldtype": "Float", "width": 110},
        {"fieldname": "da_dung", "label": "Đã ghi tiêu hao", "fieldtype": "Float", "width": 120},
        {"fieldname": "tu_nhien", "label": "Quyết toán: tự nhiên", "fieldtype": "Float", "width": 130},
        {"fieldname": "bat_thuong", "label": "Quyết toán: vượt định mức", "fieldtype": "Float", "width": 150},
        {"fieldname": "con_tren_so", "label": "Còn trên sổ (chưa quyết toán)", "fieldtype": "Float", "width": 150},
        {"fieldname": "thuc_te", "label": "Thực tế", "fieldtype": "Float", "width": 110},
        {"fieldname": "chenh", "label": "Chênh so với định mức", "fieldtype": "Float", "width": 140},
        {"fieldname": "pt", "label": "% chênh", "fieldtype": "Percent", "width": 90},
    ]
    rows = []
    for nl in sorted(set(can) | set(ky["da_dung"]) | set(qt) | set(ton)):
        q = qt.get(nl, {"tu_nhien": 0.0, "bat_thuong": 0.0})
        thuc = ky["da_dung"].get(nl, 0.0) + q["tu_nhien"] + q["bat_thuong"] + ton.get(nl, 0.0)
        c = can.get(nl, 0.0)
        rows.append({"item_code": nl, "dinh_muc": round(c, 3), "muc": round(muc.get(nl, 0.0), 3),
                     "da_dung": ky["da_dung"].get(nl, 0.0), "tu_nhien": q["tu_nhien"], "bat_thuong": q["bat_thuong"],
                     "con_tren_so": ton.get(nl, 0.0), "thuc_te": round(thuc, 3), "chenh": round(thuc - c, 3),
                     "pt": round((thuc - c) / c * 100, 2) if c else None})
    tu = ky["tu"].strftime("%d/%m/%Y %H:%M") if ky["tu"] else "đầu sổ"
    thieu = sorted(set(ky["san_luong"]) - set(dm))
    msg = (f"Kỳ {tu} → {moc:%d/%m/%Y %H:%M}, {len(ky['phieu'])} phiếu sản xuất, "
           + ("đã quyết toán." if da_dong else "chưa quyết toán (cột Còn trên sổ tính vào thực tế).")
           + (f" Thành phẩm chưa có định mức: {', '.join(thieu)}." if thieu else ""))
    return cols, rows, msg
