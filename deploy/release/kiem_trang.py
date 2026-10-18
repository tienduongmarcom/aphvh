"""Đọc tệp dấu vân (dau_van_site.py) và báo site còn TRẮNG (chưa có dữ liệu nghiệp vụ) hay không. Chỉ đọc tệp.

    python3 deploy/release/kiem_trang.py ~/dv-truoc.txt     # mã thoát 1 nếu đã có dữ liệu
"""
import json
import sys

NGHIEP_VU = ("Customer", "Supplier", "Item", "Sales Order", "Delivery Note", "Sales Invoice", "Purchase Order",
             "Purchase Receipt", "Purchase Invoice", "Payment Entry", "Journal Entry", "Stock Entry",
             "Stock Reconciliation", "GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")


def main(duong_dan):
    with open(duong_dan, encoding="utf-8") as f:
        d = json.loads([dong for dong in f if dong.startswith("DAU_VAN ")][0][8:])
    co_du_lieu = {k: d["dem"][k] for k in NGHIEP_VU if d["dem"].get(k)}
    print("versions", d["versions"])
    print("co", d["co"])
    if co_du_lieu:
        print("DỪNG: site đã có dữ liệu", co_du_lieu)
        return 1
    print("TRẮNG: được tiếp tục")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
