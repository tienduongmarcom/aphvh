# Bản cài ERPNext có kèm app aphvh.
# Dựng:  docker build -t aphvh-erpnext:0.4.13 .
# ERPNEXT_IMAGE phải trùng phiên bản ERPNext đang chạy (hiện là v16.36.1).
ARG ERPNEXT_IMAGE=frappe/erpnext:v16.36.1
FROM ${ERPNEXT_IMAGE}

USER frappe
WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe . apps/aphvh

# Tệp JS của app nạp qua hook doctype_js (đọc thẳng từ thư mục app), không cần build asset: chỉ cần đưa thư mục app vào đường dẫn
# import của môi trường Python của bench (tương đương cài "editable"), không cần mạng.
# Ghi aphvh vào sites/apps.txt của bản dựng để `bench version` và site mới trên ổ trống đều thấy app
# (site đang chạy đọc apps.txt trong ổ dữ liệu sites của nó).
RUN SITE_PACKAGES="$(./env/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
 && echo "/home/frappe/frappe-bench/apps/aphvh" > "${SITE_PACKAGES}/aphvh.pth" \
 && (grep -qx aphvh sites/apps.txt || { sed -i -e '$a\' sites/apps.txt && echo aphvh >> sites/apps.txt; }) \
 && ./env/bin/python -c "import aphvh, aphvh.hooks, aphvh.costing_rules; print('aphvh', aphvh.__version__)" \
 && ./env/bin/python -m unittest aphvh.tests.test_costing_rules aphvh.tests.test_vn_words aphvh.tests.test_print_formats aphvh.tests.test_translations aphvh.tests.test_sales_rules aphvh.tests.test_control_rules aphvh.tests.test_vat_rules aphvh.tests.test_print_rules aphvh.tests.test_tong_hop_khach aphvh.tests.test_so_hkd aphvh.tests.test_hkd_accounts aphvh.tests.test_ben_thu_ba -v
