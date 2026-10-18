app_name = "kh_aph"
app_title = "APH - VH"
app_publisher = "9xLab"
app_description = "App riêng của khách An Phú Hưng - Vĩnh Hưng, chạy trên lõi 9xLab (lab9x)"
app_email = "tienduongmarcom@gmail.com"
app_license = "Proprietary"

required_apps = ["erpnext", "lab9x"]  # lõi dùng chung 9xLab

# Cài đặt cấu hình (custom field, loại phiếu kho) — chạy lại được nhiều lần
after_install = "kh_aph.install.after_install"
before_migrate = ["kh_aph.install.before_migrate"]
after_migrate = ["kh_aph.install.after_migrate"]

# Mở rộng lớp Stock Entry: chia giá thành phẩm theo kg cho loại phiếu "Đóng gói theo kg".
# Cơ chế extend_doctype_class của Frappe v16 ghép lớp này TRƯỚC lớp chuẩn trong MRO;
# repost nạp phiếu qua cùng lớp đã ghép nên quy tắc vẫn chạy khi tính lại giá.
extend_doctype_class = {
    "Stock Entry": ["kh_aph.stock_entry_kg.StockEntryKgCosting", "kh_aph.server_cost_guard.CostReadGuard"],
    "Purchase Receipt": ["kh_aph.server_cost_guard.CostReadGuard"],
    "Purchase Order": ["kh_aph.server_cost_guard.CostReadGuard"],
    "Serial and Batch Bundle": ["kh_aph.server_cost_guard.CostReadGuard"],
    "Item": ["kh_aph.server_cost_guard.CostReadGuard"],
    "Sales Order": ["kh_aph.server_cost_guard.CostReadGuard"],
    "Delivery Note": ["kh_aph.server_cost_guard.CostReadGuard"],
}

# --- 0.2: phân quyền nhà máy, ẩn giá (mức màn hình + báo cáo), mẫu in Việt Nam ------------

# Cho trình duyệt biết người dùng có bị ẩn giá không và nhóm hàng nhà máy được tự nhập giá.
boot_session = ["kh_aph.price_visibility.boot_session"]

# Phiếu nhập: vật tư vận hành chỉ nhận nhóm hàng được tích; người bị ẩn giá nhận nguyên phụ liệu
# phải lấy từ đơn mua.
# before_print: xóa giá trên bản in (mọi mẫu, kể cả Standard) với người bị ẩn giá.
_BLANK = "kh_aph.price_visibility.blank_prices_for_print"
_PD = "kh_aph.controls.validate_posting_date"
_VAT = "kh_aph.vat.before_validate_sales"
_VAT_MUA = "kh_aph.vat.before_validate_purchase"  # chỉ gắn dòng thuế 1331, không chọn thuế suất
_TK_THUE = "kh_aph.vat.validate_tai_khoan_thue"  # chặn nhầm 33311 trên phiếu mua / 1331 trên phiếu bán

doc_events = {
    "Purchase Receipt": {
        "before_validate": _VAT_MUA,
        "validate": ["kh_aph.price_visibility.validate_purchase_receipt", _PD, _TK_THUE],
        "before_print": _BLANK,
    },
    "Purchase Order": {"before_validate": _VAT_MUA, "validate": _TK_THUE, "before_print": _BLANK},
    "Stock Entry": {"validate": _PD, "before_print": _BLANK},
    "Stock Reconciliation": {"validate": _PD},
    "Serial and Batch Bundle": {"before_print": _BLANK},
    # Đổi nhóm hàng / tài khoản kho của nhóm: quy tắc ở lõi lab9x (lab9x/nhom_hang.py).
    "Item": {"before_print": _BLANK},
    # 0.3: cảnh báo công nợ/giá khi lưu và xác nhận đơn; hóa đơn nháp tự tạo từ phiếu giao hàng;
    # thủ kho chỉ giao theo đơn; ẩn giá vốn trên bản in với nhân viên bán hàng, thủ kho.
    # 0.3.1: có/không xuất hóa đơn GTGT (Không = bỏ thuế) chạy trước cảnh báo công nợ.
    # 0.3.5: thuế GTGT theo loại khách — chọn mẫu thuế mặt hàng trước validate của ERPNext.
    "Customer": {"validate": "kh_aph.vat.validate_customer"},
    "Sales Order": {
        "before_validate": _VAT,
        "validate": ["kh_aph.invoice_flag.apply_invoice_flag", "kh_aph.sales_warnings.validate_sales_order", _TK_THUE],
        "before_print": _BLANK,
    },
    "Delivery Note": {
        "before_validate": _VAT,
        "validate": ["kh_aph.invoice_flag.apply_invoice_flag", "kh_aph.sales_flow.validate_delivery_note", _PD, _TK_THUE],
        "on_submit": "kh_aph.sales_flow.make_draft_invoice",
        "on_cancel": "kh_aph.sales_flow.remove_draft_invoices",
        "before_print": _BLANK,
    },
    # 0.3.4: khách vãng lai chung chỉ bán thu tiền ngay (tự lập phiếu thu); chặn ngày tương lai.
    "Sales Invoice": {
        "before_validate": _VAT,
        "validate": [
            "kh_aph.invoice_flag.apply_invoice_flag",
            "kh_aph.invoice_flag.validate_einvoice",
            "kh_aph.controls.validate_sales_invoice",
            _TK_THUE,
        ],
        "on_submit": "kh_aph.controls.sales_invoice_on_submit",
        "before_update_after_submit": "kh_aph.invoice_flag.validate_einvoice",
    },
    # 0.3.4: không ghi tay vào tài khoản kho; cảnh báo tiền mặt lớn, tiền trả trước chưa gắn đơn.
    "Journal Entry": {"validate": ["kh_aph.controls.validate_journal_entry", "kh_aph.thu_ho.validate", _PD],
                      "before_update_after_submit": "kh_aph.thu_ho.before_update_after_submit"},
    "Payment Entry": {"validate": "kh_aph.controls.validate_payment_entry", "before_update_after_submit": "kh_aph.controls.before_update_after_submit_payment_entry"},
    "Purchase Invoice": {"before_validate": _VAT_MUA, "validate": ["kh_aph.controls.validate_purchase_invoice", _TK_THUE]},
}

# 0.3: nhân viên bán hàng chỉ thấy giá của bảng giá bán.
permission_query_conditions = {
    "Item Price": "kh_aph.price_visibility.item_price_query_conditions",
}
has_permission = {
    "Item Price": "kh_aph.price_visibility.item_price_has_permission",
}

# Xem trước sổ cái / sổ kho trên phiếu nháp lộ giá vốn: chặn với người bị ẩn giá vốn.
override_whitelisted_methods = {
    "erpnext.controllers.stock_controller.show_accounting_ledger_preview":
        "kh_aph.price_visibility.show_accounting_ledger_preview",
    "erpnext.controllers.stock_controller.show_stock_ledger_preview":
        "kh_aph.price_visibility.show_stock_ledger_preview",
}

# Ẩn cột giá trên màn hình với vai trò "Kế toán nhà máy" (không cần build asset).
doctype_js = {
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Item": "public/js/item.js",
    "Serial and Batch Bundle": "public/js/serial_and_batch_bundle.js",
    "Sales Order": "public/js/sales_order.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Customer": "public/js/customer.js",
}
doctype_list_js = {
    "Purchase Receipt": "public/js/purchase_receipt_list.js",
    "Purchase Order": "public/js/purchase_order_list.js",
}

# Hàm dùng trong mẫu in Phiếu nhập kho / Phiếu kho / phiếu xuất kho bán hàng, biên bản giao nhận.
jinja = {
    "methods": [
        "kh_aph.print_utils.kh_aph_an_gia",
        "kh_aph.print_utils.kh_aph_no_co",
        "kh_aph.print_utils.kh_aph_ngay",
        "kh_aph.print_utils.kh_aph_so",
        "kh_aph.print_utils.kh_aph_bang_chu",
        "kh_aph.print_utils.kh_aph_cong_ty",
        "kh_aph.print_utils.kh_aph_ten_nguoi",
        "kh_aph.print_utils.kh_aph_sl_chung_tu",
        "kh_aph.print_utils.kh_aph_ten_kho",
        "kh_aph.print_utils.kh_aph_sl_don_ban",
        "kh_aph.print_utils.kh_aph_dia_chi",
        "kh_aph.print_utils.kh_aph_mau",
        "kh_aph.print_utils.kh_aph_loai_phieu_kho",
        "kh_aph.print_utils.kh_aph_thu_chi",
        "kh_aph.print_utils.kh_aph_ban_hang",
        "kh_aph.print_utils.kh_aph_lo",
        "kh_aph.print_utils.kh_aph_gia_gom_thue",
    ],
}

# APHVH UAT child query correction v1
override_whitelisted_methods.update({
    "frappe.client.get_list": "kh_aph.cost_query_api.get_list",
    "frappe.client.get_value": "kh_aph.cost_query_api.get_value",
})

# UAT_GLOBAL_CREDIT_WARNING_V1
_credit_dn = doc_events.setdefault("Delivery Note", {})
_credit_validate = _credit_dn.get("validate", [])
if isinstance(_credit_validate, str):
    _credit_validate = [_credit_validate]
else:
    _credit_validate = list(_credit_validate)
if "kh_aph.global_credit.validate_delivery" not in _credit_validate:
    _credit_validate.append("kh_aph.global_credit.validate_delivery")
_credit_dn["validate"] = _credit_validate

# UAT_HIGH_RISK_CREDIT_V1
for _dt,_event,_handler in (
    ("Customer","validate","kh_aph.credit_release.validate_customer"),
    ("Delivery Note","before_submit","kh_aph.credit_release.before_submit_delivery"),
    ("APH Credit Release","validate","kh_aph.credit_release.validate_release"),
    ("APH Credit Release","on_trash","kh_aph.credit_release.prevent_release_delete"),
):
    _events=doc_events.setdefault(_dt,{})
    _handlers=_events.get(_event,[])
    _handlers=[_handlers] if isinstance(_handlers,str) else list(_handlers)
    if _handler not in _handlers: _handlers.append(_handler)
    _events[_event]=_handlers

# UAT_SI_BYPASS_GUARD_V1
_si_events=doc_events.setdefault("Sales Invoice",{})
_si_handlers=_si_events.get("before_submit",[])
_si_handlers=[_si_handlers] if isinstance(_si_handlers,str) else list(_si_handlers)
if "kh_aph.credit_release.before_submit_invoice" not in _si_handlers:
    _si_handlers.append("kh_aph.credit_release.before_submit_invoice")
_si_events["before_submit"]=_si_handlers

# Opt-in delivery states share the atomic dispatch flag.
for _event in ('validate', 'before_submit', 'before_update_after_submit'):
    _events = doc_events.setdefault('Delivery Note', {})
    _handlers = _events.get(_event, [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    _handler = 'kh_aph.delivery_status.' + _event
    if _handler not in _handlers:
        _handlers.append(_handler)
    _events[_event] = _handlers

# Explicit Dũng deny profile. Native permissions remain required on allowed paths.
auth_hooks = ["kh_aph.dung_cost_policy.before_request",
              # 0.11.0: chặn lối in/xem trước bỏ qua bước xóa giá (mọi người bị ẩn giá)
              "kh_aph.print_guard.before_request"]
for _dt in ("Bin", "Stock Ledger Entry", "GL Entry", "Purchase Invoice",
            "Landed Cost Voucher", "Stock Reconciliation", "BOM", "Work Order",
            "Repost Item Valuation"):
    has_permission[_dt] = "kh_aph.dung_cost_policy.has_permission"
    permission_query_conditions[_dt] = "kh_aph.dung_cost_policy.query_conditions"
after_request = ["kh_aph.dung_cost_policy.after_request"]
for _dt in ("Stock Closing Entry", "Stock Closing Balance"):
    has_permission[_dt] = "kh_aph.dung_cost_policy.closing_has_permission"
    permission_query_conditions[_dt] = "kh_aph.dung_cost_policy.closing_query_conditions"

# Opt-in quantity/pending-valuation MVP; same native transaction owns all ledgers.
extend_doctype_class["Landed Cost Voucher"] = ["kh_aph.landed_cost_kg.LandedCostKg"]
for _dt in ("Stock Entry", "Purchase Receipt", "Delivery Note", "Sales Invoice", "Purchase Invoice"):
    for _event, _handler in (("before_validate", "kh_aph.bag_stock.validate"),
                             ("on_submit", "kh_aph.bag_stock.post"),
                             ("on_cancel", "kh_aph.bag_stock.reverse")):
        _events = doc_events.setdefault(_dt, {})
        _handlers = _events.get(_event, [])
        _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
        if _handler not in _handlers:
            _handlers.append(_handler)
        _events[_event] = _handlers
for _dt, _handler in (("Item", "kh_aph.bag_stock.validate_item"),
                       ("Sales Order", "kh_aph.bag_stock.validate"),
                       ("Stock Reconciliation", "kh_aph.bag_stock.validate")):
    _events = doc_events.setdefault(_dt, {})
    _handlers = _events.get("before_validate", [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    _handlers.append(_handler)
    _events["before_validate"] = _handlers
doc_events["APH Bag Movement"] = {"validate": "kh_aph.bag_stock.protect", "on_trash": "kh_aph.bag_stock.protect"}

for _dt in ("Stock Entry", "Purchase Receipt", "Purchase Invoice"):
    _handlers = doc_events[_dt].get("validate", [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    _handlers.append("kh_aph.bag_stock.validate_valued_receipt")
    doc_events[_dt]["validate"] = _handlers

doc_events["Purchase Receipt"]["validate"].append("kh_aph.pending_valuation.validate_link")

# Explicit quantity UI only when the UAT quantity flag is enabled.
boot_session.append("kh_aph.bag_stock.boot_session")
for _dt in ("Stock Entry", "Purchase Receipt", "Purchase Invoice", "Sales Order", "Delivery Note", "Sales Invoice", "APH Shared Sales Order", "APH Pending Receipt"):
    _scripts = doctype_js.get(_dt, [])
    if isinstance(_scripts, str):
        _scripts = [_scripts]
    doctype_js[_dt] = _scripts + ["public/js/bag_quantity.js"]
doctype_js["APH Pending Receipt"].append("public/js/pending_receipt.js")

# Explicit money/deposit plans: native JE owns GL; no automatic bank movement.
for _dt in ("APH Funds Route", "APH Funds Receipt", "APH Funds Action"):
    has_permission[_dt] = "kh_aph.funds.has_permission"
    permission_query_conditions[_dt] = "kh_aph.funds.query_conditions"
for _event in ("validate", "before_cancel", "before_update_after_submit"):
    _handlers = doc_events.setdefault("Journal Entry", {}).get(_event, [])
    if isinstance(_handlers, str): _handlers = [_handlers]
    doc_events["Journal Entry"][_event] = _handlers + ["kh_aph.funds.protect_journal"]
_handlers = doc_events["Payment Entry"]["validate"]
if isinstance(_handlers, str): _handlers = [_handlers]
doc_events["Payment Entry"]["validate"] = _handlers + ["kh_aph.funds.guard_native_order_advance"]

# Quantity-only source changes, preserving native cancellation and delivery guards.
for _dt, _event, _method in (("Sales Order","on_cancel","coordinator_links"),("Sales Order","on_change","prevent_reopen"),("Delivery Note","before_submit","lock_delivery_sources")):
    _handlers = doc_events.setdefault(_dt,{}).get(_event,[])
    if isinstance(_handlers,str): _handlers=[_handlers]
    doc_events[_dt][_event]=_handlers+["kh_aph.source_change."+_method]

# 0.11.1 (cờ kh_aph_factory_costing): giá tạm cho hàng nhà máy (R064). Hệ số phẩm cấp, xưởng, lệch kg đóng gói lại
# nằm trong stock_entry_kg (quy tắc kg-v4); phân bổ cuối tháng và vét bồn là thao tác kế toán gọi tay.
for _dt in ("Purchase Order", "Purchase Receipt", "Stock Reconciliation"):
    _handlers = doc_events.setdefault(_dt, {}).get("validate", [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    if "kh_aph.factory_costing.validate_gia_tam" not in _handlers:
        _handlers.append("kh_aph.factory_costing.validate_gia_tam")
    doc_events[_dt]["validate"] = _handlers

# 0.11.1 (cờ kh_aph_factory_cash): khóa giá thành phẩm chính khi người vận hành nhà máy bán (R091, Q138).
for _dt in ("Sales Order", "Sales Invoice", "Delivery Note", "APH Shared Sales Order"):
    _handlers = doc_events.setdefault(_dt, {}).get("validate", [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    if "kh_aph.factory_cash.validate_khoa_gia" not in _handlers:
        _handlers.append("kh_aph.factory_cash.validate_khoa_gia")
    doc_events[_dt]["validate"] = _handlers

# 0.11.1 (cờ kh_aph_sales_adjust): loại điều chỉnh trên chứng từ trả lại/giảm (R022/R024); cảnh báo dưới giá vốn chỉ cho
# kế toán (R011/R084); hàm in biên bản giao nhận (Q192/Q198/R053/Q199).
for _dt, _handler in (("Delivery Note", "kh_aph.sales_adjust.validate_dieu_chinh"),
                      ("Sales Invoice", "kh_aph.sales_adjust.validate_dieu_chinh"),
                      ("Sales Order", "kh_aph.sales_adjust.canh_bao_gia_von"),
                      ("APH Shared Sales Order", "kh_aph.sales_adjust.canh_bao_gia_von")):
    _handlers = doc_events.setdefault(_dt, {}).get("validate", [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    if _handler not in _handlers:
        _handlers.append(_handler)
    doc_events[_dt]["validate"] = _handlers
jinja["methods"] += ["kh_aph.print_utils.kh_aph_bbgn_an_gia", "kh_aph.print_utils.kh_aph_sl_hien_thi",
                     "kh_aph.print_utils.kh_aph_thuc_nhan"]

# 0.11.1: nút Dialog (chỉ hiện khi cờ bật).
for _dt in ("Delivery Note", "APH Shared Sales Order", "Warehouse"):
    _scripts = doctype_js.get(_dt, [])
    _scripts = [_scripts] if isinstance(_scripts, str) else list(_scripts)
    doctype_js[_dt] = _scripts + ["public/js/ban_0111.js"]
doctype_list_js["Landed Cost Voucher"] = "public/js/ban_0111_lcv_list.js"

# 0.11.2 (cờ kh_aph_kho_chuan): cây kho chuẩn, chặn bán từ kho không bán, quyết toán dở dang theo định mức, kiểm kê có mốc.
for _dt, _handler in (("Sales Order", "kh_aph.kho_chuan.validate_kho_ban"),
                      ("APH Shared Sales Order", "kh_aph.kho_chuan.validate_kho_ban"),
                      ("Delivery Note", "kh_aph.kho_chuan.validate_kho_ban"),
                      ("Sales Invoice", "kh_aph.kho_chuan.validate_kho_ban"),
                      ("Warehouse", "kh_aph.kho_chuan.validate_kho")):
    _handlers = doc_events.setdefault(_dt, {}).get("validate", [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    if _handler not in _handlers:
        _handlers.append(_handler)
    doc_events[_dt]["validate"] = _handlers
doctype_js["Warehouse"] = list(doctype_js["Warehouse"]) + ["public/js/ban_0112.js"]

# 0.11.3 (cờ kh_aph_sales_p1): trả hàng 2 chiều, giảm giá sau giao, hạn thanh toán chung, đổi địa chỉ, hồ sơ hóa đơn MISA.
for _dt, _event, _handler in (("Delivery Note", "validate", "kh_aph.sales_p1.validate_tra_hang"),
                              ("Delivery Note", "on_submit", "kh_aph.sales_p1.sau_ghi_tra_hang"),
                              ("Sales Invoice", "on_submit", "kh_aph.sales_p1.sau_ghi_hoa_don_giam"),
                              ("Sales Order", "validate", "kh_aph.sales_p1.validate_don")):
    _handlers = doc_events.setdefault(_dt, {}).get(_event, [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    if _handler not in _handlers:
        _handlers.append(_handler)
    doc_events[_dt][_event] = _handlers
for _dt in ("Sales Order", "Delivery Note", "Sales Invoice"):
    _scripts = doctype_js.get(_dt, [])
    _scripts = [_scripts] if isinstance(_scripts, str) else list(_scripts)
    doctype_js[_dt] = _scripts + ["public/js/ban_0113.js"]

# 0.11.4 (cờ kh_aph_quan_tri): cảnh báo mềm xác nhận công nợ (R039); nút khóa kỳ / xác nhận công nợ.
_handlers = doc_events.setdefault("Sales Order", {}).get("validate", [])
_handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
if "kh_aph.quan_tri.canh_bao_xac_nhan" not in _handlers:
    _handlers.append("kh_aph.quan_tri.canh_bao_xac_nhan")
doc_events["Sales Order"]["validate"] = _handlers
for _dt in ("Customer", "Company"):
    _scripts = doctype_js.get(_dt, [])
    _scripts = [_scripts] if isinstance(_scripts, str) else list(_scripts)
    doctype_js[_dt] = _scripts + ["public/js/ban_0114.js"]

# 0.12.0 (cờ kh_aph_du_lieu): Trung tâm dữ liệu, đề nghị cập nhật số liệu có duyệt.
# 0.12.1 (cờ kh_aph_dau_ky): số dư đầu kỳ theo bảng nguồn, báo cáo đối chiếu, chốt.
has_permission["APH De nghi so lieu"] = "kh_aph.du_lieu.has_permission"
has_permission["APH So du dau ky nguon"] = "kh_aph.dau_ky.has_permission"
permission_query_conditions["APH So du dau ky nguon"] = "kh_aph.dau_ky.query_conditions"

# Lượt 0.13 (cờ kh_aph_kho_van_hanh, kh_aph_gia_san): kho vận hành, giá sàn, quầy bán hàng.
jinja["methods"] += ["kh_aph.print_utils.kh_aph_doi_soat"]
has_permission["APH Gia san"] = "kh_aph.ban_quay.has_permission"
for _dt in ("Sales Order", "Sales Invoice"):
    for _event, _handler in (("validate", "kh_aph.ban_quay.validate"), ("before_submit", "kh_aph.ban_quay.before_submit")):
        _handlers = doc_events.setdefault(_dt, {}).get(_event, [])
        _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
        if _handler not in _handlers:
            _handlers.append(_handler)
        doc_events[_dt][_event] = _handlers
for _dt in ("Delivery Note", "Sales Order", "Sales Invoice", "Customer"):
    _scripts = doctype_js.get(_dt, [])
    _scripts = [_scripts] if isinstance(_scripts, str) else list(_scripts)
    doctype_js[_dt] = _scripts + (["public/js/kho_013.js"] if _dt == "Delivery Note" else []) + ["public/js/quay_013.js"]

# Lượt 0.14 (cờ kh_aph_trung_tam_ban, kh_aph_tien_vay): Trung tâm Bán hàng, tiền và vay.
jinja["methods"] += ["kh_aph.print_utils.kh_aph_so_hoa_don_misa"]
has_permission["APH Khe uoc vay"] = "kh_aph.tien_vay.has_permission"
for _dt, _event, _handler in (("APH Shared Sales Order", "validate", "kh_aph.trung_tam_ban.validate_chung"),
                              ("APH Shared Sales Order", "before_submit", "kh_aph.trung_tam_ban.before_submit_chung"),
                              ("APH Shared Sales Order", "on_submit", "kh_aph.trung_tam_ban.on_submit_chung"),
                              ("Journal Entry", "validate", "kh_aph.tien_vay.validate_but_toan")):
    _handlers = doc_events.setdefault(_dt, {}).get(_event, [])
    _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
    if _handler not in _handlers:
        _handlers.append(_handler)
    doc_events[_dt][_event] = _handlers
for _dt, _js in (("APH Shared Sales Order", "public/js/ban_014.js"), ("Delivery Note", "public/js/ban_014.js"),
                 ("Bank Account", "public/js/tien_014.js")):
    _scripts = doctype_js.get(_dt, [])
    _scripts = [_scripts] if isinstance(_scripts, str) else list(_scripts)
    doctype_js[_dt] = _scripts + [_js]
# 0.14 (cờ kh_aph_sales_adjust, thay Q176): mã khách / nhà cung cấp đưa vào giữ nguyên.
for _dt in ("Customer", "Supplier"):
    for _event, _handler in (("autoname", "kh_aph.sales_adjust.dat_ma"), ("validate", "kh_aph.sales_adjust.giu_ma")):
        _handlers = doc_events.setdefault(_dt, {}).get(_event, [])
        _handlers = [_handlers] if isinstance(_handlers, str) else list(_handlers)
        if _handler not in _handlers:
            _handlers.append(_handler)
        doc_events[_dt][_event] = _handlers

# Hồ sơ giao nhận dùng cờ Trung tâm Bán hàng và quyền phiếu giao hiện có.
for _event in ("validate", "before_update_after_submit"):
    doc_events["Delivery Note"].setdefault(_event, []).append("kh_aph.ho_so_giao_nhan.validate")
extend_doctype_class.setdefault("File", []).append("kh_aph.ho_so_giao_nhan.HoSoFileMixin")
doc_events.setdefault("File", {})["before_validate"] = "kh_aph.ho_so_giao_nhan.protect_file_update"

# Chống ghi hai lần một mã thực thu/chi qua PE, JE và phiếu tiền/cọc.
for _dt in ("Payment Entry", "Journal Entry"):
    doc_events[_dt]["validate"].append("kh_aph.money_reference.validate")

# Thông tin giao nhận theo đợt; giá/kho/công nợ vẫn qua controller chuẩn.
for _event in ("before_validate", "before_update_after_submit"):
    doc_events["Delivery Note"].setdefault(_event, []).append("kh_aph.delivery_info.validate")
doc_events["Delivery Note"].setdefault("before_submit", []).append("kh_aph.delivery_info.before_submit")

# Hồ sơ chênh lệch gắn phiếu nguồn, dùng cờ Trung tâm Bán hàng hiện có.
for _event in ("before_validate", "before_update_after_submit"):
    doc_events["Delivery Note"].setdefault(_event, []).append("kh_aph.delivery_issue.validate")
for _dt in ("Delivery Note", "Sales Invoice"):
    doc_events.setdefault(_dt, {}).setdefault("before_cancel", []).append("kh_aph.delivery_issue.before_cancel")
doctype_js["Delivery Note"].append("public/js/chenh_lech_giao_nhan.js")
