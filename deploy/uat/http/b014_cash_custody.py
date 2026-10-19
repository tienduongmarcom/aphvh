"""Lát 2A trên dữ liệu giả, dùng backup/restore của runner b014."""
import json
import os
from pathlib import Path
import subprocess
import uuid

H = "kh_aph_nguoi_giu_tien"


def chay(rpc, get, insert, submit, lst, denied, ktt, ktbh, dung, f, phien, emit):
    def call(method, args): return rpc(method, args, ktt)
    args = {"company": f["aph"], "from_date": f["date"], "to_date": f["date"]}
    def review(): return call("kh_aph.cash_custody.review", args)
    def counts(): return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("GL Entry", "Payment Ledger Entry", "Payment Entry", "Journal Entry")}

    # Màn thu cũ: tiền mặt có người giữ, chuyển khoản không tự nhận metadata mặt.
    received = rpc("kh_aph.ban_quay.thu_tien", {"request_id": f["p"] + "-thu-quay-b014-cash-custody-1", "company": f["aph"], "customer": f["kh2"],
        "tien_mat": 100000, "chuyen_khoan": 200000, "tk_ngan_hang": f["acc"]["bank"],
        "ma_gd": f["p"] + "-custody-" + uuid.uuid4().hex[:6], "nguoi_giu_tien": f["ktbh"]}, ktbh)
    notes = [get("Payment Entry", name, ktt) for name in received["phieu_thu"]]
    cash_note = next(doc for doc in notes if doc["paid_to"] == f["acc"]["tien"])
    assert cash_note.get(H) == f["ktbh"]
    assert all(not doc.get(H) for doc in notes if doc["name"] != cash_note["name"])
    before = counts()
    selected = [r for r in review() if r["voucher_no"] in received["phieu_thu"]]
    assert len(selected) == 1 and selected[0]["holder"] == f["ktbh"] and float(selected[0]["debit"]) == 100000, selected
    assert counts() == before
    emit("HTTP_2A_QUAY_CASH_SOURCE", "PASS", {"cash_holder": True, "bank_not_cash": True, "report_read_only": True})

    def journal(holder=None):
        return {"doctype": "Journal Entry", "company": f["aph"], "posting_date": f["date"], "accounts": [
            {"account": f["acc"]["tien"], "debit_in_account_currency": 17, H: holder},
            {"account": f["acc"]["cp"], "credit_in_account_currency": 17}]}
    known = submit(insert(journal(f["ktbh"]), ktt), ktt)
    unknown = submit(insert(journal(), ktt), ktt)
    rows = {r["voucher_no"]: r for r in review() if r["voucher_no"] in (known["name"], unknown["name"])}
    assert rows[known["name"]]["holder"] == f["ktbh"]
    assert rows[unknown["name"]]["holder"] == "" and rows[unknown["name"]]["status"] == "Chưa xác minh"
    invalid = journal(f["ktbh"])
    invalid["accounts"].insert(1, {"account": f["acc"]["tien"], "debit_in_account_currency": 1, H: f["ktt"]})
    invalid["accounts"][-1]["credit_in_account_currency"] = 18
    denied(lambda: insert(invalid, ktt), text="Cùng tài khoản")
    denied(lambda: insert(journal("Guest"), ktt), text="tài khoản nội bộ")
    denied(lambda: rpc("frappe.client.set_value", {"doctype": "Payment Entry", "name": cash_note["name"], "fieldname": H, "value": f["ktt"]}, ktt))
    assert get("Payment Entry", cash_note["name"], ktt)[H] == f["ktbh"]
    emit("HTTP_2A_SOURCE_IMMUTABLE_UNKNOWN", "PASS", {"no_owner_default": True, "no_reassign_submitted": True, "merge_ambiguity_denied": True})

    # Tiền thực thu và JE liên kết là cùng một nguồn GL: không đếm cả hai.
    route = submit(insert({"doctype": "APH Funds Route", "receiving_company": f["aph"], "owner_company": f["aph"],
        "holding_account": f["acc"]["holding"], "reason": "UAT 2A tuyến mặt"}, ktt), ktt)
    receipt = submit(insert({"doctype": "APH Funds Receipt", "company": f["aph"], "posting_date": f["date"],
        "bank_account": f["acc"]["tien"], "route": route["name"], "customer": f["kh2"], "amount": 54321,
        "external_reference": f["p"] + "-cash-receipt", "reason": "UAT nguồn mặt", H: f["ktbh"]}, ktt), ktt)
    je = get("Journal Entry", receipt["journal_entry"], ktt)
    assert next(r for r in je["accounts"] if r["account"] == f["acc"]["tien"])[H] == f["ktbh"]
    money_rows = [r for r in review() if r["voucher_no"] in (receipt["name"], je["name"])]
    assert len(money_rows) == 1 and money_rows[0]["holder"] == f["ktbh"] and float(money_rows[0]["debit"]) == 54321, money_rows
    refund = call("kh_aph.funds.create_action", {"values": json.dumps({"receipt": receipt["name"], "action_type": "Hoàn tiền",
        "amount": 1000, "posting_date": f["date"], "reason": "UAT kiểm phía chi", "bank_account": f["acc"]["tien"],
        "external_reference": f["p"] + "-custody-refund", "kh_aph_nguoi_giao_tien": f["ktbh"]})})
    refunded = [r for r in review() if r["voucher_no"] == refund["journal_entry"]]
    assert len(refunded) == 1 and refunded[0]["holder"] == f["ktbh"] and float(refunded[0]["credit"]) == 1000, refunded
    emit("HTTP_2A_FUNDS_SINGLE_GL_SOURCE", "PASS", {"receipt_je_metadata": True, "cash_counted_once": True, "refund_payer": True})

    before = counts()
    denied(lambda: rpc("kh_aph.cash_custody.review", args, dung), ("PermissionError",))
    denied(lambda: rpc("kh_aph.cash_custody.review", {**args, "company": f["vh"]}, phien(f["scope_co"])), ("PermissionError",))
    denied(lambda: rpc("kh_aph.cash_custody.review", {**args, "to_date": "2030-01-01"}, ktt))
    cash_vh = lst("Account", {"company": f["vh"], "account_type": "Cash", "is_group": 0}, ["name"], ktt)[0]["name"]
    expense_vh = lst("Account", {"company": f["vh"], "root_type": "Expense", "is_group": 0}, ["name"], ktt)[0]["name"]
    denied(lambda: insert({**journal(f["scope_co"]), "company": f["vh"], "accounts": [
        {"account": cash_vh, "debit_in_account_currency": 17, H: f["scope_co"]},
        {"account": expense_vh, "credit_in_account_currency": 17}]}, ktt), ("PermissionError",))
    report = call("frappe.desk.query_report.run", {"report_name": "Ra nguoi giu tien mat", "filters": json.dumps(args)})
    assert any(r.get("voucher_no") == cash_note["name"] for r in report["result"])
    assert counts() == before
    emit("HTTP_2A_REPORT_PERMISSION", "PASS", {"no_cost_role_denied": True, "company_scope": True, "native_report": True, "ledger_unchanged": True})

    from b014_cash_extra import chay as extra_cases
    extra_cases(rpc, get, insert, submit, lst, ktt, f, emit)

    if os.environ.get("GITHUB_ACTIONS"):
        proc = subprocess.run(["node", str(Path(__file__).with_name("ban-nhanh-desk.mjs")), cash_note["name"], "nguoi-giu-tien"],
            text=True, capture_output=True, timeout=150)
        assert proc.returncode == 0, (proc.stdout[-2000:], proc.stderr[-2000:])
        for line in proc.stdout.splitlines():
            if line.startswith('{"case":'):
                value = json.loads(line); emit(value["case"], value["status"], value.get("detail"))
