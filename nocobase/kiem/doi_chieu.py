#!/usr/bin/env python3
"""Đối chiếu bảo toàn toàn hệ thống (chỉ đọc): Σ sổ kho = tồn, Σ sổ giá trị = giá trị tồn, mọi điều chỉnh giá trị cân.
    python3 doi_chieu.py --email <kế toán / quản trị> --password <mật khẩu>"""
import argparse
import json
import sys

from kiem_api import API

a = argparse.ArgumentParser()
a.add_argument("--url", default="http://localhost:13000")
a.add_argument("--email", required=True)
a.add_argument("--password", required=True)
o = a.parse_args()
s, r = API(o.url, o.email, o.password).call("gia_von:doiChieu", {})
d = r.get("data") or {}
print(json.dumps(d.get("tong"), ensure_ascii=False))
for k in ("lech_so_luong", "lech_gia_tri", "dieu_chinh_khong_can"):
    for x in d.get(k) or []:
        print("LỆCH", k, json.dumps(x, ensure_ascii=False))
print("ĐỐI CHIẾU:", "CÂN" if d.get("can") else "CÓ LỆCH")
sys.exit(0 if d.get("can") else 1)
