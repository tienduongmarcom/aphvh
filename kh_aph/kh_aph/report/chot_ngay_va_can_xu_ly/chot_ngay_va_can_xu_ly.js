frappe.query_reports["Chot ngay va can xu ly"] = {filters: [
  {fieldname:"company", label:__("Đơn vị"), fieldtype:"Link", options:"Company", reqd:1, default:frappe.defaults.get_user_default("Company")},
  {fieldname:"day", label:__("Ngày đối chiếu"), fieldtype:"Date", reqd:1, default:frappe.datetime.get_today()}
]};
