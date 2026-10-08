"""Đã chuyển sang app lõi 9xLab: lab9x.tong_hop_khach_rules. Giữ đường dẫn aphvh.tong_hop_khach_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.tong_hop_khach_rules as _m

sys.modules[__name__] = _m
