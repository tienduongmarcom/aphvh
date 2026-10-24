/** 0.4.0 Unified Operations: đăng ký thao tác nghiệp vụ và hook của các phân hệ mới. */
import { dangKyBanHang, hookBanHang } from './sales';
import { dangKyGiaoNhan, hookGiaoNhan } from './logistics';
import { dangKyTaiChinh, hookTaiChinh } from './finance';
import { dangKyPos } from './pos';
import { dangKyNhaMay } from './manufacturing';
import { dangKyNguon, hookNguon } from './import';
import { dangKyNangCap } from './nang_cap';
import { dangKyBaoCao } from './reports';

type H = Record<string, (ctx: any, t: any) => Promise<any>>;
export function dangKy040(p: any, H: H, h: any) {
  dangKyBanHang(p, H, h);
  dangKyGiaoNhan(p, H, h);
  dangKyTaiChinh(p, H, h);
  dangKyPos(p, H, h);
  dangKyNhaMay(p, H, h);
  dangKyNguon(p, H, h);
  dangKyNangCap(p, H, h);
  dangKyBaoCao(p, H, h);
}
export function hook040(p: any) {
  hookBanHang(p);
  hookTaiChinh(p);
  hookGiaoNhan(p);
  hookNguon(p);
}
