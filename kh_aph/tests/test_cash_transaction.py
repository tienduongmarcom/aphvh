"""Lỗi 1020 phải rollback cả RPC; lỗi nghiệp vụ và caller lớn không bị thử lại."""
import sys
import types
import unittest
from unittest.mock import Mock,patch
from kh_aph.cash_transaction import retry_rpc

class Conflict(Exception):pass

class TransactionRetry(unittest.TestCase):
    def test_rpc_restarts_whole_operation_and_returns_new_result(self):
        operation=Mock(side_effect=[Conflict('1020'), 'đã đọc nguồn mới'])
        @retry_rpc
        def run():return operation()
        fake=types.SimpleNamespace(local=types.SimpleNamespace(form_dict={'cmd':__name__+'.run'}),QueryDeadlockError=Conflict,db=Mock())
        with patch.dict(sys.modules,{'frappe':fake}),patch('kh_aph.cash_transaction.time.sleep'):
            self.assertEqual(run(),'đã đọc nguồn mới')
        self.assertEqual(operation.call_count,2);fake.db.rollback.assert_called_once();fake.db.commit.assert_not_called()
    def test_internal_caller_never_loses_prior_work(self):
        @retry_rpc
        def run():raise Conflict('1020')
        fake=types.SimpleNamespace(local=types.SimpleNamespace(form_dict={'cmd':'other.business'}),QueryDeadlockError=Conflict,db=Mock())
        with patch.dict(sys.modules,{'frappe':fake}),self.assertRaises(Conflict):run()
        fake.db.rollback.assert_not_called()
    def test_validation_not_retried_and_conflicts_bounded(self):
        for error,calls in [(ValueError('thiếu nguồn'),1),(Conflict('1020'),3)]:
            operation=Mock(side_effect=error)
            @retry_rpc
            def run():return operation()
            fake=types.SimpleNamespace(local=types.SimpleNamespace(form_dict={'cmd':__name__+'.run'}),QueryDeadlockError=Conflict,db=Mock())
            with patch.dict(sys.modules,{'frappe':fake}),patch('kh_aph.cash_transaction.time.sleep'),self.assertRaises(type(error)):run()
            self.assertEqual(operation.call_count,calls)
            self.assertEqual(fake.db.rollback.call_count,0 if calls==1 else 3)
