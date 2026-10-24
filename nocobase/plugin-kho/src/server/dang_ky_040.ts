import { loi } from './tienich';
/** 0.4.0 Unified Operations: đăng ký thao tác nghiệp vụ và hook của các phân hệ mới. */
import { dangKyBanHang, hookBanHang } from './sales';
import { dangKyGiaoNhan, hookGiaoNhan } from './logistics';
import { dangKyTaiChinh, hookTaiChinh } from './finance';
import { dangKyPos } from './pos';
import { dangKyNhaMay } from './manufacturing';
import { dangKyNguon, hookNguon } from './import';
import { dangKyNangCap } from './nang_cap';
import { dangKyBaoCao } from './reports';
import { dangKyNhaMay041, hookNhaMay041 } from './factory';

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
  dangKyNhaMay041(p, H, h);
  chanKhoHangGui(p, H, h);
}
export function hook040(p: any) {
  hookBanHang(p);
  hookTaiChinh(p);
  hookGiaoNhan(p);
  hookNguon(p);
  hookNhaMay041(p);
}

/** 0.4.1: kho hàng gửi gia công chỉ nhận / xuất qua hồ sơ gia công và mẻ gia công — không nhập thường, không chuyển, không bán nhanh. */
function chanKhoHangGui(p: any, H: H, h: any) {
  const laHangGui = async (t: any, k: any) => !!k && (await p.bang('kho').findByPk(k, { transaction: t }))?.loai_kho === 'hang_gui';
  const ghiPk = H['phieu_kho:ghiSo'];
  H['phieu_kho:ghiSo'] = async (ctx, t) => {
    const pk = await p.bang('phieu_kho').findByPk(h.id(ctx), { transaction: t });
    if (pk && pk.trang_thai === 'nhap'
      && ((await laHangGui(t, pk.kho_id)) || (await laHangGui(t, pk.kho_dich_id)))) {
      const me = pk.me_sx_id ? await p.bang('me_sx').findByPk(pk.me_sx_id, { transaction: t }) : null;
      const meGiaCong = !!me?.ho_so_gia_cong_id && me.kho_id === pk.kho_id
        && (!pk.kho_dich_id || pk.kho_dich_id === me.kho_id)
        && ['cap_nvl', 'thu_hoi'].includes(pk.loai);
      const traGiaCong = pk.loai === 'xuat' && !!pk.ho_so_gia_cong_id
        && ctx.state?.aphGiaCongPosting === pk.id;
      if (!meGiaCong && !traGiaCong)
        loi('Kho hàng gửi chỉ ghi qua mẻ/hồ sơ gia công. Không nhập, xuất, kiểm kê hoặc chuyển kho thủ công.');
    }
    return ghiPk(ctx, t);
  };
  const xuatCh = H['chuyen_hang:xacNhanXuat'];
  H['chuyen_hang:xacNhanXuat'] = async (ctx, t) => {
    const ch = await p.bang('chuyen_hang').findByPk(h.id(ctx), { transaction: t });
    if (ch && ((await laHangGui(t, ch.kho_di_id)) || (await laHangGui(t, ch.kho_den_id))))
      loi('Không chuyển hàng vào / ra kho hàng gửi: dùng hồ sơ gia công (nhận / trả hàng).');
    return xuatCh(ctx, t);
  };
  const moCa = H['ca_pos:mo'];
  H['ca_pos:mo'] = async (ctx, t) => {
    if (await laHangGui(t, h.val(ctx).kho_id)) loi('Không bán từ kho hàng gửi gia công.');
    return moCa(ctx, t);
  };
}
