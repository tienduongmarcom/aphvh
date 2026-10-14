"""Kiểm tệp dịch vi.csv: không trùng khóa, giữ nguyên biến {0} và thẻ HTML."""

import csv
import os
import re
import unittest

TEP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations", "vi.csv")
BIEN = re.compile(r"\{[^{}]*\}|<[^>]+>")


class TestBanDich(unittest.TestCase):
    def setUp(self):
        with open(TEP, encoding="utf-8") as f:
            self.dong = [r for r in csv.reader(f) if r]

    def test_dinh_dang(self):
        for r in self.dong:
            self.assertIn(len(r), (2, 3), r)
            self.assertTrue(r[1].strip(), r)

    def test_khong_trung(self):
        khoa = [(r[0], r[2] if len(r) == 3 else "") for r in self.dong]
        self.assertEqual(len(khoa), len(set(khoa)))

    def test_giu_bien(self):
        for r in self.dong:
            self.assertEqual(sorted(BIEN.findall(r[0])), sorted(BIEN.findall(r[1])), r[0][:80])
