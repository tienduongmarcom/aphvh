/** Báo cáo (kế toán / quản lý): lãi gộp theo lượt đã xuất; hàng đợi hóa đơn MISA. */
import { App, Button, Card, DatePicker, Input, Segmented, Space, Table, Tabs, Typography } from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useState } from 'react';
import { fmt, homNay, ngayVN, useGoi } from './chung';

function LaiGop() {
  const goi = useGoi();
  const [theo, setTheo] = useState('don_vi');
  const [khoang, setKhoang] = useState<any>([dayjs(homNay()).startOf('month'), dayjs(homNay())]);
  const [ds, setDs] = useState<any[] | null>(null);
  const [loi, setLoi] = useState('');
  const tai = () => goi('don_ban:baoCao', { data: { theo, tu: khoang?.[0]?.format('YYYY-MM-DD'), den: khoang?.[1]?.format('YYYY-MM-DD') }, im: true })
    .then((r) => { setLoi(''); setDs(r.data || []); })
    .catch((e) => { setLoi(e?.response?.data?.errors?.[0]?.message || 'Không xem được'); setDs([]); });
  useEffect(() => { tai(); }, [theo, khoang?.[0]?.valueOf(), khoang?.[1]?.valueOf()]);
  if (loi) return <Typography.Text type="secondary">{loi}</Typography.Text>;
  const tong = (k: string) => (ds || []).reduce((s, r) => s + Number(r[k] || 0), 0);
  return <>
    <Space style={{ marginBottom: 12 }} wrap>
      <Segmented value={theo} onChange={(v: any) => setTheo(v)} options={[{ value: 'don_vi', label: 'Theo đơn vị' }, { value: 'khach', label: 'Theo khách' },
        { value: 'mat_hang', label: 'Theo mặt hàng' }, { value: 'ngay', label: 'Theo ngày' }]} />
      <DatePicker.RangePicker format="DD/MM/YYYY" value={khoang} onChange={setKhoang} />
    </Space>
    <Typography.Paragraph type="secondary">Tính trên các lượt đã xuất kho (bàn giao xe / khách nhận), giá vốn bình quân theo kho tại lúc xuất. Chưa trừ hàng trả và giảm giá sau bán.</Typography.Paragraph>
    <Table size="small" rowKey="nhom" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 100 }} columns={[
      { title: 'Nhóm', dataIndex: 'nhom', render: (v) => (theo === 'ngay' ? ngayVN(v) : v) },
      { title: 'Số lượng', dataIndex: 'so_luong', align: 'right', render: (v) => fmt(v, 3) },
      { title: 'Doanh số', dataIndex: 'doanh_so', align: 'right', render: (v) => fmt(v) },
      { title: 'Giá vốn', dataIndex: 'gia_von', align: 'right', render: (v) => fmt(v) },
      { title: 'Lãi gộp', align: 'right', render: (_, r) => <b>{fmt(Number(r.doanh_so || 0) - Number(r.gia_von || 0))}</b> },
      { title: 'Tỷ lệ', align: 'right', render: (_, r) => (Number(r.doanh_so) ? fmt(((r.doanh_so - r.gia_von) / r.doanh_so) * 100, 1) + '%' : '') },
    ]} summary={() => <Table.Summary.Row><Table.Summary.Cell index={0}><b>Cộng</b></Table.Summary.Cell><Table.Summary.Cell index={1} />
      <Table.Summary.Cell index={2} align="right"><b>{fmt(tong('doanh_so'))}</b></Table.Summary.Cell>
      <Table.Summary.Cell index={3} align="right"><b>{fmt(tong('gia_von'))}</b></Table.Summary.Cell>
      <Table.Summary.Cell index={4} align="right"><b>{fmt(tong('doanh_so') - tong('gia_von'))}</b></Table.Summary.Cell><Table.Summary.Cell index={5} /></Table.Summary.Row>} />
  </>;
}

function HoaDon() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [nhap, setNhap] = useState<Record<string, any>>({});
  const tai = async () => setDs((await goi('don_ban:list', { params: { filter: { trang_thai_hd: 'cho_xuat' }, appends: ['khach', 'don_vi_ban'], sort: ['ngay', 'id'], pageSize: 500 } })).data || []);
  useEffect(() => { tai(); }, []);
  const doi = (id: any, k: string, v: any) => setNhap({ ...nhap, [id]: { ...(nhap[id] || {}), [k]: v } });
  return <>
    <Typography.Paragraph type="secondary">Đơn đánh dấu "Xuất hóa đơn MISA" và đã giao. Xuất hóa đơn trên MISA xong thì nhập ký hiệu + số để đối chiếu (hệ thống chặn trùng số).</Typography.Paragraph>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Đơn', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
      { title: 'Đơn vị bán', render: (_, r) => r.don_vi_ban?.ten }, { title: 'Khách', render: (_, r) => <span>{r.khach?.ten}<div style={{ fontSize: 12, color: '#888' }}>MST {r.khach?.mst || '—'}</div></span> },
      { title: 'Giá trị đã giao', dataIndex: 'phai_thu', align: 'right', render: (v) => fmt(v) },
      { title: 'Ký hiệu', width: 130, render: (_, r) => <Input value={nhap[r.id]?.ky_hieu_hd} onChange={(e) => doi(r.id, 'ky_hieu_hd', e.target.value)} placeholder="1C26TAA" /> },
      { title: 'Số HĐ', width: 120, render: (_, r) => <Input value={nhap[r.id]?.so_hoa_don} onChange={(e) => doi(r.id, 'so_hoa_don', e.target.value)} /> },
      { title: 'Ngày HĐ', width: 150, render: (_, r) => <DatePicker format="DD/MM/YYYY" value={nhap[r.id]?.ngay_hd} onChange={(v) => doi(r.id, 'ngay_hd', v)} /> },
      { render: (_, r) => <Button size="small" type="primary" onClick={async () => {
        const n = nhap[r.id] || {};
        await goi('don_ban:ghiHoaDon', { params: { filterByTk: r.id }, data: { ...n, ngay_hd: n.ngay_hd?.format('YYYY-MM-DD') } });
        message.success('Đã ghi số hóa đơn'); tai();
      }}>Ghi</Button> },
    ]} />
  </>;
}

export function BaoCao() {
  return (
    <Card title="Báo cáo">
      <Tabs items={[{ key: 'lg', label: 'Lãi gộp', children: <LaiGop /> }, { key: 'hd', label: 'Hàng đợi hóa đơn MISA', children: <HoaDon /> }]} />
    </Card>
  );
}
