"""Nhóm hàng và tài khoản kho (lõi 9xLab).

Tài khoản kho (152/153/154/155/156...) đi theo NHÓM HÀNG (ERPNext v16 bật tồn kho theo mặt hàng). Các quy tắc dưới đây
giữ cho kế toán sửa cây nhóm hàng linh hoạt mà sổ không lệch:

1. Nhóm con mới tạo chưa có tài khoản kho: tự lấy của nhóm cha gần nhất (theo từng công ty).
2. Tạo / lưu mã hàng tồn kho trong nhóm mà cả cây cha không có tài khoản kho nào: cảnh báo (không chặn).
3. Đổi nhóm của mã hàng đã có giao dịch kho: CHO PHÉP nếu tài khoản kho hiệu lực (theo từng công ty) của nhóm cũ và
   nhóm mới giống nhau; KHÔNG cho nếu khác (số dư cũ sẽ kẹt ở tài khoản cũ).
4. Đổi / xóa tài khoản kho của một nhóm khi đã có mã hàng trong nhóm (kể cả nhóm con) phát sinh giao dịch kho ở công ty
   đó: KHÔNG cho.

Phần quy tắc thuần (không cần Frappe) ở đầu tệp để kiểm thử.
"""


def tk_hieu_luc(chuoi: list) -> dict:
    """chuoi: [{công ty: tài khoản}, ...] từ nhóm hiện tại lên gốc. -> {công ty: tài khoản gần nhất} (thuần)."""
    kq = {}
    for muc in chuoi:
        for cty, tk in (muc or {}).items():
            if tk and cty not in kq:
                kq[cty] = tk
    return kq


def khac_tai_khoan(cu: dict, moi: dict) -> dict:
    """{công ty: (tk cũ, tk mới)} ở những công ty mà tài khoản hiệu lực khác nhau (thuần)."""
    return {c: (cu.get(c), moi.get(c)) for c in sorted(set(cu) | set(moi)) if cu.get(c) != moi.get(c)}


def tk_bi_doi(cu: dict, moi: dict) -> dict:
    """Tài khoản khai trực tiếp trên nhóm: {công ty: (cũ, mới)} ở công ty có tài khoản cũ mà bị đổi hoặc bỏ (thuần)."""
    return {c: (tk, moi.get(c)) for c, tk in cu.items() if tk and moi.get(c) != tk}


# --- phần gắn vào Frappe -------------------------------------------------------------------------------------------


def _tk_cua_nhom(nhom: str) -> dict:
    import frappe

    return {r.company: r.default_inventory_account
            for r in frappe.get_all("Item Default", {"parent": nhom, "parenttype": "Item Group"}, ["company", "default_inventory_account"])
            if r.default_inventory_account}


def _chuoi(nhom: str) -> list:
    import frappe

    out, n, gap = [], nhom, set()
    while n and n not in gap:
        gap.add(n)
        out.append(_tk_cua_nhom(n))
        n = frappe.db.get_value("Item Group", n, "parent_item_group")
    return out


def tk_hieu_luc_cua_nhom(nhom: str) -> dict:
    return tk_hieu_luc(_chuoi(nhom))


def item_group_after_insert(doc, method=None):
    """1) Nhóm con mới: thiếu tài khoản kho ở công ty nào thì lấy của nhóm cha gần nhất."""
    import frappe

    if not doc.parent_item_group:
        return
    cha = tk_hieu_luc_cua_nhom(doc.parent_item_group)
    co = _tk_cua_nhom(doc.name)
    for cty, tk in cha.items():
        if cty in co:
            continue
        frappe.get_doc({"doctype": "Item Default", "parenttype": "Item Group", "parentfield": "item_group_defaults",
                        "parent": doc.name, "company": cty, "default_inventory_account": tk}).insert(ignore_permissions=True)


def _co_phat_sinh(nhom: str, cty: str) -> bool:
    import frappe

    lft, rgt = frappe.db.get_value("Item Group", nhom, ["lft", "rgt"])
    return bool(frappe.db.sql(
        """select 1 from `tabStock Ledger Entry` sle join `tabItem` i on i.name = sle.item_code
           join `tabItem Group` g on g.name = i.item_group
           where sle.is_cancelled = 0 and sle.company = %s and g.lft >= %s and g.rgt <= %s limit 1""", (cty, lft, rgt)))


def item_group_validate(doc, method=None):
    """4) Không đổi / bỏ tài khoản kho của nhóm khi mã hàng trong nhóm đã có giao dịch kho ở công ty đó."""
    import frappe

    if doc.is_new():
        return
    cu = _tk_cua_nhom(doc.name)
    moi = {r.company: r.default_inventory_account for r in doc.get("item_group_defaults") or [] if r.default_inventory_account}
    for cty, (a, b) in tk_bi_doi(cu, moi).items():
        if _co_phat_sinh(doc.name, cty):
            frappe.throw(
                f"Nhóm {frappe.bold(doc.name)} đã có mã hàng phát sinh giao dịch kho ở {cty}: không đổi tài khoản kho "
                f"({a} → {b or 'bỏ trống'}). Số dư đang nằm ở {a}; đổi sẽ làm hàng mới ghi sang tài khoản khác và sổ lệch. "
                "Muốn tách: tạo nhóm mới gắn tài khoản mới, tạo mã mới trong nhóm đó và chuyển tồn bằng phiếu kho.",
                title="Không đổi tài khoản kho của nhóm hàng",
            )


def item_validate(doc, method=None):
    """3) Đổi nhóm mã hàng đã có giao dịch kho: chỉ cho khi tài khoản kho hiệu lực như nhau. 2) Cảnh báo nhóm không có tài khoản kho."""
    import frappe

    if doc.get("is_stock_item") and doc.get("item_group") and not tk_hieu_luc_cua_nhom(doc.item_group):
        frappe.msgprint(
            f"Nhóm {frappe.bold(doc.item_group)} (và các nhóm cha) chưa gắn tài khoản kho: hàng sẽ ghi vào tài khoản kho "
            "mặc định của công ty. Nếu đây là nguyên liệu, thành phẩm, công cụ... hãy chọn nhóm đúng hoặc gắn tài khoản kho cho nhóm.",
            title="Nhóm hàng chưa có tài khoản kho", indicator="orange",
        )
    if doc.is_new() or not doc.has_value_changed("item_group"):
        return
    truoc = doc.get_doc_before_save()
    cu_nhom = truoc.item_group if truoc else None
    if not cu_nhom or not frappe.db.exists("Stock Ledger Entry", {"item_code": doc.name, "is_cancelled": 0}):
        return
    khac = khac_tai_khoan(tk_hieu_luc_cua_nhom(cu_nhom), tk_hieu_luc_cua_nhom(doc.item_group))
    if khac:
        chi_tiet = "; ".join(f"{c}: {a or 'mặc định công ty'} → {b or 'mặc định công ty'}" for c, (a, b) in khac.items())
        frappe.throw(
            f"Mã {frappe.bold(doc.name)} đã có giao dịch kho: không chuyển từ nhóm {cu_nhom} sang {doc.item_group} vì "
            f"tài khoản kho khác nhau ({chi_tiet}). Chuyển sang nhóm cùng tài khoản thì được. Muốn đổi loại hàng: "
            "tạo mã mới ở nhóm đúng và chuyển tồn bằng phiếu kho (đổi mã).",
            title="Không đổi nhóm hàng",
        )
