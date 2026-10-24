import { Plugin } from '@nocobase/client';
import { App } from 'antd';
import React from 'react';
import models from './models';
import { InPhieu } from './InPhieu';
import { BanHang } from './BanHang';
import { KhoVan } from './Kho';
import { ThuTien } from './ThuTien';
import { DanhMuc } from './DanhMuc';
import { BaoCao } from './BaoCao';
import { GoLive } from './GoLive';
import { TaiSan } from './TaiSan';
import { TrangBanHang } from './DonGop';
import { BanNhanh } from './BanNhanh';
import { DuLieu } from './DuLieu';

const boc = (C: any) => () => (
  <App>
    <div style={{ padding: 16 }}>
      <C />
    </div>
  </App>
);

export class PluginKhoClient extends Plugin {
  async load() {
    this.flowEngine.registerModels(models);
    // Trang in riêng (không khung menu): /in/don_ban/<id>, /in/luot_giao/<id>, /in/phieu_thu/<id>
    this.router.add('in-phieu', { path: '/in/:loai/:id', Component: () => <App><InPhieu /></App> });
    // Màn hình nghiệp vụ trong khung quản trị; menu trỏ tới bằng mục "Liên kết".
    this.router.add('admin.aph-ban-hang', { path: '/admin/aph/ban-hang', Component: boc(() => <TrangBanHang BanHang={BanHang} />) });
    this.router.add('admin.aph-ban-nhanh', { path: '/admin/aph/ban-nhanh', Component: boc(BanNhanh) });
    this.router.add('admin.aph-du-lieu', { path: '/admin/aph/du-lieu', Component: boc(DuLieu) });
    this.router.add('admin.aph-kho-van', { path: '/admin/aph/kho-van', Component: boc(KhoVan) });
    this.router.add('admin.aph-thu-chi', { path: '/admin/aph/thu-chi', Component: boc(ThuTien) });
    this.router.add('admin.aph-go-live', { path: '/admin/aph/go-live', Component: boc(GoLive) });
    this.router.add('admin.aph-tai-san', { path: '/admin/aph/tai-san', Component: boc(TaiSan) });
    this.router.add('admin.aph-bao-cao', { path: '/admin/aph/bao-cao', Component: boc(BaoCao) });
    this.router.add('admin.aph-danh-muc', { path: '/admin/aph/danh-muc', Component: boc(DanhMuc) });
  }
}

export default PluginKhoClient;
