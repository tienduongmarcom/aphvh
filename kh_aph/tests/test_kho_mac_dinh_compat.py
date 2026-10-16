import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from kh_aph.kiem_trien_khai import kho_mac_dinh_stock_settings


class KhoMacDinhCompat(unittest.TestCase):
    def test_removed_field_does_not_read_stale_single(self):
        db = Mock()
        db.get_single_value.side_effect = ValueError("Field default_warehouse does not exist")
        runtime = SimpleNamespace(get_meta=lambda dt: SimpleNamespace(has_field=lambda f: False), db=db)
        with patch.dict(sys.modules, {"frappe": runtime}):
            self.assertIsNone(kho_mac_dinh_stock_settings())
        db.get_single_value.assert_not_called()

    def test_old_platform_retains_configured_warehouse(self):
        db = Mock()
        db.get_single_value.return_value = "Kho đang dùng - APH"
        runtime = SimpleNamespace(get_meta=lambda dt: SimpleNamespace(has_field=lambda f: True), db=db)
        with patch.dict(sys.modules, {"frappe": runtime}):
            self.assertEqual(kho_mac_dinh_stock_settings(), "Kho đang dùng - APH")
        db.get_single_value.assert_called_once_with("Stock Settings", "default_warehouse")
