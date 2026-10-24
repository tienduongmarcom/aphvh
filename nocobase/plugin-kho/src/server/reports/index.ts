/**
 * 0.4.0 Báo cáo vận hành + truy vết nguồn gốc.
 * - tongQuan: đơn gộp còn giao thiếu, công nợ theo bên bán, tiền chưa phân bổ, thu hộ đang giữ, CK chờ xác minh, WIP (mẻ mở), chênh lệch giao – nhận,
 *   hàng trong kho trung chuyển, hàng đợi hóa đơn, mẻ giá thành tạm tính. Số liệu lấy thẳng từ sổ — không có bảng tổng hợp riêng.
 * - truyVet: từ một lượt giao (bán) lần ngược: kho xuất ← các nguồn hình thành tồn (bình quân di động: liệt kê chứng từ nhập theo tỷ trọng)
 *   ← chuyến chuyển hàng / mẻ sản xuất ← NVL cấp ← phiếu nhập; và xuôi: đơn con → đơn gộp → phiếu thu → quỹ / tài khoản.
 */
import { Transaction } from 'sequelize';
import { kg, loi, tien } from '../tienich';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

export function dangKyBaoCao(p: any, H: H, h: any) {
  const { id, val } = h;
  H['don_gop:tongQuan'] = async (ctx, t) => {
    const gia = p.xemGia(ctx);
    const q = (s: string, r: any = {}) => p.sql(s, r, t);
    const out: any = {};
    out.don_gop_thieu = await q(`SELECT g.so, k.ten AS khach, g.tt_duyet, g.tt_giao, g.tt_thanh_toan, g.tt_hoa_don, g.tong_tien, g.con_no
      FROM don_gop g JOIN khach_hang k ON k.id = g.khach_id WHERE g.tt_duyet <> 'da_huy' AND g.tt_giao NOT IN ('du','dong') ORDER BY g.ngay, g.id LIMIT 500`);
    out.giao_con_thieu = await q(`SELECT d.so, v.ma AS ben_ban, m.ma AS mat_hang, dd.so_kg AS dat, COALESCE(dd.da_giao,0) AS da_giao,
        dd.so_kg - COALESCE(dd.da_giao,0) AS con, COALESCE(dd.giu_don,0) + COALESCE(dd.dang_giu,0) AS dang_giu
      FROM don_ban_dong dd JOIN don_ban d ON d.id = dd.don_ban_id JOIN don_vi v ON v.id = d.don_vi_ban_id JOIN mat_hang m ON m.id = dd.mat_hang_id
      WHERE d.trang_thai IN ('cho_xuat','dang_giao') AND dd.so_kg - COALESCE(dd.da_giao,0) > 0.0005 ORDER BY d.ngay, d.id LIMIT 1000`);
    out.cong_no_ben_ban = await q(`SELECT v.ma AS ben_ban, COUNT(*)::int AS so_don, SUM(d.con_no) AS con_no, SUM(d.phai_hoan) AS phai_hoan
      FROM don_ban d JOIN don_vi v ON v.id = d.don_vi_ban_id WHERE d.trang_thai <> 'da_huy' AND (d.con_no > 0 OR d.phai_hoan > 0) GROUP BY v.ma ORDER BY v.ma`);
    out.tien_chua_phan_bo = await q(`SELECT v.ma AS don_vi, p.loai_thu, COUNT(*)::int AS so_phieu, SUM(p.chua_phan_bo) AS so_tien FROM phieu_thu p JOIN don_vi v ON v.id = p.don_vi_id
      WHERE p.trang_thai = 'da_ghi' AND p.chua_phan_bo > 0 GROUP BY 1,2 ORDER BY 1,2`);
    out.ck_cho_xac_minh = await q(`SELECT v.ma AS don_vi, COUNT(*)::int AS so_phieu, SUM(p.so_tien) AS so_tien FROM phieu_thu p JOIN don_vi v ON v.id = p.don_vi_id
      WHERE p.trang_thai = 'cho_xac_minh' GROUP BY 1 ORDER BY 1`);
    out.thu_ho_dang_giu = await q(`SELECT a.ma AS don_vi_giu, b.ma AS giu_ho_cho, COUNT(*)::int AS so_khoan, SUM(h.so_tien - COALESCE(h.da_tat_toan,0)) AS con_giu
      FROM thu_ho h JOIN don_vi a ON a.id = h.don_vi_nhan_id JOIN don_vi b ON b.id = h.don_vi_chu_no_id WHERE h.trang_thai = 'dang_giu_ho' GROUP BY 1,2 ORDER BY 1,2`);
    out.wip = await q(`SELECT me.so, me.xuong, me.trang_thai, me.kg_nvl, me.kg_tp, ${gia ? 'me.gia_tri_nvl + me.gia_tri_bao_bi + me.chi_phi AS chi_phi,' : ''} me.ngay_mo
      FROM me_sx me WHERE me.trang_thai IN ('mo','tam_hoan_thanh','can_chot_lai') ORDER BY me.ngay_mo, me.id`);
    out.chenh_lech_giao_nhan = await q(`SELECT c.id, ch.so AS chuyen, m.ma AS mat_hang, c.so_kg, c.ly_do FROM chenh_lech_giao_nhan c
      JOIN chuyen_hang ch ON ch.id = c.chuyen_hang_id JOIN mat_hang m ON m.id = c.mat_hang_id WHERE c.trang_thai = 'cho_xu_ly' ORDER BY c.id`);
    out.hang_dang_di_duong = await q(`SELECT k.ten AS kho, m.ma AS mat_hang, t.so_kg FROM ton_kho t JOIN kho k ON k.id = t.kho_id JOIN mat_hang m ON m.id = t.mat_hang_id
      WHERE k.trung_chuyen = true AND ABS(t.so_kg) > 0.0005 ORDER BY 1,2`);
    out.hang_doi_hoa_don = await q(`SELECT v.ma AS ben_ban, h.trang_thai, COUNT(*)::int AS so_dong, SUM(h.tong) AS tong FROM hoa_don_cho_xuat h
      JOIN don_vi v ON v.id = h.don_vi_id WHERE h.trang_thai <> 'huy' GROUP BY 1,2 ORDER BY 1,2`);
    if (gia) {
      out.gia_thanh_tam = await q(`SELECT DISTINCT me.so, me.trang_thai FROM me_sx me JOIN phieu_kho k ON k.me_sx_id = me.id JOIN phieu_kho_dong d ON d.phieu_kho_id = k.id
        WHERE d.trang_thai_gia = 'tam' OR me.trang_thai IN ('mo','tam_hoan_thanh','can_chot_lai') ORDER BY me.so`);
    }
    return out;
  };

  /** Nguồn hình thành tồn của (mặt hàng × kho) tại thời điểm dòng sổ kho `den_id`: các lần nhập kể từ lần tồn về 0 gần nhất (tối đa 20). */
  const nguon = async (t: Transaction, mh: any, kho: any, denId: number, bac: number, daQua: Set<string>): Promise<any[]> => {
    const k0 = `${mh}|${kho}|${denId}`;
    if (bac > 4 || daQua.has(k0)) return [];
    daQua.add(k0);
    const rows = await p.sql(`SELECT id, so_kg, loai, chung_tu, nguon, nguon_id, ngay FROM so_kho WHERE mat_hang_id = :m AND kho_id = :k AND id < :d ORDER BY id DESC LIMIT 2000`,
      { m: mh, k: kho, d: denId }, t);
    // Đi lùi tới khi tồn tích lũy (từ đầu) về 0: tính số dư trước mỗi dòng.
    const [b] = await p.sql(`SELECT COALESCE(SUM(so_kg),0) AS b FROM so_kho WHERE mat_hang_id = :m AND kho_id = :k AND id < :d`, { m: mh, k: kho, d: denId }, t);
    let du = kg(b.b);
    const vao: any[] = [];
    for (const r of rows) {
      const q = kg(r.so_kg);
      if (q > 0) vao.push(r);
      du = kg(du - q);
      if (du <= 0.0005 || vao.length >= 20) break;
    }
    const tong = vao.reduce((a, r) => a + kg(r.so_kg), 0) || 1;
    const out: any[] = [];
    for (const r of vao) {
      const x: any = { chung_tu: r.chung_tu, loai: r.loai, ngay: r.ngay, so_luong: kg(r.so_kg), ty_trong_pct: Math.round((kg(r.so_kg) / tong) * 10000) / 100 };
      if (r.loai === 'chuyen_den') {
        const [di] = await p.sql(`SELECT s.id, s.kho_id, k.ten FROM so_kho s JOIN kho k ON k.id = s.kho_id WHERE s.chung_tu = :c AND s.mat_hang_id = :m AND s.loai = 'chuyen_di'
          AND s.so_kg < 0 AND s.id < :i ORDER BY s.id DESC LIMIT 1`, { c: r.chung_tu, m: mh, i: r.id }, t);
        if (di) { x.tu_kho = di.ten; x.nguon = await nguon(t, mh, di.kho_id, Number(di.id), bac + 1, daQua); }
      } else if (r.loai === 'thu_hoi_ra') {
        const [me] = await p.sql(`SELECT me.id, me.so FROM phieu_kho k JOIN me_sx me ON me.id = k.me_sx_id WHERE k.so = :c`, { c: r.chung_tu }, t);
        if (me) {
          x.me_sx = me.so;
          const nvl = await p.sql(`SELECT s.id, s.mat_hang_id, s.kho_id, s.so_kg, s.chung_tu, m.ma FROM so_kho s JOIN phieu_kho k ON k.so = s.chung_tu JOIN mat_hang m ON m.id = s.mat_hang_id
            WHERE k.me_sx_id = :me AND s.loai = 'cap_nvl' ORDER BY s.id`, { me: me.id }, t);
          x.nvl = [];
          for (const n of nvl) x.nvl.push({ mat_hang: n.ma, so_luong: -kg(n.so_kg), phieu: n.chung_tu, nguon: await nguon(t, n.mat_hang_id, n.kho_id, Number(n.id), bac + 1, daQua) });
        }
      }
      out.push(x);
    }
    return out;
  };
  H['luot_giao:truyVet'] = async (ctx, t) => {
    const lg = await p.bang('luot_giao').findByPk(id(ctx), { transaction: t });
    if (!lg) loi('Không thấy lượt giao.');
    const don = await p.bang('don_ban').findByPk(lg.don_ban_id, { transaction: t });
    const dg = don.don_gop_id ? await p.bang('don_gop').findByPk(don.don_gop_id, { transaction: t }) : null;
    const dong = await p.sql(`SELECT l.id, l.mat_hang_id, l.kho_id, l.so_kg_thuc, l.sl_tinh_tien, m.ma, k.ten AS kho FROM luot_giao_dong l
      JOIN mat_hang m ON m.id = l.mat_hang_id JOIN kho k ON k.id = l.kho_id WHERE l.luot_giao_id = :l ORDER BY l.id`, { l: lg.id }, t);
    const hang: any[] = [];
    for (const d of dong) {
      const [sk] = await p.sql(`SELECT id, so_kg FROM so_kho WHERE chung_tu = :c AND nguon = 'luot_giao_dong' AND nguon_id = :n AND loai = 'ban' ORDER BY id LIMIT 1`, { c: lg.so, n: d.id }, t);
      const [dem] = await p.sql(`SELECT COUNT(*)::int AS n, COALESCE(SUM(so_kg),0) AS sl FROM so_kho WHERE chung_tu = :c AND nguon = 'luot_giao_dong' AND nguon_id = :n
        AND loai = 'ban'`, { c: lg.so, n: d.id }, t);
      hang.push({ mat_hang: d.ma, kho: d.kho, thuc_xuat: kg(d.so_kg_thuc), tinh_tien: kg(d.sl_tinh_tien), so_dong_so_kho_xuat: dem.n, tong_tru_kho: -kg(dem.sl),
        nguon: sk ? await nguon(t, d.mat_hang_id, d.kho_id, Number(sk.id), 0, new Set()) : [] });
    }
    const thu = await p.sql(`SELECT p.so, p.trang_thai, p.hinh_thuc, q.ten AS quy, v.ma AS don_vi_nhan, b.so_tien, COALESCE(b.thu_ho,false) AS thu_ho FROM phieu_thu_phan_bo b
      JOIN phieu_thu p ON p.id = b.phieu_thu_id JOIN quy q ON q.id = p.quy_id JOIN don_vi v ON v.id = p.don_vi_id WHERE b.don_ban_id = :d ORDER BY p.id`, { d: don.id }, t);
    const [bv] = await p.sql(`SELECT ma FROM don_vi WHERE id = :i`, { i: don.don_vi_ban_id }, t);
    return { luot: lg.so, don_con: don.so, ben_ban: bv?.ma, don_gop: dg?.so || null, phai_thu: tien(don.phai_thu), da_thu: tien(don.da_thu), con_no: tien(don.con_no),
      ...(p.xemGia(ctx) ? { gia_von: tien(lg.gia_von) } : {}), hang, thanh_toan: thu };
  };
  void val;
}
