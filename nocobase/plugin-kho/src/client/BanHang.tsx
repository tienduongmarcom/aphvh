/** Màn hình Bán hàng: danh sách đơn + lập đơn (chọn đơn vị bán) + chốt & in + xác nhận giao. */
import {
  Alert, App, Button, Card, Checkbox, Col, Select, DatePicker, Drawer, Form, Input, InputNumber, Radio, Row, Segmented, Space, Table, Tag, Typography,
} from 'antd';
import dayjs from 'dayjs';
import React, { useEffect, useMemo, useState } from 'react';
import { ChonDanhMuc, TRANG_THAI_DON, dvt, fmt, homNay, ngayVN, theTrangThai, useGoi } from './chung';
import { GiaoHangDon, moInLuot, taoLuot } from './LuotGiao';

const moIn = (id: any) => window.open(`/in/don_ban/${id}`, '_blank');

function DongHang({ dong, setDong, sua, khoMacDinh }: any) {
  const goi = useGoi();
  const [ton, setTon] = useState<Record<string, number>>({});
  useEffect(() => {
    dong.forEach(async (d: any) => {
      if (!d.mat_hang_id || !d.kho_id) return;
      const k = `${d.kho_id}-${d.mat_hang_id}`;
      if (k in ton) return;
      const r = await goi('ton_kho:list', { params: { filter: { kho_id: d.kho_id, mat_hang_id: d.mat_hang_id } }, im: true });
      const x = r.data?.[0];
      // Khả dụng = tồn − đang giữ cho lượt chưa giao − hàng chờ định giá
      setTon((t) => ({ ...t, [k]: x ? Number(x.so_kg || 0) - Number(x.so_giu || 0) - Number(x.so_cho_gia || 0) : 0 }));
    });
  }, [JSON.stringify(dong.map((d: any) => [d.kho_id, d.mat_hang_id]))]);
  const doi = (i: number, v: any) => setDong(dong.map((d: any, j: number) => (j === i ? { ...d, ...v } : d)));
  const [qd, setQd] = useState<Record<string, any[]>>({});
  useEffect(() => {
    dong.forEach(async (d: any) => {
      if (!d.mat_hang_id || d.mat_hang_id in qd) return;
      const r = await goi('quy_doi_dvt:list', { params: { filter: { mat_hang_id: d.mat_hang_id }, pageSize: 20 }, im: true }).catch(() => ({ data: [] }));
      setQd((x) => ({ ...x, [d.mat_hang_id]: r.data || [] }));
    });
  }, [JSON.stringify(dong.map((d: any) => d.mat_hang_id))]);
  const heSo = (d: any) => (qd[d.mat_hang_id] || []).find((x: any) => x.dvt === d.dvt_nhap)?.he_so;
  const cot: any[] = [
    { title: 'Mã hàng', width: 260, render: (_: any, d: any, i: number) => sua
      ? <ChonDanhMuc bang="mat_hang" value={d.mat_hang_id} style={{ width: 250 }} locThem={{ ngung_dung: { $ne: true } }}
          onChange={(v, mh) => doi(i, { mat_hang_id: v, ma: mh?.ma, ten_hang: mh?.ten, dvt_ton: mh?.dvt_ton, kg_bao: mh?.kg_bao, gia_san: mh?.gia_san, don_gia: d.don_gia ?? mh?.gia_ban,
            so_kg: d.so_bao && mh?.kg_bao ? d.so_bao * mh.kg_bao : d.so_kg })} placeholder="Gõ mã hoặc tên hàng" />
      : <b>{d.mat_hang?.ma || d.ma}</b> },
    { title: 'Tên hàng', render: (_: any, d: any) => d.ten_hang || d.mat_hang?.ten },
    { title: 'Kho xuất', width: 200, render: (_: any, d: any, i: number) => sua
      ? <ChonDanhMuc bang="kho" value={d.kho_id ?? khoMacDinh} style={{ width: 190 }} locThem={{ ngung_dung: { $ne: true } }}
          onChange={(v) => doi(i, { kho_id: v })} />
      : d.kho?.ten },
    { title: 'Số bao', width: 100, render: (_: any, d: any, i: number) => sua
      ? <InputNumber min={0} value={d.so_bao} style={{ width: 90 }}
          onChange={(v) => doi(i, { so_bao: v, so_kg: v && d.kg_bao ? Math.round(v * d.kg_bao * 1000) / 1000 : d.so_kg })} />
      : fmt(d.so_bao, 2) },
    { title: 'ĐVT bán', width: 100, render: (_: any, d: any, i: number) => {
      const ds = qd[d.mat_hang_id] || [];
      if (!sua) return d.dvt_nhap ? `${fmt(d.sl_nhap, 3)} ${d.dvt_nhap}` : dvt(d.mat_hang || d);
      if (!ds.length) return dvt(d.mat_hang || d);
      return <Select size="small" style={{ width: 90 }} value={d.dvt_nhap || ''} onChange={(v) => doi(i, v ? { dvt_nhap: v, sl_nhap: d.sl_nhap || 1,
        so_kg: Math.round((d.sl_nhap || 1) * Number(ds.find((x: any) => x.dvt === v)?.he_so || 0) * 1000) / 1000 } : { dvt_nhap: null, sl_nhap: null })}
        options={[{ value: '', label: dvt(d.mat_hang || d) }, ...ds.map((x: any) => ({ value: x.dvt, label: x.dvt }))]} />;
    } },
    { title: 'Số lượng', width: 130, render: (_: any, d: any, i: number) => {
      const t = ton[`${d.kho_id ?? khoMacDinh}-${d.mat_hang_id}`];
      if (sua && d.dvt_nhap) return <div><InputNumber min={0} value={d.sl_nhap} style={{ width: 110 }}
        onChange={(v) => doi(i, { sl_nhap: v, so_kg: Math.round(Number(v || 0) * Number(heSo(d) || 0) * 1000) / 1000 })} />
        <div style={{ fontSize: 12, color: '#888' }}>= {fmt(d.so_kg, 3)} {dvt(d.mat_hang || d)}{t !== undefined ? ` · khả dụng ${fmt(t, 3)}` : ''}</div></div>;
      return sua ? <div><InputNumber min={0} value={d.so_kg} style={{ width: 110 }} onChange={(v) => doi(i, { so_kg: v })} />
        {t !== undefined && <div style={{ fontSize: 12, color: t < (d.so_kg || 0) ? '#cf1322' : '#888' }}>Khả dụng: {fmt(t, 3)} {dvt(d.mat_hang || d)}</div>}</div>
        : `${fmt(d.so_kg, 3)} ${dvt(d.mat_hang || d)}`;
    } },
    { title: 'Đơn giá', width: 130, render: (_: any, d: any, i: number) => sua
      ? <InputNumber min={0} value={d.don_gia} style={{ width: 120 }} formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))}
          onChange={(v) => doi(i, { don_gia: v })} />
      : fmt(d.don_gia) },
    { title: '', width: 90, render: (_: any, d: any) => (Number(d.gia_san) > 0 && Number(d.don_gia || 0) < Number(d.gia_san)
      ? <Tag color="purple">Dưới giá sàn</Tag> : null) },
    { title: 'Thành tiền', width: 130, align: 'right', render: (_: any, d: any) => fmt(Math.round((d.so_kg || 0) * (d.don_gia || 0))) },
  ];
  if (sua) cot.push({ width: 50, render: (_: any, __: any, i: number) => <Button danger size="small" onClick={() => setDong(dong.filter((_: any, j: number) => j !== i))}>Xóa</Button> });
  return (
    <>
      <Table size="small" rowKey={(d: any, i: any) => d.id || `moi-${i}`} pagination={false} columns={cot} dataSource={dong}
        summary={() => <Table.Summary.Row><Table.Summary.Cell index={0} colSpan={5} align="right"><b>Cộng</b></Table.Summary.Cell>
          <Table.Summary.Cell index={1}><b>{fmt(dong.reduce((s: number, d: any) => s + Number(d.so_kg || 0), 0), 3)}</b></Table.Summary.Cell>
          <Table.Summary.Cell index={2} /><Table.Summary.Cell index={4} />
          <Table.Summary.Cell index={3} align="right"><b>{fmt(dong.reduce((s: number, d: any) => s + Math.round((d.so_kg || 0) * (d.don_gia || 0)), 0))}</b></Table.Summary.Cell>
        </Table.Summary.Row>} />
      {sua && <Button style={{ marginTop: 8 }} onClick={() => setDong([...dong, { kho_id: khoMacDinh }])}>+ Thêm hàng</Button>}
    </>
  );
}

function DonBan({ id, dong: dongDong, xong }: any) {
  const goi = useGoi();
  const { modal, message } = App.useApp();
  const [form] = Form.useForm();
  const [don, setDon] = useState<any>(null);
  const [dong, setDong] = useState<any[]>([{}]);
  const [khach, setKhach] = useState<any>(null);
  const [dang, setDang] = useState(false);
  const [khoMacDinh, setKhoMacDinh] = useState<any>(() => { try { return Number(localStorage.getItem('aph_kho_mac_dinh')) || undefined; } catch { return undefined; } });
  const sua = !don || don.trang_thai === 'nhap';

  const tai = async (x = id) => {
    if (!x) {
      form.setFieldsValue({ ngay: dayjs(homNay()), ngay_giao: dayjs(homNay()), cach_giao: 'khach_den_lay' });
      return;
    }
    const r = await goi('don_ban:get', { params: { filterByTk: x, appends: ['khach', 'don_vi_ban', 'dong', 'dong.mat_hang', 'dong.kho'] } });
    const d = r.data;
    setDon(d);
    setKhach(d.khach);
    setDong((d.dong || []).sort((a: any, b: any) => a.id - b.id).map((l: any) => ({ ...l, kg_bao: l.mat_hang?.kg_bao, gia_san: l.mat_hang?.gia_san })));
    form.setFieldsValue({ ...d, ngay: d.ngay ? dayjs(d.ngay) : null, ngay_giao: d.ngay_giao ? dayjs(d.ngay_giao) : null });
  };
  useEffect(() => { tai(); }, [id]);

  const luu = async () => {
    const v = await form.validateFields();
    const hang = dong.filter((d) => d.mat_hang_id);
    if (!hang.length) { message.warning('Thêm ít nhất một dòng hàng.'); throw new Error('thieu'); }
    for (const d of hang) if (!(d.kho_id ?? khoMacDinh)) { message.warning('Chọn kho xuất cho mọi dòng.'); throw new Error('thieu'); }
    const values = {
      ...v, ngay: v.ngay?.format('YYYY-MM-DD'), ngay_giao: v.ngay_giao?.format('YYYY-MM-DD'),
      dong: hang.map((d) => ({ ...(d.id ? { id: d.id } : {}), mat_hang_id: d.mat_hang_id, kho_id: d.kho_id ?? khoMacDinh, so_bao: d.so_bao || 0, so_kg: d.so_kg || 0, don_gia: d.don_gia || 0,
        dvt_nhap: d.dvt_nhap || null, sl_nhap: d.dvt_nhap ? d.sl_nhap : null })),
    };
    const k = hang[hang.length - 1].kho_id ?? khoMacDinh;
    try { localStorage.setItem('aph_kho_mac_dinh', String(k)); } catch { /* bỏ qua */ }
    setKhoMacDinh(k);
    if (don?.id) {
      await goi('don_ban:update', { params: { filterByTk: don.id, updateAssociationValues: ['dong'] }, data: values });
      return don.id;
    }
    const r = await goi('don_ban:create', { params: { updateAssociationValues: ['dong'] }, data: values });
    return r.data.id;
  };
  const chay = async (fn: () => Promise<any>) => {
    setDang(true);
    try { await fn(); } catch { /* đã báo lỗi */ } finally { setDang(false); }
  };
  const luuNhap = () => chay(async () => { const x = await luu(); message.success('Đã lưu nháp'); await tai(x); dongDong?.(x); });
  const chotIn = () => chay(async () => {
    const x = await luu();
    const r = await goi('don_ban:chotDon', { params: { filterByTk: x }, data: {} });
    if (r.data?.cho_duyet) message.warning(`Đơn cần quản lý duyệt trước khi giao: ${r.data?.ly_do || 'dưới giá sàn hoặc vượt hạn mức công nợ'}.`, 8);
    else {
      message.success('Đã chốt đơn');
      // Mặc định một lượt giao toàn bộ (đa số khách đến lấy). Giao nhiều đợt: hủy lượt này và tạo lượt theo lượng.
      const d = (await goi('don_ban:get', { params: { filterByTk: x, appends: ['dong'] } })).data;
      try { const l = await taoLuot(goi, d, d.dong || []); if (l) moInLuot(l); } catch { /* thiếu hàng khả dụng: đã báo, đơn vẫn chốt */ }
    }
    await tai(x); xong?.();
  });
  const hoi = (title: string, url: string, okText: string, canLyDo = true) => {
    let ly_do = '';
    modal.confirm({
      title, okText, cancelText: 'Thôi', okButtonProps: { danger: true },
      content: canLyDo ? <Input.TextArea placeholder="Lý do (bắt buộc nếu đơn đã giao)" onChange={(e) => (ly_do = e.target.value)} /> : null,
      onOk: () => goi(url, { params: { filterByTk: don.id }, data: { ly_do } }).then(() => { tai(don.id); xong?.(); }),
    });
  };
  const [tt, mau] = theTrangThai(TRANG_THAI_DON, don?.trang_thai || 'nhap');

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {don && <Space><Typography.Title level={4} style={{ margin: 0 }}>{don.so}</Typography.Title><Tag color={mau}>{tt}</Tag>
        {Number(don.phai_thu) > 0 && <span>Phải thu <b>{fmt(don.phai_thu)}</b> · Đã thu <b>{fmt(don.da_thu)}</b> · Còn nợ: <b>{fmt(don.con_no)}</b> đ</span>}</Space>}
      <Form form={form} layout="vertical" disabled={!sua}>
        <Row gutter={12}>
          <Col span={10}><Form.Item name="khach_id" label="Khách hàng" rules={[{ required: true, message: 'Chọn khách' }]}>
            <ChonDanhMuc bang="khach_hang" timTheo={['ma', 'ten', 'sdt', 'nhan']} placeholder="Gõ tên, mã hoặc số điện thoại" style={{ width: '100%' }}
              onChange={(v, k) => { form.setFieldValue('khach_id', v); setKhach(k); form.setFieldsValue({ dia_chi_giao: k?.dia_chi, sdt: k?.sdt }); }} />
          </Form.Item></Col>
          <Col span={8}><Form.Item name="don_vi_ban_id" label="Đơn vị bán" rules={[{ required: true, message: 'Chọn đơn vị bán' }]}>
            <ChonDanhMuc bang="don_vi" style={{ width: '100%' }} />
          </Form.Item></Col>
          <Col span={3}><Form.Item name="ngay" label="Ngày đặt"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
          <Col span={3}><Form.Item name="ngay_giao" label="Ngày giao"><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
        </Row>
        {khach && <Alert style={{ marginBottom: 12 }} type="info" showIcon={false} message={<span>
          <b>{khach.ten}</b> · Mã {khach.ma} · ĐT <b>{khach.sdt || '—'}</b> · Địa chỉ: {khach.dia_chi || '—'}{khach.mst ? ` · MST ${khach.mst}` : ''}</span>} />}
        <Row gutter={12}>
          <Col span={8}><Form.Item name="cach_giao" label="Cách giao">
            <Radio.Group optionType="button" options={[{ value: 'khach_den_lay', label: 'Khách đến lấy' }, { value: 'van_chuyen', label: 'Vận chuyển' }]} />
          </Form.Item></Col>
          <Col span={8}><Form.Item name="nguoi_nhan" label="Người nhận / lái xe"><Input /></Form.Item></Col>
          <Col span={8}><Form.Item name="bien_so" label="Biển số xe"><Input /></Form.Item></Col>
        </Row>
        <Row gutter={12}>
          <Col span={12}><Form.Item name="dia_chi_giao" label="Địa chỉ giao"><Input /></Form.Item></Col>
          <Col span={8}><Form.Item name="ghi_chu" label="Ghi chú"><Input /></Form.Item></Col>
          <Col span={4}><Form.Item name="xuat_hoa_don" label="Hóa đơn" valuePropName="checked"><Checkbox>Xuất hóa đơn MISA</Checkbox></Form.Item></Col>
        </Row>
      </Form>
      <Card size="small" title="Hàng bán">
        <DongHang dong={dong} setDong={setDong} sua={sua} khoMacDinh={khoMacDinh} />
      </Card>
      <Space wrap>
        {sua && <Button onClick={luuNhap} loading={dang}>Lưu nháp</Button>}
        {sua && <Button type="primary" size="large" onClick={chotIn} loading={dang}>Chốt đơn &amp; In phiếu xuất</Button>}
        {don?.trang_thai === 'cho_duyet' && <Button type="primary" size="large" onClick={() => {
          let ly_do = '';
          modal.confirm({ title: `Duyệt đơn ${don.so}? (${don.ly_do_duyet || ''})`, okText: 'Duyệt', cancelText: 'Thôi',
            content: <Input.TextArea placeholder="Lý do đồng ý (bắt buộc)" onChange={(e) => (ly_do = e.target.value)} />,
            onOk: () => goi('don_ban:duyetGia', { params: { filterByTk: don.id }, data: { ly_do } }).then(() => { message.success('Đã duyệt'); tai(don.id); xong?.(); }) });
        }}>Duyệt (quản lý)</Button>}
        {don?.trang_thai === 'cho_duyet' && <Tag color="purple">Cần duyệt: {don.ly_do_duyet}</Tag>}
        {don?.duyet_boi && <Tag color="purple">Đã duyệt giá: {don.duyet_boi} — {don.ly_do_gia}</Tag>}
        {don && ['cho_xuat', 'dang_giao', 'da_giao', 'da_dong'].includes(don.trang_thai) && <Button onClick={() => moIn(don.id)}>In đơn hàng</Button>}
        {['cho_xuat', 'cho_duyet'].includes(don?.trang_thai) && <Button onClick={() => hoi('Mở lại đơn để sửa?', 'don_ban:moLai', 'Mở lại', false)}>Mở lại để sửa</Button>}
        {don && ['nhap', 'cho_duyet', 'cho_xuat'].includes(don.trang_thai) && <Button danger onClick={() => hoi(`Hủy đơn ${don.so}?`, 'don_ban:huy', 'Hủy đơn')}>Hủy đơn</Button>}
      </Space>
      {don && ['cho_xuat', 'dang_giao', 'da_giao', 'da_dong'].includes(don.trang_thai) && <GiaoHangDon don={don} dong={dong} tai={() => tai(don.id)} />}
    </Space>
  );
}

export function BanHang() {
  const goi = useGoi();
  const [loc, setLoc] = useState('cho_xuat');
  const [q, setQ] = useState('');
  const [ds, setDs] = useState<any[]>([]);
  const [tong, setTong] = useState(0);
  const [trang, setTrang] = useState(1);
  const [mo, setMo] = useState<any>(null);
  const tai = async () => {
    const f: any = { $and: [{ loai: 'ban' }] };
    if (loc !== 'tat_ca') f.$and.push({ trang_thai: loc });
    if (q) f.$and.push({ $or: [{ so: { $includes: q } }, { 'khach.ten': { $includes: q } }, { 'khach.sdt': { $includes: q } }] });
    const r = await goi('don_ban:list', { params: { filter: f, appends: ['khach', 'don_vi_ban'], sort: ['-id'], page: trang, pageSize: 30 } });
    setDs(r.data || []);
    setTong(r.meta?.count || 0);
  };
  useEffect(() => { tai(); }, [loc, trang]);
  return (
    <Card title="Bán hàng" extra={<Button type="primary" size="large" onClick={() => setMo('moi')}>+ Lập đơn bán</Button>}>
      <Space style={{ marginBottom: 12 }} wrap>
        <Segmented value={loc} onChange={(v: any) => { setTrang(1); setLoc(v); }} options={[
          { value: 'nhap', label: 'Nháp' }, { value: 'cho_duyet', label: 'Chờ duyệt giá' }, { value: 'cho_xuat', label: 'Đã chốt' }, { value: 'dang_giao', label: 'Giao một phần' },
          { value: 'da_giao', label: 'Đã giao đủ' }, { value: 'da_dong', label: 'Đã đóng' }, { value: 'da_huy', label: 'Đã hủy' }, { value: 'tat_ca', label: 'Tất cả' }]} />
        <Input.Search placeholder="Số đơn, tên khách, SĐT" allowClear onSearch={(v) => { setQ(v); setTrang(1); setTimeout(tai); }} style={{ width: 280 }} />
      </Space>
      <Table size="middle" rowKey="id" dataSource={ds}
        pagination={{ current: trang, total: tong, pageSize: 30, onChange: setTrang, showTotal: (t) => `${t} đơn` }}
        onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })}
        columns={[
          { title: 'Số đơn', dataIndex: 'so', render: (v) => <b>{v}</b> },
          { title: 'Ngày', dataIndex: 'ngay', render: ngayVN },
          { title: 'Khách hàng', render: (_, r) => <span>{r.khach?.ten}<div style={{ fontSize: 12, color: '#888' }}>{r.sdt}</div></span> },
          { title: 'Đơn vị bán', render: (_, r) => r.don_vi_ban?.ten },
          { title: 'Cách giao', dataIndex: 'cach_giao', render: (v) => (v === 'van_chuyen' ? 'Vận chuyển' : 'Khách đến lấy') },
          { title: 'Tổng tiền', dataIndex: 'tong_tien', align: 'right', render: (v) => fmt(v) },
          { title: 'Còn nợ', dataIndex: 'con_no', align: 'right', render: (v, r) => (Number(r.phai_thu) > 0 ? fmt(v) : '') },
          { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_DON, v); return <Tag color={m}>{t}</Tag>; } },
        ]} />
      <Drawer width="92%" open={!!mo} onClose={() => { setMo(null); tai(); }} title={mo === 'moi' ? 'Lập đơn bán' : 'Đơn bán'} destroyOnClose>
        {mo && <DonBan id={mo === 'moi' ? null : mo} dong={(x: any) => setMo(x)} xong={tai} />}
      </Drawer>
    </Card>
  );
}
