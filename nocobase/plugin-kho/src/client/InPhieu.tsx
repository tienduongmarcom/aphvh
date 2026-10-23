/**
 * Trang in A5: /in/don_ban/:id (phiếu xuất kho kiêm giao nhận, 2 liên trên một tờ A4 hoặc từng tờ A5)
 *              /in/phieu_thu/:id (phiếu thu, 2 liên)
 * Mở bằng nút "In phiếu" (liên kết) trong màn hình đơn bán / phiếu thu. Phiếu xuất KHÔNG in giá.
 */
import { useAPIClient } from '@nocobase/client';
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

const so = (v: any, d = 0) =>
  Number(v || 0).toLocaleString('vi-VN', { minimumFractionDigits: 0, maximumFractionDigits: d });
const ngay = (v: string) => (v ? v.slice(0, 10).split('-').reverse().join('/') : '');

const DOC_SO = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];
function docBa(n: number, day: boolean) {
  const t = Math.floor(n / 100), c = Math.floor((n % 100) / 10), d = n % 10;
  const r: string[] = [];
  if (day || t) r.push(DOC_SO[t], 'trăm');
  if (c > 1) r.push(DOC_SO[c], 'mươi');
  else if (c === 1) r.push('mười');
  else if ((day || t) && d) r.push('linh');
  if (d === 1 && c > 1) r.push('mốt');
  else if (d === 5 && c > 0) r.push('lăm');
  else if (d) r.push(DOC_SO[d]);
  return r.join(' ');
}
export function docTien(v: number) {
  let n = Math.round(Math.abs(v || 0));
  if (!n) return 'Không đồng';
  const don = ['', 'nghìn', 'triệu', 'tỷ'];
  const nhom: number[] = [];
  while (n > 0) { nhom.push(n % 1000); n = Math.floor(n / 1000); }
  const r: string[] = [];
  for (let i = nhom.length - 1; i >= 0; i--) {
    if (!nhom[i]) continue;
    r.push(docBa(nhom[i], i < nhom.length - 1), don[i % 4] + (i >= 4 ? ' tỷ' : ''));
  }
  const s = r.join(' ').replace(/\s+/g, ' ').trim() + ' đồng';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const css = `
@page { size: A5 landscape; margin: 8mm; }
body { margin: 0; background: #fff; }
.lien { font-family: Arial, sans-serif; font-size: 12px; color: #111; width: 194mm; min-height: 128mm; box-sizing: border-box;
  padding: 2mm 3mm; page-break-after: always; }
.lien:last-child { page-break-after: auto; }
.dau { display: flex; justify-content: space-between; }
.tieu-de { font-size: 18px; font-weight: 700; text-align: center; margin: 4px 0; }
.khung { border: 1.5px solid #111; padding: 2px 8px; font-weight: 700; }
table { width: 100%; border-collapse: collapse; margin-top: 6px; }
th, td { border: 1px solid #111; padding: 3px 5px; }
th { background: #f0f0f0; }
.so { text-align: right; }
.ky { display: grid; grid-template-columns: repeat(4, 1fr); text-align: center; margin-top: 10px; gap: 6px; }
.ky div { min-height: 60px; }
.nho { color: #444; font-size: 11px; }
.nut { margin: 12px; } @media print { .nut { display: none; } }
`;

function PhieuXuat({ d, lien }: any) {
  const tongKg = (d.dong || []).reduce((s: number, x: any) => s + Number(x.so_kg || 0), 0);
  const tongBao = (d.dong || []).reduce((s: number, x: any) => s + Number(x.so_bao || 0), 0);
  return (
    <div className="lien">
      <div className="dau">
        <div><b>{d.don_vi_ban?.ten}</b><div className="nho">{d.don_vi_ban?.dia_chi} {d.don_vi_ban?.mst ? '· MST ' + d.don_vi_ban.mst : ''}</div></div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/2</span><div className="nho">{lien === 1 ? 'Kho giữ' : 'Khách giữ'}</div></div>
      </div>
      <div className="tieu-de">PHIẾU XUẤT KHO KIÊM GIAO NHẬN</div>
      <div className="dau"><div>Số: <b>{d.so}</b></div><div>Ngày: {ngay(d.ngay_giao || d.ngay)}</div></div>
      <div>Khách hàng: <b>{d.khach?.ten}</b> {d.sdt ? '· ĐT ' + d.sdt : ''}</div>
      <div>Địa chỉ: {d.dia_chi_giao}</div>
      <div>Cách giao: {d.cach_giao === 'van_chuyen' ? 'Vận chuyển' : 'Khách đến lấy'}
        {d.nguoi_nhan ? ' · Người nhận: ' + d.nguoi_nhan : ''}{d.bien_so ? ' · Xe: ' + d.bien_so : ''}</div>
      <table>
        <thead><tr><th>STT</th><th>Mã hàng</th><th>Tên hàng</th><th>Kho xuất</th><th>Số bao</th><th>Số kg</th><th>Ghi chú</th></tr></thead>
        <tbody>
          {(d.dong || []).map((x: any, i: number) => (
            <tr key={x.id}><td className="so">{i + 1}</td><td>{x.mat_hang?.ma}</td><td>{x.ten_hang || x.mat_hang?.ten}</td>
              <td>{x.kho?.ten}</td><td className="so">{so(x.so_bao, 2)}</td><td className="so">{so(x.so_kg, 3)}</td><td></td></tr>
          ))}
          <tr><td colSpan={4} className="so"><b>Cộng</b></td><td className="so"><b>{so(tongBao, 2)}</b></td><td className="so"><b>{so(tongKg, 3)}</b></td><td></td></tr>
        </tbody>
      </table>
      <div className="nho">Phiếu không in giá. Chữ ký nhận hàng chỉ xác nhận số lượng, không xác nhận đã thanh toán.
        {d.trang_thai === 'da_giao' ? ' — IN LẠI SAU KHI ĐÃ GIAO: BẢN SAO.' : ''}</div>
      <div className="ky">
        <div><b>Người lập phiếu</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người xuất kho</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người nhận hàng</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Bảo vệ / cổng</b><div className="nho">(nếu có)</div></div>
      </div>
    </div>
  );
}

function PhieuThu({ d, lien }: any) {
  return (
    <div className="lien">
      <div className="dau">
        <div><b>{d.don_vi?.ten}</b><div className="nho">{d.don_vi?.dia_chi}</div></div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/2</span></div>
      </div>
      <div className="tieu-de">PHIẾU THU</div>
      <div className="dau"><div>Số: <b>{d.so}</b></div><div>Ngày: {ngay(d.ngay)}</div></div>
      <div>Họ tên người nộp: {d.nguoi_nop || d.khach?.ten}</div>
      <div>Khách hàng: <b>{d.khach?.ten}</b></div>
      <div>Hình thức: {d.hinh_thuc === 'chuyen_khoan' ? 'Chuyển khoản' + (d.ma_gd ? ' · ' + d.ma_gd : '') : 'Tiền mặt'}</div>
      <div>Số tiền: <b>{so(d.so_tien)} đ</b> — <i>{docTien(d.so_tien)}</i></div>
      <table>
        <thead><tr><th>Trả cho đơn</th><th>Số tiền</th></tr></thead>
        <tbody>
          {(d.phan_bo || []).map((p: any) => <tr key={p.id}><td>{p.don_ban?.so}</td><td className="so">{so(p.so_tien)}</td></tr>)}
          <tr><td>Chưa phân bổ</td><td className="so">{so(d.chua_phan_bo)}</td></tr>
        </tbody>
      </table>
      <div className="ky" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div><b>Người nộp tiền</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người thu tiền</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Kế toán</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
      </div>
    </div>
  );
}

export function InPhieu() {
  const { loai, id } = useParams();
  const api = useAPIClient();
  const [d, setD] = useState<any>(null);
  const [loi, setLoi] = useState('');
  useEffect(() => {
    const appends = loai === 'don_ban'
      ? ['khach', 'don_vi_ban', 'dong', 'dong.mat_hang', 'dong.kho']
      : ['khach', 'don_vi', 'phan_bo', 'phan_bo.don_ban'];
    api.request({ url: `${loai}:get`, params: { filterByTk: id, appends } })
      .then((r: any) => setD(r.data.data))
      .catch((e: any) => setLoi(e?.response?.data?.errors?.[0]?.message || 'Không mở được chứng từ (kiểm tra quyền).'));
  }, [loai, id]);
  if (loi) return <div style={{ padding: 24 }}>{loi}</div>;
  if (!d) return <div style={{ padding: 24 }}>Đang tải…</div>;
  const Mau = loai === 'don_ban' ? PhieuXuat : PhieuThu;
  return (
    <div>
      <style>{css}</style>
      <div className="nut"><button onClick={() => window.print()} style={{ fontSize: 16, padding: '6px 18px' }}>In (A5 ngang, 2 liên)</button></div>
      <Mau d={d} lien={1} />
      <Mau d={d} lien={2} />
    </div>
  );
}
