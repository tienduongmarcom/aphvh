import unittest
from kh_aph.staff_scope import FULL_CUSTOMER_DEBT_ROLE, financial_summary_only


class StaffScope(unittest.TestCase):
    def test_only_explicit_financial_authority_and_stock_scoped_permissions(self):
        rows={'Warehouse':[{'doc':'WH','applicable_for':'Delivery Note'}, {'doc':'WH','applicable_for':'Warehouse'}]}
        self.assertTrue(financial_summary_only({FULL_CUSTOMER_DEBT_ROLE},rows))
        self.assertFalse(financial_summary_only({'Kế toán bán hàng'},rows))
        self.assertFalse(financial_summary_only({FULL_CUSTOMER_DEBT_ROLE},{}))
        for row in ({'doc':'WH'}, {'applicable_for':'GL Entry'}, 'WH'):
            self.assertFalse(financial_summary_only({FULL_CUSTOMER_DEBT_ROLE},{'Warehouse':[row]}))


class WarehousePlan(unittest.TestCase):
    def setUp(self):
        self.config={'cong_ty':[{'abbr':'APH'},{'abbr':'VH'}],'cay_kho':{'dia_diem':[
            {'ten':'Nhà máy Phú Thọ','loai':'nha_may','cong_ty':['APH'],'gui':['VH']},
            {'ten':'Hà Nội','loai':'ban_hang','cong_ty':['APH','VH']}]}}
        self.rows=[self.row('Nhà máy Phú Thọ - APH',group=1),self.row('Hà Nội - APH',group=1),
                   self.row('Nhà máy Phú Thọ - VH','VH',group=1),
                   self.row('Kho tên bất kỳ',parent='Nhà máy Phú Thọ - APH'),
                   self.row('Tên có chữ nhà máy nhưng ở cửa hàng',parent='Hà Nội - APH')]

    def row(self,name,company='APH',parent=None,group=0,**kw):
        return dict(name=name,company_abbr=company,parent_warehouse=parent,is_group=group,**kw)

    def test_location_tree_not_substring(self):
        from kh_aph.staff_scope import warehouse_plan
        result=warehouse_plan(self.config,self.rows)
        self.assertEqual(result['nha_may'],['Kho tên bất kỳ'])
        self.assertEqual(result['cua_hang'],['Tên có chữ nhà máy nhưng ở cửa hàng'])

    def test_descendants_transit_and_company_mismatch(self):
        from kh_aph.staff_scope import warehouse_plan
        self.rows += [self.row('Nhóm tùy chỉnh',parent='Nhà máy Phú Thọ - APH',group=1),
                      self.row('Cách ly mới',parent='Nhóm tùy chỉnh'),
                      self.row('Kho vận chuyển - APH',warehouse_type='Transit'),
                      self.row('Kho sai pháp nhân','VH',parent='Nhà máy Phú Thọ - APH')]
        result=warehouse_plan(self.config,self.rows)
        self.assertIn('Cách ly mới',result['nha_may'])
        # Tên transit thực tế do lõi định nghĩa; không suy chuỗi gần đúng.
        from lab9x import cay_kho as C
        self.rows[-2]['name']=C.ten_kho(C.TEN_VAN_CHUYEN,'APH')
        result=warehouse_plan(self.config,self.rows)
        self.assertIn(self.rows[-2]['name'],result['nha_may'])
        self.assertIn(self.rows[-2]['name'],result['cua_hang'])
        self.assertIn('Kho sai pháp nhân',result['chua_phan_loai'])

    def test_unknown_and_cycle_not_assigned_disabled_ignored(self):
        from kh_aph.staff_scope import warehouse_plan
        self.rows += [self.row('Kho mới'),self.row('Vòng A',parent='Vòng B'),self.row('Vòng B',parent='Vòng A'),
                      self.row('Kho cũ',disabled=1)]
        result=warehouse_plan(self.config,self.rows)
        self.assertEqual(result['chua_phan_loai'],['Kho mới','Vòng A','Vòng B'])
