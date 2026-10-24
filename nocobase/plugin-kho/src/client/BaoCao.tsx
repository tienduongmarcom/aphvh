/** Báo cáo (kế toán / quản lý): lãi gộp theo lượt đã xuất; hàng đợi hóa đơn MISA. */
import { Alert, App, Button, Card, DatePicker, Input, Segmented, Space, Table, Tabs, Typography } from 'antd';
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
  const [tam, setTam] = useState<string[]>([]);
  useEffect(() => {
    Promise.all([goi('me_sx:list', { params: { filter: { trang_thai: { $in: ['mo', 'can_chot_lai'] } }, pageSize: 1 }, im: true }).catch(() => ({ meta: { count: 0 } })),
      goi('phieu_kho_dong:list', { params: { filter: { trang_thai_gia: 'tam' }, pageSize: 1 }, im: true }).catch(() => ({ meta: { count: 0 } })),
      goi('phieu_kho_dong:list', { params: { filter: { trang_thai_gia: 'cho_gia', 'phieu_kho.trang_thai': 'da_ghi' }, pageSize: 1 }, im: true }).catch(() => ({ meta: { count: 0 } }))])
      .then(([a, b, c]: any) => setTam([a.meta?.count ? `${a.meta.count} mẻ sản xuất chưa chốt / cần chốt lại giá thành` : '',
        b.meta?.count ? `${b.meta.count} dòng hàng đang giá tạm` : '', c.meta?.count ? `${c.meta.count} dòng hàng chờ định giá` : ''].filter(Boolean)));
  }, []);
  if (loi) return <Typography.Text type="secondary">{loi}</Typography.Text>;
  const tong = (k: string) => (ds || []).filter((r) => !r.chua_xac_dinh).reduce((s, r) => s + Number(r[k] || 0), 0);
  return <>
    <Space style={{ marginBottom: 12 }} wrap>
      <Segmented value={theo} onChange={(v: any) => setTheo(v)} options={[{ value: 'don_vi', label: 'Theo đơn vị' }, { value: 'khach', label: 'Theo khách' },
        { value: 'mat_hang', label: 'Theo mặt hàng' }, { value: 'ngay', label: 'Theo ngày' }]} />
      <DatePicker.RangePicker format="DD/MM/YYYY" value={khoang} onChange={setKhoang} />
    </Space>
    {(ds || []).some((r: any) => r.chua_xac_dinh) && <Alert type="error" showIcon style={{ marginBottom: 12 }} message="Có doanh số chuyển tiếp CHƯA CÓ GIÁ VỐN: đã tách riêng, không tính vào lãi gộp. Kế toán nhập giá vốn ở lượt giao của đơn." />}
    {tam.length > 0 && <Alert type="warning" showIcon style={{ marginBottom: 12 }} message="Lãi gộp TẠM TÍNH — chưa phải số chốt" description={tam.join(' · ')} />}
    <Typography.Paragraph type="secondary">Tính trên các lượt đã xuất kho (bàn giao xe / khách nhận), giá vốn bình quân theo kho tại lúc xuất. Lãi gộp THUẦN: đã trừ hàng trả, giảm giá sau bán và cộng điều chỉnh giá vốn (giá thành / giá tạm của hàng đã xuất). Lượt chuyển tiếp chưa có giá vốn tách riêng, không tính lãi.</Typography.Paragraph>
    <Table size="small" rowKey="nhom" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 100 }} columns={[
      { title: 'Nhóm', dataIndex: 'nhom', render: (v) => (theo === 'ngay' ? ngayVN(v) : v) },
      { title: 'Số lượng', dataIndex: 'so_luong', align: 'right', render: (v) => fmt(v, 3) },
      { title: 'Doanh số', dataIndex: 'doanh_so', align: 'right', render: (v) => fmt(v) },
      { title: 'Giá vốn', dataIndex: 'gia_von', align: 'right', render: (v) => fmt(v) },
      { title: 'Lãi gộp', align: 'right', render: (_, r) => (r.chua_xac_dinh ? <span style={{ color: '#cf1322' }}>không tính</span> : <b>{fmt(Number(r.doanh_so || 0) - Number(r.gia_von || 0))}</b>) },
      { title: 'Tỷ lệ', align: 'right', render: (_, r) => (!r.chua_xac_dinh && Number(r.doanh_so) ? fmt(((r.doanh_so - r.gia_von) / r.doanh_so) * 100, 1) + '%' : '') },
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

function TuoiNo() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[] | null>(null);
  useEffect(() => {
    goi('don_ban:list', { params: { filter: { trang_thai: { $in: ['dang_giao', 'da_giao', 'da_dong'] }, con_no: { $gt: 0 } }, appends: ['khach', 'don_vi_ban'], pageSize: 10000 } }).then((r) => {
      const hn = new Date(homNay()).getTime();
      const m: Record<string, any> = {};
      for (const d of r.data || []) {
        const han = d.han_tt || d.ngay_giao || d.ngay;
        const qua = Math.floor((hn - new Date(han).getTime()) / 86400000);
        const nhom = qua <= 0 ? 'chua' : qua <= 30 ? 'd30' : qua <= 60 ? 'd60' : qua <= 90 ? 'd90' : 'tren90';
        const k = `${d.khach_id}-${d.don_vi_ban_id}`;
        m[k] = m[k] || { k, khach: d.khach, dv: d.don_vi_ban, chua: 0, d30: 0, d60: 0, d90: 0, tren90: 0, tong: 0 };
        m[k][nhom] += Number(d.con_no); m[k].tong += Number(d.con_no);
      }
      setDs(Object.values(m).sort((a: any, b: any) => b.tren90 - a.tren90 || b.tong - a.tong));
    }).catch(() => setDs([]));
  }, []);
  const c = (k: string, t: string) => ({ title: t, dataIndex: k, align: 'right' as const, render: (v: number) => (v ? fmt(v) : '') });
  const tong = (k: string) => (ds || []).reduce((s, r) => s + r[k], 0);
  return <>
    <Typography.Paragraph type="secondary">Tính từ hạn thanh toán (nợ đầu kỳ có hạn) hoặc ngày giao. Theo khách × đơn vị, không cấn chéo đơn vị.</Typography.Paragraph>
    <Table size="small" rowKey="k" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 100 }} columns={[
      { title: 'Khách', render: (_, r) => <span><b>{r.khach?.ten}</b><div style={{ fontSize: 12, color: '#888' }}>{r.khach?.ma}</div></span> },
      { title: 'Đơn vị', render: (_, r) => r.dv?.ma }, c('chua', 'Chưa đến hạn'), c('d30', 'Quá 1–30 ngày'), c('d60', '31–60'), c('d90', '61–90'),
      { ...c('tren90', 'Trên 90 ngày'), render: (v: number) => (v ? <b style={{ color: '#cf1322' }}>{fmt(v)}</b> : '') }, { ...c('tong', 'Tổng còn nợ'), render: (v: number) => <b>{fmt(v)}</b> },
    ]} summary={() => <Table.Summary.Row><Table.Summary.Cell index={0} colSpan={2}><b>Cộng</b></Table.Summary.Cell>
      {['chua', 'd30', 'd60', 'd90', 'tren90', 'tong'].map((k, i) => <Table.Summary.Cell key={k} index={i + 2} align="right"><b>{fmt(tong(k))}</b></Table.Summary.Cell>)}</Table.Summary.Row>} />
  </>;
}

export function BaoCao() {
  return (
    <Card title="Báo cáo">
      <Tabs items={[{ key: 'lg', label: 'Lãi gộp', children: <LaiGop /> }, { key: 'tn', label: 'Tuổi nợ khách', children: <TuoiNo /> },
      { key: 'hd', label: 'Hàng đợi hóa đơn MISA', children: <HoaDon /> }]} />
    </Card>
  );
}
