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
        srcs = [r[0] for r in rows]
        self.assertEqual(len(srcs), len(set(srcs)), 'trùng chuỗi nguồn')
        for r in rows:
            self.assertEqual(len(r), 2, r)
            self.assertTrue(r[0].strip() and r[1].strip(), r)

    def test_placeholders_kept(self):
        for src, vi in load():
            self.assertEqual(sorted(re.findall(r'\{\d*\}|%s', src)), sorted(re.findall(r'\{\d*\}|%s', vi)), src)

    def test_no_known_mistranslations(self):
        for src, vi in load():
            low = vi.lower()
            self.assertNotIn('cổ phiếu', low, src)
            self.assertNotIn('hoá', low, src)
            if re.search(r'\bBill(ed|ing)?\b', src) and 'Not Billed' not in src and 'Bill No' not in src and 'Bill Date' not in src:
                self.assertNotIn('thanh toán', low, src)
            if src in ('Credit', 'Credit in Company Currency', 'Credit To'):
                self.assertNotIn('nợ', low, src)

    def test_decided_terms(self):
        d = dict(load())
        expect = {
            'Stock Reconciliation': 'Điều chỉnh theo kiểm kê', 'Opening Stock': 'Nhập số dư đầu kỳ',
            'BOM': 'Định mức nguyên vật liệu', 'Submit': 'Xác nhận', 'Valuation Rate': 'Đơn giá vốn',
            'Purchase Receipt': 'Phiếu nhập mua hàng', 'Stock Entry': 'Phiếu kho', 'Delete': 'Xóa',
            'Credit in Company Currency': 'Có (tiền tệ công ty)', 'Clearance Date': 'Ngày ngân hàng ghi nhận',
            'Stock Received But Not Billed': 'Hàng đã nhận chưa nhận hóa đơn', 'Excise Entry': 'Bút toán Excise',
        }
        for k, v in expect.items():
            self.assertEqual(d.get(k), v, k)


if __name__ == '__main__':
    unittest.main()
