import unittest

from aphvh import bang_tai_khoan as B
from aphvh import tai_khoan_chuan as T


class TestBangTaiKhoan(unittest.TestCase):
    def test_cau_truc(self):
        for loai in ("aph", "vh"):
            self.assertEqual(B.loi_cau_truc(B.bang(loai), loai), [])

    def test_du_tk_app_can(self):
        for loai in ("aph", "vh"):
            so = {d["so"] for d in B.bang(loai)}
            self.assertEqual(T.thieu(so, T.CAN[loai]), [], loai)

    def test_aph_theo_tt133(self):
        so = {d["so"] for d in B.bang("aph")}
        for k in ("621", "622", "623", "627", "641", "3389"):
            self.assertNotIn(k, so)
        for k in ("6421", "6422", "3385", "154", "642"):
            self.assertIn(k, so)

    def test_vh_theo_tt99(self):
        so = {d["so"] for d in B.bang("vh")}
        for k in ("621", "622", "623", "627", "641", "642", "113", "215"):
            self.assertIn(k, so)

    def test_nguon_ghi_ro(self):
        for loai in ("aph", "vh"):
            for d in B.bang(loai):
                self.assertIn(d["nguon"], ("TT", "DN"))
        thu_ho = [d for d in B.bang("aph") if d["so"] == "33880"][0]
        self.assertEqual((thu_ho["cha"], thu_ho["nguon"]), ("338", "DN"))

    def test_nhom_co_con(self):
        ds = B.bang("aph")
        cha = {d["cha"] for d in ds if d["cha"]}
        for d in ds:
            self.assertEqual(bool(d["nhom"]), d["so"] in cha)


if __name__ == "__main__":
    unittest.main()


# Danh mục số hiệu theo bản "Hệ thống tài khoản kế toán TT133" do anh Tiến cung cấp (PDF, 06/10/2026), bỏ 911 (kết chuyển; ERPNext tự xác định kết quả qua Period Closing Voucher).
TT133_CHINH_THUC = ['111', '1111', '1112', '112', '1121', '1122', '121', '128', '1281', '1288', '131', '133', '1331', '1332', '136', '1361', '1368', '138', '1381', '1386', '1388', '141', '151', '152', '153', '154', '155', '156', '157', '211', '2111', '2112', '2113', '214', '2141', '2142', '2143', '2147', '217', '228', '2281', '2288', '229', '2291', '2292', '2293', '2294', '241', '2411', '2412', '2413', '242', '331', '333', '3331', '33311', '33312', '3332', '3333', '3334', '3335', '3336', '3337', '3338', '33381', '33382', '3339', '334', '335', '336', '3361', '3368', '338', '3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388', '341', '3411', '3412', '352', '3521', '3522', '3524', '353', '3531', '3532', '3533', '3534', '356', '3561', '3562', '411', '4111', '4112', '4118', '413', '418', '419', '421', '4211', '4212', '511', '5111', '5112', '5113', '5118', '515', '611', '631', '632', '635', '642', '6421', '6422', '711', '811', '821']


class TestKhopBanChinhThucTT133(unittest.TestCase):
    def test_aph_tt_khop_ban_chinh_thuc(self):
        ds = B.bang("aph")
        tt = {d["so"] for d in ds if d["nguon"] == "TT"}
        self.assertEqual(sorted(tt), sorted(TT133_CHINH_THUC))

    def test_ten_chinh_thuc(self):
        ten = {d["so"]: d["ten"] for d in B.bang("aph")}
        self.assertEqual(ten["228"], "Đầu tư góp vào đơn vị khác")
        self.assertEqual(ten["3333"], "Thuế xuất khẩu, nhập khẩu")
        self.assertEqual(ten["3387"], "Doanh thu chưa thực hiện")
        self.assertEqual(ten["3386"], "Nhận ký quỹ, ký cược")
