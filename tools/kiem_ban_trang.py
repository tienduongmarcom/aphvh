# Kiểm bộ cài bản trắng (0.5.2) trên site TRẮNG trang2.localhost: công ty viết tắt thật APH / VH. Chỉ làm trên site này.
import sys, json, datetime, frappe
site, out = sys.argv[1:3]
frappe.init(site=site, sites_path="."); frappe.connect(); frappe.set_user("Administrator")
R = []
def ok(ma, dat, ghi=""):
    R.append((ma, "ĐẠT" if dat else "KHÔNG ĐẠT", str(ghi))); print(ma, "ĐẠT" if dat else "KHÔNG ĐẠT", ghi)
import aphvh
from aphvh import cai_ban_trang as C, tai_khoan_chuan as T
from aphvh.bang_tai_khoan import bang
print("   phiên bản aphvh", aphvh.__version__)
print("   số công ty có sẵn:", frappe.db.count("Company"))
if not frappe.is_setup_complete():
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
    y = datetime.date.today().year
    setup_complete({"language": "vi", "country": "Vietnam", "timezone": "Asia/Ho_Chi_Minh", "currency": "VND", "full_name": "Quản trị",
                    "company_name": "APH Bản Trắng", "company_abbr": "APH", "chart_of_accounts": "Standard",
                    "fy_start_date": f"{y}-01-01", "fy_end_date": f"{y}-12-31", "company_tagline": "thử", "bank_account": "Tiền gửi ngân hàng"})
    frappe.db.commit()
ok("B0b bước thiết lập ban đầu xong", frappe.is_setup_complete())
cty = {"APH": frappe.db.get_value("Company", {"abbr": "APH"}, "name") or "APH Bản Trắng"}
if not frappe.db.exists("Company", {"abbr": "VH"}):
    frappe.get_doc({"doctype": "Company", "company_name": "VH Bản Trắng", "abbr": "VH", "default_currency": "VND", "country": "Vietnam",
                    "create_chart_of_accounts_based_on": "Standard Template", "chart_of_accounts": "Standard"}).insert(ignore_permissions=True)
    frappe.db.commit()
cty["VH"] = frappe.db.get_value("Company", {"abbr": "VH"}, "name")
for ab, co in cty.items():
    loai = ab.lower()
    n0 = frappe.db.count("Account", {"company": co})
    r = C.cai(co); print("   ", ab, "trước", n0, "tài khoản |", {k: v for k, v in r.items() if k != "company"})
    chuan = bang(loai)
    so = {d.account_number: d for d in frappe.get_all("Account", {"company": co, "account_number": ["is", "set"]}, ["name", "account_number", "is_group", "parent_account", "account_type"])}
    ok(f"B1 {ab}: đủ tài khoản chuẩn", all(d["so"] in so for d in chuan), [d["so"] for d in chuan if d["so"] not in so][:10])
    ngoai = [d.get("account_number") or d["name"] for d in frappe.get_all("Account", {"company": co, "parent_account": ["is", "set"]}, ["name", "account_number"]) if not d.get("account_number")]
    ok(f"B2 {ab}: không còn tài khoản mẫu không số hiệu", not ngoai, ngoai[:8])
    thua = sorted(set(so) - {d["so"] for d in chuan} - {C.TK_TAM[0]} - set(T.CAN[loai]))
    ok(f"B3 {ab}: không có tài khoản ngoài bảng chuẩn", not thua, thua[:10])
    cam = ["621", "622", "623", "627", "641", "3389"] if loai == "aph" else ["3389", "3385"]
    ok(f"B4 {ab}: không có tài khoản cấm theo thông tư ({'TT133' if loai == 'aph' else 'TT99'})", not [k for k in cam if k in so], [k for k in cam if k in so])
    if loai == "vh":
        ok("B4b VH có 621–627, 641, 642", all(k in so for k in ("621", "622", "623", "627", "641", "642")))
    else:
        ok("B4b APH có 6421, 6422, 3385", all(k in so for k in ("6421", "6422", "3385")))
    mdk = {k: s for k, s in C.mac_dinh(loai).items() if frappe.get_meta("Company").has_field(k)}
    md = frappe.db.get_value("Company", co, list(mdk), as_dict=True)
    sai = {k: (md.get(k), so[s].name) for k, s in mdk.items() if s in so and md.get(k) != so[s].name}
    ok(f"B5 {ab}: tài khoản mặc định đúng", not sai, sai)
    ok(f"B6 {ab}: tồn kho vĩnh viễn + theo mặt hàng", bool(frappe.db.get_value("Company", co, "enable_perpetual_inventory")) and bool(frappe.db.get_value("Company", co, "enable_item_wise_inventory_account")))
    kho = {w.warehouse_name for w in frappe.get_all("Warehouse", {"company": co, "disabled": 0}, ["warehouse_name"])}
    ok(f"B7 {ab}: có kho địa điểm + Hàng đang vận chuyển", {"Hà Nội", "Kho bán hàng Hà Nội", "Kho Đà Nẵng", "Kho Hồ Chí Minh", "Hàng đang vận chuyển"} <= kho)
    ok(f"B8 {ab}: nhà máy {'có' if loai == 'aph' else 'không có'}", (C.NHA_MAY in kho) == (loai == "aph") and ({"Kho nguyên liệu đỗ", "Kho thành phẩm đỗ"} <= kho) == (loai == "aph"))
    ok(f"B9 {ab}: không còn kho mẫu ERPNext", not (kho & set(C.KHO_MAC_DINH_ERPNEXT)), kho & set(C.KHO_MAC_DINH_ERPNEXT))
    nh = {}
    for ten, s in C.NHOM_HANG[loai]:
        g = frappe.db.get_value("Item Default", {"parent": ten, "company": co}, "default_inventory_account")
        nh[ten] = g
    sai = [t for t, s in C.NHOM_HANG[loai] if (s and nh[t] != so[s].name) or (not s and nh[t])]
    ok(f"B10 {ab}: nhóm hàng gắn đúng tài khoản kho", not sai, sai)
    ok(f"B11 {ab}: không còn nhóm hàng mẫu ERPNext", not [g for g in C.NHOM_MAC_DINH_ERPNEXT if frappe.db.exists("Item Group", g)], "")
    r2 = C.cai(co)
    ok(f"B12 {ab}: chạy lại không tạo/xóa thêm", r2["tao"] == 0 and r2["bo"] == 0 and r2["kho_nhom"]["kho"] == 0 and r2["kho_nhom"]["nhom"] == 0, {k: v for k, v in r2.items() if k != "company"})
    t = T.setup(co)
    ok(f"B13 {ab}: bộ kiểm tài khoản chuẩn cũ vẫn đạt", not t["thieu"], t["thieu"] or t["viec"])
    ok(f"B14 {ab}: có tài khoản thu hộ dưới 3388", bool(frappe.db.exists("Account", {"company": co, "account_name": T.TEN_TK_THU_HO})), t["canh_bao"])
    from aphvh import vat_rules as V
    ok(f"B14b {ab}: có mẫu thuế GTGT theo thuế suất", all(frappe.db.exists("Item Tax Template", f"{ti} - {ab}") for ti, _ in V.VAT_TEMPLATES) and bool(frappe.db.exists("Sales Taxes and Charges Template", f"{V.SALES_TAX_TEMPLATE} - {ab}")))
    ok(f"B15 {ab}: nhận diện công ty theo viết tắt", T.loai_don_vi(frappe.db.get_value("Company", co, "abbr")) == loai)
# nhóm con thừa kế tài khoản kho
if not frappe.db.exists("Item Group", "HH.THU"):
    frappe.get_doc({"doctype": "Item Group", "item_group_name": "HH.THU", "parent_item_group": "HH - Hàng hóa"}).insert(ignore_permissions=True)
n = C.gan_tk_cho_nhom_con(cty["APH"])
ok("B16 nhóm con lấy tài khoản kho của nhóm cha (APH)", bool(frappe.db.get_value("Item Default", {"parent": "HH.THU", "company": cty["APH"]}, "default_inventory_account")), n)
json.dump(R, open(out, "w"), ensure_ascii=False, indent=1)
print("TỔNG", len(R), "dòng, KHÔNG ĐẠT:", sum(1 for r in R if r[1] != "ĐẠT"))
frappe.destroy()
