"""GN09 trên dữ liệu b014 dùng một lần; không dùng Administrator cho thao tác nghiệp vụ."""
import json
import os
from pathlib import Path
import subprocess


def chay(rpc, get, insert, submit, lst, denied, ktt, ktbh, f, dn, emit, phien):
    name = dn["name"]
    state = "kh_aph_chenh_lech_state"
    def current(): return get("Delivery Note", name, ktt)
    def action(kind, values, caller=ktt, stamp=None):
        return rpc("kh_aph.delivery_issue.cap_nhat", {"name": name, "modified": stamp or current()["modified"],
                   "action": kind, "values": json.dumps(values)}, caller)
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("GL Entry", "Stock Ledger Entry", "Sales Invoice")}
    before = counts()
    old = current()
    perm = insert({"doctype": "User Permission", "user": f["scope_co"], "allow": "Customer", "for_value": f["kh1"],
                   "apply_to_all_doctypes": 1}, ktt)
    # Cùng vai trò trưởng nhưng không đúng scope vẫn bị từ chối trước khi nhận nội dung.
    scoped = phien(f["scope_co"])
    denied(lambda: action("report", {"noi_dung": "Ngoài phạm vi"}, scoped), ("PermissionError",))
    report = action("report", {"noi_dung": "Bản ký ghi thiếu 1 kg; xác minh hàng có chở về kho hay không"}, ktbh)
    assert report[state] == "Cần xử lý" and report["kh_aph_chenh_lech_bao_boi"] == f["ktbh"]
    assert not any(key in report for key in ("items", "grand_total", "valuation_rate", "amount"))
    denied(lambda: action("assign", {"nguoi_phu_trach": f["ktt2"], "han_xu_ly": f["date"]}, ktbh), ("PermissionError",))
    denied(lambda: action("report", {"noi_dung": "x", "docstatus": 1}, ktbh))
    forged = {**current(), state: "Đã xử lý", "kh_aph_chenh_lech_chot_boi": f["ktbh"]}
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(forged)}, ktbh))
    denied(lambda: action("assign", {"nguoi_phu_trach": f["ktt2"], "han_xu_ly": f["date"]}, stamp=old["modified"]),
           ("TimestampMismatchError",))
    denied(lambda: action("assign", {"nguoi_phu_trach": f["scope_co"], "han_xu_ly": f["date"]}))
    ktt("/api/method/frappe.client.delete", {"doctype": "User Permission", "name": perm["name"]})
    assert counts() == before
    emit("HTTP_014_CHENH_LECH_QUYEN", "PASS", {"chief_only": True, "assignee_scope": True,
         "stale_denied": True, "overposting_denied": True, "minimal_response": True})

    doc = current()
    rpc("kh_aph.ho_so_giao_nhan.doi_chieu", {"name": name, "modified": doc["modified"]}, ktt)
    assert current()[state] == "Cần xử lý", "Đối chiếu bản ký đã tự đóng chênh lệch"
    action("assign", {"nguoi_phu_trach": f["ktt2"], "han_xu_ly": f["date"]})
    if os.environ.get("GITHUB_ACTIONS") == "true":
        result = subprocess.run(["node", "--experimental-websocket", str(Path(__file__).with_name("ban-nhanh-desk.mjs")), name, "chenh-lech"],
                                check=True, text=True, capture_output=True, timeout=150)
        evidence = json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{"case":')))
        assert evidence["status"] == "PASS", evidence
        emit(evidence["case"], "PASS", evidence["detail"])
    result = action("resolve", {"ket_qua": "Kiểm lại phiếu cân và bản ký: đủ hàng, ghi nhầm trên giấy", "cach_xu_ly": "Đối chiếu, không điều chỉnh sổ"})
    assert result[state] == "Đã xử lý" and result["kh_aph_chenh_lech_chot_boi"] == f["ktt"]
    assert result["kh_aph_chenh_lech_chot_luc"] and counts() == before
    # Cùng nội dung đã lưu không thêm lịch sử hoặc chuyển trạng thái mới khi bấm lặp.
    comments = lst("Comment", {"reference_doctype": "Delivery Note", "reference_name": name}, ["name"], ktt)
    denied(lambda: action("resolve", {"ket_qua": "Lặp", "cach_xu_ly": "Đối chiếu, không điều chỉnh sổ"}))
    assert len(lst("Comment", {"reference_doctype": "Delivery Note", "reference_name": name}, ["name"], ktt)) == len(comments)
    emit("HTTP_014_CHENH_LECH_KHONG_GHI_SO", "PASS", {"review_not_resolution": True, "ledger_unchanged": True, "repeat_no_history": True})

    doc = current(); doc["kh_aph_ghi_chu_ban_ky"] = "Có bằng chứng mới: 1 kg thực chở về kho"
    rpc("frappe.client.save", {"doc": json.dumps(doc)}, ktbh)
    reopened = current()
    assert reopened[state] == "Đang xử lý" and not reopened.get("kh_aph_chenh_lech_ket_qua")
    assert not reopened.get("kh_aph_chenh_lech_chot_boi") and not reopened.get("kh_aph_doi_chieu_boi")
    denied(lambda: action("resolve", {"ket_qua": "Đã xem", "cach_xu_ly": "Đối chiếu, không điều chỉnh sổ"}))
    rpc("kh_aph.ho_so_giao_nhan.doi_chieu", {"name": name, "modified": reopened["modified"]}, ktt)
    audit = lst("Comment", {"reference_doctype": "Delivery Note", "reference_name": name}, ["content"], ktt)
    assert any("ghi nhầm trên giấy" in r["content"] for r in audit), "Mất kết quả cũ khi mở lại"
    assert counts() == before
    emit("HTTP_014_CHENH_LECH_MO_LAI", "PASS", {"changed_evidence_reopens": True, "review_reset": True, "old_result_retained_in_audit": True})

    ret = rpc("erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return", {"source_name": name}, ktt)
    for row in ret["items"]: row["qty"] = -1
    ret["kh_aph_loai_dieu_chinh"] = "Giao thiếu - hàng chở về kho (R022/R024)"
    ret = insert(ret, ktt)
    proof = {"ket_qua": "1 kg thực nhập lại kho theo phiếu trả", "cach_xu_ly": "Phiếu trả hàng", "phieu_tra": ret["name"]}
    denied(lambda: action("resolve", proof))
    denied(lambda: action("resolve", {**proof, "phieu_tra": name}))
    ret = submit(ret, ktt)
    ledger_after_return = counts()
    result = action("resolve", proof)
    assert result[state] == "Đã xử lý" and counts() == ledger_after_return, "Chốt hồ sơ đã ghi sổ lần nữa"
    denied(lambda: rpc("frappe.client.cancel", {"doctype": "Delivery Note", "name": ret["name"]}, ktt))
    denied(lambda: action("reopen", {"ly_do": "Thử vượt quyền"}, ktbh), ("PermissionError",))
    action("reopen", {"ly_do": "Kiểm liên kết hóa đơn giảm do phiếu trả đã tạo"})
    assert not current().get("kh_aph_chenh_lech_phieu_tra")
    credits = lst("Sales Invoice", [["Sales Invoice Item", "delivery_note", "=", ret["name"]], ["docstatus", "=", 1]], ["name"], ktt)
    assert len(credits) == 1
    credit = credits[0]["name"]
    result = action("resolve", {"ket_qua": "Đã kiểm kho nhập lại và hóa đơn giảm tương ứng", "cach_xu_ly": "Hóa đơn giảm", "hoa_don_giam": credit})
    assert result[state] == "Đã xử lý" and counts() == ledger_after_return
    denied(lambda: rpc("frappe.client.cancel", {"doctype": "Sales Invoice", "name": credit}, ktt))
    emit("HTTP_014_CHENH_LECH_CHUNG_TU", "PASS", {"submitted_return_source": True, "credit_source": True,
         "draft_and_wrong_proof_denied": True, "cancel_proof_denied": True, "resolution_does_not_post": True})
