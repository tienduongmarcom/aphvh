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
        aphvh_cong_ty=lambda c: {"ten": "CÔNG TY TNHH APH", "dia_chi": "Phú Thọ", "mst": "2600123456"},
        aphvh_ngay=lambda d: "Ngày 15 tháng 09 năm 2026",
        aphvh_so=so_vn,
        aphvh_bang_chu=so_tien_bang_chu,
        aphvh_ten_nguoi=lambda u: "Dũng",
        aphvh_sl_chung_tu=lambda row: 1000 if row.get("purchase_order_item") else None,
        aphvh_ten_kho=lambda w: (w or "").replace(" - APH", ""),
        aphvh_sl_don_ban=lambda row: 800 if row.get("so_detail") else None,
        aphvh_dia_chi=lambda t: (t or "").replace("<br>", ", ").strip(", "),
        aphvh_lo=lambda row: row.get("batch_no") or "",
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


def _dn(**kw):
    base = dict(
        doctype="Delivery Note", name="MAT-DN-2026-00012", company="APH", posting_date="2026-10-02",
        customer="KH-0001", customer_name="Công ty TNHH Bình An", tax_id="0101234567", owner="thukho@x",
        shipping_address="Số 5 ngõ 12 Láng<br>Hà Nội<br>", is_return=0, return_against=None, po_no="PO-KH-77",
        total_qty=700, base_net_total=21_600_000, base_total_taxes_and_charges=1_080_000,
        base_grand_total=22_680_000, base_rounded_total=22_680_000,
        aphvh_hinh_thuc_giao="Khách tự lấy", aphvh_nguoi_nhan="Trần Văn Nhận",
        items=[
            Row(item_code="HH.DXA", item_name="Đậu xanh hạt loại A", uom="Kg", qty=500, base_net_rate=32000,
                base_net_amount=16_000_000, warehouse="Kho Hà Nội - APH", against_sales_order="SAL-ORD-2026-00031",
                so_detail="x", incoming_rate=28100),
            Row(item_code="TP.PT8", item_name="Phồng tôm cao cấp xanh", uom="Kg", qty=200, base_net_rate=28000,
                base_net_amount=5_600_000, warehouse="Kho Hà Nội - APH", against_sales_order="SAL-ORD-2026-00031",
                so_detail="y", batch_no="PT-2609-01", incoming_rate=21000),
        ],
    )
    base.update(kw)
    return Row(**base)


class TestDeliveryNotePrints(unittest.TestCase):
    @unittest.skipIf(jinja2 is None, "chưa có jinja2")
    def test_phieu_xuat_kho(self):
        html = (ROOT / "phieu_xuat_kho_ban_hang_aph" / "phieu_xuat_kho_ban_hang_aph.html").read_text(encoding="utf-8")
        out = _env(False).from_string(html).render(doc=_dn())
        self.assertIn("PHIẾU XUẤT KHO", out)
        self.assertIn("Mẫu số 02 - VT", out)
        self.assertIn("Trần Văn Nhận", out)
        self.assertIn("theo đơn hàng số SAL-ORD-2026-00031", out)
        self.assertIn("Giao đến: Số 5 ngõ 12 Láng, Hà Nội", out)
        self.assertIn("32.000", out)  # giá bán
        self.assertIn("21.600.000", out)
        self.assertIn("Hai mươi mốt triệu sáu trăm nghìn đồng", out)
        self.assertIn("Lô: PT-2609-01", out)
        self.assertIn("800", out)  # số lượng theo đơn
        self.assertNotIn("28.100", out)  # giá vốn không bao giờ in
        self.assertNotIn("22.680.000", out)  # phiếu xuất kho không có thuế

        out = _env(False).from_string(html).render(
            doc=_dn(aphvh_hinh_thuc_giao="Thuê xe, nhà xe", aphvh_lai_xe="Lê Văn Xe", aphvh_nha_xe="Hùng Phát",
                    aphvh_bien_so_xe="29C-123.45")
        )
        self.assertIn("Lê Văn Xe – lái xe nhà xe Hùng Phát, biển số 29C-123.45", out)

    @unittest.skipIf(jinja2 is None, "chưa có jinja2")
    def test_phieu_nhap_hang_tra_lai(self):
        html = (ROOT / "phieu_xuat_kho_ban_hang_aph" / "phieu_xuat_kho_ban_hang_aph.html").read_text(encoding="utf-8")
        items = [Row(item_code="HH.DXA", item_name="Đậu xanh hạt loại A", uom="Kg", qty=-50, base_net_rate=32000,
                     base_net_amount=-1_600_000, warehouse="Kho Hà Nội - APH")]
        out = _env(False).from_string(html).render(
            doc=_dn(is_return=1, return_against="MAT-DN-2026-00012", items=items, total_qty=-50,
                    base_net_total=-1_600_000)
        )
        self.assertIn("PHIẾU NHẬP KHO", out)
        self.assertIn("Mẫu số 01 - VT", out)
        self.assertIn("phiếu giao hàng số MAT-DN-2026-00012", out)
        self.assertIn("1.600.000", out)
        self.assertNotIn("-1.600.000", out)
        self.assertNotIn("-50", out)

    @unittest.skipIf(jinja2 is None, "chưa có jinja2")
    def test_bien_ban_giao_nhan_hai_lien(self):
        html = (ROOT / "bien_ban_giao_nhan_aph" / "bien_ban_giao_nhan_aph.html").read_text(encoding="utf-8")
        out = _env(False).from_string(html).render(doc=_dn())
        self.assertEqual(out.count("BIÊN BẢN GIAO NHẬN HÀNG HÓA"), 2)
        self.assertIn("Liên 1: Giao khách hàng", out)
        self.assertIn("Liên 2: Lưu tại công ty", out)
        self.assertIn("page-break-after", out)
        self.assertIn("BÊN GIAO (Bên A): CÔNG TY TNHH APH", out)
        self.assertIn("BÊN NHẬN (Bên B): Công ty TNHH Bình An", out)
        self.assertIn("Mã số thuế: 0101234567", out)
        self.assertIn("Căn cứ đơn hàng số SAL-ORD-2026-00031; đơn đặt hàng của khách số PO-KH-77", out)
        self.assertIn("1.080.000", out)
        self.assertIn("22.680.000", out)
        self.assertIn("Hai mươi hai triệu sáu trăm tám mươi nghìn đồng", out)
        self.assertIn("PT-2609-01", out)
        self.assertNotIn("NGƯỜI VẬN CHUYỂN", out)
        self.assertNotIn("28.100", out)

        out = _env(False).from_string(html).render(
            doc=_dn(aphvh_hinh_thuc_giao="Thuê xe, nhà xe", aphvh_nha_xe="Hùng Phát", aphvh_lai_xe="Lê Văn Xe",
                    aphvh_sdt_lai_xe="0912 345 678", aphvh_bien_so_xe="29C-123.45")
        )
        self.assertEqual(out.count("NGƯỜI VẬN CHUYỂN"), 4)  # 2 liên × (thông tin + chữ ký)
        self.assertIn("Nhà xe Hùng Phát", out)
        self.assertIn("0912 345 678", out)

        out = _env(False).from_string(html).render(
            doc=_dn(is_return=1, return_against="MAT-DN-2026-00012", base_net_total=-1_600_000,
                    base_total_taxes_and_charges=-80_000, base_grand_total=-1_680_000, base_rounded_total=-1_680_000)
        )
        self.assertIn("BIÊN BẢN NHẬN LẠI HÀNG HÓA", out)
        self.assertIn("BÊN GIAO (Bên A): Công ty TNHH Bình An", out)
        self.assertIn("BÊN NHẬN (Bên B): CÔNG TY TNHH APH", out)
        self.assertIn("1.680.000", out)
        self.assertNotIn("-1.680.000", out)


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
