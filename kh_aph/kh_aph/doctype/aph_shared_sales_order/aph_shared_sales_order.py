"""Candidate coordinator. Native company Sales Orders retain their own accounting."""
import uuid
import frappe
from frappe.model.document import Document
from frappe.utils import cint, getdate
from kh_aph.shared_order_rules import plan_orders


class APHSharedSalesOrder(Document):
    def _require_enabled(self):
        if not cint(frappe.conf.get("kh_aph_shared_sales_order")):
            frappe.throw("Đơn bán chung chưa được bật trên site này")

    def _plan(self):
        warehouses = {}
        rows = []
        for line in self.items:
            if not line.line_id:
                line.line_id = uuid.uuid4().hex
            wh = frappe.get_doc("Warehouse", line.warehouse)
            wh.check_permission("read")
            # Draft ownership is derived from the source warehouse.
            if cint(self.docstatus) == 0:
                line.company = wh.company
            item = frappe.get_doc("Item", line.item_code)
            item.check_permission("read")
            if item.disabled or item.stock_uom != "Kg":
                frappe.throw("MVP đơn chung chỉ nhận mã đang hoạt động có đơn vị tồn kho Kg")
            co = frappe.get_doc("Company", wh.company)
            co.check_permission("read")
            warehouses[wh.name] = {"company": wh.company, "abbr": co.abbr,
                                   "disabled": wh.disabled, "is_group": wh.is_group}
            rows.append({"line_id": line.line_id, "item_code": line.item_code,
                         "warehouse": line.warehouse, "company": line.company,
                         "qty": line.qty, "rate": line.rate,
                         "kh_aph_bags": line.get("kh_aph_bags"),
                         "kh_aph_kg_per_bag": line.get("kh_aph_kg_per_bag")})
        try:
            return plan_orders(rows, warehouses)
        except ValueError as exc:
            frappe.throw(str(exc))

    def validate(self):
        self._require_enabled()
        if not self.delivery_date or getdate(self.delivery_date) < getdate(self.transaction_date):
            frappe.throw("Ngày giao không được trước ngày đặt hàng")
        if self.currency != "VND":
            frappe.throw("MVP đơn chung sử dụng VND")
        from kh_aph.bag_stock import validate as validate_bags
        validate_bags(self)
        plan = self._plan()
        company_by_line = {r["line_id"]: company for company, rows in plan["companies"].items() for r in rows}
        for row in self.items:
            row.company = company_by_line[row.line_id]
            row.amount = float(row.qty) * float(row.rate)
        self.net_total = float(plan["net_total"])
        from kh_aph import global_credit
        global_credit.validate_shared(self)

    def on_submit(self):
        self._require_enabled()
        frappe.db.sql("SELECT name FROM `tabAPH Shared Sales Order` WHERE name=%s FOR UPDATE", self.name)
        plan = self._plan()
        # Explicit setup must install these backlinks before using this workflow.
        for dt, field in (("Sales Order", "kh_aph_shared_order"),
                          ("Sales Order", "kh_aph_shared_fingerprint"),
                          ("Sales Order Item", "kh_aph_shared_line")):
            if not frappe.get_meta(dt).has_field(field):
                frappe.throw("Thiếu liên kết đơn chung trên " + dt)
        linked = frappe.get_all("Sales Order", filters={"kh_aph_shared_order": self.name},
                                 fields=["name", "company", "docstatus", "kh_aph_shared_fingerprint"])
        if linked:
            if (len(linked) == len(plan["companies"])
                and {r.company for r in linked} == set(plan["companies"])
                and all(r.docstatus == 1 and r.kh_aph_shared_fingerprint == plan["fingerprint"] for r in linked)):
                return
            frappe.throw("Chứng từ của đơn chung không khớp; cần đối soát, không tự tạo thêm")
        from kh_aph.constants import INV_FLAG
        from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
        for company, rows in plan["companies"].items():
            values = {"doctype": "Sales Order", "company": company, "customer": self.customer,
                      "transaction_date": self.transaction_date, "delivery_date": self.delivery_date,
                      "selling_price_list": self.selling_price_list, "currency": "VND",
                      "conversion_rate": 1, "order_type": "Sales",
                      "kh_aph_shared_order": self.name, "kh_aph_shared_fingerprint": plan["fingerprint"],
                      "items": [{"item_code": r["item_code"], "warehouse": r["warehouse"],
                                 "qty": float(r["qty"]), "rate": float(r["rate"]), "uom": "Kg",
                                 "conversion_factor": 1, "delivery_date": self.delivery_date,
                                 "kh_aph_bags": r.get("kh_aph_bags"),
                                 "kh_aph_kg_per_bag": r.get("kh_aph_kg_per_bag"),
                                 "kh_aph_shared_line": r["line_id"]} for r in rows]}
            customer = frappe.get_doc("Customer", self.customer)
            if customer.get(INV_FLAG):
                values[INV_FLAG] = customer.get(INV_FLAG)
            so = frappe.get_doc(values)
            if not isinstance(so, SalesOrder):
                frappe.throw("Sai controller Sales Order")
            so.insert()
            so.submit()
        # Never commit or swallow a company failure. The request owns atomicity.

    def before_cancel(self):
        self._require_enabled()
        for name in frappe.get_all("Sales Order", filters={"kh_aph_shared_order": self.name}, pluck="name"):
            so = frappe.get_doc("Sales Order", name)
            if so.docstatus == 1:
                so.cancel()  # Native guard rejects cancellation after delivery/billing.
