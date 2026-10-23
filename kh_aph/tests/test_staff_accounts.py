"""Mã riêng từng người, không chiếm tài khoản trùng hoặc tự gửi thư."""
import unittest
from kh_aph.staff_accounts import plan


class StaffAccounts(unittest.TestCase):
    def test_distinct_and_deferred(self):
        rows = plan([])
        codes = [row['username'] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertIn('dungktt', codes)
        self.assertIn('dungnm', codes)
        self.assertNotIn('tam', codes)
        self.assertTrue(all(row['status'] == 'chua_co' for row in rows))
        self.assertTrue(all(row['send_welcome_email'] == 0 for row in rows))
        self.assertTrue(all(row['email'].endswith('@nhansu.invalid') for row in rows))

    def test_collision_by_username_even_other_email(self):
        rows = plan([{'name': 'other@example.org', 'username': ' HUONG '}])
        self.assertEqual(rows[0]['status'], 'can_doi_chieu')
        self.assertEqual(rows[0]['existing'], ['other@example.org'])

    def test_collision_by_internal_identity_even_renamed(self):
        rows = plan([{'name': 'DUNGKTT@NHANSU.INVALID', 'username': 'other'}])
        self.assertEqual(rows[2]['status'], 'can_doi_chieu')
        self.assertEqual(rows[-1]['status'], 'chua_co')

    def test_never_match_by_display_name(self):
        rows = plan([{'name': 'someone@example.org', 'full_name': 'Dung'}])
        self.assertEqual(rows[2]['status'], 'chua_co')
