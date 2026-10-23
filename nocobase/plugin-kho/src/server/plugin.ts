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
    p: { ngay: string; kho_id: any; mat_hang_id: any; so_kg: number; so_bao: number; loai: string; chung_tu: string; nguon: string; nguon_id: any },
    choPhepAm = false,
  ) {
    if (!p.kho_id || !p.mat_hang_id) loi('Dòng hàng thiếu kho hoặc mặt hàng');
    const so_kg = kg(p.so_kg);
    const so_bao = kg(p.so_bao);
    if (!so_kg && !so_bao) return;
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
  }

  /** Đảo toàn bộ sổ kho của một chứng từ (khi hủy). */
  async daoSo(t: Transaction, chung_tu: string, ngay: string, loai: string) {
    const dong = await this.bang('so_kho').findAll({ where: { chung_tu }, transaction: t });
    for (const d of dong) {
      await this.ghiSo(t, { ngay, kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, so_kg: -d.so_kg, so_bao: -d.so_bao, loai, chung_tu, nguon: d.nguon, nguon_id: d.nguon_id }, false);
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
    for (const bang of ['so_kho', 'ton_kho']) {
      for (const su_kien of ['beforeCreate', 'beforeUpdate', 'beforeDestroy']) {
        db.on(`${bang}.${su_kien}`, () => loi('Sổ kho và tồn kho chỉ thay đổi qua phiếu kho hoặc xác nhận giao hàng.'));
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

    this.app.resourceManager.registerActionHandlers({
      'phieu_kho:ghiSo': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const pk = await this.khoa('phieu_kho', id(ctx), t);
          if (pk.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true, so: pk.so };
          if (pk.trang_thai !== 'nhap') loi('Phiếu đã hủy.');
          const dong = await this.bang('phieu_kho_dong').findAll({ where: { phieu_kho_id: pk.id }, transaction: t });
          if (!dong.length) loi('Phiếu chưa có dòng hàng.');
          if (pk.loai === 'chuyen' && (!pk.kho_dich_id || pk.kho_dich_id === pk.kho_id)) loi('Chuyển kho cần kho nhận khác kho xuất.');
          for (const d of dong) {
            const q = kg(d.so_kg);
            const b = kg(d.so_bao);
            const chung = { ngay: pk.ngay, mat_hang_id: d.mat_hang_id, chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id };
            if (pk.loai === 'nhap' || pk.loai === 'dau_ky') {
              if (q <= 0) loi('Phiếu nhập cần số kg dương.');
              await this.ghiSo(t, { ...chung, kho_id: pk.kho_id, so_kg: q, so_bao: b, loai: pk.loai });
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
          await pk.update({ trang_thai: 'da_ghi', ghi_boi: this.nguoi(ctx) }, { transaction: t , choPhep: true } as any);
          return { ok: true, so: pk.so };
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
          await don.update({ trang_thai: 'cho_xuat' }, { transaction: t , choPhep: true } as any);
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
          for (const d of dong) {
            await this.ghiSo(t, {
              ngay: homNay(), kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, so_kg: -kg(d.so_kg), so_bao: -kg(d.so_bao),
              loai: 'ban', chung_tu: don.so, nguon: 'don_ban_dong', nguon_id: d.id,
            });
          }
          const v = ctx.action.params.values || {};
          await don.update(
            { trang_thai: 'da_giao', giao_boi: this.nguoi(ctx), nguoi_nhan: v.nguoi_nhan || don.nguoi_nhan, bien_so: v.bien_so || don.bien_so },
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
          await don.update({ trang_thai: 'da_huy', ly_do_huy: ly_do || '', tong_tien: 0, con_no: 0 }, { transaction: t , choPhep: true } as any);
          return { ok: true };
        });
        await next();
      },
      // Mở lại đơn Chờ xuất về Nháp để sửa (chưa trừ kho nên không ảnh hưởng tồn).
      'don_ban:moLai': async (ctx: any, next: any) => {
        await giaoDich(ctx, async (t) => {
          const don = await this.khoa('don_ban', id(ctx), t);
          if (don.trang_thai !== 'cho_xuat') loi('Chỉ mở lại được đơn Chờ xuất.');
          await don.update({ trang_thai: 'nhap' }, { transaction: t , choPhep: true } as any);
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
      ghiSo: 'Ghi sổ kho', huy: 'Hủy chứng từ', chotDon: 'Chốt đơn', giaoHang: 'Xác nhận giao hàng', moLai: 'Mở lại đơn', ghi: 'Ghi phiếu thu',
    };
    for (const [k, v] of Object.entries(thaoTac)) {
      this.app.acl.setAvailableAction(k, { displayName: v, type: 'old-data', onNewRecord: false } as any);
    }
  }

  async install() {}
}

export default PluginKhoServer;
