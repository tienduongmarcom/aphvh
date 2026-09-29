"""Xuất bản dịch chốt (final_rows.json) ra aphvh/translations/vi.csv.

Frappe nạp translations/<lang>.csv của từng app theo thứ tự cài đặt (frappe → erpnext → aphvh), nên
bản của aphvh đè bản chính thức. Chỉ ghi các chuỗi có bản chốt khác bản ERPNext đang hiện.
"""
import csv, json, os
H = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(H, 'final_rows.json')))
out = os.path.join(H, '..', '..', 'aphvh', 'translations', 'vi.csv')
seen, n = set(), 0
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n', quoting=csv.QUOTE_ALL)
    for r in sorted(rows, key=lambda r: r['src'].lower()):
        src, fin, cur = r['src'], (r['final'] or '').strip(), (r['cur'] or '').strip()
        if not fin or fin == cur or src in seen or (not cur and fin == src):
            continue
        seen.add(src)
        w.writerow([src.replace('\n', '\\n'), fin.replace('\n', '\\n')])
        n += 1
    # Thuật ngữ đã chốt nhưng không nằm trên màn hình Dung (vẫn áp cho toàn hệ thống)
    EXTRA = {'BOM': 'Định mức nguyên vật liệu', 'Raw Material': 'Nguyên vật liệu', 'Naming Series': 'Ký hiệu chứng từ',
             'Balance Sheet': 'Báo cáo tình hình tài chính',
             # Nút trên màn hình Dung (trường kiểu Button, kiểm tra trên 8080 ngày 29/09)
             'Update Rate and Availability': 'Cập nhật đơn giá và tồn kho khả dụng', 'Get Items': 'Lấy hàng',
             'Add Serial / Batch No': 'Thêm Serial / số lô', 'Add Serial / Batch No (Rejected Qty)': 'Thêm Serial / số lô (SL không đạt)',
             'Landed Cost Help': 'Hướng dẫn chi phí nhập hàng', 'Make Difference Entry': 'Tạo bút toán chênh lệch',
             'Get Outstanding Invoices': 'Lấy hóa đơn còn nợ'}
    for k, v in EXTRA.items():
        if k not in seen:
            w.writerow([k, v]); seen.add(k); n += 1
print(out, n)
