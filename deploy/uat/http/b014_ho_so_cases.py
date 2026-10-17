"""Hồ sơ bản ký trên phiếu nguồn; chỉ chạy trên fixture UAT và restore của b014."""
import json
import uuid


def chay(rpc, get, insert, lst, denied, ktt, dn, emit):
    name = dn["name"]
    def save(doc):
        return rpc("frappe.client.save", {"doc": json.dumps(doc)}, ktt)
    def counts():
        return {dt: len(lst(dt, {}, ["name"], ktt)) for dt in ("GL Entry", "Stock Ledger Entry", "Sales Invoice")}
    before = counts()
    rpc("kh_aph.delivery_status.confirm", {"name": name, "action": "receive"}, ktt)
    doc = get("Delivery Note", name, ktt)
    assert not doc.get("kh_aph_ban_ky"), "Giao nhận không bắt buộc đính kèm"
    denied(lambda: rpc("kh_aph.ho_so_giao_nhan.doi_chieu", {"name": name, "modified": doc["modified"]}, ktt))
    for url in ("https://example.invalid/ky.pdf", "/files/cong-khai.pdf", "/private/files/khong-ton-tai.pdf"):
        bad = {**doc, "kh_aph_ban_ky": url}
        denied(lambda: save(bad))
    file = insert({"doctype": "File", "file_name": "uat-ban-ky-" + uuid.uuid4().hex + ".txt", "is_private": 1,
                   "attached_to_doctype": "Delivery Note", "attached_to_name": name,
                   "content": "Bản ký giả lập kiểm thử. Không phải hồ sơ khách hàng."}, ktt)
    doc = get("Delivery Note", name, ktt)
    doc["kh_aph_ban_ky"] = file["file_url"]
    doc = save(doc)
    assert not doc.get("kh_aph_doi_chieu_boi")
    denied(lambda: rpc("kh_aph.ho_so_giao_nhan.doi_chieu", {"name": name, "modified": "2000-01-01 00:00:00"}, ktt), ("TimestampMismatchError",))
    result = rpc("kh_aph.ho_so_giao_nhan.doi_chieu", {"name": name, "modified": doc["modified"]}, ktt)
    assert result["doi_chieu_boi"] == doc["modified_by"] and result["doi_chieu_luc"], result
    denied(lambda: rpc("frappe.client.delete", {"doctype": "File", "name": file["name"]}, ktt))
    public = {**get("File", file["name"], ktt), "is_private": 0}
    denied(lambda: rpc("frappe.client.save", {"doc": json.dumps(public)}, ktt))
    doc = get("Delivery Note", name, ktt)
    forged = {**doc, "kh_aph_doi_chieu_boi": "Administrator"}
    denied(lambda: save(forged))
    doc["kh_aph_ghi_chu_ban_ky"] = "Bản ký giả lập: cần kiểm lại 1 bao"
    doc = save(doc)
    assert not doc.get("kh_aph_doi_chieu_boi") and not doc.get("kh_aph_doi_chieu_luc"), doc["name"]
    assert counts() == before, "Hồ sơ bản ký đã làm thay đổi sổ"
    emit("HTTP_014_HO_SO_BAN_KY", "PASS", {"private_file": True, "stale_denied": True,
         "reset_on_change": True, "ledger_unchanged": True})
