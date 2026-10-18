"""Xuất ngay, rollback trọn đợt và retry sau commit trên fixture dùng một lần."""
import json
import os
from pathlib import Path
import subprocess
import uuid
import urllib.error
from concurrent.futures import ThreadPoolExecutor


def chay(rpc, get, insert, submit, lst, denied, ktt, dung, f, phien, emit):
    def counts(): return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("Delivery Note", "Sales Invoice", "GL Entry", "Stock Ledger Entry")}
    def make(multi=False):
        items = [{"item_code": f["A"], "warehouse": f["kho"], "qty": 20, "rate": 35000}]
        if multi: items.append({"item_code": f["B"], "warehouse": f["kho_vh"], "qty": 20, "rate": 35000})
        return submit(insert({"doctype": "APH Shared Sales Order", "customer": f["kh2"], "transaction_date": f["date"],
            "delivery_date": f["date"], "selling_price_list": f["pl"], "currency": "VND", "items": items}, ktt), ktt)
    def payload(root, method="Vận chuyển"):
        rows = rpc("kh_aph.ban_nhanh.preview", {"shared_order": root["name"]}, ktt)["rows"]
        return {"shared_order": root["name"], "request_id": uuid.uuid4().hex,
            "selections": json.dumps([{"source_row": r["source_row"], "qty": 2} for r in rows]),
            "delivery": json.dumps({"delivery_method": method, "recipient": "Người nhận UAT"}), "dispatcher": "Kho UAT"}
    def dispatch(p, caller=ktt): return rpc("kh_aph.ban_nhanh.create_and_dispatch", p, caller)
    root = make(); p = payload(root)
    before = counts()
    no_submit = phien(f["ktbh_no_submit"])
    assert rpc("kh_aph.ban_nhanh.preview", {"shared_order":root["name"]}, no_submit)["can_dispatch"] is False
    denied(lambda: dispatch(p, no_submit), ("PermissionError",))
    denied(lambda: dispatch(p, dung), ("PermissionError",))
    denied(lambda: dispatch({**p, "dispatcher": ""}))
    denied(lambda: dispatch({**p, "delivery": "{}"}))
    assert counts() == before
    emit("HTTP_014_XUAT_NGAY_QUYEN", "PASS", {"submit_required": True, "no_cost_denied": True, "no_partial_draft": True})

    for method, expected in (("Vận chuyển", "Đang giao"), ("Khách đến lấy", "Khách đã nhận")):
        if method == "Khách đến lấy": root = make(); p = payload(root, method)
        made = dispatch(p)
        assert len(made["delivery_notes"]) == 1 and made["delivery_notes"][0]["docstatus"] == 1
        dn = get("Delivery Note", made["delivery_notes"][0]["name"], ktt)
        assert dn["kh_aph_delivery_state"] == expected and dn["kh_aph_nguoi_thuc_giao"] == "Kho UAT"
        assert dn["kh_aph_ban_giao_boi"] == f["ktt"] and dn["kh_aph_ban_giao_luc"]
        state = counts()
        printed = rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": dn["name"]}, ktt)["html"]
        assert "ĐÃ XÁC NHẬN XUẤT - BẢN SAO" in printed and dn["name"] in printed and "Kho UAT" in printed
        assert counts() == state and get("Delivery Note", dn["name"], ktt)["modified"] == dn["modified"]
        again = dispatch(p)
        assert again["reused"] and again["delivery_notes"] == made["delivery_notes"] and counts() == state
        denied(lambda: dispatch({**p, "dispatcher": "Kho khác"}))
        draft_args = {k: v for k, v in p.items() if k != "dispatcher"}
        denied(lambda: rpc("kh_aph.ban_nhanh.create_drafts", draft_args, ktt))
        if method == "Vận chuyển":
            rpc("kh_aph.delivery_status.confirm", {"name": dn["name"], "action": "receive"}, ktt)
            assert dispatch(p)["reused"] and counts() == state
    draft_root = make(); draft_p = payload(draft_root)
    rpc("kh_aph.ban_nhanh.create_drafts", {k:v for k,v in draft_p.items() if k!="dispatcher"}, ktt)
    state = counts(); denied(lambda: dispatch(draft_p)); assert counts() == state
    emit("HTTP_014_XUAT_NGAY_HAI_CACH_GIAO", "PASS", {"handoff_and_pickup": True, "retry_after_receive": True,
        "no_mode_escalation": True, "no_duplicate_ledger": True})

    multi = make(True); batch = payload(multi)
    rows = rpc("kh_aph.ban_nhanh.preview", {"shared_order": multi["name"]}, ktt)["rows"]
    assert [r["company"] for r in sorted(rows, key=lambda r:(r["source_order"],r["warehouse"]))] == [f["aph"],f["vh"]]
    state = counts()
    bin_before = lst("Bin", {"item_code":f["A"], "warehouse":f["kho"]}, ["actual_qty"], ktt)[0]["actual_qty"]
    denied(lambda: dispatch(batch), ("NegativeStockError", "ValidationError"))
    assert counts() == state, "Thiếu tồn nhóm sau đã để lại phiếu hoặc sổ của nhóm đầu"
    assert lst("Bin", {"item_code":f["A"], "warehouse":f["kho"]}, ["actual_qty"], ktt)[0]["actual_qty"] == bin_before
    account = lst("Account", {"company":f["vh"],"account_number":"9990"}, ["name"], ktt)[0]["name"]
    submit(insert({"doctype":"Stock Reconciliation","company":f["vh"],"purpose":"Opening Stock","expense_account":account,
        "items":[{"item_code":f["B"],"warehouse":f["kho_vh"],"qty":10,"valuation_rate":20000}]}, ktt), ktt)
    made = dispatch(batch)
    assert len(made["delivery_notes"]) == 2 and {n["company"] for n in made["delivery_notes"]} == {f["aph"],f["vh"]}
    state = counts(); assert dispatch(batch)["reused"] and counts() == state
    vh_note = next(n["name"] for n in made["delivery_notes"] if n["company"] == f["vh"])
    for user in ("scope_co", "scope_wh"):
        denied(lambda: dispatch(batch, phien(f[user])), ("PermissionError",))
        denied(lambda: rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": vh_note}, phien(f[user])), ("PermissionError",))
    assert counts() == state
    emit("HTTP_014_XUAT_NGAY_NHIEU_NGUON", "PASS", {"later_stock_failure_atomic":True,"retry_failed_batch":True,
        "two_companies":True,"scope_retry_denied":True})

    concurrent = payload(make()); state = counts()
    callers = [phien(f["ktt"]), phien(f["ktt"])]
    def call(caller):
        try: return dispatch(concurrent, caller)
        except urllib.error.HTTPError as exc:
            error = json.loads(exc.read().decode())
            assert error.get("exc_type") == "QueryDeadlockError", error
            return None
    with ThreadPoolExecutor(2) as pool: results = list(pool.map(call, callers))
    results = [r or dispatch(concurrent) for r in results]
    assert results[0]["delivery_notes"] == results[1]["delivery_notes"]
    after = counts(); assert after["Delivery Note"] == state["Delivery Note"]+1 and after["Sales Invoice"] == state["Sales Invoice"]+1
    assert dispatch(concurrent)["reused"] and counts() == after
    emit("HTTP_014_XUAT_NGAY_DONG_THOI", "PASS", {"one_note":True,"one_invoice":True,"ledger_stable":True})

    if os.environ.get("GITHUB_ACTIONS") == "true":
        browser_root = make()
        result = subprocess.run(["node","--experimental-websocket",str(Path(__file__).with_name("ban-nhanh-desk.mjs")),browser_root["name"],"xuat-ngay"],
            check=True,text=True,capture_output=True,timeout=180)
        evidence = json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{"case":')))
        assert evidence["status"] == "PASS", evidence
        emit(evidence["case"], "PASS", evidence["detail"])
