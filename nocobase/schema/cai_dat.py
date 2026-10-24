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
    ("Báo cáo", "barchartoutlined", "/admin/aph/bao-cao"),
    ("Tài sản", "tooloutlined", "/admin/aph/tai-san"),
    ("Go-Live & số dư đầu kỳ", "rocketoutlined", "/admin/aph/go-live"),
    ("Bán nhanh", "thunderboltoutlined", "/admin/aph/ban-nhanh"),
    ("Trung tâm dữ liệu", "databaseoutlined", "/admin/aph/du-lieu"),
]

DON_VI = [
    ("APH", "Công ty TNHH Sản xuất Thương mại và Xuất nhập khẩu An Phú Hưng"),
    ("VH", "Công ty Cổ phần Thương mại Vĩnh Hưng"),
    ("MK", "Hộ kinh doanh Minh Khang"),
    ("TL", "TL (nội bộ)"),
]

DOC = ["view"]  # "view" bao cả list/get
SUA = DOC + ["create", "update", "destroy"]
DANH_MUC = ["khach_hang", "mat_hang", "kho", "don_vi", "nha_cung_cap", "quy", "quy_doi_dvt"]
DOC_DANH_MUC = {b: DOC for b in DANH_MUC}
# Quyền theo nhóm: bảng -> các thao tác (thao tác nghiệp vụ do plugin kiểm thêm trạng thái / giá vốn ở máy chủ).
NHOM = {
    "ban_hang": ("Bán hàng", ["Bán hàng", "Danh mục"], {**DOC_DANH_MUC,
        "khach_hang": DOC + ["create", "update"],
        "don_ban": SUA + ["chotDon", "moLai", "dongPhanCon"], "don_ban_dong": SUA, "luot_giao": DOC + ["taoLuot", "huy", "update"],
        "luot_giao_dong": DOC, "tra_hang": SUA + ["ghi"], "tra_hang_dong": SUA, "dieu_chinh_gia": DOC + ["create"],
        "ton_kho": DOC, "phieu_thu": DOC, "phieu_thu_phan_bo": DOC}),
    "kho": ("Kho vận", ["Kho vận", "Tài sản"], {**DOC_DANH_MUC,
        "don_ban": DOC, "don_ban_dong": DOC, "luot_giao": DOC + ["banGiaoXe", "khachNhan", "update"], "luot_giao_dong": DOC,
        "tra_hang": SUA + ["ghi"], "tra_hang_dong": SUA,
        "phieu_kho": SUA + ["ghiSo"], "phieu_kho_dong": SUA, "so_kho": DOC, "ton_kho": DOC,
        "tai_san": DOC, "tai_san_giu": DOC, "tai_san_su_kien": DOC + ["create", "update", "ghi", "huy"]}),
    "nha_may": ("Nhà máy", ["Kho vận", "Tài sản"], {**DOC_DANH_MUC,
        "phieu_kho": SUA + ["ghiSo"], "phieu_kho_dong": SUA, "so_kho": DOC, "ton_kho": DOC,
        "me_sx": DOC + ["create", "update", "baoXong"], "tai_san": DOC, "tai_san_giu": DOC, "tai_san_su_kien": DOC + ["create", "update", "ghi", "huy"],
        "phieu_chi": DOC + ["create", "ghi"], "so_quy": DOC, "chot_ca": DOC + ["chot"]}),
    "thu_chi": ("Thu chi và công nợ", ["Thu chi và công nợ", "Danh mục"], {**DOC_DANH_MUC,
        "khach_hang": DOC + ["create", "update"],
        "phieu_thu": SUA + ["ghi", "phanBo", "nhanDien"], "phieu_thu_phan_bo": SUA, "don_ban": DOC, "don_ban_dong": DOC,
        "luot_giao": DOC, "tra_hang": DOC, "dieu_chinh_gia": DOC, "thu_ho": DOC,
        "so_quy": DOC, "no_ncc_dau_ky": DOC, "nha_cung_cap": DOC, "phieu_chi": SUA + ["ghi"], "chuyen_tien": SUA + ["ghi"], "chot_ca": DOC + ["chot"], "phieu_kho": DOC}),
}
# 0.4.0 Unified Operations: bổ sung quyền cho bảng / thao tác mới.
DOC_GIA = {"bang_gia": DOC, "bang_gia_dong": DOC}
NHOM["ban_hang"][2].update({**DOC_GIA, "don_gop": SUA + ["chot", "huy", "taoGiao"], "don_gop_dong": SUA, "giao_gop": DOC, "giao_gop_luot": DOC,
                            "hoa_don_cho_xuat": DOC, "dat_giu_ton": DOC})
for _n in ("kho", "nha_may"):
    NHOM[_n][2].update({"chuyen_hang": SUA + ["xacNhanXuat", "xacNhanNhan"], "chuyen_hang_dong": SUA, "chenh_lech_giao_nhan": DOC,
                        "giao_gop": DOC + ["xacNhan", "huy"], "giao_gop_luot": DOC, "don_gop": DOC, "don_gop_dong": DOC, "dat_giu_ton": DOC})
NHOM["nha_may"][2]["me_sx"] = DOC + ["create", "update", "baoXong", "nhapNhanh", "hieuSuat"]
NHOM["nha_may"][2]["sx_ra_soat"] = DOC + ["boSung", "boQua"]
NHOM["thu_chi"][2]["phieu_thu"] = SUA + ["ghi", "phanBo", "nhanDien", "baoChuyen"]
NHOM["thu_chi"][2].update({"sao_ke": DOC, "sao_ke_dong": DOC, "ca_pos": DOC, "don_gop": DOC})
NHOM["pos"] = ("Thu ngân bán nhanh", ["Bán nhanh"], {**DOC_DANH_MUC, **DOC_GIA, "khach_hang": DOC + ["create"], "ca_pos": DOC + ["mo", "ban", "chot"],
               "ton_kho": DOC, "don_ban": DOC, "don_ban_dong": DOC, "phieu_thu": DOC, "phieu_thu_phan_bo": DOC})
TAT_CA_040 = ["cau_hinh", "phien_ban_schema", "dat_giu_ton", "bang_gia", "bang_gia_dong", "lich_su_duyet_gia", "don_gop", "don_gop_dong", "giao_gop",
              "giao_gop_luot", "hoa_don_cho_xuat", "chuyen_hang", "chuyen_hang_dong", "chenh_lech_giao_nhan", "ca_pos", "sao_ke", "sao_ke_dong",
              "sx_ra_soat", "nguon_tep", "nguon_ban_ghi", "anh_xa_ma", "khop_chung_tu"]
NGHIEP_VU_040 = ["taoGiao", "xacNhan", "nhan", "xacNhanXuat", "xacNhanNhan", "xuLy", "mo", "ban", "baoChuyen", "xacMinh", "tuChoiXacMinh", "nap",
                 "goiY", "khop", "taoThu", "boQua", "xuLyHoan", "nhapNhanh", "boSung", "hieuSuat", "phanLoai", "timTrung", "goiYAnhXa", "dat",
                 "taoLoTon", "bacBo", "tongQuan", "truyVet", "nangCap"]
TAT_CA = ["don_ban", "don_ban_dong", "luot_giao", "luot_giao_dong", "tra_hang", "tra_hang_dong", "dieu_chinh_gia", "phieu_kho", "phieu_kho_dong",
          "phieu_thu", "phieu_thu_phan_bo", "phieu_chi", "chuyen_tien", "thu_ho", "chot_ca", "so_kho", "ton_kho", "so_quy",
          "gia_von", "so_gia_von", "ky_mo_so", "nhap_lo", "nhap_dong", "mo_so_khoa", "no_ncc_dau_ky", "tai_san", "tai_san_su_kien",
          "me_sx", "me_sx_chi_phi", "me_sx_phien_ban", "dieu_chinh_gia_tri", "pham_vi", "tai_san_giu"] + DANH_MUC
NGHIEP_VU = ["ghiSo", "huy", "dinhGia", "chotDon", "duyetGia", "moLai", "dongPhanCon", "ghiHoaDon", "taoLuot", "banGiaoXe", "khachNhan",
             "ghi", "phanBo", "phanBoThuHo", "nhanDien", "tatToan", "chot", "baoCao",
             "kiem", "duyet", "khoa", "uocTinh", "taiTep", "duyetNgoaiLe", "doiChieu", "nhapGiaVon", "baoXong"]
for ten, tieu_de in (("ke_toan", "Kế toán"), ("quan_ly", "Quản lý")):
    NHOM[ten] = (tieu_de, [m[0] for m in MENU], {b: SUA + NGHIEP_VU + NGHIEP_VU_040 for b in TAT_CA + TAT_CA_040})
    # Cấu hình chỉ đổi qua thao tác "dat" (ghi vết); dữ liệu nguồn / sao kê không sửa tay.
    NHOM[ten][2]["cau_hinh"] = DOC + ["dat"]
    for _b in ("phien_ban_schema", "nguon_tep", "nguon_ban_ghi", "sao_ke", "sao_ke_dong", "hoa_don_cho_xuat", "dat_giu_ton", "lich_su_duyet_gia", "chenh_lech_giao_nhan"):
        NHOM[ten][2][_b] = DOC + [x for x in NGHIEP_VU + NGHIEP_VU_040 if x not in ("create", "update", "destroy")]
# Vai trò cờ: gán THÊM cho người không được xem giá vốn (vd. nhân viên nhà máy kiêm việc khác). Phủ quyết mọi vai trò khác ở máy chủ.
for ten in ("ke_toan", "quan_ly"):
    NHOM[ten][2]["users"] = DOC  # chọn người dùng khi cấu hình phạm vi kho / quỹ
NHOM["khong_xem_gia"] = ("Không xem giá vốn (phủ quyết)", [], {})


def ds_truong(api, bang, long_con):
    """Tên trường cho whitelist ACL: cả khóa ngoại (kho_id) và trường bảng con dạng dong.mat_hang_id."""
    kq = []
    for f in api.call(f"collections/{bang}/fields:list", params="?paginate=false")["data"]:
        kq.append(f["name"])
        if f.get("type") == "belongsTo" and f.get("foreignKey"):
            kq.append(f["foreignKey"])
        if long_con and f.get("type") == "hasMany" and f.get("target") and f["name"] not in ("don_con", "luot_ds"):
            kq += [f"{f['name']}.{x}" for x in ds_truong(api, f["target"], False)]
    return sorted(set(kq))


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
    # NocoBase 2.x: fields=[] nghĩa là KHÔNG trường nào -> khai đủ tên trường (giá vốn vẫn do plugin cắt ở máy chủ).
    truong = {}
    for name, (title, menu, quyen) in NHOM.items():
        if name not in roles:
            api.call("roles:create", {"name": name, "title": title, "allowNewMenu": False, "snippets": ["!ui.*", "!pm", "!pm.*", "!app"],
                                      "strategy": {"actions": []}, "defaultRole": False})
            print("+ nhóm", title)
        for bang, thao_tac in quyen.items():
            if bang not in truong:
                truong[bang] = ds_truong(api, bang, True)
            loc = "?filter=" + urllib.parse.quote(json.dumps({"dataSourceKey": "main", "name": bang}))
            body = {"name": bang, "dataSourceKey": "main", "usingActionsConfig": True,
                    "actions": [{"name": t, "fields": truong[bang] if t in ("view", "create", "update", "export") else []} for t in thao_tac]}
            if api.call(f"roles/{name}/dataSourceResources:get", params=loc).get("data"):
                api.call(f"roles/{name}/dataSourceResources:update", body, params=loc)
            else:
                api.call(f"roles/{name}/dataSourceResources:create", body)
        api.call(f"roles/{name}/desktopRoutes:set", [menu_id[m] for m in menu if m in menu_id])
    # Nhóm mặc định "member" của NocoBase không thấy menu nghiệp vụ (chỉ gán người vào 4 nhóm trên).
    if "member" in roles:
        api.call("roles/member/desktopRoutes:set", [])
    print("Xong.")


if __name__ == "__main__":
    main()
