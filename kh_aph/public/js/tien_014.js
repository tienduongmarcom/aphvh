// Lượt 0.14 (cờ kh_aph_tien_vay): đối chiếu sao kê trên thẻ tài khoản ngân hàng (chỉ đọc; dòng chưa ghi sổ mở phiếu nháp).
(function () {
	const bat = () => (frappe.boot.kh_aph || {}).tien_vay;
	const MAU = {dong_tieu_de: 1, ngay: "Ngày", ma: "Số tham chiếu", noi_dung: "Diễn giải", ghi_no: "Ghi nợ", ghi_co: "Ghi có"};

	function bang_ket_qua(m, frm) {
		const mau = {"Khớp": "green", "Lệch": "orange", "Trùng": "red", "Chưa ghi sổ": "blue"};
		const tong = Object.entries(m.tong || {}).map(([k, v]) => `<span class="indicator-pill ${mau[k] || "gray"}">${k}: ${v}</span>`).join(" ");
		const dong = (m.dong || []).map((r, i) => `<tr><td>${r.dong}</td><td>${frappe.datetime.str_to_user(r.ngay)}</td>
			<td>${frappe.utils.escape_html(r.ma || "")}</td><td>${frappe.utils.escape_html(r.noi_dung || "")}</td>
			<td style="text-align:right">${format_number(r.so_tien, null, 0)}</td>
			<td><span class="indicator-pill ${mau[r.trang_thai] || "gray"}">${r.trang_thai}</span></td>
			<td>${r.chung_tu ? frappe.utils.escape_html(r.chung_tu) : (r.trang_thai === "Chưa ghi sổ"
				? `<a data-i="${i}" class="kh-lap">${__("Lập phiếu nháp")}</a>` : "")}</td></tr>`).join("");
		const html = `<div>${tong}</div>${(m.loi || []).length ? `<div class="text-muted">${m.loi.join("<br>")}</div>` : ""}
			<table class="table table-bordered table-sm" style="font-size:12px"><thead><tr><th>Dòng</th><th>Ngày</th><th>Mã GD</th>
			<th>Nội dung</th><th>Số tiền</th><th>Trạng thái</th><th>Chứng từ</th></tr></thead><tbody>${dong}</tbody></table>`;
		const d = new frappe.ui.Dialog({title: __("Kết quả đối chiếu sao kê"), size: "extra-large",
			fields: [{fieldname: "kq", fieldtype: "HTML", options: html}]});
		d.$wrapper.on("click", ".kh-lap", (e) => {
			const r = m.dong[$(e.currentTarget).data("i")];
			const vao = r.so_tien > 0;
			frappe.new_doc("Payment Entry", {
				company: m.company, payment_type: vao ? "Receive" : "Pay",
				[vao ? "paid_to" : "paid_from"]: m.tai_khoan, paid_amount: Math.abs(r.so_tien), received_amount: Math.abs(r.so_tien),
				reference_no: r.ma || ("SK-" + r.ngay + "-" + r.dong), reference_date: r.ngay, posting_date: r.ngay,
				remarks: r.noi_dung,
			});
		});
		d.show();
	}

	frappe.ui.form.on("Bank Account", {
		refresh(frm) {
			if (!bat() || frm.is_new() || !frm.doc.is_company_account) return;
			frm.add_custom_button(__("Đối chiếu sao kê"), () => {
				frappe.db.get_value("Bank", frm.doc.bank, "kh_aph_mau_sao_ke").then(({message}) => {
					const co_mau = message && message.kh_aph_mau_sao_ke;
					const d = new frappe.ui.Dialog({
						title: __("Đối chiếu sao kê {0}", [frm.doc.account_name]),
						fields: [
							{fieldname: "file_url", label: __("Tệp sao kê (.xlsx / .csv)"), fieldtype: "Attach", reqd: 1},
							{fieldname: "anh_xa", label: __("Mẫu cột (để trống: dùng mẫu đã lưu của ngân hàng)"), fieldtype: "Code",
							 options: "JSON", default: co_mau ? "" : JSON.stringify(MAU, null, 1)},
							{fieldname: "luu_mau", label: __("Lưu mẫu cột cho ngân hàng này"), fieldtype: "Check", default: co_mau ? 0 : 1},
						],
						primary_action_label: __("Đối chiếu"),
						primary_action(v) {
							frappe.call({method: "kh_aph.tien_vay.doi_chieu_sao_ke", freeze: true,
								args: {bank_account: frm.doc.name, ...v}, callback: (r) => { d.hide(); bang_ket_qua(r.message, frm); }});
						},
					});
					d.show();
				});
			});
		},
	});
})();
