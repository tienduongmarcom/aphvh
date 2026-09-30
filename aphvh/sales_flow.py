"""Luồng bán hàng kho Hà Nội (0.3): hóa đơn nháp tự tạo từ phiếu giao hàng.

- Thủ kho xác nhận phiếu giao hàng (khách đã ký) → app tạo Hóa đơn bán hàng NHÁP đúng số lượng đã
  giao, giá và thuế lấy từ đơn (qua phiếu giao). Kế toán kiểm tra, đối chiếu hóa đơn MISA rồi mới
  xác nhận; công nợ 131 và doanh thu chỉ ghi lúc đó.
- Phiếu nhận hàng trả lại:
  - hóa đơn của phiếu giao gốc còn NHÁP (app tạo) → trừ số trả lại thẳng vào hóa đơn nháp đó
    (trả hết thì xóa hóa đơn nháp), không lập hóa đơn trả lại;
  - hóa đơn gốc đã xác nhận → hóa đơn trả lại nháp, gắn hóa đơn gốc, giảm công nợ của hóa đơn gốc.
- Không tạo được hóa đơn (thiếu tài khoản, sai cấu hình…) thì KHÔNG chặn phiếu giao hàng: ghi Nhật ký
  lỗi và báo để kế toán lập tay.
- Hủy phiếu giao hàng → xóa hóa đơn nháp do app tạo từ chính phiếu đó (chưa xác nhận nên chưa ghi sổ).
- Phiếu giao có dòng lập từ hóa đơn, hoặc đơn đã lập hóa đơn một phần trước khi giao: không tự tạo
  (tránh lập trùng), báo kế toán.

Bật/tắt: Cài đặt bán hàng → "Tự tạo hóa đơn nháp khi xác nhận phiếu giao hàng".
"""

from collections import defaultdict

import frappe
from frappe.utils import cint, escape_html, flt, fmt_money, get_link_to_form

from aphvh.constants import SI_AUTO, SS_AUTO_INVOICE
from aphvh.sales_warnings import setting_on
from aphvh.vn_words import so_vn

_SAVEPOINT = "aphvh_auto_invoice"
_QTY_EPS = 1e-9


# --- tiện ích ---------------------------------------------------------------------------------


def _tien(si) -> str:
    amount = abs(flt(si.rounded_total or si.grand_total))
    if si.currency == "VND":
        return f"{so_vn(amount, 0)} đ"
    return fmt_money(amount, currency=si.currency)


def _ten_hd(name: str) -> str:
    return get_link_to_form("Sales Invoice", name) if frappe.has_permission("Sales Invoice", "read") else name


def _notice(msg: str, indicator: str = "orange"):
    frappe.msgprint(msg, title="Hóa đơn tự động", indicator=indicator)


def _run_safely(fn, *args):
    """Chạy fn trong savepoint. Lỗi → hoàn tác phần của fn, bỏ thông báo lỗi của nó, trả (None, lỗi, vết)."""
    start = len(frappe.local.message_log)
    frappe.db.savepoint(_SAVEPOINT)
    try:
        return fn(*args), None, None
    except Exception as e:
        trace = frappe.get_traceback()
        frappe.db.rollback(save_point=_SAVEPOINT)
        del frappe.local.message_log[start:]  # phiếu giao vẫn xác nhận được
        frappe.flags.error_message = None
        return None, e, trace


def _report_failure(doc, error, trace):
    from aphvh.price_visibility import is_cost_restricted

    doc.log_error(f"aphvh: không tạo được hóa đơn nháp từ {doc.name}", trace)
    # Lỗi chuẩn có thể nêu giá vốn (vd. kiểm tra giá bán dưới giá vốn): không hiện cho người bị ẩn giá vốn.
    detail = "" if is_cost_restricted() else f" ({escape_html(str(error) or type(error).__name__)[:300]})"
    _notice(
        f"Phiếu giao hàng đã xác nhận nhưng không tạo được hóa đơn nháp tự động{detail}. "
        "Kế toán lập hóa đơn từ phiếu giao hàng này (nút Tạo → Hóa đơn bán hàng); chi tiết trong Nhật ký lỗi."
    )


# --- tạo hóa đơn nháp -------------------------------------------------------------------------


def _original_invoices(doc) -> list[str]:
    """Hóa đơn bán hàng (không phải hóa đơn trả lại) đã xác nhận của phiếu giao gốc."""
    if not doc.return_against:
        return []
    parents = {
        r.parent
        for r in frappe.get_all(
            "Sales Invoice Item",
            filters={"delivery_note": doc.return_against, "docstatus": 1},
            fields=["parent"],
            distinct=True,
        )
    }
    if not parents:
        return []
    return frappe.get_all(
        "Sales Invoice", filters={"name": ["in", list(parents)], "is_return": 0, "docstatus": 1}, pluck="name"
    )


def _link_return_rows(si, return_against: str):
    """Gắn hóa đơn trả lại với hóa đơn gốc: từng dòng trỏ về dòng hóa đơn gốc (để ERPNext kiểm số lượng
    trả không vượt số đã bán) và giảm công nợ của chính hóa đơn gốc (không để thành khoản âm riêng)."""
    si.return_against = return_against
    si.update_outstanding_for_self = 0
    by_dn_row = {
        r.dn_detail: r.name
        for r in frappe.get_all(
            "Sales Invoice Item", filters={"parent": return_against}, fields=["name", "dn_detail"]
        )
        if r.dn_detail
    }
    for row in si.items:
        # dòng hóa đơn trả lại → dòng phiếu nhận trả lại → dòng phiếu giao gốc → dòng hóa đơn gốc
        original = frappe.db.get_value("Delivery Note Item", row.dn_detail, "dn_detail") if row.dn_detail else None
        if original in by_dn_row:
            row.sales_invoice_item = by_dn_row[original]


def _build_invoice(doc, return_against: str | None):
    from erpnext.accounts.party import get_due_date
    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

    # Thủ kho không có quyền trên hóa đơn: lập hóa đơn thay họ. Truyền sẵn hóa đơn đích có cờ bỏ qua
    # quyền để hàm chuẩn không đòi quyền "tạo hóa đơn" của người đang xác nhận phiếu giao.
    target = frappe.new_doc("Sales Invoice")
    target.flags.ignore_permissions = True
    si = make_sales_invoice(doc.name, target_doc=target)
    si.set_posting_time = 1
    si.posting_date = doc.posting_date
    si.posting_time = doc.posting_time
    if cint(doc.is_return):
        si.is_return = 1
        si.due_date = doc.posting_date
        if return_against:
            _link_return_rows(si, return_against)
    else:
        # Hạn thanh toán tính từ ngày giao hàng, không phải ngày app chạy
        si.due_date = get_due_date(
            doc.posting_date, "Customer", si.customer, si.company, template_name=si.payment_terms_template
        )
    si.set("payment_schedule", [])
    si.set(SI_AUTO, 1)
    si.flags.ignore_permissions = True
    si.insert()
    return si


def _create_invoice(doc):
    originals = _original_invoices(doc) if cint(doc.is_return) else []
    # Gắn hóa đơn gốc khi phiếu gốc chỉ có một hóa đơn; không hợp lệ thì lập hóa đơn trả lại không gắn.
    attempts = [originals[0], None] if len(originals) == 1 else [None]
    error = trace = None
    for return_against in attempts:
        si, error, trace = _run_safely(_build_invoice, doc, return_against)
        if si:
            loai = "hóa đơn trả lại" if cint(doc.is_return) else "hóa đơn bán hàng"
            frappe.msgprint(
                f"Đã tạo {loai} nháp {_ten_hd(si.name)} ({_tien(si)}) để kế toán kiểm tra và xác nhận.",
                indicator="green",
                alert=True,
            )
            return
    _report_failure(doc, error, trace)


# --- trả lại khi hóa đơn gốc còn nháp ---------------------------------------------------------


def _returned_by_row(ret) -> dict[str, float]:
    """Số lượng trả lại theo dòng phiếu giao gốc (dương, cùng ĐVT với dòng gốc)."""
    out: dict[str, float] = defaultdict(float)
    for r in ret.items:
        if r.get("dn_detail"):
            out[r.dn_detail] += abs(flt(r.qty))
    return dict(out)


def _draft_invoices_of(dn_name: str) -> list:
    parents = {
        r.parent
        for r in frappe.get_all(
            "Sales Invoice Item", filters={"delivery_note": dn_name, "docstatus": 0}, fields=["parent"], distinct=True
        )
    }
    docs = [frappe.get_doc("Sales Invoice", n) for n in sorted(parents)]
    return [d for d in docs if cint(d.get(SI_AUTO)) and not cint(d.is_return)]


def _net_into_drafts(drafts, returned: dict[str, float]) -> list[str]:
    left = dict(returned)
    changes = []
    for si in drafts:
        touched = False
        for row in si.items:
            need = left.get(row.dn_detail, 0)
            if need <= _QTY_EPS:
                continue
            take = min(need, flt(row.qty))
            row.qty = flt(row.qty) - take
            left[row.dn_detail] = need - take
            touched = True
        if not touched:
            continue
        keep = [r for r in si.items if flt(r.qty) > _QTY_EPS]
        if keep:
            for i, r in enumerate(keep, 1):
                r.idx = i
            si.set("items", keep)
            si.flags.ignore_permissions = True
            si.save()
            changes.append(f"trừ vào hóa đơn nháp {_ten_hd(si.name)}, còn {_tien(si)}")
        else:
            frappe.delete_doc("Sales Invoice", si.name, ignore_permissions=True)
            changes.append(f"xóa hóa đơn nháp {si.name} (khách trả lại toàn bộ)")
    return changes


def _return_into_draft(ret) -> bool:
    """Trả lại khi hóa đơn của phiếu giao gốc chưa xác nhận: sửa hóa đơn nháp thay vì lập hóa đơn trả lại.

    Chỉ làm khi các hóa đơn nháp app tạo trừ được TOÀN BỘ số trả lại; không thì để lập hóa đơn trả lại.
    """
    if not ret.return_against:
        return False
    returned = _returned_by_row(ret)
    if not returned:
        return False
    drafts = _draft_invoices_of(ret.return_against)
    if not drafts:
        return False
    available: dict[str, float] = defaultdict(float)
    for si in drafts:
        for row in si.items:
            available[row.dn_detail] += flt(row.qty)
    if any(available.get(k, 0) + _QTY_EPS < v for k, v in returned.items()):
        return False

    changes, error, trace = _run_safely(_net_into_drafts, drafts, returned)
    if changes is None:
        _report_failure(ret, error, trace)
        return True  # không lập thêm hóa đơn trả lại khi hóa đơn gốc còn nháp: kế toán xử lý tay
    frappe.msgprint(
        "Hóa đơn của phiếu giao gốc chưa xác nhận nên không lập hóa đơn trả lại: "
        + "; ".join(changes)
        + ".",
        indicator="green",
        alert=True,
    )
    return True


# --- móc nối Delivery Note --------------------------------------------------------------------


def make_draft_invoice(doc, method=None):
    """Delivery Note on_submit."""
    if not setting_on(SS_AUTO_INVOICE) or not frappe.get_meta("Sales Invoice").has_field(SI_AUTO):
        return
    if cint(doc.get("is_internal_customer")):
        return

    if cint(doc.is_return):
        # "Issue Credit Note" chuẩn của ERPNext đã tự lập và xác nhận hóa đơn trả lại
        if cint(doc.get("issue_credit_note")) or _return_into_draft(doc):
            return
        _create_invoice(doc)
        return

    if flt(doc.per_billed) >= 100:
        return  # phiếu giao lập từ hóa đơn đã có
    if any(r.get("against_sales_invoice") for r in doc.items):
        _notice("Phiếu giao có dòng lập từ hóa đơn đã có nên app không tự tạo hóa đơn nháp. Kế toán kiểm tra phần còn lại.")
        return
    if flt(doc.per_billed) > 0:
        _notice(
            "Đơn bán hàng đã lập hóa đơn một phần trước khi giao nên app không tự tạo hóa đơn nháp "
            "(tránh lập trùng). Kế toán lập hóa đơn phần còn lại."
        )
        return
    _create_invoice(doc)


def remove_draft_invoices(doc, method=None):
    """Delivery Note on_cancel: xóa hóa đơn NHÁP do app tạo từ chính phiếu này.

    Chỉ xóa hóa đơn còn nháp, có đánh dấu tự tạo và mọi dòng đều thuộc phiếu này; hóa đơn đã xác nhận
    thì ERPNext đã chặn hủy phiếu giao hàng từ trước.
    """
    if not frappe.get_meta("Sales Invoice").has_field(SI_AUTO):
        return
    rows = frappe.get_all(
        "Sales Invoice Item",
        filters={"delivery_note": doc.name, "docstatus": 0},
        fields=["parent"],
        distinct=True,
    )
    removed = []
    for name in {r.parent for r in rows}:
        si = frappe.get_doc("Sales Invoice", name)
        if si.docstatus != 0 or not cint(si.get(SI_AUTO)):
            continue
        if any(r.delivery_note != doc.name for r in si.items):
            continue
        frappe.delete_doc("Sales Invoice", name, ignore_permissions=True)
        removed.append(name)
    if removed:
        frappe.msgprint(
            f"Đã xóa hóa đơn nháp tự tạo từ phiếu này: {', '.join(sorted(removed))}.",
            indicator="blue",
            alert=True,
        )


def validate_delivery_note(doc, method=None):
    """Thủ kho Hà Nội chỉ giao hàng theo đơn bán hàng và không sửa giá (trừ phiếu nhận hàng trả lại)."""
    from aphvh.price_visibility import is_hn_storekeeper

    if cint(doc.is_return) or not is_hn_storekeeper():
        return
    bad = [r for r in doc.items if not r.get("against_sales_order") or not r.get("so_detail")]
    if bad:
        frappe.throw(
            "Thủ kho chỉ lập phiếu giao hàng từ đơn bán hàng (mở đơn → Tạo → Phiếu giao hàng). "
            "Dòng chưa gắn đơn: " + ", ".join(f"#{r.idx} {r.item_code}" for r in bad),
            title="Thiếu đơn bán hàng",
        )

    so_rows = {
        r.name: r
        for r in frappe.get_all(
            "Sales Order Item",
            filters={"name": ["in", [r.so_detail for r in doc.items]]},
            fields=["name", "rate", "conversion_factor"],
        )
    }

    def per_stock_unit(rate, factor):
        return flt(rate) / (flt(factor) or 1)

    changed = [
        r
        for r in doc.items
        if r.so_detail in so_rows
        and abs(
            per_stock_unit(r.rate, r.conversion_factor)
            - per_stock_unit(so_rows[r.so_detail].rate, so_rows[r.so_detail].conversion_factor)
        )
        > 0.01
    ]
    if changed:
        frappe.throw(
            "Giá trên phiếu giao hàng phải đúng giá trên đơn bán hàng; muốn đổi giá thì nhân viên bán hàng "
            "sửa đơn. Dòng bị đổi giá: " + ", ".join(f"#{r.idx} {r.item_code}" for r in changed),
            title="Không sửa giá khi giao hàng",
        )
