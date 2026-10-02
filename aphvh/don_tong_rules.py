"""Đơn tổng (0.3.9) — quy tắc thuần Python, kiểm thử không cần Frappe.

Một đơn của khách lấy hàng của nhiều đơn vị (APH, VH, HKD Minh Khang), mỗi dòng có hoặc không xuất hóa đơn.
Khi xác nhận, app tách thành các Đơn bán hàng chuẩn, mỗi đơn một (đơn vị × có/không hóa đơn): sau đó giao hàng,
lập hóa đơn, thu tiền đi theo luồng chuẩn của từng đơn vị. Đơn tổng gom tình hình của cả nhóm đơn con.
"""


def _get(row, key):
    return row.get(key) if hasattr(row, "get") else getattr(row, key, None)


def group_rows(rows) -> list:
    """Nhóm dòng theo (đơn vị, xuất hóa đơn), giữ thứ tự xuất hiện. -> [((cong_ty, xuat_hd), [rows])]."""
    groups: dict = {}
    for r in rows or []:
        key = (_get(r, "cong_ty"), _get(r, "xuat_hoa_don"))
        groups.setdefault(key, []).append(r)
    return list(groups.items())


def row_problems(rows) -> list:
    """Lỗi dòng trước khi xác nhận: thiếu đơn vị, thiếu có/không HĐ, số lượng hoặc giá không dương."""
    out = []
    for r in rows or []:
        idx = _get(r, "idx")
        if not _get(r, "cong_ty"):
            out.append(f"Dòng {idx}: chưa chọn đơn vị bán")
        if _get(r, "xuat_hoa_don") not in ("Có", "Không"):
            out.append(f"Dòng {idx}: chưa chọn có / không xuất hóa đơn")
        if float(_get(r, "qty") or 0) <= 0:
            out.append(f"Dòng {idx}: số lượng phải lớn hơn 0")
        if float(_get(r, "rate") or 0) < 0:
            out.append(f"Dòng {idx}: đơn giá âm")
    return out


def tong_hop(don_con: list) -> dict:
    """don_con: [{"tong", "da_lap_hd", "da_thu"}, ...] — mỗi đơn con một dòng.

    tong: tiền đơn bán (gồm thuế); da_lap_hd: tiền hóa đơn đã xác nhận; da_thu: tiền đã thu gắn với đơn con
    hoặc hóa đơn của nó (tiền cọc theo đơn được ERPNext chuyển sang hóa đơn khi trừ cọc nên không tính hai lần).
    Còn phải thu = tiền đơn − đã thu.
    """
    t = {"tong": 0.0, "da_lap_hd": 0.0, "chua_lap_hd": 0.0, "da_thu": 0.0}
    for d in don_con or []:
        tong = float(d.get("tong") or 0)
        lap = float(d.get("da_lap_hd") or 0)
        t["tong"] += tong
        t["da_lap_hd"] += lap
        t["chua_lap_hd"] += max(tong - lap, 0.0)
        t["da_thu"] += float(d.get("da_thu") or 0)
    t["con_phai_thu"] = t["tong"] - t["da_thu"]
    return t


# --- 0.4.0: phiếu thu gộp -------------------------------------------------------------------

# Tài khoản nội bộ giữa các đơn vị: NOI_BO[đơn vị ghi sổ][đơn vị đối ứng] = (phải thu, phải trả) — số hiệu TK.
# APH: 13883/33885 với VH, 13884/33886 với HKD (đã thống nhất 1388/3388 chi tiết theo đơn vị);
# VH và HKD: 13881/33881 với APH. Kế toán trưởng xác nhận lại trước khi lên hệ thống chính thức.
NOI_BO = {
    "APH": {"VHT": ("13883", "33885"), "MKT": ("13884", "33886")},
    "VHT": {"APH": ("13881", "33881"), "MKT": ("13884", "33886")},
    "MKT": {"APH": ("13881", "33881"), "VHT": ("13883", "33885")},
}


def tk_noi_bo(cong_ty: str, doi_ung: str) -> tuple:
    """(phải thu, phải trả) của `cong_ty` với `doi_ung`; KeyError nếu chưa khai báo."""
    return NOI_BO[cong_ty][doi_ung]


def phan_bo_thu_gop(so_tien, don_vi_nhan: str, cho_thu: list) -> dict:
    """Chia tiền khách trả một lần cho các khoản còn phải thu của đơn tổng.

    cho_thu: [{"cong_ty", "loai": "SI" | "SO", "ten", "con_lai", "ngay"}]. Thứ tự: hóa đơn trước đơn chưa lập hóa đơn;
    trong mỗi loại, đơn vị nhận tiền trước rồi đơn vị khác; cùng nhóm thì ngày cũ trước.
    -> {"dong": [{"cong_ty", "loai", "ten", "so_tien"}], "tra_truoc": phần thừa (ghi trả trước tại đơn vị nhận)}.
    """
    con = round(float(so_tien or 0), 2)
    if con <= 0:
        raise ValueError("Số tiền thu phải lớn hơn 0")
    thu_tu = sorted(
        [c for c in cho_thu or [] if float(c.get("con_lai") or 0) > 0],
        key=lambda c: (c["loai"] != "SI", c["cong_ty"] != don_vi_nhan, str(c.get("ngay") or ""), c["ten"]),
    )
    dong = []
    for c in thu_tu:
        if con <= 0:
            break
        a = round(min(con, float(c["con_lai"])), 2)
        dong.append({"cong_ty": c["cong_ty"], "loai": c["loai"], "ten": c["ten"], "so_tien": a})
        con = round(con - a, 2)
    return {"dong": dong, "tra_truoc": con}
