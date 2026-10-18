"""Chờ endpoint ping sẵn sàng có hạn chót; 200 phải trả đúng message=pong."""
import argparse
import json
import time
import urllib.error
import urllib.request


def cho(url, timeout=180, interval=2):
    deadline = time.monotonic() + timeout
    last = "chưa có phản hồi"
    while True:
        try:
            with urllib.request.urlopen(url, timeout=min(5, max(0.1, deadline-time.monotonic()))) as response:
                data = json.loads(response.read(4096))
                if response.status == 200 and data == {"message": "pong"}:
                    return
                last = "Phản hồi không phải ping pong"
        except urllib.error.HTTPError as exc:
            last = "HTTP " + str(exc.code)
        except (OSError, ValueError) as exc:
            last = type(exc).__name__
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("Web chưa sẵn sàng trong hạn chót: " + last)
        time.sleep(min(interval, remaining))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    cho(args.url, args.timeout)
    print("HTTP_READY: ĐẠT (200, message=pong)")
