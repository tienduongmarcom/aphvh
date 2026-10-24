/**
 * 0.4.0 Kho: giữ tồn từ lúc duyệt đơn (một số dư so_giu duy nhất ở ton_kho, chuyển cấp đơn → cấp lượt không cộng trùng),
 * ATP = tồn − đang giữ − chờ định giá. Nhật ký dat_giu_ton để truy vết.
 */
import { Transaction } from 'sequelize';
import { kg } from '../tienich';
import { cauHinh } from '../security/cau_hinh';

export const atp = (ton: any) => kg(Number(ton.so_kg || 0) - Number(ton.so_giu || 0) - Number(ton.so_cho_gia || 0));

export async function ghiNhatKyGiu(p: any, t: Transaction, a: { kho_id: any; mat_hang_id: any; don_ban_dong_id: any; so_luong: number; loai: string; chung_tu: string }) {
  if (!kg(a.so_luong)) return;
  await p.bang('dat_giu_ton').create({ ...a, so_luong: kg(a.so_luong) }, { transaction: t, hooks: false });
}

/** Giữ hàng cấp đơn cho phần chưa giao / chưa lập lượt / chưa giữ. Giữ tối đa bằng ATP (không giữ vượt), trả danh sách dòng giữ thiếu. */
export async function giuDon(p: any, t: Transaction, don: any) {
  if ((await cauHinh(p, 'giu_khi_duyet', t)) !== 'co') return { bo_qua: true, thieu: [] as string[] };
  const dong = await p.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t, order: [['id', 'ASC']], lock: t.LOCK.UPDATE });
  const thieu: string[] = [];
  for (const d of dong) {
    const can = kg(Number(d.so_kg) - Number(d.da_giao || 0) - Number(d.dang_giu || 0) - Number(d.giu_don || 0));
    if (can <= 0 || !d.kho_id) continue;
    const ton = await p.dongTon(t, d.kho_id, d.mat_hang_id);
    const g = Math.max(0, Math.min(can, atp(ton)));
    if (g > 0) {
      await ton.update({ so_giu: kg(Number(ton.so_giu || 0) + g) }, { transaction: t, hooks: false });
      await d.update({ giu_don: kg(Number(d.giu_don || 0) + g) }, { transaction: t, hooks: false });
      await ghiNhatKyGiu(p, t, { kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, don_ban_dong_id: d.id, so_luong: g, loai: 'giu_don', chung_tu: don.so });
    }
    if (g < can - 0.0005) thieu.push(`${d.ten_hang}: giữ ${kg(g)}/${can}`);
  }
  return { bo_qua: false, thieu };
}

/** Giải phóng toàn bộ phần giữ cấp đơn (hủy / mở lại / đóng phần chưa giao). */
export async function nhaGiuDon(p: any, t: Transaction, don: any) {
  const dong = await p.bang('don_ban_dong').findAll({ where: { don_ban_id: don.id }, transaction: t, lock: t.LOCK.UPDATE });
  for (const d of dong) {
    const g = kg(d.giu_don);
    if (!(g > 0)) continue;
    const ton = await p.dongTon(t, d.kho_id, d.mat_hang_id);
    await ton.update({ so_giu: Math.max(0, kg(Number(ton.so_giu || 0) - g)) }, { transaction: t, hooks: false });
    await d.update({ giu_don: 0 }, { transaction: t, hooks: false });
    await ghiNhatKyGiu(p, t, { kho_id: d.kho_id, mat_hang_id: d.mat_hang_id, don_ban_dong_id: d.id, so_luong: -g, loai: 'nha', chung_tu: don.so });
  }
}
