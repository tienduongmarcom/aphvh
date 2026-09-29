"""Kiểm thử mẫu in không cần Frappe: .json khớp nguồn, và mẫu dựng được với dữ liệu giả."""

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "aph_vh" / "print_format"

try:
    import jinja2
    from jinja2.sandbox import SandboxedEnvironment
except ImportError:  # trong image ERPNext luôn có jinja2
    jinja2 = None


class Row:
    """Giả lập Document của Frappe: đọc thuộc tính, .get(), thiếu trường thì None."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __getattr__(self, key):
        return None

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


def _env(an):
    from aphvh.vn_words import so_tien_bang_chu, so_vn

    env = SandboxedEnvironment(extensions=["jinja2.ext.do"])
    env.globals.update(
        aphvh_an_gia=lambda doc: an,
        aphvh_no_co=lambda doc: {"no": "155", "co": "152"},
        aphvh_cong_ty=lambda c: {"ten": "CÔNG TY TNHH APH", "dia_chi": "Phú Thọ"},
        aphvh_ngay=lambda d: "Ngày 15 tháng 09 năm 2026",
        aphvh_so=so_vn,
        aphvh_bang_chu=so_tien_bang_chu,
        aphvh_ten_nguoi=lambda u: "Dũng",
        aphvh_sl_chung_tu=lambda row: 1000 if row.get("purchase_order_item") else None,
        aphvh_ten_kho=lambda w: (w or "").replace(" - APH", ""),
    )
    return env


class TestPrintFormats(unittest.TestCase):
    @unittest.skipIf(jinja2 is None, "chưa có jinja2")
    def test_purchase_receipt_renders(self):
        html = (ROOT / "phieu_nhap_kho_aph" / "phieu_nhap_kho_aph.html").read_text(encoding="utf-8")
        doc = Row(
            doctype="Purchase Receipt", name="MAT-PRE-2026-00010", company="APH", posting_date="2026-09-15",
            supplier="NCC A", supplier_name="Nhà cung cấp A", supplier_delivery_note="GH-01", owner="dung@x",
            total_qty=1500, base_total=34_500_000,
            items=[
                Row(item_code="NL.DXHAT7", item_name="Đỗ xanh hạt", uom="Kg", qty=1000, base_rate=23000,
                    base_amount=23_000_000, warehouse="Kho nguyên liệu đỗ - APH", purchase_order="PO-1",
                    purchase_order_item="x", lo_nhap_khau="LNK-26-0002"),
                Row(item_code="VT.BAO17", item_name="Bao", uom="Kg", qty=500, base_rate=23000,
                    base_amount=11_500_000, warehouse="Kho nguyên liệu đỗ - APH", purchase_order="PO-1",
                    purchase_order_item="y"),
            ],
        )
        shown = _env(False).from_string(html).render(doc=doc)
        self.assertIn("PHIẾU NHẬP KHO", shown)
        self.assertIn("23.000.000", shown)
        self.assertIn("Ba mươi tư triệu năm trăm nghìn đồng", shown)
        self.assertIn("đơn mua hàng số PO-1", shown)
        self.assertIn("lô nhập khẩu LNK-26-0002", shown)
        self.assertIn("1.500", shown)
        hidden = _env(True).from_string(html).render(doc=doc)
        self.assertNotIn("23.000", hidden)
        self.assertNotIn("triệu", hidden)

    @unittest.skipIf(jinja2 is None, "chưa có jinja2")
    def test_stock_entry_renders_each_purpose(self):
        html = (ROOT / "phieu_kho_aph" / "phieu_kho_aph.html").read_text(encoding="utf-8")

        def se(purpose, items):
            return Row(doctype="Stock Entry", name="MAT-STE-2026-00004", company="APH", posting_date="2026-09-15",
                       purpose=purpose, stock_entry_type=purpose, remarks="", owner="dung@x", items=items)

        nl = Row(item_code="NL.DXHAT7", item_name="Đỗ xanh hạt", uom="Kg", qty=100, valuation_rate=23000,
                 amount=2_300_000, s_warehouse="Kho sản phẩm dở dang đậu - APH", t_warehouse=None)
        tp = Row(item_code="TP.PT8", item_name="Phồng tôm cao cấp xanh", uom="Thùng", qty=5, valuation_rate=460000,
                 amount=2_300_000, s_warehouse=None, t_warehouse="Kho thành phẩm phồng tôm - APH", aphvh_kg=90)
        mv = Row(item_code="NL.DXHAT7", item_name="Đỗ xanh hạt", uom="Kg", qty=500, valuation_rate=23000,
                 amount=11_500_000, s_warehouse="Kho nguyên liệu đỗ - APH", t_warehouse="Kho sản phẩm dở dang đậu - APH")

        for an in (False, True):
            env = _env(an)
            out = env.from_string(html).render(doc=se("Repack", [nl, tp]))
            self.assertIn("PHIẾU SẢN XUẤT", out)
            self.assertIn("I. Nguyên liệu, bao bì xuất dùng", out)
            self.assertIn("90 kg", out)
            self.assertEqual("2.300.000" in out, not an)

            out = env.from_string(html).render(doc=se("Material Transfer", [mv]))
            self.assertIn("PHIẾU XUẤT KHO", out)
            self.assertIn("Mẫu số 02 - VT", out)
            self.assertIn("Sang kho: Kho sản phẩm dở dang đậu", out)
            self.assertIn("Giám đốc", out)

            out = env.from_string(html).render(doc=se("Material Receipt", [tp]))
            self.assertIn("PHIẾU NHẬP KHO", out)
            self.assertIn("Mẫu số 01 - VT", out)

            out = env.from_string(html).render(doc=se("Material Issue", [nl]))
            self.assertIn("PHIẾU XUẤT KHO", out)


def _load_tools():
    import importlib.util

    path = pathlib.Path(__file__).resolve().parents[2] / "tools" / "build_print_formats.py"
    spec = importlib.util.spec_from_file_location("tools_path", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestJsonInSync(unittest.TestCase):
    def test_json_in_sync(self):
        tools = _load_tools()
        for folder in tools.FORMATS:
            on_disk = json.loads((ROOT / folder / f"{folder}.json").read_text(encoding="utf-8"))
            self.assertEqual(on_disk, tools.build_doc(folder), f"{folder}.json lệch nguồn: chạy tools/build_print_formats.py")
