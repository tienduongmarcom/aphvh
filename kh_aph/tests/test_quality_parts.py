"""Giảm một phần lô không làm đổi giá phần còn lại hoặc hoàn lại khoản đã giảm."""
import unittest
from decimal import Decimal
from kh_aph.quality_parts import balances, select


class QualityParts(unittest.TestCase):
    def parts(self, used=()):
        return balances(25,35000,[{'key':'GIAM-1','qty':5,'net_discount':50000}],used)

    def test_distinguish_discounted_and_untouched_goods(self):
        parts={row['key']:row for row in self.parts()}
        self.assertEqual((parts['GIAM-1']['qty'],parts['GIAM-1']['net_rate']),(5,25000))
        self.assertEqual((parts['']['qty'],parts['']['net_rate']),(20,35000))
        self.assertEqual(select(list(parts.values()),[{'key':'GIAM-1','qty':5}])[0]['net_amount'],125000)
        self.assertEqual(select(list(parts.values()),[{'key':'','qty':5}])[0]['net_amount'],175000)

    def test_mixed_return_keeps_auditable_breakdown(self):
        result=select(self.parts(),[{'key':'GIAM-1','qty':3},{'key':'','qty':2}])
        self.assertEqual([r['net_amount'] for r in result],[75000,70000])
        self.assertEqual(sum(r['net_amount'] for r in result),145000)

    def test_draft_and_posted_reservations_both_consume_their_own_part(self):
        parts=self.parts([{'key':'GIAM-1','qty':2},{'key':'GIAM-1','qty':1},{'key':'','qty':4}])
        by_key={row['key']:row for row in parts}
        self.assertEqual((by_key['GIAM-1']['remaining'],by_key['']['remaining']),(2,16))
        with self.assertRaises(ValueError):select(parts,[{'key':'GIAM-1','qty':3}])
        select(parts,[{'key':'','qty':3}])

    def test_separate_agreements_keep_separate_prices(self):
        parts=balances(25,35000,[{'key':'A','qty':5,'net_discount':50000},
                              {'key':'B','qty':10,'net_discount':20000}],[])
        self.assertEqual([p['net_rate'] for p in parts],[25000,33000,35000])

    def test_full_return_never_refunds_prior_discount_again(self):
        result=select(self.parts(),[{'key':'GIAM-1','qty':5},{'key':'','qty':20}])
        self.assertEqual(sum(r['net_amount'] for r in result),25*35000-50000)

    def test_overlapping_or_overvalued_agreement_is_not_authority(self):
        for rows in ([{'key':'A','qty':26,'net_discount':1}],
                     [{'key':'A','qty':5,'net_discount':175001}],
                     [{'key':'A','qty':5,'net_discount':1}]*2,
                     [{'key':'','qty':5,'net_discount':1}]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):balances(25,35000,rows,[])

    def test_cannot_move_prior_return_to_a_different_agreement(self):
        with self.assertRaises(ValueError):self.parts([{'key':'KHAC','qty':1}])
        with self.assertRaises(ValueError):self.parts([{'key':'GIAM-1','qty':6}])

    def test_invalid_and_duplicate_selection_cannot_allocate_implicitly(self):
        for rows in ([],[{'key':'','qty':0}],[{'key':'','qty':-1}],
                     [{'key':'','qty':21}],[{'key':'','qty':1}]*2,
                     [{'key':'KHAC','qty':1}],[{'key':'GIAM-1','qty':'NaN'}]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):select(self.parts(),rows)

    def test_decimal_quantities_and_complete_price_reduction(self):
        parts=balances('0.3','10',[{'key':'A','qty':'0.1','net_discount':'1'}],[])
        self.assertEqual(select(parts,[{'key':'A','qty':'0.1'}])[0]['net_amount'],0)
        self.assertEqual(select(parts,[{'key':'','qty':'0.2'}])[0]['net_amount'],Decimal('2'))
