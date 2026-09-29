"""Lọc chuỗi trên màn hình của Dung, so bản dịch hiện tại (ERPNext 16.36.1 / Frappe 16.35.0 chính thức,
đúng như cloud đang hiện) với ERPNext2VI 2.9 và bảng thuật ngữ, đề xuất bản chuẩn."""
import json, re, polib, openpyxl
from collections import OrderedDict

H = '/tmp/claude-0/-home-claude-aphvh/d2acb522-ba05-58f5-8225-01c43da2a258/scratchpad/tr/'
WB = '/root/.claude/uploads/d2acb522-ba05-58f5-8225-01c43da2a258/219ec697-ERPNext2VI_Cumulative_Translation_Step2.9_FULL_AUDIT_2026-09-29.xlsx'

def po(p):
    return {e.msgid: e.msgstr for e in polib.pofile(p) if not e.msgctxt and e.msgstr}
cur = {**po(H + 'frappe/frappe/locale/vi.po'), **po(H + 'erpnext/erpnext/locale/vi.po')}
don = {**po(H + 'e2v/frappe_vi_v2.po'), **po(H + 'e2v/erpnext_vi_v2.po')}
# 3 bản dịch riêng đang có trên cloud
cur.update({'Ton kho so luong APH': 'Tồn kho số lượng APH', 'Lo nhap khau': 'Lô nhập khẩu', 'Lo Nhap Khau': 'Lô nhập khẩu'})

wb = openpyxl.load_workbook(WB, read_only=True)
canon, ctx_only = {}, {}
for r in list(wb['Canonical 2.9 cumulative'].iter_rows(values_only=True))[1:]:
    if not r or not r[2]:
        continue
    if r[6] == 'THEO NGỮ CẢNH':
        ctx_only[r[2]] = (r[4], r[5])
    else:
        canon[r[2]] = (r[4], r[6], r[7])
for r in list(wb['Theo ngữ cảnh'].iter_rows(values_only=True))[1:]:
    if r and r[1]:
        ctx_only[r[1]] = (r[2], r[3])

# ---- Màn hình của Dung -------------------------------------------------------------------
idx = json.load(open(H + 'dt_index.json'))
SCREENS = OrderedDict([
    ('Mã hàng', ['Item', 'Item Group', 'UOM']),
    ('Nhà cung cấp', ['Supplier', 'Supplier Group']),
    ('Đơn mua', ['Purchase Order']),
    ('Phiếu nhập mua', ['Purchase Receipt']),
    ('Phiếu kho', ['Stock Entry', 'Stock Entry Type', 'Batch']),
    ('Kiểm kê / tồn đầu kỳ', ['Stock Reconciliation']),
    ('Phân bổ chi phí mua', ['Landed Cost Voucher']),
    ('Kho', ['Warehouse']),
    ('Công ty / khóa sổ', ['Company']),
    ('Tài sản', ['Asset', 'Asset Category', 'Asset Movement', 'Asset Capitalization', 'Asset Value Adjustment',
                 'Asset Repair', 'Location', 'Asset Depreciation Schedule']),
    ('Bút toán (CCDC, khấu hao)', ['Journal Entry']),
])
# Nhóm ưu tiên: tên chứng từ + trường người dùng gõ/đọc hằng ngày
CORE_DT = {'Item', 'Supplier', 'Purchase Order', 'Purchase Order Item', 'Purchase Receipt', 'Purchase Receipt Item',
           'Stock Entry', 'Stock Entry Detail', 'Stock Reconciliation', 'Stock Reconciliation Item',
           'Landed Cost Voucher', 'Landed Cost Item', 'Landed Cost Purchase Receipt', 'Landed Cost Taxes and Charges',
           'Asset', 'Asset Category', 'Asset Category Account', 'Asset Finance Book', 'Journal Entry', 'Journal Entry Account',
           'Warehouse', 'Item Group', 'Supplier Group', 'Stock Entry Type'}
rows = OrderedDict()

def add(src, screen, kind, dt=None, prio=2):
    if not src or not isinstance(src, str):
        return
    s = src.strip()
    if not s or len(s) > 160 or s.startswith('{') or re.fullmatch(r'[A-Z0-9.\-#]+', s) and len(s) < 4:
        return
    r = rows.setdefault(s, {'src': s, 'screens': [], 'kinds': set(), 'prio': 9})
    if screen not in r['screens']:
        r['screens'].append(screen)
    r['kinds'].add(kind)
    r['prio'] = min(r['prio'], prio)

seen = set()
def walk(dt, screen, depth=0):
    if (dt, screen) in seen or dt not in idx:
        return
    seen.add((dt, screen))
    d = json.load(open(idx[dt]))
    core = dt in CORE_DT
    add(dt, screen, 'Tên chứng từ/danh mục', dt, 1 if core else 2)
    for f in d.get('fields', []):
        if f.get('hidden'):
            continue
        ft, lab = f.get('fieldtype'), f.get('label')
        if ft in ('Tab Break', 'Section Break', 'Column Break'):
            add(lab, screen, 'Thẻ/mục', dt, 2 if core else 3)
            continue
        if ft in ('HTML', 'Button', 'Fold', 'Heading'):
            continue
        p = 3
        if core and (f.get('reqd') or f.get('in_list_view') or f.get('bold') or f.get('in_standard_filter')):
            p = 1
        elif core:
            p = 2
        add(lab, screen, 'Trường', dt, p)
        if ft == 'Select' and f.get('options'):
            for o in f['options'].split('\n'):
                add(o, screen, 'Lựa chọn', dt, 2 if core else 3)
        if ft in ('Table', 'Table MultiSelect') and depth < 2:
            walk(f['options'], screen, depth + 1)

for sc, dts in SCREENS.items():
    for dt in dts:
        walk(dt, sc)

UI = ['Save', 'Submit', 'Cancel', 'Amend', 'Delete', 'Duplicate', 'Print', 'New', 'Edit', 'Draft', 'Submitted',
      'Cancelled', 'Not Saved', 'Get Items From', 'Add Row', 'Add Multiple', 'Download', 'Upload', 'Filters', 'Refresh',
      'Actions', 'Create', 'View', 'Update Items', 'Close', 'Re-open', 'Status', 'To Receive and Bill', 'To Bill',
      'To Receive', 'Completed', 'Closed', 'Return', 'Stock Ledger', 'Stock Balance', 'Stock Projected Qty',
      'Stock and Account Value Comparison', 'General Ledger', 'Trial Balance', 'Fixed Asset Register',
      'Batch-Wise Balance History', 'Stock Ageing', 'Material Receipt', 'Material Issue', 'Material Transfer',
      'Material Transfer for Manufacture', 'Repack', 'Manufacture', 'Opening Stock', 'Generate New Report', 'Rebuild',
      'Edit Posting Date and Time', 'Set Posting Time', 'Accounts Frozen Till Date', 'Role Allowed for Frozen Entries',
      'Frozen Accounts Modifier', 'Row', 'Rows', 'Items', 'Report', 'Export', 'Import', 'Data Import', 'Settings',
      'Stock', 'Buying', 'Assets', 'Accounting', 'Home', 'Purchase Receipts', 'Get Items From Purchase Receipts',
      'Purchase Invoice', 'Debit', 'Credit', 'Party', 'Party Type', 'Stock Settings', 'Buying Settings']
for s in UI:
    add(s, 'Chung (nút, trạng thái, báo cáo, menu)', 'Giao diện', None, 1)

# ---- Thuật ngữ chuẩn (nguồn: 15 thuật ngữ kế toán chốt 28/09 + đề xuất Claude cho màn hình Dung) -------------
APPROVED = {  # kế toán đã chốt 28/09 (doc "Rà soát bản dịch ERPNext")
    'Submit': 'Xác nhận', 'Submitted': 'Đã xác nhận', 'Row': 'Dòng', 'Party': 'Đối tượng',
    'Valuation Rate': 'Đơn giá vốn', 'Net Total': 'Cộng tiền hàng', 'Grand Total': 'Tổng tiền thanh toán',
    'Naming Series': 'Ký hiệu chứng từ', 'Balance Sheet': 'Báo cáo tình hình tài chính',
    'Stock Reconciliation': 'Điều chỉnh theo kiểm kê', 'Purchase Receipt': 'Phiếu nhập mua hàng',
    'Item': 'Mặt hàng', 'Items': 'Mặt hàng', 'Add Row': 'Thêm dòng',
    # chốt 29/09 21:11 (anh Tiến)
    'Opening Stock': 'Nhập số dư đầu kỳ', 'Raw Material': 'Nguyên vật liệu', 'BOM': 'Định mức nguyên vật liệu',
}
DECIDED_2909 = {'Stock Reconciliation', 'Opening Stock', 'Raw Material', 'BOM'}
GLOSS = {  # đề xuất mới, cần Dung duyệt
    'Stock Entry': 'Phiếu kho', 'Stock Entry Type': 'Loại phiếu kho', 'Stock Entry Detail': 'Chi tiết phiếu kho',
    'Landed Cost Item': 'Dòng hàng được phân bổ',
    'Landed Cost Purchase Receipt': 'Phiếu nhập được phân bổ', 'Landed Cost Taxes and Charges': 'Chi phí nhập hàng phân bổ',
    'Landed Cost Vendor Invoice': 'Hóa đơn chi phí nhập hàng của nhà cung cấp',
    'Basic Rate (as per Stock UOM)': 'Đơn giá (theo ĐVT tồn kho)', 'Issue': 'Cấp phát', 'Receipt': 'Tiếp nhận', 'Transfer': 'Điều chuyển',
    'Filters': 'Bộ lọc', 'Import': 'Nhập dữ liệu', 'Dashboard': 'Trang tổng quan', 'Domain': 'Lĩnh vực',
    'Applicable Charges': 'Chi phí được phân bổ', 'Distribute Charges Based On': 'Phân bổ chi phí theo',
    'Receipt Document Type': 'Loại chứng từ nhập', 'Receipt Document': 'Chứng từ nhập',
    'Get Items From Purchase Receipts': 'Lấy hàng từ phiếu nhập',
    'Purchase Receipt Item': 'Dòng phiếu nhập mua hàng', 'Purchase Receipts': 'Phiếu nhập mua hàng',
    'Stock Reconciliation Item': 'Dòng điều chỉnh theo kiểm kê',
    'Posting Date': 'Ngày hạch toán', 'Posting Time': 'Giờ hạch toán',
    'Edit Posting Date and Time': 'Sửa ngày, giờ hạch toán', 'Set Posting Time': 'Sửa giờ hạch toán',
    'Item Code': 'Mã hàng', 'Item Name': 'Tên hàng', 'Item Group': 'Nhóm hàng', 'Item Group Name': 'Tên nhóm hàng',
    'Parent Item Group': 'Nhóm hàng cấp trên',
    'UOM': 'ĐVT', 'Stock UOM': 'ĐVT tồn kho', 'Default Unit of Measure': 'Đơn vị tính mặc định',
    'Conversion Factor': 'Hệ số quy đổi', 'UOM Conversion Factor': 'Hệ số quy đổi ĐVT',
    'Maintain Stock': 'Theo dõi tồn kho', 'Has Batch No': 'Quản lý theo lô', 'Batch No': 'Số lô', 'Batch': 'Lô',
    'Valuation Method': 'Phương pháp tính giá', 'Moving Average': 'Bình quân gia quyền di động',
    'FIFO': 'Nhập trước xuất trước (FIFO)', 'Basic Rate': 'Đơn giá', 'Basic Amount': 'Thành tiền',
    'Rate': 'Đơn giá', 'Amount': 'Thành tiền', 'Qty': 'Số lượng', 'Quantity': 'Số lượng',
    'Price List Rate': 'Đơn giá theo bảng giá', 'Blanket Order Rate': 'Đơn giá đơn hàng khung',
    'Source Warehouse': 'Kho xuất', 'Target Warehouse': 'Kho nhập', 'Set Target Warehouse': 'Kho nhận (mọi dòng)',
    'Set From Warehouse': 'Kho xuất (mọi dòng)', 'Default Source Warehouse': 'Kho xuất mặc định',
    'Default Target Warehouse': 'Kho nhập mặc định', 'Accepted Warehouse': 'Kho nhận hàng đạt',
    'Rejected Warehouse': 'Kho hàng không đạt', 'Accepted Quantity': 'SL nhận đạt', 'Rejected Quantity': 'SL không đạt',
    'Received Quantity': 'SL đã nhận', 'Received Qty': 'SL đã nhận', 'Required By': 'Ngày cần hàng',
    'Get Items From': 'Lấy hàng từ', 'Series': 'Ký hiệu chứng từ', 'Draft': 'Nháp', 'Amend': 'Sửa đổi',
    'Material Receipt': 'Nhập kho khác', 'Material Issue': 'Xuất kho khác', 'Material Transfer': 'Chuyển kho',
    'Material Transfer for Manufacture': 'Chuyển kho cho sản xuất', 'Repack': 'Đóng gói lại',
    'Stock Ledger': 'Sổ chi tiết vật tư hàng hóa', 'Stock Balance': 'Tổng hợp nhập – xuất – tồn',
    'Stock Projected Qty': 'Số lượng tồn dự kiến', 'Stock and Account Value Comparison': 'So sánh giá trị tồn kho và sổ cái',
    'General Ledger': 'Sổ cái', 'Trial Balance': 'Bảng cân đối số phát sinh',
    'Accounts Frozen Till Date': 'Khóa sổ đến ngày', 'Role Allowed for Frozen Entries': 'Vai trò được sửa sổ đã khóa',
    'Frozen Accounts Modifier': 'Vai trò được sửa sổ đã khóa',
    'Roles Allowed to Set and Edit Frozen Account Entries': 'Vai trò được sửa sổ đã khóa',
    'Asset Category': 'Nhóm tài sản', 'Fixed Asset Account': 'TK nguyên giá TSCĐ',
    'Accumulated Depreciation Account': 'TK hao mòn lũy kế', 'Depreciation Expense Account': 'TK chi phí khấu hao',
    'Capital Work in Progress Account': 'TK XDCB dở dang', 'Gross Purchase Amount': 'Nguyên giá',
    'Opening Accumulated Depreciation': 'Hao mòn lũy kế đầu kỳ', 'Available-for-use Date': 'Ngày đưa vào sử dụng',
    'Available For Use Date': 'Ngày đưa vào sử dụng', 'Total Number of Depreciations': 'Tổng số kỳ khấu hao',
    'Frequency of Depreciation (Months)': 'Số tháng mỗi kỳ khấu hao', 'Depreciation Method': 'Phương pháp khấu hao',
    'Straight Line': 'Đường thẳng', 'Written Down Value': 'Số dư giảm dần', 'Existing Asset': 'Tài sản có từ trước',
    'Location': 'Vị trí', 'Journal Entry': 'Bút toán', 'Journal Entry Account': 'Dòng bút toán',
    'Debit': 'Nợ', 'Credit': 'Có', 'Debit in Company Currency': 'Phát sinh Nợ', 'Credit in Company Currency': 'Phát sinh Có',
    'Party Type': 'Loại đối tượng', 'Is Frozen': 'Bị khóa', 'Billing Currency': 'Tiền tệ lập hóa đơn',
    'Difference Account': 'Tài khoản chênh lệch', 'Difference Amount': 'Số chênh lệch',
}
PROPOSE = {**GLOSS, **APPROVED}
# Cụm sai lặp lại trong bản hiện tại → sửa trong mọi chuỗi ghép
FIX = [
    ('Tỷ giá định giá', 'Đơn giá vốn'), ('Tỷ lệ định giá', 'Đơn giá vốn'), ('Đơn giá định giá', 'Đơn giá vốn'),
    ('Bút toán tồn kho', 'Phiếu kho'), ('Biên nhận mua hàng', 'Phiếu nhập mua hàng'),
    ('Phiếu chi phí vận chuyển', 'Phiếu phân bổ chi phí vào giá trị tồn kho'), ('Chi phí hạ tầng', 'Chi phí nhập hàng'),
    ('chi phí đã đáp tàu', 'chi phí nhập hàng'), ('Chi phí nhập hàng Nhà cung cấp', 'chi phí nhập hàng của nhà cung cấp'), ('Ngày đăng', 'Ngày hạch toán'),
    ('Thời gian đăng', 'Giờ hạch toán'), ('Đối soát tồn kho', 'Điều chỉnh theo kiểm kê'),
    ('giá trị cổ phiếu', 'giá trị tồn kho'), ('Tỷ giá Danh sách Giá', 'Đơn giá theo bảng giá'),
    ('UOM tồn kho', 'ĐVT tồn kho'), ('Mã Mặt hàng', 'Mã hàng'), ('Tên Mặt hàng', 'Tên hàng'), ('Nhóm Mặt hàng', 'Nhóm hàng'),
    ('Danh mục Tài sản', 'Nhóm tài sản'), ('Phiếu nhập hàng', 'Phiếu nhập mua hàng'), ('Nguyên liệu thô', 'Nguyên vật liệu'),
]
def fix(v):
    v = re.sub(r'\bBOM\b', 'định mức nguyên vật liệu', v)
    v = re.sub(r'^định mức', 'Định mức', v)
    for a, b in FIX:
        v = v.replace(a, b).replace(a[0].lower() + a[1:], b[0].lower() + b[1:])
    return v

OLD = {'oá':'óa','oà':'òa','oả':'ỏa','oã':'õa','oạ':'ọa','Oá':'Óa','Oà':'Òa','uý':'úy','uỳ':'ùy','uỷ':'ủy','uỹ':'ũy','uỵ':'ụy','oé':'óe','oè':'òe'}
def old_tone(v):
    for a,b in OLD.items():
        v = re.sub(a + r'(?![a-zà-ỹ])', b, v)
    return v
def origin_is_donor(src): return src.startswith('ERPNext2VI') and '2.9' not in src
ASCII = re.compile(r"\b[A-Za-z]{3,}\b")
VN = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
def new_english(c, p, en=''):
    enw = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", en)}
    words = lambda t: {w for w in ASCII.findall(t) if not (set(w.lower()) & VN)}
    leak = {w for w in words(p) - words(c) if any(e.startswith(w.lower()) or w.lower().startswith(e) for e in enw)}
    return bool(leak - {'Serial', 'FIFO', 'BOM', 'Incoterm'})
KEEP = {'Nợ','Có','Việt','Nam','FIFO','LIFO','Serial','Incoterm','HTML','ID','UOM','ĐVT','TK','TSCĐ','XDCB','NVL','Email','Excel','USD','VND','SL','GIT','WIP','API','PDF','APH','ERPNext','Frappe'}
def norm_case(v):
    if not v or '{' in v or '<' in v or len(v.split()) > 8 or '\n' in v:
        return v
    out, first = [], True
    for w in v.split(' '):
        core = w.strip('()%#:,./-–')
        if first:
            out.append(w[:1].upper() + w[1:] if w else w); first = not core
        elif core in KEEP or (len(core) > 1 and core.isupper()) or any(ch.isdigit() for ch in core):
            out.append(w)
        else:
            out.append(w.lower())
    return ' '.join(out)
CONFLICT_OLD = {'Stock Reconciliation': 'Kế toán chốt 28/09 "Điều chỉnh theo kiểm kê" ≠ ERPNext2VI 2.9 "Đối soát tồn kho" – Dung chọn',
            'BOM': 'Kế toán chốt "Định mức NVL" ≠ 2.9 "Định mức nguyên vật liệu" – Dung chọn'}
BAD = [(r'\bBilled?\b|\bBilling\b', r'thanh toán|đã tính', 'Billing = lập hóa đơn (2.9)'),
       (r'\bStock\b', r'cổ phiếu', 'Stock ≠ cổ phiếu'), (r'Valuation Rate', r'[Tt]ỷ giá', 'Rate ≠ tỷ giá'),
       (r'\bRate\b', r'Tỷ giá(?! hối)', 'Rate thường là đơn giá')]

out = []
for s, r in rows.items():
    c, d = cur.get(s, ''), don.get(s, '')
    note, src = '', ''
    if s in PROPOSE:
        p, src = PROPOSE[s], ('Đã chốt 29/09' if s in DECIDED_2909 else 'Kế toán chốt 28/09' if s in APPROVED else 'Đề xuất (thuật ngữ)')
    elif s in canon:
        p, src = canon[s][0], 'ERPNext2VI 2.9 (' + (canon[s][1] or '') + ')'
    elif s in ctx_only:
        p, src, note = c or d, 'Giữ – chỉ đúng theo ngữ cảnh', f'2.9: "{ctx_only[s][0]}" chỉ cho {ctx_only[s][1]}'
    elif not c and d:
        p, src = d, 'ERPNext2VI (hiện chưa dịch)'
    elif not c and not d:
        p, src = '', 'Chưa có bản dịch'
    elif d and d != c:
        p, src = d, 'ERPNext2VI'
    else:
        p, src = c, 'Giữ'
    if origin_is_donor(src) and p and c and new_english(c, p, s):
        p, src = c, 'Giữ (bản ERPNext2VI thêm từ tiếng Anh)'
    if p:
        f1 = fix(old_tone(p))
        if f1 != p:
            src += ' + chuẩn hóa thuật ngữ'
        f2 = norm_case(f1)
        if f2 != f1:
            src += ' + viết hoa đầu câu'
        p = f2
    for en_re, vi_re, why in BAD:
        if re.search(en_re, s) and re.search(vi_re, p or ''):
            note = (note + '; ' if note else '') + 'Kiểm tra: ' + why
    CONFLICT = {}
    if s in CONFLICT:
        note = (note + '; ' if note else '') + CONFLICT[s]
    changed = (p or '') != (c or '')
    case_only = changed and (p or '').lower() == (c or '').lower()
    out.append({**r, 'cur': c, 'don': d, 'prop': p, 'origin': src, 'changed': changed, 'case_only': case_only, 'note': note})

json.dump(out, open(H + 'rows.json', 'w'), ensure_ascii=False, default=list)
import collections
print(len(out), 'changed', sum(o['changed'] for o in out), 'case_only', sum(o['case_only'] for o in out))
print(collections.Counter((o['prio'], o['changed']) for o in out))
print(collections.Counter(o['origin'].split(' (')[0] for o in out if o['changed']))
