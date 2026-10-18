"""Quy tắc thuần cho hồ sơ chênh lệch trên phiếu giao, không tính hoặc ghi sổ."""
from datetime import date

PENDING = "Cần xử lý"
ACTIVE = "Đang xử lý"
CLOSED = "Đã xử lý"
NO_LEDGER = "Đối chiếu, không điều chỉnh sổ"
RETURN = "Phiếu trả hàng"
CREDIT = "Hóa đơn giảm"
CANCELLED = "Phiếu nguồn đã hủy"  # Chỉ do thao tác hủy native ghi; không nhận từ Dialog chốt.
KEYS = {"report": {"noi_dung"}, "assign": {"nguoi_phu_trach", "han_xu_ly"},
        "resolve": {"ket_qua", "cach_xu_ly", "phieu_tra", "hoa_don_giam"}, "reopen": {"ly_do"}}


def normalize(action, values):
    if not isinstance(action, str) or action not in KEYS or not isinstance(values, dict) or set(values) - KEYS[action]:
        raise ValueError("Thao tác hoặc trường thông tin xử lý chênh lệch không hợp lệ")
    result = {}
    for key in KEYS[action]:
        value = values.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str) or any(ord(c) < 32 and c not in "\n\t\r" for c in value):
            raise ValueError("Thông tin xử lý chênh lệch phải là văn bản hợp lệ")
        value = value.strip()
        if len(value) > (2000 if key in {"noi_dung", "ket_qua", "ly_do"} else 140):
            raise ValueError("Thông tin xử lý chênh lệch quá dài")
        result[key] = value
    required = {"report": ("noi_dung",), "assign": ("nguoi_phu_trach", "han_xu_ly"),
                "resolve": ("ket_qua", "cach_xu_ly"), "reopen": ("ly_do",)}[action]
    if any(not result[k] for k in required):
        raise ValueError("Điền đủ thông tin bắt buộc của thao tác xử lý chênh lệch")
    if action == "assign":
        try:
            if date.fromisoformat(result["han_xu_ly"]).isoformat() != result["han_xu_ly"]:
                raise ValueError()
        except ValueError:
            raise ValueError("Hạn xử lý phải có dạng ngày YYYY-MM-DD") from None
    if action == "resolve":
        mode = result["cach_xu_ly"]
        if mode not in (NO_LEDGER, RETURN, CREDIT):
            raise ValueError("Chọn cách xử lý chênh lệch hợp lệ")
        if bool(result["phieu_tra"]) != (mode == RETURN) or bool(result["hoa_don_giam"]) != (mode == CREDIT):
            raise ValueError("Chứng từ liên quan phải khớp cách xử lý đã chọn")
    return result


def transition(state, action):
    if action == "report" and state in (None, "", PENDING, ACTIVE):
        return state or PENDING
    if action == "assign" and state in (PENDING, ACTIVE):
        return ACTIVE
    if action == "resolve" and state == ACTIVE:
        return CLOSED
    if action == "reopen" and state == CLOSED:
        return ACTIVE
    raise ValueError("Hồ sơ chênh lệch không còn ở trạng thái phù hợp; tải lại phiếu")
