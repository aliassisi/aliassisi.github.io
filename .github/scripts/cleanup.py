#!/usr/bin/env python3
"""Turn the raw wget mirror into a clean static site.

Usage: python3 -I scripts/cleanup.py RAW_DIR PMAP_TSV OUT_DIR DOMAIN

RAW_DIR   the folder wget wrote (raw/<domain>)
PMAP_TSV  lines of "<id>\t<status> <permalink url>" for each /?p=ID short link
OUT_DIR   the folder to create (it is deleted first)
DOMAIN    the preview domain to strip from links
"""
import os
import re
import shutil
import sys
from urllib.parse import urlparse

raw, pmap_file, out, domain = sys.argv[1:5]
# Custom domain for GitHub Pages. None serves the site at https://aliassisi.github.io/.
# Set it (e.g. "aliassisi.it") at go-live, once the DNS points at GitHub.
PAGES_DOMAIN = None
TEXT_EXT = (".html", ".css", ".js")
ASSET_EXT = r"css|js|woff2?|ttf|eot|svg|png|jpe?g|gif|webp"


def read(path):
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(text)


# Cart and checkout pages under other slugs. They cannot work without WooCommerce.
DROP_DIRS = {"pagamento", "en/basket-2"}

# 1. Copy the mirror. Skip the /?p=ID duplicates. Strip "?query" from file names.
shutil.rmtree(out, ignore_errors=True)
renamed = 0
for dirpath, _, files in os.walk(raw):
    rel_dir = os.path.relpath(dirpath, raw)
    os.makedirs(os.path.join(out, rel_dir), exist_ok=True)
    for name in files:
        if name.startswith("index.html?p="):
            continue
        if os.path.normpath(rel_dir) in DROP_DIRS:
            continue
        clean = name.split("?", 1)[0]
        if clean != name:
            renamed += 1
        dest = os.path.join(out, rel_dir, clean)
        if not os.path.exists(dest):
            shutil.copy2(os.path.join(dirpath, name), dest)
print(f"copied mirror, renamed {renamed} files with a query string")

# 2. Map short-link id -> real page file (root-relative, ending in index.html).
id_target, missing = {}, []
for line in read(pmap_file).splitlines():
    pid, rest = line.split("\t")
    status, _, url = rest.partition(" ")
    path = urlparse(url).path
    target = path.lstrip("/") + ("index.html" if path.endswith("/") else "")
    if status == "301" and os.path.isfile(os.path.join(out, target)):
        id_target[pid] = target
    else:
        missing.append((pid, url))
print(f"short links: {len(id_target)} mapped, {len(missing)} without a page")
for pid, url in missing:
    print("  no page for", pid, url)

# 3. Rewrite every text file.
P_LINK = re.compile(r"((?:\.\./)*)index\.html(?:%3F|\?)p=(\d+)\.html")
ABS = re.compile(r"https?://" + re.escape(domain) + r"(/[^\s\"'<>)\\]*)?")
ABS_ESC = "https:\\/\\/" + domain
# Only the encoded form ("file.css%3Fver=1", written by wget). A literal "?" is
# left alone: servers ignore it, and in JS it can be code (e.g. "i.svg?a:b").
ASSET_QUERY = re.compile(r"(\.(?:%s))%%3F(?:ver=)?[\w.\-]*" % ASSET_EXT)
DROP_LINK = re.compile(
    r"<link\b[^>]*(?:wp-json|/feed/|xmlrpc|rel=['\"](?:shortlink|EditURI|canonical)['\"]"
    r"|hreflang=|rel=['\"]https://api\.w\.org/['\"])[^>]*>\s*",
    re.I,
)
DROP_META = re.compile(r"<meta\b[^>]*property=['\"]og:url['\"][^>]*>\s*", re.I)

# Links the live site sends to the wrong place. The live server redirects /en/,
# and /product-category/intensive/ is a 404 (the real slug is "intensivi").
REDIRECTS = {
    "en/index.html": "en/home/index.html",
    "product-category/intensive/index.html": "product-category/intensivi/index.html",
}
ATTR = re.compile(r'\b(href|src)="([^"#?]*)([#?][^"]*)?"')
AUTHOR = re.compile(r'\bhref="[^"]*(?:^|/)author/[^"]*"')


def fix_links(text, here, self_path):
    def fix(m):
        attr, value, tail = m.group(1), m.group(2), m.group(3) or ""
        if not value or re.match(r"[a-z][a-z0-9+.-]*:", value, re.I):
            return m.group(0)
        target = os.path.normpath(os.path.join(here, value))
        if value.endswith("/") or os.path.basename(value) in (".", ".."):
            target = os.path.join(target, "index.html")
        # wget turns href="#" into "<this page>#". Elementor's menu needs "#".
        if attr == "href" and target == self_path and tail.startswith("#"):
            return f'href="{tail}"'
        new = REDIRECTS.get(target)
        if new is None:
            return m.group(0)
        return f'{attr}="{os.path.relpath(new, here)}{tail}"'

    text = AUTHOR.sub('href="#"', text)
    return ATTR.sub(fix, text)

SEARCH_PAGES = {"it": "search/index.html", "en": "en/search/index.html"}
SEARCH_FORM = re.compile(r'(<form class="elementor-search-form") action="[^"]*"')


def point_search_forms(text, here):
    lang = "en" if re.search(r'<html[^>]*\blang="en', text) else "it"
    page = os.path.relpath(SEARCH_PAGES[lang], here)
    return SEARCH_FORM.sub(rf'\1 action="{page}"', text)


SEARCH_HTML = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link href="{up}pagefind/pagefind-ui.css" rel="stylesheet">
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem}}</style>
</head>
<body data-pagefind-ignore>
<p><a href="{home}">&larr; {back}</a></p>
<h1>{title}</h1>
<div id="search"></div>
<script src="{up}pagefind/pagefind-ui.js"></script>
<script>
window.addEventListener("DOMContentLoaded", function () {{
  var ui = new PagefindUI({{ element: "#search", showSubResults: true, autofocus: true }});
  var q = new URLSearchParams(location.search).get("s");
  if (q) ui.triggerSearch(q);
}});
</script>
</body>
</html>
"""
for lang, path, home, title, back in [
    ("it-IT", "search/index.html", "../index.html", "Cerca", "Torna alla home"),
    ("en-GB", "en/search/index.html", "../home/index.html", "Search", "Back to home"),
]:
    full = os.path.join(out, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    up = "../" * path.count("/")
    write(full, SEARCH_HTML.format(lang=lang, title=title, up=up, home=home, back=back))

unmapped = set()
for dirpath, _, files in os.walk(out):
    for name in files:
        if not name.endswith(TEXT_EXT):
            continue
        path = os.path.join(dirpath, name)
        text = read(path)
        here = os.path.relpath(dirpath, out)

        def short(m):
            target = id_target.get(m.group(2))
            if target is None:
                unmapped.add(m.group(2))
                return m.group(0)
            return m.group(1) + target

        if name.endswith(".html"):
            text = DROP_LINK.sub("", text)
            text = DROP_META.sub("", text)
        text = P_LINK.sub(short, text)
        text = ASSET_QUERY.sub(r"\1", text)
        text = text.replace(ABS_ESC, "")

        def rel(m):
            p = m.group(1) or "/"
            bare = re.split(r"[?#]", p, maxsplit=1)[0]
            tail = p[len(bare):]
            if bare.endswith("/"):
                bare += "index.html"
            r = os.path.relpath(bare.lstrip("/"), here)
            return r + tail

        text = ABS.sub(rel, text)
        text = text.replace("//" + domain, "")  # protocol-relative, e.g. slider lazyload
        if name.endswith(".html"):
            text = fix_links(text, here, os.path.normpath(os.path.relpath(path, out)))
            text = point_search_forms(text, here)
        write(path, text)

if unmapped:
    print("short-link ids with no page (left as is):", sorted(unmapped))
# GitHub Pages: skip the Jekyll build, and serve the site on its own domain.
write(os.path.join(out, ".nojekyll"), "")
if PAGES_DOMAIN:
    write(os.path.join(out, "CNAME"), PAGES_DOMAIN + "\n")
print("done")
