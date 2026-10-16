"""Rà bản dịch tiếng Việt CÓ SẴN của Frappe / ERPNext (locale/vi.po) và sinh bản ghi đè cho kh_aph/translations/vi.csv.

Lý do (15/10/2026): bản dịch cộng đồng có lỗi nặng, ví dụ "Delete" trong menu Thao tác dịch thành "Đã cập nhật giá trị mặc định",
"Credit Amount" thành "Số tiền Ghi nợ" (ngược Nợ / Có), "Write Off" thành "Viết tắt". Công cụ gồm:
  1. SUA: bản dịch đúng cho từng chuỗi rà tay (msgid, ngữ cảnh, bản dịch).
  2. QUY_TAC: sửa thuật ngữ theo từ khóa trong msgid (Posting → hạch toán, Opening → đầu kỳ, Credit → Có...).
Chạy:  python tools/sua_ban_dich_frappe.py <thư mục apps của bench> [--ghi]
Không có --ghi: in danh sách thay đổi để rà. Có --ghi: thêm vào vi.csv (bỏ qua chuỗi app đã có bản dịch).
"""
import csv
import pathlib
import re
import sys

VI_CSV = pathlib.Path(__file__).resolve().parents[1] / "kh_aph" / "translations" / "vi.csv"

# (msgid, ngữ cảnh, bản dịch) — rà tay
SUA = [
    ("Delete", "Button in list view actions menu", "Xóa"),
    ("Delete", "Button in web form", "Xóa"),
    ("Delete", "", "Xóa"),
    ("Closing (Cr)", "", "Cuối kỳ (Có)"),
    ("Closing (Dr)", "", "Cuối kỳ (Nợ)"),
    ("Opening (Cr)", "", "Đầu kỳ (Có)"),
    ("Opening (Dr)", "", "Đầu kỳ (Nợ)"),
    ("Credit", "", "Có"),
    ("Credit (Transaction)", "", "Có (tiền giao dịch)"),
    ("Debit (Transaction)", "", "Nợ (tiền giao dịch)"),
    ("Credit ({0})", "", "Có ({0})"),
    ("Debit ({0})", "", "Nợ ({0})"),
    ("Credit Amount", "", "Số tiền Có"),
    ("Debit Amount", "", "Số tiền Nợ"),
    ("Credit Amount in Account Currency", "", "Số tiền Có (tiền tệ tài khoản)"),
    ("Debit Amount in Account Currency", "", "Số tiền Nợ (tiền tệ tài khoản)"),
    ("Credit Amount in Reporting Currency", "", "Số tiền Có (tiền tệ báo cáo)"),
    ("Debit Amount in Reporting Currency", "", "Số tiền Nợ (tiền tệ báo cáo)"),
    ("Credit Amount in Transaction Currency", "", "Số tiền Có (tiền giao dịch)"),
    ("Debit Amount in Transaction Currency", "", "Số tiền Nợ (tiền giao dịch)"),
    ("Credit Note Issued", "", "Đã lập phiếu ghi có"),
    ("Credit Note Amount", "", "Số tiền phiếu ghi có"),
    ("Debit Note Amount", "", "Số tiền phiếu ghi nợ"),
    ("Debit Note Issued", "", "Đã lập phiếu ghi nợ"),
    ("Debit to", "", "Ghi Nợ vào"),
    ("Debit-Credit Mismatch", "", "Lệch Nợ - Có"),
    ("Debit-Credit mismatch", "", "Lệch Nợ - Có"),
    ("Customer Credit Balance", "", "Số dư Có của khách"),
    ("Consolidated Credit Note", "", "Phiếu ghi có tổng hợp"),
    ("Debtors", "", "Phải thu khách hàng"),
    ("Creditors", "", "Phải trả người bán"),
    ("Debtor/Creditor", "", "Phải thu / phải trả"),
    ("Debtor/Creditor Advance", "", "Trả trước / người mua trả trước"),
    ("Against", "", "Đối ứng"),
    ("Against Account", "", "Tài khoản đối ứng"),
    ("Against Voucher", "", "Chứng từ đối ứng"),
    ("Against Voucher Type", "", "Loại chứng từ đối ứng"),
    ("Against Docname", "", "Chứng từ đối ứng"),
    ("Against Doctype", "", "Loại chứng từ đối ứng"),
    ("Accounts Payable", "", "Công nợ phải trả"),
    ("Accounts Receivable", "", "Công nợ phải thu"),
    ("Accounts Payable Summary", "", "Tổng hợp công nợ phải trả"),
    ("Accounts Receivable Summary", "", "Tổng hợp công nợ phải thu"),
    ("Accounts Closing", "", "Khóa sổ kế toán"),
    ("Accounts User", "", "Kế toán viên"),
    ("Accounts Manager", "", "Kế toán trưởng"),
    ("Actual Posting", "", "Hạch toán thực tế"),
    ("Add Child", "", "Thêm nhánh con"),
    ("Ageing Range", "", "Khoảng tuổi nợ"),
    ("Apply To", "", "Áp dụng cho"),
    ("Assignment", "", "Giao việc"),
    ("Assignments", "", "Việc được giao"),
    ("Assignment Completed", "", "Đã hoàn thành việc được giao"),
    ("Assignment Rule", "", "Quy tắc giao việc"),
    ("Assignment Rules", "", "Quy tắc giao việc"),
    ("Assigned By", "", "Người giao"),
    ("Assignee", "", "Người được giao"),
    ("Assign", "", "Giao việc"),
    ("Audit Trail", "", "Nhật ký kiểm tra"),
    ("Average Rate", "", "Đơn giá bình quân"),
    ("Avg Rate", "", "Đơn giá bình quân"),
    ("Balance Qty", "", "Số lượng tồn"),
    ("Billed", "", "Đã lập hóa đơn"),
    ("% Billed", "", "% đã lập hóa đơn"),
    ("Billed Amount", "", "Số tiền đã lập hóa đơn"),
    ("Billed Amt", "", "Số tiền đã lập hóa đơn"),
    ("Billed Qty", "", "Số lượng đã lập hóa đơn"),
    ("Fully Billed", "", "Đã lập hóa đơn đủ"),
    ("Partially Billed", "", "Đã lập hóa đơn một phần"),
    ("Not Billed", "", "Chưa lập hóa đơn"),
    ("Billing", "", "Hóa đơn"),
    ("Billing Address", "", "Địa chỉ xuất hóa đơn"),
    ("Billing Status", "", "Trạng thái lập hóa đơn"),
    ("Billing Rate", "", "Đơn giá xuất hóa đơn"),
    ("Billing Currency", "", "Tiền tệ hóa đơn"),
    ("Blanket Order", "", "Đơn hàng khung"),
    ("BOM Rate", "", "Đơn giá theo định mức"),
    ("Buying Rate", "", "Đơn giá mua"),
    ("Base Rate", "", "Đơn giá (tiền tệ công ty)"),
    ("Condition", "", "Điều kiện"),
    ("Custom?", "", "Tùy chỉnh?"),
    ("Current Asset", "", "Tài sản ngắn hạn"),
    ("Current Assets", "", "Tài sản ngắn hạn"),
    ("dd/mm/yyyy", "", "dd/mm/yyyy"),
    ("dd.mm.yyyy", "", "dd.mm.yyyy"),
    ("'Opening'", "", "'Đầu kỳ'"),
    ("Opening", "", "Đầu kỳ"),
    ("Opening & Closing", "", "Đầu kỳ và cuối kỳ"),
    ("Opening and Closing", "", "Đầu kỳ và cuối kỳ"),
    ("Opening Amount", "", "Số tiền đầu kỳ"),
    ("Opening Date", "", "Ngày đầu kỳ"),
    ("Closing (Opening + Total)", "", "Cuối kỳ (đầu kỳ + phát sinh)"),
    ("Closing [Opening + Total] ", "", "Cuối kỳ [đầu kỳ + phát sinh] "),
    ("Temporary Opening", "", "Đầu kỳ tạm"),
    ("Temporary Opening Account", "", "Tài khoản đầu kỳ tạm"),
    ("Opening Invoice Creation Tool", "", "Công cụ tạo hóa đơn đầu kỳ"),
    ("Opening Invoices", "", "Hóa đơn đầu kỳ"),
    ("Opening Invoices Summary", "", "Tổng hợp hóa đơn đầu kỳ"),
    ("Show Opening Entries", "", "Hiện bút toán đầu kỳ"),
    ("Reconcile", "", "Đối soát"),
    ("Write Off", "", "Xóa nợ"),
    ("Write Off Limit", "", "Hạn mức xóa nợ"),
    ("Ledger", "", "Sổ chi tiết"),
    ("Convert to Ledger", "", "Chuyển thành tài khoản chi tiết"),
    ("Convert to Ledger", "Warehouse", "Chuyển thành kho chi tiết"),
    ("Convert to Group", "Warehouse", "Chuyển thành kho nhóm"),
    ("Customer Ledger", "", "Sổ chi tiết công nợ khách"),
    ("Supplier Ledger", "", "Sổ chi tiết công nợ nhà cung cấp"),
    ("Customer Ledger Summary", "", "Tổng hợp công nợ khách"),
    ("Supplier Ledger Summary", "", "Tổng hợp công nợ nhà cung cấp"),
    ("General Ledger", "", "Sổ cái"),
    ("Journal Entries", "", "Bút toán"),
    ("Journal Entry Type", "", "Loại bút toán"),
    ("Journal Entry Template", "", "Mẫu bút toán"),
    ("Submit", "", "Xác nhận"),
    ("Submit", "Button in list view actions menu", "Xác nhận"),
    ("Submit {0} documents?", "", "Xác nhận {0} chứng từ?"),
    ("Submit {0} documents?", "Title of confirmation dialog", "Xác nhận {0} chứng từ?"),
    ("Submitting", "", "Đang xác nhận"),
    ("You submitted this document", "", "Bạn đã xác nhận chứng từ này"),
    ("You submitted this document {0}", "", "Bạn đã xác nhận chứng từ này {0}"),
    ("{0} submitted this document {1}", "", "{0} đã xác nhận chứng từ này {1}"),
    ("Delivered Items To Be Billed", "", "Hàng đã giao chưa lập hóa đơn"),
    ("Billed Items To Be Received", "", "Hàng đã có hóa đơn chưa nhận"),
    ("Set Posting Date", "", "Sửa ngày hạch toán"),
    ("From Posting Date", "", "Từ ngày hạch toán"),
    ("To Posting Date", "", "Đến ngày hạch toán"),
    ("Invalid Posting Time", "", "Giờ hạch toán không hợp lệ"),
    ("Invoice Posting Date", "", "Ngày hạch toán hóa đơn"),
    ("Stock Settings", "", "Cài đặt kho"),
    ("Please set default UOM in Stock Settings", "", "Đặt đơn vị tính mặc định trong Cài đặt kho"),
    ("Clear Assignment", "Button in list view actions menu", "Bỏ giao việc"),
    ("Apply Assignment Rule", "Button in list view actions menu", "Áp dụng quy tắc giao việc"),
    ("Assign To", "Button in list view actions menu", "Giao việc cho"),
    ("Add Tags", "Button in list view actions menu", "Thêm thẻ"),
    # rà tay đợt 2 (15/10): nghĩa sai rõ
    ("Right", "", "Phải"), ("Right", "alignment", "Phải"), ("Left", "alignment", "Trái"), ("Left", "", "Trái"),
    ("Top", "", "Trên"), ("Top Center", "", "Giữa trên"), ("Margin Bottom", "", "Lề dưới"),
    ("Refreshing...", "", "Đang làm mới..."), ("Sales Pipeline", "", "Phễu bán hàng"),
    ("Selling Rate", "", "Đơn giá bán"), ("Hour Rate", "", "Đơn giá giờ"),
    ("States", "", "Trạng thái"), ("Document States", "", "Trạng thái chứng từ"),
    ("Sub-contracting", "", "Gia công"), ("Subcontract", "", "Gia công"), ("Subcontracting", "", "Gia công"),
    ("Subcontract Order", "", "Đơn gia công"), ("Subcontracting BOM", "", "Định mức gia công"),
    ("Subcontracting Inward", "", "Nhận hàng gia công"), ("Subcontracting Settings", "", "Cài đặt gia công"),
    ("Has Subcontracted", "", "Có gia công"), (" Is Subcontracted", "", " Là gia công"),
    ("Unique", "", "Duy nhất"), ("Write", "", "Sửa"), ("write", "", "sửa"),
    ("Variance", "", "Chênh lệch"), ("Variance ({})", "", "Chênh lệch ({})"),
    ("Voucher Name", "", "Số chứng từ"), ("Work Orders", "", "Lệnh sản xuất"),
    ("POST", "", "POST"), ("GET", "", "GET"), ("PUT", "", "PUT"), ("PATCH", "", "PATCH"), ("HEAD", "", "HEAD"),
    ("Use POST", "", "Dùng POST"),
    ("Sr", "", "STT"), ("Tonne", "", "Tấn"), ("Teaspoon", "", "Thìa cà phê"), ("Sticky", "", "Ghim"),
    ("Table Trimmed", "", "Đã cắt bớt bảng"), ("Tabloid", "", "Tabloid"),
    ("{0} only.", "Money in words", "{0} chẵn."),
    ("Is Single", "", "Là bản ghi đơn"), ("Parent", "", "Cấp trên"), ("Parent Missing", "", "Thiếu cấp trên"),
    ("Plant", "", "Nhà máy"), ("Portrait", "", "Dọc"), ("Landscape", "", "Ngang"), ("Orientation", "", "Hướng giấy"),
    ("Property Setter", "", "Thiết lập thuộc tính"), ("Permission Inspector", "", "Kiểm tra quyền"),
    ("Permission Level", "", "Cấp quyền"), ("Permission Error", "", "Lỗi quyền"), ("Permission Rules", "", "Quy tắc phân quyền"),
    ("Not Like", "", "Không giống"), ("Non Negative", "", "Không âm"),
    ("Float", "", "Số thực"), ("Float Precision", "", "Độ chính xác số thực"), ("Frappe Support", "", "Hỗ trợ Frappe"),
    ("Force", "", "Bắt buộc"), ("From No", "", "Từ số"), ("Include Disabled", "", "Gồm cả đã tắt"),
    ("Designation", "", "Chức danh"), ("Dispatch", "", "Giao hàng"), ("Donut", "", "Biểu đồ vành khuyên"),
    ("Idx", "", "STT"), ("Import Type", "", "Kiểu nhập dữ liệu"), ("Import Warnings", "", "Cảnh báo khi nhập dữ liệu"),
    ("Accepted Warehouse", "", "Kho nhận hàng đạt"), ("Map Columns", "", "Ghép cột"), ("Monospace", "", "Phông đơn cách"),
    ("On Hand", "", "Hiện có"), ("Pass", "", "Đạt"), ("Per Received", "", "% đã nhận"), ("Prorate", "", "Phân bổ theo tỷ lệ"),
    ("Produce Qty", "", "Số lượng sản xuất"), ("Queue", "", "Hàng đợi"), ("Key", "", "Khóa"),
    ("Light Theme", "", "Giao diện sáng"), ("Major", "", "Lớn"), ("Submit button label", "", "Nhãn nút gửi"),
    ("Payment Entries", "", "Phiếu thu / chi"), ("Holiday", "", "Ngày nghỉ"), ("Custody", "", "Giữ hộ"),
]

# Thuật ngữ: msgid chứa từ khóa thì thay cụm sai trong bản dịch (chỉ áp cho chuỗi chưa có trong SUA / vi.csv).
QUY_TAC = [
    (r"\bposting\b", [(r"Ngày đăng", "Ngày hạch toán"), (r"ngày đăng", "ngày hạch toán"), (r"Giờ đăng", "Giờ hạch toán"),
                      (r"giờ đăng", "giờ hạch toán"), (r"\bđăng\b", "hạch toán")]),
    (r"\bopening\b", [(r"[Mm]ục [Mm]ở đầu", "bút toán đầu kỳ"), (r"số dư mở đầu", "số dư đầu kỳ"), (r"[Hh]óa đơn [Mm]ở đầu", "hóa đơn đầu kỳ"),
                      (r"[Hh]óa đơn [Mm]ở\b", "hóa đơn đầu kỳ"), (r"mở đầu", "đầu kỳ")]),
    (r"\bagainst\b", [(r"[Cc]hống lại", "đối ứng")]),
    (r"\breconcil", [(r"[Hh]òa giải", "đối soát")]),
    (r"\bwrite[ -]?off\b", [(r"viết tắt", "xóa nợ"), (r"Viết tắt", "Xóa nợ")]),
    (r"\bsubmit", [(r"\bgửi\b", "xác nhận"), (r"\bGửi\b", "Xác nhận")]),
    (r"\bdebtors?\b", [(r"[Cc]on nợ", "phải thu khách hàng")]),
    (r"\bstock settings\b", [(r"[Cc]ài đặt chứng khoán", "Cài đặt kho")]),
    (r"\bbilled\b", [(r"đã thanh toán", "đã lập hóa đơn"), (r"đã tính", "đã lập hóa đơn")]),
]
# Ngữ cảnh web / bình luận / cổng khách: "Submit" vẫn là "Gửi".
GIU_GUI = re.compile(r"web form|comment|response|portal|quotation|issue|feedback|form to|order|password|button label", re.I)


def doc_po(apps):
    out = []
    for app in ("frappe/frappe", "erpnext/erpnext"):
        s = (pathlib.Path(apps) / app / "locale" / "vi.po").read_text(encoding="utf-8")
        for m in re.finditer(r'(?:msgctxt "((?:[^"\\]|\\.)*)"\n)?msgid "((?:[^"\\]|\\.)*)"\nmsgstr "((?:[^"\\]|\\.)*)"', s):
            c, i, t = m.groups()
            if i and t:
                out.append((i.replace('\\"', '"'), (c or "").replace('\\"', '"'), t.replace('\\"', '"')))
    return out


def de_xuat(po, da_co):
    sua = {(i, c): t for i, c, t in SUA}
    ra = {}
    for i, c, t in po:
        k = (i, c)
        if k in da_co or k in ra:
            continue
        if k in sua:
            if sua[k] != t:
                ra[k] = sua[k]
            continue
        moi = t
        for tu_khoa, thay in QUY_TAC:
            if re.search(tu_khoa, i, re.I):
                if tu_khoa == r"\bsubmit" and (GIU_GUI.search(i) or GIU_GUI.search(c)):
                    continue
                for a, b in thay:
                    moi = re.sub(a, b, moi)
        if moi != t:
            ra[k] = moi[0].upper() + moi[1:] if t[:1].isupper() else moi
    for k, v in sua.items():  # chuỗi trong SUA mà vi.po không có (vẫn ghi đè an toàn)
        if k not in da_co and k not in ra and not any((i, c) == k for i, c, _t in po):
            ra[k] = v
    return ra


def main():
    apps = sys.argv[1]
    rows = list(csv.reader(VI_CSV.open(encoding="utf-8")))
    da_co = {(r[0], r[2] if len(r) == 3 else "") for r in rows}
    ra = de_xuat(doc_po(apps), da_co)
    for (i, c), v in sorted(ra.items()):
        print(f"{i}{' [' + c + ']' if c else ''} => {v}")
    print(len(ra), "chuỗi", file=sys.stderr)
    if "--ghi" in sys.argv:
        with VI_CSV.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
            for (i, c), v in sorted(ra.items()):
                w.writerow([i, v, c] if c else [i, v])


if __name__ == "__main__":
    main()
