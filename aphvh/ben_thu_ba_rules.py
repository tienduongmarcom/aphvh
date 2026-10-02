"""Thanh toán qua bên thứ ba (0.4.11) — quy tắc thuần, kiểm thử không cần Frappe.

Khách hàng (hoặc nhà cung cấp) không tự trả mà người/đơn vị khác chuyển tiền thay (J17, J32):
- Kế toán đánh dấu "Bên thứ ba trả / nhận thay", ghi tên, CCCD/MST, căn cứ, đính kèm văn bản.
- Chưa có giấy tờ vẫn ghi nhận được (tiền đã về), nhưng chứng từ mang trạng thái "Cần rà soát" để kế toán trưởng
  theo dõi (rủi ro tranh chấp, rửa tiền). Có văn bản đính kèm thì "Đủ hồ sơ".
- Hóa đơn có xuất GTGT mà bên trả là tổ chức khác (MST 10 số khác MST khách): nhắc rủi ro bên mua không được
  khấu trừ thuế đầu vào nếu không có thỏa thuận ba bên.
"""

import re

CAN_CU_UY_QUYEN = "Có văn bản ủy quyền / thỏa thuận ba bên"
CAN_CU_NGUOI_NHA = "Người nhà / nhân viên của khách (khách xác nhận bằng văn bản)"
CAN_CU_CHUA_CO = "Chưa có giấy tờ – cần rà soát"
CAN_CU = (CAN_CU_UY_QUYEN, CAN_CU_NGUOI_NHA, CAN_CU_CHUA_CO)

TT_CAN_RA_SOAT = "Cần rà soát"
TT_DU_HO_SO = "Đủ hồ sơ"
TT_DA_DUYET = "Kế toán trưởng đã duyệt"
TRANG_THAI = (TT_CAN_RA_SOAT, TT_DU_HO_SO, TT_DA_DUYET)


def _mst(x) -> str:
    return re.sub(r"\D", "", str(x or "").split("-")[0])


def kiem_tra(ben_thu_ba, ten, can_cu, co_file, trang_thai_cu=None) -> dict:
    """-> {"loi": [..] (chặn lưu), "trang_thai": str | None}."""
    if not ben_thu_ba:
        return {"loi": [], "trang_thai": None}
    loi = []
    if not (ten or "").strip():
        loi.append("Ghi tên người / đơn vị trả (nhận) thay.")
    if not can_cu:
        loi.append("Chọn căn cứ thanh toán qua bên thứ ba.")
    elif can_cu != CAN_CU_CHUA_CO and not co_file:
        loi.append("Đính kèm văn bản ủy quyền / xác nhận của khách, hoặc chọn căn cứ 'Chưa có giấy tờ – cần rà soát'.")
    if can_cu == CAN_CU_CHUA_CO or not co_file:
        tt = TT_CAN_RA_SOAT if trang_thai_cu != TT_DA_DUYET else TT_DA_DUYET
    else:
        tt = trang_thai_cu if trang_thai_cu == TT_DA_DUYET else TT_DU_HO_SO
    return {"loi": loi, "trang_thai": tt}


def canh_bao_thue(ben_thu_ba, mst_ben_tra, mst_khach, co_hoa_don_gtgt) -> str | None:
    """Tổ chức khác (MST 10 số) trả tiền cho hóa đơn GTGT của khách -> nhắc rủi ro khấu trừ thuế."""
    if not ben_thu_ba or not co_hoa_don_gtgt:
        return None
    a, b = _mst(mst_ben_tra), _mst(mst_khach)
    if len(a) == 10 and a != b:
        return ("Hóa đơn GTGT của khách được tổ chức khác thanh toán: bên mua có thể không được khấu trừ thuế GTGT đầu vào "
                "nếu không có thỏa thuận ba bên (bên mua – bên bán – bên trả). Đề nghị khách gửi văn bản này.")
    return None


def nguoi_tren_phieu(ben_thu_ba, ten_ben_tra, ten_doi_tuong, kieu) -> str | None:
    """Dòng 'Họ và tên người nộp / nhận tiền' trên phiếu: 'Trần Văn X (nộp thay cho Công ty A)'."""
    if not ben_thu_ba or not (ten_ben_tra or "").strip():
        return None
    dong = "nộp thay cho" if kieu == "thu" else "nhận thay cho"
    return f"{ten_ben_tra.strip()} ({dong} {ten_doi_tuong})" if ten_doi_tuong else ten_ben_tra.strip()
