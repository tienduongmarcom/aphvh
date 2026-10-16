"""Chứng minh bộ kiểm phát hiện sửa/thêm/xóa core, không chỉ kiểm git status."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "deploy/release/kiem_toan_core.py"


@unittest.skipUnless(SCRIPT.exists(), "Không có công cụ triển khai trong image")
class CoreIntegrity(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("kiem_toan_core", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for app in ("frappe", "erpnext"):
            (self.root / app).mkdir()
            (self.root / app / "core.py").write_text("nguyên bản")

    def test_added_removed_changed_and_permissions(self):
        before = self.m.snapshot(self.root)
        (self.root / "frappe/core.py").write_text("đã sửa")
        (self.root / "erpnext/core.py").unlink()
        (self.root / "erpnext/new.py").write_text("thêm")
        self.assertEqual(self.m.compare(before, self.m.snapshot(self.root)), {
            "added": ["erpnext/new.py"], "removed": ["erpnext/core.py"], "changed": ["frappe/core.py"]})

    def test_runtime_cache_ignored_but_symlink_not_followed(self):
        before = self.m.snapshot(self.root)
        (self.root / "frappe/__pycache__").mkdir()
        (self.root / "frappe/__pycache__/a.pyc").write_bytes(b"cache")
        self.assertFalse(any(self.m.compare(before, self.m.snapshot(self.root)).values()))
        link = self.root / "frappe/link"
        link.symlink_to("../erpnext", target_is_directory=True)
        self.assertEqual(self.m.snapshot(self.root)["frappe/link"]["link"], "../erpnext")
        (self.root / "frappe/core.py").chmod(0o700)
        self.assertEqual(self.m.compare(before, self.m.snapshot(self.root))["changed"], ["frappe/core.py"])

    def test_missing_and_empty_core_rejected(self):
        (self.root / "erpnext/core.py").unlink()
        with self.assertRaises(ValueError):
            self.m.snapshot(self.root)
        with self.assertRaises(ValueError):
            self.m.compare({}, {})
