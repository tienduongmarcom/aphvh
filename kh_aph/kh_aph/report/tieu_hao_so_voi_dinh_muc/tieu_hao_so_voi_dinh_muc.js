// 0.11.2: Tiêu hao so với định mức theo kho dở dang dây chuyền và kỳ quyết toán (docs/dac-ta-0.11.2.md mục 3).
frappe.query_reports["Tieu hao so voi dinh muc"] = {
	filters: [
		{fieldname: "kho", label: __("Kho dở dang dây chuyền"), fieldtype: "Link", options: "Warehouse", reqd: 1,
			get_query: () => ({filters: {kh_aph_loai_kho: "Dở dang dây chuyền", is_group: 0}})},
		{fieldname: "moc", label: __("Đến mốc (trống = bây giờ)"), fieldtype: "Datetime",
			description: __("Kỳ tính từ lần quyết toán về 0 trước mốc này. Chọn đúng giờ của một lần quyết toán để xem kỳ đã đóng.")},
	],
};
