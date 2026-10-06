"""Bảng tài khoản chuẩn theo thông tư cho bản cài trắng (0.4.24).
APH: TT133/2016 (không có 621, 622, 623, 627, 641; bán hàng và quản lý là 6421, 6422).
VH: TT99/2025 (71 tài khoản cấp 1).
Mỗi tài khoản có nguồn: "TT" = có trong thông tư, "DN" = chi tiết doanh nghiệp mở thêm cho nghiệp vụ của app (được phép, ghi rõ).
Danh mục cấp 1 đã đối chiếu (docs/doi-chieu-tai-khoan-thong-tu.md). Cấp 2 theo nguồn đã đọc; phần chưa có danh mục đầy đủ để ở mức DN.
Không có 911: ERPNext kết chuyển lãi lỗ bằng Period Closing Voucher.
"""

# (số, tên, loại gốc, loại tài khoản ERPNext)
_A, _L, _E, _I, _X = "Asset", "Liability", "Equity", "Income", "Expense"

# ---------- cấp 1 chung cho TT133 và TT99 (cùng số, cùng tên gần như nhau) ----------
CHUNG = [
    ("111", "Tiền mặt", _A, ""), ("112", "Tiền gửi ngân hàng", _A, ""), ("121", "Chứng khoán kinh doanh", _A, ""),
    ("128", "Đầu tư nắm giữ đến ngày đáo hạn", _A, ""), ("131", "Phải thu của khách hàng", _A, "Receivable"),
    ("133", "Thuế GTGT được khấu trừ", _A, ""), ("136", "Phải thu nội bộ", _A, ""), ("138", "Phải thu khác", _A, ""),
    ("141", "Tạm ứng", _A, ""), ("151", "Hàng mua đang đi đường", _A, ""), ("152", "Nguyên liệu, vật liệu", _A, "Stock"),
    ("153", "Công cụ, dụng cụ", _A, "Stock"), ("154", "Chi phí sản xuất, kinh doanh dở dang", _A, "Stock"),
    ("155", "Thành phẩm", _A, "Stock"), ("156", "Hàng hóa", _A, "Stock"), ("157", "Hàng gửi đi bán", _A, ""),
    ("211", "Tài sản cố định", _A, "Fixed Asset"), ("214", "Hao mòn tài sản cố định", _A, "Accumulated Depreciation"),
    ("217", "Bất động sản đầu tư", _A, ""), ("228", "Đầu tư khác", _A, ""), ("229", "Dự phòng tổn thất tài sản", _A, ""),
    ("241", "Xây dựng cơ bản dở dang", _A, "Capital Work in Progress"), ("242", "Chi phí trả trước", _A, ""),
    ("331", "Phải trả cho người bán", _L, "Payable"), ("333", "Thuế và các khoản phải nộp Nhà nước", _L, ""),
    ("334", "Phải trả người lao động", _L, ""), ("335", "Chi phí phải trả", _L, ""), ("336", "Phải trả nội bộ", _L, ""),
    ("338", "Phải trả, phải nộp khác", _L, ""), ("341", "Vay và nợ thuê tài chính", _L, ""), ("352", "Dự phòng phải trả", _L, ""),
    ("353", "Quỹ khen thưởng, phúc lợi", _L, ""), ("356", "Quỹ phát triển khoa học và công nghệ", _L, ""),
    ("411", "Vốn đầu tư của chủ sở hữu", _E, "Equity"), ("413", "Chênh lệch tỷ giá hối đoái", _E, ""),
    ("418", "Các quỹ thuộc vốn chủ sở hữu", _E, "Equity"), ("419", "Cổ phiếu quỹ", _E, "Equity"),
    ("421", "Lợi nhuận sau thuế chưa phân phối", _E, "Equity"),
    ("511", "Doanh thu bán hàng và cung cấp dịch vụ", _I, ""), ("515", "Doanh thu hoạt động tài chính", _I, ""),
    ("632", "Giá vốn hàng bán", _X, "Cost of Goods Sold"), ("635", "Chi phí tài chính", _X, ""),
    ("711", "Thu nhập khác", _I, ""), ("811", "Chi phí khác", _X, ""), ("821", "Chi phí thuế thu nhập doanh nghiệp", _X, "Tax"),
]
# riêng TT133
RIENG_133 = [("611", "Mua hàng", _X, ""), ("631", "Giá thành sản xuất", _X, ""), ("642", "Chi phí quản lý kinh doanh", _X, "")]
# riêng TT99 (cấp 1 đã đối chiếu)
RIENG_99 = [
    ("113", "Tiền đang chuyển", _A, ""), ("158", "Nguyên liệu, vật tư tại kho bảo thuế", _A, "Stock"),
    ("171", "Giao dịch mua, bán lại trái phiếu chính phủ", _A, ""), ("212", "Tài sản cố định thuê tài chính", _A, "Fixed Asset"),
    ("213", "Tài sản cố định vô hình", _A, "Fixed Asset"), ("215", "Tài sản sinh học", _A, ""),
    ("221", "Đầu tư vào công ty con", _A, ""), ("222", "Đầu tư vào công ty liên doanh, liên kết", _A, ""),
    ("243", "Tài sản thuế thu nhập hoãn lại", _A, ""), ("244", "Ký quỹ, ký cược", _A, ""),
    ("332", "Phải trả cổ tức, lợi nhuận", _L, ""), ("337", "Thanh toán theo tiến độ hợp đồng xây dựng", _L, ""),
    ("343", "Trái phiếu phát hành", _L, ""), ("344", "Nhận ký quỹ, ký cược", _L, ""), ("347", "Thuế thu nhập hoãn lại phải trả", _L, ""),
    ("357", "Quỹ bình ổn giá", _L, ""), ("412", "Chênh lệch đánh giá lại tài sản", _E, ""), ("414", "Quỹ đầu tư phát triển", _E, "Equity"),
    ("521", "Các khoản giảm trừ doanh thu", _I, ""), ("621", "Chi phí nguyên liệu, vật liệu trực tiếp", _X, ""),
    ("622", "Chi phí nhân công trực tiếp", _X, ""), ("623", "Chi phí sử dụng máy thi công", _X, ""),
    ("627", "Chi phí sản xuất chung", _X, ""), ("641", "Chi phí bán hàng", _X, ""), ("642", "Chi phí quản lý doanh nghiệp", _X, ""),
]
# tên 112 khác nhau
TEN_KHAC = {"tt99": {"112": "Tiền gửi không kỳ hạn", "211": "Tài sản cố định hữu hình", "138": "Phải thu khác",
                     "228": "Đầu tư khác", "242": "Chi phí chờ phân bổ", "632": "Giá vốn hàng bán"}}

# ---------- cấp 2: (cha, số, tên, nguồn, loại tài khoản) ----------
CAP2_133 = [
    ("111", "1111", "Tiền Việt Nam", "TT", "Cash"), ("111", "1112", "Ngoại tệ", "TT", "Cash"),
    ("112", "1121", "Tiền Việt Nam", "TT", "Bank"), ("112", "1122", "Ngoại tệ", "TT", "Bank"),
    ("133", "1331", "Thuế GTGT được khấu trừ của hàng hóa, dịch vụ", "TT", "Tax"), ("133", "1332", "Thuế GTGT được khấu trừ của TSCĐ", "TT", "Tax"),
    ("136", "1361", "Vốn kinh doanh ở các đơn vị trực thuộc", "TT", ""), ("136", "1368", "Phải thu nội bộ khác", "TT", ""),
    ("138", "1381", "Tài sản thiếu chờ xử lý", "TT", ""), ("138", "1386", "Cầm cố, thế chấp, ký quỹ, ký cược", "TT", ""),
    ("138", "1388", "Phải thu khác", "TT", ""),
    ("211", "2111", "TSCĐ hữu hình", "TT", "Fixed Asset"), ("211", "2112", "TSCĐ thuê tài chính", "TT", "Fixed Asset"), ("211", "2113", "TSCĐ vô hình", "TT", "Fixed Asset"),
    ("214", "2141", "Hao mòn TSCĐ hữu hình", "TT", "Accumulated Depreciation"), ("214", "2142", "Hao mòn TSCĐ thuê tài chính", "TT", "Accumulated Depreciation"),
    ("214", "2143", "Hao mòn TSCĐ vô hình", "TT", "Accumulated Depreciation"), ("214", "2147", "Hao mòn bất động sản đầu tư", "TT", "Accumulated Depreciation"),
    ("333", "3331", "Thuế giá trị gia tăng phải nộp", "TT", "Tax"), ("333", "3332", "Thuế tiêu thụ đặc biệt", "TT", "Tax"),
    ("333", "3333", "Thuế xuất, nhập khẩu", "TT", "Tax"), ("333", "3334", "Thuế thu nhập doanh nghiệp", "TT", "Tax"),
    ("333", "3335", "Thuế thu nhập cá nhân", "TT", "Tax"), ("333", "3336", "Thuế tài nguyên", "TT", "Tax"),
    ("333", "3337", "Thuế nhà đất, tiền thuê đất", "TT", "Tax"), ("333", "3338", "Thuế bảo vệ môi trường và các loại thuế khác", "TT", "Tax"),
    ("333", "3339", "Phí, lệ phí và các khoản phải nộp khác", "TT", "Tax"),
    ("338", "3381", "Tài sản thừa chờ giải quyết", "TT", ""), ("338", "3382", "Kinh phí công đoàn", "TT", ""),
    ("338", "3383", "Bảo hiểm xã hội", "TT", ""), ("338", "3384", "Bảo hiểm y tế", "TT", ""), ("338", "3385", "Bảo hiểm thất nghiệp", "TT", ""),
    ("338", "3386", "Nhận ký quỹ, ký cược", "TT", ""), ("338", "3387", "Doanh thu chưa thực hiện", "TT", ""), ("338", "3388", "Phải trả, phải nộp khác", "TT", ""),
    ("341", "3411", "Các khoản đi vay", "TT", ""), ("341", "3412", "Nợ thuê tài chính", "TT", ""),
    ("411", "4111", "Vốn góp của chủ sở hữu", "TT", "Equity"), ("411", "4112", "Thặng dư vốn cổ phần", "TT", "Equity"), ("411", "4118", "Vốn khác", "TT", "Equity"),
    ("421", "4211", "Lợi nhuận sau thuế chưa phân phối năm trước", "TT", "Equity"), ("421", "4212", "Lợi nhuận sau thuế chưa phân phối năm nay", "TT", "Equity"),
    ("511", "5111", "Doanh thu bán hàng hóa", "TT", ""), ("511", "5112", "Doanh thu bán các thành phẩm", "TT", ""),
    ("511", "5113", "Doanh thu cung cấp dịch vụ", "TT", ""), ("511", "5118", "Doanh thu khác", "TT", ""),
    ("642", "6421", "Chi phí bán hàng", "TT", ""), ("642", "6422", "Chi phí quản lý doanh nghiệp", "TT", ""),
]
CAP2_99 = [
    ("111", "1111", "Tiền Việt Nam", "DN", "Cash"), ("111", "1112", "Ngoại tệ", "DN", "Cash"),
    ("112", "1121", "Tiền Việt Nam", "DN", "Bank"), ("112", "1122", "Ngoại tệ", "DN", "Bank"),
    ("133", "1331", "Thuế GTGT được khấu trừ của hàng hóa, dịch vụ", "TT", "Tax"), ("133", "1332", "Thuế GTGT được khấu trừ của TSCĐ", "TT", "Tax"),
    ("138", "1381", "Tài sản thiếu chờ xử lý", "TT", ""), ("138", "1383", "Thuế tiêu thụ đặc biệt của hàng nhập khẩu", "TT", ""), ("138", "1388", "Phải thu khác", "TT", ""),
    ("333", "3331", "Thuế giá trị gia tăng phải nộp", "TT", "Tax"), ("333", "3338", "Thuế bảo vệ môi trường và các loại thuế khác", "TT", "Tax"),
    ("338", "3381", "Tài sản thừa chờ giải quyết", "TT", ""), ("338", "3382", "Kinh phí công đoàn", "TT", ""), ("338", "3383", "Bảo hiểm xã hội", "TT", ""),
    ("338", "3384", "Bảo hiểm y tế", "TT", ""), ("338", "3385", "Bảo hiểm thất nghiệp", "TT", ""), ("338", "3386", "Nhận ký quỹ, ký cược", "TT", ""),
    ("338", "3387", "Doanh thu chưa thực hiện", "TT", ""), ("338", "3388", "Phải trả, phải nộp khác", "TT", ""),
    ("156", "1561", "Giá mua hàng hóa", "DN", "Stock"),
    ("511", "5111", "Doanh thu bán hàng hóa", "DN", ""), ("511", "5112", "Doanh thu bán thành phẩm", "DN", ""), ("511", "5113", "Doanh thu cung cấp dịch vụ", "DN", ""),
    ("627", "6271", "Chi phí nhân viên phân xưởng", "TT", ""), ("627", "6272", "Chi phí vật liệu", "TT", ""), ("627", "6273", "Chi phí dụng cụ sản xuất", "TT", ""),
    ("627", "6274", "Chi phí khấu hao TSCĐ", "TT", ""), ("627", "6277", "Chi phí dịch vụ mua ngoài", "TT", ""), ("627", "6278", "Chi phí bằng tiền khác", "TT", ""),
    ("641", "6411", "Chi phí nhân viên", "TT", ""), ("641", "6412", "Chi phí vật liệu, bao bì", "TT", ""), ("641", "6413", "Chi phí dụng cụ, đồ dùng", "TT", ""),
    ("641", "6414", "Chi phí khấu hao TSCĐ", "TT", ""), ("641", "6417", "Chi phí dịch vụ mua ngoài", "TT", ""), ("641", "6418", "Chi phí bằng tiền khác", "TT", ""),
    ("642", "6421", "Chi phí nhân viên quản lý", "TT", ""), ("642", "6422", "Chi phí vật liệu quản lý", "TT", ""), ("642", "6423", "Chi phí đồ dùng văn phòng", "TT", ""),
    ("642", "6424", "Chi phí khấu hao TSCĐ", "TT", ""), ("642", "6425", "Thuế, phí và lệ phí", "TT", ""), ("642", "6426", "Chi phí dự phòng", "TT", ""),
    ("642", "6427", "Chi phí dịch vụ mua ngoài", "TT", ""), ("642", "6428", "Chi phí bằng tiền khác", "TT", ""),
]
# ---------- chi tiết doanh nghiệp mở thêm cho nghiệp vụ của app (cả hai đơn vị) ----------
CAP_DN_CHUNG = [
    ("152", "1521", "Nguyên liệu, vật liệu chính", "DN", "Stock"), ("152", "1522", "Nguyên liệu, vật liệu phụ, phụ gia", "DN", "Stock"),
    ("152", "1523", "Bao bì sản xuất", "DN", "Stock"), ("152", "1524", "Nhiên liệu, vật tư phục vụ sản xuất", "DN", "Stock"),
    ("155", "1551", "Thành phẩm sơ chế", "DN", "Stock"), ("155", "1552", "Thành phẩm phồng tôm", "DN", "Stock"), ("155", "1558", "Phụ phẩm, phế liệu thu hồi", "DN", "Stock"),
    ("154", "15411", "Sản phẩm dở dang sơ chế", "DN", "Stock"), ("154", "15421", "Sản phẩm dở dang phồng tôm", "DN", "Stock"),
    ("331", "3311", "Phải trả người bán bằng VND", "DN", "Payable"), ("331", "3318", "Hàng đã nhận chưa có hóa đơn", "DN", ""),
    ("335", "3351", "Chi phí nhập khẩu tạm tính", "DN", ""),
    ("338", "33880", "Tiền thu hộ đơn vị khác", "DN", ""),
    ("632", "6321", "Giá vốn hàng bán", "DN", "Cost of Goods Sold"), ("632", "6322", "Tổn thất hàng tồn kho ghi nhận vào giá vốn", "DN", "Stock Adjustment"),
    ("635", "6359", "Chênh lệch tỷ giá trung gian", "DN", ""),
]


def bang(loai: str) -> list:
    """Danh sách (số, tên, cha, là_nhóm, loại gốc, loại TK, nguồn) cho 'aph' (TT133) hoặc 'vh' (TT99). Chuẩn, không rác."""
    t99 = loai == "vh"
    c1 = CHUNG + (RIENG_99 if t99 else RIENG_133)
    cap2 = list(CAP2_99 if t99 else CAP2_133) + [x for x in CAP_DN_CHUNG if not (not t99 and False)]
    ten_khac = TEN_KHAC["tt99"] if t99 else {}
    ten_cha = {}
    out, so_co = [], set()
    cha_co_con = {x[0] for x in cap2}
    for so, ten, root, at in sorted(c1, key=lambda x: x[0]):
        ten = ten_khac.get(so, ten)
        if t99 and so == "642":
            ten = "Chi phí quản lý doanh nghiệp"
        ten_cha[so] = (ten, root)
    for so, (ten, root) in sorted(ten_cha.items()):
        at = next((x[3] for x in c1 if x[0] == so), "")
        out.append({"so": so, "ten": ten, "cha": None, "nhom": 1 if so in cha_co_con else 0, "root": root,
                    "loai_tk": "" if so in cha_co_con else at, "nguon": "TT"})
        so_co.add(so)
    for cha, so, ten, nguon, at in cap2:
        if cha not in ten_cha:  # ví dụ APH không có 627, 641: bỏ chi tiết của tài khoản không tồn tại
            continue
        if so in so_co:
            continue
        # 5111.. không thuộc bảng cha nào khác; 15411/15421 cần cha 1541/1542 -> gắn thẳng vào 154
        out.append({"so": so, "ten": ten, "cha": cha, "nhom": 0, "root": ten_cha[cha][1], "loai_tk": at, "nguon": nguon})
        so_co.add(so)
    return out


def loi_cau_truc(ds: list, loai: str) -> list:
    """Kiểm thuần: số hiệu không trùng, cha có mặt và là nhóm, APH không có tài khoản của TT99."""
    loi, so = [], {d["so"] for d in ds}
    if len(so) != len(ds):
        loi.append("trùng số hiệu")
    for d in ds:
        if d["cha"] and d["cha"] not in so:
            loi.append(f"{d['so']}: thiếu cha {d['cha']}")
    if loai == "aph":
        for k in ("621", "622", "623", "627", "641"):
            if k in so:
                loi.append(f"APH (TT133) không được có {k}")
    return loi
