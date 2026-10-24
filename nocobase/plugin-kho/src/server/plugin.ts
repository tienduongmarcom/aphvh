/**
 * APH-VH — sổ vận hành trên NocoBase (0.3.0, 24/10/2026).
 *
 * Nguyên tắc (không tự suy diễn ngoài các điểm này):
 * - Tồn kho = mã hàng × kho vật lý, KHÔNG chia đơn vị sở hữu. Số lượng theo ĐVT tồn của mặt hàng (Kg, Cái, Gói…).
 *   Khả dụng = tồn vật lý − đang giữ cho lượt giao − chờ định giá. Mọi thay đổi tồn đi qua SỔ KHO, khóa dòng tồn (FOR UPDATE).
 * - Giá vốn quản trị bình quân gia quyền theo MẶT HÀNG × KHO. Hàng chờ định giá không vào giá trị và không bán được.
 *   Chuyển kho mang giá trị xuất thực tế sang kho nhận. Đây là giá vốn quản trị, không phải sổ kế toán pháp nhân (MISA).
 * - Đơn bán: chốt → tạo LƯỢT GIAO (giữ hàng) → bàn giao xe / khách nhận (trừ kho + ghi phải thu một lần) → khách nhận sau chỉ đổi trạng thái.
 *   Đơn đã giao KHÔNG hủy được: hàng về kho chỉ qua phiếu TRẢ HÀNG theo lượng thực nhận; giảm giá qua phiếu GIẢM GIÁ.
 * - Thu tiền: trả đúng đơn được chọn, không FIFO, không cấn chéo đơn vị. Thu hộ giữa đơn vị chỉ qua phân bổ thu hộ của kế toán
 *   (ghi khoản giữ hộ riêng, không chuyển tiền giữa tài khoản). Tiền chưa rõ người nộp / tiền cọc nằm ở chưa phân bổ.
 * - Mọi thao tác ghi: một giao dịch, khóa chứng từ gốc, kiểm trạng thái (bấm lặp/thử lại chỉ ghi một lần).
 * - Giá vốn, giá thành, giá mua bị cắt khỏi mọi phản hồi API với người không thuộc nhóm kế toán / quản lý.
 */
import { Plugin } from '@nocobase/server';
import { Transaction } from 'sequelize';

const kg = (v: any) => Math.round(Number(v || 0) * 1000) / 1000;
const tien = (v: any) => Math.round(Number(v || 0));
const homNay = () => new Date(Date.now() + 7 * 3600 * 1000).toISOString().slice(0, 10);
const vnd = (v: any) => tien(v).toLocaleString('vi-VN');

class LoiNghiepVu extends Error {
  status = 400;
}
const loi = (msg: string): never => {
  throw new LoiNghiepVu(msg);
};

export const NHOM_XEM_GIA = ['root', 'admin', 'quan_ly', 'ke_toan'];
const TRUONG_GIA_VON = new Set(['gia_von', 'gia_von_da_giao', 'gia_bq', 'gia_bq_sau', 'gia_tri_nvl', 'gia_thanh', 'chi_phi_sx']);
const TRUONG_GIA_MUA = new Set(['don_gia', 'phai_tra', 'da_tra', 'gia_tri', 'thanh_tien']);
const BANG_KHO = new Set(['phieu_kho', 'phieu_kho_dong', 'so_kho', 'ton_kho']);
const BANG_CAM = new Set(['gia_von', 'so_gia_von']);

/** Cắt trường giá vốn ở mọi mức; cắt thêm giá mua khi đọc chứng từ kho (kể cả dòng / phiếu kho được nhúng). */
export function catGia(v: any, catMua: boolean): any {
  if (Array.isArray(v)) return v.map((x) => catGia(x, catMua));
  if (v instanceof Date) return v;
  if (v && typeof v === 'object') {
    const o: any = typeof v.toJSON === 'function' ? v.toJSON() : v;
    const r: any = {};
    for (const [k, x] of Object.entries(o)) {
      if (TRUONG_GIA_VON.has(k)) continue;
      if (catMua && TRUONG_GIA_MUA.has(k)) continue;
      r[k] = x && typeof x === 'object' ? catGia(x, catMua || k === 'phieu_kho') : x;
    }
    return r;
  }
  return v;
}

export class PluginKhoServer extends Plugin {
  daCoKhoa = false;

  bang(name: string) {
    return this.db.getCollection(name).model as any;
  }

  async khoa(name: string, id: any, t: Transaction) {
    const r = await this.bang(name).findOne({ where: { id }, transaction: t, lock: t.LOCK.UPDATE });
    if (!r) loi(`Không tìm thấy chứng từ (${name} ${id}).`);
    return r;
  }

  async sql(q: string, replacements: any, t?: Transaction) {
    const [rows]: any = await this.db.sequelize.query(q, { replacements, transaction: t });
    return rows;
  }

  async damBaoKhoa() {
    if (this.daCoKhoa) return;
    for (const l of [
      'CREATE UNIQUE INDEX IF NOT EXISTS ton_kho_kho_mat_hang ON ton_kho (kho_id, mat_hang_id)',
      'DROP INDEX IF EXISTS gia_von_mat_hang',
      'CREATE UNIQUE INDEX IF NOT EXISTS gia_von_mat_hang_kho ON gia_von (mat_hang_id, kho_id)',
    ]) await this.db.sequelize.query(l);
    this.daCoKhoa = true;
  }

  async matHang(id: any, t: Transaction) {
    const mh = await this.bang('mat_hang').findByPk(id, { transaction: t });
    if (!mh) loi('Không tìm thấy mặt hàng.');
    return mh;
  }
  laKg(mh: any) {
    return !mh?.dvt_ton || mh.dvt_ton === 'kg';
  }
  dvt(mh: any) {
    return ({ kg: 'kg', cai: 'cái', goi: 'gói', bao: 'bao', thung: 'thùng' } as any)[mh?.dvt_ton || 'kg'] || mh?.dvt_ton;
  }

  async dongTon(t: Transaction, kho_id: any, mat_hang_id: any) {
    await this.damBaoKhoa();
    await this.sql(`INSERT INTO ton_kho (kho_id, mat_hang_id, so_kg, so_bao, so_giu, so_cho_gia, "createdAt", "updatedAt")
       VALUES (:k, :m, 0, 0, 0, 0, now(), now()) ON CONFLICT (kho_id, mat_hang_id) DO NOTHING`, { k: kho_id, m: mat_hang_id }, t);
    return this.bang('ton_kho').findOne({ where: { kho_id, mat_hang_id }, transaction: t, lock: t.LOCK.UPDATE });
  }

  async ghiSo(t: Transaction, p: {
    ngay: string; kho_id: any; mat_hang_id: any; so_luong: number; so_bao?: number; loai: string; chung_tu: string; nguon: string; nguon_id: any;
    gia?: number | null; gia_tri?: number | null; choGia?: boolean; giaiPhongGiu?: number; boQuaGia?: boolean; choPhepAm?: boolean;
  }): Promise<number> {
    if (!p.kho_id || !p.mat_hang_id) loi('Dòng hàng thiếu kho hoặc mặt hàng.');
    const q = kg(p.so_luong);
    const b = kg(p.so_bao);
    if (!q && !b) return 0;
    const ton = await this.dongTon(t, p.kho_id, p.mat_hang_id);
    const moi_giu = kg(Number(ton.so_giu || 0) - kg(p.giaiPhongGiu));
    if (q < 0 && !p.choPhepAm) {
      const khaDung = kg(Number(ton.so_kg || 0) - Number(ton.so_cho_gia || 0) - moi_giu);
      if (khaDung + q < -0.0005) {
        const mh = await this.matHang(p.mat_hang_id, t);
        const kho = await this.bang('kho').findByPk(p.kho_id, { transaction: t });
        loi(`Không đủ hàng khả dụng: ${mh.nhan || mh.ma} tại ${kho?.ten} còn ${kg(khaDung)} ${this.dvt(mh)} ` +
          `(tồn ${kg(ton.so_kg)}, đang giữ ${kg(moi_giu)}, chờ định giá ${kg(ton.so_cho_gia)}), cần ${-q}.`);
      }
    }
    await ton.update({
      so_kg: kg(Number(ton.so_kg || 0) + q), so_bao: kg(Number(ton.so_bao || 0) + b), so_giu: Math.max(0, moi_giu),
      so_cho_gia: kg(Number(ton.so_cho_gia || 0) + (p.choGia ? q : 0)),
    }, { transaction: t, hooks: false });
    await this.bang('so_kho').create({ ngay: p.ngay, kho_id: p.kho_id, mat_hang_id: p.mat_hang_id, so_kg: q, so_bao: b, loai: p.loai,
      chung_tu: p.chung_tu, nguon: p.nguon, nguon_id: p.nguon_id }, { transaction: t, hooks: false });
    if (p.boQuaGia || p.choGia || !q) return 0;
    return this.capNhatGia(t, { ngay: p.ngay, mat_hang_id: p.mat_hang_id, kho_id: p.kho_id, so_luong: q, gia: p.gia, gia_tri: p.gia_tri,
      loai: p.loai, chung_tu: p.chung_tu });
  }

  async capNhatGia(t: Transaction, p: { ngay: string; mat_hang_id: any; kho_id: any; so_luong: number; gia?: number | null; gia_tri?: number | null;
    loai: string; chung_tu: string }) {
    await this.damBaoKhoa();
    await this.sql(`INSERT INTO gia_von (mat_hang_id, kho_id, so_kg, gia_tri, gia_bq, "createdAt", "updatedAt")
      VALUES (:m, :k, 0, 0, 0, now(), now()) ON CONFLICT (mat_hang_id, kho_id) DO NOTHING`, { m: p.mat_hang_id, k: p.kho_id }, t);
    const g = await this.bang('gia_von').findOne({ where: { mat_hang_id: p.mat_hang_id, kho_id: p.kho_id }, transaction: t, lock: t.LOCK.UPDATE });
    const bq = Number(g.gia_bq || 0);
    let val: number;
    if (p.gia_tri !== undefined && p.gia_tri !== null) val = tien(p.gia_tri);
    else if (p.so_luong > 0 && p.gia !== undefined && p.gia !== null) val = tien(p.so_luong * Number(p.gia));
    else val = tien(p.so_luong * bq);
    const moi_sl = kg(Number(g.so_kg || 0) + p.so_luong);
    let moi_gt = tien(Number(g.gia_tri || 0) + val);
    let moi_bq = bq;
    if (moi_sl > 0.0005) moi_bq = Math.round((moi_gt / moi_sl) * 100) / 100;
    else if (Math.abs(moi_sl) <= 0.0005) moi_gt = 0;
    await g.update({ so_kg: moi_sl, gia_tri: moi_gt, gia_bq: moi_bq }, { transaction: t, hooks: false });
    await this.bang('so_gia_von').create({ ngay: p.ngay, mat_hang_id: p.mat_hang_id, kho_id: p.kho_id, so_kg: p.so_luong, gia_tri: val,
      gia_bq_sau: moi_bq, loai: p.loai, chung_tu: p.chung_tu }, { transaction: t, hooks: false });
    return val;
  }

  async daoSo(t: Transaction, chung_tu: string, ngay: string, loai: string) {
    const dong = await this.bang('so_kho').findAll({ where: { chung_tu }, transaction: t, order: [['id', 'ASC']] });
    const goc = dong.filter((d: any) => !String(d.loai).startsWith('huy_'));
    // Đảo phần nhập trước (âm), rồi phần xuất (dương) — hủy nhập kiểm khả dụng, không làm âm kho.
    for (const d of [...goc].sort((a: any, b: any) => b.so_kg - a.so_kg)) {
      await this.ghiSo(t, { ngay, kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, so_luong: -d.so_kg, so_bao: -d.so_bao, loai, chung_tu,
        nguon: d.nguon, nguon_id: d.nguon_id, boQuaGia: true });
    }
    const gv = await this.bang('so_gia_von').findAll({ where: { chung_tu }, transaction: t });
    const gom: Record<string, { mh: any; kho: any; sl: number; gt: number }> = {};
    for (const x of gv) {
      if (String(x.loai).startsWith('huy_')) continue;
      const k = `${x.mat_hang_id}-${x.kho_id}`;
      gom[k] = gom[k] || { mh: x.mat_hang_id, kho: x.kho_id, sl: 0, gt: 0 };
      gom[k].sl += Number(x.so_kg || 0);
      gom[k].gt += Number(x.gia_tri || 0);
    }
    for (const v of Object.values(gom)) {
      if (!kg(v.sl) && !tien(v.gt)) continue;
      await this.capNhatGia(t, { ngay, mat_hang_id: v.mh, kho_id: v.kho, so_luong: -kg(v.sl), gia_tri: -tien(v.gt), loai, chung_tu });
    }
  }

  async ghiQuy(t: Transaction, p: { ngay: string; quy_id: any; so_tien: number; loai: string; chung_tu: string; dien_giai?: string }) {
    if (!p.quy_id) loi('Chưa chọn quỹ / tài khoản tiền.');
    const quy = await this.khoa('quy', p.quy_id, t);
    const [r] = await this.sql('SELECT COALESCE(SUM(so_tien),0) AS du FROM so_quy WHERE quy_id = :q', { q: p.quy_id }, t);
    const du = tien(Number(r.du) + tien(p.so_tien));
    if (quy.loai === 'tien_mat' && p.so_tien < 0 && du < 0) loi(`Quỹ ${quy.ten} chỉ còn ${vnd(r.du)} đ, không chi được ${vnd(-p.so_tien)} đ.`);
    await this.bang('so_quy').create({ ngay: p.ngay, quy_id: p.quy_id, so_tien: tien(p.so_tien), loai: p.loai, chung_tu: p.chung_tu,
      dien_giai: p.dien_giai || '' }, { transaction: t, hooks: false });
    return quy;
  }
  async daoQuy(t: Transaction, chung_tu: string, ngay: string) {
    const dong = await this.bang('so_quy').findAll({ where: { chung_tu }, transaction: t, order: [['id', 'ASC']] });
    const goc = dong.filter((d: any) => !String(d.loai).startsWith('huy_'));
    for (const d of [...goc].sort((a: any, b: any) => b.so_tien - a.so_tien)) {
      await this.ghiQuy(t, { ngay, quy_id: d.quy_id, so_tien: -d.so_tien, loai: 'huy_' + d.loai, chung_tu });
    }
  }

  async tinhCongNo(t: Transaction, don: any) {
    const [a] = await this.sql(`SELECT
        COALESCE((SELECT SUM(thanh_tien) FROM don_ban_dong WHERE don_ban_id = :d), 0) AS tong,
        COALESCE((SELECT SUM(gia_tri) FROM luot_giao WHERE don_ban_id = :d AND trang_thai IN ('da_ban_giao_xe','khach_da_nhan')), 0) AS giao,
        COALESCE((SELECT SUM(gia_von) FROM luot_giao WHERE don_ban_id = :d AND trang_thai IN ('da_ban_giao_xe','khach_da_nhan')), 0) AS gv_giao,
        COALESCE((SELECT SUM(gia_tri) FROM tra_hang WHERE don_ban_id = :d AND trang_thai = 'da_ghi'), 0) AS tra,
        COALESCE((SELECT SUM(so_tien) FROM dieu_chinh_gia WHERE don_ban_id = :d AND trang_thai = 'da_ghi'), 0) AS giam,
        COALESCE((SELECT SUM(b.so_tien) FROM phieu_thu_phan_bo b JOIN phieu_thu p ON p.id = b.phieu_thu_id
                  WHERE b.don_ban_id = :d AND p.trang_thai = 'da_ghi'), 0) AS thu`, { d: don.id }, t);
    const v: any = { da_thu: tien(a.thu) };
    if (don.loai === 'dau_ky') {
      v.phai_thu = tien(don.tong_tien);
    } else {
      v.tong_tien = tien(a.tong);
      v.gia_tri_giao = tien(a.giao);
      v.gia_tri_tra = tien(a.tra);
      v.giam_gia = tien(a.giam);
      v.phai_thu = tien(a.giao) - tien(a.tra) - tien(a.giam);
      const [gvTra] = await this.sql(`SELECT COALESCE(SUM(g.gia_tri),0) AS v FROM so_gia_von g JOIN tra_hang h ON g.chung_tu = h.so
        WHERE h.don_ban_id = :d AND h.trang_thai = 'da_ghi'`, { d: don.id }, t);
      v.gia_von = tien(a.gv_giao) - tien(gvTra.v);
    }
    if (don.trang_thai === 'da_huy') v.phai_thu = 0;
    v.con_no = v.phai_thu - v.da_thu;
    await don.update(v, { transaction: t, hooks: false });
    return v;
  }

  async capNhatTrangThaiDon(t: Transaction, don: any) {
    if (['da_huy', 'da_dong', 'nhap', 'cho_duyet'].includes(don.trang_thai) || don.loai === 'dau_ky') return;
    const dong = await this.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t });
    const du = dong.every((d: any) => kg(d.da_giao) >= kg(d.so_kg) - 0.0005);
    const co = dong.some((d: any) => kg(d.da_giao) > 0);
    const capNhat: any = { trang_thai: du ? 'da_giao' : co ? 'dang_giao' : 'cho_xuat' };
    if (don.xuat_hoa_don && co && don.trang_thai_hd !== 'da_xuat') capNhat.trang_thai_hd = 'cho_xuat';
    await don.update(capNhat, { transaction: t, hooks: false });
  }

  nguoi(ctx: any) {
    const u = ctx.state?.currentUser;
    return u ? u.nickname || u.username || u.email || String(u.id) : '';
  }
  xemGia(ctx: any) {
    const roles: string[] = [].concat(ctx.state?.currentRoles || [], ctx.state?.currentRole || []);
    return roles.some((r) => NHOM_XEM_GIA.includes(r));
  }

  async beforeLoad() {
    const db = this.db;
    const tenHienThi = (b: string, f: (m: any) => string) => db.on(`${b}.beforeSave`, (m: any) => m.set('nhan', f(m)));
    tenHienThi('mat_hang', (m) => [m.get('ma'), m.get('ten')].filter(Boolean).join(' – '));
    tenHienThi('khach_hang', (m) => [m.get('ten'), m.get('sdt')].filter(Boolean).join(' – '));
    tenHienThi('nha_cung_cap', (m) => [m.get('ten'), m.get('sdt')].filter(Boolean).join(' – '));
    for (const b of ['kho', 'don_vi', 'quy']) tenHienThi(b, (m) => m.get('ten'));

    const khoaSua = (b: string, choSua: string[] = ['ghi_chu', 'updatedAt', 'updatedById']) => {
      db.on(`${b}.beforeUpdate`, (m: any, opts: any) => {
        const truoc = m.previous('trang_thai');
        if (opts?.choPhep || !truoc || truoc === 'nhap') return;
        const doi = (m.changed() || []).filter((k: string) => !choSua.includes(k));
        if (doi.length) loi('Chứng từ đã ghi / đã chốt / đã hủy: không sửa được. Dùng thao tác nghiệp vụ tương ứng.');
      });
    };
    for (const b of ['phieu_kho', 'phieu_chi', 'chuyen_tien', 'tra_hang', 'dieu_chinh_gia', 'phieu_thu']) khoaSua(b);
    khoaSua('don_ban', ['ghi_chu', 'updatedAt', 'updatedById', 'nguoi_nhan', 'bien_so', 'dia_chi_giao', 'sdt']);
    db.on('luot_giao.beforeUpdate', (m: any, opts: any) => {
      if (!opts?.choPhep && (m.changed() || []).some((k: string) => !['nguoi_nhan', 'bien_so', 'ben_van_chuyen', 'updatedAt', 'updatedById'].includes(k)))
        loi('Lượt giao chỉ thay đổi qua thao tác Bàn giao xe / Khách đã nhận / Hủy lượt.');
    });
    for (const b of ['luot_giao', 'luot_giao_dong', 'thu_ho']) {
      db.on(`${b}.beforeCreate`, (_m: any, opts: any) => { if (!opts?.choPhep) loi('Chỉ tạo qua thao tác nghiệp vụ.'); });
      db.on(`${b}.beforeDestroy`, () => loi('Không xóa được; dùng thao tác hủy.'));
    }
    for (const b of ['phieu_kho', 'don_ban', 'phieu_thu', 'phieu_chi', 'chuyen_tien', 'tra_hang', 'dieu_chinh_gia']) {
      db.on(`${b}.beforeDestroy`, (m: any) => { if (m.get('trang_thai') && m.get('trang_thai') !== 'nhap') loi('Chứng từ đã ghi không xóa được; dùng Hủy.'); });
    }
    for (const b of ['phieu_kho', 'phieu_chi', 'chuyen_tien', 'tra_hang', 'dieu_chinh_gia', 'phieu_thu']) {
      db.on(`${b}.beforeCreate`, (m: any) => {
        if (!m.get('ngay')) m.set('ngay', homNay());
        m.set('trang_thai', 'nhap');
      });
    }
    db.on('don_ban.beforeCreate', async (m: any, { transaction }: any) => {
      if (!m.get('ngay')) m.set('ngay', homNay());
      if (!m.get('ngay_giao')) m.set('ngay_giao', m.get('ngay'));
      if (!m.get('cach_giao')) m.set('cach_giao', 'khach_den_lay');
      m.set('trang_thai', m.get('loai') === 'dau_ky' ? 'da_giao' : 'nhap');
      m.set('trang_thai_hd', 'khong');
      if (m.get('khach_id')) {
        const k = await this.bang('khach_hang').findByPk(m.get('khach_id'), { transaction });
        if (k) {
          if (!m.get('sdt')) m.set('sdt', k.sdt);
          if (!m.get('dia_chi_giao')) m.set('dia_chi_giao', k.dia_chi);
        }
      }
      m.set('da_thu', 0);
      if (m.get('loai') === 'dau_ky') {
        m.set('phai_thu', tien(m.get('tong_tien')));
        m.set('con_no', tien(m.get('tong_tien')));
      }
    });
    db.on('don_ban.beforeUpdate', async (m: any, opts: any) => {
      if (m.changed('khach_id') && m.get('khach_id') && m.previous('trang_thai') === 'nhap') {
        const k = await this.bang('khach_hang').findByPk(m.get('khach_id'), { transaction: opts?.transaction });
        if (k) {
          m.set('sdt', k.sdt);
          m.set('dia_chi_giao', k.dia_chi);
        }
      }
    });
    const dongDon = async (m: any, transaction: any) => {
      const don = await this.bang('don_ban').findByPk(m.get('don_ban_id'), { transaction });
      if (don && don.trang_thai !== 'nhap') loi('Đơn không còn ở trạng thái Nháp: không sửa được hàng trên đơn (bấm Mở lại nếu chưa giao).');
      if (m.get('mat_hang_id')) {
        const mh = await this.bang('mat_hang').findByPk(m.get('mat_hang_id'), { transaction });
        if (mh) {
          m.set('ten_hang', mh.ten);
          if (m.get('don_gia') === null || m.get('don_gia') === undefined) m.set('don_gia', mh.gia_ban);
          if (!m.get('so_kg') && m.get('so_bao') && mh.kg_bao && this.laKg(mh)) m.set('so_kg', kg(Number(m.get('so_bao')) * Number(mh.kg_bao)));
        }
      }
      m.set('thanh_tien', tien(Number(m.get('so_kg') || 0) * Number(m.get('don_gia') || 0)));
    };
    db.on('don_ban_dong.beforeSave', (m: any, opts: any) => (opts?.hooks === false ? undefined : dongDon(m, opts?.transaction)));
    db.on('don_ban_dong.beforeDestroy', async (m: any, { transaction }: any) => {
      const don = await this.bang('don_ban').findByPk(m.get('don_ban_id'), { transaction });
      if (don && don.trang_thai !== 'nhap') loi('Đơn không còn ở trạng thái Nháp: không xóa được dòng hàng.');
    });
    const tinhLai = async (m: any, { transaction }: any) => {
      const don = m.get('don_ban_id') && (await this.bang('don_ban').findByPk(m.get('don_ban_id'), { transaction }));
      if (don && don.loai !== 'dau_ky') await this.tinhCongNo(transaction, don);
    };
    db.on('don_ban_dong.afterSave', tinhLai);
    db.on('don_ban_dong.afterDestroy', tinhLai);

    db.on('phieu_kho_dong.beforeSave', async (m: any, { transaction }: any) => {
      const pk = await this.bang('phieu_kho').findByPk(m.get('phieu_kho_id'), { transaction });
      if (pk && pk.trang_thai !== 'nhap') loi('Phiếu đã ghi sổ hoặc đã hủy: không sửa được dòng hàng.');
      const mh = m.get('mat_hang_id') && (await this.bang('mat_hang').findByPk(m.get('mat_hang_id'), { transaction }));
      if (mh) {
        m.set('ten_hang', mh.ten);
        if (!m.get('so_kg') && m.get('so_bao') && mh.kg_bao && this.laKg(mh)) m.set('so_kg', kg(Number(m.get('so_bao')) * Number(mh.kg_bao)));
      }
    });
    for (const [b, cha, fk] of [['phieu_thu_phan_bo', 'phieu_thu', 'phieu_thu_id'], ['tra_hang_dong', 'tra_hang', 'tra_hang_id']]) {
      db.on(`${b}.beforeSave`, async (m: any, opts: any) => {
        if (opts?.choPhep) return;
        const p = await this.bang(cha).findByPk(m.get(fk), { transaction: opts?.transaction });
        if (p && p.trang_thai !== 'nhap') loi('Chứng từ đã ghi: không sửa được dòng.');
      });
    }
    for (const b of ['so_kho', 'ton_kho', 'so_quy', 'gia_von', 'so_gia_von']) {
      for (const sk of ['beforeCreate', 'beforeUpdate', 'beforeDestroy']) {
        db.on(`${b}.${sk}`, () => loi('Sổ kho, tồn, sổ quỹ, giá vốn chỉ thay đổi qua chứng từ (phiếu kho, lượt giao, trả hàng, phiếu thu / chi).'));
      }
    }
    for (const b of ['don_ban', 'phieu_kho', 'phieu_thu', 'phieu_chi']) {
      db.on(`${b}.beforeCreate`, async (m: any, { transaction }: any) => {
        const r = m.get('request_id');
        if (r && (await this.bang(b).findOne({ where: { request_id: r }, transaction }))) loi('DA_LUU: chứng từ này đã được lưu trước đó (mạng chập chờn).');
      });
    }
  }

  async load() {
    this.app.on('afterStart', () => this.damBaoKhoa().catch((e) => this.log.warn('Chưa tạo khóa: ' + e.message)));

    // Cắt giá vốn / giá mua khỏi mọi phản hồi với người không thuộc nhóm kế toán / quản lý; chặn hẳn bảng giá vốn.
    this.app.resourceManager.use(async (ctx: any, next: any) => {
      const res: string = ctx.action?.resourceName || '';
      const goc = res.split('.')[0];
      if ((BANG_CAM.has(goc) || res.split('.').some((x) => BANG_CAM.has(x))) && !this.xemGia(ctx)) ctx.throw(403, 'Không có quyền xem giá vốn.');
      const ap = ctx.action?.params?.appends;
      if (!this.xemGia(ctx) && ap && [].concat(ap).some((x: string) => /gia_von/.test(String(x)))) ctx.throw(403, 'Không có quyền xem giá vốn.');
      if (['export', 'exportXlsx', 'exportAttachments'].includes(ctx.action?.actionName) && !this.xemGia(ctx)) ctx.throw(403, 'Chỉ kế toán / quản lý xuất dữ liệu.');
      await next();
      if (!this.xemGia(ctx) && ctx.body && typeof ctx.body === 'object') {
        const catMua = BANG_KHO.has(goc) || res.includes('phieu_kho');
        ctx.body = catGia(ctx.body, catMua);
      }
    }, { tag: 'aphvh-cat-gia', after: 'acl' } as any);

    const giaoDich = async (ctx: any, fn: (t: Transaction) => Promise<any>) => {
      try {
        ctx.body = await this.db.sequelize.transaction(fn);
      } catch (e) {
        if (e instanceof LoiNghiepVu) ctx.throw(400, e.message);
        throw e;
      }
    };
    const id = (ctx: any) => {
      const v = ctx.action.params.filterByTk ?? ctx.action.params.values?.id;
      if (!v) ctx.throw(400, 'Thiếu mã chứng từ.');
      return v;
    };
    const val = (ctx: any) => ctx.action.params.values || {};
    const lyDo = (ctx: any) => val(ctx).ly_do || ctx.action.params.ly_do;
    const H: Record<string, (ctx: any, t: Transaction) => Promise<any>> = {};

    // ---------------- KHO ----------------
    H['phieu_kho:ghiSo'] = async (ctx, t) => {
      const pk = await this.khoa('phieu_kho', id(ctx), t);
      if (pk.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pk.so };
      if (pk.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
      const dong = await this.bang('phieu_kho_dong').findAll({ where: { phieu_kho_id: pk.id }, transaction: t, order: [['id', 'ASC']] });
      if (!dong.length) loi('Phiếu chưa có dòng hàng.');
      if (pk.loai === 'chuyen' && (!pk.kho_dich_id || pk.kho_dich_id === pk.kho_id)) loi('Chuyển kho cần kho nhận khác kho xuất.');
      let capNhat: any = {};
      if (pk.loai === 'san_xuat' || pk.loai === 'dong_goi') capNhat = await this.ghiSanXuat(t, pk, dong);
      else {
        let phai_tra = 0;
        for (const d of dong) {
          const q = kg(d.so_kg);
          const b = kg(d.so_bao);
          const c = { ngay: pk.ngay, mat_hang_id: d.mat_hang_id, chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id };
          if (pk.loai === 'nhap' || pk.loai === 'dau_ky') {
            if (q <= 0) loi('Phiếu nhập cần số lượng dương.');
            const coGia = d.don_gia !== null && d.don_gia !== undefined && Number(d.don_gia) > 0;
            // Người không thuộc kế toán không được nhập giá mua: mọi dòng thành chờ định giá.
            const gia = coGia && this.xemGia(ctx);
            await this.ghiSo(t, { ...c, kho_id: pk.kho_id, so_luong: q, so_bao: b, loai: pk.loai, gia: gia ? d.don_gia : null, choGia: !gia });
            await d.update({ trang_thai_gia: gia ? 'co_gia' : 'cho_gia', ...(gia ? {} : { don_gia: null }) }, { transaction: t, hooks: false });
            if (gia) phai_tra += tien(q * Number(d.don_gia));
          } else if (pk.loai === 'xuat') {
            if (q <= 0) loi('Phiếu xuất cần số lượng dương.');
            await this.ghiSo(t, { ...c, kho_id: pk.kho_id, so_luong: -q, so_bao: -b, loai: 'xuat' });
          } else if (pk.loai === 'chuyen') {
            if (q <= 0) loi('Phiếu chuyển cần số lượng dương.');
            const v = await this.ghiSo(t, { ...c, kho_id: pk.kho_id, so_luong: -q, so_bao: -b, loai: 'chuyen_di' });
            await this.ghiSo(t, { ...c, kho_id: pk.kho_dich_id, so_luong: q, so_bao: b, loai: 'chuyen_den', gia_tri: -v });
          } else if (pk.loai === 'kiem_ke') {
            if (!pk.ghi_chu) loi('Điều chỉnh kiểm kê cần ghi lý do ở ô Ghi chú.');
            await this.ghiSo(t, { ...c, kho_id: pk.kho_id, so_luong: q, so_bao: b, loai: 'kiem_ke' });
          } else loi('Loại phiếu không hợp lệ.');
        }
        if (pk.loai === 'nhap') capNhat = { phai_tra };
      }
      await pk.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx), ...capNhat }, { transaction: t, choPhep: true } as any);
      return { ok: true, so: pk.so, ...capNhat };
    };
    H['phieu_kho:huy'] = async (ctx, t) => {
      const pk = await this.khoa('phieu_kho', id(ctx), t);
      if (pk.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
      if (pk.trang_thai === 'da_ghi') {
        if (!lyDo(ctx)) loi('Hủy phiếu đã ghi sổ cần lý do.');
        if (tien(pk.da_tra) > 0) loi('Phiếu nhập đã trả tiền NCC: hủy phiếu chi liên quan trước.');
        const dong = await this.bang('phieu_kho_dong').findAll({ where: { phieu_kho_id: pk.id, trang_thai_gia: 'cho_gia' }, transaction: t });
        for (const d of dong) {
          const ton = await this.dongTon(t, pk.kho_id, d.mat_hang_id);
          await ton.update({ so_cho_gia: Math.max(0, kg(Number(ton.so_cho_gia) - kg(d.so_kg))) }, { transaction: t, hooks: false });
        }
        await this.daoSo(t, pk.so, homNay(), 'huy_' + pk.loai);
      }
      await pk.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['phieu_kho:dinhGia'] = async (ctx, t) => {
      if (!this.xemGia(ctx)) loi('Chỉ kế toán / quản lý định giá hàng nhập.');
      const pk = await this.khoa('phieu_kho', id(ctx), t);
      if (pk.trang_thai !== 'da_ghi' || !['nhap', 'dau_ky'].includes(pk.loai)) loi('Chỉ định giá phiếu nhập đã ghi sổ.');
      const gia = val(ctx).gia || {};
      let them = 0;
      let so = 0;
      for (const [dongId, g] of Object.entries(gia)) {
        const d = await this.khoa('phieu_kho_dong', dongId, t);
        if (d.phieu_kho_id !== pk.id) loi('Dòng không thuộc phiếu.');
        if (d.trang_thai_gia !== 'cho_gia') continue;
        if (!(Number(g) > 0)) loi('Đơn giá phải lớn hơn 0.');
        const ton = await this.dongTon(t, pk.kho_id, d.mat_hang_id);
        await ton.update({ so_cho_gia: Math.max(0, kg(Number(ton.so_cho_gia) - kg(d.so_kg))) }, { transaction: t, hooks: false });
        await this.capNhatGia(t, { ngay: homNay(), mat_hang_id: d.mat_hang_id, kho_id: pk.kho_id, so_luong: kg(d.so_kg), gia: Number(g),
          loai: 'dinh_gia', chung_tu: pk.so });
        await d.update({ don_gia: Number(g), trang_thai_gia: 'co_gia', dinh_gia_boi: this.nguoi(ctx) }, { transaction: t, hooks: false });
        them += tien(kg(d.so_kg) * Number(g));
        so++;
      }
      if (pk.loai === 'nhap') await pk.update({ phai_tra: tien(pk.phai_tra) + them }, { transaction: t, choPhep: true } as any);
      return { ok: true, so_dong: so, gia_tri: them };
    };

    // ---------------- BÁN HÀNG ----------------
    H['don_ban:chotDon'] = async (ctx, t) => {
      const don = await this.khoa('don_ban', id(ctx), t);
      if (['cho_xuat', 'dang_giao', 'da_giao'].includes(don.trang_thai)) return { ok: true, da_chot_truoc: true };
      if (don.trang_thai !== 'nhap') loi('Chỉ chốt được đơn đang Nháp.');
      const dong = await this.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t });
      if (!dong.length) loi('Đơn chưa có hàng.');
      const can: string[] = [];
      for (const d of dong) {
        if (!(kg(d.so_kg) > 0)) loi(`Dòng ${d.ten_hang || ''}: số lượng phải lớn hơn 0.`);
        if (!d.kho_id) loi(`Dòng ${d.ten_hang || ''}: chưa chọn kho xuất dự kiến.`);
        const mh = await this.matHang(d.mat_hang_id, t);
        if (Number(mh.gia_san) > 0 && Number(d.don_gia || 0) < Number(mh.gia_san)) can.push(`${mh.ma} dưới giá sàn`);
      }
      const v = await this.tinhCongNo(t, don);
      const kh = await this.bang('khach_hang').findByPk(don.khach_id, { transaction: t });
      if (Number(kh?.han_muc) > 0) {
        const [r] = await this.sql(`SELECT COALESCE(SUM(con_no),0) AS no FROM don_ban WHERE khach_id = :k AND id <> :d AND trang_thai <> 'da_huy'`,
          { k: don.khach_id, d: don.id }, t);
        if (tien(r.no) + v.tong_tien > Number(kh.han_muc)) can.push(`vượt hạn mức (nợ ${vnd(r.no)} + đơn ${vnd(v.tong_tien)} > ${vnd(kh.han_muc)})`);
      }
      if (can.length && !don.duyet_boi) {
        await don.update({ trang_thai: 'cho_duyet', ly_do_duyet: can.join('; ') }, { transaction: t, choPhep: true } as any);
        return { ok: true, so: don.so, cho_duyet: true, ly_do: can };
      }
      await don.update({ trang_thai: 'cho_xuat' }, { transaction: t, choPhep: true } as any);
      return { ok: true, so: don.so };
    };
    H['don_ban:duyetGia'] = async (ctx, t) => {
      const don = await this.khoa('don_ban', id(ctx), t);
      if (don.trang_thai !== 'cho_duyet') loi('Đơn không ở trạng thái Chờ duyệt.');
      if (!lyDo(ctx)) loi('Ghi lý do đồng ý.');
      await don.update({ trang_thai: 'cho_xuat', duyet_boi: this.nguoi(ctx), ly_do_gia: lyDo(ctx) }, { transaction: t, choPhep: true } as any);
      return { ok: true, so: don.so };
    };
    H['don_ban:moLai'] = async (ctx, t) => {
      const don = await this.khoa('don_ban', id(ctx), t);
      if (!['cho_xuat', 'cho_duyet'].includes(don.trang_thai)) loi('Chỉ mở lại được đơn đã chốt nhưng CHƯA giao lần nào.');
      const [r] = await this.sql(`SELECT COUNT(*)::int AS n FROM luot_giao WHERE don_ban_id = :d AND trang_thai <> 'da_huy'`, { d: don.id }, t);
      if (r.n > 0) loi('Đơn đã có lượt giao: hủy các lượt chưa giao trước khi mở lại.');
      await don.update({ trang_thai: 'nhap', duyet_boi: null, ly_do_gia: null, ly_do_duyet: null }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['don_ban:huy'] = async (ctx, t) => {
      const don = await this.khoa('don_ban', id(ctx), t);
      if (don.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
      const [r] = await this.sql(`SELECT COUNT(*)::int AS n FROM luot_giao WHERE don_ban_id = :d AND trang_thai <> 'da_huy'`, { d: don.id }, t);
      if (r.n > 0) loi('Đơn đã có lượt giao: không hủy được. Hàng khách trả lập phiếu Trả hàng theo lượng thực nhận; hàng chưa giao dùng "Đóng phần chưa giao".');
      if (tien(don.da_thu) > 0) loi('Đơn đã có tiền phân bổ: hủy phiếu thu liên quan trước.');
      if (don.loai === 'dau_ky' && !lyDo(ctx)) loi('Hủy công nợ đầu kỳ cần lý do.');
      await don.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '', phai_thu: 0, con_no: 0 }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['don_ban:dongPhanCon'] = async (ctx, t) => {
      const don = await this.khoa('don_ban', id(ctx), t);
      if (!['cho_xuat', 'dang_giao'].includes(don.trang_thai)) loi('Chỉ đóng phần chưa giao của đơn đang giao.');
      const [r] = await this.sql(`SELECT COUNT(*)::int AS n FROM luot_giao WHERE don_ban_id = :d AND trang_thai = 'cho_xuat'`, { d: don.id }, t);
      if (r.n > 0) loi('Còn lượt đang chờ xuất: giao xong hoặc hủy lượt đó trước.');
      if (!lyDo(ctx)) loi('Ghi lý do đóng phần chưa giao.');
      await don.update({ trang_thai: 'da_dong', ghi_chu: [don.ghi_chu, 'Đóng phần chưa giao: ' + lyDo(ctx)].filter(Boolean).join(' | ') },
        { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['don_ban:ghiHoaDon'] = async (ctx, t) => {
      const don = await this.khoa('don_ban', id(ctx), t);
      const v = val(ctx);
      if (!don.xuat_hoa_don) loi('Đơn không đánh dấu xuất hóa đơn.');
      if (!v.so_hoa_don || !v.ky_hieu_hd) loi('Nhập ký hiệu và số hóa đơn MISA.');
      const trung = await this.bang('don_ban').findOne({ where: { so_hoa_don: v.so_hoa_don, ky_hieu_hd: v.ky_hieu_hd }, transaction: t });
      if (trung && trung.id !== don.id) loi(`Ký hiệu + số hóa đơn đã dùng cho đơn ${trung.so}.`);
      await don.update({ so_hoa_don: v.so_hoa_don, ky_hieu_hd: v.ky_hieu_hd, ngay_hd: v.ngay_hd || homNay(), trang_thai_hd: 'da_xuat' },
        { transaction: t, choPhep: true } as any);
      return { ok: true };
    };

    H['luot_giao:taoLuot'] = async (ctx, t) => {
      const v = val(ctx);
      if (v.request_id) {
        const co = await this.bang('luot_giao').findOne({ where: { request_id: v.request_id }, transaction: t });
        if (co) return { ok: true, da_tao_truoc: true, id: co.id, so: co.so };
      }
      const don = await this.khoa('don_ban', v.don_ban_id, t);
      if (!['cho_xuat', 'dang_giao'].includes(don.trang_thai)) loi('Đơn phải ở trạng thái Đã chốt / Giao một phần mới tạo lượt giao.');
      const dong = (v.dong || []).filter((d: any) => kg(d.so_kg) > 0);
      if (!dong.length) loi('Nhập lượng giao cho ít nhất một dòng.');
      const lg = await this.bang('luot_giao').create({ don_ban_id: don.id, ngay: homNay(), cach_giao: v.cach_giao || don.cach_giao,
        nguoi_nhan: v.nguoi_nhan || don.nguoi_nhan, bien_so: v.bien_so || don.bien_so, ben_van_chuyen: v.ben_van_chuyen || '',
        trang_thai: 'cho_xuat', request_id: v.request_id || null }, { transaction: t, choPhep: true } as any);
      let gia_tri = 0;
      for (const x of dong) {
        const dd = await this.khoa('don_ban_dong', x.don_ban_dong_id, t);
        if (dd.don_ban_id !== don.id) loi('Dòng không thuộc đơn.');
        const con = kg(Number(dd.so_kg) - Number(dd.da_giao || 0) - Number(dd.dang_giu || 0));
        if (kg(x.so_kg) > con + 0.0005) loi(`${dd.ten_hang}: chỉ còn ${con} chưa giao / chưa lập lượt, không lập ${kg(x.so_kg)}.`);
        const kho_id = x.kho_id || dd.kho_id;
        const ton = await this.dongTon(t, kho_id, dd.mat_hang_id);
        const khaDung = kg(Number(ton.so_kg) - Number(ton.so_giu || 0) - Number(ton.so_cho_gia || 0));
        if (khaDung < kg(x.so_kg) - 0.0005) {
          const kho = await this.bang('kho').findByPk(kho_id, { transaction: t });
          loi(`Không đủ hàng khả dụng để giữ: ${dd.ten_hang} tại ${kho?.ten} còn ${khaDung}, cần ${kg(x.so_kg)}.`);
        }
        await ton.update({ so_giu: kg(Number(ton.so_giu || 0) + kg(x.so_kg)) }, { transaction: t, hooks: false });
        await dd.update({ dang_giu: kg(Number(dd.dang_giu || 0) + kg(x.so_kg)) }, { transaction: t, hooks: false });
        const tt = tien(kg(x.so_kg) * Number(dd.don_gia || 0));
        gia_tri += tt;
        await this.bang('luot_giao_dong').create({ luot_giao_id: lg.id, don_ban_dong_id: dd.id, mat_hang_id: dd.mat_hang_id, kho_id,
          so_kg: kg(x.so_kg), so_bao: kg(x.so_bao), don_gia: dd.don_gia, thanh_tien: tt }, { transaction: t, choPhep: true } as any);
      }
      await lg.update({ gia_tri }, { transaction: t, choPhep: true } as any);
      return { ok: true, id: lg.id, so: lg.so };
    };
    const xuatLuot = async (ctx: any, t: Transaction, lg: any, trangThai: string) => {
      const dong = await this.bang('luot_giao_dong').findAll({ where: { luot_giao_id: lg.id }, transaction: t, order: [['id', 'ASC']] });
      let gia_von = 0;
      for (const x of dong) {
        const v = await this.ghiSo(t, { ngay: homNay(), kho_id: x.kho_id, mat_hang_id: x.mat_hang_id, so_luong: -kg(x.so_kg), so_bao: -kg(x.so_bao),
          loai: 'ban', chung_tu: lg.so, nguon: 'luot_giao_dong', nguon_id: x.id, giaiPhongGiu: kg(x.so_kg) });
        gia_von += -v;
        await x.update({ gia_von: -v }, { transaction: t, hooks: false });
        const dd = await this.khoa('don_ban_dong', x.don_ban_dong_id, t);
        await dd.update({ da_giao: kg(Number(dd.da_giao || 0) + kg(x.so_kg)), dang_giu: Math.max(0, kg(Number(dd.dang_giu || 0) - kg(x.so_kg))),
          gia_von_da_giao: tien(Number(dd.gia_von_da_giao || 0) - v) }, { transaction: t, hooks: false });
      }
      const v = val(ctx);
      await lg.update({ trang_thai: trangThai, gia_von: tien(gia_von), xuat_boi: this.nguoi(ctx), nguoi_nhan: v.nguoi_nhan || lg.nguoi_nhan,
        bien_so: v.bien_so || lg.bien_so, ...(trangThai === 'khach_da_nhan' ? { nhan_xac_nhan_boi: this.nguoi(ctx) } : {}) },
        { transaction: t, choPhep: true } as any);
      const don = await this.khoa('don_ban', lg.don_ban_id, t);
      await this.tinhCongNo(t, don);
      await this.capNhatTrangThaiDon(t, don);
    };
    H['luot_giao:banGiaoXe'] = async (ctx, t) => {
      const lg = await this.khoa('luot_giao', id(ctx), t);
      if (['da_ban_giao_xe', 'khach_da_nhan'].includes(lg.trang_thai)) return { ok: true, da_xuat_truoc: true, so: lg.so };
      if (lg.trang_thai !== 'cho_xuat') loi('Lượt đã hủy.');
      if (lg.cach_giao !== 'van_chuyen') loi('Lượt khách đến lấy: bấm "Khách đã nhận".');
      await xuatLuot(ctx, t, lg, 'da_ban_giao_xe');
      return { ok: true, so: lg.so };
    };
    H['luot_giao:khachNhan'] = async (ctx, t) => {
      const lg = await this.khoa('luot_giao', id(ctx), t);
      if (lg.trang_thai === 'khach_da_nhan') return { ok: true, da_nhan_truoc: true, so: lg.so };
      if (lg.trang_thai === 'da_ban_giao_xe') {
        await lg.update({ trang_thai: 'khach_da_nhan', nhan_xac_nhan_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
        return { ok: true, so: lg.so };
      }
      if (lg.trang_thai !== 'cho_xuat') loi('Lượt đã hủy.');
      await xuatLuot(ctx, t, lg, 'khach_da_nhan');
      return { ok: true, so: lg.so };
    };
    H['luot_giao:huy'] = async (ctx, t) => {
      const lg = await this.khoa('luot_giao', id(ctx), t);
      if (lg.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
      if (lg.trang_thai !== 'cho_xuat') loi('Lượt đã xuất: không hủy được. Hàng khách trả lập phiếu Trả hàng.');
      const dong = await this.bang('luot_giao_dong').findAll({ where: { luot_giao_id: lg.id }, transaction: t });
      for (const x of dong) {
        const ton = await this.dongTon(t, x.kho_id, x.mat_hang_id);
        await ton.update({ so_giu: Math.max(0, kg(Number(ton.so_giu || 0) - kg(x.so_kg))) }, { transaction: t, hooks: false });
        const dd = await this.khoa('don_ban_dong', x.don_ban_dong_id, t);
        await dd.update({ dang_giu: Math.max(0, kg(Number(dd.dang_giu || 0) - kg(x.so_kg))) }, { transaction: t, hooks: false });
      }
      await lg.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };

    H['tra_hang:ghi'] = async (ctx, t) => {
      const th = await this.khoa('tra_hang', id(ctx), t);
      if (th.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: th.so };
      if (th.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
      if (!th.ly_do) loi('Ghi lý do trả hàng.');
      const dong = await this.bang('tra_hang_dong').findAll({ where: { tra_hang_id: th.id }, transaction: t });
      if (!dong.length) loi('Phiếu trả chưa có dòng hàng.');
      let gia_tri = 0;
      for (const x of dong) {
        const dd = await this.khoa('don_ban_dong', x.don_ban_dong_id, t);
        if (dd.don_ban_id !== th.don_ban_id) loi('Dòng không thuộc đơn.');
        const duoc = kg(Number(dd.da_giao || 0) - Number(dd.da_tra || 0));
        if (!(kg(x.so_kg) > 0) || kg(x.so_kg) > duoc + 0.0005) loi(`${dd.ten_hang}: chỉ trả được tối đa ${duoc} (đã giao − đã trả).`);
        const dv = kg(dd.da_giao) > 0 ? Number(dd.gia_von_da_giao || 0) / kg(dd.da_giao) : 0;
        await this.ghiSo(t, { ngay: th.ngay, kho_id: th.kho_nhan_id, mat_hang_id: dd.mat_hang_id, so_luong: kg(x.so_kg), loai: 'tra_hang',
          chung_tu: th.so, nguon: 'tra_hang_dong', nguon_id: x.id, gia_tri: tien(kg(x.so_kg) * dv) });
        const tt = tien(kg(x.so_kg) * Number(dd.don_gia || 0));
        gia_tri += tt;
        await x.update({ mat_hang_id: dd.mat_hang_id, don_gia: dd.don_gia, thanh_tien: tt }, { transaction: t, hooks: false });
        await dd.update({ da_tra: kg(Number(dd.da_tra || 0) + kg(x.so_kg)) }, { transaction: t, hooks: false });
      }
      await th.update({ trang_thai: 'da_ghi', gia_tri, ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
      const cn = await this.tinhCongNo(t, await this.khoa('don_ban', th.don_ban_id, t));
      return { ok: true, so: th.so, gia_tri, con_no: cn.con_no };
    };
    H['dieu_chinh_gia:ghi'] = async (ctx, t) => {
      const gg = await this.khoa('dieu_chinh_gia', id(ctx), t);
      if (gg.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true };
      if (gg.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
      if (!(tien(gg.so_tien) > 0)) loi('Nhập số tiền giảm.');
      if (!gg.ly_do) loi('Ghi lý do giảm giá.');
      const don = await this.khoa('don_ban', gg.don_ban_id, t);
      if (tien(gg.so_tien) > tien(don.phai_thu)) loi(`Giảm ${vnd(gg.so_tien)} đ lớn hơn giá trị phải thu của đơn (${vnd(don.phai_thu)} đ).`);
      await gg.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
      const cn = await this.tinhCongNo(t, don);
      return { ok: true, con_no: cn.con_no };
    };
    H['dieu_chinh_gia:huy'] = async (ctx, t) => {
      const gg = await this.khoa('dieu_chinh_gia', id(ctx), t);
      if (gg.trang_thai === 'da_huy') return { ok: true };
      if (gg.trang_thai === 'da_ghi' && !lyDo(ctx)) loi('Hủy cần lý do.');
      await gg.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
      await this.tinhCongNo(t, await this.khoa('don_ban', gg.don_ban_id, t));
      return { ok: true };
    };

    // ---------------- TIỀN ----------------
    const phanBo = async (ctx: any, t: Transaction, pt: any, ds: { don_ban_id: any; so_tien: number }[], thuHo: boolean) => {
      let tong = 0;
      const dung = new Set();
      for (const p of ds) {
        if (dung.has(p.don_ban_id)) loi('Một đơn chỉ chọn một lần trong một lần phân bổ.');
        dung.add(p.don_ban_id);
        const don = await this.khoa('don_ban', p.don_ban_id, t);
        if (!pt.khach_id) loi('Phiếu thu chưa rõ khách: nhận diện khách trước khi phân bổ.');
        if (don.khach_id !== pt.khach_id) loi(`Đơn ${don.so} không phải của khách trên phiếu thu.`);
        const khacDv = don.don_vi_ban_id !== pt.don_vi_id;
        if (khacDv && !thuHo) loi(`Đơn ${don.so} thuộc đơn vị khác: tiền nhận vào đơn vị này không trả nợ đơn vị khác (kế toán dùng "Phân bổ thu hộ").`);
        if (!khacDv && thuHo) loi(`Đơn ${don.so} cùng đơn vị: dùng phân bổ thường.`);
        const a = tien(p.so_tien);
        if (a <= 0) loi(`Số tiền trả cho đơn ${don.so} phải lớn hơn 0.`);
        const cn = await this.tinhCongNo(t, don);
        if (a > cn.con_no) loi(`Đơn ${don.so} còn nợ ${vnd(cn.con_no)} đ, không trả quá số này.`);
        await this.bang('phieu_thu_phan_bo').create({ phieu_thu_id: pt.id, don_ban_id: don.id, so_tien: a, thu_ho: thuHo,
          phan_bo_boi: this.nguoi(ctx), ngay_phan_bo: homNay() }, { transaction: t, choPhep: true } as any);
        if (thuHo) {
          await this.bang('thu_ho').create({ phieu_thu_id: pt.id, don_vi_nhan_id: pt.don_vi_id, don_vi_chu_no_id: don.don_vi_ban_id, don_ban_id: don.id,
            so_tien: a, trang_thai: 'dang_giu_ho', nguoi_phan_bo: this.nguoi(ctx), ghi_chu: val(ctx).ghi_chu || '' }, { transaction: t, choPhep: true } as any);
        }
        await this.tinhCongNo(t, don);
        tong += a;
      }
      if (tong > tien(pt.chua_phan_bo)) loi(`Tổng phân bổ ${vnd(tong)} đ lớn hơn số chưa phân bổ ${vnd(pt.chua_phan_bo)} đ.`);
      await pt.update({ chua_phan_bo: tien(pt.chua_phan_bo) - tong }, { transaction: t, choPhep: true } as any);
      return tong;
    };
    H['phieu_thu:ghi'] = async (ctx, t) => {
      const pt = await this.khoa('phieu_thu', id(ctx), t);
      if (pt.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pt.so };
      if (pt.trang_thai !== 'nhap') loi('Phiếu thu đã hủy.');
      const so_tien = tien(pt.so_tien);
      if (so_tien <= 0) loi('Nhập số tiền thực nhận.');
      if (!pt.khach_id && pt.loai_thu !== 'chua_ro') loi('Chọn khách, hoặc chọn loại "Chưa rõ người nộp".');
      if (pt.hinh_thuc === 'chuyen_khoan' && !pt.ma_gd) loi('Chuyển khoản cần mã giao dịch / nội dung chuyển khoản.');
      if (!pt.quy_id) loi('Chọn quỹ / tài khoản nhận tiền.');
      const quy = await this.bang('quy').findByPk(pt.quy_id, { transaction: t });
      if (quy.don_vi_id !== pt.don_vi_id) loi('Quỹ / tài khoản nhận không thuộc đơn vị nhận tiền.');
      if ((pt.hinh_thuc === 'tien_mat') !== (quy.loai === 'tien_mat')) loi('Tiền mặt vào quỹ tiền mặt; chuyển khoản vào tài khoản ngân hàng.');
      const nhap = await this.bang('phieu_thu_phan_bo').findAll({ where: { phieu_thu_id: pt.id }, transaction: t, order: [['id', 'ASC']] });
      if (nhap.length && pt.loai_thu !== 'thu_no') loi('Tiền cọc / chưa rõ người nộp không phân bổ lúc ghi; phân bổ sau khi xác minh.');
      await this.ghiQuy(t, { ngay: pt.ngay, quy_id: pt.quy_id, so_tien, loai: 'thu', chung_tu: pt.so,
        dien_giai: pt.loai_thu === 'coc' ? 'Đặt cọc: ' + (pt.muc_dich_coc || '') : pt.loai_thu === 'chua_ro' ? 'Chưa rõ người nộp' : 'Thu tiền khách' });
      await pt.update({ trang_thai: 'da_ghi', chua_phan_bo: so_tien, ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
      if (nhap.length) {
        const ds = nhap.map((x: any) => ({ don_ban_id: x.don_ban_id, so_tien: x.so_tien }));
        for (const x of nhap) await x.destroy({ transaction: t, hooks: false });
        await phanBo(ctx, t, pt, ds, false);
      }
      const moi = await this.bang('phieu_thu').findByPk(pt.id, { transaction: t });
      return { ok: true, so: pt.so, chua_phan_bo: tien(moi.chua_phan_bo) };
    };
    H['phieu_thu:phanBo'] = async (ctx, t) => {
      const pt = await this.khoa('phieu_thu', id(ctx), t);
      if (pt.trang_thai !== 'da_ghi') loi('Chỉ phân bổ phiếu thu đã ghi.');
      return { ok: true, da_phan_bo: await phanBo(ctx, t, pt, val(ctx).phan_bo || [], false) };
    };
    H['phieu_thu:phanBoThuHo'] = async (ctx, t) => {
      if (!this.xemGia(ctx)) loi('Chỉ kế toán / quản lý phân bổ thu hộ giữa các đơn vị.');
      const pt = await this.khoa('phieu_thu', id(ctx), t);
      if (pt.trang_thai !== 'da_ghi') loi('Chỉ phân bổ phiếu thu đã ghi.');
      if (!val(ctx).ghi_chu) loi('Ghi căn cứ thu hộ (vd. khách xác nhận chuyển nhầm tài khoản / thỏa thuận thu hộ).');
      return { ok: true, da_phan_bo: await phanBo(ctx, t, pt, val(ctx).phan_bo || [], true) };
    };
    H['phieu_thu:nhanDien'] = async (ctx, t) => {
      const pt = await this.khoa('phieu_thu', id(ctx), t);
      if (pt.trang_thai !== 'da_ghi' || pt.khach_id) loi('Chỉ nhận diện phiếu thu đã ghi và chưa có khách.');
      if (!val(ctx).khach_id) loi('Chọn khách.');
      await pt.update({ khach_id: val(ctx).khach_id, loai_thu: 'thu_no' }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['phieu_thu:huy'] = async (ctx, t) => {
      const pt = await this.khoa('phieu_thu', id(ctx), t);
      if (pt.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
      if (pt.trang_thai === 'da_ghi') {
        if (!lyDo(ctx)) loi('Hủy phiếu thu đã ghi cần lý do.');
        await this.daoQuy(t, pt.so, homNay());
        await this.sql(`UPDATE thu_ho SET trang_thai = 'da_huy', "updatedAt" = now() WHERE phieu_thu_id = :p`, { p: pt.id }, t);
      }
      await pt.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '', chua_phan_bo: 0 }, { transaction: t, choPhep: true } as any);
      const ds = await this.bang('phieu_thu_phan_bo').findAll({ where: { phieu_thu_id: pt.id }, transaction: t });
      for (const p of ds) await this.tinhCongNo(t, await this.khoa('don_ban', p.don_ban_id, t));
      return { ok: true };
    };
    H['thu_ho:tatToan'] = async (ctx, t) => {
      if (!this.xemGia(ctx)) loi('Chỉ kế toán / quản lý.');
      const th = await this.khoa('thu_ho', id(ctx), t);
      if (th.trang_thai !== 'dang_giu_ho') loi('Khoản thu hộ không ở trạng thái đang giữ hộ.');
      if (!val(ctx).ghi_chu) loi('Ghi căn cứ tất toán (chứng từ giữa hai đơn vị).');
      await th.update({ trang_thai: 'da_tat_toan', ghi_chu: [th.ghi_chu, 'Tất toán: ' + val(ctx).ghi_chu].filter(Boolean).join(' | ') },
        { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['phieu_chi:ghi'] = async (ctx, t) => {
      const pc = await this.khoa('phieu_chi', id(ctx), t);
      if (pc.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pc.so };
      if (pc.trang_thai !== 'nhap') loi('Phiếu chi đã hủy.');
      if (!(tien(pc.so_tien) > 0)) loi('Nhập số tiền chi.');
      if (!pc.ly_do) loi('Ghi lý do chi.');
      const quy = await this.bang('quy').findByPk(pc.quy_id, { transaction: t });
      if (!quy || quy.don_vi_id !== pc.don_vi_id) loi('Quỹ chi không thuộc đơn vị chi.');
      if (quy.loai === 'ngan_hang' && !pc.ma_gd) loi('Chi qua ngân hàng cần mã giao dịch.');
      if (pc.phieu_kho_id) {
        const pk = await this.khoa('phieu_kho', pc.phieu_kho_id, t);
        if (pk.trang_thai !== 'da_ghi' || pk.loai !== 'nhap') loi('Chỉ trả tiền cho phiếu nhập đã ghi sổ.');
        if (pc.nha_cung_cap_id && pk.nha_cung_cap_id !== pc.nha_cung_cap_id) loi('Phiếu nhập không phải của nhà cung cấp này.');
        const con = tien(pk.phai_tra) - tien(pk.da_tra);
        if (tien(pc.so_tien) > con) loi(`Phiếu nhập ${pk.so} còn phải trả ${vnd(con)} đ (hàng chờ định giá chưa tính).`);
        await pk.update({ da_tra: tien(pk.da_tra) + tien(pc.so_tien) }, { transaction: t, choPhep: true } as any);
      }
      await this.ghiQuy(t, { ngay: pc.ngay, quy_id: pc.quy_id, so_tien: -tien(pc.so_tien), loai: 'chi', chung_tu: pc.so, dien_giai: pc.ly_do });
      await pc.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
      return { ok: true, so: pc.so };
    };
    H['phieu_chi:huy'] = async (ctx, t) => {
      const pc = await this.khoa('phieu_chi', id(ctx), t);
      if (pc.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
      if (pc.trang_thai === 'da_ghi') {
        if (!lyDo(ctx)) loi('Hủy phiếu chi đã ghi cần lý do.');
        await this.daoQuy(t, pc.so, homNay());
        if (pc.phieu_kho_id) {
          const pk = await this.khoa('phieu_kho', pc.phieu_kho_id, t);
          await pk.update({ da_tra: tien(pk.da_tra) - tien(pc.so_tien) }, { transaction: t, choPhep: true } as any);
        }
      }
      await pc.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['chuyen_tien:ghi'] = async (ctx, t) => {
      const ct = await this.khoa('chuyen_tien', id(ctx), t);
      if (ct.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: ct.so };
      if (ct.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
      if (!(tien(ct.so_tien) > 0)) loi('Nhập số tiền.');
      if (ct.tu_quy_id === ct.den_quy_id) loi('Quỹ đi và quỹ đến phải khác nhau.');
      const [a, b] = await Promise.all([this.bang('quy').findByPk(ct.tu_quy_id, { transaction: t }), this.bang('quy').findByPk(ct.den_quy_id, { transaction: t })]);
      if (a.don_vi_id !== b.don_vi_id) loi('Chỉ chuyển giữa các quỹ cùng một đơn vị. Tiền giữa hai đơn vị không ghi ở đây.');
      await this.ghiQuy(t, { ngay: ct.ngay, quy_id: ct.tu_quy_id, so_tien: -tien(ct.so_tien), loai: 'chuyen_di', chung_tu: ct.so, dien_giai: `Bàn giao cho ${ct.nguoi_nhan || b.ten}` });
      await this.ghiQuy(t, { ngay: ct.ngay, quy_id: ct.den_quy_id, so_tien: tien(ct.so_tien), loai: 'chuyen_den', chung_tu: ct.so, dien_giai: `Nhận từ ${ct.nguoi_giao || a.ten}` });
      await ct.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
      return { ok: true, so: ct.so };
    };
    H['chuyen_tien:huy'] = async (ctx, t) => {
      const ct = await this.khoa('chuyen_tien', id(ctx), t);
      if (ct.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
      if (ct.trang_thai === 'da_ghi') {
        if (!lyDo(ctx)) loi('Hủy phiếu đã ghi cần lý do.');
        await this.daoQuy(t, ct.so, homNay());
      }
      await ct.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
      return { ok: true };
    };
    H['chot_ca:chot'] = async (ctx, t) => {
      const v = val(ctx);
      if (!v.quy_id) loi('Chọn quỹ tiền mặt.');
      if (v.thuc_dem === undefined || v.thuc_dem === null || v.thuc_dem === '') loi('Nhập số tiền thực đếm.');
      const quy = await this.khoa('quy', v.quy_id, t);
      if (quy.loai !== 'tien_mat') loi('Chốt ca chỉ áp dụng cho quỹ tiền mặt.');
      const [r] = await this.sql('SELECT COALESCE(SUM(so_tien),0) AS du FROM so_quy WHERE quy_id = :q', { q: v.quy_id }, t);
      const so_sach = tien(r.du);
      const chenh = tien(v.thuc_dem) - so_sach;
      if (chenh !== 0 && !v.ly_do) loi(`Lệch ${vnd(chenh)} đ so với sổ (${vnd(so_sach)} đ): ghi lý do.`);
      const cc = await this.bang('chot_ca').create({ ngay: homNay(), quy_id: v.quy_id, so_sach, thuc_dem: tien(v.thuc_dem), chenh_lech: chenh,
        ly_do: v.ly_do || '', nguoi_chot: this.nguoi(ctx) }, { transaction: t });
      return { ok: true, so: cc.so, so_sach, chenh_lech: chenh };
    };
    H['don_ban:baoCao'] = async (ctx, t) => {
      if (!this.xemGia(ctx)) loi('Chỉ kế toán / quản lý xem báo cáo lãi gộp.');
      const p = { ...ctx.action.params, ...val(ctx) };
      const theo = ({ don_vi: 'dv.ten', khach: 'k.ten', mat_hang: "mh.ma || ' – ' || mh.ten", ngay: "to_char(g.ngay, 'YYYY-MM-DD')" } as any)[p.theo] || 'dv.ten';
      return this.sql(`SELECT ${theo} AS nhom, SUM(l.thanh_tien) AS doanh_so, SUM(l.gia_von) AS gia_von, SUM(l.so_kg) AS so_luong
        FROM luot_giao_dong l JOIN luot_giao g ON g.id = l.luot_giao_id JOIN don_ban d ON d.id = g.don_ban_id
        JOIN don_vi dv ON dv.id = d.don_vi_ban_id JOIN khach_hang k ON k.id = d.khach_id JOIN mat_hang mh ON mh.id = l.mat_hang_id
        WHERE g.trang_thai IN ('da_ban_giao_xe','khach_da_nhan') AND g.ngay BETWEEN :tu AND :den GROUP BY 1 ORDER BY 2 DESC`,
        { tu: p.tu || '2000-01-01', den: p.den || '2999-12-31' }, t);
    };

    const handlers: Record<string, any> = {};
    for (const [ten, fn] of Object.entries(H)) {
      handlers[ten] = async (ctx: any, next: any) => {
        await giaoDich(ctx, (t) => fn(ctx, t));
        await next();
      };
    }
    this.app.resourceManager.registerActionHandlers(handlers);
    const tenThaoTac: Record<string, string> = {
      ghiSo: 'Ghi sổ kho', huy: 'Hủy chứng từ', dinhGia: 'Định giá hàng nhập', chotDon: 'Chốt đơn', duyetGia: 'Duyệt đơn (giá sàn / hạn mức)',
      moLai: 'Mở lại đơn', dongPhanCon: 'Đóng phần chưa giao', ghiHoaDon: 'Ghi số hóa đơn', taoLuot: 'Tạo lượt giao', banGiaoXe: 'Bàn giao xe',
      khachNhan: 'Khách đã nhận', ghi: 'Ghi chứng từ', phanBo: 'Phân bổ tiền', phanBoThuHo: 'Phân bổ thu hộ', nhanDien: 'Nhận diện khách',
      tatToan: 'Tất toán thu hộ', chot: 'Chốt ca tiền', baoCao: 'Báo cáo lãi gộp',
    };
    for (const [k, v] of Object.entries(tenThaoTac)) this.app.acl.setAvailableAction(k, { displayName: v, type: 'old-data', onNewRecord: false } as any);
  }

  async ghiSanXuat(t: Transaction, pk: any, dong: any[]) {
    if (dong.some((d) => !d.huong)) loi('Mỗi dòng phải chọn Vào (nguyên liệu / bao bì) / Ra (thành phẩm) / Phụ phẩm.');
    const vao = dong.filter((d) => d.huong === 'vao');
    const ra = dong.filter((d) => d.huong === 'ra');
    const phu = dong.filter((d) => d.huong === 'phu_pham');
    if (!vao.length || !ra.length) loi('Cần ít nhất một dòng nguyên liệu vào và một dòng thành phẩm ra.');
    if (dong.some((d) => !(kg(d.so_kg) > 0))) loi('Số lượng mỗi dòng phải lớn hơn 0.');
    const mh: Record<string, any> = {};
    for (const d of dong) mh[d.mat_hang_id] = mh[d.mat_hang_id] || (await this.matHang(d.mat_hang_id, t));
    const kgCua = (ds: any[]) => kg(ds.filter((d) => this.laKg(mh[d.mat_hang_id])).reduce((s, d) => s + kg(d.so_kg), 0));
    const kg_vao = kgCua(vao);
    const kg_ra = kg(kgCua(ra) + kgCua(phu));
    if (Math.abs(kg_vao - kg_ra) > 0.0005 && !pk.ghi_chu)
      loi(`Kg vào ${kg_vao} khác kg ra ${kg_ra} (chênh ${kg(kg_vao - kg_ra)} kg): ghi lý do hao hụt / chênh lệch ở ô Ghi chú. Bao bì theo Cái không tính vào kg.`);
    if (phu.some((d) => d.don_gia === null || d.don_gia === undefined || Number(d.don_gia) < 0)) loi('Phụ phẩm cần đơn giá (nhập 0 nếu không có giá trị).');
    const ngay = pk.ngay;
    let gia_tri_nvl = 0;
    for (const d of vao) {
      gia_tri_nvl += -(await this.ghiSo(t, { ngay, kho_id: pk.kho_id, mat_hang_id: d.mat_hang_id, so_luong: -kg(d.so_kg), so_bao: -kg(d.so_bao),
        loai: pk.loai + '_vao', chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id }));
    }
    const chi_phi = tien(pk.chi_phi_sx);
    const kho_ra = pk.kho_dich_id || pk.kho_id;
    let gt_phu = 0;
    for (const d of phu) {
      const v = tien(kg(d.so_kg) * Number(d.don_gia || 0));
      gt_phu += v;
      await this.ghiSo(t, { ngay, kho_id: kho_ra, mat_hang_id: d.mat_hang_id, so_luong: kg(d.so_kg), so_bao: kg(d.so_bao), loai: pk.loai + '_phu_pham',
        chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id, gia_tri: v });
    }
    const tong = tien(gia_tri_nvl + chi_phi - gt_phu);
    if (tong < 0) loi('Giá trị phụ phẩm lớn hơn giá trị nguyên liệu + chi phí: kiểm tra lại đơn giá phụ phẩm.');
    const sl_tp = ra.reduce((s, d) => s + kg(d.so_kg), 0);
    const gia_thanh = sl_tp > 0 ? Math.round((tong / sl_tp) * 100) / 100 : 0;
    let con = tong;
    for (let i = 0; i < ra.length; i++) {
      const d = ra[i];
      const v = i === ra.length - 1 ? con : tien(kg(d.so_kg) * gia_thanh);
      con -= v;
      await this.ghiSo(t, { ngay, kho_id: kho_ra, mat_hang_id: d.mat_hang_id, so_luong: kg(d.so_kg), so_bao: kg(d.so_bao), loai: pk.loai + '_ra',
        chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id, gia_tri: v });
      await d.update({ don_gia: gia_thanh }, { transaction: t, hooks: false });
    }
    return { gia_tri_nvl: tien(gia_tri_nvl), kg_vao, kg_ra, gia_thanh };
  }

  async install() {}
}

export default PluginKhoServer;
