# Bản cài ERPNext có kèm app aphvh.
# Dựng:  docker build -t aphvh-erpnext:0.2.0 .
# ERPNEXT_IMAGE phải trùng phiên bản ERPNext đang chạy (hiện là v16.36.0).
ARG ERPNEXT_IMAGE=frappe/erpnext:v16.36.0
FROM ${ERPNEXT_IMAGE}

USER frappe
WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe . apps/aphvh

# Tệp JS của app nạp qua hook doctype_js (đọc thẳng từ thư mục app), không cần build asset: chỉ cần đưa thư mục app vào đường dẫn
# import của môi trường Python của bench (tương đương cài "editable"), không cần mạng.
RUN SITE_PACKAGES="$(./env/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
 && echo "/home/frappe/frappe-bench/apps/aphvh" > "${SITE_PACKAGES}/aphvh.pth" \
 && ./env/bin/python -c "import aphvh, aphvh.hooks, aphvh.costing_rules; print('aphvh', aphvh.__version__)" \
 && ./env/bin/python -m unittest aphvh.tests.test_costing_rules aphvh.tests.test_vn_words aphvh.tests.test_print_formats -v
