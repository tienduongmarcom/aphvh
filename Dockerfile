# Bản cài ERPNext có kèm app aphvh.
# Dựng:  docker build -t aphvh-erpnext:0.6.2 .
# ERPNEXT_IMAGE phải trùng phiên bản ERPNext đang chạy (hiện là v16.36.1).
ARG ERPNEXT_IMAGE=frappe/erpnext:v16.36.1
FROM ${ERPNEXT_IMAGE}

USER frappe
WORKDIR /home/frappe/frappe-bench

# 0.7.0: hai app: lõi 9xLab (lab9x, nằm ở apps/lab9x của repo) và app riêng của khách (aphvh).
COPY --chown=frappe:frappe apps/lab9x apps/lab9x
COPY --chown=frappe:frappe . apps/aphvh

# Tệp JS của app nạp qua hook doctype_js (đọc thẳng từ thư mục app), không cần build asset: chỉ cần đưa thư mục app vào đường dẫn
# import của môi trường Python của bench (tương đương cài "editable"), không cần mạng.
# Ghi aphvh vào sites/apps.txt của bản dựng để `bench version` và site mới trên ổ trống đều thấy app
# (site đang chạy đọc apps.txt trong ổ dữ liệu sites của nó).
RUN rm -rf apps/aphvh/apps \
 && SITE_PACKAGES="$(./env/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
 && echo "/home/frappe/frappe-bench/apps/lab9x" > "${SITE_PACKAGES}/lab9x.pth" \
 && echo "/home/frappe/frappe-bench/apps/aphvh" > "${SITE_PACKAGES}/aphvh.pth" \
 && sed -i -e '$a\' sites/apps.txt \
 && (grep -qx lab9x sites/apps.txt || echo lab9x >> sites/apps.txt) \
 && (grep -qx aphvh sites/apps.txt || echo aphvh >> sites/apps.txt) \
 && ./env/bin/python -c "import lab9x, lab9x.hooks, aphvh, aphvh.hooks, aphvh.costing_rules; print('lab9x', lab9x.__version__, 'aphvh', aphvh.__version__)" \
 && (cd apps/lab9x && ../../env/bin/python -m unittest discover -s lab9x/tests -t . -v) \
 && (cd apps/aphvh && ../../env/bin/python -m unittest discover -s aphvh/tests -t . -v)
