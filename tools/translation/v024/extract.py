"""0.2.4: gom chuỗi màn hình Dũng + thông báo/báo cáo kho, so với bản dịch đang chạy (po + aphvh vi.csv 0.2.3)."""
import re, json, glob, os, csv, polib
T='/tmp/claude-0/-home-claude-aphvh/d2acb522-ba05-58f5-8225-01c43da2a258/scratchpad/tr/'
E=T+'erpnext/erpnext/'
def po(p):
    d={}
    for e in polib.pofile(p):
        if e.msgstr: d[(e.msgid,e.msgctxt or '')]=e.msgstr
    return d
cur={**po(T+'frappe/frappe/locale/vi.po'),**po(T+'erpnext/erpnext/locale/vi.po')}
app={}
for r in csv.reader(open('/home/claude/aphvh/aphvh/translations/vi.csv')):
    app[(r[0].replace('\\n','\n'), r[2] if len(r)>2 else '')]=r[1].replace('\\n','\n')
def now(s,c=''):
    return app.get((s,c)) or cur.get((s,c)) or (cur.get((s,'')) if c else None)
rows={}
def add(s, where, kind, ctx=''):
    if not s or not isinstance(s,str): return
    s=s.strip()
    if not s or len(s)>300 or not re.search('[A-Za-z]{2,}',s): return
    k=(s,ctx)
    r=rows.setdefault(k,{'src':s,'ctx':ctx,'where':set(),'kind':set()})
    r['where'].add(where); r['kind'].add(kind)
# 1. chuỗi _()/__() trong mã
PAT=re.compile(r'''(?<![A-Za-z0-9_])__?\(\s*(?P<q>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')''', re.S)
CODE=[
 'stock/report/stock_balance/*','stock/report/stock_ledger/*','stock/report/stock_and_account_value_comparison/*',
 'stock/report/stock_projected_qty/*','stock/report/batch_wise_balance_history/*','stock/report/stock_ageing/*',
 'stock/report/warehouse_wise_stock_balance/*','stock/report/received_items_to_be_billed/*',
 'stock/doctype/stock_entry/*.py','stock/doctype/stock_entry/*.js','stock/doctype/purchase_receipt/*.py','stock/doctype/purchase_receipt/*.js',
 'stock/doctype/stock_reconciliation/*.py','stock/doctype/stock_reconciliation/*.js','stock/doctype/landed_cost_voucher/*.py','stock/doctype/landed_cost_voucher/*.js',
 'stock/doctype/item/item.py','stock/doctype/item/item.js','stock/doctype/batch/batch.py','stock/doctype/batch/batch.js',
 'stock/doctype/serial_and_batch_bundle/serial_and_batch_bundle.py','stock/doctype/serial_and_batch_bundle/serial_and_batch_bundle.js',
 'stock/stock_ledger.py','stock/utils.py','stock/serial_batch_bundle.py','stock/get_item_details.py',
 'buying/doctype/purchase_order/purchase_order.js','buying/doctype/purchase_order/purchase_order.py','buying/doctype/supplier/supplier.js','buying/doctype/supplier/supplier.py',
 'controllers/stock_controller.py','controllers/buying_controller.py','controllers/status_updater.py',
 'public/js/controllers/buying.js','public/js/controllers/transaction.js','public/js/utils/serial_no_batch_selector.js','public/js/utils.js',
 'public/js/utils/sales_common.js',
]
for g in CODE:
    for f in glob.glob(E+g):
        if f.endswith(('.json','.pyc')) or 'test_' in f: continue
        txt=open(f,encoding='utf-8').read()
        rel=f[len(E):]
        for m in PAT.finditer(txt):
            q=m.group('q')
            try: s=eval(q) if q[0]=='"' else eval(q)
            except Exception: continue
            add(s, rel, 'thông báo/nhãn mã')
# 2. doctype JSON: Dũng screens (+ mô tả của các doctype chính của Dung + Dũng)
idx=json.load(open(T+'dt_index.json'))
DT=['Purchase Receipt','Purchase Receipt Item','Stock Entry','Stock Entry Detail','Serial and Batch Bundle','Serial and Batch Entry','Batch',
    'Item','Item Default','Item Reorder','Item Barcode','UOM Conversion Detail','Supplier','Purchase Order','Purchase Order Item','Stock Reconciliation','Stock Reconciliation Item',
    'Landed Cost Voucher','Landed Cost Item','Landed Cost Purchase Receipt','Landed Cost Taxes and Charges','Company','Warehouse','Item Group','Stock Entry Type']
for dt in DT:
    if dt not in idx: print('missing',dt); continue
    d=json.load(open(T+idx[dt] if not idx[dt].startswith('/') else idx[dt]))
    add(dt, 'doctype:'+dt,'tên chứng từ')
    for fd in d.get('fields',[]):
        if fd.get('hidden'): continue
        add(fd.get('label'),'doctype:'+dt,'nhãn trường')
        add(fd.get('description'),'doctype:'+dt,'mô tả trường')
        if fd.get('fieldtype')=='Select' and fd.get('options'):
            for o in fd['options'].split('\n'): add(o,'doctype:'+dt,'lựa chọn')
# 3. mục riêng
add('No.','grid','cột STT',"Title of the 'row number' column")
add('Lead','workspace','nhãn'); add('Subcontracting','workspace','nhãn')
out=[]
for (s,c),r in rows.items():
    t=now(s,c)
    out.append({'src':s,'ctx':c,'now':t or '','where':sorted(r['where']),'kind':sorted(r['kind'])})
json.dump(out,open('all.json','w'),ensure_ascii=False,indent=0)
miss=[o for o in out if not o['now']]
same=[o for o in out if o['now'] and o['now'].strip()==o['src']]
print('tổng',len(out),'chưa dịch',len(miss),'giữ tiếng Anh',len(same))
from collections import Counter
print(Counter(k for o in miss for k in o['kind']))
