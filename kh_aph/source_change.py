"""Opt-in re-source of open quantity, retaining dispatched voucher identities."""
import json
from decimal import Decimal
import frappe
from frappe.model.document import Document
from frappe.utils import cint, now, get_datetime

def number(value):
    try:
        value = Decimal(str(value or 0))
        if not value.is_finite():
            raise ValueError()
        return value
    except Exception:
        frappe.throw("Số lượng không hợp lệ")

def effective_plan(shared):
    original = {r.line_id: r for r in shared.items}
    qty = {k: Decimal(0) for k in original}
    for name in frappe.get_all("Sales Order", filters={"kh_aph_shared_order": shared.name, "docstatus": 1}, pluck="name"):
        so = frappe.get_doc("Sales Order", name)
        if so.customer != shared.customer:
            frappe.throw("Đơn nguồn không khớp khách")
        for row in so.items:
            source = original.get(row.kh_aph_shared_line)
            if not source or source.item_code != row.item_code or number(source.rate) != number(row.rate):
                frappe.throw("Dòng/giá nguồn bị lệch hợp đồng; cần đối soát")
            if frappe.db.get_value("Warehouse", row.warehouse, "company") != so.company:
                frappe.throw("Kho nguồn không khớp chủ hàng")
            qty[source.line_id] += number(row.delivered_qty if so.status == "Closed" else row.qty)
    if any(qty[k] != number(row.qty) for k, row in original.items()):
        frappe.throw("Tổng lượng các nguồn không khớp hợp đồng")

def coordinator_links(doc, method=None):
    if frappe.flags.source_change_internal:
        doc.ignore_linked_doctypes = tuple(getattr(doc, "ignore_linked_doctypes", ()) or ()) + ("APH Source Change",)

def prevent_reopen(doc, method=None):
    if not frappe.flags.source_change_internal and doc.docstatus == 1 and doc.status != "Closed" and frappe.db.exists(
        "APH Source Change", {"source_order": doc.name, "closed_source": 1, "docstatus": 1}):
        frappe.throw("Nguồn đã chuyển hết; đảo phiếu đổi nguồn trước khi mở lại")

def lock_delivery_sources(doc, method=None):
    if not cint(frappe.conf.get("kh_aph_source_change")):
        return
    names = sorted({row.against_sales_order for row in doc.items if row.get("against_sales_order")})
    for name in names:
        frappe.db.sql("SELECT name FROM `tabSales Order` WHERE name=%s FOR UPDATE", name)
    if doc.is_return:
        return
    grouped = {}
    for row in doc.items:
        if row.get("so_detail"):
            grouped[row.so_detail] = grouped.get(row.so_detail, Decimal(0)) + number(row.qty)
    for name, qty in grouped.items():
        row = frappe.get_doc("Sales Order Item", name)
        if not frappe.db.get_value("Sales Order", row.parent, "kh_aph_shared_order"):
            continue
        if frappe.db.get_value("Sales Order", row.parent, "status") == "Closed" or qty > number(row.qty) - number(row.delivered_qty):
            frappe.throw("Nguồn/lượng đã đổi; lấy lại phiếu giao từ nguồn đang hiệu lực")

def update_row(so, row_name, qty, restored=None):
    from erpnext.controllers.accounts_controller import update_child_qty_rate, set_order_defaults
    data = []
    for row in so.items:
        value = number(qty) if row.name == row_name else number(row.qty)
        if value == 0:
            continue
        if row.name == row_name and row.get("kh_aph_kg_per_bag"):
            bags = value / number(row.kh_aph_kg_per_bag)
            if bags != bags.to_integral_value():
                frappe.throw("Đổi nguồn phải đủ bao theo snapshot")
            frappe.db.set_value(row.doctype, row.name, "kh_aph_bags", int(bags))
        data.append({"docname": row.name, "item_code": row.item_code, "qty": float(value), "rate": row.rate,
            "uom": row.uom, "conversion_factor": row.conversion_factor, "delivery_date": str(row.delivery_date),
            "description": row.description})
    if restored:
        values = {"item_code": restored["item_code"], "warehouse": restored["warehouse"],
            "uom": "Kg", "conversion_factor": 1, "delivery_date": restored["delivery_date"]}
        child = set_order_defaults("Sales Order", so.name, "Sales Order Item", "items", values)
        child.update({"qty": float(qty), "rate": restored["rate"],
            "kh_aph_shared_line": restored["kh_aph_shared_line"],
            "kh_aph_kg_per_bag": restored["kh_aph_kg_per_bag"], "kh_aph_bags": restored["kh_aph_bags"]})
        # Native update-after-submit skips before_validate; restore the bag-price
        # display from the approved root selling rate and stored package weight.
        child.kh_aph_bag_rate = float(number(restored["rate"]) * number(restored["kh_aph_kg_per_bag"]))
        child.parent, child.parenttype, child.parentfield = so.name, "Sales Order", "items"
        child.idx = len(so.items) + 1
        child.flags.ignore_validate_update_after_submit = True
        child.insert(ignore_permissions=True)
        data.append({"docname": child.name, "item_code": child.item_code, "qty": float(qty),
            "rate": restored["rate"], "uom": "Kg", "conversion_factor": 1,
            "delivery_date": restored["delivery_date"], "description": restored["description"]})
    if not data:
        so.update_status("Closed")
        return
    update_child_qty_rate("Sales Order", json.dumps(data), so.name)

class SourceChange(Document):
    def validate(self):
        if not cint(frappe.conf.get("kh_aph_source_change")):
            frappe.throw("Đổi nguồn chưa bật")
        so = frappe.get_doc("Sales Order", self.source_order)
        so.check_permission("write")
        if so.docstatus != 1 or not so.kh_aph_shared_order or so.status == "Closed":
            frappe.throw("Chọn nguồn đang hiệu lực của đơn chung")
        if self.shared_order and self.shared_order != so.kh_aph_shared_order:
            frappe.throw("Nguồn không thuộc đơn chung đã chọn")
        shared = frappe.get_doc("APH Shared Sales Order", so.kh_aph_shared_order)
        shared.check_permission("read")
        if shared.docstatus != 1:
            frappe.throw("Đơn chung không còn hiệu lực")
        row = next((r for r in so.items if r.name == self.source_row), None)
        if not row:
            frappe.throw("Dòng không thuộc đơn nguồn")
        wh = frappe.get_doc("Warehouse", self.target_warehouse)
        wh.check_permission("read")
        co = frappe.get_doc("Company", wh.company)
        co.check_permission("read")
        if wh.disabled or wh.is_group or co.abbr not in ("APH","VH","MK","TL") or wh.name == row.warehouse:
            frappe.throw("Chọn kho lá khác, đúng APH/VH/MK/TL")
        moved = number(self.qty)
        if moved <= 0 or moved > number(row.qty) - number(row.delivered_qty):
            frappe.throw("Chỉ chuyển lượng chưa giao")
        if row.get("kh_aph_kg_per_bag"):
            bags = moved / number(row.kh_aph_kg_per_bag)
            if bags != bags.to_integral_value():
                frappe.throw("Lượng đổi nguồn phải đủ bao nguyên")
        if not (self.reason or "").strip():
            frappe.throw("Cần lý do đổi nguồn")
        self.shared_order, self.line_id, self.source_item = shared.name, row.kh_aph_shared_line, row.item_code
        self.source_company, self.target_company = so.company, wh.company
        if self.is_new() and (self.target_order or self.original_row_json):
            frappe.throw("Không gắn thủ công chứng từ/lịch sử nguồn")
    def before_submit(self):
        shared = frappe.db.get_value("Sales Order", self.source_order, "kh_aph_shared_order")
        frappe.db.sql("SELECT name FROM `tabAPH Shared Sales Order` WHERE name=%s FOR UPDATE", shared)
        frappe.db.sql("SELECT name FROM `tabSales Order` WHERE name=%s FOR UPDATE", self.source_order)
        self.validate()
        effective_plan(frappe.get_doc("APH Shared Sales Order", self.shared_order))
        self.changed_by, self.changed_at = frappe.session.user, now()
    def on_submit(self):
        so = frappe.get_doc("Sales Order", self.source_order)
        row = next(r for r in so.items if r.name == self.source_row)
        old = {f: row.get(f) for f in ("name","item_code","warehouse","qty","description","delivery_date",
            "kh_aph_shared_line","kh_aph_kg_per_bag","kh_aph_bags")}
        old["delivery_date"] = str(old["delivery_date"])
        self.db_set("original_row_json", json.dumps(old, ensure_ascii=False, default=str))
        values = {"doctype":"Sales Order","company":self.target_company,"customer":so.customer,
            "transaction_date":so.transaction_date,"delivery_date":so.delivery_date,
            "currency":so.currency,"conversion_rate":so.conversion_rate,"selling_price_list":so.selling_price_list,
            "order_type":so.order_type,"kh_aph_shared_order":self.shared_order,
            "kh_aph_shared_fingerprint":so.kh_aph_shared_fingerprint,
            "items":[{"item_code":row.item_code,"warehouse":self.target_warehouse,"qty":float(number(self.qty)),
                "rate":row.rate,"uom":row.uom,"conversion_factor":row.conversion_factor,"delivery_date":row.delivery_date,
                "kh_aph_shared_line":self.line_id,"kh_aph_kg_per_bag":row.get("kh_aph_kg_per_bag"),
                "kh_aph_bags":float(number(self.qty)/number(row.kh_aph_kg_per_bag)) if row.get("kh_aph_kg_per_bag") else 0}]}
        frappe.flags.source_change_internal = True
        try:
            # Derived state comes from the actual source, never client JSON.
            self.db_set("closed_source", int(len(so.items) == 1 and number(row.qty) == number(self.qty)))
            update_row(so,row.name,number(row.qty)-number(self.qty))
            target = frappe.get_doc(values).insert()
            target.submit()
            self.db_set("target_order",target.name)
        finally:
            frappe.flags.source_change_internal = False
        effective_plan(frappe.get_doc("APH Shared Sales Order",self.shared_order))
    def before_update_after_submit(self):
        frappe.throw("Đổi nguồn đã xác nhận bất biến")
    def before_cancel(self):
        self.check_permission("cancel")
        persisted = frappe.get_doc(self.doctype, self.name)
        for field in ("shared_order", "source_order", "source_row", "target_warehouse", "target_order",
                      "original_row_json", "line_id", "source_item", "source_company", "target_company",
                      "reason", "changed_by"):
            if str(self.get(field) or "") != str(persisted.get(field) or ""):
                frappe.throw("Không sửa lịch sử đổi nguồn khi hủy")
        if (get_datetime(self.changed_at) if self.changed_at else None) != (get_datetime(persisted.changed_at) if persisted.changed_at else None):
            frappe.throw("Không sửa thời điểm đổi nguồn khi hủy")
        if number(self.qty) != number(persisted.qty) or cint(self.closed_source) != cint(persisted.closed_source):
            frappe.throw("Không sửa lượng/trạng thái nguồn khi hủy")
        frappe.db.sql("SELECT name FROM `tabAPH Shared Sales Order` WHERE name=%s FOR UPDATE",self.shared_order)
        source = frappe.get_doc("Sales Order",self.source_order)
        target = frappe.get_doc("Sales Order",self.target_order)
        source.check_permission("write")
        target.check_permission("cancel")
        frappe.db.sql("SELECT name FROM `tabSales Order` WHERE name IN (%s,%s) ORDER BY name FOR UPDATE",
            (source.name,target.name))
        if frappe.db.exists("APH Source Change",{"source_order":target.name,"docstatus":1}):
            frappe.throw("Nguồn đã đổi tiếp; đảo thay đổi sau trước")
        old = json.loads(self.original_row_json)
        shared = frappe.get_doc("APH Shared Sales Order",self.shared_order)
        old["rate"] = next(r.rate for r in shared.items if r.line_id == self.line_id)
        if source.docstatus != 1:
            frappe.throw("Nguồn bị hủy ngoài kế hoạch; cần đối soát")
        frappe.flags.source_change_internal = True
        try:
            target.cancel()
            if self.closed_source:
                if source.status != "Closed":
                    frappe.throw("Nguồn đóng bị sửa ngoài kế hoạch")
                source.update_status("Draft")
            else:
                row = next((r for r in source.items if r.kh_aph_shared_line == self.line_id
                    and r.item_code == old["item_code"] and r.warehouse == old["warehouse"]),None)
                update_row(source,row.name if row else None,
                    number(row.qty)+number(self.qty) if row else self.qty,restored=old if not row else None)
        finally:
            frappe.flags.source_change_internal = False
        effective_plan(frappe.get_doc("APH Shared Sales Order",self.shared_order))
