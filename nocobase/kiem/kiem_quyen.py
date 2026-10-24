#!/usr/bin/env python3
"""Kiểm phân quyền 4 nhóm bằng tài khoản thử (tạo nếu chưa có)."""
import argparse, json, sys, uuid, urllib.parse
sys.path.insert(0, __file__.rsplit('/', 2)[0] + '/schema')
from tao_bang import API

def main():
    a = argparse.ArgumentParser(); a.add_argument('--url', default='http://localhost:13000'); a.add_argument('--email'); a.add_argument('--password'); o = a.parse_args()
    ad = API(o.url, o.email, o.password)
    kq = []
    pw = 'Thu' + uuid.uuid4().hex[:10]
    for role in ['ban_hang', 'kho', 'thu_chi']:
        em = f'thu-{role}@aphvh.local'
        u = ad.call('users:list', params='?filter=' + urllib.parse.quote(json.dumps({'email': em})))['data']
        if u: ad.call('users:update', {'password': pw, 'roles': [role]}, params=f"?filterByTk={u[0]['id']}")
        else: ad.call('users:create', {'email': em, 'nickname': 'Thử ' + role, 'password': pw, 'roles': [role]})
    import time; time.sleep(2)  # NocoBase: token cấp cùng giây với lúc đổi mật khẩu bị coi là hết hạn
    def thu(role, action, body=None, params=''):
        api = API(o.url, f'thu-{role}@aphvh.local', pw)
        import urllib.request, urllib.error
        req = urllib.request.Request(f"{o.url}/api/{action}{params}", method='POST' if body is not None else 'GET',
            data=json.dumps(body).encode() if body is not None else None, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api.token}', 'X-Role': role})
        try:
            with urllib.request.urlopen(req) as r: return r.status
        except urllib.error.HTTPError as e: return e.code
    don = ad.call('don_ban:list', params='?pageSize=1&sort=-id')['data'][0]['id']
    ca = [('ban_hang', 'don_ban:list', None, '', 200), ('ban_hang', 'luot_giao:banGiaoXe', {}, '?filterByTk=1', 403),
          ('ban_hang', 'phieu_kho:ghiSo', {}, '?filterByTk=1', 403), ('ban_hang', 'phieu_thu:ghi', {}, '?filterByTk=1', 403),
          ('kho', 'phieu_kho:list', None, '', 200), ('kho', 'don_ban:chotDon', {}, f'?filterByTk={don}', 403),
          ('kho', 'phieu_thu:list', None, '', 403), ('thu_chi', 'phieu_thu:list', None, '', 200),
          ('thu_chi', 'luot_giao:khachNhan', {}, '?filterByTk=1', 403), ('thu_chi', 'gia_von:list', None, '', 403)]
    loi = 0
    for role, act, body, p, mong in ca:
        s = thu(role, act, body, p)
        dat = s == mong or (mong == 200 and s == 200)
        loi += not dat
        print(('ĐẠT ' if dat else 'LỖI ') + f'{role} {act} → {s} (mong {mong})')
    print(f'TỔNG {len(ca)} ca, LỖI {loi}'); sys.exit(1 if loi else 0)

main()
