"""Quyền công nợ toàn khách độc lập phạm vi kho; không nới đọc phiếu nguồn."""
FULL_CUSTOMER_DEBT_ROLE = 'Đối soát công nợ toàn khách'
STOCK_SCOPE_DOCTYPES = frozenset(('Warehouse','Stock Entry','Stock Reconciliation',
    'Sales Order','Delivery Note','Sales Invoice','Purchase Order','Purchase Receipt',
    'Purchase Invoice','APH Shared Sales Order','APH Pending Receipt','Work Order','BOM'))


def financial_summary_only(roles, restrictions):
    rows = restrictions.get('Warehouse') or []
    return (FULL_CUSTOMER_DEBT_ROLE in roles and bool(rows) and
            all(isinstance(row, dict) and row.get('applicable_for') in STOCK_SCOPE_DOCTYPES for row in rows))


def warehouse_plan(config, rows):
    """Phân nhóm bằng địa điểm trong cấu hình và cây cha thực tế, không đoán tên lá."""
    from lab9x import cay_kho as C
    abbrs=[company['abbr'] for company in config['cong_ty']]
    errors=C.kiem_cau_hinh(config['cay_kho'],abbrs)
    if errors: raise ValueError('; '.join(errors))
    roots={}; factory_companies=set();store_companies=set()
    for location in config['cay_kho']['dia_diem']:
        category='nha_may' if location['loai']=='nha_may' else 'cua_hang'
        for abbr in (location.get('cong_ty') or [])+(location.get('gui') or []):
            roots[C.ten_kho(location['ten'],abbr)]=(abbr,category)
            (factory_companies if category=='nha_may' else store_companies).add(abbr)
    rows=list(rows);by_name={row['name']:row for row in rows}
    if len(by_name)!=len(rows):raise ValueError('Trùng mã kho trong dữ liệu đối chiếu')
    result={'nha_may':[],'cua_hang':[],'chua_phan_loai':[]}
    for row in rows:
        if row.get('is_group') or row.get('disabled'):continue
        name=row['name'];abbr=row.get('company_abbr');categories=set()
        if (abbr in abbrs and name==C.ten_kho(C.TEN_VAN_CHUYEN,abbr) and row.get('warehouse_type')=='Transit'):
            if abbr in factory_companies:categories.add('nha_may')
            if abbr in store_companies:categories.add('cua_hang')
        else:
            node=row;visited=set()
            while node and node['name'] not in visited:
                visited.add(node['name'])
                if node.get('disabled') or node.get('company_abbr')!=abbr:break
                match=roots.get(node['name'])
                if match:
                    if match[0]==abbr and node.get('is_group'):categories.add(match[1])
                    break
                node=by_name.get(node.get('parent_warehouse'))
        if not categories:result['chua_phan_loai'].append(name)
        for category in categories:result[category].append(name)
    return {key:sorted(values) for key,values in result.items()}
