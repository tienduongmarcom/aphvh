"""Quy tắc giá thành dùng chung (thuần, không import frappe) — từ lab9x 0.2.2 / kh_aph 0.11.1.

- Tài khoản chi phí sản xuất theo yếu tố cho công ty TT133 (TT133 không có 621/622/627; chi phí sản xuất tập hợp trên 154).
  Xưởng tách bằng trung tâm chi phí, không bằng tài khoản.
- Hệ số phẩm cấp (quy tắc kg-v4): trọng số chia giá = kg × hệ số.
- Kế hoạch phân bổ chi phí cuối tháng: số dư tài khoản yếu tố theo trung tâm chi phí → Landed Cost Voucher cho từng
  xưởng (chia theo trọng số các dòng thành phẩm) và bút toán kết chuyển phần "nhà máy chung" sang 632 chi tiết.
- Kiểm lệch kg khi đóng gói lại (Q103).
"""

from lab9x.costing_rules import split_by_weight

# (số hiệu, tên). Số cuối giống 627x để kế toán dễ đối chiếu (6272 → 15482, 6274 → 15484…).
TK_YEU_TO_154 = (
    ("15481", "Chi phí nhân công trực tiếp sản xuất"),
    ("15482", "Chi phí vật liệu, công cụ dụng cụ sản xuất"),
    ("15484", "Chi phí khấu hao TSCĐ sản xuất"),
    ("15487", "Chi phí dịch vụ mua ngoài sản xuất"),
    ("15488", "Chi phí sản xuất bằng tiền khác, hao hụt tự nhiên"),
)
TK_HAO_HUT_TU_NHIEN = "15488"
# TT133 TK 154 nguyên tắc 1(đ): CPSXC cố định không phân bổ tính vào giá vốn hàng bán trong kỳ.
TK_KHONG_PHAN_BO = ("632", "6323", "Chi phí sản xuất chung cố định không phân bổ")
TK_TON_THAT = "6322"  # đã có trong CAP_DN_CHUNG: tổn thất hàng tồn kho ghi nhận vào giá vốn

QUY_TAC_HE_SO = "kg-v4"
SAI_SO_KG = 0.001


def he_so_hop_le(he_so) -> float:
    """Hệ số phẩm cấp: trống/0 coi là 1; âm báo lỗi."""
    h = float(he_so or 0)
    if h < 0:
        raise ValueError("Hệ số phân bổ giá thành không được âm")
    return h or 1.0


def trong_so(kg, he_so) -> float:
    return float(kg or 0) * he_so_hop_le(he_so)


def lech_kg(kg_vao, kg_ra, sai_so=SAI_SO_KG) -> float:
    """Chênh kg đầu vào − đầu ra; trả 0 khi trong sai số."""
    d = round(float(kg_vao or 0) - float(kg_ra or 0), 6)
    return 0.0 if abs(d) <= sai_so else d


def ke_hoach_phan_bo(so_du, xuong, chung, dong_thanh_pham, precision=0):
    """Kế hoạch phân bổ chi phí sản xuất cuối tháng.

    so_du: {(tài khoản, trung tâm chi phí): số dư Nợ} — chỉ tài khoản yếu tố.
    xuong: danh sách trung tâm chi phí là xưởng (được phân bổ vào giá thành).
    chung: trung tâm chi phí "Nhà máy chung" (kết chuyển 632) hoặc None.
    dong_thanh_pham: {trung tâm chi phí xưởng: [(phiếu, dòng, kg, hệ số), ...]}.

    Trả {"lcv": {xưởng: {"thue": [(tk, tiền)], "dong": [(phiếu, dòng, tiền)]}},
         "chung": [(tk, tiền)], "bo_qua": [(trung tâm, tk|None, lý do)]}.
    Số dư ≤ 0 không phân bổ (báo trong bo_qua). Xưởng không có phiếu sản xuất: giữ số dư, báo bo_qua.
    """
    kq = {"lcv": {}, "chung": [], "bo_qua": []}
    xuong = list(xuong)
    for (tk, ttcp), tien in sorted(so_du.items()):
        tien = round(float(tien or 0), precision)
        if ttcp not in xuong and ttcp != chung:
            kq["bo_qua"].append((ttcp, tk, "trung tâm chi phí không phải xưởng hay nhà máy chung"))
            continue
        if tien <= 0:
            if tien < 0:
                kq["bo_qua"].append((ttcp, tk, "số dư Có (đã phân bổ thừa): kế toán xem lại"))
            continue
        if ttcp == chung:
            kq["chung"].append((tk, tien))
            continue
        kq["lcv"].setdefault(ttcp, {"thue": [], "dong": []})["thue"].append((tk, tien))
    for ttcp in list(kq["lcv"]):
        rows = [r for r in dong_thanh_pham.get(ttcp) or [] if trong_so(r[2], r[3]) > 0]
        if not rows:
            kq["bo_qua"].append((ttcp, None, "không có phiếu sản xuất trong kỳ: giữ số dư sang kỳ sau"))
            del kq["lcv"][ttcp]
            continue
        tong = sum(t for _tk, t in kq["lcv"][ttcp]["thue"])
        phan = split_by_weight(tong, [trong_so(r[2], r[3]) for r in rows], precision)
        kq["lcv"][ttcp]["dong"] = [(r[0], r[1], p) for r, p in zip(rows, phan, strict=True)]
    return kq


def ke_hoach_vet_bon(ton):
    """ton: [(mã, số lượng sổ, giá trị sổ)]. Trả (dòng cần xuất hết, dòng bất thường cần kế toán xem).

    Dòng bất thường: số lượng âm, hoặc số lượng 0 mà còn giá trị (không xuất được bằng phiếu xuất số lượng).
    """
    xuat, bat_thuong = [], []
    for ma, sl, gt in ton:
        sl, gt = float(sl or 0), float(gt or 0)
        if sl > 0:
            xuat.append((ma, sl))
        elif sl < 0 or gt:
            bat_thuong.append((ma, sl, gt))
    return xuat, bat_thuong
