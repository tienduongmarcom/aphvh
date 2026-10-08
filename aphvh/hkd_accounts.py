"""Đã chuyển sang app lõi 9xLab: lab9x.hkd_accounts. Giữ đường dẫn aphvh.hkd_accounts để mã, hook và site cũ không vỡ."""
import sys

import lab9x.hkd_accounts as _m

sys.modules[__name__] = _m
