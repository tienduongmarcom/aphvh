"""Entrypoint and static assets for the isolated UAT HTTP/Desk runner only."""
from pathlib import Path
from frappe import app
from werkzeug.middleware.shared_data import SharedDataMiddleware
app._site = 'aphvh-web-uat'
# Production nginx is not involved. Assets resolve inside this disposable container.
assets = Path('/home/frappe/frappe-bench/sites/assets')
application = SharedDataMiddleware(app.application, {'/assets': str(assets)})
