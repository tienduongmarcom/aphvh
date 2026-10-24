/**
 * 0.4.0 Chuyển hàng hai đầu (nhà máy ↔ kho bán hàng) qua kho "Hàng đang vận chuyển"; chênh lệch giao – nhận chờ xử lý.
 * Nhập nhanh phiếu sản xuất + hàng đợi rà soát (phiếu thiếu mã / lệch cân bằng).
 */
import { Alert, App, Button, Drawer, Input, InputNumber, Modal, Segmented, Select, Space, Table, Tag, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, fmt, homNay, ngayVN, useGoi } from './chung';

const TT_CH: Record<string, [string, string]> = { nhap: ['Nháp', 'default'], da_xuat: ['Đang đi đường', 'orange'], da_nhan: ['Đã nhận đủ', 'green'],
  co_chenh_lech: ['Có chênh lệch chờ xử lý', 'red'], da_huy: ['Đã hủy', 'red'] };
const rid = () => (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`);

function LapChuyen({ xong }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [v, setV] = useState<any>({ ngay: homNay() });
  const [dong, setDong] = useState<any[]>([{}]);
  const [req] = useState(rid());
  const luu = async () => {
    const r = await goi('chuyen_hang:create', { params: { 'updateAssociationValues[]': 'dong' }, data: { ...v, request_id: req,
      dong: dong.filter((d) => d.mat_hang_id && d.so_kg > 0).map((d) => ({ mat_hang_id: d.mat_hang_id, so_kg: d.so_kg, so_bao: d.so_bao ?? null, so_lo: d.so_lo || null })) } });
    message.success(`Đã lưu ${r.data.so}`);
    xong(r.data.id);
  };
  return <>
    <Space wrap style={{ marginBottom: 8 }}>
      <ChonDanhMuc bang="kho" value={v.kho_di_id} onChange={(x) => setV({ ...v, kho_di_id: x })} placeholder="Kho đi" />
      <ChonDanhMuc bang="kho" value={v.kho_den_id} onChange={(x) => setV({ ...v, kho_den_id: x })} placeholder="Kho đến" />
      <ChonDanhMuc bang="kho" value={v.kho_tg_id} onChange={(x) => setV({ ...v, kho_tg_id: x })} placeholder="Kho đang vận chuyển (trống = mặc định)" locThem={{ trung_chuyen: true }} />
      <Input placeholder="Xe / biển số" value={v.xe} onChange={(e) => setV({ ...v, xe: e.target.value })} style={{ width: 150 }} />
      <Input placeholder="Người giao" value={v.nguoi_giao} onChange={(e) => setV({ ...v, nguoi_giao: e.target.value })} style={{ width: 150 }} />
    </Space>
    <Table size="small" rowKey={(_, i) => String(i)} pagination={false} dataSource={dong} columns={[
      { title: 'Mặt hàng', render: (_, d, i) => <ChonDanhMuc bang="mat_hang" value={d.mat_hang_id} style={{ width: 280 }} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, mat_hang_id: x } : y)))} /> },
      { title: 'Số lượng', render: (_, d, i) => <InputNumber min={0} value={d.so_kg} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, so_kg: x } : y)))} /> },
      { title: 'Bao', render: (_, d, i) => <InputNumber min={0} value={d.so_bao} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, so_bao: x } : y)))} /> },
      { title: 'Lô', render: (_, d, i) => <Input value={d.so_lo} onChange={(e) => setDong(dong.map((y, j) => (j === i ? { ...y, so_lo: e.target.value } : y)))} /> },
    ]} />
    <Space style={{ marginTop: 8 }}><Button onClick={() => setDong([...dong, {}])}>+ Dòng</Button><Button type="primary" onClick={luu}>Lưu nháp</Button></Space>
  </>;
}

function XemChuyen({ id, xong }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ch, setCh] = useState<any>(null);
  const [nhan, setNhan] = useState<Record<string, any>>({});
  const [lyDo, setLyDo] = useState('');
  const [cl, setCl] = useState<any[]>([]);
  const tai = async () => {
    setCh((await goi('chuyen_hang:get', { params: { filterByTk: id, appends: ['dong', 'dong.mat_hang', 'kho_di', 'kho_den', 'kho_tg'] } })).data);
    setCl((await goi('chenh_lech_giao_nhan:list', { params: { filter: { chuyen_hang_id: id }, appends: ['mat_hang'] }, im: true }).catch(() => ({ data: [] }))).data || []);
  };
  useEffect(() => { tai(); }, [id]);
  if (!ch) return null;
  const lam = async (act: string, data: any = {}) => { await goi(`chuyen_hang:${act}`, { params: { filterByTk: id }, data }); message.success('Xong'); tai(); xong(); };
  const xuLy = (c: any) => {
    let cach = 'hao_hut', ly = '';
    Modal.confirm({ title: `Xử lý chênh lệch ${fmt(c.so_kg, 3)} ${c.mat_hang?.ma}`, content: <Space direction="vertical">
      <Select defaultValue="hao_hut" style={{ width: 280 }} onChange={(v) => (cach = v)} options={[{ value: 'hao_hut', label: 'Hao hụt (duyệt)' },
        { value: 'nhan_bo_sung', label: 'Tìm thấy — nhận bổ sung vào kho đến' }, { value: 'tra_ve', label: 'Trả về kho đi' }, { value: 'boi_thuong', label: 'Bồi thường' }]} />
      <Input.TextArea placeholder="Lý do / số biên bản" onChange={(e) => (ly = e.target.value)} /></Space>,
    onOk: async () => { await goi('chenh_lech_giao_nhan:xuLy', { params: { filterByTk: c.id }, data: { cach_xu_ly: cach, ly_do: ly } }); tai(); xong(); } });
  };
  return <>
    <Typography.Paragraph><b>{ch.so}</b> · {ngayVN(ch.ngay)} · {ch.kho_di?.ten} → <i>{ch.kho_tg?.ten || 'đang vận chuyển'}</i> → {ch.kho_den?.ten} · {ch.xe}
      {' '}<Tag color={TT_CH[ch.trang_thai]?.[1]}>{TT_CH[ch.trang_thai]?.[0]}</Tag></Typography.Paragraph>
    <Table size="small" rowKey="id" pagination={false} dataSource={(ch.dong || []) as any[]} columns={[
      { title: 'Hàng', render: (_, d) => `${d.mat_hang?.ma} ${d.mat_hang?.ten}` }, { title: 'Xuất', align: 'right', render: (_, d) => `${fmt(d.so_kg, 3)} / ${fmt(d.so_bao, 2)} bao` },
      { title: 'Thực nhận', render: (_, d) => ch.trang_thai === 'da_xuat'
        ? <Space><InputNumber placeholder={String(d.so_kg)} value={nhan[d.id]?.so_kg} onChange={(v) => setNhan({ ...nhan, [d.id]: { ...nhan[d.id], so_kg: v } })} />
          <InputNumber placeholder="bao" value={nhan[d.id]?.so_bao} onChange={(v) => setNhan({ ...nhan, [d.id]: { ...nhan[d.id], so_bao: v } })} /></Space>
        : d.so_kg_nhan !== null && d.so_kg_nhan !== undefined ? fmt(d.so_kg_nhan, 3) : '' },
    ]} />
    <Space style={{ marginTop: 8 }} wrap>
      {ch.trang_thai === 'nhap' && <Button type="primary" onClick={() => lam('xacNhanXuat')}>Xác nhận xuất (đầu đi)</Button>}
      {ch.trang_thai === 'da_xuat' && <><Input placeholder="Lý do nếu nhận lệch" value={lyDo} onChange={(e) => setLyDo(e.target.value)} style={{ width: 260 }} />
        <Button type="primary" onClick={() => lam('xacNhanNhan', { nhan, ly_do: lyDo })}>Xác nhận nhận (đầu đến)</Button></>}
      <Button onClick={() => window.open(`/in/chuyen_hang/${id}`, '_blank')}>In phiếu chuyển</Button>
    </Space>
    {cl.length > 0 && <><Typography.Title level={5} style={{ marginTop: 16 }}>Chênh lệch giao – nhận</Typography.Title>
      <Table size="small" rowKey="id" pagination={false} dataSource={cl} columns={[
        { title: 'Hàng', render: (_, c) => c.mat_hang?.ma }, { title: 'Chênh', align: 'right', render: (_, c) => fmt(c.so_kg, 3) },
        { title: 'Trạng thái', render: (_, c) => (c.trang_thai === 'cho_xu_ly' ? <Tag color="orange">Chờ xử lý</Tag> : <Tag color="green">{c.cach_xu_ly}</Tag>) },
        { title: 'Lý do', dataIndex: 'ly_do' }, { render: (_, c) => c.trang_thai === 'cho_xu_ly' && <Button size="small" onClick={() => xuLy(c)}>Xử lý</Button> },
      ]} /></>}
  </>;
}

export function ChuyenHang() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [loc, setLoc] = useState('mo');
  const [mo, setMo] = useState<any>(null);
  const tai = async () => setDs((await goi('chuyen_hang:list', { params: { filter: loc === 'mo' ? { trang_thai: { $in: ['nhap', 'da_xuat', 'co_chenh_lech'] } } : {},
    appends: ['kho_di', 'kho_den'], sort: ['-id'], pageSize: 100 } })).data || []);
  useEffect(() => { tai(); }, [loc]);
  return <>
    <Space style={{ marginBottom: 8 }}><Button type="primary" onClick={() => setMo('moi')}>+ Chuyến chuyển hàng</Button>
      <Segmented value={loc} onChange={(v: any) => setLoc(v)} options={[{ value: 'mo', label: 'Đang xử lý' }, { value: 'tat_ca', label: 'Tất cả' }]} /></Space>
    <Table size="small" rowKey="id" dataSource={ds} onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Số', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Đi', render: (_, r) => r.kho_di?.ten }, { title: 'Đến', render: (_, r) => r.kho_den?.ten },
      { title: 'Xe', dataIndex: 'xe' }, { title: 'Nguồn', dataIndex: 'nguon' },
      { title: 'Trạng thái', render: (_, r) => <Tag color={TT_CH[r.trang_thai]?.[1]}>{TT_CH[r.trang_thai]?.[0]}</Tag> },
    ]} />
    <Drawer width="80%" open={!!mo} onClose={() => { setMo(null); tai(); }} destroyOnClose title="Chuyển hàng">
      {mo === 'moi' ? <LapChuyen xong={setMo} /> : mo && <XemChuyen id={mo} xong={tai} />}
    </Drawer>
  </>;
}

/** Nhập nhanh một phiếu sản xuất (nhà máy): NVL vào / thành phẩm / phụ phẩm / hao hụt — không hiển thị giá. */
function NhapNhanhSX({ xong }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [v, setV] = useState<any>({ ngay: homNay() });
  const [dong, setDong] = useState<any[]>([{ nhom: 'nvl' }, { nhom: 'tp' }]);
  const gui = async () => {
    const lay = (n: string) => dong.filter((d) => d.nhom === n && (d.mat_hang_id || d.so_kg)).map((d) => ({ mat_hang_id: d.mat_hang_id, so_kg: d.so_kg, so_bao: d.so_bao,
      ...(n === 'phu_pham' ? { don_gia: 0 } : {}), ...(n === 'hao' ? { loai_hao: d.loai_hao || 'tu_nhien' } : {}) }));
    const r = await goi('me_sx:nhapNhanh', { data: { ...v, nvl: lay('nvl'), tp: lay('tp'), phu_pham: lay('phu_pham'), hao: lay('hao') } });
    if (r.data.ok) message.success(`Đã tạo mẻ ${r.data.so} (vào ${fmt(r.data.kg_vao, 3)} kg / ra ${fmt(r.data.kg_ra, 3)} kg)`);
    else message.warning(`Phiếu vào hàng đợi rà soát: ${r.data.van_de.join('; ')}`, 8);
    xong();
  };
  return <>
    <Space wrap style={{ marginBottom: 8 }}>
      <Input placeholder="Số phiếu SX" value={v.so_phieu} onChange={(e) => setV({ ...v, so_phieu: e.target.value })} style={{ width: 140 }} />
      <Input type="date" value={v.ngay} onChange={(e) => setV({ ...v, ngay: e.target.value })} style={{ width: 150 }} />
      <Input placeholder="Dây chuyền / xưởng" value={v.xuong} onChange={(e) => setV({ ...v, xuong: e.target.value })} style={{ width: 180 }} />
      <ChonDanhMuc bang="kho" value={v.kho_id} onChange={(x) => setV({ ...v, kho_id: x })} placeholder="Kho lấy NVL (kho mẻ)" />
      <ChonDanhMuc bang="kho" value={v.kho_tp_id} onChange={(x) => setV({ ...v, kho_tp_id: x })} placeholder="Kho nhận thành phẩm" />
    </Space>
    <Table size="small" rowKey={(_, i) => String(i)} pagination={false} dataSource={dong} columns={[
      { title: 'Dòng', width: 140, render: (_, d, i) => <Select value={d.nhom} style={{ width: 130 }} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, nhom: x } : y)))}
        options={[{ value: 'nvl', label: 'Đầu vào' }, { value: 'tp', label: 'Thành phẩm' }, { value: 'phu_pham', label: 'Phụ phẩm' }, { value: 'hao', label: 'Hao hụt' }]} /> },
      { title: 'Mặt hàng', render: (_, d, i) => <ChonDanhMuc bang="mat_hang" value={d.mat_hang_id} style={{ width: 280 }} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, mat_hang_id: x } : y)))} /> },
      { title: 'Số kg / số lượng', render: (_, d, i) => <InputNumber min={0} value={d.so_kg} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, so_kg: x } : y)))} /> },
      { title: 'Bao', render: (_, d, i) => <InputNumber min={0} value={d.so_bao} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, so_bao: x } : y)))} /> },
      { title: 'Hao hụt', render: (_, d, i) => d.nhom === 'hao' && <Select value={d.loai_hao || 'tu_nhien'} style={{ width: 130 }} onChange={(x) => setDong(dong.map((y, j) => (j === i ? { ...y, loai_hao: x } : y)))}
        options={[{ value: 'tu_nhien', label: 'Tự nhiên' }, { value: 'bat_thuong', label: 'Bất thường' }]} /> },
      { width: 40, render: (_, __, i) => <Button size="small" danger onClick={() => setDong(dong.filter((_, j) => j !== i))}>×</Button> },
    ]} />
    <Space style={{ marginTop: 8 }}><Button onClick={() => setDong([...dong, { nhom: 'nvl' }])}>+ Dòng</Button><Button type="primary" onClick={gui}>Ghi phiếu sản xuất</Button></Space>
    <Typography.Paragraph type="secondary" style={{ marginTop: 6 }}>Thiếu mã hàng, thiếu số lượng hoặc lệch cân bằng kg vượt ngưỡng: phiếu vào "Cần rà soát", không ghi sổ, không tự sinh đầu vào.</Typography.Paragraph>
  </>;
}

export function RaSoatSX() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [moi, setMoi] = useState(false);
  const tai = async () => setDs((await goi('sx_ra_soat:list', { params: { filter: { trang_thai: { $in: ['cho_bo_sung', 'du_dieu_kien'] } }, sort: ['ngay', 'id'], pageSize: 200 } })).data || []);
  useEffect(() => { tai(); }, []);
  const boSung = (r: any) => {
    const d = JSON.parse(r.du_lieu || '{}');
    let txt = JSON.stringify({ nvl: d.nvl, tp: d.tp, phu_pham: d.phu_pham, hao: d.hao, kho_id: d.kho_id, kho_tp_id: d.kho_tp_id }, null, 1);
    Modal.confirm({ width: 720, title: `Bổ sung phiếu ${r.so_phieu}`, content: <><Alert type="warning" message={r.van_de} style={{ marginBottom: 8 }} />
      <Input.TextArea rows={14} defaultValue={txt} onChange={(e) => (txt = e.target.value)} /><Typography.Text type="secondary">Điền mat_hang_id cho dòng thiếu mã (tra ở Danh mục).</Typography.Text></>,
    onOk: async () => { await goi('sx_ra_soat:boSung', { params: { filterByTk: r.id }, data: JSON.parse(txt) }); tai(); } });
  };
  const boQua = (r: any) => {
    let ly = '';
    Modal.confirm({ title: `Bỏ qua phiếu ${r.so_phieu}`, content: <Input onChange={(e) => (ly = e.target.value)} placeholder="Lý do" />,
      onOk: async () => { await goi('sx_ra_soat:boQua', { params: { filterByTk: r.id }, data: { ly_do: ly } }); tai(); } });
  };
  return <>
    <Button type="primary" style={{ marginBottom: 8 }} onClick={() => setMoi(true)}>+ Nhập nhanh phiếu sản xuất</Button>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Phiếu', dataIndex: 'so_phieu' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Xưởng', dataIndex: 'xuong' }, { title: 'Nguồn', dataIndex: 'nguon' },
      { title: 'Vấn đề', dataIndex: 'van_de', render: (v) => <span style={{ whiteSpace: 'pre-line' }}>{v}</span> },
      { render: (_, r) => <Space><Button size="small" onClick={() => boSung(r)}>Bổ sung</Button><Button size="small" danger onClick={() => boQua(r)}>Bỏ qua</Button></Space> },
    ]} />
    <Modal width="90%" open={moi} onCancel={() => setMoi(false)} footer={null} title="Nhập nhanh phiếu sản xuất" destroyOnClose>
      <NhapNhanhSX xong={() => { setMoi(false); tai(); }} />
    </Modal>
  </>;
}
