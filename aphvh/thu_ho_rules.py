"""Đã chuyển sang app lõi 9xLab: lab9x.thu_ho_rules. Giữ đường dẫn aphvh.thu_ho_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.thu_ho_rules as _m

sys.modules[__name__] = _m
