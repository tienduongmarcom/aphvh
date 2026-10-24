/**
 * Trang in A5: /in/don_ban/:id (phiếu xuất kho kiêm giao nhận, 2 liên trên một tờ A4 hoặc từng tờ A5)
 *              /in/luot_giao/:id (phiếu xuất cho một lượt giao — giao nhiều đợt mỗi đợt một phiếu)
 *              /in/phieu_thu/:id (phiếu thu, 2 liên)
 * Mở bằng nút "In phiếu" (liên kết) trong màn hình đơn bán / phiếu thu. Phiếu xuất KHÔNG in giá.
 */
import { useAPIClient } from '@nocobase/client';
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

const so = (v: any, d = 0) =>
  Number(v || 0).toLocaleString('vi-VN', { minimumFractionDigits: 0, maximumFractionDigits: d });
const ngay = (v: string) => (v ? v.slice(0, 10).split('-').reverse().join('/') : '');

const DVT_IN: any = { kg: 'kg', cai: 'cái', goi: 'gói', bao: 'bao', thung: 'thùng' };
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

function PhieuXuat({ d, lien, soLien }: any) {
  const vc = d.cach_giao === 'van_chuyen';
  const giu = vc ? ['Kho giữ', 'Bên vận chuyển giữ', 'Khách ký nhận — gửi lại kho'][lien - 1] : (lien === 1 ? 'Kho giữ' : 'Khách giữ');
  const tongKg = (d.dong || []).reduce((s: number, x: any) => s + Number(x.so_kg || 0), 0);
  const tongBao = (d.dong || []).reduce((s: number, x: any) => s + Number(x.so_bao || 0), 0);
  return (
    <div className="lien">
      <div className="dau">
        <div><b>{d.don_vi_ban?.ten}</b><div className="nho">{d.don_vi_ban?.dia_chi} {d.don_vi_ban?.mst ? '· MST ' + d.don_vi_ban.mst : ''}</div></div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/{soLien}</span><div className="nho">{giu}</div></div>
      </div>
      <div className="tieu-de">{vc ? 'PHIẾU XUẤT KHO GIAO VẬN CHUYỂN' : 'PHIẾU XUẤT KHO KIÊM GIAO NHẬN'}</div>
      <div className="dau"><div>Số: <b>{d.so}</b></div><div>Ngày: {ngay(d.ngay_giao || d.ngay)}</div></div>
      <div>Khách hàng: <b>{d.khach?.ten}</b> {d.sdt ? '· ĐT ' + d.sdt : ''}</div>
      <div>Địa chỉ: {d.dia_chi_giao}</div>
      <div>Cách giao: {d.cach_giao === 'van_chuyen' ? 'Vận chuyển' : 'Khách đến lấy'}
        {d.nguoi_nhan ? ' · Người nhận: ' + d.nguoi_nhan : ''}{d.bien_so ? ' · Xe: ' + d.bien_so : ''}</div>
      <table>
        <thead><tr><th>STT</th><th>Mã hàng</th><th>Tên hàng</th><th>Kho xuất</th><th>Số bao</th><th>Số lượng</th><th>ĐVT</th></tr></thead>
        <tbody>
          {(d.dong || []).map((x: any, i: number) => (
            <tr key={x.id}><td className="so">{i + 1}</td><td>{x.mat_hang?.ma}</td><td>{x.ten_hang || x.mat_hang?.ten}</td>
              <td>{x.kho?.ten}</td><td className="so">{so(x.so_bao, 2)}</td><td className="so">{so(x.so_kg, 3)}</td><td>{DVT_IN[x.mat_hang?.dvt_ton || 'kg']}</td></tr>
          ))}
          <tr><td colSpan={4} className="so"><b>Cộng</b></td><td className="so"><b>{so(tongBao, 2)}</b></td><td className="so"><b>{so(tongKg, 3)}</b></td><td></td></tr>
        </tbody>
      </table>
      <div className="nho">Phiếu không in giá. Chữ ký nhận hàng chỉ xác nhận số lượng, không xác nhận đã thanh toán.
        {['da_giao', 'da_ban_giao_xe', 'khach_da_nhan'].includes(d.trang_thai) ? ' — IN LẠI SAU KHI ĐÃ XUẤT: BẢN SAO.' : ''}</div>
      {vc ? <div className="ky">
        <div><b>Người xuất kho</b><div className="nho">Phần 1 — tại kho, giờ …h…</div></div>
        <div><b>Bên vận chuyển nhận</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Bên vận chuyển giao</b><div className="nho">Phần 2 — giao khách, …/… …h…</div></div>
        <div><b>Khách / người nhận</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
      </div> : <div className="ky">
        <div><b>Người lập phiếu</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người xuất kho</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người nhận hàng</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Bảo vệ / cổng</b><div className="nho">(nếu có)</div></div>
      </div>}
    </div>
  );
}

function PhieuThu({ d, lien, soLien }: any) {
  return (
    <div className="lien">
      <div className="dau">
        <div><b>{d.don_vi?.ten}</b><div className="nho">{d.don_vi?.dia_chi}</div></div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/{soLien}</span></div>
      </div>
      <div className="tieu-de">PHIẾU THU</div>
      <div className="dau"><div>Số: <b>{d.so}</b></div><div>Ngày: {ngay(d.ngay)}</div></div>
      <div>Họ tên người nộp: {d.nguoi_nop || d.khach?.ten}</div>
      <div>Khách hàng: <b>{d.khach?.ten || 'Chưa rõ — chờ xác minh'}</b>{d.loai_thu === 'coc' ? ' · TIỀN ĐẶT CỌC' + (d.muc_dich_coc ? ': ' + d.muc_dich_coc : '') : ''}</div>
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

function PhieuChi({ d, lien, soLien }: any) {
  return (
    <div className="lien">
      <div className="dau"><div><b>{d.don_vi?.ten}</b><div className="nho">{d.don_vi?.dia_chi}</div></div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/{soLien}</span></div></div>
      <div className="tieu-de">PHIẾU CHI</div>
      <div className="dau"><div>Số: <b>{d.so}</b></div><div>Ngày: {ngay(d.ngay)}</div></div>
      <div>Họ tên người nhận tiền: <b>{d.nguoi_nhan}</b></div>
      <div>Lý do chi: {d.ly_do}</div>
      <div>Chi từ: {d.quy?.ten}{d.ma_gd ? ' · Mã GD ' + d.ma_gd : ''}</div>
      <div>Số tiền: <b>{so(d.so_tien)} đ</b> — <i>{docTien(d.so_tien)}</i></div>
      <div className="ky" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div><b>Người lập phiếu</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Kế toán</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Thủ quỹ</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người nhận tiền</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
      </div>
    </div>
  );
}

const TEN_LOAI: any = { nhap: 'PHIẾU NHẬP KHO', xuat: 'PHIẾU XUẤT KHO', chuyen: 'PHIẾU CHUYỂN KHO KIÊM GIAO NHẬN NỘI BỘ', dau_ky: 'PHIẾU NHẬP TỒN ĐẦU KỲ',
  kiem_ke: 'BIÊN BẢN ĐIỀU CHỈNH KIỂM KÊ', san_xuat: 'PHIẾU SẢN XUẤT', dong_goi: 'PHIẾU ĐÓNG GÓI / ĐỔI BAO' };
function PhieuKho({ d, lien, soLien }: any) {
  const ck = d.loai === 'chuyen';
  const sx = d.loai === 'san_xuat' || d.loai === 'dong_goi';
  const giu = ck ? ['Kho nguồn giữ', 'Người vận chuyển giữ', 'Kho đích giữ'][lien - 1] : '';
  const dong = (d.dong || []).sort((a: any, b: any) => a.id - b.id);
  return (
    <div className="lien">
      <div className="dau"><div><b>Kho: {d.kho?.ten}</b>{d.kho_dich ? <span> → <b>{d.kho_dich.ten}</b></span> : null}</div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/{soLien}</span><div className="nho">{giu}</div></div></div>
      <div className="tieu-de">{TEN_LOAI[d.loai] || 'PHIẾU KHO'}</div>
      <div className="dau"><div>Số: <b>{d.so}</b>{d.trang_thai === 'nhap' ? ' (NHÁP — chưa ghi sổ)' : d.trang_thai === 'da_huy' ? ' (ĐÃ HỦY)' : ''}</div><div>Ngày: {ngay(d.ngay)}</div></div>
      {d.nguoi_giao_nhan && <div>Người giao / nhận: {d.nguoi_giao_nhan}</div>}
      {d.xuong && <div>Xưởng / tổ: {d.xuong}</div>}
      {d.ghi_chu && <div>Ghi chú: {d.ghi_chu}</div>}
      <table>
        <thead><tr><th>STT</th>{sx && <th>Vào / ra</th>}<th>Mã hàng</th><th>Tên hàng</th><th>Số bao</th><th>Số kg</th>{ck && <th>Kg thực nhận</th>}<th>Ghi chú</th></tr></thead>
        <tbody>{dong.map((x: any, i: number) => <tr key={x.id}><td className="so">{i + 1}</td>
          {sx && <td>{({ vao: 'Nguyên liệu vào', ra: 'Thành phẩm ra', phu_pham: 'Phụ phẩm' } as any)[x.huong]}</td>}
          <td>{x.mat_hang?.ma}</td><td>{x.ten_hang || x.mat_hang?.ten}</td><td className="so">{so(x.so_bao, 2)}</td><td className="so">{so(x.so_kg, 3)}</td>
          {ck && <td></td>}<td>{x.ghi_chu}</td></tr>)}</tbody>
      </table>
      {ck ? <div className="ky">
        <div><b>Người xuất (kho nguồn)</b><div className="nho">Phần 1 — giờ …h…</div></div>
        <div><b>Người vận chuyển nhận</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Người vận chuyển giao</b><div className="nho">Phần 2 — giờ …h…</div></div>
        <div><b>Người nhận (kho đích)</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
      </div> : <div className="ky" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div><b>Người lập phiếu</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>{sx ? 'Tổ trưởng sản xuất' : 'Người giao / nhận'}</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Thủ kho</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
      </div>}
    </div>
  );
}


/** Đơn gộp — bản cho KHÁCH: một phiếu tổng, ghi rõ bên bán từng dòng (mỗi bên bán là một nghĩa vụ / hóa đơn riêng). */
function DonGopIn({ d, lien, soLien }: any) {
  const dong = (d.dong || []).sort((a: any, b: any) => a.id - b.id);
  const theoBen: Record<string, number> = {};
  for (const c of d.don_con || []) if (c.trang_thai !== 'da_huy') theoBen[c.don_vi_ban?.ten || c.don_vi_ban_id] = (theoBen[c.don_vi_ban?.ten || c.don_vi_ban_id] || 0) + Number(c.tong_tien || 0);
  const dd: Record<string, any> = {};
  for (const c of d.don_con || []) for (const x of c.dong || []) dd[x.id] = x;
  return (
    <div className="lien">
      <div className="dau"><div><b>ĐƠN HÀNG TỔNG HỢP</b><div className="nho">Hàng do nhiều đơn vị bán — xem cột "Bên bán"</div></div>
        <div style={{ textAlign: 'right' }}><span className="khung">LIÊN {lien}/{soLien}</span></div></div>
      <div className="tieu-de">ĐƠN ĐẶT HÀNG</div>
      <div className="dau"><div>Số: <b>{d.so}</b></div><div>Ngày: {ngay(d.ngay)}</div></div>
      <div>Khách hàng: <b>{d.khach?.ten}</b> {d.sdt ? '· ĐT ' + d.sdt : ''}</div>
      <div>Địa chỉ giao: {d.dia_chi_giao}</div>
      <table>
        <thead><tr><th>STT</th><th>Bên bán</th><th>Mã hàng</th><th>Tên hàng</th><th>Số lượng</th><th>ĐVT</th><th>Đơn giá</th><th>Thành tiền</th></tr></thead>
        <tbody>{dong.map((x: any, i: number) => { const c = dd[x.don_ban_dong_id] || {}; return <tr key={x.id}><td className="so">{i + 1}</td><td>{x.don_vi_ban?.ma}</td>
          <td>{x.mat_hang?.ma}</td><td>{x.mat_hang?.ten}</td><td className="so">{so(x.so_kg, 3)}</td><td>{DVT_IN[x.mat_hang?.dvt_ton || 'kg']}</td>
          <td className="so">{so(c.don_gia_tt || c.don_gia)}</td><td className="so">{so(c.thanh_tien)}</td></tr>; })}
          {Object.entries(theoBen).map(([b, v]) => <tr key={b}><td colSpan={7} className="so">Cộng {b}</td><td className="so">{so(v)}</td></tr>)}
          <tr><td colSpan={7} className="so"><b>TỔNG CỘNG</b></td><td className="so"><b>{so(d.tong_tien)}</b></td></tr></tbody>
      </table>
      <div><i>{docTien(d.tong_tien)}</i></div>
      <div className="nho">Mỗi bên bán xuất hóa đơn / thu tiền theo phần hàng của mình. Thanh toán ghi rõ trả cho bên bán nào.</div>
      <div className="ky" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div><b>Người lập</b><div className="nho">(ký, ghi rõ họ tên)</div></div><div><b>Khách hàng</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
        <div><b>Duyệt</b><div className="nho">(ký, ghi rõ họ tên)</div></div>
      </div>
    </div>
  );
}

/** Chuyến chuyển hàng hai đầu: có cột thực nhận để kho đến ghi tay. */
function ChuyenHangIn({ d, lien, soLien }: any) {
  return PhieuKho({ d: { ...d, loai: 'chuyen', kho: d.kho_di, kho_dich: d.kho_den, nguoi_giao_nhan: [d.nguoi_giao, d.xe].filter(Boolean).join(' · '),
    dong: (d.dong || []).map((x: any) => ({ ...x, ghi_chu: x.so_kg_nhan !== null && x.so_kg_nhan !== undefined ? `Đã nhận ${so(x.so_kg_nhan, 3)}` : x.so_lo ? `Lô ${x.so_lo}` : '' })) }, lien, soLien });
}

export function InPhieu() {
  const { loai, id } = useParams();
  const api = useAPIClient();
  const [d, setD] = useState<any>(null);
  const [loi, setLoi] = useState('');
  useEffect(() => {
    const appends = ({
      don_ban: ['khach', 'don_vi_ban', 'dong', 'dong.mat_hang', 'dong.kho'],
      phieu_thu: ['khach', 'don_vi', 'phan_bo', 'phan_bo.don_ban', 'quy'],
      phieu_chi: ['don_vi', 'quy'],
      phieu_kho: ['kho', 'kho_dich', 'dong', 'dong.mat_hang'],
      luot_giao: ['dong', 'dong.mat_hang', 'dong.kho', 'don_ban', 'don_ban.khach', 'don_ban.don_vi_ban'],
      don_gop: ['khach', 'dong', 'dong.mat_hang', 'dong.don_vi_ban', 'don_con', 'don_con.don_vi_ban', 'don_con.dong'],
      chuyen_hang: ['kho_di', 'kho_den', 'dong', 'dong.mat_hang'],
    } as any)[loai as string] || [];
    if (loai === 'giao_gop') {
      // Chuyến giao gộp: in phiếu xuất của từng lượt (mỗi đơn con / bên bán một phiếu) liền nhau.
      api.request({ url: 'giao_gop_luot:list', params: { filter: JSON.stringify({ giao_gop_id: id }), pageSize: 50 } })
        .then((r: any) => Promise.all((r.data.data || []).map((l: any) => api.request({ url: 'luot_giao:get', params: { filterByTk: l.luot_giao_id,
          appends: ['dong', 'dong.mat_hang', 'dong.kho', 'don_ban', 'don_ban.khach', 'don_ban.don_vi_ban'] } }))))
        .then((rs: any[]) => setD({ nhieu: rs.map((r) => { const x = r.data.data; return { ...x, so: `${x.so} (đơn ${x.don_ban?.so})`, ngay_giao: x.ngay, khach: x.don_ban?.khach,
          don_vi_ban: x.don_ban?.don_vi_ban, sdt: x.don_ban?.sdt, dia_chi_giao: x.don_ban?.dia_chi_giao, dong: (x.dong || []).sort((a: any, b: any) => a.id - b.id) }; }) }))
        .catch((e: any) => setLoi(e?.response?.data?.errors?.[0]?.message || 'Không mở được chuyến giao.'));
      return;
    }
    api.request({ url: `${loai}:get`, params: { filterByTk: id, appends } })
      .then((r: any) => {
        const x = r.data.data;
        if (loai === 'giao_gop') return;
        if (loai !== 'luot_giao') return setD(x);
        // Lượt giao in theo mẫu phiếu xuất của đơn: thông tin khách / đơn vị lấy từ đơn.
        setD({ ...x, so: `${x.so} (đơn ${x.don_ban?.so})`, ngay_giao: x.ngay, khach: x.don_ban?.khach, don_vi_ban: x.don_ban?.don_vi_ban,
          sdt: x.don_ban?.sdt, dia_chi_giao: x.don_ban?.dia_chi_giao, dong: (x.dong || []).sort((a: any, b: any) => a.id - b.id) });
      })
      .catch((e: any) => setLoi(e?.response?.data?.errors?.[0]?.message || 'Không mở được chứng từ (kiểm tra quyền).'));
  }, [loai, id]);
  if (loi) return <div style={{ padding: 24 }}>{loi}</div>;
  if (!d) return <div style={{ padding: 24 }}>Đang tải…</div>;
  if (d.nhieu) return <div><style>{css}</style><div className="nut"><button onClick={() => window.print()} style={{ fontSize: 16, padding: '6px 18px' }}>In chuyến giao (mỗi bên bán một phiếu)</button></div>
    {d.nhieu.map((x: any) => [1, 2].map((l) => <PhieuXuat key={`${x.id}-${l}`} d={x} lien={l} soLien={2} />))}</div>;
  const Mau: any = ({ don_ban: PhieuXuat, luot_giao: PhieuXuat, phieu_thu: PhieuThu, phieu_chi: PhieuChi, phieu_kho: PhieuKho, don_gop: DonGopIn, chuyen_hang: ChuyenHangIn } as any)[loai as string] || PhieuThu;
  const soLien = (['don_ban', 'luot_giao'].includes(loai as string) && d.cach_giao === 'van_chuyen') || (loai === 'phieu_kho' && d.loai === 'chuyen') || loai === 'chuyen_hang' ? 3 : 2;
  return (
    <div>
      <style>{css}</style>
      <div className="nut"><button onClick={() => window.print()} style={{ fontSize: 16, padding: '6px 18px' }}>In (A5 ngang, {soLien} liên)</button>
        {d.trang_thai === 'da_huy' && <b style={{ color: '#cf1322', marginLeft: 12 }}>CHỨNG TỪ ĐÃ HỦY</b>}</div>
      {Array.from({ length: soLien }, (_, i) => <Mau key={i} d={d} lien={i + 1} soLien={soLien} />)}
    </div>
  );
}
