"""Theo dõi xử lý chênh lệch trên Delivery Note; không tạo chứng từ hoặc ghi sổ."""
from html import escape
import json

import frappe
from frappe.utils import cint, now_datetime
from kh_aph import delivery_issue_rules as R
from kh_aph.ho_so_giao_nhan import FILE, NOTE, ACTOR, TIME, enabled

STATE = "kh_aph_chenh_lech_state"
DETAIL = "kh_aph_chenh_lech_noi_dung"
ASSIGNEE = "kh_aph_chenh_lech_phu_trach"
DUE = "kh_aph_chenh_lech_han"
RESULT = "kh_aph_chenh_lech_ket_qua"
MODE = "kh_aph_chenh_lech_cach_xu_ly"
RETURN = "kh_aph_chenh_lech_phieu_tra"
CREDIT = "kh_aph_chenh_lech_hoa_don_giam"
OPEN_BY = "kh_aph_chenh_lech_bao_boi"
OPEN_AT = "kh_aph_chenh_lech_bao_luc"
CLOSE_BY = "kh_aph_chenh_lech_chot_boi"
CLOSE_AT = "kh_aph_chenh_lech_chot_luc"
FIELDS = (STATE, DETAIL, ASSIGNEE, DUE, RESULT, MODE, RETURN, CREDIT, OPEN_BY, OPEN_AT, CLOSE_BY, CLOSE_AT)
RESOLUTION = (RESULT, MODE, RETURN, CREDIT, CLOSE_BY, CLOSE_AT)
FLAG = "kh_aph_xu_ly_chenh_lech"


def fields():
    specs = [(STATE, "Xử lý chênh lệch giao nhận", "Select", "\n".join(("", R.PENDING, R.ACTIVE, R.CLOSED))),
             (DETAIL, "Nội dung chênh lệch", "Small Text", None),
             (ASSIGNEE, "Người phụ trách xử lý", "Link", "User"), (DUE, "Hạn xử lý chênh lệch", "Date", None),
             (RESULT, "Kết quả xử lý chênh lệch", "Small Text", None),
             (MODE, "Cách xử lý chênh lệch", "Select", "\n".join(("", R.NO_LEDGER, R.RETURN, R.CREDIT))),
             (RETURN, "Phiếu trả hàng đã xử lý", "Link", "Delivery Note"),
             (CREDIT, "Hóa đơn giảm đã xử lý", "Link", "Sales Invoice"),
             (OPEN_BY, "Người báo chênh lệch", "Link", "User"), (OPEN_AT, "Thời điểm báo chênh lệch", "Datetime", None),
             (CLOSE_BY, "Người chốt xử lý chênh lệch", "Link", "User"), (CLOSE_AT, "Thời điểm chốt chênh lệch", "Datetime", None)]
    result, previous = [], TIME
    for name, label, kind, options in specs:
        f = {"fieldname": name, "label": label, "fieldtype": kind, "read_only": 1, "allow_on_submit": 1,
             "no_copy": 1, "insert_after": previous,
             "depends_on": "eval:doc.docstatus==1 && !doc.is_return" + (" && doc." + STATE if name != STATE else "")}
        if options is not None:
            f["options"] = options
        if name == STATE:
            f["in_standard_filter"] = 1
            f["description"] = "Đối chiếu bản ký không tự hoàn tất việc xử lý chênh lệch."
        result.append(f)
        previous = name
    return result


def _snapshot(doc):
    return {f: str(doc.get(f)) if f in (DUE, OPEN_AT, CLOSE_AT) and doc.get(f) is not None else doc.get(f) for f in FIELDS}


def _audit(doc, action, before):
    data = {"truoc": before, "sau": _snapshot(doc)}
    doc.add_comment("Comment", "Chênh lệch giao nhận — " + escape(action) + "<pre>" +
                    escape(json.dumps(data, ensure_ascii=False, default=str, indent=2)) + "</pre>")


def validate(doc, method=None):
    if not enabled() or not doc.meta.has_field(STATE):
        return
    old = doc.get_doc_before_save()
    internal = frappe.flags.get(FLAG) == doc.name
    if not internal and any(str(doc.get(f) or "") != str((old.get(f) if old else None) or "") for f in FIELDS):
        frappe.throw("Dùng thao tác Xử lý chênh lệch; không sửa trực tiếp trạng thái, người hoặc kết quả")
    # Thay hồ sơ đầu vào bắt buộc xem xét lại cả kết quả, độc lập dấu đối chiếu bản ký.
    if old and old.get(STATE) == R.CLOSED and doc.get(STATE) == R.CLOSED and any(
            (doc.get(f) or "") != (old.get(f) or "") for f in (FILE, NOTE)):
        before = _snapshot(old)
        doc.set(STATE, R.ACTIVE if doc.get(ASSIGNEE) else R.PENDING)
        for f in RESOLUTION:
            doc.set(f, None)
        _audit(doc, "Mở lại do thay bản ký hoặc ghi chú", before)


def _chief():
    if frappe.session.user != "Administrator" and "Accounts Manager" not in frappe.get_roles():
        frappe.throw("Kế toán trưởng mới được giao người xử lý, chốt hoặc mở lại chênh lệch", frappe.PermissionError)


def _assignee(doc, user):
    data = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
    if not data or not cint(data.enabled) or data.user_type != "System User" or any(
            not frappe.has_permission("Delivery Note", p, doc=doc, user=user) for p in ("read", "write")):
        frappe.throw("Người phụ trách phải đang hoạt động và có quyền đọc, sửa phiếu giao này")


def _proof(doc, mode, name):
    dt = "Delivery Note" if mode == R.RETURN else "Sales Invoice"
    # Cùng khóa với hủy native: không chốt bằng chứng từ vừa bị hủy đồng thời.
    frappe.db.sql(f"SELECT name FROM `tab{dt}` WHERE name=%s FOR UPDATE", name)
    proof = frappe.get_doc(dt, name)
    proof.check_permission("read")
    if cint(proof.docstatus) != 1 or not cint(proof.is_return) or proof.company != doc.company or proof.customer != doc.customer:
        frappe.throw("Chứng từ xử lý phải đã ghi sổ, là chứng từ trả/giảm, đúng công ty và khách của phiếu")
    if mode == R.RETURN:
        if proof.return_against != doc.name:
            frappe.throw("Phiếu trả hàng phải tham chiếu đúng phiếu giao đang xử lý")
    else:
        if cint(proof.update_stock) or not proof.return_against:
            frappe.throw("Hóa đơn giảm phải giảm hóa đơn gốc, không ghi kho lần nữa")
        original = frappe.get_doc("Sales Invoice", proof.return_against)
        original.check_permission("read")
        sources = {row.get("delivery_note") for row in original.items if row.get("delivery_note")}
        direct = any(row.get("delivery_note") == doc.name for row in proof.items)
        if original.docstatus != 1 or original.company != doc.company or original.customer != doc.customer or (
                doc.name not in sources or (sources != {doc.name} and not direct)):
            frappe.throw("Hóa đơn giảm phải truy được về đúng phiếu giao; hóa đơn gộp cần dòng tham chiếu rõ phiếu này")


@frappe.whitelist(methods=["POST"])
def cap_nhat(name, modified, action, values=None):
    if not enabled():
        frappe.throw("Xử lý chênh lệch giao nhận chưa được bật")
    frappe.db.sql("SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE", name)
    doc = frappe.get_doc("Delivery Note", name)
    doc.check_permission("read")
    doc.check_permission("write")
    if cint(doc.docstatus) != 1 or cint(doc.is_return):
        frappe.throw("Chỉ xử lý chênh lệch trên phiếu giao đã xuất, không phải phiếu trả hoặc phiếu hủy")
    if str(doc.modified) != str(modified):
        frappe.throw("Phiếu đã thay đổi. Tải lại trước khi xử lý chênh lệch", frappe.TimestampMismatchError)
    if action != "report":
        _chief()
    try:
        v = R.normalize(action, frappe.parse_json(values) if isinstance(values, str) else values)
        state = R.transition(doc.get(STATE), action)
    except ValueError as exc:
        frappe.throw(str(exc))
    before = _snapshot(doc)
    if action == "report":
        doc.set(DETAIL, v["noi_dung"])
        if not doc.get(OPEN_BY):
            doc.set(OPEN_BY, frappe.session.user)
            doc.set(OPEN_AT, now_datetime())
    elif action == "assign":
        _assignee(doc, v["nguoi_phu_trach"])
        doc.set(ASSIGNEE, v["nguoi_phu_trach"])
        doc.set(DUE, v["han_xu_ly"])
    elif action == "resolve":
        if not doc.get(ASSIGNEE) or not doc.get(DUE):
            frappe.throw("Giao người phụ trách và hạn xử lý trước khi chốt kết quả")
        _assignee(doc, doc.get(ASSIGNEE))
        if not doc.get(ACTOR) or not doc.get(TIME) or not doc.get(FILE):
            frappe.throw("Đối chiếu bản ký hiện tại trước khi chốt xử lý chênh lệch")
        from kh_aph.ho_so_giao_nhan import _file
        _file(doc)
        if v["cach_xu_ly"] != R.NO_LEDGER:
            _proof(doc, v["cach_xu_ly"], v["phieu_tra"] or v["hoa_don_giam"])
        for f, k in ((RESULT, "ket_qua"), (MODE, "cach_xu_ly"), (RETURN, "phieu_tra"), (CREDIT, "hoa_don_giam")):
            doc.set(f, v[k] or None)
        doc.set(CLOSE_BY, frappe.session.user)
        doc.set(CLOSE_AT, now_datetime())
    else:
        for f in RESOLUTION:
            doc.set(f, None)
    doc.set(STATE, state)
    if _snapshot(doc) != before:
        previous = frappe.flags.get(FLAG)
        frappe.flags[FLAG] = doc.name
        try:
            doc.save()
            _audit(doc, {"report": "Ghi nhận", "assign": "Giao xử lý", "resolve": "Chốt xử lý",
                         "reopen": "Mở lại: " + v.get("ly_do", "")}[action], before)
        finally:
            frappe.flags[FLAG] = previous
    return {"name": doc.name, "modified": doc.modified, **_snapshot(doc)}


def before_cancel(doc, method=None):
    if not enabled() or not frappe.get_meta("Delivery Note").has_field(STATE):
        return
    if doc.doctype == "Delivery Note" and doc.get(STATE) in (R.PENDING, R.ACTIVE):
        frappe.throw("Phiếu còn chênh lệch cần xử lý; kế toán trưởng chốt hồ sơ trước khi hủy")
    field = RETURN if doc.doctype == "Delivery Note" else CREDIT
    if frappe.db.exists("Delivery Note", {field: doc.name, "docstatus": 1}):
        frappe.throw("Chứng từ đang làm căn cứ xử lý chênh lệch. Mở lại hồ sơ trên phiếu giao trước khi hủy")
