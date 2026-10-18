"""Shipment-specific credit approval binding and increase calculation."""
from decimal import Decimal
import hashlib,json

def credit_increase(balance, amount):
    b,a=Decimal(str(balance)),Decimal(str(amount))
    if not b.is_finite() or not a.is_finite() or a<0:
        raise ValueError('Invalid credit increase inputs')
    return max(Decimal(0),b+a)-max(Decimal(0),b)

def shipment_fingerprint(doc):
    fields=('customer','company','currency','posting_date',
            'grand_total','discount_amount','additional_discount_percentage','apply_discount_on')
    data={k:str(doc.get(k) or '') for k in fields}
    data['items']=[{k:str(r.get(k) or '') for k in
        ('item_code','warehouse','qty','rate','uom','conversion_factor','against_sales_order','so_detail','item_tax_template')}
        for r in doc.get('items') or []]
    data['taxes']=[{k:str(r.get(k) or '') for k in
        ('charge_type','account_head','rate','tax_amount','included_in_print_rate')}
        for r in doc.get('taxes') or []]
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
