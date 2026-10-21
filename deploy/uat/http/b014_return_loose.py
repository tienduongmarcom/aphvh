"""Nhận5kg trong bao25kg sau khi khách đã nhận: kiểm thật kho, nợ, sổ bao và retry."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktt, f, emit):
    old = get("Item", f["A"], ktt)
    item = f["p"] + "-TRA-LE-25"
    insert({"doctype": "Item", "item_code": item, "item_name": "Hàng thử trả lẻ 25kg", "item_group": old["item_group"],
            "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average", "kh_aph_kg_per_bag": 25}, ktt)
    submit(insert({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": f["aph"],
        "posting_date": f["date"], "items": [{"item_code": item, "t_warehouse": f["kho"], "qty": 50,
        "basic_rate": 20000, "kh_aph_bags": 2, "kh_aph_kg_per_bag": 25, "expense_account": f["acc"]["cp"]}]}, ktt), ktt)
    root = submit(insert({"doctype": "APH Shared Sales Order", "customer": f["kh2"], "transaction_date": f["date"],
        "delivery_date": f["date"], "selling_price_list": f["pl"], "currency": "VND", "kh_aph_xuat_hoa_don": "Không",
        "items": [{"item_code": item, "warehouse": f["kho"], "qty": 25, "rate": 35000, "kh_aph_bags": 1, "kh_aph_kg_per_bag": 25}]}, ktt), ktt)
    source = rpc("kh_aph.ban_nhanh.preview", {"shared_order": root["name"]}, ktt)["rows"][0]
    made = rpc("kh_aph.ban_nhanh.create_and_dispatch", {"shared_order": root["name"], "request_id": uuid.uuid4().hex,
        "selections": json.dumps([{"source_row": source["source_row"], "qty": 25}]),
        "delivery": json.dumps({"delivery_method": "Khách đến lấy", "recipient": "Khách UAT"}), "dispatcher": "Kho UAT"}, ktt)
    dn = get("Delivery Note", made["delivery_notes"][0]["name"], ktt)
    assert dn["kh_aph_delivery_state"] == "Khách đã nhận"
    view = rpc("kh_aph.sales_return.preview", {"delivery_note": dn["name"]}, ktt)
    row = view["rows"][0]
    assert row["remaining_qty"] == 25 and row["remaining_bags"] == 1, view
    payload = {"delivery_note": dn["name"], "selections": json.dumps([{"source_row": row["source_row"], "qty": 5, "bags": 0}]),
        "request_id": uuid.uuid4().hex, "reason": "Khách trả5kg hỏng, giữ20kg", "condition": "Cách ly", "settlement": "Bù trừ công nợ"}
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("Delivery Note", "Sales Invoice", "Stock Ledger Entry", "GL Entry", "Payment Entry")}
    before = counts()
    created = rpc("kh_aph.sales_return.create_draft", payload, ktt)
    draft = get("Delivery Note", created["name"], ktt)
    assert draft["docstatus"] == 0 and draft["items"][0]["qty"] == -5 and draft["items"][0]["kh_aph_bags"] == 0, draft["name"]
    after_draft = counts()
    assert after_draft["Delivery Note"] == before["Delivery Note"] + 1
    assert all(after_draft[dt] == before[dt] for dt in before if dt != "Delivery Note"), (before, after_draft)
    assert rpc("kh_aph.sales_return.create_draft", payload, ktt)["name"] == created["name"] and counts() == after_draft
    denied(lambda: rpc("kh_aph.sales_return.create_draft", {**payload, "reason": "Đổi nội dung"}, ktt))
    denied(lambda: rpc("kh_aph.sales_return.create_draft", {**payload, "request_id": uuid.uuid4().hex,
        "selections": json.dumps([{"source_row": row["source_row"], "qty": 21, "bags": 0}])}, ktt))
    assert rpc("kh_aph.sales_return.preview", {"delivery_note": dn["name"]}, ktt)["rows"][0]["remaining_qty"] == 20
    posted = submit(draft, ktt)
    wh = posted["items"][0]["warehouse"]
    assert get("Warehouse", wh, ktt)["kh_aph_loai_kho"] == "Cách ly"
    bins = lst("Bin", {"item_code": item, "warehouse": wh}, ["actual_qty"], ktt)
    assert len(bins) == 1 and bins[0]["actual_qty"] == 5, bins
    source_bin = lst("Bin", {"item_code": item, "warehouse": f["kho"]}, ["actual_qty"], ktt)
    assert source_bin[0]["actual_qty"] == 25, source_bin
    bags = lst("APH Bag Movement", {"voucher_no": posted["name"], "inactive": 0}, ["bags", "kg"], ktt)
    assert len(bags) == 1 and bags[0]["bags"] == 0 and bags[0]["kg"] == 5, bags
    returns = lst("Sales Invoice", {"return_against": ["is", "set"], "customer": f["kh2"], "docstatus": 1}, ["name"], ktt)
    matches = [get("Sales Invoice", r["name"], ktt) for r in returns]
    credit = [r for r in matches if any(i.get("delivery_note") == posted["name"] for i in r["items"])]
    assert len(credit) == 1 and abs(abs(credit[0]["grand_total"]) - abs(dn["grand_total"]) / 5) < 1, credit
    assert counts()["Payment Entry"] == before["Payment Entry"], "Bù trừ đã tạo tiền thực chi"
    emit("HTTP_014_TRA_LE_5KG", "PASS", {"delivered": 25, "returned": 5, "customer_keeps": 20,
         "physical_bags": 0, "quarantine": True, "draft_no_posting": True, "retry_no_duplicate": True,
         "reserved_limits": True, "credit_once": credit[0]["name"]})
