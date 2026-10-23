import { chromium } from 'playwright';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const ctx = await b.newContext({ viewport: { width: 1400, height: 950 } });
const p = await ctx.newPage();
const errs = [];
p.on('pageerror', e => errs.push(String(e).slice(0, 300)));
await p.goto('http://localhost:13000/signin'); await p.waitForTimeout(6000);
await p.fill('input[type=text]', 'admin@nocobase.com'); await p.fill('input[type=password]', 'admin123'); await p.keyboard.press('Enter');
await p.waitForTimeout(6000);
await p.goto('http://localhost:13000/admin/aph/ban-hang'); await p.waitForTimeout(5000);
await p.getByRole('button', { name: '+ Lập đơn bán' }).click(); await p.waitForTimeout(1500);
const chon = async (label, text) => {
  const item = p.locator('.ant-form-item').filter({ hasText: label }).first();
  await item.locator('.ant-select').click();
  await p.keyboard.type(text); await p.waitForTimeout(1500);
  await p.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click(); await p.waitForTimeout(500);
};
await chon('Khách hàng', 'Khách thử');
await chon('Đơn vị bán', 'Đơn vị thử A');
await p.screenshot({ path: 'e2e-1.png' });
// dòng hàng
const row = p.locator('.ant-drawer .ant-table-tbody tr.ant-table-row').first();
await row.locator('.ant-select').nth(0).click(); await p.keyboard.type('DX'); await p.waitForTimeout(1500);
await p.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click(); await p.waitForTimeout(500);
await row.locator('.ant-select').nth(1).click(); await p.keyboard.type('Kho thử 1'); await p.waitForTimeout(1500);
await p.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click(); await p.waitForTimeout(500);
await row.locator('.ant-input-number-input').nth(1).fill('2'); await p.waitForTimeout(1000);
await p.screenshot({ path: 'e2e-2.png' });
const [popup] = await Promise.all([ctx.waitForEvent('page', { timeout: 15000 }).catch(() => null), p.getByRole('button', { name: /Chốt đơn/ }).click()]);
await p.waitForTimeout(4000);
if (popup) { await popup.waitForTimeout(5000); await popup.screenshot({ path: 'e2e-in.png' }); }
await p.screenshot({ path: 'e2e-3.png' });
await p.getByRole('button', { name: 'Xác nhận đã giao' }).click(); await p.waitForTimeout(1000);
await p.locator('.ant-modal-confirm input').first().fill('Anh Lái Thử');
await p.getByRole('button', { name: /Đã giao — trừ kho/ }).click(); await p.waitForTimeout(3000);
await p.screenshot({ path: 'e2e-4.png' });
console.log('popup', !!popup, 'errors', JSON.stringify(errs));
await b.close();
