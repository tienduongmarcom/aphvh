# Bản cài ERPNext có kèm app kh_aph.
# Dựng:  docker build -t kh-aph-erpnext:0.8.0 .
# ERPNEXT_IMAGE phải trùng phiên bản ERPNext đang chạy (ứng viên 16.51.1; kiểm Frappe đi kèm trong CI, ghim digest bên dưới).
ARG ERPNEXT_IMAGE=frappe/erpnext@sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268
# = ERPNext 16.51.1; phiên bản Frappe ghi bởi bench version trong CI (ứng viên nâng nền từ 0.14.4; đổi nền = PR riêng, qua đủ các cổng)
FROM ${ERPNEXT_IMAGE}

USER frappe
WORKDIR /home/frappe/frappe-bench

# 0.7.0: hai app: lõi 9xLab (lab9x, nằm ở apps/lab9x của repo) và app riêng của khách (kh_aph).
COPY --chown=frappe:frappe apps/lab9x apps/lab9x
COPY --chown=frappe:frappe . apps/kh_aph

# Tệp JS của app nạp qua hook doctype_js (đọc thẳng từ thư mục app), không cần build asset: chỉ cần đưa thư mục app vào đường dẫn
# import của môi trường Python của bench (tương đương cài "editable"), không cần mạng.
# Ghi kh_aph vào sites/apps.txt của bản dựng để `bench version` và site mới trên ổ trống đều thấy app
# (site đang chạy đọc apps.txt trong ổ dữ liệu sites của nó).
RUN rm -rf apps/kh_aph/apps \
 && SITE_PACKAGES="$(./env/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
 && echo "/home/frappe/frappe-bench/apps/lab9x" > "${SITE_PACKAGES}/lab9x.pth" \
 && echo "/home/frappe/frappe-bench/apps/kh_aph" > "${SITE_PACKAGES}/kh_aph.pth" \
 && sed -i -e '$a\' sites/apps.txt \
 && (grep -qx lab9x sites/apps.txt || echo lab9x >> sites/apps.txt) \
 && (grep -qx kh_aph sites/apps.txt || echo kh_aph >> sites/apps.txt) \
 && ./env/bin/python -c "import lab9x, lab9x.hooks, kh_aph, kh_aph.hooks, lab9x.costing_rules; print('lab9x', lab9x.__version__, 'kh_aph', kh_aph.__version__)" \
 && (cd apps/lab9x && ../../env/bin/python -m unittest discover -s lab9x/tests -t . -v) \
 && (cd apps/kh_aph && ../../env/bin/python -m unittest discover -s kh_aph/tests -t . -v)
