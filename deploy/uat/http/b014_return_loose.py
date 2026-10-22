"""Nhận5kg trong bao25kg sau khi khách đã nhận: kiểm thật kho, nợ, sổ bao và retry."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktt, f, emit):
    old = get("Item", f["A"], ktt)
    item = f["p"] + "-TRA-LE-25"
    insert({"doctype": "Item", "item_code": item, "item_name": "Hàng thử trả lẻ 25kg", "item_group": old["item_group"],
            "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average", "kh_aph_kg_per_bag": 25,
            "taxes": [{"item_tax_template": t["item_tax_template"]} for t in old["taxes"]]}, ktt)
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
    denied(lambda: rpc("frappe.client.set_value", {"doctype": "Delivery Note", "name": draft["name"],
        "fieldname": "kh_aph_ma_nhan_tra", "value": ""}, ktt))
    after_draft = counts()
    assert after_draft["Delivery Note"] == before["Delivery Note"] + 1
    assert all(after_draft[dt] == before[dt] for dt in before if dt != "Delivery Note"), (before, after_draft)
    assert rpc("kh_aph.sales_return.create_draft", payload, ktt)["name"] == created["name"] and counts() == after_draft
    denied(lambda: rpc("kh_aph.sales_return.create_draft", {**payload, "reason": "Đổi nội dung"}, ktt))
    denied(lambda: rpc("kh_aph.sales_return.create_draft", {**payload, "request_id": uuid.uuid4().hex,
        "selections": json.dumps([{"source_row": row["source_row"], "qty": 21, "bags": 0}])}, ktt))
    assert rpc("kh_aph.sales_return.preview", {"delivery_note": dn["name"]}, ktt)["rows"][0]["remaining_qty"] == 20
    moved = json.loads(json.dumps(draft))
    assert moved['items'][0].get('against_sales_order') and moved['items'][0].get('so_detail')
    moved['items'][0]['against_sales_order'] = None
    moved['items'][0]['so_detail'] = None
    denied(lambda: rpc('frappe.client.save', {'doc': json.dumps(moved)}, ktt))
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

    def receive_return(settlement):
        args = {**payload, "request_id": uuid.uuid4().hex, "settlement": settlement}
        return submit(get("Delivery Note", rpc("kh_aph.sales_return.create_draft", args, ktt)["name"], ktt), ktt)

    # Chưa thu tiền: chọn hoàn cũng chỉ giảm khoản nợ đúng lượng, không chuẩn bị chi khống.
    no_cash_before = counts()["Payment Entry"]
    unpaid = receive_return("Hoàn tiền")
    assert not get("Delivery Note", unpaid["name"], ktt).get("kh_aph_chung_tu_xu_ly")
    assert counts()["Payment Entry"] == no_cash_before
    original_invoice = get("Sales Invoice", credit[0]["return_against"], ktt)
    per_return = abs(float(credit[0]["grand_total"]))
    assert original_invoice["outstanding_amount"] > per_return
    emit("HTTP_014_TRA_LE_CHUA_THU_KHONG_HOAN", "PASS", {"reduce_debt_only": True, "no_cash_draft": True})

    # Thu một phần còn nợ nửa giá trị5kg. Trả tiếp5kg: chỉ hoàn phần vượt nợ.
    remaining_debt = per_return / 2
    payment = rpc("erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
                  {"dt": "Sales Invoice", "dn": original_invoice["name"], "bank_account": f["acc"]["tien"]}, ktt)
    payment["paid_amount"] = payment["received_amount"] = float(original_invoice["outstanding_amount"]) - remaining_debt
    payment["references"][0]["allocated_amount"] = payment["paid_amount"]
    payment["kh_aph_nguoi_giu_tien"] = f["ktbh"]
    submit(insert(payment, ktt), ktt)
    assert abs(get("Sales Invoice", original_invoice["name"], ktt)["outstanding_amount"] - remaining_debt) < 1
    partly_paid = receive_return("Hoàn tiền")
    refund = get("Payment Entry", get("Delivery Note", partly_paid["name"], ktt)["kh_aph_chung_tu_xu_ly"], ktt)
    assert refund["docstatus"] == 0 and abs(refund["paid_amount"] - (per_return - remaining_debt)) < 1, refund["name"]
    assert len(refund["references"]) == 1
    refund_source = get("Sales Invoice", refund["references"][0]["reference_name"], ktt)
    assert refund_source["is_return"] == 1 and refund_source["return_against"] == original_invoice["name"]
    assert abs(get("Sales Invoice", original_invoice["name"], ktt)["outstanding_amount"]) < 1
    assert refund["references"][0]["allocated_amount"] < 0
    invoices_before_refund = counts()["Sales Invoice"]
    refund["kh_aph_nguoi_giao_tien"] = f["ktbh"]
    refund = submit(refund, ktt)
    assert abs(get("Sales Invoice", original_invoice["name"], ktt)["outstanding_amount"]) < 1
    assert counts()["Sales Invoice"] == invoices_before_refund, "Chi hoàn sinh thêm hóa đơn giảm"
    assert abs(get("Sales Invoice", refund_source["name"], ktt)["outstanding_amount"]) < 1
    assert abs(get("Sales Invoice", original_invoice["name"], ktt)["outstanding_amount"]) < 1

    # Đã thanh toán đủ phần còn giữ:5kg trả lần sau được hoàn đủ giá trị5kg.
    paid = receive_return("Hoàn tiền")
    paid_refund = get("Payment Entry", get("Delivery Note", paid["name"], ktt)["kh_aph_chung_tu_xu_ly"], ktt)
    assert paid_refund["docstatus"] == 0 and abs(paid_refund["paid_amount"] - per_return) < 1
    paid_refund["kh_aph_nguoi_giao_tien"] = f["ktbh"]
    submit(paid_refund, ktt)
    assert abs(get("Sales Invoice", paid_refund["references"][0]["reference_name"], ktt)["outstanding_amount"]) < 1
    assert abs(get("Sales Invoice", original_invoice["name"], ktt)["outstanding_amount"]) < 1
    emit("HTTP_014_TRA_LE_THU_MOT_PHAN_HOAN_DUNG", "PASS", {"partial_refund": per_return - remaining_debt,
         "full_refund": per_return, "source_invoice_cleared": True, "no_second_credit_invoice": True})
    opened_before = counts()
    opened = rpc('kh_aph.sales_return.money_document', {'delivery_note': paid['name']}, ktt)
    assert opened == {'doctype': 'Payment Entry', 'name': paid_refund['name'], 'docstatus': 1}
    linked_return = get('Delivery Note', paid['name'], ktt)
    denied(lambda: rpc('frappe.client.save', {'doc': json.dumps({**linked_return, 'kh_aph_chung_tu_xu_ly': ''})}, ktt))
    denied(lambda: rpc('kh_aph.sales_return.money_document', {'delivery_note': unpaid['name']}, ktt))
    assert counts() == opened_before
    emit('HTTP_014_MO_PHIEU_HOAN', 'PASS', {'opens_existing_payment': True, 'source_link_protected': True,
         'unpaid_no_refund_link': True, 'no_additional_posting': True})

    # Đổi mã khác: nhận lại lượng thực, rồi chọn mã mới trên đơn chuẩn, không sinh lại mã cũ.
    exchange = receive_return("Đổi hàng")
    assert not get("Delivery Note", exchange["name"], ktt).get("kh_aph_chung_tu_xu_ly"), "Tự sinh lại phiếu cùng mã cũ"
    exchange_before = counts()
    prepared = rpc("kh_aph.sales_exchange.prepare", {"return_note": exchange["name"]}, ktt)
    assert prepared["company"] == f["aph"] and prepared["defaults"]["customer"] == f["kh2"]
    assert counts() == exchange_before
    defaults = prepared["defaults"]
    replacement_values = {"doctype": "APH Shared Sales Order", **defaults, "items": [
        {"item_code": f["A"], "qty": 2, "rate": 40000, "warehouse": f["kho"]}]}
    replacement = insert(replacement_values, ktt)
    assert replacement["docstatus"] == 0 and replacement["items"][0]["item_code"] != item
    assert counts() == exchange_before, "Lưu đơn thay nháp làm phát sinh kho/nợ/tiền"
    assert rpc("kh_aph.sales_exchange.prepare", {"return_note": exchange["name"]}, ktt) == {"existing": replacement["name"]}
    denied(lambda: insert(replacement_values, ktt))
    denied(lambda: rpc("frappe.client.set_value", {"doctype": "APH Shared Sales Order", "name": replacement["name"],
        "fieldname": "kh_aph_phieu_tra_doi", "value": ""}, ktt))
    replacement = submit(get("APH Shared Sales Order", replacement["name"], ktt), ktt)
    children = lst("Sales Order", {"kh_aph_shared_order": replacement["name"], "docstatus": 1}, ["name"], ktt)
    child = get("Sales Order", children[0]["name"], ktt)
    denied(lambda: insert({"doctype": "APH Source Change", "shared_order": replacement["name"], "source_order": child["name"],
        "source_row": child["items"][0]["name"], "target_warehouse": f["kho_vh"], "qty": 1, "reason": "Thử cấn chéo đơn vị"}, ktt))
    # Hủy đơn chưa xuất: giữ nguồn lịch sử và cho lập lại, không kẹt khóa duy nhất.
    rpc("frappe.client.cancel", {"doctype": "APH Shared Sales Order", "name": replacement["name"]}, ktt)
    cancelled = get("APH Shared Sales Order", replacement["name"], ktt)
    assert cancelled["kh_aph_phieu_tra_doi"] == exchange["name"] and not cancelled.get("kh_aph_luot_doi_dang_mo")
    assert "defaults" in rpc("kh_aph.sales_exchange.prepare", {"return_note": exchange["name"]}, ktt)
    replacement = submit(insert(replacement_values, ktt), ktt)
    selected = rpc("kh_aph.ban_nhanh.preview", {"shared_order": replacement["name"]}, ktt)["rows"][0]
    replaced = rpc("kh_aph.ban_nhanh.create_and_dispatch", {"shared_order": replacement["name"], "request_id": uuid.uuid4().hex,
        "selections": json.dumps([{"source_row": selected["source_row"], "qty": 2}]),
        "delivery": json.dumps({"delivery_method": "Khách đến lấy", "recipient": "Khách UAT đổi mã"}), "dispatcher": "Kho UAT"}, ktt)
    issued = get("Delivery Note", replaced["delivery_notes"][0]["name"], ktt)
    assert issued["docstatus"] == 1 and issued["items"][0]["item_code"] == f["A"] and issued["items"][0]["qty"] == 2
    assert issued["company"] == f["aph"] and counts()["Sales Invoice"] == exchange_before["Sales Invoice"] + 1
    emit("HTTP_014_DOI_MA_MOI", "PASS", {"return_note": exchange["name"], "new_order": replacement["name"],
         "new_item": f["A"], "native_sales_flow": True, "draft_no_posting": True, "one_active_order": True})

    # Đơn cũ đã giảm chất lượng100.000: trả cả bao không được hoàn cả giá gốc cho khách chưa trả tiền.
    quality_root = submit(insert({"doctype": "APH Shared Sales Order", "customer": f["kh2"], "transaction_date": f["date"],
        "delivery_date": f["date"], "selling_price_list": f["pl"], "currency": "VND",
        "items": [{"item_code": item, "warehouse": f["kho"], "qty": 25, "rate": 35000, "kh_aph_bags": 1, "kh_aph_kg_per_bag": 25}]}, ktt), ktt)
    qrow = rpc("kh_aph.ban_nhanh.preview", {"shared_order": quality_root["name"]}, ktt)["rows"][0]
    qmade = rpc("kh_aph.ban_nhanh.create_and_dispatch", {"shared_order": quality_root["name"], "request_id": uuid.uuid4().hex,
        "selections": json.dumps([{"source_row": qrow["source_row"], "qty": 25}]),
        "delivery": json.dumps({"delivery_method": "Khách đến lấy", "recipient": "Khách UAT chất lượng"}), "dispatcher": "Kho UAT"}, ktt)
    qdn = get("Delivery Note", qmade["delivery_notes"][0]["name"], ktt)
    qinvoices = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", qdn["name"]], ["docstatus", "=", 1]], ["name"], ktt)
    qinvoice = get("Sales Invoice", qinvoices[0]["name"], ktt)
    reduced = rpc("kh_aph.sales_p1.giam_gia_sau_giao", {"sales_invoice": qinvoice["name"], "so_tien": 100000,
        "ly_do": "Thỏa thuận giảm chất lượng đơn cũ"}, ktt)
    submit(get("Journal Entry", reduced["but_toan"], ktt), ktt)
    pending_quality = rpc("kh_aph.sales_p1.giam_gia_sau_giao", {"sales_invoice": qinvoice["name"], "so_tien": 20000,
        "ly_do": "Đang đề nghị thêm, chưa thống nhất"}, ktt)
    denied(lambda: rpc("frappe.client.set_value", {"doctype": "Journal Entry", "name": pending_quality["but_toan"],
        "fieldname": "kh_aph_giam_gia_hd", "value": ""}, ktt))
    qr = rpc("kh_aph.sales_return.preview", {"delivery_note": qdn["name"]}, ktt)["rows"][0]
    qr_payload = {**payload, "delivery_note": qdn["name"], "request_id": uuid.uuid4().hex, "settlement": "Hoàn tiền",
        "reason": "Khách trả cả25kg sau giảm chất lượng, đối chiếu giá trị còn lại",
        "selections": json.dumps([{"source_row": qr["source_row"], "qty": 25, "bags": 1}])}
    qdraft = get("Delivery Note", rpc("kh_aph.sales_return.create_draft", qr_payload, ktt)["name"], ktt)
    state = counts()
    denied(lambda: submit(qdraft, ktt))
    assert counts() == state and get("Delivery Note", qdraft["name"], ktt)["docstatus"] == 0
    assert abs(get("Sales Invoice", qinvoice["name"], ktt)["outstanding_amount"] - (qinvoice["grand_total"] - 100000)) < 1
    # Kế toán đối chiếu thỏa thuận và hạ giá trị nhận trả còn lại trên phiếu chuẩn; giữ đủ25kg thực nhận.
    qdraft = get("Delivery Note", qdraft["name"], ktt)
    qdraft["items"][0]["rate"] *= (qinvoice["grand_total"] - 100000) / qinvoice["grand_total"]
    qposted = submit(qdraft, ktt)
    assert qposted["items"][0]["qty"] == -25
    assert abs(get("Sales Invoice", qinvoice["name"], ktt)["outstanding_amount"]) < 1
    assert counts()["Payment Entry"] == state["Payment Entry"], "Khách chưa trả tiền nhưng nhận hoàn khoản giảm chất lượng"
    denied(lambda: submit(get("Journal Entry", pending_quality["but_toan"], ktt), ktt))
    assert abs(get("Sales Invoice", qinvoice["name"], ktt)["outstanding_amount"]) < 1
    emit("HTTP_014_TRA_SAU_GIAM_CHAT_LUONG", "PASS", {"old_quality_discount": 100000, "unpaid_no_refund": True,
         "full_physical_quantity": 25, "remaining_value_reviewed": True, "stale_discount_denied": True})
    return {'refund_return': paid['name'], 'refund': paid_refund['name']}
