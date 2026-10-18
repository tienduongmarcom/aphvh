"""Dấu "diễn tập bản sao ĐẠT" (0.14.3): ràng buộc với đúng thứ sẽ được triển khai. Chỉ đọc / ghi tệp dấu, không đụng site.

    python3 dau_dien_tap.py tao  <tệp dấu> --pb 0.14.3 --image sha256:… --nguon <git sha> --khach khach.json --site frontend [--co cờ …]
    python3 dau_dien_tap.py kiem <tệp dấu> --pb 0.14.3 --image sha256:… --nguon <git sha> --khach khach.json --site frontend [--co cờ …]

`kiem` thoát mã 1 khi dấu sai bất kỳ thành phần nào (phiên bản, image ID, commit nguồn, khach.json, cờ mới, site) hoặc quá 12 giờ.
"""
import argparse
import hashlib
import json
import sys
import time

HAN_GIAY = 12 * 3600


def sha_tep(duong_dan):
    with open(duong_dan, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def noi_dung(pb, image, nguon, khach_sha, site, co, luc=None):
    return {"phien_ban": pb, "image": image, "nguon": nguon, "khach_sha256": khach_sha, "site": site,
            "co_moi": sorted(set(c for c in co if c)), "luc": int(luc if luc is not None else time.time())}


def so_khop(dau, mong, bay_gio=None):
    """Trả danh sách lý do không khớp (rỗng = hợp lệ)."""
    loi = []
    for k in ("phien_ban", "image", "nguon", "khach_sha256", "site", "co_moi"):
        if dau.get(k) != mong.get(k):
            loi.append(f"{k}: dấu {dau.get(k)!r} ≠ triển khai {mong.get(k)!r}")
    tuoi = (bay_gio if bay_gio is not None else time.time()) - int(dau.get("luc") or 0)
    if not 0 <= tuoi < HAN_GIAY:
        loi.append(f"dấu đã {int(tuoi // 3600)} giờ (hạn 12 giờ)")
    return loi


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("lenh", choices=("tao", "kiem"))
    ap.add_argument("tep")
    for k in ("pb", "image", "nguon", "khach", "site"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--co", nargs="*", default=[])
    ns = ap.parse_args(argv)
    mong = noi_dung(ns.pb, ns.image, ns.nguon, sha_tep(ns.khach), ns.site, ns.co)
    if ns.lenh == "tao":
        with open(ns.tep, "w", encoding="utf-8") as f:
            json.dump(mong, f, ensure_ascii=False)
        print("Đã ghi dấu diễn tập", ns.tep)
        return 0
    try:
        with open(ns.tep, encoding="utf-8") as f:
            dau = json.load(f)
    except (OSError, ValueError) as e:
        print("Không đọc được dấu diễn tập:", e)
        return 1
    loi = so_khop(dau, mong)
    for x in loi:
        print("Dấu diễn tập không khớp —", x)
    if not loi:
        print(f"Dấu diễn tập hợp lệ: {dau['phien_ban']}, cách đây {int((time.time() - dau['luc']) // 60)} phút")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
