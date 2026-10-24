/**
 * 0.3.1 — Go-Live & số dư đầu kỳ, quản lý tài sản, mẻ sản xuất (dở dang, chi phí đến sau, chốt / chốt lại giá thành).
 *
 * Nguyên tắc:
 * - Không ghi thẳng vào sổ kho / tồn / sổ quỹ / giá vốn. Lô nhập → kiểm tra → duyệt → ghi sổ qua chứng từ và lõi nghiệp vụ sẵn có.
 * - Mỗi số dư có KHÓA CHỐNG TRÙNG (bảng mo_so_khoa, unique): dán lại cùng file / lập tay trùng đều bị chặn.
 * - Ghi một lô = một giao dịch: lỗi một dòng thì không ghi dòng nào.
 * - Chỉ kế toán / quản lý mở sổ, duyệt, ghi; kiểm ở máy chủ, không chỉ ẩn nút.
 * - Mẻ sản xuất chỉ tập hợp chi phí và phân bổ; số lượng, giá trị kho vẫn qua sổ kho / sổ giá trị.
 */
import { Transaction } from 'sequelize';
import { homNay, kg, loi, tien, vnd } from './tienich';
import { dieuChinhGiaTri, docCsv, kiemKho } from './toan_ven';
import * as crypto from 'crypto';

type H = Record<string, (ctx: any, t: Transaction) => Promise<any>>;

// ---------------- Cột theo loại dữ liệu ----------------
type Cot = { k: string; ten: string[]; kieu?: 'so' | 'ngay' | 'chu'; bat_buoc?: boolean };
const C = (k: string, ten: string | string[], kieu?: Cot['kieu'], bat_buoc = false): Cot => ({ k, ten: ([] as string[]).concat(ten), kieu, bat_buoc });
export const COT: Record<string, Cot[]> = {
  mat_hang: [C('ma', ['Mã hàng', 'Item Code', 'Mã'], 'chu', true), C('ten', ['Tên hàng', 'Tên'], 'chu', true), C('dvt_ton', ['ĐVT tồn', 'ĐVT', 'UOM']),
    C('loai_hang', ['Loại hàng']), C('kg_bao', ['Kg/bao', 'Quy cách kg'], 'so'), C('gia_ban', ['Giá bán'], 'so'), C('gia_san', ['Giá sàn'], 'so')],
  khach_hang: [C('ma', ['Mã khách', 'Mã'], 'chu', true), C('ten', ['Tên khách', 'Tên'], 'chu', true), C('sdt', ['Điện thoại', 'SĐT']),
    C('dia_chi', ['Địa chỉ']), C('mst', ['MST', 'Mã số thuế']), C('han_muc', ['Hạn mức'], 'so'), C('ghi_chu', ['Ghi chú'])],
  nha_cung_cap: [C('ma', ['Mã NCC', 'Mã'], 'chu', true), C('ten', ['Tên nhà cung cấp', 'Tên NCC', 'Tên'], 'chu', true), C('sdt', ['Điện thoại', 'SĐT']),
    C('dia_chi', ['Địa chỉ']), C('mst', ['MST', 'Mã số thuế']), C('ghi_chu', ['Ghi chú'])],
  kho: [C('ma', ['Mã kho', 'Mã'], 'chu', true), C('ten', ['Tên kho', 'Tên'], 'chu', true), C('loai_kho', ['Loại kho']), C('dia_diem', ['Địa điểm']),
    C('trung_chuyen', ['Kho đang vận chuyển'])],
  quy: [C('ma', ['Mã quỹ', 'Mã'], 'chu', true), C('ten', ['Tên quỹ / tài khoản', 'Tên quỹ', 'Tên'], 'chu', true), C('don_vi', ['Đơn vị', 'Mã đơn vị'], 'chu', true),
    C('loai', ['Loại'], 'chu', true), C('nguoi_giu', ['Người giữ quỹ', 'Người giữ'])],
  tai_san: [C('ma', ['Mã tài sản', 'Mã'], 'chu', true), C('ten', ['Tên tài sản', 'Tên'], 'chu', true), C('loai', ['Loại']), C('serial', ['Serial', 'Số serial']),
    C('dia_diem', ['Địa điểm']), C('nguoi_quan_ly', ['Người quản lý', 'Người giữ']), C('bo_phan', ['Bộ phận']), C('tinh_trang', ['Tình trạng']),
    C('ngay_mua', ['Ngày mua'], 'ngay'), C('nguyen_gia', ['Nguyên giá'], 'so'), C('so_thang_sd', ['Số tháng sử dụng', 'Thời gian sử dụng (tháng)'], 'so'),
    C('so_luong', ['Số lượng'], 'so'), C('don_vi', ['Đơn vị đứng tên', 'Pháp nhân']), C('chung_tu_mua', ['Chứng từ mua']),
    C('dung_cho_san_xuat', ['Dùng cho sản xuất'])],
  ton_dau_ky: [C('kho', ['Mã kho', 'Kho'], 'chu', true), C('mat_hang', ['Mã hàng', 'Item Code'], 'chu', true), C('so_luong', ['Số lượng', 'Số lượng tồn'], 'so', true),
    C('so_bao', ['Số bao', 'Số bao/thùng'], 'so'), C('gia_tri', ['Giá trị', 'Giá trị tồn'], 'so'),
    C('tinh_trang_gia', ['Tình trạng giá']), C('tinh_trang_hang', ['Tình trạng hàng']), C('ghi_chu', ['Ghi chú', 'Người xác nhận'])],
  no_khach: [C('khach', ['Mã khách'], 'chu', true), C('don_vi', ['Đơn vị', 'Mã đơn vị', 'Pháp nhân'], 'chu', true), C('so_tien', ['Số dư', 'Số tiền', 'Số nợ'], 'so', true),
    C('chung_tu_goc', ['Chứng từ gốc', 'Số chứng từ']), C('ngay_ct', ['Ngày phát sinh', 'Ngày chứng từ'], 'ngay'), C('han_tt', ['Hạn thanh toán'], 'ngay'),
    C('doi_chieu', ['Đối chiếu']), C('ghi_chu', ['Ghi chú'])],
  no_ncc: [C('ncc', ['Mã NCC'], 'chu', true), C('don_vi', ['Đơn vị', 'Mã đơn vị', 'Pháp nhân'], 'chu', true), C('so_tien', ['Số dư', 'Số tiền', 'Số nợ'], 'so', true),
    C('chung_tu_goc', ['Chứng từ gốc', 'Số chứng từ']), C('ngay_ct', ['Ngày phát sinh', 'Ngày chứng từ'], 'ngay'), C('han_tt', ['Hạn thanh toán'], 'ngay'),
    C('doi_chieu', ['Đối chiếu']), C('ghi_chu', ['Ghi chú'])],
  quy_dau_ky: [C('quy', ['Mã quỹ', 'Mã tài khoản'], 'chu', true), C('so_tien', ['Số dư', 'Số tiền'], 'so', true), C('ghi_chu', ['Ghi chú', 'Căn cứ'])],
  tien_chua_pb: [C('quy', ['Mã quỹ', 'Mã tài khoản'], 'chu', true), C('loai_thu', ['Loại'], 'chu', true), C('so_tien', ['Số tiền'], 'so', true),
    C('ma_tham_chieu', ['Mã tham chiếu', 'Mã GD', 'Mã giao dịch'], 'chu', true), C('khach', ['Mã khách']), C('muc_dich_coc', ['Mục đích cọc', 'Thỏa thuận']),
    C('ngay', ['Ngày nhận'], 'ngay'), C('ghi_chu', ['Ghi chú'])],
  thu_ho_dau_ky: [C('don_vi_giu', ['Đơn vị giữ tiền'], 'chu', true), C('don_vi_chu_no', ['Đơn vị được trả', 'Giữ hộ cho'], 'chu', true),
    C('so_tien', ['Số tiền'], 'so', true), C('ma_tham_chieu', ['Mã tham chiếu'], 'chu', true), C('ghi_chu', ['Ghi chú', 'Căn cứ'])],
  quy_doi_dvt: [C('mat_hang', ['Mã hàng'], 'chu', true), C('dvt', ['Đơn vị giao dịch', 'ĐVT'], 'chu', true), C('he_so', ['Hệ số', 'Bằng bao nhiêu ĐVT tồn'], 'so', true),
    C('mac_dinh', ['Mặc định'])],
  do_dang_dau_ky: [C('ma', ['Mã dở dang', 'Mã'], 'chu', true), C('kho', ['Mã kho nhà máy', 'Mã kho'], 'chu', true), C('kg', ['Kg dở dang', 'Kg'], 'so', true),
    C('gia_tri', ['Giá trị'], 'so', true), C('xuong', ['Xưởng / tổ', 'Xưởng']), C('san_pham', ['Sản phẩm dự kiến']), C('ghi_chu', ['Ghi chú', 'Căn cứ'])],
  don_chuyen_tiep: [C('so_don_cu', ['Số đơn cũ', 'Số đơn'], 'chu', true), C('khach', ['Mã khách'], 'chu', true), C('don_vi', ['Đơn vị bán', 'Mã đơn vị'], 'chu', true),
    C('mat_hang', ['Mã hàng'], 'chu', true), C('kho', ['Mã kho', 'Kho xuất'], 'chu', true), C('so_luong', ['Số lượng còn giao', 'Số lượng'], 'so', true),
    C('don_gia', ['Đơn giá'], 'so', true), C('tinh_trang', ['Tình trạng']), C('cach_giao', ['Cách giao']), C('ngay', ['Ngày đặt'], 'ngay'),
    C('nguoi_nhan', ['Người nhận / xe', 'Người nhận']), C('ghi_chu', ['Ghi chú']), C('gia_von', ['Giá vốn', 'Giá vốn quản trị'], 'so'),
    C('dang_giu', ['Đang giữ hàng']), C('da_thu', ['Đã thu', 'Khách đã trả'], 'so'), C('quy_da_thu', ['Mã quỹ đã thu'])],
};
const DANH_MUC = ['mat_hang', 'khach_hang', 'nha_cung_cap', 'kho', 'quy', 'tai_san'];
const TIEN_NO = ['no_khach', 'no_ncc', 'quy_dau_ky', 'tien_chua_pb', 'thu_ho_dau_ky'];
const MO_SO = ['ton_dau_ky', 'no_khach', 'no_ncc', 'quy_dau_ky', 'tien_chua_pb', 'thu_ho_dau_ky', 'don_chuyen_tiep', 'do_dang_dau_ky'];

const boDau = (s: string) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().trim();
/** Đọc số kiểu Việt / Excel: 1.234.567 | 1,5 | 1.234,5 | 25.5 */
export const docSo = (v: string) => {
  v = String(v ?? '').replace(/\s|đ|VND/gi, '');
  if (!v) return null;
  let n: number;
  if (v.includes('.') && v.includes(',')) n = v.lastIndexOf(',') > v.lastIndexOf('.') ? Number(v.replace(/\./g, '').replace(',', '.')) : Number(v.replace(/,/g, ''));
  else if (v.includes(',')) n = /^-?\d{1,3}(,\d{3})+$/.test(v) ? Number(v.replace(/,/g, '')) : Number(v.replace(',', '.'));
  else if (/^-?\d{1,3}(\.\d{3})+$/.test(v)) n = Number(v.replace(/\./g, ''));
  else n = Number(v);
  return Number.isFinite(n) ? n : NaN;
};
const docNgay = (v: string) => {
  v = String(v || '').trim();
  if (!v) return null;
  let m = v.match(/^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$/);
  if (m) return `${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`;
  m = v.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  return 'SAI';
};
const co = (v: any) => /^(1|x|có|co|true|yes|đúng)$/i.test(String(v || '').trim());
/** Chọn giá trị theo nhãn tiếng Việt hoặc mã. */
const chon = (v: string, m: Record<string, string[]>, macDinh?: string) => {
  const b = boDau(v);
  if (!b) return macDinh;
  for (const [k, ds] of Object.entries(m)) if (b === k || ds.some((x) => boDau(x) === b)) return k;
  return 'SAI';
};
const M_DVT = { kg: ['kg', 'kilogram'], cai: ['cái', 'chiếc', 'pcs'], goi: ['gói'], bao: ['bao'], thung: ['thùng'], lit: ['lít', 'lit', 'l'] };
const M_LOAI_HANG = { hang_hoa: ['hàng hóa'], nguyen_lieu: ['nguyên liệu', 'nvl'], thanh_pham: ['thành phẩm'], phu_pham: ['phụ phẩm'], bao_bi: ['bao bì', 'vật tư', 'bao bì / vật tư'] };
const M_LOAI_KHO = { ban_duoc: ['bán được', 'kho bán được'], nha_may: ['nhà máy', 'kho nhà máy'], cho_xu_ly: ['chờ xử lý', 'kho chờ xử lý'] };
const M_LOAI_QUY = { tien_mat: ['tiền mặt', 'tm'], ngan_hang: ['ngân hàng', 'nh', 'ck', 'chuyển khoản'] };
const M_GIA = { co_gia: ['đã chốt', 'có giá', 'chốt'], tam: ['tạm tính', 'tạm', 'tạm tính được duyệt'], cho_gia: ['chưa xác định', 'chờ định giá', 'chưa có giá', 'chưa'] };
const M_HANG = { ban_duoc: ['bán được'], cho_xu_ly: ['chờ xử lý', 'hỏng'], dang_van_chuyen: ['đang vận chuyển'] };
const M_THU = { coc: ['cọc', 'đặt cọc'], chua_ro: ['chưa rõ', 'chưa rõ người nộp'], thu_no: ['chưa phân bổ', 'tiền thừa', 'khách đã nộp chưa phân bổ', 'trả nợ'] };
const M_DC = { da: ['đã đối chiếu', 'đã', 'rồi'], cho: ['chờ đối chiếu', 'chờ', 'chưa'] };
const M_TS = { tscd: ['tài sản cố định', 'tscđ', 'tscd'], ccdc: ['công cụ dụng cụ', 'ccdc'], van_phong: ['thiết bị văn phòng', 'văn phòng'] };
const M_TT_TS = { dang_dung: ['đang dùng'], trong_kho: ['trong kho'], hong: ['hỏng'], cho_thanh_ly: ['chờ thanh lý'], da_thanh_ly: ['đã thanh lý'], mat: ['mất'] };
const M_DON = { cho_giao: ['chưa giao', 'chờ giao', 'đã chốt'], dang_van_chuyen: ['đang vận chuyển', 'đã bàn giao xe', 'trên xe'] };
const M_GIAO = { khach_den_lay: ['khách đến lấy', 'khách lấy'], van_chuyen: ['vận chuyển', 'giao xe'] };

/** Tách bảng dán từ Excel / Google Sheets (tab) hoặc CSV. Dòng đầu là tiêu đề. */
export function tachBang(goc: string, cot: Cot[]) {
  const bang = docCsv(goc);
  if (bang.length < 2) loi('Dán cả dòng tiêu đề và ít nhất một dòng dữ liệu.');
  const dau = bang[0].map((x) => boDau(x));
  const viTri: Record<string, number> = {};
  for (const c of cot) {
    const i = dau.findIndex((h) => c.ten.some((t) => boDau(t) === h) || h === c.k);
    if (i >= 0) viTri[c.k] = i;
    else if (c.bat_buoc) loi(`Thiếu cột bắt buộc "${c.ten[0]}". Tiêu đề phải có: ${cot.filter((x) => x.bat_buoc).map((x) => x.ten[0]).join(', ')}.`);
  }
  return bang.slice(1).map((o, i) => {
    const r: any = { _stt: i + 2 };
    for (const c of cot) if (viTri[c.k] !== undefined) r[c.k] = String(o[viTri[c.k]] ?? '').trim();
    return r;
  }).filter((r) => cot.some((c) => r[c.k]));
}

export function dangKyMoRong(p: any, H: H, h: { id: (ctx: any) => any; val: (ctx: any) => any; lyDo: (ctx: any) => any }) {
  const { id, val, lyDo } = h;
  const bang = (n: string) => p.bang(n);
  const canQuyen = (ctx: any, viec = 'thao tác này') => { if (!p.xemGia(ctx)) loi(`Chỉ kế toán / quản lý được ${viec}.`); };
  /** Gọi một thao tác nghiệp vụ có sẵn với cùng người dùng (giữ kiểm quyền / nghiệp vụ của thao tác đó). */
  const goi = (ten: string, ctx: any, t: Transaction, filterByTk: any, values: any = {}) =>
    H[ten]({ ...ctx, action: { ...ctx.action, params: { filterByTk, values } } }, t);

  const timMa = async (b: string, ma: any, t: Transaction) => (ma ? bang(b).findOne({ where: { ma: String(ma).trim() }, transaction: t }) : null);
  const kyMo = async (t: Transaction) => {
    const k = await bang('ky_mo_so').findOne({ where: { trang_thai: 'mo' }, order: [['id', 'DESC']], transaction: t });
    if (!k) loi('Chưa có kỳ mở sổ đang mở (Go-Live → Kỳ mở sổ), hoặc kỳ đã khóa: không ghi số dư đầu kỳ được nữa.');
    if (!k.ngay_chot) loi(`Kỳ ${k.ma} chưa có ngày chốt số dư: nhập ngày chốt trước.`);
    return k;
  };
  p.kyMo = kyMo;
  /** Ghi khóa chống trùng; trùng thì báo lỗi rõ ràng. */
  const giuKhoa = async (t: Transaction, khoa: string, nhap_lo_id: any, ket_qua: string) => {
    const [d] = await p.sql(`SELECT ket_qua FROM mo_so_khoa WHERE khoa = :k`, { k: khoa }, t);
    if (d) loi(`Số dư này đã được ghi trước đó (${d.ket_qua}). Khóa: ${khoa}. Sai thì lập chứng từ điều chỉnh / hủy chứng từ cũ, không nhập lại.`);
    await bang('mo_so_khoa').create({ khoa, nhap_lo_id, ket_qua }, { transaction: t, hooks: false });
  };
  p.giuKhoa = giuKhoa;
  const boKhoa = (t: Transaction, ket_qua: string) => p.sql(`DELETE FROM mo_so_khoa WHERE ket_qua = :k`, { k: ket_qua }, t);
  p.boKhoa = boKhoa;

  // ---------------- KỲ MỞ SỔ ----------------
  H['ky_mo_so:khoa'] = async (ctx, t) => {
    canQuyen(ctx, 'khóa kỳ mở sổ');
    const k = await p.khoa('ky_mo_so', id(ctx), t);
    if (k.trang_thai === 'da_khoa') return { ok: true };
    const [r] = await p.sql(`SELECT COUNT(*)::int AS n FROM nhap_lo WHERE ky_mo_so_id = :k AND trang_thai IN ('nhap','da_kiem','da_duyet')`, { k: k.id }, t);
    if (r.n > 0 && !val(ctx).bo_qua_lo_dang_do) loi(`Còn ${r.n} lô nhập chưa ghi / chưa hủy trong kỳ này.`);
    await k.update({ trang_thai: 'da_khoa', khoa_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };

  // ---------------- LÔ NHẬP ----------------
  /** Kiểm từng dòng: tra mã, tính khóa chống trùng, gom tổng đối chiếu. Không ghi sổ. */
  const kiemLo = async (ctx: any, t: Transaction, lo: any, ky: any) => {
    const cot = COT[lo.loai] || loi('Loại dữ liệu không hợp lệ.');
    const rows = tachBang(lo.du_lieu_goc, cot);
    const kq: any[] = [];
    const daThay = new Set<string>();
    const tong: Record<string, { so_luong: number; gia_tri: number; so_dong: number }> = {};
    const cong = (nhom: string, sl: number, gt: number) => {
      tong[nhom] = tong[nhom] || { so_luong: 0, gia_tri: 0, so_dong: 0 };
      tong[nhom].so_luong = kg(tong[nhom].so_luong + (sl || 0));
      tong[nhom].gia_tri = tien(tong[nhom].gia_tri + (gt || 0));
      tong[nhom].so_dong++;
    };
    const cache: Record<string, any> = {};
    const tra = async (b: string, ma: string) => {
      const k = `${b}:${ma}`;
      if (!(k in cache)) cache[k] = await timMa(b, ma, t);
      return cache[k];
    };
    for (const r of rows) {
      const L: string[] = [];
      const d: any = { ...r };
      for (const c of cot) {
        if (c.bat_buoc && !String(r[c.k] ?? '').trim()) L.push(`thiếu "${c.ten[0]}"`);
        if (c.kieu === 'so' && String(r[c.k] ?? '').trim()) { d[c.k] = docSo(r[c.k]); if (Number.isNaN(d[c.k])) L.push(`"${c.ten[0]}" không phải số`); }
        if (c.kieu === 'ngay' && String(r[c.k] ?? '').trim()) { d[c.k] = docNgay(r[c.k]); if (d[c.k] === 'SAI') L.push(`"${c.ten[0]}" sai ngày (dd/mm/yyyy)`); }
        if ((c.kieu === 'ngay' || c.kieu === 'so') && !String(r[c.k] ?? '').trim()) d[c.k] = null;
      }
      let khoa = '';
      let trung = '';
      const L2 = async () => {
        if (lo.loai === 'quy_doi_dvt') {
          const mh = await tra('mat_hang', d.mat_hang);
          if (!mh) L.push(`không có mặt hàng mã "${d.mat_hang}"`);
          d.dvt = chon(r.dvt, { bao: ['bao'], thung: ['thùng'], goi: ['gói'], cai: ['cái'], kg: ['kg'] });
          if (!d.dvt || d.dvt === 'SAI') L.push('ĐVT: Bao / Thùng / Gói / Cái / Kg');
          if (!(d.he_so > 0)) L.push('hệ số phải > 0');
          d.mac_dinh = co(r.mac_dinh);
          if (mh) {
            d.mat_hang_id = mh.id; delete d.mat_hang;
            const [cu] = await p.sql(`SELECT id, he_so FROM quy_doi_dvt WHERE mat_hang_id = :m AND dvt = :d`, { m: mh.id, d: d.dvt }, t);
            if (cu) { d._co_id = cu.id; trung = Number(cu.he_so) === Number(d.he_so) ? 'Đã có, không khác' : `Đã có hệ số ${cu.he_so}` + (lo.che_do === 'cap_nhat' ? ' → sẽ CẬP NHẬT' : ' → bỏ qua'); }
          }
          khoa = `qd|${d.mat_hang_id}|${d.dvt}`;
          return;
        }
        if (DANH_MUC.includes(lo.loai)) {
          const cu = await tra(lo.loai, d.ma);
          khoa = `dm|${lo.loai}|${d.ma}`;
          if (lo.loai === 'mat_hang') {
            if (r.dvt_ton !== undefined) { d.dvt_ton = chon(r.dvt_ton, M_DVT, 'kg'); if (d.dvt_ton === 'SAI') L.push('ĐVT tồn phải là Kg / Cái / Gói / Bao / Thùng'); }
            if (r.loai_hang !== undefined) { d.loai_hang = chon(r.loai_hang, M_LOAI_HANG, 'hang_hoa'); if (d.loai_hang === 'SAI') L.push('Loại hàng không hợp lệ'); }
          }
          if (lo.loai === 'kho') {
            d.loai_kho = chon(r.loai_kho, M_LOAI_KHO, 'ban_duoc'); if (d.loai_kho === 'SAI') L.push('Loại kho: Bán được / Nhà máy / Chờ xử lý');
            d.trung_chuyen = co(r.trung_chuyen);
          }
          if (lo.loai === 'quy') {
            const dv = await tra('don_vi', d.don_vi); if (!dv) L.push(`không có đơn vị mã "${d.don_vi}"`); else d.don_vi_id = dv.id;
            d.loai = chon(r.loai, M_LOAI_QUY); if (!d.loai || d.loai === 'SAI') L.push('Loại quỹ: Tiền mặt / Ngân hàng');
            delete d.don_vi;
          }
          if (lo.loai === 'tai_san') {
            d.loai = chon(r.loai, M_TS, 'tscd'); if (d.loai === 'SAI') L.push('Loại: TSCĐ / CCDC / Thiết bị văn phòng');
            d.tinh_trang = chon(r.tinh_trang, M_TT_TS, 'dang_dung'); if (d.tinh_trang === 'SAI') L.push('Tình trạng không hợp lệ');
            if (d.don_vi) { const dv = await tra('don_vi', d.don_vi); if (!dv) L.push(`không có đơn vị mã "${d.don_vi}"`); else d.don_vi_so_huu_id = dv.id; }
            delete d.don_vi;
            d.dung_cho_san_xuat = co(r.dung_cho_san_xuat);
          }
          if (cu) {
            const khac = Object.keys(d).filter((k) => !k.startsWith('_') && d[k] !== '' && d[k] !== null && d[k] !== undefined && String(cu[k] ?? '') !== String(d[k]));
            trung = khac.length ? `Mã đã có, khác ở: ${khac.join(', ')}` + (lo.che_do === 'cap_nhat' ? ' → sẽ CẬP NHẬT' : ' → bỏ qua (chọn "Cập nhật theo file" nếu muốn ghi đè)') : 'Mã đã có, không khác';
            d._co_id = cu.id;
          }
          return;
        }
        const kyMa = ky.ma;
        if (lo.loai === 'ton_dau_ky') {
          const kho = await tra('kho', d.kho); const mh = await tra('mat_hang', d.mat_hang);
          if (!kho) L.push(`không có kho mã "${d.kho}"`);
          if (!mh) L.push(`không có mặt hàng mã "${d.mat_hang}"`);
          if (!(d.so_luong > 0)) L.push('số lượng phải lớn hơn 0');
          d.tinh_trang_gia = chon(r.tinh_trang_gia, M_GIA, d.gia_tri > 0 ? 'co_gia' : 'cho_gia');
          if (d.tinh_trang_gia === 'SAI') L.push('Tình trạng giá: Đã chốt / Tạm tính / Chưa xác định');
          if (d.tinh_trang_gia !== 'cho_gia' && !(d.gia_tri > 0)) L.push('đã chốt / tạm tính thì phải có giá trị > 0 (chưa có giá: ghi "Chưa xác định", không ghi 0)');
          if (d.tinh_trang_gia === 'cho_gia' && d.gia_tri) L.push('chưa xác định giá thì để trống giá trị');
          d.tinh_trang_hang = chon(r.tinh_trang_hang, M_HANG, 'ban_duoc');
          if (d.tinh_trang_hang === 'SAI') L.push('Tình trạng hàng: Bán được / Chờ xử lý / Đang vận chuyển');
          if (kho && d.tinh_trang_hang === 'cho_xu_ly' && kho.loai_kho !== 'cho_xu_ly') L.push('hàng chờ xử lý phải nhập vào kho loại "Chờ xử lý"');
          if (kho && d.tinh_trang_hang === 'dang_van_chuyen' && !kho.trung_chuyen) L.push('hàng đang vận chuyển phải nhập vào kho "đang vận chuyển"');
          if (kho && d.tinh_trang_hang === 'ban_duoc' && kho.loai_kho === 'cho_xu_ly') L.push('kho chờ xử lý không chứa hàng bán được');
          if (kho && mh) {
            d.kho_id = kho.id; d.mat_hang_id = mh.id; khoa = `ton|${kyMa}|${kho.id}|${mh.id}`; cong(kho.ma, d.so_luong, d.gia_tri || 0);
            // Mở tồn chỉ khi mã × kho CHƯA có phát sinh ngoài quy trình mở sổ (nếu đã có: dùng phiếu kiểm kê có duyệt, không mở tồn chồng lên).
            const [ps] = await p.sql(`SELECT COUNT(*)::int AS n, MIN(chung_tu) AS ct FROM so_kho WHERE kho_id = :k AND mat_hang_id = :m
              AND loai NOT IN ('dau_ky','huy_dau_ky')`, { k: kho.id, m: mh.id }, t);
            if (ps.n > 0) L.push(`mã × kho đã có ${ps.n} phát sinh (vd. ${ps.ct}) trước khi mở sổ — không mở tồn chồng; đối chiếu và dùng phiếu kiểm kê có duyệt`);
          }
        } else if (lo.loai === 'no_khach' || lo.loai === 'no_ncc') {
          const ben = lo.loai === 'no_khach' ? await tra('khach_hang', d.khach) : await tra('nha_cung_cap', d.ncc);
          const dv = await tra('don_vi', d.don_vi);
          if (!ben) L.push(`không có ${lo.loai === 'no_khach' ? 'khách' : 'NCC'} mã "${d.khach || d.ncc}"`);
          if (!dv) L.push(`không có đơn vị mã "${d.don_vi}" (APH / VH / MK / TL)`);
          if (!(d.so_tien > 0)) L.push('số dư phải lớn hơn 0 (khách trả trước / NCC ứng trước: nhập ở "Tiền cọc / chưa phân bổ")');
          d.doi_chieu = chon(r.doi_chieu, M_DC, 'cho'); if (d.doi_chieu === 'SAI') L.push('Đối chiếu: Đã đối chiếu / Chờ đối chiếu');
          if (ben && dv) { d.ben_id = ben.id; d.don_vi_id = dv.id; khoa = `${lo.loai}|${kyMa}|${ben.id}|${dv.id}|${boDau(d.chung_tu_goc) || 'tong'}`; cong(dv.ma, 0, d.so_tien); }
        } else if (lo.loai === 'quy_dau_ky') {
          const q = await tra('quy', d.quy);
          if (!q) L.push(`không có quỹ mã "${d.quy}"`);
          if (d.so_tien === null || d.so_tien === undefined || d.so_tien < 0) L.push('số dư phải ≥ 0');
          if (q) {
            d.quy_id = q.id; khoa = `quy|${kyMa}|${q.id}`; cong(q.ma, 0, d.so_tien);
            const [x] = await p.sql(`SELECT COUNT(*)::int AS n FROM so_quy WHERE quy_id = :q`, { q: q.id }, t);
            if (x.n > 0) L.push(`quỹ đã có ${x.n} dòng sổ quỹ: số dư đầu kỳ phải ghi trước mọi phát sinh`);
          }
        } else if (lo.loai === 'tien_chua_pb') {
          const q = await tra('quy', d.quy);
          if (!q) L.push(`không có quỹ mã "${d.quy}"`);
          d.loai_thu = chon(r.loai_thu, M_THU); if (!d.loai_thu || d.loai_thu === 'SAI') L.push('Loại: Cọc / Chưa rõ / Chưa phân bổ');
          if (!(d.so_tien > 0)) L.push('số tiền phải lớn hơn 0');
          if (d.khach) { const k = await tra('khach_hang', d.khach); if (!k) L.push(`không có khách mã "${d.khach}"`); else d.khach_id = k.id; }
          if (d.loai_thu !== 'chua_ro' && !d.khach_id) L.push('cọc / tiền thừa phải có mã khách (không rõ khách: loại "Chưa rõ")');
          if (d.loai_thu === 'chua_ro' && d.khach_id) L.push('loại "Chưa rõ" thì để trống mã khách');
          if (q) { d.quy_id = q.id; d.don_vi_id = q.don_vi_id; d.hinh_thuc = q.loai === 'tien_mat' ? 'tien_mat' : 'chuyen_khoan'; khoa = `tpb|${kyMa}|${q.id}|${boDau(d.ma_tham_chieu)}`; cong(q.ma, 0, d.so_tien); }
        } else if (lo.loai === 'thu_ho_dau_ky') {
          const a = await tra('don_vi', d.don_vi_giu); const b = await tra('don_vi', d.don_vi_chu_no);
          if (!a || !b) L.push('mã đơn vị không đúng (APH / VH / MK / TL)');
          if (a && b && a.id === b.id) L.push('hai đơn vị phải khác nhau');
          if (!(d.so_tien > 0)) L.push('số tiền phải lớn hơn 0');
          if (a && b) { d.don_vi_nhan_id = a.id; d.don_vi_chu_no_id = b.id; khoa = `thuho|${kyMa}|${boDau(d.ma_tham_chieu)}`; cong(`${a.ma}→${b.ma}`, 0, d.so_tien); }
        } else if (lo.loai === 'do_dang_dau_ky') {
          const kho = await tra('kho', d.kho);
          if (!kho) L.push(`không có kho mã "${d.kho}"`); else if (kho.loai_kho !== 'nha_may') L.push('dở dang phải thuộc kho nhà máy');
          if (!(d.kg > 0)) L.push('kg dở dang phải > 0');
          if (!(d.gia_tri > 0)) L.push('giá trị dở dang phải > 0 (chưa có giá trị: chưa nhập dòng này)');
          if (kho) { d.kho_id = kho.id; khoa = `wip|${kyMa}|${boDau(d.ma)}`; cong(kho.ma, d.kg, d.gia_tri); }
        } else if (lo.loai === 'quy_doi_dvt') {
          return;
        } else if (lo.loai === 'don_chuyen_tiep') {
          const k = await tra('khach_hang', d.khach); const dv = await tra('don_vi', d.don_vi);
          const mh = await tra('mat_hang', d.mat_hang); const kho = await tra('kho', d.kho);
          if (!k) L.push(`không có khách mã "${d.khach}"`); if (!dv) L.push(`không có đơn vị mã "${d.don_vi}"`);
          if (!mh) L.push(`không có mặt hàng mã "${d.mat_hang}"`); if (!kho) L.push(`không có kho mã "${d.kho}"`);
          if (!(d.so_luong > 0)) L.push('số lượng còn giao phải > 0');
          if (!(d.don_gia >= 0)) L.push('thiếu đơn giá');
          d.tinh_trang = chon(r.tinh_trang, M_DON, 'cho_giao'); if (d.tinh_trang === 'SAI') L.push('Tình trạng: Chưa giao / Đang vận chuyển');
          d.cach_giao = chon(r.cach_giao, M_GIAO, d.tinh_trang === 'dang_van_chuyen' ? 'van_chuyen' : 'khach_den_lay');
          if (d.tinh_trang !== 'dang_van_chuyen' && d.gia_von) L.push('chỉ đơn đang vận chuyển mới nhập giá vốn chuyển tiếp');
          d.dang_giu = co(r.dang_giu);
          if (d.dang_giu && d.tinh_trang === 'dang_van_chuyen') L.push('đơn đang vận chuyển không giữ hàng');
          if (d.da_thu) { const q = await tra('quy', d.quy_da_thu); if (!q) L.push('đã thu thì ghi "Mã quỹ đã thu" (tiền đã nằm trong số dư quỹ đầu kỳ)'); else d.quy_da_thu_id = q.id; }
          if (k && dv && mh && kho) {
            Object.assign(d, { khach_id: k.id, don_vi_ban_id: dv.id, mat_hang_id: mh.id, kho_id: kho.id });
            if (d.tinh_trang === 'dang_van_chuyen') {
              // Đối chiếu: hàng đang vận chuyển KHÔNG được đồng thời nằm trong tồn đầu kỳ ở kho "đang vận chuyển".
              const [x] = await p.sql(`SELECT COALESCE(SUM(s.so_kg),0) AS sl FROM so_kho s JOIN kho kk ON kk.id = s.kho_id
                WHERE kk.trung_chuyen = true AND s.mat_hang_id = :m AND s.loai = 'dau_ky'`, { m: mh.id }, t);
              if (Number(x.sl) > 0) L.push(`mặt hàng đã có ${kg(x.sl)} trong tồn đầu kỳ ở kho đang vận chuyển — kiểm tra tính hai lần (bỏ khỏi tồn hoặc khỏi đơn chuyển tiếp)`);
            }
            const [x] = await p.sql(`SELECT so FROM don_ban WHERE so_don_cu = :s AND trang_thai <> 'da_huy' LIMIT 1`, { s: d.so_don_cu }, t);
            if (x) trung = `Đơn cũ ${d.so_don_cu} đã chuyển thành ${x.so}`;
            cong(`${dv.ma} · ${d.tinh_trang === 'dang_van_chuyen' ? 'đang vận chuyển' : 'chưa giao'}`, d.so_luong, tien(d.so_luong * d.don_gia));
          }
          khoa = `don|${kyMa}|${boDau(d.so_don_cu)}|${r._stt}`;
        }
      };
      await L2();
      if (khoa && !DANH_MUC.includes(lo.loai) && !['don_chuyen_tiep', 'quy_doi_dvt'].includes(lo.loai)) {
        if (daThay.has(khoa)) L.push('trùng với một dòng khác trong cùng file');
        daThay.add(khoa);
        const [x] = await p.sql(`SELECT ket_qua FROM mo_so_khoa WHERE khoa = :k`, { k: khoa }, t);
        if (x) trung = `Đã ghi trước đó (${x.ket_qua})`;
      }
      if (DANH_MUC.includes(lo.loai) || lo.loai === 'quy_doi_dvt') {
        if (daThay.has(khoa)) L.push('mã trùng trong cùng file');
        daThay.add(khoa);
      }
      kq.push({ stt: r._stt, du_lieu: d, khoa_trung: khoa, loi: [...L, ...(trung ? [trung] : [])].join('; '),
        trang_thai: L.length ? 'loi' : trung && !((DANH_MUC.includes(lo.loai) || lo.loai === 'quy_doi_dvt') && lo.che_do === 'cap_nhat' && !/không khác/.test(trung)) ? 'trung' : 'hop_le' });
    }
    // Đơn chuyển tiếp: các dòng cùng số đơn phải cùng khách / đơn vị / tình trạng.
    if (lo.loai === 'don_chuyen_tiep') {
      const g: Record<string, any> = {};
      for (const x of kq) {
        const d = x.du_lieu;
        const k = d.so_don_cu;
        g[k] = g[k] || d;
        if (g[k].khach_id !== d.khach_id || g[k].don_vi_ban_id !== d.don_vi_ban_id || g[k].tinh_trang !== d.tinh_trang) {
          x.trang_thai = 'loi'; x.loi = [x.loi, 'các dòng cùng số đơn phải cùng khách, đơn vị, tình trạng'].filter(Boolean).join('; ');
        }
      }
      const loiDon = new Set(kq.filter((x) => x.trang_thai !== 'hop_le').map((x) => x.du_lieu.so_don_cu));
      for (const x of kq) if (x.trang_thai === 'hop_le' && loiDon.has(x.du_lieu.so_don_cu)) { x.trang_thai = 'loi'; x.loi = 'dòng khác của cùng đơn bị lỗi / trùng'; }
    }
    return { kq, tong };
  };

  /** Số trong hệ thống để đối chiếu trước / sau (theo cùng nhóm với tổng của file). */
  const tongHeThong = async (t: Transaction, loai: string, nhom: string[]) => {
    const r: Record<string, any> = {};
    for (const n of nhom) {
      let x: any = null;
      if (loai === 'ton_dau_ky') [x] = await p.sql(`SELECT COALESCE(SUM(tk.so_kg),0) AS so_luong, COALESCE((SELECT SUM(g.gia_tri) FROM gia_von g WHERE g.kho_id = k.id),0) AS gia_tri
          FROM kho k LEFT JOIN ton_kho tk ON tk.kho_id = k.id WHERE k.ma = :n GROUP BY k.id`, { n }, t);
      else if (loai === 'no_khach') [x] = await p.sql(`SELECT 0 AS so_luong, COALESCE(SUM(d.con_no),0) AS gia_tri FROM don_ban d JOIN don_vi v ON v.id = d.don_vi_ban_id
          WHERE v.ma = :n AND d.loai = 'dau_ky' AND d.trang_thai <> 'da_huy'`, { n }, t);
      else if (loai === 'no_ncc') [x] = await p.sql(`SELECT 0 AS so_luong, COALESCE(SUM(n.so_tien - COALESCE(n.da_tra,0)),0) AS gia_tri FROM no_ncc_dau_ky n
          JOIN don_vi v ON v.id = n.don_vi_id WHERE v.ma = :n AND n.trang_thai = 'da_ghi'`, { n }, t);
      else if (loai === 'quy_dau_ky') [x] = await p.sql(`SELECT 0 AS so_luong, COALESCE(SUM(s.so_tien),0) AS gia_tri FROM quy q LEFT JOIN so_quy s ON s.quy_id = q.id
          WHERE q.ma = :n GROUP BY q.id`, { n }, t);
      else if (loai === 'tien_chua_pb') [x] = await p.sql(`SELECT 0 AS so_luong, COALESCE(SUM(pt.chua_phan_bo),0) AS gia_tri,
          (SELECT COALESCE(SUM(s.so_tien),0) FROM so_quy s WHERE s.quy_id = q.id) AS so_du_quy
          FROM quy q LEFT JOIN phieu_thu pt ON pt.quy_id = q.id AND pt.trang_thai = 'da_ghi' WHERE q.ma = :n GROUP BY q.id`, { n }, t);
      r[n] = x ? { so_luong: kg(x.so_luong), gia_tri: tien(x.gia_tri), ...(x.so_du_quy !== undefined ? { so_du_quy: tien(x.so_du_quy) } : {}) } : null;
    }
    return r;
  };

  /** Kiểm bảo toàn số dư (CHẶN, không chỉ cảnh báo): tiền chưa phân bổ / cọc không vượt số dư quỹ. */
  const canhBao = async (t: Transaction, loai: string, tong: Record<string, any>, truoc?: Record<string, any>) => {
    const cb: string[] = [];
    if (loai === 'tien_chua_pb') {
      const ht = truoc || (await tongHeThong(t, loai, Object.keys(tong)));
      for (const [n, v] of Object.entries<any>(tong)) {
        const h = ht[n];
        if (h && v.gia_tri + h.gia_tri > h.so_du_quy) cb.push(`Quỹ ${n}: tiền chưa phân bổ ${vnd(v.gia_tri + h.gia_tri)} đ lớn hơn số dư quỹ ${vnd(h.so_du_quy)} đ — nhập số dư quỹ trước / kiểm tra đếm đôi.`);
      }
    }
    return cb;
  };
  const tachNguoi = async (t: Transaction, ctx: any, lo: any) => {
    if (!TIEN_NO.includes(lo.loai)) return;
    const ky = lo.ky_mo_so_id ? await bang('ky_mo_so').findByPk(lo.ky_mo_so_id, { transaction: t }) : null;
    if (ky && ky.tach_nguoi_duyet !== false && lo.createdById && lo.createdById === ctx.state?.currentUser?.id)
      loi('Lô tiền / công nợ: người duyệt phải khác người nhập (cấu hình ở kỳ mở sổ).');
  };
  H['nhap_lo:duyetNgoaiLe'] = async (ctx, t) => {
    const roles: string[] = [].concat(ctx.state?.currentRoles || [], ctx.state?.currentRole || []);
    if (!roles.some((r) => ['quan_ly', 'root', 'admin'].includes(r)) || ctx.state?.aphKhongGia) loi('Chỉ quản lý duyệt ngoại lệ số dư.');
    const lo = await p.khoa('nhap_lo', id(ctx), t);
    if (!['da_kiem'].includes(lo.trang_thai)) loi('Chỉ duyệt ngoại lệ cho lô đã kiểm tra, chưa duyệt.');
    if (!val(ctx).ly_do || String(val(ctx).ly_do).length < 10) loi('Ghi rõ căn cứ ngoại lệ (≥ 10 ký tự).');
    await lo.update({ ngoai_le: val(ctx).ly_do, ngoai_le_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['nhap_lo:kiem'] = async (ctx, t) => {
    canQuyen(ctx, 'nhập số dư / danh mục hàng loạt');
    const lo = await p.khoa('nhap_lo', id(ctx), t);
    if (!['nhap', 'da_kiem', 'da_duyet'].includes(lo.trang_thai)) loi('Lô đã ghi sổ hoặc đã hủy.');
    const ky = MO_SO.includes(lo.loai) ? await kyMo(t) : null;
    const { kq, tong } = await kiemLo(ctx, t, lo, ky || { ma: '-' });
    await p.sql(`DELETE FROM nhap_dong WHERE nhap_lo_id = :l`, { l: lo.id }, t);
    for (const x of kq) {
      await bang('nhap_dong').create({ nhap_lo_id: lo.id, stt: x.stt, du_lieu: JSON.stringify(x.du_lieu), khoa_trung: x.khoa_trung,
        trang_thai: x.trang_thai, loi: x.loi }, { transaction: t, hooks: false });
    }
    const dem = (s: string) => kq.filter((x) => x.trang_thai === s).length;
    const tong_kiem = { file: tong, truoc: MO_SO.includes(lo.loai) ? await tongHeThong(t, lo.loai, Object.keys(tong)) : {} };
    (tong_kiem as any).canh_bao = await canhBao(t, lo.loai, tong, tong_kiem.truoc);
    await lo.update({ trang_thai: 'da_kiem', so_dong: kq.length, so_hop_le: dem('hop_le'), so_loi: dem('loi'), so_trung: dem('trung'),
      ky_mo_so_id: ky?.id || null, tong_kiem: JSON.stringify(tong_kiem),
      checksum: lo.tep_goc ? lo.checksum : crypto.createHash('sha256').update(String(lo.du_lieu_goc || '')).digest('hex'),
      thoi_diem_lay: lo.thoi_diem_lay || new Date().toISOString(), nguoi_nhap: lo.nguoi_nhap || p.nguoi(ctx), nguoi_duyet: null, ngoai_le: null, ngoai_le_boi: null },
    { transaction: t, hooks: false });
    return { ok: true, so_dong: kq.length, hop_le: dem('hop_le'), loi: dem('loi'), trung: dem('trung'), tong_kiem };
  };
  /** Tải tệp gốc (.xlsx / .csv / .tsv): lưu tệp, SHA-256, thời điểm lấy; đọc trang tính thành bảng để kiểm tra. Ghi sổ vẫn qua Kiểm tra → Duyệt. */
  H['nhap_lo:taiTep'] = async (ctx, t) => {
    canQuyen(ctx, 'nhập dữ liệu');
    const lo = await p.khoa('nhap_lo', id(ctx), t);
    if (!['nhap', 'da_kiem'].includes(lo.trang_thai)) loi('Lô đã duyệt / đã ghi: không đổi tệp.');
    const v = val(ctx);
    if (!v.base64 || !v.ten_tep) loi('Thiếu tệp.');
    const buf = Buffer.from(String(v.base64), 'base64');
    if (buf.length > 8 * 1024 * 1024) loi('Tệp lớn hơn 8 MB: tách thành nhiều lô.');
    const checksum = crypto.createHash('sha256').update(buf).digest('hex');
    let text = '';
    let sheets: string[] = [];
    let sheet = '';
    if (/\.(xlsx|xls)$/i.test(v.ten_tep)) {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const XLSX = require('xlsx');
      const wb = XLSX.read(buf, { type: 'buffer', cellDates: true });
      sheets = wb.SheetNames;
      sheet = v.trang_tinh && sheets.includes(v.trang_tinh) ? v.trang_tinh : sheets[0];
      text = XLSX.utils.sheet_to_csv(wb.Sheets[sheet], { FS: '\t', RS: '\n', blankrows: false, dateNF: 'dd/mm/yyyy', rawNumbers: true });
    } else text = buf.toString('utf8');
    await lo.update({ du_lieu_goc: text, tep_goc: buf.toString('base64'), ten_tep: v.ten_tep, checksum, thoi_diem_lay: new Date().toISOString(),
      trang_tinh: sheet || null, nguon: lo.nguon || v.ten_tep + (sheet ? ` / ${sheet}` : ''), ma_nguon: v.ma_nguon || lo.ma_nguon || null, trang_thai: 'nhap' },
    { transaction: t, hooks: false });
    return { ok: true, checksum, trang_tinh: sheets, dang_doc: sheet, so_dong: text.split('\n').filter((x) => x.trim()).length - 1 };
  };
  H['nhap_lo:duyet'] = async (ctx, t) => {
    canQuyen(ctx, 'duyệt lô nhập');
    const lo = await p.khoa('nhap_lo', id(ctx), t);
    if (lo.trang_thai !== 'da_kiem') loi('Bấm "Kiểm tra" trước khi duyệt (hoặc lô đã duyệt / đã ghi).');
    if (Number(lo.so_loi) > 0) loi(`Còn ${lo.so_loi} dòng lỗi: sửa dữ liệu, dán lại và kiểm tra lại.`);
    if (!Number(lo.so_hop_le)) loi('Không có dòng hợp lệ để ghi.');
    const cb = JSON.parse(lo.tong_kiem || '{}').canh_bao || [];
    if (cb.length && !lo.ngoai_le) loi(`Số dư không cân: ${cb.join(' ')} Sửa dữ liệu, hoặc quản lý duyệt ngoại lệ có căn cứ.`);
    await tachNguoi(t, ctx, lo);
    await lo.update({ trang_thai: 'da_duyet', nguoi_duyet: p.nguoi(ctx) }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['nhap_lo:huy'] = async (ctx, t) => {
    canQuyen(ctx, 'hủy lô nhập');
    const lo = await p.khoa('nhap_lo', id(ctx), t);
    if (lo.trang_thai === 'da_ghi') loi('Lô đã ghi sổ: không hủy lô. Sai thì hủy / điều chỉnh từng chứng từ đã tạo (giữ lịch sử).');
    await lo.update({ trang_thai: 'da_huy' }, { transaction: t, hooks: false });
    return { ok: true };
  };

  H['nhap_lo:ghi'] = async (ctx, t) => {
    canQuyen(ctx, 'ghi sổ lô nhập');
    const lo = await p.khoa('nhap_lo', id(ctx), t);
    if (lo.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true };
    if (lo.trang_thai !== 'da_duyet') loi('Lô phải được duyệt trước khi ghi sổ.');
    const ky = MO_SO.includes(lo.loai) ? await kyMo(t) : null;
    if (ky && lo.ky_mo_so_id && ky.id !== lo.ky_mo_so_id) loi('Kỳ mở sổ đã đổi từ lúc kiểm tra: kiểm tra lại.');
    // Kiểm lại ngay trong giao dịch ghi (có thể có người ghi trùng giữa lúc kiểm và lúc ghi).
    const { kq, tong: tongGhi } = await kiemLo(ctx, t, lo, ky || { ma: '-' });
    if (kq.some((x) => x.trang_thai === 'loi')) loi('Dữ liệu có lỗi mới phát sinh từ lúc kiểm tra: bấm Kiểm tra lại.');
    const cbGhi = await canhBao(t, lo.loai, tongGhi);
    if (cbGhi.length && !lo.ngoai_le) loi(`Số dư không cân (kiểm lại lúc ghi): ${cbGhi.join(' ')}`);
    await tachNguoi(t, ctx, lo);
    const dong = await bang('nhap_dong').findAll({ where: { nhap_lo_id: lo.id }, transaction: t, order: [['stt', 'ASC']] });
    const theoStt = new Map(dong.map((x: any) => [x.stt, x]));
    const ghiDong = async (x: any, trang_thai: string, ket_qua = '') => {
      const d = theoStt.get(x.stt) as any;
      if (d) await d.update({ trang_thai, ket_qua, loi: x.loi }, { transaction: t, hooks: false });
    };
    const ngay = ky?.ngay_chot || homNay();
    const nguon = `${lo.so}${lo.nguon ? ' · ' + lo.nguon : ''}`;
    let so = 0;
    const hopLe = kq.filter((x) => x.trang_thai === 'hop_le');
    for (const x of kq.filter((x) => x.trang_thai !== 'hop_le')) await ghiDong(x, 'bo_qua');

    if (lo.loai === 'quy_doi_dvt') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        if (d._co_id) await bang('quy_doi_dvt').update({ he_so: d.he_so, mac_dinh: d.mac_dinh }, { where: { id: d._co_id }, transaction: t });
        else await bang('quy_doi_dvt').create({ mat_hang_id: d.mat_hang_id, dvt: d.dvt, he_so: d.he_so, mac_dinh: d.mac_dinh }, { transaction: t });
        await ghiDong(x, 'da_ghi', `${d.dvt} = ${d.he_so}`); so++;
      }
    } else if (lo.loai === 'do_dang_dau_ky') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        const me = await bang('me_sx').create({ kho_id: d.kho_id, xuong: d.xuong, san_pham_du_kien: d.san_pham || `Dở dang đầu kỳ ${d.ma}`,
          ghi_chu: [`Dở dang đầu kỳ ${ky.ma} (${d.ma})`, d.ghi_chu, nguon].filter(Boolean).join(' — ') }, { transaction: t });
        await me.update({ kg_do_dang_dau: kg(d.kg) }, { transaction: t, hooks: false });
        await bang('me_sx_chi_phi').create({ me_sx_id: me.id, loai: 'do_dang_dau_ky', so_tien: tien(d.gia_tri), ky: ky.ma, so_chung_tu: `WIP ${d.ma}`,
          ghi_chu: `Dở dang đầu kỳ ${kg(d.kg)} kg — ${nguon}`, nguoi_ghi: p.nguoi(ctx) }, { transaction: t, choPhepWip: true } as any);
        await giuKhoa(t, x.khoa_trung, lo.id, me.so);
        await ghiDong(x, 'da_ghi', me.so); so++;
      }
    } else if (DANH_MUC.includes(lo.loai)) {
      for (const x of hopLe) {
        const d = { ...x.du_lieu };
        const coId = d._co_id;
        for (const k of Object.keys(d)) if (k.startsWith('_') || d[k] === '' || d[k] === null) delete d[k];
        if (coId) {
          await bang(lo.loai).update(d, { where: { id: coId }, transaction: t, individualHooks: true, choPhep: true } as any);
          await ghiDong(x, 'da_ghi', `cập nhật ${d.ma}`);
        } else {
          await bang(lo.loai).create(d, { transaction: t });
          await ghiDong(x, 'da_ghi', `thêm ${d.ma}`);
        }
        so++;
      }
    } else if (lo.loai === 'ton_dau_ky') {
      const theoKho: Record<string, any[]> = {};
      for (const x of hopLe) (theoKho[x.du_lieu.kho_id] = theoKho[x.du_lieu.kho_id] || []).push(x);
      for (const [kho_id, ds] of Object.entries(theoKho)) {
        const pk = await bang('phieu_kho').create({ loai: 'dau_ky', kho_id, ngay, nhap_lo_id: lo.id, ghi_chu: `Tồn đầu kỳ ${ky.ma} — ${nguon}` }, { transaction: t });
        for (const x of ds) {
          const d = x.du_lieu;
          await bang('phieu_kho_dong').create({ phieu_kho_id: pk.id, mat_hang_id: d.mat_hang_id, so_kg: d.so_luong, so_bao: d.so_bao || 0,
            don_gia: d.tinh_trang_gia === 'cho_gia' ? null : Math.round((d.gia_tri / d.so_luong) * 10000) / 10000,
            trang_thai_gia: d.tinh_trang_gia === 'tam' ? 'tam' : null, tinh_trang_hang: d.tinh_trang_hang, ghi_chu: d.ghi_chu || `dòng ${x.stt}` }, { transaction: t });
        }
        await goi('phieu_kho:ghiSo', ctx, t, pk.id);
        // Giá trị đúng theo file (đơn giá làm tròn có thể lệch vài đồng): chỉnh phần lệch bằng một dòng giá trị.
        for (const x of ds) {
          const d = x.du_lieu;
          if (d.tinh_trang_gia === 'cho_gia') continue;
          const [g] = await p.sql(`SELECT COALESCE(SUM(gia_tri),0) AS v FROM so_gia_von WHERE chung_tu = :c AND mat_hang_id = :m AND kho_id = :k`,
            { c: pk.so, m: d.mat_hang_id, k: kho_id }, t);
          const lech = tien(d.gia_tri) - tien(g.v);
          if (lech) await p.capNhatGia(t, { ngay, mat_hang_id: d.mat_hang_id, kho_id, so_luong: 0, gia_tri: lech, loai: 'dau_ky_lam_tron', chung_tu: pk.so });
          await ghiDong(x, 'da_ghi', pk.so);
          so++;
        }
        for (const x of ds) if (x.du_lieu.tinh_trang_gia === 'cho_gia') { await ghiDong(x, 'da_ghi', pk.so + ' (chờ định giá)'); so++; }
      }
    } else if (lo.loai === 'no_khach') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        const don = await bang('don_ban').create({ loai: 'dau_ky', khach_id: d.ben_id, don_vi_ban_id: d.don_vi_id, tong_tien: d.so_tien,
          ngay: d.ngay_ct || ngay, ngay_giao: d.ngay_ct || ngay, han_tt: d.han_tt, chung_tu_goc: d.chung_tu_goc, doi_chieu: d.doi_chieu,
          nhap_lo_id: lo.id, ghi_chu: [`Nợ đầu kỳ ${ky.ma}`, d.ghi_chu, nguon].filter(Boolean).join(' — ') }, { transaction: t, choPhep: true } as any);
        await giuKhoa(t, x.khoa_trung, lo.id, don.so);
        await ghiDong(x, 'da_ghi', don.so); so++;
      }
    } else if (lo.loai === 'no_ncc') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        const n = await bang('no_ncc_dau_ky').create({ nha_cung_cap_id: d.ben_id, don_vi_id: d.don_vi_id, so_tien: tien(d.so_tien), da_tra: 0,
          chung_tu_goc: d.chung_tu_goc, ngay_ct: d.ngay_ct || ngay, han_tt: d.han_tt, doi_chieu: d.doi_chieu, trang_thai: 'da_ghi', nhap_lo_id: lo.id,
          ghi_chu: [d.ghi_chu, nguon].filter(Boolean).join(' — ') }, { transaction: t, choPhep: true } as any);
        await giuKhoa(t, x.khoa_trung, lo.id, n.so);
        await ghiDong(x, 'da_ghi', n.so); so++;
      }
    } else if (lo.loai === 'quy_dau_ky') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        const ct = `${lo.so}-${x.stt}`;
        await giuKhoa(t, x.khoa_trung, lo.id, ct);
        if (tien(d.so_tien)) await p.ghiQuy(t, { ngay, quy_id: d.quy_id, so_tien: tien(d.so_tien), loai: 'dau_ky', chung_tu: ct,
          dien_giai: [`Số dư đầu kỳ ${ky.ma}`, d.ghi_chu].filter(Boolean).join(' — ') });
        await ghiDong(x, 'da_ghi', ct); so++;
      }
    } else if (lo.loai === 'tien_chua_pb') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        const pt = await bang('phieu_thu').create({ dau_ky: true, loai_thu: d.loai_thu, khach_id: d.khach_id || null, don_vi_id: d.don_vi_id,
          quy_id: d.quy_id, hinh_thuc: d.hinh_thuc, so_tien: tien(d.so_tien), ma_gd: d.ma_tham_chieu, ma_tham_chieu: d.ma_tham_chieu,
          muc_dich_coc: d.muc_dich_coc, ngay: d.ngay || ngay, nhap_lo_id: lo.id, ghi_chu: [`Đầu kỳ ${ky.ma}`, d.ghi_chu, nguon].filter(Boolean).join(' — ') },
        { transaction: t, choPhep: true } as any);
        // Tiền đã nằm trong số dư quỹ đầu kỳ: KHÔNG ghi sổ quỹ lần nữa, chỉ ghi khoản chưa phân bổ.
        await pt.update({ trang_thai: 'da_ghi', chua_phan_bo: tien(d.so_tien), ghi_boi: p.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
        await giuKhoa(t, x.khoa_trung, lo.id, pt.so);
        await ghiDong(x, 'da_ghi', pt.so); so++;
      }
    } else if (lo.loai === 'thu_ho_dau_ky') {
      for (const x of hopLe) {
        const d = x.du_lieu;
        const th = await bang('thu_ho').create({ dau_ky: true, don_vi_nhan_id: d.don_vi_nhan_id, don_vi_chu_no_id: d.don_vi_chu_no_id, so_tien: tien(d.so_tien),
          trang_thai: 'dang_giu_ho', ma_tham_chieu: d.ma_tham_chieu, nguoi_phan_bo: p.nguoi(ctx),
          ghi_chu: [`Đầu kỳ ${ky.ma}`, d.ghi_chu, nguon].filter(Boolean).join(' — ') }, { transaction: t, choPhep: true } as any);
        await giuKhoa(t, x.khoa_trung, lo.id, `thu_ho#${th.id}`);
        await ghiDong(x, 'da_ghi', `thu_ho#${th.id}`); so++;
      }
    } else if (lo.loai === 'don_chuyen_tiep') {
      const g: Record<string, any[]> = {};
      for (const x of hopLe) (g[x.du_lieu.so_don_cu] = g[x.du_lieu.so_don_cu] || []).push(x);
      for (const [soCu, ds] of Object.entries(g)) {
        const d0 = ds[0].du_lieu;
        await giuKhoa(t, `don|${ky.ma}|${boDau(soCu)}`, lo.id, soCu);
        const don = await bang('don_ban').create({ loai: 'ban', khach_id: d0.khach_id, don_vi_ban_id: d0.don_vi_ban_id, ngay: d0.ngay || ngay,
          cach_giao: d0.cach_giao, nguoi_nhan: d0.nguoi_nhan, so_don_cu: soCu, nhap_lo_id: lo.id,
          ghi_chu: [`Chuyển tiếp từ đơn ${soCu}`, d0.ghi_chu, nguon].filter(Boolean).join(' — ') }, { transaction: t });
        const dongDon: any[] = [];
        for (const x of ds) {
          const d = x.du_lieu;
          dongDon.push(await bang('don_ban_dong').create({ don_ban_id: don.id, mat_hang_id: d.mat_hang_id, kho_id: d.kho_id, so_kg: d.so_luong,
            don_gia: d.don_gia }, { transaction: t }));
        }
        // Đơn đã được chốt ở hệ thống cũ: vào thẳng trạng thái đã chốt (không qua duyệt lại).
        await don.update({ trang_thai: 'cho_xuat', duyet_boi: `Chuyển tiếp ${lo.so}` }, { transaction: t, choPhep: true } as any);
        if (d0.tinh_trang === 'dang_van_chuyen') {
          // Hàng đã rời kho trước mốc chốt (không nằm trong tồn đầu kỳ): lượt "đã bàn giao xe", KHÔNG trừ kho lần nữa.
          let gia_tri = 0;
          const lg = await bang('luot_giao').create({ don_ban_id: don.id, ngay, cach_giao: 'van_chuyen', nguoi_nhan: d0.nguoi_nhan || '',
            trang_thai: 'da_ban_giao_xe', xuat_boi: `Chuyển tiếp ${lo.so} (xuất trước Go-Live)` }, { transaction: t, choPhep: true } as any);
          for (const dd of dongDon) {
            const tt = tien(kg(dd.so_kg) * Number(dd.don_gia || 0));
            gia_tri += tt;
            await bang('luot_giao_dong').create({ luot_giao_id: lg.id, don_ban_dong_id: dd.id, mat_hang_id: dd.mat_hang_id, kho_id: dd.kho_id,
              so_kg: kg(dd.so_kg), don_gia: dd.don_gia, thanh_tien: tt, gia_von: 0 }, { transaction: t, choPhep: true } as any);
            await dd.update({ da_giao: kg(dd.so_kg) }, { transaction: t, hooks: false });
          }
          // Giá vốn chuyển tiếp: có căn cứ thì ghi; không có thì "chưa xác định" — lượt bị loại khỏi lãi gộp cho tới khi kế toán nhập.
          const coGv = ds.every((x) => x.du_lieu.gia_von !== null && x.du_lieu.gia_von !== undefined && Number(x.du_lieu.gia_von) > 0);
          const gvTong = coGv ? tien(ds.reduce((a, x) => a + Number(x.du_lieu.gia_von), 0)) : 0;
          if (coGv) {
            const lds = await bang('luot_giao_dong').findAll({ where: { luot_giao_id: lg.id }, transaction: t, order: [['id', 'ASC']] });
            for (let i = 0; i < lds.length; i++) {
              const gv = tien(ds[i].du_lieu.gia_von);
              await lds[i].update({ gia_von: gv }, { transaction: t, hooks: false });
              await dongDon[i].update({ gia_von_da_giao: gv }, { transaction: t, hooks: false });
            }
          }
          await lg.update({ gia_tri, gia_von: gvTong, tt_gia_von: coGv ? 'co' : 'chua_xac_dinh' }, { transaction: t, choPhep: true } as any);
        } else if (d0.dang_giu) {
          // Đơn chưa giao mà hàng đang được giữ: tạo lượt chờ xuất (giữ hàng trong tồn đầu kỳ).
          await goi('luot_giao:taoLuot', ctx, t, null, { don_ban_id: don.id, cach_giao: d0.cach_giao, nguoi_nhan: d0.nguoi_nhan,
            dong: dongDon.map((dd: any) => ({ don_ban_dong_id: dd.id, so_kg: kg(dd.so_kg) })) });
        }
        const m = await p.khoa('don_ban', don.id, t);
        await p.tinhCongNo(t, m);
        await p.capNhatTrangThaiDon(t, m);
        const daThu = tien(ds.reduce((a, x) => a + Number(x.du_lieu.da_thu || 0), 0));
        if (daThu > 0) {
          // Khách đã trả một phần trước Go-Live: tiền đã nằm trong số dư quỹ → phiếu thu đầu kỳ (không ghi sổ quỹ lần nữa), phân bổ vào đơn.
          if (d0.tinh_trang !== 'dang_van_chuyen') loi(`Đơn ${soCu}: "Đã thu" chỉ cho đơn đang vận chuyển (đã ghi nợ); đơn chưa giao thì ghi tiền ở "Tiền cọc / chưa phân bổ".`);
          if (daThu > tien(m.con_no)) loi(`Đơn ${soCu}: đã thu ${vnd(daThu)} lớn hơn giá trị ${vnd(m.con_no)}.`);
          const q = await bang('quy').findByPk(d0.quy_da_thu_id, { transaction: t });
          if (q.don_vi_id !== d0.don_vi_ban_id) loi(`Đơn ${soCu}: quỹ đã thu phải thuộc đơn vị bán.`);
          const pt = await bang('phieu_thu').create({ dau_ky: true, loai_thu: 'thu_no', khach_id: d0.khach_id, don_vi_id: d0.don_vi_ban_id, quy_id: q.id,
            hinh_thuc: q.loai === 'tien_mat' ? 'tien_mat' : 'chuyen_khoan', so_tien: daThu, ma_gd: `${soCu}-DA-THU`, ma_tham_chieu: `${soCu}-DA-THU`, ngay,
            nhap_lo_id: lo.id, ghi_chu: `Khách đã trả trước Go-Live cho đơn ${soCu}` }, { transaction: t, choPhep: true } as any);
          await pt.update({ trang_thai: 'da_ghi', chua_phan_bo: daThu, ghi_boi: p.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
          await bang('phieu_thu_phan_bo').create({ phieu_thu_id: pt.id, don_ban_id: m.id, so_tien: daThu, phan_bo_boi: p.nguoi(ctx), ngay_phan_bo: ngay },
            { transaction: t, choPhep: true } as any);
          await pt.update({ chua_phan_bo: 0 }, { transaction: t, choPhep: true } as any);
          await p.tinhCongNo(t, m);
        }
        for (const x of ds) { await ghiDong(x, 'da_ghi', don.so); so++; }
      }
    }
    const tk = JSON.parse(lo.tong_kiem || '{}');
    if (MO_SO.includes(lo.loai)) tk.sau = await tongHeThong(t, lo.loai, Object.keys(tk.file || {}));
    await lo.update({ trang_thai: 'da_ghi', ghi_boi: p.nguoi(ctx), tong_kiem: JSON.stringify(tk) }, { transaction: t, hooks: false });
    return { ok: true, da_ghi: so, tong_kiem: tk };
  };

  H['no_ncc_dau_ky:huy'] = async (ctx, t) => {
    canQuyen(ctx, 'hủy nợ NCC đầu kỳ');
    const n = await p.khoa('no_ncc_dau_ky', id(ctx), t);
    if (n.trang_thai === 'da_huy') return { ok: true };
    if (tien(n.da_tra) > 0) loi('Khoản nợ đã có phiếu chi trả: hủy phiếu chi trước.');
    if (!lyDo(ctx)) loi('Hủy cần lý do.');
    await n.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) }, { transaction: t, hooks: false });
    await boKhoa(t, n.so);
    return { ok: true };
  };

  // ---------------- TÀI SẢN ----------------
  const tongGiu = async (t: Transaction, tsId: any) => {
    const [g] = await p.sql(`SELECT COALESCE(SUM(so_luong),0) AS sl FROM tai_san_giu WHERE tai_san_id = :t`, { t: tsId }, t);
    return Number(g.sl);
  };
  const doiGiu = async (t: Transaction, tsId: any, nguoi: string, sl: number) => {
    const g = await bang('tai_san_giu').findOne({ where: { tai_san_id: tsId, nguoi_giu: nguoi }, transaction: t, lock: t.LOCK.UPDATE });
    if (g) await g.update({ so_luong: Number(g.so_luong) + sl }, { transaction: t, hooks: false });
    else await bang('tai_san_giu').create({ tai_san_id: tsId, nguoi_giu: nguoi, so_luong: sl }, { transaction: t, hooks: false });
  };
  H['tai_san_su_kien:ghi'] = async (ctx, t) => {
    const e = await p.khoa('tai_san_su_kien', id(ctx), t);
    if (e.trang_thai === 'da_ghi') return { ok: true, da_ghi_truoc: true };
    if (e.trang_thai !== 'nhap') loi('Sự kiện đã hủy.');
    const ts = await p.khoa('tai_san', e.tai_san_id, t);
    if (['da_thanh_ly', 'mat'].includes(ts.tinh_trang) && e.loai !== 'thu_hoi') loi('Tài sản đã thanh lý / báo mất.');
    const v: any = {};
    switch (e.loai) {
      case 'ban_giao': if (!e.nguoi_nhan) loi('Ghi người nhận.'); v.nguoi_quan_ly = e.nguoi_nhan; v.tinh_trang = 'dang_dung'; if (e.dia_diem_moi) v.dia_diem = e.dia_diem_moi; break;
      case 'dieu_chuyen': if (!e.dia_diem_moi) loi('Ghi địa điểm mới.'); v.dia_diem = e.dia_diem_moi; if (e.nguoi_nhan) v.nguoi_quan_ly = e.nguoi_nhan; break;
      case 'cap_phat': {
        if (!e.nguoi_nhan) loi('Ghi người / tổ nhận.');
        const sl = Number(e.so_luong || 0);
        if (ts.loai === 'ccdc' && Number(ts.so_luong || 0) + (await tongGiu(t, ts.id)) > 0) {
          // CCDC theo số lượng: kho → người giữ; tổng (kho + đang giữ) không đổi.
          if (!(sl > 0)) loi('Ghi số lượng cấp phát.');
          if (sl > Number(ts.so_luong || 0)) loi(`Trong kho chỉ còn ${ts.so_luong}.`);
          v.so_luong = Number(ts.so_luong) - sl;
          await doiGiu(t, ts.id, e.nguoi_nhan, sl);
        } else { v.nguoi_quan_ly = e.nguoi_nhan; v.tinh_trang = 'dang_dung'; }
        break;
      }
      case 'thu_hoi': {
        const sl = Number(e.so_luong || 0);
        if (ts.loai === 'ccdc' && Number(ts.so_luong || 0) + (await tongGiu(t, ts.id)) > 0) {
          if (!e.nguoi_tra) loi('Ghi người / tổ trả lại.');
          if (!(sl > 0)) loi('Ghi số lượng thu hồi.');
          const [g] = await p.sql(`SELECT COALESCE(SUM(so_luong),0) AS sl FROM tai_san_giu WHERE tai_san_id = :t AND nguoi_giu = :n`, { t: ts.id, n: e.nguoi_tra }, t);
          if (Number(g.sl) < sl) loi(`${e.nguoi_tra} chỉ đang giữ ${Number(g.sl)}, không thu hồi ${sl}.`);
          await doiGiu(t, ts.id, e.nguoi_tra, -sl);
          v.so_luong = Number(ts.so_luong || 0) + sl;
        } else { v.nguoi_quan_ly = ''; v.tinh_trang = 'trong_kho'; }
        if (e.dia_diem_moi) v.dia_diem = e.dia_diem_moi;
        break;
      }
      case 'bao_tri': case 'sua_chua': v.tinh_trang = 'dang_dung'; if (e.ngay_bao_tri_tiep) v.ngay_bao_tri = e.ngay_bao_tri_tiep; break;
      case 'bao_hong': v.tinh_trang = 'hong'; break;
      case 'de_nghi_thanh_ly': if (!e.ghi_chu) loi('Ghi lý do đề nghị thanh lý.'); v.tinh_trang = 'cho_thanh_ly'; break;
      case 'thanh_ly': canQuyen(ctx, 'duyệt thanh lý tài sản'); if (ts.tinh_trang !== 'cho_thanh_ly') loi('Phải có đề nghị thanh lý trước.'); v.tinh_trang = 'da_thanh_ly'; break;
      case 'bao_mat': if (!e.ghi_chu) loi('Ghi tình huống mất.'); v.tinh_trang = 'mat'; break;
      default: loi('Chọn nghiệp vụ.');
    }
    await ts.update(v, { transaction: t, hooks: false });
    await e.update({ trang_thai: 'da_ghi', ghi_boi: p.nguoi(ctx) }, { transaction: t, choPhep: true } as any);
    return { ok: true };
  };
  H['tai_san_su_kien:huy'] = async (ctx, t) => {
    const e = await p.khoa('tai_san_su_kien', id(ctx), t);
    if (e.trang_thai === 'da_ghi') loi('Sự kiện đã ghi: lập sự kiện mới để sửa (giữ lịch sử).');
    await e.update({ trang_thai: 'da_huy', ly_do_huy: lyDo(ctx) || '' }, { transaction: t, choPhep: true } as any);
    return { ok: true };
  };
  /** Chi phí sử dụng tài sản ƯỚC TÍNH (quản trị, cho giá thành) — không phải khấu hao kế toán, không sinh bút toán. */
  H['tai_san:uocTinh'] = async (ctx, t) => {
    canQuyen(ctx, 'xem chi phí tài sản ước tính');
    const thang = String(val(ctx).thang || homNay().slice(0, 7));
    const cuoi = `${thang}-28`;
    return p.sql(`SELECT id, ma, ten, dia_diem, nguyen_gia, so_thang_sd, ngay_mua, ngay_su_dung, bo_phan_chi_phi, dung_cho_san_xuat,
        CASE WHEN COALESCE(so_thang_sd,0) > 0 AND COALESCE(nguyen_gia,0) > 0 AND COALESCE(ngay_su_dung, ngay_mua) IS NOT NULL
             AND COALESCE(ngay_su_dung, ngay_mua) <= :cuoi::date AND (COALESCE(ngay_su_dung, ngay_mua) + (so_thang_sd || ' month')::interval) > :cuoi::date
             THEN ROUND(nguyen_gia / so_thang_sd) ELSE 0 END AS chi_phi_thang
      FROM tai_san WHERE loai = 'tscd' AND tinh_trang NOT IN ('da_thanh_ly','mat') ORDER BY dung_cho_san_xuat DESC, ma`, { cuoi }, t);
  };

  // ---------------- MẺ SẢN XUẤT ----------------
  /** Tính lại toàn bộ số liệu mẻ từ các phiếu đã ghi + chi phí (không cộng dồn → hủy phiếu không làm sai). */
  const tinhLaiMe = async (t: Transaction, me: any) => {
    // 0.4.1: PHÂN LOẠI THEO VAI TRÒ DÒNG, KHÔNG THEO ĐVT.
    // Cùng Item có thể dùng theo các vai trò khác nhau; phân bổ trị giá ghi sổ theo SL từng vai trò.
    // Dòng cũ chưa có vai trò giữ cách phân loại legacy để không đổi giá trị lịch sử.
    const [a] = await p.sql(`WITH cap AS (
      SELECT k.id, k.so FROM phieu_kho k WHERE k.me_sx_id = :m AND k.loai = 'cap_nvl' AND k.trang_thai = 'da_ghi'
    ), cap_dong AS (
      SELECT k.so, d.mat_hang_id, SUM(d.so_kg) AS tong_sl,
        SUM(CASE WHEN COALESCE(d.vai_tro,
            CASE WHEN m.loai_hang = 'bao_bi' OR LOWER(COALESCE(m.dvt_ton,'kg')) <> 'kg' THEN 'bao_bi' ELSE 'nvl' END
          ) = 'nvl' THEN d.so_kg ELSE 0 END) AS sl_nvl
      FROM cap k JOIN phieu_kho_dong d ON d.phieu_kho_id = k.id
        JOIN mat_hang m ON m.id = d.mat_hang_id GROUP BY k.so, d.mat_hang_id
    )
    SELECT
      COALESCE((SELECT -SUM(g.gia_tri * x.sl_nvl / NULLIF(x.tong_sl,0))
        FROM so_gia_von g JOIN cap_dong x ON x.so = g.chung_tu AND x.mat_hang_id = g.mat_hang_id
        WHERE g.loai = 'cap_nvl'),0) AS nvl,
      COALESCE((SELECT -SUM(g.gia_tri * (x.tong_sl - x.sl_nvl) / NULLIF(x.tong_sl,0))
        FROM so_gia_von g JOIN cap_dong x ON x.so = g.chung_tu AND x.mat_hang_id = g.mat_hang_id
        WHERE g.loai = 'cap_nvl'),0) AS bb,
      COALESCE((SELECT SUM(CASE WHEN LOWER(COALESCE(m.dvt_ton,'kg')) = 'kg' THEN d.so_kg
                  WHEN m.kg_moi_dvt > 0 AND NULLIF(TRIM(m.kg_dvt_can_cu),'') IS NOT NULL THEN d.so_kg * m.kg_moi_dvt ELSE 0 END)
        FROM phieu_kho_dong d JOIN cap k ON k.id = d.phieu_kho_id JOIN mat_hang m ON m.id = d.mat_hang_id
        WHERE COALESCE(d.vai_tro, CASE WHEN m.loai_hang = 'bao_bi' OR LOWER(COALESCE(m.dvt_ton,'kg')) <> 'kg' THEN 'bao_bi' ELSE 'nvl' END) = 'nvl'),0) AS kg_nvl,
      COALESCE((SELECT SUM(CASE WHEN LOWER(COALESCE(m.dvt_ton,'kg')) = 'kg' THEN d.so_kg
                  WHEN m.kg_moi_dvt > 0 AND NULLIF(TRIM(m.kg_dvt_can_cu),'') IS NOT NULL THEN d.so_kg * m.kg_moi_dvt ELSE 0 END)
        FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id JOIN mat_hang m ON m.id = d.mat_hang_id
        WHERE k.me_sx_id = :m AND k.loai = 'thu_hoi' AND k.trang_thai = 'da_ghi' AND d.huong = 'ra'),0) AS kg_tp,
      COALESCE((SELECT SUM(d.so_kg) FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id WHERE k.me_sx_id = :m AND k.loai = 'thu_hoi'
        AND k.trang_thai = 'da_ghi' AND d.huong = 'phu_pham'),0) AS kg_pp,
      COALESCE((SELECT SUM(d.so_kg) FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id WHERE k.me_sx_id = :m AND k.loai = 'thu_hoi'
        AND k.trang_thai = 'da_ghi' AND d.huong = 'hao_hut' AND d.loai_hao = 'bat_thuong'),0) AS kg_bt,
      COALESCE((SELECT SUM(d.so_kg) FROM phieu_kho_dong d JOIN phieu_kho k ON k.id = d.phieu_kho_id WHERE k.me_sx_id = :m AND k.loai = 'thu_hoi'
        AND k.trang_thai = 'da_ghi' AND d.huong = 'hao_hut' AND COALESCE(d.loai_hao,'tu_nhien') = 'tu_nhien'),0) AS kg_tn,
      COALESCE((SELECT SUM(g.gia_tri) FROM so_gia_von g JOIN phieu_kho k ON k.so = g.chung_tu WHERE k.me_sx_id = :m AND k.trang_thai = 'da_ghi'
        AND g.loai = 'thu_hoi_phu_pham'),0) + COALESCE((SELECT SUM(a.chenh_lech) FROM dieu_chinh_gia_tri a WHERE a.nguon = :npp),0) AS pp,
      COALESCE((SELECT SUM(g.gia_tri) FROM so_gia_von g JOIN phieu_kho k ON k.so = g.chung_tu WHERE k.me_sx_id = :m AND k.trang_thai = 'da_ghi'
        AND g.loai = 'thu_hoi_ra'),0) + COALESCE((SELECT SUM(a.chenh_lech) FROM dieu_chinh_gia_tri a WHERE a.nguon = :ntp),0) AS vao_kho,
      COALESCE((SELECT SUM(so_tien) FROM me_sx_chi_phi WHERE me_sx_id = :m),0) AS cp`,
      { m: me.id, npp: `me#${me.id}:pp`, ntp: `me#${me.id}:tp` }, t);
    const v = { gia_tri_nvl: tien(a.nvl), gia_tri_bao_bi: tien(a.bb), kg_nvl: kg(a.kg_nvl), kg_tp: kg(a.kg_tp), kg_phu_pham: kg(a.kg_pp),
      kg_hao_bat_thuong: kg(a.kg_bt), kg_hao_tu_nhien: kg(a.kg_tn), gia_tri_phu_pham: tien(a.pp), da_vao_kho: tien(a.vao_kho), chi_phi: tien(a.cp) };
    await me.update(v, { transaction: t, hooks: false });
    return v;
  };
  p.tinhLaiMe = tinhLaiMe;

  /** Ghi phiếu cấp NVL / thu hồi thành phẩm của mẻ (gọi từ phieu_kho:ghiSo). */
  p.ghiPhieuMe = async (ctx: any, t: Transaction, pk: any, dong: any[]) => {
    if (!pk.me_sx_id) loi('Phiếu cấp NVL / thu hồi phải chọn mẻ sản xuất.');
    const me = await p.khoa('me_sx', pk.me_sx_id, t);
    if (me.trang_thai === 'da_huy') loi('Mẻ đã hủy.');
    if (me.trang_thai === 'da_khoa') loi('Mẻ đã khóa kỳ: không cấp / thu hồi thêm. Mở mẻ mới (gắn mẻ gốc) nếu sản xuất tiếp.');
    if (pk.kho_id !== me.kho_id) {
      // 0.4.1: được cấp từ kho nhà máy khác (vd. kho vật tư - bao bì); mẻ gia công chỉ dùng kho hàng gửi của hồ sơ.
      const k = await p.bang('kho').findByPk(pk.kho_id, { transaction: t });
      if (me.ho_so_gia_cong_id || k?.loai_kho !== 'nha_may') loi('Phiếu của mẻ phải dùng kho nhà máy (mẻ gia công: kho hàng gửi của hồ sơ).');
    }
    const c = (d: any) => ({ ngay: pk.ngay, mat_hang_id: d.mat_hang_id, chung_tu: pk.so, nguon: 'phieu_kho_dong', nguon_id: d.id });
    if (dong.some((d) => !(kg(d.so_kg) > 0))) loi('Số lượng mỗi dòng phải lớn hơn 0.');
    if (pk.loai === 'cap_nvl') {
      for (const d of dong) {
        const v = await p.ghiSo(t, { ...c(d), kho_id: pk.kho_id, so_luong: -kg(d.so_kg), so_bao: -kg(d.so_bao), loai: 'cap_nvl' });
        await d.update({ huong: 'vao', don_gia: Math.round((-v / kg(d.so_kg)) * 100) / 100 }, { transaction: t, hooks: false });
      }
    } else {
      if (dong.some((d) => !['ra', 'phu_pham', 'hao_hut'].includes(d.huong))) loi('Mỗi dòng thu hồi chọn: Thành phẩm ra / Phụ phẩm ra / Hao hụt.');
      if (dong.some((d) => d.huong === 'hao_hut' && !d.loai_hao)) loi('Dòng hao hụt phải chọn Tự nhiên / Bất thường.');
      if (dong.some((d) => d.huong === 'hao_hut' && d.loai_hao === 'bat_thuong') && !pk.ghi_chu) loi('Hao hụt bất thường: ghi nguyên nhân ở ô Ghi chú.');
      if (dong.some((d) => d.huong === 'phu_pham' && (d.don_gia === null || d.don_gia === undefined || Number(d.don_gia) < 0)))
        loi('Phụ phẩm cần đơn giá thu hồi (0 nếu chưa có — kế toán chỉnh khi chốt mẻ).');
      const s = await tinhLaiMe(t, me);
      // Giá trị TẠM khi thu hồi = chi phí đã tập hợp / kg NVL đã cấp (giả định hiệu suất 100%); chốt mẻ sẽ điều chỉnh về giá thành thực.
      const tam = s.kg_nvl > 0 ? Math.max(0, (s.gia_tri_nvl + s.gia_tri_bao_bi + s.chi_phi - s.gia_tri_phu_pham) / s.kg_nvl) : 0;
      const kho_ra = me.kho_tp_id || me.kho_id;
      for (const d of dong) {
        if (d.huong === 'hao_hut') continue;
        const gt = d.huong === 'phu_pham' ? tien(kg(d.so_kg) * Number(d.don_gia || 0)) : tien(kg(d.so_kg) * tam);
        await p.ghiSo(t, { ...c(d), kho_id: kho_ra, so_luong: kg(d.so_kg), so_bao: kg(d.so_bao), loai: d.huong === 'ra' ? 'thu_hoi_ra' : 'thu_hoi_phu_pham', gia_tri: gt });
        if (d.huong === 'ra') await d.update({ don_gia: Math.round(tam * 100) / 100, trang_thai_gia: 'tam' }, { transaction: t, hooks: false });
      }
    }
    await pk.update({ kho_dich_id: pk.loai === 'thu_hoi' ? me.kho_tp_id || me.kho_id : null }, { transaction: t, choPhep: true } as any);
    const s = await tinhLaiMe(t, me);
    if (['da_chot', 'tam_hoan_thanh'].includes(me.trang_thai)) await me.update({ trang_thai: me.trang_thai === 'da_chot' ? 'can_chot_lai' : 'mo' }, { transaction: t, hooks: false });
    return { kg_vao: s.kg_nvl, kg_ra: s.kg_tp };
  };

  H['me_sx:chot'] = async (ctx, t) => {
    canQuyen(ctx, 'chốt giá thành');
    const me = await p.khoa('me_sx', id(ctx), t);
    if (me.trang_thai === 'da_huy') loi('Mẻ đã hủy.');
    kiemKho(ctx, me.kho_id);
    const v = val(ctx);
    const ngay = homNay();
    // 1. Chỉnh giá phụ phẩm (nếu kế toán nhập lại): chỉ chỉnh giá trị, không đổi số lượng.
    for (const [dongId, gia] of Object.entries<any>(v.gia_phu_pham || {})) {
      const d = await p.khoa('phieu_kho_dong', dongId, t);
      const pk = await bang('phieu_kho').findByPk(d.phieu_kho_id, { transaction: t });
      if (!pk || pk.me_sx_id !== me.id || d.huong !== 'phu_pham' || pk.trang_thai !== 'da_ghi') loi('Dòng phụ phẩm không thuộc mẻ.');
      if (!(Number(gia) >= 0)) loi('Giá phụ phẩm không hợp lệ.');
      const delta = tien(kg(d.so_kg) * Number(gia)) - tien(kg(d.so_kg) * Number(d.don_gia || 0));
      const [sk] = await p.sql(`SELECT MIN(id) AS id FROM so_kho WHERE chung_tu = :c AND nguon_id = :n`, { c: pk.so, n: d.id }, t);
      if (delta) await dieuChinhGiaTri(p, t, { mat_hang_id: d.mat_hang_id, kho_id: pk.kho_dich_id || me.kho_tp_id || me.kho_id, so_luong_goc: kg(d.so_kg),
        chenh_lech: delta, tu_so_kho_id: Number(sk?.id || 0), chung_tu: me.so, nguon: `me#${me.id}:pp`, ly_do: `Giá phụ phẩm ${d.don_gia} → ${gia}` });
      await d.update({ don_gia: Number(gia) }, { transaction: t, hooks: false });
    }
    for (const [dongId, hs] of Object.entries<any>(v.he_so || {})) {
      const d = await p.khoa('phieu_kho_dong', dongId, t);
      const pk = await bang('phieu_kho').findByPk(d.phieu_kho_id, { transaction: t });
      // Mọi dòng gửi lên phải đúng mẻ này, phiếu thu hồi đã ghi, hướng thành phẩm ra.
      if (!pk || pk.me_sx_id !== me.id || pk.loai !== 'thu_hoi' || pk.trang_thai !== 'da_ghi' || d.huong !== 'ra') loi('Dòng hệ số không thuộc thành phẩm của mẻ này.');
      if (!(Number(hs) > 0)) loi('Hệ số phải lớn hơn 0.');
      await d.update({ he_so: Number(hs) }, { transaction: t, hooks: false });
    }
    if (v.phuong_phap) await me.update({ phuong_phap: v.phuong_phap }, { transaction: t, hooks: false });
    const do_dang = tien(v.do_dang_cuoi ?? me.do_dang_cuoi ?? 0);
    if (do_dang < 0) loi('Dở dang cuối không âm.');
    const s = await tinhLaiMe(t, me);
    if (!(s.kg_tp > 0)) loi('Mẻ chưa có thành phẩm thu hồi.');
    const tongCp = s.gia_tri_nvl + s.gia_tri_bao_bi + s.chi_phi;
    const goc = tongCp - s.gia_tri_phu_pham - do_dang;
    if (goc < 0) loi(`Phụ phẩm + dở dang (${vnd(s.gia_tri_phu_pham + do_dang)}) lớn hơn tổng chi phí (${vnd(tongCp)}).`);
    // Hao hụt bất thường không vào giá thành: tách phần chi phí tương ứng theo kg.
    const hao_bt = s.kg_hao_bat_thuong > 0 ? tien((goc * s.kg_hao_bat_thuong) / (s.kg_tp + s.kg_hao_bat_thuong)) : 0;
    const tong_pb = goc - hao_bt;
    const ra = await p.sql(`SELECT d.id, d.mat_hang_id, d.so_kg, d.he_so, k.kho_dich_id, k.so, m.gia_ban, m.ma FROM phieu_kho_dong d
      JOIN phieu_kho k ON k.id = d.phieu_kho_id JOIN mat_hang m ON m.id = d.mat_hang_id
      WHERE k.me_sx_id = :m AND k.loai = 'thu_hoi' AND k.trang_thai = 'da_ghi' AND d.huong = 'ra' ORDER BY d.id`, { m: me.id }, t);
    const pp = me.phuong_phap || 'kg';
    const w = ra.map((d: any) => {
      if (pp === 'he_so') return kg(d.so_kg) * Number(d.he_so || 1);
      if (pp === 'gia_tri') { if (!(Number(d.gia_ban) > 0)) loi(`Phân bổ theo giá trị: mặt hàng ${d.ma} chưa có giá bán.`); return kg(d.so_kg) * Number(d.gia_ban); }
      return kg(d.so_kg);
    });
    const tw = w.reduce((a: number, b: number) => a + b, 0);
    let con = tong_pb;
    const chiTiet: any[] = [];
    const muc: Record<string, number> = {};
    ra.forEach((d: any, i: number) => {
      const gt = i === ra.length - 1 ? con : tien((tong_pb * w[i]) / tw);
      con -= gt;
      const k = `${d.mat_hang_id}|${d.kho_dich_id || me.kho_tp_id || me.kho_id}`;
      muc[k] = (muc[k] || 0) + gt;
      chiTiet.push({ dong: d.id, phieu: d.so, ma: d.ma, so_kg: kg(d.so_kg), trong_so: w[i], gia_tri: gt, gia_thanh: Math.round((gt / kg(d.so_kg)) * 100) / 100 });
    });
    for (const c of chiTiet) await bang('phieu_kho_dong').update({ don_gia: c.gia_thanh, trang_thai_gia: 'co_gia' }, { where: { id: c.dong }, transaction: t, hooks: false });
    // Chênh lệch = phân bổ mới − đã ghi (giá tạm + các lần chốt trước), theo mặt hàng × kho; chia cho tồn còn / kho nhận / giá vốn kỳ.
    let dieu_chinh = 0;
    let vao_gia_von = 0;
    for (const [k, gt] of Object.entries(muc)) {
      const [mh, kho] = k.split('|');
      const [x] = await p.sql(`SELECT COALESCE((SELECT SUM(g.gia_tri) FROM so_gia_von g JOIN phieu_kho pk ON pk.so = g.chung_tu
          WHERE pk.me_sx_id = :m AND pk.trang_thai = 'da_ghi' AND g.loai = 'thu_hoi_ra' AND g.mat_hang_id = :mh AND g.kho_id = :kho),0)
        + COALESCE((SELECT SUM(a.chenh_lech) FROM dieu_chinh_gia_tri a WHERE a.nguon = :n AND a.mat_hang_id = :mh AND a.kho_id = :kho),0) AS v,
        (SELECT MIN(s.id) FROM so_kho s JOIN phieu_kho pk ON pk.so = s.chung_tu WHERE pk.me_sx_id = :m AND pk.trang_thai = 'da_ghi'
          AND s.loai = 'thu_hoi_ra' AND s.mat_hang_id = :mh AND s.kho_id = :kho) AS tu,
        (SELECT SUM(d.so_kg) FROM phieu_kho_dong d JOIN phieu_kho pk ON pk.id = d.phieu_kho_id WHERE pk.me_sx_id = :m AND pk.trang_thai = 'da_ghi'
          AND pk.loai = 'thu_hoi' AND d.huong = 'ra' AND d.mat_hang_id = :mh AND COALESCE(pk.kho_dich_id, :kho) = :kho) AS q`,
      { m: me.id, n: `me#${me.id}:tp`, mh, kho }, t);
      const delta = tien(gt) - tien(x.v);
      if (delta) {
        const r = await dieuChinhGiaTri(p, t, { mat_hang_id: mh, kho_id: kho, so_luong_goc: kg(x.q), chenh_lech: delta, tu_so_kho_id: Number(x.tu || 0),
          chung_tu: me.so, nguon: `me#${me.id}:tp`, ly_do: `Chốt giá thành ${me.so} phiên bản ${Number(me.phien_ban || 0) + 1}` });
        dieu_chinh += delta;
        vao_gia_von += Number(r?.vao_gia_von || 0);
      }
    }
    const phien = Number(me.phien_ban || 0) + 1;
    const gia_thanh = Math.round((tong_pb / s.kg_tp) * 100) / 100;
    await bang('me_sx_phien_ban').create({ me_sx_id: me.id, phien_ban: phien, ngay, tong_chi_phi: tongCp, phu_pham: s.gia_tri_phu_pham, do_dang_cuoi: do_dang,
      hao_bat_thuong: hao_bt, tong_phan_bo: tong_pb, dieu_chinh, chi_tiet: JSON.stringify({ phuong_phap: pp, dong: chiTiet }), nguoi: p.nguoi(ctx) },
    { transaction: t, hooks: false });
    if (me.trang_thai === 'da_khoa' && !v.dieu_chinh_ky_sau) loi('Mẻ đã khóa kỳ: chốt lại chỉ dưới dạng điều chỉnh kỳ sau (chọn "điều chỉnh kỳ sau").');
    await me.update({ trang_thai: me.trang_thai === 'da_khoa' ? 'da_khoa' : 'da_chot', do_dang_cuoi: do_dang, kg_do_dang: kg(v.kg_do_dang ?? me.kg_do_dang), hao_bat_thuong_gt: hao_bt,
      tong_phan_bo: tong_pb, gia_thanh, phien_ban: phien, chot_boi: p.nguoi(ctx) }, { transaction: t, hooks: false });
    await tinhLaiMe(t, me);
    return { ok: true, phien_ban: phien, tong_phan_bo: tong_pb, gia_thanh, dieu_chinh, vao_gia_von, vao_ton: dieu_chinh - vao_gia_von, hao_bat_thuong: hao_bt, chi_tiet: chiTiet };
  };
  H['me_sx:baoXong'] = async (ctx, t) => {
    const me = await p.khoa('me_sx', id(ctx), t);
    kiemKho(ctx, me.kho_id);
    if (me.trang_thai !== 'mo') loi('Chỉ mẻ đang sản xuất mới báo tạm hoàn thành.');
    await me.update({ trang_thai: 'tam_hoan_thanh' }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['me_sx:khoa'] = async (ctx, t) => {
    canQuyen(ctx, 'khóa kỳ giá thành');
    const me = await p.khoa('me_sx', id(ctx), t);
    if (me.trang_thai !== 'da_chot') loi('Chỉ khóa mẻ đã chốt (không còn chi phí / sản lượng chờ).');
    await me.update({ trang_thai: 'da_khoa' }, { transaction: t, hooks: false });
    return { ok: true };
  };
  H['me_sx:huy'] = async (ctx, t) => {
    const me = await p.khoa('me_sx', id(ctx), t);
    const [r] = await p.sql(`SELECT COUNT(*)::int AS n FROM phieu_kho WHERE me_sx_id = :m AND trang_thai = 'da_ghi'`, { m: me.id }, t);
    if (r.n) loi('Mẻ đã có phiếu cấp / thu hồi đã ghi: hủy các phiếu đó trước.');
    await me.update({ trang_thai: 'da_huy' }, { transaction: t, hooks: false });
    return { ok: true };
  };
}

/** Hook cho các bảng mới (gọi trong beforeLoad). */
export function hookMoRong(p: any) {
  const db = p.db;
  db.on('tai_san.beforeSave', (m: any) => m.set('nhan', [m.get('ma'), m.get('ten')].filter(Boolean).join(' – ')));
  db.on('tai_san_su_kien.beforeCreate', (m: any) => { if (!m.get('ngay')) m.set('ngay', homNay()); m.set('trang_thai', 'nhap'); });
  db.on('tai_san_su_kien.beforeUpdate', (m: any, o: any) => {
    if (!o?.choPhep && m.previous('trang_thai') && m.previous('trang_thai') !== 'nhap') loi('Sự kiện đã ghi: không sửa được.');
  });
  db.on('tai_san.beforeUpdate', (m: any, o: any) => {
    // Người giữ / tình trạng / địa điểm chỉ đổi qua sự kiện (giữ lịch sử bàn giao).
    if (o?.hooks === false || o?.choPhep) return;
    const doi = (m.changed() || []).filter((k: string) => ['nguoi_quan_ly', 'tinh_trang', 'dia_diem', 'so_luong'].includes(k));
    if (doi.length && m.previous('ma')) loi('Người giữ / địa điểm / tình trạng / số lượng thay đổi qua "Sự kiện tài sản" (bàn giao, điều chuyển, báo hỏng…).');
  });
  db.on('me_sx.beforeCreate', (m: any) => { if (!m.get('ngay_mo')) m.set('ngay_mo', homNay()); m.set('trang_thai', 'mo'); m.set('phien_ban', 0); });
  db.on('me_sx.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    const doi = (m.changed() || []).filter((k: string) => !['ghi_chu', 'san_pham_du_kien', 'xuong', 'phuong_phap', 'do_dang_cuoi', 'kg_do_dang', 'updatedAt', 'updatedById'].includes(k));
    if (doi.length) loi('Số liệu mẻ do hệ thống tính từ phiếu và chi phí: không sửa tay.');
  });
  const capNhatMe = async (m: any, o: any) => {
    const t = o?.transaction;
    const me = await p.bang('me_sx').findByPk(m.get('me_sx_id'), { transaction: t });
    if (!me) return;
    if (me.trang_thai === 'da_huy') loi('Mẻ đã hủy.');
    await p.tinhLaiMe(t, me);
    if (['da_chot', 'da_khoa'].includes(me.trang_thai)) await me.update({ trang_thai: 'can_chot_lai' }, { transaction: t, hooks: false });
  };
  db.on('me_sx_chi_phi.beforeSave', async (m: any, o: any) => {
    const t = o?.transaction;
    // Chống tính hai lần: cùng phiếu chi không phân bổ quá số tiền phiếu; cùng số chứng từ + khoản không ghi hai lần.
    if (m.get('phieu_chi_id')) {
      const pc = await p.bang('phieu_chi').findByPk(m.get('phieu_chi_id'), { transaction: t });
      if (!pc || pc.trang_thai !== 'da_ghi') loi('Phiếu chi chưa ghi hoặc đã hủy.');
      const [x] = await p.sql(`SELECT COALESCE(SUM(so_tien),0) AS v FROM me_sx_chi_phi WHERE phieu_chi_id = :p AND id <> :i`, { p: pc.id, i: m.get('id') || 0 }, t);
      if (Number(x.v) + Number(m.get('so_tien') || 0) > Number(pc.so_tien)) loi(`Phiếu chi ${pc.so} chỉ có ${vnd(pc.so_tien)} đ, đã phân bổ vào mẻ ${vnd(x.v)} đ.`);
    }
    if (m.get('so_chung_tu')) {
      const [x] = await p.sql(`SELECT c.id, me.so FROM me_sx_chi_phi c JOIN me_sx me ON me.id = c.me_sx_id WHERE c.so_chung_tu = :s AND c.loai = :l
        AND c.me_sx_id = :me AND c.id <> :i LIMIT 1`, { s: m.get('so_chung_tu'), l: m.get('loai'), me: m.get('me_sx_id'), i: m.get('id') || 0 }, t);
      if (x) loi(`Chứng từ ${m.get('so_chung_tu')} (${m.get('loai')}) đã ghi vào mẻ ${x.so}.`);
    }
    if (!m.get('ngay')) m.set('ngay', homNay());
    if (!(Number(m.get('so_tien')) > 0) && m.get('loai') !== 'do_dang_dau_ky') loi('Số tiền chi phí phải lớn hơn 0.');
    if (!m.get('loai')) loi('Chọn khoản chi phí.');
    return o;
  });
  for (const sk of ['afterSave', 'afterDestroy']) db.on(`me_sx_chi_phi.${sk}`, capNhatMe);
  for (const b of ['me_sx_phien_ban', 'mo_so_khoa', 'nhap_dong', 'tai_san_giu', 'dieu_chinh_gia_tri']) {
    for (const sk of ['beforeCreate', 'beforeUpdate', 'beforeDestroy']) db.on(`${b}.${sk}`, (_m: any, o: any) => { if (o?.hooks !== false) loi('Chỉ thay đổi qua thao tác nghiệp vụ.'); });
  }
  db.on('nhap_lo.beforeCreate', (m: any) => { m.set('trang_thai', 'nhap'); });
  db.on('nhap_lo.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    const tr = m.previous('trang_thai');
    if (tr && !['nhap', 'da_kiem'].includes(tr)) loi('Lô đã duyệt / đã ghi: không sửa được dữ liệu.');
    if ((m.changed() || []).some((k: string) => ['du_lieu_goc', 'loai', 'che_do'].includes(k))) m.set('trang_thai', 'nhap');
  });
  db.on('nhap_lo.beforeDestroy', (m: any) => { if (m.get('trang_thai') === 'da_ghi') loi('Lô đã ghi sổ không xóa được.'); });
  db.on('no_ncc_dau_ky.beforeCreate', (_m: any, o: any) => { if (!o?.choPhep) loi('Nợ NCC đầu kỳ nhập qua Go-Live (lô nhập có kiểm tra, duyệt).'); });
  db.on('no_ncc_dau_ky.beforeUpdate', (m: any, o: any) => {
    if (o?.choPhep || o?.hooks === false) return;
    if ((m.changed() || []).some((k: string) => !['ghi_chu', 'doi_chieu', 'han_tt', 'updatedAt', 'updatedById'].includes(k))) loi('Chỉ sửa ghi chú / đối chiếu / hạn; số tiền sai thì hủy và nhập lại.');
  });
  db.on('ky_mo_so.beforeUpdate', (m: any, o: any) => {
    if (o?.hooks === false) return;
    if (m.previous('trang_thai') === 'da_khoa') loi('Kỳ mở sổ đã khóa.');
    if (m.changed('trang_thai')) loi('Khóa kỳ bằng nút "Khóa kỳ".');
  });
  db.on('ky_mo_so.beforeCreate', async (m: any, o: any) => {
    const co = await p.bang('ky_mo_so').findOne({ where: { trang_thai: 'mo' }, transaction: o?.transaction });
    if (co) loi(`Kỳ ${co.ma} đang mở: khóa kỳ đó trước khi mở kỳ mới.`);
    m.set('trang_thai', 'mo');
  });
}
