"""Thử lại toàn RPC tiền khi MariaDB báo xung đột snapshot/khóa."""
from functools import wraps
import time


def retry_rpc(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        import frappe
        form = getattr(getattr(frappe, "local", None), "form_dict", {}) or {}
        # Không rollback phần việc của caller nếu service được gọi bên trong
        # một nghiệp vụ lớn hơn. Chỉ retry ở biên RPC do chính module phục vụ.
        if form.get("cmd") != function.__module__ + "." + function.__name__:
            return function(*args, **kwargs)
        for attempt in range(3):
            try:
                return function(*args, **kwargs)
            except frappe.QueryDeadlockError:
                # Toàn bộ JE/kết quả nhận trong lần này cùng rollback; không
                # commit giữa chuỗi hoặc thử lại chỉ câu SQL trên snapshot cũ.
                frappe.db.rollback()
                if attempt == 2:
                    raise
                time.sleep(0.05 * (attempt + 1))
    return wrapped
