"""Thu quầy gửi lại/đồng thời: dùng PE thật, không ghi tăng GL/PLE lần nữa."""
from concurrent.futures import ThreadPoolExecutor
import uuid


def chay(rpc, get, insert, lst, denied, ktt, ktbh, f, phien, emit):
    method = "kh_aph.ban_quay.thu_tien"
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("Payment Entry", "GL Entry", "Payment Ledger Entry")}
    def args():
        return {"company": f["aph"], "customer": f["kh2"], "tien_mat": 31,
                "nguoi_giu_tien": f["ktbh"], "request_id": uuid.uuid4().hex}

    a = args()
    first = rpc(method, a, ktbh)  # Bỏ phản hồi rồi gửi lại cùng mã, như mất mạng sau commit.
    baseline = counts()
    assert rpc(method, {**a, "tien_mat": "31.00"}, ktbh) == first
    assert counts() == baseline
    denied(lambda: rpc(method, {**a, "tien_mat": 32}, ktbh), text="nội dung khác")
    denied(lambda: rpc(method, {**a, "nguoi_giu_tien": f["ktt"]}, ktbh), text="nội dung khác")
    denied(lambda: rpc(method, {**a, "request_id": None}, ktbh), text="mã lượt thu")
    assert counts() == baseline
    emit("HTTP_2B_QUAY_RETRY", "PASS", {"same_pe": first, "changed_content_denied": True, "no_extra_ledger": True})

    a = args()
    a.update(chuyen_khoan=19, tk_ngan_hang=f["acc"]["bank"], ma_gd=uuid.uuid4().hex)
    before = counts()
    # Hai phiên riêng cùng tài khoản, không dùng chung cookie jar giữa các luồng.
    sessions = [phien(f["ktbh"]), phien(f["ktbh"])]
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(lambda caller: rpc(method, a, caller), sessions))
    assert result[0] == result[1] and len(result[0]["phieu_thu"]) == 2, result
    after = counts()
    assert after["Payment Entry"] == before["Payment Entry"] + 2, (before, after)
    assert rpc(method, a, ktbh) == result[0] and counts() == after
    docs = [get("Payment Entry", n, ktt) for n in result[0]["phieu_thu"]]
    assert sum(float(d["paid_amount"]) for d in docs) == 50
    assert len({d["kh_aph_luot_thu_quay"] for d in docs}) == 1
    assert next(d for d in docs if d["paid_to"] == f["acc"]["tien"])["kh_aph_nguoi_giu_tien"] == f["ktbh"]
    emit("HTTP_2B_QUAY_CONCURRENT", "PASS", {"two_sessions": True, "two_methods_one_batch": True, "retry_no_gl_ple": True})

    source = docs[0]
    forged = {"doctype": "Payment Entry", "payment_type": "Receive", "company": f["aph"],
        "posting_date": f["date"], "party_type": "Customer", "party": f["kh2"],
        "paid_from": source["paid_from"], "paid_to": f["acc"]["tien"], "paid_amount": 1,
        "received_amount": 1, "source_exchange_rate": 1, "target_exchange_rate": 1,
        "kh_aph_luot_thu_quay": source["kh_aph_luot_thu_quay"], "kh_aph_noi_dung_thu_quay": source["kh_aph_noi_dung_thu_quay"]}
    denied(lambda: insert(forged, ktt), text="không sửa hoặc sao chép")
    denied(lambda: rpc("frappe.client.set_value", {"doctype": "Payment Entry", "name": source["name"],
        "fieldname": "kh_aph_luot_thu_quay", "value": "fake"}, ktt))
    # Hủy theo quyền native vẫn được; gửi lại mã cũ phải dừng, không tự tái thu.
    rpc("frappe.client.cancel", {"doctype": "Payment Entry", "name": source["name"]}, ktt)
    after_cancel = counts()
    denied(lambda: rpc(method, a, ktbh), text="phiếu bị hủy")
    assert counts() == after_cancel
    denied(lambda: rpc("frappe.client.delete", {"doctype": "Payment Entry", "name": source["name"]}, ktt))
    assert get("Payment Entry", source["name"], ktt)["docstatus"] == 2
    emit("HTTP_2B_QUAY_HISTORY", "PASS", {"forged_metadata_denied": True, "cancel_no_recollect": True, "history_kept": True})

    import json
    import os
    import subprocess
    from pathlib import Path
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Chrome chỉ chạy site UAT dùng một lần trên CI")
    proc = subprocess.run(["node", str(Path(__file__).with_name("ban-nhanh-desk.mjs")),
        json.dumps({"company": f["aph"], "customer": f["kh2"]}), "thu-quay"], text=True, capture_output=True, timeout=180)
    assert proc.returncode == 0, (proc.stdout[-2500:], proc.stderr[-2500:])
    results = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith('{"case":')]
    assert len(results) == 1 and results[0]["case"] == "DESK_2B_CASHIER_LOST_RESPONSE" and results[0]["status"] == "PASS", proc.stdout
    value = results[0]
    emit(value["case"], value["status"], value.get("detail"))
