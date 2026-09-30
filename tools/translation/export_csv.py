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
    # 0.2.4 (30/09): cột/bộ lọc báo cáo kho, thông báo Python/JS kho + mua hàng, mô tả trường, màn hình Dũng.
    # Rà 6 phần song song + kiểm định độc lập (v024/BRIEF.md). Dòng có ngữ cảnh (msgctxt) ghi cột thứ 3.
    rows24 = json.load(open(os.path.join(H, 'v024', 'final_rows_024.json')))
    for r in sorted(rows24, key=lambda r: (r['en'].lower(), r['ctx'])):
        src, ctx, fin, cur = r['en'], r.get('ctx') or '', (r['final'] or '').strip(), (r['cur'] or '').strip()
        key = src + ('\x00' + ctx if ctx else '')
        if not fin or fin == cur or key in seen or (not cur and fin == src):
            continue
        seen.add(key)
        row = [src.replace('\n', '\\n'), fin.replace('\n', '\\n')]
        w.writerow(row + [ctx] if ctx else row)
        n += 1
    EXTRA24 = {'Stock Reservation Entry': 'Phiếu giữ chỗ tồn kho', 'Inventory Dimension': 'Chiều phân tích tồn kho',
               'Stock Closing Entry': 'Phiếu khóa sổ kho', 'Period Closing Voucher': 'Chứng từ khóa sổ cuối kỳ',
               'Repost Item Valuation': 'Tính lại giá vốn mặt hàng', 'Accounts Settings': 'Cài đặt kế toán',
               'Buying Settings': 'Cài đặt mua hàng', 'Serial and Batch Bundle': 'Gói serial/lô'}
    for k, v in EXTRA24.items():
        if k not in seen:
            w.writerow([k, v]); seen.add(k); n += 1
print(out, n)
