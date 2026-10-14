"""Trung tâm dữ liệu (0.12.0, cờ `kh_aph_du_lieu`, mặc định tắt). Đặc tả docs/dac-ta-0.12.0-0.12.1.md mục 2.

- Workspace chuẩn "Trung tâm dữ liệu": lối vào nhập dữ liệu (Data Import chuẩn), đề nghị chờ duyệt, danh sách rà soát,
  công cụ số dư đầu kỳ.
- "APH De nghi so lieu": số liệu nhà máy (kg tịnh, sản lượng mẻ, hao hụt, định mức mặc định) không sửa thẳng mà qua đề nghị
  có người duyệt (K5 của 0.11.2). Duyệt thì app ghi vào mã hàng / định mức và lưu nhật ký trước–sau.
  Định mức đã xác nhận: tạo bản định mức mới (ERPNext không cho sửa), bản cũ giữ nguyên.
Quy tắc kiểm thuần ở lab9x.du_lieu.
"""
import json

import frappe
from frappe.utils import cint, flt, now_datetime
from lab9x import du_lieu as D

from kh_aph.constants import ROLE_FACTORY, ROLE_NO_COST

FLAG = "kh_aph_du_lieu"
DT = "APH De nghi so lieu"
F_HAO_HUT = "kh_aph_hao_hut_cho_phep"
WORKSPACE = "Trung tâm dữ liệu"
VAI_TRO_LAP = {ROLE_FACTORY, "Manufacturing Manager", "Manufacturing User", "Stock Manager", "Item Manager",
               "Accounts Manager", "System Manager"}
VAI_TRO_DUYET = {"Accounts Manager", "System Manager"}

# truong -> (DocType đích, fieldname, nhãn)
TRUONG = {
    "kg_tinh": ("Item", "weight_per_unit", "Kg tịnh mỗi đơn vị"),
    "san_luong_me": ("BOM", "quantity", "Sản lượng mỗi mẻ (số lượng thành phẩm của định mức)"),
    "hao_hut": ("BOM", F_HAO_HUT, "Tỷ lệ hao hụt cho phép (%)"),
    "dinh_muc_mac_dinh": ("BOM", "is_default", "Đặt làm định mức mặc định"),
}


def enabled():
    return cint(frappe.conf.get(FLAG))


def _can_bat():
    if not enabled():
        frappe.throw("Trung tâm dữ liệu 0.12.0 chưa được bật")


def _co_vai_tro(vai_tro):
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles())
    return bool(roles & set(vai_tro))


def co_quyen_duyet():
    """Chị Dung / quản trị. Người dùng hồ sơ không xem giá vốn (Dũng) không duyệt được dù có vai trò kế toán."""
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles())
    return bool(roles & VAI_TRO_DUYET) and ROLE_NO_COST not in roles


# ---------------------------------------------------------------- cài đặt

def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_du_lieu trước khi cài")
    for dt in ("APH Dong de nghi so lieu", DT):
        frappe.reload_doc("kh_aph", "doctype", frappe.scrub(dt))
    _workspace()
    return {"doctype": DT, "workspace": WORKSPACE}


def _workspace():
    loi_vao = [
        ("Đề nghị cập nhật số liệu", "DocType", DT),
        ("Dữ liệu cần rà soát", "Report", "Du lieu can ra soat"),
        ("Nhập dữ liệu (Data Import)", "DocType", "Data Import"),
        ("Đối chiếu số dư đầu kỳ", "Report", "Doi chieu so du dau ky"),
        ("Số dư đầu kỳ theo bảng nguồn", "DocType", "APH So du dau ky nguon"),
        ("Tồn kho đầu kỳ (Điều chỉnh theo kiểm kê)", "DocType", "Stock Reconciliation"),
        ("Công nợ đầu kỳ (Opening Invoice Creation Tool)", "DocType", "Opening Invoice Creation Tool"),
        ("Tiền đầu kỳ (Bút toán)", "DocType", "Journal Entry"),
    ]
    loi_vao = [x for x in loi_vao if frappe.db.exists(x[1], x[2])]
    noi_dung = [{"id": "td-tieu-de", "type": "header",
                 "data": {"text": f"<span class=\"h4\"><b>{WORKSPACE}</b></span>", "col": 12}}]
    noi_dung += [{"id": f"td-{i}", "type": "shortcut", "data": {"shortcut_name": nhan, "col": 4}}
                 for i, (nhan, _l, _t) in enumerate(loi_vao)]
    ws = frappe.get_doc("Workspace", WORKSPACE) if frappe.db.exists("Workspace", WORKSPACE) else frappe.new_doc("Workspace")
    ws.update({"label": WORKSPACE, "title": WORKSPACE, "public": 1, "module": "Kh Aph", "icon": "database",
               "content": json.dumps(noi_dung, ensure_ascii=False)})
    ws.set("shortcuts", [{"label": nhan, "type": loai, "link_to": dich, "color": "Grey"} for nhan, loai, dich in loi_vao])
    ws.set("roles", [{"role": r} for r in sorted(VAI_TRO_LAP)])
    ws.flags.ignore_permissions = True
    ws.save() if not ws.is_new() else ws.insert()


# ---------------------------------------------------------------- đề nghị

def _dich(dong):
    if dong.truong not in TRUONG:
        frappe.throw(f"Dòng {dong.idx}: trường \"{dong.truong}\" không được sửa qua đề nghị")
    return TRUONG[dong.truong]


def gia_tri_hien_tai(dong):
    dt, f, _n = _dich(dong)
    if not dong.doi_tuong or not frappe.db.exists(dt, dong.doi_tuong):
        frappe.throw(f"Dòng {dong.idx}: không có {dt} \"{dong.doi_tuong}\"")
    if f == F_HAO_HUT and not frappe.get_meta(dt).has_field(f):
        frappe.throw(f"Dòng {dong.idx}: site chưa có ô tỷ lệ hao hụt trên định mức (cài 0.11.1)")
    return frappe.db.get_value(dt, dong.doi_tuong, f)


def validate(doc, method=None):
    """Kiểm từng dòng: lỗi cấu trúc chặn lưu; cảnh báo ghi cạnh dòng (BA nguyên tắc 1: không chặn cứng số liệu)."""
    _can_bat()
    if doc.is_new() and not _co_vai_tro(VAI_TRO_LAP):
        frappe.throw("Không có quyền lập đề nghị cập nhật số liệu", frappe.PermissionError)
    if not doc.trang_thai:
        doc.trang_thai = "Nháp"
    if doc.trang_thai in ("Đã áp dụng",) and not doc.flags.dang_ap_dung:
        frappe.throw("Đề nghị đã áp dụng, không sửa được")
    if not doc.dong:
        frappe.throw("Thêm ít nhất một dòng")
    for d in doc.dong:
        d.loai_doi_tuong = _dich(d)[0]
        d.doi_tuong = d.mat_hang if d.loai_doi_tuong == "Item" else d.dinh_muc
        if doc.trang_thai == "Nháp":
            hien = gia_tri_hien_tai(d)
            d.gia_tri_hien_tai = "" if hien is None else str(hien)
        kq = D.kiem_gia_tri(d.truong, d.gia_tri_moi, d.so_goi, d.gram_moi_goi)
        if kq and kq[0] == D.LOI:
            frappe.throw(f"Dòng {d.idx} ({d.doi_tuong}): {kq[1]}")
        d.canh_bao = kq[1] if kq else ""
        if d.truong == "dinh_muc_mac_dinh":
            item = frappe.db.get_value("BOM", d.doi_tuong, ["docstatus", "is_active"], as_dict=True)
            if item.docstatus != 1 or not item.is_active:
                frappe.throw(f"Dòng {d.idx}: định mức {d.doi_tuong} phải đã xác nhận và đang dùng mới đặt làm mặc định")


def _lay(name):
    _can_bat()
    doc = frappe.get_doc(DT, name)
    doc.check_permission("read")
    return doc


@frappe.whitelist(methods=["POST"])
def gui(name):
    doc = _lay(name)
    if doc.trang_thai not in ("Nháp", "Trả lại"):
        frappe.throw(f"Đề nghị đang ở trạng thái {doc.trang_thai}")
    if not _co_vai_tro(VAI_TRO_LAP):
        frappe.throw("Không có quyền gửi đề nghị", frappe.PermissionError)
    doc.trang_thai = "Nháp"
    doc.save()  # chạy lại kiểm và giá trị hiện tại
    doc.db_set({"trang_thai": "Chờ duyệt", "nguoi_gui": frappe.session.user, "ly_do_tra": None})
    doc.add_comment("Comment", f"Gửi duyệt bởi {frappe.session.user}")
    return {"trang_thai": "Chờ duyệt"}


@frappe.whitelist(methods=["POST"])
def tra_lai(name, ly_do):
    doc = _lay(name)
    if not co_quyen_duyet():
        frappe.throw("Chỉ kế toán trưởng được trả lại đề nghị", frappe.PermissionError)
    if doc.trang_thai != "Chờ duyệt":
        frappe.throw("Chỉ trả lại đề nghị đang chờ duyệt")
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do trả lại")
    doc.db_set({"trang_thai": "Trả lại", "ly_do_tra": ly_do.strip(), "nguoi_duyet": frappe.session.user})
    doc.add_comment("Comment", f"Trả lại bởi {frappe.session.user}. Lý do: {ly_do.strip()}")
    return {"trang_thai": "Trả lại"}


@frappe.whitelist(methods=["POST"])
def duyet(name):
    """Duyệt và áp dụng từng dòng. Một dòng lỗi thì không dòng nào được ghi (cả yêu cầu chạy trong một giao dịch)."""
    doc = _lay(name)
    if not co_quyen_duyet():
        frappe.throw("Chỉ kế toán trưởng được duyệt đề nghị", frappe.PermissionError)
    if doc.trang_thai != "Chờ duyệt":
        frappe.throw("Chỉ duyệt đề nghị đang chờ duyệt")
    nhat_ky = []
    for d in doc.dong:
        hien = gia_tri_hien_tai(d)
        if str("" if hien is None else hien) != (d.gia_tri_hien_tai or "") and d.truong != "dinh_muc_mac_dinh":
            frappe.throw(f"Dòng {d.idx}: {d.doi_tuong} đã đổi từ lúc lập đề nghị "
                         f"({d.gia_tri_hien_tai} → {hien}); trả lại để lập lại")
    # Mọi thay đổi của cùng một định mức gộp vào MỘT bản mới (không tách thành nhiều bản).
    theo_bom = {}
    for d in doc.dong:
        if TRUONG[d.truong][0] == "BOM" and d.truong != "dinh_muc_mac_dinh":
            theo_bom.setdefault(d.doi_tuong, []).append(d)
    for ten_bom, cac_dong in theo_bom.items():
        moi = _ap_dung_bom(ten_bom, cac_dong, doc.name)
        for d in cac_dong:
            d.ket_qua = moi
    for d in doc.dong:
        if d.truong == "kg_tinh":
            d.ket_qua = _ap_dung_item(d)
        elif d.truong == "dinh_muc_mac_dinh":
            d.ket_qua = _dat_mac_dinh(d)
        nhat_ky.append(f"{d.doi_tuong} · {TRUONG[d.truong][2]}: {d.gia_tri_hien_tai} → {d.gia_tri_moi} ({d.ket_qua})")
    doc.flags.dang_ap_dung = True
    doc.trang_thai = "Đã áp dụng"
    doc.nguoi_duyet = frappe.session.user
    doc.luc_duyet = now_datetime()
    doc.save(ignore_permissions=True)
    doc.add_comment("Comment", "Duyệt và áp dụng:<br>" + "<br>".join(frappe.utils.escape_html(x) for x in nhat_ky))
    return {"trang_thai": "Đã áp dụng", "ket_qua": [d.ket_qua for d in doc.dong]}


def _ap_dung_item(d):
    _dt, f, nhan = TRUONG[d.truong]
    item = frappe.get_doc("Item", d.doi_tuong)
    cu = item.get(f)
    item.set(f, flt(d.gia_tri_moi))
    if f == "weight_per_unit" and not item.weight_uom:
        item.weight_uom = "Kg"
    item.flags.ignore_permissions = True
    item.save()
    item.add_comment("Comment", f"{nhan}: {cu} → {d.gia_tri_moi} theo đề nghị {d.parent}")
    return item.name


def _dat_mac_dinh(d):
    bom = frappe.get_doc("BOM", d.doi_tuong)
    frappe.db.set_value("BOM", bom.name, "is_default", 1)
    bom.reload()
    bom.manage_default_bom()  # bỏ mặc định của định mức khác cùng mã, cập nhật Item.default_bom
    bom.add_comment("Comment", f"Đặt làm định mức mặc định theo đề nghị {d.parent}")
    return bom.name


def _ap_dung_bom(ten_bom, cac_dong, de_nghi):
    bom = frappe.get_doc("BOM", ten_bom)
    mo_ta = "; ".join(f"{TRUONG[d.truong][2]} {d.gia_tri_hien_tai} → {d.gia_tri_moi}" for d in cac_dong)
    if bom.docstatus == 0:
        for d in cac_dong:
            bom.set(TRUONG[d.truong][1], flt(d.gia_tri_moi))
        bom.flags.ignore_permissions = True
        bom.save()
        bom.add_comment("Comment", f"{mo_ta} theo đề nghị {de_nghi}")
        return bom.name
    moi = frappe.copy_doc(bom)
    for d in cac_dong:
        moi.set(TRUONG[d.truong][1], flt(d.gia_tri_moi))
    moi.is_default = cint(bom.is_default)
    moi.flags.ignore_permissions = True
    moi.insert()
    moi.submit()
    moi.add_comment("Comment", f"Tạo từ {bom.name} theo đề nghị {de_nghi}: {mo_ta}")
    bom.add_comment("Comment", f"Bản mới {moi.name} thay thế theo đề nghị {de_nghi}; bản này giữ nguyên")
    return moi.name


def has_permission(doc, ptype=None, user=None):
    """Frappe 16: chỉ trả True (không ý kiến) hoặc False (chặn)."""
    if not enabled():
        return False
    return True


# ---------------------------------------------------------------- rà soát (mở rộng báo cáo Du lieu can ra soat)

def ra_soat(company=None):
    """Các dòng nhóm "Danh mục" (0.12.0) cho báo cáo Du lieu can ra soat. Rỗng khi cờ tắt."""
    if not enabled():
        return []
    out = []
    for dt in ("Customer", "Supplier"):
        cot_mst = "tax_id"
        dong = [(r.name, "", r.get(cot_mst)) for r in frappe.get_all(dt, {"disabled": 0}, ["name", cot_mst])]
        for ma in [r for r in dong if D.kiem_mst(r[2])]:
            out.append({"ma": "g", "loai": dt, "ten": ma[0], "gia_tri": None, "mo_ta": D.kiem_mst(ma[2])})
        for _c, mst, tens in D.nhom_trung_mst(dong):
            for t in tens:
                out.append({"ma": "g", "loai": dt, "ten": t, "gia_tri": len(tens),
                            "mo_ta": f"Trùng MST {mst} với: " + ", ".join(x for x in tens if x != t)})
    co ={"company": company} if company else {}
    for r in frappe.db.sql("""SELECT DISTINCT i.name FROM `tabItem` i JOIN `tabUOM Conversion Detail` u ON u.parent=i.name
            WHERE i.disabled=0 AND i.is_stock_item=1 AND u.uom!=i.stock_uom AND i.stock_uom!='Kg'
              AND IFNULL(i.weight_per_unit,0)=0""", as_dict=True):
        out.append({"ma": "h", "loai": "Item", "ten": r.name, "gia_tri": None,
                    "mo_ta": "Bán theo thùng/gói nhưng chưa có kg tịnh mỗi đơn vị"})
    kho = frappe.get_all("Warehouse", {"is_group": 0, **co}, pluck="name")
    for b in frappe.get_all("Bin", {"warehouse": ["in", kho or [""]], "actual_qty": [">", 0],
                                    "valuation_rate": ["<=", 0]}, ["item_code", "warehouse", "actual_qty"]):
        out.append({"ma": "h", "loai": "Item", "ten": b.item_code, "gia_tri": flt(b.actual_qty),
                    "mo_ta": f"{b.warehouse}: còn tồn nhưng giá vốn bằng 0"})
    for r in frappe.db.sql("""SELECT item, COUNT(*) n FROM `tabBOM` WHERE docstatus=1 AND is_active=1 AND is_default=1
            {co} GROUP BY item HAVING n>1""".format(co="AND company=%(c)s" if company else ""), {"c": company}, as_dict=True):
        out.append({"ma": "i", "loai": "Item", "ten": r.item, "gia_tri": r.n, "mo_ta": "Nhiều hơn một định mức mặc định"})
    for r in frappe.db.sql("""SELECT DISTINCT wo.production_item FROM `tabWork Order` wo WHERE wo.docstatus=1 {co}
            AND NOT EXISTS (SELECT 1 FROM `tabBOM` b WHERE b.item=wo.production_item AND b.is_default=1 AND b.docstatus=1)""".format(
            co="AND wo.company=%(c)s" if company else ""), {"c": company}, as_dict=True):
        out.append({"ma": "i", "loai": "Item", "ten": r.production_item, "gia_tri": None,
                    "mo_ta": "Đã có lệnh sản xuất nhưng chưa có định mức mặc định"})
    out += _lech_san_luong(company)
    return out


def _lech_san_luong(company):
    """Sản lượng bình quân mỗi phiếu sản xuất 30 ngày gần nhất lệch định mức quá 20%."""
    out = []
    for r in frappe.db.sql("""SELECT se.bom_no, AVG(se.fg_completed_qty) tb, b.quantity dm, b.item
            FROM `tabStock Entry` se JOIN `tabBOM` b ON b.name=se.bom_no
            WHERE se.docstatus=1 AND se.purpose='Manufacture' AND se.posting_date>=DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            {co} GROUP BY se.bom_no, b.quantity, b.item""".format(co="AND se.company=%(c)s" if company else ""),
                           {"c": company}, as_dict=True):
        if D.lech_san_luong(r.dm, r.tb):
            out.append({"ma": "i", "loai": "BOM", "ten": r.bom_no, "gia_tri": flt(r.tb),
                        "mo_ta": f"{r.item}: sản lượng thực tế bình quân {flt(r.tb):g} lệch định mức {flt(r.dm):g} quá 20%"})
    return out
