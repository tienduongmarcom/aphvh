"""Bán hàng – giao nhận – in (0.11.1, cờ `kh_aph_sales_adjust`, mặc định tắt). Đặc tả docs/dac-ta-0.11.1.md mục 3.9–3.12.

- R011/R084: cảnh báo "dưới giá vốn" chỉ cho người được xem giá vốn (kế toán, Admin); người khác không nhận bất kỳ thông tin
  nào về giá vốn. Cảnh báo "thấp hơn bảng giá" (sales_warnings) giữ nguyên cho mọi người.
- R016/R022/R024: chứng từ trả lại/giảm có loại điều chỉnh; "Xe quay về", "Chuyển sang khách khác" tạo chứng từ NHÁP.
  Ghi nợ lúc shipper nhận giữ nguyên (delivery_receivable); phiếu trả lại tự sinh hóa đơn giảm như cũ.
- Q175/Q176: mã khách KH-.#####. Q181/Q182: kế toán đóng phần chưa giao của đơn chung (Sales Order Closed chuẩn).
- Q192/Q198/R053/Q199: biên bản giao nhận mặc định không giá; in giá khi tích "In kèm giá" và người in được xem giá bán;
  cột lượng thực nhận khi có phiếu trả lại loại giao thiếu; số lượng in "bao + kg" hoặc ĐVT bán kèm quy đổi.
"""
import frappe
from frappe.utils import cint, flt, now_datetime

from kh_aph import sales_adjust_rules as R

FLAG = "kh_aph_sales_adjust"
F_LOAI = "kh_aph_loai_dieu_chinh"
F_IN_GIA = "kh_aph_in_gia"
VAI_TRO_XEM_GIA_VON = {"Accounts User", "Accounts Manager", "System Manager"}
VAI_TRO_DONG_DON = {"Accounts User", "Accounts Manager", "Sales Manager", "System Manager"}


def enabled():
    return cint(frappe.conf.get(FLAG))


def schema():
    """Gọi từ uat_candidate_setup.schema. Không gắn after_install/after_migrate."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_sales_adjust trước khi cài")
    loai = {"fieldname": F_LOAI, "label": "Loại điều chỉnh (trả lại / giảm)", "fieldtype": "Select",
            "options": "\n".join(R.LOAI_DIEU_CHINH), "default": R.DC_TRA_HANG, "insert_after": "is_return",
            "depends_on": "eval:doc.is_return", "no_copy": 0,
            "description": "R024: giao thiếu xử lý bằng chứng từ điều chỉnh hợp lệ; không tạo trả hàng giả do lỗi nhập liệu."}
    create_custom_fields({
        "Delivery Note": [loai, {"fieldname": F_IN_GIA, "label": "In kèm giá trên biên bản giao nhận", "fieldtype": "Check",
                                 "insert_after": F_LOAI, "allow_on_submit": 1, "no_copy": 1,
                                 "description": "Q192: mặc định in không giá."}],
        "Sales Invoice": [loai],
        "APH Shared Sales Order": [
            {"fieldname": "kh_aph_dong_boi", "label": "Người đóng phần chưa giao", "fieldtype": "Link", "options": "User",
             "insert_after": "net_total", "read_only": 1, "allow_on_submit": 1, "no_copy": 1},
            {"fieldname": "kh_aph_dong_luc", "label": "Thời điểm đóng phần chưa giao", "fieldtype": "Datetime",
             "insert_after": "kh_aph_dong_boi", "read_only": 1, "allow_on_submit": 1, "no_copy": 1},
            {"fieldname": "kh_aph_ly_do_dong", "label": "Lý do đóng phần chưa giao", "fieldtype": "Small Text",
             "insert_after": "kh_aph_dong_luc", "read_only": 1, "allow_on_submit": 1, "no_copy": 1}],
    })
    # Q181/Q182: kế toán bán hàng xem đơn chung để đóng phần chưa giao (chuẩn chỉ cấp cho bán hàng).
    from frappe.permissions import add_permission, update_permission_property
    for role in ("Accounts User", "Accounts Manager"):
        if not frappe.db.exists("Custom DocPerm", {"parent": "APH Shared Sales Order", "role": role, "permlevel": 0}):
            add_permission("APH Shared Sales Order", role, 0)
        for p in ("read", "print"):
            update_permission_property("APH Shared Sales Order", role, 0, p, 1, validate=False)
    # Q176: mã khách do hệ thống cấp KH-00001…; không giữ mã MISA cũ.
    if frappe.db.get_single_value("Selling Settings", "cust_master_name") != "Naming Series":
        ss = frappe.get_single("Selling Settings")
        ss.cust_master_name = "Naming Series"
        ss.save(ignore_permissions=True)  # on_update đặt mặc định toàn hệ thống mà Customer.autoname đọc
    make_property_setter("Customer", "naming_series", "options", "KH-.#####", "Text", validate_fields_for_doctype=False)
    make_property_setter("Customer", "naming_series", "default", "KH-.#####", "Text", validate_fields_for_doctype=False)
    return {"cust_master_name": "Naming Series"}


# ---------------------------------------------------------------- R011/R084

def duoc_xem_gia_von(user=None):
    from kh_aph.constants import ROLE_NO_COST
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    roles = set(frappe.get_roles(user))
    return bool(roles & VAI_TRO_XEM_GIA_VON) and ROLE_NO_COST not in roles


def canh_bao_gia_von(doc, method=None):
    if not enabled() or not duoc_xem_gia_von():
        return  # người không được xem giá vốn: không trả bất kỳ thông tin nào
    dong = []
    for d in doc.get("items") or []:
        if not d.get("warehouse") or not d.get("item_code"):
            continue
        von = flt(frappe.db.get_value("Bin", {"item_code": d.item_code, "warehouse": d.warehouse}, "valuation_rate"))
        gia = flt(d.rate) / (flt(d.get("conversion_factor")) or 1)
        dong.append((d.idx, d.item_code, gia, von))
    loi = R.canh_bao_gia_von(dong)
    if loi:
        frappe.msgprint("<br>".join(loi), title="Bán dưới giá vốn (chỉ kế toán thấy)", indicator="orange")


# ---------------------------------------------------------------- R022/R024

def validate_dieu_chinh(doc, method=None):
    if not enabled():
        return
    dn = None
    if doc.doctype == "Sales Invoice" and cint(doc.is_return):
        # Hóa đơn giảm tự sinh từ phiếu giao trả lại: kho đã nhập qua phiếu đó; mang theo loại của phiếu.
        dn = next((d.delivery_note for d in doc.items if d.get("delivery_note")), None)
        if dn and not cint(frappe.db.get_value("Delivery Note", dn, "is_return")):
            dn = None
        if dn and not doc.get(F_LOAI):
            doc.set(F_LOAI, frappe.db.get_value("Delivery Note", dn, F_LOAI))
    loi = R.kiem_dieu_chinh(doc.doctype, cint(doc.is_return), cint(doc.get("update_stock")), doc.get(F_LOAI),
                            theo_phieu_tra=bool(dn))
    if loi:
        frappe.throw(loi, title="Điều chỉnh giao hàng")
    if not cint(doc.is_return) and doc.get(F_LOAI):
        doc.set(F_LOAI, None)


def _phieu_tra_nhap(dn_name):
    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_return
    dn = frappe.get_doc("Delivery Note", dn_name)
    dn.check_permission("read")
    if dn.docstatus != 1 or cint(dn.is_return):
        frappe.throw("Chỉ dùng cho phiếu giao đã xuất kho")
    from kh_aph.delivery_status import STATE, TRANSIT
    if dn.meta.has_field(STATE) and dn.get(STATE) not in (None, "", TRANSIT):
        frappe.throw("Chỉ dùng khi phiếu đang ở trạng thái Đang giao")
    ret = make_sales_return(dn.name)
    ret.set(F_LOAI, R.DC_CHO_VE)
    ret.insert()  # quyền tạo phiếu giao chuẩn
    return dn, ret


@frappe.whitelist(methods=["POST"])
def xe_quay_ve(delivery_note):
    """R022: phiếu trả lại NHÁP theo toàn bộ lượng đã xuất; người dùng sửa thành lượng thực chở về rồi ghi sổ."""
    if not enabled():
        frappe.throw("Tính năng điều chỉnh giao hàng chưa được bật")
    _dn, ret = _phieu_tra_nhap(delivery_note)
    return {"phieu_tra": ret.name}


@frappe.whitelist(methods=["POST"])
def chuyen_khach(delivery_note, sales_order):
    """R022: hàng trên xe chuyển cho khách khác — phiếu trả lại NHÁP + phiếu giao NHÁP từ đơn của khách mới."""
    if not enabled():
        frappe.throw("Tính năng điều chỉnh giao hàng chưa được bật")
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
    so = frappe.get_doc("Sales Order", sales_order)
    so.check_permission("read")
    dn = frappe.get_doc("Delivery Note", delivery_note)
    if so.docstatus != 1 or so.company != dn.company or so.customer == dn.customer:
        frappe.throw("Chọn đơn đã xác nhận của khách khác, cùng đơn vị bán")
    _dn, ret = _phieu_tra_nhap(delivery_note)
    moi = make_delivery_note(so.name)
    moi.insert()
    return {"phieu_tra": ret.name, "phieu_giao_moi": moi.name}


# ---------------------------------------------------------------- Q181/Q182

@frappe.whitelist(methods=["POST"])
def dong_phan_chua_giao(shared_order, ly_do):
    if not enabled():
        frappe.throw("Tính năng chưa được bật")
    if frappe.session.user != "Administrator" and not set(frappe.get_roles()) & VAI_TRO_DONG_DON:
        frappe.throw("Cần quyền kế toán bán hàng", frappe.PermissionError)
    if not (ly_do or "").strip():
        frappe.throw("Ghi lý do đóng phần chưa giao")
    frappe.db.sql("SELECT name FROM `tabAPH Shared Sales Order` WHERE name=%s FOR UPDATE", shared_order)
    doc = frappe.get_doc("APH Shared Sales Order", shared_order)
    doc.check_permission("read")
    if doc.docstatus != 1:
        frappe.throw("Đơn chung chưa xác nhận")
    dong = []
    for name in frappe.get_all("Sales Order", {"kh_aph_shared_order": doc.name, "docstatus": 1}, pluck="name"):
        so = frappe.get_doc("Sales Order", name)
        if so.status in ("Closed", "Completed", "Cancelled"):
            continue
        so.update_status("Closed")  # chuẩn ERPNext: giữ phần đã giao, công nợ, cọc; giải phóng lượng đặt giữ
        dong.append(name)
    doc.db_set({"kh_aph_dong_boi": frappe.session.user, "kh_aph_dong_luc": now_datetime(), "kh_aph_ly_do_dong": ly_do})
    return {"don_da_dong": dong}


# ---------------------------------------------------------------- in (jinja)

def kh_aph_bbgn_an_gia(doc):
    """Biên bản giao nhận: ẩn giá? Cờ tắt: như cũ (chỉ ẩn với người bị ẩn giá). Cờ bật: mặc định ẩn, tích In kèm giá mới in."""
    if not enabled():
        return False  # như cũ: cột giá vẫn in, before_print xóa giá với người bị ẩn giá
    from kh_aph.price_visibility import is_price_restricted
    return is_price_restricted() or not cint(doc.get(F_IN_GIA))


def kh_aph_sl_hien_thi(row):
    if not enabled():
        return None
    return R.hien_thi_sl(row.get("qty"), row.get("uom"), row.get("stock_qty"), row.get("stock_uom"), row.get("kh_aph_bags"))


def kh_aph_thuc_nhan(doc):
    """{dòng phiếu giao: lượng thực nhận} khi có phiếu trả lại loại giao thiếu đã ghi sổ; rỗng nếu không có."""
    if not enabled() or cint(doc.get("is_return")) or doc.docstatus != 1:
        return {}
    rows = frappe.db.sql("""SELECT i.dn_detail, SUM(i.qty) AS qty FROM `tabDelivery Note Item` i
        JOIN `tabDelivery Note` d ON d.name=i.parent
        WHERE d.return_against=%s AND d.docstatus=1 AND d.is_return=1 AND d.kh_aph_loai_dieu_chinh IN %s
        GROUP BY i.dn_detail""", (doc.name, R.GIAO_THIEU), as_dict=True)
    tra = {r.dn_detail: flt(r.qty) for r in rows}
    if not tra:
        return {}
    return {d.name: flt(d.qty) + tra.get(d.name, 0) for d in doc.items}  # qty trả lại là số âm
