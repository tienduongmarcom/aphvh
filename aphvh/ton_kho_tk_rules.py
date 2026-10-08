"""Đã chuyển sang app lõi 9xLab: lab9x.ton_kho_tk_rules. Giữ đường dẫn aphvh.ton_kho_tk_rules để mã, hook và site cũ không vỡ."""
import sys

import lab9x.ton_kho_tk_rules as _m

sys.modules[__name__] = _m
