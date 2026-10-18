"""Tồn kho theo TÀI KHOẢN × ĐỊA ĐIỂM (0.4.18) — quy tắc thuần, kiểm thử không cần Frappe.

Kho chỉ cho biết hàng nằm ở đâu; tài khoản kho (152/153/154/155/156) lấy theo mặt hàng / nhóm hàng. Báo cáo này ghép hai chiều
cho kế toán: mỗi tài khoản, mỗi địa điểm (nhóm kho cấp trên cùng: Hà Nội, Đà Nẵng, Nhà máy…) là bao nhiêu tiền, và tổng từng
tài khoản so với số dư sổ cái cùng ngày.
"""

KHONG_RO = "(chưa gắn tài khoản kho)"
KHAC = "(kho ngoài các nhóm địa điểm)"


def dia_diem(kho: str, cha: dict, goc: set) -> str:
    """Tên nhóm kho nằm ngay dưới gốc cây kho của công ty. cha: {kho: kho cấp trên | None}; goc: tên các kho gốc."""
    cur, seen = kho, set()
    while cur and cur not in seen:
        seen.add(cur)
        up = cha.get(cur)
        if not up or up in goc:
            return cur
        cur = up
    return KHAC


def tai_khoan(mac_dinh_mat_hang, mac_dinh_nhom, mac_dinh_cong_ty):
    """Thứ tự ERPNext v16: mặt hàng → nhóm hàng → mặc định công ty."""
    return mac_dinh_mat_hang or mac_dinh_nhom or mac_dinh_cong_ty or KHONG_RO


def tong_hop(dong, so_cai: dict, ten_dia_diem=lambda x: x) -> list:
    """dong: [{"tk", "dia_diem", "gia_tri"}]; so_cai: {tk: số dư sổ cái}.
    -> các dòng: từng (tk, địa điểm), cuối mỗi tk có dòng tổng kèm số sổ cái và chênh lệch; cuối cùng dòng tổng cộng."""
    by = {}
    for d in dong:
        by.setdefault(d["tk"], {}).setdefault(d["dia_diem"], 0.0)
        by[d["tk"]][d["dia_diem"]] += float(d["gia_tri"] or 0)
    out, tong, tong_sc = [], 0.0, 0.0
    for tk in sorted(set(by) | set(so_cai)):
        ct = by.get(tk, {})
        s = 0.0
        for dd in sorted(ct):
            out.append({"tk": tk, "dia_diem": ten_dia_diem(dd), "gia_tri": round(ct[dd], 2), "kieu": "chi_tiet"})
            s += ct[dd]
        sc = float(so_cai.get(tk, 0) or 0)
        out.append({"tk": tk, "dia_diem": "Cộng tài khoản", "gia_tri": round(s, 2), "so_cai": round(sc, 2),
                    "chenh_lech": round(s - sc, 2), "kieu": "tong_tk"})
        tong += s
        tong_sc += sc
    out.append({"tk": "", "dia_diem": "TỔNG CỘNG", "gia_tri": round(tong, 2), "so_cai": round(tong_sc, 2),
                "chenh_lech": round(tong - tong_sc, 2), "kieu": "tong"})
    return out
