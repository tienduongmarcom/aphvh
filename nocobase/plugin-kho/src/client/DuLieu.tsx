/**
 * 0.4.0 Trung tâm dữ liệu: nạp sheet nhà máy + sổ bán hàng → ánh xạ mã → phân loại theo mốc Go-Live → ghép chuyến hai nguồn → ghi sổ có kiểm soát.
 * Không có nút "ghi tất cả bất chấp": chỉ bản ghi "Nhập được" và cặp ĐÃ XÁC NHẬN mới ghi; mỗi bản ghi giữ dòng nguồn + chứng từ đích.
 */
import { Alert, App, Button, Card, Checkbox, Collapse, Input, Modal, Segmented, Select, Space, Table, Tabs, Tag, Typography, Upload } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, ngayVN, useGoi } from './chung';

const KQ: Record<string, [string, string]> = { nhap_duoc: ['Nhập được', 'green'], chua_du: ['Chưa đủ căn cứ', 'orange'], co_the_trung: ['Có thể trùng', 'purple'],
  bi_chan: ['Bị chặn', 'red'], truoc_moc: ['Trước mốc (trong số dư)', 'default'], da_ghi: ['Đã ghi sổ', 'blue'], bo_qua: ['Bỏ qua', 'default'], chua_phan_loai: ['Chưa phân loại', 'default'] };
const NV: Record<string, string> = { nhan_hang: 'Nhận hàng NM', san_xuat: 'Sản xuất', chuyen_kho: 'Chuyển kho', ban_nm: 'Bán tại NM', ton_dau: 'Tồn đầu NM', kiem_ke: 'Kiểm kê',
  don_ban: 'Đơn bán', tra_lai: 'Trả lại', nhap_kho: 'Nhập kho', thu_tien: 'Thu tiền', ton_dau_bh: 'Tồn đầu (DM hàng)' };
const BANG_AX: Record<string, string> = { kho: 'kho', mat_hang: 'mat_hang', khach_hang: 'khach_hang', don_vi: 'don_vi', nha_cung_cap: 'nha_cung_cap', quy: 'quy' };
const docB64 = (f: File) => new Promise<string>((ok, hong) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1]); r.onerror = hong; r.readAsDataURL(f); });

function BaoCao({ lamMoi }: any) {
  const goi = useGoi();
  const [bc, setBc] = useState<any>(null);
  useEffect(() => { goi('nguon_tep:baoCao', { data: {} }).then((r) => setBc(r.data)); }, [lamMoi]);
  if (!bc) return null;
  const nhom: Record<string, any> = {};
  for (const r of bc.phan_loai) { const k = `${r.he_thong}|${r.loai_nv}`; nhom[k] = nhom[k] || { k, he: r.he_thong, nv: r.loai_nv }; nhom[k][r.ket_qua] = r.n; }
  return <>
    <Space style={{ marginBottom: 8 }}><Tag>Ánh xạ: {bc.anh_xa.da} đã đặt / <b>{bc.anh_xa.chua}</b> chưa</Tag><Tag>Cặp ghép: {bc.ghep.de_xuat} đề xuất · {bc.ghep.xac_nhan} xác nhận · {bc.ghep.bac_bo} bác bỏ</Tag></Space>
    <Table size="small" rowKey="k" pagination={false} dataSource={Object.values(nhom)} columns={[
      { title: 'Nguồn', dataIndex: 'he', render: (v) => (v === 'nha_may' ? 'Sheet nhà máy' : 'Sổ bán hàng') }, { title: 'Nghiệp vụ', dataIndex: 'nv', render: (v) => NV[v] || v },
      ...Object.keys(KQ).map((k) => ({ title: KQ[k][0], dataIndex: k, align: 'right' as const, render: (v: any) => v || '' })),
    ]} />
    <Typography.Title level={5} style={{ marginTop: 12 }}>Vấn đề thường gặp</Typography.Title>
    <Table size="small" rowKey="van_de" pagination={{ pageSize: 15 }} dataSource={bc.van_de_thuong_gap} columns={[{ title: 'Vấn đề', dataIndex: 'van_de' }, { title: 'Số dòng', dataIndex: 'n', align: 'right' }]} />
  </>;
}

function AnhXa() {
  const goi = useGoi();
  const [loai, setLoai] = useState('kho');
  const [chua, setChua] = useState(true);
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('anh_xa_ma:list', { params: { filter: { loai, ...(chua ? { dich_id: { $in: [0, null] } } : {}) }, sort: ['ma_nguon'], pageSize: 500 } })).data || []);
  useEffect(() => { tai(); }, [loai, chua]);
  return <>
    <Space style={{ marginBottom: 8 }}>
      <Segmented value={loai} onChange={(v: any) => setLoai(v)} options={[{ value: 'kho', label: 'Kho' }, { value: 'mat_hang', label: 'Mặt hàng' }, { value: 'khach_hang', label: 'Khách' },
        { value: 'don_vi', label: 'Công ty' }, { value: 'quy', label: 'Quỹ / TK' }, { value: 'nha_cung_cap', label: 'NCC' }]} />
      <Checkbox checked={chua} onChange={(e) => setChua(e.target.checked)}>Chỉ mã chưa ánh xạ</Checkbox>
    </Space>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Nguồn', dataIndex: 'he_thong' }, { title: 'Mã / tên ở nguồn', dataIndex: 'ma_nguon' }, { title: 'Tên ở nguồn', dataIndex: 'ten_nguon' },
      { title: 'Mã đích trên hệ thống', width: 340, render: (_, r) => <ChonDanhMuc bang={BANG_AX[r.loai]} value={r.dich_id || undefined} style={{ width: 320 }}
        onChange={async (v) => { await goi('anh_xa_ma:dat', { params: { filterByTk: r.id }, data: { dich_id: v, bo_trong: !v } }); tai(); }} /> },
      { title: 'Ghi chú', dataIndex: 'ghi_chu' },
    ]} />
  </>;
}

function BanGhi() {
  const goi = useGoi();
  const [kq, setKq] = useState('chua_du');
  const [nv, setNv] = useState<any>(null);
  const [ds, setDs] = useState<any[]>([]);
  const [tong, setTong] = useState(0);
  const [trang, setTrang] = useState(1);
  const tai = async () => {
    const r = await goi('nguon_ban_ghi:list', { params: { filter: { ket_qua: kq, ...(nv ? { loai_nv: nv } : {}) }, sort: ['ngay', 'id'], page: trang, pageSize: 50 } });
    setDs(r.data || []); setTong(r.meta?.count || 0);
  };
  useEffect(() => { tai(); }, [kq, nv, trang]);
  return <>
    <Space style={{ marginBottom: 8 }} wrap>
      <Segmented value={kq} onChange={(v: any) => { setTrang(1); setKq(v); }} options={Object.entries(KQ).filter(([k]) => k !== 'chua_phan_loai').map(([k, v]) => ({ value: k, label: v[0] }))} />
      <Select allowClear placeholder="Nghiệp vụ" style={{ width: 180 }} value={nv} onChange={setNv} options={Object.entries(NV).map(([k, v]) => ({ value: k, label: v }))} />
    </Space>
    <Table size="small" rowKey="id" dataSource={ds} pagination={{ current: trang, total: tong, pageSize: 50, onChange: setTrang }} columns={[
      { title: 'Nguồn', render: (_, r) => `${r.he_thong === 'nha_may' ? 'NM' : 'BH'} · ${r.trang_tinh} #${r.dong}` }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
      { title: 'Số CT', dataIndex: 'so_ct' }, { title: 'Nghiệp vụ', dataIndex: 'loai_nv', render: (v) => NV[v] || v },
      { title: 'Dữ liệu', render: (_, r) => <Typography.Text style={{ fontSize: 12 }}>{Object.entries(JSON.parse(r.du_lieu || '{}')).filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`).join(' · ').slice(0, 220)}</Typography.Text> },
      { title: 'Vấn đề', dataIndex: 'van_de' }, { title: 'Chứng từ', dataIndex: 'chung_tu_dich' },
      { render: (_, r) => !['da_ghi', 'bo_qua'].includes(r.ket_qua) && <Button size="small" danger onClick={() => {
        let ly = '';
        Modal.confirm({ title: 'Bỏ qua bản ghi nguồn', content: <Input onChange={(e) => (ly = e.target.value)} placeholder="Lý do (trùng / sai / đã có trong số dư…)" />,
          onOk: async () => { await goi('nguon_ban_ghi:boQua', { params: { filterByTk: r.id }, data: { ly_do: ly } }); tai(); } });
      }}>Bỏ qua</Button> },
    ]} />
  </>;
}

function GhepCap() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('khop_chung_tu:list', { params: { filter: { trang_thai: 'de_xuat' }, appends: ['ban_ghi_a', 'ban_ghi_b'], sort: ['-diem'], pageSize: 500 } })).data || []);
  useEffect(() => { tai(); }, []);
  const tom = (b: any) => { const d = JSON.parse(b?.du_lieu || '{}'); return `${ngayVN(b?.ngay)} ${b?.so_ct || ''} · ${d.kho_di || d.kho || ''} → ${d.kho_den || ''} · ${d.ma_hang || ''} · ${d.so_kg || d.so_luong || ''}`; };
  return <Table size="small" rowKey="id" dataSource={ds} columns={[
    { title: 'Bản ghi A (đầu xuất)', render: (_, r) => <span>{r.ban_ghi_a?.he_thong === 'nha_may' ? 'NM' : 'BH'}: {tom(r.ban_ghi_a)}</span> },
    { title: 'Bản ghi B (đầu nhận)', render: (_, r) => <span>{r.ban_ghi_b?.he_thong === 'nha_may' ? 'NM' : 'BH'}: {tom(r.ban_ghi_b)}</span> },
    { title: 'Căn cứ', dataIndex: 'ly_do' }, { title: 'Điểm', dataIndex: 'diem' },
    { render: (_, r) => <Space><Button size="small" type="primary" onClick={async () => { await goi('khop_chung_tu:xacNhan', { params: { filterByTk: r.id }, data: {} }); tai(); }}>Là một chuyến</Button>
      <Button size="small" danger onClick={async () => { await goi('khop_chung_tu:bacBo', { params: { filterByTk: r.id }, data: {} }); tai(); }}>Không phải</Button></Space> },
  ]} />;
}

export function DuLieu() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [he, setHe] = useState('nha_may');
  const [moc, setMoc] = useState('');
  const [lm, setLm] = useState(0);
  const [kq, setKq] = useState<any>(null);
  const [loaiGhi, setLoaiGhi] = useState<string[]>(['chuyen_ghep', 'chuyen_kho', 'nhap_kho', 'nhan_hang', 'san_xuat']);
  useEffect(() => { goi('cau_hinh:list', { params: { filter: { khoa: 'ngay_moc_golive' } }, im: true }).then((r) => setMoc(r.data?.[0]?.gia_tri || '')).catch(() => null); }, []);
  const nap = async (f: File) => {
    const r = await goi('nguon_tep:nap', { data: { he_thong: he, ten_tep: f.name, base64: await docB64(f) } });
    setKq({ nap: r.data }); setLm(lm + 1); return false;
  };
  return <Card title="Trung tâm dữ liệu (Go-Live hai nguồn)">
    <Alert type="info" showIcon style={{ marginBottom: 12 }} message="Thứ tự: 1) Nạp hai tệp → 2) Ánh xạ mã → 3) Phân loại theo mốc → 4) Xác nhận cặp chuyến → 5) Ghi sổ. Bản ghi trước mốc nằm trong số dư đầu kỳ (không ghi lại phát sinh)." />
    <Space wrap style={{ marginBottom: 12 }}>
      <Segmented value={he} onChange={(v: any) => setHe(v)} options={[{ value: 'nha_may', label: 'Sheet nhà máy Phú Thọ' }, { value: 'ban_hang', label: 'Sổ bán hàng – kho – công nợ' }]} />
      <Upload accept=".xlsx,.xls,.csv,.txt" showUploadList={false} beforeUpload={nap as any}><Button type="primary">1. Nạp tệp…</Button></Upload>
      <Input type="date" value={moc} onChange={(e) => setMoc(e.target.value)} style={{ width: 160 }} />
      <Button onClick={async () => { const r = await goi('nguon_tep:phanLoai', { data: { moc } }); setKq({ phan_loai: r.data }); setLm(lm + 1); }}>3. Phân loại theo mốc</Button>
      <Button onClick={async () => { const r = await goi('nguon_tep:taoLoTon', { data: {} }); message.success(`Đã tạo lô tồn đầu (${r.data.so_dong} dòng) — duyệt ở Go-Live`); setKq({ lo_ton: r.data }); }}>Tạo lô tồn đầu kỳ</Button>
    </Space>
    <Space wrap style={{ marginBottom: 12 }}>
      <Select mode="multiple" style={{ minWidth: 420 }} value={loaiGhi} onChange={setLoaiGhi} options={[{ value: 'chuyen_ghep', label: 'Chuyến ghép hai nguồn' }, { value: 'chuyen_kho', label: 'Chuyển nội bộ / xuất khác' },
        { value: 'nhap_kho', label: 'Nhập kho (BH)' }, { value: 'nhan_hang', label: 'Nhận hàng (NM)' }, { value: 'san_xuat', label: 'Sản xuất' }, { value: 'ban_nm', label: 'Bán tại NM' },
        { value: 'don_ban', label: 'Đơn bán' }, { value: 'thu_tien', label: 'Thu tiền' }, { value: 'tra_lai', label: 'Trả lại' }]} />
      <Button type="primary" danger onClick={async () => { const r = await goi('nguon_tep:ghiSo', { data: { loai_nv: loaiGhi, gioi_han: 200 } }); setKq({ ghi: r.data }); setLm(lm + 1); }}>5. Ghi sổ (tối đa 200 nhóm / lần)</Button>
    </Space>
    {kq && <Collapse style={{ marginBottom: 12 }} items={[{ key: '1', label: 'Kết quả lần chạy gần nhất', children: <pre style={{ fontSize: 12, maxHeight: 300, overflow: 'auto' }}>{JSON.stringify(kq, null, 1)}</pre> }]} />}
    <Tabs items={[{ key: 'bc', label: 'Tổng hợp', children: <BaoCao lamMoi={lm} /> }, { key: 'ax', label: '2. Ánh xạ mã', children: <AnhXa /> },
      { key: 'gh', label: '4. Cặp chuyến hai nguồn', children: <GhepCap key={lm} /> }, { key: 'bg', label: 'Bản ghi nguồn', children: <BanGhi key={lm} /> }]} />
  </Card>;
}
