"""Dấu vân chỉ đọc của core; chạy trong image nền và ứng viên, không khởi tạo site."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat


def snapshot(root):
    root = Path(root)
    result = {}
    for app in ("frappe", "erpnext"):
        base = root / app
        if not base.is_dir() or base.is_symlink():
            raise ValueError("Thiếu thư mục core thật: " + app)
        count = 0
        for folder, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in (".git", "__pycache__"))
            links = [d for d in dirs if (Path(folder) / d).is_symlink()]
            dirs[:] = [d for d in dirs if d not in links]
            for name in sorted(files + links):
                if name.endswith((".pyc", ".pyo")):
                    continue
                p = Path(folder) / name
                key = p.relative_to(root).as_posix()
                mode = stat.S_IMODE(p.lstat().st_mode)
                if p.is_symlink():
                    result[key] = {"link": os.readlink(p), "mode": mode}
                elif p.is_file():
                    h = hashlib.sha256()
                    with p.open("rb") as f:
                        for block in iter(lambda: f.read(1024 * 1024), b""):
                            h.update(block)
                    result[key] = {"sha256": h.hexdigest(), "mode": mode}
                else:
                    raise ValueError("Kiểu tệp core không hỗ trợ: " + key)
                count += 1
        if not count:
            raise ValueError("Core rỗng: " + app)
    return result


def compare(before, after):
    if not before or not after:
        raise ValueError("Không chấp nhận dấu vân rỗng")
    return {"added": sorted(after.keys() - before.keys()),
            "removed": sorted(before.keys() - after.keys()),
            "changed": sorted(k for k in before.keys() & after.keys() if before[k] != after[k])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apps", default="/home/frappe/frappe-bench/apps")
    p.add_argument("--compare", nargs=2, metavar=("NEN", "UNG_VIEN"))
    args = p.parse_args()
    if args.compare:
        before, after = [json.loads(Path(f).read_text()) for f in args.compare]
        diff = compare(before, after)
        ok = not any(diff.values())
        print(json.dumps({"case": "CORE_IMAGE_INTEGRITY", "status": "PASS" if ok else "FAIL",
                          "files": len(after), **diff}, ensure_ascii=False))
        return 0 if ok else 1
    print(json.dumps(snapshot(args.apps), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
