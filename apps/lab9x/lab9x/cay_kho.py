"""Cây kho chuẩn 9xLab (thuần, không import frappe) — từ lab9x 0.2.3 / kh_aph 0.11.2.

Nguyên tắc (docs/dac-ta-0.11.2.md mục 2): kho cho biết hàng nằm ở đâu và thuộc pháp nhân nào; tài khoản kho lấy theo nhóm hàng
(tồn kho theo mặt hàng). Mỗi tình trạng đặc biệt chỉ một kho cho mỗi địa điểm. Tên kho do app sinh; bộ dựng chỉ thêm kho thiếu.

Cấu hình (khach.json, mục "cay_kho"):
    {"dia_diem": [
        {"ten": "Nhà máy Phú Thọ", "loai": "nha_may", "cong_ty": ["APH"], "gui": ["VH", "MK"]},
        {"ten": "Hà Nội", "loai": "ban_hang", "cong_ty": ["APH", "VH"], "kho_ve_tinh": ["Bác Hiền", ...]}]}
"""

# Loại kho (giá trị ô kh_aph_loai_kho)
BAN_HANG, NGUYEN_LIEU, THANH_PHAM = "Bán hàng", "Nguyên liệu", "Thành phẩm"
DO_DANG, CHO_DONG_GOI, CHO_XU_LY, CACH_LY = "Dở dang dây chuyền", "Chờ đóng gói", "Chờ xử lý", "Cách ly"
GUI, VAN_CHUYEN = "Gửi", "Vận chuyển"
LOAI_KHO = (BAN_HANG, NGUYEN_LIEU, THANH_PHAM, DO_DANG, CHO_DONG_GOI, CHO_XU_LY, CACH_LY, GUI, VAN_CHUYEN)
# Không tính vào lượng có thể bán; đơn bán / phiếu giao không xuất từ các kho này.
KHONG_BAN = (DO_DANG, CHO_DONG_GOI, CHO_XU_LY, CACH_LY, GUI)
DAY_CHUYEN = ("Đậu", "Phồng tôm")

KHO_NHA_MAY = (
    ("Kho nguyên liệu", NGUYEN_LIEU, None),
    ("Kho vật tư - bao bì - phụ tùng", NGUYEN_LIEU, None),
    ("Dở dang dây chuyền đậu", DO_DANG, "Đậu"),
    ("Dở dang dây chuyền phồng tôm", DO_DANG, "Phồng tôm"),
    ("Kho chờ đóng gói", CHO_DONG_GOI, None),
    ("Kho thành phẩm nhà máy", THANH_PHAM, None),
)
TEN_VAN_CHUYEN = "Hàng đang vận chuyển"
TEN_CHO_XU_LY = "Hàng chờ xử lý"
TEN_CACH_LY = "Hàng cách ly"


def ten_kho(ten, abbr):
    """Tên ERPNext sinh cho kho: '<tên> - <viết tắt>'."""
    return f"{ten} - {abbr}"


def ten_kho_tinh_trang(goc, dia_diem=None):
    """Kho tình trạng đặc biệt tạo khi cần (Chờ xử lý, Cách ly): một kho cho mỗi địa điểm, tên kèm địa điểm để không trùng
    trong cùng pháp nhân (warehouse_name là duy nhất theo công ty)."""
    dia_diem = (dia_diem or "").strip()
    return f"{goc} {dia_diem}" if dia_diem else goc


def kiem_cau_hinh(cay, cac_abbr):
    """Trả danh sách lỗi của mục cay_kho (rỗng = hợp lệ)."""
    loi = []
    if not cay:
        return loi
    ds = cay.get("dia_diem")
    if not isinstance(ds, list) or not ds:
        return ["cay_kho.dia_diem phải là danh sách địa điểm"]
    ten_da_co = set()
    nha_may_cua = {}
    for i, dd in enumerate(ds, 1):
        if dd.get("loai") == "nha_may":
            for ab in dd.get("cong_ty") or []:
                if ab in nha_may_cua:
                    loi.append(f"địa điểm #{i}: {ab} đã có nhà máy {nha_may_cua[ab]} (mỗi pháp nhân một nhà máy; "
                               "tên kho nhà máy không kèm địa điểm)")
                nha_may_cua[ab] = (dd.get("ten") or "").strip()
        ten = (dd.get("ten") or "").strip()
        if not ten:
            loi.append(f"địa điểm #{i}: thiếu 'ten'")
        elif ten in ten_da_co:
            loi.append(f"địa điểm #{i}: trùng tên {ten}")
        ten_da_co.add(ten)
        if dd.get("loai") not in ("nha_may", "ban_hang"):
            loi.append(f"địa điểm #{i}: 'loai' phải là nha_may hoặc ban_hang")
        for k in ("cong_ty", "gui"):
            for ab in dd.get(k) or []:
                if ab not in cac_abbr:
                    loi.append(f"địa điểm #{i}: '{k}' có {ab} không phải công ty trong cấu hình")
        if not dd.get("cong_ty"):
            loi.append(f"địa điểm #{i}: cần ít nhất một công ty")
        if dd.get("loai") != "nha_may" and dd.get("gui"):
            loi.append(f"địa điểm #{i}: chỉ nhà máy mới có kho gửi")
        if set(dd.get("gui") or []) & set(dd.get("cong_ty") or []):
            loi.append(f"địa điểm #{i}: một công ty không vừa sở hữu vừa gửi hàng ở cùng địa điểm")
        vt = [v.strip() for v in dd.get("kho_ve_tinh") or []]
        if len(vt) != len(set(vt)) or any(not v for v in vt):
            loi.append(f"địa điểm #{i}: kho vệ tinh trùng hoặc trống")
    return loi


def ke_hoach(cay, cac_abbr):
    """Danh sách kho cần có, cha trước con.

    Mỗi phần tử: {"abbr", "ten" (warehouse_name), "cha" (tên ERPNext của nhóm cha hoặc None = gốc công ty),
    "nhom" (0/1), "loai_kho", "day_chuyen", "transit" (0/1)}.
    """
    out = []

    def them(abbr, ten, cha, nhom=0, loai=None, day=None, transit=0):
        out.append({"abbr": abbr, "ten": ten, "cha": cha, "nhom": nhom, "loai_kho": loai,
                    "day_chuyen": day, "transit": transit})

    co_dia_diem = {ab: False for ab in cac_abbr}
    for dd in (cay or {}).get("dia_diem") or []:
        ten_dd = dd["ten"].strip()
        for ab in dd.get("cong_ty") or []:
            co_dia_diem[ab] = True
            them(ab, ten_dd, None, nhom=1)
            nhom = ten_kho(ten_dd, ab)
            if dd["loai"] == "nha_may":
                for ten, loai, day in KHO_NHA_MAY:
                    them(ab, ten, nhom, loai=loai, day=day)
            else:
                them(ab, f"Kho bán hàng {ten_dd}", nhom, loai=BAN_HANG)
                for vt in dd.get("kho_ve_tinh") or []:
                    them(ab, f"Kho vệ tinh {vt.strip()}", nhom, loai=BAN_HANG)
        for ab in dd.get("gui") or []:
            co_dia_diem[ab] = True
            them(ab, ten_dd, None, nhom=1)
            them(ab, f"Gửi tại {ten_dd}", ten_kho(ten_dd, ab), loai=GUI)
    for ab in cac_abbr:
        if co_dia_diem.get(ab):
            them(ab, TEN_VAN_CHUYEN, None, loai=VAN_CHUYEN, transit=1)
    # bỏ trùng (một công ty vừa có địa điểm vừa gửi ở địa điểm khác cùng tên nhóm: kiem_cau_hinh đã chặn trường hợp xấu)
    seen, kq = set(), []
    for k in out:
        key = (k["abbr"], k["ten"])
        if key not in seen:
            seen.add(key)
            kq.append(k)
    return kq


def so_sanh(ke, hien_co):
    """ke: kết quả ke_hoach; hien_co: {tên ERPNext: {"company_abbr", "loai_kho", "is_group"}}.

    Trả (cần tạo, cảnh báo). Không bao giờ đề xuất xóa hay đổi tên.
    """
    tao, canh_bao = [], []
    muon = {ten_kho(k["ten"], k["abbr"]): k for k in ke}
    for ten, k in muon.items():
        h = hien_co.get(ten)
        if not h:
            tao.append(k)
            continue
        if h.get("company_abbr") != k["abbr"]:
            canh_bao.append(f"{ten}: thuộc công ty khác ({h.get('company_abbr')}), không tự sửa")
        if int(h.get("is_group") or 0) != k["nhom"]:
            canh_bao.append(f"{ten}: loại nhóm/lá khác cây chuẩn, không tự sửa")
        elif not k["nhom"] and k["loai_kho"] and h.get("loai_kho") not in (None, "", k["loai_kho"]):
            canh_bao.append(f"{ten}: loại kho đang là {h.get('loai_kho')}, cây chuẩn là {k['loai_kho']}")
    for ten, h in hien_co.items():
        if ten not in muon and not int(h.get("is_group") or 0) and h.get("loai_kho") not in (CHO_XU_LY, CACH_LY):
            canh_bao.append(f"{ten}: kho ngoài cây chuẩn (giữ nguyên, kế toán xem có cần tắt)")
    return tao, canh_bao
