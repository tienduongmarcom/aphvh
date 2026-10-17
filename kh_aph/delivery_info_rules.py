"""Thông tin của một đợt giao; kiểm thuần, không ghi kho hoặc công nợ."""
METHODS = ("Vận chuyển", "Khách đến lấy")
LABELS = {"delivery_method": "Cách giao", "recipient": "Người nhận tại kho", "phone": "Điện thoại liên hệ",
          "driver_name": "Tên lái xe", "vehicle_no": "Biển số xe", "shipping_address_name": "Địa chỉ giao"}
LIMITS = {key: (60 if key == "phone" else 140) for key in LABELS}


def normalize(values):
    if values is None or values == "":
        return {}
    if not isinstance(values, dict) or set(values) - set(LABELS):
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
    if result["delivery_method"] not in METHODS:
        raise ValueError("Chọn Vận chuyển hoặc Khách đến lấy")
    if not result["recipient"]:
        raise ValueError("Ghi người thực nhận hàng tại kho; không bắt buộc là người dùng phần mềm")
    return result
