"""Đã chuyển sang app lõi 9xLab: lab9x.bang_tai_khoan. Giữ đường dẫn aphvh.bang_tai_khoan để mã, hook và site cũ không vỡ."""
import sys

import lab9x.bang_tai_khoan as _m

sys.modules[__name__] = _m
