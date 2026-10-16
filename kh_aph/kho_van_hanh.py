"""Kho vận hành (lượt 0.13, cờ `kh_aph_kho_van_hanh`, mặc định tắt). Đặc tả docs/dac-ta-0.13.md mục 3–6.

- Workspace "Trung tâm Kho" (điều hướng, số đếm nhanh).
- R022: hàng không giao được → chuyển kho khác (xe quay về / chuyển khách đã có từ 0.11.1, kh_aph.sales_adjust).
- R024: sửa số lượng giao nhập sai bằng hủy và sửa chứng từ (không tạo trả hàng giả).
- R057–R059: báo cáo đề nghị bổ sung hàng theo mức đặt lại chuẩn, tạo Yêu cầu vật tư chuyển kho nhiều kho nguồn.
- Rà soát dòng 16: xử lý chênh lệch kiểm kê bước 2 theo vụ (biên bản kiểm kê 0.11.2) bằng bút toán nháp.
Quy tắc thuần ở lab9x.van_hanh.
"""
import frappe
from frappe.utils import cint, flt, getdate, nowdate
from lab9x import van_hanh as V

FLAG = "kh_aph_kho_van_hanh"
WORKSPACE = "Trung tâm Kho"
F_VU = "kh_aph_vu_kiem_ke"
F_LY_DO_SUA = "kh_aph_ly_do_sua_sl"
VAI_TRO_KHO = {"Stock User", "Stock Manager", "Thủ kho bán hàng", "Kế toán nhà máy", "Accounts User", "Accounts Manager",
               "System Manager"}

FIELDS = {
    "Journal Entry": [
        {"fieldname": F_VU, "label": "Vụ chênh lệch kiểm kê", "fieldtype": "Data", "insert_after": "voucher_type",
         "read_only": 1, "no_copy": 1, "description": "Biên bản kiểm kê có mốc (0.11.2) mà bút toán này xử lý (bước 2)."}],
    "Delivery Note": [
        {"fieldname": F_LY_DO_SUA, "label": "Lý do sửa số lượng nhập sai (R024)", "fieldtype": "Small Text",
         "insert_after": "kh_aph_delivery_at", "read_only": 1, "no_copy": 1}],
}


def enabled():
    return cint(frappe.conf.get(FLAG))


def _can_bat():
    if not enabled():
        frappe.throw("Kho vận hành 0.13 chưa được bật")


def _vai_tro(vai_tro):
    if frappe.session.user != "Administrator" and not (set(frappe.get_roles()) & set(vai_tro)):
        frappe.throw("Không đủ quyền", frappe.PermissionError)


def _ktt():
    from kh_aph.constants import ROLE_NO_COST
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and ("Accounts Manager" not in roles or ROLE_NO_COST in roles):
        frappe.throw("Cần quyền kế toán trưởng", frappe.PermissionError)


def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_kho_van_hanh trước khi cài")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    _workspace()
    return {"fields": sum(len(v) for v in FIELDS.values()), "workspace": WORKSPACE}


def _workspace():
    import json
    loi_vao = [
        ("Phiếu giao đang giao", "DocType", "Delivery Note", {"docstatus": 1, "kh_aph_delivery_state": "Đang giao"}),
        ("Phiếu giao chờ xuất", "DocType", "Delivery Note", {"docstatus": 0}),
        ("Phiếu kho", "DocType", "Stock Entry", None),
        ("Kiểm kê", "DocType", "Stock Reconciliation", None),
        ("Yêu cầu chuyển kho", "DocType", "Material Request", {"docstatus": 1, "status": ["not in", ["Transferred", "Stopped"]]}),
        ("Chênh lệch kiểm kê chờ xử lý", "Report", "Chenh lech kiem ke cho xu ly", None),
        ("Đề nghị bổ sung hàng", "Report", "De nghi bo sung hang", None),
        ("Tồn kho số lượng", "Report", "Ton kho so luong", None),
    ]
    loi_vao = [x for x in loi_vao if frappe.db.exists(x[1], x[2])]
    noi_dung = [{"id": "tk-tieu-de", "type": "header", "data": {"text": f"<span class=\"h4\"><b>{WORKSPACE}</b></span>", "col": 12}}]
    noi_dung += [{"id": f"tk-{i}", "type": "shortcut", "data": {"shortcut_name": x[0], "col": 4}} for i, x in enumerate(loi_vao)]
    ws = frappe.get_doc("Workspace", WORKSPACE) if frappe.db.exists("Workspace", WORKSPACE) else frappe.new_doc("Workspace")
    ws.update({"label": WORKSPACE, "title": WORKSPACE, "public": 1, "module": "Kh Aph", "icon": "stock",
               "content": json.dumps(noi_dung, ensure_ascii=False)})
    ws.set("shortcuts", [{"label": nhan, "type": loai, "link_to": dich, "color": "Grey",
                          **({"stats_filter": json.dumps(loc), "format": "{} " + nhan.lower()} if loc else {})}
                         for nhan, loai, dich, loc in loi_vao])
    ws.set("roles", [{"role": r} for r in sorted(VAI_TRO_KHO) if frappe.db.exists("Role", r)])
    ws.flags.ignore_permissions = True
    ws.save() if not ws.is_new() else ws.insert()


# ---------------------------------------------------------------- R022 chuyển kho khác

@frappe.whitelist(methods=["POST"])
def chuyen_kho_khac(delivery_note, warehouse):
    """Hàng trên xe không giao được, đưa về một kho khác cùng đơn vị: phiếu trả lại NHÁP vào kho đó (loại chở về kho)."""
    _can_bat()
    from kh_aph.sales_adjust import _phieu_tra_nhap
    cty = frappe.db.get_value("Delivery Note", delivery_note, "company")
    kho = frappe.db.get_value("Warehouse", warehouse, ["company", "is_group"], as_dict=True)
    if not kho or kho.company != cty or cint(kho.is_group):
        frappe.throw("Chọn kho chi tiết cùng đơn vị với phiếu giao")
    _dn, ret = _phieu_tra_nhap(delivery_note)
    for d in ret.items:
        d.warehouse = warehouse
    ret.add_comment("Comment", f"Hàng không giao được, chuyển về kho {warehouse} (R022)")
    ret.save()
    return {"phieu_tra": ret.name}


# ---------------------------------------------------------------- R024 sửa số lượng nhập sai

def _hoa_don_cua(dn_name):
    return frappe.db.sql_list("""SELECT DISTINCT si.name FROM `tabSales Invoice` si JOIN `tabSales Invoice Item` i
        ON i.parent=si.name WHERE i.delivery_note=%s AND si.docstatus=1 AND si.is_return=0""", dn_name)


@frappe.whitelist(methods=["POST"])
def sua_so_luong(delivery_note, so_luong, ly_do):
    """Hủy chứng từ sai rồi lập lại bản sửa (Amend). so_luong: {dn_detail: số lượng đúng} (JSON).

    - Chưa có hóa đơn: hủy phiếu giao, lập bản sửa nháp.
    - Có hóa đơn chưa thu / chưa phân bổ tiền: hủy hóa đơn rồi phiếu giao, lập bản sửa nháp (hóa đơn tự lập lại khi xuất).
    - Hóa đơn đã thu một phần / đã phân bổ, hoặc kỳ đã khóa: từ chối.
    """
    _can_bat()
    _ktt()
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do sửa số lượng")
    so_luong = frappe.parse_json(so_luong) if isinstance(so_luong, str) else (so_luong or {})
    frappe.db.sql("SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE", delivery_note)
    dn = frappe.get_doc("Delivery Note", delivery_note)
    if dn.docstatus != 1 or cint(dn.is_return):
        frappe.throw("Chỉ sửa phiếu giao đã xuất (không phải phiếu trả)")
    if frappe.db.exists("Delivery Note", {"return_against": dn.name, "docstatus": ["<", 2]}):
        frappe.throw("Phiếu đã có phiếu trả lại: xử lý bằng điều chỉnh có chứng từ, không hủy-sửa")
    hd = _hoa_don_cua(dn.name)
    for name in hd:
        si = frappe.db.get_value("Sales Invoice", name, ["outstanding_amount", "rounded_total", "grand_total"], as_dict=True)
        tong = flt(si.rounded_total or si.grand_total)
        if abs(flt(si.outstanding_amount) - tong) > 0.5 or frappe.db.exists(
                "Payment Ledger Entry", {"against_voucher_no": name, "voucher_no": ["!=", name], "delinked": 0}):
            frappe.throw(f"Hóa đơn {name} đã thu hoặc đã phân bổ tiền: dùng trả hàng / điều chỉnh có chứng từ (R024)")
    for d in dn.items:
        if d.name in so_luong and flt(so_luong[d.name]) <= 0:
            frappe.throw(f"Dòng {d.idx}: số lượng đúng phải lớn hơn 0 (giao 0 thì dùng trả hàng)")
    for name in hd:
        frappe.get_doc("Sales Invoice", name).cancel()
    dn.reload()
    dn.cancel()
    moi = frappe.copy_doc(dn)
    moi.amended_from = dn.name
    for f in ("kh_aph_delivery_state", "kh_aph_delivery_actor", "kh_aph_delivery_at"):
        if moi.meta.has_field(f):
            moi.set(f, None)
    for goc, d in zip(dn.items, moi.items):
        if goc.name in so_luong:
            d.qty = flt(so_luong[goc.name])
            if d.meta.has_field("kh_aph_bags") and d.get("kh_aph_bags") and flt(d.get("kh_aph_kg_per_bag")):
                d.kh_aph_bags = flt(d.qty) / flt(d.kh_aph_kg_per_bag)
    moi.set(F_LY_DO_SUA, ly_do.strip())
    moi.insert()
    moi.add_comment("Comment", f"Sửa số lượng nhập sai từ {dn.name} (R024) bởi {frappe.session.user}. "
                               f"Lý do: {ly_do.strip()}. Hóa đơn đã hủy: {', '.join(hd) or 'không có'}")
    return {"phieu_moi": moi.name, "hoa_don_da_huy": hd}


# ---------------------------------------------------------------- R057–R059 đề nghị bổ sung

def de_nghi(company=None, warehouse=None):
    """Mã × kho có mức đặt lại (Item Reorder) mà khả dụng + đang về dưới ngưỡng."""
    dk, gt = ["ir.warehouse_reorder_level>0"], {}
    if company:
        dk.append("w.company=%(c)s")
        gt["c"] = company
    if warehouse:
        dk.append("ir.warehouse=%(w)s")
        gt["w"] = warehouse
    rows = frappe.db.sql(f"""SELECT ir.parent AS item_code, ir.warehouse, ir.warehouse_reorder_level AS nguong,
            ir.warehouse_reorder_qty AS so_dat, w.company,
            IFNULL(b.actual_qty,0) AS ton, IFNULL(b.reserved_qty,0)+IFNULL(b.reserved_stock,0) AS da_giu,
            IFNULL(b.indented_qty,0)+IFNULL(b.ordered_qty,0) AS dang_ve
        FROM `tabItem Reorder` ir JOIN `tabWarehouse` w ON w.name=ir.warehouse
        JOIN `tabItem` i ON i.name=ir.parent AND i.disabled=0
        LEFT JOIN `tabBin` b ON b.item_code=ir.parent AND b.warehouse=ir.warehouse
        WHERE {' AND '.join(dk)}""", gt, as_dict=True)
    thieu = _thieu_cho_xu_ly()
    out = []
    for r in rows:
        r.thieu_cho = thieu.get((r.item_code, r.warehouse), 0)
        r.kha_dung = V.kha_dung(flt(r.ton), flt(r.da_giu), r.thieu_cho)
        r.de_nghi = V.so_de_nghi(r.kha_dung, flt(r.dang_ve), flt(r.nguong), flt(r.so_dat))
        if r.de_nghi > 0:
            out.append(r)
    return out


def _thieu_cho_xu_ly():
    """R056: phiếu xuất thiếu kiểm kê còn NHÁP (chưa xử lý) làm giảm lượng khả dụng."""
    from kh_aph.kho_chuan import F_KIEM_KE
    if not frappe.get_meta("Stock Entry").has_field(F_KIEM_KE):
        return {}
    return {(r.item_code, r.s_warehouse): flt(r.qty) for r in frappe.db.sql("""SELECT d.item_code, d.s_warehouse,
            SUM(d.transfer_qty) AS qty FROM `tabStock Entry` se JOIN `tabStock Entry Detail` d ON d.parent=se.name
            WHERE se.docstatus=0 AND se.purpose='Material Issue' AND IFNULL(se.{f},'')!=''
            GROUP BY d.item_code, d.s_warehouse""".format(f=F_KIEM_KE), as_dict=True)}


@frappe.whitelist(methods=["POST"])
def tao_yeu_cau_chuyen(dong):
    """Yêu cầu vật tư loại chuyển kho; mỗi dòng kho nguồn riêng (R059). Yêu cầu chưa xuất không giữ hàng (R058)."""
    _can_bat()
    _vai_tro(VAI_TRO_KHO)
    dong = frappe.parse_json(dong) if isinstance(dong, str) else dong
    if not dong:
        frappe.throw("Chọn ít nhất một dòng")
    theo_cty = {}
    for d in dong:
        if not d.get("from_warehouse") or d.get("from_warehouse") == d.get("warehouse") or flt(d.get("qty")) <= 0:
            frappe.throw(f"{d.get('item_code')}: chọn kho nguồn khác kho nhận và số lượng > 0")
        cty = frappe.db.get_value("Warehouse", d["warehouse"], "company")
        if frappe.db.get_value("Warehouse", d["from_warehouse"], "company") != cty:
            frappe.throw(f"{d.get('item_code')}: kho nguồn và kho nhận phải cùng đơn vị (khác đơn vị là mua bán nội bộ)")
        theo_cty.setdefault(cty, []).append(d)
    ten = []
    for cty, ds in theo_cty.items():
        mr = frappe.get_doc({"doctype": "Material Request", "material_request_type": "Material Transfer", "company": cty,
                             "transaction_date": nowdate(), "schedule_date": nowdate(),
                             "items": [{"item_code": d["item_code"], "qty": flt(d["qty"]), "warehouse": d["warehouse"],
                                        "from_warehouse": d["from_warehouse"], "schedule_date": nowdate()} for d in ds]})
        mr.insert()
        ten.append(mr.name)
    return {"yeu_cau": ten}


# ---------------------------------------------------------------- kiểm kê bước 2 (rà soát dòng 16)

def _tk(company, so):
    """TK lá theo số hiệu; nếu số hiệu là nhóm (vd 632) thì lấy lá chi tiết đầu tiên (632 ưu tiên 6322 hao hụt)."""
    uu_tien = {"632": ("6322", "632")}.get(so, (so,))
    for s in uu_tien:
        t = frappe.db.get_value("Account", {"company": company, "account_number": s, "is_group": 0}, "name")
        if t:
            return t
    t = frappe.db.sql("""SELECT name FROM `tabAccount` WHERE company=%s AND is_group=0 AND account_number LIKE %s
        ORDER BY account_number LIMIT 1""", (company, so + "%"))
    if not t:
        frappe.throw(f"{company} chưa có tài khoản {so}")
    return t[0][0]


def vu_con_lai(bien_ban):
    """(công ty, thiếu 1381 còn chờ, thừa 3381 còn chờ) của một vụ: phiếu kiểm kê đã ghi sổ + bút toán xử lý đã ghi sổ."""
    from kh_aph.kho_chuan import F_KIEM_KE, TK_THIEU, TK_THUA
    phieu = frappe.get_all("Stock Entry", {F_KIEM_KE: bien_ban, "docstatus": 1}, ["name", "company"])
    if not phieu:
        frappe.throw(f"Không có phiếu kiểm kê đã ghi sổ cho biên bản {bien_ban}")
    cty = phieu[0].company
    je = frappe.get_all("Journal Entry", {F_VU: bien_ban, "docstatus": 1}, pluck="name")
    ct = [p.name for p in phieu] + je
    def du(so):
        tk = _tk(cty, so)
        return flt(frappe.db.sql("""SELECT SUM(debit-credit) FROM `tabGL Entry` WHERE is_cancelled=0 AND account=%s
            AND voucher_no IN %s""", (tk, ct))[0][0])
    return cty, round(du(TK_THIEU), 2), round(-du(TK_THUA), 2)


@frappe.whitelist(methods=["POST"])
def xu_ly_chenh_lech(bien_ban, dong):
    """Bút toán NHÁP xử lý vụ chênh lệch. dong: [{"phuong_an", "so_tien", "party_type", "party", "ghi_chu"}] (JSON).
    Kế toán trưởng xem và xác nhận bút toán; vụ hết chờ khi 1381 / 3381 của vụ về 0."""
    _can_bat()
    _ktt()
    dong = frappe.parse_json(dong) if isinstance(dong, str) else dong
    cty, thieu, thua = vu_con_lai(bien_ban)
    # bút toán nháp chưa ghi sổ của cùng vụ cũng chiếm phần còn lại (tránh lập trùng)
    for je in frappe.get_all("Journal Entry", {F_VU: bien_ban, "docstatus": 0}, pluck="name"):
        for a in frappe.get_doc("Journal Entry", je).accounts:
            so = frappe.get_cached_value("Account", a.account, "account_number") or ""
            if so.startswith("1381"):
                thieu -= flt(a.credit_in_account_currency)
            elif so.startswith("3381"):
                thua -= flt(a.debit_in_account_currency)
    loi = V.kiem_xu_ly(thieu, thua, [(d.get("phuong_an"), flt(d.get("so_tien"))) for d in dong or []])
    if loi:
        frappe.throw("<br>".join(loi), title="Xử lý chênh lệch kiểm kê")
    acc = []
    for d in dong:
        _ben, no, co = V.PHUONG_AN[d["phuong_an"]]
        tien = flt(d["so_tien"])
        for so, phia in ((no, "debit_in_account_currency"), (co, "credit_in_account_currency")):
            tk = _tk(cty, so)
            row = {"account": tk, phia: tien, "user_remark": d.get("ghi_chu") or d["phuong_an"]}
            if frappe.get_cached_value("Account", tk, "account_type") in ("Receivable", "Payable"):
                if not (d.get("party_type") and d.get("party")):
                    frappe.throw(f"{d['phuong_an']}: tài khoản {tk} cần chọn đối tượng (người bồi thường / người nhận)")
                row.update({"party_type": d["party_type"], "party": d["party"]})
            acc.append(row)
    je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": cty, "posting_date": nowdate(),
                         F_VU: bien_ban, "user_remark": f"Xử lý chênh lệch kiểm kê {bien_ban} (bước 2)", "accounts": acc})
    je.insert()
    return {"but_toan": je.name, "con_thieu": thieu, "con_thua": thua}


def cac_vu(company=None):
    """Các vụ (biên bản) có phiếu kiểm kê đã ghi sổ còn chênh lệch chờ xử lý."""
    from kh_aph.kho_chuan import F_KIEM_KE
    if not frappe.get_meta("Stock Entry").has_field(F_KIEM_KE):
        return []
    loc = {"docstatus": 1, F_KIEM_KE: ["is", "set"]}
    if company:
        loc["company"] = company
    out = []
    for bb in sorted(set(frappe.get_all("Stock Entry", loc, pluck=F_KIEM_KE))):
        cty, thieu, thua = vu_con_lai(bb)
        if abs(thieu) > 0.5 or abs(thua) > 0.5:
            nhap = frappe.get_all("Journal Entry", {F_VU: bb, "docstatus": 0}, pluck="name")
            out.append({"bien_ban": bb, "company": cty, "thieu": thieu, "thua": thua, "but_toan_nhap": ", ".join(nhap)})
    return out
