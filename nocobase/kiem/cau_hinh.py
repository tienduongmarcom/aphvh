#!/usr/bin/env python3
"""Đặt bộ cấu hình vận hành cho lượt kiểm (chỉ dùng trên bản thử).
    python3 cau_hinh.py --email … --password … cu     # hành vi 0.3.2 (để chạy nguyên vẹn bộ kiểm 0.3.2)
    python3 cau_hinh.py --email … --password … moi    # mặc định 0.4.0
"""
import argparse
import sys

from kiem_api import API

BO = {
    "cu": {"giu_khi_duyet": "khong", "vuot_han_muc_khach_thuong": "duyet", "pham_vi_mac_dinh": "cho_phep", "ck_can_xac_minh": "khong"},
    "moi": {"giu_khi_duyet": "co", "vuot_han_muc_khach_thuong": "canh_bao", "pham_vi_mac_dinh": "tu_choi", "ck_can_xac_minh": "khong"},
}
a = argparse.ArgumentParser()
a.add_argument("--url", default="http://localhost:13000")
a.add_argument("--email", required=True)
a.add_argument("--password", required=True)
a.add_argument("bo", choices=list(BO))
o = a.parse_args()
api = API(o.url, o.email, o.password)
api.lam("cau_hinh:nangCap")
for k, v in BO[o.bo].items():
    s, r = api.lam("cau_hinh:dat", None, {"khoa": k, "gia_tri": v})
    if s != 200:
        sys.exit(f"Lỗi đặt {k}: {r}")
print("Cấu hình:", o.bo, BO[o.bo])
