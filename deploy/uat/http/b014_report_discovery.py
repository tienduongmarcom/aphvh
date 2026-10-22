"""NoCost: lối phụ tìm biến thể chỉ trả rỗng, không mở danh mục/SQL hay dữ liệu kho."""
import json


def chay(rpc, denied, dung, ktt, emit):
    method = 'frappe.desk.reportview.get_list'
    args = {'doctype':'Report','fields':json.dumps(['name','report_name']),
        'filters':json.dumps({'reference_report':'Ton kho so luong','report_type':'Custom Report','disabled':0}),
        'order_by':'report_name asc','limit':0}
    assert rpc(method,args,dung) == []
    for changed in [{'fields':json.dumps(['query'])},{'fields':json.dumps(['*'])},
                    {'filters':json.dumps({'reference_report':'Stock Balance','report_type':'Custom Report','disabled':0})},
                    {'doctype':'Bin'}, {'ignore_permissions':1}]:
        denied(lambda:rpc(method,{**args,**changed},dung),('PermissionError',))
    owned = rpc(method,{'doctype':'APH Phieu quy nha may','fields':json.dumps(['name']),'limit':0},dung)
    assert isinstance(owned,list)
    assert isinstance(rpc(method,args,ktt),list)
    emit('HTTP_014_AN_VON_TIM_BIEN_THE_BAO_CAO','PASS',{'empty_no_cost_discovery':True,
         'sql_and_cost_report_denied':True,'owned_factory_list_native':True,'accountant_native':True})
