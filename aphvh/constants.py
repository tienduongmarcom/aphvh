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

# --- Phân quyền nhà máy (0.2) -------------------------------------------------------------

# Vai trò của kế toán nhà máy: nhận hàng, cấp liệu, sản xuất, chuyển kho; không xem giá
# nguyên phụ liệu, giá trị tồn kho và giá thành.
ROLE_FACTORY = "Kế toán nhà máy APH"

# Người có một trong các vai trò này luôn xem được giá, kể cả khi có thêm ROLE_FACTORY.
PRICE_ROLES = (
    "Administrator",
    "System Manager",
    "Stock Manager",
    "Accounts User",
    "Accounts Manager",
    "Purchase User",
    "Purchase Manager",
    "Auditor",
)

# Ô trên Nhóm hàng: nhóm nào được tích thì kế toán nhà máy tự nhập giá (vật tư vận hành).
IG_FACTORY_CAN_PRICE = "aphvh_factory_can_price"
# Nhóm được tích sẵn lần đầu tạo ô (sau đó kế toán trưởng tự tích/bỏ trên Nhóm hàng).
DEFAULT_FACTORY_PRICE_GROUPS = ("Vật tư tiêu hao",)

# Ô trên Phiếu nhập mua hàng: phiếu nhập vật tư vận hành (được xem, nhập giá).
PR_OPEX = "aphvh_vat_tu_van_hanh"

# Mẫu in (tên hiển thị) và báo cáo tồn kho số lượng.
PRINT_PURCHASE_RECEIPT = "Phiếu nhập kho APH"
PRINT_STOCK_ENTRY = "Phiếu kho APH"
REPORT_QTY = "Ton kho so luong APH"
REPORT_QTY_LABEL = "Tồn kho số lượng APH"
