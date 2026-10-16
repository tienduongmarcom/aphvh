import importlib.util
import os
import unittest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEP = os.path.join(GOC, "deploy", "release", "dau_dien_tap.py")


def _nap():
    spec = importlib.util.spec_from_file_location("dau_dien_tap", TEP)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipUnless(os.path.exists(TEP), "không có deploy/release trong image")
class DauDienTap(unittest.TestCase):
    def setUp(self):
        self.D = _nap()
        self.goc = self.D.noi_dung("0.14.3", "sha256:aa", "abc", "k1", "frontend", ["b", "a", ""], luc=1000)

    def test_khop(self):
        mong = self.D.noi_dung("0.14.3", "sha256:aa", "abc", "k1", "frontend", ["a", "b"], luc=1000)
        self.assertEqual(self.D.so_khop(self.goc, mong, bay_gio=1000 + 3600), [])

    def test_sai_tung_thanh_phan(self):
        for k, v in (("phien_ban", "0.14.4"), ("image", "sha256:bb"), ("nguon", "def"), ("khach_sha256", "k2"),
                     ("site", "khac"), ("co_moi", ["a"])):
            mong = dict(self.goc, **{k: v})
            loi = self.D.so_khop(self.goc, mong, bay_gio=1000)
            self.assertEqual(len(loi), 1, k)
            self.assertIn(k, loi[0])

    def test_qua_han_va_tuong_lai(self):
        self.assertTrue(self.D.so_khop(self.goc, self.goc, bay_gio=1000 + 12 * 3600))
        self.assertTrue(self.D.so_khop(self.goc, self.goc, bay_gio=999))

    def test_dong_lenh(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            kj, dau = os.path.join(d, "khach.json"), os.path.join(d, "dau.ok")
            open(kj, "w").write("{}")
            chung = ["--pb", "0.14.3", "--image", "sha256:aa", "--nguon", "abc", "--khach", kj, "--site", "frontend"]
            self.assertEqual(self.D.main(["kiem", dau] + chung), 1)
            self.assertEqual(self.D.main(["tao", dau] + chung + ["--co", "x"]), 0)
            self.assertEqual(self.D.main(["kiem", dau] + chung + ["--co", "x"]), 0)
            self.assertEqual(self.D.main(["kiem", dau] + chung), 1)
            open(kj, "w").write('{"doi": 1}')
            self.assertEqual(self.D.main(["kiem", dau] + chung + ["--co", "x"]), 1)


if __name__ == "__main__":
    unittest.main()
