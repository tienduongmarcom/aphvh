/** Danh mục: mặt hàng, khách hàng, kho, đơn vị; công nợ đầu kỳ. Thêm/sửa và dán nhanh từ Excel (cập nhật theo mã). */
import { App, Button, Card, Checkbox, Form, Input, InputNumber, Modal, Select, Space, Table, Tabs, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, fmt, homNay, ngayVN, useGoi } from './chung';

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
        if (cot.kieu === 'don_vi') return;
        if (cot.kieu === 'chon') { const m = Object.entries(cot.chon || {}).find(([a, b]) => a === v || b.toLowerCase() === v.toLowerCase()); if (m) o[k] = m[0]; return; }
        o[k] = cot.kieu === 'so' ? docSo(v) : cot.kieu === 'co' ? /^(1|x|có|co|true)$/i.test(v) : v;
      });
      return o;
    }).filter((o) => o.ma);
    let moi = 0, cap = 0, loi = 0;
    for (const o of hang) {
      try {
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

/** Công nợ đầu kỳ: một dòng cho mỗi khách × đơn vị, ghi như đơn "Công nợ đầu kỳ" đã giao (thu tiền trừ vào được). */
function CongNoDauKy() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [khach, setKhach] = useState<any>();
  const [dv, setDv] = useState<any>();
  const [tien, setTien] = useState<number | null>(null);
  const tai = async () => setDs((await goi('don_ban:list', { params: { filter: { loai: 'dau_ky' }, appends: ['khach', 'don_vi_ban'], sort: ['-id'], pageSize: 2000 } })).data || []);
  useEffect(() => { tai(); }, []);
  const them = async () => {
    if (!khach || !dv || !tien) return message.warning('Chọn khách, đơn vị và nhập số nợ.');
    await goi('don_ban:create', { data: { loai: 'dau_ky', khach_id: khach, don_vi_ban_id: dv, tong_tien: tien, ngay: homNay(), ngay_giao: homNay(), ghi_chu: 'Công nợ đầu kỳ' } });
    setTien(null); tai();
  };
  return (
    <>
      <Space style={{ marginBottom: 12 }} wrap>
        <ChonDanhMuc bang="khach_hang" value={khach} onChange={setKhach} timTheo={['ma', 'ten', 'sdt', 'nhan']} placeholder="Khách" style={{ width: 300 }} />
        <ChonDanhMuc bang="don_vi" value={dv} onChange={setDv} placeholder="Đơn vị" />
        <InputNumber placeholder="Số nợ (đ)" value={tien} onChange={(v) => setTien(v as any)} style={{ width: 180 }} formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))} />
        <Button type="primary" onClick={them}>Thêm nợ đầu kỳ</Button>
      </Space>
      <Table size="small" rowKey="id" dataSource={ds} columns={[
        { title: 'Số', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Khách', render: (_, r) => r.khach?.ten },
        { title: 'Đơn vị', render: (_, r) => r.don_vi_ban?.ten }, { title: 'Nợ đầu kỳ', dataIndex: 'tong_tien', align: 'right', render: (v) => fmt(v) },
        { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v) => fmt(v) },
      ]} />
    </>
  );
}

export function DanhMuc() {
  return (
    <Card title="Danh mục">
      <Tabs items={[
        ...Object.entries(BANG).map(([k, v]) => ({ key: k, label: v.ten, children: <BangDanhMuc bang={k} /> })),
        { key: 'no', label: 'Công nợ đầu kỳ', children: <CongNoDauKy /> },
      ]} />
    </Card>
  );
}
