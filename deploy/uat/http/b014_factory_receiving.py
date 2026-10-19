"""Nhận nhanh từ PO bằng phiên nhà máy, không giá vốn trong facade."""
import json
from concurrent.futures import ThreadPoolExecutor


def chay(rpc,get,insert,submit,lst,denied,f,phien,emit):
    dung=phien(f['dung'])
    po=submit(insert({'doctype':'Purchase Order','company':f['aph'],'supplier':f['ncc'],
        'transaction_date':f['date'],'schedule_date':f['date'],'currency':'VND','conversion_rate':1,
        'items':[{'item_code':f['A'],'qty':10,'uom':'Kg','conversion_factor':1,'rate':20000,
                  'warehouse':f['kho'],'schedule_date':f['date']}] }))
    orders=rpc('kh_aph.factory_receiving.orders',{'company':f['aph']},dung)
    assert po['name'] in [x['name'] for x in orders] and all(set(x)=={'name','supplier'} for x in orders)
    denied(lambda:rpc('kh_aph.factory_receiving.orders',{'company':f['vh']},phien(f['scope_co'])),('PermissionError',))
    script=rpc('frappe.desk.query_report.get_script',{'report_name':'Ton kho so luong'},dung)['script']
    assert 'kh_aph.receiving.open' in script and '{% include' not in script and '/assets/kh_aph/js/factory_receiving.js' not in script
    view=rpc('kh_aph.factory_receiving.preview',{'purchase_order':po['name']},dung)
    assert set(view)=={'purchase_order','company','supplier','price_mode','items'}
    assert view['items'][0]['remaining']==10 and not any(k in json.dumps(view) for k in ('"rate"','"amount"','"valuation_rate"'))
    denied(lambda:rpc('kh_aph.factory_receiving.preview',{'purchase_order':po['name']},phien(f['tp'])),('PermissionError',))
    emit('HTTP_3A_RECEIVING_SCOPE_PREVIEW','PASS',{'restricted_principal':True,'quantity_only':True})
    row={'source_row':view['items'][0]['source_row'],'warehouse':f['kho'],'qty':4,'bags':0,'quality_qty':1}
    file=insert({'doctype':'File','file_name':f['p']+'-phieu-can.txt','is_private':1,'content':'Can UAT '+f['p']},dung)
    args={'purchase_order':po['name'],'request_id':f['p']+'-nhan-1','rows':json.dumps([row]),
          'received_date':f['date'],'receiver':'Nhân viên kho ký giấy','ticket':file['file_url'],'note':'UAT nhận từng phần, hàng có vấn đề vẫn dùng, chờ đàm phán giảm giá'}
    result=rpc('kh_aph.factory_receiving.receive',args,dung)
    receipt=get('Purchase Receipt',result['name'])
    attached=get('File',file['name'],dung)
    assert attached['is_private']==1 and attached['attached_to_doctype']=='Purchase Receipt' and attached['attached_to_name']==result['name']
    assert receipt['kh_aph_receiving_ticket']==file['file_url']
    assert receipt['kh_aph_receiving_price_review']==1 and receipt['items'][0]['kh_aph_receiving_quality_qty']==1
    assert receipt['docstatus']==1 and receipt['items'][0]['qty']==4 and receipt['items'][0]['rate']==20000
    assert receipt['items'][0]['purchase_order']==po['name'] and receipt['kh_aph_receiving_actor']==f['dung']
    def counts():return {dt:len(lst(dt,{},['name'])) for dt in ('Purchase Receipt','Stock Ledger Entry','GL Entry','Payment Ledger Entry')}
    masked=get('Purchase Receipt',result['name'],dung)
    assert not masked['items'][0].get('rate') and not masked.get('grand_total')
    before=counts()
    assert rpc('kh_aph.factory_receiving.receive',args,dung)==result and counts()==before
    denied(lambda:rpc('kh_aph.factory_receiving.receive',{**args,'note':'đổi nội dung'},dung))
    assert rpc('kh_aph.factory_receiving.preview',{'purchase_order':po['name']},dung)['items'][0]['remaining']==6
    emit('HTTP_3A_RECEIVING_PARTIAL_REPLAY','PASS',{'qty':4,'remaining':6,'one_receipt_one_posting':True,'retry_unchanged':True})
    denied(lambda:rpc('kh_aph.factory_receiving.receive',{**args,'request_id':'forged','rows':json.dumps([{**row,'rate':1}])},dung))
    denied(lambda:rpc('kh_aph.factory_receiving.receive',{**args,'request_id':'other-company','rows':json.dumps([{**row,'warehouse':f['kho_vh']}])},dung))
    denied(lambda:rpc('frappe.client.set_value',{'doctype':'Purchase Receipt','name':result['name'],
        'fieldname':'kh_aph_receiving_receiver','value':'sửa người nhận'}))
    assert counts()==before
    emit('HTTP_3A_RECEIVING_TAMPER','PASS',{'no_input_prices':True,'wrong_company_denied':True,'source_stamp_kept':True})
    a,b=phien(f['dung']),phien(f['dung'])
    def racing(pair):
        token,caller=pair
        try:return rpc('kh_aph.factory_receiving.receive',{**args,'request_id':token,'ticket':''},caller)['name']
        except Exception as exc:
            if not hasattr(exc,'read'):raise
            data=json.loads(exc.read())
            assert data.get('exc_type')=='ValidationError',data
            return None
    with ThreadPoolExecutor(2) as pool: outcomes=list(pool.map(racing,[('race-a',a),('race-b',b)]))
    assert len([r for r in outcomes if r])==1,outcomes
    assert rpc('kh_aph.factory_receiving.preview',{'purchase_order':po['name']},dung)['items'][0]['remaining']==2
    emit('HTTP_3A_RECEIVING_RACE','PASS',{'two_sessions_only_one_four_kg_receipt':True,'remaining':2})

    import os,subprocess
    from pathlib import Path
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    before=counts()
    browser=subprocess.run(['node',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),json.dumps({'purchase_order':po['name'],'user':f['dung'],'company':f['aph']}),'nhan-hang-nha-may'],
        input=json.dumps({'cookies':phien(f['dung']).browser_cookies()}),text=True,capture_output=True,timeout=180)
    assert browser.returncode==0,(browser.stdout[-1600:],browser.stderr[-2400:])
    cases=[json.loads(line) for line in browser.stdout.splitlines() if line.startswith('{"case":')]
    assert len(cases)==1 and cases[0]['status']=='PASS',browser.stdout
    after=counts()
    assert after['Purchase Receipt']==before['Purchase Receipt']+1 and after['Stock Ledger Entry']==before['Stock Ledger Entry']+1
    assert after['Payment Ledger Entry']==before['Payment Ledger Entry']
    assert get('Purchase Receipt',cases[0]['detail']['name'])['items'][0]['qty']==1
    assert rpc('kh_aph.factory_receiving.preview',{'purchase_order':po['name']},dung)['items'][0]['remaining']==1
    emit(cases[0]['case'],'PASS',cases[0].get('detail'))
