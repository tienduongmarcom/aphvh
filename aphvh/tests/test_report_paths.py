"""Tên thư mục báo cáo phải đúng quy ước Frappe: scrub(tên báo cáo). Sai là chạy báo cáo báo ModuleNotFoundError (lỗi 0.4.18)."""
import glob, json, os, re, unittest

ROOT = os.path.join(os.path.dirname(__file__), '..', 'aph_vh', 'report')


def scrub(name):
    return re.sub(r'[\s\-]+', '_', name.strip().lower()).replace('.', '')


class TestReportPaths(unittest.TestCase):
    def test_folder_files_and_name_match(self):
        found = glob.glob(os.path.join(ROOT, '*', '*.json'))
        self.assertGreater(len(found), 3)
        for p in found:
            folder = os.path.basename(os.path.dirname(p))
            j = json.load(open(p, encoding='utf-8'))
            s = scrub(j['name'])
            self.assertEqual(folder, s, p)
            self.assertEqual(os.path.basename(p), s + '.json', p)
            self.assertTrue(os.path.exists(os.path.join(os.path.dirname(p), s + '.py')), p)


if __name__ == '__main__':
    unittest.main()
