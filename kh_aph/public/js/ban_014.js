// Lượt 0.14 (cờ kh_aph_trung_tam_ban): duyệt giá dưới sàn trên đơn chung; in lại phiếu xuất kho kèm số hóa đơn MISA.
(function () {
	const bat = () => (frappe.boot.kh_aph || {}).trung_tam_ban;

	frappe.ui.form.on("APH Shared Sales Order", {
		refresh(frm) {
			if (!bat() || !(frappe.boot.kh_aph || {}).gia_san) return;
			if (frm.doc.docstatus !== 0 || frm.is_new() || !frm.doc.kh_aph_duoi_san || frm.doc.kh_aph_duyet_san_boi) return;
			frm.dashboard.set_headline_alert(__("Có dòng dưới giá sàn, cần duyệt trước khi xác nhận"), "orange");
			frm.add_custom_button(__("Duyệt giá dưới sàn"), () => {
				frappe.call({method: "kh_aph.trung_tam_ban.xem_duoi_san_chung", args: {name: frm.doc.name}}).then((r) => {
					const m = r.message || {};
					if (!m.duoc_duyet) return frappe.msgprint(__("Dòng {0} dưới giá sàn. Bạn không có quyền duyệt; báo người duyệt.",
						[(m.dong || []).map((x) => x.idx).join(", ")]));
					frappe.prompt({fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1,
						description: (m.dong || []).map((x) => `Dòng ${x.idx} ${x.item_code} (${x.company}): thấp hơn sàn ${x.phan_tram}%`).join("<br>")},
					(v) => frappe.call({method: "kh_aph.trung_tam_ban.duyet_don_chung", args: {name: frm.doc.name, ly_do: v.ly_do},
						callback: () => frm.reload_doc()}), __("Duyệt giá dưới sàn"));
				});
			});
		},
	});

	frappe.ui.form.on("Delivery Note", {
		refresh(frm) {
			for (const field of ["kh_aph_ho_so_giao_nhan", "kh_aph_ban_ky", "kh_aph_ghi_chu_ban_ky", "kh_aph_doi_chieu_boi", "kh_aph_doi_chieu_luc"]) {
				frm.toggle_display(field, !!bat() && frm.doc.docstatus === 1 && !frm.doc.is_return);
			}
            if (bat() && frm.doc.kh_aph_lich_su_ban_ky && !frm.doc.is_return) {
                frm.add_custom_button("Lịch sử bản ký", () => {
                    const e = frappe.utils.escape_html;
                    const link = url => typeof url === "string" && url.startsWith("/private/files/")
                        ? `<a href="${e(url)}" target="_blank" rel="noopener">Mở bản ký</a>` : "Chưa có";
                    let history;
                    try { history = JSON.parse(frm.doc.kh_aph_lich_su_ban_ky); }
                    catch (_) { return frappe.msgprint("Lịch sử cần quản trị kiểm tra."); }
                    const rows = (history.events || []).map(x => {
                        const a = x.before || {}, b = x.after || {};
                        return `<tr><td>${e(x.at || "")}</td><td>${e(x.by || "")}</td><td>
                            ${link(a.kh_aph_ban_ky)} → ${link(b.kh_aph_ban_ky)}<br>
                            Ghi chú: ${e(a.kh_aph_ghi_chu_ban_ky || "")} → ${e(b.kh_aph_ghi_chu_ban_ky || "")}<br>
                            Đối chiếu: ${e(a.kh_aph_doi_chieu_boi || "Chưa đối chiếu")} → ${e(b.kh_aph_doi_chieu_boi || "Chưa đối chiếu")}<br>
                            Giấy gốc tại kho: ${e(a.kh_aph_vi_tri_goc || "Chưa nhận")} → ${e(b.kh_aph_vi_tri_goc || "Chưa nhận")}<br>
                            Bản khách ký tại đích: ${link(a.kh_aph_ban_ky_khach)} → ${link(b.kh_aph_ban_ky_khach)}<br>
                            Kiểm bản khách ký: ${e(a.kh_aph_kiem_ky_khach_boi || "Chưa kiểm")} → ${e(b.kh_aph_kiem_ky_khach_boi || "Chưa kiểm")}<br>
                            Gốc khách ký: ${e(a.kh_aph_vi_tri_goc_khach || "Chưa nhận")} → ${e(b.kh_aph_vi_tri_goc_khach || "Chưa nhận")}</td></tr>`;
                    }).join("");
                    const dialog = new frappe.ui.Dialog({title: "Lịch sử bản ký", size: "extra-large", fields: [
                        {fieldtype: "HTML", options: `<div class="table-responsive"><table class="table table-bordered"><thead><tr><th>Thời điểm</th><th>Người thao tác</th><th>Trước → Sau</th></tr></thead><tbody>${rows}</tbody></table></div>`}
                    ]});
                    dialog.show();
                }, "Hồ sơ giao nhận");
            }
			if (!bat() || frm.doc.docstatus !== 1 || frm.doc.is_return) return;
            const needsCustomerProof = frm.doc.kh_aph_mau_giao_nhan === 1 && frm.doc.kh_aph_cach_giao === "Vận chuyển"
                && frm.doc.kh_aph_can_ky_khach === "Có";
            if (needsCustomerProof && frm.perm.some(p => p.write)) {
                frm.add_custom_button("Nhận hồ sơ khách ký", () => {
                    if (frm.is_dirty()) return frappe.msgprint("Lưu phiếu và tệp đã tải trước khi nhận hồ sơ khách ký.");
                    const inTransit = frm.doc.kh_aph_delivery_state !== "Khách đã nhận";
                    const dialog = new frappe.ui.Dialog({title: "Nhận hồ sơ khách ký tại đích", fields: [
                        {fieldtype: "HTML", options: "<p>Kiểm bản khách ký riêng với bản giao nhà xe. Có thể nhận giấy gốc trước, tải ảnh sau; thao tác này không ghi thêm kho hoặc tiền.</p>"},
                        {fieldname: "location", label: "Vị trí tập giấy gốc tại kế toán", fieldtype: "Data",
                            default: frm.doc.kh_aph_vi_tri_goc_khach,
                            reqd: !frm.doc.kh_aph_ban_ky_khach && !frm.doc.kh_aph_nhan_goc_khach_boi},
                        {fieldname: "received_on", label: "Ngày khách đã nhận hàng", fieldtype: "Date", hidden: !inTransit,
                            reqd: inTransit, default: frappe.datetime.get_today()}
                    ], primary_action_label: "Xác nhận đã kiểm hồ sơ", async primary_action(v) {
                        dialog.disable_primary_action();
                        try {
                            await frappe.call({method: "kh_aph.customer_delivery_proof.receive", args: {
                                name: frm.doc.name, modified: frm.doc.modified, location: v.location || "",
                                received_on: inTransit ? v.received_on : null}, freeze: true});
                            dialog.hide(); await frm.reload_doc();
                        } finally {dialog.enable_primary_action();}
                    }});
                    dialog.show();
                }, "Hồ sơ giao nhận");
            }
            if (!frm.doc.kh_aph_nhan_goc_boi && frm.perm.some(p => p.write)) {
                frm.add_custom_button("Nhận giấy gốc", () => {
                    if (frm.is_dirty()) return frappe.msgprint("Lưu phiếu trước khi nhận giấy gốc.");
                    frappe.prompt({fieldname: "location", label: "Vị trí tập lưu tại kế toán cửa hàng", fieldtype: "Data", reqd: 1},
                        values => frappe.call({method: "kh_aph.ho_so_giao_nhan.nhan_giay_goc",
                            args: {name: frm.doc.name, modified: frm.doc.modified, ...values}, freeze: true}).then(() => frm.reload_doc()),
                        "Nhận giấy gốc", "Xác nhận đã nhận");
                }, "Hồ sơ giao nhận");
            }
			if (frm.doc.kh_aph_ban_ky && frm.perm[0] && frm.perm[0].write) {
				frm.add_custom_button(__("Gỡ bản ký khỏi phiếu"), () => {
					frappe.confirm(__("Gỡ bản ký sẽ bỏ dấu đối chiếu. Tệp vẫn giữ trong hồ sơ đính kèm."), () => {
						frm.set_value("kh_aph_ban_ky", "").then(() => frm.save("Update"));
					});
				}, __("Hồ sơ giao nhận"));
			}
			if (!frm.doc.kh_aph_ban_ky && frm.doc.kh_aph_delivery_state === "Khách đã nhận") {
				frm.dashboard.set_headline_alert(__("Đã nhận hàng, còn thiếu bản phiếu có chữ ký"), "orange");
			} else if (frm.doc.kh_aph_ban_ky && !frm.doc.kh_aph_doi_chieu_boi) {
				frm.dashboard.set_headline_alert(__("Đã có bản ký, cần đối chiếu nội dung và ghi chú chênh lệch"), "orange");
				if (frm.perm[0] && frm.perm[0].write && (frm.doc.kh_aph_delivery_state === "Khách đã nhận" || (frm.doc.kh_aph_mau_giao_nhan && frm.doc.kh_aph_delivery_state === "Đang giao"))) {
					frm.add_custom_button(__("Đối chiếu bản ký"), () => {
						if (frm.is_dirty()) return frappe.msgprint(__("Lưu phiếu trước khi đối chiếu bản ký"));
						frappe.confirm(__("Bạn đã mở bản ký, kiểm tra lượng thực nhận và ghi chú các chênh lệch?"), () =>
							frappe.call({method: "kh_aph.ho_so_giao_nhan.doi_chieu",
								args: {name: frm.doc.name, modified: frm.doc.modified}, freeze: true
							}).then(() => frm.reload_doc()));
					}, __("Hồ sơ giao nhận"));
				}
			}
			frm.add_custom_button(__("In lại phiếu xuất kho"), () => frappe.call({method: "kh_aph.trung_tam_ban.in_lai",
				args: {delivery_note: frm.doc.name}}).then((r) => {
				const w = window.open("", "_blank");
				w.document.write(r.message.html);
				w.document.close();
				w.focus();
				setTimeout(() => w.print(), 600);
				frm.reload_doc();
			}), "In");
		},
	});
})();
