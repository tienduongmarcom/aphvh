/**
 * 0.4.0 Bán nhanh (POS Lite) — dùng chung sổ với bán sỉ: mỗi lần bán là đơn bán kênh POS + lượt khách nhận + phiếu thu.
 * Quét mã vạch / gõ mã rồi Enter để thêm hàng; nhiều hình thức thanh toán trong một giao dịch; CK là "chờ xác minh".
 */
import { Alert, App, Button, Card, Col, Divider, Input, InputNumber, Row, Select, Space, Statistic, Table, Typography } from 'antd';
import React, { useEffect, useRef, useState } from 'react';
import { ChonDanhMuc, dvt, fmt, useGoi } from './chung';

const rid = () => (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`);

function MoCa({ xong }: any) {
  const goi = useGoi();
  const [v, setV] = useState<any>({ tien_dau_ca: 0 });
  return <Card title="Mở ca bán">
    <Space direction="vertical">
      <ChonDanhMuc bang="quy" value={v.quy_id} onChange={(x) => setV({ ...v, quy_id: x })} placeholder="Quỹ tiền mặt của quầy" locThem={{ loai: 'tien_mat' }} style={{ width: 320 }} />
      <ChonDanhMuc bang="kho" value={v.kho_id} onChange={(x) => setV({ ...v, kho_id: x })} placeholder="Kho bán" locThem={{ trung_chuyen: { $ne: true } }} style={{ width: 320 }} />
      <InputNumber addonBefore="Tiền đầu ca" value={v.tien_dau_ca} min={0} style={{ width: 320 }} onChange={(x) => setV({ ...v, tien_dau_ca: x })} />
      <Button type="primary" onClick={async () => xong((await goi('ca_pos:mo', { data: v })).data.id)}>Mở ca</Button>
    </Space>
  </Card>;
}

export function BanNhanh() {
  const goi = useGoi();
  const { message, modal } = App.useApp();
  const [ca, setCa] = useState<any>(null);
  const [gio, setGio] = useState<any[]>([]);
  const [kh, setKh] = useState<any>(null);
  const [tt, setTt] = useState<any[]>([{ hinh_thuc: 'tien_mat', so_tien: 0 }]);
  const [req, setReq] = useState(rid());
  const [kq, setKq] = useState<any>(null);
  const [nhNh, setNhNh] = useState<any[]>([]);
  const quet = useRef<any>();
  const taiCa = async (id?: any) => {
    const r = await goi('ca_pos:list', { params: { filter: id ? { id } : { trang_thai: 'mo' }, appends: ['quy', 'kho'], sort: ['-id'], pageSize: 1 }, im: true }).catch(() => ({ data: [] }));
    setCa(r.data?.[0] || null);
  };
  useEffect(() => { taiCa(); goi('quy:list', { params: { filter: { loai: 'ngan_hang' }, pageSize: 50 }, im: true }).then((r) => setNhNh(r.data || [])).catch(() => null); }, []);
  if (!ca) return <MoCa xong={taiCa} />;
  const them = async (mh: any) => {
    if (!mh) return;
    const co = gio.findIndex((x) => x.mat_hang_id === mh.id && !x.dvt_nhap);
    if (co >= 0) setGio(gio.map((x, i) => (i === co ? { ...x, so_kg: Number(x.so_kg || 0) + 1 } : x)));
    else setGio([...gio, { mat_hang_id: mh.id, mh, so_kg: 1 }]);
  };
  const timMa = async (ma: string) => {
    if (!ma) return;
    const r = await goi('mat_hang:list', { params: { filter: { $or: [{ ma_vach: ma }, { ma }] }, pageSize: 2 } });
    if (!r.data?.length) return message.warning(`Không thấy mã ${ma}`);
    them(r.data[0]);
  };
  const ban = async () => {
    if (!gio.length) return message.warning('Chưa có hàng.');
    const r = await goi('ca_pos:ban', { params: { filterByTk: ca.id }, data: { ca_pos_id: ca.id, request_id: req, khach_id: kh || null,
      dong: gio.map((x) => ({ mat_hang_id: x.mat_hang_id, ...(x.dvt_nhap ? { dvt_nhap: x.dvt_nhap, sl_nhap: x.so_kg } : { so_kg: x.so_kg }), don_gia: x.don_gia ?? null,
        ly_do_sua_gia: x.don_gia ? 'Sửa giá tại quầy' : null })),
      thanh_toan: tt.filter((x) => Number(x.so_tien) > 0) } });
    setKq(r.data);
    setGio([]); setKh(null); setTt([{ hinh_thuc: 'tien_mat', so_tien: 0 }]); setReq(rid());
    taiCa(ca.id);
  };
  const chot = () => {
    let dem: any = 0, ly = '';
    modal.confirm({ title: `Chốt ca ${ca.so}`, content: <Space direction="vertical">
      <InputNumber addonBefore="Tiền mặt đếm được" style={{ width: 300 }} onChange={(v) => (dem = v)} />
      <Input placeholder="Lý do nếu lệch" onChange={(e) => (ly = e.target.value)} /></Space>,
    onOk: async () => { const r = await goi('ca_pos:chot', { params: { filterByTk: ca.id }, data: { thuc_dem: dem, ly_do: ly } });
      message.info(`Phải có ${fmt(r.data.so_sach)} · lệch ${fmt(r.data.chenh_lech)} · CK chờ xác minh ${r.data.ck_cho_xac_minh.so_phieu} phiếu`); setCa(null); } });
  };
  return <Row gutter={16}>
    <Col span={15}>
      <Card size="small" title={`Ca ${ca.so} · ${ca.kho?.ten} · ${ca.quy?.ten}`} extra={<Button onClick={chot}>Chốt ca</Button>}>
        <Space style={{ marginBottom: 8 }} wrap>
          <Input ref={quet} autoFocus placeholder="Quét mã vạch / gõ mã rồi Enter" style={{ width: 280 }} onPressEnter={(e: any) => { timMa(e.target.value.trim()); e.target.value = ''; }} />
          <ChonDanhMuc bang="mat_hang" value={null} onChange={(_, mh) => them(mh)} placeholder="Tìm theo tên" timTheo={['ma', 'ten', 'ma_vach', 'nhan']} style={{ width: 280 }} />
        </Space>
        <Table size="small" rowKey={(_, i) => String(i)} pagination={false} dataSource={gio} columns={[
          { title: 'Hàng', render: (_, x) => <span><b>{x.mh?.ma}</b> {x.mh?.ten}</span> },
          { title: 'Số lượng', width: 130, render: (_, x, i) => <InputNumber min={0} value={x.so_kg} onChange={(v) => setGio(gio.map((y, j) => (j === i ? { ...y, so_kg: v } : y)))} /> },
          { title: 'ĐVT', width: 90, render: (_, x, i) => <Input value={x.dvt_nhap || ''} placeholder={dvt(x.mh)} onChange={(e) => setGio(gio.map((y, j) => (j === i ? { ...y, dvt_nhap: e.target.value || null } : y)))} /> },
          { title: 'Giá (trống = giá lẻ)', width: 150, render: (_, x, i) => <InputNumber min={0} value={x.don_gia} onChange={(v) => setGio(gio.map((y, j) => (j === i ? { ...y, don_gia: v } : y)))} /> },
          { width: 40, render: (_, __, i) => <Button size="small" danger onClick={() => setGio(gio.filter((_, j) => j !== i))}>×</Button> },
        ]} />
        <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>Giá tính ở máy chủ theo bảng giá kênh bán lẻ; tổng tiền hiển thị sau khi bán. Khách lẻ phải trả đủ.</Typography.Paragraph>
      </Card>
    </Col>
    <Col span={9}>
      <Card size="small" title="Thanh toán">
        <ChonDanhMuc bang="khach_hang" value={kh} onChange={setKh} placeholder="Khách lẻ (để trống) / chọn khách có mã" timTheo={['ma', 'ten', 'sdt', 'nhan']} style={{ width: '100%' }} />
        <Divider style={{ margin: '8px 0' }} />
        {tt.map((x, i) => <Space key={i} style={{ marginBottom: 6 }} wrap>
          <Select value={x.hinh_thuc} style={{ width: 130 }} onChange={(v) => setTt(tt.map((y, j) => (j === i ? { ...y, hinh_thuc: v } : y)))}
            options={[{ value: 'tien_mat', label: 'Tiền mặt' }, { value: 'chuyen_khoan', label: 'Chuyển khoản' }, { value: 'ghi_no', label: 'Ghi nợ' }]} />
          <InputNumber min={0} value={x.so_tien} style={{ width: 140 }} onChange={(v) => setTt(tt.map((y, j) => (j === i ? { ...y, so_tien: v } : y)))} />
          {x.hinh_thuc === 'chuyen_khoan' && <><Select placeholder="TK nhận" style={{ width: 160 }} value={x.quy_id} onChange={(v) => setTt(tt.map((y, j) => (j === i ? { ...y, quy_id: v } : y)))}
            options={nhNh.map((q: any) => ({ value: q.id, label: q.ten }))} />
            <Input placeholder="Mã GD" style={{ width: 120 }} value={x.ma_gd} onChange={(e) => setTt(tt.map((y, j) => (j === i ? { ...y, ma_gd: e.target.value } : y)))} /></>}
        </Space>)}
        <Button size="small" onClick={() => setTt([...tt, { hinh_thuc: 'chuyen_khoan', so_tien: 0 }])}>+ Hình thức</Button>
        <Divider style={{ margin: '8px 0' }} />
        <Button type="primary" size="large" block onClick={ban}>Bán</Button>
        {kq && <Alert style={{ marginTop: 12 }} type="success" showIcon message={`Đã bán ${kq.so}`} description={<>
          <Statistic title="Phải thu" value={kq.phai_thu} groupSeparator="." />
          <div>Tiền mặt thu: {fmt(kq.tien_mat)} · Thối lại: <b>{fmt(kq.tien_thoi)}</b></div>
          <div>Chuyển khoản chờ xác minh: {fmt(kq.chuyen_khoan_cho_xac_minh)} · Ghi nợ: {fmt(kq.ghi_no)}</div>
          <Button size="small" style={{ marginTop: 6 }} onClick={() => window.open(`/in/don_ban/${kq.id}`, '_blank')}>In phiếu</Button></>} />}
        <Divider style={{ margin: '8px 0' }} />
        <div>Ca: tiền mặt {fmt(ca.thu_tien_mat)} · CK {fmt(ca.thu_ck)} · ghi nợ {fmt(ca.ghi_no)} · {ca.so_don || 0} đơn</div>
      </Card>
    </Col>
  </Row>;
}
