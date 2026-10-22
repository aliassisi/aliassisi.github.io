#!/usr/bin/env python3
"""Load every page in headless Chrome and list the files it asks for.

Usage:
  python3 -I .github/scripts/runtime_check.py SITE_DIR OUT.json [--widths 1280,420]
  python3 -I .github/scripts/runtime_check.py --compare BEFORE.json AFTER.json

Static scans miss files that scripts load at run time. This one sees them.
It serves SITE_DIR on a free port, opens each page, and records every request
with its status. OUT.json has "missing" (404s, per page and width) and "used"
(all files that were served).
--compare prints 404s that are in AFTER but not in BEFORE. Exit 1 if any.
"""
import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

CHROME = os.environ.get(
    "CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


def compare(before, after):
    b, a = json.load(open(before)), json.load(open(after))
    new = {}
    for key, paths in a["missing"].items():
        extra = sorted(set(paths) - set(b["missing"].get(key, [])))
        if extra:
            new[key] = extra
    for key, extra in new.items():
        print(key)
        for p in extra:
            print("   new 404:", p)
    print(f"{sum(len(v) for v in new.values())} new 404(s)")
    return 1 if new else 0


def main():
    if sys.argv[1] == "--compare":
        return compare(sys.argv[2], sys.argv[3])
    site, out = os.path.abspath(sys.argv[1]), sys.argv[2]
    widths = [1280, 420]
    if "--widths" in sys.argv:
        widths = [int(w) for w in sys.argv[sys.argv.index("--widths") + 1].split(",")]

    log, lock = [], threading.Lock()

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            code = args[1] if len(args) > 1 else "0"
            with lock:
                log.append((self.path.split("?")[0], str(code)))

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=site))
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    pages = []
    for dp, dirs, files in os.walk(site):
        if os.path.relpath(dp, site) == ".":
            dirs[:] = [d for d in dirs if d not in {".git", ".github", ".claude", "pagefind"}]
        if "index.html" in files:
            pages.append("/" + os.path.relpath(dp, site).replace(os.sep, "/").replace(".", "", 1).lstrip("/"))
    pages = sorted({p if p.endswith("/") else p + "/" for p in pages})

    def run(job):
        page, width = job
        url = f"http://127.0.0.1:{port}{page}"
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             f"--window-size={width},1800", "--virtual-time-budget=6000",
             f"--user-data-dir=/tmp/rc-{os.getpid()}-{threading.get_ident()}",
             "--dump-dom", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120,
        )

    jobs = [(p, w) for p in pages for w in widths]
    print(f"{len(pages)} pages x {len(widths)} widths on port {port}", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(run, jobs))
    server.shutdown()

    missing = sorted({p for p, c in log if c == "404" and p.startswith("/assets/")})
    used = sorted({p for p, c in log if c.startswith(("2", "3")) and p.startswith("/assets/")})
    # Per-page attribution is not possible with parallel loads. Keep one list.
    result = {"missing": {"all": missing}, "used": used}
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print(f"{len(used)} assets used, {len(missing)} missing under /assets/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
