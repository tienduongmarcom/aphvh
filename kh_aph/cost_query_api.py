"""Opt-in plain-field Stock Entry child reads with native parent permissions.

The v16.35 client validator checks high levels against the child itself. These
wrappers avoid that validator for this one known table, retain native QB row and
field permissions, and apply the same app masks as document reads. Expressions
and all other doctypes delegate to Frappe unchanged.
"""
import re
import frappe
from frappe.utils import cint


def _fields(doctype, parent, fieldnames):
    if not cint(frappe.conf.get("kh_aph_server_cost_guard")):
        return None
    if doctype != "Stock Entry Detail" or parent != "Stock Entry":
        return None
    if isinstance(fieldnames, str):
        try:
            fieldnames = frappe.parse_json(fieldnames)
        except ValueError:
            fieldnames = [fieldnames]
    if isinstance(fieldnames, str):
        fieldnames = [fieldnames]
    if not isinstance(fieldnames, (list, tuple)) or not fieldnames:
        return None
    if any(not isinstance(f, str) or (f != "*" and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", f)) for f in fieldnames):
        return None
    from frappe.model import get_permitted_fields
    from kh_aph.price_visibility import COST_MASK, PRINT_MASK, is_cost_restricted, is_price_restricted
    meta = frappe.get_meta(doctype)
    valid = set(meta.get_valid_columns())
    for field in fieldnames:
        if field != "*" and field not in valid:
            frappe.throw("Field not permitted in query: " + field, frappe.DataError)
    allowed = set(get_permitted_fields(doctype, parenttype=parent, ignore_virtual=True))
    blocked = set()
    if is_cost_restricted():
        blocked.update(COST_MASK[parent]["tables"]["items"])
    if is_price_restricted():
        blocked.update(PRINT_MASK[parent]["tables"]["items"])
    requested = sorted(valid) if "*" in fieldnames else list(fieldnames)
    return [f for f in requested if f in allowed and f not in blocked] or ["name"]


@frappe.whitelist()
def get_list(doctype, fields=None, filters=None, group_by=None, order_by=None,
             limit_start=None, limit_page_length=20, parent=None, debug=False,
             as_dict=True, or_filters=None, expand=None):
    from frappe import client
    selected = _fields(doctype, parent, fields)
    if selected is None or group_by or expand:
        return client.get_list(doctype=doctype, fields=fields, filters=filters,
            group_by=group_by, order_by=order_by, limit_start=limit_start,
            limit_page_length=limit_page_length, parent=parent, debug=debug,
            as_dict=as_dict, or_filters=or_filters, expand=expand)
    # Native QB checks parent read permissions, field permissions, filters,
    # user permissions, and ordering. Never use get_all or ignore_permissions.
    return frappe.get_list(doctype, parent_doctype=parent, fields=selected,
        filters=frappe.parse_json(filters), or_filters=frappe.parse_json(or_filters),
        order_by=order_by, limit_start=cint(limit_start),
        limit_page_length=cint(limit_page_length), debug=cint(debug),
        as_list=not cint(as_dict))


@frappe.whitelist()
def get_value(doctype, fieldname, filters=None, as_dict=True, debug=False, parent=None):
    from frappe import client
    selected = _fields(doctype, parent, fieldname)
    if selected is None:
        return client.get_value(doctype, fieldname, filters, as_dict, debug, parent)
    # Match native filter parsing, including a document name supplied as a string.
    filters = client.get_safe_filters(filters)
    if isinstance(filters, str):
        filters = {"name": filters}
    rows = get_list(doctype, fields=selected, filters=filters, parent=parent,
                    limit_page_length=1, as_dict=as_dict, debug=debug)
    if cint(as_dict):
        return rows[0] if rows else {}
    if not rows:
        return None
    return rows[0] if len(selected) > 1 else rows[0][0]
