"""Giá thành nhà máy (0.11.1, cờ `kh_aph_factory_costing`, mặc định tắt). Đặc tả: docs/dac-ta-0.11.1.md mục 3.1–3.5.

- Giá tạm cho hàng nhà máy (R064): ô "Giá tạm" trên Purchase Order / Purchase Receipt / Stock Reconciliation, chỉ cho mã thuộc
  nhóm hàng có tích "Cho nhập giá tạm", giá > 0. Chốt giá bằng Purchase Invoice (ERPNext tự điều chỉnh phiếu nhập và repost
  khi Buying Settings `set_landed_cost_based_on_purchase_invoice_rate` = 1).
- Hệ số phẩm cấp (R078): quy tắc kg-v4 trong stock_entry_kg.py, trọng số = kg × hệ số đã lưu trên dòng.
- Phân bổ chi phí sản xuất cuối tháng (R079, R088, D1, D2): số dư 1548x theo trung tâm chi phí → Landed Cost Voucher NHÁP cho
  từng xưởng; phần "Nhà máy chung" → bút toán NHÁP Nợ 6323 / Có 1548x. Kế toán xem rồi tự ghi sổ.
- Vét bồn (R075, R076, R068): phiếu xuất NHÁP toàn bộ tồn sổ của kho bồn; hao hụt tự nhiên vào 15488 của xưởng (được phân bổ
  vào giá thành), bất thường vào 6322.
App không tạo kho, không tạo trung tâm chi phí, không tự ghi sổ chứng từ nào.
"""
import frappe
from frappe.utils import cint, flt, get_first_day, get_last_day, getdate, nowdate

from lab9x import gia_thanh as G

FLAG = "kh_aph_factory_costing"
IG_GIA_TAM = "kh_aph_gia_tam"
F_GIA_TAM = "kh_aph_gia_tam"
F_HE_SO_ITEM = "kh_aph_he_so_gia_thanh"
F_HE_SO = "kh_aph_he_so"
F_XUONG = "kh_aph_xuong"
F_XAC_NHAN_LECH = "kh_aph_xac_nhan_lech_kg"
F_LY_DO_LECH = "kh_aph_ly_do_lech_kg"
F_KHO_BON = "kh_aph_kho_bon"
F_LOAI_TTCP = "kh_aph_loai_ttcp"
F_KY = "kh_aph_phan_bo_ky"
F_VET_BON = "kh_aph_vet_bon"
TTCP_XUONG = "Xưởng sản xuất"
REPACK_TYPE = "Đổi bao, đóng gói lại"
TTCP_CHUNG = "Nhà máy chung"
VAI_TRO_KE_TOAN = {"Accounts Manager", "Accounts User", "System Manager"}

FIELDS = {
    "Item": [{"fieldname": F_HE_SO_ITEM, "label": "Hệ số phân bổ giá thành", "fieldtype": "Float", "default": "1",
              "insert_after": "stock_uom", "non_negative": 1,
              "description": "Thành phẩm cùng một phiếu sản xuất chia giá theo kg × hệ số (R078). 1 = chia theo kg."}],
    "Stock Entry Detail": [{"fieldname": F_HE_SO, "label": "Hệ số giá thành đã lưu", "fieldtype": "Float",
                            "insert_after": "kh_aph_kg", "non_negative": 1,
                            "description": "Lấy từ mã hàng khi lưu phiếu, sửa được trên dòng; tính lại giá dùng số đã lưu."}],
    "Stock Entry": [
        {"fieldname": F_XUONG, "label": "Xưởng (trung tâm chi phí)", "fieldtype": "Link", "options": "Cost Center",
         "insert_after": "stock_entry_type"},
        {"fieldname": F_XAC_NHAN_LECH, "label": "Xác nhận đóng gói lại lệch kg", "fieldtype": "Check",
         "insert_after": "kh_aph_process_loss_kg"},
        {"fieldname": F_LY_DO_LECH, "label": "Lý do lệch kg khi đóng gói lại", "fieldtype": "Small Text",
         "insert_after": F_XAC_NHAN_LECH},
        {"fieldname": F_VET_BON, "label": "Quyết toán vét bồn", "fieldtype": "Link", "options": "Warehouse",
         "insert_after": F_LY_DO_LECH, "read_only": 1, "no_copy": 1}],
    "Item Group": [{"fieldname": IG_GIA_TAM, "label": "Cho nhập giá tạm (hàng nhà máy, R064)", "fieldtype": "Check",
                    "insert_after": "parent_item_group",
                    "description": "Nguyên vật liệu, bán thành phẩm, bao bì, vật tư nhà máy. Hàng thương mại không tích: "
                                   "chưa rõ giá thì dùng Chờ định giá."}],
    "Purchase Order": [{"fieldname": F_GIA_TAM, "label": "Giá tạm (chốt sau bằng hóa đơn mua)", "fieldtype": "Check",
                        "insert_after": "supplier"}],
    "Purchase Receipt": [{"fieldname": F_GIA_TAM, "label": "Giá tạm (chốt sau bằng hóa đơn mua)", "fieldtype": "Check",
                          "insert_after": "supplier"}],
    "Stock Reconciliation": [{"fieldname": F_GIA_TAM, "label": "Giá tạm (sửa dần bằng phiếu kiểm kê sau)",
                              "fieldtype": "Check", "insert_after": "purpose"}],
    "Warehouse": [{"fieldname": F_KHO_BON, "label": "Kho bồn dở dang (R076)", "fieldtype": "Check",
                   "insert_after": "warehouse_name"}],
    "Cost Center": [{"fieldname": F_LOAI_TTCP, "label": "Loại trong giá thành (0.11.1)", "fieldtype": "Select",
                     "options": f"\n{TTCP_XUONG}\n{TTCP_CHUNG}", "insert_after": "cost_center_name",
                     "description": "Xưởng sản xuất: chi phí 1548x được phân bổ vào giá thành. Nhà máy chung: kết chuyển 6323."}],
    "Landed Cost Voucher": [{"fieldname": F_KY, "label": "Phân bổ chi phí sản xuất kỳ", "fieldtype": "Data",
                             "insert_after": "posting_date", "read_only": 1, "no_copy": 1}],
    "Journal Entry": [{"fieldname": F_KY, "label": "Kết chuyển chi phí sản xuất kỳ", "fieldtype": "Data",
                       "insert_after": "voucher_type", "read_only": 1, "no_copy": 1}],
}


def enabled():
    return cint(frappe.conf.get(FLAG))


# ---------------------------------------------------------------- cài đặt (bộ cài rõ ràng, idempotent)

def schema():
    """Gọi từ uat_candidate_setup.schema (UAT và bộ cài production). Không gắn after_install/after_migrate."""
    if not enabled():
        frappe.throw("Cần bật cờ kh_aph_factory_costing trước khi cài")
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(FIELDS)
    tk = tao_tai_khoan()
    if not frappe.db.exists("Stock Entry Type", REPACK_TYPE):
        frappe.get_doc({"doctype": "Stock Entry Type", "name": REPACK_TYPE, "purpose": "Repack"}).insert()
    if not cint(frappe.db.get_single_value("Buying Settings", "set_landed_cost_based_on_purchase_invoice_rate")):
        frappe.db.set_single_value("Buying Settings", "set_landed_cost_based_on_purchase_invoice_rate", 1)
    _quyen_lcv()
    return {"tai_khoan_tao": tk}


def _la_tt133(so_hieu):
    return "154" in so_hieu and "631" in so_hieu and "627" not in so_hieu


def tao_tai_khoan():
    """Tạo 1548x dưới 154 và 6323 dưới 632 cho công ty TT133 có sẵn hai nhóm này. Chạy lại không tạo trùng."""
    tao = 0
    for company in frappe.get_all("Company", pluck="name"):
        rows = frappe.get_all("Account", {"company": company, "account_number": ["is", "set"]},
                              ["name", "account_number", "is_group", "root_type"])
        co = {r.account_number: r for r in rows}
        if not _la_tt133(set(co)):
            continue
        can = [("154", so, ten) for so, ten in G.TK_YEU_TO_154] + [G.TK_KHONG_PHAN_BO]
        for cha, so, ten in can:
            if so in co or cha not in co or not cint(co[cha].is_group):
                continue
            frappe.get_doc({"doctype": "Account", "account_name": ten, "account_number": so, "company": company,
                            "parent_account": co[cha].name, "root_type": co[cha].root_type, "is_group": 0,
                            "account_type": None}).insert(ignore_permissions=True)
            tao += 1
    return tao


def _quyen_lcv():
    """Kế toán trưởng lập/ghi sổ Landed Cost Voucher phân bổ (chuẩn ERPNext chỉ có Stock Manager)."""
    from frappe.permissions import add_permission, update_permission_property
    if not frappe.db.exists("Custom DocPerm", {"parent": "Landed Cost Voucher", "role": "Accounts Manager",
                                               "permlevel": 0}):
        add_permission("Landed Cost Voucher", "Accounts Manager", 0)
    for ptype in ("read", "write", "create", "submit", "cancel"):
        update_permission_property("Landed Cost Voucher", "Accounts Manager", 0, ptype, 1, validate=False)


# ---------------------------------------------------------------- giá tạm (R064)

def nhom_co_co(item_group, field):
    """Nhóm hàng (hoặc một nhóm cha) có tích ô `field`."""
    from frappe.utils.nestedset import get_ancestors_of
    if not item_group or not frappe.get_meta("Item Group").has_field(field):
        return False
    return any(cint(frappe.get_cached_value("Item Group", g, field))
               for g in [item_group, *(get_ancestors_of("Item Group", item_group) or [])])


def validate_gia_tam(doc, method=None):
    if not enabled() or not cint(doc.get(F_GIA_TAM)):
        return
    gia = "valuation_rate" if doc.doctype == "Stock Reconciliation" else "rate"
    for d in doc.get("items") or []:
        nhom = frappe.get_cached_value("Item", d.item_code, "item_group")
        if not nhom_co_co(nhom, IG_GIA_TAM):
            frappe.throw(f"Dòng {d.idx} ({d.item_code}): nhóm hàng {nhom} không cho nhập giá tạm. "
                         "Hàng thương mại chưa rõ giá dùng phiếu Chờ định giá.", title="Không dùng giá tạm")
        if flt(d.get(gia)) <= 0:
            frappe.throw(f"Dòng {d.idx} ({d.item_code}): giá tạm phải lớn hơn 0.", title="Thiếu giá tạm")


# ---------------------------------------------------------------- kg-v4 (gọi từ stock_entry_kg)

def quy_tac_moi():
    return G.QUY_TAC_HE_SO if enabled() else None


def snapshot_he_so(doc, rows):
    for d in rows:
        if flt(d.get(F_HE_SO)) <= 0:
            d.set(F_HE_SO, flt(frappe.get_cached_value("Item", d.item_code, F_HE_SO_ITEM)) or 1.0)
        try:
            G.he_so_hop_le(d.get(F_HE_SO))
        except ValueError as e:
            frappe.throw(f"Dòng {d.idx}: {e}")


def kiem_xuong(doc, rows):
    """kg-v4: "Sản xuất theo kg" bắt buộc xưởng; "Đóng gói theo kg" (sản xuất có phụ phẩm) chọn xưởng thì được phân bổ
    cuối tháng. Gán trung tâm chi phí xưởng cho dòng thành phẩm để Landed Cost Voucher ghi Có đúng xưởng."""
    xuong = doc.get(F_XUONG)
    if not xuong:
        if doc.purpose == "Manufacture":
            frappe.throw("Phiếu sản xuất theo kg cần chọn Xưởng (trung tâm chi phí loại Xưởng sản xuất).")
        return
    cc = frappe.db.get_value("Cost Center", xuong, ["company", F_LOAI_TTCP, "is_group"], as_dict=True)
    if not cc or cc.company != doc.company or cc.get(F_LOAI_TTCP) != TTCP_XUONG or cint(cc.is_group):
        frappe.throw(f"{xuong} không phải trung tâm chi phí loại \"{TTCP_XUONG}\" của {doc.company}.")
    for d in rows:
        d.cost_center = xuong


def kiem_lech_repack(doc, kg_vao, kg_ra):
    """Q103: đóng gói lại phải bảo toàn kg; lệch thì phải xác nhận kèm lý do, không ghi hao hụt."""
    lech = G.lech_kg(kg_vao, kg_ra)
    doc.kh_aph_process_loss_kg = lech
    if lech and not (cint(doc.get(F_XAC_NHAN_LECH)) and (doc.get(F_LY_DO_LECH) or "").strip()):
        frappe.throw(f"Đóng gói lại lệch {lech:g} kg (đầu vào − đầu ra). Kiểm lại số kg; nếu đúng thực tế, "
                     "tích \"Xác nhận đóng gói lại lệch kg\" và ghi lý do.", title="Lệch kg khi đóng gói lại")


# ---------------------------------------------------------------- công cụ của kế toán

def _can_ke_toan():
    if not enabled():
        frappe.throw("Tính năng giá thành nhà máy chưa được bật")
    if frappe.session.user != "Administrator" and not (set(frappe.get_roles()) & {"Accounts Manager", "System Manager"}):
        frappe.throw("Cần quyền Kế toán trưởng (Accounts Manager)", frappe.PermissionError)


def _tai_khoan_yeu_to(company):
    so = [s for s, _t in G.TK_YEU_TO_154]
    return {r.account_number: r.name for r in frappe.get_all(
        "Account", {"company": company, "account_number": ["in", so], "is_group": 0}, ["name", "account_number"])}


@frappe.whitelist(methods=["POST"])
def phan_bo_thang(company, thang):
    """Tạo chứng từ NHÁP phân bổ chi phí sản xuất tháng `thang` (YYYY-MM). Chạy lại không tạo trùng."""
    _can_ke_toan()
    frappe.get_doc("Company", company).check_permission("read")
    dau = get_first_day(getdate(f"{thang}-01"))
    cuoi = get_last_day(dau)
    ky = dau.strftime("%Y-%m")
    tk = _tai_khoan_yeu_to(company)
    if not tk:
        frappe.throw("Công ty chưa có tài khoản 1548x (chạy bộ cài tính năng giá thành)")
    ttcp = frappe.get_all("Cost Center", {"company": company, F_LOAI_TTCP: ["in", [TTCP_XUONG, TTCP_CHUNG]],
                                          "is_group": 0}, ["name", F_LOAI_TTCP])
    xuong = [c.name for c in ttcp if c.get(F_LOAI_TTCP) == TTCP_XUONG]
    chung = [c.name for c in ttcp if c.get(F_LOAI_TTCP) == TTCP_CHUNG]
    if len(chung) > 1:
        frappe.throw("Chỉ đặt một trung tâm chi phí loại Nhà máy chung cho mỗi công ty")
    chung = chung[0] if chung else None
    if not xuong:
        frappe.throw("Chưa có trung tâm chi phí loại Xưởng sản xuất")
    so_du = {}
    if ttcp:
        for r in frappe.db.sql("""SELECT account, cost_center, SUM(debit) - SUM(credit) AS so_du
                FROM `tabGL Entry` WHERE company=%s AND is_cancelled=0 AND posting_date<=%s
                AND account IN %s AND cost_center IN %s GROUP BY account, cost_center""",
                               (company, cuoi, tuple(tk.values()), tuple(c.name for c in ttcp)), as_dict=True):
            so_du[(r.account, r.cost_center)] = flt(r.so_du)
    dong = {}
    for r in frappe.db.sql("""SELECT se.name AS phieu, d.name AS dong, d.kh_aph_kg AS kg, d.kh_aph_he_so AS he_so,
                se.kh_aph_xuong AS xuong
            FROM `tabStock Entry` se JOIN `tabStock Entry Detail` d ON d.parent=se.name
            WHERE se.docstatus=1 AND se.company=%s AND se.purpose IN ('Manufacture','Repack') AND se.kh_aph_costing_rule=%s
              AND IFNULL(se.kh_aph_xuong,'')!=''
              AND se.posting_date BETWEEN %s AND %s AND IFNULL(d.t_warehouse,'')!='' AND IFNULL(d.s_warehouse,'')=''
              AND (d.is_finished_item=1 OR IFNULL(d.secondary_item_type,'')!='') AND IFNULL(d.kh_aph_gia_co_dinh,0)=0
            ORDER BY se.posting_date, se.name, d.idx""", (company, G.QUY_TAC_HE_SO, dau, cuoi), as_dict=True):
        dong.setdefault(r.xuong, []).append((r.phieu, r.dong, flt(r.kg), flt(r.he_so)))
    kh = G.ke_hoach_phan_bo(so_du, xuong, chung, dong)
    kq = {"ky": ky, "lcv": {}, "but_toan_chung": None, "bo_qua": kh["bo_qua"]}
    for cc, phan in kh["lcv"].items():
        kq["lcv"][cc] = _tao_lcv(company, cuoi, f"{ky}|{cc}", cc, phan)
    if kh["chung"]:
        kq["but_toan_chung"] = _tao_je_chung(company, cuoi, f"{ky}|{chung}", chung, kh["chung"])
    return kq


def _da_co(dt, ky):
    return frappe.db.get_value(dt, {F_KY: ky, "docstatus": ["<", 2]}, "name")


def _tao_lcv(company, ngay, ky, cc, phan):
    ten = _da_co("Landed Cost Voucher", ky)
    if ten:
        return ten
    dong_se = {}
    for phieu, dong, _tien in phan["dong"]:
        dong_se[dong] = frappe.db.get_value("Stock Entry Detail", dong,
                                            ["item_code", "transfer_qty", "basic_rate", "basic_amount", "description"],
                                            as_dict=True)
    phieu = list(dict.fromkeys(p for p, _d, _t in phan["dong"]))
    doc = frappe.get_doc({
        "doctype": "Landed Cost Voucher", "company": company, "posting_date": ngay,
        "distribute_charges_based_on": "Distribute Manually", F_KY: ky,
        "purchase_receipts": [{"receipt_document_type": "Stock Entry", "receipt_document": p,
                               "posting_date": frappe.db.get_value("Stock Entry", p, "posting_date"),
                               "grand_total": flt(frappe.db.get_value("Stock Entry", p, "total_incoming_value"))}
                              for p in phieu],
        "items": [{"item_code": dong_se[d].item_code, "description": dong_se[d].description,
                   "qty": dong_se[d].transfer_qty, "rate": dong_se[d].basic_rate, "amount": dong_se[d].basic_amount,
                   "receipt_document_type": "Stock Entry", "receipt_document": p, "stock_entry_item": d,
                   "cost_center": cc, "applicable_charges": tien} for p, d, tien in phan["dong"]],
        "taxes": [{"expense_account": a, "description": f"Phân bổ {frappe.db.get_value('Account', a, 'account_name')} "
                   f"kỳ {ky.split('|')[0]}", "amount": tien, "cost_center": cc} for a, tien in phan["thue"]],
    })
    doc.insert(ignore_permissions=True)  # quyền đã kiểm ở _can_ke_toan; chứng từ NHÁP, kế toán tự ghi sổ
    return doc.name


def _tao_je_chung(company, ngay, ky, cc, dong):
    ten = _da_co("Journal Entry", ky)
    if ten:
        return ten
    tk632 = frappe.db.get_value("Account", {"company": company, "account_number": G.TK_KHONG_PHAN_BO[1]}, "name")
    if not tk632:
        frappe.throw(f"Thiếu tài khoản {G.TK_KHONG_PHAN_BO[1]} (chạy bộ cài tính năng giá thành)")
    tong = sum(t for _a, t in dong)
    doc = frappe.get_doc({
        "doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": company, "posting_date": ngay, F_KY: ky,
        "user_remark": f"Kết chuyển chi phí sản xuất chung cố định không phân bổ kỳ {ky.split('|')[0]} "
                       "(TT133 TK 154 nguyên tắc 1(đ); quyết định D2, chờ kế toán trưởng xác nhận)",
        "accounts": [{"account": tk632, "debit_in_account_currency": tong, "cost_center": cc}]
                    + [{"account": a, "credit_in_account_currency": t, "cost_center": cc} for a, t in dong],
    })
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist(methods=["POST"])
def vet_bon(kho, xuong, loai_hao_hut, ly_do, ngay=None):
    """Quyết toán vét bồn về 0: phiếu xuất NHÁP toàn bộ tồn sổ. Trả tên phiếu và các dòng bất thường cần xem."""
    _can_ke_toan()
    from erpnext.stock.utils import get_stock_balance
    wh = frappe.get_doc("Warehouse", kho)
    wh.check_permission("read")
    if not cint(wh.get(F_KHO_BON)):
        frappe.throw(f"{kho} chưa được đánh dấu Kho bồn dở dang")
    if loai_hao_hut not in ("Hao hụt tự nhiên", "Hao hụt bất thường") or not (ly_do or "").strip():
        frappe.throw("Chọn loại hao hụt (tự nhiên/bất thường) và ghi lý do")
    cc = frappe.db.get_value("Cost Center", xuong, ["company", F_LOAI_TTCP], as_dict=True)
    if not cc or cc.company != wh.company or cc.get(F_LOAI_TTCP) != TTCP_XUONG:
        frappe.throw("Chọn trung tâm chi phí loại Xưởng sản xuất của cùng công ty")
    ngay = ngay or nowdate()
    da = frappe.db.get_value("Stock Entry", {F_VET_BON: kho, "docstatus": 0}, "name")
    if da:
        return {"phieu": da, "bat_thuong": [], "da_co": True}
    so = G.TK_HAO_HUT_TU_NHIEN if loai_hao_hut == "Hao hụt tự nhiên" else G.TK_TON_THAT
    tk = frappe.db.get_value("Account", {"company": wh.company, "account_number": so, "is_group": 0}, "name")
    if not tk:
        frappe.throw(f"Thiếu tài khoản {so}")
    ton = []
    for item in frappe.get_all("Bin", {"warehouse": kho}, pluck="item_code"):
        sl, gt = get_stock_balance(item, kho, ngay, with_valuation_rate=True)[:2]
        ton.append((item, sl, flt(sl) * flt(gt)))
    xuat, bat_thuong = G.ke_hoach_vet_bon(ton)
    # Hàng trong bồn là hàng rời: mã quản lý bao không vét tự động (sổ bao phải khớp kg), để kế toán xử lý tay.
    bao = {i for i, _sl in xuat if flt(frappe.get_cached_value("Item", i, "kh_aph_kg_per_bag"))} \
        if frappe.get_meta("Item").has_field("kh_aph_kg_per_bag") else set()
    bat_thuong += [(i, sl, "mã quản lý bao: dùng mã hàng rời cho kho bồn") for i, sl in xuat if i in bao]
    xuat = [(i, sl) for i, sl in xuat if i not in bao]
    if not xuat:
        return {"phieu": None, "bat_thuong": bat_thuong}
    doc = frappe.get_doc({
        "doctype": "Stock Entry", "stock_entry_type": "Material Issue", "purpose": "Material Issue",
        "company": wh.company, "posting_date": ngay, "set_posting_time": 1, F_VET_BON: kho,
        "kh_aph_loss_type": loai_hao_hut, "kh_aph_loss_reason": ly_do,
        "items": [{"item_code": item, "qty": sl, "s_warehouse": kho, "expense_account": tk, "cost_center": xuong}
                  for item, sl in xuat],
    })
    doc.insert(ignore_permissions=True)  # quyền đã kiểm ở _can_ke_toan; phiếu NHÁP, người có quyền kho ghi sổ
    return {"phieu": doc.name, "bat_thuong": bat_thuong}
