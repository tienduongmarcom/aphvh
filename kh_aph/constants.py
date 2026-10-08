"""Hằng số dùng chung của app kh_aph.

Đổi tên loại phiếu hoặc mã quy tắc ở đây là đổi dữ liệu nghiệp vụ: phiếu đã gửi lưu
mã quy tắc của chính nó (xem stock_entry_kg.py), nên KHÔNG đổi giá trị của quy tắc cũ.
Quy tắc mới thì thêm hằng số mới.
"""

# Loại phiếu kho (Stock Entry Type) dùng cách chia giá theo kg. Mục đích (purpose) = Repack.
KG_ENTRY_TYPE = "Đóng gói theo kg"

# Mã quy tắc tính giá lưu trên từng phiếu. Phiếu nào mang mã nào thì khi tính lại giá
# (repost) vẫn dùng đúng quy tắc đó, dù sau này có thêm quy tắc mới.
RULE_KG_V1 = "kg-v1"
# kg-v2 (0.3.3): như kg-v1, thêm dòng GIÁ CỐ ĐỊNH (phế, dở dang cuối kỳ): giá nhập tay trên dòng,
# trừ khỏi tổng đầu vào trước; phần còn lại chia theo kg cho các thành phẩm khác.
RULE_KG_V2 = "kg-v2"
SUPPORTED_RULES = (RULE_KG_V1, RULE_KG_V2)

# Nhóm hàng được tích ô này: dòng đầu ra thuộc nhóm (hoặc nhóm con) trên phiếu "Đóng gói theo kg"
# là dòng giá cố định (kế toán nhập giá). Ô trên dòng phiếu lưu lại kết quả lúc lưu/gửi phiếu.
IG_FIXED_RATE = "kh_aph_gia_co_dinh_kg"
SED_FIXED_RATE = "kh_aph_gia_co_dinh"

# Tên đơn vị đo "Kg" trên site.
KG_UOM = "Kg"

# --- Phân quyền nhà máy (0.2) -------------------------------------------------------------

# Vai trò của kế toán nhà máy: nhận hàng, cấp liệu, sản xuất, chuyển kho; không xem giá
# nguyên phụ liệu, giá trị tồn kho và giá thành.
ROLE_FACTORY = "Kế toán nhà máy"

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
IG_FACTORY_CAN_PRICE = "kh_aph_factory_can_price"
# Nhóm được tích sẵn lần đầu tạo ô (sau đó kế toán trưởng tự tích/bỏ trên Nhóm hàng).
DEFAULT_FACTORY_PRICE_GROUPS = ("Vật tư tiêu hao",)

# Ô trên Phiếu nhập mua hàng: phiếu nhập vật tư vận hành (được xem, nhập giá).
PR_OPEX = "kh_aph_vat_tu_van_hanh"

# Mẫu in (tên hiển thị) và báo cáo tồn kho số lượng.
PRINT_PURCHASE_RECEIPT = "Phiếu nhập kho"
PRINT_STOCK_ENTRY = "Phiếu kho"
REPORT_QTY = "Ton kho so luong"
REPORT_QTY_LABEL = "Tồn kho số lượng"

# --- Bán hàng kho Hà Nội (0.3) ------------------------------------------------------------

# Vai trò: nhân viên bán hàng lập đơn; thủ kho Hà Nội lập phiếu giao hàng. Cả hai thấy giá bán,
# không thấy giá vốn (xem price_visibility.is_cost_restricted). Kế toán dùng vai trò chuẩn.
ROLE_SALES = "Nhân viên bán hàng"
ROLE_HN_STOCK = "Thủ kho bán hàng"
COST_HIDDEN_ROLES = (ROLE_SALES, ROLE_HN_STOCK, ROLE_FACTORY)

# Cài đặt bán hàng (Selling Settings): bật/tắt từng phần của luồng bán hàng APH.
SS_AUTO_INVOICE = "kh_aph_tu_tao_hoa_don"
SS_WARN_CREDIT = "kh_aph_canh_bao_cong_no"
SS_WARN_PRICE = "kh_aph_canh_bao_gia"

# Hạn mức cảnh báo: ô trên bảng hạn mức tín dụng (Customer Credit Limit) của khách và nhóm khách,
# theo từng công ty. Chỉ cảnh báo, không chặn (hạn mức chuẩn của ERPNext chặn nên bị ẩn).
CCL_WARN_LIMIT = "kh_aph_han_muc_canh_bao"

# Đơn bán hàng: đánh dấu đơn bị cảnh báo để kế toán lọc.
SO_OVER_LIMIT = "kh_aph_vuot_han_muc"
SO_BELOW_PRICE = "kh_aph_duoi_gia"
SO_WARNING = "kh_aph_canh_bao"

# Hóa đơn bán hàng do app tự tạo từ phiếu giao hàng (để lọc, và để dọn nháp khi hủy phiếu giao).
SI_AUTO = "kh_aph_tu_tao"

# Phiếu giao hàng: thông tin giao nhận in lên phiếu xuất kho và biên bản giao nhận.
DN_MODE = "kh_aph_hinh_thuc_giao"
DN_MODE_PICKUP = "Khách tự lấy"
DN_MODE_HIRED = "Thuê xe, nhà xe"
DN_RECEIVER = "kh_aph_nguoi_nhan"
DN_CARRIER = "kh_aph_nha_xe"
DN_DRIVER = "kh_aph_lai_xe"
DN_PLATE = "kh_aph_bien_so_xe"
DN_DRIVER_PHONE = "kh_aph_sdt_lai_xe"

PRINT_DN_ISSUE = "Phiếu xuất kho bán hàng"
PRINT_DN_HANDOVER = "Biên bản giao nhận"
PRINT_PAYMENT = "Phiếu thu chi"
PRINT_SALES_INVOICE = "Phiếu bán hàng"
PE_PERSON = "kh_aph_nguoi_nop_nhan"
# 0.4.11: thanh toán qua bên thứ ba
PE_BTB = "kh_aph_ben_thu_ba"
PE_BTB_TEN = "kh_aph_btb_ten"
PE_BTB_GIAY = "kh_aph_btb_cccd_mst"
PE_BTB_CAN_CU = "kh_aph_btb_can_cu"
PE_BTB_FILE = "kh_aph_btb_van_ban"
PE_BTB_TT = "kh_aph_btb_trang_thai"

# --- Có / không xuất hóa đơn GTGT (0.3.1) ---------------------------------------------------
# ERPNext ghi mọi lần bán thật; MISA chỉ ghi lần bán có hóa đơn. Ô này trên khách (mặc định do
# kế toán đặt), đơn bán hàng, phiếu giao hàng, hóa đơn bán hàng. "Không" = không tính thuế GTGT.
INV_FLAG = "kh_aph_xuat_hoa_don"
INV_YES = "Có"
INV_NO = "Không"
INV_DOCTYPES = ("Sales Order", "Delivery Note", "Sales Invoice")

# Hóa đơn điện tử đã xuất trên MISA: kế toán ghi lên hóa đơn bán hàng ERPNext (sửa được sau khi
# xác nhận) để đối chiếu với bảng kê đầu ra MISA.
SI_EINV_SERIES = "kh_aph_hd_ky_hieu"
SI_EINV_NO = "kh_aph_hd_so"
SI_EINV_DATE = "kh_aph_hd_ngay"
EINV_FIELDS = (SI_EINV_SERIES, SI_EINV_NO, SI_EINV_DATE)

REPORT_INVOICED = "Ban hang co hoa don"
REPORT_INVOICED_LABEL = "Bán hàng có hóa đơn"
