/**
 * 0.4.0 Bán hàng hợp nhất:
 * - Chính sách tín dụng: phơi nhiễm = nợ thực tế (mọi bên bán) + giá trị còn cam kết giao của đơn đã duyệt + đơn mới; không cộng trùng phần đã giao.
 *   Khách rủi ro vượt hạn mức / có nợ quá hạn → chờ duyệt (kế toán trưởng / quản lý). Khách thường → theo cấu hình (cảnh báo hoặc duyệt).
 * - Đơn gộp (don_gop): khách thấy một đơn; nội bộ tách đơn con (don_ban) theo bên bán trong CÙNG giao dịch; chỉ tạo đơn con cho bên có hàng.
 * - Giao gộp: một chuyến gồm nhiều lượt của nhiều đơn con / nhiều kho; xác nhận theo cân thực.
 * - Hàng đợi hóa đơn MISA theo bên bán (hoa_don_cho_xuat), không tự gọi API xuất hóa đơn.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien, vnd } from '../tienich';
import { cauHinh } from '../security/cau_hinh';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

export function dangKyBanHang(p: any, H: H, h: any) {
  const { id, val, lyDo } = h;
  const bang = (n: string) => p.bang(n);
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);

  p.kiemTinDung = async (t: Transaction, khach_id: any, boQua: any[], giaTriMoi: number) => {
    const kh = await bang('khach_hang').findByPk(khach_id, { transaction: t });
    if (!kh) return {};
    const [r] = await p.sql(`SELECT
        COALESCE((SELECT SUM(con_no) FROM don_ban WHERE khach_id = :k AND trang_thai <> 'da_huy' AND NOT (id IN (:bo))),0) AS no,
        COALESCE((SELECT SUM(GREATEST(dd.so_kg - COALESCE(dd.da_giao,0), 0) * COALESCE(dd.don_gia_tt, dd.don_gia, 0))
          FROM don_ban_dong dd JOIN don_ban d ON d.id = dd.don_ban_id
          WHERE d.khach_id = :k AND d.trang_thai IN ('cho_xuat','dang_giao') AND NOT (d.id IN (:bo))),0) AS cam_ket,
        COALESCE((SELECT SUM(d.con_no) FROM don_ban d WHERE d.khach_id = :k AND d.trang_thai <> 'da_huy' AND d.con_no > 0 AND NOT (d.id IN (:bo))
          AND COALESCE(d.han_tt, d.ngay_giao + (COALESCE(:ngay_no, 0) || ' day')::interval) < :hom_nay::date),0) AS qua_han`,
    { k: khach_id, bo: boQua.length ? boQua.map(Number) : [0], ngay_no: Number(kh.so_ngay_no || 0), hom_nay: homNay() }, t);
    const phoi = tien(Number(r.no) + Number(r.cam_ket) + giaTriMoi);
    const han = Number(kh.han_muc || 0);
    const vuot = han > 0 && phoi > han;
    const mo_ta = `nợ ${vnd(r.no)} + cam kết chưa giao ${vnd(r.cam_ket)} + đơn này ${vnd(giaTriMoi)} = ${vnd(phoi)}${han ? ` / hạn mức ${vnd(han)}` : ''}${Number(r.qua_han) > 0 ? `; quá hạn ${vnd(r.qua_han)}` : ''}`;
    if (kh.rui_ro && (vuot || Number(r.qua_han) > 0)) return { can_duyet: true, ly_do: `khách rủi ro: ${vuot ? 'vượt hạn mức' : 'có nợ quá hạn'} (${mo_ta})` };
    if (vuot) {
      if ((await cauHinh(p, 'vuot_han_muc_khach_thuong', t)) === 'duyet') return { can_duyet: true, ly_do: `vượt hạn mức (${mo_ta})` };
      return { canh_bao: `Vượt hạn mức — đã cảnh báo, vẫn bán theo chính sách khách thường (${mo_ta})` };
    }
    return {};
  };

  // ---------------- ĐƠN GỘP ----------------
  p.capNhatGop = async (t: Transaction, dgId: any) => {
    const dg = await bang('don_gop').findByPk(dgId, { transaction: t, lock: t.LOCK.UPDATE });
    if (!dg) return;
    const con = await bang('don_ban').findAll({ where: { don_gop_id: dg.id }, transaction: t });
    const song = con.filter((d: any) => d.trang_thai !== 'da_huy');
    const tong = (k: string) => tien(song.reduce((a: number, d: any) => a + Number(d[k] || 0), 0));
    const [g] = await p.sql(`SELECT COALESCE(SUM(dd.so_kg),0) AS dat, COALESCE(SUM(dd.da_giao),0) AS giao, COALESCE(SUM(dd.giu_don),0) AS giu_don,
        COALESCE(SUM(dd.dang_giu),0) AS giu_luot FROM don_ban_dong dd JOIN don_ban d ON d.id = dd.don_ban_id WHERE d.don_gop_id = :g AND d.trang_thai <> 'da_huy'`, { g: dg.id }, t);
    const [hd] = await p.sql(`SELECT
        COUNT(*) FILTER (WHERE h.trang_thai = 'cho_xu_ly')::int AS cho, COUNT(*) FILTER (WHERE h.trang_thai = 'dang_lap')::int AS lap,
        COUNT(*) FILTER (WHERE h.trang_thai = 'da_xuat')::int AS xuat, COUNT(*) FILTER (WHERE h.trang_thai = 'can_dieu_chinh')::int AS dc
      FROM hoa_don_cho_xuat h JOIN don_ban d ON d.id = h.don_ban_id WHERE d.don_gop_id = :g`, { g: dg.id }, t);
    const st = song.map((d: any) => d.trang_thai);
    const tt_duyet = !song.length ? 'da_huy' : st.includes('nhap') && dg.tt_duyet === 'nhap' ? 'nhap' : st.includes('cho_duyet') ? 'cho_duyet' : 'da_duyet';
    const dat = kg(g.dat), giao = kg(g.giao);
    let tt_giao = 'chua_giu';
    if (st.length && st.every((x: string) => ['da_giao', 'da_dong'].includes(x))) tt_giao = st.includes('da_dong') ? 'dong' : 'du';
    else if (giao > 0) tt_giao = 'mot_phan';
    else if (kg(g.giu_luot) > 0) tt_giao = 'cho_xuat';
    else if (kg(g.giu_don) > 0) tt_giao = kg(g.giu_don) + 0.0005 >= dat ? 'da_giu' : 'thieu_giu';
    const phai_thu = tong('phai_thu'), da_thu = tong('da_thu'), phai_hoan = tong('phai_hoan');
    const tt_thanh_toan = phai_hoan > 0 ? 'phai_hoan' : da_thu <= 0 ? 'chua_thu' : tong('con_no') > 0 || phai_thu < tong('tong_tien') ? 'mot_phan' : 'du';
    const tt_hoa_don = hd.dc ? 'can_dieu_chinh' : hd.cho ? 'cho_xu_ly' : hd.lap ? 'dang_lap' : hd.xuat ? 'da_xuat' : 'khong';
    await dg.update({ tong_tien: tong('tong_tien'), phai_thu, da_thu, con_no: tong('con_no'), tt_duyet, tt_giao, tt_thanh_toan, tt_hoa_don }, { transaction: t, hooks: false });
  };

  H['don_gop:chot'] = async (ctx, t) => {
    const dg = await p.khoa('don_gop', id(ctx), t);
    if (dg.tt_duyet !== 'nhap') {
      const con = await bang('don_ban').findAll({ where: { don_gop_id: dg.id }, transaction: t });
      return { ok: true, da_chot_truoc: true, don_con: con.map((d: any) => d.so) };
    }
    const dong = await bang('don_gop_dong').findAll({ where: { don_gop_id: dg.id }, transaction: t, order: [['id', 'ASC']] });
    if (!dong.length) loi('Đơn gộp chưa có hàng.');
    const nhom: Record<string, any[]> = {};
    for (const d of dong) {
      if (!d.don_vi_ban_id) loi('Mỗi dòng phải chọn bên bán (APH / VH / MK / TL).');
      if (!d.kho_id) loi('Mỗi dòng phải chọn kho xuất.');
      if (!(kg(d.so_kg) > 0) && !(Number(d.sl_nhap) > 0)) loi('Số lượng phải > 0.');
      (nhom[d.don_vi_ban_id] = nhom[d.don_vi_ban_id] || []).push(d);
    }
    // Tách đơn con theo bên bán (chỉ bên có hàng); cùng mặt hàng ở hai bên bán là hai nghĩa vụ riêng.
    const con: any[] = [];
    for (const [dv, ds] of Object.entries(nhom)) {
      const don = await bang('don_ban').create({ loai: 'ban', kenh: 'si', khach_id: dg.khach_id, don_vi_ban_id: Number(dv), ngay: dg.ngay || homNay(),
        ngay_giao: dg.ngay_giao || dg.ngay || homNay(), cach_giao: dg.cach_giao, nguoi_nhan: dg.nguoi_nhan, sdt: dg.sdt, dia_chi_giao: dg.dia_chi_giao,
        xuat_hoa_don: ds.some((d: any) => d.vat_ap_dung), don_gop_id: dg.id, ghi_chu: `Thuộc đơn gộp ${dg.so}` }, { transaction: t });
      for (const d of ds) {
        const x = await bang('don_ban_dong').create({ don_ban_id: don.id, mat_hang_id: d.mat_hang_id, kho_id: d.kho_id, so_kg: d.so_kg, so_bao: d.so_bao,
          dvt_nhap: d.dvt_nhap, sl_nhap: d.sl_nhap, don_gia: d.don_gia ?? null, vat_ap_dung: !!d.vat_ap_dung, thue_suat: d.thue_suat ?? null,
          gia_gom_vat: d.gia_gom_vat ?? null, ly_do_sua_gia: d.ghi_chu || null, ...(d.vat_ap_dung ? {} : { loai_vat: 'khong_hd' }) }, { transaction: t });
        await d.update({ don_ban_dong_id: x.id, so_kg: x.so_kg, don_gia: x.don_gia }, { transaction: t, hooks: false });
      }
      con.push(await p.khoa('don_ban', don.id, t));
    }
    for (const d of con) await p.tinhCongNo(t, d);
    const tong = con.reduce((a, d) => a + Number(d.tong_tien || 0), 0);
    const td = await p.kiemTinDung(t, dg.khach_id, con.map((d) => d.id), tong);
    const kq: any[] = [];
    ctx.state.aphBoQuaTinDung = true; // tín dụng kiểm một lần ở cấp đơn gộp (tổng các đơn con)
    try {
      for (const d of con) {
        if (td.can_duyet) await d.update({ trang_thai: 'cho_duyet', ly_do_duyet: td.ly_do }, { transaction: t, choPhep: true } as any);
        else kq.push({ so: d.so, ...(await goi('don_ban:chotDon', ctx, t, d.id)) });
      }
    } finally { ctx.state.aphBoQuaTinDung = false; }
    if (td.canh_bao) for (const d of con) await d.update({ canh_bao_tin_dung: td.canh_bao }, { transaction: t, hooks: false });
    await dg.update({ tt_duyet: 'da_duyet', ly_do_duyet: td.can_duyet ? td.ly_do : kq.filter((x) => x.cho_duyet).map((x) => `${x.so}: ${x.ly_do}`).join('; ') || null },
      { transaction: t, hooks: false });
    await p.capNhatGop(t, dg.id);
    const moi = await bang('don_gop').findByPk(dg.id, { transaction: t });
    return { ok: true, don_con: con.map((d) => d.so), tt_duyet: moi.tt_duyet, tt_giao: moi.tt_giao, canh_bao: td.canh_bao || null, ket_qua: kq };
  };
  H['don_gop:duyet'] = async (ctx, t) => {
    const dg = await p.khoa('don_gop', id(ctx), t);
    if (!lyDo(ctx)) loi('Ghi lý do duyệt.');
    const con = await bang('don_ban').findAll({ where: { don_gop_id: dg.id, trang_thai: 'cho_duyet' }, transaction: t });
    if (!con.length) loi('Không có đơn con chờ duyệt.');
    for (const d of con) await goi('don_ban:duyetGia', ctx, t, d.id, { ly_do: lyDo(ctx) });
    await dg.update({ duyet_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    await p.capNhatGop(t, dg.id);
    return { ok: true };
  };
  H['don_gop:huy'] = async (ctx, t) => {
    const dg = await p.khoa('don_gop', id(ctx), t);
    if (!lyDo(ctx)) loi('Ghi lý do hủy.');
    const con = await bang('don_ban').findAll({ where: { don_gop_id: dg.id }, transaction: t });
    for (const d of con) if (d.trang_thai !== 'da_huy') await goi('don_ban:huy', ctx, t, d.id, { ly_do: lyDo(ctx) });
    await dg.update({ tt_duyet: 'da_huy' }, { transaction: t, hooks: false });
    await p.capNhatGop(t, dg.id);
    return { ok: true };
  };
  /** Một chuyến giao gồm nhiều dòng của nhiều đơn con / kho: tạo lượt cho từng đơn con và liên kết vào chuyến. */
  H['don_gop:taoGiao'] = async (ctx, t) => {
    const v = val(ctx);
    if (v.request_id) {
      const co = await bang('giao_gop').findOne({ where: { request_id: v.request_id }, transaction: t });
      if (co) return { ok: true, da_tao_truoc: true, id: co.id, so: co.so };
    }
    const dg = await p.khoa('don_gop', id(ctx), t);
    const ds = (v.dong || []).filter((x: any) => kg(x.so_kg) > 0);
    if (!ds.length) loi('Nhập lượng giao.');
    const theoDon: Record<string, any[]> = {};
    for (const x of ds) {
      const gd = await bang('don_gop_dong').findByPk(x.don_gop_dong_id, { transaction: t });
      if (!gd || gd.don_gop_id !== dg.id || !gd.don_ban_dong_id) loi('Dòng không thuộc đơn gộp hoặc đơn chưa chốt.');
      const dd = await bang('don_ban_dong').findByPk(gd.don_ban_dong_id, { transaction: t });
      (theoDon[dd.don_ban_id] = theoDon[dd.don_ban_id] || []).push({ don_ban_dong_id: dd.id, so_kg: kg(x.so_kg), so_bao: x.so_bao, so_lo: x.so_lo });
    }
    const gg = await bang('giao_gop').create({ don_gop_id: dg.id, ngay: homNay(), cach_giao: v.cach_giao || dg.cach_giao, nguoi_nhan: v.nguoi_nhan || dg.nguoi_nhan,
      bien_so: v.bien_so || null, request_id: v.request_id || null, trang_thai: 'cho_xuat' }, { transaction: t, hooks: false });
    const luot: string[] = [];
    for (const [donId, dong] of Object.entries(theoDon)) {
      const r = await goi('luot_giao:taoLuot', ctx, t, null, { don_ban_id: Number(donId), cach_giao: gg.cach_giao, nguoi_nhan: gg.nguoi_nhan, bien_so: gg.bien_so, dong });
      await bang('giao_gop_luot').create({ giao_gop_id: gg.id, luot_giao_id: r.id }, { transaction: t, hooks: false });
      luot.push(r.so);
    }
    await p.capNhatGop(t, dg.id);
    return { ok: true, id: gg.id, so: gg.so, luot };
  };
  /** Xác nhận chuyến gộp: thuc = {luot_giao_dong_id: {so_kg, so_bao, ly_do}}; mỗi lượt xuất đúng một lần. */
  H['giao_gop:xacNhan'] = async (ctx, t) => {
    const gg = await p.khoa('giao_gop', id(ctx), t);
    if (gg.trang_thai === 'da_xuat') return { ok: true, da_xuat_truoc: true };
    if (gg.trang_thai !== 'cho_xuat') loi('Chuyến đã hủy.');
    const ls = await bang('giao_gop_luot').findAll({ where: { giao_gop_id: gg.id }, transaction: t });
    const v = val(ctx);
    for (const l of ls) {
      const lg = await bang('luot_giao').findByPk(l.luot_giao_id, { transaction: t });
      await goi(lg.cach_giao === 'van_chuyen' ? 'luot_giao:banGiaoXe' : 'luot_giao:khachNhan', ctx, t, lg.id,
        { thuc: v.thuc || {}, giu_lai: v.giu_lai, nguoi_nhan: v.nguoi_nhan, bien_so: v.bien_so });
    }
    await gg.update({ trang_thai: 'da_xuat' }, { transaction: t, hooks: false });
    if (gg.don_gop_id) await p.capNhatGop(t, gg.don_gop_id);
    return { ok: true };
  };
  H['giao_gop:huy'] = async (ctx, t) => {
    const gg = await p.khoa('giao_gop', id(ctx), t);
    if (gg.trang_thai !== 'cho_xuat') loi('Chỉ hủy chuyến chưa xuất.');
    const ls = await bang('giao_gop_luot').findAll({ where: { giao_gop_id: gg.id }, transaction: t });
    for (const l of ls) await goi('luot_giao:huy', ctx, t, l.luot_giao_id, { ly_do: lyDo(ctx) || 'Hủy chuyến gộp' });
    await gg.update({ trang_thai: 'da_huy' }, { transaction: t, hooks: false });
    if (gg.don_gop_id) await p.capNhatGop(t, gg.don_gop_id);
    return { ok: true };
  };

  // ---------------- HÀNG ĐỢI HÓA ĐƠN MISA ----------------
  /** Sinh / cập nhật dòng chờ xuất hóa đơn cho phần đã giao chưa vào hàng đợi (theo bên bán = đơn con). */
  p.capNhatHangDoiHD = async (t: Transaction, don: any) => {
    if (!don.xuat_hoa_don || don.loai === 'dau_ky') return;
    const [g] = await p.sql(`SELECT COALESCE(SUM(l.thanh_tien),0) AS tong, COALESCE(SUM(l.tien_thue),0) AS thue FROM luot_giao_dong l JOIN luot_giao g ON g.id = l.luot_giao_id
      WHERE g.don_ban_id = :d AND g.trang_thai IN ('da_ban_giao_xe','khach_da_nhan')`, { d: don.id }, t);
    const [q] = await p.sql(`SELECT COALESCE(SUM(tong),0) AS tong, COALESCE(SUM(tien_thue),0) AS thue, COUNT(*)::int AS n FROM hoa_don_cho_xuat
      WHERE don_ban_id = :d AND trang_thai <> 'huy'`, { d: don.id }, t);
    const con = tien(Number(g.tong) - Number(q.tong));
    if (con > 0) {
      const thue = tien(Number(g.thue) - Number(q.thue));
      const lan = Number(q.n) + 1;
      await bang('hoa_don_cho_xuat').create({ don_ban_id: don.id, don_vi_id: don.don_vi_ban_id, khach_id: don.khach_id, lan, khoa_trung: `${don.id}|${lan}`,
        tong: con, tien_thue: thue, tien_truoc_thue: con - thue, trang_thai: 'cho_xu_ly' }, { transaction: t, hooks: false });
    }
    if (don.trang_thai_hd !== 'da_xuat') await don.update({ trang_thai_hd: 'cho_xuat' }, { transaction: t, hooks: false });
  };
  H['hoa_don_cho_xuat:nhan'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán xử lý hàng đợi hóa đơn.');
    const x = await p.khoa('hoa_don_cho_xuat', id(ctx), t);
    if (!['cho_xu_ly', 'can_dieu_chinh'].includes(x.trang_thai)) loi('Dòng không ở trạng thái chờ xử lý.');
    await x.update({ trang_thai: 'dang_lap', nguoi_xu_ly: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['hoa_don_cho_xuat:ghiSo'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán ghi số hóa đơn.');
    const x = await p.khoa('hoa_don_cho_xuat', id(ctx), t);
    const v = val(ctx);
    if (x.trang_thai === 'da_xuat') return { ok: true, da_ghi_truoc: true };
    if (!['dang_lap', 'cho_xu_ly'].includes(x.trang_thai)) loi('Dòng đã hủy.');
    if (!v.ky_hieu || !v.so_hd) loi('Nhập ký hiệu và số hóa đơn đã xuất trên MISA.');
    const [tr] = await p.sql(`SELECT h.id, d.so FROM hoa_don_cho_xuat h JOIN don_ban d ON d.id = h.don_ban_id
      WHERE h.ky_hieu = :k AND h.so_hd = :s AND h.don_vi_id = :dv AND h.id <> :i AND h.trang_thai <> 'huy' LIMIT 1`, { k: v.ky_hieu, s: v.so_hd, dv: x.don_vi_id, i: x.id }, t);
    if (tr) loi(`Ký hiệu + số hóa đơn đã ghi cho đơn ${tr.so} (cùng bên bán) — không xuất trùng.`);
    await x.update({ trang_thai: 'da_xuat', ky_hieu: v.ky_hieu, so_hd: v.so_hd, ngay_hd: v.ngay_hd || homNay(), nguoi_xu_ly: p.nguoi(ctx) }, { transaction: t, hooks: false });
    const don = await p.khoa('don_ban', x.don_ban_id, t);
    const [c] = await p.sql(`SELECT COUNT(*)::int AS n FROM hoa_don_cho_xuat WHERE don_ban_id = :d AND trang_thai IN ('cho_xu_ly','dang_lap','can_dieu_chinh')`, { d: don.id }, t);
    await don.update({ so_hoa_don: v.so_hd, ky_hieu_hd: v.ky_hieu, ngay_hd: v.ngay_hd || homNay(), trang_thai_hd: c.n ? 'cho_xuat' : 'da_xuat' }, { transaction: t, hooks: false });
    if (don.don_gop_id) await p.capNhatGop(t, don.don_gop_id);
    return { ok: true };
  };
  H['hoa_don_cho_xuat:huy'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán.');
    const x = await p.khoa('hoa_don_cho_xuat', id(ctx), t);
    if (x.trang_thai === 'da_xuat') loi('Hóa đơn đã xuất: dùng "Cần điều chỉnh" và xử lý trên MISA.');
    if (!lyDo(ctx)) loi('Ghi lý do.');
    await x.update({ trang_thai: 'huy', ghi_chu: lyDo(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };
}

export function hookBanHang(p: any) {
  const db = p.db;
  db.on('don_gop.beforeCreate', async (m: any, o: any) => {
    if (!m.get('ngay')) m.set('ngay', homNay());
    m.set('tt_duyet', 'nhap');
    const r = m.get('request_id');
    if (r && (await p.bang('don_gop').findOne({ where: { request_id: r }, transaction: o?.transaction }))) loi('DA_LUU: đơn gộp này đã được lưu (mạng chập chờn).');
    if (m.get('khach_id') && (!m.get('sdt') || !m.get('dia_chi_giao'))) {
      const k = await p.bang('khach_hang').findByPk(m.get('khach_id'), { transaction: o?.transaction });
      if (k) { if (!m.get('sdt')) m.set('sdt', k.sdt); if (!m.get('dia_chi_giao')) m.set('dia_chi_giao', k.dia_chi); }
    }
  });
  db.on('don_gop.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    if (m.previous('tt_duyet') && m.previous('tt_duyet') !== 'nhap' && (m.changed() || []).some((k: string) => !['ghi_chu', 'nguoi_nhan', 'updatedAt', 'updatedById'].includes(k)))
      loi('Đơn gộp đã chốt: sửa trên từng đơn con (mở lại) hoặc hủy.');
  });
  db.on('don_gop_dong.beforeSave', async (m: any, o: any) => {
    if (o?.hooks === false) return;
    const dg = await p.bang('don_gop').findByPk(m.get('don_gop_id'), { transaction: o?.transaction });
    if (dg && dg.tt_duyet !== 'nhap') loi('Đơn gộp đã chốt: không sửa dòng.');
    const dvt = m.get('dvt_nhap');
    const sl = Number(m.get('sl_nhap'));
    if (dvt && sl > 0 && m.get('mat_hang_id')) {
      const mh = await p.bang('mat_hang').findByPk(m.get('mat_hang_id'), { transaction: o?.transaction });
      if ((mh?.dvt_ton || 'kg') === dvt) m.set('so_kg', kg(sl));
      else {
        const q = await p.bang('quy_doi_dvt').findOne({ where: { mat_hang_id: m.get('mat_hang_id'), dvt }, transaction: o?.transaction });
        if (!q) loi(`Mặt hàng ${mh?.ma} chưa khai quy đổi "${dvt}".`);
        m.set('so_kg', kg(sl * Number(q.he_so)));
        if (['bao', 'thung'].includes(dvt)) m.set('so_bao', kg(sl));
      }
    }
  });
  for (const b of ['giao_gop', 'giao_gop_luot', 'hoa_don_cho_xuat', 'dat_giu_ton', 'lich_su_duyet_gia']) {
    db.on(`${b}.beforeCreate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ tạo qua thao tác nghiệp vụ.'); });
    db.on(`${b}.beforeUpdate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ thay đổi qua thao tác nghiệp vụ.'); });
    db.on(`${b}.beforeDestroy`, () => loi('Không xóa được.'));
  }
}
