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

# --- Bán hàng kho Hà Nội (0.3) ------------------------------------------------------------

# Vai trò: nhân viên bán hàng lập đơn; thủ kho Hà Nội lập phiếu giao hàng. Cả hai thấy giá bán,
# không thấy giá vốn (xem price_visibility.is_cost_restricted). Kế toán dùng vai trò chuẩn.
ROLE_SALES = "Nhân viên bán hàng APH"
ROLE_HN_STOCK = "Thủ kho Hà Nội APH"
COST_HIDDEN_ROLES = (ROLE_SALES, ROLE_HN_STOCK, ROLE_FACTORY)

# Cài đặt bán hàng (Selling Settings): bật/tắt từng phần của luồng bán hàng APH.
SS_AUTO_INVOICE = "aphvh_tu_tao_hoa_don"
SS_WARN_CREDIT = "aphvh_canh_bao_cong_no"
SS_WARN_PRICE = "aphvh_canh_bao_gia"

# Hạn mức cảnh báo: ô trên bảng hạn mức tín dụng (Customer Credit Limit) của khách và nhóm khách,
# theo từng công ty. Chỉ cảnh báo, không chặn (hạn mức chuẩn của ERPNext chặn nên bị ẩn).
CCL_WARN_LIMIT = "aphvh_han_muc_canh_bao"

# Đơn bán hàng: đánh dấu đơn bị cảnh báo để kế toán lọc.
SO_OVER_LIMIT = "aphvh_vuot_han_muc"
SO_BELOW_PRICE = "aphvh_duoi_gia"
SO_WARNING = "aphvh_canh_bao"

# Hóa đơn bán hàng do app tự tạo từ phiếu giao hàng (để lọc, và để dọn nháp khi hủy phiếu giao).
SI_AUTO = "aphvh_tu_tao"

# Phiếu giao hàng: thông tin giao nhận in lên phiếu xuất kho và biên bản giao nhận.
DN_MODE = "aphvh_hinh_thuc_giao"
DN_MODE_PICKUP = "Khách tự lấy"
DN_MODE_HIRED = "Thuê xe, nhà xe"
DN_RECEIVER = "aphvh_nguoi_nhan"
DN_CARRIER = "aphvh_nha_xe"
DN_DRIVER = "aphvh_lai_xe"
DN_PLATE = "aphvh_bien_so_xe"
DN_DRIVER_PHONE = "aphvh_sdt_lai_xe"

PRINT_DN_ISSUE = "Phiếu xuất kho bán hàng APH"
PRINT_DN_HANDOVER = "Biên bản giao nhận APH"
