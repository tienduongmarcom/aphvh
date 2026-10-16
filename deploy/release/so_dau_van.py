"""So hai dấu vân của deploy/release/dau_van_site.py. In khác biệt; mã thoát 1 nếu lệch.

    python3 so_dau_van.py truoc.txt sau.txt --phan schema,dem,tong,co,versions,cai_dat,giao_dien [--bo-qua REGEX ...]

giao_dien (0.11.2): Property Setter cột danh sách do người dùng chỉnh trên giao diện, tách khỏi schema.

--bo-qua: bỏ các mục schema khớp biểu thức (ở cả hai bên) — chỉ dùng cho khác biệt đã biết và có lý do ghi ở nơi gọi.

Tệp đầu vào là output của dau_van_site.py (dòng bắt đầu bằng "DAU_VAN "; các dòng khác bỏ qua).
"""
import argparse
import json
import re
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
    ap.add_argument("--bo-qua", action="append", default=[], help="regex mục bỏ qua (schema: mục; phần khác: '<phần>.<khóa>', chi_tiet: 'chi_tiet.<nhóm>.<khóa>')")
    ns = ap.parse_args()
    bo = [re.compile(x) for x in ns.bo_qua]
    a, b = doc(ns.a), doc(ns.b)
    lech = 0
    for phan in ns.phan.split(","):
        if phan == "schema":
            ma = {m for m in a["schema"]["muc"] if not any(r.search(m) for r in bo)}
            mb = {m for m in b["schema"]["muc"] if not any(r.search(m) for r in bo)}
            if bo:
                print(f"schema: bỏ qua {len(a['schema']['muc']) - len(ma)} / {len(b['schema']['muc']) - len(mb)} mục theo --bo-qua")
            for m in sorted(ma - mb):
                print(f"schema chỉ có ở {ns.a}: {m}")
            for m in sorted(mb - ma):
                print(f"schema chỉ có ở {ns.b}: {m}")
            lech += len(ma ^ mb)
            print(f"schema: {len(ma)} / {len(mb)} mục, lệch {len(ma ^ mb)}")
        elif phan == "chi_tiet":
            if "chi_tiet" not in a or "chi_tiet" not in b:
                print("chi_tiet: THIẾU ở một bên (dấu vân cũ) — LỆCH")
                lech += 1
                continue
            n_phan = 0
            for nhom in sorted(set(a["chi_tiet"]) | set(b["chi_tiet"])):
                xa, xb = a["chi_tiet"].get(nhom) or {}, b["chi_tiet"].get(nhom) or {}
                khac = [k for k in sorted(set(xa) | set(xb)) if xa.get(k) != xb.get(k)
                        and not any(r.search(f"chi_tiet.{nhom}.{k}") for r in bo)]
                for k in khac[:30]:
                    print(f"chi_tiet.{nhom}.{k}: {xa.get(k)} ≠ {xb.get(k)}")
                if len(khac) > 30:
                    print(f"chi_tiet.{nhom}: … còn {len(khac) - 30} dòng lệch")
                print(f"chi_tiet.{nhom}: {len(xa)} / {len(xb)} nhóm, lệch {len(khac)}")
                n_phan += len(khac)
            lech += n_phan
            print(f"chi_tiet: {'khớp' if not n_phan else 'LỆCH'}")
        else:
            xa, xb = a.get(phan) or {}, b.get(phan) or {}
            for k in sorted(set(xa) | set(xb)):
                if xa.get(k) != xb.get(k) and not any(r.search(f"{phan}.{k}") for r in bo):
                    print(f"{phan}.{k}: {xa.get(k)} ≠ {xb.get(k)}")
                    lech += 1
            print(f"{phan}: {'khớp' if all(xa.get(k) == xb.get(k) or any(r.search(f'{phan}.{k}') for r in bo) for k in set(xa) | set(xb)) else 'LỆCH'}")
    print("KẾT QUẢ: " + ("KHỚP" if not lech else f"LỆCH {lech}"))
    sys.exit(1 if lech else 0)


if __name__ == "__main__":
    main()
