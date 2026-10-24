// Quét giao diện 0.4.1 (Sản xuất): mở các tab, mở mẻ từ mẫu, điền theo dự kiến, ghi & kết thúc, xem cân đối.
//   NB_EMAIL=… NB_PASSWORD=… MAU=<mã mẫu> KHO_NL=<tên kho NVL> KHO_TP=<tên kho TP> ANH=<thư mục ảnh> node e2e-041.mjs
import { chromium } from 'playwright';
const U = process.env.NB_URL || 'http://localhost:13000';
const ANH = process.env.ANH || '.';
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1600, height: 1000 } });
const p = await ctx.newPage();
const errs = [], api5 = [], kq = [];
p.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
p.on('response', (r) => { if (r.url().includes('/api/') && r.status() >= 500) api5.push(`${r.status()} ${r.url().slice(0, 160)}`); });
await p.goto(`${U}/signin`); await p.waitForTimeout(5000);
await p.fill('input[type=text]', process.env.NB_EMAIL); await p.fill('input[type=password]', process.env.NB_PASSWORD); await p.keyboard.press('Enter');
await p.waitForTimeout(6000);
await p.goto(`${U}/admin/aph/kho-van`); await p.waitForTimeout(4500);
await p.getByRole('tab', { name: 'Sản xuất (nhà máy)' }).click(); await p.waitForTimeout(2500);
for (const t of ['Mẫu & định mức', 'Giải trình chờ duyệt', 'Đề xuất mã hàng', 'Hàng gửi gia công', 'Hiệu suất', 'Phiếu sản xuất']) {
  await p.getByRole('tab', { name: t }).click(); await p.waitForTimeout(2000);
  await p.screenshot({ path: `${ANH}/sx-${t.replace(/[^a-zA-Z]+/g, '_')}.png` });
  kq.push([t, true]);
}
const chonSel = async (o, text) => { await o.click(); await p.keyboard.type(text); await p.waitForTimeout(1800);
  await p.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click(); await p.waitForTimeout(500); };
const the = p.locator('.ant-card').filter({ hasText: 'Mở mẻ từ mẫu' });
await chonSel(the.locator('.ant-select').nth(0), process.env.MAU);
await chonSel(the.locator('.ant-select').nth(2), process.env.KHO_NL);
await chonSel(the.locator('.ant-select').nth(3), process.env.KHO_TP);
await p.getByRole('button', { name: 'Mở mẻ' }).click(); await p.waitForTimeout(4000);
const dr = p.locator('.ant-drawer-content');
await dr.locator('.ant-input-number-input').first().fill('1000'); await p.waitForTimeout(2500);
await p.getByRole('button', { name: 'Điền theo dự kiến' }).click(); await p.waitForTimeout(800);
await p.screenshot({ path: `${ANH}/sx-nhap.png` });
await p.getByRole('button', { name: 'Ghi & kết thúc mẻ' }).click(); await p.waitForTimeout(4000);
await p.screenshot({ path: `${ANH}/sx-ghi.png` });
const loiNguyenNhan = await p.getByText('ghi nguyên nhân').first().isVisible().catch(() => false);
const canDoi = await p.getByText('Cân đối khối lượng (lũy kế cả mẻ)').isVisible().catch(() => false);
kq.push(['mở mẻ + điền dự kiến + ghi (cân đối hiển thị)', canDoi || loiNguyenNhan]);
for (const x of kq) console.log(x[1] ? 'ĐẠT' : 'LỖI', x[0]);
console.log('pageerror', JSON.stringify(errs)); console.log('api5xx', JSON.stringify(api5));
await b.close();
process.exit(errs.length || api5.length || kq.some((x) => !x[1]) ? 1 : 0);
