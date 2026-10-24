/**
 * 0.3.2 — Toàn vẹn dữ liệu:
 * - ĐIỀU CHỈNH GIÁ TRỊ thống nhất (giá tạm → giá chính thức, chốt / chốt lại mẻ, giá phụ phẩm):
 *   chênh lệch của một lượng nguồn Q tại (mặt hàng × kho) được chia thành
 *     (a) phần còn tồn ở kho nguồn → vào giá trị tồn,
 *     (b) phần đã chuyển sang kho khác mà kho nhận còn giữ → vào giá trị tồn kho nhận,
 *     (c) phần đã bán / tiêu hao / không còn truy được → vào GIÁ VỐN / CHI PHÍ KỲ (bảng dieu_chinh_gia_tri, không đổi tồn).
 *   Bảo toàn: chênh lệch = (a) + (b) + (c) + làm tròn; làm tròn phải = 0 (kiểm trong code và trong bộ kiểm).
 * - Tồn về 0 mà còn giá trị lẻ: không xóa im lặng — ghi dòng "lam_tron_ton_0" ở sổ giá trị + một điều chỉnh vào giá vốn.
 * - Đối chiếu bảo toàn toàn hệ thống: Σ sổ kho = tồn; Σ sổ giá trị = giá trị tồn (theo mặt hàng × kho).
 * - Quyền: vai trò "Không xem giá vốn" phủ quyết mọi vai trò khác; phạm vi kho / quỹ theo người dùng kiểm ở máy chủ.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien } from './tienich';

export const VAI_TRO_KHONG_GIA = 'khong_xem_gia';

/**
 * 0.4.0 — Phân bổ chênh lệch giá trị D của một lô nguồn theo VẾT BÌNH QUÂN DI ĐỘNG (không dùng tồn hiện tại):
 * đi qua từng dòng sổ kho của (mặt hàng × kho) từ dòng nhập của lô; mỗi lần xuất mang đi phần D tỷ lệ (lượng xuất / tồn trước xuất).
 * - chuyển kho (chuyen_di): theo sang dòng nhập tương ứng ở kho nhận và đi tiếp (tối đa 3 bậc, gồm kho hàng đang vận chuyển);
 * - cấp NVL cho mẻ (cap_nvl): thành chi phí "điều chỉnh NVL" của mẻ tiêu thụ (mẻ chuyển "cần chốt lại");
 * - bán / tiêu hao / hủy / khác: vào giá vốn – chi phí kỳ;
 * - phần còn lại khi hết sổ: còn tồn → vào giá trị tồn; hết tồn → vào giá vốn.
 * Bảo toàn: D = vào tồn + vào giá vốn + vào mẻ; lệch làm tròn ≠ 0 thì dừng.
 */
export async function dieuChinhGiaTri(p: any, t: Transaction, a: {
  mat_hang_id: any; kho_id: any; so_luong_goc: number; chenh_lech: number; tu_so_kho_id: number; chung_tu: string; nguon: string; ly_do: string; ngay?: string;
}) {
  const D = tien(a.chenh_lech);
  if (!D) return null;
  const Q = kg(a.so_luong_goc);
  if (!(Q > 0)) loi('Điều chỉnh giá trị cần số lượng gốc > 0.');
  const ngay = a.ngay || homNay();
  const kq = { vao_ton: 0, vao_gia_von: 0, vao_me: 0, ton: [] as any[], me: {} as Record<string, number>, buoc: [] as any[] };
  const lan = async (kho: any, tuId: number, R: number, bac: number) => {
    const [b] = await p.sql(`SELECT COALESCE(SUM(so_kg),0) AS b FROM so_kho WHERE mat_hang_id = :m AND kho_id = :k AND id < :tu`, { m: a.mat_hang_id, k: kho, tu: tuId }, t);
    let B = kg(b.b);
    const rows = await p.sql(`SELECT id, so_kg, loai, chung_tu FROM so_kho WHERE mat_hang_id = :m AND kho_id = :k AND id >= :tu ORDER BY id`,
      { m: a.mat_hang_id, k: kho, tu: tuId }, t);
    for (const r of rows) {
      const q = kg(r.so_kg);
      if (q >= 0 || !R) { B = kg(B + q); continue; }
      if (B <= 0.0005) { B = kg(B + q); continue; }
      const phan = -q >= B ? R : tien((R * -q) / B);
      R -= phan;
      B = kg(B + q);
      if (!phan) continue;
      // Chuyển kho (và dòng đảo của chứng từ chuyển bị hủy): đi theo dòng nhập tương ứng ở kho kia.
      if ((r.loai === 'chuyen_di' || String(r.loai).startsWith('huy_')) && bac < 4) {
        const [d] = await p.sql(`SELECT id, kho_id FROM so_kho WHERE chung_tu = :c AND mat_hang_id = :m AND so_kg > 0 AND kho_id <> :k AND id > :i
          AND (loai = 'chuyen_den' OR loai = :l) ORDER BY id LIMIT 1`, { c: r.chung_tu, m: a.mat_hang_id, k: kho, i: r.id, l: r.loai }, t);
        if (d) { kq.buoc.push({ kho, sang: d.kho_id, chung_tu: r.chung_tu, phan }); await lan(d.kho_id, Number(d.id), phan, bac + 1); continue; }
      }
      if (r.loai === 'cap_nvl') {
        const [pk] = await p.sql(`SELECT me_sx_id FROM phieu_kho WHERE so = :c`, { c: r.chung_tu }, t);
        if (pk?.me_sx_id) { kq.me[pk.me_sx_id] = (kq.me[pk.me_sx_id] || 0) + phan; kq.vao_me += phan; continue; }
      }
      kq.vao_gia_von += phan;
    }
    if (!R) return;
    if (B > 0.0005) {
      await p.capNhatGia(t, { ngay, mat_hang_id: a.mat_hang_id, kho_id: kho, so_luong: 0, gia_tri: R, loai: 'dieu_chinh_ton', chung_tu: a.chung_tu });
      kq.vao_ton += R;
      kq.ton.push({ kho_id: kho, ton: B, vao_ton: R });
    } else kq.vao_gia_von += R;
  };
  await lan(a.kho_id, Number(a.tu_so_kho_id || 0), D, 0);
  for (const [meId, st] of Object.entries(kq.me)) {
    if (!st) continue;
    await p.bang('me_sx_chi_phi').create({ me_sx_id: Number(meId), loai: 'dieu_chinh_nvl', so_tien: st, ngay, so_chung_tu: `${a.chung_tu}|${a.nguon}`,
      ghi_chu: `Điều chỉnh giá trị NVL đã cấp: ${a.ly_do}` }, { transaction: t, hooks: false });
    const me = await p.bang('me_sx').findByPk(Number(meId), { transaction: t });
    if (me && p.tinhLaiMe) {
      await p.tinhLaiMe(t, me);
      if (['da_chot', 'da_khoa'].includes(me.trang_thai)) await me.update({ trang_thai: 'can_chot_lai' }, { transaction: t, hooks: false });
    }
  }
  const lam_tron = D - (kq.vao_ton + kq.vao_gia_von + kq.vao_me);
  if (lam_tron !== 0) loi(`Điều chỉnh giá trị không cân (lệch ${lam_tron} đ) — dừng ghi.`);
  const con = kq.ton.filter((x) => x.kho_id === a.kho_id).reduce((s, x) => s + x.ton, 0);
  return p.bang('dieu_chinh_gia_tri').create({ ngay, nguon: a.nguon, chung_tu: a.chung_tu, mat_hang_id: a.mat_hang_id, kho_id: a.kho_id,
    so_luong_goc: Q, so_luong_con: kg(Math.min(Q, con)), chenh_lech: D, vao_ton: kq.vao_ton, vao_gia_von: kq.vao_gia_von, vao_me: kq.vao_me, lam_tron,
    chi_tiet: JSON.stringify({ phuong_phap: 'vet_binh_quan', ton: kq.ton, me: kq.me, buoc: kq.buoc }), ly_do: a.ly_do }, { transaction: t, hooks: false });
}

/** Đối chiếu bảo toàn: số lượng (sổ kho ↔ tồn), giá trị (sổ giá trị ↔ giá trị tồn), điều chỉnh (chênh = vào tồn + vào giá vốn). */
export async function doiChieuBaoToan(p: any, t?: Transaction) {
  const sl = await p.sql(`SELECT k.ma AS kho, m.ma AS mat_hang, tk.so_kg AS ton, COALESCE(s.sl,0) AS so
    FROM ton_kho tk JOIN kho k ON k.id = tk.kho_id JOIN mat_hang m ON m.id = tk.mat_hang_id
    LEFT JOIN (SELECT kho_id, mat_hang_id, SUM(so_kg) AS sl FROM so_kho GROUP BY 1,2) s ON s.kho_id = tk.kho_id AND s.mat_hang_id = tk.mat_hang_id
    WHERE ABS(tk.so_kg - COALESCE(s.sl,0)) > 0.0005`, {}, t);
  const gt = await p.sql(`SELECT k.ma AS kho, m.ma AS mat_hang, g.gia_tri AS ton, COALESCE(s.gt,0) AS so
    FROM gia_von g JOIN kho k ON k.id = g.kho_id JOIN mat_hang m ON m.id = g.mat_hang_id
    LEFT JOIN (SELECT kho_id, mat_hang_id, SUM(gia_tri) AS gt FROM so_gia_von GROUP BY 1,2) s ON s.kho_id = g.kho_id AND s.mat_hang_id = g.mat_hang_id
    WHERE ABS(g.gia_tri - COALESCE(s.gt,0)) > 0.5`, {}, t);
  const dc = await p.sql(`SELECT id, chung_tu, chenh_lech, vao_ton, vao_gia_von, lam_tron FROM dieu_chinh_gia_tri
    WHERE chenh_lech <> vao_ton + vao_gia_von + COALESCE(vao_me,0) + lam_tron OR lam_tron <> 0`, {}, t);
  const [tong] = await p.sql(`SELECT
      (SELECT COALESCE(SUM(gia_tri),0) FROM so_gia_von) AS so_gia_tri, (SELECT COALESCE(SUM(gia_tri),0) FROM gia_von) AS gia_tri_ton,
      (SELECT COALESCE(SUM(vao_gia_von),0) FROM dieu_chinh_gia_tri) AS dieu_chinh_gia_von,
      (SELECT COALESCE(SUM(gia_tri),0) FROM so_gia_von WHERE loai IN ('dau_ky')) AS mo_dau,
      (SELECT COALESCE(SUM(so_tien),0) FROM so_quy) AS tong_quy`, {}, t);
  return { lech_so_luong: sl, lech_gia_tri: gt, dieu_chinh_khong_can: dc, tong, can: !sl.length && !gt.length && !dc.length };
}

/** Nạp vai trò + phạm vi của người dùng vào ctx.state (một lần / yêu cầu). */
export async function napNguoiDung(p: any, ctx: any) {
  const u = ctx.state?.currentUser;
  if (!u || ctx.state.aphNap) return;
  ctx.state.aphNap = true;
  const vt = await p.sql(`SELECT "roleName" AS r FROM "rolesUsers" WHERE "userId" = :u`, { u: u.id });
  ctx.state.aphKhongGia = vt.some((x: any) => x.r === VAI_TRO_KHONG_GIA);
  const pv = await p.sql(`SELECT kho_id, quy_id, COALESCE(tat_ca_kho,false) AS tk, COALESCE(tat_ca_quy,false) AS tq FROM pham_vi WHERE nguoi_dung_id = :u`, { u: u.id })
    .catch(() => p.sql(`SELECT kho_id, quy_id, false AS tk, false AS tq FROM pham_vi WHERE nguoi_dung_id = :u`, { u: u.id }).catch(() => []));
  // 0.4.0: mặc định TỪ CHỐI khi người dùng không có dòng phạm vi (cấu hình pham_vi_mac_dinh); quản trị hệ thống thấy tất cả.
  const quanTri = vt.some((x: any) => ['root', 'admin'].includes(x.r));
  // Kế toán / quản lý (vai trò toàn hệ thống) không bị từ chối mặc định; nếu được cấp dòng phạm vi thì vẫn bị giới hạn theo dòng đó.
  const toanHeThong = vt.some((x: any) => ['ke_toan', 'quan_ly'].includes(x.r));
  const [ch] = await p.sql(`SELECT gia_tri FROM cau_hinh WHERE khoa = 'pham_vi_mac_dinh'`, {}).catch(() => [null]);
  const tuChoi = (ch?.gia_tri || 'cho_phep') === 'tu_choi' && !quanTri && !toanHeThong;
  const ds = (k: string, tat: string) => {
    if (quanTri || pv.some((x: any) => x[tat])) return null;
    const l = pv.filter((x: any) => x[k]).map((x: any) => Number(x[k]));
    return l.length ? l : tuChoi ? [] : null;
  };
  ctx.state.aphKho = ds('kho_id', 'tk');
  ctx.state.aphQuy = ds('quy_id', 'tq');
}
export const kiemKho = (ctx: any, ...khoIds: any[]) => {
  const ds = ctx.state?.aphKho;
  if (!ds) return;
  for (const k of khoIds.filter(Boolean)) if (!ds.includes(Number(k))) loi('Kho này không thuộc phạm vi được giao cho bạn.');
};
export const kiemQuy = (ctx: any, ...quyIds: any[]) => {
  const ds = ctx.state?.aphQuy;
  if (!ds) return;
  for (const q of quyIds.filter(Boolean)) if (!ds.includes(Number(q))) loi('Quỹ / tài khoản này không thuộc phạm vi được giao cho bạn.');
};
/** Lọc đọc theo phạm vi (list / get / in phiếu dùng get). */
export const LOC_KHO: Record<string, (ds: number[]) => any> = {
  ton_kho: (ds) => ({ kho_id: { $in: ds } }), so_kho: (ds) => ({ kho_id: { $in: ds } }),
  phieu_kho: (ds) => ({ $or: [{ kho_id: { $in: ds } }, { kho_dich_id: { $in: ds } }] }),
  me_sx: (ds) => ({ kho_id: { $in: ds } }),
  chuyen_hang: (ds) => ({ $or: [{ kho_di_id: { $in: ds } }, { kho_den_id: { $in: ds } }] }),
  ca_pos: (ds) => ({ kho_id: { $in: ds } }),
};
export const LOC_QUY: Record<string, (ds: number[]) => any> = {
  so_quy: (ds) => ({ quy_id: { $in: ds } }), phieu_thu: (ds) => ({ quy_id: { $in: ds } }), phieu_chi: (ds) => ({ quy_id: { $in: ds } }),
  chot_ca: (ds) => ({ quy_id: { $in: ds } }), sao_ke: (ds) => ({ quy_id: { $in: ds } }), sao_ke_dong: (ds) => ({ quy_id: { $in: ds } }), chuyen_tien: (ds) => ({ $or: [{ tu_quy_id: { $in: ds } }, { den_quy_id: { $in: ds } }] }),
};

/** Tách CSV / TSV chuẩn (ngoặc kép, dấu phân cách trong ô, xuống dòng trong ô). */
export function docCsv(text: string, sep?: string): string[][] {
  const s = String(text || '').replace(/^﻿/, '').replace(/\r\n?/g, '\n');
  const dau = s.split('\n', 1)[0];
  const d = sep || (dau.includes('\t') ? '\t' : (dau.split(';').length > dau.split(',').length ? ';' : ','));
  const rows: string[][] = [];
  let row: string[] = [];
  let f = '';
  let q = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === '"') { if (s[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c;
    } else if (c === '"' && f === '') q = true;
    else if (c === d) { row.push(f); f = ''; }
    else if (c === '\n') { row.push(f); rows.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f !== '' || row.length) { row.push(f); rows.push(row); }
  return rows.filter((r) => r.some((x) => String(x).trim()));
}
