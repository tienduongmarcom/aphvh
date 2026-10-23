/** Thu chi và công nợ: ghi nhận khách trả tiền (trả đúng đơn được chọn, phần thừa chưa phân bổ), danh sách phiếu thu, công nợ tổng hợp. */
import { Alert, App, Button, Card, Checkbox, Col, DatePicker, Drawer, Form, Input, InputNumber, Radio, Row, Space, Table, Tabs, Tag, Typography } from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useMemo, useState } from 'react';
import { ChonDanhMuc, TRANG_THAI_PHIEU, fmt, homNay, ngayVN, theTrangThai, useGoi } from './chung';

function GhiThu({ khachBanDau, xong }: any) {
  const goi = useGoi();
  const { message, modal } = App.useApp();
  const [form] = Form.useForm();
  const [khach, setKhach] = useState<any>(khachBanDau);
  const [don, setDon] = useState<any[]>([]);
  const [chon, setChon] = useState<{ id: any; so_tien: number }[]>([]);
  const donVi = Form.useWatch('don_vi_id', form);
  const soTien = Form.useWatch('so_tien', form) || 0;
  const hinhThuc = Form.useWatch('hinh_thuc', form);
  useEffect(() => { form.setFieldsValue({ ngay: dayjs(homNay()), hinh_thuc: 'tien_mat' }); }, []);
  useEffect(() => {
    setChon([]);
    if (!khach) return setDon([]);
    goi('don_ban:list', { params: { filter: { khach_id: khach, trang_thai: 'da_giao', con_no: { $gt: 0 } }, appends: ['don_vi_ban'], sort: ['ngay', 'id'], pageSize: 500 } })
      .then((r) => setDon(r.data || []));
  }, [khach]);
  const theoDonVi = useMemo(() => {
    const m: Record<string, { ten: string; no: number }> = {};
    don.forEach((d) => { const k = d.don_vi_ban_id; m[k] = m[k] || { ten: d.don_vi_ban?.ten, no: 0 }; m[k].no += Number(d.con_no || 0); });
    return m;
  }, [don]);
  const donCuaDonVi = don.filter((d) => d.don_vi_ban_id === donVi);
  const daPhanBo = chon.reduce((s, c) => s + (c.so_tien || 0), 0);
  const tick = (d: any, on: boolean) => {
    if (!on) return setChon(chon.filter((c) => c.id !== d.id));
    const con = Math.max(0, soTien - daPhanBo);
    setChon([...chon, { id: d.id, so_tien: Math.min(con, Number(d.con_no)) }]);
  };
  const ghi = async () => {
    const v = await form.validateFields();
    if (daPhanBo > v.so_tien) return message.error('Tổng tiền trả cho các đơn lớn hơn số tiền thực nhận.');
    if (chon.some((c) => !(c.so_tien > 0))) return message.error('Mỗi đơn được chọn phải có số tiền lớn hơn 0 (bỏ chọn nếu không trả).');
    modal.confirm({
      title: 'Ghi phiếu thu?', okText: 'Ghi & In phiếu thu', cancelText: 'Xem lại',
      content: <div>Thu <b>{fmt(v.so_tien)} đ</b> vào <b>{theoDonVi[donVi]?.ten || 'đơn vị đã chọn'}</b>. Trả cho {chon.length} đơn: {fmt(daPhanBo)} đ.
        Chưa phân bổ: <b>{fmt(v.so_tien - daPhanBo)} đ</b>.</div>,
      onOk: async () => {
        const r = await goi('phieu_thu:create', { params: { updateAssociationValues: ['phan_bo'] }, data: {
          ...v, ngay: v.ngay.format('YYYY-MM-DD'), khach_id: khach, phan_bo: chon.map((c) => ({ don_ban_id: c.id, so_tien: c.so_tien })) } });
        await goi('phieu_thu:ghi', { params: { filterByTk: r.data.id }, data: {} });
        window.open(`/in/phieu_thu/${r.data.id}`, '_blank');
        message.success('Đã ghi phiếu thu');
        xong?.();
      },
    });
  };
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <div><b>1. Khách hàng</b><br />
        <ChonDanhMuc bang="khach_hang" value={khach} onChange={setKhach} timTheo={['ma', 'ten', 'sdt', 'nhan']} placeholder="Gõ tên, mã hoặc SĐT" style={{ width: 420 }} /></div>
      {khach && <Table size="small" pagination={false} rowKey="k" title={() => 'Công nợ theo đơn vị (mỗi đơn vị một số riêng, không cấn chéo)'}
        dataSource={Object.entries(theoDonVi).map(([k, v]) => ({ k, ...v }))}
        columns={[{ title: 'Đơn vị', dataIndex: 'ten' }, { title: 'Còn phải thu', dataIndex: 'no', align: 'right', render: (v) => <b>{fmt(v)}</b> }]} />}
      <Form form={form} layout="vertical">
        <b>2. Tiền thực nhận</b>
        <Row gutter={12}>
          <Col span={7}><Form.Item name="don_vi_id" label="Đơn vị nhận tiền" rules={[{ required: true, message: 'Chọn đơn vị' }]}>
            <ChonDanhMuc bang="don_vi" style={{ width: '100%' }} onChange={(v) => { form.setFieldValue('don_vi_id', v); setChon([]); }} /></Form.Item></Col>
          <Col span={5}><Form.Item name="hinh_thuc" label="Hình thức"><Radio.Group optionType="button" options={[{ value: 'tien_mat', label: 'Tiền mặt' }, { value: 'chuyen_khoan', label: 'Chuyển khoản' }]} /></Form.Item></Col>
          <Col span={5}><Form.Item name="so_tien" label="Số tiền (đ)" rules={[{ required: true, message: 'Nhập số tiền' }]}>
            <InputNumber min={1} style={{ width: '100%' }} formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))} /></Form.Item></Col>
          <Col span={4}><Form.Item name="ngay" label="Ngày thu"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
        </Row>
        <Row gutter={12}>
          {hinhThuc === 'chuyen_khoan' && <Col span={8}><Form.Item name="ma_gd" label="Mã GD / nội dung CK" rules={[{ required: true, message: 'Bắt buộc với chuyển khoản' }]}><Input /></Form.Item></Col>}
          <Col span={8}><Form.Item name="nguoi_nop" label="Người nộp"><Input /></Form.Item></Col>
          <Col span={8}><Form.Item name="ghi_chu" label="Ghi chú"><Input /></Form.Item></Col>
        </Row>
      </Form>
      <b>3. Trả cho đơn nào (tích theo thứ tự muốn trả; không tích = chưa phân bổ)</b>
      {!donVi ? <Alert type="info" message="Chọn đơn vị nhận tiền để xem các đơn còn nợ của đơn vị đó." /> :
        <Table size="small" rowKey="id" pagination={false} dataSource={donCuaDonVi} locale={{ emptyText: 'Đơn vị này không có đơn còn nợ: toàn bộ tiền là chưa phân bổ.' }}
          columns={[
            { width: 40, render: (_, d) => <Checkbox checked={!!chon.find((c) => c.id === d.id)} onChange={(e) => tick(d, e.target.checked)} /> },
            { title: 'Đơn', dataIndex: 'so' }, { title: 'Ngày giao', dataIndex: 'ngay_giao', render: ngayVN },
            { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v) => fmt(v) },
            { title: 'Trả lần này', width: 170, render: (_, d) => { const c = chon.find((x) => x.id === d.id); return c ? <InputNumber min={0} max={Number(d.con_no)} value={c.so_tien} style={{ width: 150 }}
              formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))}
              onChange={(v) => setChon(chon.map((x) => (x.id === d.id ? { ...x, so_tien: Number(v || 0) } : x)))} /> : null; } },
          ]} />}
      <Alert type={daPhanBo > soTien ? 'error' : 'success'} message={<span>4. Xem trước: thực nhận <b>{fmt(soTien)}</b> — trả cho đơn <b>{fmt(daPhanBo)}</b> — chưa phân bổ <b>{fmt(soTien - daPhanBo)}</b> (kế toán phân bổ sau khi xác minh)</span>} />
      <Button type="primary" size="large" disabled={!khach} onClick={ghi}>5. Ghi phiếu thu &amp; In</Button>
    </Space>
  );
}

function DanhSachThu() {
  const goi = useGoi();
  const { modal } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('phieu_thu:list', { params: { appends: ['khach', 'don_vi'], sort: ['-id'], pageSize: 100 } })).data || []);
  useEffect(() => { tai(); }, []);
  return <Table size="small" rowKey="id" dataSource={ds} columns={[
    { title: 'Số', dataIndex: 'so', render: (v, r) => <a href={`/in/phieu_thu/${r.id}`} target="_blank" rel="noreferrer">{v}</a> },
    { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Khách', render: (_, r) => r.khach?.ten }, { title: 'Đơn vị', render: (_, r) => r.don_vi?.ten },
    { title: 'Hình thức', dataIndex: 'hinh_thuc', render: (v) => (v === 'chuyen_khoan' ? 'Chuyển khoản' : 'Tiền mặt') },
    { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) },
    { title: 'Chưa phân bổ', dataIndex: 'chua_phan_bo', align: 'right', render: (v) => fmt(v) },
    { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{t}</Tag>; } },
    { render: (_, r) => r.trang_thai === 'da_ghi' && <Button size="small" danger onClick={() => { let ly_do = ''; modal.confirm({
      title: `Hủy phiếu thu ${r.so}?`, content: <Input.TextArea placeholder="Lý do (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} />,
      okText: 'Hủy phiếu', cancelText: 'Thôi', okButtonProps: { danger: true },
      onOk: () => goi('phieu_thu:huy', { params: { filterByTk: r.id }, data: { ly_do } }).then(tai) }); }}>Hủy</Button> },
  ]} />;
}

function CongNo() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [q, setQ] = useState('');
  useEffect(() => {
    Promise.all([
      goi('don_ban:list', { params: { filter: { trang_thai: 'da_giao', con_no: { $ne: 0 } }, appends: ['khach', 'don_vi_ban'], pageSize: 5000 } }),
      goi('phieu_thu:list', { params: { filter: { trang_thai: 'da_ghi', chua_phan_bo: { $gt: 0 } }, appends: ['khach', 'don_vi'], pageSize: 5000 } }),
    ]).then(([a, b]) => {
      const m: Record<string, any> = {};
      const homnay = new Date().toISOString().slice(0, 10);
      (a.data || []).forEach((d: any) => {
        const k = `${d.khach_id}-${d.don_vi_ban_id}`;
        m[k] = m[k] || { k, khach: d.khach, don_vi: d.don_vi_ban, no: 0, so_don: 0, cu_nhat: d.ngay_giao, chua_pb: 0 };
        m[k].no += Number(d.con_no || 0); m[k].so_don += 1;
        if (d.ngay_giao < m[k].cu_nhat) m[k].cu_nhat = d.ngay_giao;
      });
      (b.data || []).forEach((p: any) => {
        const k = `${p.khach_id}-${p.don_vi_id}`;
        m[k] = m[k] || { k, khach: p.khach, don_vi: p.don_vi, no: 0, so_don: 0, cu_nhat: '', chua_pb: 0 };
        m[k].chua_pb += Number(p.chua_phan_bo || 0);
      });
      setDs(Object.values(m).sort((x: any, y: any) => y.no - x.no));
    });
  }, []);
  const loc = ds.filter((r) => !q || `${r.khach?.ten} ${r.khach?.sdt} ${r.khach?.ma}`.toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <Input.Search placeholder="Lọc theo khách / SĐT" allowClear onChange={(e) => setQ(e.target.value)} style={{ width: 280, marginBottom: 12 }} />
      <Table size="small" rowKey="k" dataSource={loc} pagination={{ pageSize: 50 }} columns={[
        { title: 'Khách', render: (_, r) => <span><b>{r.khach?.ten}</b><div style={{ fontSize: 12, color: '#888' }}>{r.khach?.ma} · {r.khach?.sdt}</div></span> },
        { title: 'Đơn vị', render: (_, r) => r.don_vi?.ten },
        { title: 'Số đơn còn nợ', dataIndex: 'so_don', align: 'right' },
        { title: 'Nợ từ ngày', dataIndex: 'cu_nhat', render: ngayVN },
        { title: 'Còn phải thu', dataIndex: 'no', align: 'right', render: (v) => <b>{fmt(v)}</b> },
        { title: 'Tiền đã nhận chưa phân bổ', dataIndex: 'chua_pb', align: 'right', render: (v) => (v ? fmt(v) : '') },
      ]} summary={(rows) => <Table.Summary.Row><Table.Summary.Cell index={0} colSpan={4} align="right"><b>Cộng</b></Table.Summary.Cell>
        <Table.Summary.Cell index={1} align="right"><b>{fmt(rows.reduce((s, r: any) => s + r.no, 0))}</b></Table.Summary.Cell>
        <Table.Summary.Cell index={2} align="right"><b>{fmt(rows.reduce((s, r: any) => s + r.chua_pb, 0))}</b></Table.Summary.Cell></Table.Summary.Row>} />
    </>
  );
}

export function ThuTien() {
  const [ban, setBan] = useState(0);
  return (
    <Card title="Thu chi và công nợ">
      <Tabs items={[
        { key: 'thu', label: 'Ghi nhận khách trả tiền', children: <GhiThu key={ban} xong={() => setBan(ban + 1)} /> },
        { key: 'ds', label: 'Phiếu thu', children: <DanhSachThu key={ban} /> },
        { key: 'cn', label: 'Công nợ khách', children: <CongNo key={ban} /> },
      ]} />
    </Card>
  );
}
