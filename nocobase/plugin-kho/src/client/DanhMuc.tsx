/** Danh mục: mặt hàng, khách hàng, kho, đơn vị; công nợ đầu kỳ. Thêm/sửa và dán nhanh từ Excel (cập nhật theo mã). */
import { App, Button, Card, Checkbox, Form, Input, InputNumber, Modal, Select, Space, Table, Tabs, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, fmt, useGoi } from './chung';

/** Đọc số dán từ Excel: "1.234.567" / "1,5" / "25.5" / "1.234,5". */
export const docSo = (v: string) => {
  v = v.replace(/\s|đ/g, '');
  if (!v) return null;
  if (v.includes('.') && v.includes(',')) return Number(v.replace(/\./g, '').replace(',', '.'));
  if (v.includes(',')) return /^\d{1,3}(,\d{3})+$/.test(v) ? Number(v.replace(/,/g, '')) : Number(v.replace(',', '.'));
  if (/^\d{1,3}(\.\d{3})+$/.test(v)) return Number(v.replace(/\./g, ''));
  return Number(v);
};

type Cot = { key: string; title: string; kieu?: 'so' | 'chu' | 'co' | 'dai' | 'don_vi' | 'loai_quy' | 'chon'; bat_buoc?: boolean; rong?: number; chon?: Record<string, string> };
const DVT_TON = { kg: 'Kg', cai: 'Cái', goi: 'Gói', bao: 'Bao', thung: 'Thùng' };
const LOAI_HANG = { hang_hoa: 'Hàng hóa', nguyen_lieu: 'Nguyên liệu', thanh_pham: 'Thành phẩm', phu_pham: 'Phụ phẩm', bao_bi: 'Bao bì / vật tư' };
const LOAI_KHO = { ban_duoc: 'Kho bán được', nha_may: 'Kho nhà máy', cho_xu_ly: 'Kho chờ xử lý (không bán)' };
const BANG: Record<string, { ten: string; cot: Cot[]; tim: string[] }> = {
  mat_hang: { ten: 'Mặt hàng', tim: ['ma', 'ten'], cot: [
    { key: 'ma', title: 'Mã hàng', bat_buoc: true, rong: 140 }, { key: 'ten', title: 'Tên hàng', bat_buoc: true },
    { key: 'dvt_ton', title: 'ĐVT tồn', kieu: 'chon', chon: DVT_TON, rong: 90 }, { key: 'loai_hang', title: 'Loại hàng', kieu: 'chon', chon: LOAI_HANG, rong: 130 },
    { key: 'kg_bao', title: 'Kg/bao', kieu: 'so', rong: 90 },
    { key: 'gia_ban', title: 'Giá bán (đ/ĐVT)', kieu: 'so', rong: 130 }, { key: 'gia_san', title: 'Giá sàn (đ/ĐVT)', kieu: 'so', rong: 130 },
    { key: 'ngung_dung', title: 'Ngừng dùng', kieu: 'co', rong: 100 }] },
  khach_hang: { ten: 'Khách hàng', tim: ['ma', 'ten', 'sdt'], cot: [
    { key: 'ma', title: 'Mã khách', bat_buoc: true, rong: 120 }, { key: 'ten', title: 'Tên khách', bat_buoc: true },
    { key: 'sdt', title: 'Điện thoại', rong: 130 }, { key: 'dia_chi', title: 'Địa chỉ', kieu: 'dai' }, { key: 'mst', title: 'MST', rong: 120 },
    { key: 'han_muc', title: 'Hạn mức nợ (đ, 0 = không)', kieu: 'so', rong: 140 }, { key: 'ghi_chu', title: 'Ghi chú', kieu: 'dai' }] },
  nha_cung_cap: { ten: 'Nhà cung cấp', tim: ['ma', 'ten', 'sdt'], cot: [
    { key: 'ma', title: 'Mã NCC', bat_buoc: true, rong: 120 }, { key: 'ten', title: 'Tên nhà cung cấp', bat_buoc: true },
    { key: 'sdt', title: 'Điện thoại', rong: 130 }, { key: 'dia_chi', title: 'Địa chỉ', kieu: 'dai' }, { key: 'mst', title: 'MST', rong: 120 },
    { key: 'ghi_chu', title: 'Ghi chú', kieu: 'dai' }] },
  kho: { ten: 'Kho', tim: ['ma', 'ten'], cot: [
    { key: 'ma', title: 'Mã kho', bat_buoc: true, rong: 120 }, { key: 'ten', title: 'Tên kho', bat_buoc: true },
    { key: 'loai_kho', title: 'Loại kho', kieu: 'chon', chon: LOAI_KHO, rong: 190 }, { key: 'dia_diem', title: 'Địa điểm', rong: 160 },
    { key: 'ngung_dung', title: 'Ngừng dùng', kieu: 'co', rong: 100 }, { key: 'ghi_chu', title: 'Ghi chú', kieu: 'dai' }] },
  quy: { ten: 'Quỹ / tài khoản tiền', tim: ['ma', 'ten'], cot: [
    { key: 'ma', title: 'Mã quỹ', bat_buoc: true, rong: 120 }, { key: 'ten', title: 'Tên quỹ / tài khoản', bat_buoc: true },
    { key: 'don_vi_id', title: 'Đơn vị', kieu: 'don_vi', bat_buoc: true, rong: 220 }, { key: 'loai', title: 'Loại', kieu: 'loai_quy', bat_buoc: true, rong: 120 },
    { key: 'nguoi_giu', title: 'Người giữ quỹ', rong: 160 }, { key: 'ngung_dung', title: 'Ngừng dùng', kieu: 'co', rong: 100 }] },
  don_vi: { ten: 'Đơn vị bán', tim: ['ma', 'ten'], cot: [
    { key: 'ma', title: 'Mã', bat_buoc: true, rong: 100 }, { key: 'ten', title: 'Tên đơn vị', bat_buoc: true },
    { key: 'mst', title: 'MST', rong: 130 }, { key: 'dia_chi', title: 'Địa chỉ', kieu: 'dai' }, { key: 'dien_thoai', title: 'Điện thoại', rong: 130 }] },
};

function BangDanhMuc({ bang }: { bang: string }) {
  const goi = useGoi();
  const { message } = App.useApp();
  const cfg = BANG[bang];
  const [ds, setDs] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [sua, setSua] = useState<any>(null);
  const [dan, setDan] = useState(false);
  const [text, setText] = useState('');
  const [form] = Form.useForm();
  const tai = async () => {
    const filter = q ? { $or: cfg.tim.map((t) => ({ [t]: { $includes: q } })) } : {};
    setDs((await goi(`${bang}:list`, { params: { filter, sort: ['ma'], pageSize: 2000, ...(bang === 'quy' ? { appends: ['don_vi'] } : {}) } })).data || []);
  };
  useEffect(() => { tai(); }, [bang]);
  const luu = async () => {
    const v = await form.validateFields();
    if (sua?.id) await goi(`${bang}:update`, { params: { filterByTk: sua.id }, data: v });
    else await goi(`${bang}:create`, { data: v });
    message.success('Đã lưu');
    setSua(null);
    tai();
  };
  const nhapExcel = async () => {
    const dong = text.split(/\r?\n/).map((l) => l.split('\t')).filter((c) => c.some((x) => x.trim()));
    if (!dong.length) return;
    const dau = dong[0].map((x) => x.trim().toLowerCase());
    const coDau = cfg.cot.some((c) => dau.includes(c.title.toLowerCase()));
    const thuTu = coDau ? dau.map((h) => cfg.cot.find((c) => c.title.toLowerCase() === h)?.key) : cfg.cot.map((c) => c.key);
    const hang = (coDau ? dong.slice(1) : dong).map((c) => {
      const o: any = {};
      thuTu.forEach((k, i) => {
        if (!k || c[i] === undefined) return;
        const cot = cfg.cot.find((x) => x.key === k)!;
        const v = c[i].trim();
        if (cot.kieu === 'don_vi') { o._ma_don_vi = v; return; }
        if (cot.kieu === 'chon') { const m = Object.entries(cot.chon || {}).find(([a, b]) => a === v || b.toLowerCase() === v.toLowerCase()); if (m) o[k] = m[0]; return; }
        o[k] = cot.kieu === 'so' ? docSo(v) : cot.kieu === 'co' ? /^(1|x|có|co|true)$/i.test(v) : v;
      });
      return o;
    }).filter((o) => o.ma);
    let moi = 0, cap = 0, loi = 0;
    const dv = (await goi('don_vi:list', { params: { pageSize: 100 } })).data || [];
    for (const o of hang) {
      try {
        if ('_ma_don_vi' in o) {
          const x = dv.find((d: any) => d.ma === o._ma_don_vi || d.ten === o._ma_don_vi);
          delete o._ma_don_vi;
          if (!x) { loi++; continue; }
          o.don_vi_id = x.id;
        }
        const co = await goi(`${bang}:list`, { params: { filter: { ma: o.ma }, pageSize: 1 }, im: true });
        if (co.data?.[0]) { await goi(`${bang}:update`, { params: { filterByTk: co.data[0].id }, data: o, im: true }); cap++; }
        else { await goi(`${bang}:create`, { data: o, im: true }); moi++; }
      } catch { loi++; }
    }
    message.info(`Thêm ${moi}, cập nhật ${cap}, lỗi ${loi} dòng`, 8);
    setDan(false); setText(''); tai();
  };
  return (
    <>
      <Space style={{ marginBottom: 12 }} wrap>
        <Input.Search placeholder={'Tìm ' + cfg.tim.join(' / ')} allowClear onSearch={(v) => { setQ(v); setTimeout(tai); }} style={{ width: 260 }} />
        <Button type="primary" onClick={() => { form.resetFields(); setSua({}); }}>+ Thêm</Button>
        <Button onClick={() => setDan(true)}>Dán từ Excel</Button>
        <Typography.Text type="secondary">{ds.length} dòng</Typography.Text>
      </Space>
      <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 50 }}
        onRow={(r) => ({ onClick: () => { form.setFieldsValue(r); setSua(r); }, style: { cursor: 'pointer' } })}
        columns={cfg.cot.map((c) => ({ title: c.title, dataIndex: c.key, width: c.rong, align: c.kieu === 'so' ? 'right' as const : undefined,
          render: (v: any, r: any) => (c.kieu === 'so' ? fmt(v, 3) : c.kieu === 'co' ? (v ? '✓' : '') : c.kieu === 'don_vi' ? r.don_vi?.ten
            : c.kieu === 'loai_quy' ? (v === 'ngan_hang' ? 'Ngân hàng' : 'Tiền mặt') : c.kieu === 'chon' ? c.chon?.[v] : v) }))} />
      <Modal open={!!sua} title={(sua?.id ? 'Sửa ' : 'Thêm ') + cfg.ten.toLowerCase()} onOk={luu} onCancel={() => setSua(null)} okText="Lưu" cancelText="Thôi" destroyOnClose>
        <Form form={form} layout="vertical">
          {cfg.cot.map((c) => <Form.Item key={c.key} name={c.key} label={c.title} valuePropName={c.kieu === 'co' ? 'checked' : 'value'}
            rules={c.bat_buoc ? [{ required: true, message: 'Bắt buộc' }] : []}>
            {c.kieu === 'don_vi' ? <ChonDanhMuc bang="don_vi" style={{ width: '100%' }} /> : c.kieu === 'loai_quy'
              ? <Select options={[{ value: 'tien_mat', label: 'Tiền mặt' }, { value: 'ngan_hang', label: 'Ngân hàng' }]} /> :
              c.kieu === 'chon' ? <Select options={Object.entries(c.chon || {}).map(([value, label]) => ({ value, label }))} /> :
              c.kieu === 'so' ? <InputNumber style={{ width: '100%' }} /> : c.kieu === 'co' ? <Checkbox /> : c.kieu === 'dai' ? <Input.TextArea rows={2} /> : <Input />}
          </Form.Item>)}
        </Form>
      </Modal>
      <Modal open={dan} width={800} title={`Dán ${cfg.ten.toLowerCase()} từ Excel`} onOk={nhapExcel} onCancel={() => setDan(false)} okText="Nhập" cancelText="Thôi">
        <Typography.Paragraph>Chọn vùng trong Excel (có hoặc không dòng tiêu đề) rồi dán vào đây. Thứ tự cột khi không có tiêu đề:{' '}
          <b>{cfg.cot.map((c) => c.title).join(' | ')}</b>. Trùng mã thì cập nhật, mã mới thì thêm.</Typography.Paragraph>
        <Input.TextArea rows={12} value={text} onChange={(e) => setText(e.target.value)} />
      </Modal>
    </>
  );
}

const DVT_GD: Record<string, string> = { bao: 'Bao', thung: 'Thùng', goi: 'Gói', cai: 'Cái', kg: 'Kg' };
function QuyDoi() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [f] = Form.useForm();
  const tai = async () => setDs((await goi('quy_doi_dvt:list', { params: { appends: ['mat_hang'], sort: ['mat_hang_id', 'dvt'], pageSize: 5000 } })).data || []);
  useEffect(() => { tai(); }, []);
  return <>
    <Typography.Paragraph type="secondary">1 đơn vị giao dịch = bao nhiêu ĐVT tồn của mặt hàng (vd. phồng tôm: 1 thùng = 25 gói × 200 g = 5 kg). Tồn và giá vốn luôn theo ĐVT tồn. Nhập hàng loạt: Go-Live → "Quy đổi đơn vị tính".</Typography.Paragraph>
    <Form form={f} layout="inline" style={{ marginBottom: 12 }} onFinish={async (v) => { await goi('quy_doi_dvt:create', { data: v }); message.success('Đã thêm'); f.resetFields(); tai(); }}>
      <Form.Item name="mat_hang_id" rules={[{ required: true }]}><ChonDanhMuc bang="mat_hang" placeholder="Mặt hàng" style={{ width: 280 }} /></Form.Item>
      <Form.Item name="dvt" rules={[{ required: true }]}><Select placeholder="ĐVT" style={{ width: 110 }} options={Object.entries(DVT_GD).map(([value, label]) => ({ value, label }))} /></Form.Item>
      <Form.Item name="he_so" rules={[{ required: true }]}><InputNumber placeholder="Hệ số" min={0.0001} /></Form.Item>
      <Form.Item name="mac_dinh" valuePropName="checked"><Checkbox>Mặc định khi bán</Checkbox></Form.Item>
      <Button htmlType="submit" type="primary">Thêm</Button>
    </Form>
    <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 50 }} columns={[
      { title: 'Mặt hàng', render: (_, r) => r.mat_hang?.nhan }, { title: 'ĐVT giao dịch', dataIndex: 'dvt', render: (v) => DVT_GD[v] },
      { title: 'Hệ số', dataIndex: 'he_so', align: 'right', render: (v, r) => `1 ${DVT_GD[r.dvt]} = ${fmt(v, 4)} ${r.mat_hang?.dvt_ton || 'kg'}` },
      { title: 'Mặc định', dataIndex: 'mac_dinh', render: (v) => (v ? '✓' : '') },
      { render: (_, r) => <Button size="small" danger onClick={() => goi('quy_doi_dvt:destroy', { params: { filterByTk: r.id }, data: {} }).then(tai)}>Xóa</Button> }]} />
  </>;
}

function PhamVi() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[] | null>(null);
  const [f] = Form.useForm();
  const tai = () => goi('pham_vi:list', { params: { appends: ['nguoi_dung', 'kho', 'quy'], sort: ['nguoi_dung_id'], pageSize: 2000 }, im: true })
    .then((r) => setDs(r.data || [])).catch(() => setDs(null));
  useEffect(() => { tai(); }, []);
  if (ds === null) return <Typography.Text type="secondary">Chỉ kế toán / quản lý cấu hình phạm vi.</Typography.Text>;
  return <>
    <Typography.Paragraph type="secondary">Người dùng KHÔNG có dòng nào ở đây: không giới hạn kho / quỹ. Có dòng kho: chỉ xác nhận / ghi phiếu và chỉ thấy tồn, phiếu của các kho đó. Có dòng quỹ: chỉ ghi thu / chi / chốt ca của quỹ đó. Kiểm ở máy chủ (cả API, in phiếu). Người không được xem giá vốn: gán thêm vai trò "Không xem giá vốn (phủ quyết)" trong Quản lý người dùng.</Typography.Paragraph>
    <Form form={f} layout="inline" style={{ marginBottom: 12 }} onFinish={async (v) => { if (!v.kho_id && !v.quy_id) return message.warning('Chọn kho hoặc quỹ.'); await goi('pham_vi:create', { data: v }); f.resetFields(); tai(); }}>
      <Form.Item name="nguoi_dung_id" rules={[{ required: true }]}><ChonDanhMuc bang="users" nhan="nickname" timTheo={['nickname', 'email']} placeholder="Người dùng" style={{ width: 240 }} /></Form.Item>
      <Form.Item name="kho_id"><ChonDanhMuc bang="kho" placeholder="Kho" style={{ width: 200 }} /></Form.Item>
      <Form.Item name="quy_id"><ChonDanhMuc bang="quy" placeholder="Quỹ / tài khoản" style={{ width: 200 }} /></Form.Item>
      <Button htmlType="submit" type="primary">Thêm</Button>
    </Form>
    <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 50 }} columns={[
      { title: 'Người dùng', render: (_, r) => `${r.nguoi_dung?.nickname || ''} (${r.nguoi_dung?.email || ''})` }, { title: 'Kho', render: (_, r) => r.kho?.ten },
      { title: 'Quỹ', render: (_, r) => r.quy?.ten }, { render: (_, r) => <Button size="small" danger onClick={() => goi('pham_vi:destroy', { params: { filterByTk: r.id }, data: {} }).then(tai)}>Bỏ</Button> }]} />
  </>;
}

export function DanhMuc() {
  return (
    <Card title="Danh mục">
      <Tabs items={[
        ...Object.entries(BANG).map(([k, v]) => ({ key: k, label: v.ten, children: <BangDanhMuc bang={k} /> })),
        { key: 'qd', label: 'Quy đổi ĐVT', children: <QuyDoi /> },
        { key: 'pv', label: 'Phạm vi kho / quỹ', children: <PhamVi /> },
        { key: 'no', label: 'Công nợ / tồn đầu kỳ', children: <Typography.Paragraph>Số dư đầu kỳ (tồn kho, công nợ khách / NCC, quỹ, tiền cọc, đơn chuyển tiếp) nhập ở menu <b>Go-Live &amp; số dư đầu kỳ</b> — có kiểm tra, chống nhập trùng, duyệt và khóa kỳ.</Typography.Paragraph> },
      ]} />
    </Card>
  );
}
