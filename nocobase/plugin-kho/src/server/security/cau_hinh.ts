/** Cấu hình vận hành (bảng cau_hinh). Mặc định 0.4.0 ghi trong MAC_DINH; bản cài cũ chưa có dòng thì dùng giá trị tương thích 0.3.2 (TUONG_THICH). */
import { Transaction } from 'sequelize';

export const MAC_DINH: Record<string, [string, string]> = {
  giu_khi_duyet: ['co', 'Giữ tồn ngay khi đơn được duyệt (co / khong)'],
  vuot_han_muc_khach_thuong: ['canh_bao', 'Khách thường vượt hạn mức: canh_bao (vẫn bán, ghi cảnh báo) / duyet (chờ duyệt)'],
  pham_vi_mac_dinh: ['tu_choi', 'Người dùng nghiệp vụ chưa được cấp phạm vi kho / quỹ: tu_choi / cho_phep'],
  dung_sai_can_pct: ['2', 'Dung sai cân mặc định (%) khi mặt hàng chưa khai'],
  gia_danh_muc_gom_vat: ['co', 'Giá bán trên danh mục mặt hàng đã gồm VAT (co / khong)'],
  ck_can_xac_minh: ['khong', 'Phiếu thu chuyển khoản của thủ quỹ phải chờ đối soát ngân hàng mới vào quỹ (co / khong)'],
  nguong_lech_sx_pct: ['0.5', 'Ngưỡng lệch kg phiếu sản xuất (%) — vượt thì vào hàng đợi rà soát'],
  ma_khach_le: ['KHACH-LE', 'Mã khách lẻ cho bán nhanh'],
  ngay_moc_golive: ['', 'Ngày mốc Go-Live (yyyy-mm-dd): phát sinh trước ngày này nằm trong số dư đầu kỳ'],
};
/** Giá trị khi chưa có dòng cấu hình (giữ hành vi 0.3.2 cho bản đang chạy cho tới khi chạy nâng cấp 0.4.0). */
export const TUONG_THICH: Record<string, string> = { giu_khi_duyet: 'khong', vuot_han_muc_khach_thuong: 'duyet', pham_vi_mac_dinh: 'cho_phep' };

export async function cauHinh(p: any, khoa: string, t?: Transaction): Promise<string> {
  const [r] = await p.sql(`SELECT gia_tri FROM cau_hinh WHERE khoa = :k`, { k: khoa }, t).catch(() => [null]);
  if (r && r.gia_tri !== null && r.gia_tri !== undefined) return String(r.gia_tri);
  return TUONG_THICH[khoa] ?? MAC_DINH[khoa]?.[0] ?? '';
}
export const so = (v: any, d = 0) => { const n = Number(String(v ?? '').replace(',', '.')); return Number.isFinite(n) ? n : d; };
