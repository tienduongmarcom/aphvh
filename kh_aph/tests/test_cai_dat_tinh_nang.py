"""Lớp khóa của bộ cài production và sự nhất quán danh sách cờ giữa app, script triển khai và CI.

Không cần Frappe: thay frappe bằng một module giả tối thiểu.
"""
import importlib
import re
import sys
import types
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]


class _Loi(Exception):
    pass


def _frappe_gia(user="Administrator", site="frontend", conf=None):
    f = types.ModuleType("frappe")
    f.session = types.SimpleNamespace(user=user)
    f.local = types.SimpleNamespace(site=site)
    f.conf = dict(conf or {})
    f.PermissionError = type("PermissionError", (_Loi,), {})

    def throw(msg, exc=_Loi, **kw):
        raise (exc if isinstance(exc, type) and issubclass(exc, Exception) else _Loi)(msg)

    f.throw = throw
    u = types.ModuleType("frappe.utils")
    u.cint = lambda v: int(str(v or 0).strip() or 0) if str(v or 0).strip().lstrip("-").isdigit() else 0
    f.utils = u
    return f, u


class KhoaBoCai(unittest.TestCase):
    def _nap(self, **kw):
        f, u = _frappe_gia(**kw)
        self._cu = {k: sys.modules.get(k) for k in ("frappe", "frappe.utils")}
        sys.modules["frappe"], sys.modules["frappe.utils"] = f, u
        sys.modules.pop("kh_aph.cai_dat_tinh_nang", None)
        return importlib.import_module("kh_aph.cai_dat_tinh_nang")

    def tearDown(self):
        for k, v in getattr(self, "_cu", {}).items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        sys.modules.pop("kh_aph.cai_dat_tinh_nang", None)

    def _du_co(self):
        m = self._nap()
        return {f: "1" for f in m.FLAGS}

    def test_dung_dau_vao_thi_qua(self):
        m = self._nap(conf=self._du_co())
        m._kiem_dau_vao("frontend")

    def test_khong_phai_administrator(self):
        m = self._nap(user="ke-toan@x", conf=self._du_co())
        with self.assertRaises(_Loi):
            m._kiem_dau_vao("frontend")

    def test_go_sai_hoac_thieu_ten_site(self):
        m = self._nap(conf=self._du_co())
        for sai in (None, "", "Frontend", "aphvh-web-uat"):
            with self.assertRaises(_Loi):
                m._kiem_dau_vao(sai)

    def test_cam_erpnext_local(self):
        m = self._nap(site="erpnext.local", conf=self._du_co())
        with self.assertRaises(_Loi):
            m._kiem_dau_vao("erpnext.local")

    def test_thieu_co_bao_ten_co(self):
        co = self._du_co()
        co["kh_aph_source_change"] = "0"
        m = self._nap(conf=co)
        with self.assertRaisesRegex(_Loi, "kh_aph_source_change"):
            m._kiem_dau_vao("frontend")


class NhatQuanDanhSachCo(unittest.TestCase):
    def _co_app(self):
        src = (GOC / "kh_aph/cai_dat_tinh_nang.py").read_text(encoding="utf-8")
        khoi = re.search(r"FLAGS = \((.*?)\)", src, re.S).group(1)
        return set(re.findall(r'"(kh_aph_\w+)"', khoi))

    def test_muoi_lam_co(self):
        self.assertEqual(len(self._co_app()), 24)  # 8 (0.10.0) + 4 (0.11.1) + 1 (0.11.2) + 1 (0.11.3) + 1 (0.11.4) + 2 (0.12) + 2 (0.13) + 2 (0.14)

    def test_quay_lui_dau_van_ci_cung_danh_sach(self):
        if not (GOC / ".github").exists() or not (GOC / "deploy/khach-hang").exists():
            # Trong image: .dockerignore loại .github và deploy/khach-hang. Bước "Test đơn vị" của
            # phat-hanh.yml chạy test này đầy đủ trên repo.
            self.skipTest("chạy trong image: thiếu .github/deploy/khach-hang")
        co = self._co_app()
        for tep in ("deploy/khach-hang/quay-lui.sh", "deploy/release/dau_van_site.py",
                    ".github/workflows/cong-3-nang-cap-production.yml", "kh_aph/handoff_preflight.py"):
            tim = set(re.findall(r"\b(?:" + "|".join(sorted(co)) + r")\b", (GOC / tep).read_text(encoding="utf-8")))
            self.assertEqual(tim, co, tep)

    def test_khong_tu_chay_khi_cai_hoac_migrate(self):
        hooks = (GOC / "kh_aph/hooks.py").read_text(encoding="utf-8")
        self.assertNotIn("cai_dat_tinh_nang", hooks)


if __name__ == "__main__":
    unittest.main()
