/**
 * 0.4.0 Bán nhanh (POS) — KHÔNG có sổ song song: mỗi lần bán tạo đơn bán kênh "pos" + lượt giao khách nhận + phiếu thu như bán sỉ.
 * - Ca bán gắn thu ngân + quỹ tiền mặt + kho; mỗi thu ngân chỉ một ca mở trên một quỹ.
 * - Thanh toán nhiều hình thức: tiền mặt (vào quỹ ca ngay), chuyển khoản (phiếu thu CHỜ XÁC MINH, chưa trừ nợ), ghi nợ (chỉ khách có mã, theo chính sách tín dụng).
 * - Khách lẻ (mã cấu hình ma_khach_le) phải trả đủ; không ghi nợ khách lẻ.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien, vnd } from '../tienich';
import { kiemKho, kiemQuy } from '../toan_ven';
import { cauHinh } from '../security/cau_hinh';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

export function dangKyPos(p: any, H: H, h: any) {
  const { id, val } = h;
  const bang = (n: string) => p.bang(n);
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);
  const uid = (ctx: any) => ctx.state?.currentUser?.id;

  H['ca_pos:mo'] = async (ctx, t) => {
    const v = val(ctx);
    if (!v.quy_id || !v.kho_id) loi('Chọn quỹ tiền mặt và kho bán.');
    kiemQuy(ctx, v.quy_id);
    kiemKho(ctx, v.kho_id);
    const quy = await p.khoa('quy', v.quy_id, t);
    if (quy.loai !== 'tien_mat') loi('Ca bán gắn với quỹ tiền mặt.');
    const kho = await bang('kho').findByPk(v.kho_id, { transaction: t });
    if (kho?.trung_chuyen || kho?.loai_kho === 'cho_xu_ly') loi('Không bán từ kho trung chuyển / chờ xử lý.');
    const mo = await bang('ca_pos').findOne({ where: { quy_id: v.quy_id, trang_thai: 'mo' }, transaction: t });
    if (mo) {
      if (Number(mo.thu_ngan_id) === Number(uid(ctx))) return { ok: true, da_mo_truoc: true, id: mo.id, so: mo.so };
      loi(`Quỹ ${quy.ten} đang có ca ${mo.so} của ${mo.thu_ngan} chưa chốt.`);
    }
    const ca = await bang('ca_pos').create({ quy_id: v.quy_id, kho_id: v.kho_id, don_vi_id: v.don_vi_id || quy.don_vi_id, thu_ngan: p.nguoi(ctx), thu_ngan_id: uid(ctx),
      mo_luc: new Date().toISOString(), tien_dau_ca: tien(v.tien_dau_ca), trang_thai: 'mo' }, { transaction: t, hooks: false });
    return { ok: true, id: ca.id, so: ca.so };
  };

  /** values: {ca_pos_id, khach_id?, request_id, dong:[{mat_hang_id, dvt_nhap?, sl_nhap? | so_kg, so_bao?, don_gia?, vat_ap_dung?}], thanh_toan:[{hinh_thuc, so_tien, quy_id?, ma_gd?}], khach_dua?} */
  H['ca_pos:ban'] = async (ctx, t) => {
    const v = val(ctx);
    if (!v.request_id) loi('Thiếu mã yêu cầu (chống bấm trùng).');
    const co = await bang('don_ban').findOne({ where: { request_id: v.request_id }, transaction: t });
    if (co) return { ok: true, da_ban_truoc: true, so: co.so, id: co.id };
    const ca = await p.khoa('ca_pos', v.ca_pos_id, t);
    if (ca.trang_thai !== 'mo') loi('Ca đã chốt: mở ca mới.');
    if (Number(ca.thu_ngan_id) !== Number(uid(ctx)) && !p.xemGia(ctx)) loi('Ca này của thu ngân khác.');
    const maLe = await cauHinh(p, 'ma_khach_le', t);
    let khachId = v.khach_id;
    if (!khachId) {
      const kl = await bang('khach_hang').findOne({ where: { ma: maLe }, transaction: t });
      if (!kl) loi(`Chưa có khách lẻ mã ${maLe}: tạo trong danh mục khách.`);
      khachId = kl.id;
    }
    const kh = await bang('khach_hang').findByPk(khachId, { transaction: t });
    const laKhachLe = kh?.ma === maLe;
    const dong = (v.dong || []).filter((d: any) => Number(d.sl_nhap || d.so_kg) > 0);
    if (!dong.length) loi('Chưa có hàng.');
    const don = await bang('don_ban').create({ loai: 'ban', kenh: 'pos', khach_id: khachId, don_vi_ban_id: ca.don_vi_id, ngay: homNay(), ngay_giao: homNay(),
      cach_giao: 'khach_den_lay', ca_pos_id: ca.id, request_id: v.request_id, xuat_hoa_don: !!v.xuat_hoa_don, ghi_chu: v.ghi_chu || `Bán nhanh ca ${ca.so}` },
    { transaction: t });
    for (const d of dong) {
      await bang('don_ban_dong').create({ don_ban_id: don.id, mat_hang_id: d.mat_hang_id, kho_id: ca.kho_id, dvt_nhap: d.dvt_nhap || null, sl_nhap: d.sl_nhap ?? null,
        so_kg: d.sl_nhap ? undefined : d.so_kg, so_bao: d.so_bao ?? null, don_gia: d.don_gia ?? null, vat_ap_dung: !!d.vat_ap_dung, ly_do_sua_gia: d.ly_do_sua_gia || null },
      { transaction: t });
    }
    const r = await goi('don_ban:chotDon', ctx, t, don.id);
    if (r?.cho_duyet) loi(`Đơn cần duyệt (${r.ly_do}) — bán nhanh không chờ duyệt: chuyển sang đơn sỉ hoặc nhờ quản lý.`);
    const dd = await bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t, order: [['id', 'ASC']] });
    const lg = await goi('luot_giao:taoLuot', ctx, t, null, { don_ban_id: don.id, cach_giao: 'khach_den_lay', request_id: `${v.request_id}-L`,
      dong: dd.map((x: any) => ({ don_ban_dong_id: x.id, so_kg: x.so_kg, so_bao: x.so_bao })) });
    await goi('luot_giao:khachNhan', ctx, t, lg.id, { thuc: v.thuc || {} });
    const sau = await p.khoa('don_ban', don.id, t);
    const phai = tien(sau.phai_thu);
    const tt = (v.thanh_toan || []).filter((x: any) => tien(x.so_tien) > 0);
    const tm = tt.filter((x: any) => x.hinh_thuc === 'tien_mat').reduce((a: number, x: any) => a + tien(x.so_tien), 0);
    const ck = tt.filter((x: any) => x.hinh_thuc === 'chuyen_khoan').reduce((a: number, x: any) => a + tien(x.so_tien), 0);
    const no = tt.filter((x: any) => x.hinh_thuc === 'ghi_no').reduce((a: number, x: any) => a + tien(x.so_tien), 0);
    if (tt.some((x: any) => !['tien_mat', 'chuyen_khoan', 'ghi_no'].includes(x.hinh_thuc))) loi('Hình thức thanh toán không hợp lệ.');
    // Tiền mặt khách đưa dư: chỉ thu đúng phần phải trả, phần dư là tiền thối lại.
    const tmThu = Math.min(tm, Math.max(0, phai - ck));
    const conLai = phai - tmThu - ck;
    if (ck > phai) loi(`Chuyển khoản ${vnd(ck)} đ lớn hơn tiền hàng ${vnd(phai)} đ.`);
    if (laKhachLe && conLai > 0) loi(`Khách lẻ phải trả đủ ${vnd(phai)} đ (còn thiếu ${vnd(conLai)} đ). Ghi nợ cần chọn khách có mã.`);
    if (conLai > 0 && no + 0.5 < conLai) loi(`Còn ${vnd(conLai)} đ chưa thanh toán: thêm tiền hoặc chọn "Ghi nợ".`);
    const thu: string[] = [];
    if (tmThu > 0) {
      const pt = await bang('phieu_thu').create({ ngay: homNay(), khach_id: khachId, don_vi_id: ca.don_vi_id, hinh_thuc: 'tien_mat', so_tien: tmThu, quy_id: ca.quy_id,
        loai_thu: 'thu_no', ca_pos_id: ca.id, request_id: `${v.request_id}-TM`, nguoi_nop: kh?.ten},
      { transaction: t });
      await bang('phieu_thu_phan_bo').create({ phieu_thu_id: pt.id, don_ban_id: don.id, so_tien: tmThu }, { transaction: t });
      await goi('phieu_thu:ghi', ctx, t, pt.id);
      thu.push(pt.so);
    }
    let i = 0;
    for (const x of tt.filter((x: any) => x.hinh_thuc === 'chuyen_khoan')) {
      if (!x.quy_id) loi('Chuyển khoản: chọn tài khoản ngân hàng nhận.');
      kiemQuy(ctx, x.quy_id);
      const q = await bang('quy').findByPk(x.quy_id, { transaction: t });
      if (!q || q.loai !== 'ngan_hang' || q.don_vi_id !== ca.don_vi_id) loi('Tài khoản nhận chuyển khoản phải là tài khoản ngân hàng của bên bán.');
      const pt = await bang('phieu_thu').create({ ngay: homNay(), khach_id: khachId, don_vi_id: ca.don_vi_id, hinh_thuc: 'chuyen_khoan', so_tien: tien(x.so_tien),
        quy_id: x.quy_id, ma_gd: x.ma_gd || null, loai_thu: 'thu_no', ca_pos_id: ca.id, request_id: `${v.request_id}-CK${i++}`, nguoi_nop: kh?.ten }, { transaction: t });
      await bang('phieu_thu_phan_bo').create({ phieu_thu_id: pt.id, don_ban_id: don.id, so_tien: tien(x.so_tien) }, { transaction: t });
      await goi('phieu_thu:baoChuyen', ctx, t, pt.id);
      thu.push(pt.so);
    }
    await ca.update({ thu_tien_mat: tien(ca.thu_tien_mat) + tmThu, thu_ck: tien(ca.thu_ck) + ck, ghi_no: tien(ca.ghi_no) + Math.max(0, conLai),
      so_don: Number(ca.so_don || 0) + 1 }, { transaction: t, hooks: false });
    return { ok: true, id: don.id, so: sau.so, phai_thu: phai, tien_mat: tmThu, tien_thoi: tm - tmThu, chuyen_khoan_cho_xac_minh: ck, ghi_no: Math.max(0, conLai), phieu_thu: thu };
  };

  H['ca_pos:chot'] = async (ctx, t) => {
    const ca = await p.khoa('ca_pos', id(ctx), t);
    if (ca.trang_thai === 'da_chot') return { ok: true, da_chot_truoc: true };
    if (Number(ca.thu_ngan_id) !== Number(uid(ctx)) && !p.xemGia(ctx)) loi('Ca này của thu ngân khác.');
    const v = val(ctx);
    if (v.thuc_dem === undefined || v.thuc_dem === null || v.thuc_dem === '') loi('Nhập số tiền mặt thực đếm cuối ca.');
    // Số phải có = tiền đầu ca + tiền mặt thu trong ca (theo phiếu thu đã ghi của ca) − chi trong ca (nếu có phiếu chi gắn ca).
    const [r] = await p.sql(`SELECT COALESCE(SUM(so_tien),0) AS v FROM phieu_thu WHERE ca_pos_id = :c AND hinh_thuc = 'tien_mat' AND trang_thai = 'da_ghi'`, { c: ca.id }, t);
    const so_sach = tien(ca.tien_dau_ca) + tien(r.v);
    const chenh = tien(v.thuc_dem) - so_sach;
    if (chenh !== 0 && !v.ly_do) loi(`Lệch ${vnd(chenh)} đ so với phải có ${vnd(so_sach)} đ: ghi lý do.`);
    const [ck] = await p.sql(`SELECT COUNT(*)::int AS n, COALESCE(SUM(so_tien),0) AS v FROM phieu_thu WHERE ca_pos_id = :c AND trang_thai = 'cho_xac_minh'`, { c: ca.id }, t);
    await ca.update({ trang_thai: 'da_chot', dong_luc: new Date().toISOString(), thuc_dem: tien(v.thuc_dem), chenh_lech: chenh, ly_do: v.ly_do || null,
      thu_tien_mat: tien(r.v) }, { transaction: t, hooks: false });
    return { ok: true, so_sach, chenh_lech: chenh, ck_cho_xac_minh: { so_phieu: ck.n, so_tien: tien(ck.v) },
      canh_bao: chenh ? 'Chênh lệch tiền mặt không tự điều chỉnh quỹ: kế toán xử lý bằng phiếu thu / chi có lý do.' : null };
  };
  void kg;
}
