"""UX-01 PR-A: Workspace mới song song và áp cấu hình người dùng (chạy thử mặc định)."""
import json


def chay(rpc, get, lst, denied, f, phien, emit):
    for ten in ('Việc bán hàng', 'Việc kho', 'Việc tiền và công nợ', 'Việc nhà máy'):
        ws = get('Workspace', ten)
        heads = [c for c in json.loads(ws['content']) if c['type'] == 'header']
        assert len(heads) == 3 and ws['shortcuts'] and ws['roles'], ten
    assert get('Workspace', 'Trung tâm Bán hàng')['name']  # Workspace cũ giữ nguyên để quay lui
    bang = [{'user': f['dung'], 'nhom': 'nha_may'}]
    thu = rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps(bang)})
    assert thu['chay_thu'] and get('User', f['dung'])['default_workspace'] != 'Việc nhà máy'
    denied(lambda: rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps(bang)}, phien(f['ktbh'])), ('PermissionError',))
    denied(lambda: rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps([{'user': f['ktbh'], 'nhom': 'ban_hang', 'kho': [f['kho']]}])}))
    that = rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps(bang), 'chay_that': 1})
    assert not that['chay_thu'] and get('User', f['dung'])['default_workspace'] == 'Việc nhà máy'
    emit('HTTP_UX01_WORKSPACE_APPLY', 'PASS', {'workspaces': 4, 'old_kept': True, 'dry_run_default': True,
                                               'sales_not_locked': True, 'admin_only': True})
