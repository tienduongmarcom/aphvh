"""Đã chuyển sang app lõi 9xLab: lab9x.ben_thu_ba_rules. Giữ đường dẫn aphvh.ben_thu_ba_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.ben_thu_ba_rules as _m

sys.modules[__name__] = _m
