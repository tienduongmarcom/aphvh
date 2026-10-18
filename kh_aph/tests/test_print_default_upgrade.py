"""Tái hiện cổng 3: site mới dùng Classic, site nâng cấp giữ mẫu app/người dùng."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]


class PrintDefaultUpgrade(unittest.TestCase):
    def test_installer_fresh_upgrade_and_user_selection(self):
        # Chạy chính hàm bộ cài với trạng thái DB tối thiểu; không import bộ Frappe.
        source = ast.parse((ROOT / "kh_aph/install.py").read_text())
        function = next(n for n in source.body if isinstance(n, ast.FunctionDef)
                        and n.name == "ensure_default_print_formats")
        expected = {"Delivery Note": "Phiếu xuất kho bán hàng", "Sales Invoice": "Phiếu bán hàng"}
        for initial in ("Classic", "Modern with Images", "with Item Image", "app", "riêng"):
            with self.subTest(initial=initial):
                values = {dt: value if initial == "app" else
                          "Mẫu riêng khách" if initial == "riêng" else f"{dt} {initial}"
                          for dt, value in expected.items()}
                db = SimpleNamespace(exists=lambda *args: True,
                                     get_value=lambda dt, filters, field: values[filters["doc_type"]])
                def set_value(data, **kwargs):
                    values[data["doctype"]] = data["value"]
                setter = Mock(side_effect=set_value)
                env = {"frappe": SimpleNamespace(db=db, make_property_setter=setter),
                       "reload_print_formats": Mock(), "DEFAULT_PRINT_FORMATS": expected}
                exec(compile(ast.Module(body=[function], type_ignores=[]), "install.py", "exec"), env)
                env["ensure_default_print_formats"]()
                self.assertEqual(values, {dt: "Mẫu riêng khách" for dt in expected}
                                 if initial == "riêng" else expected)
                calls = setter.call_count
                env["ensure_default_print_formats"]()
                self.assertEqual(setter.call_count, calls, "Cài lại không được ghi đè mẫu đã chọn")
