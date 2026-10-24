/**
 * 0.4.0 Giá & VAT: ba tầng giá (danh mục mat_hang → bảng giá theo nhóm khách / kênh / hiệu lực / số lượng → giá chốt trên dòng đơn).
 * VAT theo dòng: có / không VAT, thuế suất, giá đã gồm hay chưa gồm VAT; thanh_tien của dòng = số phải thu (gồm VAT nếu có).
 */
import { Transaction } from 'sequelize';
import { homNay, kg, tien } from '../tienich';
import { cauHinh } from '../security/cau_hinh';

export async function giaApDung(p: any, t: Transaction | undefined, a: { khach_id?: any; mat_hang_id: any; so_luong: number; ngay?: string; kenh?: string }) {
  const kh = a.khach_id ? await p.bang('khach_hang').findByPk(a.khach_id, { transaction: t }) : null;
  const ngay = a.ngay || homNay();
  const [r] = await p.sql(`SELECT d.don_gia, d.gia_san, b.ma, b.gia_gom_vat FROM bang_gia_dong d JOIN bang_gia b ON b.id = d.bang_gia_id
    WHERE d.mat_hang_id = :m AND COALESCE(b.ngung, false) = false
      AND (COALESCE(b.nhom_gia, '') = '' OR b.nhom_gia = :nhom) AND (b.kenh IS NULL OR b.kenh = :kenh)
      AND (b.tu_ngay IS NULL OR b.tu_ngay <= :ngay) AND (b.den_ngay IS NULL OR b.den_ngay >= :ngay)
      AND COALESCE(d.sl_toi_thieu, 0) <= :sl
    ORDER BY (COALESCE(b.nhom_gia, '') <> '') DESC, COALESCE(b.uu_tien, 0) DESC, COALESCE(d.sl_toi_thieu, 0) DESC, d.id DESC LIMIT 1`,
  { m: a.mat_hang_id, nhom: kh?.nhom_gia || '', kenh: a.kenh || 'si', ngay, sl: kg(a.so_luong) }, t).catch(() => [null]);
  if (r && Number(r.don_gia) > 0) return { don_gia: Number(r.don_gia), gia_san: Number(r.gia_san || 0), nguon: `Bảng giá ${r.ma}`, gia_gom_vat: !!r.gia_gom_vat };
  const mh = await p.bang('mat_hang').findByPk(a.mat_hang_id, { transaction: t });
  return { don_gia: Number(mh?.gia_ban || 0), gia_san: Number(mh?.gia_san || 0), nguon: 'Giá danh mục',
    gia_gom_vat: (await cauHinh(p, 'gia_danh_muc_gom_vat', t)) === 'co' };
}

/** Tính tiền một dòng: trả về trước thuế, thuế, tổng phải thu, đơn giá thanh toán / ĐVT tồn. */
export function tinhTien(so_luong: number, don_gia: number, vat: boolean, thue_suat: number, gom_vat: boolean) {
  const tien_hang = tien(kg(so_luong) * Number(don_gia || 0));
  const ts = vat ? Number(thue_suat || 0) : 0;
  let truoc: number, thue: number, tong: number;
  if (!vat || !ts) { truoc = tien_hang; thue = 0; tong = tien_hang; }
  else if (gom_vat) { tong = tien_hang; truoc = tien(tien_hang / (1 + ts / 100)); thue = tong - truoc; }
  else { truoc = tien_hang; thue = tien(tien_hang * ts / 100); tong = truoc + thue; }
  return { tien_truoc_thue: truoc, tien_thue: thue, thanh_tien: tong, don_gia_tt: kg(so_luong) > 0 ? Math.round((tong / kg(so_luong)) * 10000) / 10000 : 0 };
}

/** Điền giá / VAT vào dòng đơn (gọi trong hook trước khi lưu dòng của đơn nháp). */
export async function dienGiaDong(p: any, m: any, don: any, t: Transaction | undefined) {
  if (!m.get('mat_hang_id')) return;
  const mh = await p.bang('mat_hang').findByPk(m.get('mat_hang_id'), { transaction: t });
  const g = await giaApDung(p, t, { khach_id: don?.khach_id, mat_hang_id: m.get('mat_hang_id'), so_luong: Number(m.get('so_kg') || 0), ngay: don?.ngay, kenh: don?.kenh });
  m.set('gia_niem_yet', g.don_gia);
  m.set('gia_san_ap', g.gia_san);
  m.set('nguon_gia', g.nguon);
  if (m.get('don_gia') === null || m.get('don_gia') === undefined || m.get('don_gia') === '') m.set('don_gia', g.don_gia);
  // Dòng mới của đơn có yêu cầu hóa đơn: mặc định có VAT (trừ dòng đánh dấu "Không xuất hóa đơn").
  if (m.get('vat_ap_dung') === null || m.get('vat_ap_dung') === undefined || (m.isNewRecord && !m.get('vat_ap_dung') && don?.xuat_hoa_don && m.get('loai_vat') !== 'khong_hd'))
    m.set('vat_ap_dung', !!don?.xuat_hoa_don && m.get('loai_vat') !== 'khong_hd');
  if (m.get('thue_suat') === null || m.get('thue_suat') === undefined) m.set('thue_suat', Number(mh?.thue_suat || 0));
  if (m.get('loai_vat') === null || m.get('loai_vat') === undefined) m.set('loai_vat', mh?.loai_vat || null);
  if (m.get('gia_gom_vat') === null || m.get('gia_gom_vat') === undefined) m.set('gia_gom_vat', g.gia_gom_vat);
  m.set('price_basis', m.get('gia_gom_vat') ? 'gom_vat' : 'chua_vat');
  const r = tinhTien(Number(m.get('so_kg') || 0), Number(m.get('don_gia') || 0), !!m.get('vat_ap_dung'), Number(m.get('thue_suat') || 0), !!m.get('gia_gom_vat'));
  for (const [k, v] of Object.entries(r)) m.set(k, v);
}
