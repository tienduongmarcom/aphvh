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

/** Phân bổ chênh lệch giá trị của lượng nguồn Q (đã vào kho nguồn từ dòng sổ kho tu_id trở đi). */
export async function dieuChinhGiaTri(p: any, t: Transaction, a: {
  mat_hang_id: any; kho_id: any; so_luong_goc: number; chenh_lech: number; tu_so_kho_id: number; chung_tu: string; nguon: string; ly_do: string; ngay?: string;
}) {
  const D = tien(a.chenh_lech);
  if (!D) return null;
  const Q = kg(a.so_luong_goc);
  if (!(Q > 0)) loi('Điều chỉnh giá trị cần số lượng gốc > 0.');
  const ngay = a.ngay || homNay();
  const [g] = await p.sql(`SELECT COALESCE(so_kg,0) AS sl FROM gia_von WHERE mat_hang_id = :m AND kho_id = :k`, { m: a.mat_hang_id, k: a.kho_id }, t);
  const S = Math.max(0, kg(g?.sl || 0));
  const con = Math.min(Q, S);
  const vaoTonNguon = tien((D * con) / Q);
  if (vaoTonNguon) await p.capNhatGia(t, { ngay, mat_hang_id: a.mat_hang_id, kho_id: a.kho_id, so_luong: 0, gia_tri: vaoTonNguon, loai: 'dieu_chinh_ton', chung_tu: a.chung_tu });
  let conLai = D - vaoTonNguon;
  const daRa = kg(Q - con);
  const chiTiet: any = { kho_nguon: { kho_id: a.kho_id, ton: S, con, vao_ton: vaoTonNguon }, kho_nhan: [] as any[] };
  let vaoTonNhan = 0;
  if (daRa > 0 && conLai) {
    // Lượng đã ra khỏi kho nguồn sau thời điểm nhập: chuyển kho được theo tới kho nhận (một bậc); còn lại coi là đã tiêu thụ.
    const ra = await p.sql(`SELECT s.loai, -SUM(s.so_kg) AS sl, pk.kho_dich_id FROM so_kho s LEFT JOIN phieu_kho pk ON pk.so = s.chung_tu AND s.loai = 'chuyen_di'
      WHERE s.mat_hang_id = :m AND s.kho_id = :k AND s.id >= :tu AND s.so_kg < 0 AND s.loai NOT LIKE 'huy_%' GROUP BY s.loai, pk.kho_dich_id`,
    { m: a.mat_hang_id, k: a.kho_id, tu: a.tu_so_kho_id }, t);
    const tongRa = Math.max(ra.reduce((s: number, x: any) => s + Number(x.sl || 0), 0), daRa);
    const phanRa = conLai;
    for (const x of ra.filter((x: any) => x.loai === 'chuyen_di' && x.kho_dich_id)) {
      const w = Number(x.sl) / tongRa; // tỷ trọng của chuyển kho trong tổng lượng đã ra
      const phan = tien(phanRa * w);
      const slChuyen = kg(daRa * w);
      if (!phan || !(slChuyen > 0)) continue;
      const [gd] = await p.sql(`SELECT COALESCE(so_kg,0) AS sl FROM gia_von WHERE mat_hang_id = :m AND kho_id = :k`, { m: a.mat_hang_id, k: x.kho_dich_id }, t);
      const conNhan = Math.min(slChuyen, Math.max(0, kg(gd?.sl || 0)));
      const vao = tien((phan * conNhan) / slChuyen);
      if (vao) await p.capNhatGia(t, { ngay, mat_hang_id: a.mat_hang_id, kho_id: x.kho_dich_id, so_luong: 0, gia_tri: vao, loai: 'dieu_chinh_ton', chung_tu: a.chung_tu });
      vaoTonNhan += vao;
      chiTiet.kho_nhan.push({ kho_id: x.kho_dich_id, sl_chuyen: slChuyen, con: conNhan, vao_ton: vao });
    }
    conLai -= vaoTonNhan;
    chiTiet.ra_theo_loai = ra.map((x: any) => ({ loai: x.loai, sl: kg(x.sl), kho_dich_id: x.kho_dich_id }));
  }
  const vaoGiaVon = conLai;
  const lam_tron = D - (vaoTonNguon + vaoTonNhan + vaoGiaVon);
  if (lam_tron !== 0) loi(`Điều chỉnh giá trị không cân (lệch ${lam_tron} đ) — dừng ghi.`);
  return p.bang('dieu_chinh_gia_tri').create({ ngay, nguon: a.nguon, chung_tu: a.chung_tu, mat_hang_id: a.mat_hang_id, kho_id: a.kho_id,
    so_luong_goc: Q, so_luong_con: con, chenh_lech: D, vao_ton: vaoTonNguon + vaoTonNhan, vao_gia_von: vaoGiaVon, lam_tron,
    chi_tiet: JSON.stringify(chiTiet), ly_do: a.ly_do }, { transaction: t, hooks: false });
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
    WHERE chenh_lech <> vao_ton + vao_gia_von + lam_tron OR lam_tron <> 0`, {}, t);
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
  const pv = await p.sql(`SELECT kho_id, quy_id FROM pham_vi WHERE nguoi_dung_id = :u`, { u: u.id }).catch(() => []);
  ctx.state.aphKho = pv.some((x: any) => x.kho_id) ? pv.filter((x: any) => x.kho_id).map((x: any) => Number(x.kho_id)) : null;
  ctx.state.aphQuy = pv.some((x: any) => x.quy_id) ? pv.filter((x: any) => x.quy_id).map((x: any) => Number(x.quy_id)) : null;
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
};
export const LOC_QUY: Record<string, (ds: number[]) => any> = {
  so_quy: (ds) => ({ quy_id: { $in: ds } }), phieu_thu: (ds) => ({ quy_id: { $in: ds } }), phieu_chi: (ds) => ({ quy_id: { $in: ds } }),
  chot_ca: (ds) => ({ quy_id: { $in: ds } }), chuyen_tien: (ds) => ({ $or: [{ tu_quy_id: { $in: ds } }, { den_quy_id: { $in: ds } }] }),
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
