"""Nhận chờ giá theo đơn mua, giữ chỗ chung với các đường native."""
import json
from concurrent.futures import ThreadPoolExecutor


def chay(rpc,get,insert,submit,lst,denied,f,phien,emit,feature):
    dung=phien(f['dung']);ktt=phien(f['ktt'])
    def order(qty=10,rate=20000):
        return submit(insert({'doctype':'Purchase Order','company':f['aph'],'supplier':f['ncc'],
            'transaction_date':f['date'],'schedule_date':f['date'],'currency':'VND','conversion_rate':1,
            'items':[{'item_code':f['A'],'qty':qty,'uom':'Kg','conversion_factor':1,'rate':rate,
                'warehouse':f['kho'],'schedule_date':f['date']}] }))
    po=order();source=po['items'][0]['name']
    row={'source_row':source,'warehouse':f['kho'],'qty':4,'bags':0,'quality_qty':1}
    file=insert({'doctype':'File','file_name':f['p']+'-cho-gia.txt','is_private':1,'content':'Nhan cho gia '+f['p']},dung)
    args={'purchase_order':po['name'],'request_id':f['p']+'-pending','rows':json.dumps([row]),
        'received_date':f['date'],'receiver':'Người kho nhận chờ giá','ticket':file['file_url'],
        'note':'Có1kg cần đàm phán, chưa vào tồn khả dụng','mode':'pending'}
    def ledgers():return {dt:len(lst(dt,{},['name'])) for dt in ('Stock Ledger Entry','GL Entry','Payment Ledger Entry')}
    before=ledgers()
    result=rpc('kh_aph.factory_receiving.receive',args,dung)
    assert result['doctype']=='APH Pending Receipt' and result['docstatus']==1 and ledgers()==before
    pending=get(result['doctype'],result['name'],dung)
    assert pending['kh_aph_receiving_purchase_order']==po['name'] and pending['items'][0]['kh_aph_receiving_source_row']==source
    assert pending['items'][0]['qty']==4 and pending['items'][0]['kh_aph_receiving_quality_qty']==1
    attached=get('File',file['name'],dung)
    assert attached['is_private']==1 and attached['attached_to_name']==pending['name'] and attached['attached_to_doctype']=='APH Pending Receipt'
    assert rpc('kh_aph.factory_receiving.receive',args,dung)==result
    assert ledgers()==before
    def remaining(order_name=po['name'],mode='pending'):
        return rpc('kh_aph.factory_receiving.preview',{'purchase_order':order_name,'mode':mode},dung)['items'][0]['remaining']
    assert remaining()==remaining(mode='valued')==6
    emit('HTTP_3B_PENDING_RESERVE_REPLAY','PASS',{'pending_qty':4,'remaining':6,'private_file':True,'no_ledger':True})

    def native(dt,qty):
        key='purchase_order_item' if dt=='Purchase Receipt' else 'po_detail'
        return {'doctype':dt,'company':f['aph'],'supplier':f['ncc'],'posting_date':f['date'],
            'currency':'VND','conversion_rate':1,**({'update_stock':1} if dt=='Purchase Invoice' else {}),
            'items':[{'item_code':f['A'],'warehouse':f['kho'],'qty':qty,'received_qty':qty,'rate':20000,
                'uom':'Kg','conversion_factor':1,'purchase_order':po['name'],key:source}]}
    try:
        feature(False,'kh_aph_factory_receiving')
        for dt in ('Purchase Receipt','Purchase Invoice'):
            draft=insert(native(dt,7))
            denied(lambda draft=draft:submit(draft))
        assert ledgers()==before
    finally:
        feature(True,'kh_aph_factory_receiving')
    emit('HTTP_3B_NATIVE_RESERVATION_FLAG_OFF','PASS',{'native_pr_pi_blocked':True,'reservation_survives_flag_off':True})

    denied(lambda:rpc('kh_aph.factory_receiving.receive',{**args,'mode':'valued'},dung))
    denied(lambda:rpc('kh_aph.factory_receiving.receive',{**args,'request_id':'changed','rows':json.dumps([{**row,'rate':1}])},dung))
    denied(lambda:rpc('frappe.client.set_value',{'doctype':'APH Pending Receipt','name':pending['name'],
        'fieldname':'kh_aph_receiving_purchase_order','value':''}))
    denied(lambda:rpc('frappe.client.cancel',{'doctype':'Purchase Order','name':po['name']}))
    def change_po(qty=10,rate=20000):
        return rpc('erpnext.controllers.accounts_controller.update_child_qty_rate',{
            'parent_doctype':'Purchase Order','parent_doctype_name':po['name'],
            'trans_items':json.dumps([{'docname':source,'qty':qty,'rate':rate,'uom':'Kg','conversion_factor':1}])})
    denied(lambda:change_po(qty=3))
    assert get('Purchase Order',po['name'])['items'][0]['qty']==10 and ledgers()==before
    emit('HTTP_3B_PENDING_SOURCE_TAMPER','PASS',{'mode_bound':True,'immutable_source':True,'po_cannot_discard_pending':True})

    callers=[phien(f['dung']),phien(f['dung'])]
    def racing(pair):
        mode,caller=pair
        try:return rpc('kh_aph.factory_receiving.receive',{**args,'mode':mode,'ticket':'',
            'request_id':'3b-race-'+mode},caller)
        except Exception as exc:
            if not hasattr(exc,'read'):raise
            data=json.loads(exc.read());assert data.get('exc_type')=='ValidationError',data
            return None
    with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(racing,zip(['pending','valued'],callers)))
    assert len([x for x in outcomes if x])==1,outcomes
    assert remaining()==2
    emit('HTTP_3B_PENDING_VALUED_RACE','PASS',{'cross_mode_only_one_four_kg':True,'remaining':2})

    pending=get('APH Pending Receipt',pending['name'])
    rates={pending['items'][0]['name']:25000}
    final_args={'name':pending['name'],'rates':json.dumps(rates),'reason':'Chốt giá theo đơn mua đã xác minh'}
    denied(lambda:rpc('kh_aph.pending_valuation.finalize',final_args,dung),('PermissionError',))
    denied(lambda:rpc('kh_aph.pending_valuation.finalize',final_args,ktt))
    change_po(rate=25000)
    name=rpc('kh_aph.pending_valuation.finalize',final_args,ktt)
    receipt=get('Purchase Receipt',name)
    assert receipt['docstatus']==1 and receipt['items'][0]['qty']==4 and receipt['items'][0]['rate']==25000
    assert receipt['items'][0]['purchase_order']==po['name'] and receipt['items'][0]['purchase_order_item']==source
    assert receipt['items'][0]['kh_aph_receiving_quality_qty']==1 and receipt['kh_aph_receiving_actor']==f['dung']
    assert remaining()==2
    after=ledgers()
    assert rpc('kh_aph.pending_valuation.finalize',final_args,ktt)==name and ledgers()==after
    emit('HTTP_3B_PENDING_FINALIZE_ONCE','PASS',{'qty':4,'native_po_link':True,'same_order_price':True,'reservation_not_double_counted':True})

    rpc('frappe.client.cancel',{'doctype':'Purchase Receipt','name':name})
    assert remaining()==2 and get('APH Pending Receipt',pending['name'])['status']=='Chờ định giá'
    rpc('frappe.client.cancel',{'doctype':'APH Pending Receipt','name':pending['name']})
    assert remaining()==6
    denied(lambda:rpc('frappe.client.delete',{'doctype':'APH Pending Receipt','name':pending['name']}))
    assert get('APH Pending Receipt',pending['name'])['kh_aph_receiving_ticket']==file['file_url']
    emit('HTTP_3B_PENDING_CANCEL_HISTORY','PASS',{'cancel_pr_restores_reservation':True,'cancel_pending_releases':True,'history_kept':True})

    import os,subprocess
    from pathlib import Path
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    browser_po=order(3)
    before=ledgers();count=len(lst('APH Pending Receipt',{},['name']))
    browser=subprocess.run(['node',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),
        json.dumps({'purchase_order':browser_po['name'],'user':f['dung'],'company':f['aph']}),'nhan-cho-gia-nha-may'],
        input=json.dumps({'cookies':phien(f['dung']).browser_cookies()}),text=True,capture_output=True,timeout=180)
    assert browser.returncode==0,(browser.stdout[-1800:],browser.stderr[-2400:])
    cases=[json.loads(line) for line in browser.stdout.splitlines() if line.startswith('{"case":')]
    assert len(cases)==1 and cases[0]['status']=='PASS',browser.stdout
    assert len(lst('APH Pending Receipt',{},['name']))==count+1 and ledgers()==before
    assert remaining(browser_po['name'])==2
    for case in cases:emit(case['case'],case['status'],case['detail'])
