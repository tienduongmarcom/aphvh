"""Đã chuyển sang app lõi 9xLab: lab9x.control_rules. Giữ đường dẫn aphvh.control_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.control_rules as _m

sys.modules[__name__] = _m
