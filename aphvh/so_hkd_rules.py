"""Đã chuyển sang app lõi 9xLab: lab9x.so_hkd_rules. Giữ đường dẫn aphvh.so_hkd_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.so_hkd_rules as _m

sys.modules[__name__] = _m
