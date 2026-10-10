"""Opt-in document read protection. Query/report gates remain separate UAT cases."""

import frappe
from frappe.utils import cint

FLAG = "kh_aph_server_cost_guard"


def enabled():
    return bool(cint(frappe.conf.get(FLAG)))


class CostReadGuard:
    def apply_fieldlevel_read_permissions(self):
        super().apply_fieldlevel_read_permissions()
        if not enabled():
            return
        from kh_aph.price_visibility import (
            COST_MASK, PRINT_MASK, _apply_mask, is_cost_restricted,
            is_price_restricted,
        )
        from kh_aph.constants import PR_OPEX

        if is_price_restricted() and not (self.doctype == "Purchase Receipt" and cint(self.get(PR_OPEX))):
            spec = PRINT_MASK.get(self.doctype)
            if spec:
                _apply_mask(self, spec)
        if is_cost_restricted():
            spec = COST_MASK.get(self.doctype)
            if spec:
                _apply_mask(self, spec)


def apply_query_field_permissions():
    """Explicit site-local setup, not after_migrate. Supports native list/value/export paths.

    Only cost fields are elevated. Purchase-price exceptions and raw SQL reports must be
    audited separately; this function does not claim to secure arbitrary endpoints.
    """
    if not enabled():
        frappe.throw("Bật kh_aph_server_cost_guard trên UAT trước khi thiết lập quyền trường.")
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    from kh_aph.price_visibility import COST_MASK, COST_ROLES

    changed = []
    for parent, spec in COST_MASK.items():
        meta = frappe.get_meta(parent)
        groups = [(parent, spec["parent"])]
        for table, fields in spec["tables"].items():
            df = meta.get_field(table)
            if df:
                groups.append((df.options, fields))
        for table in spec["clear"]:
            # Protect the table field itself (e.g. additional_costs).
            groups.append((parent, (table,)))
        for dt, fields in groups:
            for field in fields:
                df = frappe.get_meta(dt).get_field(field)
                if not df:
                    continue
                if cint(df.permlevel) not in (0, 9):
                    frappe.throw(f"{dt}.{field} đã có permlevel khác; cần rà soát trước khi thay đổi.")
                make_property_setter(dt, field, "permlevel", 9, "Int", validate_fields_for_doctype=False)
                changed.append(f"{dt}.{field}")
        # Child field levels inherit permission access from the parent document.
        for role in COST_ROLES:
            if role == "Administrator" or not frappe.db.exists("Role", role):
                continue
            # Preserve default level-0 permissions before the first Custom DocPerm.
            if not frappe.db.exists("Custom DocPerm", {"parent": parent}):
                for row in meta.permissions:
                    values = row.as_dict()
                    for key in ("name", "doctype", "parent", "parenttype", "parentfield", "idx"):
                        values.pop(key, None)
                    frappe.get_doc({"doctype": "Custom DocPerm", "parent": parent,
                                    "parenttype": "DocType", "parentfield": "permissions", **values}).insert()
            filters = {"parent": parent, "role": role, "permlevel": 9}
            if not frappe.db.exists("Custom DocPerm", filters):
                frappe.get_doc({"doctype": "Custom DocPerm", "parenttype": "DocType",
                                "parentfield": "permissions", **filters,
                                "read": 1, "write": 1}).insert()
        frappe.clear_cache(doctype=parent)
    return changed

