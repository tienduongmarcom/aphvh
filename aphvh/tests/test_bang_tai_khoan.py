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


# Danh mục số hiệu theo Phụ lục II Thông tư 99/2025/TT-BTC (bản PDF do anh Tiến cung cấp, 06/10/2026), gồm 911 (cố ý không tạo, như APH).
TT99_CHINH_THUC = """111 112 113 121 128 1281 1282 1283 1288 131 133 1331 1332 136 1361 1362 1363 1368 138 1381 1383 1388 141 151 152 153 154 155 156 157 158 171
211 212 213 214 2141 2142 2143 2147 215 2151 21511 21512 215121 215122 2152 2153 217 221 222 228 2281 2288 229 2291 2292 2293 2294 2295
241 2411 2412 2413 2414 242 243 244 331 332 333 3331 33311 33312 3332 3333 3334 3335 3336 3337 3338 33381 33382 3339 334 335 336 3361 3362 3363 3368 337
338 3381 3382 3383 3384 3386 3387 3388 341 3411 3412 343 3431 3432 344 347 352 3521 3522 3523 3525 353 3531 3532 3533 3534 356 3561 3562 357
411 4111 41111 41112 4112 4113 4118 412 413 414 418 419 421 4211 4212 511 515 521 621 622 623 6231 6232 6233 6234 6237 6238 627 6271 6272 6273 6274 6275 6277 6278
632 635 641 6411 6412 6413 6414 6415 6417 6418 642 6421 6422 6423 6424 6425 6426 6427 6428 711 811 821 8211 82111 82112 8212 911""".split()


class TestKhopBanChinhThucTT99(unittest.TestCase):
    def test_vh_tt_khop_ban_chinh_thuc(self):
        ds = B.bang("vh")
        tt = {d["so"] for d in ds if d["nguon"] == "TT"}
        self.assertEqual(sorted(tt), sorted(set(TT99_CHINH_THUC) - {"911"}))

    def test_vh_ten_chinh_thuc(self):
        ten = {d["so"]: d["ten"] for d in B.bang("vh")}
        self.assertEqual(ten["155"], "Sản phẩm")
        self.assertEqual(ten["3387"], "Doanh thu chờ phân bổ")
        self.assertEqual(ten["3386"], "Bảo hiểm thất nghiệp")
        self.assertNotIn("3385", ten)
        self.assertNotIn("3389", ten)
        # 511, 111, 112 không có cấp 2 trong TT99: 5111, 1111, 1121 là chi tiết doanh nghiệp
        nguon = {d["so"]: d["nguon"] for d in B.bang("vh")}
        for k in ("5111", "1111", "1121"):
            self.assertEqual(nguon[k], "DN")
