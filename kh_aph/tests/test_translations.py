"""Kiểm tra tệp bản dịch vi.csv của app (không cần Frappe)."""
import csv, os, re, unittest

PATH = os.path.join(os.path.dirname(__file__), '..', 'translations', 'vi.csv')


def load():
    with open(PATH, encoding='utf-8', newline='') as f:
        return list(csv.reader(f))


class TestViCsv(unittest.TestCase):
    def test_shape(self):
        rows = load()
        self.assertGreater(len(rows), 600)
        keys = [(r[0], r[2] if len(r) > 2 else '') for r in rows]
        self.assertEqual(len(keys), len(set(keys)), 'trùng chuỗi nguồn')
        for r in rows:
            self.assertIn(len(r), (2, 3), r)
            self.assertTrue(r[0].strip() and r[1].strip(), r)
            if len(r) == 3:
                self.assertTrue(r[2].strip(), r)

    def test_placeholders_kept(self):
        for src, vi, *_ in load():
            self.assertEqual(sorted(re.findall(r'\{\d*\}|%s', src)), sorted(re.findall(r'\{\d*\}|%s', vi)), src)

    def test_no_known_mistranslations(self):
        for src, vi, *_ in load():
            low = vi.lower()
            self.assertNotIn('chứng khoán', low, src)
            self.assertNotIn('tỷ giá định giá', low, src)
            self.assertNotIn('cổ phiếu', low, src)
            self.assertNotIn('hoá', low, src)
            if re.search(r'\bBill(ed|ing)?\b', src) and 'Not Billed' not in src and 'Bill No' not in src and 'Bill Date' not in src:
                self.assertNotIn('thanh toán', low, src)
            if src in ('Credit', 'Credit in Company Currency', 'Credit To'):
                self.assertNotIn('nợ', low, src)

    def test_decided_terms(self):
        d = {r[0]: r[1] for r in load() if len(r) == 2}
        expect = {
            'Stock Reconciliation': 'Điều chỉnh theo kiểm kê', 'Opening Stock': 'Nhập số dư đầu kỳ',
            'BOM': 'Định mức nguyên vật liệu', 'Submit': 'Xác nhận', 'Valuation Rate': 'Đơn giá vốn',
            'Purchase Receipt': 'Phiếu nhập mua hàng', 'Stock Entry': 'Phiếu kho', 'Delete': 'Xóa',
            'Credit in Company Currency': 'Có (tiền tệ công ty)', 'Clearance Date': 'Ngày ngân hàng ghi nhận',
            'Stock Received But Not Billed': 'Hàng đã nhận chưa nhận hóa đơn', 'Excise Entry': 'Bút toán Excise',
            # 0.2.4
            'Opening Qty': 'SL đầu kỳ', 'In Qty': 'SL nhập', 'Out Qty': 'SL xuất', 'Balance Qty': 'SL tồn cuối',
            'Lead': 'Khách hàng tiềm năng', 'Subcontracting': 'Gia công', 'Serial and Batch Bundle': 'Gói serial/lô',
            # 0.4.16: sửa bản dịch sai nghĩa Nợ/Có của ERPNext
            'Debit To': 'Ghi Nợ tài khoản (phải thu)', 'Credit To': 'Ghi Có tài khoản (phải trả)',
            'Debit Account': 'Tài khoản ghi Nợ', 'Credit Account': 'Tài khoản ghi Có', 'Territory': 'Khu vực',
            'Base Total Billed Amount': 'Tổng giá trị đã lập hóa đơn (tiền tệ công ty)',
            'Please select Company and Posting Date to getting entries': 'Chọn Công ty và Ngày hạch toán để lấy các bút toán.',
            'Please set opening number of booked depreciations': 'Nhập số kỳ khấu hao đã hạch toán trước đầu kỳ.',
        }
        ctx = {(r[0], r[2]): r[1] for r in load() if len(r) == 3}
        self.assertEqual(ctx.get(('No.', "Title of the 'row number' column")), 'STT')
        for k, v in expect.items():
            self.assertEqual(d.get(k), v, k)


if __name__ == '__main__':
    unittest.main()
