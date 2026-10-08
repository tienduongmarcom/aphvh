"""Đã chuyển sang app lõi 9xLab: lab9x.print_rules. Giữ đường dẫn aphvh.print_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.print_rules as _m

sys.modules[__name__] = _m
