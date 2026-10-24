/** Đọc tệp nguồn (xlsx / csv / văn bản "## Sheet name:") thành các trang tính dạng mảng dòng. */
import crypto from 'crypto';
import { docCsv } from '../toan_ven';
import { loi } from '../tienich';

export type TrangTinh = { ten: string; dong: string[][] };

export function docTep(v: { base64?: string; ten_tep?: string; van_ban?: string }, gioiHanMb = 25) {
  let buf: Buffer;
  if (v.base64) buf = Buffer.from(String(v.base64), 'base64');
  else if (v.van_ban) buf = Buffer.from(String(v.van_ban), 'utf8');
  else return loi('Thiếu tệp.');
  if (buf.length > gioiHanMb * 1024 * 1024) loi(`Tệp lớn hơn ${gioiHanMb} MB.`);
  const checksum = crypto.createHash('sha256').update(buf).digest('hex');
  const ten = v.ten_tep || 'tep';
  const trang: TrangTinh[] = [];
  if (/\.(xlsx|xls|xlsm)$/i.test(ten)) {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const XLSX = require('xlsx');
    const wb = XLSX.read(buf, { type: 'buffer', cellDates: true });
    for (const s of wb.SheetNames) {
      const dong: any[][] = XLSX.utils.sheet_to_json(wb.Sheets[s], { header: 1, raw: false, dateNF: 'dd/mm/yyyy', defval: '', blankrows: false });
      trang.push({ ten: s, dong: dong.map((r) => r.map((x) => String(x ?? '').trim())) });
    }
  } else {
    const text = buf.toString('utf8');
    if (/^## Sheet name:/m.test(text)) {
      const phan = text.split(/^## Sheet name:\s*/m).slice(1);
      for (const p of phan) {
        const nl = p.indexOf('\n');
        trang.push({ ten: p.slice(0, nl).trim(), dong: docCsv(p.slice(nl + 1), ',').map((r) => r.map((x) => String(x ?? '').trim())) });
      }
    } else trang.push({ ten: ten, dong: docCsv(text).map((r) => r.map((x) => String(x ?? '').trim())) });
  }
  return { checksum, trang, kich_thuoc: buf.length };
}

export const boDau = (s: any) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().replace(/\s+/g, ' ').trim();

/** Số kiểu Việt Nam / Excel: "1.234.567", "1,234,567.5", "12,5", "(1.000)". */
export function soVN(x: any): number | null {
  let s = String(x ?? '').trim();
  if (!s || s === '-') return null;
  let am = false;
  if (/^\(.*\)$/.test(s)) { am = true; s = s.slice(1, -1); }
  s = s.replace(/[^\d.,-]/g, '');
  if (!s) return null;
  const c = (s.match(/,/g) || []).length, d = (s.match(/\./g) || []).length;
  if (c && d) s = s.lastIndexOf(',') > s.lastIndexOf('.') ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
  else if (c) s = c > 1 || /,\d{3}$/.test(s) ? s.replace(/,/g, '') : s.replace(',', '.');
  else if (d) s = d > 1 || /\.\d{3}$/.test(s) ? s.replace(/\./g, '') : s;
  const n = Number(s);
  if (!isFinite(n)) return null;
  return am ? -n : n;
}

/** Ngày "dd/mm/yyyy", "d/m/yy", "yyyy-mm-dd", "dd-mm-yyyy" → yyyy-mm-dd. */
export function ngayVN(x: any): string | null {
  const s = String(x ?? '').trim();
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`;
  m = s.match(/^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})/);
  if (m) {
    const y = m[3].length === 2 ? `20${m[3]}` : m[3];
    const mm = Number(m[2]), dd = Number(m[1]);
    if (mm < 1 || mm > 12 || dd < 1 || dd > 31) return null;
    return `${y}-${String(mm).padStart(2, '0')}-${String(dd).padStart(2, '0')}`;
  }
  return null;
}

/** Tìm dòng tiêu đề: dòng đầu tiên (trong 15 dòng) chứa đủ các từ khóa bắt buộc. */
export function timTieuDe(dong: string[][], batBuoc: string[][]) {
  for (let i = 0; i < Math.min(15, dong.length); i++) {
    const h = dong[i].map(boDau);
    if (batBuoc.every((ds) => h.some((c) => ds.some((k) => c.includes(k))))) return i;
  }
  return -1;
}
export function cot(tieuDe: string[], ...tu: string[]) {
  const h = tieuDe.map(boDau);
  for (const k of tu) { const i = h.findIndex((c) => c === k); if (i >= 0) return i; }
  for (const k of tu) { const i = h.findIndex((c) => c.includes(k)); if (i >= 0) return i; }
  return -1;
}
