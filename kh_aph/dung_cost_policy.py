"""Explicit cost-deny profile for operational users; opt-in candidate only.

Administrator is the control account. Do not assign System Manager or developer
access to a user this policy is intended to constrain. Blocking report/export
surfaces is intentional; the quantity report is the supported stock overview.
"""
import frappe
from frappe.utils import cint
from kh_aph.constants import ROLE_NO_COST, REPORT_QTY

SENSITIVE = ("Bin", "Stock Ledger Entry", "GL Entry", "Purchase Invoice",
             "Landed Cost Voucher", "Stock Reconciliation", "BOM", "Work Order",
             "Repost Item Valuation", "Item Price")

def restricted(user=None):
    user = user or frappe.session.user
    return (bool(cint(frappe.conf.get("kh_aph_server_cost_guard")))
            and user != "Administrator" and ROLE_NO_COST in frappe.get_roles(user))

def has_permission(doc, ptype=None, user=None, **kwargs):
    if restricted(user):
        return False
    return None

def query_conditions(user=None, **kwargs):
    return "1=0" if restricted(user) else ""

def before_request():
    if not restricted():
        return
    cmd = frappe.form_dict.get("cmd") or ""
    path = frappe.request.path
    if not cmd and "/api/method/" in path:
        cmd = path.split("/api/method/", 1)[1]
    deny = ("export" in cmd.lower() or "download_template" in cmd.lower()
            or cmd.startswith("frappe.desk.reportview.")
            or cmd.startswith("erpnext.stock.get_item_details.")
            or cmd.endswith(".get_item_details"))
    if cmd.startswith("frappe.desk.query_report."):
        deny = frappe.form_dict.get("report_name") != REPORT_QTY
    if cmd in ("frappe.client.get_list", "frappe.client.get_value", "frappe.client.get_count"):
        dt = frappe.form_dict.get("doctype")
        # Only the permission-aware plain-field child wrapper is allowed here.
        if dt == "Stock Entry Detail":
            from kh_aph.cost_query_api import _fields
            fields = frappe.form_dict.get("fields") or frappe.form_dict.get("fieldname")
            deny = _fields(dt, frappe.form_dict.get("parent"), fields) is None
        elif dt in SENSITIVE or dt in ("Stock Entry", "Item", "Purchase Receipt", "Purchase Order",
                                      "Sales Order Item", "Delivery Note Item", "Serial and Batch Bundle"):
            deny = True
    # Generic REST list endpoints do not pass through the child RPC wrapper.
    if path.startswith("/api/resource/") or path.startswith("/api/v2/document/"):
        from urllib.parse import unquote
        tail = unquote(path).split("/", 4)[-1]
        if "/" not in tail and frappe.request.method == "GET":
            deny = True
    if deny:
        frappe.throw("Hồ sơ không xem giá vốn: dùng báo cáo tồn kho số lượng hoặc phiếu được phép.",
                     frappe.PermissionError)

def mask_response(value):
    """Mask typed document responses without mutating transaction documents."""
    from kh_aph.price_visibility import COST_MASK
    if isinstance(value, list):
        for child in value:
            mask_response(child)
    elif isinstance(value, dict):
        spec = COST_MASK.get(value.get("doctype"))
        if spec:
            for field in spec["parent"]:
                if field in value:
                    value[field] = None
            for table, fields in spec["tables"].items():
                for row in value.get(table) or []:
                    for field in fields:
                        if field in row:
                            row[field] = None
            for table in spec["clear"]:
                if table in value:
                    value[table] = []
        for child in value.values():
            mask_response(child)

def after_request(response, request=None):
    if not restricted() or not response.is_json or response.status_code >= 400:
        return
    payload = response.get_json()
    mask_response(payload)
    response.set_data(frappe.as_json(payload))
