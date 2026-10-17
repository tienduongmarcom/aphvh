"""Gọi sau bộ b014 trên site dữ liệu giả; dùng chung cơ chế backup/restore của runner."""
import json
import uuid
import os
from pathlib import Path
import subprocess
import urllib.error
from concurrent.futures import ThreadPoolExecutor


def chay(rpc, get, insert, submit, lst, denied, ktbh, dung, ktt, f, emit, phien):
    def ledger_counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("GL Entry", "Stock Ledger Entry", "Sales Invoice")}

    before = ledger_counts()
    root = insert({"doctype": "APH Shared Sales Order", "customer": f["kh2"],
                   "transaction_date": f["date"], "delivery_date": f["date"],
                   "selling_price_list": f["pl"], "currency": "VND",
                   "items": [{"item_code": f["A"], "warehouse": f["kho"], "qty": 20, "rate": 35000}]}, ktbh)
    root = submit(root, ktbh)
    args = {"shared_order": root["name"]}
    denied(lambda: rpc("kh_aph.ban_nhanh.preview", args, dung), ("PermissionError",))
    view = rpc("kh_aph.ban_nhanh.preview", args, ktbh)
    assert len(view["rows"]) == 1 and view["rows"][0]["remaining_qty"] == 20, view
    row = view["rows"][0]
    assert not ({"rate", "valuation_rate", "basic_rate", "amount"} & set(row)), row
    token = uuid.uuid4().hex
    selected = [{"source_row": row["source_row"], "qty": 5}]
    payload = {**args, "selections": json.dumps(selected), "request_id": token}
    made = rpc("kh_aph.ban_nhanh.create_drafts", payload, ktbh)
    assert len(made["delivery_notes"]) == 1 and made["delivery_notes"][0]["docstatus"] == 0, made
    note = get("Delivery Note", made["delivery_notes"][0]["name"], ktbh)
    assert note["items"][0]["qty"] == 5 and note["items"][0]["warehouse"] == f["kho"], note["name"]
    assert ledger_counts() == before, "Lập phiếu nháp đã phát sinh sổ/hoá đơn"
    repeat = rpc("kh_aph.ban_nhanh.create_drafts", payload, ktbh)
    assert repeat["reused"] and repeat["delivery_notes"] == made["delivery_notes"], repeat
    denied(lambda: rpc("kh_aph.ban_nhanh.create_drafts", {**payload,
        "selections": json.dumps([{**selected[0], "qty": 6}])}, ktbh))
    view = rpc("kh_aph.ban_nhanh.preview", args, ktbh)["rows"][0]
    assert (view["ordered_qty"], view["delivered_qty"], view["draft_qty"], view["remaining_qty"]) == (20, 0, 5, 15), view
    denied(lambda: rpc("kh_aph.ban_nhanh.create_drafts", {**payload, "request_id": uuid.uuid4().hex,
        "selections": json.dumps([{**selected[0], "qty": 16}])}, ktbh))
    emit("HTTP_014_BAN_NHANH_DRAFT_REPEAT", "PASS", {"delivery_note": note["name"], "remaining_kg": 15, "ledger_unchanged": True})

    html = rpc("kh_aph.ban_nhanh.print_batch", {**args, "request_id": token}, ktbh)["html"]
    for text in ("CHỜ XUẤT", note["name"], root["name"], "Người thực giao hàng", "Người thực nhận hàng", "Kg/bao"):
        assert text in html, text
    for text in ("valuation_rate", "basic_rate", "Đơn giá vốn", "Giá bán/kg"):
        assert text not in html, text
    denied(lambda: rpc("kh_aph.ban_nhanh.print_batch", {**args, "request_id": token}, dung), ("PermissionError",))
    assert ledger_counts() == before, "In đã phát sinh sổ"
    emit("HTTP_014_BAN_NHANH_PRINT", "PASS", {"quantity_only": True, "draft_label": True, "ledger_unchanged": True})

    if os.environ.get("GITHUB_ACTIONS") == "true":
        result = subprocess.run(["node", "--experimental-websocket", str(Path(__file__).with_name("ban-nhanh-desk.mjs")), root["name"]],
                                check=True, text=True, capture_output=True, timeout=150)
        evidence = json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{"case":')))
        assert evidence["status"] == "PASS", evidence
        emit(evidence["case"], "PASS", evidence["detail"])

    callers = [phien(f["ktbh"]), phien(f["ktbh"])]
    concurrent_payload = {**payload, "request_id": uuid.uuid4().hex,
                          "selections": json.dumps([{**selected[0], "qty": 4}])}
    def create(caller):
        try:
            return rpc("kh_aph.ban_nhanh.create_drafts", concurrent_payload, caller)
        except urllib.error.HTTPError as exc:
            data = json.loads(exc.read().decode())
            assert data.get("exc_type") == "QueryDeadlockError", data
            return None  # Deadlock không được ghi thêm; thử lại cùng mã sau khi request kia hoàn tất.
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(create, callers))
    assert any(results), "Cả hai yêu cầu đều lỗi"
    results = [r or rpc("kh_aph.ban_nhanh.create_drafts", concurrent_payload, ktbh) for r in results]
    assert results[0]["delivery_notes"] == results[1]["delivery_notes"], results
    final = rpc("kh_aph.ban_nhanh.preview", args, ktbh)["rows"][0]
    assert (final["draft_qty"], final["remaining_qty"]) == (9, 11), final
    assert ledger_counts() == before
    emit("HTTP_014_BAN_NHANH_CONCURRENT", "PASS", {"single_new_note": True, "draft_kg": 9, "remaining_kg": 11})

    closing = insert({"doctype": "Stock Closing Entry", "company": f["aph"], "to_date": f["date"]}, ktt)
    denied(lambda: get("Stock Closing Entry", closing["name"], dung), ("PermissionError",))
    denied(lambda: lst("Stock Closing Entry", {}, ["name"], dung), ("PermissionError",))
    assert get("Stock Closing Entry", closing["name"], ktt)["docstatus"] == 0
    emit("HTTP_014_STOCK_CLOSING_NO_COST", "PASS", {"denied_even_with_stock_user": True, "chief_read": True})

    from b014_ban_nhanh_scope import chay as scope_cases
    scope_cases(rpc, get, insert, submit, lst, denied, ktbh, ktt, f, emit, phien)
