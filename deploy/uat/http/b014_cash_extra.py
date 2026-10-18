"""Đối chứng dương cho nguồn hóa đơn trả ngay và quỹ nhà máy của2A."""
H = "kh_aph_nguoi_giu_tien"


def chay(rpc, get, insert, submit, lst, ktt, f, emit):
    def call(method, args): return rpc(method, args, ktt)
    args = {"company": f["aph"], "from_date": f["date"], "to_date": f["date"]}
    def review(): return call("kh_aph.cash_custody.review", args)
    invoice = submit(insert({"doctype": "Sales Invoice", "company": f["aph"], "customer": f["kh2"],
        "posting_date": f["date"], "due_date": f["date"], "currency": "VND", "selling_price_list": f["pl"],
        "kh_aph_thu_ngay_tk": f["acc"]["tien"], H: f["ktbh"],
        "items": [{"item_code": f["A"], "qty": 1, "rate": 35000, "warehouse": f["kho"]}]}, ktt), ktt)
    payments = lst("Payment Entry", {"docstatus": 1, "remarks": ["like", "%" + invoice["name"] + "%"]}, ["name"], ktt)
    assert len(payments) == 1, payments
    pe = get("Payment Entry", payments[0]["name"], ktt)
    assert pe.get(H) == f["ktbh"] and pe["paid_to"] == f["acc"]["tien"]
    si_rows = [r for r in review() if r["voucher_no"] == pe["name"]]
    assert len(si_rows) == 1 and si_rows[0]["holder"] == f["ktbh"]
    assert abs(float(si_rows[0]["debit"]) - float(invoice["grand_total"])) < .05
    purchase = submit(insert({"doctype": "Purchase Invoice", "company": f["aph"], "supplier": f["ncc"],
        "posting_date": f["date"], "due_date": f["date"], "currency": "VND", "is_paid": 1,
        "cash_bank_account": f["acc"]["tien"], "paid_amount": 100, H: f["ktbh"],
        "items": [{"item_code": f["A"], "qty": 1, "rate": 100, "expense_account": f["acc"]["cp"]}]}, ktt), ktt)
    pi_rows = [r for r in review() if r["voucher_no"] == purchase["name"]]
    assert len(pi_rows) == 1 and pi_rows[0]["holder"] == f["ktbh"] and float(pi_rows[0]["credit"]) == 100, pi_rows
    emit("HTTP_2A_INVOICE_CASH_SOURCES", "PASS", {"sales_auto_payment_holder": True, "purchase_paid_cash_holder": True})

    company = get("Company", f["aph"], ktt)
    original = company.get("kh_aph_quy_nha_may")
    try:
        call("frappe.client.set_value", {"doctype": "Company", "name": f["aph"], "fieldname": "kh_aph_quy_nha_may", "value": f["acc"]["tien"]})
        source = submit(insert({"doctype": "APH Phieu quy nha may", "company": f["aph"], "posting_date": f["date"],
            "loai": "Thu tiền khách", "customer": f["kh2"], H: f["ktbh"],
            "dong": [{"dien_giai": "UAT người thực giữ quỹ nhà máy", "so_tien": 12345}]}, ktt), ktt)
        rows = [r for r in review() if r["voucher_no"] == source["journal_entry"]]
        assert len(rows) == 1 and rows[0]["holder"] == f["ktbh"] and float(rows[0]["debit"]) == 12345, rows
    finally:
        call("frappe.client.set_value", {"doctype": "Company", "name": f["aph"], "fieldname": "kh_aph_quy_nha_may", "value": original or ""})
    emit("HTTP_2A_FACTORY_CASH_SOURCE", "PASS", {"native_je_holder": True, "cash_counted_once": True})
