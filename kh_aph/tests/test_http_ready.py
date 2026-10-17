"""Kiểm HTTP thật ở localhost: khởi động chậm và phản hồi giả thành công."""
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

spec = importlib.util.spec_from_file_location("cho_http", Path(__file__).resolve().parents[2] / "deploy/release/cho_http.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HttpReady(unittest.TestCase):
    def serve(self, responses):
        self.requests = 0
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                status, body = responses[min(owner.requests, len(responses)-1)]
                owner.requests += 1
                self.send_response(status)
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def cleanup():
            server.shutdown()
            server.server_close()
            thread.join()
        self.addCleanup(cleanup)
        return f"http://127.0.0.1:{server.server_port}/api/method/ping"

    def test_startup_503_then_ready(self):
        url = self.serve([(503, b"maintenance"), (200, b'{"message":"pong"}')])
        module.cho(url, timeout=1, interval=0.01)
        self.assertEqual(self.requests, 2)

    def test_permanent_503_is_not_pass(self):
        url = self.serve([(503, b"maintenance")])
        with self.assertRaises(RuntimeError):
            module.cho(url, timeout=0.05, interval=0.01)

    def test_200_wrong_body_is_not_pass(self):
        url = self.serve([(200, b'{"message":"not ready"}')])
        with self.assertRaises(RuntimeError):
            module.cho(url, timeout=0.05, interval=0.01)
