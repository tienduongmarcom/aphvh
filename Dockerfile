# Bản cài ERPNext có kèm app kh_aph.
# Dựng:  docker build -t kh-aph-erpnext:0.8.0 .
# ERPNEXT_IMAGE phải trùng phiên bản ERPNext đang chạy (hiện là v16.36.1).
ARG ERPNEXT_IMAGE=frappe/erpnext@sha256:ac5b4591e80b52d2e22f6f5cad5d5e7e300f9764dbfeb3f92d325e86baede08d
# = ERPNext 16.50.0 + Frappe 16.51.0 (ghim theo digest từ 0.11.0; đổi nền = PR riêng, qua đủ các cổng)
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
