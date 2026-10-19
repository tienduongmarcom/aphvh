"""Tiền mặt và chi phí nhỏ tại nhà máy cho Dũng; khóa giá thành phẩm chính (0.11.1, cờ `kh_aph_factory_cash`).

Đặc tả docs/dac-ta-0.11.1.md mục 3.7–3.8 (R046–R048, R085–R087, R090–R091, Q138).
- Phiếu quỹ nhà máy (DocType "APH Phieu quy nha may"): Dũng tạo/xem phiếu của mình (if_owner); server lập Journal Entry, Dũng
  không cần và không có quyền Journal Entry/GL. Thu tiền khách: Nợ quỹ nhà máy / Có 131 theo khách (không cấn hóa đơn —
  quyết định 5). Chi phí nhỏ: Nợ tài khoản của khoản mục / Có quỹ (gộp nhiều dòng, không bắt buộc chứng từ). Bàn giao tiền: người
  nhận xác nhận số đếm được mới ghi sổ; chênh lệch "chờ điều tra", không tự quy trách nhiệm.
- Khóa giá: người vận hành nhà máy (vai trò Kế toán nhà máy / APH Không xem giá vốn, không có vai trò kế toán) bán mã thuộc nhóm
  "Thành phẩm chính: giá Hà Nội chốt" phải đúng giá bảng giá; phụ phẩm tự nhập giá.
Phần thuần ở factory_cash_rules.py.
"""
import frappe
from frappe.utils import cint, flt, now_datetime
from kh_aph.cash_transaction import retry_rpc

from kh_aph.factory_cash_rules import (LOAI_BAN_GIAO, LOAI_CHI, LOAI_THU, TT_CHO_NHAN, TT_GHI_SO, TT_HUY,
                                     VAI_TRO_NHA_MAY, bi_khoa_gia, kiem_phieu, trang_thai_nhan, vi_pham_khoa_gia)


FLAG = "kh_aph_factory_cash"
F_QUY = "kh_aph_quy_nha_may"
IG_KHOA_GIA = "kh_aph_khoa_gia_nha_may"
DT = "APH Phieu quy nha may"
DT_KM = "APH Khoan muc chi nha may"
KET_QUA_NHAN = ("trang_thai", "so_thuc_nhan", "nhan_boi", "nhan_luc", "journal_entry")


def enabled():
    return cint(frappe.conf.get(FLAG))


def _can_bat():
    if not enabled():
        frappe.throw("Phiếu quỹ nhà máy chưa được bật")


def schema():
    """Gọi từ uat_candidate_setup.schema. Không gắn after_install/after_migrate."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from frappe.permissions import add_permission, update_permission_property
    _can_bat()
    for slug in ("aph_khoan_muc_chi_nha_may", "aph_dong_phieu_quy_nha_may", "aph_phieu_quy_nha_may"):
        frappe.reload_doc("kh_aph", "doctype", slug)
    create_custom_fields({
        "Company": [{"fieldname": F_QUY, "label": "Quỹ tiền mặt nhà máy (0.11.1)", "fieldtype": "Link",
                     "options": "Account", "insert_after": "default_cash_account",
                     "description": "Tài khoản tiền mặt chi tiết do kế toán mở (ví dụ 11111). Phiếu quỹ nhà máy ghi vào đây."}],
        "Item Group": [{"fieldname": IG_KHOA_GIA, "label": "Thành phẩm chính: giá Hà Nội chốt (R091)", "fieldtype": "Check",
                        "insert_after": "parent_item_group",
                        "description": "Người vận hành nhà máy bán đúng giá bảng giá; phụ phẩm không tích (tự nhập giá)."}],
    })
    for role in VAI_TRO_NHA_MAY:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()
        if not frappe.db.exists("Custom DocPerm", {"parent": DT, "role": role, "permlevel": 0}):
            add_permission(DT, role, 0)
        for p in ("read", "write", "create", "submit", "print", "if_owner"):
            update_permission_property(DT, role, 0, p, 1, validate=False)
        if not frappe.db.exists("Custom DocPerm", {"parent": DT_KM, "role": role, "permlevel": 0}):
            add_permission(DT_KM, role, 0)
    return {"doctype": DT}


def validate_khoan_muc(doc):
    a = frappe.db.get_value("Account", doc.account, ["company", "is_group", "account_type"], as_dict=True)
    if not a or a.company != doc.company or a.is_group or a.account_type in (
            "Stock", "Bank", "Cash", "Receivable", "Payable", "Tax"):
        frappe.throw("Tài khoản chi phí: chi tiết, đúng đơn vị, không phải tài khoản kho/tiền/công nợ/thuế")
    if frappe.db.get_value("Cost Center", doc.cost_center, "company") != doc.company:
        frappe.throw("Trung tâm chi phí khác đơn vị")


def _quy(company):
    tk = frappe.db.get_value("Company", company, F_QUY) if frappe.get_meta("Company").has_field(F_QUY) else None
    if not tk:
        frappe.throw(f"Kế toán chưa đặt Quỹ tiền mặt nhà máy cho {company}")
    return tk


def validate_phieu(doc):
    _can_bat()
    old = doc.get_doc_before_save()
    for field in KET_QUA_NHAN:
        current = doc.get(field)
        previous = old.get(field) if old else None
        if str(current or "") != str(previous or ""):
            frappe.throw("Không sửa trực tiếp kết quả ghi sổ/nhận tiền; dùng thao tác xác nhận nhận tiền")
    loi = kiem_phieu(doc.loai, [(d.dien_giai, d.khoan_muc, d.so_tien) for d in doc.dong], doc.customer, doc.nguoi_nhan)
    if loi:
        frappe.throw("<br>".join(loi), title="Phiếu quỹ nhà máy")
    _quy(doc.company)
    for d in doc.dong:
        if d.khoan_muc:
            km = frappe.db.get_value(DT_KM, d.khoan_muc, ["company", "disabled"], as_dict=True)
            if not km or km.company != doc.company or km.disabled:
                frappe.throw(f"Dòng {d.idx}: khoản mục không thuộc {doc.company} hoặc đã ngừng dùng")
    if doc.loai != LOAI_THU:
        doc.customer = None
    if doc.loai != LOAI_BAN_GIAO:
        doc.nguoi_nhan = None
    else:
        _nguoi_nhan(doc)
    doc.tong_tien = sum(float(d.so_tien or 0) for d in doc.dong)


def _nguoi_nhan(doc):
    """Người nhận độc lập với người lập và người thực giữ, không suy người giữ từ owner."""
    from kh_aph import cash_custody
    if doc.nguoi_nhan in (doc.owner, doc.get(cash_custody.HOLDER)):
        frappe.throw("Người lập/người giữ tiền không được tự nhận bàn giao")
    if cash_custody.enabled():
        cash_custody._person(doc.nguoi_nhan, doc.company)


def _tao_je(doc, dong, ghi_chu):
    from kh_aph import cash_custody
    if cash_custody.enabled():
        holders = {_quy(doc.company): doc.get(cash_custody.HOLDER)}
        if doc.loai == LOAI_BAN_GIAO:
            for row in dong:
                if row.get("debit_in_account_currency"):
                    holders[row["account"]] = doc.nguoi_nhan
        cash_custody.stamp_rows(dong, holders)
    je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Cash Entry", "company": doc.company,
                         "posting_date": doc.posting_date, "user_remark": f"{ghi_chu} — {doc.name}",
                         "cheque_no": doc.name, "cheque_date": doc.posting_date, "accounts": dong})
    # Quyền được kiểm trên phiếu quỹ (if_owner + cờ); người lập phiếu không có quyền Journal Entry.
    je.flags.ignore_permissions = True
    je.insert()
    je.submit()
    return je.name


def ghi_so(doc):
    _can_bat()
    quy = _quy(doc.company)
    if doc.loai == LOAI_BAN_GIAO:
        doc.db_set("trang_thai", TT_CHO_NHAN)
        return
    if doc.loai == LOAI_THU:
        from erpnext.accounts.party import get_party_account
        cong_no = get_party_account("Customer", doc.customer, doc.company)
        dong = [{"account": quy, "debit_in_account_currency": doc.tong_tien},
                {"account": cong_no, "party_type": "Customer", "party": doc.customer,
                 "credit_in_account_currency": doc.tong_tien, "is_advance": "Yes"}]
        ghi_chu = "Thu tiền khách tại nhà máy (chưa cấn hóa đơn)"
    else:
        dong = []
        for d in doc.dong:
            km = frappe.db.get_value(DT_KM, d.khoan_muc, ["account", "cost_center"], as_dict=True)
            dong.append({"account": km.account, "cost_center": km.cost_center, "debit_in_account_currency": d.so_tien,
                         "user_remark": d.dien_giai})
        dong.append({"account": quy, "credit_in_account_currency": doc.tong_tien})
        ghi_chu = "Chi phí nhỏ tại nhà máy"
    doc.db_set({"journal_entry": _tao_je(doc, dong, ghi_chu), "trang_thai": TT_GHI_SO})


def truoc_huy(doc):
    if doc.journal_entry and frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus") == 1:
        je = frappe.get_doc("Journal Entry", doc.journal_entry)
        je.flags.ignore_permissions = True
        je.cancel()
    doc.db_set("trang_thai", TT_HUY)


@frappe.whitelist(methods=["POST"])
@retry_rpc
def xac_nhan_nhan(name, so_thuc_nhan, tai_khoan_nhan):
    """Đúng người nhận đếm và xác nhận; gửi lại cùng kết quả không ghi sổ lần hai."""
    _can_bat()
    frappe.db.sql(f"SELECT name FROM `tab{DT}` WHERE name=%s FOR UPDATE", name)
    doc = frappe.get_doc(DT, name, for_update=True)
    doc.check_permission("read")
    # Người nhận có thể chỉ có quyền đọc phiếu; vẫn phải nằm trong phạm vi
    # Company được cấp. Không đòi quyền đọc GL/Account của hồ sơ nhà máy.
    company_doc = frappe.get_doc("Company", doc.company)
    company_doc.check_permission("read")
    if frappe.session.user != doc.nguoi_nhan:
        frappe.throw("Chỉ đúng người nhận xác nhận; quản lý không nhận thay", frappe.PermissionError)
    _nguoi_nhan(doc)
    if doc.docstatus != 1 or doc.loai != LOAI_BAN_GIAO:
        frappe.throw("Phiếu không ở trạng thái chờ nhận")
    from kh_aph.funds_rules import money
    try:
        so = float(money(so_thuc_nhan))
    except ValueError as exc:
        frappe.throw(str(exc))
    if so <= 0:
        frappe.throw("Số tiền nhận phải lớn hơn 0")
    if doc.trang_thai != TT_CHO_NHAN:
        account = frappe.db.get_value("Journal Entry Account", {
            "parent": doc.journal_entry, "parenttype": "Journal Entry", "debit_in_account_currency": [">", 0]}, "account") if doc.journal_entry else None
        if (doc.nhan_boi == frappe.session.user and doc.journal_entry and account == tai_khoan_nhan
                and float(doc.so_thuc_nhan or 0) == so
                and frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus") == 1):
            return {"name": doc.name, "trang_thai": doc.trang_thai, "so_thuc_nhan": so}
        frappe.throw("Phiếu đã xử lý với kết quả khác; kiểm tra hồ sơ, không nhận lại")
    quy = _quy(doc.company)
    a = frappe.db.get_value("Account", tai_khoan_nhan, ["company", "account_type", "is_group"], as_dict=True)
    if not a or a.company != doc.company or a.is_group or a.account_type not in ("Cash", "Bank") or tai_khoan_nhan == quy:
        frappe.throw("Chọn quỹ/ngân hàng nhận của cùng đơn vị, khác quỹ nhà máy")
    je = _tao_je(doc, [{"account": tai_khoan_nhan, "debit_in_account_currency": so},
                       {"account": quy, "credit_in_account_currency": so}],
                 "Nhận tiền bàn giao từ nhà máy")
    doc.db_set({"so_thuc_nhan": so, "nhan_boi": frappe.session.user, "nhan_luc": now_datetime(),
                "journal_entry": je, "trang_thai": trang_thai_nhan(doc.tong_tien, so)})
    return {"name": doc.name, "trang_thai": doc.trang_thai, "so_thuc_nhan": so}


def validate_khoa_gia(doc, method=None):
    """R091/Q138: chặn ở server, không tin trình duyệt."""
    if not enabled() or frappe.session.user == "Administrator" or not bi_khoa_gia(frappe.get_roles()):
        return
    from kh_aph.factory_costing import nhom_co_co
    bang = doc.get("selling_price_list")
    dong = []
    for d in doc.get("items") or []:
        nhom = frappe.get_cached_value("Item", d.item_code, "item_group")
        khoa = nhom_co_co(nhom, IG_KHOA_GIA)
        gia_bang = None
        if khoa and bang:
            v = frappe.db.get_value("Item Price", {"price_list": bang, "item_code": d.item_code, "selling": 1},
                                    "price_list_rate", order_by="valid_from desc")
            gia_bang = flt(v) if v is not None else None
        dong.append((d.idx, d.item_code, d.rate, gia_bang, khoa))
    loi = vi_pham_khoa_gia(dong)
    if loi:
        frappe.throw("<br>".join(loi), title="Giá thành phẩm chính do Hà Nội chốt")


def protect_submitted(doc):
    """Kết quả nhận/ghi sổ do server cập nhật; không mở đường sửa tay sau submit."""
    frappe.throw("Phiếu quỹ đã gửi không được sửa trực tiếp; dùng xác nhận nhận tiền hoặc hủy theo quyền")
