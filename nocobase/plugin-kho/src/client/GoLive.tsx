/** Go-Live & số dư đầu kỳ: kỳ mở sổ → dán / tải tệp → kiểm tra → đối chiếu → duyệt → ghi sổ. Chỉ kế toán / quản lý. */
import { Alert, App, Button, Card, Col, DatePicker, Descriptions, Drawer, Input, Radio, Row, Select, Space, Steps, Table, Tabs, Tag, Typography, Upload } from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useState } from 'react';
import { fmt, homNay, ngayVN, useGoi } from './chung';

/** Tiêu đề cột + một dòng ví dụ cho từng loại (khớp máy chủ mo_rong.ts). */
export const MAU: Record<string, { ten: string; nhom: string; tieu_de: string[]; vi_du: string[]; ghi_chu?: string }> = {
  mat_hang: { ten: 'Mặt hàng', nhom: '1. Danh mục', tieu_de: ['Mã hàng', 'Tên hàng', 'ĐVT tồn', 'Loại hàng', 'Kg/bao', 'Giá bán', 'Giá sàn'],
    vi_du: ['DX-25', 'Đỗ xanh bao 25kg', 'Kg', 'Hàng hóa', '25', '40000', '36000'], ghi_chu: 'ĐVT tồn: Kg / Cái / Gói / Bao / Thùng. Loại hàng: Hàng hóa / Nguyên liệu / Thành phẩm / Phụ phẩm / Bao bì.' },
  khach_hang: { ten: 'Khách hàng', nhom: '1. Danh mục', tieu_de: ['Mã khách', 'Tên khách', 'Điện thoại', 'Địa chỉ', 'MST', 'Hạn mức', 'Ghi chú'],
    vi_du: ['KH001', 'Cửa hàng Minh An', '0912345678', 'Hà Nội', '', '50000000', ''] },
  nha_cung_cap: { ten: 'Nhà cung cấp', nhom: '1. Danh mục', tieu_de: ['Mã NCC', 'Tên nhà cung cấp', 'Điện thoại', 'Địa chỉ', 'MST', 'Ghi chú'],
    vi_du: ['NCC01', 'HTX Đỗ Sơn La', '0987000000', 'Sơn La', '', ''] },
  kho: { ten: 'Kho', nhom: '1. Danh mục', tieu_de: ['Mã kho', 'Tên kho', 'Loại kho', 'Địa điểm', 'Kho đang vận chuyển'],
    vi_du: ['HN', 'Kho Hà Nội', 'Bán được', 'Hà Nội', ''], ghi_chu: 'Loại kho: Bán được / Nhà máy / Chờ xử lý. Kho hàng trên đường: ghi x ở cột "Kho đang vận chuyển".' },
  quy: { ten: 'Quỹ / tài khoản', nhom: '1. Danh mục', tieu_de: ['Mã quỹ', 'Tên quỹ', 'Đơn vị', 'Loại', 'Người giữ quỹ'],
    vi_du: ['APH-MB', 'MB APH ****1234', 'APH', 'Ngân hàng', ''], ghi_chu: 'Đơn vị: mã APH / VH / MK / TL. Không ghi đủ số tài khoản ngân hàng.' },
  tai_san: { ten: 'Tài sản / CCDC', nhom: '6. Nhà máy & tài sản', tieu_de: ['Mã tài sản', 'Tên tài sản', 'Loại', 'Serial', 'Địa điểm', 'Người quản lý', 'Tình trạng',
    'Ngày mua', 'Nguyên giá', 'Số tháng sử dụng', 'Số lượng', 'Đơn vị đứng tên', 'Chứng từ mua', 'Dùng cho sản xuất'],
    vi_du: ['MS-01', 'Máy sàng đỗ', 'TSCĐ', '', 'Nhà máy Phú Thọ', 'Tổ trưởng A', 'Đang dùng', '01/03/2024', '120000000', '60', '', '', '', 'x'],
    ghi_chu: 'Loại: TSCĐ / CCDC / Thiết bị văn phòng. Đơn vị đứng tên chỉ ghi khi có chứng từ mua rõ.' },
  ton_dau_ky: { ten: 'Tồn kho đầu kỳ', nhom: '2. Tồn kho đầu kỳ', tieu_de: ['Mã kho', 'Mã hàng', 'Số lượng', 'Số bao', 'Giá trị', 'Tình trạng giá', 'Tình trạng hàng', 'Ghi chú'],
    vi_du: ['HN', 'DX-25', '1000', '40', '30000000', 'Đã chốt', 'Bán được', 'Kiểm kê 25/10, thủ kho A'],
    ghi_chu: 'Số lượng theo ĐVT tồn (Kg / Cái). Tình trạng giá: Đã chốt / Tạm tính (kế toán đã duyệt) / Chưa xác định (để trống giá trị — hàng chờ định giá, chưa bán được). Không ghi giá trị 0. Hàng chờ xử lý → kho loại Chờ xử lý; hàng đang vận chuyển → kho đang vận chuyển. Không chia theo đơn vị.' },
  no_khach: { ten: 'Công nợ khách', nhom: '3. Công nợ đầu kỳ', tieu_de: ['Mã khách', 'Đơn vị', 'Số dư', 'Chứng từ gốc', 'Ngày phát sinh', 'Hạn thanh toán', 'Đối chiếu', 'Ghi chú'],
    vi_du: ['KH001', 'APH', '12000000', 'HĐ 0000101', '01/09/2026', '30/10/2026', 'Đã đối chiếu', ''],
    ghi_chu: 'Mỗi khoản nợ một dòng (một khách được nhiều dòng). Đơn vị = đơn vị có khoản phải thu. Khách trả trước nhập ở "Tiền cọc / chưa phân bổ".' },
  no_ncc: { ten: 'Công nợ nhà cung cấp', nhom: '3. Công nợ đầu kỳ', tieu_de: ['Mã NCC', 'Đơn vị', 'Số dư', 'Chứng từ gốc', 'Ngày phát sinh', 'Hạn thanh toán', 'Đối chiếu', 'Ghi chú'],
    vi_du: ['NCC01', 'APH', '20000000', 'PN cũ 55', '10/10/2026', '', 'Chờ đối chiếu', ''], ghi_chu: 'Không tạo phiếu nhập kho để ghi nợ NCC cũ.' },
  quy_dau_ky: { ten: 'Số dư quỹ / ngân hàng', nhom: '4. Quỹ & ngân hàng', tieu_de: ['Mã quỹ', 'Số dư', 'Ghi chú'], vi_du: ['APH-MB', '300000000', 'Sao kê MB 25/10'],
    ghi_chu: 'Số dư thực tế (đếm quỹ / sao kê). Ghi trước mọi phát sinh của quỹ. Tiền cọc / chưa rõ đã nằm TRONG số dư này.' },
  tien_chua_pb: { ten: 'Tiền cọc / chưa phân bổ', nhom: '4. Quỹ & ngân hàng', tieu_de: ['Mã quỹ', 'Loại', 'Số tiền', 'Mã tham chiếu', 'Mã khách', 'Mục đích cọc', 'Ngày nhận', 'Ghi chú'],
    vi_du: ['APH-MB', 'Cọc', '10000000', 'FT26290001', 'KH001', 'Giữ 1 tấn tháng 11', '20/10/2026', ''],
    ghi_chu: 'Loại: Cọc / Chưa rõ (không có mã khách) / Chưa phân bổ (khách đã nộp, chưa trừ đơn). KHÔNG cộng thêm vào số dư quỹ.' },
  thu_ho_dau_ky: { ten: 'Thu hộ còn giữ', nhom: '4. Quỹ & ngân hàng', tieu_de: ['Đơn vị giữ tiền', 'Đơn vị được trả', 'Số tiền', 'Mã tham chiếu', 'Ghi chú'],
    vi_du: ['APH', 'TL', '6000000', 'TH-09-01', 'Khách chuyển nhầm TK APH'] },
  quy_doi_dvt: { ten: 'Quy đổi đơn vị tính', nhom: '1. Danh mục', tieu_de: ['Mã hàng', 'Đơn vị giao dịch', 'Hệ số', 'Mặc định'],
    vi_du: ['PT-200G', 'Thùng', '5', 'x'], ghi_chu: 'Hệ số = 1 đơn vị giao dịch bằng bao nhiêu ĐVT tồn (vd. 1 thùng = 25 gói × 200 g = 5 kg). Tồn và giá vốn vẫn theo ĐVT tồn.' },
  do_dang_dau_ky: { ten: 'Dở dang sản xuất đầu kỳ', nhom: '6. Nhà máy & tài sản', tieu_de: ['Mã dở dang', 'Mã kho nhà máy', 'Kg dở dang', 'Giá trị', 'Xưởng / tổ', 'Sản phẩm dự kiến', 'Ghi chú'],
    vi_du: ['WIP-01', 'PT', '200', '4200000', 'Tổ 2', 'Đỗ tách vỏ', 'Biên bản kiểm kê chuyền 25/10'], ghi_chu: 'Mỗi dòng mở một mẻ với chi phí "dở dang đầu kỳ"; thu hồi / chốt như mẻ thường. Chưa có giá trị thì chưa nhập.' },
  don_chuyen_tiep: { ten: 'Đơn chưa giao / đang vận chuyển', nhom: '5. Đơn hàng chuyển tiếp', tieu_de: ['Số đơn cũ', 'Mã khách', 'Đơn vị bán', 'Mã hàng', 'Mã kho',
    'Số lượng còn giao', 'Đơn giá', 'Tình trạng', 'Cách giao', 'Ngày đặt', 'Người nhận / xe', 'Ghi chú', 'Giá vốn', 'Đang giữ hàng', 'Đã thu', 'Mã quỹ đã thu'],
    vi_du: ['SO-1023', 'KH001', 'APH', 'DX-25', 'HN', '300', '40000', 'Chưa giao', 'Khách đến lấy', '24/10/2026', '', '', '', 'x', '', ''],
    ghi_chu: 'Chưa giao: hàng còn trong tồn đầu kỳ, đơn vào trạng thái đã chốt. Đang vận chuyển: hàng đã rời kho trước mốc chốt (KHÔNG có trong tồn đầu kỳ), ghi nợ khi chuyển, không trừ kho; KHÔNG nhập khoản này vào công nợ đầu kỳ. Giá vốn (tổng của dòng, có căn cứ): để trống thì lượt "giá vốn chưa xác định" và không vào lãi gộp. Đang giữ hàng = x: tạo lượt chờ xuất giữ hàng. Đã thu (chỉ đơn đang vận chuyển): tiền khách trả trước, đã nằm trong số dư quỹ.' },
};
const TT_LO: Record<string, [string, string]> = { nhap: ['Mới dán', 'default'], da_kiem: ['Đã kiểm tra', 'blue'], da_duyet: ['Đã duyệt', 'purple'],
  da_ghi: ['Đã ghi sổ', 'green'], da_huy: ['Đã hủy', 'red'] };
const TT_DONG: Record<string, [string, string]> = { hop_le: ['Hợp lệ', 'blue'], loi: ['Lỗi', 'red'], trung: ['Trùng / đã có', 'orange'], da_ghi: ['Đã ghi', 'green'], bo_qua: ['Bỏ qua', 'default'] };

function KyMoSo({ doi }: any) {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [ma, setMa] = useState('GOLIVE-2026');
  const [ngay, setNgay] = useState<any>(dayjs('2026-10-25'));
  const [tach, setTach] = useState(true);
  const tai = async () => setDs((await goi('ky_mo_so:list', { params: { sort: ['-id'] } })).data || []);
  useEffect(() => { tai(); }, []);
  return <Space direction="vertical" style={{ width: '100%' }}>
    <Typography.Paragraph type="secondary">Một kỳ mở sổ = một mốc chốt số dư. Trong kỳ đang mở mới ghi được tồn / nợ / tiền đầu kỳ. Xong và đối chiếu khớp thì <b>Khóa kỳ</b>: sau đó không ai (kể cả quản trị) ghi thêm số dư đầu kỳ; sai thì lập chứng từ điều chỉnh.</Typography.Paragraph>
    <Space wrap><Input value={ma} onChange={(e) => setMa(e.target.value)} style={{ width: 200 }} addonBefore="Mã kỳ" />
      <DatePicker format="DD/MM/YYYY" value={ngay} onChange={setNgay} />
      <Radio.Group value={tach} onChange={(e) => setTach(e.target.value)} options={[{ value: true, label: 'Tiền / công nợ: người duyệt khác người nhập' }, { value: false, label: 'Một người nhập và duyệt' }]} />
      <Button type="primary" onClick={async () => { await goi('ky_mo_so:create', { data: { ma, ngay_chot: ngay?.format('YYYY-MM-DD'), tach_nguoi_duyet: tach } }); message.success('Đã mở kỳ'); tai(); doi?.(); }}>Mở kỳ mở sổ</Button></Space>
    <Table size="small" rowKey="id" dataSource={ds} pagination={false} columns={[
      { title: 'Mã kỳ', dataIndex: 'ma', render: (v) => <b>{v}</b> }, { title: 'Ngày chốt số dư', dataIndex: 'ngay_chot', render: ngayVN },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => <Tag color={v === 'mo' ? 'blue' : 'green'}>{v === 'mo' ? 'Đang mở sổ' : 'Đã khóa'}</Tag> },
      { title: 'Tách người duyệt', dataIndex: 'tach_nguoi_duyet', render: (v) => (v === false ? 'Không' : 'Có') }, { title: 'Người khóa', dataIndex: 'khoa_boi' },
      { render: (_, r) => r.trang_thai === 'mo' && <Button danger onClick={() => modal.confirm({ title: `Khóa kỳ ${r.ma}?`, okText: 'Khóa kỳ', cancelText: 'Thôi',
        content: 'Sau khi khóa không ghi thêm được số dư đầu kỳ nào. Chỉ khóa khi tồn, công nợ, tiền đã đối chiếu khớp.',
        onOk: () => goi('ky_mo_so:khoa', { params: { filterByTk: r.id }, data: {} }).then(() => { tai(); doi?.(); }) })}>Khóa kỳ</Button> },
    ]} />
  </Space>;
}

function BangTong({ tk, loai }: any) {
  if (!tk?.file) return null;
  const tien = !['ton_dau_ky', 'don_chuyen_tiep'].includes(loai) || loai === 'don_chuyen_tiep';
  const rows = Object.entries<any>(tk.file).map(([n, f]) => ({ n, f, tr: tk.truoc?.[n], s: tk.sau?.[n] }));
  return <>
    {(tk.canh_bao || []).map((c: string) => <Alert key={c} type="error" showIcon message={c} description="Lô bị CHẶN duyệt / ghi cho tới khi sửa dữ liệu hoặc quản lý duyệt ngoại lệ có căn cứ." style={{ marginBottom: 8 }} />)}
    <Table size="small" rowKey="n" pagination={false} title={() => <b>Tổng đối chiếu</b>} dataSource={rows} columns={[
      { title: loai === 'ton_dau_ky' ? 'Kho' : loai === 'tien_chua_pb' || loai === 'quy_dau_ky' ? 'Quỹ' : 'Đơn vị / nhóm', dataIndex: 'n' },
      { title: 'Số dòng', render: (_, r) => r.f.so_dong },
      ...(loai === 'ton_dau_ky' || loai === 'don_chuyen_tiep' ? [{ title: 'Số lượng trong file', align: 'right' as const, render: (_: any, r: any) => fmt(r.f.so_luong, 3) }] : []),
      ...(tien || loai === 'ton_dau_ky' ? [{ title: 'Giá trị / số tiền trong file', align: 'right' as const, render: (_: any, r: any) => <b>{fmt(r.f.gia_tri)}</b> }] : []),
      ...(tk.truoc && Object.keys(tk.truoc).length ? [{ title: 'Hệ thống trước khi ghi', align: 'right' as const,
        render: (_: any, r: any) => (r.tr ? (loai === 'ton_dau_ky' ? `${fmt(r.tr.so_luong, 3)} · ${fmt(r.tr.gia_tri)} đ` : fmt(r.tr.gia_tri)) : '—') }] : []),
      ...(tk.sau ? [{ title: 'Hệ thống sau khi ghi', align: 'right' as const,
        render: (_: any, r: any) => (r.s ? <b>{loai === 'ton_dau_ky' ? `${fmt(r.s.so_luong, 3)} · ${fmt(r.s.gia_tri)} đ` : fmt(r.s.gia_tri)}</b> : '—') }] : []),
    ]} />
  </>;
}

function Lo({ id, xong }: any) {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [lo, setLo] = useState<any>(null);
  const [dong, setDong] = useState<any[]>([]);
  const [loai, setLoai] = useState<string>('ton_dau_ky');
  const [text, setText] = useState('');
  const [nguon, setNguon] = useState('');
  const [cheDo, setCheDo] = useState('bo_qua');
  const [loc, setLoc] = useState('tat_ca');
  const [dang, setDang] = useState(false);
  const tai = async (x = id) => {
    if (!x) return;
    const r = (await goi('nhap_lo:get', { params: { filterByTk: x } })).data;
    setLo(r); setLoai(r.loai); setText(r.du_lieu_goc || ''); setNguon(r.nguon || ''); setCheDo(r.che_do || 'bo_qua');
    setDong((await goi('nhap_dong:list', { params: { filter: { nhap_lo_id: x }, sort: ['stt'], pageSize: 5000 } })).data || []);
  };
  useEffect(() => { tai(); }, [id]);
  const sua = !lo || ['nhap', 'da_kiem'].includes(lo.trang_thai);
  const mau = MAU[loai];
  const chay = async (fn: () => Promise<any>) => { setDang(true); try { await fn(); } catch { /* đã báo */ } finally { setDang(false); } };
  const kiem = () => chay(async () => {
    let x = lo?.id;
    if (!x) x = (await goi('nhap_lo:create', { data: { loai, du_lieu_goc: text, nguon, che_do: cheDo } })).data.id;
    else await goi('nhap_lo:update', { params: { filterByTk: x }, data: { loai, du_lieu_goc: text, nguon, che_do: cheDo } });
    const r = await goi('nhap_lo:kiem', { params: { filterByTk: x }, data: {} });
    message.info(`Kiểm tra: ${r.data.hop_le} hợp lệ, ${r.data.loi} lỗi, ${r.data.trung} trùng / đã có`, 6);
    await tai(x); xong?.(x);
  });
  const tk = lo?.tong_kiem ? JSON.parse(lo.tong_kiem) : null;
  const buoc = !lo ? 0 : ({ nhap: 0, da_kiem: 1, da_duyet: 2, da_ghi: 3, da_huy: 0 } as any)[lo.trang_thai];
  const dsLoc = dong.filter((d) => loc === 'tat_ca' || d.trang_thai === loc);
  const [sheets, setSheets] = useState<string[]>([]);
  const tepRef = React.useRef<any>(null);
  const guiTep = async (f: File, trang_tinh?: string) => {
    const b64: string = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1] || ''); r.readAsDataURL(f); });
    let x = lo?.id;
    if (!x) x = (await goi('nhap_lo:create', { data: { loai, nguon: nguon || f.name, che_do: cheDo } })).data.id;
    const r = await goi('nhap_lo:taiTep', { params: { filterByTk: x }, data: { ten_tep: f.name, base64: b64, trang_tinh } });
    tepRef.current = f; setSheets(r.data.trang_tinh || []);
    message.success(`Đã đọc ${f.name}${r.data.dang_doc ? ' / ' + r.data.dang_doc : ''}: ${r.data.so_dong} dòng (SHA-256 ${String(r.data.checksum).slice(0, 12)}…)`);
    await tai(x); xong?.(x);
  };
  const docFile = (f: File) => { chay(() => guiTep(f)); return false; };
  return <Space direction="vertical" style={{ width: '100%' }} size="middle">
    <Steps size="small" current={buoc} items={[{ title: 'Dán / tải tệp' }, { title: 'Kiểm tra & đối chiếu' }, { title: 'Duyệt' }, { title: 'Ghi sổ' }]} />
    {lo && <Space><Typography.Title level={5} style={{ margin: 0 }}>{lo.so}</Typography.Title><Tag color={TT_LO[lo.trang_thai]?.[1]}>{TT_LO[lo.trang_thai]?.[0]}</Tag>
      <span>Nhập: {lo.nguoi_nhap || '—'} · Duyệt: {lo.nguoi_duyet || '—'} · Ghi sổ: {lo.ghi_boi || '—'}</span></Space>}
    <Row gutter={12}>
      <Col span={8}><div>Loại dữ liệu</div><Select value={loai} disabled={!!lo} style={{ width: '100%' }} onChange={setLoai}
        options={Object.entries(MAU).map(([value, m]) => ({ value, label: `${m.nhom} — ${m.ten}` }))} /></Col>
      <Col span={10}><div>Nguồn (tên tệp / link Google Sheet + tab)</div><Input value={nguon} disabled={!sua} onChange={(e) => setNguon(e.target.value)} placeholder="vd. Kiem-ke-25-10.xlsx / tab Ton" /></Col>
      {['mat_hang', 'khach_hang', 'nha_cung_cap', 'kho', 'quy', 'tai_san'].includes(loai) && <Col span={6}><div>Mã đã có trong hệ thống</div>
        <Radio.Group value={cheDo} disabled={!sua} onChange={(e) => setCheDo(e.target.value)} options={[{ value: 'bo_qua', label: 'Bỏ qua' }, { value: 'cap_nhat', label: 'Cập nhật theo file' }]} /></Col>}
    </Row>
    {mau && <Alert type="info" message={<span><b>Cột cần có (dòng đầu là tiêu đề):</b> {mau.tieu_de.join(' | ')}</span>} description={mau.ghi_chu}
      action={<Button size="small" onClick={() => { const v = mau.tieu_de.join('\t') + '\n' + mau.vi_du.join('\t'); navigator.clipboard?.writeText(v).catch(() => null); if (!text) setText(v); message.success('Đã chép tiêu đề + dòng mẫu: dán vào Excel / Google Sheets'); }}>Chép mẫu</Button>} />}
    {sua && <Space wrap><Typography.Text>Chọn vùng trong Excel / Google Sheets (cả dòng tiêu đề) rồi dán vào ô dưới, hoặc</Typography.Text>
      <Upload accept=".xlsx,.xls,.csv,.tsv,.txt" showUploadList={false} beforeUpload={docFile}><Button>Tải tệp .xlsx / .csv</Button></Upload>
      {sheets.length > 1 && <Select style={{ width: 200 }} placeholder="Trang tính" value={lo?.trang_tinh} onChange={(v) => tepRef.current && chay(() => guiTep(tepRef.current, v))}
        options={sheets.map((x) => ({ value: x, label: x }))} />}
      <Typography.Text type="secondary">Google Sheets: Tệp → Tải xuống → .xlsx (ảnh chụp tại thời điểm lấy; Sheet đổi sau không tự ghi sổ).</Typography.Text></Space>}
    {lo?.checksum && <Typography.Text type="secondary">Nguồn lưu: {lo.ten_tep || 'dữ liệu dán'}{lo.trang_tinh ? ' / ' + lo.trang_tinh : ''} · SHA-256 {lo.checksum.slice(0, 16)}… · lấy lúc {String(lo.thoi_diem_lay || '').slice(0, 16).replace('T', ' ')}{lo.tep_goc ? <> · <a href={`data:application/octet-stream;base64,${lo.tep_goc}`} download={lo.ten_tep}>tải tệp gốc</a></> : null}</Typography.Text>}
    <Input.TextArea rows={8} value={text} disabled={!sua} onChange={(e) => setText(e.target.value)} style={{ fontFamily: 'monospace', fontSize: 12 }} />
    <Space wrap>
      {sua && <Button type="primary" loading={dang} disabled={!text.trim()} onClick={kiem}>Lưu & Kiểm tra</Button>}
      {lo?.trang_thai === 'da_kiem' && <Button type="primary" loading={dang} disabled={Number(lo.so_loi) > 0 || !Number(lo.so_hop_le)}
        onClick={() => chay(async () => { await goi('nhap_lo:duyet', { params: { filterByTk: lo.id }, data: {} }); await tai(lo.id); })}>Duyệt lô</Button>}
      {lo?.trang_thai === 'da_duyet' && <Button type="primary" danger loading={dang} onClick={() => modal.confirm({ title: `Ghi sổ ${lo.so}?`, okText: 'Ghi sổ', cancelText: 'Thôi',
        content: `Ghi ${lo.so_hop_le} dòng hợp lệ (bỏ qua ${Number(lo.so_trung) || 0} dòng trùng). Cả lô ghi trong một lần: lỗi một dòng thì không ghi dòng nào. Đã ghi thì không xóa lô — sai lập chứng từ điều chỉnh.`,
        onOk: () => chay(async () => { const r = await goi('nhap_lo:ghi', { params: { filterByTk: lo.id }, data: {} }); message.success(`Đã ghi ${r.data.da_ghi} dòng`); await tai(lo.id); xong?.(lo.id); }) })}>Ghi sổ</Button>}
      {lo && !['da_ghi', 'da_huy'].includes(lo.trang_thai) && <Button onClick={() => goi('nhap_lo:huy', { params: { filterByTk: lo.id }, data: {} }).then(() => tai(lo.id))}>Hủy lô</Button>}
      {lo?.trang_thai === 'da_kiem' && tk?.canh_bao?.length > 0 && !lo.ngoai_le && <Button danger onClick={() => { let ly_do = ''; modal.confirm({ title: 'Duyệt ngoại lệ số dư (chỉ quản lý)',
        content: <Input.TextArea placeholder="Căn cứ (biên bản đối chiếu, sao kê…)" onChange={(e) => (ly_do = e.target.value)} />, okText: 'Duyệt ngoại lệ', cancelText: 'Thôi',
        onOk: () => goi('nhap_lo:duyetNgoaiLe', { params: { filterByTk: lo.id }, data: { ly_do } }).then(() => tai(lo.id)) }); }}>Duyệt ngoại lệ (quản lý)</Button>}
      {lo?.ngoai_le && <Tag color="purple">Ngoại lệ: {lo.ngoai_le} — {lo.ngoai_le_boi}</Tag>}
      {lo?.trang_thai === 'da_kiem' && Number(lo.so_loi) > 0 && <Typography.Text type="danger">Còn {lo.so_loi} dòng lỗi: sửa trong Excel / Sheets, dán lại, Kiểm tra lại.</Typography.Text>}
    </Space>
    {tk && <BangTong tk={tk} loai={lo.loai} />}
    {dong.length > 0 && <>
      <Radio.Group value={loc} onChange={(e) => setLoc(e.target.value)} optionType="button" options={[{ value: 'tat_ca', label: `Tất cả ${dong.length}` },
        ...Object.entries(TT_DONG).map(([v, [l]]) => ({ value: v, label: `${l} ${dong.filter((d) => d.trang_thai === v).length}` }))]} />
      <Table size="small" rowKey="id" dataSource={dsLoc} pagination={{ pageSize: 50 }} columns={[
        { title: 'Dòng', dataIndex: 'stt', width: 60 },
        { title: 'Dữ liệu', render: (_, d) => { const o = JSON.parse(d.du_lieu || '{}'); return Object.entries(o).filter(([k, v]) => !k.startsWith('_') && !k.endsWith('_id') && v !== null && v !== '').map(([k, v]) => `${k}: ${v}`).join(' · '); } },
        { title: 'Trạng thái', dataIndex: 'trang_thai', width: 120, render: (v) => <Tag color={TT_DONG[v]?.[1]}>{TT_DONG[v]?.[0]}</Tag> },
        { title: 'Lỗi / ghi chú', dataIndex: 'loi', render: (v) => <span style={{ color: '#cf1322' }}>{v}</span> },
        { title: 'Chứng từ đã tạo', dataIndex: 'ket_qua' },
      ]} />
    </>}
  </Space>;
}

function DanhSachLo() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [mo, setMo] = useState<any>(null);
  const tai = async () => setDs((await goi('nhap_lo:list', { params: { sort: ['-id'], pageSize: 200, appends: ['ky_mo_so'] } })).data || []);
  useEffect(() => { tai(); }, []);
  return <>
    <Space style={{ marginBottom: 12 }}><Button type="primary" onClick={() => setMo('moi')}>+ Lô nhập mới</Button><Button onClick={tai}>Tải lại</Button></Space>
    <Table size="small" rowKey="id" dataSource={ds} onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Lô', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Loại', dataIndex: 'loai', render: (v) => MAU[v] ? `${MAU[v].nhom} — ${MAU[v].ten}` : v },
      { title: 'Kỳ', render: (_, r) => r.ky_mo_so?.ma }, { title: 'Nguồn', dataIndex: 'nguon' },
      { title: 'Dòng', align: 'right', render: (_, r) => `${r.so_dong || 0} (${r.so_hop_le || 0} hợp lệ / ${r.so_loi || 0} lỗi / ${r.so_trung || 0} trùng)` },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => <Tag color={TT_LO[v]?.[1]}>{TT_LO[v]?.[0]}</Tag> },
      { title: 'Người nhập / duyệt / ghi', render: (_, r) => [r.nguoi_nhap, r.nguoi_duyet, r.ghi_boi].map((x) => x || '—').join(' / ') },
      { title: 'Ngày', dataIndex: 'createdAt', render: (v) => ngayVN(v) },
    ]} />
    <Drawer width="92%" open={!!mo} onClose={() => { setMo(null); tai(); }} title="Lô nhập dữ liệu" destroyOnClose>
      {mo && <Lo id={mo === 'moi' ? null : mo} xong={(x: any) => { setMo(x); tai(); }} />}
    </Drawer>
  </>;
}

function NoNccDauKy() {
  const goi = useGoi();
  const { modal } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('no_ncc_dau_ky:list', { params: { appends: ['nha_cung_cap', 'don_vi'], sort: ['-id'], pageSize: 2000 } })).data || []);
  useEffect(() => { tai(); }, []);
  return <Table size="small" rowKey="id" dataSource={ds} columns={[
    { title: 'Số', dataIndex: 'so' }, { title: 'NCC', render: (_, r) => r.nha_cung_cap?.ten }, { title: 'Đơn vị nợ', render: (_, r) => r.don_vi?.ma },
    { title: 'Chứng từ gốc', dataIndex: 'chung_tu_goc' }, { title: 'Ngày', dataIndex: 'ngay_ct', render: ngayVN }, { title: 'Hạn', dataIndex: 'han_tt', render: ngayVN },
    { title: 'Số dư đầu kỳ', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) }, { title: 'Đã trả', dataIndex: 'da_tra', align: 'right', render: (v) => fmt(v) },
    { title: 'Đối chiếu', dataIndex: 'doi_chieu', render: (v) => <Tag color={v === 'da' ? 'green' : 'orange'}>{v === 'da' ? 'Đã đối chiếu' : 'Chờ'}</Tag> },
    { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => (v === 'da_huy' ? <Tag color="red">Đã hủy</Tag> : '') },
    { render: (_, r) => r.trang_thai === 'da_ghi' && <Space>
      {r.doi_chieu !== 'da' && <Button size="small" onClick={() => goi('no_ncc_dau_ky:update', { params: { filterByTk: r.id }, data: { doi_chieu: 'da' } }).then(tai)}>Đã đối chiếu</Button>}
      <Button size="small" danger onClick={() => { let ly_do = ''; modal.confirm({ title: `Hủy ${r.so}?`, okText: 'Hủy', cancelText: 'Thôi',
        content: <Input placeholder="Lý do" onChange={(e) => (ly_do = e.target.value)} />, onOk: () => goi('no_ncc_dau_ky:huy', { params: { filterByTk: r.id }, data: { ly_do } }).then(tai) }); }}>Hủy</Button></Space> },
  ]} />;
}

function NoKhachDauKy() {
  const goi = useGoi();
  const { modal } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('don_ban:list', { params: { filter: { loai: 'dau_ky' }, appends: ['khach', 'don_vi_ban'], sort: ['-id'], pageSize: 5000 } })).data || []);
  useEffect(() => { tai(); }, []);
  return <Table size="small" rowKey="id" dataSource={ds} columns={[
    { title: 'Số', dataIndex: 'so' }, { title: 'Khách', render: (_, r) => r.khach?.ten }, { title: 'Đơn vị', render: (_, r) => r.don_vi_ban?.ma },
    { title: 'Chứng từ gốc', dataIndex: 'chung_tu_goc' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Hạn', dataIndex: 'han_tt', render: ngayVN },
    { title: 'Nợ đầu kỳ', dataIndex: 'tong_tien', align: 'right', render: (v) => fmt(v) }, { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v) => <b>{fmt(v)}</b> },
    { title: 'Đối chiếu', dataIndex: 'doi_chieu', render: (v) => <Tag color={v === 'da' ? 'green' : 'orange'}>{v === 'da' ? 'Đã đối chiếu' : 'Chờ'}</Tag> },
    { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => (v === 'da_huy' ? <Tag color="red">Đã hủy</Tag> : '') },
    { render: (_, r) => r.trang_thai !== 'da_huy' && Number(r.da_thu) === 0 && <Button size="small" danger onClick={() => { let ly_do = ''; modal.confirm({ title: `Hủy nợ đầu kỳ ${r.so}?`,
      okText: 'Hủy', cancelText: 'Thôi', content: <Input placeholder="Lý do (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} />,
      onOk: () => goi('don_ban:huy', { params: { filterByTk: r.id }, data: { ly_do } }).then(tai) }); }}>Hủy</Button> },
  ]} />;
}

function DoiChieu() {
  const goi = useGoi();
  const [d, setD] = useState<any>(null);
  const tai = () => goi('gia_von:doiChieu', { data: {} }).then((r) => setD(r.data));
  useEffect(() => { tai(); }, []);
  if (!d) return null;
  return <Space direction="vertical" style={{ width: '100%' }}>
    <Alert type={d.can ? 'success' : 'error'} showIcon message={d.can ? 'CÂN: Σ sổ kho = tồn, Σ sổ giá trị = giá trị tồn, mọi điều chỉnh giá trị cân' : 'CÓ LỆCH — xem bảng dưới, chưa dùng số liệu'} />
    <Descriptions size="small" bordered column={3} items={[
      { label: 'Σ sổ giá trị', children: fmt(d.tong?.so_gia_tri) }, { label: 'Giá trị tồn', children: fmt(d.tong?.gia_tri_ton) },
      { label: 'Trong đó mở đầu', children: fmt(d.tong?.mo_dau) }, { label: 'Điều chỉnh vào giá vốn kỳ', children: fmt(d.tong?.dieu_chinh_gia_von) },
      { label: 'Tổng số dư quỹ', children: fmt(d.tong?.tong_quy) }]} />
    {['lech_so_luong', 'lech_gia_tri', 'dieu_chinh_khong_can'].map((k) => (d[k] || []).length > 0 && <Table key={k} size="small" title={() => k} rowKey={(r: any) => JSON.stringify(r)}
      dataSource={d[k]} columns={Object.keys(d[k][0]).map((c) => ({ title: c, dataIndex: c }))} pagination={false} />)}
    <Button onClick={tai}>Đối chiếu lại</Button>
  </Space>;
}

export function GoLive() {
  const [k, setK] = useState(0);
  return (
    <Card title="Go-Live & số dư đầu kỳ">
      <Alert style={{ marginBottom: 12 }} showIcon type="info" message="Thứ tự: 1. Mở kỳ → 2. Danh mục (kho, hàng, khách, NCC, quỹ) → 3. Tồn đầu kỳ → 4. Công nợ khách / NCC → 5. Số dư quỹ, rồi tiền cọc / chưa phân bổ / thu hộ → 6. Đơn chuyển tiếp → 7. Đối chiếu → Khóa kỳ. Sao lưu trước khi ghi sổ lô lớn." />
      <Tabs items={[
        { key: 'ky', label: 'Kỳ mở sổ', children: <KyMoSo key={k} doi={() => setK(k + 1)} /> },
        { key: 'lo', label: 'Nhập dữ liệu (lô)', children: <DanhSachLo /> },
        { key: 'nk', label: 'Nợ khách đầu kỳ', children: <NoKhachDauKy /> },
        { key: 'nn', label: 'Nợ NCC đầu kỳ', children: <NoNccDauKy /> },
        { key: 'dc', label: 'Đối chiếu bảo toàn', children: <DoiChieu /> },
      ]} />
    </Card>
  );
}
