/** Quản lý tài sản / công cụ dụng cụ vận hành (người giữ, địa điểm, bảo trì, thanh lý). MISA vẫn hạch toán & khấu hao chính thức. */
import { App, Button, Card, Checkbox, Col, DatePicker, Drawer, Form, Input, InputNumber, Modal, Row, Select, Space, Table, Tabs, Tag, Typography } from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, fmt, homNay, ngayVN, useGoi } from './chung';

const LOAI: Record<string, string> = { tscd: 'TSCĐ', ccdc: 'CCDC', van_phong: 'Thiết bị văn phòng' };
const TT: Record<string, [string, string]> = { dang_dung: ['Đang dùng', 'green'], trong_kho: ['Trong kho', 'blue'], hong: ['Hỏng / chờ sửa', 'orange'],
  cho_thanh_ly: ['Chờ thanh lý', 'purple'], da_thanh_ly: ['Đã thanh lý', 'default'], mat: ['Mất', 'red'] };
const SU_KIEN: Record<string, string> = { ban_giao: 'Bàn giao người giữ', dieu_chuyen: 'Điều chuyển địa điểm', cap_phat: 'Cấp phát CCDC', thu_hoi: 'Thu hồi về kho',
  bao_tri: 'Bảo trì', sua_chua: 'Sửa chữa', bao_hong: 'Báo hỏng', de_nghi_thanh_ly: 'Đề nghị thanh lý', thanh_ly: 'Thanh lý (kế toán duyệt)', bao_mat: 'Báo mất' };

function ChiTiet({ id, xong }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ts, setTs] = useState<any>(null);
  const [mo, setMo] = useState(false);
  const [form] = Form.useForm();
  const loai = Form.useWatch('loai', form);
  const tai = async () => setTs((await goi('tai_san:get', { params: { filterByTk: id, appends: ['su_kien', 'don_vi_so_huu'] } })).data);
  useEffect(() => { tai(); }, [id]);
  if (!ts) return null;
  return <Space direction="vertical" style={{ width: '100%' }}>
    <Typography.Title level={4} style={{ margin: 0 }}>{ts.ma} — {ts.ten} <Tag color={TT[ts.tinh_trang]?.[1]}>{TT[ts.tinh_trang]?.[0]}</Tag></Typography.Title>
    <Row gutter={12}>{[['Loại', LOAI[ts.loai]], ['Serial', ts.serial], ['Địa điểm', ts.dia_diem], ['Người giữ', ts.nguoi_quan_ly], ['Bộ phận', ts.bo_phan],
      ['Ngày mua', ngayVN(ts.ngay_mua)], ['Nguyên giá', ts.nguyen_gia !== undefined ? fmt(ts.nguyen_gia) : '—'], ['Số lượng', ts.so_luong ? fmt(ts.so_luong) : ''],
      ['Đơn vị đứng tên', ts.don_vi_so_huu?.ma || 'Chưa xác định'], ['Bảo trì kế tiếp', ngayVN(ts.ngay_bao_tri)], ['Chứng từ mua', ts.chung_tu_mua]]
      .map(([a, b]) => <Col span={6} key={a}><Typography.Text type="secondary">{a}</Typography.Text><div><b>{b || '—'}</b></div></Col>)}</Row>
    <Button type="primary" onClick={() => { form.resetFields(); form.setFieldsValue({ ngay: dayjs(homNay()), loai: 'ban_giao' }); setMo(true); }}>+ Ghi sự kiện</Button>
    <Table size="small" rowKey="id" pagination={false} dataSource={(ts.su_kien || []).sort((a: any, b: any) => b.id - a.id)} columns={[
      { title: 'Số', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Nghiệp vụ', dataIndex: 'loai', render: (v) => SU_KIEN[v] },
      { title: 'Người nhận', dataIndex: 'nguoi_nhan' }, { title: 'Địa điểm mới', dataIndex: 'dia_diem_moi' }, { title: 'Chi phí', dataIndex: 'chi_phi', render: (v) => (v ? fmt(v) : '') },
      { title: 'Ghi chú', dataIndex: 'ghi_chu' }, { title: 'Người ghi', dataIndex: 'ghi_boi' },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => <Tag color={v === 'da_ghi' ? 'green' : v === 'da_huy' ? 'red' : 'default'}>{v === 'da_ghi' ? 'Đã ghi' : v === 'da_huy' ? 'Đã hủy' : 'Nháp'}</Tag> },
    ]} />
    <Modal open={mo} title="Ghi sự kiện tài sản" okText="Ghi" cancelText="Thôi" onCancel={() => setMo(false)} onOk={async () => {
      const v = await form.validateFields();
      const r = await goi('tai_san_su_kien:create', { data: { ...v, tai_san_id: ts.id, ngay: v.ngay?.format('YYYY-MM-DD'), ngay_bao_tri_tiep: v.ngay_bao_tri_tiep?.format('YYYY-MM-DD') } });
      try { await goi('tai_san_su_kien:ghi', { params: { filterByTk: r.data.id }, data: {} }); message.success('Đã ghi'); } catch { /* đã báo; sự kiện ở nháp */ }
      setMo(false); tai(); xong?.();
    }}>
      <Form form={form} layout="vertical">
        <Form.Item name="loai" label="Nghiệp vụ" rules={[{ required: true }]}><Select options={Object.entries(SU_KIEN).map(([value, label]) => ({ value, label }))} /></Form.Item>
        <Form.Item name="ngay" label="Ngày"><DatePicker format="DD/MM/YYYY" /></Form.Item>
        {['ban_giao', 'dieu_chuyen', 'cap_phat'].includes(loai) && <Form.Item name="nguoi_nhan" label="Người nhận / người giữ mới"><Input /></Form.Item>}
        {['ban_giao', 'dieu_chuyen', 'thu_hoi'].includes(loai) && <Form.Item name="dia_diem_moi" label="Địa điểm mới"><Input /></Form.Item>}
        {['cap_phat', 'thu_hoi'].includes(loai) && <Form.Item name="so_luong" label="Số lượng"><InputNumber min={1} /></Form.Item>}
        {['bao_tri', 'sua_chua'].includes(loai) && <><Form.Item name="chi_phi" label="Chi phí"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="ngay_bao_tri_tiep" label="Hẹn bảo trì kế tiếp"><DatePicker format="DD/MM/YYYY" /></Form.Item></>}
        <Form.Item name="ghi_chu" label="Ghi chú / lý do" rules={['de_nghi_thanh_ly', 'bao_mat', 'thanh_ly'].includes(loai) ? [{ required: true, message: 'Bắt buộc' }] : []}>
          <Input.TextArea /></Form.Item>
      </Form>
    </Modal>
  </Space>;
}

function DanhSach() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [mo, setMo] = useState<any>(null);
  const [them, setThem] = useState(false);
  const [form] = Form.useForm();
  const tai = async () => {
    const f = q ? { $or: ['ma', 'ten', 'dia_diem', 'nguoi_quan_ly', 'serial'].map((k) => ({ [k]: { $includes: q } })) } : {};
    setDs((await goi('tai_san:list', { params: { filter: f, sort: ['ma'], pageSize: 2000 } })).data || []);
  };
  useEffect(() => { tai(); }, []);
  const homnay = homNay();
  return <>
    <Space style={{ marginBottom: 12 }} wrap>
      <Input.Search placeholder="Mã, tên, địa điểm, người giữ, serial" allowClear onSearch={(v) => { setQ(v); setTimeout(tai); }} style={{ width: 320 }} />
      <Button type="primary" onClick={() => { form.resetFields(); form.setFieldsValue({ loai: 'tscd', tinh_trang: 'dang_dung' }); setThem(true); }}>+ Thêm tài sản</Button>
      <Typography.Text type="secondary">Nhập hàng loạt: Go-Live → Nhập dữ liệu → "Tài sản / CCDC".</Typography.Text>
    </Space>
    <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 50 }} onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Mã', dataIndex: 'ma', render: (v) => <b>{v}</b> }, { title: 'Tên', dataIndex: 'ten' }, { title: 'Loại', dataIndex: 'loai', render: (v) => LOAI[v] },
      { title: 'Địa điểm', dataIndex: 'dia_diem' }, { title: 'Người giữ', dataIndex: 'nguoi_quan_ly' },
      { title: 'Tình trạng', dataIndex: 'tinh_trang', render: (v) => <Tag color={TT[v]?.[1]}>{TT[v]?.[0]}</Tag> },
      { title: 'Bảo trì kế tiếp', dataIndex: 'ngay_bao_tri', render: (v) => (v ? <span style={{ color: v <= homnay ? '#cf1322' : undefined }}>{ngayVN(v)}</span> : '') },
    ]} />
    <Drawer width="80%" open={!!mo} onClose={() => { setMo(null); tai(); }} title="Tài sản" destroyOnClose>{mo && <ChiTiet id={mo} xong={tai} />}</Drawer>
    <Modal open={them} title="Thêm tài sản / CCDC" okText="Lưu" cancelText="Thôi" onCancel={() => setThem(false)} width={720} onOk={async () => {
      const v = await form.validateFields();
      await goi('tai_san:create', { data: { ...v, ngay_mua: v.ngay_mua?.format('YYYY-MM-DD') } });
      message.success('Đã thêm'); setThem(false); tai();
    }}>
      <Form form={form} layout="vertical"><Row gutter={12}>
        <Col span={8}><Form.Item name="ma" label="Mã" rules={[{ required: true }]}><Input /></Form.Item></Col>
        <Col span={16}><Form.Item name="ten" label="Tên" rules={[{ required: true }]}><Input /></Form.Item></Col>
        <Col span={8}><Form.Item name="loai" label="Loại"><Select options={Object.entries(LOAI).map(([value, label]) => ({ value, label }))} /></Form.Item></Col>
        <Col span={8}><Form.Item name="serial" label="Serial"><Input /></Form.Item></Col>
        <Col span={8}><Form.Item name="tinh_trang" label="Tình trạng ban đầu"><Select options={Object.entries(TT).map(([value, [label]]) => ({ value, label }))} /></Form.Item></Col>
        <Col span={8}><Form.Item name="dia_diem" label="Địa điểm"><Input /></Form.Item></Col>
        <Col span={8}><Form.Item name="nguoi_quan_ly" label="Người giữ"><Input /></Form.Item></Col>
        <Col span={8}><Form.Item name="bo_phan" label="Bộ phận"><Input /></Form.Item></Col>
        <Col span={8}><Form.Item name="ngay_mua" label="Ngày mua"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={8}><Form.Item name="nguyen_gia" label="Nguyên giá tham khảo"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={8}><Form.Item name="so_thang_sd" label="Thời gian dùng ước tính (tháng)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={8}><Form.Item name="so_luong" label="Số lượng (CCDC)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={8}><Form.Item name="don_vi_so_huu_id" label="Đơn vị đứng tên (nếu rõ)"><ChonDanhMuc bang="don_vi" style={{ width: '100%' }} /></Form.Item></Col>
        <Col span={8}><Form.Item name="chung_tu_mua" label="Chứng từ mua"><Input /></Form.Item></Col>
        <Col span={12}><Form.Item name="dung_cho_san_xuat" valuePropName="checked"><Checkbox>Dùng cho sản xuất (ước tính chi phí giá thành)</Checkbox></Form.Item></Col>
      </Row></Form>
    </Modal>
  </>;
}

function UocTinh() {
  const goi = useGoi();
  const [thang, setThang] = useState<any>(dayjs(homNay()));
  const [ds, setDs] = useState<any[] | null>(null);
  const [loi, setLoi] = useState('');
  useEffect(() => {
    goi('tai_san:uocTinh', { data: { thang: thang?.format('YYYY-MM') }, im: true }).then((r) => { setLoi(''); setDs(r.data || []); })
      .catch((e) => { setLoi(e?.response?.data?.errors?.[0]?.message || 'Không xem được'); setDs([]); });
  }, [thang?.valueOf()]);
  if (loi) return <Typography.Text type="secondary">{loi}</Typography.Text>;
  const sx = (ds || []).filter((x) => x.dung_cho_san_xuat).reduce((s, x) => s + Number(x.chi_phi_thang || 0), 0);
  return <>
    <Space style={{ marginBottom: 12 }}><DatePicker picker="month" value={thang} onChange={setThang} format="MM/YYYY" />
      <span>Tài sản dùng cho sản xuất: <b>{fmt(sx)} đ/tháng</b> (ghi vào mẻ ở khoản "Khấu hao / chi phí tài sản" nếu kế toán trưởng duyệt)</span></Space>
    <Typography.Paragraph type="secondary">Ước tính quản trị = nguyên giá / số tháng dùng, trong thời gian dùng. Không phải khấu hao kế toán, không sinh bút toán — MISA hạch toán chính thức.</Typography.Paragraph>
    <Table size="small" rowKey="id" loading={!ds} dataSource={ds || []} pagination={{ pageSize: 50 }} columns={[
      { title: 'Mã', dataIndex: 'ma' }, { title: 'Tên', dataIndex: 'ten' }, { title: 'Địa điểm', dataIndex: 'dia_diem' },
      { title: 'Sản xuất', dataIndex: 'dung_cho_san_xuat', render: (v) => (v ? '✓' : '') }, { title: 'Ngày mua', dataIndex: 'ngay_mua', render: ngayVN },
      { title: 'Nguyên giá', dataIndex: 'nguyen_gia', align: 'right', render: (v) => fmt(v) }, { title: 'Số tháng', dataIndex: 'so_thang_sd', align: 'right' },
      { title: 'Chi phí ước tính tháng', dataIndex: 'chi_phi_thang', align: 'right', render: (v) => <b>{fmt(v)}</b> },
    ]} />
  </>;
}

export function TaiSan() {
  return <Card title="Tài sản & công cụ dụng cụ">
    <Tabs items={[{ key: 'ds', label: 'Danh sách', children: <DanhSach /> }, { key: 'ut', label: 'Chi phí sử dụng ước tính', children: <UocTinh /> }]} />
  </Card>;
}
