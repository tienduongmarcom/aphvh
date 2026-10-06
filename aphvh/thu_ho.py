"""Bút toán thu hộ (0.4.20): gắn vào Journal Entry. Quy tắc thuần nằm ở thu_ho_rules."""

import frappe
from frappe.utils import nowdate

from aphvh import thu_ho_rules as T

F = {
    "co": "aphvh_thu_ho",
    "chu_hang": "aphvh_th_chu_hang",
    "khach": "aphvh_th_khach",
    "tham_chieu": "aphvh_th_tham_chieu",
    "tt": "aphvh_th_trang_thai",
    "ghi_chu": "aphvh_th_ghi_chu_xu_ly",
    "ngay": "aphvh_th_ngay_xu_ly",
}


def _dong(doc):
    out = []
    for r in doc.get("accounts") or []:
        so, ten = frappe.get_cached_value("Account", r.account, ["account_number", "account_name"]) or ("", "")
        out.append({"so_tk": so, "ten_tk": ten or r.account, "debit": r.debit_in_account_currency or r.debit,
                    "credit": r.credit_in_account_currency or r.credit})
    return out


def _kiem_tra(doc):
    if not doc.meta.has_field(F["co"]):
        return None
    kq = T.kiem_tra(doc.get(F["co"]), doc.get(F["khach"]), doc.get(F["chu_hang"]), T.so_tien_thu_ho(_dong(doc)),
                    doc.get(F["tt"]), doc.get(F["ghi_chu"]))
    if kq["loi"]:
        frappe.throw("<br>".join(kq["loi"]), title="Bút toán thu hộ")
    if not doc.get(F["co"]):
        for k in ("tt", "ngay"):
            if doc.get(F[k]):
                doc.set(F[k], None)
        return None
    doc.set(F["tt"], kq["trang_thai"])
    doc.set(F["ngay"], (doc.get(F["ngay"]) or nowdate()) if kq["trang_thai"] == T.TT_DA_XU_LY else None)
    return kq


def validate(doc, method=None):
    kq = _kiem_tra(doc)
    if kq and kq["trang_thai"] == T.TT_CAN_XU_LY and doc.is_new():
        frappe.msgprint("Bút toán thu hộ được ghi nhận ở trạng thái <b>Cần xử lý</b>. Sau khi xử lý các nghiệp vụ phía sau "
                        "trên MISA, đổi sang 'Đã xử lý' và ghi số chứng từ.", title="Bút toán thu hộ", indicator="orange")


def before_update_after_submit(doc, method=None):
    _kiem_tra(doc)
