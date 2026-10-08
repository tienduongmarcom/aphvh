"""Đã chuyển sang app lõi 9xLab: lab9x.vn_words. Giữ đường dẫn aphvh.vn_words để mã, hook và site cũ không vỡ."""
import sys

import lab9x.vn_words as _m

sys.modules[__name__] = _m
