#!/usr/bin/env python3
"""Find links in the site that point at files that do not exist.

Usage:
  python3 -I .github/scripts/check_links.py SITE_DIR
  python3 -I .github/scripts/check_links.py SITE_DIR --hook   # Claude Code hook

Targets listed in known_broken.txt (next to this script) are allowed.
Exit 1 if there is a new missing target. In --hook mode the exit code is 2,
so the agent sees the message on stderr. The hook only runs for .html and
.css files.
"""
import json
import os
import posixpath
import re
import sys
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
ATTR = re.compile(r"""\b(?:href|src|data-lazyload|data-mp4)=["']([^"'#?]+)""")
CSS_URL = re.compile(r"""url\(["']?([^"')?#]+)""")
# Root-relative paths inside inline JSON, in three forms: plain, "\/" and
# inside HTML-escaped JSON (&quot;...&quot;).
JSON_PATH = re.compile(r"""(?<![\w.\-])(?:\\/|/)assets(?:\\/|/)[^"'\s)?#<>,&\\]+(?:\\/[^"'\s)?#<>,&\\]+)*""")
EXTERNAL = re.compile(r"[a-z][a-z0-9+.-]*:|//|data:|mailto:", re.I)


def known():
    path = os.path.join(HERE, "known_broken.txt")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {
            line.split("#")[0].strip()
            for line in f
            if line.split("#")[0].strip()
        }


def pages(site):
    for dirpath, dirs, files in os.walk(site):
        rel = os.path.relpath(dirpath, site)
        if rel == ".":
            dirs[:] = [d for d in dirs if d not in {".git", ".github", ".claude", "pagefind"}]
        for name in files:
            if name.endswith((".html", ".css")):
                yield os.path.join(dirpath, name)


def targets(site, path):
    here = os.path.relpath(os.path.dirname(path), site).replace(os.sep, "/")
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    found = []
    if path.endswith(".css"):
        found = [(v, False) for v in CSS_URL.findall(text)]
    else:
        found = [(v, False) for v in ATTR.findall(text)]
        found += [(v.replace("\\/", "/"), True) for v in JSON_PATH.findall(text)]
    for value, rooted in found:
        if EXTERNAL.match(value):
            continue
        value = unquote(value)
        if rooted or value.startswith("/"):
            tgt = posixpath.normpath(value.lstrip("/"))
        else:
            tgt = posixpath.normpath(posixpath.join(here, value))
        if value.endswith("/"):
            tgt += "/index.html"
        yield tgt


def check(site, files):
    missing = {}
    for path in files:
        for tgt in set(targets(site, path)):
            if not os.path.exists(os.path.join(site, tgt)):
                missing.setdefault(tgt, []).append(os.path.relpath(path, site))
    return missing


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hook = "--hook" in sys.argv
    site = os.path.abspath(args[0]) if args else os.getcwd()
    files = None
    if hook:
        try:
            event = json.load(sys.stdin)
        except ValueError:
            return 0
        edited = (event.get("tool_input") or {}).get("file_path", "")
        if not edited.endswith((".html", ".css")) or not os.path.isfile(edited):
            return 0
        if not os.path.abspath(edited).startswith(site + os.sep):
            return 0
        files = [edited]
    missing = check(site, files if files is not None else pages(site))
    allowed = known()
    new = {t: p for t, p in missing.items() if t not in allowed}
    for tgt, where in sorted(new.items(), key=lambda x: -len(x[1])):
        print(f"{len(where):4d} missing {tgt}  (e.g. {where[0]})", file=sys.stderr if hook else sys.stdout)
    if not hook:
        print(f"{len(new)} new missing target(s), {len(missing) - len(new)} known")
    return (2 if hook else 1) if new else 0


if __name__ == "__main__":
    sys.exit(main())
