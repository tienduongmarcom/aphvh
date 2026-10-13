"""So hai dấu vân của deploy/release/dau_van_site.py. In khác biệt; mã thoát 1 nếu lệch.

    python3 so_dau_van.py truoc.txt sau.txt --phan schema,dem,tong,co,versions

Tệp đầu vào là output của dau_van_site.py (dòng bắt đầu bằng "DAU_VAN "; các dòng khác bỏ qua).
"""
import argparse
import json
import sys


def doc(duong_dan):
    with open(duong_dan, encoding="utf-8") as f:
        for dong in f:
            if dong.startswith("DAU_VAN "):
                return json.loads(dong[len("DAU_VAN "):])
    sys.exit(f"Không thấy dòng DAU_VAN trong {duong_dan}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--phan", default="schema,dem,tong")
    ns = ap.parse_args()
    a, b = doc(ns.a), doc(ns.b)
    lech = 0
    for phan in ns.phan.split(","):
        if phan == "schema":
            ma, mb = set(a["schema"]["muc"]), set(b["schema"]["muc"])
            for m in sorted(ma - mb):
                print(f"schema chỉ có ở {ns.a}: {m}")
            for m in sorted(mb - ma):
                print(f"schema chỉ có ở {ns.b}: {m}")
            lech += len(ma ^ mb)
            print(f"schema: {a['schema']['so_muc']} / {b['schema']['so_muc']} mục, lệch {len(ma ^ mb)}")
        else:
            xa, xb = a.get(phan) or {}, b.get(phan) or {}
            for k in sorted(set(xa) | set(xb)):
                if xa.get(k) != xb.get(k):
                    print(f"{phan}.{k}: {xa.get(k)} ≠ {xb.get(k)}")
                    lech += 1
            print(f"{phan}: {'khớp' if all(xa.get(k) == xb.get(k) for k in set(xa) | set(xb)) else 'LỆCH'}")
    print("KẾT QUẢ: " + ("KHỚP" if not lech else f"LỆCH {lech}"))
    sys.exit(1 if lech else 0)


if __name__ == "__main__":
    main()
