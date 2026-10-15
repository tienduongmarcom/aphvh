"""Quy tắc thuần lượt 0.14 (lõi 9xLab): tài khoản ngân hàng khai trong cấu hình khách, sổ quỹ / sổ tiền gửi (tồn sau
từng phiếu), lãi vay theo khế ước, lịch đến hạn, đọc và đối chiếu sao kê ngân hàng. Không import frappe.
"""
import datetime
import re

LOAI_TIEN = {"VND": "1121", "USD": "1122"}
SO_CUOI_RE = re.compile(r"^\d{4}$")


# ---------------------------------------------------------------- tài khoản ngân hàng (mục 3)

def kiem_ngan_hang(ds, abbrs):
    """ds: [{don_vi, ngan_hang, so_cuoi, loai_tien}]. Trả danh sách lỗi. Không nhận số tài khoản đầy đủ (repo công khai)."""
    loi, thay = [], set()
    for i, r in enumerate(ds or [], 1):
        dv, nh, so, lt = (str(r.get(k) or "").strip() for k in ("don_vi", "ngan_hang", "so_cuoi", "loai_tien"))
        lt = lt or "VND"
        if dv not in abbrs:
            loi.append(f"dòng {i}: đơn vị \"{dv}\" không có trong 'cong_ty'")
        if not nh:
            loi.append(f"dòng {i}: thiếu 'ngan_hang'")
        if not SO_CUOI_RE.match(so):
            loi.append(f"dòng {i}: 'so_cuoi' phải đúng 4 chữ số (không khai số tài khoản đầy đủ)")
        if lt not in LOAI_TIEN:
            loi.append(f"dòng {i}: 'loai_tien' phải là VND hoặc USD")
        if set(r) - {"don_vi", "ngan_hang", "so_cuoi", "loai_tien", "ghi_chu"}:
            loi.append(f"dòng {i}: khóa lạ " + ", ".join(sorted(set(r) - {"don_vi", "ngan_hang", "so_cuoi", "loai_tien", "ghi_chu"})))
        k = (dv, nh.upper(), so, lt)
        if k in thay:
            loi.append(f"dòng {i}: trùng {dv} {nh} {so} {lt}")
        thay.add(k)
    return loi


def ten_tk(ngan_hang, so_cuoi, loai_tien="VND"):
    t = f"{ngan_hang.strip()} {so_cuoi}"
    return t + " USD" if (loai_tien or "VND") == "USD" else t


def so_hieu_moi(goc, so_co):
    """Số hiệu chi tiết còn trống dưới gốc (1121 -> 112101..112199)."""
    for n in range(1, 100):
        s = f"{goc}{n:02d}"
        if s not in so_co:
            return s
    return None


# ---------------------------------------------------------------- sổ quỹ / sổ tiền gửi (mục 4)

def so_ton(dau_ky, phieu):
    """phieu: [{ngay, so, dien_giai, thu, chi}] đã xếp. Trả (dòng có 'ton' sau từng phiếu, tổng thu, tổng chi, cuối kỳ)."""
    ton, out, thu, chi = round(dau_ky or 0, 2), [], 0.0, 0.0
    for p in phieu:
        t, c = round(p.get("thu") or 0, 2), round(p.get("chi") or 0, 2)
        ton = round(ton + t - c, 2)
        thu, chi = thu + t, chi + c
        out.append({**p, "thu": t, "chi": c, "ton": ton})
    return out, round(thu, 2), round(chi, 2), ton


# ---------------------------------------------------------------- vay (mục 6)

def _d(x):
    return x if isinstance(x, datetime.date) else datetime.date.fromisoformat(str(x)[:10])


def lai(du_no, lai_suat_nam, so_ngay, ngay_nam=365):
    """Lãi đơn theo ngày: dư nợ × lãi suất %/năm × số ngày / 365, làm tròn đồng."""
    if not du_no or not lai_suat_nam or so_ngay <= 0:
        return 0.0
    return float(round(du_no * lai_suat_nam / 100 * so_ngay / ngay_nam))


def lai_ky(bien_dong, lai_suat_nam, tu, den):
    """Lãi phát sinh trong [tu, den] (cả hai đầu) theo dư nợ thực từng ngày.

    bien_dong: [(ngay, so_tien)] gốc nhận (+) / trả (−), mọi thời điểm. Ngày nhận vay tính lãi, ngày trả không tính phần trả.
    Trả (lãi, dư nợ cuối)."""
    tu, den = _d(tu), _d(den)
    if den < tu:
        return 0.0, 0.0
    bd = sorted(((_d(n), t) for n, t in bien_dong), key=lambda x: x[0])
    du = sum(t for n, t in bd if n < tu)
    trong = [(n, t) for n, t in bd if tu <= n <= den]
    tong, moc = 0.0, tu
    for n, t in trong:
        tong += lai(du, lai_suat_nam, (n - moc).days)
        du += t
        moc = n
    tong += lai(du, lai_suat_nam, (den - moc).days + 1)
    return float(round(tong)), round(du, 2)


def nhom_han(ngay_den_han, hom_nay):
    if not ngay_den_han:
        return ""
    con = (_d(ngay_den_han) - _d(hom_nay)).days
    if con < 0:
        return "Quá hạn"
    for moc in (7, 30, 90):
        if con <= moc:
            return f"Trong {moc} ngày"
    return "Sau 90 ngày"


def tai_khoan_vay(ngay_vay, ngay_den_han):
    """TT133/TT99: 3411 cho cả ngắn và dài hạn; phân loại trình bày theo kỳ hạn (≤ 12 tháng là ngắn hạn)."""
    if not ngay_vay or not ngay_den_han:
        return "Ngắn hạn"
    return "Ngắn hạn" if (_d(ngay_den_han) - _d(ngay_vay)).days <= 366 else "Dài hạn"


# ---------------------------------------------------------------- sao kê (mục 7)

COT = ("ngay", "ma", "noi_dung", "ghi_no", "ghi_co")


def so(x):
    """Đọc số tiền trên sao kê VN: '1.234.567', '1,234,567', '1.234.567,50', '(1.000)', '-1000', số thực."""
    if x is None or x == "":
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(" ", "").replace(" ", "").replace("VND", "").replace("đ", "")
    am = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = s.strip("()-+")
    if not s:
        return 0.0
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3):
        s = s.replace(".", "")
    elif s.count(",") > 1 or (s.count(",") == 1 and len(s.split(",")[1]) == 3):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    v = float(s)
    return -v if am else v


def ngay(x):
    """dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd, có thể kèm giờ; date/datetime giữ nguyên."""
    if isinstance(x, datetime.datetime):
        return x.date()
    if isinstance(x, datetime.date):
        return x
    s = str(x or "").strip().split(" ")[0]
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return datetime.date(int(m[1]), int(m[2]), int(m[3]))
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", s)
    if m:
        y = int(m[3])
        return datetime.date(y + 2000 if y < 100 else y, int(m[2]), int(m[1]))
    return None


def _chi_so(tieu_de, cot):
    """cot: số thứ tự cột (bắt đầu 1) hoặc tên tiêu đề (không phân biệt hoa thường)."""
    if cot in (None, ""):
        return None
    if isinstance(cot, int) or str(cot).isdigit():
        return int(cot) - 1
    t = [str(h or "").strip().lower() for h in tieu_de]
    c = str(cot).strip().lower()
    return t.index(c) if c in t else None


def doc_sao_ke(bang, anh_xa):
    """bang: danh sách dòng (list). anh_xa: {dong_tieu_de (1-based), ngay, ma, noi_dung, ghi_no, ghi_co} — cột theo số
    hoặc tên. Trả (dòng chuẩn, lỗi). so_tien > 0 là tiền vào (ghi có trên sao kê), < 0 là tiền ra."""
    hd = int(anh_xa.get("dong_tieu_de") or 1)
    if hd > len(bang):
        return [], ["Tệp không có dòng tiêu đề như mẫu"]
    tieu_de = bang[hd - 1]
    ci, loi = {}, []
    for k in COT:
        ci[k] = _chi_so(tieu_de, anh_xa.get(k))
        if ci[k] is None and k in ("ngay", "ghi_no", "ghi_co"):
            loi.append(f"Không thấy cột '{anh_xa.get(k)}' cho {k}")
    if loi:
        return [], loi
    out = []
    for i, r in enumerate(bang[hd:], hd + 1):
        def o(k):
            j = ci[k]
            return r[j] if j is not None and j < len(r) else None
        n = ngay(o("ngay"))
        if not n:
            if any(str(x or "").strip() for x in r):
                continue  # dòng cộng / chú thích
            continue
        try:
            vao, ra = so(o("ghi_co")), so(o("ghi_no"))
        except ValueError:
            loi.append(f"Dòng {i}: số tiền không đọc được")
            continue
        tien = round(vao - ra, 2)
        if not tien:
            continue
        out.append({"dong": i, "ngay": n, "ma": str(o("ma") or "").strip(), "noi_dung": str(o("noi_dung") or "").strip(),
                    "so_tien": tien})
    return out, loi


def khop_sao_ke(dong, so_sach, sai_ngay=2):
    """dong: kết quả doc_sao_ke. so_sach: [{chung_tu, ma, ngay, so_tien (+ thu / − chi)}] đã ghi trên tài khoản.

    Trạng thái: "Khớp" (cùng mã, cùng số tiền, ngày lệch ≤ sai_ngay; hoặc không mã mà cùng số tiền, ngày ±sai_ngay và
    chỉ một chứng từ phù hợp), "Lệch" (cùng mã khác số tiền / ngày), "Trùng" (mã lặp trên sao kê hoặc đã ghi ở hơn
    một chứng từ), "Chưa ghi sổ". Mỗi chứng từ chỉ khớp một lần."""
    dung, ket, dem = set(), [], {}
    for d in dong:
        if d["ma"]:
            dem[d["ma"]] = dem.get(d["ma"], 0) + 1
    theo_ma = {}
    for i, s in enumerate(so_sach):
        if s.get("ma"):
            theo_ma.setdefault(str(s["ma"]).strip(), []).append(i)
    for d in dong:
        kq = {**d, "trang_thai": "Chưa ghi sổ", "chung_tu": None}
        if d["ma"] and dem[d["ma"]] > 1:
            kq["trang_thai"] = "Trùng"
            ket.append(kq)
            continue
        ung = [i for i in theo_ma.get(d["ma"], []) if i not in dung] if d["ma"] else []
        if len(theo_ma.get(d["ma"], [])) > 1:
            kq.update(trang_thai="Trùng", chung_tu=", ".join(so_sach[i]["chung_tu"] for i in theo_ma[d["ma"]]))
        elif ung:
            s = so_sach[ung[0]]
            dung.add(ung[0])
            lech = abs(round(s["so_tien"] - d["so_tien"], 2)) > 0.5 or abs((_d(s["ngay"]) - d["ngay"]).days) > sai_ngay
            kq.update(trang_thai="Lệch" if lech else "Khớp", chung_tu=s["chung_tu"])
        else:
            hop = [i for i, s in enumerate(so_sach) if i not in dung and not s.get("ma")
                   and abs(round(s["so_tien"] - d["so_tien"], 2)) <= 0.5 and abs((_d(s["ngay"]) - d["ngay"]).days) <= sai_ngay]
            if len(hop) == 1:
                dung.add(hop[0])
                kq.update(trang_thai="Khớp", chung_tu=so_sach[hop[0]]["chung_tu"])
        ket.append(kq)
    return ket
