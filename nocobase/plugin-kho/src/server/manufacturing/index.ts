/**
 * 0.4.0 Nhà máy Phú Thọ:
 * - Nhập nhanh một phiếu sản xuất (NVL vào / thành phẩm / phụ phẩm / hao hụt) → mẻ + phiếu cấp NVL + phiếu thu hồi trong MỘT giao dịch.
 *   Phiếu thiếu mã hàng, thiếu số lượng hoặc lệch cân bằng kg vượt ngưỡng → hàng đợi "Sản xuất cần rà soát" (không ghi sổ).
 * - Không chốt giá thành bằng 0 (thiếu giá NVL / chi phí).
 * - Báo cáo hiệu suất: tỷ lệ thu hồi, phụ phẩm, hao hụt theo mẻ / xưởng.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien } from '../tienich';
import { kiemKho } from '../toan_ven';
import { cauHinh } from '../security/cau_hinh';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

export function dangKyNhaMay(p: any, H: H, h: any) {
  const { id, val, lyDo } = h;
  const bang = (n: string) => p.bang(n);
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);

  /** Kiểm một phiếu sản xuất; trả danh sách vấn đề (rỗng = đủ điều kiện). */
  p.kiemPhieuSx = async (t: Transaction, v: any) => {
    const vd: string[] = [];
    if (!v.so_phieu) vd.push('Thiếu số phiếu');
    if (!v.kho_id) vd.push('Thiếu kho nhà máy');
    const nhom = { nvl: v.nvl || [], tp: v.tp || [], phu_pham: v.phu_pham || [], hao: v.hao || [] };
    if (!nhom.nvl.length) vd.push('Không có nguyên liệu vào');
    if (!nhom.tp.length) vd.push('Không có thành phẩm ra');
    const kgOf = async (ds: any[], ten: string) => {
      let s = 0;
      for (const [i, d] of ds.entries()) {
        if (!d.mat_hang_id) { vd.push(`${ten} dòng ${i + 1}: chưa có mã hàng${d.ten_nguon ? ` ("${d.ten_nguon}")` : ''}`); continue; }
        if (!(kg(d.so_kg) > 0)) { vd.push(`${ten} dòng ${i + 1}: số lượng phải > 0`); continue; }
        const mh = await bang('mat_hang').findByPk(d.mat_hang_id, { transaction: t });
        if (!mh) { vd.push(`${ten} dòng ${i + 1}: mã hàng không tồn tại`); continue; }
        if (!mh.dvt_ton || mh.dvt_ton === 'kg') s += kg(d.so_kg);
      }
      return s;
    };
    const vao = await kgOf(nhom.nvl, 'NVL');
    const ra = (await kgOf(nhom.tp, 'Thành phẩm')) + (await kgOf(nhom.phu_pham, 'Phụ phẩm')) + (await kgOf(nhom.hao, 'Hao hụt'));
    for (const [i, d] of nhom.phu_pham.entries()) if (d.don_gia === undefined || d.don_gia === null || d.don_gia === '') vd.push(`Phụ phẩm dòng ${i + 1}: thiếu đơn giá thu hồi (0 nếu chưa có)`);
    for (const [i, d] of nhom.hao.entries()) if (!['tu_nhien', 'bat_thuong'].includes(d.loai_hao)) vd.push(`Hao hụt dòng ${i + 1}: chọn tự nhiên / bất thường`);
    const nguong = Number(await cauHinh(p, 'nguong_lech_sx_pct', t)) || 0.5;
    const lech = kg(vao - ra);
    const pct = vao > 0 ? (Math.abs(lech) / vao) * 100 : 0;
    if (vao > 0 && pct > nguong + 1e-9 && !v.chap_nhan_lech) vd.push(`Lệch cân bằng ${lech} kg (${pct.toFixed(2)}% > ngưỡng ${nguong}%): vào ${kg(vao)} ≠ ra ${kg(ra)}`);
    return { van_de: vd, kg_vao: kg(vao), kg_ra: kg(ra), lech, pct };
  };

  H['me_sx:nhapNhanh'] = async (ctx, t) => {
    const v = val(ctx);
    const nguon = v.nguon || 'nhap_tay';
    const khoa = `${nguon}|${v.so_phieu || ''}|${v.ngay || ''}|${v.xuong || ''}`;
    let rs = await bang('sx_ra_soat').findOne({ where: { khoa_trung: khoa }, transaction: t, lock: t.LOCK.UPDATE });
    if (rs?.trang_thai === 'da_tao') return { ok: true, da_tao_truoc: true, me_sx_id: rs.me_sx_id };
    if (v.chap_nhan_lech && (!p.xemGia(ctx) || !v.ly_do)) loi('Chấp nhận lệch cân bằng: chỉ kế toán / quản lý, kèm lý do.');
    if (v.kho_id) kiemKho(ctx, v.kho_id);
    const k = await p.kiemPhieuSx(t, v);
    const luu = { nguon, so_phieu: v.so_phieu || null, ngay: v.ngay || homNay(), xuong: v.xuong || null, du_lieu: JSON.stringify(v), khoa_trung: khoa };
    if (k.van_de.length) {
      if (rs) await rs.update({ ...luu, van_de: k.van_de.join('\n'), trang_thai: 'cho_bo_sung' }, { transaction: t, hooks: false });
      else rs = await bang('sx_ra_soat').create({ ...luu, van_de: k.van_de.join('\n'), trang_thai: 'cho_bo_sung' }, { transaction: t, hooks: false });
      return { ok: false, ra_soat: true, id: rs.id, van_de: k.van_de, kg_vao: k.kg_vao, kg_ra: k.kg_ra };
    }
    const me = await bang('me_sx').create({ ngay_mo: luu.ngay, xuong: v.xuong || null, kho_id: v.kho_id, kho_tp_id: v.kho_tp_id || null,
      san_pham_du_kien: v.so_phieu ? `Phiếu SX ${v.so_phieu}` : null, ghi_chu: [v.ghi_chu, v.chap_nhan_lech ? `Chấp nhận lệch ${k.lech} kg: ${v.ly_do}` : ''].filter(Boolean).join(' | ') || null },
    { transaction: t });
    const phieu = async (loai: string, dong: any[]) => {
      const pk = await bang('phieu_kho').create({ loai, ngay: luu.ngay, kho_id: v.kho_id, kho_dich_id: loai === 'thu_hoi' ? v.kho_tp_id || null : null, me_sx_id: me.id,
        xuong: v.xuong || null, ghi_chu: loai === 'thu_hoi' && (v.hao || []).some((x: any) => x.loai_hao === 'bat_thuong') ? v.ghi_chu || v.ly_do || 'Hao hụt bất thường (phiếu SX)' : v.ghi_chu || null },
      { transaction: t });
      for (const d of dong) await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, ...d }, { transaction: t });
      await goi('phieu_kho:ghiSo', ctx, t, pk.id);
      return pk.so;
    };
    const cap = await phieu('cap_nvl', (v.nvl || []).map((d: any) => ({ mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), so_bao: d.so_bao ?? null, huong: 'vao' })));
    const thu = await phieu('thu_hoi', [
      ...(v.tp || []).map((d: any) => ({ mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), so_bao: d.so_bao ?? null, huong: 'ra', tinh_trang_hang: d.tinh_trang_hang || 'ban_duoc' })),
      ...(v.phu_pham || []).map((d: any) => ({ mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), huong: 'phu_pham', don_gia: Number(d.don_gia || 0) })),
      ...(v.hao || []).map((d: any) => ({ mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), huong: 'hao_hut', loai_hao: d.loai_hao })),
    ]);
    for (const c of v.chi_phi || []) {
      if (!(tien(c.so_tien) > 0)) continue;
      await bang('me_sx_chi_phi').create({ me_sx_id: me.id, loai: c.loai || 'chung', so_tien: tien(c.so_tien), ngay: luu.ngay, so_chung_tu: c.so_chung_tu || null,
        ghi_chu: c.ghi_chu || null, nguoi_ghi: p.nguoi(ctx) }, { transaction: t });
    }
    if (rs) await rs.update({ ...luu, van_de: null, trang_thai: 'da_tao', me_sx_id: me.id }, { transaction: t, hooks: false });
    else await bang('sx_ra_soat').create({ ...luu, trang_thai: 'da_tao', me_sx_id: me.id }, { transaction: t, hooks: false });
    const moi = await bang('me_sx').findByPk(me.id, { transaction: t });
    return { ok: true, me_sx_id: me.id, so: moi.so, phieu_cap: cap, phieu_thu_hoi: thu, kg_vao: k.kg_vao, kg_ra: k.kg_ra, lech: k.lech };
  };
  /** Bổ sung dữ liệu cho phiếu đang rà soát rồi thử tạo lại. */
  H['sx_ra_soat:boSung'] = async (ctx, t) => {
    const rs = await p.khoa('sx_ra_soat', id(ctx), t);
    if (rs.trang_thai === 'da_tao') return { ok: true, da_tao_truoc: true, me_sx_id: rs.me_sx_id };
    if (rs.trang_thai === 'bo_qua') loi('Phiếu đã bỏ qua.');
    const cu = JSON.parse(rs.du_lieu || '{}');
    const moi = { ...cu, ...val(ctx), nguon: cu.nguon || rs.nguon, so_phieu: cu.so_phieu ?? rs.so_phieu, ngay: cu.ngay ?? rs.ngay, xuong: cu.xuong ?? rs.xuong };
    return goi('me_sx:nhapNhanh', ctx, t, null, moi);
  };
  H['sx_ra_soat:boQua'] = async (ctx, t) => {
    const rs = await p.khoa('sx_ra_soat', id(ctx), t);
    if (rs.trang_thai === 'da_tao') loi('Đã tạo mẻ: hủy mẻ nếu cần.');
    if (!lyDo(ctx)) loi('Ghi lý do bỏ qua.');
    await rs.update({ trang_thai: 'bo_qua', van_de: [rs.van_de, `Bỏ qua: ${lyDo(ctx)}`].filter(Boolean).join('\n') }, { transaction: t, hooks: false });
    return { ok: true };
  };

  const chotGoc = H['me_sx:chot'];
  H['me_sx:chot'] = async (ctx, t) => {
    const me = await p.khoa('me_sx', id(ctx), t);
    const s = await p.tinhLaiMe(t, me);
    const tong = s.gia_tri_nvl + s.gia_tri_bao_bi + s.chi_phi;
    if (!(tong > 0)) loi('Tổng chi phí mẻ = 0 (NVL chưa có giá / chưa tập hợp chi phí): không chốt giá thành bằng 0.');
    const [cg] = await p.sql(`SELECT COUNT(*)::int AS n FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id
      WHERE k.me_sx_id = :m AND k.loai = 'cap_nvl' AND k.trang_thai = 'da_ghi' AND COALESCE(d.don_gia,0) <= 0`, { m: me.id }, t);
    if (cg.n && !val(ctx).chap_nhan_nvl_gia_0) loi(`${cg.n} dòng NVL cấp với giá vốn 0 (kho chưa định giá): định giá hàng nhập trước khi chốt.`);
    return chotGoc(ctx, t);
  };

  H['me_sx:hieuSuat'] = async (ctx, t) => {
    const v = val(ctx);
    const ds = await p.sql(`SELECT me.id, me.so, me.xuong, me.ngay_mo, me.trang_thai, me.kg_nvl, me.kg_tp, me.kg_phu_pham, me.kg_hao_tu_nhien, me.kg_hao_bat_thuong,
        ${p.xemGia(ctx) ? 'me.gia_thanh, me.tong_phan_bo,' : ''} k.ten AS kho
      FROM me_sx me LEFT JOIN kho k ON k.id = me.kho_id WHERE me.trang_thai <> 'da_huy'
      AND (:tu::date IS NULL OR me.ngay_mo >= :tu::date) AND (:den::date IS NULL OR me.ngay_mo <= :den::date)
      ${ctx.state?.aphKho ? 'AND me.kho_id IN (:kho)' : ''} ORDER BY me.ngay_mo, me.id`,
    { tu: v.tu || null, den: v.den || null, kho: ctx.state?.aphKho?.length ? ctx.state.aphKho : [0] }, t);
    const pct = (a: any, b: any) => (Number(b) > 0 ? Math.round((Number(a) / Number(b)) * 10000) / 100 : null);
    return ds.map((r: any) => ({ ...r, ty_le_thu_hoi: pct(r.kg_tp, r.kg_nvl), ty_le_phu_pham: pct(r.kg_phu_pham, r.kg_nvl),
      ty_le_hao: pct(Number(r.kg_hao_tu_nhien) + Number(r.kg_hao_bat_thuong), r.kg_nvl),
      lech_can_bang: kg(Number(r.kg_nvl) - Number(r.kg_tp) - Number(r.kg_phu_pham) - Number(r.kg_hao_tu_nhien) - Number(r.kg_hao_bat_thuong)) }));
  };
}
