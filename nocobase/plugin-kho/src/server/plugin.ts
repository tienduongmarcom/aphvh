/**
 * APH-VH — nghiệp vụ kho, bán hàng, thu tiền trên NocoBase (bản tối thiểu dùng thật 26/10/2026).
 *
 * Nguyên tắc:
 * - Tồn kho chỉ thay đổi qua SỔ KHO (so_kho). Bảng ton_kho là số cộng dồn, cập nhật cùng giao dịch, khóa từng dòng
 *   (SELECT ... FOR UPDATE) nên hai người cùng xuất một mặt hàng ở một kho không làm âm kho hay ghi trùng.
 * - Mọi thao tác ghi (ghi sổ, giao hàng, ghi phiếu thu, hủy) khóa chứng từ gốc rồi kiểm trạng thái: bấm hai lần chỉ ghi một lần.
 * - Tồn tính TỔNG theo kho (chưa tách theo đơn vị). Đơn bán chọn đơn vị bán; công nợ theo khách × đơn vị bán.
 * - Thu tiền chỉ trả vào các đơn người dùng chọn; phần còn lại là CHƯA PHÂN BỔ. Không tự trả nợ cũ nhất, không cấn chéo đơn vị.
 */
import { Plugin } from '@nocobase/server';
import { Transaction } from 'sequelize';

const kg = (v: any) => Math.round(Number(v || 0) * 1000) / 1000;
const tien = (v: any) => Math.round(Number(v || 0));
const homNay = () => {
  const d = new Date(Date.now() + 7 * 3600 * 1000); // giờ Việt Nam
  return d.toISOString().slice(0, 10);
};

class LoiNghiepVu extends Error {
  status = 400;
}
const loi = (msg: string) => {
  throw new LoiNghiepVu(msg);
};

export class PluginKhoServer extends Plugin {
  coKhoaTon = false;
  coKhoaGia = false;

  bang(name: string) {
    return this.db.getCollection(name).model as any;
  }

  /** Khóa và đọc một bản ghi trong giao dịch. */
  async khoa(name: string, id: any, t: Transaction) {
    const r = await this.bang(name).findOne({ where: { id }, transaction: t, lock: t.LOCK.UPDATE });
    if (!r) loi(`Không tìm thấy ${name} ${id}`);
    return r;
  }

  /** Ghi một dòng sổ kho và cộng vào tồn; chặn âm kho. */
  async ghiSo(
    t: Transaction,
    p: { ngay: string; kho_id: any; mat_hang_id: any; so_kg: number; so_bao: number; loai: string; chung_tu: string; nguon: string; nguon_id: any;
      gia?: number | null; gia_tri?: number | null; boQuaGia?: boolean },
    choPhepAm = false,
  ): Promise<number> {
    if (!p.kho_id || !p.mat_hang_id) loi('Dòng hàng thiếu kho hoặc mặt hàng');
    const so_kg = kg(p.so_kg);
    const so_bao = kg(p.so_bao);
    if (!so_kg && !so_bao) return 0;
    const Ton = this.bang('ton_kho');
    if (!this.coKhoaTon) {
      await this.db.sequelize.query('CREATE UNIQUE INDEX IF NOT EXISTS ton_kho_kho_mat_hang ON ton_kho (kho_id, mat_hang_id)');
      this.coKhoaTon = true;
    }
    await this.db.sequelize.query(
      `INSERT INTO ton_kho (kho_id, mat_hang_id, so_kg, so_bao, "createdAt", "updatedAt") VALUES (:k, :m, 0, 0, now(), now())
       ON CONFLICT (kho_id, mat_hang_id) DO NOTHING`,
      { replacements: { k: p.kho_id, m: p.mat_hang_id }, transaction: t },
    );
    const ton = await Ton.findOne({ where: { kho_id: p.kho_id, mat_hang_id: p.mat_hang_id }, transaction: t, lock: t.LOCK.UPDATE });
    const moi_kg = kg(Number(ton.so_kg || 0) + so_kg);
    const moi_bao = kg(Number(ton.so_bao || 0) + so_bao);
    if (!choPhepAm && so_kg < 0 && moi_kg < -0.0005) {
      const mh = await this.bang('mat_hang').findByPk(p.mat_hang_id, { transaction: t });
      const kho = await this.bang('kho').findByPk(p.kho_id, { transaction: t });
      loi(`Không đủ hàng: ${mh?.nhan || mh?.ma} tại ${kho?.ten} còn ${kg(ton.so_kg)} kg, cần ${-so_kg} kg. ` +
        'Kiểm tra lại kho xuất hoặc nhập hàng trước.');
    }
    await ton.update({ so_kg: moi_kg, so_bao: moi_bao }, { transaction: t, hooks: false });
    await this.bang('so_kho').create(
      { ngay: p.ngay, kho_id: p.kho_id, mat_hang_id: p.mat_hang_id, so_kg, so_bao, loai: p.loai, chung_tu: p.chung_tu, nguon: p.nguon, nguon_id: p.nguon_id },
      { transaction: t, hooks: false },
    );
    if (p.boQuaGia || !so_kg) return 0;
    return this.capNhatGia(t, { ngay: p.ngay, mat_hang_id: p.mat_hang_id, so_kg, gia: p.gia, gia_tri: p.gia_tri, loai: p.loai, chung_tu: p.chung_tu });
  }

  /**
   * Giá vốn bình quân gia quyền theo MẶT HÀNG (tồn tính tổng mọi kho, chưa tách đơn vị).
   * Nhập có giá: giá trị = kg × giá; không có giá (xuất, chuyển, kiểm kê, nhập chưa có giá): theo giá bình quân hiện tại.
   * Trả về giá trị thay đổi (âm khi xuất) để tính giá vốn hàng bán / giá thành.
   */
  async capNhatGia(t: Transaction, p: { ngay: string; mat_hang_id: any; so_kg: number; gia?: number | null; gia_tri?: number | null; loai: string; chung_tu: string }) {
    if (!this.coKhoaGia) {
      await this.db.sequelize.query('CREATE UNIQUE INDEX IF NOT EXISTS gia_von_mat_hang ON gia_von (mat_hang_id)');
      this.coKhoaGia = true;
    }
    await this.db.sequelize.query(
      `INSERT INTO gia_von (mat_hang_id, so_kg, gia_tri, gia_bq, "createdAt", "updatedAt") VALUES (:m, 0, 0, 0, now(), now()) ON CONFLICT (mat_hang_id) DO NOTHING`,
      { replacements: { m: p.mat_hang_id }, transaction: t },
    );
    const g = await this.bang('gia_von').findOne({ where: { mat_hang_id: p.mat_hang_id }, transaction: t, lock: t.LOCK.UPDATE });
    const bq = Number(g.gia_bq || 0);
    let val: number;
    if (p.gia_tri !== undefined && p.gia_tri !== null) val = tien(p.gia_tri);
    else if (p.so_kg > 0 && p.gia !== undefined && p.gia !== null && Number(p.gia) > 0) val = tien(p.so_kg * Number(p.gia));
    else val = tien(p.so_kg * bq);
    const moi_kg = kg(Number(g.so_kg || 0) + p.so_kg);
    let moi_gt = tien(Number(g.gia_tri || 0) + val);
    let moi_bq = bq;
    if (moi_kg > 0.0005) moi_bq = Math.round((moi_gt / moi_kg) * 100) / 100;
    else if (Math.abs(moi_kg) <= 0.0005) moi_gt = 0;
    await g.update({ so_kg: moi_kg, gia_tri: moi_gt, gia_bq: moi_bq }, { transaction: t, hooks: false });
    await this.bang('so_gia_von').create(
      { ngay: p.ngay, mat_hang_id: p.mat_hang_id, so_kg: p.so_kg, gia_tri: val, gia_bq_sau: moi_bq, loai: p.loai, chung_tu: p.chung_tu },
      { transaction: t, hooks: false },
    );
    return val;
  }

  /**
   * Phiếu sản xuất / đóng gói: nguyên liệu VÀO xuất khỏi kho (theo giá bình quân), thành phẩm RA nhập vào kho thành phẩm
   * (kho nhận nếu có, không thì cùng kho). Giá thành = (giá trị nguyên liệu + chi phí sản xuất − phụ phẩm theo đơn giá nhập tay)
   * chia đều theo kg thành phẩm chính. Chênh kg vào/ra (hao hụt hoặc tăng) bắt buộc ghi lý do.
   */
  async ghiSanXuat(t: Transaction, pk: any, dong: any[]) {
    const vao = dong.filter((d) => d.huong === 'vao');
    const ra = dong.filter((d) => d.huong === 'ra');
    const phu = dong.filter((d) => d.huong === 'phu_pham');
    if (dong.some((d) => !d.huong)) loi('Mỗi dòng phải chọn Vào (nguyên liệu) / Ra (thành phẩm) / Phụ phẩm.');
    if (!vao.length || !ra.length) loi('Phiếu sản xuất cần ít nhất một dòng nguyên liệu vào và một dòng thành phẩm ra.');
    if (dong.some((d) => !(kg(d.so_kg) > 0))) loi('Số kg mỗi dòng phải lớn hơn 0.');
    const kg_vao = kg(vao.reduce((s, d) => s + kg(d.so_kg), 0));
    const kg_tp = kg(ra.reduce((s, d) => s + kg(d.so_kg), 0));
    const kg_phu = kg(phu.reduce((s, d) => s + kg(d.so_kg), 0));
    const kg_ra = kg(kg_tp + kg_phu);
    if (Math.abs(kg_vao - kg_ra) > 0.0005 && !pk.ghi_chu)
      loi(`Kg vào ${kg_vao} khác kg ra ${kg_ra} (chênh ${kg(kg_vao - kg_ra)} kg): ghi lý do hao hụt / chênh lệch ở ô Ghi chú.`);
    if (phu.some((d) => !(Number(d.don_gia) >= 0) || d.don_gia === null)) loi('Phụ phẩm cần đơn giá để tính giá thành (nhập 0 nếu không có giá trị).');
    const ngay = pk.ngay;
    let gia_tri_nvl = 0;
    for (const d of vao) {
      gia_tri_nvl += -(await this.ghiSo(t, { ngay, kho_id: pk.kho_id, mat_hang_id: d.mat_hang_id, so_kg: -kg(d.so_kg), so_bao: -kg(d.so_bao),
        loai: pk.loai + '_vao', chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id }));
    }
    const chi_phi = tien(pk.chi_phi_sx);
    const kho_ra = pk.kho_dich_id || pk.kho_id;
    let gt_phu = 0;
    for (const d of phu) {
      const v = tien(kg(d.so_kg) * Number(d.don_gia || 0));
      gt_phu += v;
      await this.ghiSo(t, { ngay, kho_id: kho_ra, mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), so_bao: kg(d.so_bao), loai: pk.loai + '_phu_pham',
        chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id, gia_tri: v });
    }
    const tong = tien(gia_tri_nvl + chi_phi - gt_phu);
    if (tong < 0) loi('Giá trị phụ phẩm lớn hơn giá trị nguyên liệu + chi phí: kiểm tra lại đơn giá phụ phẩm.');
    const gia_thanh = kg_tp > 0 ? Math.round((tong / kg_tp) * 100) / 100 : 0;
    let con = tong;
    for (let i = 0; i < ra.length; i++) {
      const d = ra[i];
      const v = i === ra.length - 1 ? con : tien(kg(d.so_kg) * gia_thanh);
      con -= v;
      await this.ghiSo(t, { ngay, kho_id: kho_ra, mat_hang_id: d.mat_hang_id, so_kg: kg(d.so_kg), so_bao: kg(d.so_bao), loai: pk.loai + '_ra',
        chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id, gia_tri: v });
      await d.update({ don_gia: gia_thanh }, { transaction: t, hooks: false });
    }
    return { gia_tri_nvl: tien(gia_tri_nvl), kg_vao, kg_ra, gia_thanh };
  }

  /** Ghi sổ quỹ; quỹ tiền mặt không được âm. Khóa dòng quỹ để hai phiếu cùng lúc không làm sai số dư. */
  async ghiQuy(t: Transaction, p: { ngay: string; quy_id: any; so_tien: number; loai: string; chung_tu: string; dien_giai?: string }, choPhepAm = false) {
    if (!p.quy_id) loi('Chưa chọn quỹ / tài khoản tiền.');
    const quy = await this.khoa('quy', p.quy_id, t);
    const [[r]]: any = await this.db.sequelize.query('SELECT COALESCE(SUM(so_tien),0) AS du FROM so_quy WHERE quy_id = :q', { replacements: { q: p.quy_id }, transaction: t });
    const du = tien(Number(r.du) + tien(p.so_tien));
    if (!choPhepAm && quy.loai === 'tien_mat' && p.so_tien < 0 && du < 0)
      loi(`Quỹ ${quy.ten} chỉ còn ${tien(r.du).toLocaleString('vi-VN')} đ, không chi được ${(-tien(p.so_tien)).toLocaleString('vi-VN')} đ.`);
    await this.bang('so_quy').create({ ngay: p.ngay, quy_id: p.quy_id, so_tien: tien(p.so_tien), loai: p.loai, chung_tu: p.chung_tu, dien_giai: p.dien_giai || '' },
      { transaction: t, hooks: false });
    return quy;
  }
  async daoQuy(t: Transaction, chung_tu: string, ngay: string) {
    const dong = await this.bang('so_quy').findAll({ where: { chung_tu }, transaction: t });
    for (const d of dong) if (!String(d.loai).startsWith('huy_')) await this.ghiQuy(t, { ngay, quy_id: d.quy_id, so_tien: -d.so_tien, loai: 'huy_' + d.loai, chung_tu }, false);
  }

  /** Đảo toàn bộ sổ kho của một chứng từ (khi hủy). */
  async daoSo(t: Transaction, chung_tu: string, ngay: string, loai: string) {
    const dong = await this.bang('so_kho').findAll({ where: { chung_tu }, transaction: t, order: [['id', 'ASC']] });
    const goc = dong.filter((d: any) => !String(d.loai).startsWith('huy_'));
    // Nhập lại trước, xuất sau: tránh âm kho tạm thời khi đảo phiếu chuyển / sản xuất.
    for (const d of [...goc].sort((a: any, b: any) => a.so_kg - b.so_kg)) {
      await this.ghiSo(t, { ngay, kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, so_kg: -d.so_kg, so_bao: -d.so_bao, loai, chung_tu, nguon: d.nguon, nguon_id: d.nguon_id, boQuaGia: true }, false);
    }
    const gv = await this.bang('so_gia_von').findAll({ where: { chung_tu }, transaction: t });
    const theoMh: Record<string, { kg: number; gt: number }> = {};
    for (const x of gv) {
      if (String(x.loai).startsWith('huy_')) continue;
      const k = String(x.mat_hang_id);
      theoMh[k] = theoMh[k] || { kg: 0, gt: 0 };
      theoMh[k].kg += Number(x.so_kg || 0);
      theoMh[k].gt += Number(x.gia_tri || 0);
    }
    for (const [mh, v] of Object.entries(theoMh)) {
      if (!kg(v.kg) && !tien(v.gt)) continue;
      await this.capNhatGia(t, { ngay, mat_hang_id: mh, so_kg: -kg(v.kg), gia_tri: -tien(v.gt), loai, chung_tu });
    }
  }

  async tinhDonBan(t: Transaction, don: any) {
    const dong = await this.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t });
    const tong = don.loai === 'dau_ky' ? tien(don.tong_tien) : dong.reduce((s: number, d: any) => s + tien(d.thanh_tien), 0);
    const da_thu = tien(don.da_thu);
    await don.update({ tong_tien: tong, con_no: tong - da_thu }, { transaction: t, hooks: false });
  }

  nguoi(ctx: any) {
    const u = ctx.state?.currentUser;
    return u ? u.nickname || u.username || u.email || String(u.id) : '';
  }

  async beforeLoad() {
    const db = this.db;
    // Tên hiển thị dễ phân biệt: mặt hàng "mã – tên", khách "tên – SĐT", kho/đơn vị theo tên.
    db.on('mat_hang.beforeSave', (m: any) => m.set('nhan', [m.get('ma'), m.get('ten')].filter(Boolean).join(' – ')));
    db.on('khach_hang.beforeSave', (m: any) => m.set('nhan', [m.get('ten'), m.get('sdt')].filter(Boolean).join(' – ')));
    db.on('kho.beforeSave', (m: any) => m.set('nhan', m.get('ten')));
    db.on('don_vi.beforeSave', (m: any) => m.set('nhan', m.get('ten')));

    db.on('phieu_kho.beforeCreate', (m: any) => {
      if (!m.get('ngay')) m.set('ngay', homNay());
      m.set('trang_thai', 'nhap');
    });
    db.on('phieu_kho.beforeUpdate', (m: any, opts: any) => {
      if (m.previous('trang_thai') && m.previous('trang_thai') !== 'nhap' && !opts?.choPhep) {
        const doi = m.changed() || [];
        if (doi.some((k: string) => !['ghi_chu', 'updatedAt', 'updatedById'].includes(k)))
          loi('Phiếu đã ghi sổ hoặc đã hủy, không sửa được. Hủy phiếu và lập phiếu mới.');
      }
    });

    db.on('don_ban.beforeCreate', async (m: any, { transaction }: any) => {
      if (!m.get('ngay')) m.set('ngay', homNay());
      if (!m.get('ngay_giao')) m.set('ngay_giao', m.get('ngay'));
      if (!m.get('cach_giao')) m.set('cach_giao', 'khach_den_lay');
      if (m.get('loai') !== 'dau_ky') m.set('trang_thai', 'nhap');
      if (m.get('khach_id')) {
        const k = await this.bang('khach_hang').findByPk(m.get('khach_id'), { transaction });
        if (k) {
          if (!m.get('sdt')) m.set('sdt', k.sdt);
          if (!m.get('dia_chi_giao')) m.set('dia_chi_giao', k.dia_chi);
        }
      }
      m.set('da_thu', 0);
      if (m.get('loai') === 'dau_ky') {
        m.set('trang_thai', 'da_giao');
        m.set('con_no', tien(m.get('tong_tien')));
      }
    });
    db.on('don_ban.beforeUpdate', async (m: any, opts: any) => {
      const transaction = opts?.transaction;
      const truoc = m.previous('trang_thai');
      if (m.changed('khach_id') && m.get('khach_id')) {
        const k = await this.bang('khach_hang').findByPk(m.get('khach_id'), { transaction });
        if (k) {
          m.set('sdt', k.sdt);
          m.set('dia_chi_giao', k.dia_chi);
        }
      }
      if (truoc && truoc !== 'nhap' && !opts?.choPhep) {
        const doi = (m.changed() || []).filter((k: string) => !['ghi_chu', 'updatedAt', 'updatedById', 'nguoi_nhan', 'bien_so', 'dia_chi_giao', 'sdt'].includes(k));
        if (doi.length) loi('Đơn đã chuyển sang chờ xuất / đã giao / đã hủy: chỉ sửa được ghi chú, người nhận, biển số, địa chỉ giao.');
      }
    });

    const dongDon = async (m: any, transaction: any) => {
      const don = await this.bang('don_ban').findByPk(m.get('don_ban_id'), { transaction });
      if (don && don.trang_thai !== 'nhap') loi('Đơn không còn ở trạng thái Nháp: không sửa được hàng trên đơn.');
      if (m.get('mat_hang_id')) {
        const mh = await this.bang('mat_hang').findByPk(m.get('mat_hang_id'), { transaction });
        if (mh) {
          m.set('ten_hang', mh.ten);
          if (m.get('don_gia') === null || m.get('don_gia') === undefined) m.set('don_gia', mh.gia_ban);
          if (!m.get('so_kg') && m.get('so_bao') && mh.kg_bao) m.set('so_kg', kg(Number(m.get('so_bao')) * Number(mh.kg_bao)));
        }
      }
      m.set('thanh_tien', tien(Number(m.get('so_kg') || 0) * Number(m.get('don_gia') || 0)));
    };
    db.on('don_ban_dong.beforeSave', (m: any, { transaction }: any) => dongDon(m, transaction));
    db.on('don_ban_dong.beforeDestroy', async (m: any, { transaction }: any) => {
      const don = await this.bang('don_ban').findByPk(m.get('don_ban_id'), { transaction });
      if (don && don.trang_thai !== 'nhap') loi('Đơn không còn ở trạng thái Nháp: không xóa được dòng hàng.');
    });
    const capNhatTong = async (m: any, { transaction }: any) => {
      const id = m.get('don_ban_id');
      if (!id) return;
      const don = await this.bang('don_ban').findByPk(id, { transaction });
      if (don) await this.tinhDonBan(transaction, don);
    };
    db.on('don_ban_dong.afterSave', capNhatTong);
    db.on('don_ban_dong.afterDestroy', capNhatTong);
    db.on('don_ban.afterCreate', async (m: any, opts: any) => {
      if (m.get('loai') !== 'dau_ky') await this.tinhDonBan(opts.transaction, m);
    });

    db.on('phieu_kho_dong.beforeSave', async (m: any, { transaction }: any) => {
      const pk = await this.bang('phieu_kho').findByPk(m.get('phieu_kho_id'), { transaction });
      if (pk && pk.trang_thai !== 'nhap') loi('Phiếu đã ghi sổ hoặc đã hủy: không sửa được dòng hàng.');
      const mh = m.get('mat_hang_id') && (await this.bang('mat_hang').findByPk(m.get('mat_hang_id'), { transaction }));
      if (mh) {
        m.set('ten_hang', mh.ten);
        if (!m.get('so_kg') && m.get('so_bao') && mh.kg_bao) m.set('so_kg', kg(Number(m.get('so_bao')) * Number(mh.kg_bao)));
      }
    });
    for (const b of ['phieu_chi', 'chuyen_tien']) {
      db.on(`${b}.beforeCreate`, (m: any) => { if (!m.get('ngay')) m.set('ngay', homNay()); m.set('trang_thai', 'nhap'); });
      db.on(`${b}.beforeUpdate`, (m: any, opts: any) => {
        if (m.previous('trang_thai') && m.previous('trang_thai') !== 'nhap' && !opts?.choPhep) loi('Phiếu đã ghi hoặc đã hủy: không sửa được.');
      });
    }
    db.on('quy.beforeSave', (m: any) => m.set('nhan', m.get('ten')));
    db.on('phieu_thu.beforeCreate', (m: any) => {
      if (!m.get('ngay')) m.set('ngay', homNay());
      m.set('trang_thai', 'nhap');
    });
    db.on('phieu_thu.beforeUpdate', (m: any, opts: any) => {
      if (m.previous('trang_thai') && m.previous('trang_thai') !== 'nhap' && !opts?.choPhep) {
        const doi = (m.changed() || []).filter((k: string) => !['ghi_chu', 'updatedAt', 'updatedById'].includes(k));
        if (doi.length) loi('Phiếu thu đã ghi hoặc đã hủy: không sửa được. Hủy phiếu và lập phiếu mới.');
      }
    });
    db.on('phieu_thu_phan_bo.beforeSave', async (m: any, { transaction }: any) => {
      const pt = await this.bang('phieu_thu').findByPk(m.get('phieu_thu_id'), { transaction });
      if (pt && pt.trang_thai !== 'nhap') loi('Phiếu thu đã ghi: không sửa phân bổ.');
    });
    // Sổ kho / tồn kho chỉ ghi qua thao tác nghiệp vụ (các lệnh ghi nội bộ chạy với hooks: false).
    for (const bang of ['so_kho', 'ton_kho', 'so_quy', 'gia_von', 'so_gia_von']) {
      for (const su_kien of ['beforeCreate', 'beforeUpdate', 'beforeDestroy']) {
        db.on(`${bang}.${su_kien}`, () => loi('Sổ kho, sổ quỹ, tồn và giá vốn chỉ thay đổi qua chứng từ (phiếu kho, giao hàng, phiếu thu / chi).'));
      }
    }
  }

  async load() {
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
      if (!v) ctx.throw(400, 'Thiếu mã chứng từ');
      return v;
    };

    const lyDo = (ctx: any) => ctx.action.params.values?.ly_do || ctx.action.params.ly_do;
    this.app.resourceManager.registerActionHandlers({
      'phieu_chi:ghi': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pc = await this.khoa('phieu_chi', id(ctx), t);
          if (pc.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pc.so };
          if (pc.trang_thai !== 'nhap') loi('Phiếu chi đã hủy.');
          if (!(tien(pc.so_tien) > 0)) loi('Nhập số tiền chi.');
          if (!pc.ly_do) loi('Ghi lý do chi.');
          const quy = await this.bang('quy').findByPk(pc.quy_id, { transaction: t });
          if (!quy || quy.don_vi_id !== pc.don_vi_id) loi('Quỹ chi không thuộc đơn vị chi.');
          if (quy.loai === 'ngan_hang' && !pc.ma_gd) loi('Chi qua ngân hàng cần mã giao dịch.');
          await this.ghiQuy(t, { ngay: pc.ngay, quy_id: pc.quy_id, so_tien: -tien(pc.so_tien), loai: 'chi', chung_tu: pc.so, dien_giai: pc.ly_do });
          await pc.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
          return { ok: true, so: pc.so };
        });
        await next();
      },
      'phieu_chi:huy': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pc = await this.khoa('phieu_chi', id(ctx), t);
          if (pc.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
          if (pc.trang_thai === 'da_ghi') {
            if (!lyDo(ctx)) loi('Hủy phiếu chi đã ghi cần lý do.');
            await this.daoQuy(t, pc.so, homNay());
          }
          await pc.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
      // Bàn giao / nộp tiền giữa hai quỹ CÙNG đơn vị (vd. thu ngân nộp kế toán, nộp tiền mặt vào ngân hàng).
      'chuyen_tien:ghi': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const ct = await this.khoa('chuyen_tien', id(ctx), t);
          if (ct.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: ct.so };
          if (ct.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
          if (!(tien(ct.so_tien) > 0)) loi('Nhập số tiền.');
          if (ct.tu_quy_id === ct.den_quy_id) loi('Quỹ đi và quỹ đến phải khác nhau.');
          const [a, b] = await Promise.all([this.bang('quy').findByPk(ct.tu_quy_id, { transaction: t }), this.bang('quy').findByPk(ct.den_quy_id, { transaction: t })]);
          if (a.don_vi_id !== b.don_vi_id) loi('Chỉ chuyển giữa các quỹ cùng một đơn vị. Tiền giữa hai đơn vị là nghiệp vụ khác, không ghi ở đây.');
          await this.ghiQuy(t, { ngay: ct.ngay, quy_id: ct.tu_quy_id, so_tien: -tien(ct.so_tien), loai: 'chuyen_di', chung_tu: ct.so, dien_giai: `Bàn giao cho ${ct.nguoi_nhan || b.ten}` });
          await this.ghiQuy(t, { ngay: ct.ngay, quy_id: ct.den_quy_id, so_tien: tien(ct.so_tien), loai: 'chuyen_den', chung_tu: ct.so, dien_giai: `Nhận từ ${ct.nguoi_giao || a.ten}` });
          await ct.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
          return { ok: true, so: ct.so };
        });
        await next();
      },
      'chuyen_tien:huy': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const ct = await this.khoa('chuyen_tien', id(ctx), t);
          if (ct.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
          if (ct.trang_thai === 'da_ghi') {
            if (!lyDo(ctx)) loi('Hủy phiếu đã ghi cần lý do.');
            await this.daoQuy(t, ct.so, homNay());
          }
          await ct.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
      // Chốt ca: so tiền thực đếm với số theo sổ quỹ; chỉ ghi nhận, không tự sửa sổ (lệch thì kế toán lập phiếu điều chỉnh).
      'chot_ca:chot': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const v = ctx.action.params.values || {};
          if (!v.quy_id) loi('Chọn quỹ tiền mặt.');
          if (v.thuc_dem === undefined || v.thuc_dem === null || v.thuc_dem === '') loi('Nhập số tiền thực đếm.');
          const quy = await this.khoa('quy', v.quy_id, t);
          if (quy.loai !== 'tien_mat') loi('Chốt ca chỉ áp dụng cho quỹ tiền mặt.');
          const [[r]]: any = await this.db.sequelize.query('SELECT COALESCE(SUM(so_tien),0) AS du FROM so_quy WHERE quy_id = :q', { replacements: { q: v.quy_id }, transaction: t });
          const so_sach = tien(r.du);
          const chenh = tien(v.thuc_dem) - so_sach;
          if (chenh !== 0 && !v.ly_do) loi(`Lệch ${chenh.toLocaleString('vi-VN')} đ so với sổ (${so_sach.toLocaleString('vi-VN')} đ): ghi lý do.`);
          const cc = await this.bang('chot_ca').create({ ngay: homNay(), quy_id: v.quy_id, so_sach, thuc_dem: tien(v.thuc_dem), chenh_lech: chenh,
            ly_do: v.ly_do || '', nguoi_chot: this.nguoi(ctx) }, { transaction: t });
          return { ok: true, so: cc.so, so_sach, chenh_lech: chenh };
        });
        await next();
      },
      'phieu_kho:ghiSo': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pk = await this.khoa('phieu_kho', id(ctx), t);
          if (pk.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pk.so };
          if (pk.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
          const dong = await this.bang('phieu_kho_dong').findAll({ where: { phieu_kho_id: pk.id }, transaction: t });
          if (!dong.length) loi('Phiếu chưa có dòng hàng.');
          if (pk.loai === 'chuyen' && (!pk.kho_dich_id || pk.kho_dich_id === pk.kho_id)) loi('Chuyển kho cần kho nhận khác kho xuất.');
          let capNhat: any = {};
          if (pk.loai === 'san_xuat' || pk.loai === 'dong_goi') {
            capNhat = await this.ghiSanXuat(t, pk, dong);
          } else for (const d of dong) {
            const q = kg(d.so_kg);
            const b = kg(d.so_bao);
            const chung = { ngay: pk.ngay, mat_hang_id: d.mat_hang_id, chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id };
            if (pk.loai === 'nhap' || pk.loai === 'dau_ky') {
              if (q <= 0) loi('Phiếu nhập cần số kg dương.');
              await this.ghiSo(t, { ...chung, kho_id: pk.kho_id, so_kg: q, so_bao: b, loai: pk.loai, gia: d.don_gia });
            } else if (pk.loai === 'xuat') {
              if (q <= 0) loi('Phiếu xuất cần số kg dương.');
              await this.ghiSo(t, { ...chung, kho_id: pk.kho_id, so_kg: -q, so_bao: -b, loai: 'xuat' });
            } else if (pk.loai === 'chuyen') {
              if (q <= 0) loi('Phiếu chuyển cần số kg dương.');
              await this.ghiSo(t, { ...chung, kho_id: pk.kho_id, so_kg: -q, so_bao: -b, loai: 'chuyen_di' });
              await this.ghiSo(t, { ...chung, kho_id: pk.kho_dich_id, so_kg: q, so_bao: b, loai: 'chuyen_den' });
            } else if (pk.loai === 'kiem_ke') {
              if (!pk.ghi_chu) loi('Điều chỉnh kiểm kê cần ghi lý do ở ô Ghi chú.');
              await this.ghiSo(t, { ...chung, kho_id: pk.kho_id, so_kg: q, so_bao: b, loai: 'kiem_ke' });
            } else loi('Loại phiếu không hợp lệ.');
          }
          await pk.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx), ...capNhat }, { transaction: t , choPhep: true } as any);
          return { ok: true, so: pk.so, ...capNhat };
        });
        await next();
      },
      'phieu_kho:huy': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pk = await this.khoa('phieu_kho', id(ctx), t);
          if (pk.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
          const ly_do = ctx.action.params.values?.ly_do || ctx.action.params.ly_do;
          if (pk.trang_thai === 'da_ghi') {
            if (!ly_do) loi('Hủy phiếu đã ghi sổ cần lý do.');
            await this.daoSo(t, pk.so, homNay(), 'huy_' + pk.loai);
          }
          await pk.update({ trang_thai: 'da_huy', ly_do_huy: ly_do || '' }, { transaction: t , choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
      // Nháp -> Chờ xuất: chốt hàng trên đơn, kho in phiếu A5 để giao. Chưa trừ kho.
      'don_ban:chotDon': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const don = await this.khoa('don_ban', id(ctx), t);
          if (don.trang_thai === 'cho_xuat') return { ok: true, da_chot_truoc: true };
          if (don.trang_thai !== 'nhap') loi('Chỉ chốt được đơn đang Nháp.');
          const dong = await this.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t });
          if (!dong.length) loi('Đơn chưa có hàng.');
          for (const d of dong) {
            if (!(kg(d.so_kg) > 0)) loi(`Dòng ${d.ten_hang || ''}: số kg phải lớn hơn 0.`);
            if (!d.kho_id) loi(`Dòng ${d.ten_hang || ''}: chưa chọn kho xuất.`);
          }
          await this.tinhDonBan(t, don);
          const duoiSan: string[] = [];
          for (const d of dong) {
            const mh = await this.bang('mat_hang').findByPk(d.mat_hang_id, { transaction: t });
            if (Number(mh?.gia_san) > 0 && Number(d.don_gia || 0) < Number(mh.gia_san)) duoiSan.push(mh.ma);
          }
          if (duoiSan.length && !don.duyet_boi) {
            await don.update({ trang_thai: 'cho_duyet' }, { transaction: t, choPhep: true } as any);
            return { ok: true, so: don.so, cho_duyet: true, mat_hang: duoiSan };
          }
          await don.update({ trang_thai: 'cho_xuat' }, { transaction: t , choPhep: true } as any);
          return { ok: true, so: don.so };
        });
        await next();
      },
      // Quản lý duyệt bán dưới giá sàn: Chờ duyệt giá -> Chờ xuất.
      'don_ban:duyetGia': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const don = await this.khoa('don_ban', id(ctx), t);
          if (don.trang_thai !== 'cho_duyet') loi('Đơn không ở trạng thái Chờ duyệt giá.');
          const ly_do = ctx.action.params.values?.ly_do;
          if (!ly_do) loi('Ghi lý do đồng ý bán dưới giá sàn.');
          await don.update({ trang_thai: 'cho_xuat', duyet_boi: this.nguoi(ctx), ly_do_gia: ly_do }, { transaction: t, choPhep: true } as any);
          return { ok: true, so: don.so };
        });
        await next();
      },
      // Chờ xuất -> Đã giao: trừ kho, ghi công nợ. Bấm hai lần chỉ ghi một lần.
      'don_ban:giaoHang': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const don = await this.khoa('don_ban', id(ctx), t);
          if (don.trang_thai === 'da_giao') return { ok: true, da_giao_truoc: true, so: don.so };
          if (don.trang_thai !== 'cho_xuat') loi('Chỉ xác nhận giao được đơn đang Chờ xuất (bấm "Chốt đơn & in phiếu" trước).');
          const dong = await this.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t, order: [['id', 'ASC']] });
          let gia_von = 0;
          for (const d of dong) {
            gia_von += -(await this.ghiSo(t, {
              ngay: homNay(), kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, so_kg: -kg(d.so_kg), so_bao: -kg(d.so_bao),
              loai: 'ban', chung_tu: don.so, nguon: 'don_ban_dong', nguon_id: d.id,
            }));
          }
          const v = ctx.action.params.values || {};
          await don.update(
            { trang_thai: 'da_giao', gia_von: tien(gia_von), giao_boi: this.nguoi(ctx), nguoi_nhan: v.nguoi_nhan || don.nguoi_nhan, bien_so: v.bien_so || don.bien_so },
            { transaction: t, choPhep: true } as any,
          );
          await this.tinhDonBan(t, don);
          return { ok: true, so: don.so };
        });
        await next();
      },
      'don_ban:huy': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const don = await this.khoa('don_ban', id(ctx), t);
          if (don.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
          const ly_do = ctx.action.params.values?.ly_do || ctx.action.params.ly_do;
          if (tien(don.da_thu) > 0) loi('Đơn đã có tiền thu phân bổ: hủy phiếu thu liên quan trước.');
          if (don.trang_thai === 'da_giao') {
            if (!ly_do) loi('Hủy đơn đã giao cần lý do (hàng nhập lại kho).');
            await this.daoSo(t, don.so, homNay(), 'huy_ban');
          }
          await don.update({ trang_thai: 'da_huy', ly_do_huy: ly_do || '', tong_tien: 0, con_no: 0, gia_von: 0 }, { transaction: t , choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
      // Mở lại đơn Chờ xuất về Nháp để sửa (chưa trừ kho nên không ảnh hưởng tồn).
      'don_ban:moLai': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const don = await this.khoa('don_ban', id(ctx), t);
          if (!['cho_xuat', 'cho_duyet'].includes(don.trang_thai)) loi('Chỉ mở lại được đơn Chờ xuất / Chờ duyệt giá.');
          await don.update({ trang_thai: 'nhap', duyet_boi: null, ly_do_gia: null }, { transaction: t , choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
      'phieu_thu:ghi': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pt = await this.khoa('phieu_thu', id(ctx), t);
          if (pt.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pt.so };
          if (pt.trang_thai !== 'nhap') loi('Phiếu thu đã hủy.');
          const so_tien = tien(pt.so_tien);
          if (so_tien <= 0) loi('Nhập số tiền khách thực trả.');
          if (pt.hinh_thuc === 'chuyen_khoan' && !pt.ma_gd) loi('Chuyển khoản cần mã giao dịch / nội dung chuyển khoản.');
          if (!pt.quy_id) loi('Chọn quỹ / tài khoản nhận tiền.');
          const quy = await this.bang('quy').findByPk(pt.quy_id, { transaction: t });
          if (quy.don_vi_id !== pt.don_vi_id) loi('Quỹ / tài khoản nhận không thuộc đơn vị nhận tiền.');
          if ((pt.hinh_thuc === 'tien_mat') !== (quy.loai === 'tien_mat')) loi('Tiền mặt phải vào quỹ tiền mặt; chuyển khoản phải vào tài khoản ngân hàng.');
          await this.ghiQuy(t, { ngay: pt.ngay, quy_id: pt.quy_id, so_tien: so_tien, loai: 'thu', chung_tu: pt.so, dien_giai: 'Thu tiền khách' });
          const pb = await this.bang('phieu_thu_phan_bo').findAll({ where: { phieu_thu_id: pt.id }, transaction: t, order: [['id', 'ASC']] });
          let da_phan_bo = 0;
          const dung = new Set();
          for (const p of pb) {
            if (dung.has(p.don_ban_id)) loi('Một đơn chỉ được chọn một lần trong phiếu thu.');
            dung.add(p.don_ban_id);
            const don = await this.khoa('don_ban', p.don_ban_id, t);
            if (don.khach_id !== pt.khach_id) loi(`Đơn ${don.so} không phải của khách trên phiếu thu.`);
            if (don.don_vi_ban_id !== pt.don_vi_id) loi(`Đơn ${don.so} thuộc đơn vị khác: tiền nhận vào đơn vị này không trả nợ đơn vị khác.`);
            if (don.trang_thai !== 'da_giao') loi(`Đơn ${don.so} chưa giao: chưa có công nợ để trả.`);
            const a = tien(p.so_tien);
            if (a <= 0) loi(`Số tiền trả cho đơn ${don.so} phải lớn hơn 0.`);
            if (a > tien(don.con_no)) loi(`Đơn ${don.so} còn nợ ${tien(don.con_no).toLocaleString('vi-VN')} đ, không trả quá số này.`);
            da_phan_bo += a;
            await don.update({ da_thu: tien(don.da_thu) + a, con_no: tien(don.con_no) - a }, { transaction: t , choPhep: true } as any);
          }
          if (da_phan_bo > so_tien) loi('Tổng phân bổ lớn hơn số tiền thực nhận.');
          await pt.update({ trang_thai: 'da_ghi', chua_phan_bo: so_tien - da_phan_bo, ghi_boi: this.nguoi(ctx) }, { transaction: t , choPhep: true } as any);
          return { ok: true, so: pt.so, chua_phan_bo: so_tien - da_phan_bo };
        });
        await next();
      },
      'phieu_thu:huy': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pt = await this.khoa('phieu_thu', id(ctx), t);
          if (pt.trang_thai === 'da_huy') return { ok: true, da_huy_truoc: true };
          const ly_do = ctx.action.params.values?.ly_do || ctx.action.params.ly_do;
          if (pt.trang_thai === 'da_ghi') {
            if (!ly_do) loi('Hủy phiếu thu đã ghi cần lý do.');
            await this.daoQuy(t, pt.so, homNay());
            const pb = await this.bang('phieu_thu_phan_bo').findAll({ where: { phieu_thu_id: pt.id }, transaction: t });
            for (const p of pb) {
              const don = await this.khoa('don_ban', p.don_ban_id, t);
              await don.update({ da_thu: tien(don.da_thu) - tien(p.so_tien), con_no: tien(don.con_no) + tien(p.so_tien) }, { transaction: t , choPhep: true } as any);
            }
          }
          await pt.update({ trang_thai: 'da_huy', ly_do_huy: ly_do || '', chua_phan_bo: 0 }, { transaction: t , choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
    });

    const thaoTac: Record<string, string> = {
      ghiSo: 'Ghi sổ kho', huy: 'Hủy chứng từ', chotDon: 'Chốt đơn', giaoHang: 'Xác nhận giao hàng', moLai: 'Mở lại đơn', ghi: 'Ghi phiếu thu / chi', duyetGia: 'Duyệt giá dưới sàn', chot: 'Chốt ca tiền',
    };
    for (const [k, v] of Object.entries(thaoTac)) {
      this.app.acl.setAvailableAction(k, { displayName: v, type: 'old-data', onNewRecord: false } as any);
    }
  }

  async install() {}
}

export default PluginKhoServer;
