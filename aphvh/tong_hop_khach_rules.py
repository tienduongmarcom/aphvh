"""Tổng hợp bán hàng theo khách, nhiều đơn vị (0.4.1) — quy tắc thuần, kiểm thử không cần Frappe.

Chỉ để xem và in cho khách: mỗi đơn vị (APH, VH, HKD Minh Khang) nợ đầu kỳ, từng chứng từ phát sinh
(hóa đơn = phát sinh nợ, phiếu thu / trả hàng = phát sinh có), số dư chạy, nợ cuối kỳ; cuối bảng cộng cả các đơn vị.
Không tạo nghiệp vụ: giao hàng, thu tiền vẫn tách từng đơn vị.
"""

LOAI = {
    "Sales Invoice": "Hóa đơn",
    "Payment Entry": "Phiếu thu/chi",
    "Journal Entry": "Chứng từ khác",
}


VIET_TAT = {"Hóa đơn": "HĐ", "Trả hàng": "TH", "Phiếu thu": "PT", "Phiếu chi": "PC", "Phiếu thu/chi": "PT", "Chứng từ khác": "CT"}


def so_gon(loai, so) -> str:
    """0.4.10 — số chứng từ gọn cho bản in: "Hóa đơn", "ACC-SINV-2026-00043" -> "HĐ 43"; số tự đặt giữ nguyên."""
    import re

    s = str(so or "")
    m = re.search(r"(\d+)$", s)
    if not m or not re.search(r"\d{4}-\d+$", s):
        return s
    return f"{VIET_TAT.get(loai, loai or '')} {int(m.group(1))}".strip()


def dien_giai_gon(text, n=60) -> str:
    t = " ".join(str(text or "").split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def dong_bao_cao(don_vi: list) -> list:
    """don_vi: [{"don_vi", "ten", "dau_ky", "chung_tu": [{"ngay", "loai", "so", "dien_giai", "xuat_hd", "so_hd",
    "tien_hang", "thue", "no", "co"}]}] -> các dòng báo cáo (đã có số dư chạy, dòng đầu kỳ, dòng cộng)."""
    rows = []
    tong = {"dau_ky": 0.0, "tien_hang": 0.0, "thue": 0.0, "no": 0.0, "co": 0.0, "cuoi_ky": 0.0}
    for dv in don_vi or []:
        du = float(dv.get("dau_ky") or 0)
        cts = dv.get("chung_tu") or []
        if not du and not cts:
            continue
        rows.append({"kieu": "dau_ky", "don_vi": dv["don_vi"], "dien_giai": f"{dv.get('ten') or dv['don_vi']} — nợ đầu kỳ", "so_du": du, "indent": 0})
        c = {"tien_hang": 0.0, "thue": 0.0, "no": 0.0, "co": 0.0}
        for ct in cts:
            no, co = float(ct.get("no") or 0), float(ct.get("co") or 0)
            du += no - co
            for k in c:
                c[k] += float(ct.get(k) or 0)
            rows.append(dict(ct, kieu="chung_tu", don_vi=dv["don_vi"], so_du=du, indent=1,
                             so_gon=so_gon(ct.get("loai"), ct.get("so")), dien_giai_gon=dien_giai_gon(ct.get("dien_giai"))))
        rows.append({"kieu": "cong", "don_vi": dv["don_vi"], "dien_giai": f"Cộng {dv.get('ten') or dv['don_vi']} — nợ cuối kỳ",
                     **c, "so_du": du, "indent": 0})
        tong["dau_ky"] += float(dv.get("dau_ky") or 0)
        for k in c:
            tong[k] += c[k]
        tong["cuoi_ky"] += du
    if rows:
        rows.append({"kieu": "tong", "don_vi": "", "dien_giai": "TỔNG CỘNG CÁC ĐƠN VỊ", "tien_hang": tong["tien_hang"], "thue": tong["thue"],
                     "no": tong["no"], "co": tong["co"], "dau_ky": tong["dau_ky"], "so_du": tong["cuoi_ky"], "indent": 0})
    return rows
