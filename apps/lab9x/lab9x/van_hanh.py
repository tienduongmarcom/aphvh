"""Quy tắc thuần lượt 0.13 (lõi 9xLab): chênh lệch kiểm kê bước 2, đề nghị bổ sung hàng, giá sàn, thu tiền nhanh,
thu hồi nợ. Không import frappe.
"""

# ---------------------------------------------------------------- chênh lệch kiểm kê bước 2 (rà soát pháp lý dòng 16)

# phương án -> (bên, TK Nợ, TK Có); "thieu" giảm 1381, "thua" giảm 3381. Số hiệu là gốc; app tìm TK lá theo số hiệu.
PHUONG_AN = {
    "Thiếu: ghi giá vốn (hao hụt)": ("thieu", "632", "1381"),
    "Thiếu: cá nhân bồi thường": ("thieu", "1388", "1381"),
    "Thừa: trả lại người khác": ("thua", "3381", "3388"),
    "Thừa: không rõ chủ, ghi thu nhập khác": ("thua", "3381", "711"),
}


def kiem_xu_ly(con_thieu, con_thua, dong):
    """dong: [(phuong_an, so_tien)]. Trả danh sách lỗi; mỗi bên không vượt số còn chờ xử lý của vụ."""
    loi, dung = [], {"thieu": 0.0, "thua": 0.0}
    for i, (pa, tien) in enumerate(dong, 1):
        if pa not in PHUONG_AN:
            loi.append(f"Dòng {i}: phương án \"{pa}\" không hợp lệ")
            continue
        if not tien or tien <= 0:
            loi.append(f"Dòng {i}: số tiền phải lớn hơn 0")
            continue
        dung[PHUONG_AN[pa][0]] += tien
    if dung["thieu"] > round(con_thieu or 0, 2) + 0.5:
        loi.append(f"Tổng xử lý thiếu {dung['thieu']:,.0f} vượt số còn chờ {con_thieu or 0:,.0f}")
    if dung["thua"] > round(con_thua or 0, 2) + 0.5:
        loi.append(f"Tổng xử lý thừa {dung['thua']:,.0f} vượt số còn chờ {con_thua or 0:,.0f}")
    return loi


# ---------------------------------------------------------------- đề nghị bổ sung (R057)

def kha_dung(ton, da_giu=0, thieu_cho_xu_ly=0):
    """R056: thiếu đang chờ xử lý làm giảm lượng có thể bán; không âm."""
    return max(0.0, (ton or 0) - (da_giu or 0) - (thieu_cho_xu_ly or 0))


def so_de_nghi(kha, dang_ve, nguong, so_dat):
    """Dưới ngưỡng (tính cả hàng đang về) thì đề nghị đủ lên ngưỡng, tối thiểu bằng số đặt lại khai trên mã."""
    co = (kha or 0) + (dang_ve or 0)
    if not nguong or co >= nguong:
        return 0.0
    return max(nguong - co, so_dat or 0)


# ---------------------------------------------------------------- giá sàn (R011, rà soát dòng 19)

def phan_tram_duoi_san(gia, san):
    """% thấp hơn giá sàn (0 nếu không dưới sàn hoặc chưa có giá sàn)."""
    if not san or san <= 0 or gia is None or gia >= san:
        return 0.0
    return round((san - gia) / san * 100, 4)


def quyen_duyet(nguoi, chu_don, cong_ty, muc_can, bang):
    """bang: [{"user", "muc", "cong_ty", "tu_duyet"}]. Trả (được, lý do). muc None/0 = không giới hạn."""
    dong = [b for b in bang if b.get("user") == nguoi and (not b.get("cong_ty") or b.get("cong_ty") == cong_ty)]
    if not dong:
        return False, "Bạn không có trong bảng người duyệt giá dưới sàn của đơn vị này"
    if nguoi == chu_don and not any(b.get("tu_duyet") for b in dong):
        return False, "Bạn không được tự duyệt đơn mình lập"
    muc = [b.get("muc") for b in dong if (nguoi != chu_don or b.get("tu_duyet"))]
    if any(not m for m in muc):
        return True, ""
    cao = max(muc)
    if muc_can > cao + 1e-9:
        return False, f"Đơn dưới sàn {muc_can:g}% vượt mức bạn được duyệt ({cao:g}%)"
    return True, ""


# ---------------------------------------------------------------- thu tiền nhanh, thu hồi nợ

def tach_thu(tien_mat, chuyen_khoan, ma_gd):
    """Trả [(hình thức, số tiền)] hoặc ném ValueError."""
    tm, ck = float(tien_mat or 0), float(chuyen_khoan or 0)
    if tm < 0 or ck < 0 or tm + ck <= 0:
        raise ValueError("Nhập số tiền mặt hoặc chuyển khoản lớn hơn 0")
    if ck and not (ma_gd or "").strip():
        raise ValueError("Chuyển khoản cần mã giao dịch hoặc nội dung chuyển khoản")
    return [x for x in (("Tiền mặt", tm), ("Chuyển khoản", ck)) if x[1]]


def phan_bo(so_tien, hoa_don):
    """Phân bổ vào đúng các hóa đơn được chọn theo thứ tự đã chọn (không tự FIFO toàn bộ công nợ).
    hoa_don: [(tên, còn nợ)]. Trả ([(tên, phân bổ)], phần dư chưa phân bổ)."""
    con, out = round(so_tien, 2), []
    for ten, no in hoa_don:
        if con <= 0:
            break
        a = round(min(con, no or 0), 2)
        if a > 0:
            out.append((ten, a))
            con = round(con - a, 2)
    return out, con


def can_goi(con_no, qua_han, den_han_3_ngay, hen_tra, hom_nay, ngay_xac_nhan, so_ngay_xac_nhan=30):
    """Lý do đưa khách vào danh sách gọi hôm nay (rỗng = không cần gọi). Ngày là date hoặc None."""
    if not con_no or con_no <= 0.5:
        return []
    ly_do = []
    if qua_han and qua_han > 0.5:
        ly_do.append("Quá hạn")
    if den_han_3_ngay and den_han_3_ngay > 0.5:
        ly_do.append("Sắp đến hạn")
    if hen_tra and hen_tra <= hom_nay:
        ly_do.append("Đến ngày hẹn trả")
    if not ngay_xac_nhan or (hom_nay - ngay_xac_nhan).days > so_ngay_xac_nhan:
        ly_do.append("Lâu chưa xác nhận công nợ")
    if hen_tra and hen_tra > hom_nay and ly_do:
        # đã hẹn ngày trả sau hôm nay: chỉ gọi lại khi đến hẹn (trừ khi quá hạn)
        ly_do = [x for x in ly_do if x == "Quá hạn"]
    return ly_do
