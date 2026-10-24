/** Màn hình Kho vận: tồn theo kho, phiếu kho (nhập / xuất khác / chuyển / đầu kỳ / kiểm kê), sổ kho, đơn chờ xuất. */
import { App, Button, Card, Col, DatePicker, Drawer, Form, Input, InputNumber, Row, Select, Space, Table, Tabs, Tag, Typography } from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, LOAI_PHIEU_KHO, TRANG_THAI_PHIEU, dvt, fmt, homNay, ngayVN, theTrangThai, useGoi } from './chung';
import { LuotChoXuat } from './LuotGiao';

function TonKho() {
  const goi = useGoi();
  const [kho, setKho] = useState<any>();
  const [q, setQ] = useState('');
  const [ds, setDs] = useState<any[]>([]);
  const [hien0, setHien0] = useState(false);
  const tai = async () => {
    const f: any = { $and: [] };
    if (kho) f.$and.push({ kho_id: kho });
    if (!hien0) f.$and.push({ so_kg: { $ne: 0 } });
    if (q) f.$and.push({ $or: [{ 'mat_hang.ma': { $includes: q } }, { 'mat_hang.ten': { $includes: q } }] });
    const r = await goi('ton_kho:list', { params: { filter: f, appends: ['kho', 'mat_hang'], pageSize: 500, sort: ['kho_id', 'mat_hang_id'] } });
    setDs(r.data || []);
  };
  useEffect(() => { tai(); }, [kho, hien0]);
  return (
    <>
      <Space style={{ marginBottom: 12 }} wrap>
        <ChonDanhMuc bang="kho" value={kho} onChange={setKho} placeholder="Tất cả kho" />
        <Input.Search placeholder="Mã hoặc tên hàng" allowClear onSearch={(v) => { setQ(v); setTimeout(tai); }} style={{ width: 240 }} />
        <Button onClick={() => setHien0(!hien0)}>{hien0 ? 'Ẩn dòng tồn 0' : 'Hiện cả dòng tồn 0'}</Button>
        <Button onClick={tai}>Tải lại</Button>
      </Space>
      <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 50 }}
        columns={[
          { title: 'Kho', render: (_, r) => r.kho?.ten },
          { title: 'Mã hàng', render: (_, r) => <b>{r.mat_hang?.ma}</b> },
          { title: 'Tên hàng', render: (_, r) => r.mat_hang?.ten },
          { title: 'ĐVT', render: (_, r) => dvt(r.mat_hang) },
          { title: 'Tồn thực tế', dataIndex: 'so_kg', align: 'right', render: (v) => <b style={{ color: v < 0 ? '#cf1322' : undefined }}>{fmt(v, 3)}</b> },
          { title: 'Đang giữ cho đơn', dataIndex: 'so_giu', align: 'right', render: (v) => (Number(v) ? fmt(v, 3) : '') },
          { title: 'Chờ định giá', dataIndex: 'so_cho_gia', align: 'right', render: (v) => (Number(v) ? <Tag color="gold">{fmt(v, 3)}</Tag> : '') },
          { title: 'Khả dụng bán', align: 'right', render: (_, r) => <b style={{ color: '#237804' }}>{fmt(Number(r.so_kg || 0) - Number(r.so_giu || 0) - Number(r.so_cho_gia || 0), 3)}</b> },
          { title: 'Tồn (bao)', dataIndex: 'so_bao', align: 'right', render: (v) => fmt(v, 2) },
        ]}
        summary={(rows) => <Table.Summary.Row><Table.Summary.Cell index={0} colSpan={3} align="right"><b>Cộng</b></Table.Summary.Cell>
          <Table.Summary.Cell index={1} /><Table.Summary.Cell index={2} align="right"><b>{fmt(rows.reduce((s, r: any) => s + Number(r.so_kg || 0), 0), 3)}</b></Table.Summary.Cell>
          <Table.Summary.Cell index={3} colSpan={4} /></Table.Summary.Row>} />
    </>
  );
}

function PhieuKho({ id, xong }: any) {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [form] = Form.useForm();
  const [pk, setPk] = useState<any>(null);
  const [dong, setDong] = useState<any[]>([{}]);
  const loai = Form.useWatch('loai', form);
  const sx = loai === 'san_xuat' || loai === 'dong_goi';
  const sua = !pk || pk.trang_thai === 'nhap';
  const tai = async (x = id) => {
    if (!x) { form.setFieldsValue({ loai: 'nhap', ngay: dayjs(homNay()) }); return; }
    const r = await goi('phieu_kho:get', { params: { filterByTk: x, appends: ['dong', 'dong.mat_hang', 'kho', 'kho_dich'] } });
    setPk(r.data);
    setDong((r.data.dong || []).sort((a: any, b: any) => a.id - b.id).map((d: any) => ({ ...d, kg_bao: d.mat_hang?.kg_bao })));
    form.setFieldsValue({ ...r.data, ngay: r.data.ngay ? dayjs(r.data.ngay) : null });
  };
  useEffect(() => { tai(); }, [id]);
  const luu = async () => {
    const v = await form.validateFields();
    const hang = dong.filter((d) => d.mat_hang_id);
    if (!hang.length) { message.warning('Thêm ít nhất một dòng hàng.'); throw new Error('thieu'); }
    const values = { ...v, ngay: v.ngay?.format('YYYY-MM-DD'), dong: hang.map((d) => ({ ...(d.id ? { id: d.id } : {}), mat_hang_id: d.mat_hang_id, so_bao: d.so_bao || 0, so_kg: d.so_kg || 0, ghi_chu: d.ghi_chu, huong: d.huong || null, don_gia: d.don_gia ?? null })) };
    if (pk?.id) { await goi('phieu_kho:update', { params: { filterByTk: pk.id, updateAssociationValues: ['dong'] }, data: values }); return pk.id; }
    return (await goi('phieu_kho:create', { params: { updateAssociationValues: ['dong'] }, data: values })).data.id;
  };
  const ghi = async () => {
    try {
      const x = await luu();
      await goi('phieu_kho:ghiSo', { params: { filterByTk: x }, data: {} });
      message.success('Đã ghi sổ kho');
      await tai(x); xong?.();
    } catch { /* đã báo */ }
  };
  const doi = (i: number, v: any) => setDong(dong.map((d, j) => (j === i ? { ...d, ...v } : d)));
  const [tt, mau] = theTrangThai(TRANG_THAI_PHIEU, pk?.trang_thai || 'nhap');
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      {pk && <Space><Typography.Title level={4} style={{ margin: 0 }}>{pk.so}</Typography.Title><Tag color={mau}>{tt}</Tag>{pk.ghi_boi && <span>Ghi bởi {pk.ghi_boi}</span>}</Space>}
      <Form form={form} layout="vertical" disabled={!sua}>
        <Row gutter={12}>
          <Col span={6}><Form.Item name="loai" label="Loại phiếu" rules={[{ required: true }]}>
            <Select options={Object.entries(LOAI_PHIEU_KHO).map(([value, label]) => ({ value, label }))} /></Form.Item></Col>
          <Col span={4}><Form.Item name="ngay" label="Ngày"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
          <Col span={7}><Form.Item name="kho_id" label={loai === 'chuyen' ? 'Kho xuất' : 'Kho'} rules={[{ required: true, message: 'Chọn kho' }]}>
            <ChonDanhMuc bang="kho" style={{ width: '100%' }} /></Form.Item></Col>
          {loai === 'chuyen' && <Col span={7}><Form.Item name="kho_dich_id" label="Kho nhận" rules={[{ required: true, message: 'Chọn kho nhận' }]}>
            <ChonDanhMuc bang="kho" style={{ width: '100%' }} /></Form.Item></Col>}
          {sx && <Col span={7}><Form.Item name="kho_dich_id" label="Kho thành phẩm (trống = cùng kho)">
            <ChonDanhMuc bang="kho" style={{ width: '100%' }} /></Form.Item></Col>}
        </Row>
        {loai === 'nhap' && <Row gutter={12}>
          <Col span={10}><Form.Item name="nha_cung_cap_id" label="Nhà cung cấp"><ChonDanhMuc bang="nha_cung_cap" timTheo={['ma', 'ten', 'sdt', 'nhan']} style={{ width: '100%' }} /></Form.Item></Col>
          <Col span={6}><Form.Item name="chung_tu_ncc" label="Số hóa đơn / phiếu NCC"><Input /></Form.Item></Col>
          {pk?.phai_tra !== undefined && pk?.trang_thai === 'da_ghi' && <Col span={8}><div style={{ paddingTop: 30 }}>
            Phải trả NCC <b>{fmt(pk.phai_tra)}</b> · Đã trả <b>{fmt(pk.da_tra)}</b></div></Col>}
        </Row>}
        {loai === 'nhap' && sua && <Typography.Paragraph type="secondary">Chưa biết giá thì để trống: hàng vào kho ở trạng thái <b>chờ định giá</b>, chưa bán được cho tới khi kế toán định giá. Thủ kho nhập thì luôn ở trạng thái chờ định giá.</Typography.Paragraph>}
        {sx && <Row gutter={12}>
          <Col span={8}><Form.Item name="xuong" label="Xưởng / tổ"><Input /></Form.Item></Col>
          <Col span={8}><Form.Item name="chi_phi_sx" label="Chi phí sản xuất lô này (nhân công, điện, bao bì…)">
            <InputNumber min={0} style={{ width: '100%' }} formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))} /></Form.Item></Col>
        </Row>}
        {pk?.trang_thai === 'da_ghi' && sx && <Card size="small" style={{ marginBottom: 12, background: '#f6ffed' }}>
          Kg vào <b>{fmt(pk.kg_vao, 3)}</b> · Kg ra <b>{fmt(pk.kg_ra, 3)}</b> · Hao hụt <b>{fmt((pk.kg_vao || 0) - (pk.kg_ra || 0), 3)}</b> kg ·
          Giá trị nguyên liệu <b>{fmt(pk.gia_tri_nvl)}</b> · Chi phí <b>{fmt(pk.chi_phi_sx)}</b> · <b>Giá thành: {fmt(pk.gia_thanh, 2)} đ/kg</b></Card>}
        <Row gutter={12} style={{ display: 'none' }}>
        </Row>
        <Row gutter={12}>
          <Col span={8}><Form.Item name="nguoi_giao_nhan" label="Người giao / nhận"><Input /></Form.Item></Col>
          <Col span={16}><Form.Item name="ghi_chu" label={loai === 'kiem_ke' ? 'Lý do điều chỉnh (bắt buộc)' : sx ? 'Ghi chú / lý do hao hụt (bắt buộc khi kg vào ≠ kg ra)' : 'Ghi chú'}><Input /></Form.Item></Col>
        </Row>
      </Form>
      {loai === 'kiem_ke' && sua && <Typography.Text type="secondary">Kiểm kê: nhập số kg CHÊNH LỆCH — số dương nếu thừa, số âm nếu thiếu.</Typography.Text>}
      <Table size="small" rowKey={(d: any, i: any) => d.id || `m${i}`} pagination={false} dataSource={dong} columns={[
        { title: 'Mã hàng', width: 280, render: (_, d, i) => (sua ? <ChonDanhMuc bang="mat_hang" value={d.mat_hang_id} style={{ width: 270 }}
          onChange={(v, mh) => doi(i, { mat_hang_id: v, ten_hang: mh?.ten, kg_bao: mh?.kg_bao, mat_hang: mh })} /> : <b>{d.mat_hang?.ma}</b>) },
        { title: 'Tên hàng', render: (_, d) => d.ten_hang || d.mat_hang?.ten },
        { title: 'Số bao', width: 110, render: (_, d, i) => (sua ? <InputNumber value={d.so_bao} onChange={(v) => doi(i, { so_bao: v, so_kg: v && d.kg_bao ? Math.round(v * d.kg_bao * 1000) / 1000 : d.so_kg })} /> : fmt(d.so_bao, 2)) },
        { title: 'Số lượng', width: 150, render: (_, d, i) => (sua ? <Space size={4}><InputNumber value={d.so_kg} onChange={(v) => doi(i, { so_kg: v })} />{dvt(d.mat_hang)}</Space>
          : `${fmt(d.so_kg, 3)} ${dvt(d.mat_hang)}`) },
        ...(sx ? [{ title: 'Vào / ra', width: 170, render: (_: any, d: any, i: number) => (sua ? <Select value={d.huong} style={{ width: 160 }} placeholder="Chọn"
          onChange={(v) => doi(i, { huong: v })} options={[{ value: 'vao', label: 'Nguyên liệu vào' }, { value: 'ra', label: 'Thành phẩm ra' }, { value: 'phu_pham', label: 'Phụ phẩm ra' }]} />
          : ({ vao: 'Nguyên liệu vào', ra: 'Thành phẩm ra', phu_pham: 'Phụ phẩm ra' } as any)[d.huong]) }] : []),
        ...(['nhap', 'dau_ky'].includes(loai) || sx ? [{ title: sx ? 'Đơn giá (phụ phẩm) / giá thành' : 'Giá nhập (đ/kg)', width: 150,
          render: (_: any, d: any, i: number) => (sua && (!sx || d.huong === 'phu_pham') ? <InputNumber min={0} value={d.don_gia} style={{ width: 140 }}
            formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/[^\d]/g, ''))} onChange={(v) => doi(i, { don_gia: v })} />
            : d.trang_thai_gia === 'cho_gia' ? <Tag color="gold">Chờ định giá</Tag> : fmt(d.don_gia, 2)) }] : []),
        { title: 'Ghi chú', render: (_, d, i) => (sua ? <Input value={d.ghi_chu} onChange={(e) => doi(i, { ghi_chu: e.target.value })} /> : d.ghi_chu) },
        ...(sua ? [{ width: 60, render: (_: any, __: any, i: number) => <Button danger size="small" onClick={() => setDong(dong.filter((_, j) => j !== i))}>Xóa</Button> }] : []),
      ]} />
      <Space wrap>
        {sua && <Button onClick={() => setDong([...dong, {}])}>+ Thêm hàng</Button>}
        {sua && <Button onClick={async () => { try { const x = await luu(); message.success('Đã lưu nháp'); tai(x); } catch { /* */ } }}>Lưu nháp</Button>}
        {sua && <Button type="primary" size="large" onClick={() => modal.confirm({ title: 'Ghi sổ kho?', content: 'Sau khi ghi, tồn kho thay đổi và phiếu không sửa được (chỉ hủy).', okText: 'Ghi sổ', cancelText: 'Thôi', onOk: ghi })}>Ghi sổ kho</Button>}
        {pk && <Button onClick={() => window.open(`/in/phieu_kho/${pk.id}`, '_blank')}>In phiếu</Button>}
        {pk && pk.trang_thai !== 'da_huy' && <Button danger onClick={() => {
          let ly_do = '';
          modal.confirm({ title: `Hủy phiếu ${pk.so}?`, okText: 'Hủy phiếu', cancelText: 'Thôi', okButtonProps: { danger: true },
            content: <Input.TextArea placeholder="Lý do (bắt buộc nếu đã ghi sổ)" onChange={(e) => (ly_do = e.target.value)} />,
            onOk: () => goi('phieu_kho:huy', { params: { filterByTk: pk.id }, data: { ly_do } }).then(() => { tai(pk.id); xong?.(); }) });
        }}>Hủy phiếu</Button>}
      </Space>
    </Space>
  );
}

function DanhSachPhieu() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [mo, setMo] = useState<any>(null);
  const tai = async () => setDs((await goi('phieu_kho:list', { params: { appends: ['kho', 'kho_dich'], sort: ['-id'], pageSize: 100 } })).data || []);
  useEffect(() => { tai(); }, []);
  return (
    <>
      <Button type="primary" style={{ marginBottom: 12 }} onClick={() => setMo('moi')}>+ Lập phiếu kho</Button>
      <Table size="small" rowKey="id" dataSource={ds} onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
        { title: 'Số', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
        { title: 'Loại', dataIndex: 'loai', render: (v) => LOAI_PHIEU_KHO[v] || v },
        { title: 'Kho', render: (_, r) => r.kho?.ten + (r.kho_dich ? ` → ${r.kho_dich.ten}` : '') },
        { title: 'Ghi chú', dataIndex: 'ghi_chu' },
        { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{t}</Tag>; } },
      ]} />
      <Drawer width="85%" open={!!mo} onClose={() => { setMo(null); tai(); }} title="Phiếu kho" destroyOnClose>
        {mo && <PhieuKho id={mo === 'moi' ? null : mo} xong={tai} />}
      </Drawer>
    </>
  );
}

function SoKho() {
  const goi = useGoi();
  const [mh, setMh] = useState<any>();
  const [kho, setKho] = useState<any>();
  const [ds, setDs] = useState<any[]>([]);
  useEffect(() => {
    if (!mh) return setDs([]);
    const f: any = { mat_hang_id: mh, ...(kho ? { kho_id: kho } : {}) };
    goi('so_kho:list', { params: { filter: f, appends: ['kho'], sort: ['id'], pageSize: 1000 } }).then((r) => {
      let ton = 0;
      setDs((r.data || []).map((x: any) => ({ ...x, ton: (ton = Math.round((ton + Number(x.so_kg || 0)) * 1000) / 1000) })));
    });
  }, [mh, kho]);
  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <ChonDanhMuc bang="mat_hang" value={mh} onChange={setMh} placeholder="Chọn mặt hàng" style={{ width: 300 }} />
        <ChonDanhMuc bang="kho" value={kho} onChange={setKho} placeholder="Tất cả kho" />
      </Space>
      <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 100 }} columns={[
        { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Chứng từ', dataIndex: 'chung_tu' },
        { title: 'Nghiệp vụ', dataIndex: 'loai' }, { title: 'Kho', render: (_, r) => r.kho?.ten },
        { title: 'Nhập (kg)', align: 'right', render: (_, r) => (r.so_kg > 0 ? fmt(r.so_kg, 3) : '') },
        { title: 'Xuất (kg)', align: 'right', render: (_, r) => (r.so_kg < 0 ? fmt(-r.so_kg, 3) : '') },
        { title: kho ? 'Tồn sau (kg)' : 'Lũy kế mọi kho (kg)', dataIndex: 'ton', align: 'right', render: (v) => <b>{fmt(v, 3)}</b> },
      ]} />
    </>
  );
}

function ChoDinhGia() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[] | null>(null);
  const [gia, setGia] = useState<Record<string, number>>({});
  const tai = () => goi('phieu_kho_dong:list', { params: { filter: { trang_thai_gia: 'cho_gia', 'phieu_kho.trang_thai': 'da_ghi' },
    appends: ['phieu_kho', 'phieu_kho.kho', 'phieu_kho.nha_cung_cap', 'mat_hang'], sort: ['id'], pageSize: 500 }, im: true })
    .then((r) => setDs(r.data || [])).catch(() => setDs([]));
  useEffect(() => { tai(); }, []);
  const dinhGia = async (pkId: any) => {
    const g = Object.fromEntries((ds || []).filter((d) => d.phieu_kho_id === pkId && Number(gia[d.id]) > 0).map((d) => [d.id, Number(gia[d.id])]));
    if (!Object.keys(g).length) return message.warning('Nhập đơn giá cho dòng của phiếu này.');
    await goi('phieu_kho:dinhGia', { params: { filterByTk: pkId }, data: { gia: g } });
    message.success('Đã định giá — hàng thành khả dụng để bán');
    tai();
  };
  return <>
    <Typography.Paragraph type="secondary">Hàng đã vào kho nhưng chưa có giá: chưa bán được, chưa vào giá vốn. Chỉ kế toán / quản lý định giá.</Typography.Paragraph>
    <Table size="small" rowKey="id" loading={!ds} dataSource={ds || []} pagination={false} columns={[
      { title: 'Phiếu', render: (_, d) => <b>{d.phieu_kho?.so}</b> }, { title: 'Ngày', render: (_, d) => ngayVN(d.phieu_kho?.ngay) },
      { title: 'Kho', render: (_, d) => d.phieu_kho?.kho?.ten }, { title: 'NCC', render: (_, d) => d.phieu_kho?.nha_cung_cap?.ten },
      { title: 'Hàng', render: (_, d) => <span><b>{d.mat_hang?.ma}</b> {d.mat_hang?.ten}</span> },
      { title: 'Số lượng', align: 'right', render: (_, d) => `${fmt(d.so_kg, 3)} ${dvt(d.mat_hang)}` },
      { title: 'Đơn giá', width: 160, render: (_, d) => <InputNumber min={0} style={{ width: 150 }} value={gia[d.id]} formatter={(v) => fmt(v)}
        parser={(v: any) => Number(String(v).replace(/\D/g, ''))} onChange={(v) => setGia({ ...gia, [d.id]: Number(v || 0) })} /> },
      { render: (_, d) => <Button size="small" type="primary" onClick={() => dinhGia(d.phieu_kho_id)}>Định giá phiếu {d.phieu_kho?.so}</Button> },
    ]} />
  </>;
}

function GiaThanh() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[] | null>(null);
  useEffect(() => { goi('phieu_kho:list', { params: { filter: { loai: { $in: ['san_xuat', 'dong_goi'] }, trang_thai: 'da_ghi' }, appends: ['dong', 'dong.mat_hang'], sort: ['-ngay', '-id'], pageSize: 300 }, im: true })
    .then((r) => setDs(r.data || [])).catch(() => setDs([])); }, []);
  return <Table size="small" rowKey="id" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 50 }} columns={[
    { title: 'Phiếu', dataIndex: 'so', render: (v, r) => <a href={`/in/phieu_kho/${r.id}`} target="_blank" rel="noreferrer">{v}</a> },
    { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Xưởng', dataIndex: 'xuong' },
    { title: 'Thành phẩm', render: (_, r) => (r.dong || []).filter((d: any) => d.huong === 'ra').map((d: any) => d.mat_hang?.ma).join(', ') },
    { title: 'Kg vào', dataIndex: 'kg_vao', align: 'right', render: (v) => fmt(v, 3) }, { title: 'Kg ra', dataIndex: 'kg_ra', align: 'right', render: (v) => fmt(v, 3) },
    { title: 'Hao hụt %', align: 'right', render: (_, r) => (r.kg_vao ? fmt(((r.kg_vao - r.kg_ra) / r.kg_vao) * 100, 2) + '%' : '') },
    { title: 'Giá trị NVL', dataIndex: 'gia_tri_nvl', align: 'right', render: (v) => fmt(v) }, { title: 'Chi phí SX', dataIndex: 'chi_phi_sx', align: 'right', render: (v) => fmt(v) },
    { title: 'Giá thành (đ/kg)', dataIndex: 'gia_thanh', align: 'right', render: (v) => <b>{fmt(v, 2)}</b> },
  ]} />;
}

function GiaVon() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[] | null>(null);
  const [loi, setLoi] = useState(false);
  useEffect(() => { goi('gia_von:list', { params: { appends: ['mat_hang'], pageSize: 2000, sort: ['mat_hang_id'] }, im: true })
    .then((r) => setDs(r.data || [])).catch(() => { setLoi(true); setDs([]); }); }, []);
  if (loi) return <Typography.Text type="secondary">Chỉ nhóm quản lý xem được giá vốn.</Typography.Text>;
  return <Table size="small" rowKey="id" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 50 }} columns={[
    { title: 'Mã hàng', render: (_, r) => <b>{r.mat_hang?.ma}</b> }, { title: 'Tên hàng', render: (_, r) => r.mat_hang?.ten },
    { title: 'Tổng tồn (kg)', dataIndex: 'so_kg', align: 'right', render: (v) => fmt(v, 3) },
    { title: 'Giá trị tồn', dataIndex: 'gia_tri', align: 'right', render: (v) => fmt(v) },
    { title: 'Giá vốn bình quân (đ/kg)', dataIndex: 'gia_bq', align: 'right', render: (v) => <b>{fmt(v, 2)}</b> },
  ]} />;
}

export function KhoVan() {
  return (
    <Card title="Kho vận">
      <Tabs items={[
        { key: 'cho', label: 'Lượt chờ xuất', children: <LuotChoXuat /> },
        { key: 'ton', label: 'Tồn kho', children: <TonKho /> },
        { key: 'phieu', label: 'Phiếu kho', children: <DanhSachPhieu /> },
        { key: 'so', label: 'Thẻ kho', children: <SoKho /> },
        { key: 'gt', label: 'Giá thành sản xuất', children: <GiaThanh /> },
        { key: 'dg', label: 'Chờ định giá', children: <ChoDinhGia /> },
        { key: 'gv', label: 'Giá vốn', children: <GiaVon /> },
      ]} />
    </Card>
  );
}
