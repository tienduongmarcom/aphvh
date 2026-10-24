/**
 * 0.4.0 Nâng cấp dữ liệu tại chỗ (không xóa, không tạo lại DB) — chạy được nhiều lần:
 *  1. Thêm dòng cấu hình mặc định còn thiếu (không ghi đè cấu hình đã đặt).
 *  2. Giữ quyền hiện có: người dùng nghiệp vụ đang KHÔNG có dòng phạm vi (0.3.2 = thấy mọi kho / quỹ) được cấp "mọi kho / mọi quỹ" —
 *     từ 0.4.0 người dùng MỚI chưa cấp phạm vi bị từ chối. Danh sách được trả về để quản lý rà lại.
 *  3. Bổ sung số liệu dòng đơn / lượt giao cũ: đơn giá thanh toán, tiền trước thuế, số lượng tính tiền.
 *  4. Ghi phiên bản dữ liệu 0.4.0.
 */
import { Transaction } from 'sequelize';
import { homNay, loi } from '../tienich';
import { MAC_DINH, cauHinh } from '../security/cau_hinh';
import { giuDon } from '../inventory';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;
export const PHIEN_BAN = '0.4.1';
/** Các bước một lần (cấp phạm vi cho người dùng cũ, giữ tồn đơn cũ) chỉ chạy khi nâng từ 0.3.x (chưa có bản ghi 0.4.0). */
const MOC_MOT_LAN = '0.4.0';

export async function nangCap(p: any, t: Transaction, nguoi = 'he_thong') {
  const bc: any = { cau_hinh_them: [], cap_pham_vi: [], dong_don: 0, dong_luot: 0 };
  // Khóa một hồ sơ/một kho gửi gia công ở tầng DB để chống tạo song song.
  // Nếu dữ liệu cũ dùng chung kho cho hai hồ sơ, nâng cấp DỪNG để đối chiếu trước.
  await p.sql(`CREATE UNIQUE INDEX IF NOT EXISTS sx_ho_so_kho_duy_nhat ON sx_ho_so_gia_cong (kho_id)`, {}, t);
  // Dữ liệu chống ghi trùng nằm tại collection sx_thao_tac, request_id UNIQUE do schema khai báo.

  for (const [k, [gt, mt]] of Object.entries(MAC_DINH)) {
    const r = await p.sql(`INSERT INTO cau_hinh (khoa, gia_tri, mo_ta, "createdAt", "updatedAt") VALUES (:k, :g, :m, now(), now())
      ON CONFLICT (khoa) DO NOTHING RETURNING khoa`, { k, g: gt, m: mt }, t);
    if (r.length) bc.cau_hinh_them.push(k);
  }
  const u = await p.sql(`SELECT u.id, u.email FROM users u WHERE NOT EXISTS (SELECT 1 FROM pham_vi v WHERE v.nguoi_dung_id = u.id)
    AND NOT EXISTS (SELECT 1 FROM "rolesUsers" r WHERE r."userId" = u.id AND r."roleName" IN ('root','admin'))`, {}, t);
  const [daNang] = await p.sql(`SELECT 1 AS c FROM phien_ban_schema WHERE phien_ban IN (:v)`, { v: [MOC_MOT_LAN, PHIEN_BAN] }, t);
  const [daGhi] = await p.sql(`SELECT 1 AS c FROM phien_ban_schema WHERE phien_ban = :v`, { v: PHIEN_BAN }, t);
  if (!daNang) {
    for (const x of u) {
      await p.sql(`INSERT INTO pham_vi (nguoi_dung_id, tat_ca_kho, tat_ca_quy, ghi_chu, "createdAt", "updatedAt")
        VALUES (:u, true, true, 'Nâng cấp 0.4.0: giữ quyền như 0.3.2 — rà lại', now(), now())`, { u: x.id }, t);
      bc.cap_pham_vi.push(x.email || x.id);
    }
  }
  const a = await p.sql(`UPDATE don_ban_dong SET don_gia_tt = COALESCE(don_gia_tt, don_gia), tien_truoc_thue = COALESCE(tien_truoc_thue, thanh_tien),
      tien_thue = COALESCE(tien_thue, 0), giu_don = COALESCE(giu_don, 0), "updatedAt" = now()
    WHERE don_gia_tt IS NULL OR tien_truoc_thue IS NULL OR tien_thue IS NULL OR giu_don IS NULL RETURNING id`, {}, t);
  bc.dong_don = a.length;
  const b = await p.sql(`UPDATE luot_giao_dong SET so_kg_thuc = COALESCE(so_kg_thuc, so_kg), sl_tinh_tien = COALESCE(sl_tinh_tien, so_kg), tien_thue = COALESCE(tien_thue, 0),
      "updatedAt" = now() WHERE so_kg_thuc IS NULL OR sl_tinh_tien IS NULL RETURNING id`, {}, t);
  bc.dong_luot = b.length;
  await p.sql(`UPDATE don_ban SET tien_thue = COALESCE(tien_thue,0), phai_hoan = COALESCE(phai_hoan,0), kenh = COALESCE(kenh,'si') WHERE tien_thue IS NULL OR phai_hoan IS NULL OR kenh IS NULL`, {}, t);
  const [kl] = await p.sql(`SELECT id FROM khach_hang WHERE ma = (SELECT gia_tri FROM cau_hinh WHERE khoa = 'ma_khach_le')`, {}, t);
  bc.khach_le = kl ? 'có' : 'CHƯA CÓ — tạo khách mã KHACH-LE trước khi dùng Bán nhanh';
  const [tg] = await p.sql(`SELECT COUNT(*)::int AS n FROM kho WHERE trung_chuyen = true`, {}, t);
  bc.kho_trung_chuyen = tg.n ? `${tg.n} kho` : 'CHƯA CÓ — khai kho "Hàng đang vận chuyển" (đánh dấu trung chuyển) trước khi dùng Chuyển hàng';
  // Đơn đã duyệt đang chờ giao (từ 0.3.2): giữ tồn cấp đơn ngay khi nâng cấp (nếu cấu hình giữ khi duyệt) — báo phần giữ thiếu, không ép âm.
  bc.giu_don_cu = { so_don: 0, thieu: [] as string[] };
  if (!daNang && (await cauHinh(p, 'giu_khi_duyet', t)) === 'co') {
    const ds = await p.bang('don_ban').findAll({ where: { trang_thai: ['cho_xuat', 'dang_giao'] }, transaction: t, order: [['ngay', 'ASC'], ['id', 'ASC']] });
    for (const d of ds) {
      const r = await giuDon(p, t, d);
      bc.giu_don_cu.so_don++;
      for (const x of r.thieu) bc.giu_don_cu.thieu.push(`${d.so}: ${x}`);
    }
  }
  if (!daGhi) await p.sql(`INSERT INTO phien_ban_schema (phien_ban, ngay, ghi_chu, "createdAt", "updatedAt") VALUES (:v, :n, :g, now(), now())`,
    { v: PHIEN_BAN, n: new Date().toISOString(), g: JSON.stringify({ ...bc, nguoi, ngay: homNay() }) }, t);
  bc.phien_ban = PHIEN_BAN;
  bc.da_nang_truoc = !!daGhi;
  return bc;
}

export function dangKyNangCap(p: any, H: H, _h: any) {
  H['cau_hinh:nangCap'] = async (ctx, t) => {
    const vt = ctx.state?.currentRoles || [ctx.state?.currentRole];
    const [qt] = await p.sql(`SELECT 1 AS c FROM "rolesUsers" WHERE "userId" = :u AND "roleName" IN ('root','admin')`, { u: ctx.state?.currentUser?.id || 0 }, t);
    if (!qt && !(vt || []).includes('root')) loi('Chỉ quản trị hệ thống chạy nâng cấp dữ liệu.');
    return { ok: true, ...(await nangCap(p, t, p.nguoi(ctx))) };
  };
  H['cau_hinh:dat'] = async (ctx, t) => {
    if (!p.xemGia(ctx)) loi('Chỉ kế toán trưởng / quản lý đổi cấu hình.');
    const v = ctx.action?.params?.values || {};
    if (!MAC_DINH[v.khoa]) loi('Khóa cấu hình không hợp lệ.');
    await p.sql(`INSERT INTO cau_hinh (khoa, gia_tri, mo_ta, "createdAt", "updatedAt") VALUES (:k, :g, :m, now(), now())
      ON CONFLICT (khoa) DO UPDATE SET gia_tri = EXCLUDED.gia_tri, mo_ta = EXCLUDED.mo_ta || ' (đổi bởi ' || :n || ' ' || :d || ')', "updatedAt" = now()`,
    { k: v.khoa, g: String(v.gia_tri ?? ''), m: MAC_DINH[v.khoa][1], n: p.nguoi(ctx), d: homNay() }, t);
    return { ok: true };
  };
}
