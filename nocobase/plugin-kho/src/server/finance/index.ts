/**
 * 0.4.0 Tiền & công nợ:
 * - Chuyển khoản "khách báo đã chuyển" → phiếu thu CHỜ XÁC MINH (không vào quỹ, không trừ nợ) cho tới khi kế toán đối chiếu sao kê.
 * - Sao kê ngân hàng: nạp tệp (xlsx / csv) → dòng sao kê chống trùng; khớp với phiếu thu chờ xác minh hoặc tạo phiếu thu mới (chưa rõ người nộp nếu chưa biết khách).
 * - Khoản PHẢI HOÀN (khách trả thừa sau trả hàng / giảm giá): giữ làm tiền chưa phân bổ của khách HOẶC hoàn bằng phiếu chi — không tự cấn sang đơn khác.
 */
import { Transaction } from 'sequelize';
import { homNay, loi, tien, vnd } from '../tienich';
import { kiemQuy } from '../toan_ven';
import { cauHinh } from '../security/cau_hinh';
import { boDau, cot, docTep, ngayVN, soVN, timTieuDe } from '../import/tep';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

export function dangKyTaiChinh(p: any, H: H, h: any) {
  const { id, val, lyDo } = h;
  const bang = (n: string) => p.bang(n);
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);

  // Ghi phiếu thu chuyển khoản: nếu cấu hình yêu cầu xác minh → chuyển sang chờ xác minh (người có quyền kế toán xác minh ngay được).
  const ghiGoc = H['phieu_thu:ghi'];
  H['phieu_thu:ghi'] = async (ctx, t) => {
    const pt = await p.khoa('phieu_thu', id(ctx), t);
    if (pt.trang_thai === 'cho_xac_minh') loi('Phiếu đang chờ xác minh: kế toán bấm "Xác minh" sau khi đối chiếu sao kê.');
    if (pt.trang_thai === 'nhap' && pt.hinh_thuc === 'chuyen_khoan' && !ctx.state?.aphDaXacMinh && (await cauHinh(p, 'ck_can_xac_minh', t)) === 'co') {
      return H['phieu_thu:baoChuyen'](ctx, t);
    }
    return ghiGoc(ctx, t);
  };
  H['phieu_thu:baoChuyen'] = async (ctx, t) => {
    const pt = await p.khoa('phieu_thu', id(ctx), t);
    if (pt.trang_thai === 'cho_xac_minh') return { ok: true, da_bao_truoc: true, so: pt.so };
    if (pt.trang_thai !== 'nhap') loi('Chỉ báo chuyển khoản cho phiếu nháp.');
    if (pt.hinh_thuc !== 'chuyen_khoan') loi('Chỉ áp dụng cho chuyển khoản.');
    kiemQuy(ctx, pt.quy_id);
    if (!(tien(pt.so_tien) > 0)) loi('Nhập số tiền khách báo đã chuyển.');
    if (!pt.quy_id) loi('Chọn tài khoản nhận.');
    await pt.update({ trang_thai: 'cho_xac_minh' }, { transaction: t, choPhep: true } as any);
    return { ok: true, so: pt.so, cho_xac_minh: true };
  };
  /** Xác minh: tiền đã thấy trên sao kê → ghi vào quỹ + phân bổ như phiếu thu thường. */
  H['phieu_thu:xacMinh'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán xác minh tiền chuyển khoản.');
    const pt = await p.khoa('phieu_thu', id(ctx), t);
    if (pt.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pt.so };
    if (pt.trang_thai !== 'cho_xac_minh') loi('Phiếu không ở trạng thái chờ xác minh.');
    const v = val(ctx);
    if (!pt.ma_gd && !v.ma_gd) loi('Nhập mã giao dịch ngân hàng (theo sao kê).');
    await pt.update({ trang_thai: 'nhap', ...(v.ma_gd ? { ma_gd: v.ma_gd } : {}) }, { transaction: t, choPhep: true } as any);
    ctx.state.aphDaXacMinh = true;
    try {
      const r = await ghiGoc(ctx, t);
      await bang('phieu_thu').update({ xac_minh_boi: p.nguoi(ctx) }, { where: { id: pt.id }, transaction: t, hooks: false });
      return { ...r, xac_minh: true };
    } finally { ctx.state.aphDaXacMinh = false; }
  };
  H['phieu_thu:tuChoiXacMinh'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán.');
    const pt = await p.khoa('phieu_thu', id(ctx), t);
    if (pt.trang_thai !== 'cho_xac_minh') loi('Phiếu không ở trạng thái chờ xác minh.');
    if (!lyDo(ctx)) loi('Ghi lý do (không thấy tiền trên sao kê…).');
    await pt.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx), chua_phan_bo: 0 }, { transaction: t, choPhep: true } as any);
    return { ok: true };
  };

  // ---------------- SAO KÊ ----------------
  H['sao_ke:nap'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán nạp sao kê.');
    const v = val(ctx);
    if (!v.quy_id) loi('Chọn tài khoản ngân hàng.');
    kiemQuy(ctx, v.quy_id);
    const quy = await bang('quy').findByPk(v.quy_id, { transaction: t });
    if (!quy || quy.loai !== 'ngan_hang') loi('Sao kê chỉ nạp cho tài khoản ngân hàng.');
    const { checksum, trang } = docTep(v, 10);
    const daCo = await bang('sao_ke').findOne({ where: { checksum, quy_id: v.quy_id }, transaction: t });
    if (daCo) return { ok: true, da_nap_truoc: true, so: daCo.so };
    let moi = 0, trung = 0, tong = 0;
    const sk = await bang('sao_ke').create({ quy_id: v.quy_id, ten_tep: v.ten_tep, checksum, nguoi_nap: p.nguoi(ctx) }, { transaction: t, hooks: false });
    for (const tr of trang) {
      const i = timTieuDe(tr.dong, [['ngay', 'date'], ['noi dung', 'dien giai', 'mo ta', 'description', 'remark'], ['so tien', 'ghi co', 'credit', 'phat sinh co', ' co', 'so tien vao']]);
      if (i < 0) continue;
      const td = tr.dong[i];
      const cNgay = cot(td, 'ngay giao dich', 'ngay gd', 'ngay hieu luc', 'ngay', 'date');
      const cNd = cot(td, 'noi dung', 'dien giai', 'mo ta', 'description', 'remark');
      const cCo = cot(td, 'ghi co', 'phat sinh co', 'so tien ghi co', 'credit', 'so tien vao', 'co');
      const cNo = cot(td, 'ghi no', 'phat sinh no', 'so tien ghi no', 'debit', 'so tien ra', 'no');
      const cTien = cot(td, 'so tien');
      const cMa = cot(td, 'ma giao dich', 'so tham chieu', 'so but toan', 'reference', 'ma gd', 'so ct');
      for (const r of tr.dong.slice(i + 1)) {
        const ngay = ngayVN(r[cNgay]);
        if (!ngay) continue;
        let st: number | null = null;
        if (cCo >= 0 && cCo !== cNo && (soVN(r[cCo]) || 0) !== 0) st = soVN(r[cCo]);
        else if (cNo >= 0 && (soVN(r[cNo]) || 0) !== 0) st = -Math.abs(soVN(r[cNo]) || 0);
        else if (cTien >= 0) st = soVN(r[cTien]);
        if (!st) continue;
        tong++;
        const nd = cNd >= 0 ? r[cNd] : '';
        const ma = cMa >= 0 ? r[cMa] : '';
        const khoa = `${v.quy_id}|${ngay}|${tien(st)}|${ma || boDau(nd).slice(0, 120)}`;
        const co = await bang('sao_ke_dong').findOne({ where: { khoa_trung: khoa }, transaction: t });
        if (co) { trung++; continue; }
        await bang('sao_ke_dong').create({ sao_ke_id: sk.id, quy_id: v.quy_id, ngay, so_tien: tien(st), noi_dung: nd, ma_gd: ma || null, khoa_trung: khoa,
          trang_thai: st > 0 ? 'chua_khop' : 'bo_qua' }, { transaction: t, hooks: false });
        moi++;
      }
    }
    if (!tong) loi('Không đọc được dòng sao kê nào: cần các cột Ngày, Nội dung, Số tiền / Ghi có.');
    await sk.update({ so_dong: tong, so_moi: moi, so_trung: trung }, { transaction: t, hooks: false });
    const goiY = await H['sao_ke:goiY']({ ...ctx, action: { ...ctx.action, params: { filterByTk: sk.id, values: {} } } }, t);
    return { ok: true, so: sk.so, so_dong: tong, so_moi: moi, so_trung: trung, goi_y: goiY.goi_y };
  };
  /** Gợi ý khớp: dòng sao kê vào ↔ phiếu thu chờ xác minh cùng tài khoản, cùng số tiền, mã GD / SĐT / tên khách xuất hiện trong nội dung. */
  H['sao_ke:goiY'] = async (ctx, t) => {
    const ds = await p.sql(`SELECT d.id, d.so_tien, d.noi_dung, d.ma_gd, d.ngay, d.quy_id FROM sao_ke_dong d WHERE d.trang_thai = 'chua_khop'
      ${id(ctx) ? 'AND d.sao_ke_id = :s' : ''} ORDER BY d.id`, { s: id(ctx) }, t);
    const goi_y: any[] = [];
    for (const d of ds) {
      const cho = await p.sql(`SELECT p.id, p.so, p.ma_gd, k.ten, k.sdt FROM phieu_thu p LEFT JOIN khach_hang k ON k.id = p.khach_id
        WHERE p.trang_thai = 'cho_xac_minh' AND p.quy_id = :q AND p.so_tien = :st ORDER BY p.id`, { q: d.quy_id, st: d.so_tien }, t);
      const nd = boDau(`${d.noi_dung} ${d.ma_gd || ''}`);
      const diem = cho.map((c: any) => ({ ...c, diem: (c.ma_gd && nd.includes(boDau(c.ma_gd)) ? 3 : 0) + (c.sdt && nd.includes(String(c.sdt).replace(/\D/g, '')) ? 2 : 0)
        + (c.ten && nd.includes(boDau(c.ten)) ? 1 : 0) + 1 })).sort((a: any, b: any) => b.diem - a.diem);
      if (diem.length) goi_y.push({ sao_ke_dong_id: d.id, phieu_thu_id: diem[0].id, phieu_thu: diem[0].so, diem: diem[0].diem, so_ung_vien: diem.length });
    }
    return { ok: true, goi_y };
  };
  H['sao_ke_dong:khop'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán.');
    const d = await p.khoa('sao_ke_dong', id(ctx), t);
    if (d.trang_thai === 'da_khop') return { ok: true, da_khop_truoc: true };
    if (d.trang_thai !== 'chua_khop') loi('Dòng đã bỏ qua.');
    const pt = await p.khoa('phieu_thu', val(ctx).phieu_thu_id, t);
    if (pt.quy_id !== d.quy_id) loi('Phiếu thu khác tài khoản ngân hàng của dòng sao kê.');
    if (tien(pt.so_tien) !== tien(d.so_tien)) loi(`Số tiền lệch: phiếu ${vnd(pt.so_tien)} đ, sao kê ${vnd(d.so_tien)} đ. Sửa phiếu (nếu nháp) trước khi khớp.`);
    const [x] = await p.sql(`SELECT id FROM sao_ke_dong WHERE phieu_thu_id = :p AND id <> :i`, { p: pt.id, i: d.id }, t);
    if (x) loi('Phiếu thu này đã khớp với dòng sao kê khác.');
    if (pt.trang_thai === 'cho_xac_minh') await goi('phieu_thu:xacMinh', ctx, t, pt.id, { ma_gd: d.ma_gd || pt.ma_gd || `SK${d.id}` });
    else if (pt.trang_thai !== 'da_ghi') loi('Phiếu thu đã hủy / còn nháp.');
    await d.update({ trang_thai: 'da_khop', phieu_thu_id: pt.id, khop_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };
  /** Tạo phiếu thu từ dòng sao kê (chưa có phiếu): có khách → thu nợ (phân bổ sau), không rõ → "chưa rõ người nộp". */
  H['sao_ke_dong:taoThu'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán.');
    const d = await p.khoa('sao_ke_dong', id(ctx), t);
    if (d.trang_thai !== 'chua_khop') loi('Dòng đã khớp / bỏ qua.');
    const v = val(ctx);
    const quy = await bang('quy').findByPk(d.quy_id, { transaction: t });
    const pt = await bang('phieu_thu').create({ ngay: d.ngay, khach_id: v.khach_id || null, don_vi_id: quy.don_vi_id, hinh_thuc: 'chuyen_khoan', so_tien: d.so_tien,
      ma_gd: d.ma_gd || `SK${d.id}`, quy_id: d.quy_id, loai_thu: v.khach_id ? 'thu_no' : 'chua_ro', nguoi_nop: v.nguoi_nop || null,
      ghi_chu: `Từ sao kê: ${String(d.noi_dung || '').slice(0, 200)}`, request_id: `SK-${d.id}` }, { transaction: t });
    ctx.state.aphDaXacMinh = true;
    try { await goi('phieu_thu:ghi', ctx, t, pt.id); } finally { ctx.state.aphDaXacMinh = false; }
    await bang('phieu_thu').update({ xac_minh_boi: p.nguoi(ctx) }, { where: { id: pt.id }, transaction: t, hooks: false });
    await d.update({ trang_thai: 'da_khop', phieu_thu_id: pt.id, khop_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true, so: pt.so };
  };
  H['sao_ke_dong:boQua'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán.');
    const d = await p.khoa('sao_ke_dong', id(ctx), t);
    if (d.trang_thai === 'da_khop') loi('Dòng đã khớp phiếu thu.');
    if (!lyDo(ctx)) loi('Ghi lý do bỏ qua (lãi NH, nội bộ, phí…).');
    await d.update({ trang_thai: 'bo_qua', noi_dung: `${d.noi_dung || ''} [bỏ qua: ${lyDo(ctx)}]` }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- PHẢI HOÀN ----------------
  /** cach = 'giu' (trả về tiền chưa phân bổ của phiếu thu, khách dùng cho đơn sau khi có lệnh phân bổ) | 'hoan' (phiếu chi hoàn tiền từ quỹ của bên bán). */
  H['don_ban:xuLyHoan'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán xử lý khoản phải hoàn.');
    const don = await p.khoa('don_ban', id(ctx), t);
    await p.tinhCongNo(t, don);
    const ph = tien((await bang('don_ban').findByPk(don.id, { transaction: t })).phai_hoan);
    if (!(ph > 0)) loi('Đơn không có khoản phải hoàn.');
    const v = val(ctx);
    const st = v.so_tien ? tien(v.so_tien) : ph;
    if (!(st > 0) || st > ph) loi(`Số xử lý phải > 0 và ≤ ${vnd(ph)} đ.`);
    if (!['giu', 'hoan'].includes(v.cach)) loi('Chọn: giữ làm tiền chưa phân bổ / hoàn tiền.');
    if (!v.ly_do) loi('Ghi căn cứ (biên bản trả hàng / thỏa thuận).');
    // Gỡ phân bổ từ các phiếu thu mới nhất của chính bên bán (không gỡ thu hộ), trả về chưa phân bổ của phiếu đó.
    const pb = await p.sql(`SELECT b.id, b.so_tien, b.phieu_thu_id FROM phieu_thu_phan_bo b JOIN phieu_thu p ON p.id = b.phieu_thu_id
      WHERE b.don_ban_id = :d AND p.trang_thai = 'da_ghi' AND COALESCE(b.thu_ho,false) = false ORDER BY p.ngay DESC, b.id DESC`, { d: don.id }, t);
    let con = st;
    const go: any[] = [];
    for (const b of pb) {
      if (!con) break;
      const a = Math.min(con, tien(b.so_tien));
      con -= a;
      await bang('phieu_thu_phan_bo').update({ so_tien: tien(b.so_tien) - a }, { where: { id: b.id }, transaction: t, hooks: false });
      const pt = await p.khoa('phieu_thu', b.phieu_thu_id, t);
      await pt.update({ chua_phan_bo: tien(pt.chua_phan_bo) + a }, { transaction: t, choPhep: true } as any);
      go.push({ phieu_thu: pt.so, phieu_thu_id: pt.id, so_tien: a, quy_id: pt.quy_id });
    }
    if (con) loi('Phần phải hoàn còn lại không thuộc phiếu thu của bên bán (thu hộ): xử lý tất toán thu hộ trước.');
    let pc: any = null;
    if (v.cach === 'hoan') {
      const quyId = v.quy_id || go[0]?.quy_id;
      kiemQuy(ctx, quyId);
      const quy = await bang('quy').findByPk(quyId, { transaction: t });
      if (!quy || quy.don_vi_id !== don.don_vi_ban_id) loi('Quỹ hoàn tiền phải thuộc bên bán của đơn.');
      if (quy.loai === 'ngan_hang' && !v.ma_gd) loi('Hoàn qua ngân hàng cần mã giao dịch.');
      const kh = await bang('khach_hang').findByPk(don.khach_id, { transaction: t });
      pc = await bang('phieu_chi').create({ ngay: homNay(), don_vi_id: don.don_vi_ban_id, quy_id: quyId, loai_chi: 'hoan_khach', nguoi_nhan: kh?.ten || 'Khách',
        so_tien: st, ly_do: `Hoàn tiền đơn ${don.so}: ${v.ly_do}`, ma_gd: v.ma_gd || null, hoan_cho_don_id: don.id }, { transaction: t });
      await goi('phieu_chi:ghi', ctx, t, pc.id);
      // Tiền đã hoàn: tiêu phần chưa phân bổ vừa trả lại (không để phiếu thu "còn tiền" ảo).
      for (const g of go) {
        const pt = await p.khoa('phieu_thu', g.phieu_thu_id, t);
        await pt.update({ chua_phan_bo: tien(pt.chua_phan_bo) - g.so_tien }, { transaction: t, choPhep: true } as any);
      }
    }
    await p.tinhCongNo(t, await p.khoa('don_ban', don.id, t));
    return { ok: true, cach: v.cach, so_tien: st, phieu_thu: go, phieu_chi: pc?.so || null };
  };
  const ghiHdGoc = H['don_ban:ghiHoaDon'];
  H['don_ban:ghiHoaDon'] = async (ctx, t) => {
    const [x] = await p.sql(`SELECT COUNT(*)::int AS n FROM hoa_don_cho_xuat WHERE don_ban_id = :d`, { d: id(ctx) }, t);
    if (x.n) loi('Đơn này dùng hàng đợi hóa đơn theo bên bán (Báo cáo → Hàng đợi hóa đơn MISA).');
    return ghiHdGoc(ctx, t);
  };
  const huyChiGoc = H['phieu_chi:huy'];
  H['phieu_chi:huy'] = async (ctx, t) => {
    const pc = await p.khoa('phieu_chi', id(ctx), t);
    if (pc.hoan_cho_don_id && pc.trang_thai === 'da_ghi') loi('Phiếu hoàn tiền đã ghi: không hủy — lập phiếu thu lại khoản khách trả về.');
    return huyChiGoc(ctx, t);
  };
}

export function hookTaiChinh(p: any) {
  const db = p.db;
  for (const b of ['sao_ke', 'sao_ke_dong']) {
    db.on(`${b}.beforeCreate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Sao kê nạp qua "Nạp sao kê".'); });
    db.on(`${b}.beforeUpdate`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ thay đổi qua thao tác khớp / bỏ qua.'); });
    db.on(`${b}.beforeDestroy`, () => loi('Không xóa sao kê.'));
  }
}
