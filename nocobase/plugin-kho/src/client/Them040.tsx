/** 0.4.0: Bảng giá, Cấu hình vận hành, Tổng quan vận hành, Hàng đợi hóa đơn MISA theo bên bán. */
import { App, Button, Card, Checkbox, Collapse, Drawer, Input, InputNumber, Modal, Segmented, Select, Space, Table, Tag, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, fmt, ngayVN, useGoi } from './chung';

export function BangGia() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [mo, setMo] = useState<any>(null);
  const tai = async () => setDs((await goi('bang_gia:list', { params: { sort: ['-uu_tien', 'ma'], pageSize: 200 } })).data || []);
  useEffect(() => { tai(); }, []);
  const luu = async () => {
    const { id, dong, ...v } = mo;
    const data = { ...v, dong: (dong || []).filter((d: any) => d.mat_hang_id).map(({ mat_hang, ...d }: any) => d) };
    if (id) await goi('bang_gia:update', { params: { filterByTk: id, 'updateAssociationValues[]': 'dong' }, data });
    else await goi('bang_gia:create', { params: { 'updateAssociationValues[]': 'dong' }, data });
    message.success('Đã lưu bảng giá'); setMo(null); tai();
  };
  const sua = async (r: any) => setMo((await goi('bang_gia:get', { params: { filterByTk: r.id, appends: ['dong', 'dong.mat_hang'] } })).data);
  const d = (k: string, v: any) => setMo({ ...mo, [k]: v });
  return <>
    <Button type="primary" style={{ marginBottom: 8 }} onClick={() => setMo({ kenh: 'si', dong: [{}] })}>+ Bảng giá</Button>
    <Table size="small" rowKey="id" dataSource={ds} onRow={(r) => ({ onClick: () => sua(r), style: { cursor: 'pointer' } })} columns={[
      { title: 'Mã', dataIndex: 'ma' }, { title: 'Tên', dataIndex: 'ten' }, { title: 'Nhóm khách', dataIndex: 'nhom_gia', render: (v) => v || 'Mọi khách' },
      { title: 'Kênh', dataIndex: 'kenh', render: (v) => (v === 'pos' ? 'Bán lẻ / POS' : 'Bán sỉ') }, { title: 'Hiệu lực', render: (_, r) => `${ngayVN(r.tu_ngay) || '…'} → ${ngayVN(r.den_ngay) || '…'}` },
      { title: 'Gồm VAT', dataIndex: 'gia_gom_vat', render: (v) => (v ? 'Có' : 'Không') }, { title: 'Ưu tiên', dataIndex: 'uu_tien' },
      { title: '', dataIndex: 'ngung', render: (v) => v && <Tag>Ngừng</Tag> },
    ]} />
    <Drawer width="80%" open={!!mo} onClose={() => setMo(null)} title="Bảng giá" destroyOnClose extra={<Button type="primary" onClick={luu}>Lưu</Button>}>
      {mo && <>
        <Space wrap style={{ marginBottom: 8 }}>
          <Input placeholder="Mã" value={mo.ma} onChange={(e) => d('ma', e.target.value)} style={{ width: 140 }} />
          <Input placeholder="Tên" value={mo.ten} onChange={(e) => d('ten', e.target.value)} style={{ width: 220 }} />
          <Input placeholder="Nhóm giá khách (trống = mọi khách)" value={mo.nhom_gia} onChange={(e) => d('nhom_gia', e.target.value)} style={{ width: 240 }} />
          <Select value={mo.kenh} onChange={(v) => d('kenh', v)} style={{ width: 140 }} options={[{ value: 'si', label: 'Bán sỉ' }, { value: 'pos', label: 'Bán lẻ / POS' }]} />
          <Input type="date" value={mo.tu_ngay || ''} onChange={(e) => d('tu_ngay', e.target.value || null)} />
          <Input type="date" value={mo.den_ngay || ''} onChange={(e) => d('den_ngay', e.target.value || null)} />
          <Checkbox checked={!!mo.gia_gom_vat} onChange={(e) => d('gia_gom_vat', e.target.checked)}>Giá đã gồm VAT</Checkbox>
          <InputNumber addonBefore="Ưu tiên" value={mo.uu_tien} onChange={(v) => d('uu_tien', v)} style={{ width: 150 }} />
          <Checkbox checked={!!mo.ngung} onChange={(e) => d('ngung', e.target.checked)}>Ngừng dùng</Checkbox>
        </Space>
        <Table size="small" rowKey={(_, i) => String(i)} pagination={false} dataSource={mo.dong || []} columns={[
          { title: 'Mặt hàng', render: (_, x, i) => <ChonDanhMuc bang="mat_hang" value={x.mat_hang_id} style={{ width: 280 }} onChange={(v) => d('dong', mo.dong.map((y: any, j: number) => (j === i ? { ...y, mat_hang_id: v } : y)))} /> },
          { title: 'Từ số lượng', render: (_, x, i) => <InputNumber min={0} value={x.sl_toi_thieu} onChange={(v) => d('dong', mo.dong.map((y: any, j: number) => (j === i ? { ...y, sl_toi_thieu: v } : y)))} /> },
          { title: 'Đơn giá / ĐVT tồn', render: (_, x, i) => <InputNumber min={0} value={x.don_gia} onChange={(v) => d('dong', mo.dong.map((y: any, j: number) => (j === i ? { ...y, don_gia: v } : y)))} /> },
          { title: 'Giá sàn', render: (_, x, i) => <InputNumber min={0} value={x.gia_san} onChange={(v) => d('dong', mo.dong.map((y: any, j: number) => (j === i ? { ...y, gia_san: v } : y)))} /> },
        ]} />
        <Button style={{ marginTop: 8 }} onClick={() => d('dong', [...(mo.dong || []), {}])}>+ Dòng</Button>
      </>}
    </Drawer>
  </>;
}

const CH_GT: Record<string, { ten: string; chon?: [string, string][] }> = {
  giu_khi_duyet: { ten: 'Giữ tồn ngay khi duyệt đơn', chon: [['co', 'Có'], ['khong', 'Không (chỉ giữ khi lập lượt)']] },
  vuot_han_muc_khach_thuong: { ten: 'Khách thường vượt hạn mức', chon: [['canh_bao', 'Cảnh báo, vẫn bán'], ['duyet', 'Chờ duyệt']] },
  pham_vi_mac_dinh: { ten: 'Người dùng chưa cấp phạm vi kho / quỹ', chon: [['tu_choi', 'Từ chối'], ['cho_phep', 'Cho phép (kiểu 0.3.2)']] },
  ck_can_xac_minh: { ten: 'Chuyển khoản thủ quỹ ghi phải chờ đối soát', chon: [['co', 'Có'], ['khong', 'Không']] },
  gia_danh_muc_gom_vat: { ten: 'Giá bán trên danh mục đã gồm VAT', chon: [['co', 'Có'], ['khong', 'Không']] },
  dung_sai_can_pct: { ten: 'Dung sai cân mặc định (%)' }, nguong_lech_sx_pct: { ten: 'Ngưỡng lệch kg phiếu sản xuất (%)' },
  ma_khach_le: { ten: 'Mã khách lẻ (bán nhanh)' }, ngay_moc_golive: { ten: 'Ngày mốc Go-Live (yyyy-mm-dd)' },
};
export function CauHinh() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<Record<string, any>>({});
  const tai = async () => setDs(Object.fromEntries(((await goi('cau_hinh:list', { params: { pageSize: 100 } })).data || []).map((x: any) => [x.khoa, x])));
  useEffect(() => { tai(); }, []);
  const dat = async (khoa: string, gia_tri: any) => { await goi('cau_hinh:dat', { data: { khoa, gia_tri } }); message.success('Đã đổi cấu hình'); tai(); };
  return <Table size="small" rowKey="k" pagination={false} dataSource={Object.entries(CH_GT).map(([k, v]) => ({ k, ...v, gt: ds[k]?.gia_tri, mo_ta: ds[k]?.mo_ta }))} columns={[
    { title: 'Cấu hình', dataIndex: 'ten' },
    { title: 'Giá trị', render: (_, r: any) => r.chon ? <Select value={r.gt} style={{ width: 240 }} onChange={(v) => dat(r.k, v)} options={r.chon.map(([v, l]: any) => ({ value: v, label: l }))} />
      : <Input defaultValue={r.gt} style={{ width: 240 }} onPressEnter={(e: any) => dat(r.k, e.target.value)} onBlur={(e) => e.target.value !== (r.gt || '') && dat(r.k, e.target.value)} /> },
    { title: 'Ghi chú', dataIndex: 'mo_ta' },
  ]} />;
}

const T = (cot: any[]) => cot.map((c) => (typeof c === 'string' ? { title: c, dataIndex: c, render: (v: any) => (typeof v === 'number' || /^-?\d+(\.\d+)?$/.test(String(v ?? '')) ? fmt(v, 3) : v) } : c));
export function TongQuan() {
  const goi = useGoi();
  const [d, setD] = useState<any>(null);
  useEffect(() => { goi('don_gop:tongQuan', { data: {} }).then((r) => setD(r.data)); }, []);
  if (!d) return null;
  const muc: [string, string, string[]][] = [
    ['don_gop_thieu', 'Đơn gộp đang xử lý', ['so', 'khach', 'tt_duyet', 'tt_giao', 'tt_thanh_toan', 'tt_hoa_don', 'tong_tien', 'con_no']],
    ['giao_con_thieu', 'Giao còn thiếu', ['so', 'ben_ban', 'mat_hang', 'dat', 'da_giao', 'con', 'dang_giu']],
    ['cong_no_ben_ban', 'Công nợ theo bên bán', ['ben_ban', 'so_don', 'con_no', 'phai_hoan']],
    ['tien_chua_phan_bo', 'Tiền chưa phân bổ', ['don_vi', 'loai_thu', 'so_phieu', 'so_tien']],
    ['ck_cho_xac_minh', 'Chuyển khoản chờ xác minh', ['don_vi', 'so_phieu', 'so_tien']],
    ['thu_ho_dang_giu', 'Thu hộ đang giữ', ['don_vi_giu', 'giu_ho_cho', 'so_khoan', 'con_giu']],
    ['wip', 'Mẻ dở dang (WIP)', ['so', 'xuong', 'trang_thai', 'kg_nvl', 'kg_tp', 'chi_phi']],
    ['chenh_lech_giao_nhan', 'Chênh lệch giao – nhận chờ xử lý', ['chuyen', 'mat_hang', 'so_kg', 'ly_do']],
    ['hang_dang_di_duong', 'Hàng đang đi đường', ['kho', 'mat_hang', 'so_kg']],
    ['hang_doi_hoa_don', 'Hàng đợi hóa đơn', ['ben_ban', 'trang_thai', 'so_dong', 'tong']],
    ['gia_thanh_tam', 'Giá thành tạm tính / cần chốt lại', ['so', 'trang_thai']],
  ];
  return <Collapse defaultActiveKey={['don_gop_thieu', 'cong_no_ben_ban']} items={muc.filter(([k]) => d[k]).map(([k, ten, cot]) => ({ key: k,
    label: <span>{ten} <Tag>{d[k].length}</Tag></span>, children: <Table size="small" rowKey={(_, i) => String(i)} dataSource={d[k]} pagination={{ pageSize: 20 }} columns={T(cot)} /> }))} />;
}

export function HangDoiHD() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [loc, setLoc] = useState('cho');
  const [ds, setDs] = useState<any[]>([]);
  const [nhap, setNhap] = useState<Record<string, any>>({});
  const tai = async () => setDs((await goi('hoa_don_cho_xuat:list', { params: { filter: { trang_thai: loc === 'cho' ? { $in: ['cho_xu_ly', 'dang_lap', 'can_dieu_chinh'] } : 'da_xuat' },
    appends: ['don_ban', 'don_vi', 'khach'], sort: ['id'], pageSize: 500 } })).data || []);
  useEffect(() => { tai(); }, [loc]);
  const lam = async (r: any, act: string, data: any = {}) => { await goi(`hoa_don_cho_xuat:${act}`, { params: { filterByTk: r.id }, data }); message.success('Xong'); tai(); };
  const TT: any = { cho_xu_ly: ['Chờ xử lý', 'orange'], dang_lap: ['Đang lập nháp', 'blue'], da_xuat: ['Đã xuất', 'green'], can_dieu_chinh: ['Cần điều chỉnh', 'red'] };
  return <>
    <Space style={{ marginBottom: 8 }}><Segmented value={loc} onChange={(v: any) => setLoc(v)} options={[{ value: 'cho', label: 'Cần xử lý' }, { value: 'da', label: 'Đã xuất' }]} /></Space>
    <Typography.Paragraph type="secondary">Mỗi dòng là phần đã giao chưa xuất hóa đơn của MỘT bên bán. Lập hóa đơn trên MISA rồi ghi ký hiệu + số (hệ thống chặn trùng số theo bên bán). Không tự gọi MISA.</Typography.Paragraph>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Dòng', dataIndex: 'so' }, { title: 'Bên bán', render: (_, r) => <Tag>{r.don_vi?.ma}</Tag> }, { title: 'Đơn con', render: (_, r) => r.don_ban?.so },
      { title: 'Khách', render: (_, r) => <span>{r.khach?.ten}<div style={{ fontSize: 12, color: '#888' }}>MST {r.khach?.mst || '—'}</div></span> },
      { title: 'Trước thuế', dataIndex: 'tien_truoc_thue', align: 'right', render: (v) => fmt(v) }, { title: 'Thuế', dataIndex: 'tien_thue', align: 'right', render: (v) => fmt(v) },
      { title: 'Tổng', dataIndex: 'tong', align: 'right', render: (v) => <b>{fmt(v)}</b> },
      { title: 'Trạng thái', render: (_, r) => <Tag color={TT[r.trang_thai]?.[1]}>{TT[r.trang_thai]?.[0]}</Tag> },
      { title: 'Ký hiệu / số', render: (_, r) => r.trang_thai === 'da_xuat' ? `${r.ky_hieu} ${r.so_hd}` : <Space>
        <Input size="small" style={{ width: 100 }} placeholder="Ký hiệu" onChange={(e) => setNhap({ ...nhap, [r.id]: { ...nhap[r.id], ky_hieu: e.target.value } })} />
        <Input size="small" style={{ width: 100 }} placeholder="Số HĐ" onChange={(e) => setNhap({ ...nhap, [r.id]: { ...nhap[r.id], so_hd: e.target.value } })} /></Space> },
      { render: (_, r) => r.trang_thai !== 'da_xuat' && <Space>
        {r.trang_thai !== 'dang_lap' && <Button size="small" onClick={() => lam(r, 'nhan')}>Nhận xử lý</Button>}
        <Button size="small" type="primary" onClick={() => lam(r, 'ghiSo', nhap[r.id] || {})}>Ghi số HĐ</Button>
        <Button size="small" danger onClick={() => { let ly = ''; Modal.confirm({ title: 'Hủy dòng hàng đợi', content: <Input onChange={(e) => (ly = e.target.value)} />, onOk: () => lam(r, 'huy', { ly_do: ly }) }); }}>Hủy</Button>
      </Space> },
    ]} />
  </>;
}
