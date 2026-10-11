"""Entrypoint used only by the isolated UAT HTTP runner."""
from frappe import app
app._site = 'aphvh-web-uat'
application = app.application
