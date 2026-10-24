/**
 * 0.4.0 Đơn gộp: khách thấy MỘT đơn; mỗi dòng chọn bên bán (APH / VH / MK / TL) + kho. Chốt → hệ thống tách đơn con theo bên bán.
 * Bốn trạng thái độc lập: duyệt · giao · thanh toán · hóa đơn. Giao một chuyến gồm nhiều đơn con / kho, xác nhận theo cân thực.
 */
import { Alert, App, Button, Card, Checkbox, Descriptions, Drawer, Input, InputNumber, Modal, Segmented, Select, Space, Table, Tag, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, TRANG_THAI_DON, dvt, fmt, ngayVN, theTrangThai, useGoi } from './chung';

export const TT_GOP: Record<string, Record<string, [string, string]>> = {
  tt_duyet: { nhap: ['Nháp', 'default'], cho_duyet: ['Chờ duyệt', 'purple'], da_duyet: ['Đã duyệt', 'green'], tu_choi: ['Từ chối', 'red'], da_huy: ['Đã hủy', 'red'] },
  tt_giao: { chua_giu: ['Chưa giữ hàng', 'default'], da_giu: ['Đã giữ hàng', 'cyan'], thieu_giu: ['Giữ thiếu', 'orange'], cho_xuat: ['Chờ xuất', 'orange'],
    dang_giao: ['Đang giao', 'blue'], mot_phan: ['Giao một phần', 'blue'], du: ['Đã giao đủ', 'green'], dong: ['Đóng phần chưa giao', 'default'] },
  tt_thanh_toan: { chua_thu: ['Chưa thu', 'default'], mot_phan: ['Thu một phần', 'orange'], du: ['Đã thu đủ', 'green'], phai_hoan: ['Có khoản phải hoàn', 'red'] },
  tt_hoa_don: { khong: ['Không yêu cầu HĐ', 'default'], cho_xu_ly: ['HĐ chờ xử lý', 'orange'], dang_lap: ['HĐ đang lập', 'blue'], da_xuat: ['Đã xuất HĐ', 'green'],
    can_dieu_chinh: ['HĐ cần điều chỉnh', 'red'] },
};
const the = (k: string, v: string) => { const [t, m] = TT_GOP[k]?.[v] || [v, 'default']; return <Tag color={m}>{t}</Tag>; };
const rid = () => (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`);

function LapDonGop({ xong }: { xong: (id: any) => void }) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [kh, setKh] = useState<any>(null);
  const [cach, setCach] = useState('khach_den_lay');
  const [dvBan, setDvBan] = useState<any[]>([]);
  const [dong, setDong] = useState<any[]>([{}]);
  const [qd, setQd] = useState<Record<string, any[]>>({});
  const [req] = useState(rid());
  useEffect(() => { goi('don_vi:list', { params: { pageSize: 20 } }).then((r) => setDvBan(r.data || [])); }, []);
  const doi = (i: number, v: any) => setDong(dong.map((d, j) => (j === i ? { ...d, ...v } : d)));
  const napQd = async (mh: any) => {
    if (!mh || mh in qd) return;
    const r = await goi('quy_doi_dvt:list', { params: { filter: { mat_hang_id: mh } }, im: true }).catch(() => ({ data: [] }));
    setQd((x) => ({ ...x, [mh]: r.data || [] }));
  };
  const luu = async () => {
    if (!kh) return message.warning('Chọn khách.');
    const ds = dong.filter((d) => d.mat_hang_id);
    if (!ds.length) return message.warning('Thêm hàng.');
    if (ds.some((d) => !d.don_vi_ban_id || !d.kho_id)) return message.warning('Mỗi dòng chọn bên bán và kho.');
    const r = await goi('don_gop:create', { params: { 'updateAssociationValues[]': 'dong' }, data: { khach_id: kh, cach_giao: cach, request_id: req,
      dong: ds.map((d) => ({ mat_hang_id: d.mat_hang_id, don_vi_ban_id: d.don_vi_ban_id, kho_id: d.kho_id, so_bao: d.so_bao ?? null,
        ...(d.dvt_nhap ? { dvt_nhap: d.dvt_nhap, sl_nhap: d.sl_nhap } : { so_kg: d.so_kg }), don_gia: d.don_gia ?? null, vat_ap_dung: !!d.vat_ap_dung,
        ghi_chu: d.ghi_chu || null })) } });
    message.success(`Đã lưu ${r.data.so}`);
    xong(r.data.id);
  };
  return <>
    <Space wrap style={{ marginBottom: 12 }}>
      <ChonDanhMuc bang="khach_hang" value={kh} onChange={setKh} placeholder="Khách (mã / tên / SĐT)" timTheo={['ma', 'ten', 'sdt', 'nhan']} style={{ width: 320 }} />
      <Segmented value={cach} onChange={(v: any) => setCach(v)} options={[{ value: 'khach_den_lay', label: 'Khách đến lấy' }, { value: 'van_chuyen', label: 'Vận chuyển' }]} />
    </Space>
    <Table size="small" rowKey={(_, i) => String(i)} pagination={false} dataSource={dong} columns={[
      { title: 'Mặt hàng', width: 260, render: (_, d, i) => <ChonDanhMuc bang="mat_hang" value={d.mat_hang_id} style={{ width: 250 }} timTheo={['ma', 'ten', 'ma_vach', 'nhan']}
        onChange={(v, mh) => { doi(i, { mat_hang_id: v, mh }); napQd(v); }} /> },
      { title: 'Bên bán', width: 120, render: (_, d, i) => <Select style={{ width: 110 }} value={d.don_vi_ban_id} onChange={(v) => doi(i, { don_vi_ban_id: v })}
        options={dvBan.map((x) => ({ value: x.id, label: x.ma }))} /> },
      { title: 'Kho xuất', width: 200, render: (_, d, i) => <ChonDanhMuc bang="kho" value={d.kho_id} style={{ width: 190 }} locThem={{ trung_chuyen: { $ne: true } }}
        onChange={(v) => doi(i, { kho_id: v })} /> },
      { title: 'ĐVT', width: 100, render: (_, d, i) => {
        const ds = qd[d.mat_hang_id] || [];
        return ds.length ? <Select style={{ width: 90 }} value={d.dvt_nhap || ''} onChange={(v) => doi(i, { dvt_nhap: v || null, sl_nhap: v ? d.sl_nhap || 1 : null })}
          options={[{ value: '', label: dvt(d.mh) }, ...ds.map((x: any) => ({ value: x.dvt, label: `${x.dvt} (=${fmt(x.he_so, 3)})` }))]} /> : dvt(d.mh);
      } },
      { title: 'Số lượng', width: 120, render: (_, d, i) => <InputNumber min={0} value={d.dvt_nhap ? d.sl_nhap : d.so_kg} style={{ width: 110 }}
        onChange={(v) => doi(i, d.dvt_nhap ? { sl_nhap: v } : { so_kg: v, so_bao: d.mh?.kg_bao && v ? Math.round((Number(v) / d.mh.kg_bao) * 100) / 100 : d.so_bao })} /> },
      { title: 'Số bao', width: 90, render: (_, d, i) => <InputNumber min={0} value={d.so_bao} style={{ width: 80 }}
        onChange={(v) => doi(i, { so_bao: v, ...(d.mh?.kg_bao && v && !d.dvt_nhap ? { so_kg: Math.round(Number(v) * d.mh.kg_bao * 1000) / 1000 } : {}) })} /> },
      { title: 'Đơn giá (trống = bảng giá)', width: 150, render: (_, d, i) => <InputNumber min={0} value={d.don_gia} style={{ width: 140 }} onChange={(v) => doi(i, { don_gia: v })} /> },
      { title: 'VAT', width: 60, render: (_, d, i) => <Checkbox checked={!!d.vat_ap_dung} onChange={(e) => doi(i, { vat_ap_dung: e.target.checked })} /> },
      { title: 'Ghi chú / lý do giá', render: (_, d, i) => <Input value={d.ghi_chu} onChange={(e) => doi(i, { ghi_chu: e.target.value })} /> },
      { width: 40, render: (_, __, i) => <Button size="small" danger onClick={() => setDong(dong.filter((_, j) => j !== i))}>×</Button> },
    ]} />
    <Space style={{ marginTop: 12 }}>
      <Button onClick={() => setDong([...dong, { don_vi_ban_id: dong[dong.length - 1]?.don_vi_ban_id, kho_id: dong[dong.length - 1]?.kho_id }])}>+ Dòng</Button>
      <Button type="primary" onClick={luu}>Lưu nháp</Button>
    </Space>
    <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>Cùng mặt hàng có thể thuộc nhiều bên bán (hai dòng). Khi chốt, mỗi bên bán thành một đơn con;
      công nợ, thu tiền, trả hàng và hóa đơn đi theo đơn con.</Typography.Paragraph>
  </>;
}

function GiaoGop({ dg, dong, xong }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [sl, setSl] = useState<Record<string, any>>({});
  const [req] = useState(rid());
  const [chuyen, setChuyen] = useState<any>(null);
  const [thuc, setThuc] = useState<Record<string, any>>({});
  const tao = async () => {
    const ds = dong.filter((d: any) => Number(sl[d.id]?.so_kg) > 0).map((d: any) => ({ don_gop_dong_id: d.id, ...sl[d.id] }));
    if (!ds.length) return message.warning('Nhập lượng giao.');
    const r = await goi('don_gop:taoGiao', { params: { filterByTk: dg.id }, data: { request_id: req, dong: ds } });
    const ls = await goi('giao_gop_luot:list', { params: { filter: { giao_gop_id: r.data.id }, appends: ['luot_giao', 'luot_giao.dong', 'luot_giao.dong.mat_hang'] } });
    setChuyen({ id: r.data.id, so: r.data.so, luot: ls.data || [] });
  };
  const xn = async () => {
    await goi('giao_gop:xacNhan', { params: { filterByTk: chuyen.id }, data: { thuc } });
    message.success('Đã xuất chuyến');
    window.open(`/in/giao_gop/${chuyen.id}`, '_blank');
    xong();
  };
  if (chuyen) {
    return <>
      <Alert type="info" showIcon message={`Chuyến ${chuyen.so}: cân / đếm thực tế từng dòng rồi xác nhận (để trống = đúng như chuẩn bị).`} style={{ marginBottom: 8 }} />
      <Table size="small" rowKey="id" pagination={false} dataSource={(chuyen.luot as any[]).flatMap((l: any) => (l.luot_giao?.dong || []).map((x: any) => ({ ...x, luot: l.luot_giao?.so })))}
        columns={[{ title: 'Lượt', dataIndex: 'luot' }, { title: 'Hàng', render: (_, x) => x.mat_hang?.ma }, { title: 'Chuẩn bị', render: (_, x) => `${fmt(x.so_kg, 3)} / ${fmt(x.so_bao, 2)} bao` },
          { title: 'Thực xuất (cân)', render: (_, x) => <InputNumber min={0} value={thuc[x.id]?.so_kg} onChange={(v) => setThuc({ ...thuc, [x.id]: { ...thuc[x.id], so_kg: v } })} /> },
          { title: 'Bao thực', render: (_, x) => <InputNumber min={0} value={thuc[x.id]?.so_bao} onChange={(v) => setThuc({ ...thuc, [x.id]: { ...thuc[x.id], so_bao: v } })} /> },
          { title: 'Lý do chênh', render: (_, x) => <Input value={thuc[x.id]?.ly_do} onChange={(e) => setThuc({ ...thuc, [x.id]: { ...thuc[x.id], ly_do: e.target.value } })} /> }]} />
      <Button type="primary" style={{ marginTop: 8 }} onClick={xn}>{dg.cach_giao === 'van_chuyen' ? 'Xác nhận bàn giao xe' : 'Xác nhận khách đã nhận'}</Button>
    </>;
  }
  return <>
    <Table size="small" rowKey="id" pagination={false} dataSource={dong as any[]} columns={[
      { title: 'Bên bán', render: (_, d) => d.don_vi_ban?.ma }, { title: 'Hàng', render: (_, d) => d.mat_hang?.ma }, { title: 'Kho', render: (_, d) => d.kho?.ten },
      { title: 'Đặt', render: (_, d) => fmt(d.so_kg, 3) }, { title: 'Đã giao', render: (_, d) => fmt(d.da_giao, 3) },
      { title: 'Giao đợt này', render: (_, d) => <InputNumber min={0} value={sl[d.id]?.so_kg} onChange={(v) => setSl({ ...sl, [d.id]: { ...sl[d.id], so_kg: v } })} /> },
      { title: 'Bao', render: (_, d) => <InputNumber min={0} value={sl[d.id]?.so_bao} onChange={(v) => setSl({ ...sl, [d.id]: { ...sl[d.id], so_bao: v } })} /> },
    ]} />
    <Space style={{ marginTop: 8 }}>
      <Button onClick={() => setSl(Object.fromEntries(dong.map((d: any) => [d.id, { so_kg: Math.max(0, Number(d.so_kg) - Number(d.da_giao || 0)), so_bao: d.so_bao }])))}>Giao hết phần còn lại</Button>
      <Button type="primary" onClick={tao}>Tạo chuyến giao</Button>
    </Space>
  </>;
}

function XemDonGop({ id, xong }: any) {
  const goi = useGoi();
  const { message, modal } = App.useApp();
  const [dg, setDg] = useState<any>(null);
  const [con, setCon] = useState<any[]>([]);
  const [dong, setDong] = useState<any[]>([]);
  const [giao, setGiao] = useState(false);
  const tai = async () => {
    const r = await goi('don_gop:get', { params: { filterByTk: id, appends: ['khach', 'dong', 'dong.mat_hang', 'dong.don_vi_ban', 'dong.kho'] } });
    setDg(r.data);
    const c = await goi('don_ban:list', { params: { filter: { don_gop_id: id }, appends: ['don_vi_ban', 'dong'], pageSize: 20 } });
    setCon(c.data || []);
    const daGiao: Record<string, number> = {};
    for (const d of c.data || []) for (const x of d.dong || []) daGiao[x.id] = Number(x.da_giao || 0);
    setDong((r.data.dong || []).map((x: any) => ({ ...x, da_giao: daGiao[x.don_ban_dong_id] || 0 })));
  };
  useEffect(() => { tai(); }, [id]);
  if (!dg) return null;
  const lam = async (act: string, data: any = {}) => { const r = await goi(`don_gop:${act}`, { params: { filterByTk: id }, data }); message.success('Xong'); await tai(); xong(); return r; };
  const lyDo = (act: string, tieuDe: string) => {
    let v = '';
    modal.confirm({ title: tieuDe, content: <Input.TextArea onChange={(e) => (v = e.target.value)} placeholder="Lý do (bắt buộc)" />, onOk: () => lam(act, { ly_do: v }) });
  };
  return <>
    <Descriptions size="small" column={3} bordered items={[
      { label: 'Số', children: <b>{dg.so}</b> }, { label: 'Khách', children: dg.khach?.ten }, { label: 'Ngày', children: ngayVN(dg.ngay) },
      { label: 'Duyệt', children: the('tt_duyet', dg.tt_duyet) }, { label: 'Giao', children: the('tt_giao', dg.tt_giao) },
      { label: 'Thanh toán', children: the('tt_thanh_toan', dg.tt_thanh_toan) }, { label: 'Hóa đơn', children: the('tt_hoa_don', dg.tt_hoa_don) },
      { label: 'Tổng tiền', children: fmt(dg.tong_tien) }, { label: 'Còn nợ', children: <b>{fmt(dg.con_no)}</b> },
    ]} />
    {dg.ly_do_duyet && <Alert type="warning" showIcon style={{ marginTop: 8 }} message={dg.ly_do_duyet} />}
    <Space style={{ margin: '12px 0' }} wrap>
      {dg.tt_duyet === 'nhap' && <Button type="primary" onClick={() => lam('chot')}>Chốt đơn gộp (tách đơn con)</Button>}
      {con.some((c) => c.trang_thai === 'cho_duyet') && <Button onClick={() => lyDo('duyet', 'Duyệt các đơn con chờ duyệt')}>Duyệt</Button>}
      {con.some((c) => ['cho_xuat', 'dang_giao'].includes(c.trang_thai)) && <Button type="primary" onClick={() => setGiao(true)}>Giao hàng…</Button>}
      <Button onClick={() => window.open(`/in/don_gop/${id}`, '_blank')}>In đơn cho khách</Button>
      {dg.tt_duyet !== 'da_huy' && <Button danger onClick={() => lyDo('huy', 'Hủy đơn gộp (hủy mọi đơn con chưa giao)')}>Hủy</Button>}
    </Space>
    <Typography.Title level={5}>Dòng hàng</Typography.Title>
    <Table size="small" rowKey="id" pagination={false} dataSource={dong} columns={[
      { title: 'Bên bán', render: (_, d) => <Tag>{d.don_vi_ban?.ma}</Tag> }, { title: 'Mã', render: (_, d) => d.mat_hang?.ma }, { title: 'Tên', render: (_, d) => d.mat_hang?.ten },
      { title: 'Kho', render: (_, d) => d.kho?.ten }, { title: 'Số lượng', align: 'right', render: (_, d) => `${fmt(d.so_kg, 3)} ${dvt(d.mat_hang)}` },
      { title: 'Đã giao', align: 'right', render: (_, d) => fmt(d.da_giao, 3) }, { title: 'VAT', render: (_, d) => (d.vat_ap_dung ? `${fmt(d.thue_suat, 2)}%` : '') },
    ]} />
    {con.length > 0 && <><Typography.Title level={5} style={{ marginTop: 16 }}>Đơn con theo bên bán</Typography.Title>
      <Table size="small" rowKey="id" pagination={false} dataSource={con} columns={[
        { title: 'Đơn con', dataIndex: 'so' }, { title: 'Bên bán', render: (_, c) => c.don_vi_ban?.ma },
        { title: 'Trạng thái', render: (_, c) => { const [t, m] = theTrangThai(TRANG_THAI_DON, c.trang_thai); return <Tag color={m}>{t}</Tag>; } },
        { title: 'Tổng', align: 'right', render: (_, c) => fmt(c.tong_tien) }, { title: 'Phải thu (đã giao)', align: 'right', render: (_, c) => fmt(c.phai_thu) },
        { title: 'Đã thu', align: 'right', render: (_, c) => fmt(c.da_thu) }, { title: 'Còn nợ', align: 'right', render: (_, c) => fmt(c.con_no) },
        { title: 'Phải hoàn', align: 'right', render: (_, c) => (Number(c.phai_hoan) ? <b style={{ color: '#cf1322' }}>{fmt(c.phai_hoan)}</b> : '') },
        { title: 'Cảnh báo', render: (_, c) => c.canh_bao_tin_dung ? <Typography.Text type="warning">{c.canh_bao_tin_dung}</Typography.Text> : c.ly_do_duyet },
      ]} /></>}
    <Modal width="90%" open={giao} onCancel={() => setGiao(false)} footer={null} title="Giao hàng — một chuyến nhiều đơn con" destroyOnClose>
      <GiaoGop dg={dg} dong={dong.filter((d) => d.don_ban_dong_id)} xong={() => { setGiao(false); tai(); xong(); }} />
    </Modal>
  </>;
}

export function DonGop() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [loc, setLoc] = useState('mo');
  const [q, setQ] = useState('');
  const [mo, setMo] = useState<any>(null);
  const tai = async () => {
    const f: any = { $and: [] };
    if (loc === 'mo') f.$and.push({ tt_duyet: { $ne: 'da_huy' } }, { tt_giao: { $notIn: ['du', 'dong'] } });
    if (loc === 'no') f.$and.push({ con_no: { $gt: 0 } });
    if (q) f.$and.push({ $or: [{ so: { $includes: q } }, { 'khach.ten': { $includes: q } }, { 'khach.sdt': { $includes: q } }] });
    const r = await goi('don_gop:list', { params: { filter: f, appends: ['khach'], sort: ['-id'], pageSize: 50 } });
    setDs(r.data || []);
  };
  useEffect(() => { tai(); }, [loc]);
  return <>
    <Space style={{ marginBottom: 12 }} wrap>
      <Button type="primary" size="large" onClick={() => setMo('moi')}>+ Lập đơn gộp</Button>
      <Segmented value={loc} onChange={(v: any) => setLoc(v)} options={[{ value: 'mo', label: 'Đang xử lý' }, { value: 'no', label: 'Còn nợ' }, { value: 'tat_ca', label: 'Tất cả' }]} />
      <Input.Search placeholder="Số đơn, khách, SĐT" allowClear onSearch={(v) => { setQ(v); setTimeout(tai); }} style={{ width: 260 }} />
    </Space>
    <Table size="middle" rowKey="id" dataSource={ds} onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Số', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Khách', render: (_, r) => r.khach?.ten },
      { title: 'Duyệt', render: (_, r) => the('tt_duyet', r.tt_duyet) }, { title: 'Giao', render: (_, r) => the('tt_giao', r.tt_giao) },
      { title: 'Thanh toán', render: (_, r) => the('tt_thanh_toan', r.tt_thanh_toan) }, { title: 'Hóa đơn', render: (_, r) => the('tt_hoa_don', r.tt_hoa_don) },
      { title: 'Tổng tiền', dataIndex: 'tong_tien', align: 'right', render: (v) => fmt(v) }, { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v) => fmt(v) },
    ]} />
    <Drawer width="94%" open={!!mo} onClose={() => { setMo(null); tai(); }} title={mo === 'moi' ? 'Lập đơn gộp' : 'Đơn gộp'} destroyOnClose>
      {mo === 'moi' ? <LapDonGop xong={(id) => setMo(id)} /> : mo && <XemDonGop id={mo} xong={tai} />}
    </Drawer>
  </>;
}

export function TrangBanHang({ BanHang }: { BanHang: any }) {
  const [tab, setTab] = useState('gop');
  return <Card title="Bán hàng" extra={<Segmented value={tab} onChange={(v: any) => setTab(v)} options={[{ value: 'gop', label: 'Đơn gộp (nhiều bên bán)' }, { value: 'don', label: 'Đơn từng bên bán' }]} />}>
    {tab === 'gop' ? <DonGop /> : <BanHang />}
  </Card>;
}
