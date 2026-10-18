"""Lớp chặn lối in / xem trước bỏ qua bước xóa giá (0.11.0) — phần thuần, không cần Frappe."""
import runpy
import unittest
from pathlib import Path

from kh_aph.print_guard import CHAN_HAN, XEM_TRUOC, can_chan, lay_lenh


class LayLenh(unittest.TestCase):
    def test_tham_so_cmd(self):
        self.assertEqual(lay_lenh(" frappe.utils.weasyprint.download_pdf ", "/"), "frappe.utils.weasyprint.download_pdf")

    def test_duong_dan_v1_v2(self):
        for p in ("/api/method/frappe.desk.doc_preview.get_preview", "/api/v2/method/frappe.desk.doc_preview.get_preview/",
                  "/api/method/frappe.desk.doc_preview.get_preview?doctype=X"):
            self.assertEqual(lay_lenh(None, p), XEM_TRUOC, p)

    def test_khong_phai_lenh(self):
        self.assertEqual(lay_lenh(None, "/app/stock-entry"), "")


class CanChan(unittest.TestCase):
    def test_chan_moi_loi_khi_bi_an_gia(self):
        for lenh in CHAN_HAN:
            self.assertTrue(can_chan(lenh, True), lenh)
            self.assertFalse(can_chan(lenh, False), lenh)

    def test_xem_truoc_chi_chan_dong_con(self):
        self.assertTrue(can_chan(XEM_TRUOC, True, la_bang_con=True))
        self.assertFalse(can_chan(XEM_TRUOC, True, la_bang_con=False))
        self.assertFalse(can_chan(XEM_TRUOC, False, la_bang_con=True))

    def test_khong_chan_loi_in_chuan(self):
        for lenh in ("frappe.www.printview.get_html_and_style", "frappe.utils.print_format.download_pdf",
                     "frappe.utils.print_format_generator.download_pdf", "frappe.client.get", ""):
            self.assertFalse(can_chan(lenh, True), lenh)

    def test_danh_sach_du(self):
        for lenh in ("frappe.utils.weasyprint.download_pdf", "frappe.utils.weasyprint_legacy.download_pdf",
                     "frappe.utils.print_format_generator.get_formatted_field_values",
                     "frappe.utils.print_format_generator.check_conditions"):
            self.assertIn(lenh, CHAN_HAN)


class GanHook(unittest.TestCase):
    def test_auth_hook(self):
        h = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hooks.py"))
        self.assertIn("kh_aph.print_guard.before_request", h["auth_hooks"])
        self.assertIn("kh_aph.dung_cost_policy.before_request", h["auth_hooks"])


if __name__ == "__main__":
    unittest.main()
