"""Ghép mẫu in (.html + .css chung) vào tệp .json mà Frappe đồng bộ khi migrate.

Chạy lại sau mỗi lần sửa .html/.css:  python tools/build_print_formats.py
Kiểm thử tests/test_print_formats.py báo lỗi nếu .json lệch với nguồn.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / "kh_aph" / "kh_aph" / "print_format"
# Frappe chỉ nạp lại mẫu in khi "modified" mới hơn bản trên site: sửa mẫu nào thì tăng mốc này.
MODIFIED = "2026-10-14 14:00:00.000000"

FORMATS = {
    "phieu_nhap_kho": ("Phiếu nhập kho", "Purchase Receipt"),
    "phieu_kho": ("Phiếu kho", "Stock Entry"),
    "phieu_xuat_kho_ban_hang": ("Phiếu xuất kho bán hàng", "Delivery Note"),
    "bien_ban_giao_nhan": ("Biên bản giao nhận", "Delivery Note"),
    "phieu_thu_chi": ("Phiếu thu chi", "Payment Entry"),
    "phieu_ban_hang": ("Phiếu bán hàng", "Sales Invoice"),
}


def build_doc(folder: str) -> dict:
    name, doc_type = FORMATS[folder]
    return {
        "absolute_value": 0,
        "align_labels_right": 0,
        "creation": MODIFIED,
        "css": (ROOT / "phieu_in.css").read_text(encoding="utf-8"),
        "custom_format": 1,
        "default_print_language": "vi",
        "disabled": 0,
        "doc_type": doc_type,
        "docstatus": 0,
        "doctype": "Print Format",
        "font_size": 0,
        "html": (ROOT / folder / f"{folder}.html").read_text(encoding="utf-8"),
        "idx": 0,
        "line_breaks": 0,
        "margin_bottom": 12.0,
        "margin_left": 12.0,
        "margin_right": 12.0,
        "margin_top": 12.0,
        "modified": MODIFIED,
        "modified_by": "Administrator",
        "module": "Kh Aph",
        "name": name,
        "owner": "Administrator",
        "page_number": "Hide",
        "print_format_builder": 0,
        "print_format_builder_beta": 0,
        "print_format_type": "Jinja",
        "raw_printing": 0,
        "show_section_headings": 0,
        "standard": "Yes",
    }


def main():
    for folder in FORMATS:
        path = ROOT / folder / f"{folder}.json"
        path.write_text(json.dumps(build_doc(folder), ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote", path.relative_to(ROOT.parents[2]))


if __name__ == "__main__":
    main()
