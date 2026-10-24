/** Hàm dùng chung phía máy chủ. */
export const kg = (v: any) => Math.round(Number(v || 0) * 1000) / 1000;
export const tien = (v: any) => Math.round(Number(v || 0));
export const homNay = () => new Date(Date.now() + 7 * 3600 * 1000).toISOString().slice(0, 10);
export const vnd = (v: any) => { const n = tien(v); return (n < 0 ? '-' : '') + String(Math.abs(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };

export class LoiNghiepVu extends Error {
  status = 400;
}
export const loi = (msg: string): never => {
  throw new LoiNghiepVu(msg);
};
