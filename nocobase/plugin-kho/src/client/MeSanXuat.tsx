/** Mẻ sản xuất: cấp NVL → thu hồi (nhiều lần, dở dang qua ngày) → kế toán tập hợp chi phí → chốt / chốt lại giá thành (giữ phiên bản). */
import { App, Alert, Button, Checkbox, Col, DatePicker, Drawer, Form, Input, InputNumber, Modal, Row, Select, Space, Table, Tag, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { ChonDanhMuc, LOAI_PHIEU_KHO, TRANG_THAI_PHIEU, fmt, ngayVN, theTrangThai, useGoi } from './chung';
import { PhieuKho } from './Kho';

const TT: Record<string, [string, string]> = { mo: ['Đang sản xuất', 'blue'], tam_hoan_thanh: ['Tạm hoàn thành — chờ chi phí', 'cyan'], da_chot: ['Đã chốt giá thành', 'green'],
  can_chot_lai: ['Cần điều chỉnh (chi phí / sản lượng mới)', 'orange'], da_khoa: ['Đã khóa kỳ', 'default'], da_huy: ['Đã hủy', 'red'] };
const PP: Record<string, string> = { kg: 'Theo kg tương đương', he_so: 'Theo hệ số định mức', gia_tri: 'Theo giá trị tương đối (giá bán)' };
const CP: Record<string, string> = { nhan_cong: 'Nhân công trực tiếp', dien: 'Điện / nước', bao_bi: 'Bao bì ngoài phiếu', van_chuyen: 'Vận chuyển / thu mua',
  khau_hao: 'Khấu hao / chi phí tài sản (ước tính)', chung: 'Chi phí sản xuất chung', do_dang_dau_ky: 'Dở dang đầu kỳ / chuyển từ mẻ trước' };

function ChiTietMe({ id, xong }: any) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [me, setMe] = useState<any>(null);
  const [phieu, setPhieu] = useState<any[]>([]);
  const [cp, setCp] = useState<any[] | null>(null);
  const [pb, setPb] = useState<any[] | null>(null);
  const [moPhieu, setMoPhieu] = useState<any>(null);
  const [moCp, setMoCp] = useState(false);
  const [moChot, setMoChot] = useState(false);
  const [fCp] = Form.useForm();
  const [fChot] = Form.useForm();
  const [heSo, setHeSo] = useState<Record<string, number>>({});
  const [giaPp, setGiaPp] = useState<Record<string, number>>({});
  const tai = async () => {
    const m = (await goi('me_sx:get', { params: { filterByTk: id, appends: ['kho', 'kho_tp', 'me_goc'] } })).data;
    setMe(m);
    setPhieu((await goi('phieu_kho:list', { params: { filter: { me_sx_id: id }, appends: ['dong', 'dong.mat_hang'], sort: ['id'], pageSize: 500 } })).data || []);
    goi('me_sx_chi_phi:list', { params: { filter: { me_sx_id: id }, sort: ['id'], pageSize: 500 }, im: true }).then((r) => setCp(r.data || [])).catch(() => setCp(null));
    goi('me_sx_phien_ban:list', { params: { filter: { me_sx_id: id }, sort: ['-phien_ban'], pageSize: 100 }, im: true }).then((r) => setPb(r.data || [])).catch(() => setPb(null));
  };
  useEffect(() => { tai(); }, [id]);
  if (!me) return null;
  const xemGia = me.gia_tri_nvl !== undefined;
  const daGhi = phieu.filter((p) => p.trang_thai === 'da_ghi');
  const dongRa = daGhi.filter((p) => p.loai === 'thu_hoi').flatMap((p) => (p.dong || []).filter((d: any) => d.huong === 'ra').map((d: any) => ({ ...d, so: p.so })));
  const dongPp = daGhi.filter((p) => p.loai === 'thu_hoi').flatMap((p) => (p.dong || []).filter((d: any) => d.huong === 'phu_pham').map((d: any) => ({ ...d, so: p.so })));
  const ty = me.kg_nvl ? (Number(me.kg_tp || 0) / Number(me.kg_nvl)) * 100 : 0;
  return <Space direction="vertical" style={{ width: '100%' }} size="middle">
    <Space wrap><Typography.Title level={4} style={{ margin: 0 }}>{me.so}</Typography.Title><Tag color={TT[me.trang_thai]?.[1]}>{TT[me.trang_thai]?.[0]}</Tag>
      <span>{me.xuong} · {me.kho?.ten} → {me.kho_tp?.ten || me.kho?.ten}{me.me_goc ? ` · tái chế từ ${me.me_goc.so}` : ''}</span></Space>
    <Row gutter={12}>{[['Kg NVL cấp', fmt(me.kg_nvl, 3)], ['Kg thành phẩm', fmt(me.kg_tp, 3)], ['Kg phụ phẩm', fmt(me.kg_phu_pham, 3)],
      ['Hao tự nhiên', fmt(me.kg_hao_tu_nhien, 3)], ['Hao bất thường', fmt(me.kg_hao_bat_thuong, 3)], ['Tỷ lệ thành phẩm', fmt(ty, 2) + '%'],
      ['Dở dang (kg)', fmt(me.kg_do_dang, 3)]].map(([a, b]) => <Col span={3} key={a}><Typography.Text type="secondary">{a}</Typography.Text><div><b>{b}</b></div></Col>)}</Row>
    {xemGia && <Row gutter={12}>{[['NVL tiêu hao', me.gia_tri_nvl], ['Bao bì / vật tư (Cái…)', me.gia_tri_bao_bi], ['Chi phí tập hợp', me.chi_phi], ['Phụ phẩm thu hồi', me.gia_tri_phu_pham],
      ['Dở dang cuối', me.do_dang_cuoi], ['Hao bất thường (chi phí kỳ)', me.hao_bat_thuong_gt], ['Phân bổ thành phẩm', me.tong_phan_bo], ['Đã ghi vào kho', me.da_vao_kho]]
      .map(([a, b]) => <Col span={3} key={a}><Typography.Text type="secondary">{a}</Typography.Text><div><b>{fmt(b)}</b></div></Col>)}
      <Col span={24}>Giá thành bình quân: <b style={{ fontSize: 16 }}>{fmt(me.gia_thanh, 2)} đ/kg</b> {me.phien_ban ? `(phiên bản ${me.phien_ban}, ${me.chot_boi || ''})` : '(chưa chốt — thành phẩm đang mang giá TẠM)'}</Col></Row>}
    {me.trang_thai !== 'da_chot' && me.trang_thai !== 'da_huy' && <Alert type="warning" showIcon message="Giá thành mẻ đang TẠM TÍNH: lãi gộp của hàng từ mẻ này chưa phải số chốt." />}
    <Space wrap>
      {me.trang_thai === 'mo' && <Button onClick={() => goi('me_sx:baoXong', { params: { filterByTk: me.id }, data: {} }).then(() => { message.success('Đã báo tạm hoàn thành'); tai(); })}>Báo tạm hoàn thành</Button>}
      {xemGia && me.trang_thai === 'da_chot' && <Button onClick={() => goi('me_sx:khoa', { params: { filterByTk: me.id }, data: {} }).then(() => { message.success('Đã khóa kỳ giá thành'); tai(); })}>Khóa kỳ giá thành</Button>}
      {!['da_huy', 'da_khoa'].includes(me.trang_thai) && <Button type="primary" onClick={() => setMoPhieu({ loai: 'cap_nvl', kho_id: me.kho_id, me_sx_id: me.id })}>+ Cấp nguyên liệu / bao bì</Button>}
      {!['da_huy', 'da_khoa'].includes(me.trang_thai) && <Button type="primary" onClick={() => setMoPhieu({ loai: 'thu_hoi', kho_id: me.kho_id, me_sx_id: me.id })}>+ Thu hồi thành phẩm / phụ phẩm / hao hụt</Button>}
      {cp !== null && me.trang_thai !== 'da_huy' && <Button onClick={() => { fCp.resetFields(); setMoCp(true); }}>+ Chi phí (kế toán)</Button>}
      {xemGia && me.trang_thai !== 'da_huy' && <Button type="primary" danger onClick={() => { fChot.setFieldsValue({ phuong_phap: me.phuong_phap || 'kg', do_dang_cuoi: me.do_dang_cuoi || 0, kg_do_dang: me.kg_do_dang || 0 }); setHeSo({}); setGiaPp({}); setMoChot(true); }}>
        {me.phien_ban ? 'Chốt lại giá thành' : 'Chốt giá thành'}</Button>}
    </Space>
    <Table size="small" rowKey="id" pagination={false} title={() => <b>Phiếu của mẻ</b>} dataSource={phieu} onRow={(r) => ({ onClick: () => setMoPhieu(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Phiếu', dataIndex: 'so' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Loại', dataIndex: 'loai', render: (v) => LOAI_PHIEU_KHO[v] },
      { title: 'Hàng', render: (_, p) => (p.dong || []).map((d: any) => `${d.mat_hang?.ma} ${fmt(d.so_kg, 3)}${d.huong === 'hao_hut' ? ' (hao)' : ''}`).join('; ') },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => { const [t, m] = theTrangThai(TRANG_THAI_PHIEU, v); return <Tag color={m}>{t}</Tag>; } },
    ]} />
    {cp !== null && <Table size="small" rowKey="id" pagination={false} title={() => <b>Chi phí tập hợp (kế toán)</b>} dataSource={cp} columns={[
      { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Khoản', dataIndex: 'loai', render: (v) => CP[v] }, { title: 'Kỳ', dataIndex: 'ky' },
      { title: 'Số tiền', dataIndex: 'so_tien', align: 'right', render: (v) => fmt(v) }, { title: 'Số chứng từ', dataIndex: 'so_chung_tu' }, { title: 'Căn cứ', dataIndex: 'ghi_chu' },
    ]} />}
    {pb !== null && pb.length > 0 && <Table size="small" rowKey="id" pagination={false} title={() => <b>Phiên bản giá thành (không ghi đè lịch sử)</b>} dataSource={pb} columns={[
      { title: 'Phiên bản', dataIndex: 'phien_ban' }, { title: 'Ngày', dataIndex: 'ngay', render: ngayVN }, { title: 'Chi phí', dataIndex: 'tong_chi_phi', align: 'right', render: (v) => fmt(v) },
      { title: 'Phụ phẩm', dataIndex: 'phu_pham', align: 'right', render: (v) => fmt(v) }, { title: 'Dở dang cuối', dataIndex: 'do_dang_cuoi', align: 'right', render: (v) => fmt(v) },
      { title: 'Hao bất thường', dataIndex: 'hao_bat_thuong', align: 'right', render: (v) => fmt(v) }, { title: 'Phân bổ', dataIndex: 'tong_phan_bo', align: 'right', render: (v) => <b>{fmt(v)}</b> },
      { title: 'Điều chỉnh kho', dataIndex: 'dieu_chinh', align: 'right', render: (v) => fmt(v) }, { title: 'Người', dataIndex: 'nguoi' },
      { title: 'Chi tiết', render: (_, r) => { const c = JSON.parse(r.chi_tiet || '{}'); return `${PP[c.phuong_phap] || ''}: ` + (c.dong || []).map((d: any) => `${d.ma} ${fmt(d.gia_thanh, 2)}đ/kg`).join('; '); } },
    ]} />}
    <Drawer width="85%" open={!!moPhieu} onClose={() => { setMoPhieu(null); tai(); xong?.(); }} title="Phiếu của mẻ" destroyOnClose>
      {moPhieu && <PhieuKho id={typeof moPhieu === 'object' ? null : moPhieu} macDinh={typeof moPhieu === 'object' ? moPhieu : undefined} xong={tai} />}
    </Drawer>
    <Modal open={moCp} title="Thêm chi phí cho mẻ" okText="Lưu" cancelText="Thôi" onCancel={() => setMoCp(false)} onOk={async () => {
      const v = await fCp.validateFields();
      await goi('me_sx_chi_phi:create', { data: { ...v, me_sx_id: me.id, ngay: v.ngay?.format('YYYY-MM-DD') } });
      message.success('Đã thêm — mẻ đã chốt sẽ chuyển "Cần chốt lại"'); setMoCp(false); tai();
    }}>
      <Form form={fCp} layout="vertical">
        <Form.Item name="loai" label="Khoản chi phí" rules={[{ required: true }]}><Select options={Object.entries(CP).map(([value, label]) => ({ value, label }))} /></Form.Item>
        <Form.Item name="so_tien" label="Số tiền" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))} /></Form.Item>
        <Form.Item name="so_chung_tu" label="Số chứng từ (hóa đơn / bảng lương / bảng phân bổ) — chống ghi hai lần"><Input /></Form.Item>
        <Form.Item name="phieu_chi_id" label="Gắn phiếu chi (nếu có) — không phân bổ quá số tiền phiếu"><ChonDanhMuc bang="phieu_chi" nhan="so" timTheo={['so', 'ly_do', 'nguoi_nhan']} locThem={{ trang_thai: 'da_ghi' }} style={{ width: '100%' }} /></Form.Item>
        <Form.Item name="ky" label="Kỳ (vd 2026-10)"><Input /></Form.Item>
        <Form.Item name="ngay" label="Ngày"><DatePicker format="DD/MM/YYYY" /></Form.Item>
        <Form.Item name="ghi_chu" label="Căn cứ (bảng lương, hóa đơn điện, bảng phân bổ…)"><Input.TextArea /></Form.Item>
      </Form>
    </Modal>
    <Modal open={moChot} width={820} title={`Chốt giá thành ${me.so}`} okText="Chốt" cancelText="Thôi" onCancel={() => setMoChot(false)} onOk={async () => {
      const v = await fChot.validateFields();
      const r = await goi('me_sx:chot', { params: { filterByTk: me.id }, data: { ...v, he_so: heSo, gia_phu_pham: giaPp } });
      message.success(`Đã chốt phiên bản ${r.data.phien_ban}: ${fmt(r.data.gia_thanh, 2)} đ/kg. Chênh ${fmt(r.data.dieu_chinh)} đ: vào tồn ${fmt(r.data.vao_ton)}, vào giá vốn hàng đã xuất ${fmt(r.data.vao_gia_von)}`, 10);
      setMoChot(false); tai(); xong?.();
    }}>
      <Typography.Paragraph type="secondary">Tổng phân bổ = NVL + bao bì + chi phí − phụ phẩm − dở dang cuối − phần hao hụt bất thường (đưa vào chi phí kỳ). Giá trị thành phẩm trong kho được điều chỉnh đúng phần chênh so với giá tạm / phiên bản trước; hàng đã bán hết thì chênh lệch nằm ở sổ giá trị (giá vốn kỳ).</Typography.Paragraph>
      <Form form={fChot} layout="vertical"><Row gutter={12}>
        <Col span={8}><Form.Item name="phuong_phap" label="Phân bổ cho thành phẩm"><Select options={Object.entries(PP).map(([value, label]) => ({ value, label }))} /></Form.Item></Col>
        <Col span={8}><Form.Item name="do_dang_cuoi" label="Dở dang cuối (giá trị còn trên chuyền)"><InputNumber min={0} style={{ width: '100%' }} formatter={(v) => fmt(v)} parser={(v: any) => Number(String(v).replace(/\D/g, ''))} /></Form.Item></Col>
        <Col span={8}><Form.Item name="kg_do_dang" label="Dở dang cuối (kg)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
        {me.trang_thai === 'da_khoa' || (me.trang_thai === 'can_chot_lai' && me.phien_ban) ? <Col span={24}><Form.Item name="dieu_chinh_ky_sau" valuePropName="checked" initialValue={me.trang_thai !== 'can_chot_lai'}>
          <Checkbox>Điều chỉnh kỳ sau (mẻ đã khóa kỳ: giữ phiên bản cũ, ghi phiên bản điều chỉnh)</Checkbox></Form.Item></Col> : null}
      </Row></Form>
      {dongRa.length > 0 && <Table size="small" rowKey="id" pagination={false} title={() => 'Hệ số định mức (khi phân bổ theo hệ số)'} dataSource={dongRa} columns={[
        { title: 'Phiếu', dataIndex: 'so' }, { title: 'Thành phẩm', render: (_, d) => d.mat_hang?.ma }, { title: 'Kg', dataIndex: 'so_kg', render: (v) => fmt(v, 3) },
        { title: 'Hệ số', render: (_, d) => <InputNumber min={0.001} value={heSo[d.id] ?? d.he_so ?? 1} onChange={(v) => setHeSo({ ...heSo, [d.id]: Number(v) })} /> }]} />}
      {dongPp.length > 0 && <Table size="small" rowKey="id" pagination={false} title={() => 'Giá phụ phẩm (sửa nếu đã có giá chốt)'} dataSource={dongPp} columns={[
        { title: 'Phiếu', dataIndex: 'so' }, { title: 'Phụ phẩm', render: (_, d) => d.mat_hang?.ma }, { title: 'Kg', dataIndex: 'so_kg', render: (v) => fmt(v, 3) },
        { title: 'Giá hiện tại', dataIndex: 'don_gia', render: (v) => fmt(v, 2) },
        { title: 'Giá mới', render: (_, d) => <InputNumber min={0} value={giaPp[d.id]} onChange={(v) => setGiaPp({ ...giaPp, [d.id]: Number(v) })} /> }]} />}
    </Modal>
  </Space>;
}

export function MeSanXuat() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [mo, setMo] = useState<any>(null);
  const [moi, setMoi] = useState(false);
  const [form] = Form.useForm();
  const tai = async () => setDs((await goi('me_sx:list', { params: { appends: ['kho'], sort: ['-id'], pageSize: 300 } })).data || []);
  useEffect(() => { tai(); }, []);
  return <>
    <Space style={{ marginBottom: 12 }}><Button type="primary" onClick={() => { form.resetFields(); form.setFieldsValue({ phuong_phap: 'kg' }); setMoi(true); }}>+ Mở mẻ sản xuất</Button>
      <Typography.Text type="secondary">Mẻ nhiều ngày / nhiều lần thu hồi / chi phí đến sau. Mẻ một bước đủ số liệu vẫn dùng phiếu "Sản xuất (một bước)".</Typography.Text></Space>
    <Table size="small" rowKey="id" dataSource={ds} onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Mẻ', dataIndex: 'so', render: (v) => <b>{v}</b> }, { title: 'Ngày mở', dataIndex: 'ngay_mo', render: ngayVN }, { title: 'Xưởng', dataIndex: 'xuong' },
      { title: 'Kho', render: (_, r) => r.kho?.ten }, { title: 'Sản phẩm dự kiến', dataIndex: 'san_pham_du_kien' },
      { title: 'Kg NVL', dataIndex: 'kg_nvl', align: 'right', render: (v) => fmt(v, 3) }, { title: 'Kg thành phẩm', dataIndex: 'kg_tp', align: 'right', render: (v) => fmt(v, 3) },
      { title: 'Giá thành', dataIndex: 'gia_thanh', align: 'right', render: (v) => (v !== undefined ? fmt(v, 2) : '') },
      { title: 'Trạng thái', dataIndex: 'trang_thai', render: (v) => <Tag color={TT[v]?.[1]}>{TT[v]?.[0]}</Tag> },
    ]} />
    <Drawer width="92%" open={!!mo} onClose={() => { setMo(null); tai(); }} title="Mẻ sản xuất" destroyOnClose>{mo && <ChiTietMe id={mo} xong={tai} />}</Drawer>
    <Modal open={moi} title="Mở mẻ sản xuất" okText="Mở mẻ" cancelText="Thôi" onCancel={() => setMoi(false)} onOk={async () => {
      const v = await form.validateFields();
      const r = await goi('me_sx:create', { data: v });
      message.success('Đã mở mẻ'); setMoi(false); tai(); setMo(r.data.id);
    }}>
      <Form form={form} layout="vertical">
        <Form.Item name="kho_id" label="Kho nhà máy (cấp NVL)" rules={[{ required: true }]}><ChonDanhMuc bang="kho" style={{ width: '100%' }} /></Form.Item>
        <Form.Item name="kho_tp_id" label="Kho nhận thành phẩm (trống = kho nhà máy)"><ChonDanhMuc bang="kho" style={{ width: '100%' }} /></Form.Item>
        <Form.Item name="xuong" label="Xưởng / tổ"><Input /></Form.Item>
        <Form.Item name="san_pham_du_kien" label="Sản phẩm dự kiến"><Input /></Form.Item>
        <Form.Item name="me_goc_id" label="Tái chế / sản xuất lại từ mẻ"><ChonDanhMuc bang="me_sx" nhan="so" timTheo={['so']} style={{ width: '100%' }} /></Form.Item>
        <Form.Item name="phuong_phap" label="Phân bổ giá thành"><Select options={Object.entries(PP).map(([value, label]) => ({ value, label }))} /></Form.Item>
      </Form>
    </Modal>
  </>;
}
