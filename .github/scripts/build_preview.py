#!/usr/bin/env python3
"""Build a pull request preview from the site in SRC.

Usage:
  python3 -I .github/scripts/build_preview.py SRC DST BASE \
      --prod-url https://aliassisi.github.io --changed-file changed.txt

BASE is the folder the preview is served from, e.g. /pr-preview/pr-12/

The site uses paths that start at the domain root ("/wp-content/..."). In a
preview these must start at BASE instead. Media in wp-content/uploads is large,
so the preview only copies the files the PR changed. Every other media file is
loaded from production.

Only .html and .css files are rewritten. JavaScript is never touched.
"""
import argparse
import os
import re
import shutil
import sys
from urllib.parse import unquote

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("base")
ap.add_argument("--prod-url", required=True)
ap.add_argument("--changed-file", required=True)
args = ap.parse_args()

src, dst = args.src, args.dst
base = "/" + args.base.strip("/") + "/"
base_esc = base.replace("/", "\\/")
prod = args.prod_url.rstrip("/")
prod_esc = prod.replace("/", "\\/")
UPLOADS = "wp-content/uploads"
SKIP_TOP = {".git", ".github", "_site", "_preview"}

changed = {
    line.strip()
    for line in open(args.changed_file, encoding="utf-8", errors="ignore")
    if line.strip()
}

# 1. Copy the site. Leave out uploads, except the files this PR changed.
shutil.rmtree(dst, ignore_errors=True)
copied_uploads = 0
for dirpath, dirnames, filenames in os.walk(src):
    rel_dir = os.path.relpath(dirpath, src)
    if rel_dir == ".":
        dirnames[:] = [d for d in dirnames if d not in SKIP_TOP]
    for name in filenames:
        rel = os.path.normpath(os.path.join(rel_dir, name))
        in_uploads = rel.startswith(UPLOADS + os.sep)
        if in_uploads and rel not in changed:
            continue
        if in_uploads:
            copied_uploads += 1
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copy2(os.path.join(dirpath, name), out)
print(f"copied the site; {copied_uploads} changed upload file(s) included")

# Top-level names the site really has. Only paths that start with one of them
# are moved under BASE. Anything else (e.g. /wp-admin/) is left alone.
tops = sorted(
    {
        n
        for n in os.listdir(dst)
        if not n.startswith(".") and n not in ("CNAME",)
    }
    | {"wp-content", "wp-includes"},
    key=len,
    reverse=True,
)
TOP = "|".join(re.escape(os.path.splitext(n)[0] if n.endswith(".html") else n) for n in tops)

# A media reference: optional "../" steps or a leading slash, then
# wp-content/uploads/<path>. The path ends at a quote, space, ? # ) or comma.
# The lookbehind skips URLs that already point at production.
MEDIA = re.compile(
    r"(?<![\w:/.])(?:(?:\.\./)+|/)?wp-content/uploads/([^\"'\s)?#<>,\\]+)"
)
MEDIA_ESC = re.compile(
    r"(?:(?:\.\.(?:\\/|/))+|\\/)?wp-content\\/uploads\\/"
    r"([^\"'\s)?#<>,\\]+(?:\\/[^\"'\s)?#<>,\\]+)*)"
)
# Root-relative paths: after a quote or "(", and the escaped form in JSON.
ROOT = re.compile(r"(?<=[\"'(])/(?=(?:%s)(?:[/\"'?#)]|$))" % TOP)
ROOT_ESC = re.compile(r"(?<=\")\\/(?=(?:%s)(?:\\/|/|\"))" % TOP)
HEAD = re.compile(r"<head\b[^>]*>", re.I)
NOINDEX = '<meta name="robots" content="noindex">'


def exists(path):
    return os.path.isfile(os.path.join(dst, UPLOADS, unquote(path)))


def media(m):
    path = m.group(1)
    if exists(path):
        return m.group(0)  # in the preview; the root rule fixes a leading slash
    return f"{prod}/{UPLOADS}/{path}"


def media_esc(m):
    path = m.group(1).replace("\\/", "/")
    if exists(path):
        return m.group(0)
    return f"{prod_esc}\\/wp-content\\/uploads\\/{m.group(1)}"


# A relative url() in a stylesheet, e.g. url("../../2026/10/a.jpg").
CSS_REL = re.compile(r"""url\(\s*(["']?)(?![a-z][a-z0-9+.-]*:|/|#|data:)([^"')]+?)\1\s*\)""", re.I)


def css_relative(css_path):
    """Send relative urls to omitted uploads to production.

    The browser resolves these against the stylesheet. If the target is in
    uploads and was not copied, the preview would answer 404.
    """
    css_dir = os.path.relpath(os.path.dirname(css_path), dst)

    def fix(m):
        ref = m.group(2)
        target = os.path.normpath(os.path.join(css_dir, unquote(re.split(r"[?#]", ref)[0])))
        if target.startswith(UPLOADS + os.sep) and not os.path.isfile(os.path.join(dst, target)):
            return f'url("{prod}/{target}")'
        return m.group(0)

    return fix


rewritten = 0
for dirpath, _, filenames in os.walk(dst):
    for name in filenames:
        if not name.endswith((".html", ".css")):
            continue
        path = os.path.join(dirpath, name)
        text = open(path, encoding="utf-8", errors="surrogateescape").read()
        new = text
        if name.endswith(".css"):
            new = CSS_REL.sub(css_relative(path), new)
        new = MEDIA_ESC.sub(media_esc, new)
        new = MEDIA.sub(media, new)
        new = ROOT_ESC.sub(lambda m: base_esc, new)
        new = ROOT.sub(lambda m: base, new)
        if name.endswith(".html") and NOINDEX not in new:
            new = HEAD.sub(lambda m: m.group(0) + NOINDEX, new, count=1)
        if new != text:
            rewritten += 1
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
                f.write(new)
print(f"rewrote {rewritten} file(s)")

# 2. Fail if a page still points at the domain root for site files.
LEFT = re.compile(r"(?<=[\"'(])/wp-(?:content|includes)/|(?<=\")\\/wp-(?:content|includes)\\/")
bad = []
for dirpath, _, filenames in os.walk(dst):
    for name in filenames:
        if name.endswith(".html"):
            p = os.path.join(dirpath, name)
            if LEFT.search(open(p, encoding="utf-8", errors="surrogateescape").read()):
                bad.append(os.path.relpath(p, dst))
if bad:
    print(f"ERROR: {len(bad)} page(s) still use root-relative site paths:", file=sys.stderr)
    for b in bad[:10]:
        print("  ", b, file=sys.stderr)
    sys.exit(1)
print("check passed")
