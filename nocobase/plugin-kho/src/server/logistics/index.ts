/**
 * 0.4.0 Kho & giao nhận — chuyến chuyển hàng HAI ĐẦU qua kho "Hàng đang vận chuyển":
 *   xác nhận xuất: kho đi → kho trung chuyển (giá trị theo bình quân kho đi);
 *   xác nhận nhận: kho trung chuyển → kho đến theo số THỰC NHẬN; phần chênh nằm lại kho trung chuyển và sinh dòng "chênh lệch giao – nhận" chờ xử lý.
 *   Không bao giờ tự xóa chênh lệch: hao hụt / bồi thường cần người duyệt (kế toán / quản lý) + lý do.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien } from '../tienich';
import { kiemKho } from '../toan_ven';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

export function dangKyGiaoNhan(p: any, H: H, h: any) {
  const { id, val, lyDo } = h;
  const bang = (n: string) => p.bang(n);

  const khoTg = async (t: Transaction, ch: any) => {
    if (ch.kho_tg_id) return ch.kho_tg_id;
    const k = await bang('kho').findOne({ where: { trung_chuyen: true }, order: [['id', 'ASC']], transaction: t });
    if (!k) loi('Chưa khai báo kho "Hàng đang vận chuyển" (đánh dấu kho trung chuyển).');
    await ch.update({ kho_tg_id: k.id }, { transaction: t, hooks: false });
    return k.id;
  };

  H['chuyen_hang:xacNhanXuat'] = async (ctx, t) => {
    const ch = await p.khoa('chuyen_hang', id(ctx), t);
    if (ch.trang_thai !== 'nhap') {
      if (ch.trang_thai === 'da_huy') loi('Chuyến đã hủy.');
      return { ok: true, da_xuat_truoc: true, so: ch.so };
    }
    kiemKho(ctx, ch.kho_di_id);
    if (!ch.kho_den_id || ch.kho_den_id === ch.kho_di_id) loi('Kho đến phải khác kho đi.');
    const tg = await khoTg(t, ch);
    if ([ch.kho_di_id, ch.kho_den_id].includes(tg)) loi('Kho đi / đến không được là kho trung chuyển.');
    const dong = await bang('chuyen_hang_dong').findAll({ where: { chuyen_hang_id: ch.id }, transaction: t, order: [['id', 'ASC']] });
    if (!dong.length) loi('Chuyến chưa có hàng.');
    const ngay = ch.ngay || homNay();
    for (const d of dong) {
      const q = kg(d.so_kg);
      if (!(q > 0)) loi('Số lượng xuất phải > 0.');
      const c = { ngay, mat_hang_id: d.mat_hang_id, chung_tu: ch.so, nguon: 'chuyen_hang_dong', nguon_id: d.id };
      const v = await p.ghiSo(t, { ...c, kho_id: ch.kho_di_id, so_luong: -q, so_bao: -kg(d.so_bao), loai: 'chuyen_di' });
      await p.ghiSo(t, { ...c, kho_id: tg, so_luong: q, so_bao: kg(d.so_bao), loai: 'chuyen_den', gia_tri: -v });
    }
    await ch.update({ trang_thai: 'da_xuat', xuat_boi: p.nguoi(ctx), ngay }, { transaction: t, hooks: false });
    return { ok: true, so: ch.so };
  };

  /** nhan = {chuyen_hang_dong_id: {so_kg, so_bao}}; thiếu khóa = nhận đủ như xuất. */
  H['chuyen_hang:xacNhanNhan'] = async (ctx, t) => {
    const ch = await p.khoa('chuyen_hang', id(ctx), t);
    if (['da_nhan', 'co_chenh_lech'].includes(ch.trang_thai)) return { ok: true, da_nhan_truoc: true, so: ch.so };
    if (ch.trang_thai !== 'da_xuat') loi('Chuyến chưa xác nhận xuất.');
    kiemKho(ctx, ch.kho_den_id);
    const v = val(ctx);
    const nhan = v.nhan || {};
    const dong = await bang('chuyen_hang_dong').findAll({ where: { chuyen_hang_id: ch.id }, transaction: t, order: [['id', 'ASC']] });
    const ngay = v.ngay || homNay();
    const chenh: any[] = [];
    for (const d of dong) {
      const x = nhan[d.id] || {};
      const qn = x.so_kg === undefined || x.so_kg === null || x.so_kg === '' ? kg(d.so_kg) : kg(x.so_kg);
      const bn = x.so_bao === undefined || x.so_bao === null || x.so_bao === '' ? kg(d.so_bao) : kg(x.so_bao);
      if (qn < 0) loi('Số thực nhận không âm.');
      const vao = Math.min(qn, kg(d.so_kg));
      const c = { ngay, mat_hang_id: d.mat_hang_id, chung_tu: ch.so, nguon: 'chuyen_hang_dong', nguon_id: d.id };
      if (vao > 0) {
        const gt = await p.ghiSo(t, { ...c, kho_id: ch.kho_tg_id, so_luong: -vao, so_bao: -Math.min(bn, kg(d.so_bao)), loai: 'chuyen_di', choPhepAm: false });
        await p.ghiSo(t, { ...c, kho_id: ch.kho_den_id, so_luong: vao, so_bao: Math.min(bn, kg(d.so_bao)), loai: 'chuyen_den', gia_tri: -gt });
      }
      await d.update({ so_kg_nhan: qn, so_bao_nhan: bn }, { transaction: t, hooks: false });
      const lech = kg(qn - kg(d.so_kg));
      if (Math.abs(lech) > 0.0005) {
        if (!v.ly_do) loi('Thực nhận khác số xuất: ghi lý do / biên bản.');
        chenh.push(await bang('chenh_lech_giao_nhan').create({ chuyen_hang_id: ch.id, mat_hang_id: d.mat_hang_id, so_kg: lech, trang_thai: 'cho_xu_ly',
          ly_do: v.ly_do }, { transaction: t, hooks: false }));
      }
    }
    await ch.update({ trang_thai: chenh.length ? 'co_chenh_lech' : 'da_nhan', nhan_boi: p.nguoi(ctx), nguoi_nhan: v.nguoi_nhan || ch.nguoi_nhan },
      { transaction: t, hooks: false });
    return { ok: true, so: ch.so, chenh_lech: chenh.map((c) => ({ id: c.id, mat_hang_id: c.mat_hang_id, so_kg: kg(c.so_kg) })) };
  };

  H['chuyen_hang:huy'] = async (ctx, t) => {
    const ch = await p.khoa('chuyen_hang', id(ctx), t);
    if (ch.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
    if (!lyDo(ctx)) loi('Ghi lý do hủy.');
    if (ch.trang_thai === 'da_xuat') {
      if (!p.xemGia(ctx)) loi('Chuyến đã xuất: chỉ kế toán / quản lý hủy (đảo sổ).');
      await p.daoSo(t, ch.so, homNay(), 'huy_chuyen');
    } else if (ch.trang_thai !== 'nhap') loi('Chuyến đã nhận: không hủy — xử lý bằng chuyến trả về.');
    await ch.update({ trang_thai: 'da_huy', ghi_chu: [ch.ghi_chu, `Hủy: ${lyDo(ctx)}`].filter(Boolean).join(' | ') }, { transaction: t, hooks: false });
    return { ok: true };
  };

  /** Xử lý chênh lệch: hao_hut / boi_thuong (xuất khỏi kho trung chuyển, vào chi phí), nhan_bo_sung (vào kho đến), tra_ve (về kho đi). */
  H['chenh_lech_giao_nhan:xuLy'] = async (ctx, t) => {
    const c = await p.khoa('chenh_lech_giao_nhan', id(ctx), t);
    if (c.trang_thai === 'da_xu_ly') return { ok: true, da_xu_ly_truoc: true };
    const v = val(ctx);
    const cach = v.cach_xu_ly;
    if (!['hao_hut', 'nhan_bo_sung', 'tra_ve', 'boi_thuong'].includes(cach)) loi('Chọn cách xử lý.');
    if (!v.ly_do) loi('Ghi lý do / số biên bản.');
    const ch = await p.khoa('chuyen_hang', c.chuyen_hang_id, t);
    const q = kg(c.so_kg);
    const ngay = homNay();
    const ct = `${ch.so}-CL${c.id}`;
    const b = { ngay, mat_hang_id: c.mat_hang_id, chung_tu: ct, nguon: 'chenh_lech_giao_nhan', nguon_id: c.id };
    if (q < 0) {
      // Thiếu: hàng còn nằm ở kho trung chuyển.
      const sl = -q;
      if (['hao_hut', 'boi_thuong'].includes(cach)) {
        if (!p.xemGia(ctx)) loi('Duyệt hao hụt / bồi thường: chỉ kế toán / quản lý.');
        await p.ghiSo(t, { ...b, kho_id: ch.kho_tg_id, so_luong: -sl, loai: cach === 'hao_hut' ? 'hao_hut_van_chuyen' : 'boi_thuong_van_chuyen' });
      } else {
        const dich = cach === 'nhan_bo_sung' ? ch.kho_den_id : ch.kho_di_id;
        const gt = await p.ghiSo(t, { ...b, kho_id: ch.kho_tg_id, so_luong: -sl, loai: 'chuyen_di' });
        await p.ghiSo(t, { ...b, kho_id: dich, so_luong: sl, loai: 'chuyen_den', gia_tri: -gt });
      }
    } else {
      // Thừa: nhận nhiều hơn xuất — chỉ ghi khi đã kiểm (kế toán / quản lý), nhập kho đến theo giá bình quân kho đi.
      if (!p.xemGia(ctx)) loi('Hàng nhận thừa: chỉ kế toán / quản lý xử lý.');
      if (cach === 'nhan_bo_sung') {
        const [g] = await p.sql(`SELECT gia_bq FROM gia_von WHERE mat_hang_id = :m AND kho_id = :k`, { m: c.mat_hang_id, k: ch.kho_di_id }, t);
        const gia = Number(g?.gia_bq || 0);
        if (!(gia > 0)) loi('Kho đi chưa có giá bình quân: không nhập thừa với giá 0 — định giá trước.');
        await p.ghiSo(t, { ...b, kho_id: ch.kho_den_id, so_luong: q, loai: 'kiem_ke', gia });
      } else if (cach === 'tra_ve') {
        loi('Hàng thừa không trả về kho đi (kho đi không thiếu). Chọn "Tìm thấy — nhận bổ sung" hoặc bỏ qua.');
      }
      // hao_hut / boi_thuong với hàng thừa: không ghi sổ (không có hàng thực).
    }
    await c.update({ trang_thai: 'da_xu_ly', cach_xu_ly: cach, ly_do: [c.ly_do, v.ly_do].filter(Boolean).join(' | '), nguoi_duyet: p.nguoi(ctx) },
      { transaction: t, hooks: false });
    const [con] = await p.sql(`SELECT COUNT(*)::int AS n FROM chenh_lech_giao_nhan WHERE chuyen_hang_id = :c AND trang_thai = 'cho_xu_ly'`, { c: ch.id }, t);
    if (!con.n) await ch.update({ trang_thai: 'da_nhan' }, { transaction: t, hooks: false });
    return { ok: true };
  };
}

export function hookGiaoNhan(p: any) {
  const db = p.db;
  db.on('chuyen_hang.beforeCreate', async (m: any, o: any) => {
    if (o?.hooks === false) return;
    m.set('trang_thai', 'nhap');
    if (!m.get('ngay')) m.set('ngay', homNay());
    const r = m.get('request_id');
    if (r && (await p.bang('chuyen_hang').findOne({ where: { request_id: r }, transaction: o?.transaction }))) loi('DA_LUU: chuyến này đã được lưu.');
  });
  db.on('chuyen_hang.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    if (m.previous('trang_thai') !== 'nhap' && (m.changed() || []).some((k: string) => !['ghi_chu', 'xe', 'nguoi_giao', 'nguoi_nhan', 'updatedAt', 'updatedById'].includes(k)))
      loi('Chuyến đã xuất: chỉ đổi qua thao tác xác nhận / hủy.');
  });
  db.on('chuyen_hang.beforeDestroy', (m: any) => { if (m.get('trang_thai') !== 'nhap') loi('Chỉ xóa chuyến nháp.'); });
  db.on('chuyen_hang_dong.beforeSave', async (m: any, o: any) => {
    if (o?.hooks === false) return;
    const ch = await p.bang('chuyen_hang').findByPk(m.get('chuyen_hang_id'), { transaction: o?.transaction });
    if (ch && ch.trang_thai !== 'nhap') loi('Chuyến đã xuất: không sửa dòng.');
  });
  db.on('chenh_lech_giao_nhan.beforeCreate', (_m: any, o: any) => { if (o?.hooks !== false) loi('Chênh lệch sinh từ xác nhận nhận hàng.'); });
  db.on('chenh_lech_giao_nhan.beforeUpdate', (_m: any, o: any) => { if (o?.hooks !== false) loi('Xử lý chênh lệch qua thao tác "Xử lý".'); });
  db.on('chenh_lech_giao_nhan.beforeDestroy', () => loi('Không xóa chênh lệch.'));
}
