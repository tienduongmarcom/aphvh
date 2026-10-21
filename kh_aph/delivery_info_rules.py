"""Thông tin của một đợt giao; kiểm thuần, không ghi kho hoặc công nợ."""
METHODS = ("Vận chuyển", "Khách đến lấy", "Xe khách đến lấy")
PICKUP_METHODS = ("Khách đến lấy", "Xe khách đến lấy")
EXTRA_LABELS = {"carrier": "Nhà xe", "carrier_phone": "Điện thoại nhà xe", "authorization": "Khách chỉ định người nhận",
                "customer_signature": "Yêu cầu khách ký giao nhận"}
LABELS = {"delivery_method": "Cách giao", "recipient": "Người nhận tại kho", "phone": "Điện thoại liên hệ",
          "driver_name": "Tên lái xe", "vehicle_no": "Biển số xe", "shipping_address_name": "Địa chỉ giao"}
LIMITS = {key: (60 if key == "phone" else 140) for key in LABELS}


def normalize(values):
    if values is None or values == "":
        return {}
    if not isinstance(values, dict) or set(values) - (set(LABELS) | set(EXTRA_LABELS)):
        raise ValueError("Thông tin giao nhận chỉ được chứa các trường của cửa sổ lập phiếu")
    if not values:
        return {}
    result = {}
    for key, label in LABELS.items():
        value = values.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(label + " phải là chuỗi văn bản")
        value = (value or "").strip()
        if len(value) > LIMITS[key] or any(ord(c) < 32 for c in value):
            raise ValueError(label + " quá dài hoặc chứa ký tự điều khiển")
        result[key] = value
    # Không thêm khóa mới vào payload cũ: giữ hash và retry của các đợt trước nâng cấp.
    if any(k in values for k in EXTRA_LABELS):
        for key, label in EXTRA_LABELS.items():
            value = values.get(key) or ""
            if not isinstance(value, str) or len(value.strip()) > (60 if key == "carrier_phone" else 140) or any(ord(c) < 32 for c in value):
                raise ValueError(label + " không hợp lệ")
            result[key] = value.strip()
        # Frappe lọc HTML khi lưu Data. Chặn trước để không âm thầm đổi tên
        # hoặc làm nội dung snapshot khác hash gửi lại của cùng một yêu cầu.
        for key, label in (LABELS | EXTRA_LABELS).items():
            if '<' in result[key] or '>' in result[key]:
                raise ValueError(label + " chỉ nhập chữ thông thường; bỏ các dấu ngoặc nhọn")
        if result["customer_signature"] not in ("", "Có", "Không"):
            raise ValueError("Chọn Có hoặc Không cho yêu cầu khách ký giao nhận")
        if result["delivery_method"] == "Vận chuyển" and (not result["carrier"] or not result["carrier_phone"]):
            raise ValueError("Ghi tên và số điện thoại nhà xe; có thể chọn cũ hoặc nhập mới")
    if result["delivery_method"] == "Xe khách đến lấy" and not result.get("authorization"):
        raise ValueError("Ghi căn cứ khách chỉ định/xác nhận người nhận hàng")
    if result["delivery_method"] not in METHODS:
        raise ValueError("Chọn cách giao hàng hợp lệ")
    if not result["recipient"]:
        raise ValueError("Ghi người thực nhận hàng tại kho; không bắt buộc là người dùng phần mềm")
    return result


def print_snapshot(doc):
    """Chỉ đọc snapshot phiếu; phiếu cũ/phiếu trả giữ ô cũ, không tra danh mục hiện tại."""
    current = bool(doc.get("kh_aph_cach_giao")) and not doc.get("is_return")
    return {
        "current": current,
        "carrier": doc.get("kh_aph_nha_xe_dot") if current else doc.get("kh_aph_nha_xe"),
        "carrier_phone": doc.get("kh_aph_sdt_nha_xe_dot") if current else "",
        "authorization": doc.get("kh_aph_chi_dinh_nhan") if current else "",
        "customer_signature": doc.get("kh_aph_can_ky_khach") if current else "",
        "version": doc.get("kh_aph_mau_giao_nhan") or 0,
        "method": doc.get("kh_aph_cach_giao") if current else doc.get("kh_aph_hinh_thuc_giao"),
        "recipient": doc.get("kh_aph_nguoi_nhan_tai_kho") if current else doc.get("kh_aph_nguoi_nhan"),
        "phone": doc.get("kh_aph_dien_thoai_nhan") if current else "",
        "driver": doc.get("driver_name") if current else doc.get("kh_aph_lai_xe"),
        "vehicle": doc.get("vehicle_no") if current else doc.get("kh_aph_bien_so_xe"),
        "dispatcher": doc.get("kh_aph_nguoi_thuc_giao") if current else "",
        "time": doc.get("kh_aph_ban_giao_luc") if current else "",
    }
