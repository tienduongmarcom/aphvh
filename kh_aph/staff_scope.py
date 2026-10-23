"""Quyền công nợ toàn khách độc lập phạm vi kho; không nới đọc phiếu nguồn."""
FULL_CUSTOMER_DEBT_ROLE = 'Đối soát công nợ toàn khách'
STOCK_SCOPE_DOCTYPES = frozenset(('Warehouse','Stock Entry','Stock Reconciliation',
    'Sales Order','Delivery Note','Sales Invoice','Purchase Order','Purchase Receipt',
    'Purchase Invoice','APH Shared Sales Order','APH Pending Receipt','Work Order','BOM'))


def financial_summary_only(roles, restrictions):
    rows = restrictions.get('Warehouse') or []
    return (FULL_CUSTOMER_DEBT_ROLE in roles and bool(rows) and
            all(isinstance(row, dict) and row.get('applicable_for') in STOCK_SCOPE_DOCTYPES for row in rows))
