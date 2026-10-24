// Quét giao diện 0.4.0: mở từng màn hình mới, bắt lỗi trang (pageerror) + lỗi API 5xx; lập + chốt một đơn gộp qua giao diện.
//   NB_EMAIL=… NB_PASSWORD=… KHACH=<mã khách> HANG=<mã hàng> KHO=<tên kho> ANH=<thư mục ảnh> node e2e-040.mjs
import { chromium } from 'playwright';
const U = process.env.NB_URL || 'http://localhost:13000';
const ANH = process.env.ANH || '.';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1500, height: 950 } });
const p = await ctx.newPage();
const errs = [], api5 = [];
p.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
p.on('response', (r) => { if (r.url().includes('/api/') && r.status() >= 500) api5.push(`${r.status()} ${r.url().slice(0, 160)}`); });
await p.goto(`${U}/signin`); await p.waitForTimeout(5000);
await p.fill('input[type=text]', process.env.NB_EMAIL); await p.fill('input[type=password]', process.env.NB_PASSWORD); await p.keyboard.press('Enter');
await p.waitForTimeout(6000);
const kq = [];
const xem = async (duong, tab, chu) => {
  await p.goto(`${U}${duong}`); await p.waitForTimeout(4500);
  if (tab) { await p.getByRole('tab', { name: tab }).first().click(); await p.waitForTimeout(2500); }
  const co = chu ? await p.getByText(chu, { exact: false }).first().isVisible().catch(() => false) : true;
  const ten = `${duong.split('/').pop()}-${(tab || 'goc').replace(/[^a-zA-Z0-9]+/g, '_').slice(0, 30)}`;
  await p.screenshot({ path: `${ANH}/${ten}.png` });
  kq.push([duong, tab || '', co]);
};
await xem('/admin/aph/ban-hang', null, 'Lập đơn gộp');
await xem('/admin/aph/ban-nhanh', null, 'Mở ca');
await xem('/admin/aph/du-lieu', null, 'Trung tâm dữ liệu');
await xem('/admin/aph/du-lieu', '2. Ánh xạ mã', 'Mã / tên ở nguồn');
await xem('/admin/aph/kho-van', 'Chuyển hàng hai đầu', 'Chuyến chuyển hàng');
await xem('/admin/aph/kho-van', 'Phiếu SX / cần rà soát', 'Nhập nhanh phiếu sản xuất');
await xem('/admin/aph/thu-chi', 'CK chờ xác minh', 'CHƯA vào tài khoản');
await xem('/admin/aph/thu-chi', 'Đối soát ngân hàng', 'Nạp sao kê');
await xem('/admin/aph/thu-chi', 'Khoản phải hoàn', null);
await xem('/admin/aph/danh-muc', 'Bảng giá', 'Bảng giá');
await xem('/admin/aph/danh-muc', 'Cấu hình vận hành', 'Giữ tồn ngay khi duyệt đơn');
await xem('/admin/aph/bao-cao', 'Tổng quan vận hành', 'Đơn gộp đang xử lý');
await xem('/admin/aph/bao-cao', 'Hàng đợi hóa đơn MISA (theo bên bán)', 'Ghi số');
// Lập đơn gộp qua giao diện
await p.goto(`${U}/admin/aph/ban-hang`); await p.waitForTimeout(4500);
await p.getByRole('button', { name: '+ Lập đơn gộp' }).click(); await p.waitForTimeout(1500);
const chonO = async (o, text) => { await o.click(); await p.keyboard.type(text); await p.waitForTimeout(1800);
  await p.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click(); await p.waitForTimeout(500); };
const dr = p.locator('.ant-drawer-content');
await chonO(dr.locator('.ant-select').first(), process.env.KHACH);
const row = dr.locator('.ant-table-tbody tr.ant-table-row').first();
await chonO(row.locator('.ant-select').nth(0), process.env.HANG);
await row.locator('.ant-select').nth(1).click(); await p.waitForTimeout(500); await p.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click();
await chonO(row.locator('.ant-select').nth(2), process.env.KHO);
await row.locator('.ant-input-number-input').first().fill('25'); await p.waitForTimeout(500);
await p.screenshot({ path: `${ANH}/dg-lap.png` });
await p.getByRole('button', { name: 'Lưu nháp' }).click(); await p.waitForTimeout(3000);
await p.getByRole('button', { name: /Chốt đơn gộp/ }).click(); await p.waitForTimeout(4000);
const daDuyet = await p.getByText('Đơn con theo bên bán').isVisible().catch(() => false);
await p.screenshot({ path: `${ANH}/dg-chot.png` });
kq.push(['lap+chot don gop qua UI', '', daDuyet]);
const [popup] = await Promise.all([ctx.waitForEvent('page', { timeout: 15000 }).catch(() => null), p.getByRole('button', { name: 'In đơn cho khách' }).click()]);
if (popup) { await popup.waitForTimeout(5000); await popup.screenshot({ path: `${ANH}/dg-in.png` }); kq.push(['in don gop', '', await popup.getByText('ĐƠN ĐẶT HÀNG').first().isVisible().catch(() => false)]); }
for (const x of kq) console.log(x[2] ? 'ĐẠT' : 'LỖI', x[0], x[1]);
console.log('pageerror', JSON.stringify(errs)); console.log('api5xx', JSON.stringify(api5));
await b.close();
process.exit(errs.length || api5.length || kq.some((x) => !x[2]) ? 1 : 0);
