"""Mã khách / mã nhà cung cấp (lõi 9xLab, từ 0.14). Không import frappe.

Mã đưa vào (nhập tay hoặc nhập từ Excel, ví dụ KH0000069 của MISA) giữ NGUYÊN làm mã trong hệ thống. Không có mã thì app cấp
mã tiếp theo cùng kiểu: tiền tố + số, độ dài số theo mã lớn nhất đang có (mặc định 7: KH0000001).
"""
import re

DO_DAI = 7


def chuan_hoa(ma):
    """Bỏ khoảng trắng hai đầu; giữ nguyên mọi ký tự khác (kể cả số 0 đứng đầu, chữ thường / hoa)."""
    return str(ma).strip() if ma is not None else ""


def kiem(ma):
    """Trả lỗi (chuỗi) hoặc ''. Frappe không nhận tên có các ký tự này."""
    if not ma:
        return ""
    if len(ma) > 140:
        return "Mã dài quá 140 ký tự"
    bad = [c for c in "%<>\"'\\" if c in ma] + (["xuống dòng"] if "\n" in ma or "\r" in ma else [])
    return ("Mã có ký tự không dùng được: " + " ".join(bad)) if bad else ""


def ma_tiep(tien_to, ma_co, do_dai=DO_DAI):
    """Mã tiếp theo sau mã lớn nhất dạng <tien_to><số> trong ma_co (giữ độ dài số của mã đang có)."""
    mau = re.compile("^" + re.escape(tien_to) + r"(\d+)$")
    so = [(int(m.group(1)), len(m.group(1))) for m in (mau.match(x or "") for x in ma_co) if m]
    lon, dai = max(so) if so else (0, do_dai)
    dai = max(dai, len(str(lon + 1)))
    return f"{tien_to}{lon + 1:0{dai}d}"
