/**
 * 0.4.1 Factory MES Lite — màn hình nhà máy: chọn mẫu → mở mẻ → nhập lượng thực tế theo 3 khu vực (A. nguyên liệu · B. thành phẩm / phụ phẩm / hao hụt đã đo ·
 * C. bao bì & vật tư) → xem cân đối khối lượng ngay → giải trình chênh lệch. Không hiển thị giá với nhà máy (máy chủ cũng cắt).
 */
import { Alert, App, Badge, Button, Card, Col, Descriptions, Divider, Drawer, Input, InputNumber, Modal, Row, Segmented, Select, Space, Statistic, Table, Tabs, Tag, Typography } from 'antd';
import React, { useEffect, useMemo, useState } from 'react';
import { ChonDanhMuc, dvt, fmt, homNay, ngayVN, useGoi } from './chung';
import { RaSoatSX } from './ChuyenHang';

const rid = () => (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`);
const LOAI_CN: Record<string, string> = { GRADING: 'Xưởng đỗ (phân loại)', BLENDING_COOKING: 'Phồng tôm (phối trộn / sấy)', REPACKING: 'Đóng gói lại', LIQUID_FILLING: 'Chiết rót dầu' };
const TT_VH: Record<string, [string, string]> = { dang_sx: ['Đang sản xuất', 'blue'], cho_can_doi: ['Chờ cân đối', 'orange'], hoan_thanh: ['Hoàn thành thực tế', 'green'],
  cho_xac_nhan: ['Chờ xác nhận hồ sơ', 'purple'], nhap: ['Nháp', 'default'] };
const KQ: Record<string, [string, string]> = { can: ['Cân đối', 'success'], co_chenh: ['Còn chênh chưa giải trình', 'warning'], chua_du: ['Chưa đủ căn cứ cân đối', 'error'],
  vuot_nguong: ['Hao hụt vượt ngưỡng — chờ kế toán', 'warning'] };
const VAI_TRO: Record<string, string> = { nvl: 'Nguyên liệu', tp: 'Thành phẩm', phu_pham: 'Phụ phẩm', bao_bi: 'Bao bì', vat_tu: 'Vật tư', nhien_lieu: 'Nhiên liệu', nuoc: 'Nước / phụ gia lỏng' };

const So = (p: any) => <Statistic {...p} precision={3} groupSeparator="." decimalSeparator="," />;
function CanDoi({ c }: { c: any }) {
  if (!c) return null;
  const [t, m] = KQ[c.ket_qua] || [c.ket_qua, 'info'];
  return <Card size="small" title="Cân đối khối lượng (lũy kế cả mẻ)">
    <Alert type={m as any} showIcon message={t} description={(c.van_de || []).join(' · ') || null} style={{ marginBottom: 8 }} />
    <Row gutter={8}>
      <Col span={8}><So title="Vào (kg)" value={c.kg_vao} /></Col>
      <Col span={8}><So title="Thành phẩm" value={c.kg_tp} /></Col>
      <Col span={8}><So title="Phụ phẩm" value={c.kg_pp} /></Col>
      <Col span={8}><So title="Hao hụt đã xác nhận" value={c.kg_hao} /></Col>
      <Col span={8}><So title="Dở dang cuối" value={c.wip_cuoi} /></Col>
      <Col span={8}><So title="Chênh ban đầu" value={c.chenh} valueStyle={{ color: c.chenh ? '#d46b08' : undefined }} /></Col>
      {(c.nuoc_vao > 0 || c.nuoc_bay_hoi !== null) && <><Col span={8}><So title="Nước thêm" value={c.nuoc_vao} /></Col>
        <Col span={8}><So title="Nước bay hơi" value={c.nuoc_bay_hoi ?? 0} /></Col></>}
      <Col span={8}><So title="Đã giải trình" value={c.da_giai_trinh} /></Col>
      <Col span={8}><So title="Còn chưa giải trình" value={c.con_lai} valueStyle={{ color: c.con_lai ? '#cf1322' : '#389e0d' }} /></Col>
      <Col span={8}><Statistic title="Tỷ lệ thu hồi" value={c.ty_le_thu_hoi ?? '—'} suffix="%" /></Col>
    </Row>
    <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>Chênh lệch KHÔNG tự thành hao hụt. Bao bì, vật tư, nhiên liệu không vào cân bằng khối lượng.</Typography.Paragraph>
  </Card>;
}

function NhapMe({ meId, xong }: { meId: any; xong: () => void }) {
  const goi = useGoi();
  const { message } = App.useApp();
  const [me, setMe] = useState<any>(null);
  const [goiY, setGoiY] = useState<any[]>([]);
  const [nvlKg, setNvlKg] = useState<any>(null);
  const [tpSl, setTpSl] = useState<any>(null);
  const [sl, setSl] = useState<Record<string, any>>({});
  const [them, setThem] = useState<any[]>([]);
  const [hao, setHao] = useState<any>(null);
  const [nuoc, setNuoc] = useState<any>({});
  const [wip, setWip] = useState<any>(null);
  const [c, setC] = useState<any>(null);
  const [req, setReq] = useState(rid());
  const tai = async () => {
    const r = await goi('me_sx:get', { params: { filterByTk: meId } });
    setMe(r.data);
    setC((await goi('me_sx:canDoi', { params: { filterByTk: meId }, data: {} })).data);
  };
  const tinhGoiY = async () => setGoiY((await goi('me_sx:goiY', { params: { filterByTk: meId }, data: { nvl_kg: nvlKg, tp_sl: tpSl } })).data.goi_y || []);
  useEffect(() => { tai(); }, [meId]);
  useEffect(() => { if (me) tinhGoiY(); }, [me?.id, nvlKg, tpSl]);
  const s = useMemo(() => { try { return JSON.parse(me?.snapshot_dinh_muc || 'null'); } catch { return null; } }, [me?.snapshot_dinh_muc]);
  if (!me) return null;
  const loai = me.loai_cn || s?.mau?.loai_cn;
  const dong = [...goiY, ...them];
  const khoa = (d: any, i: number) => `${d.vai_tro}-${d.mat_hang_id}-${i}`;
  const ghi = async (ketThuc: boolean) => {
    const lay = (vt: string[]) => dong.map((d, i) => ({ d, x: sl[khoa(d, i)] || {} })).filter(({ d, x }) => vt.includes(d.vai_tro) && Number(x.so_luong) > 0);
    const data: any = { request_id: req, ket_thuc: ketThuc,
      nvl: lay(['nvl']).map(({ d, x }) => ({ mat_hang_id: d.mat_hang_id, so_luong: x.so_luong, so_lo: x.so_lo })),
      tp: lay(['tp']).map(({ d, x }) => ({ mat_hang_id: d.mat_hang_id, so_luong: x.so_luong, so_bao: x.so_bao, so_lo: x.so_lo })),
      phu_pham: lay(['phu_pham']).map(({ d, x }) => ({ mat_hang_id: d.mat_hang_id, so_luong: x.so_luong })),
      hao: Number(hao) > 0 ? [{ so_kg: hao }] : [] };
    for (const vt of ['bao_bi', 'vat_tu', 'nhien_lieu']) data[vt] = dong.map((d, i) => ({ d, x: sl[khoa(d, i)] || {} }))
      .filter(({ d, x }) => d.vai_tro === vt && (Number(x.so_luong) > 0 || Number(x.so_hong) > 0)).map(({ d, x }) => ({ mat_hang_id: d.mat_hang_id, so_luong: x.so_luong || 0, so_hong: x.so_hong, ly_do: x.ly_do }));
    if (nuoc.vao !== undefined && nuoc.vao !== null) data.nuoc_vao = nuoc.vao;
    if (nuoc.bay_hoi !== undefined && nuoc.bay_hoi !== null) data.nuoc_bay_hoi = nuoc.bay_hoi;
    if (wip !== null && wip !== undefined) data.wip_cuoi = wip;
    const r = await goi('me_sx:ghiThucTe', { params: { filterByTk: meId }, data });
    setC(r.data);
    message.success(r.data.da_ghi_truoc ? 'Đã ghi trước đó (không ghi lại)' : `Đã ghi ${(r.data.phieu || []).join(', ')}`);
    setSl({}); setHao(null); setNuoc({}); setWip(null); setReq(rid()); tai(); xong();
  };
  const giaiTrinh = () => {
    let v: any = { phan_loai: 'do_sai' };
    Modal.confirm({ title: `Giải trình chênh lệch (còn ${fmt(c?.con_lai, 3)} kg)`, content: <Space direction="vertical" style={{ width: '100%' }}>
      <InputNumber placeholder="Số kg" style={{ width: 200 }} onChange={(x) => (v.so_kg = x)} />
      <Select defaultValue="do_sai" style={{ width: 300 }} onChange={(x) => (v.phan_loai = x)} options={[{ value: 'do_sai', label: 'Cân / đo sai (đã kiểm)' },
        { value: 'hao_bat_thuong', label: 'Hao hụt bất thường (đổ vỡ, hỏng…)' }, { value: 'khac', label: 'Khác' }]} />
      <Input.TextArea placeholder="Lý do / căn cứ" onChange={(e) => (v.ly_do = e.target.value)} /></Space>,
    onOk: async () => { await goi('me_sx:giaiTrinh', { params: { filterByTk: meId }, data: v }); message.success('Đã gửi giải trình — chờ kế toán duyệt'); tai(); } });
  };
  const o = (d: any, i: number, k: string, w = 110) => <InputNumber min={0} style={{ width: w }} value={sl[khoa(d, i)]?.[k]}
    onChange={(x) => setSl({ ...sl, [khoa(d, i)]: { ...sl[khoa(d, i)], [k]: x } })} />;
  const bang = (vt: string[], cot: any[] = []) => <Table size="small" rowKey={(d: any) => khoa(d, dong.indexOf(d))} pagination={false}
    dataSource={dong.filter((d) => vt.includes(d.vai_tro))} columns={[
      { title: 'Mặt hàng', render: (_, d: any) => <span><Tag>{VAI_TRO[d.vai_tro]}</Tag>{d.ma} {d.ten}</span> },
      { title: 'Dự kiến', align: 'right' as const, render: (_, d: any) => d.du_kien !== undefined ? `${fmt(d.du_kien, 3)} ${dvt({ dvt_ton: d.dvt })}` : '' },
      { title: 'Thực tế (cân / đếm)', render: (_, d: any) => o(d, dong.indexOf(d), 'so_luong') }, ...cot]} />;
  return <>
    <Descriptions size="small" column={4} bordered items={[{ label: 'Mẻ', children: <b>{me.so}</b> }, { label: 'Mẫu', children: s ? `${s.mau.ma} v${s.phien_ban.so}` : '—' },
      { label: 'Công nghệ', children: LOAI_CN[loai] || loai }, { label: 'Vận hành', children: <Tag color={TT_VH[me.tt_van_hanh]?.[1]}>{TT_VH[me.tt_van_hanh]?.[0] || me.tt_van_hanh}</Tag> }]} />
    <Row gutter={12} style={{ marginTop: 12 }}>
      <Col span={15}>
        <Space style={{ marginBottom: 8 }} wrap>
          <InputNumber addonBefore="Gợi ý theo kg NVL" value={nvlKg} onChange={setNvlKg} style={{ width: 240 }} />
          <InputNumber addonBefore="hoặc số ĐVT thành phẩm" value={tpSl} onChange={setTpSl} style={{ width: 260 }} />
          <Button onClick={() => setSl(Object.fromEntries(dong.map((d, i) => [khoa(d, i), { ...sl[khoa(d, i)], so_luong: d.du_kien }])))}>Điền theo dự kiến</Button>
        </Space>
        <Typography.Title level={5}>A. Nguyên liệu đầu vào</Typography.Title>
        {bang(['nvl'], [{ title: 'Lô', render: (_: any, d: any) => <Input style={{ width: 110 }} onChange={(e) => setSl({ ...sl, [khoa(d, dong.indexOf(d))]: { ...sl[khoa(d, dong.indexOf(d))], so_lo: e.target.value } })} /> }])}
        <Typography.Title level={5} style={{ marginTop: 12 }}>B. Thành phẩm, phụ phẩm, hao hụt</Typography.Title>
        {bang(['tp', 'phu_pham'], [{ title: 'Bao', render: (_: any, d: any) => d.vai_tro === 'tp' && o(d, dong.indexOf(d), 'so_bao', 80) }])}
        <Space style={{ marginTop: 6 }} wrap>
          <InputNumber addonBefore="Hao hụt đã ĐO (kg)" min={0} value={hao} onChange={setHao} style={{ width: 240 }} />
          <InputNumber addonBefore="Dở dang cuối (kg)" min={0} value={wip} onChange={setWip} style={{ width: 230 }} />
          {loai === 'BLENDING_COOKING' && <><InputNumber addonBefore="Nước thêm (kg)" min={0} value={nuoc.vao} onChange={(x) => setNuoc({ ...nuoc, vao: x })} style={{ width: 210 }} />
            <InputNumber addonBefore="Nước bay hơi (kg)" min={0} value={nuoc.bay_hoi} onChange={(x) => setNuoc({ ...nuoc, bay_hoi: x })} style={{ width: 220 }} /></>}
        </Space>
        <Typography.Title level={5} style={{ marginTop: 12 }}>C. Bao bì và vật tư tiêu hao</Typography.Title>
        {bang(['bao_bi', 'vat_tu', 'nhien_lieu'], [{ title: 'Hỏng / loại', render: (_: any, d: any) => o(d, dong.indexOf(d), 'so_hong', 90) },
          { title: 'Nguyên nhân (khi khác định mức / có hỏng)', render: (_: any, d: any) => <Input onChange={(e) => setSl({ ...sl, [khoa(d, dong.indexOf(d))]: { ...sl[khoa(d, dong.indexOf(d))], ly_do: e.target.value } })} /> }])}
        <Space style={{ marginTop: 8 }} wrap>
          <Select placeholder="+ Thêm dòng ngoài mẫu" style={{ width: 200 }} value={null as any} onChange={(vt) => setThem([...them, { vai_tro: vt, mat_hang_id: null }])}
            options={Object.entries(VAI_TRO).filter(([k]) => k !== 'nuoc').map(([k, l]) => ({ value: k, label: l }))} />
          {them.filter((d) => !d.mat_hang_id).map((d, j) => <ChonDanhMuc key={j} bang="mat_hang" value={null} placeholder={`Mặt hàng (${VAI_TRO[d.vai_tro]})`}
            onChange={(v, mh) => setThem(them.map((x) => (x === d ? { ...x, mat_hang_id: v, ma: mh?.ma, ten: mh?.ten, dvt: mh?.dvt_ton } : x)))} />)}
        </Space>
        <Divider />
        <Space>
          <Button onClick={() => ghi(false)}>Ghi thực tế (chưa kết thúc)</Button>
          <Button type="primary" onClick={() => ghi(true)}>Ghi & kết thúc mẻ</Button>
          {c && Math.abs(c.con_lai) > 0 && <Button danger onClick={giaiTrinh}>Giải trình chênh lệch</Button>}
        </Space>
      </Col>
      <Col span={9}><CanDoi c={c} /></Col>
    </Row>
  </>;
}

function PhieuSX() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [mau, setMau] = useState<any[]>([]);
  const [mo, setMo] = useState<any>(null);
  const [v, setV] = useState<any>({ ngay: homNay() });
  const [loiTai, setLoiTai] = useState<string | null>(null);
  const [dangTai, setDangTai] = useState(false);
  const tai = async () => {
    setDangTai(true);
    setLoiTai(null);
    try {
      const [me, mauMoi] = await Promise.all([
        goi('me_sx:list', { params: { filter: { tt_van_hanh: { $in: ['dang_sx', 'cho_can_doi', 'hoan_thanh'] }, trang_thai: { $ne: 'da_huy' } }, appends: ['mau_sx'], sort: ['-id'], pageSize: 100 }, im: true }),
        goi('mau_sx:list', { params: { filter: { ngung: { $ne: true } }, pageSize: 200, sort: ['ma'] }, im: true }),
      ]);
      setDs(me.data || []);
      setMau(mauMoi.data || []);
    } catch (e: any) {
      // Không được đánh đồng API 403 với danh sách thật sự rỗng.
      setDs([]);
      setMau([]);
      setLoiTai(e?.response?.status === 403
        ? 'Vai trò hiện tại không được xem Phiếu sản xuất. Chọn tài khoản ở góc trên bên phải → Chuyển vai trò → Nhà máy (nha_may), sau đó bấm Tải lại.'
        : 'Không tải được danh sách mẻ/mẫu sản xuất. Kiểm tra kết nối hoặc quyền truy cập, sau đó thử lại.');
    } finally {
      setDangTai(false);
    }
  };
  useEffect(() => { void tai(); }, []);
  const moMe = async () => {
    if (!v.mau_sx_id) return message.warning('Chọn mẫu sản xuất.');
    const r = await goi('me_sx:moTuMau', { data: { ...v, request_id: rid() } });
    message.success(`Đã mở mẻ ${r.data.so} (định mức v${r.data.phien_ban})`);
    setMo(r.data.id); tai();
  };
  return <>
    {loiTai && <Alert type="error" showIcon message="Không thể tải dữ liệu sản xuất" description={loiTai}
      action={<Button size="small" onClick={() => void tai()}>Tải lại</Button>} style={{ marginBottom: 12 }} />}
    <Card size="small" title="Mở mẻ từ mẫu" style={{ marginBottom: 12 }}>
      <Space wrap>
        <Select placeholder="Mẫu sản xuất" style={{ width: 280 }} value={v.mau_sx_id} onChange={(x) => setV({ ...v, mau_sx_id: x })}
          options={mau.map((m) => ({ value: m.id, label: `${m.ma} — ${m.ten || ''} (${LOAI_CN[m.loai_cn] || m.loai_cn})` }))} />
        <Input type="date" value={v.ngay} onChange={(e) => setV({ ...v, ngay: e.target.value })} style={{ width: 150 }} />
        <ChonDanhMuc bang="ca_sx" nhan="so" value={v.ca_sx_id} onChange={(x) => setV({ ...v, ca_sx_id: x })} placeholder="Ca (tùy chọn)" timTheo={['so', 'xuong']} style={{ width: 160 }} />
        <ChonDanhMuc bang="kho" value={v.kho_id} onChange={(x) => setV({ ...v, kho_id: x })} placeholder="Kho lấy NVL" locThem={{ loai_kho: 'nha_may' }} />
        <ChonDanhMuc bang="kho" value={v.kho_tp_id} onChange={(x) => setV({ ...v, kho_tp_id: x })} placeholder="Kho nhận thành phẩm" locThem={{ loai_kho: 'nha_may' }} />
        <ChonDanhMuc bang="sx_ho_so_gia_cong" nhan="so" value={v.ho_so_gia_cong_id} onChange={(x) => setV({ ...v, ho_so_gia_cong_id: x })} placeholder="Hồ sơ gia công (nếu có)" timTheo={['so']} style={{ width: 200 }} />
        <Button type="primary" onClick={moMe}>Mở mẻ</Button>
      </Space>
    </Card>
    <Table size="small" rowKey="id" dataSource={ds} loading={dangTai}
      locale={{ emptyText: loiTai ? 'Không tải được dữ liệu — xem thông báo bên trên' : 'Chưa có mẻ sản xuất' }}
      onRow={(r) => ({ onClick: () => setMo(r.id), style: { cursor: 'pointer' } })} columns={[
      { title: 'Mẻ', dataIndex: 'so', render: (x) => <b>{x}</b> }, { title: 'Ngày', dataIndex: 'ngay_mo', render: ngayVN }, { title: 'Mẫu', render: (_, r) => r.mau_sx?.ma || '—' },
      { title: 'Công nghệ', dataIndex: 'loai_cn', render: (x) => LOAI_CN[x] || x }, { title: 'Kg NVL', dataIndex: 'kg_nvl', align: 'right', render: (x) => fmt(x, 3) },
      { title: 'Kg thành phẩm', dataIndex: 'kg_tp', align: 'right', render: (x) => fmt(x, 3) },
      { title: 'Vận hành', dataIndex: 'tt_van_hanh', render: (x) => <Tag color={TT_VH[x]?.[1]}>{TT_VH[x]?.[0] || x}</Tag> },
    ]} />
    <Drawer width="96%" open={!!mo} onClose={() => { setMo(null); tai(); }} title="Phiếu sản xuất" destroyOnClose>{mo && <NhapMe meId={mo} xong={tai} />}</Drawer>
  </>;
}

function MauDinhMuc() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [chon, setChon] = useState<any>(null);
  const [pb, setPb] = useState<any[]>([]);
  const [moi, setMoi] = useState<any>(null);
  const [mauMoi, setMauMoi] = useState<any>(null);
  const tai = async () => setDs((await goi('mau_sx:list', { params: { sort: ['ma'], pageSize: 200 } })).data || []);
  const taiPb = async (m: any) => { setChon(m); setPb((await goi('mau_sx_phien_ban:list', { params: { filter: { mau_sx_id: m.id }, appends: ['dong', 'dong.mat_hang'], sort: ['-phien_ban'] } })).data || []); };
  useEffect(() => { tai(); }, []);
  const luuPb = async () => {
    await goi('mau_sx_phien_ban:create', { params: { 'updateAssociationValues[]': 'dong' }, data: { mau_sx_id: chon.id, hieu_luc_tu: moi.hieu_luc_tu || null,
      nguong_chenh_pct: moi.nguong_chenh_pct ?? null, can_cu: moi.can_cu, dong: moi.dong.filter((d: any) => d.mat_hang_id).map(({ mh, ...d }: any) => d) } });
    message.success('Đã lưu phiên bản (đề xuất) — chờ kế toán duyệt'); setMoi(null); taiPb(chon);
  };
  const d = (i: number, k: string, x: any) => setMoi({ ...moi, dong: moi.dong.map((y: any, j: number) => (j === i ? { ...y, [k]: x } : y)) });
  return <Row gutter={12}>
    <Col span={8}>
      <Button type="primary" style={{ marginBottom: 8 }} onClick={() => setMauMoi({ loai_cn: 'GRADING', pp_gia_thanh: 'kg' })}>+ Mẫu sản xuất</Button>
      <Table size="small" rowKey="id" dataSource={ds} pagination={false} onRow={(r) => ({ onClick: () => taiPb(r), style: { cursor: 'pointer', background: chon?.id === r.id ? '#e6f4ff' : undefined } })}
        columns={[{ title: 'Mã', dataIndex: 'ma' }, { title: 'Tên', dataIndex: 'ten' }, { title: 'Công nghệ', dataIndex: 'loai_cn', render: (x) => LOAI_CN[x] || x }]} />
    </Col>
    <Col span={16}>
      {chon && <>
        <Space style={{ marginBottom: 8 }}><b>{chon.ma}</b><Button onClick={() => setMoi({ dong: pb[0]?.dong?.map((x: any) => ({ vai_tro: x.vai_tro, mat_hang_id: x.mat_hang_id, co_so: x.co_so,
          dinh_muc: x.dinh_muc, nguong_hao_pct: x.nguong_hao_pct, he_so_gia: x.he_so_gia, cong_doan: x.cong_doan, mh: x.mat_hang })) || [{ vai_tro: 'nvl', co_so: 'nvl' }] })}>
          + Phiên bản mới (sao từ bản gần nhất)</Button></Space>
        {pb.map((p) => <Card key={p.id} size="small" style={{ marginBottom: 8 }} title={<Space>v{p.phien_ban}<Tag color={p.trang_thai === 'da_duyet' ? 'green' : p.trang_thai === 'de_xuat' ? 'orange' : 'default'}>
          {({ de_xuat: 'Đề xuất', da_duyet: 'Đã duyệt', ngung: 'Ngừng' } as any)[p.trang_thai]}</Tag>{p.hieu_luc_tu && `từ ${ngayVN(p.hieu_luc_tu)}`}</Space>}
          extra={p.trang_thai === 'de_xuat' && <Button size="small" type="primary" onClick={async () => { let cc = p.can_cu || ''; Modal.confirm({ title: `Duyệt v${p.phien_ban}`,
            content: <Input.TextArea defaultValue={cc} placeholder="Căn cứ định mức" onChange={(e) => (cc = e.target.value)} />,
            onOk: async () => { await goi('mau_sx_phien_ban:duyet', { params: { filterByTk: p.id }, data: { can_cu: cc } }); taiPb(chon); } }); }}>Duyệt</Button>}>
          <Table size="small" rowKey="id" pagination={false} dataSource={(p.dong || []) as any[]} columns={[
            { title: 'Vai trò', dataIndex: 'vai_tro', render: (x) => VAI_TRO[x] }, { title: 'Mặt hàng', render: (_, x) => `${x.mat_hang?.ma} ${x.mat_hang?.ten}` },
            { title: 'Định mức', render: (_, x) => `${fmt(x.dinh_muc, 6)} / ${x.co_so === 'tp' ? 'ĐVT thành phẩm' : 'kg NVL'}` },
            { title: 'Ngưỡng hao', dataIndex: 'nguong_hao_pct', render: (x) => (x !== null && x !== undefined ? `${x}%` : '') }, { title: 'Hệ số giá thành', dataIndex: 'he_so_gia' },
          ]} />
          {p.can_cu && <Typography.Text type="secondary">Căn cứ: {p.can_cu}</Typography.Text>}
        </Card>)}
      </>}
    </Col>
    <Modal width={980} open={!!moi} onCancel={() => setMoi(null)} onOk={luuPb} title="Phiên bản định mức mới (đề xuất)" destroyOnClose>
      {moi && <>
        <Space wrap style={{ marginBottom: 8 }}>
          <Input type="date" onChange={(e) => setMoi({ ...moi, hieu_luc_tu: e.target.value })} />
          <InputNumber addonBefore="Chênh cho phép %" onChange={(x) => setMoi({ ...moi, nguong_chenh_pct: x })} style={{ width: 220 }} />
          <Input placeholder="Căn cứ (thực nghiệm / biên bản)" style={{ width: 320 }} onChange={(e) => setMoi({ ...moi, can_cu: e.target.value })} />
        </Space>
        <Table size="small" rowKey={(_, i) => String(i)} pagination={false} dataSource={moi.dong} columns={[
          { title: 'Vai trò', render: (_, x: any, i) => <Select value={x.vai_tro} style={{ width: 130 }} onChange={(y) => d(i, 'vai_tro', y)} options={Object.entries(VAI_TRO).map(([k, l]) => ({ value: k, label: l }))} /> },
          { title: 'Mặt hàng', render: (_, x: any, i) => <ChonDanhMuc bang="mat_hang" value={x.mat_hang_id} style={{ width: 230 }} onChange={(y) => d(i, 'mat_hang_id', y)} /> },
          { title: 'Tính trên', render: (_, x: any, i) => <Select value={x.co_so} style={{ width: 130 }} onChange={(y) => d(i, 'co_so', y)} options={[{ value: 'nvl', label: '1 kg NVL' }, { value: 'tp', label: '1 ĐVT thành phẩm' }]} /> },
          { title: 'Định mức', render: (_, x: any, i) => <InputNumber value={x.dinh_muc} onChange={(y) => d(i, 'dinh_muc', y)} style={{ width: 100 }} /> },
          { title: 'Ngưỡng hao %', render: (_, x: any, i) => x.vai_tro === 'nvl' && <InputNumber value={x.nguong_hao_pct} onChange={(y) => d(i, 'nguong_hao_pct', y)} style={{ width: 90 }} /> },
          { title: 'Hệ số giá', render: (_, x: any, i) => x.vai_tro === 'tp' && <InputNumber value={x.he_so_gia} onChange={(y) => d(i, 'he_so_gia', y)} style={{ width: 80 }} /> },
          { width: 36, render: (_, __, i) => <Button size="small" danger onClick={() => setMoi({ ...moi, dong: moi.dong.filter((_: any, j: number) => j !== i) })}>×</Button> },
        ]} />
        <Button style={{ marginTop: 8 }} onClick={() => setMoi({ ...moi, dong: [...moi.dong, { vai_tro: 'nvl', co_so: 'nvl' }] })}>+ Dòng</Button>
        <Typography.Paragraph type="secondary" style={{ marginTop: 6 }}>Giá tham chiếu phụ phẩm do kế toán khai (Danh mục dữ liệu mẫu), nhà máy không xem giá.</Typography.Paragraph>
      </>}
    </Modal>
    <Modal open={!!mauMoi} onCancel={() => setMauMoi(null)} title="Mẫu sản xuất mới" onOk={async () => { await goi('mau_sx:create', { data: mauMoi }); setMauMoi(null); tai(); }} destroyOnClose>
      {mauMoi && <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="Mã mẫu" onChange={(e) => setMauMoi({ ...mauMoi, ma: e.target.value })} />
        <Input placeholder="Tên" onChange={(e) => setMauMoi({ ...mauMoi, ten: e.target.value })} />
        <Select value={mauMoi.loai_cn} onChange={(x) => setMauMoi({ ...mauMoi, loai_cn: x })} options={Object.entries(LOAI_CN).map(([k, l]) => ({ value: k, label: l }))} />
        <Input placeholder="Xưởng / dây chuyền" onChange={(e) => setMauMoi({ ...mauMoi, xuong: e.target.value })} />
        <Select value={mauMoi.pp_gia_thanh} onChange={(x) => setMauMoi({ ...mauMoi, pp_gia_thanh: x })} options={[{ value: 'kg', label: 'Trừ giá trị phụ phẩm, chia theo kg' },
          { value: 'he_so', label: 'Phân bổ theo hệ số' }, { value: 'gia_tri', label: 'Phân bổ theo giá trị tương đối' }]} />
      </Space>}
    </Modal>
  </Row>;
}

function GiaiTrinhCho() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const tai = async () => setDs((await goi('sx_giai_trinh:list', { params: { filter: { trang_thai: 'cho_duyet' }, appends: ['me_sx'], sort: ['id'], pageSize: 200 } })).data || []);
  useEffect(() => { tai(); }, []);
  return <Table size="small" rowKey="id" dataSource={ds} columns={[
    { title: 'Mẻ', render: (_, r) => r.me_sx?.so }, { title: 'Kg', dataIndex: 'so_kg', align: 'right', render: (x) => fmt(x, 3) },
    { title: 'Phân loại', dataIndex: 'phan_loai', render: (x) => ({ do_sai: 'Cân / đo sai', hao_bat_thuong: 'Hao hụt bất thường', khac: 'Khác' } as any)[x] },
    { title: 'Lý do', dataIndex: 'ly_do' }, { title: 'Người', dataIndex: 'nguoi' },
    { render: (_, r) => <Space><Button size="small" type="primary" onClick={async () => { await goi('sx_giai_trinh:duyet', { params: { filterByTk: r.id }, data: {} }); tai(); }}>Duyệt</Button>
      <Button size="small" danger onClick={() => { let l = ''; Modal.confirm({ title: 'Từ chối', content: <Input onChange={(e) => (l = e.target.value)} />,
        onOk: async () => { await goi('sx_giai_trinh:tuChoi', { params: { filterByTk: r.id }, data: { ly_do: l } }); tai(); } }); }}>Từ chối</Button></Space> },
  ]} />;
}

function DeXuatMa() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [v, setV] = useState<any>({});
  const tai = async () => setDs((await goi('de_xuat_mat_hang:list', { params: { sort: ['-id'], pageSize: 200, appends: ['mat_hang'] } })).data || []);
  useEffect(() => { tai(); }, []);
  return <>
    <Space wrap style={{ marginBottom: 8 }}>
      <Input placeholder="Tên hàng (như nhà máy gọi)" style={{ width: 260 }} value={v.ten} onChange={(e) => setV({ ...v, ten: e.target.value })} />
      <Input placeholder="ĐVT" style={{ width: 90 }} value={v.dvt} onChange={(e) => setV({ ...v, dvt: e.target.value })} />
      <Input placeholder="Quy cách" style={{ width: 150 }} value={v.quy_cach} onChange={(e) => setV({ ...v, quy_cach: e.target.value })} />
      <Input placeholder="Gặp ở phiếu" style={{ width: 150 }} value={v.gap_o_phieu} onChange={(e) => setV({ ...v, gap_o_phieu: e.target.value })} />
      <Button type="primary" onClick={async () => { await goi('de_xuat_mat_hang:create', { data: v }); message.success('Đã gửi đề xuất'); setV({}); tai(); }}>Đề xuất mã</Button>
    </Space>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Số', dataIndex: 'so' }, { title: 'Tên', dataIndex: 'ten' }, { title: 'ĐVT', dataIndex: 'dvt' }, { title: 'Quy cách', dataIndex: 'quy_cach' },
      { title: 'Phiếu', dataIndex: 'gap_o_phieu' }, { title: 'Người đề xuất', dataIndex: 'nguoi_de_xuat' },
      { title: 'Trạng thái', render: (_, r) => r.trang_thai === 'da_duyet' ? <Tag color="green">{r.mat_hang?.ma}</Tag> : r.trang_thai === 'tu_choi' ? <Tag color="red">Từ chối: {r.ly_do}</Tag> : <Tag color="orange">Chờ duyệt</Tag> },
      { render: (_, r) => r.trang_thai === 'cho_duyet' && <Space>
        <Button size="small" type="primary" onClick={() => { let x: any = { dvt_ton: 'kg' }; Modal.confirm({ title: `Duyệt "${r.ten}"`, content: <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="Mã chính thức (để trống nếu ghép mã có sẵn)" onChange={(e) => (x.ma = e.target.value)} />
          <ChonDanhMuc bang="mat_hang" value={undefined} placeholder="hoặc ghép vào mã có sẵn" onChange={(y) => (x.mat_hang_id = y)} />
          <Select defaultValue="kg" onChange={(y) => (x.dvt_ton = y)} options={['kg', 'cai', 'goi', 'bao', 'thung', 'lit'].map((y) => ({ value: y, label: y }))} />
          <InputNumber placeholder="Kg / bao" onChange={(y) => (x.kg_bao = y)} /></Space>,
          onOk: async () => { await goi('de_xuat_mat_hang:duyet', { params: { filterByTk: r.id }, data: x }); tai(); } }); }}>Duyệt</Button>
        <Button size="small" danger onClick={() => { let l = ''; Modal.confirm({ title: 'Từ chối', content: <Input onChange={(e) => (l = e.target.value)} />,
          onOk: async () => { await goi('de_xuat_mat_hang:tuChoi', { params: { filterByTk: r.id }, data: { ly_do: l } }); tai(); } }); }}>Từ chối</Button></Space> },
    ]} />
  </>;
}

function GiaCong() {
  const goi = useGoi();
  const { message } = App.useApp();
  const [ds, setDs] = useState<any[]>([]);
  const [moi, setMoi] = useState<any>(null);
  const [bc, setBc] = useState<any>(null);
  const tai = async () => setDs((await goi('sx_ho_so_gia_cong:list', { params: { appends: ['ben_gui', 'ben_nhan', 'kho', 'chu_so_huu'], sort: ['-id'], pageSize: 100 } })).data || []);
  useEffect(() => { tai(); }, []);
  const nhanTra = (r: any, act: string) => {
    let dong: any[] = [{}];
    let mh: any = null, sl: any = null;
    Modal.confirm({ title: act === 'nhanHang' ? `Nhận hàng gửi (${r.so})` : `Trả hàng cho bên gửi (${r.so})`, content: <Space direction="vertical">
      <ChonDanhMuc bang="mat_hang" value={undefined} onChange={(y) => (mh = y)} /><InputNumber placeholder="Số lượng (cân thực)" style={{ width: 220 }} onChange={(y) => (sl = y)} /></Space>,
    onOk: async () => { dong = [{ mat_hang_id: mh, so_kg: sl }]; await goi(`sx_ho_so_gia_cong:${act}`, { params: { filterByTk: r.id }, data: { dong, request_id: rid() } }); message.success('Xong'); tai(); } });
  };
  return <>
    <Button type="primary" style={{ marginBottom: 8 }} onClick={() => setMoi({})}>+ Hồ sơ gia công</Button>
    <Table size="small" rowKey="id" dataSource={ds} columns={[
      { title: 'Số', dataIndex: 'so' }, { title: 'Bên gửi', render: (_, r) => r.ben_gui?.ma }, { title: 'Bên nhận', render: (_, r) => r.ben_nhan?.ma }, { title: 'Kho giữ', render: (_, r) => r.kho?.ten },
      { title: 'Chủ sở hữu xác nhận', render: (_, r) => r.chu_so_huu?.ma || <Tag>Chưa xác định</Tag> }, { title: 'Căn cứ', dataIndex: 'can_cu' },
      { render: (_, r) => <Space wrap><Button size="small" onClick={() => nhanTra(r, 'nhanHang')}>Nhận hàng</Button><Button size="small" onClick={() => nhanTra(r, 'traHang')}>Trả hàng</Button>
        <Button size="small" onClick={async () => setBc((await goi('sx_ho_so_gia_cong:baoCao', { params: { filterByTk: r.id }, data: {} })).data)}>Báo cáo</Button>
        <Button size="small" onClick={() => { let x: any = {}; Modal.confirm({ title: 'Xác nhận chủ sở hữu', content: <Space direction="vertical">
          <ChonDanhMuc bang="don_vi" value={undefined} onChange={(y) => (x.chu_so_huu_id = y)} /><Input placeholder="Căn cứ" onChange={(e) => (x.can_cu = e.target.value)} /></Space>,
          onOk: async () => { await goi('sx_ho_so_gia_cong:xacNhanSoHuu', { params: { filterByTk: r.id }, data: x }); tai(); } }); }}>Xác nhận sở hữu</Button></Space> },
    ]} />
    <Modal open={!!moi} onCancel={() => setMoi(null)} title="Hồ sơ gia công" onOk={async () => { await goi('sx_ho_so_gia_cong:create', { data: moi }); setMoi(null); tai(); }} destroyOnClose>
      {moi && <Space direction="vertical" style={{ width: '100%' }}>
        <ChonDanhMuc bang="don_vi" value={moi.ben_gui_id} onChange={(y) => setMoi({ ...moi, ben_gui_id: y })} placeholder="Bên gửi" />
        <ChonDanhMuc bang="don_vi" value={moi.ben_nhan_id} onChange={(y) => setMoi({ ...moi, ben_nhan_id: y })} placeholder="Bên nhận gia công" />
        <ChonDanhMuc bang="kho" value={moi.kho_id} onChange={(y) => setMoi({ ...moi, kho_id: y })} placeholder="Kho hàng gửi (loại kho hàng gửi)" locThem={{ loai_kho: 'hang_gui' }} />
        <Input placeholder="Căn cứ (hợp đồng / biên bản)" onChange={(e) => setMoi({ ...moi, can_cu: e.target.value })} />
      </Space>}
    </Modal>
    <Modal width={800} open={!!bc} onCancel={() => setBc(null)} footer={null} title={`Hồ sơ ${bc?.ho_so} — ${bc?.so_me} mẻ`}>
      {bc && <Table size="small" rowKey="ma" pagination={false} dataSource={bc.hang} columns={['ma', 'ten', 'da_nhan', 'da_dung', 'da_ra', 'da_tra', 'dang_giu'].map((k) => ({ title: k, dataIndex: k,
        render: (x: any) => (typeof x === 'number' || /^-?\d/.test(String(x)) ? fmt(x, 3) : x) }))} />}
    </Modal>
  </>;
}

function HieuSuat() {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  useEffect(() => { goi('me_sx:hieuSuat', { data: {} }).then((r) => setDs(r.data || [])); }, []);
  return <Table size="small" rowKey="id" dataSource={ds} pagination={{ pageSize: 50 }} columns={[
    { title: 'Mẻ', dataIndex: 'so' }, { title: 'Xưởng', dataIndex: 'xuong' }, { title: 'Ngày', dataIndex: 'ngay_mo', render: ngayVN },
    { title: 'Kg NVL', dataIndex: 'kg_nvl', align: 'right', render: (x) => fmt(x, 3) }, { title: 'Kg TP', dataIndex: 'kg_tp', align: 'right', render: (x) => fmt(x, 3) },
    { title: 'Thu hồi %', dataIndex: 'ty_le_thu_hoi', align: 'right' }, { title: 'Phụ phẩm %', dataIndex: 'ty_le_phu_pham', align: 'right' },
    { title: 'Hao %', dataIndex: 'ty_le_hao', align: 'right' }, { title: 'Lệch cân bằng (kg)', dataIndex: 'lech_can_bang', align: 'right', render: (x) => fmt(x, 3) },
  ]} />;
}

export function SanXuat() {
  return <Tabs items={[
    { key: 'ph', label: 'Phiếu sản xuất', children: <PhieuSX /> },
    { key: 'mau', label: 'Mẫu & định mức', children: <MauDinhMuc /> },
    { key: 'gt', label: 'Giải trình chờ duyệt', children: <GiaiTrinhCho /> },
    { key: 'dx', label: 'Đề xuất mã hàng', children: <DeXuatMa /> },
    { key: 'gc', label: 'Hàng gửi gia công', children: <GiaCong /> },
    { key: 'hs', label: 'Hiệu suất', children: <HieuSuat /> },
    { key: 'rs', label: 'Rà soát nhập nhanh / import', children: <RaSoatSX /> },
  ]} />;
}
