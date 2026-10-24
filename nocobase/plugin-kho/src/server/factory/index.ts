/**
 * 0.4.1 Factory MES Lite — Nhà máy Phú Thọ. Dùng lại me_sx / phiếu cấp NVL / phiếu thu hồi / giá thành hiện có (KHÔNG có sổ hay mẻ song song).
 * - Mẫu sản xuất theo 4 công nghệ, định mức có PHIÊN BẢN (đề xuất → kế toán duyệt); mẻ lưu SNAPSHOT định mức lúc mở (đổi định mức sau không ảnh hưởng).
 * - Mẫu chỉ GỢI Ý lượng dự kiến; chỉ "Ghi thực tế" (lượng đã cân / đếm) mới phát sinh xuất / nhập kho.
 * - Cân đối khối lượng theo công nghệ: chênh lệch KHÔNG tự thành hao hụt; hao hụt chỉ là lượng đã đo + xác nhận; phần còn lại phải giải trình (kế toán duyệt).
 *   Bao bì / vật tư / nhiên liệu không vào cân bằng khối lượng dù ĐVT là kg. Thiếu quy đổi kg / thiếu số đo nước → "Chưa đủ căn cứ", không mặc định 0.
 * - Bao bì: hệ thống gợi ý theo định mức, ghi lượng THỰC dùng + hỏng có lý do; khác định mức phải ghi nguyên nhân.
 * - Hàng gửi gia công: kho hàng gửi riêng (không bán), bên gửi / bên nhận / chủ sở hữu xác nhận tách bạch; không tự tạo doanh thu, không đổi sở hữu.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien } from '../tienich';
import { kiemKho } from '../toan_ven';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;
const TRONG_CAN_BANG = new Set(['nvl', 'tp', 'phu_pham']);

export function dangKyNhaMay041(p: any, H: H, h: any) {
  const { id, val, lyDo } = h;
  const bang = (n: string) => p.bang(n);
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);
  const canQuyen = (ctx: any, viec: string) => { if (!p.xemGia(ctx)) loi(`Chỉ kế toán / quản lý được ${viec}.`); };

  /** Quy về kg: hàng tồn theo kg → chính nó; ĐVT khác cần "kg cho 1 ĐVT" có căn cứ; thiếu → null (chưa đủ căn cứ). */
  const kgCua = (mh: any, sl: number): number | null => {
    if (!mh) return null;
    if (!mh.dvt_ton || mh.dvt_ton === 'kg') return kg(sl);
    if (Number(mh.kg_moi_dvt) > 0 && mh.kg_dvt_can_cu) return kg(sl * Number(mh.kg_moi_dvt));
    return null;
  };

  const phienBanApDung = async (t: Transaction, mauId: any, ngay: string) => {
    const [pb] = await p.sql(`SELECT id FROM mau_sx_phien_ban WHERE mau_sx_id = :m AND trang_thai = 'da_duyet' AND (hieu_luc_tu IS NULL OR hieu_luc_tu <= :n)
      ORDER BY hieu_luc_tu DESC NULLS LAST, phien_ban DESC LIMIT 1`, { m: mauId, n: ngay }, t);
    return pb ? bang('mau_sx_phien_ban').findByPk(pb.id, { transaction: t }) : null;
  };
  const snap = (me: any) => JSON.parse(me.snapshot_dinh_muc || 'null');
  const snapGia = (me: any) => JSON.parse(me.snapshot_gia || '{}');

  // ---------------- MẪU & ĐỊNH MỨC ----------------
  H['mau_sx_phien_ban:duyet'] = async (ctx, t) => {
    canQuyen(ctx, 'duyệt định mức');
    const pb = await p.khoa('mau_sx_phien_ban', id(ctx), t);
    if (pb.trang_thai === 'da_duyet') return { ok: true, da_duyet_truoc: true };
    if (pb.trang_thai !== 'de_xuat') loi('Chỉ được duyệt phiên bản định mức còn ở trạng thái Đề xuất.');
    const dong = await bang('mau_sx_dong').findAll({ where: { mau_sx_phien_ban_id: pb.id }, transaction: t });
    if (!dong.some((d: any) => d.vai_tro === 'tp')) loi('Phiên bản định mức cần ít nhất một dòng thành phẩm.');
    if (!dong.some((d: any) => d.vai_tro === 'nvl')) loi('Phiên bản định mức cần ít nhất một dòng nguyên liệu.');
    if (!pb.can_cu && !val(ctx).can_cu) loi('Ghi căn cứ định mức (thực nghiệm / biên bản) trước khi duyệt.');
    await pb.update({ trang_thai: 'da_duyet', duyet_boi: p.nguoi(ctx), can_cu: val(ctx).can_cu || pb.can_cu, hieu_luc_tu: pb.hieu_luc_tu || homNay() },
      { transaction: t, hooks: false });
    return { ok: true };
  };
  H['mau_sx_phien_ban:ngung'] = async (ctx, t) => {
    canQuyen(ctx, 'ngừng định mức');
    const pb = await p.khoa('mau_sx_phien_ban', id(ctx), t);
    await pb.update({ trang_thai: 'ngung' }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- MỞ MẺ TỪ MẪU ----------------
  H['me_sx:moTuMau'] = async (ctx, t) => {
    const v = val(ctx);
    if (v.request_id) {
      const [co] = await p.sql(`SELECT id, so FROM me_sx WHERE ghi_chu LIKE :r LIMIT 1`, { r: `%[${v.request_id}]%` }, t);
      if (co) return { ok: true, da_mo_truoc: true, id: co.id, so: co.so };
    }
    const mau = await bang('mau_sx').findByPk(v.mau_sx_id, { transaction: t });
    if (!mau || mau.ngung) loi('Chọn mẫu sản xuất đang dùng.');
    const ngay = v.ngay || homNay();
    const pb = await phienBanApDung(t, mau.id, ngay);
    if (!pb) loi(`Mẫu ${mau.ma} chưa có phiên bản định mức đã duyệt hiệu lực ngày ${ngay}.`);
    let kho_id = v.kho_id, kho_tp_id = v.kho_tp_id || null, ben_gui_id = null;
    if (v.ho_so_gia_cong_id) {
      const hs = await bang('sx_ho_so_gia_cong').findByPk(v.ho_so_gia_cong_id, { transaction: t });
      if (!hs || hs.trang_thai !== 'mo') loi('Hồ sơ gia công không mở.');
      kho_id = hs.kho_id; kho_tp_id = hs.kho_id; ben_gui_id = hs.ben_gui_id; // hàng gửi: vào / ra đều ở kho hàng gửi của bên gửi
    }
    if (!kho_id) loi('Chọn kho lấy nguyên liệu.');
    kiemKho(ctx, kho_id, kho_tp_id);
    const dong = await p.sql(`SELECT d.*, m.ma, m.ten, m.dvt_ton, m.kg_moi_dvt, m.kg_dvt_can_cu FROM mau_sx_dong d JOIN mat_hang m ON m.id = d.mat_hang_id
      WHERE d.mau_sx_phien_ban_id = :p ORDER BY COALESCE(d.thu_tu,0), d.id`, { p: pb.id }, t);
    const s = { mau: { id: mau.id, ma: mau.ma, ten: mau.ten, loai_cn: mau.loai_cn }, phien_ban: { id: pb.id, so: pb.phien_ban, nguong_chenh_pct: pb.nguong_chenh_pct },
      dong: dong.map((d: any) => ({ vai_tro: d.vai_tro, mat_hang_id: Number(d.mat_hang_id), ma: d.ma, ten: d.ten, dvt: d.dvt_ton || 'kg', co_so: d.co_so,
        dinh_muc: Number(d.dinh_muc || 0), nguong_hao_pct: d.nguong_hao_pct === null ? null : Number(d.nguong_hao_pct), cong_doan: d.cong_doan })) };
    const g = { pp_gia_thanh: mau.pp_gia_thanh, dong: dong.map((d: any) => ({ mat_hang_id: Number(d.mat_hang_id), vai_tro: d.vai_tro, he_so_gia: d.he_so_gia,
      gia_tham_chieu: d.gia_tham_chieu, nguon_gia_tc: d.nguon_gia_tc })) };
    const me = await bang('me_sx').create({ ngay_mo: ngay, xuong: mau.xuong || v.xuong || null, kho_id, kho_tp_id, san_pham_du_kien: `${mau.ma} v${pb.phien_ban}`,
      phuong_phap: mau.pp_gia_thanh || 'kg', ghi_chu: [v.ghi_chu, v.request_id ? `[${v.request_id}]` : ''].filter(Boolean).join(' ') || null }, { transaction: t });
    await me.update({ mau_sx_id: mau.id, mau_phien_ban_id: pb.id, snapshot_dinh_muc: JSON.stringify(s), snapshot_gia: JSON.stringify(g), ca_sx_id: v.ca_sx_id || null,
      loai_cn: mau.loai_cn, ben_gui_id, ho_so_gia_cong_id: v.ho_so_gia_cong_id || null, sl_ke_hoach: v.sl_ke_hoach ?? null, tt_van_hanh: 'dang_sx' },
    { transaction: t, hooks: false });
    const moi = await bang('me_sx').findByPk(me.id, { transaction: t });
    return { ok: true, id: me.id, so: moi.so, phien_ban: pb.phien_ban, goi_y: goiY(s, { nvl_kg: v.nvl_kg, tp_sl: v.sl_ke_hoach }) };
  };

  /** Lượng dự kiến theo snapshot: định mức × (kg NVL vào | số ĐVT thành phẩm chính). Không ghi gì. */
  const goiY = (s: any, a: { nvl_kg?: any; tp_sl?: any }) => {
    if (!s) return [];
    let nvl = Number(a.nvl_kg) || 0, tp = Number(a.tp_sl) || 0;
    const tpChinh = s.dong.find((d: any) => d.vai_tro === 'tp');
    // Biết một đầu thì suy đầu kia theo dòng thành phẩm chính.
    const nvlChinh = s.dong.find((d: any) => d.vai_tro === 'nvl');
    if (!tp && nvl && tpChinh?.co_so === 'nvl') tp = kg(nvl * tpChinh.dinh_muc);
    else if (!tp && nvl && nvlChinh?.co_so === 'tp' && nvlChinh.dinh_muc) tp = kg(nvl / nvlChinh.dinh_muc);
    if (!nvl && tp) { const n = s.dong.find((d: any) => d.vai_tro === 'nvl'); if (n?.co_so === 'tp') nvl = kg(tp * n.dinh_muc); else if (tpChinh?.co_so === 'nvl' && tpChinh.dinh_muc) nvl = kg(tp / tpChinh.dinh_muc); }
    return s.dong.map((d: any) => ({ vai_tro: d.vai_tro, mat_hang_id: d.mat_hang_id, ma: d.ma, ten: d.ten, dvt: d.dvt, cong_doan: d.cong_doan,
      du_kien: d.vai_tro === 'nvl' && d === s.dong.find((x: any) => x.vai_tro === 'nvl') && nvl ? kg(nvl)
        : kg(d.dinh_muc * (d.co_so === 'tp' ? tp : nvl)) }));
  };
  H['me_sx:goiY'] = async (ctx, t) => {
    const me = await bang('me_sx').findByPk(id(ctx), { transaction: t });
    if (!me) loi('Không thấy mẻ.');
    return { ok: true, goi_y: goiY(snap(me), val(ctx)) };
  };

  // ---------------- CÂN ĐỐI KHỐI LƯỢNG ----------------
  /** Tính lũy kế cả mẻ (nhiều lần ghi / nhiều ngày): WIP chỉ lấy số cuối, không cộng hai lần. */
  p.canDoiMe = async (t: Transaction, me: any, them: { nuoc_vao?: number; nuoc_bay_hoi?: number; wip_cuoi?: number | null } = {}) => {
    const s = snap(me);
    const loai = me.loai_cn || s?.mau?.loai_cn || 'GRADING';
    const dong = await p.sql(`SELECT d.id, d.huong, d.vai_tro, d.loai_hao, d.so_kg, d.mat_hang_id, k.loai, m.ma, m.dvt_ton, m.kg_moi_dvt, m.kg_dvt_can_cu, m.loai_hang
      FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id JOIN mat_hang m ON m.id = d.mat_hang_id
      WHERE k.me_sx_id = :me AND k.trang_thai = 'da_ghi' AND k.loai IN ('cap_nvl','thu_hoi')`, { me: me.id }, t);
    const vd: string[] = [];
    const tong: Record<string, number> = { nvl: 0, tp: 0, phu_pham: 0, hao: 0, hao_tn: 0 };
    for (const d of dong) {
      const vt = d.vai_tro || (d.loai === 'cap_nvl' ? (['bao_bi'].includes(d.loai_hang) ? 'bao_bi' : 'nvl') : d.huong === 'ra' ? 'tp' : d.huong === 'phu_pham' ? 'phu_pham' : d.huong === 'hao_hut' ? 'hao' : 'khac');
      if (vt === 'hao' || d.huong === 'hao_hut') { tong.hao += kg(d.so_kg); if (d.loai_hao !== 'bat_thuong') tong.hao_tn += kg(d.so_kg); continue; }
      if (!TRONG_CAN_BANG.has(vt)) continue; // bao bì, vật tư, nhiên liệu, nước: không vào khối lượng sản phẩm
      const x = kgCua(d, Number(d.so_kg));
      if (x === null) { vd.push(`thiếu quy đổi kg có căn cứ cho ${d.ma} (${d.dvt_ton})`); continue; }
      tong[vt] += x;
    }
    const [truoc] = await p.sql(`SELECT nuoc_vao, nuoc_bay_hoi, wip_cuoi, lan FROM sx_doi_chieu WHERE me_sx_id = :m ORDER BY lan DESC LIMIT 1`, { m: me.id }, t);
    const nuoc_vao = kg(Number(truoc?.nuoc_vao || 0) + Number(them.nuoc_vao || 0));
    const coNuocBH = (truoc && truoc.nuoc_bay_hoi !== null) || (them.nuoc_bay_hoi !== undefined && them.nuoc_bay_hoi !== null);
    const nuoc_bay_hoi = kg(Number(truoc?.nuoc_bay_hoi || 0) + Number(them.nuoc_bay_hoi || 0));
    const wip_cuoi = them.wip_cuoi !== undefined && them.wip_cuoi !== null ? kg(them.wip_cuoi) : kg(truoc?.wip_cuoi ?? me.kg_do_dang ?? 0);
    let wip_dau = 0;
    if (me.me_goc_id) { const g = await bang('me_sx').findByPk(me.me_goc_id, { transaction: t }); wip_dau = kg(g?.kg_do_dang || 0); }
    if (loai === 'BLENDING_COOKING') {
      const canNuoc = (s?.dong || []).some((d: any) => d.vai_tro === 'nuoc') || nuoc_vao > 0;
      if (canNuoc && !(nuoc_vao > 0)) vd.push('chưa ghi lượng nước / phụ gia lỏng thêm vào');
      if (canNuoc && !coNuocBH) vd.push('chưa đo / xác nhận lượng nước bay hơi khi sấy');
    }
    if (!(tong.nvl > 0)) vd.push('chưa có nguyên liệu vào');
    const chenh = kg(tong.nvl + nuoc_vao + wip_dau - (tong.tp + tong.phu_pham + tong.hao + (coNuocBH ? nuoc_bay_hoi : 0) + wip_cuoi));
    const [gt] = await p.sql(`SELECT COALESCE(SUM(so_kg),0) AS kg FROM sx_giai_trinh WHERE me_sx_id = :m AND trang_thai = 'da_duyet' AND phan_loai <> 'hao_bat_thuong'`, { m: me.id }, t);
    const da_giai_trinh = kg(gt.kg);
    const con_lai = kg(chenh - da_giai_trinh);
    const nguongHao = (s?.dong || []).filter((d: any) => d.vai_tro === 'nvl' && d.nguong_hao_pct !== null && d.nguong_hao_pct !== undefined).map((d: any) => Number(d.nguong_hao_pct));
    const ty_le_hao = tong.nvl > 0 ? (tong.hao_tn / tong.nvl) * 100 : 0;
    const tol = s?.phien_ban?.nguong_chenh_pct !== null && s?.phien_ban?.nguong_chenh_pct !== undefined ? (tong.nvl * Number(s.phien_ban.nguong_chenh_pct)) / 100 : 0.0005;
    let ket_qua = 'can';
    if (vd.length) ket_qua = 'chua_du';
    else if (nguongHao.length && ty_le_hao > Math.max(...nguongHao) + 1e-9) { ket_qua = 'vuot_nguong'; vd.push(`hao hụt tự nhiên ${ty_le_hao.toFixed(2)}% > ngưỡng ${Math.max(...nguongHao)}% — kế toán xem xét`); }
    else if (Math.abs(con_lai) > tol + 1e-9) ket_qua = 'co_chenh';
    return { loai_cn: loai, kg_vao: kg(tong.nvl), nuoc_vao, wip_dau, kg_tp: kg(tong.tp), kg_pp: kg(tong.phu_pham), kg_hao: kg(tong.hao), nuoc_bay_hoi: coNuocBH ? nuoc_bay_hoi : null,
      wip_cuoi, chenh, da_giai_trinh, con_lai, ket_qua, van_de: vd, ty_le_thu_hoi: tong.nvl > 0 ? Math.round((tong.tp / tong.nvl) * 10000) / 100 : null,
      ty_le_hao: Math.round(ty_le_hao * 100) / 100, lan: Number(truoc?.lan || 0) };
  };
  const luuDoiChieu = async (ctx: any, t: Transaction, me: any, c: any, chiTiet: any = {}) => {
    await bang('sx_doi_chieu').create({ me_sx_id: me.id, lan: c.lan + 1, loai_cn: c.loai_cn, kg_vao: c.kg_vao, nuoc_vao: c.nuoc_vao, wip_dau: c.wip_dau, kg_tp: c.kg_tp,
      kg_pp: c.kg_pp, kg_phe: 0, kg_hao: c.kg_hao, nuoc_bay_hoi: c.nuoc_bay_hoi, wip_cuoi: c.wip_cuoi, chenh: c.chenh, da_giai_trinh: c.da_giai_trinh, con_lai: c.con_lai,
      ket_qua: c.ket_qua, van_de: c.van_de.join('; ') || null, chi_tiet: JSON.stringify(chiTiet), nguoi: p.nguoi(ctx) }, { transaction: t, hooks: false });
  };
  H['me_sx:canDoi'] = async (ctx, t) => {
    const me = await bang('me_sx').findByPk(id(ctx), { transaction: t });
    if (!me) loi('Không thấy mẻ.');
    return { ok: true, ...(await p.canDoiMe(t, me)) };
  };

  // ---------------- GHI THỰC TẾ ----------------
  /**
   * values: {request_id, nvl:[{mat_hang_id, so_luong, kho_id?, so_lo?}], tp:[{mat_hang_id, so_luong, so_bao?, so_lo?}], phu_pham:[{mat_hang_id, so_luong}],
   *          hao:[{so_kg, mat_hang_id?}] (hao đã ĐO), bao_bi|vat_tu|nhien_lieu:[{mat_hang_id, so_luong, so_hong?, ly_do?, kho_id?}],
   *          nuoc_vao?, nuoc_bay_hoi?, wip_cuoi?, ket_thuc?: bool}
   */
  H['me_sx:ghiThucTe'] = async (ctx, t) => {
    const v = val(ctx);
    if (!v.request_id) loi('Thiếu mã yêu cầu (chống ghi hai lần).');
    const me = await p.khoa('me_sx', id(ctx), t);
    const [daCo] = await p.sql(`SELECT so FROM phieu_kho WHERE request_id LIKE :r AND me_sx_id = :m LIMIT 1`, { r: `${v.request_id}%`, m: me.id }, t);
    if (daCo) return { ok: true, da_ghi_truoc: true, phieu: daCo.so, ...(await p.canDoiMe(t, me)) };
    if (['da_huy', 'da_khoa'].includes(me.trang_thai)) loi('Mẻ đã hủy / khóa kỳ.');
    if (me.tt_van_hanh === 'hoan_thanh' && !p.xemGia(ctx)) loi('Mẻ đã hoàn thành thực tế: ghi thêm cần kế toán mở lại.');
    const s = snap(me);
    const sg = snapGia(me);
    const giaPP = (mh: any) => Number((sg.dong || []).find((d: any) => d.mat_hang_id === Number(mh) && d.vai_tro === 'phu_pham')?.gia_tham_chieu || 0);
    const ngay = v.ngay || homNay();
    const chiTiet: any = { bao_bi: [] as any[] };
    // 1) Phiếu cấp: NVL + bao bì / vật tư / nhiên liệu (theo kho cấp)
    const cap: Record<string, any[]> = {};
    const can: Record<string, number> = {};
    // Dòng không chọn kho: lấy kho của mẻ nếu đủ hàng, không thì kho nhà máy khác (trong phạm vi) còn đủ hàng — nhà máy không phải nhớ hàng nằm kho nào.
    const chonKho = async (d: any, sl: number) => {
      if (d.kho_id) return d.kho_id;
      if (me.ho_so_gia_cong_id) return me.kho_id;
      const ds = await p.sql(`SELECT t.kho_id, t.so_kg - t.so_giu - t.so_cho_gia AS atp FROM ton_kho t JOIN kho k ON k.id = t.kho_id
        WHERE t.mat_hang_id = :m AND (t.kho_id = :k OR k.loai_kho = 'nha_may') ORDER BY (t.kho_id = :k) DESC, atp DESC`, { m: d.mat_hang_id, k: me.kho_id }, t);
      const pv = ctx.state?.aphKho;
      for (const x of ds) {
        if (pv && !pv.includes(Number(x.kho_id))) continue;
        const k = `${x.kho_id}|${d.mat_hang_id}`;
        if (Number(x.atp) - (can[k] || 0) + 0.0005 >= sl) { can[k] = (can[k] || 0) + sl; return Number(x.kho_id); }
      }
      return me.kho_id;
    };
    const them = async (kho: any, d: any) => { const k = await chonKho({ ...d, kho_id: kho }, d.so_kg); (cap[k] = cap[k] || []).push(d); };
    for (const d of v.nvl || []) if (Number(d.so_luong) > 0) await them(d.kho_id, { mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_luong), vai_tro: 'nvl', so_lo: d.so_lo || null });
    const tpSl = (v.tp || []).reduce((a: number, d: any) => a + Number(d.so_luong || 0), 0);
    const nvlKg = (v.nvl || []).reduce((a: number, d: any) => a + Number(d.so_luong || 0), 0);
    for (const vt of ['bao_bi', 'vat_tu', 'nhien_lieu']) {
      for (const d of v[vt] || []) {
        const dung = kg(d.so_luong), hong = kg(d.so_hong);
        if (!(dung + hong > 0)) continue;
        const dm = (s?.dong || []).find((x: any) => x.vai_tro === vt && x.mat_hang_id === Number(d.mat_hang_id));
        const duKien = dm ? kg(dm.dinh_muc * (dm.co_so === 'tp' ? tpSl : nvlKg)) : null;
        if (hong > 0 && !d.ly_do) loi('Bao bì / vật tư hỏng, loại bỏ: ghi lý do.');
        if (duKien !== null && Math.abs(dung - duKien) > 0.0005 && !d.ly_do) loi(`Dùng ${dung} khác định mức ${duKien} (mặt hàng #${d.mat_hang_id}): ghi nguyên nhân.`);
        chiTiet.bao_bi.push({ mat_hang_id: d.mat_hang_id, vai_tro: vt, dinh_muc: duKien, dung, hong, ly_do: d.ly_do || null });
        await them(d.kho_id, { mat_hang_id: d.mat_hang_id, so_kg: kg(dung + hong), so_hong: hong || null, vai_tro: vt, ghi_chu: d.ly_do || null });
      }
    }
    const so: string[] = [];
    let i = 0;
    for (const [kho, ds] of Object.entries(cap)) {
      kiemKho(ctx, kho);
      const pk = await bang('phieu_kho').create({ loai: 'cap_nvl', ngay, kho_id: Number(kho), me_sx_id: me.id, request_id: `${v.request_id}-cap${i++}`,
        ghi_chu: `Ghi thực tế ${me.so}` }, { transaction: t });
      for (const d of ds) await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, ...d }, { transaction: t });
      await goi('phieu_kho:ghiSo', ctx, t, pk.id);
      so.push(pk.so);
    }
    // 2) Phiếu thu hồi: thành phẩm, phụ phẩm, hao hụt ĐÃ ĐO (nhà máy chỉ ghi hao tự nhiên; bất thường do kế toán duyệt từ giải trình)
    const thu: any[] = [];
    for (const d of v.tp || []) if (Number(d.so_luong) > 0) thu.push({ mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_luong), so_bao: d.so_bao ?? null, huong: 'ra', vai_tro: 'tp', so_lo: d.so_lo || null });
    for (const d of v.phu_pham || []) if (Number(d.so_luong) > 0) thu.push({ mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_luong), huong: 'phu_pham', vai_tro: 'phu_pham', don_gia: giaPP(d.mat_hang_id) });
    const nvlChinh = (v.nvl || [])[0]?.mat_hang_id || (s?.dong || []).find((x: any) => x.vai_tro === 'nvl')?.mat_hang_id;
    for (const d of v.hao || []) {
      if (!(Number(d.so_kg) > 0)) continue;
      const bt = d.loai_hao === 'bat_thuong';
      if (bt && !p.xemGia(ctx)) loi('Hao hụt bất thường: ghi vào giải trình để kế toán duyệt.');
      thu.push({ mat_hang_id: d.mat_hang_id || nvlChinh, so_kg: kg(d.so_kg), huong: 'hao_hut', loai_hao: bt ? 'bat_thuong' : 'tu_nhien' });
    }
    if (thu.length) {
      const pk = await bang('phieu_kho').create({ loai: 'thu_hoi', ngay, kho_id: me.kho_id, me_sx_id: me.id, request_id: `${v.request_id}-thu`,
        ghi_chu: `Ghi thực tế ${me.so}${(v.hao || []).some((d: any) => d.loai_hao === 'bat_thuong') ? ` — hao bất thường: ${v.ly_do_hao || 'kế toán ghi'}` : ''}` }, { transaction: t });
      for (const d of thu) await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, ...d }, { transaction: t });
      await goi('phieu_kho:ghiSo', ctx, t, pk.id);
      so.push(pk.so);
    }
    if (!so.length && v.wip_cuoi === undefined && v.nuoc_bay_hoi === undefined) loi('Chưa nhập số liệu thực tế.');
    for (const [dsKey, huong] of [['nvl', 'vao'], ['tp', 'ra']] as const) {
      for (const d of v[dsKey] || []) if (d.so_lo && Number(d.so_luong) > 0)
        await bang('sx_nguon_lo').create({ me_sx_id: me.id, huong, mat_hang_id: d.mat_hang_id, so_lo: d.so_lo, so_kg: kg(d.so_luong) }, { transaction: t, hooks: false });
    }
    const meMoi = await p.khoa('me_sx', me.id, t);
    await p.tinhLaiMe(t, meMoi);
    if (v.wip_cuoi !== undefined && v.wip_cuoi !== null) await meMoi.update({ kg_do_dang: kg(v.wip_cuoi) }, { transaction: t, hooks: false });
    const c = await p.canDoiMe(t, meMoi, { nuoc_vao: v.nuoc_vao, nuoc_bay_hoi: v.nuoc_bay_hoi, wip_cuoi: v.wip_cuoi });
    await luuDoiChieu(ctx, t, meMoi, c, chiTiet);
    const tt = v.ket_thuc ? (c.ket_qua === 'can' ? 'hoan_thanh' : 'cho_can_doi') : 'dang_sx';
    await meMoi.update({ tt_van_hanh: tt }, { transaction: t, hooks: false });
    return { ok: true, phieu: so, tt_van_hanh: tt, ...c, bao_bi: chiTiet.bao_bi };
  };
  H['me_sx:ketThuc'] = async (ctx, t) => {
    const me = await p.khoa('me_sx', id(ctx), t);
    const c = await p.canDoiMe(t, me);
    await luuDoiChieu(ctx, t, me, c);
    const tt = c.ket_qua === 'can' ? 'hoan_thanh' : 'cho_can_doi';
    await me.update({ tt_van_hanh: tt }, { transaction: t, hooks: false });
    return { ok: true, tt_van_hanh: tt, ...c };
  };
  H['me_sx:moLaiVanHanh'] = async (ctx, t) => {
    canQuyen(ctx, 'mở lại mẻ đã hoàn thành');
    if (!lyDo(ctx)) loi('Ghi lý do.');
    const me = await p.khoa('me_sx', id(ctx), t);
    await me.update({ tt_van_hanh: 'dang_sx', ghi_chu: [me.ghi_chu, `Mở lại: ${lyDo(ctx)}`].filter(Boolean).join(' | ') }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- GIẢI TRÌNH CHÊNH LỆCH ----------------
  H['me_sx:giaiTrinh'] = async (ctx, t) => {
    const me = await p.khoa('me_sx', id(ctx), t);
    const v = val(ctx);
    if (!(Number(v.so_kg) > 0)) loi('Nhập số kg giải trình.');
    if (!['do_sai', 'hao_bat_thuong', 'khac'].includes(v.phan_loai)) loi('Chọn phân loại.');
    if (!v.ly_do) loi('Ghi lý do / căn cứ.');
    const c = await p.canDoiMe(t, me);
    const [cho] = await p.sql(`SELECT COALESCE(SUM(ABS(so_kg)),0) AS kg FROM sx_giai_trinh WHERE me_sx_id = :m AND trang_thai = 'cho_duyet'`, { m: me.id }, t);
    if (kg(v.so_kg) > Math.abs(c.con_lai) - Number(cho.kg) + 0.0005) loi(`Chỉ còn ${kg(Math.abs(c.con_lai) - Number(cho.kg))} kg chưa giải trình.`);
    if (v.phan_loai === 'hao_bat_thuong' && c.con_lai <= 0) loi('Chênh thừa không thể giải trình thành hao hụt bất thường.');
    const soKgCoDau = Math.sign(c.con_lai) * kg(v.so_kg);
    const g = await bang('sx_giai_trinh').create({ me_sx_id: me.id, so_kg: soKgCoDau, phan_loai: v.phan_loai, ly_do: v.ly_do, trang_thai: 'cho_duyet', nguoi: p.nguoi(ctx) },
      { transaction: t, hooks: false });
    return { ok: true, id: g.id };
  };
  H['sx_giai_trinh:duyet'] = async (ctx, t) => {
    canQuyen(ctx, 'duyệt giải trình / hao hụt bất thường');
    const g = await p.khoa('sx_giai_trinh', id(ctx), t);
    if (g.trang_thai === 'da_duyet') return { ok: true, da_duyet_truoc: true };
    if (g.trang_thai !== 'cho_duyet') loi('Giải trình đã bị từ chối.');
    const me = await p.khoa('me_sx', g.me_sx_id, t);
    const truocDuyet = await p.canDoiMe(t, me);
    if (Math.sign(Number(g.so_kg)) !== Math.sign(truocDuyet.con_lai) || Math.abs(Number(g.so_kg)) > Math.abs(truocDuyet.con_lai) + 0.0005)
      loi('Chênh lệch đã thay đổi sau khi gửi giải trình: cần lập giải trình mới theo số đo hiện tại.');
    if (g.phan_loai === 'hao_bat_thuong' && Number(g.so_kg) <= 0) loi('Hao hụt bất thường chỉ áp dụng cho lượng thiếu đã xác nhận.');
    if (g.phan_loai === 'hao_bat_thuong') {
      // Ghi nhận hao hụt bất thường bằng phiếu thu hồi (không vào giá thành), có lịch sử chứng từ.
      const s = snap(me);
      const [nvl] = await p.sql(`SELECT d.mat_hang_id FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id WHERE k.me_sx_id = :m AND k.loai = 'cap_nvl'
        AND k.trang_thai = 'da_ghi' AND COALESCE(d.vai_tro,'nvl') = 'nvl' ORDER BY d.id LIMIT 1`, { m: me.id }, t);
      const pk = await bang('phieu_kho').create({ loai: 'thu_hoi', ngay: homNay(), kho_id: me.kho_id, me_sx_id: me.id, request_id: `GT-${g.id}`,
        ghi_chu: `Hao hụt bất thường đã duyệt (giải trình #${g.id}): ${g.ly_do}` }, { transaction: t });
      await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, mat_hang_id: nvl?.mat_hang_id || s?.dong?.find((d: any) => d.vai_tro === 'nvl')?.mat_hang_id,
        so_kg: kg(g.so_kg), huong: 'hao_hut', loai_hao: 'bat_thuong' }, { transaction: t });
      await goi('phieu_kho:ghiSo', ctx, t, pk.id);
    }
    await g.update({ trang_thai: 'da_duyet', duyet_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    const meMoi = await p.khoa('me_sx', me.id, t);
    await p.tinhLaiMe(t, meMoi);
    const c = await p.canDoiMe(t, meMoi);
    await luuDoiChieu(ctx, t, meMoi, c, { giai_trinh: g.id });
    if (meMoi.tt_van_hanh === 'cho_can_doi' && c.ket_qua === 'can') await meMoi.update({ tt_van_hanh: 'hoan_thanh' }, { transaction: t, hooks: false });
    return { ok: true, ...c };
  };
  H['sx_giai_trinh:tuChoi'] = async (ctx, t) => {
    canQuyen(ctx, 'từ chối giải trình');
    const g = await p.khoa('sx_giai_trinh', id(ctx), t);
    if (g.trang_thai !== 'cho_duyet') loi('Giải trình không chờ duyệt.');
    if (!lyDo(ctx)) loi('Ghi lý do từ chối.');
    await g.update({ trang_thai: 'tu_choi', duyet_boi: p.nguoi(ctx), ly_do: `${g.ly_do} | Từ chối: ${lyDo(ctx)}` }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- CHỐT GIÁ THÀNH: điều kiện 0.4.1 + phương pháp theo mẫu ----------------
  const chotGoc = H['me_sx:chot'];
  H['me_sx:chot'] = async (ctx, t) => {
    const me = await p.khoa('me_sx', id(ctx), t);
    const [cap] = await p.sql(`SELECT COUNT(*)::int AS n FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id
      WHERE k.me_sx_id = :m AND k.loai = 'cap_nvl' AND k.trang_thai = 'da_ghi'`, { m: me.id }, t);
    const [dd] = await p.sql(`SELECT COUNT(*)::int AS n FROM me_sx_chi_phi WHERE me_sx_id = :m AND loai = 'do_dang_dau_ky'`, { m: me.id }, t);
    if (!cap.n && !dd.n && !me.me_goc_id) loi('Mẻ chỉ có thành phẩm, thiếu phiếu cấp nguyên liệu: không chốt giá thành chính thức.');
    const v = ctx.action.params.values = { ...(ctx.action.params.values || {}) };
    if (me.mau_sx_id) {
      // Chấp nhận chênh KHÔNG thay thế bước kết thúc sản xuất và không được miễn thiếu căn cứ.
      if (['dang_sx', 'nhap'].includes(me.tt_van_hanh)) loi('Mẻ chưa kết thúc sản xuất: không được chốt giá thành.');
      const canDoi = await p.canDoiMe(t, me);
      if (canDoi.ket_qua === 'chua_du') loi('Thiếu căn cứ cân đối: không được chốt giá thành, kể cả khi chấp nhận chênh.');
      if (canDoi.ket_qua === 'vuot_nguong') loi('Hao hụt vượt ngưỡng: cần xử lý và phê duyệt trước khi chốt giá thành.');
      if ((me.tt_van_hanh === 'cho_can_doi' || canDoi.ket_qua === 'co_chenh') && !v.chap_nhan_chenh)
        loi('Mẻ còn chênh lệch khối lượng chưa giải trình: duyệt giải trình hoặc chọn chấp nhận chênh kèm lý do.');
    }
    if (v.chap_nhan_chenh && !v.ly_do_chenh) loi('Chấp nhận chênh lệch: ghi lý do.');
    const sg = snapGia(me);
    if (!v.phuong_phap && sg.pp_gia_thanh) v.phuong_phap = sg.pp_gia_thanh;
    if (v.phuong_phap === 'he_so' && !v.he_so) {
      const hs: Record<string, number> = {};
      const ra = await p.sql(`SELECT d.id, d.mat_hang_id FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id WHERE k.me_sx_id = :m AND k.loai = 'thu_hoi'
        AND k.trang_thai = 'da_ghi' AND d.huong = 'ra'`, { m: me.id }, t);
      for (const r of ra) { const x = (sg.dong || []).find((d: any) => d.mat_hang_id === Number(r.mat_hang_id) && d.vai_tro === 'tp'); if (Number(x?.he_so_gia) > 0) hs[r.id] = Number(x.he_so_gia); }
      if (Object.keys(hs).length) v.he_so = hs;
    }
    const r = await chotGoc(ctx, t);
    if (v.chap_nhan_chenh) {
      const m2 = await p.khoa('me_sx', me.id, t);
      await m2.update({ ghi_chu: [m2.ghi_chu, `Chốt chấp nhận chênh: ${v.ly_do_chenh} (${p.nguoi(ctx)})`].filter(Boolean).join(' | ') }, { transaction: t, hooks: false });
    }
    return r;
  };

  // ---------------- ĐỀ XUẤT MÃ HÀNG ----------------
  H['de_xuat_mat_hang:duyet'] = async (ctx, t) => {
    canQuyen(ctx, 'duyệt mã hàng mới');
    const dx = await p.khoa('de_xuat_mat_hang', id(ctx), t);
    if (dx.trang_thai !== 'cho_duyet') loi('Đề xuất đã xử lý.');
    const v = val(ctx);
    let mh: any;
    if (v.mat_hang_id) mh = await bang('mat_hang').findByPk(v.mat_hang_id, { transaction: t });
    else {
      if (!v.ma) loi('Nhập mã chính thức (hoặc chọn mã đã có để ghép).');
      if (await bang('mat_hang').findOne({ where: { ma: v.ma }, transaction: t })) loi(`Mã ${v.ma} đã có: chọn ghép vào mã đó.`);
      mh = await bang('mat_hang').create({ ma: v.ma, ten: v.ten || dx.ten, dvt_ton: v.dvt_ton || 'kg', kg_bao: v.kg_bao ?? null, loai_hang: v.loai_hang || null,
        kg_moi_dvt: v.kg_moi_dvt ?? null, kg_dvt_can_cu: v.kg_dvt_can_cu ?? null }, { transaction: t });
    }
    if (!mh) loi('Không thấy mã hàng.');
    await dx.update({ trang_thai: 'da_duyet', mat_hang_id: mh.id, nguoi_duyet: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true, mat_hang_id: mh.id, ma: mh.ma };
  };
  H['de_xuat_mat_hang:tuChoi'] = async (ctx, t) => {
    canQuyen(ctx, 'từ chối mã hàng');
    const dx = await p.khoa('de_xuat_mat_hang', id(ctx), t);
    if (dx.trang_thai !== 'cho_duyet') loi('Đề xuất đã xử lý.');
    if (!lyDo(ctx)) loi('Ghi lý do.');
    await dx.update({ trang_thai: 'tu_choi', ly_do: lyDo(ctx), nguoi_duyet: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- HÀNG GỬI GIA CÔNG ----------------
  H['sx_ho_so_gia_cong:nhanHang'] = async (ctx, t) => {
    canQuyen(ctx, 'nhận hàng gửi gia công');
    const hs = await p.khoa('sx_ho_so_gia_cong', id(ctx), t);
    if (hs.trang_thai !== 'mo') loi('Hồ sơ đã quyết toán.');
    const v = val(ctx);
    if (v.request_id) {
      const co = await bang('phieu_kho').findOne({ where: { request_id: v.request_id }, transaction: t });
      if (co) return { ok: true, da_nhan_truoc: true, so: co.so };
    }
    const ds = (v.dong || []).filter((d: any) => Number(d.so_kg) > 0);
    if (!ds.length) loi('Nhập hàng nhận (theo cân thực).');
    // Hàng của bên gửi: vào KHO HÀNG GỬI, giá trị sở hữu 0 (không phải hàng của bên nhận); không bán, không tạo công nợ / doanh thu.
    const pk = await bang('phieu_kho').create({ loai: 'nhap', ngay: v.ngay || homNay(), kho_id: hs.kho_id, ho_so_gia_cong_id: hs.id, request_id: v.request_id || null,
      ghi_chu: `Nhận hàng gửi gia công ${hs.so}${v.ghi_chu ? ': ' + v.ghi_chu : ''}` }, { transaction: t });
    for (const d of ds) {
      const x = await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), so_bao: d.so_bao ?? null }, { transaction: t });
      await p.ghiSo(t, { ngay: pk.ngay, kho_id: hs.kho_id, mat_hang_id: d.mat_hang_id, so_luong: kg(d.so_kg), so_bao: kg(d.so_bao), loai: 'nhan_gia_cong', chung_tu: pk.so,
        nguon: 'phieu_kho_dong', nguon_id: x.id, gia_tri: 0 });
      await x.update({ don_gia: 0, trang_thai_gia: 'co_gia' }, { transaction: t, hooks: false });
    }
    await pk.update({ trang_thai: 'da_ghi', ghi_boi: p.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
    return { ok: true, so: pk.so };
  };
  H['sx_ho_so_gia_cong:traHang'] = async (ctx, t) => {
    canQuyen(ctx, 'trả hàng gia công');
    const hs = await p.khoa('sx_ho_so_gia_cong', id(ctx), t);
    const v = val(ctx);
    const pk = await bang('phieu_kho').create({ loai: 'xuat', ngay: v.ngay || homNay(), kho_id: hs.kho_id, ho_so_gia_cong_id: hs.id, request_id: v.request_id || null,
      ghi_chu: `Trả hàng gia công ${hs.so} cho bên gửi${v.ghi_chu ? ': ' + v.ghi_chu : ''}` }, { transaction: t });
    for (const d of (v.dong || []).filter((x: any) => Number(x.so_kg) > 0)) await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg) }, { transaction: t });
    await goi('phieu_kho:ghiSo', ctx, t, pk.id);
    return { ok: true, so: pk.so };
  };
  H['sx_ho_so_gia_cong:xacNhanSoHuu'] = async (ctx, t) => {
    canQuyen(ctx, 'xác nhận chủ sở hữu');
    const hs = await p.khoa('sx_ho_so_gia_cong', id(ctx), t);
    const v = val(ctx);
    if (!v.chu_so_huu_id || !v.can_cu) loi('Chọn chủ sở hữu và ghi căn cứ (hợp đồng / biên bản).');
    await hs.update({ chu_so_huu_id: v.chu_so_huu_id, can_cu: [hs.can_cu, v.can_cu].filter(Boolean).join(' | ') }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['sx_ho_so_gia_cong:baoCao'] = async (ctx, t) => {
    const hs = await bang('sx_ho_so_gia_cong').findByPk(id(ctx), { transaction: t });
    if (!hs) loi('Không thấy hồ sơ.');
    const ds = await p.sql(`SELECT m.ma, m.ten,
        COALESCE(SUM(s.so_kg) FILTER (WHERE s.loai = 'nhan_gia_cong'),0) AS da_nhan,
        COALESCE(-SUM(s.so_kg) FILTER (WHERE s.loai = 'cap_nvl'),0) AS da_dung,
        COALESCE(SUM(s.so_kg) FILTER (WHERE s.loai IN ('thu_hoi_ra','thu_hoi_phu_pham')),0) AS da_ra,
        COALESCE(-SUM(s.so_kg) FILTER (WHERE s.loai = 'xuat'),0) AS da_tra, COALESCE(SUM(s.so_kg),0) AS dang_giu
      FROM so_kho s JOIN mat_hang m ON m.id = s.mat_hang_id WHERE s.kho_id = :k GROUP BY m.ma, m.ten ORDER BY m.ma`, { k: hs.kho_id }, t);
    const [me] = await p.sql(`SELECT COUNT(*)::int AS n FROM me_sx WHERE ho_so_gia_cong_id = :h AND trang_thai <> 'da_huy'`, { h: hs.id }, t);
    return { ok: true, ho_so: hs.so, so_me: me.n, chu_so_huu_xac_nhan: hs.chu_so_huu_id || null, hang: ds };
  };
  void tien;
}

export function hookNhaMay041(p: any) {
  const db = p.db;
  db.on('mau_sx_phien_ban.beforeCreate', async (m: any, o: any) => {
    if (o?.hooks === false) return;
    m.set('trang_thai', 'de_xuat');
    const [x] = await p.sql(`SELECT COALESCE(MAX(phien_ban),0) + 1 AS n FROM mau_sx_phien_ban WHERE mau_sx_id = :m`, { m: m.get('mau_sx_id') }, o?.transaction);
    m.set('phien_ban', Number(x?.n || 1));
  });
  db.on('mau_sx_phien_ban.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    if (m.previous('trang_thai') !== 'de_xuat' || m.changed('trang_thai')) loi('Phiên bản đã duyệt / ngừng không sửa được: tạo phiên bản mới (mẻ cũ giữ định mức cũ).');
  });
  db.on('mau_sx_phien_ban.beforeDestroy', (m: any) => { if (m.get('trang_thai') !== 'de_xuat') loi('Không xóa phiên bản đã duyệt.'); });
  const khoaDong = async (m: any, o: any) => {
    if (o?.hooks === false) return;
    const pb = await p.bang('mau_sx_phien_ban').findByPk(m.get('mau_sx_phien_ban_id'), { transaction: o?.transaction });
    if (pb && pb.trang_thai !== 'de_xuat') loi('Định mức đã duyệt không sửa được: tạo phiên bản mới.');
  };
  db.on('mau_sx_dong.beforeSave', khoaDong);
  db.on('mau_sx_dong.beforeDestroy', khoaDong);
  db.on('de_xuat_mat_hang.beforeCreate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    m.set('trang_thai', 'cho_duyet');
    const u = o?.context?.state?.currentUser;
    if (u && !m.get('nguoi_de_xuat')) m.set('nguoi_de_xuat', u.nickname || u.email || String(u.id));
  });
  db.on('de_xuat_mat_hang.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    if (m.previous('trang_thai') !== 'cho_duyet' || m.changed('trang_thai') || m.changed('mat_hang_id')) loi('Đề xuất chỉ duyệt / từ chối qua thao tác.');
  });
  db.on('sx_ho_so_gia_cong.beforeSave', async (m: any, o: any) => {
    if (o?.hooks === false) return;
    const k = await p.bang('kho').findByPk(m.get('kho_id'), { transaction: o?.transaction });
    if (!k || k.loai_kho !== 'hang_gui') loi('Hồ sơ gia công phải gắn KHO HÀNG GỬI riêng (loại kho "hàng gửi gia công").');
    if (m.get('ben_gui_id') === m.get('ben_nhan_id')) loi('Bên gửi và bên nhận gia công phải khác nhau.');
    if (m.changed('chu_so_huu_id') && !m.isNewRecord) loi('Chủ sở hữu chỉ xác nhận qua thao tác có căn cứ.');
    if (m.isNewRecord && m.get('chu_so_huu_id')) loi('Chủ sở hữu chỉ xác nhận qua thao tác có căn cứ.');
  });
  for (const b of ['sx_doi_chieu', 'sx_giai_trinh', 'sx_nguon_lo']) {
    db.on(`${b}.beforeCreate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ tạo qua thao tác sản xuất.'); });
    db.on(`${b}.beforeUpdate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ thay đổi qua thao tác sản xuất.'); });
    db.on(`${b}.beforeDestroy`, () => loi('Không xóa (giữ lịch sử).'));
  }
}
