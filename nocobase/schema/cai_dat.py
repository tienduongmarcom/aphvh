#!/usr/bin/env python3
"""Cài menu, 4 nhóm quyền và 4 đơn vị bán (chạy lại an toàn).

    python3 cai_dat.py --url http://localhost:13000 --email ... --password ...
"""
import argparse
import json
import urllib.parse
import uuid

from tao_bang import API

MENU = [
    ("Bán hàng", "shoppingcartoutlined", "/admin/aph/ban-hang"),
    ("Kho vận", "inboxoutlined", "/admin/aph/kho-van"),
    ("Thu chi và công nợ", "dollaroutlined", "/admin/aph/thu-chi"),
    ("Danh mục", "unorderedlistoutlined", "/admin/aph/danh-muc"),
]

DON_VI = [
    ("APH", "Công ty TNHH Sản xuất Thương mại và Xuất nhập khẩu An Phú Hưng"),
    ("VH", "Công ty Cổ phần Thương mại Vĩnh Hưng"),
    ("MK", "Hộ kinh doanh Minh Khang"),
    ("TL", "TL (nội bộ)"),
]

DOC = ["list", "get", "view"]
# Quyền theo nhóm: bảng -> các thao tác. Thao tác nghiệp vụ: ghiSo, huy, chotDon, giaoHang, moLai, ghi.
NHOM = {
    "ban_hang": ("Bán hàng", "/admin/aph/ban-hang", {
        "don_ban": DOC + ["create", "update", "chotDon", "moLai"], "don_ban_dong": DOC + ["create", "update", "destroy"],
        "khach_hang": DOC + ["create", "update"], "mat_hang": DOC, "kho": DOC, "don_vi": DOC, "ton_kho": DOC,
        "phieu_thu": DOC, "phieu_thu_phan_bo": DOC}),
    "kho": ("Kho vận", "/admin/aph/kho-van", {
        "don_ban": DOC + ["giaoHang"], "don_ban_dong": DOC, "phieu_kho": DOC + ["create", "update", "ghiSo"],
        "phieu_kho_dong": DOC + ["create", "update", "destroy"], "so_kho": DOC, "ton_kho": DOC,
        "mat_hang": DOC, "kho": DOC, "khach_hang": DOC, "don_vi": DOC}),
    "thu_chi": ("Thu chi và công nợ", "/admin/aph/thu-chi", {
        "phieu_thu": DOC + ["create", "ghi"], "phieu_thu_phan_bo": DOC + ["create", "update", "destroy"],
        "don_ban": DOC, "don_ban_dong": DOC, "khach_hang": DOC + ["create", "update"], "don_vi": DOC, "mat_hang": DOC, "kho": DOC}),
    "quan_ly": ("Quản lý", "/admin/aph/ban-hang", {b: DOC + ["create", "update", "destroy", "ghiSo", "huy", "chotDon", "giaoHang", "moLai", "ghi"]
        for b in ["don_ban", "don_ban_dong", "phieu_kho", "phieu_kho_dong", "phieu_thu", "phieu_thu_phan_bo", "khach_hang", "mat_hang", "kho", "don_vi"]}
        | {"so_kho": DOC, "ton_kho": DOC}),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:13000")
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    a = ap.parse_args()
    api = API(a.url, a.email, a.password)

    co = {r["title"]: r for r in api.call("desktopRoutes:list", params="?paginate=false")["data"]}
    for i, (ten, icon, href) in enumerate(MENU):
        if ten in co:
            continue
        api.call("desktopRoutes:create", {"type": "link", "title": ten, "icon": icon, "schemaUid": uuid.uuid4().hex[:11],
                                          "options": {"href": href, "params": [], "openInNewWindow": False}, "sort": i + 1})
        print("+ menu", ten)
    menu_id = {r["title"]: r["id"] for r in api.call("desktopRoutes:list", params="?paginate=false")["data"]}

    for ma, ten in DON_VI:
        if not api.call("don_vi:list", params="?filter=" + urllib.parse.quote(json.dumps({"ma": ma})))["data"]:
            api.call("don_vi:create", {"ma": ma, "ten": ten})
            print("+ đơn vị", ma)

    roles = {r["name"] for r in api.call("roles:list", params="?paginate=false")["data"]}
    for name, (title, trang, quyen) in NHOM.items():
        if name not in roles:
            api.call("roles:create", {"name": name, "title": title, "allowNewMenu": False, "snippets": ["!ui.*", "!pm", "!pm.*", "!app"],
                                      "strategy": {"actions": []}, "defaultRole": False})
            print("+ nhóm", title)
        for bang, thao_tac in quyen.items():
            loc = "?filter=" + urllib.parse.quote(json.dumps({"dataSourceKey": "main", "name": bang}))
            body = {"name": bang, "dataSourceKey": "main", "usingActionsConfig": True,
                    "actions": [{"name": t, "fields": []} for t in thao_tac]}
            if api.call(f"roles/{name}/dataSourceResources:get", params=loc).get("data"):
                api.call(f"roles/{name}/dataSourceResources:update", body, params=loc)
            else:
                api.call(f"roles/{name}/dataSourceResources:create", body)
        # Menu được thấy: theo nhóm (quản lý thấy hết)
        thay = [r for r in MENU if name == "quan_ly" or r[2] == trang or r[0] == "Danh mục" and name != "kho"]
        api.call(f"roles/{name}/desktopRoutes:set", [menu_id[r[0]] for r in thay if r[0] in menu_id])
    # Nhóm mặc định "member" của NocoBase không thấy menu nghiệp vụ (chỉ gán người vào 4 nhóm trên).
    if "member" in roles:
        api.call("roles/member/desktopRoutes:set", [])
    print("Xong.")


if __name__ == "__main__":
    main()
