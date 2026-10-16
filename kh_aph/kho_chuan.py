"""Cây kho chuẩn, loại kho, đóng gói hai công đoạn, kiểm kê có mốc (0.11.2, cờ `kh_aph_kho_chuan`, mặc định tắt).

Đặc tả: docs/dac-ta-0.11.2.md mục 2, 4, 6. Quy tắc cây kho thuần ở lab9x.cay_kho.

- Bộ dựng cây kho `dung` (chạy tay, Administrator, gõ đúng tên site): đọc mục `cay_kho` của khach.json, chỉ THÊM kho
  còn thiếu; không đổi tên, không xóa, không đổi pháp nhân/loại của kho đã có; kho ngoài cây chỉ báo.
- Ô "Loại kho" + "Dây chuyền" trên Warehouse; đơn bán / phiếu giao / hóa đơn xuất kho không được chọn kho không bán
  (dở dang, chờ đóng gói, chờ xử lý, cách ly, gửi).
- Nhóm hàng "Bao bì đóng gói": dòng chỉ cộng tiền, không cộng kg (stock_entry_kg).
- Loại phiếu "Đóng gói thành phẩm" (Repack, kg-v4): công đoạn 2, bảo toàn kg hàng chính, giá thành phẩm = hàng chính + bao bì.
- Kiểm kê có mốc (R054–R056): thiếu → phiếu xuất NHÁP Nợ 1381; thừa → phiếu nhập NHÁP vào kho "Hàng chờ xử lý" của địa
  điểm, Có 3381. Vượt ngưỡng % (Stock Settings) thì bắt buộc lý do. Bước xử lý tiếp theo chờ kế toán trưởng chốt.
App không tự ghi sổ chứng từ nào.
"""

import frappe
from frappe.utils import cint, flt, get_datetime, nowdate, nowtime
from lab9x import cay_kho as C
from lab9x.vn_words import so_vn

FLAG = "kh_aph_kho_chuan"
F_LOAI = "kh_aph_loai_kho"
F_DAY = "kh_aph_day_chuyen"
IG_BAO_BI = "kh_aph_bao_bi"
F_HAO_HUT_BOM = "kh_aph_hao_hut_cho_phep"
F_NGUONG = "kh_aph_nguong_kiem_ke"
F_KIEM_KE = "kh_aph_kiem_ke"
DONG_GOI_TYPE = "Đóng gói thành phẩm"
TK_THIEU, TK_THUA = "1381", "3381"
CF_KHO_BON_CU = "Warehouse-kh_aph_kho_bon"  # 0.11.1, bỏ ở 0.11.2 (production chưa có dữ liệu)

FIELDS = {
    "Warehouse": [
        {"fieldname": F_LOAI, "label": "Loại kho", "fieldtype": "Select", "options": "\n" + "\n".join(C.LOAI_KHO),
         "insert_after": "warehouse_name", "in_standard_filter": 1,
         "description": "Dở dang, Chờ đóng gói, Chờ xử lý, Cách ly, Gửi: không bán được từ kho này."},
        {"fieldname": F_DAY, "label": "Dây chuyền", "fieldtype": "Select", "options": "\n" + "\n".join(C.DAY_CHUYEN),
         "insert_after": F_LOAI, "depends_on": f"eval:doc.{F_LOAI}=='{C.DO_DANG}'",
         "mandatory_depends_on": f"eval:doc.{F_LOAI}=='{C.DO_DANG}'"}],
    "Item Group": [{"fieldname": IG_BAO_BI, "label": "Bao bì đóng gói (chỉ cộng tiền, không cộng kg)", "fieldtype": "Check",
                    "insert_after": "parent_item_group",
                    "description": "Túi, thùng, nhãn… Trên phiếu sản xuất / đóng gói theo kg, dòng thuộc nhóm này không "
                                   "tính vào cân đối kg."}],
    "BOM": [{"fieldname": F_HAO_HUT_BOM, "label": "Tỷ lệ hao hụt cho phép (%)", "fieldtype": "Percent", "default": "0",
             "insert_after": "quantity", "non_negative": 1, "allow_on_submit": 1,
             "description": "Cộng thêm trên định mức khi quyết toán dở dang. 0 = đúng định mức là mức bình thường."}],
    "Stock Settings": [{"fieldname": F_NGUONG, "label": "Ngưỡng chênh lệch kiểm kê cần lý do (%)", "fieldtype": "Percent",
                        "insert_after": "allow_negative_stock", "non_negative": 1,
                        "description": "R055: chênh lệch kiểm kê vượt ngưỡng (so với số sổ) thì bắt buộc ghi lý do."}],
    "Stock Entry": [{"fieldname": F_KIEM_KE, "label": "Biên bản kiểm kê (mốc)", "fieldtype": "Data",
                     "insert_after": "kh_aph_vet_bon", "read_only": 1, "no_copy": 1}],
}


def enabled():
    return cint(frappe.conf.get(FLAG))


# ---------------------------------------------------------------- cài đặt (bộ cài rõ ràng, idempotent)

def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_kho_chuan trước khi cài")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    if not frappe.db.exists("Stock Entry Type", DONG_GOI_TYPE):
        frappe.get_doc({"doctype": "Stock Entry Type", "name": DONG_GOI_TYPE, "purpose": "Repack"}).insert()
    if not frappe.db.exists("Warehouse Type", "Transit"):
        frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert()
    # Bỏ ô "Kho bồn dở dang" của 0.11.1 (thay bằng loại kho Dở dang dây chuyền). Cột dữ liệu giữ nguyên.
    if frappe.db.exists("Custom Field", CF_KHO_BON_CU):
        frappe.delete_doc("Custom Field", CF_KHO_BON_CU, ignore_permissions=True)
    return {"loai_phieu": DONG_GOI_TYPE}


def _kiem_quan_tri(xac_nhan_site):
    if frappe.session.user != "Administrator":
        frappe.throw("Chỉ Administrator được dựng cây kho", frappe.PermissionError)
    if not xac_nhan_site or xac_nhan_site != frappe.local.site:
        frappe.throw(f"Gõ đúng tên site đích để xác nhận: xac_nhan_site = \"{frappe.local.site}\"")
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_kho_chuan và chạy bộ cài tính năng trước")
    if not frappe.get_meta("Warehouse").has_field(F_LOAI):
        frappe.throw("Chưa cài ô Loại kho: chạy kh_aph.cai_dat_tinh_nang.cai trước")


def _goc_kho(company):
    return frappe.db.get_value("Warehouse", {"company": company, "is_group": 1,
                                             "parent_warehouse": ["in", ["", None]]}, "name") \
        or frappe.db.get_value("Warehouse", {"company": company, "is_group": 1, "parent_warehouse": ["is", "not set"]},
                               "name")


def _hien_co(cong_ty_theo_abbr):
    abbr_cua = {v: k for k, v in cong_ty_theo_abbr.items()}
    return {w.name: {"company_abbr": abbr_cua.get(w.company), "loai_kho": w.get(F_LOAI), "is_group": w.is_group}
            for w in frappe.get_all("Warehouse", {"company": ["in", list(cong_ty_theo_abbr.values())]},
                                    ["name", "company", "is_group", F_LOAI])}


def ke_hoach_site(cfg):
    """(kế hoạch, cần tạo, cảnh báo, {abbr: company}) của site hiện tại theo cấu hình khách."""
    cay = cfg.get("cay_kho")
    if not cay:
        frappe.throw("khach.json chưa có mục cay_kho")
    co = {}
    for c in cfg["cong_ty"]:
        ten = frappe.db.get_value("Company", {"abbr": c["abbr"]}, "name")
        if ten:
            co[c["abbr"]] = ten
    ke = C.ke_hoach(cay, list(co))
    tao, canh_bao = C.so_sanh(ke, _hien_co(co))
    thieu_ct = [c["abbr"] for c in cfg["cong_ty"] if c["abbr"] not in co]
    if thieu_ct:
        canh_bao.insert(0, "chưa có công ty: " + ", ".join(thieu_ct))
    return ke, tao, canh_bao, co


def dung(duong_dan, xac_nhan_site=None):
    """Dựng cây kho chuẩn (idempotent). Lệnh:
    bench --site <site> execute kh_aph.kho_chuan.dung --kwargs '{"duong_dan": "<khach.json>", "xac_nhan_site": "<site>"}'
    """
    _kiem_quan_tri(xac_nhan_site)
    from kh_aph.khach_hang import doc_cau_hinh
    cfg = doc_cau_hinh(duong_dan)
    ke, tao, canh_bao, co = ke_hoach_site(cfg)
    da_tao = []
    for k in tao:
        company = co[k["abbr"]]
        cha = k["cha"] or _goc_kho(company)
        if not cha:
            frappe.throw(f"{company}: không thấy nhóm kho gốc")
        doc = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": k["ten"], "company": company,
                              "parent_warehouse": cha, "is_group": k["nhom"], F_LOAI: k["loai_kho"],
                              F_DAY: k["day_chuyen"], "warehouse_type": "Transit" if k["transit"] else None})
        doc.insert(ignore_permissions=True)
        da_tao.append(doc.name)
    # Kho đã có, đúng tên cây chuẩn nhưng chưa khai loại: điền loại (không đổi loại đã khai).
    bo_sung = []
    for k in ke:
        ten = C.ten_kho(k["ten"], k["abbr"])
        if k["nhom"] or not k["loai_kho"] or ten in da_tao or not frappe.db.exists("Warehouse", ten):
            continue
        if not frappe.db.get_value("Warehouse", ten, F_LOAI):
            frappe.db.set_value("Warehouse", ten, {F_LOAI: k["loai_kho"], F_DAY: k["day_chuyen"]})
            bo_sung.append(ten)
    van_chuyen = []
    for abbr, company in co.items():
        ten = C.ten_kho(C.TEN_VAN_CHUYEN, abbr)
        if frappe.db.exists("Warehouse", ten) and not frappe.db.get_value("Company", company,
                                                                          "default_in_transit_warehouse"):
            frappe.db.set_value("Company", company, "default_in_transit_warehouse", ten)
            van_chuyen.append(company)
    frappe.db.commit()
    kq = {"site": frappe.local.site, "da_tao": da_tao, "dien_loai": bo_sung, "kho_van_chuyen_mac_dinh": van_chuyen,
          "canh_bao": canh_bao, "tong_cay_chuan": len(ke)}
    print(f"Cây kho: tạo {len(da_tao)}, điền loại {len(bo_sung)}, cảnh báo {len(canh_bao)} / {len(ke)} kho chuẩn")
    for c in canh_bao:
        print("  CẢNH BÁO:", c)
    return kq


# ---------------------------------------------------------------- chặn bán từ kho không bán

def loai_kho(kho):
    if not kho or not frappe.get_meta("Warehouse").has_field(F_LOAI):
        return None
    return frappe.get_cached_value("Warehouse", kho, F_LOAI)


def validate_kho_ban(doc, method=None):
    """Đơn bán, đơn bán chung, phiếu giao, hóa đơn xuất kho không chọn kho loại không bán. Hàng trả lại thì được nhập vào."""
    if not enabled() or doc.get("is_return"):
        return
    if doc.doctype == "Sales Invoice" and not cint(doc.get("update_stock")):
        return
    sai = []
    for d in doc.get("items") or []:
        loai = loai_kho(d.get("warehouse"))
        if loai in C.KHONG_BAN:
            sai.append(f"dòng {d.idx}: {d.warehouse} ({loai})")
    if sai:
        frappe.throw("Không bán từ kho không bán được: " + "; ".join(sai)
                     + ". Chuyển hàng sang kho Bán hàng hoặc Thành phẩm trước.", title="Kho không bán được")


def validate_kho(doc, method=None):
    """Warehouse: dây chuyền chỉ đi với loại Dở dang; kho Vận chuyển phải là warehouse_type Transit."""
    if not enabled() or not doc.meta.has_field(F_LOAI):
        return
    loai = doc.get(F_LOAI)
    if loai == C.DO_DANG and not doc.get(F_DAY) and not cint(doc.is_group):
        frappe.throw("Kho dở dang dây chuyền cần chọn Dây chuyền")
    if loai != C.DO_DANG and doc.get(F_DAY):
        doc.set(F_DAY, None)
    if loai == C.VAN_CHUYEN and doc.warehouse_type != "Transit":
        doc.warehouse_type = "Transit"
    if not doc.is_new() and doc.has_value_changed(F_LOAI) and doc.get_doc_before_save().get(F_LOAI):
        if frappe.db.exists("Bin", {"warehouse": doc.name, "actual_qty": ["!=", 0]}) or frappe.db.exists(
                "Bin", {"warehouse": doc.name, "stock_value": ["!=", 0]}):
            frappe.throw("Kho đang có tồn: không đổi loại kho. Chuyển hết hàng ra trước.")


# ---------------------------------------------------------------- bao bì (gọi từ stock_entry_kg)

def la_bao_bi(item_code):
    if not enabled() or not frappe.get_meta("Item Group").has_field(IG_BAO_BI):
        return False
    from kh_aph.factory_costing import nhom_co_co
    return nhom_co_co(frappe.get_cached_value("Item", item_code, "item_group"), IG_BAO_BI)


# ---------------------------------------------------------------- kiểm kê có mốc (R054–R056)

def _dia_diem(kho):
    cha = frappe.db.get_value("Warehouse", kho, "parent_warehouse")
    if not cha or not frappe.db.get_value("Warehouse", cha, "parent_warehouse"):
        return None, cha  # kho nằm thẳng dưới gốc công ty
    return frappe.db.get_value("Warehouse", cha, "warehouse_name"), cha


def kho_tinh_trang(kho, loai=C.CHO_XU_LY):
    """Kho Chờ xử lý / Cách ly của địa điểm chứa `kho`; tạo khi lần đầu cần (một kho cho mỗi địa điểm)."""
    goc = C.TEN_CHO_XU_LY if loai == C.CHO_XU_LY else C.TEN_CACH_LY
    company = frappe.db.get_value("Warehouse", kho, "company")
    dia_diem, cha = _dia_diem(kho)
    ten = C.ten_kho(C.ten_kho_tinh_trang(goc, dia_diem), frappe.get_cached_value("Company", company, "abbr"))
    if frappe.db.exists("Warehouse", ten):
        return ten
    return frappe.get_doc({"doctype": "Warehouse", "warehouse_name": C.ten_kho_tinh_trang(goc, dia_diem),
                           "company": company, "parent_warehouse": cha, "is_group": 0, F_LOAI: loai}
                          ).insert(ignore_permissions=True).name


def _quyen_kho(kho):
    if not enabled():
        frappe.throw("Tính năng cây kho chuẩn chưa được bật")
    wh = frappe.get_doc("Warehouse", kho)
    wh.check_permission("read")
    if cint(wh.is_group):
        frappe.throw("Chọn kho lá, không chọn nhóm kho")
    if not frappe.has_permission("Stock Entry", "create"):
        frappe.throw("Cần quyền lập phiếu kho", frappe.PermissionError)
    return wh


@frappe.whitelist()
def so_sach(kho, ngay=None, gio=None):
    """Số sổ từng mã tại mốc kiểm kê (cho hộp thoại kiểm kê). Không trả giá trị (người không xem giá vốn cũng dùng được)."""
    _quyen_kho(kho)
    from erpnext.stock.utils import get_stock_balance
    ngay, gio = ngay or nowdate(), gio or nowtime()
    out = []
    for item in frappe.get_all("Bin", {"warehouse": kho}, pluck="item_code", order_by="item_code"):
        sl = flt(get_stock_balance(item, kho, ngay, gio))
        if sl:
            out.append({"item_code": item, "item_name": frappe.get_cached_value("Item", item, "item_name"),
                        "sl_so": sl, "stock_uom": frappe.get_cached_value("Item", item, "stock_uom")})
    return out


def _tk(company, so):
    tk = frappe.db.get_value("Account", {"company": company, "account_number": so, "is_group": 0}, "name")
    if not tk:
        frappe.throw(f"{company} chưa có tài khoản {so} (chi tiết, không phải nhóm)")
    return tk


@frappe.whitelist(methods=["POST"])
def ghi_kiem_ke(kho, dong, ngay=None, gio=None, ly_do=None, bien_ban=None):
    """Ghi kết quả kiểm kê có mốc: lập phiếu NHÁP cho phần thiếu (Nợ 1381) và phần thừa (nhập kho Chờ xử lý, Có 3381).

    dong: [{"item_code", "sl_thuc_te"}] (JSON). Chạy lại cùng biên bản không tạo trùng.
    """
    wh = _quyen_kho(kho)
    from erpnext.stock.utils import get_stock_balance
    dong = frappe.parse_json(dong) if isinstance(dong, str) else dong
    ngay, gio = ngay or nowdate(), gio or nowtime()
    moc = get_datetime(f"{ngay} {gio}")
    bien_ban = (bien_ban or "").strip() or f"{kho}|{moc:%Y-%m-%d %H:%M:%S}"
    da = frappe.get_all("Stock Entry", {F_KIEM_KE: bien_ban, "docstatus": ["<", 2]}, pluck="name")
    if da:
        return {"phieu": da, "da_co": True}
    nguong = flt(frappe.db.get_single_value("Stock Settings", F_NGUONG)) \
        if frappe.get_meta("Stock Settings").has_field(F_NGUONG) else 0
    thieu, thua, vuot = [], [], []
    for d in dong or []:
        item = d.get("item_code")
        tt = flt(d.get("sl_thuc_te"))
        if not item or tt < 0:
            frappe.throw("Mỗi dòng cần mã hàng và số thực tế ≥ 0")
        so = flt(get_stock_balance(item, kho, ngay, gio))
        chenh = round(tt - so, 6)
        if not chenh:
            continue
        pt = abs(chenh) / so * 100 if so else 100.0
        if nguong and pt > nguong:
            vuot.append(f"{item}: sổ {so_vn(so)}, thực tế {so_vn(tt)} ({so_vn(round(pt, 2))}%)")
        if chenh < 0:
            thieu.append((item, -chenh))
        else:
            # Hàng thừa nhập theo giá bình quân của kho đang kiểm tại mốc (kho Chờ xử lý mới chưa có giá).
            gia = flt(get_stock_balance(item, kho, ngay, gio, with_valuation_rate=True)[1])
            thua.append((item, chenh, gia))
    if vuot and not (ly_do or "").strip():
        frappe.throw("Chênh lệch vượt ngưỡng " + so_vn(nguong) + "%, cần ghi lý do: " + "; ".join(vuot),
                     title="Chênh lệch kiểm kê lớn (R055)")
    if not thieu and not thua:
        return {"phieu": [], "khop": True}
    ghi_chu = (f"Kiểm kê {kho} lúc {moc:%d/%m/%Y %H:%M} (R054). " + (f"Lý do: {ly_do.strip()}. " if ly_do else "")
               + "Bước xử lý tiếp (bồi thường, ghi giá vốn, thu nhập khác…) chờ kế toán trưởng chốt.")
    chung = {"doctype": "Stock Entry", "company": wh.company, "posting_date": ngay, "posting_time": gio,
             "set_posting_time": 1, F_KIEM_KE: bien_ban, "remarks": ghi_chu}
    phieu = []
    if thieu:
        tk = _tk(wh.company, TK_THIEU)
        doc = frappe.get_doc({**chung, "stock_entry_type": "Material Issue", "purpose": "Material Issue",
                              "items": [{"item_code": i, "qty": q, "s_warehouse": kho, "expense_account": tk}
                                        for i, q in thieu]})
        doc.insert()
        phieu.append(doc.name)
    if thua:
        tk = _tk(wh.company, TK_THUA)
        cho = kho_tinh_trang(kho, C.CHO_XU_LY)
        doc = frappe.get_doc({**chung, "stock_entry_type": "Material Receipt", "purpose": "Material Receipt",
                              "items": [{"item_code": i, "qty": q, "t_warehouse": cho, "expense_account": tk,
                                         "basic_rate": g} for i, q, g in thua]})
        doc.insert()
        phieu.append(doc.name)
    if vuot:
        frappe.get_doc("Warehouse", kho).add_comment("Comment", "Kiểm kê vượt ngưỡng: " + "; ".join(vuot)
                                                     + f". Lý do: {ly_do.strip()}. Phiếu nháp: {', '.join(phieu)}")
    return {"phieu": phieu, "thieu": thieu, "thua": [(i, q) for i, q, _g in thua], "vuot_nguong": vuot}
