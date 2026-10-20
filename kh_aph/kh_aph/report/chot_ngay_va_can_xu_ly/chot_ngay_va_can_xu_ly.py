from kh_aph.day_close import review


def execute(filters=None):
    f = filters or {}
    values = review(f.get('company'), f.get('day'))
    columns = [{'fieldname': name, 'label': label, 'fieldtype': kind, 'width': width, **extra}
        for name,label,kind,width,extra in [
            ('group','Nhóm','Data',180,{}), ('status','Tình trạng / việc cần xử lý','Data',340,{}),
            ('doctype','Loại hồ sơ','Data',160,{}), ('document','Hồ sơ','Dynamic Link',180,{'options':'doctype'}),
            ('account','Quỹ / tài khoản','Link',200,{'options':'Account'}), ('holder','Người giữ','Link',200,{'options':'User'}),
            ('party','Khách hàng','Link',180,{'options':'Customer'}),
            ('item_code','Mã hàng','Link',160,{'options':'Item'}), ('warehouse','Kho','Link',180,{'options':'Warehouse'}),
            ('quantity','Lượng thực xuất','Float',130,{}), ('uom','Đơn vị lượng','Link',100,{'options':'UOM'}), ('bags','Số bao','Float',110,{}),
            ('opening','Nợ đầu ngày','Currency',140,{'options':'VND'}), ('increase','Nợ tăng','Currency',130,{'options':'VND'}),
            ('decrease','Nợ giảm','Currency',130,{'options':'VND'}), ('amount','Trách nhiệm / dư cuối / giá trị','Currency',190,{'options':'VND'}),
            ('reserved','Giữ chỗ / cọc','Currency',140,{'options':'VND'}), ('available','Khả dụng / chưa phân bổ','Currency',180,{'options':'VND'}),
            ('counted','Thực đếm gần nhất','Currency',150,{'options':'VND'}), ('difference','Chênh lệch','Currency',130,{'options':'VND'}),
            ('checked_at','Thời điểm số đếm / sao kê','Datetime',180,{}), ('assignee','Người xử lý','Link',180,{'options':'User'}),
            ('due_date','Hạn xử lý','Date',120,{}), ('overdue','Quá hạn','Check',90,{})]]
    return columns, values['rows'], 'Tiền, cọc và việc tồn theo trạng thái hiện tại; thực đếm ghi rõ thời điểm ca gần nhất. Công nợ theo ngày chọn; hàng gồm trong ngày và hồ sơ còn thiếu. Sao kê chỉ gồm Bank Transaction native đã lưu, không tự coi kết quả đối chiếu tệp tạm là đã khớp. Số liệu trong phạm vi quyền, không tự ghi sổ hoặc chốt số.'
