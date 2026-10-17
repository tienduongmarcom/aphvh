"""Trung tâm Bán hàng (lượt 0.14, cờ `kh_aph_trung_tam_ban`, mặc định tắt). Đặc tả docs/dac-ta-0.14.md mục 2.

- Workspace "Trung tâm Bán hàng": gom lối vào các việc đã có từ 0.10–0.13 (không làm báo cáo trùng).
- Giá sàn trên đơn chung nhiều công ty (dùng bảng giá sàn / người duyệt của 0.13, kh_aph.ban_quay; cần cả cờ kh_aph_gia_san):
  kiểm theo đơn vị của từng dòng; người duyệt phải có quyền ở mọi đơn vị có dòng dưới sàn; đơn con sinh ra mang theo duyệt.
- In lại phiếu xuất kho (Q197): thêm dòng "Hóa đơn số …" lấy từ hồ sơ hóa đơn MISA (0.11.3) và dấu "In lại lần n";
  bản gốc giữ nguyên (lượng thực nhận Q198 đã có ở mẫu biên bản giao nhận 0.11.1).
"""
import json

import frappe
from frappe.utils import cint, flt
from lab9x import van_hanh as V

FLAG = "kh_aph_trung_tam_ban"
WORKSPACE = "Trung tâm Bán hàng"
DT_CHUNG = "APH Shared Sales Order"
F_LAN_IN = "kh_aph_so_lan_in"
VAI_TRO_BAN = {"Kế toán bán hàng", "Sales User", "Sales Manager", "Accounts User", "Accounts Manager", "System Manager"}


def enabled():
    return cint(frappe.conf.get(FLAG))


def _can_bat():
    if not enabled():
        frappe.throw("Trung tâm Bán hàng 0.14 chưa được bật")


def _fields():
    from kh_aph.ban_quay import _duyet_fields
    return {
        DT_CHUNG: _duyet_fields("customer"),
        "Delivery Note": [
            {"fieldname": F_LAN_IN, "label": "Số lần in lại", "fieldtype": "Int", "insert_after": "kh_aph_delivery_at",
             "read_only": 1, "no_copy": 1, "allow_on_submit": 1}],
    }


def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_trung_tam_ban trước khi cài")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    f = _fields()
    create_custom_fields(f)
    from kh_aph import ban_nhanh
    ban_nhanh.schema()
    _workspace()
    return {"fields": sum(len(v) for v in f.values()), "workspace": WORKSPACE}


def _workspace():
    cho_duyet = {"docstatus": 0, "kh_aph_duoi_san": 1, "kh_aph_duyet_san_boi": ["is", "not set"]}
    loi_vao = [
        ("Đơn bán", "DocType", "Sales Order", {"docstatus": 0}),
        ("Đơn chung nhiều công ty", "DocType", DT_CHUNG, {"docstatus": 0}),
        ("Đơn chờ duyệt dưới giá sàn", "DocType", "Sales Order", cho_duyet),
        ("Đơn chung chờ duyệt dưới giá sàn", "DocType", DT_CHUNG, cho_duyet),
        ("Phiếu giao chờ xuất", "DocType", "Delivery Note", {"docstatus": 0}),
        ("Phiếu giao đang giao", "DocType", "Delivery Note", {"docstatus": 1, "kh_aph_delivery_state": "Đang giao"}),
        ("Hóa đơn còn nợ", "DocType", "Sales Invoice", {"docstatus": 1, "outstanding_amount": [">", 0]}),
        ("Hóa đơn quá hạn", "DocType", "Sales Invoice", {"docstatus": 1, "status": "Overdue"}),
        ("Thu tiền", "DocType", "Payment Entry", {"docstatus": 0, "payment_type": "Receive"}),
        ("Khách cần gọi hôm nay", "Report", "Khach can goi hom nay", None),
        ("Khách chưa xác nhận công nợ", "Report", "Khach chua xac nhan cong no", None),
        ("Đơn quá hạn giao", "Report", "Don qua han giao", None),
        ("Hóa đơn chờ xuất MISA", "Report", "Hoa don cho xuat", None),
        ("Tổng hợp bán hàng theo khách", "Report", "Tong hop ban hang theo khach", None),
        ("Khách hàng", "DocType", "Customer", None),
        ("Giá sàn", "DocType", "APH Gia san", None),
    ]
    loi_vao = [x for x in loi_vao if frappe.db.exists(x[1], x[2])
               and (not x[3] or x[1] != "DocType" or all(frappe.get_meta(x[2]).has_field(k) or k == "docstatus" for k in x[3]))]
    noi_dung = [{"id": "tb-tieu-de", "type": "header", "data": {"text": f"<span class=\"h4\"><b>{WORKSPACE}</b></span>", "col": 12}}]
    noi_dung += [{"id": f"tb-{i}", "type": "shortcut", "data": {"shortcut_name": x[0], "col": 3}} for i, x in enumerate(loi_vao)]
    ws = frappe.get_doc("Workspace", WORKSPACE) if frappe.db.exists("Workspace", WORKSPACE) else frappe.new_doc("Workspace")
    ws.update({"label": WORKSPACE, "title": WORKSPACE, "public": 1, "module": "Kh Aph", "icon": "sell",
               "content": json.dumps(noi_dung, ensure_ascii=False)})
    ws.set("shortcuts", [{"label": nhan, "type": loai, "link_to": dich, "color": "Grey",
                          **({"stats_filter": json.dumps(loc, ensure_ascii=False), "format": "{} " + nhan.lower()} if loc else {})}
                         for nhan, loai, dich, loc in loi_vao])
    ws.set("roles", [{"role": r} for r in sorted(VAI_TRO_BAN) if frappe.db.exists("Role", r)])
    ws.flags.ignore_permissions = True
    ws.save() if not ws.is_new() else ws.insert()


# ---------------------------------------------------------------- giá sàn trên đơn chung

def _gia_san_bat():
    from kh_aph import ban_quay
    return enabled() and ban_quay.enabled()


def dong_duoi_san_chung(doc):
    """[(idx, item, % dưới sàn, đơn vị)] — giá sàn theo đơn vị (chủ kho) của từng dòng."""
    from kh_aph.ban_quay import gia_san
    out = []
    for d in doc.get("items") or []:
        if not d.get("item_code") or not d.get("company"):
            continue
        pt = V.phan_tram_duoi_san(flt(d.rate), gia_san(d.company, d.item_code))
        if pt > 0:
            out.append((d.idx, d.item_code, pt, d.company))
    return out


def _muc_theo_cong_ty(dong):
    muc = {}
    for _i, _m, p, c in dong:
        muc[c] = max(muc.get(c, 0), p)
    return muc


def validate_chung(doc, method=None):
    """APH Shared Sales Order validate (sau khi controller gán đơn vị từng dòng)."""
    from kh_aph.ban_quay import F_BOI, F_DUOI, F_LY_DO, F_MUC
    if not _gia_san_bat() or not doc.meta.has_field(F_DUOI):
        return
    dong = dong_duoi_san_chung(doc)
    doc.set(F_DUOI, 1 if dong else 0)
    muc = max((p for _i, _m, p, _c in dong), default=0)
    if doc.get(F_BOI) and (not dong or muc > flt(doc.get(F_MUC)) + 1e-6):
        doc.set(F_BOI, None)
        doc.set(F_MUC, 0)
        doc.set(F_LY_DO, None)


def before_submit_chung(doc, method=None):
    from kh_aph.ban_quay import F_BOI, F_DUOI
    if not _gia_san_bat() or not doc.meta.has_field(F_DUOI):
        return
    dong = dong_duoi_san_chung(doc)
    if dong and not doc.get(F_BOI):
        frappe.throw("Dòng " + ", ".join(str(i) for i, *_x in dong) + " dưới giá sàn, cần người có quyền duyệt "
                     "(bấm \"Duyệt giá dưới sàn\").", title="Giá dưới sàn")


def on_submit_chung(doc, method=None):
    """Đơn con sinh từ đơn chung mang theo dấu duyệt (để tra cứu); đơn con không kiểm lại giá sàn."""
    from kh_aph.ban_quay import F_BOI, F_DUOI, F_LY_DO, F_MUC
    if not _gia_san_bat() or not doc.get(F_BOI) or not frappe.get_meta("Sales Order").has_field(F_BOI):
        return
    for so in frappe.get_all("Sales Order", {"kh_aph_shared_order": doc.name}, pluck="name"):
        frappe.db.set_value("Sales Order", so, {F_DUOI: 1, F_BOI: doc.get(F_BOI), F_MUC: doc.get(F_MUC),
                                                 F_LY_DO: doc.get(F_LY_DO)}, update_modified=False)


def _quyen_tat_ca(user, owner, muc_cty, bang):
    for cty, muc in muc_cty.items():
        duoc, ly = V.quyen_duyet(user, owner, cty, muc, bang)
        if not duoc:
            return False, f"{cty}: {ly}"
    return True, ""


@frappe.whitelist()
def xem_duoi_san_chung(name):
    _can_bat()
    from kh_aph.ban_quay import _bang_duyet
    doc = frappe.get_doc(DT_CHUNG, name)
    doc.check_permission("read")
    dong = dong_duoi_san_chung(doc)
    duoc, _ly = _quyen_tat_ca(frappe.session.user, doc.owner, _muc_theo_cong_ty(dong), _bang_duyet())
    if frappe.session.user == "Administrator" or duoc:
        return {"duoc_duyet": True, "dong": [{"idx": i, "item_code": m, "phan_tram": p, "company": c} for i, m, p, c in dong]}
    return {"duoc_duyet": False, "dong": [{"idx": i, "item_code": m} for i, m, _p, _c in dong]}


@frappe.whitelist(methods=["POST"])
def duyet_don_chung(name, ly_do):
    _can_bat()
    from kh_aph.ban_quay import F_BOI, F_DUOI, F_LY_DO, F_MUC, _bang_duyet
    if not _gia_san_bat():
        frappe.throw("Cần bật giá sàn 0.13 (kh_aph_gia_san)")
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do duyệt giá dưới sàn")
    doc = frappe.get_doc(DT_CHUNG, name)
    doc.check_permission("read")
    if doc.docstatus != 0:
        frappe.throw("Chỉ duyệt đơn chung đang nháp")
    dong = dong_duoi_san_chung(doc)
    if not dong:
        return {"duyet": False, "ly_do": "Không có dòng dưới giá sàn"}
    muc = max(p for _i, _m, p, _c in dong)
    if frappe.session.user != "Administrator":
        duoc, ly = _quyen_tat_ca(frappe.session.user, doc.owner, _muc_theo_cong_ty(dong), _bang_duyet())
        if not duoc:
            frappe.throw(ly, frappe.PermissionError)
    doc.db_set({F_DUOI: 1, F_BOI: frappe.session.user, F_MUC: muc, F_LY_DO: ly_do.strip()})
    doc.add_comment("Comment", f"Duyệt giá dưới sàn {muc:g}% bởi {frappe.session.user}. Lý do: {ly_do.strip()}")
    return {"duyet": True, "muc": muc}


# ---------------------------------------------------------------- in lại phiếu xuất kho (Q197)

def so_hoa_don_misa(doc):
    """['ký hiệu … số … ngày …'] của hóa đơn MISA trên các hóa đơn bán lập từ phiếu giao (ô số hóa đơn trên Sales Invoice do hồ sơ
    hóa đơn MISA 0.11.3 cập nhật, kể cả thay thế / hủy). Cờ tắt hoặc chưa có số: []."""
    from kh_aph.constants import SI_EINV_DATE, SI_EINV_NO, SI_EINV_SERIES
    if not enabled() or doc.doctype != "Delivery Note" or not doc.name or not frappe.get_meta("Sales Invoice").has_field(SI_EINV_NO):
        return []
    ngay = SI_EINV_DATE if frappe.get_meta("Sales Invoice").has_field(SI_EINV_DATE) else "posting_date"
    rows = frappe.db.sql(f"""SELECT DISTINCT si.{SI_EINV_SERIES} AS ky_hieu, si.{SI_EINV_NO} AS so, si.{ngay} AS ngay
        FROM `tabSales Invoice` si JOIN `tabSales Invoice Item` i ON i.parent=si.name
        WHERE i.delivery_note=%s AND si.docstatus=1 AND IFNULL(si.{SI_EINV_NO}, '')!='' ORDER BY si.{SI_EINV_NO}""",
                         doc.name, as_dict=True)
    from frappe.utils import formatdate
    return [" ".join(x for x in (f"ký hiệu {r.ky_hieu}" if r.ky_hieu else "", f"số {r.so}",
                                 f"ngày {formatdate(r.ngay, 'dd/MM/yyyy')}" if r.ngay else "") if x) for r in rows]


@frappe.whitelist(methods=["POST"])
def in_lai(delivery_note):
    """Bản in lại phiếu xuất kho: ghi "In lại lần n" và số hóa đơn MISA; tăng bộ đếm, ghi chú vết. Bản gốc không đổi."""
    _can_bat()
    from kh_aph.ban_quay import MAU_PHIEU_GIAO
    doc = frappe.get_doc("Delivery Note", delivery_note)
    doc.check_permission("print")
    if doc.docstatus != 1:
        frappe.throw("Chỉ in lại phiếu giao đã xuất")
    n = cint(doc.get(F_LAN_IN)) + 1
    doc.db_set(F_LAN_IN, n, update_modified=False)
    doc.add_comment("Comment", f"In lại phiếu xuất kho lần {n}")
    doc.kh_aph_lan_in_lai = n
    mau = MAU_PHIEU_GIAO if frappe.db.exists("Print Format", MAU_PHIEU_GIAO) else None
    return {"lan": n, "html": frappe.get_print("Delivery Note", delivery_note, print_format=mau, doc=doc)}
