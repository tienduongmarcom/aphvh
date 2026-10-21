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
