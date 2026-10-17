"""Ca đối kháng facade: nhiều nguồn, rollback, quyền native và sửa nháp thực."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktbh, ktt, f, emit, phien):
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt))
                for dt in ("Delivery Note", "Sales Invoice", "GL Entry", "Stock Ledger Entry")}

    def make(rows):
        root = insert({"doctype": "APH Shared Sales Order", "customer": f["kh2"],
                       "transaction_date": f["date"], "delivery_date": f["date"],
                       "selling_price_list": f["pl"], "currency": "VND", "items": rows}, ktbh)
        return submit(root, ktbh)

    def line(item, wh):
        return {"item_code": item, "warehouse": wh, "qty": 20, "rate": 35000}

    def preview(root, caller=ktbh):
        return rpc("kh_aph.ban_nhanh.preview", {"shared_order": root["name"]}, caller)

    def payload(root, view):
        return {"shared_order": root["name"], "request_id": uuid.uuid4().hex,
                "selections": json.dumps([{"source_row": r["source_row"], "qty": 2} for r in view["rows"]])}

    root = make([line(f["A"], f["kho"]), line(f["A"], f["kho2"]), line(f["B"], f["kho_vh"])])
    view = preview(root)
    assert len(view["rows"]) == 3, view
    baseline = counts()
    batch = payload(root, view)
    made = rpc("kh_aph.ban_nhanh.create_drafts", batch, ktbh)
    notes = [get("Delivery Note", n["name"], ktt) for n in made["delivery_notes"]]
    assert len(notes) == 3, made
    expected = {(f["aph"], f["kho"]), (f["aph"], f["kho2"]), (f["vh"], f["kho_vh"])}
    assert {(n["company"], n["items"][0]["warehouse"]) for n in notes} == expected
    for note in notes:
        assert note["docstatus"] == 0 and len(note["items"]) == 1, note["name"]
        assert note["items"][0]["qty"] == 2 and note["items"][0]["against_sales_order"], note["name"]
    after = counts()
    assert after == {**baseline, "Delivery Note": baseline["Delivery Note"] + 3}, after
    html = rpc("kh_aph.ban_nhanh.print_batch", {k: batch[k] for k in ("shared_order", "request_id")}, ktbh)["html"]
    for note in notes:
        assert note["name"] in html and note["items"][0]["warehouse"] in html
    emit("HTTP_014_FAST_MULTI_OWNER_WAREHOUSE", "PASS",
         {"drafts": 3, "companies": 2, "warehouses": 3, "no_ledger": True})

    # Sửa nháp bằng endpoint chuẩn: lượng còn lại phải lấy lượng đã sửa trong DB.
    note = next(n for n in notes if n["items"][0]["warehouse"] == f["kho"])
    note["items"][0]["qty"] = 3
    rpc("frappe.client.save", {"doc": json.dumps(note)}, ktbh)
    revised = next(r for r in preview(root)["rows"] if r["warehouse"] == f["kho"])
    assert (revised["draft_qty"], revised["remaining_qty"]) == (3, 17), revised
    assert counts() == after
    emit("HTTP_014_FAST_MANUAL_DRAFT", "PASS", {"draft_kg": 3, "remaining_kg": 17})

    # Đối chứng dương cùng endpoint trước khi yêu cầu truy cập ngoài phạm vi.
    own = make([line(f["A"], f["kho"])])
    for label in ("scope_co", "scope_wh"):
        caller = phien(f[label])
        allowed = preview(own, caller)
        assert len(allowed["rows"]) == 1 and allowed["rows"][0]["warehouse"] == f["kho"]
        allowed_payload = payload(own, allowed)
        allowed_note = rpc("kh_aph.ban_nhanh.create_drafts", allowed_payload, caller)
        assert len(allowed_note["delivery_notes"]) == 1
        own_html = rpc("kh_aph.ban_nhanh.print_batch",
                       {k: allowed_payload[k] for k in ("shared_order", "request_id")}, caller)["html"]
        assert allowed_note["delivery_notes"][0]["name"] in own_html
        state = counts()
        for method, args in (
            ("preview", {"shared_order": root["name"]}),
            ("create_drafts", payload(root, view)),
            ("create_drafts", batch),  # Mã đã lập không được bỏ qua quyền hiện tại.
            ("print_batch", {k: batch[k] for k in ("shared_order", "request_id")})):
            denied(lambda m=method, a=args: rpc("kh_aph.ban_nhanh." + m, a, caller), ("PermissionError",))
        assert counts() == state
        emit("HTTP_014_FAST_" + label.upper(), "PASS", {"positive_control": True, "outside_scope_denied": True})

    # Nguồn VH được lập sau APH. Item bị ngừng sau xác nhận SO gây lỗi native ở nhóm sau.
    atomic_root = make([line(f["A"], f["kho"]), line(f["B"], f["kho_vh"])])
    atomic_view = preview(atomic_root)
    ordered = sorted(atomic_view["rows"], key=lambda r: (r["source_order"], r["warehouse"]))
    assert [r["company"] for r in ordered] == [f["aph"], f["vh"]], ordered
    rpc("frappe.client.set_value", {"doctype": "Item", "name": f["B"], "fieldname": "disabled", "value": 1}, ktt)
    try:
        state = counts()
        denied(lambda: rpc("kh_aph.ban_nhanh.create_drafts", payload(atomic_root, atomic_view), ktbh),
               ("ValidationError", "DisabledItemError"), text=f["B"])
        assert counts() == state, "Lỗi nhóm VH để lại phiếu APH hoặc phát sinh sổ"
    finally:
        rpc("frappe.client.set_value", {"doctype": "Item", "name": f["B"], "fieldname": "disabled", "value": 0}, ktt)
    emit("HTTP_014_FAST_LATER_GROUP_ROLLBACK", "PASS", {"drafts_unchanged": True, "no_ledger": True})
