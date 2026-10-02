"""Kho dùng chung theo địa điểm (0.4.17).

Kho bán hàng và các kho vệ tinh ở Hà Nội, Đà Nẵng, TP Hồ Chí Minh là kho vật lý DÙNG CHUNG của APH, VH và HKD Minh Khang.
Hàng trong kho vẫn thuộc từng pháp nhân, nên trong ERPNext mỗi pháp nhân có một bộ kho cùng tên (đuôi viết tắt khác nhau):
  "Kho bán hàng Hà Nội - APH", "Kho bán hàng Hà Nội - VH", "Kho bán hàng Hà Nội - MK" ...
Tồn, giá vốn từng pháp nhân tính riêng; thủ kho nhìn cùng một địa điểm, chọn đúng công ty trên chứng từ.

Cây kho mẫu lấy từ APH (nhóm Hà Nội / Đà Nẵng / Hồ Chí Minh và kho con đang dùng + kho Hàng đang vận chuyển);
không chép kho nhà máy. APH chưa có cây này thì dùng cây mặc định CAY_MAC_DINH.

Chạy: bench --site <site> execute aphvh.kho_chung.setup --kwargs '{"company": "Vĩnh Hưng", "mau": "APH"}'
Chạy lại an toàn: kho đã có (theo tên) thì không tạo trùng; kho cùng tên đang tắt thì bật lại; không xóa kho nào.
"""

DIA_DIEM = ("Hà Nội", "Đà Nẵng", "Hồ Chí Minh")
TRANSIT = "Hàng đang vận chuyển"

# (tên kho, tên nhóm cha | None = gốc, là nhóm, loại kho)
CAY_MAC_DINH = [
    ("Hà Nội", None, 1, ""),
    ("Kho bán hàng Hà Nội", "Hà Nội", 0, ""),
    ("Hàng chờ xử lý Hà Nội", "Hà Nội", 0, ""),
    ("Đà Nẵng", None, 1, ""),
    ("Kho Đà Nẵng", "Đà Nẵng", 0, ""),
    ("Hồ Chí Minh", None, 1, ""),
    ("Kho Hồ Chí Minh", "Hồ Chí Minh", 0, ""),
    (TRANSIT, None, 0, "Transit"),
]


def cay_mau(rows: list) -> list:
    """rows: kho của công ty mẫu [{warehouse_name, parent_name, is_group, disabled, warehouse_type}] (parent_name = tên nhóm cha,
    None nếu nằm ngay dưới gốc). -> cây cần chép theo thứ tự cha trước con (thuần, kiểm thử không cần Frappe)."""
    by = {r["warehouse_name"]: r for r in rows}

    def dinh(r):  # nhóm cấp 1 chứa kho này
        while r.get("parent_name") and r["parent_name"] in by:
            r = by[r["parent_name"]]
        return r["warehouse_name"]

    out = []
    for r in rows:
        if r.get("disabled"):
            continue
        if dinh(r) in DIA_DIEM or (r.get("warehouse_type") == "Transit" and not r.get("parent_name")):
            out.append((r["warehouse_name"], r.get("parent_name"), int(r.get("is_group") or 0), r.get("warehouse_type") or ""))
    if not any(n in DIA_DIEM for n, *_ in out):
        return list(CAY_MAC_DINH)
    if not any(t == "Transit" for *_, t in out):
        out.append((TRANSIT, None, 0, "Transit"))

    # cha trước con
    ten = {n for n, *_ in out}
    xep, da = [], set()
    while len(xep) < len(out):
        truoc = len(xep)
        for k in out:
            if k[0] not in da and (not k[1] or k[1] in da or k[1] not in ten):
                xep.append(k); da.add(k[0])
        if len(xep) == truoc:  # vòng lặp cha-con hỏng: thêm nốt
            xep += [k for k in out if k[0] not in da]; break
    return xep


def plan(cay: list, dich: dict) -> list:
    """dich: {tên kho: {"disabled": 0/1}} của công ty đích -> việc ("tao", kho) | ("bat", tên) (thuần)."""
    jobs = []
    for k in cay:
        d = dich.get(k[0])
        if d is None:
            jobs.append(("tao", k))
        elif d.get("disabled"):
            jobs.append(("bat", k[0]))
    return jobs


def _rows(company):
    import frappe

    ws = frappe.get_all("Warehouse", {"company": company},
                        ["name", "warehouse_name", "parent_warehouse", "is_group", "disabled", "warehouse_type"])
    ten = {w.name: w.warehouse_name for w in ws}
    goc = {w.name for w in ws if not w.parent_warehouse}
    return [{"name": w.name, "warehouse_name": w.warehouse_name, "is_group": w.is_group, "disabled": w.disabled,
             "warehouse_type": w.warehouse_type,
             "parent_name": None if (not w.parent_warehouse or w.parent_warehouse in goc) else ten.get(w.parent_warehouse)}
            for w in ws if w.name not in goc]


def setup(company: str, mau: str = "APH") -> dict:
    """company: tên hoặc viết tắt công ty đích; mau: tên hoặc viết tắt công ty mẫu (mặc định APH)."""
    import frappe

    def ten_cty(x):
        return x if frappe.db.exists("Company", x) else frappe.db.get_value("Company", {"abbr": x}, "name")

    co, co_mau = ten_cty(company), ten_cty(mau)
    if not co:
        frappe.throw(f"Không có công ty {company}")
    abbr = frappe.db.get_value("Company", co, "abbr")
    cay = cay_mau(_rows(co_mau)) if co_mau and co_mau != co else list(CAY_MAC_DINH)
    hien = {r["warehouse_name"]: r for r in _rows(co)}
    goc = frappe.db.get_value("Warehouse", {"company": co, "is_group": 1, "parent_warehouse": ["in", ("", None)]}, "name")
    viec = []
    for job in plan(cay, hien):
        if job[0] == "bat":
            frappe.db.set_value("Warehouse", hien[job[1]]["name"], "disabled", 0)
            viec.append(f"bật lại {job[1]}")
            continue
        n, cha, nhom, loai = job[1]
        cha_name = frappe.db.get_value("Warehouse", {"company": co, "warehouse_name": cha}, "name") if cha else goc
        d = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": n, "company": co, "is_group": nhom,
                            "parent_warehouse": cha_name or goc, "warehouse_type": loai or None})
        d.flags.ignore_inventory_account_validation = True
        d.insert(ignore_permissions=True)
        viec.append(f"tạo {d.name}")
    # kho vận chuyển mặc định cho công ty và mọi kho
    tr = frappe.db.get_value("Warehouse", {"company": co, "warehouse_type": "Transit", "is_group": 0, "disabled": 0}, "name")
    if tr:
        if frappe.get_meta("Company").has_field("default_in_transit_warehouse"):
            frappe.db.set_value("Company", co, "default_in_transit_warehouse", tr)
        for w in frappe.get_all("Warehouse", {"company": co, "is_group": 0, "disabled": 0, "name": ["!=", tr],
                                              "default_in_transit_warehouse": ["in", ("", None)]}, pluck="name"):
            frappe.db.set_value("Warehouse", w, "default_in_transit_warehouse", tr)
    frappe.db.commit()
    kho = frappe.get_all("Warehouse", {"company": co, "is_group": 0, "disabled": 0}, pluck="name", order_by="lft")
    return {"cong_ty": co, "viet_tat": abbr, "mau": co_mau, "viec": viec, "kho": kho}
