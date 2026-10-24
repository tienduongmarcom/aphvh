/** Dùng chung cho các màn hình APH-VH: gọi API, hiển thị số, ô chọn từ danh mục. */
import { useAPIClient } from '@nocobase/client';
import { App, Select, Spin } from 'antd';
import React, { useCallback, useEffect, useRef, useState } from 'react';

export const fmt = (v: any, d = 0) =>
  Number(v || 0).toLocaleString('vi-VN', { minimumFractionDigits: 0, maximumFractionDigits: d });
export const ngayVN = (v?: string) => (v ? String(v).slice(0, 10).split('-').reverse().join('/') : '');
export const homNay = () => new Date(Date.now() + 7 * 3600 * 1000).toISOString().slice(0, 10);

export const TRANG_THAI_DON: Record<string, [string, string]> = {
  nhap: ['Nháp', 'default'], cho_duyet: ['Chờ duyệt giá', 'purple'], cho_xuat: ['Đã chốt — chờ giao', 'orange'], dang_giao: ['Giao một phần', 'blue'],
  da_giao: ['Đã giao đủ', 'green'], da_dong: ['Đã đóng (giao thiếu)', 'cyan'], da_huy: ['Đã hủy', 'red'],
};
export const TRANG_THAI_LUOT: Record<string, [string, string]> = {
  cho_xuat: ['Chờ xuất (đang giữ hàng)', 'orange'], da_ban_giao_xe: ['Đã bàn giao xe', 'blue'], khach_da_nhan: ['Khách đã nhận', 'green'], da_huy: ['Đã hủy', 'red'],
};
export const DVT: Record<string, string> = { kg: 'kg', cai: 'cái', goi: 'gói', bao: 'bao', thung: 'thùng' };
export const dvt = (mh: any) => DVT[mh?.dvt_ton || 'kg'] || 'kg';
export const TRANG_THAI_PHIEU: Record<string, [string, string]> = {
  nhap: ['Nháp', 'default'], da_ghi: ['Đã ghi', 'green'], da_huy: ['Đã hủy', 'red'],
};
export const LOAI_PHIEU_KHO: Record<string, string> = {
  nhap: 'Nhập kho', xuat: 'Xuất kho khác', chuyen: 'Chuyển kho', dau_ky: 'Tồn đầu kỳ', kiem_ke: 'Điều chỉnh kiểm kê',
  san_xuat: 'Sản xuất (một bước)', dong_goi: 'Đóng gói / đổi bao', cap_nvl: 'Cấp NVL cho mẻ', thu_hoi: 'Thu hồi thành phẩm từ mẻ',
};

/** Gọi API, báo lỗi nghiệp vụ bằng tiếng Việt. */
export function useGoi() {
  const api = useAPIClient();
  const { message } = App.useApp();
  return useCallback(
    async (url: string, opts: { params?: any; data?: any; method?: string; im?: boolean } = {}) => {
      try {
        // Bộ lọc gửi dạng JSON: tránh qs gộp nhầm các điều kiện $or thành một (lỗi tìm kiếm).
        const params = opts.params && typeof opts.params.filter === 'object' ? { ...opts.params, filter: JSON.stringify(opts.params.filter) } : opts.params;
        const r = await api.request({ url, method: opts.method || (opts.data !== undefined ? 'post' : 'get'), params, data: opts.data });
        return r.data;
      } catch (e: any) {
        const msg = e?.response?.data?.errors?.[0]?.message || e?.message || 'Lỗi không xác định';
        if (!opts.im) message.error(msg, 6);
        throw e;
      }
    },
    [api],
  );
}

/** Ô chọn từ danh mục, gõ để tìm theo mã / tên / SĐT. Hiện "nhan" (mã – tên, tên – SĐT). */
export function ChonDanhMuc(props: {
  bang: string; value?: any; onChange?: (v: any, ban_ghi?: any) => void; placeholder?: string; style?: any;
  timTheo?: string[]; nhan?: string; locThem?: any; disabled?: boolean; allowClear?: boolean;
}) {
  const goi = useGoi();
  const [ds, setDs] = useState<any[]>([]);
  const [dang, setDang] = useState(false);
  const hen = useRef<any>();
  const nhan = props.nhan || 'nhan';
  const tim = (q: string) => {
    clearTimeout(hen.current);
    hen.current = setTimeout(async () => {
      setDang(true);
      const truong = props.timTheo || ['ma', 'ten', 'nhan'];
      const filter: any = { $and: props.locThem && Object.keys(props.locThem).length ? [props.locThem] : [] };
      if (q) filter.$and.push({ $or: truong.map((t) => ({ [t]: { $includes: q } })) });
      try {
        const r = await goi(`${props.bang}:list`, { params: { filter, pageSize: 30, sort: [nhan] }, im: true });
        setDs(r.data || []);
      } finally {
        setDang(false);
      }
    }, 250);
  };
  useEffect(() => {
    tim('');
  }, [props.bang, JSON.stringify(props.locThem || {})]);
  useEffect(() => {
    if (props.value && !ds.find((x) => x.id === props.value)) {
      goi(`${props.bang}:get`, { params: { filterByTk: props.value }, im: true }).then((r) => r.data && setDs((d) => [r.data, ...d]));
    }
  }, [props.value]);
  return (
    <Select
      showSearch allowClear={props.allowClear !== false} disabled={props.disabled}
      style={{ minWidth: 220, ...(props.style || {}) }} placeholder={props.placeholder}
      value={props.value} filterOption={false} onSearch={tim}
      notFoundContent={dang ? <Spin size="small" /> : 'Không thấy — gõ mã, tên hoặc SĐT'}
      options={ds.map((x) => ({ value: x.id, label: x[nhan] || x.ten || x.ma }))}
      onChange={(v) => props.onChange?.(v, ds.find((x) => x.id === v))}
    />
  );
}

export const theTrangThai = (map: Record<string, [string, string]>, v: string) => map[v] || [v, 'default'];
