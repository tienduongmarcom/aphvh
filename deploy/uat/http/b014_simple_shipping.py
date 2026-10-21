"""Xe khách chỉ định và nhà xe nhập mới: nhận cuối chỉ ghi dấu, không phát sinh sổ lần nữa."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktt, f, emit):
    def order():
        root = submit(insert({"doctype": "APH Shared Sales Order", "customer": f["kh2"], "transaction_date": f["date"],
            "delivery_date": f["date"], "selling_price_list": f["pl"], "currency": "VND",
            "items": [{"item_code": f["A"], "warehouse": f["kho"], "qty": 2, "rate": 35000}]}, ktt), ktt)
        source = rpc("kh_aph.ban_nhanh.preview", {"shared_order": root["name"]}, ktt)["rows"][0]
        return {"shared_order": root["name"], "selections": json.dumps([{"source_row": source["source_row"], "qty": 2}]),
                "request_id": uuid.uuid4().hex, "dispatcher": "Kho UAT"}
    p = order()
    pickup = {"delivery_method": "Xe khách đến lấy", "recipient": "Lái xe do khách cử", "authorization": "Khách gọi chỉ định lái xe"}
    denied(lambda: rpc("kh_aph.ban_nhanh.create_and_dispatch", {**p, "delivery": json.dumps({**pickup, "authorization": ""})}, ktt))
    made = rpc("kh_aph.ban_nhanh.create_and_dispatch", {**p, "delivery": json.dumps(pickup)}, ktt)
    dn = get("Delivery Note", made["delivery_notes"][0]["name"], ktt)
    assert dn["kh_aph_delivery_state"] == "Khách đã nhận" and dn["kh_aph_mau_giao_nhan"] == 1, dn["name"]
    assert dn["kh_aph_chi_dinh_nhan"] == pickup["authorization"]
    html = rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": dn["name"]}, ktt)["html"]
    assert "KIÊM BIÊN BẢN GIAO NHẬN" in html and pickup["authorization"] in html
    emit("HTTP_014_XE_KHACH_CHI_DINH", "PASS", {"customer_received_at_warehouse": True, "authorization_saved": True})

    p = order()
    carrier = f["p"] + "-Nhà xe mới <UAT>"
    info = {"delivery_method": "Vận chuyển", "recipient": "Người nhà xe nhận tại kho", "carrier": carrier,
            "carrier_phone": "0901000000", "customer_signature": "Không", "vehicle_no": "29-UAT"}
    denied(lambda: rpc("kh_aph.ban_nhanh.create_and_dispatch", {**p, "delivery": json.dumps({**info, "carrier_phone": ""})}, ktt))
    p["delivery"] = json.dumps(info)
    made = rpc("kh_aph.ban_nhanh.create_and_dispatch", p, ktt)
    dn = get("Delivery Note", made["delivery_notes"][0]["name"], ktt)
    assert dn["kh_aph_delivery_state"] == "Đang giao" and dn["kh_aph_nha_xe_dot"] == carrier
    html = rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": dn["name"]}, ktt)["html"]
    assert "Người nhận vận chuyển" in html and "&lt;UAT&gt;" in html and "Khách nhận tại nơi giao:" not in html
    options = rpc("kh_aph.delivery_info.recent_carriers", {}, ktt)
    assert {"carrier": carrier, "carrier_phone": "0901000000"} in options
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("Delivery Note", "Sales Invoice", "Stock Ledger Entry", "GL Entry", "Payment Entry")}
    before = counts()
    import os
    if os.environ.get("GITHUB_ACTIONS") == "true":
        import subprocess
        from pathlib import Path
        fresh = order()
        # Chuẩn bị đơn riêng trước khi đo lại: trình duyệt chỉ mở/nhập/hủy các cửa sổ.
        before = counts()
        result = subprocess.run(["node", "--experimental-websocket", str(Path(__file__).with_name("ban-nhanh-desk.mjs")),
            json.dumps({"order": fresh["shared_order"], "delivery": dn["name"]}), "kho-giao-nhan"],
            check=True, text=True, capture_output=True, timeout=180)
        evidence = json.loads(next(x for x in result.stdout.splitlines() if x.startswith('{"case":')))
        assert evidence["status"] == "PASS" and counts() == before, evidence
        emit(evidence["case"], "PASS", evidence["detail"])
    denied(lambda: rpc("kh_aph.delivery_status.confirm", {"name": dn["name"], "action": "receive"}, ktt))
    event = {"name": dn["name"], "action": "receive", "reported_by": "Nhà xe báo", "received_on": dn["posting_date"]}
    rpc("kh_aph.delivery_status.confirm", event, ktt)
    latest = get("Delivery Note", dn["name"], ktt)
    assert latest["kh_aph_delivery_state"] == "Khách đã nhận" and latest["kh_aph_nguon_bao_nhan"] == "Nhà xe báo"
    assert latest["kh_aph_ngay_khach_nhan"] == dn["posting_date"] and not latest.get("kh_aph_ban_ky")
    assert counts() == before
    rpc("kh_aph.delivery_status.confirm", event, ktt)
    assert counts() == before and rpc("kh_aph.ban_nhanh.create_and_dispatch", p, ktt)["reused"]
    bad = get("Delivery Note", dn["name"], ktt); bad["kh_aph_nguon_bao_nhan"] = "Khách báo"
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(bad)}, ktt))
    bad = get("Delivery Note", dn["name"], ktt); bad["kh_aph_nha_xe_dot"] = "Đổi nhà xe trên phiếu cũ"
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(bad)}, ktt))
    emit("HTTP_014_NHA_XE_MOI_BAO_NHAN", "PASS", {"carrier_snapshot": True, "receipt_without_customer_signature": True,
         "no_ledger_change": True, "receipt_protected": True, "retry_no_duplicate": True})
    state = counts()
    original_filters = {"name": latest["name"], "docstatus": 1, "is_return": 0,
                        "kh_aph_mau_giao_nhan": 1, "kh_aph_nhan_goc_luc": ["is", "not set"]}
    assert lst("Delivery Note", original_filters, ["name"], ktt)
    report = rpc("kh_aph.day_close.review", {"company": f["aph"], "day": f["date"]}, ktt)
    assert any(r.get("document") == latest["name"] and "Thiếu giấy gốc" in r["status"] for r in report["rows"])
    payload = {"name": latest["name"], "modified": get("Delivery Note", latest["name"], ktt)["modified"], "location": "Tập kho cửa hàng / UAT / 10"}
    original = rpc("kh_aph.ho_so_giao_nhan.nhan_giay_goc", payload, ktt)
    assert original["received_by"] == f["ktt"] and original["received_at"] and original["location"] == payload["location"]
    assert counts() == state
    assert not lst("Delivery Note", original_filters, ["name"], ktt)
    report = rpc("kh_aph.day_close.review", {"company": f["aph"], "day": f["date"]}, ktt)
    assert any(r.get("document") == latest["name"] and "Đã nhận giấy gốc" in r["status"] for r in report["rows"])
    assert rpc("kh_aph.ho_so_giao_nhan.nhan_giay_goc", payload, ktt) == original
    denied(lambda: rpc("kh_aph.ho_so_giao_nhan.nhan_giay_goc", {**payload, "location": "Tập khác"}, ktt))
    bad = get("Delivery Note", latest["name"], ktt); bad["kh_aph_vi_tri_goc"] = "Tự đổi gốc"
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(bad)}, ktt))
    assert not get("Delivery Note", latest["name"], ktt).get("kh_aph_ban_ky")
    emit("HTTP_014_NHAN_GIAY_GOC", "PASS", {"paper_independent_of_photo": True, "actor_time_location": True,
         "retry_unchanged": True, "direct_edit_denied": True, "no_ledger_change": True})
