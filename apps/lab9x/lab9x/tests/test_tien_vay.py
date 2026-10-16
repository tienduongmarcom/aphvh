import datetime
import unittest

from lab9x import tien_vay as T

D = datetime.date


class NganHang(unittest.TestCase):
    def test_hop_le(self):
        ds = [{"don_vi": "APH", "ngan_hang": "ACB", "so_cuoi": "1234", "loai_tien": "VND"},
              {"don_vi": "APH", "ngan_hang": "ACB", "so_cuoi": "1234", "loai_tien": "USD"},
              {"don_vi": "VH", "ngan_hang": "MB", "so_cuoi": "0001"}]
        self.assertEqual(T.kiem_ngan_hang(ds, {"APH", "VH"}), [])

    def test_loi(self):
        ds = [{"don_vi": "XX", "ngan_hang": "", "so_cuoi": "123456789", "loai_tien": "EUR", "so_tk": "1"},
              {"don_vi": "APH", "ngan_hang": "acb", "so_cuoi": "1234"}, {"don_vi": "APH", "ngan_hang": "ACB", "so_cuoi": "1234"}]
        loi = " | ".join(T.kiem_ngan_hang(ds, {"APH"}))
        for x in ("XX", "ngan_hang", "4 chữ số", "VND hoặc USD", "khóa lạ so_tk", "trùng APH"):
            self.assertIn(x, loi)

    def test_ten_so_hieu(self):
        self.assertEqual(T.ten_tk("ACB", "1234"), "ACB 1234")
        self.assertEqual(T.ten_tk("ACB", "1234", "USD"), "ACB 1234 USD")
        self.assertEqual(T.so_hieu_moi("1121", {"1121", "112101"}), "112102")


class SoQuy(unittest.TestCase):
    def test_ton_sau_tung_phieu(self):
        dong, thu, chi, cuoi = T.so_ton(1000, [{"so": "PT1", "thu": 500}, {"so": "PC1", "chi": 1200}, {"so": "PT2", "thu": 100}])
        self.assertEqual([d["ton"] for d in dong], [1500, 300, 400])
        self.assertEqual((thu, chi, cuoi), (600, 1200, 400))


class Vay(unittest.TestCase):
    def test_lai_don(self):
        self.assertEqual(T.lai(100_000_000, 12, 30), 986301.0)
        self.assertEqual(T.lai(0, 12, 30), 0)

    def test_lai_ky_bien_dong(self):
        # vay 100tr ngày 1/10, trả 40tr ngày 16/10: 15 ngày × 100tr + 16 ngày × 60tr, lãi 12%/năm
        bd = [(D(2026, 10, 1), 100_000_000), (D(2026, 10, 16), -40_000_000)]
        lai, du = T.lai_ky(bd, 12, D(2026, 10, 1), D(2026, 10, 31))
        self.assertEqual(du, 60_000_000)
        self.assertEqual(lai, T.lai(100_000_000, 12, 15) + T.lai(60_000_000, 12, 16))

    def test_lai_ky_vay_tu_truoc(self):
        lai, du = T.lai_ky([("2026-01-05", 50_000_000)], 10, "2026-02-01", "2026-02-28")
        self.assertEqual((lai, du), (T.lai(50_000_000, 10, 28), 50_000_000))

    def test_nhom_han(self):
        h = D(2026, 10, 15)
        self.assertEqual(T.nhom_han(D(2026, 10, 14), h), "Quá hạn")
        self.assertEqual(T.nhom_han(D(2026, 10, 20), h), "Trong 7 ngày")
        self.assertEqual(T.nhom_han(D(2026, 11, 10), h), "Trong 30 ngày")
        self.assertEqual(T.nhom_han(D(2027, 1, 1), h), "Trong 90 ngày")
        self.assertEqual(T.nhom_han(D(2027, 6, 1), h), "Sau 90 ngày")
        self.assertEqual(T.tai_khoan_vay(D(2026, 1, 1), D(2028, 1, 1)), "Dài hạn")


class SaoKe(unittest.TestCase):
    def test_so(self):
        for x, v in (("1.234.567", 1234567), ("1,234,567", 1234567), ("1.234.567,50", 1234567.5), ("(1.000)", -1000),
                     ("-500", -500), (2500.0, 2500), ("", 0), ("12,5", 12.5), ("1.000", 1000)):
            self.assertEqual(T.so(x), v, x)

    def test_ngay(self):
        self.assertEqual(T.ngay("05/10/2026"), D(2026, 10, 5))
        self.assertEqual(T.ngay("2026-10-05 10:11:12"), D(2026, 10, 5))
        self.assertEqual(T.ngay("5-10-26"), D(2026, 10, 5))
        self.assertIsNone(T.ngay("Cộng"))

    def test_doc_theo_ten_cot(self):
        bang = [["SAO KÊ"], ["Ngày GD", "Số tham chiếu", "Diễn giải", "Ghi nợ", "Ghi có"],
                ["01/10/2026", "FT1", "KH A chuyển", "", "5.000.000"], ["02/10/2026", "FT2", "Phí", "11.000", ""],
                ["", "", "Cộng", "11.000", "5.000.000"]]
        dong, loi = T.doc_sao_ke(bang, {"dong_tieu_de": 2, "ngay": "Ngày GD", "ma": "số tham chiếu", "noi_dung": 3,
                                        "ghi_no": "Ghi nợ", "ghi_co": "Ghi có"})
        self.assertEqual(loi, [])
        self.assertEqual([(d["ma"], d["so_tien"]) for d in dong], [("FT1", 5_000_000), ("FT2", -11_000)])

    def test_thieu_cot(self):
        self.assertTrue(T.doc_sao_ke([["a", "b"]], {"ngay": "Ngày", "ghi_no": 1, "ghi_co": 2})[1])

    def test_khop(self):
        dong = [{"ngay": D(2026, 10, 1), "ma": "FT1", "so_tien": 5e6}, {"ngay": D(2026, 10, 2), "ma": "FT2", "so_tien": 7e6},
                {"ngay": D(2026, 10, 3), "ma": "", "so_tien": -11000}, {"ngay": D(2026, 10, 4), "ma": "FT9", "so_tien": 1e6},
                {"ngay": D(2026, 10, 5), "ma": "FT5", "so_tien": 2e6}, {"ngay": D(2026, 10, 5), "ma": "FT5", "so_tien": 2e6},
                {"ngay": D(2026, 10, 6), "ma": "FT6", "so_tien": 3e6}]
        so_sach = [{"chung_tu": "PE1", "ma": "FT1", "ngay": "2026-10-02", "so_tien": 5e6},
                   {"chung_tu": "PE2", "ma": "FT2", "ngay": "2026-10-02", "so_tien": 6e6},
                   {"chung_tu": "JE1", "ma": "", "ngay": "2026-10-04", "so_tien": -11000},
                   {"chung_tu": "PE6a", "ma": "FT6", "ngay": "2026-10-06", "so_tien": 3e6},
                   {"chung_tu": "PE6b", "ma": "FT6", "ngay": "2026-10-06", "so_tien": 3e6}]
        kq = [(r["trang_thai"], r["chung_tu"]) for r in T.khop_sao_ke(dong, so_sach)]
        self.assertEqual(kq, [("Khớp", "PE1"), ("Lệch", "PE2"), ("Khớp", "JE1"), ("Chưa ghi sổ", None),
                              ("Trùng", None), ("Trùng", None), ("Trùng", "PE6a, PE6b")])


if __name__ == "__main__":
    unittest.main()


class MauNganHang(unittest.TestCase):
    """Bố cục giống tệp tải từ internet banking (dữ liệu giả): dòng tiêu đề tự dò, tiêu đề có xuống dòng / song ngữ."""

    def test_acb(self):
        bang = [["Chủ tài khoản: X"], [], [None, None, None, "Số dư đầu"],
                ["Ngày hiệu lực", "Ngày giao dịch", "Số GD", "Nội dung giao dịch", "Số tiền rút ra", "Số tiền gửi vào", "Số dư"],
                ["15/10/2026", "14/10/2026 19:24:08", "3754", "A CHUYEN KHOAN FT26287670450837 GD", "", 17125000.0, 1.0],
                ["15/10/2026", "15/10/2026 08:51:39", "3756", "CHUYEN TIEN NOI BO", 53000000.0, "", 1.0]]
        dong, loi = T.doc_sao_ke(bang, T.mau_ngan_hang("ACB"))
        self.assertEqual(loi, [])
        self.assertEqual([(d["ma"], d["so_tien"]) for d in dong], [("3754", 17125000), ("3756", -53000000)])
        # phiếu thu ghi mã FT (nằm trong nội dung sao kê ACB) vẫn khớp
        kq = T.khop_sao_ke(dong, [{"chung_tu": "PE1", "ma": "FT26287670450837", "ngay": "2026-10-14", "so_tien": 17125000}])
        self.assertEqual((kq[0]["trang_thai"], kq[0]["chung_tu"]), ("Khớp", "PE1"))

    def test_mb_vietin(self):
        mb = [["SAO KÊ"], [], ["STT", "NGÀY GIAO DỊCH", "NGÀY HẠCH TOÁN", "PHÁT SINH NỢ", "PHÁT SINH CÓ", "SỐ DƯ", "ĐƠN VỊ", "NỘI DUNG",
                              "BÚT TOÁN"],
              ["1", "15/10/2026 14:34:58", "15/10/2026", 0.0, 6575000.0, 1.0, "X", "ck", "FT1"], ["TỔNG TIỀN", 0, 6575000.0]]
        dong, _l = T.doc_sao_ke(mb, T.mau_ngan_hang("MB"))
        self.assertEqual([(d["ma"], d["so_tien"]) for d in dong], [("FT1", 6575000)])
        vt = [["LỊCH SỬ"], ["STT/No.", "Ngày hạch toán/Accounting date", "Mô tả giao dịch/ Transaction description", "Nợ/ Debit",
                           "Có / Credit", "Số dư TK/ Account Balance", "Số giao dịch/ Transaction number"],
              [0.0, "15-10-2026 11:06:49", "phi", 6336000.0, 0.0, 1.0, "146K26A0PALBTMD2"], ["Từ ngày 21/03/2025 ..."]]
        dong, _l = T.doc_sao_ke(vt, T.mau_ngan_hang("VIETIN"))
        self.assertEqual([(d["ngay"], d["ma"], d["so_tien"]) for d in dong], [(D(2026, 10, 15), "146K26A0PALBTMD2", -6336000)])
        self.assertIsNone(T.mau_ngan_hang("Sacombank"))
