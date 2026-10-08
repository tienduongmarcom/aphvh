"""Đã chuyển sang app lõi 9xLab: lab9x.vat_rules. Giữ đường dẫn aphvh.vat_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.vat_rules as _m

sys.modules[__name__] = _m
