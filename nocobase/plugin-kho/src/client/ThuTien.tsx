/** Thu chi và công nợ: ghi nhận khách trả tiền (trả đúng đơn được chọn, phần thừa chưa phân bổ), danh sách phiếu thu, công nợ tổng hợp. */
import { Alert, App, Button, Card, Checkbox, Col, DatePicker, Form, Input, InputNumber, Modal, Radio, Row, Select, Space, Table, Tabs, Tag, Typography } from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useMemo, useState } from 'react';
import { ChonDanhMuc, TRANG_THAI_PHIEU, fmt, homNay, ngayVN, theTrangThai, useGoi } from './chung';

const CON_NO = ['dang_giao', 'da_giao', 'da_dong'];
const LOAI_THU: Record<string, string> = { thu_no: 'Trả nợ', coc: 'Đặt cọc', chua_ro: 'Chưa rõ người nộp' };

/** Phân bổ phần chưa phân bổ của một phiếu thu vào đơn (thường = cùng đơn vị; thu hộ = đơn vị khác, chỉ kế toán). */
function PhanBo({ pt, thuHo, onClose }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [don, setDon] = useState<any[]>([]);
  const [tien, setTien] = useState<Record<string, number>>({});
  const [ghiChu, setGhiChu] = useState('');
  useEffect(() => {
    goi('don_ban:list', { params: { filter: { khach_id: pt.khach_id, trang_thai: { $in: CON_NO }, con_no: { $gt: 0 },
      don_vi_ban_id: thuHo ? { $ne: pt.don_vi_id } : pt.don_vi_id }, appends: ['don_vi_ban'], sort: ['ngay', 'id'], pageSize: 500 } }).then((r) => setDon(r.data || []));
  }, []);
  const tong = Object.values(tien).reduce((a, b) => a + Number(b || 0), 0);
  return (
    <Modal open width={760} title={`${thuHo ? 'Phân bổ thu hộ' : 'Phân bổ'} ${pt.so} — chưa phân bổ ${fmt(pt.chua_phan_bo)} đ`} okText="Ghi phân bổ" cancelText="Thôi"
      onCancel={onClose} onOk={async () => {
        const ds = Object.entries(tien).filter(([, v]) => Number(v) > 0).map(([k, v]) => ({ don_ban_id: Number(k), so_tien: v }));
        if (!ds.length) return message.warning('Nhập số tiền cho ít nhất một đơn.');
        await goi(thuHo ? 'phieu_thu:phanBoThuHo' : 'phieu_thu:phanBo', { params: { filterByTk: pt.id }, data: { phan_bo: ds, ghi_chu: ghiChu } });
        message.success('Đã phân bổ'); onClose(true);
      }}>
      {thuHo && <Alert style={{ marginBottom: 12 }} type="warning" message={`Tiền vẫn nằm ở ${pt.don_vi?.ten}. Hệ thống ghi khoản đang giữ hộ đơn vị có đơn, chờ tất toán giữa hai đơn vị.`} />}
      {thuHo && <Input.TextArea style={{ marginBottom: 12 }} placeholder="Căn cứ thu hộ (bắt buộc): vd. khách xác nhận chuyển nhầm tài khoản" value={ghiChu} onChange={(e) => setGhiChu(e.target.value)} />}
      <Table size="small" rowKey="id" pagination={false} dataSource={don} locale={{ emptyText: 'Không có đơn còn nợ phù hợp' }} columns={[
        { title: 'Đơn', dataIndex: 'so' }, { title: 'Đơn vị', render: (_, d) => d.don_vi_ban?.ten }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
        { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v) => fmt(v) },
        { title: 'Trả', width: 160, render: (_, d) => <InputNumber min={0} max={Number(d.con_no)} style={{ width: 150 }} value={tien[d.id]} formatter={(v) => fmt(v)}
          parser={(v: any) => Number(String(v).replace(/\D/g, ''))} onChange={(v) => setTien({ ...tien, [d.id]: Number(v || 0) })} /> },
      ]} />
      <div style={{ marginTop: 8 }}>Tổng phân bổ: <b style={{ color: tong > Number(pt.chua_phan_bo) ? '#cf1322' : undefined }}>{fmt(tong)}</b> đ</div>
    </Modal>
  );
}

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
  const [loaiThu, setLoaiThu] = useState('thu_no');
  useEffect(() => { form.setFieldsValue({ ngay: dayjs(homNay()), hinh_thuc: 'tien_mat' }); }, []);
  useEffect(() => { if (loaiThu !== 'thu_no') setChon([]); }, [loaiThu]);
  useEffect(() => {
    setChon([]);
    if (!khach) return setDon([]);
    goi('don_ban:list', { params: { filter: { khach_id: khach, trang_thai: { $in: CON_NO }, con_no: { $gt: 0 } }, appends: ['don_vi_ban'], sort: ['ngay', 'id'], pageSize: 500 } })
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
    const maYc = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    modal.confirm({
      title: 'Ghi phiếu thu?', okText: 'Ghi & In phiếu thu', cancelText: 'Xem lại',
      content: <div>Thu <b>{fmt(v.so_tien)} đ</b> vào <b>{theoDonVi[donVi]?.ten || 'đơn vị đã chọn'}</b>. Trả cho {chon.length} đơn: {fmt(daPhanBo)} đ.
        Chưa phân bổ: <b>{fmt(v.so_tien - daPhanBo)} đ</b>.</div>,
      onOk: async () => {
        const r = await goi('phieu_thu:create', { params: { updateAssociationValues: ['phan_bo'] }, data: {
          ...v, ngay: v.ngay.format('YYYY-MM-DD'), loai_thu: loaiThu, khach_id: loaiThu === 'chua_ro' ? null : khach, request_id: maYc, phan_bo: chon.map((c) => ({ don_ban_id: c.id, so_tien: c.so_tien })) } });
        await goi('phieu_thu:ghi', { params: { filterByTk: r.data.id }, data: {} });
        window.open(`/in/phieu_thu/${r.data.id}`, '_blank');
        message.success('Đã ghi phiếu thu');
        xong?.();
      },
    });
  };
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <div><b>Loại tiền: </b>
        <Radio.Group optionType="button" value={loaiThu} onChange={(e) => setLoaiThu(e.target.value)} options={[{ value: 'thu_no', label: 'Khách trả nợ / trả đơn' }, { value: 'coc', label: 'Đặt cọc' }, { value: 'chua_ro', label: 'Chưa rõ người nộp' }]} /></div>
      {loaiThu === 'chua_ro' && <Alert type="warning" message="Tiền vào đúng quỹ / tài khoản, nằm ở 'chưa phân bổ'. Khi xác minh được khách, vào tab Phiếu thu → Nhận diện khách → Phân bổ." />}
      {loaiThu === 'coc' && <Alert type="info" message="Tiền cọc không tự trừ nợ cũ. Khi giao hàng, vào tab Phiếu thu → Phân bổ cọc vào đơn." />}
      {loaiThu !== 'chua_ro' && <div><b>1. Khách hàng</b><br />
        <ChonDanhMuc bang="khach_hang" value={khach} onChange={setKhach} timTheo={['ma', 'ten', 'sdt', 'nhan']} placeholder="Gõ tên, mã hoặc SĐT" style={{ width: 420 }} /></div>}
      {khach && loaiThu === 'thu_no' && <Table size="small" pagination={false} rowKey="k" title={() => 'Công nợ theo đơn vị (mỗi đơn vị một số riêng, không cấn chéo)'}
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
          <Col span={8}><Form.Item name="quy_id" label={hinhThuc === 'chuyen_khoan' ? 'Tài khoản ngân hàng nhận' : 'Quỹ tiền mặt nhận'} rules={[{ required: true, message: 'Chọn quỹ / tài khoản' }]}>
            <ChonDanhMuc bang="quy" style={{ width: '100%' }} locThem={{ don_vi_id: donVi || 0, loai: hinhThuc === 'chuyen_khoan' ? 'ngan_hang' : 'tien_mat', ngung_dung: { $ne: true } }} />
          </Form.Item></Col>
        </Row>
        <Row gutter={12}>
          {hinhThuc === 'chuyen_khoan' && <Col span={8}><Form.Item name="ma_gd" label="Mã GD / nội dung CK" rules={[{ required: true, message: 'Bắt buộc với chuyển khoản' }]}><Input /></Form.Item></Col>}
          <Col span={8}><Form.Item name="nguoi_nop" label="Người nộp"><Input /></Form.Item></Col>
          <Col span={8}><Form.Item name="ghi_chu" label="Ghi chú"><Input /></Form.Item></Col>
        </Row>
        {loaiThu === 'coc' && <Form.Item name="muc_dich_coc" label="Mục đích cọc" rules={[{ required: true, message: 'Ghi mục đích cọc' }]}><Input /></Form.Item>}
      </Form>
      {loaiThu === 'thu_no' && <><b>3. Trả cho đơn nào (tích theo thứ tự muốn trả; không tích = chưa phân bổ)</b>
      {!donVi ? <Alert type="info" message="Chọn đơn vị nhận tiền để xem các đơn còn nợ của đơn vị đó." /> :
        <Table size="small" rowKey="id" pagination={false} dataSource={donCuaDonVi} locale={{ emptyText: 'Đơn vị này không có đơn còn nợ: toàn bộ tiền là chưa phân bổ.' }}
          columns={[
            { width: 40, render: (_, d) => <Checkbox checked={!!chon.find((c) => c.id === d.id)} onChange={(e) => tick(d, e.target.checked)} /> },
            { title: 'Đơn', dataIndex: 'so' }, { title: 'Ngày giao', dataIndex: 'ngay_giao', render: ngayVN },
            { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v) => fmt(v) },
            { title: 'Trả lần này', width: 170, render: (_, d) => { const c = chon.find((x) => x.id === d.id); return c ? <InputNumber min={0} max={Number(d.con_no)} value={c.so_tien} style={{ width: 150 }}
              formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))}
              onChange={(v) => setChon(chon.map((x) => (x.id === d.id ? { ...x, so_tien: Number(v || 0) } : x)))} /> : null; } },
          ]} />}</>}
      <Alert type={daPhanBo > soTien ? 'error' : 'success'} message={<span>4. Xem trước: thực nhận <b>{fmt(soTien)}</b> — trả cho đơn <b>{fmt(daPhanBo)}</b> — chưa phân bổ <b>{fmt(soTien - daPhanBo)}</b> (kế toán phân bổ sau khi xác minh)</span>} />
      <Button type="primary" size="large" disabled={!khach && loaiThu !== 'chua_ro'} onClick={ghi}>5. Ghi phiếu thu &amp; In</Button>
    </Space>
  );
}

function DanhSachThu() {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [chiChuaPb, setChiChuaPb] = useState(false);
  const [mo, setMo] = useState<any>(null);
  const tai = async () => setDs((await goi('phieu_thu:list', { params: { filter: chiChuaPb ? { trang_thai: 'da_ghi', chua_phan_bo: { $gt: 0 } } : {},
    appends: ['khach', 'don_vi'], sort: ['-id'], pageSize: 200 } })).data || []);
  useEffect(() => { tai(); }, [chiChuaPb]);
  const nhanDien = (r: any) => {
    let khach: any;
    modal.confirm({ title: `Nhận diện người nộp ${r.so}`, okText: 'Ghi khách', cancelText: 'Thôi',
      content: <ChonDanhMuc bang="khach_hang" timTheo={['ma', 'ten', 'sdt', 'nhan']} onChange={(v) => (khach = v)} style={{ width: '100%' }} />,
      onOk: () => goi('phieu_thu:nhanDien', { params: { filterByTk: r.id }, data: { khach_id: khach } }).then(() => { message.success('Đã nhận diện — giờ phân bổ được'); tai(); }) });
  };
  return <>
    <Checkbox style={{ marginBottom: 12 }} checked={chiChuaPb} onChange={(e) => setChiChuaPb(e.target.checked)}>Chỉ phiếu còn tiền chưa phân bổ (cọc, tiền thừa, chưa rõ người nộp)</Checkbox>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Số', dataIndex: 'so', render: (v, r) => <a href={`/in/phieu_thu/${r.id}`} target="_blank" rel="noreferrer">{v}</a> },
      { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Loại', dataIndex: 'loai_thu', render: (v) => LOAI_THU[v] || v },
      { title: 'Khách', render: (_, r) => r.khach?.ten || <Tag color="gold">Chưa rõ</Tag> }, { title: 'Đơn vị', render: (_, r) => r.don_vi?.ten },
      { title: 'Hình thức', dataIndex: 'hinh_thuc', render: (v, r) => (v === 'chuyen_khoan' ? `CK ${r.ma_gd || ''}` : 'Tiền mặt') },
      { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) },
      { title: 'Chưa phân bổ', dataIndex: 'chua_phan_bo', align: 'right', render: (v) => (Number(v) ? <b>{fmt(v)}</b> : '') },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{t}</Tag>; } },
      { render: (_, r) => r.trang_thai === 'da_ghi' && <Space wrap>
        {Number(r.chua_phan_bo) > 0 && !r.khach_id && <Button size="small" onClick={() => nhanDien(r)}>Nhận diện khách</Button>}
        {Number(r.chua_phan_bo) > 0 && r.khach_id && <Button size="small" type="primary" onClick={() => setMo({ pt: r, thuHo: false })}>Phân bổ</Button>}
        {Number(r.chua_phan_bo) > 0 && r.khach_id && <Button size="small" onClick={() => setMo({ pt: r, thuHo: true })}>Thu hộ (kế toán)</Button>}
        <Button size="small" danger onClick={() => { let ly_do = ''; modal.confirm({
          title: `Hủy phiếu thu ${r.so}?`, content: <Input.TextArea placeholder="Lý do (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} />,
          okText: 'Hủy phiếu', cancelText: 'Thôi', okButtonProps: { danger: true },
          onOk: () => goi('phieu_thu:huy', { params: { filterByTk: r.id }, data: { ly_do } }).then(tai) }); }}>Hủy</Button></Space> },
    ]} />
    {mo && <PhanBo pt={mo.pt} thuHo={mo.thuHo} onClose={(x: any) => { setMo(null); if (x) tai(); }} />}
  </>;
}

function ThuHo() {
  const goi = useGoi();
  const { modal } = App.useApp();
  const [ds, setDs] = useState<any[] | null>(null);
  const tai = () => goi('thu_ho:list', { params: { appends: ['phieu_thu', 'don_vi_nhan', 'don_vi_chu_no', 'don_ban'], sort: ['-id'], pageSize: 500 }, im: true })
    .then((r) => setDs(r.data || [])).catch(() => setDs([]));
  useEffect(() => { tai(); }, []);
  return <>
    <Typography.Paragraph type="secondary">Tiền một đơn vị nhận nhưng trả nợ đơn của đơn vị khác. Khoản này là đơn vị nhận tiền đang giữ hộ; tất toán khi hai đơn vị chuyển trả / bù trừ có chứng từ.</Typography.Paragraph>
    <Table size="small" rowKey="id" loading={!ds} dataSource={ds || []} columns={[
      { title: 'Phiếu thu', render: (_, r) => r.phieu_thu?.so }, { title: 'Đơn được trả', render: (_, r) => r.don_ban?.so },
      { title: 'Đơn vị giữ tiền', render: (_, r) => r.don_vi_nhan?.ten }, { title: 'Giữ hộ cho', render: (_, r) => r.don_vi_chu_no?.ten },
      { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => <b>{fmt(v)}</b> },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => <Tag color={({ dang_giu_ho: 'orange', da_tat_toan: 'green', da_huy: 'red' } as any)[v]}>
        {({ dang_giu_ho: 'Đang giữ hộ', da_tat_toan: 'Đã tất toán', da_huy: 'Đã hủy' } as any)[v]}</Tag> },
      { title: 'Ghi chú', dataIndex: 'ghi_chu' },
      { render: (_, r) => r.trang_thai === 'dang_giu_ho' && <Button size="small" onClick={() => { let ghi_chu = ''; modal.confirm({
        title: 'Tất toán khoản thu hộ?', okText: 'Tất toán', cancelText: 'Thôi',
        content: <Input.TextArea placeholder="Căn cứ (số phiếu chi / UNC giữa hai đơn vị)" onChange={(e) => (ghi_chu = e.target.value)} />,
        onOk: () => goi('thu_ho:tatToan', { params: { filterByTk: r.id }, data: { ghi_chu } }).then(tai) }); }}>Tất toán</Button> },
    ]} />
  </>;
}

function CongNo() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [q, setQ] = useState('');
  useEffect(() => {
    Promise.all([
      goi('don_ban:list', { params: { filter: { trang_thai: { $in: CON_NO }, con_no: { $ne: 0 } }, appends: ['khach', 'don_vi_ban'], pageSize: 5000 } }),
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

const huyPhieu = (modal: any, goi: any, url: string, r: any, xong: any) => {
  let ly_do = '';
  modal.confirm({ title: `Hủy ${r.so}?`, content: <Input.TextArea placeholder="Lý do (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} />,
    okText: 'Hủy phiếu', cancelText: 'Thôi', okButtonProps: { danger: true }, onOk: () => goi(url, { params: { filterByTk: r.id }, data: { ly_do } }).then(xong) });
};
const tienVao = { formatter: (v: any) => fmt(v), parser: (v: any) => Number(String(v).replace(/\D/g, '')) };

function PhieuChi() {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [form] = Form.useForm();
  const [ds, setDs] = useState<any[]>([]);
  const donVi = Form.useWatch('don_vi_id', form);
  const loaiChi = Form.useWatch('loai_chi', form);
  const ncc = Form.useWatch('nha_cung_cap_id', form);
  const tai = async () => setDs((await goi('phieu_chi:list', { params: { appends: ['don_vi', 'quy'], sort: ['-id'], pageSize: 200 } })).data || []);
  useEffect(() => { tai(); form.setFieldsValue({ ngay: dayjs(homNay()), loai_chi: 'khac' }); }, []);
  const ghi = async () => {
    const v = await form.validateFields();
    modal.confirm({ title: `Chi ${fmt(v.so_tien)} đ cho ${v.nguoi_nhan}?`, okText: 'Ghi & In phiếu chi', cancelText: 'Xem lại', onOk: async () => {
      const r = await goi('phieu_chi:create', { data: { ...v, ngay: v.ngay.format('YYYY-MM-DD') } });
      try { await goi('phieu_chi:ghi', { params: { filterByTk: r.data.id }, data: {} }); } catch { tai(); return; }
      window.open(`/in/phieu_chi/${r.data.id}`, '_blank'); message.success('Đã ghi phiếu chi'); form.resetFields(['so_tien', 'nguoi_nhan', 'ly_do', 'ma_gd']); tai();
    } });
  };
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Form form={form} layout="vertical">
        <Row gutter={12}>
          <Col span={6}><Form.Item name="don_vi_id" label="Đơn vị chi" rules={[{ required: true }]}><ChonDanhMuc bang="don_vi" style={{ width: '100%' }} /></Form.Item></Col>
          <Col span={6}><Form.Item name="quy_id" label="Chi từ quỹ / tài khoản" rules={[{ required: true }]}>
            <ChonDanhMuc bang="quy" style={{ width: '100%' }} locThem={{ don_vi_id: donVi || 0, ngung_dung: { $ne: true } }} /></Form.Item></Col>
          <Col span={5}><Form.Item name="loai_chi" label="Loại chi"><Select options={[{ value: 'mua_hang', label: 'Trả tiền mua hàng' }, { value: 'van_chuyen', label: 'Vận chuyển' },
            { value: 'san_xuat', label: 'Chi phí sản xuất' }, { value: 'luong', label: 'Lương / công' }, { value: 'hoan_khach', label: 'Hoàn tiền khách' }, { value: 'khac', label: 'Chi khác' }]} /></Form.Item></Col>
          <Col span={4}><Form.Item name="so_tien" label="Số tiền (đ)" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} {...tienVao} /></Form.Item></Col>
          <Col span={3}><Form.Item name="ngay" label="Ngày"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
        </Row>
        {loaiChi === 'mua_hang' && <Row gutter={12}>
          <Col span={8}><Form.Item name="nha_cung_cap_id" label="Nhà cung cấp" rules={[{ required: true, message: 'Chọn NCC' }]}>
            <ChonDanhMuc bang="nha_cung_cap" timTheo={['ma', 'ten', 'sdt', 'nhan']} style={{ width: '100%' }} /></Form.Item></Col>
          <Col span={8}><Form.Item name="phieu_kho_id" label="Trả cho phiếu nhập (trống = trả chung NCC)">
            <ChonDanhMuc bang="phieu_kho" nhan="so" timTheo={['so', 'chung_tu_ncc']} style={{ width: '100%' }}
              locThem={{ loai: 'nhap', trang_thai: 'da_ghi', nha_cung_cap_id: ncc || 0 }} /></Form.Item></Col>
        </Row>}
        <Row gutter={12}>
          <Col span={6}><Form.Item name="nguoi_nhan" label="Người nhận tiền" rules={[{ required: true }]}><Input /></Form.Item></Col>
          <Col span={12}><Form.Item name="ly_do" label="Lý do chi" rules={[{ required: true }]}><Input /></Form.Item></Col>
          <Col span={6}><Form.Item name="ma_gd" label="Mã GD (nếu chi qua ngân hàng)"><Input /></Form.Item></Col>
        </Row>
      </Form>
      <Button type="primary" size="large" onClick={ghi}>Ghi phiếu chi &amp; In</Button>
      <Table size="small" rowKey="id" dataSource={ds} columns={[
        { title: 'Số', dataIndex: 'so', render: (v, r) => <a href={`/in/phieu_chi/${r.id}`} target="_blank" rel="noreferrer">{v}</a> },
        { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Đơn vị', render: (_, r) => r.don_vi?.ten }, { title: 'Quỹ', render: (_, r) => r.quy?.ten },
        { title: 'Người nhận', dataIndex: 'nguoi_nhan' }, { title: 'Lý do', dataIndex: 'ly_do' },
        { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) },
        { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{t}</Tag>; } },
        { render: (_, r) => r.trang_thai !== 'da_huy' && <Button size="small" danger onClick={() => huyPhieu(modal, goi, 'phieu_chi:huy', r, tai)}>Hủy</Button> },
      ]} />
    </Space>
  );
}

function ChuyenTien() {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [form] = Form.useForm();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('chuyen_tien:list', { params: { appends: ['tu_quy', 'den_quy'], sort: ['-id'], pageSize: 200 } })).data || []);
  useEffect(() => { tai(); form.setFieldsValue({ ngay: dayjs(homNay()) }); }, []);
  const ghi = async () => {
    const v = await form.validateFields();
    const r = await goi('chuyen_tien:create', { data: { ...v, ngay: v.ngay.format('YYYY-MM-DD') } });
    try { await goi('chuyen_tien:ghi', { params: { filterByTk: r.data.id }, data: {} }); message.success('Đã ghi bàn giao'); form.resetFields(['so_tien', 'ghi_chu']); } catch { /* đã báo */ }
    tai();
  };
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Typography.Text type="secondary">Bàn giao / nộp tiền giữa hai quỹ CÙNG một đơn vị (thu ngân nộp kế toán, nộp tiền mặt vào ngân hàng, rút tiền về quỹ).</Typography.Text>
      <Form form={form} layout="vertical"><Row gutter={12}>
        <Col span={6}><Form.Item name="tu_quy_id" label="Từ quỹ" rules={[{ required: true }]}><ChonDanhMuc bang="quy" style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={6}><Form.Item name="den_quy_id" label="Đến quỹ" rules={[{ required: true }]}><ChonDanhMuc bang="quy" style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={4}><Form.Item name="so_tien" label="Số tiền" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} {...tienVao} /></Form.Item></Col>
        <Col span={4}><Form.Item name="nguoi_giao" label="Người giao"><Input /></Form.Item></Col>
        <Col span={4}><Form.Item name="nguoi_nhan" label="Người nhận"><Input /></Form.Item></Col>
      </Row><Row gutter={12}>
        <Col span={4}><Form.Item name="ngay" label="Ngày"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={14}><Form.Item name="ghi_chu" label="Ghi chú"><Input /></Form.Item></Col>
      </Row></Form>
      <Button type="primary" onClick={() => modal.confirm({ title: 'Ghi bàn giao tiền?', okText: 'Ghi', cancelText: 'Thôi', onOk: ghi })}>Ghi bàn giao</Button>
      <Table size="small" rowKey="id" dataSource={ds} columns={[
        { title: 'Số', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
        { title: 'Từ', render: (_, r) => r.tu_quy?.ten }, { title: 'Đến', render: (_, r) => r.den_quy?.ten },
        { title: 'Giao → nhận', render: (_, r) => `${r.nguoi_giao || ''} → ${r.nguoi_nhan || ''}` },
        { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) },
        { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{t}</Tag>; } },
        { render: (_, r) => r.trang_thai === 'da_ghi' && <Button size="small" danger onClick={() => huyPhieu(modal, goi, 'chuyen_tien:huy', r, tai)}>Hủy</Button> },
      ]} />
    </Space>
  );
}

function SoQuy() {
  const goi = useGoi();
  const [quy, setQuy] = useState<any[]>([]);
  const [chon, setChon] = useState<any>();
  const [dong, setDong] = useState<any[]>([]);
  useEffect(() => {
    Promise.all([goi('quy:list', { params: { appends: ['don_vi'], pageSize: 200, sort: ['don_vi_id', 'ma'] } }),
      goi('so_quy:list', { params: { pageSize: 20000, fields: ['quy_id', 'so_tien'] } })]).then(([q, l]) => {
      const du: Record<string, number> = {};
      (l.data || []).forEach((x: any) => (du[x.quy_id] = (du[x.quy_id] || 0) + Number(x.so_tien || 0)));
      setQuy((q.data || []).map((x: any) => ({ ...x, du: du[x.id] || 0 })));
    });
  }, []);
  useEffect(() => {
    if (!chon) return setDong([]);
    goi('so_quy:list', { params: { filter: { quy_id: chon }, sort: ['id'], pageSize: 5000 } }).then((r) => {
      let du = 0;
      setDong((r.data || []).map((x: any) => ({ ...x, du: (du += Number(x.so_tien || 0)) })));
    });
  }, [chon]);
  return (
    <Row gutter={16}>
      <Col span={9}><Table size="small" rowKey="id" pagination={false} dataSource={quy} rowClassName={(r) => (r.id === chon ? 'ant-table-row-selected' : '')}
        onRow={(r) => ({ onClick: () => setChon(r.id), style: { cursor: 'pointer' } })} columns={[
          { title: 'Đơn vị', render: (_, r) => r.don_vi?.ma }, { title: 'Quỹ / tài khoản', dataIndex: 'ten' },
          { title: 'Số dư', dataIndex: 'du', align: 'right', render: (v) => <b style={{ color: v < 0 ? '#cf1322' : undefined }}>{fmt(v)}</b> }]} /></Col>
      <Col span={15}>{chon ? <Table size="small" rowKey="id" dataSource={dong} pagination={{ pageSize: 50 }} columns={[
        { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Chứng từ', dataIndex: 'chung_tu' }, { title: 'Diễn giải', dataIndex: 'dien_giai' },
        { title: 'Thu', align: 'right', render: (_, r) => (r.so_tien > 0 ? fmt(r.so_tien) : '') },
        { title: 'Chi', align: 'right', render: (_, r) => (r.so_tien < 0 ? fmt(-r.so_tien) : '') },
        { title: 'Tồn quỹ', dataIndex: 'du', align: 'right', render: (v) => <b>{fmt(v)}</b> }]} />
        : <Typography.Text type="secondary">Bấm một quỹ để xem sổ chi tiết.</Typography.Text>}</Col>
    </Row>
  );
}

function ChotCa() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('chot_ca:list', { params: { appends: ['quy'], sort: ['-id'], pageSize: 100 } })).data || []);
  useEffect(() => { tai(); }, []);
  const chot = async () => {
    const v = await form.validateFields();
    try {
      const r = await goi('chot_ca:chot', { data: v });
      message.success(`Đã chốt ca: sổ ${fmt(r.data.so_sach)} đ, lệch ${fmt(r.data.chenh_lech)} đ`, 8);
      form.resetFields(); tai();
    } catch { /* đã báo */ }
  };
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Typography.Text type="secondary">Đếm tiền thực có trong két rồi nhập. Hệ thống so với số theo sổ quỹ; lệch phải ghi lý do. Chốt ca chỉ ghi nhận, không tự sửa sổ.</Typography.Text>
      <Form form={form} layout="inline">
        <Form.Item name="quy_id" label="Quỹ tiền mặt" rules={[{ required: true }]}><ChonDanhMuc bang="quy" locThem={{ loai: 'tien_mat' }} style={{ width: 260 }} /></Form.Item>
        <Form.Item name="thuc_dem" label="Tiền thực đếm" rules={[{ required: true }]}><InputNumber min={0} style={{ width: 180 }} {...tienVao} /></Form.Item>
        <Form.Item name="ly_do" label="Lý do lệch"><Input style={{ width: 260 }} /></Form.Item>
        <Button type="primary" onClick={chot}>Chốt ca</Button>
      </Form>
      <Table size="small" rowKey="id" dataSource={ds} columns={[
        { title: 'Số', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Quỹ', render: (_, r) => r.quy?.ten },
        { title: 'Theo sổ', dataIndex: 'so_sach', align: 'right', render: (v) => fmt(v) }, { title: 'Thực đếm', dataIndex: 'thuc_dem', align: 'right', render: (v) => fmt(v) },
        { title: 'Lệch', dataIndex: 'chenh_lech', align: 'right', render: (v) => <b style={{ color: v ? '#cf1322' : undefined }}>{fmt(v)}</b> },
        { title: 'Lý do', dataIndex: 'ly_do' }, { title: 'Người chốt', dataIndex: 'nguoi_chot' }]} />
    </Space>
  );
}

function CongNoNcc() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[] | null>(null);
  useEffect(() => { goi('phieu_kho:list', { params: { filter: { loai: 'nhap', trang_thai: 'da_ghi' }, appends: ['nha_cung_cap', 'kho'], sort: ['-ngay'], pageSize: 2000 }, im: true })
    .then((r) => setDs((r.data || []).filter((x: any) => x.phai_tra === undefined || Number(x.phai_tra || 0) - Number(x.da_tra || 0) !== 0))).catch(() => setDs([])); }, []);
  const anGia = (ds || []).some((x) => x.phai_tra === undefined);
  if (anGia) return <Typography.Text type="secondary">Chỉ kế toán / quản lý xem số phải trả nhà cung cấp.</Typography.Text>;
  return <Table size="small" rowKey="id" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 50 }} columns={[
    { title: 'Phiếu nhập', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'NCC', render: (_, r) => r.nha_cung_cap?.ten || '—' },
    { title: 'Chứng từ NCC', dataIndex: 'chung_tu_ncc' }, { title: 'Phải trả', dataIndex: 'phai_tra', align: 'right', render: (v) => fmt(v) },
    { title: 'Đã trả', dataIndex: 'da_tra', align: 'right', render: (v) => fmt(v) },
    { title: 'Còn phải trả', align: 'right', render: (_, r) => <b>{fmt(Number(r.phai_tra || 0) - Number(r.da_tra || 0))}</b> },
  ]} />;
}

export function ThuTien() {
  const [ban, setBan] = useState(0);
  return (
    <Card title="Thu chi và công nợ">
      <Tabs items={[
        { key: 'thu', label: 'Ghi nhận khách trả tiền', children: <GhiThu key={ban} xong={() => setBan(ban + 1)} /> },
        { key: 'ds', label: 'Phiếu thu', children: <DanhSachThu key={ban} /> },
        { key: 'cn', label: 'Công nợ khách', children: <CongNo key={ban} /> },
        { key: 'th', label: 'Thu hộ giữa đơn vị', children: <ThuHo key={ban} /> },
        { key: 'ncc', label: 'Công nợ NCC', children: <CongNoNcc /> },
        { key: 'chi', label: 'Phiếu chi', children: <PhieuChi /> },
        { key: 'ct', label: 'Bàn giao / nộp tiền', children: <ChuyenTien /> },
        { key: 'sq', label: 'Sổ quỹ', children: <SoQuy /> },
        { key: 'cc', label: 'Chốt ca tiền', children: <ChotCa /> },
      ]} />
    </Card>
  );
}
