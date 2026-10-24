/**
 * 0.4.0 Trung tâm dữ liệu (Go-Live từ hai nguồn đang dùng):
 *   (1) Sheet "Quản lý nhà máy Phú Thọ" (nhận hàng, sản xuất, chuyển kho, bán tại NM, tồn đầu kỳ);
 *   (2) "Sổ ghi nhận bán hàng – kho – công nợ" (đơn bán, trả lại, nhập kho, chuyển kho – xuất khác, thu tiền, DM hàng có tồn đầu).
 * Quy trình: nạp tệp → bản ghi staging (chống trùng theo nội dung) → ánh xạ mã (kho / hàng / khách / công ty / quỹ, có gợi ý)
 *   → phân loại "Nhập được / Chưa đủ căn cứ / Có thể trùng / Bị chặn / Trước mốc" → ghép chuyến chuyển giữa hai nguồn (một chuyến = một chứng từ)
 *   → ghi sổ từng nhóm trong điểm lưu (savepoint) — nhóm lỗi không làm hỏng nhóm khác, không ghi hai lần (chung_tu_dich + khóa).
 * Không đọc nguồn như lệnh; mọi dữ liệu nguồn chỉ là dữ liệu.
 */
import crypto from 'crypto';
import { Op, Transaction } from 'sequelize';
import { homNay, kg, loi, tien } from '../tienich';
import { boDau, cot, docTep, ngayVN, soVN, timTieuDe } from './tep';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;
type Dong = Record<string, any>;

/** Mô tả trang tính nguồn: từ khóa nhận diện tiêu đề + cách lấy cột. */
const MAU: Record<string, Record<string, { nv: string; batBuoc: string[][]; cot: Record<string, string[]>; keoXuong?: string[] }>> = {
  nha_may: {
    'nhan hang': { nv: 'nhan_hang', batBuoc: [['so phieu'], ['kho nhan'], ['ma hang']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu'], loai: ['loai nhan'], cong_ty: ['hang cua cong ty'], ncc: ['nha cung cap'], kho: ['kho nhan'], ma_hang: ['ma hang'],
        ten_hang: ['ten hang'], dvt: ['dvt'], sl_ct: ['sl theo chung tu'], so_luong: ['sl thuc nhan'], so_kg: ['so kg can'], ghi_chu: ['ghi chu'] } },
    'san xuat': { nv: 'san_xuat', batBuoc: [['so phieu sx'], ['dong'], ['ma hang']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu sx'], day_chuyen: ['day chuyen'], dong: ['dong'], kho: ['kho lay ra'], ma_hang: ['ma hang'], ten_hang: ['ten hang'],
        dvt: ['dvt'], so_luong: ['so luong'], so_kg: ['so kg'], lo: ['lo'], ghi_chu: ['ghi chu'] } },
    'chuyen kho': { nv: 'chuyen_kho', batBuoc: [['so phieu'], ['tu kho'], ['den kho']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu'], kho_di: ['tu kho'], kho_den: ['den kho'], ma_hang: ['ma hang'], ten_hang: ['ten hang'], dvt: ['dvt'],
        so_luong: ['so luong'], so_kg: ['so kg'], lo: ['lo'], xe: ['xe'], ghi_chu: ['ghi chu'] } },
    'ban tai nm': { nv: 'ban_nm', batBuoc: [['so phieu'], ['kho xuat'], ['ma hang']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu'], cong_ty: ['cong ty ban'], khach: ['ma khach'], ten_khach: ['ten khach'], kho: ['kho xuat'], ma_hang: ['ma hang'],
        ten_hang: ['ten hang'], dvt: ['dvt'], so_luong: ['so luong'], so_kg: ['so kg'], don_gia: ['don gia'], hoa_don: ['lay hoa don'], thanh_toan: ['thanh toan'], ghi_chu: ['ghi chu'] } },
    'ton dau ky': { nv: 'ton_dau', batBuoc: [['ma kho'], ['ma hang'], ['so luong']],
      cot: { kho: ['ma kho'], ten_kho: ['kho'], ma_hang: ['ma hang'], ten_hang: ['ten hang'], dvt: ['dvt'], so_luong: ['so luong ton', 'so luong'] } },
    'kiem ke': { nv: 'kiem_ke', batBuoc: [['kho'], ['ma hang'], ['sl dem']],
      cot: { ngay: ['ngay'], kho: ['kho'], ma_hang: ['ma hang'], so_luong: ['thieu (ghi am)', 'thieu'], sl_dem: ['sl dem'], ly_do: ['ly do'], ghi_chu: ['ghi chu'] } },
  },
  ban_hang: {
    'don ban': { nv: 'don_ban', batBuoc: [['so phieu xk'], ['mat hang'], ['so luong']], keoXuong: ['ngay', 'so_ct', 'cong_ty', 'kho', 'khach', 'thanh_toan', 'xuat_hd'],
      cot: { ngay: ['ngay'], so_ct: ['so phieu xk'], cong_ty: ['cong ty'], kho: ['kho xuat'], khach: ['khach hang'], thanh_toan: ['thanh toan'], ghi_chu: ['ghi chu'],
        xuat_hd: ['xuat hd gtgt'], ma_hang: ['mat hang'], so_luong: ['so luong'], don_gia: ['don gia da bao gom thue', 'don gia'], thue_suat: ['thue suat'],
        sl_thuc: ['sl thuc xuat'] } },
    'tra lai': { nv: 'tra_lai', batBuoc: [['so phieu xk goc'], ['mat hang'], ['sl tra']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu nhan tra'], so_goc: ['so phieu xk goc'], cong_ty: ['cong ty'], kho: ['kho nhap lai'], khach: ['khach hang'],
        ma_hang: ['mat hang'], so_luong: ['sl tra'], don_gia: ['don gia chua thue'], ly_do: ['ly do'] } },
    'nhap kho': { nv: 'nhap_kho', batBuoc: [['so phieu nhap'], ['kho nhap'], ['mat hang']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu nhap'], cong_ty: ['cong ty'], kho: ['kho nhap'], loai: ['loai nhap'], ncc: ['nha cung cap'], ma_hang: ['mat hang'],
        so_luong: ['so luong'], don_gia: ['don gia chua thue'], co_hd: ['co hoa don'], thue_suat: ['thue suat'], so_hd: ['so hd nguoi ban'], thanh_toan: ['thanh toan'], ghi_chu: ['ghi chu'] } },
    'chuyen kho': { nv: 'chuyen_kho', batBuoc: [['tu kho'], ['den kho'], ['mat hang']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu'], kho_di: ['tu kho'], kho_den: ['den kho'], loai: ['loai (xuat khac)', 'loai'], ma_hang: ['mat hang'], so_luong: ['so luong'],
        ghi_chu: ['ghi chu'], dvt: ['dvt'] } },
    'thu tien': { nv: 'thu_tien', batBuoc: [['so phieu thu'], ['so tien'], ['hinh thuc']],
      cot: { ngay: ['ngay'], so_ct: ['so phieu thu'], cong_ty: ['cong ty'], khach: ['khach hang'], so_tien: ['so tien'], hinh_thuc: ['hinh thuc'],
        cho_xk: ['cho phieu xk so'], nguoi_nop: ['nguoi nop'], ghi_chu: ['ghi chu'] } },
    'dm hang': { nv: 'ton_dau_bh', batBuoc: [['ma hang'], ['ton dau']], cot: { ma_hang: ['ma hang'], ten_hang: ['ten hang'], dvt: ['dvt'] } },
  },
};
const timMau = (he: string, ten: string) => {
  const b = boDau(ten);
  const m = MAU[he] || {};
  return Object.entries(m).find(([k]) => b === k || b.startsWith(k))?.[1];
};
/** "MÃ | tên" → MÃ. */
const ma = (s: any) => String(s ?? '').split('|')[0].trim();
const coHuy = (r: Dong) => /\bhuy\b|\bhủy\b|đã hủy|da huy/i.test(`${boDau(r.ghi_chu)} ${boDau(r.so_ct)} ${boDau(r.ly_do)}`);

export function dangKyNguon(p: any, H: H, h: any) {
  const { id, val } = h;
  const bang = (n: string) => p.bang(n);
  const canQuyen = (ctx: any) => { if (!p.xemGia(ctx)) loi('Chỉ kế toán / quản lý dùng Trung tâm dữ liệu.'); };
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);
  /** Điểm lưu: lỗi trong fn chỉ hoàn tác phần của nhóm đó. */
  const diemLuu = async (t: Transaction, fn: (t2: Transaction) => Promise<any>) => {
    const sp = await p.db.sequelize.transaction({ transaction: t });
    try { const r = await fn(sp); await sp.commit(); return { ok: true, r }; } catch (e: any) { await sp.rollback(); return { ok: false, loi: e?.message || String(e) }; }
  };

  // ---------------- NẠP ----------------
  H['nguon_tep:nap'] = async (ctx, t) => {
    canQuyen(ctx);
    const v = val(ctx);
    if (!['nha_may', 'ban_hang'].includes(v.he_thong)) loi('Chọn nguồn: sheet nhà máy / sổ bán hàng.');
    const { checksum, trang } = docTep(v, 40);
    const daCo = await bang('nguon_tep').findOne({ where: { checksum }, transaction: t });
    if (daCo) return { ok: true, da_nap_truoc: true, id: daCo.id };
    const tep = await bang('nguon_tep').create({ he_thong: v.he_thong, ten_tep: v.ten_tep || 'tep', checksum, thoi_diem: new Date().toISOString(),
      nguoi_nap: p.nguoi(ctx), ghi_chu: v.ghi_chu || null }, { transaction: t, hooks: false });
    const thongKe: Record<string, { doc: number; moi: number; da_co: number }> = {};
    for (const tr of trang) {
      const mau = timMau(v.he_thong, tr.ten);
      if (!mau) continue;
      const i = timTieuDe(tr.dong, mau.batBuoc);
      if (i < 0) continue;
      const td = tr.dong[i];
      const viTri: Record<string, number> = {};
      for (const [k, tu] of Object.entries(mau.cot)) viTri[k] = cot(td, ...tu);
      // DM hàng của sổ bán hàng: các cột "Tồn đầu 01/10 <kho>".
      const cotTon = mau.nv === 'ton_dau_bh' ? td.map((c, j) => ({ j, kho: /ton dau/.test(boDau(c)) ? String(c).replace(/^.*?(Kho)/i, 'Kho').trim() : '' })).filter((x) => x.kho) : [];
      const tk = (thongKe[tr.ten] = { doc: 0, moi: 0, da_co: 0 });
      const lap: Record<string, number> = {};
      let truoc: Dong = {};
      for (const [j, r] of tr.dong.slice(i + 1).entries()) {
        const d: Dong = {};
        for (const [k, c] of Object.entries(viTri)) d[k] = c >= 0 ? String(r[c] ?? '').trim() : '';
        if (mau.keoXuong) {
          if (!d.ngay && !d.so_ct && d.ma_hang) for (const k of mau.keoXuong) d[k] = d[k] || truoc[k] || '';
          else truoc = d;
        }
        const ds: Dong[] = [];
        if (mau.nv === 'ton_dau_bh') {
          for (const c of cotTon) { const sl = soVN(r[c.j]); if (sl) ds.push({ ...d, kho: c.kho, so_luong: String(sl) }); }
        } else ds.push(d);
        for (const x of ds) {
          if (!x.ma_hang && !x.so_luong && !x.so_kg && !x.so_tien) continue;
          if (['san_xuat', 'chuyen_kho', 'nhan_hang', 'ban_nm', 'don_ban', 'nhap_kho', 'thu_tien', 'tra_lai'].includes(mau.nv) && !ngayVN(x.ngay)) continue;
          tk.doc++;
          const noiDung = JSON.stringify(x);
          const bam = crypto.createHash('sha1').update(noiDung).digest('hex').slice(0, 20);
          lap[bam] = (lap[bam] || 0) + 1;
          const khoa = `${v.he_thong}|${boDau(tr.ten)}|${bam}|${lap[bam]}`;
          const co = await bang('nguon_ban_ghi').findOne({ where: { khoa }, transaction: t });
          if (co) { tk.da_co++; continue; }
          await bang('nguon_ban_ghi').create({ tep_id: tep.id, he_thong: v.he_thong, trang_tinh: tr.ten, dong: i + 2 + j, khoa, loai_nv: mau.nv,
            ngay: ngayVN(x.ngay), so_ct: x.so_ct || null, du_lieu: noiDung, ket_qua: null }, { transaction: t, hooks: false });
          tk.moi++;
        }
      }
    }
    const tong = Object.values(thongKe).reduce((a, x) => a + x.moi, 0);
    await tep.update({ so_ban_ghi: tong }, { transaction: t, hooks: false });
    if (!Object.keys(thongKe).length) loi('Không nhận ra trang tính nào của nguồn đã chọn (kiểm tra đúng tệp / đúng nguồn).');
    await goi('nguon_tep:goiYAnhXa', ctx, t, tep.id);
    return { ok: true, id: tep.id, trang_tinh: thongKe, so_moi: tong };
  };

  // ---------------- ÁNH XẠ MÃ ----------------
  const khoaAx = (he: string, loai: string, m: string) => `${he}|${loai}|${boDau(m)}`;
  const cacheAx: Record<string, any> = {};
  const anhXa = async (t: Transaction, he: string, loai: string, m: string) => {
    if (!m) return null;
    const k = khoaAx(he, loai, m);
    if (!(k in cacheAx)) {
      const r = await bang('anh_xa_ma').findOne({ where: { khoa: k }, transaction: t });
      cacheAx[k] = r && Number(r.dich_id) > 0 ? Number(r.dich_id) : null;
    }
    return cacheAx[k];
  };
  /** Liệt kê mã nguồn dùng trong staging; tạo dòng ánh xạ còn thiếu và tự gợi ý khi khớp mã / tên đúng. */
  H['nguon_tep:goiYAnhXa'] = async (ctx, t) => {
    canQuyen(ctx);
    const where: any = { [Op.or]: [{ ket_qua: null }, { ket_qua: ['chua_du', 'nhap_duoc', 'co_the_trung', 'bi_chan'] }] };
    if (id(ctx)) where.tep_id = id(ctx);
    const ds = await bang('nguon_ban_ghi').findAll({ where, transaction: t, attributes: ['he_thong', 'loai_nv', 'du_lieu'] });
    const can = new Map<string, { he: string; loai: string; m: string; ten: string }>();
    const them = (he: string, loai: string, m: string, ten = '') => { if (m) can.set(khoaAx(he, loai, m), { he, loai, m, ten }); };
    for (const r of ds) {
      const d = JSON.parse(r.du_lieu || '{}');
      for (const k of ['kho', 'kho_di', 'kho_den']) them(r.he_thong, 'kho', d[k], d.ten_kho);
      if (d.ma_hang) them(r.he_thong, 'mat_hang', ma(d.ma_hang), d.ten_hang || String(d.ma_hang).split('|')[1] || '');
      if (d.khach) them(r.he_thong, 'khach_hang', ma(d.khach), d.ten_khach || String(d.khach).split('|')[1] || '');
      else if (d.ten_khach && /khach le/.test(boDau(d.ten_khach))) them(r.he_thong, 'khach_hang', 'Khách lẻ', 'Khách lẻ');
      if (d.cong_ty) them(r.he_thong, 'don_vi', d.cong_ty);
      if (r.loai_nv === 'thu_tien' && d.hinh_thuc) them(r.he_thong, 'quy', `${d.cong_ty}|${d.hinh_thuc}`, d.hinh_thuc);
      if (d.ncc && r.loai_nv === 'nhap_kho') them(r.he_thong, 'nha_cung_cap', ma(d.ncc), String(d.ncc).split('|')[1] || '');
    }
    let moi = 0, tu_dong = 0;
    for (const [k, x] of can) {
      const co = await bang('anh_xa_ma').findOne({ where: { khoa: k }, transaction: t });
      if (co) continue;
      let dich: any = null;
      const b = { kho: 'kho', mat_hang: 'mat_hang', khach_hang: 'khach_hang', don_vi: 'don_vi', nha_cung_cap: 'nha_cung_cap' }[x.loai as string];
      if (b) {
        const [r] = await p.sql(`SELECT id, ma FROM ${b} WHERE lower(ma) = lower(:m) ${['kho', 'don_vi'].includes(b) ? 'OR lower(ten) = lower(:m)' : ''} ORDER BY id LIMIT 1`, { m: x.m }, t);
        dich = r || null;
        if (!dich && b === 'khach_hang' && /^khach le$/.test(boDau(x.ten || x.m))) [dich] = await p.sql(`SELECT id, ma FROM khach_hang WHERE ma = 'KHACH-LE'`, {}, t);
      }
      await bang('anh_xa_ma').create({ he_thong: x.he, loai: x.loai, ma_nguon: x.m, ten_nguon: x.ten || null, dich_id: dich?.id || 0, dich_ma: dich?.ma || null, khoa: k,
        ghi_chu: dich ? 'Tự khớp theo mã / tên' : null }, { transaction: t, hooks: false });
      moi++;
      if (dich) tu_dong++;
    }
    return { ok: true, them: moi, tu_khop: tu_dong };
  };
  H['anh_xa_ma:dat'] = async (ctx, t) => {
    canQuyen(ctx);
    const a = await p.khoa('anh_xa_ma', id(ctx), t);
    const v = val(ctx);
    const b = { kho: 'kho', mat_hang: 'mat_hang', khach_hang: 'khach_hang', don_vi: 'don_vi', nha_cung_cap: 'nha_cung_cap', quy: 'quy' }[a.loai as string];
    if (!b) loi('Loại ánh xạ không hợp lệ.');
    let dich: any = null;
    if (v.dich_id) dich = await bang(b).findByPk(v.dich_id, { transaction: t });
    else if (v.dich_ma) dich = await bang(b).findOne({ where: { ma: v.dich_ma }, transaction: t });
    if (!dich && !v.bo_trong) loi('Không tìm thấy mã đích.');
    await a.update({ dich_id: dich?.id || 0, dich_ma: dich?.ma || null, ghi_chu: v.ghi_chu || a.ghi_chu }, { transaction: t, hooks: false });
    delete cacheAx[a.khoa];
    return { ok: true };
  };

  // ---------------- PHÂN LOẠI ----------------
  /** Chuẩn hóa một bản ghi theo ánh xạ; trả về {chuan, van_de}. */
  const chuanHoa = async (t: Transaction, r: any) => {
    const d = JSON.parse(r.du_lieu || '{}');
    const he = r.he_thong;
    const vd: string[] = [];
    const c: Dong = { ngay: ngayVN(d.ngay), so_ct: d.so_ct || null };
    const lay = async (loai: string, m: string, ten: string, bat = true) => {
      if (!m) { if (bat) vd.push(`thiếu ${ten}`); return null; }
      const x = await anhXa(t, he, loai, m);
      if (!x && bat) vd.push(`chưa ánh xạ ${ten} "${m}"`);
      return x;
    };
    if (['nhan_hang', 'san_xuat', 'ban_nm', 'ton_dau', 'kiem_ke', 'don_ban', 'nhap_kho', 'tra_lai', 'ton_dau_bh'].includes(r.loai_nv)) c.kho_id = await lay('kho', d.kho, 'kho');
    if (r.loai_nv === 'chuyen_kho') {
      c.kho_di_id = await lay('kho', d.kho_di, 'kho đi');
      c.kho_den_id = d.kho_den ? await lay('kho', d.kho_den, 'kho đến') : null;
      c.loai_xuat = d.loai || null;
      if (!d.kho_den && !d.loai) vd.push('xuất khác chưa chọn loại');
    }
    if (r.loai_nv !== 'thu_tien') {
      c.mat_hang_id = await lay('mat_hang', ma(d.ma_hang), 'mã hàng');
      if (!d.ma_hang && d.ghi_chu) vd.push(`(${String(d.ghi_chu).slice(0, 80)})`);
      const sl = soVN(d.so_kg) ?? soVN(d.so_luong);
      c.so_luong = sl === null ? null : kg(sl);
      if (r.loai_nv === 'don_ban' && soVN(d.sl_thuc)) c.sl_thuc = kg(soVN(d.sl_thuc));
      if (r.loai_nv !== 'kiem_ke' && !(c.so_luong && c.so_luong > 0)) vd.push('số lượng trống / ≤ 0');
      if (d.don_gia) c.don_gia = soVN(d.don_gia);
    }
    if (r.loai_nv === 'thu_tien' && !d.cong_ty && d.cho_xk) {
      // Thiếu công ty nhận tiền nhưng ghi "cho phiếu XK số": lấy công ty của đúng MỘT phiếu XK cùng số trong sổ (căn cứ chứng từ, không đoán).
      const ct = await p.sql(`SELECT DISTINCT du_lieu::json->>'cong_ty' AS c FROM nguon_ban_ghi WHERE he_thong = :h AND loai_nv = 'don_ban' AND so_ct = :s`,
        { h: he, s: String(d.cho_xk).trim() }, t);
      const ds = ct.map((x: any) => x.c).filter(Boolean);
      if (ds.length === 1) { d.cong_ty = ds[0]; c.cong_ty_suy_ra = `theo phiếu XK ${d.cho_xk}`; }
      else if (ds.length > 1) vd.push(`phiếu XK ${d.cho_xk} có ở nhiều công ty — ghi rõ công ty nhận tiền`);
    }
    if (['ban_nm', 'don_ban', 'nhap_kho', 'thu_tien', 'tra_lai'].includes(r.loai_nv)) c.don_vi_id = await lay('don_vi', d.cong_ty, 'công ty');
    if (['ban_nm', 'don_ban', 'thu_tien', 'tra_lai'].includes(r.loai_nv)) c.khach_id = await lay('khach_hang', ma(d.khach) || (d.ten_khach && /khach le/.test(boDau(d.ten_khach)) ? 'Khách lẻ' : ''), 'khách');
    if (r.loai_nv === 'thu_tien') {
      c.so_tien = tien(soVN(d.so_tien));
      if (!(c.so_tien > 0)) vd.push('số tiền trống');
      c.quy_id = await lay('quy', `${d.cong_ty}|${d.hinh_thuc}`, 'quỹ / tài khoản (theo hình thức)');
      c.tien_mat = /tien mat/.test(boDau(d.hinh_thuc));
      c.cho_xk = d.cho_xk || null;
    }
    if (r.loai_nv === 'don_ban') { c.gom_vat = true; c.xuat_hd = /^co$/.test(boDau(d.xuat_hd)); c.thue = d.thue_suat || null; }
    if (r.loai_nv === 'san_xuat') c.dong = boDau(d.dong);
    if (r.loai_nv === 'tra_lai') { c.so_goc = d.so_goc || null; c.ly_do = d.ly_do || null; if (!d.so_goc) vd.push('thiếu số phiếu XK gốc'); }
    return { c, vd, d };
  };

  /** values: {moc: 'yyyy-mm-dd' (ngày Go-Live: trước mốc = đã nằm trong số dư đầu kỳ), tep_id?} */
  H['nguon_tep:phanLoai'] = async (ctx, t) => {
    canQuyen(ctx);
    const v = val(ctx);
    const moc = v.moc || (await p.sql(`SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_moc_golive'`, {}, t))[0]?.gia_tri;
    if (!moc) loi('Nhập ngày mốc Go-Live (ngày đầu tiên ghi phát sinh trên hệ thống).');
    const where: any = { [Op.or]: [{ ket_qua: null }, { ket_qua: ['nhap_duoc', 'chua_du', 'co_the_trung', 'bi_chan', 'truoc_moc'] }] };
    const teps = v.tep_ids || (v.tep_id ? [v.tep_id] : null);
    if (teps) where.tep_id = teps;
    const ds = await bang('nguon_ban_ghi').findAll({ where, transaction: t, order: [['id', 'ASC']] });
    const bao: Record<string, Record<string, number>> = {};
    for (const r of ds) {
      const { c, vd, d } = await chuanHoa(t, r);
      let kq = 'nhap_duoc';
      if (['ton_dau', 'ton_dau_bh'].includes(r.loai_nv)) kq = vd.length ? 'chua_du' : 'nhap_duoc';
      else if (c.ngay && c.ngay < moc) kq = 'truoc_moc';
      else if (coHuy(d)) { kq = 'bi_chan'; vd.unshift('chứng từ ghi HỦY'); }
      else if (r.loai_nv === 'thu_tien' && /ghi no/.test(boDau(d.hinh_thuc))) { kq = 'bo_qua'; vd.unshift('hình thức "ghi nợ" — không phải tiền thực thu'); }
      else if (vd.length) kq = 'chua_du';
      else if (isChuyenGhep(r, c)) kq = 'co_the_trung';
      await r.update({ ket_qua: kq, van_de: vd.join('; ') || null, chuan_hoa: JSON.stringify(c) }, { transaction: t, hooks: false });
      (bao[r.loai_nv] = bao[r.loai_nv] || {})[kq] = (bao[r.loai_nv]?.[kq] || 0) + 1;
    }
    // Cùng chứng từ xuất hiện ở HAI tệp khác nhau của cùng nguồn (nạp lại bản đã sửa): không tự chọn — đánh dấu để người dùng bỏ qua bản sai.
    const trungTep = await p.sql(`WITH x AS (SELECT id, tep_id, he_thong || '|' || loai_nv || '|' || COALESCE(so_ct,'') || '|' || COALESCE(ngay::text,'') || '|' ||
        COALESCE(du_lieu::json->>'ma_hang','') || '|' || COALESCE(du_lieu::json->>'kho','') || '|' || COALESCE(du_lieu::json->>'kho_di','') || '|' ||
        COALESCE(du_lieu::json->>'kho_den','') || '|' || COALESCE(du_lieu::json->>'khach','') AS k, ket_qua FROM nguon_ban_ghi
        WHERE COALESCE(ket_qua,'') NOT IN ('bo_qua','truoc_moc') AND loai_nv NOT IN ('ton_dau','ton_dau_bh'))
      SELECT a.id, MIN(b.id) AS khac, BOOL_OR(b.ket_qua = 'da_ghi') AS da_ghi FROM x a JOIN x b ON a.k = b.k AND a.tep_id <> b.tep_id
      WHERE a.ket_qua IN ('nhap_duoc','chua_du','co_the_trung','bi_chan') GROUP BY a.id`, {}, t);
    for (const x of trungTep) {
      await bang('nguon_ban_ghi').update({ ket_qua: 'co_the_trung', van_de: x.da_ghi
        ? `Cùng chứng từ với bản ghi #${x.khac} ĐÃ GHI SỔ (tệp khác) — nếu là bản sửa: hủy chứng từ cũ rồi ghi lại, nếu trùng: bỏ qua`
        : `Cùng chứng từ với bản ghi #${x.khac} ở tệp khác — giữ một bản, bỏ qua bản kia` },
        { where: { id: x.id }, transaction: t, hooks: false });
    }
    if (trungTep.length) bao.trung_giua_tep = { co_the_trung: trungTep.length };
    const ghep = await goi('nguon_tep:timTrung', ctx, t, null, { tep_ids: teps });
    return { ok: true, moc, bao_cao: bao, ghep };
  };
  /** Chuyển liên quan "Kho nhà máy ↔ Hà Nội" phải ghép hai nguồn trước khi ghi (tránh ghi hai lần một chuyến). */
  const laKhoTg = async (t: Transaction, khoId: any) => !!khoId && !!(await bang('kho').findByPk(khoId, { transaction: t }))?.trung_chuyen;
  const khoNm = async (t: Transaction, khoId: any) => {
    if (!khoId) return false;
    const k = await bang('kho').findByPk(khoId, { transaction: t });
    return k?.loai_kho === 'nha_may' || /nha may/.test(boDau(k?.ten));
  };
  const isChuyenGhep = (r: any, c: Dong) => (r.loai_nv === 'chuyen_kho' && r.he_thong === 'nha_may' && /van chuyen/.test(boDau(JSON.parse(r.du_lieu).kho_den)))
    || (r.loai_nv === 'chuyen_kho' && r.he_thong === 'ban_hang' && /nha may/.test(boDau(JSON.parse(r.du_lieu).kho_di)) && !!c.kho_den_id)
    || (r.loai_nv === 'chuyen_kho' && r.he_thong === 'ban_hang' && /nha may/.test(boDau(JSON.parse(r.du_lieu).kho_den)))
    || (r.loai_nv === 'nhan_hang' && /ha noi/.test(boDau(JSON.parse(r.du_lieu).loai)));

  /** Ghép: (A) NM xuất → đang vận chuyển  ↔  sổ BH "Kho nhà máy → kho X";  (B) sổ BH "kho X → Kho nhà máy"  ↔  NM "Nhận hàng từ Hà Nội". */
  H['nguon_tep:timTrung'] = async (ctx, t) => {
    canQuyen(ctx);
    const tv = val(ctx);
    const ds = await bang('nguon_ban_ghi').findAll({ where: { ket_qua: 'co_the_trung', ...(tv.tep_ids ? { tep_id: tv.tep_ids } : {}) }, transaction: t,
      order: [['ngay', 'ASC'], ['id', 'ASC']] });
    const daKhop = new Set<number>((await p.sql(`SELECT ban_ghi_a_id AS a, ban_ghi_b_id AS b FROM khop_chung_tu WHERE trang_thai IN ('de_xuat','xac_nhan')`, {}, t))
      .flatMap((x: any) => [Number(x.a), Number(x.b)]));
    const J = (r: any) => ({ ...JSON.parse(r.du_lieu || '{}'), ...JSON.parse(r.chuan_hoa || '{}') });
    const nmDi = ds.filter((r: any) => r.he_thong === 'nha_may' && r.loai_nv === 'chuyen_kho');
    const bhTuNm = ds.filter((r: any) => r.he_thong === 'ban_hang' && r.loai_nv === 'chuyen_kho' && /nha may/.test(boDau(J(r).kho_di)));
    const bhVeNm = ds.filter((r: any) => r.he_thong === 'ban_hang' && r.loai_nv === 'chuyen_kho' && /nha may/.test(boDau(J(r).kho_den)));
    const nmNhan = ds.filter((r: any) => r.he_thong === 'nha_may' && r.loai_nv === 'nhan_hang');
    const ngayCach = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86400000);
    const de_xuat: any[] = [];
    const ghep = async (As: any[], Bs: any[], ten: string) => {
      const cap: any[] = [];
      for (const a of As) for (const b of Bs) {
        const x = J(a), y = J(b);
        if (!x.mat_hang_id || x.mat_hang_id !== y.mat_hang_id) continue;
        const n = ngayCach(x.ngay, y.ngay);
        if (n < 0 || n > 3) continue;
        const lech = Math.abs(Number(x.so_luong) - Number(y.so_luong));
        const pct = Number(x.so_luong) > 0 ? (lech / Number(x.so_luong)) * 100 : 100;
        if (pct > 0.5) continue;
        cap.push({ a, b, diem: Math.round((3 - n * 0.5 + (lech < 0.0005 ? 1 : 0)) * 100) / 100, ly_do: `${ten}: cùng mặt hàng, cách ${n} ngày, lệch ${kg(lech)} (${pct.toFixed(2)}%)` });
      }
      cap.sort((u, w) => w.diem - u.diem);
      for (const c of cap) {
        if (daKhop.has(c.a.id) || daKhop.has(c.b.id)) continue;
        daKhop.add(c.a.id); daKhop.add(c.b.id);
        const k = `${c.a.id}|${c.b.id}`;
        if (await bang('khop_chung_tu').findOne({ where: { khoa: k }, transaction: t })) continue;
        await bang('khop_chung_tu').create({ ban_ghi_a_id: c.a.id, ban_ghi_b_id: c.b.id, diem: c.diem, ly_do: c.ly_do, trang_thai: 'de_xuat', khoa: k }, { transaction: t, hooks: false });
        de_xuat.push({ a: c.a.id, b: c.b.id, diem: c.diem, ly_do: c.ly_do });
      }
    };
    await ghep(nmDi, bhTuNm, 'NM → HN');
    await ghep(bhVeNm, nmNhan, 'HN → NM');
    return { ok: true, de_xuat: de_xuat.length, chi_tiet: de_xuat.slice(0, 200) };
  };
  H['khop_chung_tu:xacNhan'] = async (ctx, t) => {
    canQuyen(ctx);
    const k = await p.khoa('khop_chung_tu', id(ctx), t);
    if (k.trang_thai === 'bac_bo') loi('Cặp đã bác bỏ.');
    await k.update({ trang_thai: 'xac_nhan', nguoi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['khop_chung_tu:bacBo'] = async (ctx, t) => {
    canQuyen(ctx);
    const k = await p.khoa('khop_chung_tu', id(ctx), t);
    if (k.trang_thai === 'xac_nhan') {
      const [x] = await p.sql(`SELECT COUNT(*)::int AS n FROM nguon_ban_ghi WHERE id IN (:a, :b) AND ket_qua = 'da_ghi'`, { a: k.ban_ghi_a_id, b: k.ban_ghi_b_id }, t);
      if (x.n) loi('Cặp đã ghi sổ: hủy chuyến chuyển hàng trước.');
    }
    await k.update({ trang_thai: 'bac_bo', nguoi: p.nguoi(ctx), ly_do: [k.ly_do, val(ctx).ly_do].filter(Boolean).join(' | ') }, { transaction: t, hooks: false });
    return { ok: true };
  };

  H['nguon_ban_ghi:boQua'] = async (ctx, t) => {
    canQuyen(ctx);
    const r = await p.khoa('nguon_ban_ghi', id(ctx), t);
    if (r.ket_qua === 'da_ghi') loi('Bản ghi đã ghi sổ: hủy chứng từ đích trước.');
    const ly = val(ctx).ly_do;
    if (!ly) loi('Ghi lý do bỏ qua.');
    await r.update({ ket_qua: 'bo_qua', van_de: [r.van_de, `Bỏ qua: ${ly} (${p.nguoi(ctx)})`].filter(Boolean).join(' | ') }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- GHI SỔ ----------------
  const danhDau = async (t: Transaction, ids: any[], kq: any) => {
    if (kq.ok) await bang('nguon_ban_ghi').update({ ket_qua: 'da_ghi', chung_tu_dich: String(kq.r), van_de: null }, { where: { id: ids }, transaction: t, hooks: false });
    else await bang('nguon_ban_ghi').update({ ket_qua: 'bi_chan', van_de: `Ghi lỗi: ${kq.loi}`.slice(0, 2000) }, { where: { id: ids }, transaction: t, hooks: false });
  };
  const chuyenHang = async (ctx: any, t: Transaction, a: any) => {
    const ch = await bang('chuyen_hang').create({ ngay: a.ngay, kho_di_id: a.kho_di_id, kho_den_id: a.kho_den_id, kho_tg_id: a.kho_tg_id || null, xe: a.xe || null,
      nguon: a.nguon, request_id: a.request_id, ghi_chu: a.ghi_chu || null }, { transaction: t });
    for (const d of a.dong) await bang('chuyen_hang_dong').create({ chuyen_hang_id: ch.id, mat_hang_id: d.mat_hang_id, so_kg: d.so_kg, so_lo: d.so_lo || null }, { transaction: t });
    await goi('chuyen_hang:xacNhanXuat', ctx, t, ch.id);
    if (a.nhan) {
      const dong = await bang('chuyen_hang_dong').findAll({ where: { chuyen_hang_id: ch.id }, transaction: t, order: [['id', 'ASC']] });
      const nhan: any = {};
      dong.forEach((x: any, i: number) => { nhan[x.id] = { so_kg: a.nhan[i] }; });
      await goi('chuyen_hang:xacNhanNhan', ctx, t, ch.id, { nhan, ngay: a.ngay_nhan || a.ngay, ly_do: a.ly_do_lech || 'Lệch giữa sổ hai đầu (nhập từ nguồn)' });
    }
    return ch.so;
  };

  /** values: {loai_nv?: string[], gioi_han?: number, tep_id?} — ghi các bản ghi "Nhập được" + các cặp đã xác nhận. */
  H['nguon_tep:ghiSo'] = async (ctx, t) => {
    canQuyen(ctx);
    const v = val(ctx);
    const gioiHan = Number(v.gioi_han || 500);
    const loaiNv: string[] = v.loai_nv || ['chuyen_ghep', 'chuyen_kho', 'nhap_kho', 'nhan_hang', 'san_xuat', 'ban_nm', 'don_ban', 'thu_tien', 'tra_lai'];
    const kq: Record<string, { ok: number; loi: number }> = {};
    const dem = (k: string, r: any) => { kq[k] = kq[k] || { ok: 0, loi: 0 }; kq[k][r.ok ? 'ok' : 'loi']++; };
    const J = (r: any) => JSON.parse(r.chuan_hoa || '{}');
    const teps = v.tep_ids || (v.tep_id ? [v.tep_id] : null);
    const lay = async (nv: string, extra: any = {}) => bang('nguon_ban_ghi').findAll({ where: { ket_qua: 'nhap_duoc', loai_nv: nv, ...(teps ? { tep_id: teps } : {}), ...extra },
      transaction: t, order: [['ngay', 'ASC'], ['id', 'ASC']], limit: gioiHan * 50 });
    const theo = (ds: any[], f: (r: any) => string) => { const m = new Map<string, any[]>(); for (const r of ds) { const k = f(r); m.set(k, [...(m.get(k) || []), r]); } return [...m.values()]; };
    let so = 0;

    if (loaiNv.includes('chuyen_ghep')) {
      const caps = await p.sql(`SELECT k.id, k.ban_ghi_a_id AS a, k.ban_ghi_b_id AS b FROM khop_chung_tu k JOIN nguon_ban_ghi x ON x.id = k.ban_ghi_a_id
        JOIN nguon_ban_ghi y ON y.id = k.ban_ghi_b_id WHERE k.trang_thai = 'xac_nhan' AND x.ket_qua = 'co_the_trung' AND y.ket_qua = 'co_the_trung'
        ${teps ? 'AND x.tep_id IN (:teps) AND y.tep_id IN (:teps)' : ''} ORDER BY x.ngay, k.id LIMIT :n`, { n: gioiHan, teps: teps || [0] }, t);
      for (const c of caps) {
        const a = await bang('nguon_ban_ghi').findByPk(c.a, { transaction: t });
        const b = await bang('nguon_ban_ghi').findByPk(c.b, { transaction: t });
        const x = J(a), y = J(b);
        const r = await diemLuu(t, async (t2) => {
          // Đầu xuất là bản ghi A (nơi hàng rời kho), đầu nhận là B; kho trung chuyển lấy theo nguồn nếu là kho "đang vận chuyển".
          const khoTg = (await laKhoTg(t2, x.kho_den_id)) ? x.kho_den_id : null;
          const kho_di = x.kho_di_id || x.kho_id;
          const kho_den = y.kho_den_id || y.kho_id;
          if (!kho_di || !kho_den) loi('Thiếu kho đi / kho đến sau ánh xạ.');
          return chuyenHang(ctx, t2, { ngay: x.ngay, ngay_nhan: y.ngay, kho_di_id: kho_di, kho_den_id: kho_den, kho_tg_id: khoTg, request_id: `NG-${a.id}-${b.id}`,
            nguon: `nguồn ${a.he_thong}#${a.dong} + ${b.he_thong}#${b.dong}`, ghi_chu: `${a.so_ct || ''} ↔ ${b.so_ct || ''}`,
            dong: [{ mat_hang_id: x.mat_hang_id, so_kg: x.so_luong }], nhan: [y.so_luong] });
        });
        await danhDau(t, [a.id, b.id], r);
        dem('chuyen_ghep', r);
        if (++so >= gioiHan) break;
      }
    }
    if (loaiNv.includes('chuyen_kho')) {
      // Chuyển nội bộ một nguồn (không qua nhà máy ↔ HN) và xuất khác.
      for (const g of theo(await lay('chuyen_kho'), (r) => `${r.he_thong}|${r.ngay}|${r.so_ct || r.id}|${J(r).kho_di_id}|${J(r).kho_den_id || 'xk'}`)) {
        const x = J(g[0]);
        const r = await diemLuu(t, async (t2) => {
          if (x.kho_den_id) {
            return chuyenHang(ctx, t2, { ngay: x.ngay, kho_di_id: x.kho_di_id, kho_den_id: x.kho_den_id, request_id: `NG-${g[0].id}`, nguon: `nguồn ${g[0].he_thong}#${g[0].dong}`,
              dong: g.map((r) => ({ mat_hang_id: J(r).mat_hang_id, so_kg: J(r).so_luong })), nhan: g.map((r) => J(r).so_luong) });
          }
          const pk = await bang('phieu_kho').create({ loai: 'xuat', ngay: x.ngay, kho_id: x.kho_di_id, ghi_chu: `${x.loai_xuat || 'Xuất khác'} (nguồn ${g[0].he_thong}#${g[0].dong})` },
            { transaction: t2 });
          for (const r of g) await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, mat_hang_id: J(r).mat_hang_id, so_kg: J(r).so_luong }, { transaction: t2 });
          await goi('phieu_kho:ghiSo', ctx, t2, pk.id);
          return pk.so;
        });
        await danhDau(t, g.map((r) => r.id), r);
        dem('chuyen_kho', r);
        if (++so >= gioiHan) break;
      }
    }
    for (const nv of ['nhap_kho', 'nhan_hang']) {
      if (!loaiNv.includes(nv)) continue;
      for (const g of theo(await lay(nv), (r) => `${r.he_thong}|${r.ngay}|${r.so_ct || r.id}|${J(r).kho_id}`)) {
        const x = J(g[0]);
        const r = await diemLuu(t, async (t2) => {
          const pk = await bang('phieu_kho').create({ loai: 'nhap', ngay: x.ngay, kho_id: x.kho_id, ghi_chu: `Nhập từ nguồn ${g[0].he_thong}#${g[0].dong} ${g[0].so_ct || ''}` }, { transaction: t2 });
          for (const r of g) {
            const y = J(r);
            await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, mat_hang_id: y.mat_hang_id, so_kg: y.so_luong, don_gia: y.don_gia > 0 ? y.don_gia : null }, { transaction: t2 });
          }
          await goi('phieu_kho:ghiSo', ctx, t2, pk.id);
          return pk.so;
        });
        await danhDau(t, g.map((r) => r.id), r);
        dem(nv, r);
        if (++so >= gioiHan) break;
      }
    }
    if (loaiNv.includes('san_xuat')) {
      for (const g of theo(await lay('san_xuat'), (r) => `${r.he_thong}|${r.so_ct}|${r.ngay}`)) {
        const ds = g.map((r) => ({ r, y: J(r), d: JSON.parse(r.du_lieu) }));
        const vao = ds.filter((x) => /dau vao/.test(x.y.dong));
        const v2 = {
          nguon: `nguon:${g[0].he_thong}`, so_phieu: g[0].so_ct, ngay: g[0].ngay, xuong: ds[0].d.day_chuyen || null, kho_id: vao[0]?.y.kho_id,
          kho_tp_id: ds.find((x) => /thanh pham/.test(x.y.dong))?.y.kho_id || null,
          nvl: vao.map((x) => ({ mat_hang_id: x.y.mat_hang_id, so_kg: x.y.so_luong })),
          tp: ds.filter((x) => /thanh pham/.test(x.y.dong)).map((x) => ({ mat_hang_id: x.y.mat_hang_id, so_kg: x.y.so_luong })),
          phu_pham: ds.filter((x) => /phu pham/.test(x.y.dong)).map((x) => ({ mat_hang_id: x.y.mat_hang_id, so_kg: x.y.so_luong, don_gia: 0 })),
          hao: ds.filter((x) => /hao hut/.test(x.y.dong)).map((x) => ({ mat_hang_id: x.y.mat_hang_id, so_kg: x.y.so_luong, loai_hao: /bat thuong/.test(boDau(x.d.ghi_chu)) ? 'bat_thuong' : 'tu_nhien' })),
        };
        const khoVao = new Set(vao.map((x) => x.y.kho_id));
        const r = await diemLuu(t, async (t2) => {
          if (khoVao.size > 1) loi('NVL lấy từ nhiều kho trong một phiếu SX: tách phiếu hoặc chuyển về một kho trước.');
          const kq2 = await goi('me_sx:nhapNhanh', ctx, t2, null, v2);
          if (!kq2.ok) loi(`Rà soát SX: ${kq2.van_de.join('; ')}`);
          return kq2.so;
        });
        await danhDau(t, g.map((x) => x.id), r);
        dem('san_xuat', r);
        if (++so >= gioiHan) break;
      }
    }
    for (const nv of ['ban_nm', 'don_ban']) {
      if (!loaiNv.includes(nv)) continue;
      for (const g of theo(await lay(nv), (r) => `${r.he_thong}|${J(r).don_vi_id}|${r.so_ct || r.id}|${r.ngay}`)) {
        const x = J(g[0]);
        const soCu = `${g[0].he_thong === 'nha_may' ? 'NM' : 'BH'}:${x.don_vi_id}:${g[0].so_ct || g[0].id}`;
        const r = await diemLuu(t, async (t2) => {
          const co = await bang('don_ban').findOne({ where: { so_don_cu: soCu, trang_thai: { [Op.ne]: 'da_huy' } }, transaction: t2 });
          if (co) loi(`Đã có đơn ${co.so} từ cùng chứng từ nguồn.`);
          const don = await bang('don_ban').create({ loai: 'ban', kenh: 'si', khach_id: x.khach_id, don_vi_ban_id: x.don_vi_id, ngay: x.ngay, ngay_giao: x.ngay,
            cach_giao: 'khach_den_lay', xuat_hoa_don: g.some((r) => J(r).xuat_hd), so_don_cu: soCu, ghi_chu: `Từ nguồn ${g[0].he_thong} ${g[0].so_ct || ''}` }, { transaction: t2 });
          for (const r of g) {
            const y = J(r);
            await bang('don_ban_dong').create({ don_ban_id: don.id, mat_hang_id: y.mat_hang_id, kho_id: y.kho_id, so_kg: y.so_luong, don_gia: y.don_gia ?? null,
              gia_gom_vat: !!y.gom_vat, vat_ap_dung: !!y.xuat_hd, ly_do_sua_gia: 'Giá theo sổ bán hàng (nhập nguồn)' }, { transaction: t2 });
          }
          ctx.state.aphBoQuaTinDung = true;
          try {
            const c = await goi('don_ban:chotDon', ctx, t2, don.id);
            if (c?.cho_duyet) await goi('don_ban:duyetGia', ctx, t2, don.id, { ly_do: 'Đơn đã thực hiện trước Go-Live trên sổ bán hàng (nhập nguồn)' });
          } finally { ctx.state.aphBoQuaTinDung = false; }
          const dd = await bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t2, order: [['id', 'ASC']] });
          const lg = await goi('luot_giao:taoLuot', ctx, t2, null, { don_ban_id: don.id, cach_giao: 'khach_den_lay', request_id: `NG-L-${g[0].id}`,
            dong: dd.map((z: any) => ({ don_ban_dong_id: z.id, so_kg: z.so_kg })) });
          const ld = await bang('luot_giao_dong').findAll({ where: { luot_giao_id: lg.id }, transaction: t2, order: [['id', 'ASC']] });
          const thuc: any = {};
          ld.forEach((z: any, i: number) => { const s = J(g[i]).sl_thuc; if (s) thuc[z.id] = { so_kg: s, ly_do: 'SL thực xuất theo sổ kho' }; });
          await goi('luot_giao:khachNhan', ctx, t2, lg.id, { thuc });
          return don.so;
        });
        await danhDau(t, g.map((z) => z.id), r);
        dem(nv, r);
        if (++so >= gioiHan) break;
      }
    }
    if (loaiNv.includes('thu_tien')) {
      for (const r0 of await lay('thu_tien')) {
        const x = J(r0);
        const r = await diemLuu(t, async (t2) => {
          const q = await bang('quy').findByPk(x.quy_id, { transaction: t2 });
          if (!q || q.don_vi_id !== x.don_vi_id) loi('Quỹ ánh xạ không thuộc công ty nhận tiền.');
          const pt = await bang('phieu_thu').create({ ngay: x.ngay, khach_id: x.khach_id, don_vi_id: x.don_vi_id, hinh_thuc: q.loai === 'tien_mat' ? 'tien_mat' : 'chuyen_khoan',
            so_tien: x.so_tien, quy_id: q.id, ma_gd: x.so_ct || `NG-${r0.id}`, loai_thu: 'thu_no', request_id: `NG-${r0.id}`,
            ghi_chu: `Từ sổ bán hàng dòng ${r0.dong}${x.cho_xk ? ` — cho phiếu XK ${x.cho_xk}` : ''}` }, { transaction: t2 });
          ctx.state.aphDaXacMinh = true;
          try { await goi('phieu_thu:ghi', ctx, t2, pt.id); } finally { ctx.state.aphDaXacMinh = false; }
          if (x.cho_xk) {
            const don = await bang('don_ban').findOne({ where: { so_don_cu: `BH:${x.don_vi_id}:${x.cho_xk}`, khach_id: x.khach_id }, transaction: t2 });
            if (don && tien(don.con_no) > 0) await goi('phieu_thu:phanBo', ctx, t2, pt.id, { phan_bo: [{ don_ban_id: don.id, so_tien: Math.min(tien(don.con_no), x.so_tien) }] });
          }
          return pt.so;
        });
        await danhDau(t, [r0.id], r);
        dem('thu_tien', r);
        if (++so >= gioiHan) break;
      }
    }
    if (loaiNv.includes('tra_lai')) {
      for (const g of theo(await lay('tra_lai'), (r) => `${J(r).don_vi_id}|${J(r).so_goc}|${r.ngay}|${r.so_ct || r.id}`)) {
        const x = J(g[0]);
        const r = await diemLuu(t, async (t2) => {
          const don = await bang('don_ban').findOne({ where: { so_don_cu: `BH:${x.don_vi_id}:${x.so_goc}` }, transaction: t2 });
          if (!don) loi(`Không thấy đơn gốc ${x.so_goc} (đơn gốc chưa nhập hoặc trước mốc).`);
          const th = await bang('tra_hang').create({ don_ban_id: don.id, ngay: x.ngay, kho_nhan_id: x.kho_id, ly_do: x.ly_do || 'Khách trả lại (nhập nguồn)' }, { transaction: t2 });
          for (const z of g) {
            const y = J(z);
            const dd = await bang('don_ban_dong').findOne({ where: { don_ban_id: don.id, mat_hang_id: y.mat_hang_id }, transaction: t2 });
            if (!dd) loi('Mặt hàng trả không có trong đơn gốc.');
            await bang('tra_hang_dong').create({ tra_hang_id: th.id, don_ban_dong_id: dd.id, so_kg: y.so_luong }, { transaction: t2 });
          }
          await goi('tra_hang:ghi', ctx, t2, th.id);
          return th.so;
        });
        await danhDau(t, g.map((z) => z.id), r);
        dem('tra_lai', r);
        if (++so >= gioiHan) break;
      }
    }
    return { ok: true, ket_qua: kq, so_nhom: so };
  };

  /** Lô tồn đầu kỳ từ nguồn (tồn đầu NM + tồn đầu theo kho ở DM hàng) và bảng so sánh hai nguồn cho cùng kho vật lý. */
  H['nguon_tep:taoLoTon'] = async (ctx, t) => {
    canQuyen(ctx);
    const ds = await bang('nguon_ban_ghi').findAll({ where: { loai_nv: ['ton_dau', 'ton_dau_bh'], ket_qua: 'nhap_duoc' }, transaction: t, order: [['id', 'ASC']] });
    if (!ds.length) loi('Chưa có dòng tồn đầu "Nhập được" (chạy phân loại và hoàn tất ánh xạ trước).');
    const gom: Record<string, { kho: any; mh: any; nm: number; bh: number; dong: number[] }> = {};
    for (const r of ds) {
      const c = JSON.parse(r.chuan_hoa || '{}');
      const k = `${c.kho_id}|${c.mat_hang_id}`;
      gom[k] = gom[k] || { kho: c.kho_id, mh: c.mat_hang_id, nm: 0, bh: 0, dong: [] };
      if (r.he_thong === 'nha_may') gom[k].nm = kg(gom[k].nm + c.so_luong); else gom[k].bh = kg(gom[k].bh + c.so_luong);
      gom[k].dong.push(r.id);
    }
    const ma2 = async (b: string, i: any) => (await bang(b).findByPk(i, { transaction: t }))?.ma;
    const lech: any[] = [];
    const dong: string[] = ['Mã kho\tMã hàng\tSố lượng\tGhi chú'];
    for (const g of Object.values(gom)) {
      const mk = await ma2('kho', g.kho), mh = await ma2('mat_hang', g.mh);
      // Cùng kho vật lý có ở cả hai nguồn: KHÔNG cộng dồn — lấy sổ nhà máy (sổ của thủ kho) và đưa vào bảng lệch để xác nhận.
      const sl = g.nm && g.bh ? g.nm : g.nm || g.bh;
      if (g.nm && g.bh && Math.abs(g.nm - g.bh) > 0.0005) lech.push({ kho: mk, mat_hang: mh, so_nha_may: g.nm, so_ban_hang: g.bh, chenh: kg(g.nm - g.bh) });
      if (sl > 0) dong.push(`${mk}\t${mh}\t${sl}\t${g.nm && g.bh ? `Hai nguồn: NM ${g.nm} / BH ${g.bh}` : g.nm ? 'Sổ nhà máy' : 'Sổ bán hàng'}`);
    }
    const [ky] = await p.sql(`SELECT id FROM ky_mo_so WHERE trang_thai = 'mo' ORDER BY id DESC LIMIT 1`, {}, t);
    const lo = await bang('nhap_lo').create({ loai: 'ton_dau_ky', ky_mo_so_id: ky?.id || null, nguon: 'Trung tâm dữ liệu: tồn đầu kỳ từ 2 nguồn', du_lieu_goc: dong.join('\n'),
      ghi_chu: lech.length ? `${lech.length} mặt hàng × kho lệch giữa hai nguồn — xác nhận trước khi duyệt` : null, nguoi_nhap: p.nguoi(ctx) }, { transaction: t });
    return { ok: true, nhap_lo_id: lo.id, so_dong: dong.length - 1, lech };
  };

  /** Báo cáo tổng hợp: số bản ghi theo nghiệp vụ × phân loại + 50 vấn đề thường gặp. */
  H['nguon_tep:baoCao'] = async (ctx, t) => {
    canQuyen(ctx);
    const v = val(ctx);
    const loc = v.tep_id ? 'WHERE tep_id = :tep' : '';
    const ds = await p.sql(`SELECT he_thong, loai_nv, COALESCE(ket_qua,'chua_phan_loai') AS ket_qua, COUNT(*)::int AS n FROM nguon_ban_ghi ${loc} GROUP BY 1,2,3 ORDER BY 1,2,3`, { tep: v.tep_id }, t);
    const vd = await p.sql(`SELECT split_part(van_de, ';', 1) AS van_de, COUNT(*)::int AS n FROM nguon_ban_ghi ${loc ? loc + ' AND' : 'WHERE'} van_de IS NOT NULL
      GROUP BY 1 ORDER BY 2 DESC LIMIT 50`, { tep: v.tep_id }, t);
    const [ax] = await p.sql(`SELECT COUNT(*) FILTER (WHERE dich_id > 0)::int AS da, COUNT(*) FILTER (WHERE COALESCE(dich_id,0) = 0)::int AS chua FROM anh_xa_ma`, {}, t);
    const [kh] = await p.sql(`SELECT COUNT(*) FILTER (WHERE trang_thai = 'de_xuat')::int AS de_xuat, COUNT(*) FILTER (WHERE trang_thai = 'xac_nhan')::int AS xac_nhan,
      COUNT(*) FILTER (WHERE trang_thai = 'bac_bo')::int AS bac_bo FROM khop_chung_tu`, {}, t);
    return { ok: true, phan_loai: ds, van_de_thuong_gap: vd, anh_xa: ax, ghep: kh, ngay: homNay() };
  };
  void khoNm;
}

export function hookNguon(p: any) {
  const db = p.db;
  for (const b of ['nguon_tep', 'nguon_ban_ghi', 'khop_chung_tu', 'sx_ra_soat']) {
    db.on(`${b}.beforeCreate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ tạo qua Trung tâm dữ liệu.'); });
    db.on(`${b}.beforeUpdate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ thay đổi qua thao tác nghiệp vụ.'); });
    db.on(`${b}.beforeDestroy`, () => loi('Không xóa dữ liệu nguồn (giữ vết kiểm toán).'));
  }
  db.on('anh_xa_ma.beforeUpdate', (_m: any, o: any) => { if (o?.hooks !== false) loi('Đặt ánh xạ qua thao tác "Đặt mã đích".'); });
  db.on('anh_xa_ma.beforeCreate', (_m: any, o: any) => { if (o?.hooks !== false) loi('Ánh xạ sinh từ tệp đã nạp.'); });
}
