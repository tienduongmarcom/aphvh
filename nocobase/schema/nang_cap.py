#!/usr/bin/env python3
"""Nâng cấp dữ liệu 0.4.0 tại chỗ (chạy lại an toàn, không xóa dữ liệu): cấu hình mặc định, giữ quyền người dùng cũ, bổ sung số liệu dòng cũ,
giữ tồn cho đơn đã duyệt đang chờ giao, ghi phiên bản dữ liệu. In báo cáo để lưu hồ sơ nâng cấp.
    python3 nang_cap.py --url http://localhost:13000 --email <quản trị> --password <mật khẩu>
"""
import argparse
import json
import sys

from tao_bang import API

a = argparse.ArgumentParser()
a.add_argument("--url", default="http://localhost:13000")
a.add_argument("--email", required=True)
a.add_argument("--password", required=True)
o = a.parse_args()
r = API(o.url, o.email, o.password).call("cau_hinh:nangCap", {})
d = r.get("data") or {}
print(json.dumps(d, ensure_ascii=False, indent=1))
if not str(d.get("phien_ban", "")).startswith("0.4"):
    sys.exit("Nâng cấp dữ liệu KHÔNG thành công.")
