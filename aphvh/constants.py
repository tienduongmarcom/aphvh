"""Hằng số dùng chung của app aphvh.

Đổi tên loại phiếu hoặc mã quy tắc ở đây là đổi dữ liệu nghiệp vụ: phiếu đã gửi lưu
mã quy tắc của chính nó (xem stock_entry_kg.py), nên KHÔNG đổi giá trị của quy tắc cũ.
Quy tắc mới thì thêm hằng số mới.
"""

# Loại phiếu kho (Stock Entry Type) dùng cách chia giá theo kg. Mục đích (purpose) = Repack.
KG_ENTRY_TYPE = "Đóng gói theo kg"

# Mã quy tắc tính giá lưu trên từng phiếu. Phiếu nào mang mã nào thì khi tính lại giá
# (repost) vẫn dùng đúng quy tắc đó, dù sau này có thêm quy tắc mới.
RULE_KG_V1 = "kg-v1"
SUPPORTED_RULES = (RULE_KG_V1,)

# Tên đơn vị đo "Kg" trên site.
KG_UOM = "Kg"
