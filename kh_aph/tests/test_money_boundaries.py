"""Ràng buộc nhận tiền và sao kê, trước khi được phép tác động sổ."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class MoneyBoundaries(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.conf = {"kh_aph_factory_cash": 1}
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.throw = lambda msg, *args, **kw: (_ for _ in ()).throw(ValueError(msg))
        self.f.session = types.SimpleNamespace(user="nguoi-nhan")
        self.f.get_roles = lambda: []
        self.f.db = Mock()
        self.f.flags = types.SimpleNamespace(get=lambda key: False)
        self.f.PermissionError = ValueError
        utils = types.ModuleType("frappe.utils")
        for key in ("add_days", "cint", "flt", "get_first_day", "get_last_day", "getdate", "nowdate", "now_datetime"):
            setattr(utils, key, lambda v=None, *args: v)
        utils.now_datetime = lambda: "2026-10-17 16:00:00"
        self.context = patch.dict(sys.modules, {"frappe": self.f, "frappe.utils": utils})
        self.context.start()
        self.addCleanup(self.context.stop)

    def load(self, name):
        spec = importlib.util.spec_from_file_location("unit_money_"+name, ROOT/(name+".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_scope_bi_chan_truoc_khi_tao_but_toan(self):
        m = self.load("factory_cash")
        m._tao_je = Mock()
        doc = types.SimpleNamespace(check_permission=Mock(side_effect=ValueError("ngoai pham vi")), company="VH")
        self.f.get_doc = Mock(return_value=doc)
        with self.assertRaises(ValueError): m.xac_nhan_nhan("P1", 10, "quy")
        m._tao_je.assert_not_called()
        doc.check_permission.side_effect = None
        company = types.SimpleNamespace(check_permission=Mock(side_effect=ValueError("khong Company")))
        self.f.get_doc.side_effect = [doc, company]
        with self.assertRaises(ValueError): m.xac_nhan_nhan("P1", 10, "quy")
        m._tao_je.assert_not_called()

    def test_nhan_tien_khong_chap_nhan_nan_inf_hoac_qua_le(self):
        m = self.load("factory_cash")
        m._tao_je = Mock()
        doc = types.SimpleNamespace(check_permission=Mock(), company="APH", nguoi_nhan="nguoi-nhan",
                                    docstatus=1, loai="Bàn giao tiền", trang_thai="Chờ nhận")
        company = types.SimpleNamespace(check_permission=Mock())
        for amount in ("NaN", "Infinity", "1.001", "1e100000"):
            self.f.get_doc = Mock(side_effect=[doc, company])
            with self.assertRaises(ValueError): m.xac_nhan_nhan("P1", amount, "quy")
        m._tao_je.assert_not_called()

    def test_khong_nhan_truong_ket_qua_gia_mao(self):
        m = self.load("factory_cash")
        for field in m.KET_QUA_NHAN:
            doc = types.SimpleNamespace(get_doc_before_save=lambda: None, get=lambda f: "gia" if f == field else None)
            with self.assertRaises(ValueError): m.validate_phieu(doc)
        with self.assertRaises(ValueError): m.protect_submitted(None)

    def test_file_khong_co_quyen_khong_doc_noi_dung(self):
        m = self.load("tien_vay")
        file = types.SimpleNamespace(check_permission=Mock(side_effect=ValueError("tep rieng")), get_content=Mock())
        self.f.get_doc = Mock(return_value=file)
        with self.assertRaises(ValueError): m._bang_tu_tep("/private/files/a.csv")
        file.get_content.assert_not_called()

    def test_khong_duoc_luu_mau_bank_khi_chi_co_quyen_doc(self):
        m = self.load("tien_vay")
        m._can_bat = Mock(); m._vai_tro = Mock(); m._bang_tu_tep = Mock()
        ba = types.SimpleNamespace(account="1121", company="APH", bank="ACB", check_permission=Mock())
        account = types.SimpleNamespace(company="APH", check_permission=Mock())
        bank = types.SimpleNamespace(check_permission=Mock(side_effect=ValueError("chi doc Bank")))
        self.f.get_doc = Mock(side_effect=[ba, account, bank])
        with self.assertRaises(ValueError): m.doi_chieu_sao_ke("BA", "file", anh_xa={"ngay": 1}, luu_mau=1)
        m._bang_tu_tep.assert_not_called()

    def test_bao_cao_gioi_han_truy_van_vao_company_duoc_doc(self):
        m = self.load("quan_tri")
        self.f.get_list = Mock(return_value=[types.SimpleNamespace(name="APH", abbr="APH")])
        self.f.get_meta = Mock(return_value=types.SimpleNamespace(has_field=lambda f: False))
        self.f.db.sql.return_value = []
        self.assertEqual(m.dong_lai_gop("2026-10-01", "2026-10-31"), [])
        sql, args = self.f.db.sql.call_args.args
        self.assertIn("si.company IN %(ctys)s", sql)
        self.assertEqual(args["ctys"], ("APH",))
        self.f.db.sql.reset_mock()
        with self.assertRaises(ValueError): m.dong_lai_gop("2026-10-01", "2026-10-31", "VH")
        with self.assertRaises(ValueError): m.dong_tien_cong_ty("VH", "2026-10-01")
        self.f.db.sql.assert_not_called()

    def test_ho_so_dung_khong_duoc_cong_role_de_doc_tai_chinh(self):
        m = self.load("quan_tri")
        self.f.conf = {m.FLAG: 1}
        self.f.get_roles = lambda: ["Accounts Manager", "APH Không xem giá vốn"]
        with self.assertRaises(ValueError): m.can_quyen()

    def test_ma_giao_dich_khoa_tai_khoan_va_doc_hien_tai(self):
        m = self.load("money_reference")
        bank = types.SimpleNamespace(ma_da_ghi=Mock(return_value="cu"))
        with patch.dict(sys.modules, {"kh_aph.tien_vay": bank}):
            with self.assertRaises(ValueError): m.check("1121", "GD", "moi")
        self.f.db.sql.assert_called_once()
        bank.ma_da_ghi.assert_called_once_with("1121", "GD", bo_qua="moi", lock=True)

    def test_native_thu_chi_dung_cung_kiem_ma_va_tu_loai_chinh_no(self):
        m = self.load("money_reference")
        self.f.conf = {"kh_aph_tien_vay": 1}
        values = {"reference_no": " GD ", "paid_to": "1121"}
        doc = types.SimpleNamespace(doctype="Payment Entry", docstatus=0, name="PE-1", get=values.get,
                                    set=lambda k,v: values.update({k:v}))
        self.f.get_all = Mock(return_value=["1121"])
        m.check = Mock()
        m.validate(doc)
        m.check.assert_called_once_with("1121", "GD", "PE-1")
        self.assertEqual(values["reference_no"], "GD")
        self.f.flags.get = lambda key: True
        m.check.reset_mock()
        m.validate(doc)
        m.check.assert_not_called()

    def test_so_quy_va_khoa_ky_kiem_company_truoc_truy_van(self):
        denied = types.SimpleNamespace(check_permission=Mock(side_effect=ValueError("ngoai pham vi")))
        self.f.get_doc = Mock(return_value=denied)
        m = self.load("tien_vay")
        with self.assertRaises(ValueError): m.so_quy("VH", "1121", "2026-10-01", "2026-10-31")
        self.f.db.sql.assert_not_called()
        q = self.load("quan_tri")
        q.can_quyen = Mock()
        q._ky = Mock()
        for fn in (q.khoa_ky, q.mo_khoa_ky):
            with self.assertRaises(ValueError): fn("VH", "2026-09", "kiem quyen")
        q._ky.assert_not_called()
