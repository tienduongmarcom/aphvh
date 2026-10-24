/**
 * 0.4.0 Tiền: chuyển khoản chờ xác minh, đối soát sao kê ngân hàng (nạp tệp → khớp / tạo phiếu thu / bỏ qua), xử lý khoản phải hoàn.
 */
import { Alert, App, Button, Input, Modal, Radio, Space, Table, Tag, Typography, Upload } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, fmt, ngayVN, useGoi } from './chung';

const docB64 = (f: File) => new Promise<string>((ok, hong) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1]); r.onerror = hong; r.readAsDataURL(f); });

export function ChoXacMinh() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('phieu_thu:list', { params: { filter: { trang_thai: 'cho_xac_minh' }, appends: ['khach', 'quy', 'don_vi'], sort: ['ngay', 'id'], pageSize: 500 } })).data || []);
  useEffect(() => { tai(); }, []);
  const lam = (r: any, act: string) => {
    let v = r.ma_gd || '';
    Modal.confirm({ title: act === 'xacMinh' ? `Xác minh ${r.so} — đã thấy tiền trên sao kê?` : `Từ chối ${r.so}`,
      content: <Input defaultValue={v} placeholder={act === 'xacMinh' ? 'Mã giao dịch NH' : 'Lý do'} onChange={(e) => (v = e.target.value)} />,
      onOk: async () => { await goi(`phieu_thu:${act}`, { params: { filterByTk: r.id }, data: act === 'xacMinh' ? { ma_gd: v } : { ly_do: v } }); message.success('Xong'); tai(); } });
  };
  return <>
    <Typography.Paragraph type="secondary">Chuyển khoản khách / thu ngân báo — CHƯA vào tài khoản, CHƯA trừ nợ cho tới khi kế toán xác minh (hoặc khớp sao kê).</Typography.Paragraph>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Phiếu', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Khách', render: (_, r) => r.khach?.ten || 'Chưa rõ' },
      { title: 'Tài khoản', render: (_, r) => r.quy?.ten }, { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) }, { title: 'Mã GD', dataIndex: 'ma_gd' },
      { render: (_, r) => <Space><Button size="small" type="primary" onClick={() => lam(r, 'xacMinh')}>Xác minh</Button><Button size="small" danger onClick={() => lam(r, 'tuChoiXacMinh')}>Từ chối</Button></Space> },
    ]} />
  </>;
}

export function DoiSoatNH() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [quy, setQuy] = useState<any>(null);
  const [ds, setDs] = useState<any[]>([]);
  const [goiY, setGoiY] = useState<Record<string, any>>({});
  const [kq, setKq] = useState<any>(null);
  const tai = async () => {
    if (!quy) return;
    setDs((await goi('sao_ke_dong:list', { params: { filter: { quy_id: quy, trang_thai: 'chua_khop' }, sort: ['ngay', 'id'], pageSize: 500 } })).data || []);
    const g = await goi('sao_ke:goiY', { data: {}, im: true }).catch(() => ({ data: { goi_y: [] } }));
    setGoiY(Object.fromEntries((g.data?.goi_y || []).map((x: any) => [x.sao_ke_dong_id, x])));
  };
  useEffect(() => { tai(); }, [quy]);
  const nap = async (f: File) => {
    const r = await goi('sao_ke:nap', { data: { quy_id: quy, ten_tep: f.name, base64: await docB64(f) } });
    setKq(r.data); tai(); return false;
  };
  const taoThu = (d: any) => {
    let kh: any = null;
    Modal.confirm({ title: `Tạo phiếu thu ${fmt(d.so_tien)} từ sao kê`, content: <><div style={{ marginBottom: 6 }}>{d.noi_dung}</div>
      <ChonDanhMuc bang="khach_hang" value={undefined} onChange={(v) => (kh = v)} placeholder="Khách (trống = chưa rõ người nộp)" timTheo={['ma', 'ten', 'sdt', 'nhan']} /></>,
    onOk: async () => { await goi('sao_ke_dong:taoThu', { params: { filterByTk: d.id }, data: { khach_id: kh } }); message.success('Đã tạo phiếu thu'); tai(); } });
  };
  const boQua = (d: any) => {
    let ly = '';
    Modal.confirm({ title: 'Bỏ qua dòng sao kê', content: <Input onChange={(e) => (ly = e.target.value)} placeholder="Lý do (lãi NH, nội bộ, phí…)" />,
      onOk: async () => { await goi('sao_ke_dong:boQua', { params: { filterByTk: d.id }, data: { ly_do: ly } }); tai(); } });
  };
  return <>
    <Space wrap style={{ marginBottom: 8 }}>
      <ChonDanhMuc bang="quy" value={quy} onChange={setQuy} placeholder="Tài khoản ngân hàng" locThem={{ loai: 'ngan_hang' }} style={{ width: 300 }} />
      <Upload accept=".xlsx,.xls,.csv,.txt" showUploadList={false} beforeUpload={nap as any} disabled={!quy}><Button disabled={!quy}>Nạp sao kê (xlsx / csv)…</Button></Upload>
    </Space>
    {kq && <Alert style={{ marginBottom: 8 }} type="info" showIcon message={kq.da_nap_truoc ? 'Tệp này đã nạp trước đó — không thêm dòng.' : `Đọc ${kq.so_dong} dòng: mới ${kq.so_moi}, đã có ${kq.so_trung} (bỏ qua).`} />}
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) }, { title: 'Nội dung', dataIndex: 'noi_dung' },
      { title: 'Mã GD', dataIndex: 'ma_gd' },
      { title: 'Gợi ý', render: (_, d) => goiY[d.id] ? <Tag color="blue">{goiY[d.id].phieu_thu} (điểm {goiY[d.id].diem})</Tag> : '' },
      { render: (_, d) => <Space>
        {goiY[d.id] && <Button size="small" type="primary" onClick={async () => { await goi('sao_ke_dong:khop', { params: { filterByTk: d.id }, data: { phieu_thu_id: goiY[d.id].phieu_thu_id } }); tai(); }}>Khớp</Button>}
        <Button size="small" onClick={() => taoThu(d)}>Tạo phiếu thu</Button><Button size="small" danger onClick={() => boQua(d)}>Bỏ qua</Button></Space> },
    ]} />
  </>;
}

export function PhaiHoan() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('don_ban:list', { params: { filter: { phai_hoan: { $gt: 0 } }, appends: ['khach', 'don_vi_ban'], pageSize: 500 } })).data || []);
  useEffect(() => { tai(); }, []);
  const xl = (d: any) => {
    let cach = 'giu', ly = '', quy: any = null, ma = '';
    Modal.confirm({ width: 560, title: `Đơn ${d.so}: phải hoàn ${fmt(d.phai_hoan)} đ`, content: <Space direction="vertical" style={{ width: '100%' }}>
      <Radio.Group defaultValue="giu" onChange={(e) => (cach = e.target.value)} options={[{ value: 'giu', label: 'Giữ làm tiền chưa phân bổ của khách' }, { value: 'hoan', label: 'Hoàn tiền (phiếu chi)' }]} />
      <ChonDanhMuc bang="quy" value={undefined} onChange={(v) => (quy = v)} placeholder="Quỹ hoàn (nếu hoàn tiền)" locThem={{ don_vi_id: d.don_vi_ban_id }} />
      <Input placeholder="Mã GD (nếu hoàn qua NH)" onChange={(e) => (ma = e.target.value)} />
      <Input.TextArea placeholder="Căn cứ (biên bản trả hàng / thỏa thuận)" onChange={(e) => (ly = e.target.value)} /></Space>,
    onOk: async () => { await goi('don_ban:xuLyHoan', { params: { filterByTk: d.id }, data: { cach, ly_do: ly, quy_id: quy, ma_gd: ma } }); message.success('Xong'); tai(); } });
  };
  return <Table size="small" rowKey="id" dataSource={ds} columns={[
    { title: 'Đơn', dataIndex: 'so' }, { title: 'Khách', render: (_, d) => d.khach?.ten }, { title: 'Bên bán', render: (_, d) => d.don_vi_ban?.ma },
    { title: 'Phải hoàn', dataIndex: 'phai_hoan', align: 'right', render: (v) => <b style={{ color: '#cf1322' }}>{fmt(v)}</b> }, { render: (_, d) => <Button size="small" onClick={() => xl(d)}>Xử lý</Button> },
  ]} />;
}
