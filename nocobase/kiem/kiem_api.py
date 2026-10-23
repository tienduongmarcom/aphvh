#!/usr/bin/env python3
"""Kiểm nghiệp vụ plugin kho qua API (dữ liệu giả, tiền tố KT-). Chạy: python3 kiem_api.py --email .. --password .."""
import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
import uuid

KQ = []


def ok(ten, dieu_kien, chi_tiet=""):
    KQ.append((ten, bool(dieu_kien), chi_tiet))
    print(("ĐẠT " if dieu_kien else "LỖI ") + ten + (f" — {chi_tiet}" if chi_tiet else ""))


class API:
    def __init__(self, url, email, pw):
        self.url, self.token = url.rstrip("/"), None
        self.token = self.call("auth:signIn", {"account": email, "password": pw}, h={"X-Authenticator": "basic"})[1]["data"]["token"]

    def call(self, action, body=None, q="", h=None):
        hd = {"Content-Type": "application/json", **({"Authorization": f"Bearer {self.token}"} if self.token else {}), **(h or {})}
        req = urllib.request.Request(f"{self.url}/api/{action}{q}", method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None, headers=hd)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b"{}")
            except Exception:
                return e.code, {}

    def tao(self, bang, values):
        s, r = self.call(f"{bang}:create", values)
        if s != 200:
            raise SystemExit(f"Tạo {bang} lỗi {s}: {r}")
        return r["data"]

    def lay(self, bang, id_, appends=""):
        return self.call(f"{bang}:get", q=f"?filterByTk={id_}" + (f"&appends={appends}" if appends else ""))[1]["data"]

    def ton(self, kho, mh):
        r = self.call("ton_kho:list", q=f"?filter=" + urllib.request.quote(json.dumps({"kho_id": kho, "mat_hang_id": mh})))[1]["data"]
        return r[0]["so_kg"] if r else 0


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="http://localhost:13000")
    a.add_argument("--email", required=True)
    a.add_argument("--password", required=True)
    o = a.parse_args()
    api = API(o.url, o.email, o.password)
    k = "KT-" + uuid.uuid4().hex[:6]
    dv1 = api.tao("don_vi", {"ma": k + "-A", "ten": "Đơn vị thử A"})
    dv2 = api.tao("don_vi", {"ma": k + "-B", "ten": "Đơn vị thử B"})
    kho1 = api.tao("kho", {"ma": k + "-K1", "ten": "Kho thử 1"})
    kho2 = api.tao("kho", {"ma": k + "-K2", "ten": "Kho thử 2"})
    mh = api.tao("mat_hang", {"ma": k + "-DX", "ten": "Đỗ xanh thử", "dvt": "kg", "kg_bao": 25, "gia_ban": 30000})
    ok("Mặt hàng hiện mã – tên", mh["nhan"] == f"{k}-DX – Đỗ xanh thử", mh["nhan"])
    kh = api.tao("khach_hang", {"ma": k + "-KH", "ten": "Khách thử", "sdt": "0900000000", "dia_chi": "Số 1 phố thử"})
    ok("Khách hiện tên – SĐT", kh["nhan"] == "Khách thử – 0900000000", kh["nhan"])

    pk = api.tao("phieu_kho", {"loai": "dau_ky", "kho_id": kho1["id"], "dong": [{"mat_hang_id": mh["id"], "so_bao": 4}]})
    ok("Phiếu kho có số PK-", str(pk["so"]).startswith("PK-"), pk["so"])
    s, _ = api.call("phieu_kho:ghiSo", {}, q=f"?filterByTk={pk['id']}")
    ok("Ghi sổ tồn đầu kỳ (4 bao × 25 kg)", s == 200 and api.ton(kho1["id"], mh["id"]) == 100, api.ton(kho1["id"], mh["id"]))
    s, r = api.call("phieu_kho:ghiSo", {}, q=f"?filterByTk={pk['id']}")
    ok("Ghi sổ lần hai không ghi trùng", s == 200 and api.ton(kho1["id"], mh["id"]) == 100, r)
    s, r = api.call("phieu_kho:update", {"ghi_chu": "x", "kho_id": kho2["id"]}, q=f"?filterByTk={pk['id']}")
    ok("Phiếu đã ghi sổ không sửa kho được", s >= 400, s)
    s, r = api.call("ton_kho:update", {"so_kg": 999}, q=f"?filter=" + urllib.request.quote(json.dumps({"kho_id": kho1["id"]})))
    ok("Không sửa tay được tồn kho", s >= 400 or api.ton(kho1["id"], mh["id"]) == 100, s)

    ck = api.tao("phieu_kho", {"loai": "chuyen", "kho_id": kho1["id"], "kho_dich_id": kho2["id"], "dong": [{"mat_hang_id": mh["id"], "so_kg": 30}]})
    api.call("phieu_kho:ghiSo", {}, q=f"?filterByTk={ck['id']}")
    ok("Chuyển kho 30 kg", api.ton(kho1["id"], mh["id"]) == 70 and api.ton(kho2["id"], mh["id"]) == 30)

    don = api.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": dv1["id"], "dong": [{"mat_hang_id": mh["id"], "kho_id": kho1["id"], "so_kg": 50}]})
    don = api.lay("don_ban", don["id"])
    ok("Đơn: số DB-, mặc định khách đến lấy, ngày giao = ngày đặt, SĐT/địa chỉ khách",
       str(don["so"]).startswith("DB-") and don["cach_giao"] == "khach_den_lay" and don["ngay_giao"] == don["ngay"]
       and don["sdt"] == "0900000000" and don["dia_chi_giao"] == "Số 1 phố thử", don)
    ok("Đơn tính tiền theo giá bán mặt hàng (50 × 30.000)", don["tong_tien"] == 1500000, don["tong_tien"])
    s, r = api.call("don_ban:giaoHang", {}, q=f"?filterByTk={don['id']}")
    ok("Chưa chốt đơn thì không giao được", s == 400, r)
    s, r = api.call("don_ban:chotDon", {}, q=f"?filterByTk={don['id']}")
    ok("Chốt đơn → Chờ xuất, chưa trừ kho", s == 200 and api.ton(kho1["id"], mh["id"]) == 70, r)

    kq = []
    def giao():
        kq.append(api.call("don_ban:giaoHang", {}, q=f"?filterByTk={don['id']}")[0])
    th = [threading.Thread(target=giao) for _ in range(3)]
    [t.start() for t in th]
    [t.join() for t in th]
    ok("Bấm giao 3 lần cùng lúc chỉ trừ kho một lần", api.ton(kho1["id"], mh["id"]) == 20, (kq, api.ton(kho1["id"], mh["id"])))
    don = api.lay("don_ban", don["id"])
    ok("Đơn đã giao, còn nợ 1.500.000", don["trang_thai"] == "da_giao" and don["con_no"] == 1500000, don["con_no"])

    # Hai đơn cùng lúc tranh 20 kg còn lại: chỉ một đơn được giao.
    dons = []
    for _ in range(2):
        d = api.tao("don_ban", {"khach_id": kh["id"], "don_vi_ban_id": dv1["id"], "dong": [{"mat_hang_id": mh["id"], "kho_id": kho1["id"], "so_kg": 15}]})
        api.call("don_ban:chotDon", {}, q=f"?filterByTk={d['id']}")
        dons.append(d)
    kq = []
    th = [threading.Thread(target=lambda d=d: kq.append(api.call("don_ban:giaoHang", {}, q=f"?filterByTk={d['id']}")[0])) for d in dons]
    [t.start() for t in th]
    [t.join() for t in th]
    ok("Hai đơn tranh 20 kg: một đơn giao, một đơn bị chặn, không âm kho",
       sorted(kq) == [200, 400] and api.ton(kho1["id"], mh["id"]) == 5, (kq, api.ton(kho1["id"], mh["id"])))

    pt = api.tao("phieu_thu", {"khach_id": kh["id"], "don_vi_id": dv2["id"], "so_tien": 500000, "phan_bo": [{"don_ban_id": don["id"], "so_tien": 500000}]})
    s, r = api.call("phieu_thu:ghi", {}, q=f"?filterByTk={pt['id']}")
    ok("Tiền vào đơn vị B không trả nợ đơn của đơn vị A", s == 400, r)
    pt = api.tao("phieu_thu", {"khach_id": kh["id"], "don_vi_id": dv1["id"], "so_tien": 2000000, "phan_bo": [{"don_ban_id": don["id"], "so_tien": 1500000}]})
    s, r = api.call("phieu_thu:ghi", {}, q=f"?filterByTk={pt['id']}")
    don = api.lay("don_ban", don["id"])
    pt2 = api.lay("phieu_thu", pt["id"])
    ok("Thu 2 triệu, trả 1,5 triệu cho đơn, 500.000 chưa phân bổ", s == 200 and don["con_no"] == 0 and pt2["chua_phan_bo"] == 500000, (r, don["con_no"]))
    s, r = api.call("phieu_thu:ghi", {}, q=f"?filterByTk={pt['id']}")
    ok("Ghi phiếu thu lần hai không trừ nợ hai lần", api.lay("don_ban", don["id"])["con_no"] == 0 and s == 200)
    s, r = api.call("don_ban:huy", {"ly_do": "thử"}, q=f"?filterByTk={don['id']}")
    ok("Đơn đã có tiền thu thì không hủy được", s == 400, r)
    s, r = api.call("phieu_thu:huy", {"ly_do": "thử hủy"}, q=f"?filterByTk={pt['id']}")
    ok("Hủy phiếu thu trả lại công nợ", s == 200 and api.lay("don_ban", don["id"])["con_no"] == 1500000)
    s, r = api.call("don_ban:huy", {"ly_do": "khách trả hàng"}, q=f"?filterByTk={don['id']}")
    ok("Hủy đơn đã giao nhập lại kho", s == 200 and api.ton(kho1["id"], mh["id"]) == 55, api.ton(kho1["id"], mh["id"]))

    loi = [x for x in KQ if not x[1]]
    print(f"\nTỔNG {len(KQ)} ca, LỖI {len(loi)}")
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
