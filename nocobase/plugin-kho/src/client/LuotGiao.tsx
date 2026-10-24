/** Giao hàng theo lượt, trả hàng, giảm giá sau bán (0.3.0). Kho chỉ trừ khi lượt được xác nhận xuất. */
import { App, Button, Card, Input, InputNumber, Modal, Space, Table, Tag, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, TRANG_THAI_LUOT, TRANG_THAI_PHIEU, fmt, ngayVN, theTrangThai, useGoi } from './chung';

export const moInLuot = (id: any) => window.open(`/in/luot_giao/${id}`, '_blank');
const maYeuCau = () => `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

/** Lượng còn lại có thể lập lượt cho một dòng đơn. */
export const conLai = (d: any) => Math.max(0, Math.round((Number(d.so_kg || 0) - Number(d.da_giao || 0) - Number(d.dang_giu || 0)) * 1000) / 1000);

/** Tạo một lượt giao. Không truyền "luong" = giao hết phần còn lại. Trả về id lượt. */
export async function taoLuot(goi: any, don: any, dong: any[], luong?: Record<string, number>, them: any = {}) {
  const ds = dong.map((d) => ({ don_ban_dong_id: d.id, so_kg: luong ? Number(luong[d.id] || 0) : conLai(d) })).filter((x) => x.so_kg > 0);
  const r = await goi('luot_giao:taoLuot', { data: { don_ban_id: don.id, cach_giao: don.cach_giao, nguoi_nhan: don.nguoi_nhan, bien_so: don.bien_so,
    request_id: maYeuCau(), dong: ds, ...them } });
  return r.data?.id;
}

/** Nút thao tác cho một lượt (dùng ở màn bán hàng và màn kho). */
export function NutLuot({ luot, xong }: any) {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const xacNhan = (url: string, title: string, okText: string, hoiNguoi: boolean) => {
    let nguoi = luot.nguoi_nhan || '';
    let xe = luot.bien_so || '';
    modal.confirm({
      title, okText, cancelText: 'Chưa',
      content: hoiNguoi ? <Space direction="vertical" style={{ width: '100%' }}>
        <div>Chỉ bấm khi hàng đã thực ra khỏi kho. Bấm nhiều lần cũng chỉ trừ kho một lần.</div>
        <Input placeholder="Người nhận / lái xe" defaultValue={nguoi} onChange={(e) => (nguoi = e.target.value)} />
        <Input placeholder="Biển số xe" defaultValue={xe} onChange={(e) => (xe = e.target.value)} />
      </Space> : 'Xác nhận khách đã nhận đủ hàng của lượt này (không trừ kho lần nữa).',
      onOk: () => goi(url, { params: { filterByTk: luot.id }, data: { nguoi_nhan: nguoi, bien_so: xe } }).then(() => { message.success('Đã ghi'); xong?.(); }),
    });
  };
  return (
    <Space wrap>
      <Button size="small" onClick={() => moInLuot(luot.id)}>In phiếu xuất</Button>
      {luot.trang_thai === 'cho_xuat' && luot.cach_giao === 'van_chuyen' &&
        <Button size="small" type="primary" onClick={() => xacNhan('luot_giao:banGiaoXe', `Bàn giao ${luot.so} cho xe?`, 'Đã bàn giao xe — trừ kho', true)}>Đã bàn giao xe</Button>}
      {luot.trang_thai === 'cho_xuat' && luot.cach_giao !== 'van_chuyen' &&
        <Button size="small" type="primary" onClick={() => xacNhan('luot_giao:khachNhan', `Khách đã nhận ${luot.so}?`, 'Khách đã nhận — trừ kho', true)}>Khách đã nhận</Button>}
      {luot.trang_thai === 'da_ban_giao_xe' &&
        <Button size="small" onClick={() => xacNhan('luot_giao:khachNhan', `Khách đã nhận ${luot.so}?`, 'Khách đã nhận', false)}>Khách đã nhận</Button>}
      {luot.trang_thai === 'cho_xuat' && <Button size="small" danger onClick={() => {
        let ly_do = '';
        modal.confirm({ title: `Hủy ${luot.so}? Hàng đang giữ được trả lại khả dụng.`, okText: 'Hủy lượt', cancelText: 'Thôi', okButtonProps: { danger: true },
          content: <Input placeholder="Lý do" onChange={(e) => (ly_do = e.target.value)} />,
          onOk: () => goi('luot_giao:huy', { params: { filterByTk: luot.id }, data: { ly_do } }).then(() => xong?.()) });
      }}>Hủy lượt</Button>}
    </Space>
  );
}

/** Hộp nhập lượng theo dòng đơn (dùng cho tạo lượt và trả hàng). */
function HopLuong({ open, title, dong, toiDa, nhanToiDa, onOk, onCancel, them, okText }: any) {
  const [luong, setLuong] = useState<Record<string, number>>({});
  useEffect(() => { if (open) setLuong(Object.fromEntries(dong.map((d: any) => [d.id, them?.macDinh0 ? 0 : toiDa(d)]))); }, [open]);
  const [dang, setDang] = useState(false);
  return (
    <Modal open={open} title={title} width={760} okText={okText} cancelText="Thôi" confirmLoading={dang} destroyOnClose onCancel={onCancel}
      onOk={async () => { setDang(true); try { await onOk(luong); } catch { /* đã báo */ } finally { setDang(false); } }}>
      {them?.tren}
      <Table size="small" rowKey="id" pagination={false} dataSource={dong} columns={[
        { title: 'Hàng', render: (_, d: any) => <span><b>{d.mat_hang?.ma}</b> {d.ten_hang || d.mat_hang?.ten}</span> },
        { title: nhanToiDa, align: 'right', render: (_, d: any) => fmt(toiDa(d), 3) },
        { title: 'Lượng', width: 150, render: (_, d: any) => <InputNumber min={0} max={toiDa(d)} value={luong[d.id]} style={{ width: 130 }}
          onChange={(v) => setLuong({ ...luong, [d.id]: Number(v || 0) })} /> },
      ]} />
    </Modal>
  );
}

/** Khối "Giao hàng & điều chỉnh" trong đơn đã chốt. */
export function GiaoHangDon({ don, dong, tai }: any) {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [luot, setLuot] = useState<any[]>([]);
  const [tra, setTra] = useState<any[]>([]);
  const [gg, setGg] = useState<any[]>([]);
  const [moLuot, setMoLuot] = useState(false);
  const [moTra, setMoTra] = useState(false);
  const [khoTra, setKhoTra] = useState<any>();
  const [lyDoTra, setLyDoTra] = useState('');
  const taiThem = async () => {
    const f = { filter: { don_ban_id: don.id }, sort: ['id'], pageSize: 200 };
    setLuot((await goi('luot_giao:list', { params: { ...f, appends: ['dong', 'dong.mat_hang'] }, im: true }).catch(() => ({ data: [] }))).data || []);
    setTra((await goi('tra_hang:list', { params: { ...f, appends: ['kho_nhan'] }, im: true }).catch(() => ({ data: [] }))).data || []);
    setGg((await goi('dieu_chinh_gia:list', { params: f, im: true }).catch(() => ({ data: [] }))).data || []);
  };
  useEffect(() => { taiThem(); }, [don.id, don.updatedAt]);
  const lai = () => { taiThem(); tai(); };
  const conGiao = dong.some((d: any) => conLai(d) > 0);
  const dangGiao = ['cho_xuat', 'dang_giao'].includes(don.trang_thai);
  const daGiao = dong.some((d: any) => Number(d.da_giao || 0) > 0);
  return (
    <Card size="small" title="Giao hàng theo lượt" extra={<Typography.Text type="secondary">Kho trừ khi lượt được xác nhận xuất</Typography.Text>}>
      <Table size="small" rowKey="id" pagination={false} dataSource={dong} columns={[
        { title: 'Hàng', render: (_, d: any) => <span><b>{d.mat_hang?.ma}</b> {d.ten_hang || d.mat_hang?.ten}</span> },
        { title: 'Đặt', dataIndex: 'so_kg', align: 'right', render: (v) => fmt(v, 3) },
        { title: 'Đã giao', dataIndex: 'da_giao', align: 'right', render: (v) => fmt(v, 3) },
        { title: 'Đang giữ (lượt chờ xuất)', dataIndex: 'dang_giu', align: 'right', render: (v) => fmt(v, 3) },
        { title: 'Đã trả lại', dataIndex: 'da_tra', align: 'right', render: (v) => fmt(v, 3) },
        { title: 'Chưa lập lượt', align: 'right', render: (_, d: any) => <b>{fmt(conLai(d), 3)}</b> },
      ]} />
      <Table style={{ marginTop: 12 }} size="small" rowKey="id" pagination={false} dataSource={luot} locale={{ emptyText: 'Chưa có lượt giao' }} columns={[
        { title: 'Lượt', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
        { title: 'Hàng', render: (_, l: any) => (l.dong || []).map((x: any) => `${x.mat_hang?.ma} ${fmt(x.so_kg, 3)}`).join('; ') },
        { title: 'Giá trị', dataIndex: 'gia_tri', align: 'right', render: (v) => fmt(v) },
        { title: 'Người nhận / xe', render: (_, l: any) => [l.nguoi_nhan, l.bien_so].filter(Boolean).join(' · ') },
        { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_LUOT, v); return <Tag color={m}>{t}</Tag>; } },
        { render: (_, l: any) => <NutLuot luot={l} xong={lai} /> },
      ]} />
      {(tra.length > 0 || gg.length > 0) && <Table style={{ marginTop: 12 }} size="small" rowKey={(r: any) => r.so} pagination={false}
        dataSource={[...tra.map((x) => ({ ...x, kieu: 'tra' })), ...gg.map((x) => ({ ...x, kieu: 'gg' }))]} columns={[
          { title: 'Điều chỉnh', render: (_, r: any) => <b>{r.so}</b> },
          { title: 'Loại', render: (_, r: any) => (r.kieu === 'tra' ? `Trả hàng → ${r.kho_nhan?.ten || ''}` : 'Giảm giá (không nhập kho)') },
          { title: 'Lý do', dataIndex: 'ly_do' },
          { title: 'Giá trị', align: 'right', render: (_, r: any) => fmt(r.kieu === 'tra' ? r.gia_tri : r.so_tien) },
          { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{v === 'nhap' ? 'Chờ kế toán ghi' : t}</Tag>; } },
          { render: (_, r: any) => r.trang_thai === 'nhap' ? <Space>
            <Button size="small" type="primary" onClick={() => goi(`${r.kieu === 'tra' ? 'tra_hang' : 'dieu_chinh_gia'}:ghi`, { params: { filterByTk: r.id }, data: {} })
              .then(() => { message.success('Đã ghi'); lai(); })}>Ghi</Button></Space> : null },
        ]} />}
      <Space wrap style={{ marginTop: 12 }}>
        {dangGiao && conGiao && <Button type="primary" onClick={() => setMoLuot(true)}>+ Tạo lượt giao</Button>}
        {daGiao && <Button onClick={() => { setKhoTra(undefined); setLyDoTra(''); setMoTra(true); }}>Khách trả hàng</Button>}
        {daGiao && <Button onClick={() => {
          let so_tien = 0; let ly_do = '';
          modal.confirm({ title: `Giảm giá sau bán cho ${don.so}`, okText: 'Lập phiếu giảm giá', cancelText: 'Thôi',
            content: <Space direction="vertical" style={{ width: '100%' }}>
              <div>Khách giữ hàng, chỉ giảm tiền. Không nhập lại kho.</div>
              <InputNumber min={0} style={{ width: '100%' }} placeholder="Số tiền giảm" formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))}
                onChange={(v) => (so_tien = Number(v || 0))} />
              <Input.TextArea placeholder="Lý do (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} /></Space>,
            onOk: async () => {
              const r = await goi('dieu_chinh_gia:create', { data: { don_ban_id: don.id, so_tien, ly_do } });
              await goi('dieu_chinh_gia:ghi', { params: { filterByTk: r.data.id }, data: {}, im: true })
                .then(() => message.success('Đã ghi giảm giá'))
                .catch(() => message.info('Đã lập phiếu giảm giá — chờ kế toán / quản lý ghi.', 6));
              lai();
            } });
        }}>Giảm giá sau bán</Button>}
        {don.trang_thai === 'dang_giao' && <Button onClick={() => {
          let ly_do = '';
          modal.confirm({ title: 'Đóng phần chưa giao? Đơn kết thúc, không giao thêm.', okText: 'Đóng đơn', cancelText: 'Thôi',
            content: <Input.TextArea placeholder="Lý do (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} />,
            onOk: () => goi('don_ban:dongPhanCon', { params: { filterByTk: don.id }, data: { ly_do } }).then(lai) });
        }}>Đóng phần chưa giao</Button>}
      </Space>
      <HopLuong open={moLuot} title={`Tạo lượt giao cho ${don.so}`} dong={dong} toiDa={conLai} nhanToiDa="Chưa lập lượt" okText="Tạo lượt & in phiếu xuất"
        onCancel={() => setMoLuot(false)}
        onOk={async (luong: any) => { const x = await taoLuot(goi, don, dong, luong); setMoLuot(false); if (x) moInLuot(x); lai(); }} />
      <HopLuong open={moTra} title={`Khách trả hàng — ${don.so}`} dong={dong.filter((d: any) => Number(d.da_giao || 0) - Number(d.da_tra || 0) > 0)}
        toiDa={(d: any) => Math.round((Number(d.da_giao || 0) - Number(d.da_tra || 0)) * 1000) / 1000} nhanToiDa="Trả được tối đa" okText="Ghi trả hàng"
        them={{ macDinh0: true, tren: <Space direction="vertical" style={{ width: '100%', marginBottom: 12 }}>
          <ChonDanhMuc bang="kho" value={khoTra} onChange={setKhoTra} placeholder="Kho nhận hàng trả (hàng hỏng → kho chờ xử lý)" style={{ width: '100%' }} />
          <Input.TextArea placeholder="Lý do trả (bắt buộc)" value={lyDoTra} onChange={(e) => setLyDoTra(e.target.value)} /></Space> }}
        onCancel={() => setMoTra(false)}
        onOk={async (luong: any) => {
          if (!khoTra) { message.warning('Chọn kho nhận hàng trả.'); throw new Error('thieu'); }
          const ds = Object.entries(luong).filter(([, v]) => Number(v) > 0).map(([k, v]) => ({ don_ban_dong_id: Number(k), so_kg: v }));
          if (!ds.length) { message.warning('Nhập lượng trả.'); throw new Error('thieu'); }
          const r = await goi('tra_hang:create', { params: { updateAssociationValues: ['dong'] }, data: { don_ban_id: don.id, kho_nhan_id: khoTra, ly_do: lyDoTra, dong: ds } });
          await goi('tra_hang:ghi', { params: { filterByTk: r.data.id }, data: {} });
          message.success('Đã nhập hàng trả và giảm công nợ');
          setMoTra(false); lai();
        }} />
    </Card>
  );
}

/** Màn kho: các lượt chờ xuất / đang trên xe. */
export function LuotChoXuat() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('luot_giao:list', { params: { filter: { trang_thai: { $in: ['cho_xuat', 'da_ban_giao_xe'] } },
    appends: ['don_ban', 'don_ban.khach', 'dong', 'dong.mat_hang', 'dong.kho'], sort: ['id'], pageSize: 300 } })).data || []);
  useEffect(() => { tai(); }, []);
  return (
    <>
      <Space style={{ marginBottom: 12 }}><Typography.Text type="secondary">Lượt giao đang giữ hàng hoặc đã lên xe. Hàng ra khỏi kho thì bấm xác nhận để trừ kho.</Typography.Text>
        <Button onClick={tai}>Tải lại</Button></Space>
      <Table size="middle" rowKey="id" dataSource={ds} pagination={false}
        expandable={{ defaultExpandAllRows: true, expandedRowRender: (l: any) => <Table size="small" rowKey="id" pagination={false} dataSource={l.dong} columns={[
          { title: 'Mã hàng', render: (_, r: any) => <b>{r.mat_hang?.ma}</b> }, { title: 'Tên hàng', render: (_, r: any) => r.mat_hang?.ten },
          { title: 'Kho', render: (_, r: any) => r.kho?.ten }, { title: 'Số bao', dataIndex: 'so_bao', align: 'right', render: (v) => fmt(v, 2) },
          { title: 'Số lượng', dataIndex: 'so_kg', align: 'right', render: (v) => <b>{fmt(v, 3)}</b> }]} /> }}
        columns={[
          { title: 'Lượt', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Đơn', render: (_, l) => l.don_ban?.so },
          { title: 'Khách', render: (_, l) => <span>{l.don_ban?.khach?.ten}<div style={{ fontSize: 12, color: '#888' }}>{l.don_ban?.sdt}</div></span> },
          { title: 'Cách giao', dataIndex: 'cach_giao', render: (v) => (v === 'van_chuyen' ? 'Vận chuyển' : 'Khách đến lấy') },
          { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_LUOT, v); return <Tag color={m}>{t}</Tag>; } },
          { render: (_, l) => <NutLuot luot={l} xong={tai} /> },
        ]} />
    </>
  );
}
