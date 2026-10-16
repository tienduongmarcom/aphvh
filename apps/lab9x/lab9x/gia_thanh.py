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


# ---------------------------------------------------------------- định mức (0.11.2, phồng tôm)

def nhu_cau_dinh_muc(san_luong, dinh_muc, cong_ty_le=False):
    """Lượng nguyên liệu lẽ ra phải dùng.

    san_luong: {mã đầu ra: số lượng}. dinh_muc: {mã đầu ra: (số lượng đầu ra của BOM, {mã nguyên liệu: lượng}[, % hao hụt
    cho phép])}. cong_ty_le=True: nhân thêm (1 + % hao hụt cho phép của từng BOM) — "mức" tối đa tính vào giá thành.
    Đầu ra không có định mức thì bỏ qua (trả trong danh sách thứ hai).
    """
    can, thieu_dm = {}, []
    for ma, sl in san_luong.items():
        if ma not in dinh_muc:
            thieu_dm.append(ma)
            continue
        goc, dong = dinh_muc[ma][0], dinh_muc[ma][1]
        ty_le = float(dinh_muc[ma][2] or 0) if len(dinh_muc[ma]) > 2 else 0.0
        if float(goc or 0) <= 0:
            thieu_dm.append(ma)
            continue
        if ty_le < 0:
            raise ValueError(f"Tỷ lệ hao hụt cho phép của định mức {ma} không được âm")
        he = float(sl or 0) / float(goc) * ((1 + ty_le / 100) if cong_ty_le else 1)
        for nl, q in dong.items():
            can[nl] = can.get(nl, 0.0) + he * float(q or 0)
    return can, thieu_dm


def chia_hao_hut_dinh_muc(con_lai, da_dung, can_dung, ty_le_cho_phep=0.0, muc=None):
    """Chia lượng còn trên sổ kho dở dang khi quyết toán về 0 (TT133 TK154 nguyên tắc 1(đ)).

    con_lai: {nguyên liệu: lượng còn trên sổ}; da_dung: {nguyên liệu: lượng đã ghi tiêu hao trên phiếu sản xuất trong kỳ};
    can_dung: {nguyên liệu: nhu cầu theo định mức}; ty_le_cho_phep: % hao hụt cho phép thêm trên định mức.
    muc: {nguyên liệu: mức tối đa đã cộng tỷ lệ của từng BOM} (nhu_cau_dinh_muc(..., cong_ty_le=True)); có thì thay
    cho can_dung × (1 + ty_le_cho_phep).

    Trả {nguyên liệu: {"tu_nhien": x, "bat_thuong": y, "ghi_chu": str}}. Phần còn lại trong mức (định mức × (1 + tỷ lệ)) trừ
    phần đã dùng là tự nhiên; vượt là bất thường. Nguyên liệu không có định mức: toàn bộ là bất thường, ghi chú để kế toán xem.
    """
    if float(ty_le_cho_phep or 0) < 0:
        raise ValueError("Tỷ lệ hao hụt cho phép không được âm")
    kq = {}
    for nl, r in con_lai.items():
        r = float(r or 0)
        if r <= 0:
            continue
        if nl not in can_dung:
            kq[nl] = {"tu_nhien": 0.0, "bat_thuong": r, "ghi_chu": "không có trong định mức"}
            continue
        gioi_han = (float(muc[nl]) if muc is not None and nl in muc
                    else float(can_dung[nl]) * (1 + float(ty_le_cho_phep or 0) / 100))
        con_duoc = max(0.0, gioi_han - float(da_dung.get(nl, 0)))
        tn = min(r, con_duoc)
        bt = round(r - tn, 6)
        tong = float(da_dung.get(nl, 0)) + r
        ghi = ""
        if tong < float(can_dung[nl]) - 1e-6:
            ghi = "dùng ít hơn định mức: kiểm lại cấp liệu / cân"
        kq[nl] = {"tu_nhien": round(tn, 6), "bat_thuong": bt, "ghi_chu": ghi}
    return kq


def lech_dinh_muc(thuc_te, can_dung, ty_le_cho_phep=0.0):
    """Cảnh báo cấp liệu lệch định mức (R073): trả [(nguyên liệu, thực tế, định mức, % lệch)] vượt ngưỡng ±tỷ lệ."""
    out = []
    nguong = float(ty_le_cho_phep or 0)
    for nl in sorted(set(thuc_te) | set(can_dung)):
        t, c = float(thuc_te.get(nl, 0)), float(can_dung.get(nl, 0))
        if c <= 0:
            if t > 0:
                out.append((nl, t, c, None))
            continue
        pt = (t - c) / c * 100
        if abs(pt) > nguong + 1e-9:
            out.append((nl, t, c, round(pt, 2)))
    return out
