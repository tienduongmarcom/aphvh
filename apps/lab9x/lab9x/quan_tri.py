"""Quy tắc báo cáo quản trị (thuần, không import frappe) — từ lab9x 0.2.5 / kh_aph 0.11.4.

- Cộng ngang nhiều đơn vị (R100): KHÔNG phải hợp nhất kế toán (không loại trừ giao dịch nội bộ trong lãi gộp).
- Lãi tạm tính (R101, R104): kỳ chưa khóa hoặc chưa phân bổ chi phí sản xuất.
- Dòng tiền 7/30 ngày (R102, R103): xếp khoản theo hạn, loại đối tác nội bộ.
"""
import datetime

GHI_CHU_CONG_NGANG = "Cộng ngang các đơn vị — không phải báo cáo hợp nhất kế toán (R100)"


def _ngay(x):
    if isinstance(x, str):
        return datetime.date.fromisoformat(x[:10])
    if isinstance(x, datetime.datetime):
        return x.date()
    return x


def cong_ngang(dong, cac_cty):
    """dong: [{"khoa", "abbr", "doanh_thu", "gia_von", "cp_truc_tiep", "tam_tinh" (set lý do)}].

    Trả {khoa: {"<abbr>_dt", "<abbr>_gv", "<abbr>_lg" cho từng đơn vị, "dt", "gv", "lg", "ty_le", "cp", "lai_sau_cp",
    "tam_tinh" (chuỗi lý do, rỗng = chính thức)}}.
    """
    kq = {}
    for d in dong:
        k = kq.setdefault(d["khoa"], {**{f"{a}_{c}": 0.0 for a in cac_cty for c in ("dt", "gv", "lg")},
                                      "dt": 0.0, "gv": 0.0, "cp": 0.0, "_ly_do": set()})
        dt, gv, cp = float(d.get("doanh_thu") or 0), float(d.get("gia_von") or 0), float(d.get("cp_truc_tiep") or 0)
        a = d["abbr"]
        if a in cac_cty:
            k[f"{a}_dt"] += dt
            k[f"{a}_gv"] += gv
            k[f"{a}_lg"] += dt - gv
        k["dt"] += dt
        k["gv"] += gv
        k["cp"] += cp
        k["_ly_do"] |= set(d.get("tam_tinh") or ())
    for k in kq.values():
        k["lg"] = k["dt"] - k["gv"]
        k["ty_le"] = round(k["lg"] / k["dt"] * 100, 2) if k["dt"] else None
        k["lai_sau_cp"] = k["lg"] - k["cp"]
        k["tam_tinh"] = "; ".join(sorted(k.pop("_ly_do")))
    return kq


def trang_thai_ky(da_khoa, can_phan_bo, da_phan_bo):
    """Trả tập lý do "lãi tạm tính" của một tháng của một đơn vị (rỗng = chính thức)."""
    ly_do = set()
    if not da_khoa:
        ly_do.add("chưa khóa kỳ")
    if can_phan_bo and not da_phan_bo:
        ly_do.add("chưa phân bổ chi phí sản xuất")
    return ly_do


def xep_han(han, ngay):
    """Xếp một khoản theo hạn so với ngày tính: "qua_han", "7" (trong 7 ngày), "30" (ngày 8–30), None (xa hơn)."""
    han, ngay = _ngay(han), _ngay(ngay)
    if han is None:
        return "7"  # không có hạn: coi như đến hạn ngay
    d = (han - ngay).days
    if d < 0:
        return "qua_han"
    if d <= 7:
        return "7"
    if d <= 30:
        return "30"
    return None


def la_noi_bo(ten_doi_tac, la_noi_bo_erp, ten_cac_cty):
    """Đối tác nội bộ: đánh dấu nội bộ trong ERPNext, hoặc trùng tên một đơn vị (so không phân biệt hoa thường)."""
    if la_noi_bo_erp:
        return True
    ten = " ".join(str(ten_doi_tac or "").split()).casefold()
    return any(ten == " ".join(str(c).split()).casefold() for c in ten_cac_cty)


def dong_tien(so_du, khoan_thu, khoan_chi, ngay):
    """so_du: tiền + ngân hàng hiện có. khoan_thu/khoan_chi: [(hạn, số tiền)] (đã loại nội bộ).

    Trả {"so_du", "thu_7", "chi_7", "rong_7", "thu_30", "chi_30", "rong_30", "qua_han_thu", "qua_han_chi"}; cửa sổ 30 ngày
    gồm cả 7 ngày đầu, khoản quá hạn tách riêng (không cộng vào ròng).
    """
    kq = {"so_du": float(so_du or 0), "thu_7": 0.0, "chi_7": 0.0, "thu_30": 0.0, "chi_30": 0.0,
          "qua_han_thu": 0.0, "qua_han_chi": 0.0}
    for loai, ds in (("thu", khoan_thu), ("chi", khoan_chi)):
        for han, tien in ds:
            x = xep_han(han, ngay)
            tien = float(tien or 0)
            if x == "qua_han":
                kq[f"qua_han_{loai}"] += tien
            elif x == "7":
                kq[f"{loai}_7"] += tien
                kq[f"{loai}_30"] += tien
            elif x == "30":
                kq[f"{loai}_30"] += tien
    kq["rong_7"] = kq["so_du"] + kq["thu_7"] - kq["chi_7"]
    kq["rong_30"] = kq["so_du"] + kq["thu_30"] - kq["chi_30"]
    return kq


def qua_han_xac_nhan(ngay_xac_nhan, ngay, so_ngay):
    """R039: khách có số dư mà lần xác nhận công nợ cuối quá `so_ngay` ngày (hoặc chưa từng xác nhận)."""
    if not ngay_xac_nhan:
        return True
    return (_ngay(ngay) - _ngay(ngay_xac_nhan)).days > int(so_ngay)
