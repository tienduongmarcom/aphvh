"""Một chuỗi trên cùng đơn: VAT–cọc–giao từng phần–bản ký–thu nốt–lãi gộp."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, ktt, f, chain, emit):
    root, note = chain["shared_order"], chain["delivery_note"]
    def call(method, args): return rpc(method, args, ktt)
    def near(value, expected): assert abs(float(value) - expected) < .05, (value, expected)
    def figures(): return call("kh_aph.funds.shared_financials", {"name": root})
    old_debt = {r["name"]: r["outstanding_amount"] for r in lst("Sales Invoice",
        {"customer": f["kh2"], "docstatus": 1}, ["name", "outstanding_amount"], ktt)}
    assert old_debt, "Cần nợ cũ để kiểm không tự cấn FIFO"
    near(figures()["order_total"], 770000)  # 20kg ×35000 +10%VAT, khác net_total700000.
    route = submit(insert({"doctype": "APH Funds Route", "receiving_company": f["aph"], "owner_company": f["aph"],
        "holding_account": f["acc"]["holding"], "reason": "UAT tuyến tiền thực nhận cùng đơn vị"}, ktt), ktt)
    prefix = f["p"] + "-chain-" + uuid.uuid4().hex[:6]
    def receive(amount, suffix):
        return submit(insert({"doctype": "APH Funds Receipt", "company": f["aph"], "posting_date": f["date"],
            "bank_account": f["acc"]["bank"], "route": route["name"], "customer": f["kh2"], "amount": amount,
            "external_reference": prefix + suffix, "reason": "UAT thực thu cho đơn đang kiểm"}, ktt), ktt)
    def action(receipt, kind, amount, **values):
        return call("kh_aph.funds.create_action", {"values": json.dumps({"receipt": receipt["name"],
            "action_type": kind, "amount": amount, "posting_date": f["date"], "reason": "UAT phân bổ đích danh", **values})})
    deposit = receive(100000, "-deposit")
    reserve = action(deposit, "Giữ cọc", 100000, shared_order=root, source_company=f["aph"])
    near(figures()["remaining_to_pay"], 670000)
    near(figures()["reserved_deposit"], 100000)
    call("kh_aph.delivery_status.confirm", {"name": note, "action": "handoff"})
    dn = get("Delivery Note", note, ktt)
    assert dn["kh_aph_delivery_state"] == "Đang giao" and dn["docstatus"] == 1
    invoice = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", note], ["docstatus", "=", 1]], ["name"], ktt)
    assert len(invoice) == 1, invoice
    name = invoice[0]["name"]
    near(get("Sales Invoice", name, ktt)["grand_total"], 192500)
    action(deposit, "Cấn hóa đơn", 100000, invoice=name, source_reservation=reserve["name"])
    near(figures()["dispatched_debt"], 92500)
    near(figures()["undelivered_value"], 577500)
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("GL Entry", "Stock Ledger Entry", "Sales Invoice")}
    handoff = get("Delivery Note", note, ktt)
    assert handoff["kh_aph_ban_giao_boi"] == f["ktt"] and handoff["kh_aph_ban_giao_luc"]
    before_receive = counts()
    call("kh_aph.delivery_status.confirm", {"name": note, "action": "receive"})
    file = insert({"doctype": "File", "file_name": prefix + ".txt", "content": "UAT bản ký của chuỗi có VAT",
                   "is_private": 1, "attached_to_doctype": "Delivery Note", "attached_to_name": note}, ktt)
    doc = get("Delivery Note", note, ktt)
    doc["kh_aph_ban_ky"] = file["file_url"]
    doc = call("frappe.client.save", {"doc": json.dumps(doc)})
    call("kh_aph.ho_so_giao_nhan.doi_chieu", {"name": note, "modified": doc["modified"]})
    after_sign = get("Delivery Note", note, ktt)
    assert after_sign["kh_aph_ban_giao_luc"] == handoff["kh_aph_ban_giao_luc"]
    assert after_sign["kh_aph_ban_giao_boi"] == handoff["kh_aph_ban_giao_boi"]
    assert counts() == before_receive, "Nhận hàng/lưu bản ký đã ghi sổ lần hai"
    remainder = receive(92500, "-balance")
    action(remainder, "Cấn hóa đơn", 92500, invoice=name)
    near(get("Sales Invoice", name, ktt)["outstanding_amount"], 0)
    near(figures()["remaining_to_pay"], 577500)
    near(figures()["dispatched_debt"], 0)
    for old, outstanding in old_debt.items():
        near(get("Sales Invoice", old, ktt)["outstanding_amount"], float(outstanding))
    report = call("frappe.desk.query_report.run", {"report_name": "Lai gop quan tri", "filters": json.dumps({
        "company": f["aph"], "tu_ngay": f["date"], "den_ngay": f["date"], "theo": "Đơn"})})
    so = dn["items"][0]["against_sales_order"]
    row = next(r for r in report["result"] if r["khoa"] == so)
    near(row["dt"], 175000); near(row["gv"], 100000); near(row["lg"], 75000)
    emit("HTTP_014_TIEN_GIAO_NHAN_VAT_CHAIN", "PASS", {"order_with_vat": 770000, "delivered_with_vat": 192500,
         "deposit": 100000, "balance_paid": 92500, "undelivered": 577500, "old_debt_unchanged": True, "gross_margin": 75000})
