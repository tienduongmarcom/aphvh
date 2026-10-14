"""Quy tắc thuần của báo cáo "Dữ liệu cần rà soát" (0.11.1). Không chặn gì: chỉ phân loại dấu hiệu lệch."""

from lab9x.vn_words import so_vn

NGAY_BON_TOI_DA = 31
HE_SO_KH_BAT_THUONG = 3


def kiem_tai_san(nguyen_gia, luy_ke, tong_ky, ky_da_kh, tan_suat, ttcp, ttcp_cua_vi_tri, loai_ttcp, so_tk_kh):
    """Trả [(mã, mô tả)]. tong_ky/ky_da_kh tính theo kỳ khấu hao (tan_suat tháng/kỳ)."""
    out = []
    con_ky = max(int(tong_ky or 0) - int(ky_da_kh or 0), 0)
    if nguyen_gia > 0 and luy_ke > nguyen_gia:
        out.append(("a2", f"Hao mòn lũy kế {so_vn(luy_ke, 0)} lớn hơn nguyên giá {so_vn(nguyen_gia, 0)} (có thể nhập ngược cột)"))
    elif nguyen_gia > 0 and luy_ke >= nguyen_gia and con_ky > 0:
        out.append(("a1", f"Đã khấu hao hết nguyên giá nhưng còn {con_ky} kỳ khấu hao"))
    if nguyen_gia > 0 and tong_ky and con_ky > 0 and luy_ke < nguyen_gia:
        chuan = nguyen_gia / tong_ky
        thuc = (nguyen_gia - luy_ke) / con_ky
        if thuc > HE_SO_KH_BAT_THUONG * chuan:
            out.append(("a3", f"Khấu hao mỗi kỳ dự kiến {so_vn(thuc, 0)} gấp {thuc / chuan:.1f} lần mức đường thẳng "
                              f"{so_vn(chuan, 0)} (kiểm lũy kế / số kỳ đã khấu hao)"))
    if ttcp_cua_vi_tri and ttcp and ttcp_cua_vi_tri != ttcp:
        out.append(("a4", f"Vị trí thuộc {ttcp_cua_vi_tri} nhưng trung tâm chi phí là {ttcp}"))
    if loai_ttcp and so_tk_kh and not str(so_tk_kh).startswith("154"):
        out.append(("a5", f"Tài sản sản xuất ({loai_ttcp}) nhưng nhóm tài sản ghi khấu hao vào {so_tk_kh}, không phải 15484"))
    return out


def kiem_ton(sl, gia_tri):
    if sl < 0:
        return [("c", f"Tồn âm {so_vn(sl)}")]
    if sl == 0 and abs(gia_tri) >= 1:
        return [("c", f"Số lượng 0 nhưng còn giá trị {so_vn(gia_tri, 0)}")]
    return []


def kiem_bao_bi_nhieu_quy_cach(dong):
    """0.11.2 (docs/dac-ta-0.11.2.md mục 5): một mã bao bì không mang hai quy cách.

    dong: [(BOM, mã bao bì, mô tả trên dòng BOM)]. Trả [(mã, [mô tả...], [BOM...])] cho mã xuất hiện với ≥ 2 mô tả khác nhau
    (so sánh bỏ khoảng trắng thừa, không phân biệt hoa thường).
    """
    gom = {}
    for bom, ma, mo_ta in dong:
        chuan = " ".join(str(mo_ta or "").split()).casefold()
        if not chuan:
            continue
        g = gom.setdefault(ma, {})
        g.setdefault(chuan, (" ".join(str(mo_ta).split()), set()))[1].add(bom)
    out = []
    for ma in sorted(gom):
        if len(gom[ma]) > 1:
            mo_ta = sorted(v[0] for v in gom[ma].values())
            boms = sorted(set().union(*(v[1] for v in gom[ma].values())))
            out.append((ma, mo_ta, boms))
    return out
