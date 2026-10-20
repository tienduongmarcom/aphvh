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
    address = insert({"doctype": "Address", "address_title": f["p"] + "-giao",
        "address_type": "Shipping", "address_line1": "Kho nhận số 12", "city": "Hà Nội", "country": "Vietnam",
        "links": [{"link_doctype": "Customer", "link_name": f["kh2"]}]}, ktt)
    other = insert({"doctype": "Address", "address_title": f["p"] + "-khac",
        "address_type": "Shipping", "address_line1": "Địa chỉ khách khác", "city": "Hà Nội", "country": "Vietnam",
        "links": [{"link_doctype": "Customer", "link_name": f["kh1"]}]}, ktt)
    info = {"delivery_method": "Vận chuyển", "recipient": "Anh Nhận UAT", "phone": "0901234567",
            "driver_name": "Lái xe UAT", "vehicle_no": "29A-UAT", "shipping_address_name": address["name"]}
    payload = {**args, "selections": json.dumps(selected), "request_id": token, "delivery": json.dumps(info)}
    made = rpc("kh_aph.ban_nhanh.create_drafts", payload, ktbh)
    assert len(made["delivery_notes"]) == 1 and made["delivery_notes"][0]["docstatus"] == 0, made
    note = get("Delivery Note", made["delivery_notes"][0]["name"], ktbh)
    assert note["items"][0]["qty"] == 5 and note["items"][0]["warehouse"] == f["kho"], note["name"]
    assert note["kh_aph_nguoi_nhan_tai_kho"] == info["recipient"] and note["vehicle_no"] == info["vehicle_no"]
    assert note["shipping_address_name"] == address["name"] and "Kho nhận số 12" in note["shipping_address"]
    assert ledger_counts() == before, "Lập phiếu nháp đã phát sinh sổ/hoá đơn"
    count_dn = len(lst("Delivery Note", {}, ["name"], ktt))
    for change in ({"recipient": "Người khác"}, {"phone": "0902"}, {"delivery_method": "Khách đến lấy"}, {"vehicle_no": "xe khác"}):
        denied(lambda change=change: rpc("kh_aph.ban_nhanh.create_drafts", {**payload, "delivery": json.dumps({**info, **change})}, ktbh))
    for change in ({"shipping_address_name": other["name"]}, {"phone": 123}, {"docstatus": 1}):
        denied(lambda change=change: rpc("kh_aph.ban_nhanh.create_drafts", {**payload,
            "request_id": uuid.uuid4().hex, "delivery": json.dumps({**info, **change})}, ktbh))
    # Quyền Address vẫn kiểm ở server, kể cả tên địa chỉ đã có trên client.
    permitted = insert({"doctype": "User Permission", "user": f["ktbh"], "allow": "Address", "for_value": other["name"]}, ktt)
    denied(lambda: rpc("kh_aph.ban_nhanh.create_drafts", {**payload, "request_id": uuid.uuid4().hex}, ktbh), ("PermissionError",))
    denied(lambda: rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": note["name"]}, ktbh), ("PermissionError",))
    ktt("/api/method/frappe.client.delete", {"doctype": "User Permission", "name": permitted["name"]})
    # Người bán không giả tên người thực giao; kho điền, chọn đúng cách giao rồi mới xuất.
    limited = phien(f["ktbh_no_submit"])
    fake = get("Delivery Note", note["name"], limited)
    denied(lambda: rpc("frappe.client.submit", {"doc": json.dumps(fake)}, limited), ("PermissionError",))
    fake["kh_aph_nguoi_thuc_giao"] = "Giả người giao"
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(fake)}, limited), ("PermissionError",))
    denied(lambda: rpc("kh_aph.delivery_status.confirm", {"name": note["name"], "action": "handoff"}, ktt))
    actual = get("Delivery Note", note["name"], ktt)
    actual["kh_aph_nguoi_thuc_giao"] = "Anh kho vệ tinh"
    rpc("frappe.client.save", {"doc": json.dumps(actual)}, ktt)
    denied(lambda: rpc("kh_aph.delivery_status.confirm", {"name": note["name"], "action": "pickup"}, ktt))
    assert len(lst("Delivery Note", {}, ["name"], ktt)) == count_dn and ledger_counts() == before
    emit("HTTP_014_GIAO_NHAN_METADATA", "PASS", {"customer_address": True, "address_permission": True,
         "request_content": True, "dispatcher_permission": True, "matching_action": True, "ledger_unchanged": True})
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
    Path("quick-delivery-slip.html").write_text(html, encoding="utf-8")
    for text in ("CHỜ XUẤT", note["name"], root["name"], "Người thực giao hàng", "Người thực nhận hàng",
                 "Liên: Lưu kho", "Liên: Giao nhận", info["recipient"], info["vehicle_no"], "Kho nhận số 12", "Anh kho vệ tinh"):
        assert text in html, text
    for text in ("valuation_rate", "basic_rate", "Đơn giá vốn", "Giá bán/kg"):
        assert text not in html, text
    for text in ("size: A5 landscape", "Đơn giá", "Thành tiền", "viết bằng chữ", "Kế toán trưởng", "Giám đốc"):
        assert text in html, text
    # Giá bán thuần từ DN, không đọc giá vốn hoặc tự tính lại từ bảng giá hiện hành.
    def vn_amount(value):
        return f"{value:,.2f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")
    for row in note["items"]:
        assert vn_amount(row["net_rate"]) in html
        assert vn_amount(row["net_amount"]) in html
    assert vn_amount(sum(row["net_amount"] for row in note["items"])) in html
    denied(lambda: rpc("kh_aph.ban_nhanh.print_batch", {**args, "request_id": token}, dung), ("PermissionError",))
    assert ledger_counts() == before, "In đã phát sinh sổ"
    emit("HTTP_014_BAN_NHANH_PRINT", "PASS", {"paper": "A5 landscape", "sales_price": True,
         "cost_hidden": True, "draft_label": True, "ledger_unchanged": True})

    # Mở lại đúng DN, không cần token lập đợt hoặc tạo phiếu mới.
    def frozen(doc):
        keys = ("modified", "docstatus", "items", "company", "customer", "posting_date", "shipping_address",
                "shipping_address_name", "driver_name", "vehicle_no", "kh_aph_lan_in_lai", "kh_aph_delivery_state",
                "kh_aph_cach_giao", "kh_aph_nguoi_nhan_tai_kho", "kh_aph_dien_thoai_nhan",
                "kh_aph_nguoi_thuc_giao", "kh_aph_ban_giao_luc", "kh_aph_ban_giao_boi")
        return {key: doc.get(key) for key in keys}
    saved = frozen(get("Delivery Note", note["name"], ktbh))
    counts = len(lst("Delivery Note", {}, ["name"], ktt)), ledger_counts()
    for _ in range(2):
        assert rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": note["name"]}, ktbh)["html"] == html
    denied(lambda: rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": note["name"]}, dung), ("PermissionError",))
    assert frozen(get("Delivery Note", note["name"], ktbh)) == saved
    assert (len(lst("Delivery Note", {}, ["name"], ktt)), ledger_counts()) == counts
    manual = insert({"doctype": "Delivery Note", "company": note["company"], "customer": note["customer"],
        "posting_date": f["date"], "currency": "VND", "kh_aph_nguoi_nhan": "Người nhận phiếu cũ UAT",
        "items": [{"item_code": f["A"], "warehouse": f["kho"], "qty": 1, "rate": 35000}]}, ktt)
    plain = rpc("kh_aph.ban_nhanh.print_note", {"delivery_note": manual["name"]}, ktt)["html"]
    assert "Người nhận phiếu cũ UAT" in plain and "Đơn bán chung:" not in plain
    assert "CHỜ XUẤT" in plain and manual["name"] in plain
    emit("HTTP_014_A5_EXISTING_NOTE", "PASS", {"repeat_same_html": True, "no_new_note": True,
        "document_and_ledger_unchanged": True, "no_cost_denied": True, "manual_note_legacy_snapshot": True})

    if os.environ.get("GITHUB_ACTIONS") == "true":
        result = subprocess.run(["node", "--experimental-websocket", str(Path(__file__).with_name("ban-nhanh-desk.mjs")),
            note["name"], "in-lai-a5"], check=True, text=True, capture_output=True, timeout=150)
        evidence = json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{"case":')))
        assert evidence["status"] == "PASS", evidence
        emit(evidence["case"], "PASS", evidence["detail"])
        assert frozen(get("Delivery Note", note["name"], ktbh)) == saved and ledger_counts() == before

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
    for method, values in (
        ("phan_bo_thang", {"company": f["aph"], "thang": f["date"][:7]}),
        ("vet_bon", {"kho": f["kho"], "xuong": "", "loai_hao_hut": "Hao hụt tự nhiên", "ly_do": "UAT"}),
        ("quyet_toan_do_dang", {"kho": f["kho"], "xuong": "", "ly_do": "UAT"}),
    ):
        denied(lambda method=method, values=values: rpc("kh_aph.factory_costing." + method, values, dung), ("PermissionError",))
    assert ledger_counts() == before
    emit("HTTP_014_STOCK_CLOSING_NO_COST", "PASS", {"denied_even_with_stock_user": True, "chief_read": True})

    from b014_ban_nhanh_scope import chay as scope_cases
    scope_cases(rpc, get, insert, submit, lst, denied, ktbh, ktt, f, emit, phien)

    return {"shared_order": root["name"], "delivery_note": note["name"]}
