#!/usr/bin/env python3
"""Strip WordPress leftovers from the cleaned static site.

Usage: python3 -I .github/scripts/postprocess.py SITE_DIR

Run it after cleanup.py, on the folder cleanup.py wrote. It edits SITE_DIR in
place. Steps: drop junk pages, merge wget duplicates, remove backend-only
scripts, scrub WordPress config, map old links, move wp-content and
wp-includes under assets/, and delete files nothing uses.
"""
import os
import posixpath
import re
import shutil
import sys

site = sys.argv[1]
TEXT_EXT = (".html", ".css", ".js")


def read(path):
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(text)


def text_files():
    for dirpath, _, files in os.walk(site):
        if os.path.relpath(dirpath, site).split(os.sep)[0] == "pagefind":
            continue
        for name in files:
            if name.endswith(TEXT_EXT):
                yield os.path.join(dirpath, name)


# 1. Drop test pages, shop listings, archives and old calendars.
DROP_DIRS = [
    "prova", "prova-3", "prove-tecniche", "vecchi-calendari",
    "en/coming-soon", "en/privacy-policy-2",
    "negozio", "shop", "en/basket",
    "category/uncategorized", "en/category/senza-categoria-en",
    "product-tag", "en/product-tag",
    "product-category/corsi", "en/product-category/courses",
    "product/general-italian",
]
for d in DROP_DIRS:
    shutil.rmtree(os.path.join(site, d), ignore_errors=True)
print(f"dropped {len(DROP_DIRS)} folders")

# 2. wget wrote some pages twice: "x.html" next to "x/index.html".
# Menus link to the .html copy. Point them at the folder copy.
MERGE = {
    "method.html": "method/index.html",
    "accommodation.html": "accommodation/index.html",
    "en/accommodation.html": "en/accommodation/index.html",
    "product/private.html": "product/private/index.html",
    "en/product/private.html": "en/product/private/index.html",
    "product-category/intensivi.html": "product-category/intensivi/index.html",
}

# 3. Old links to the WordPress site that still have a page here.
OLD_SITE = re.compile(r"https?://(?:www\.)?aliassisi\.it(/[^\s\"'<>)\\]*)?")
OLD_MAP = {
    "/en/method/": "en/method/index.html",
    "/angelo-chiuchiu/": "method/index.html",
    "/courses/italian-language-courses/angelo-chiuchiu/": "method/index.html",
    "/en/angelo-chiuchiu/": "en/method/index.html",
    "/en/courses/italian-language-courses/faq/": "en/faq/index.html",
    "/en/courses/italian-language-courses/credits/": "en/certifications-exams-credits-levels/index.html",
    "/en/courses/italian-language-courses/activities/": "en/school-activity/index.html",
    "/en/courses/italian-language-courses/calendario/": "en/calendar-and-fees/index.html",
    "/en/courses/italian-language-courses/alloggio/": "en/accommodation/index.html",
    "/courses/italian-language-courses/credits/": "esami-di-certificazione-crediti-livelli/index.html",
    "/courses/italian-language-courses/activities/": "attivita-facilities-e-laboratori/index.html",
}

ATTR = re.compile(r'\b(href|src)="([^"#?]*)([#?][^"]*)?"')


def dropped(target):
    return any(target == d or target.startswith(d + "/") for d in DROP_DIRS)


def fix_links(text, here):
    def fix(m):
        attr, value, tail = m.group(1), m.group(2), m.group(3) or ""
        if not value or re.match(r"[a-z][a-z0-9+.-]*:", value, re.I):
            return m.group(0)
        target = posixpath.normpath(posixpath.join(here, value))
        if value.endswith("/"):
            target += "/index.html"
        if target in MERGE:
            return f'{attr}="{posixpath.relpath(MERGE[target], here)}{tail}"'
        if attr == "href" and dropped(target):
            return 'href="#"'
        return m.group(0)

    def old(m):
        path = m.group(1) or "/"
        new = OLD_MAP.get(path)
        if new is None:
            unmapped_old[path] = unmapped_old.get(path, 0) + 1
            return m.group(0)
        return posixpath.relpath(new, here)

    return OLD_SITE.sub(old, ATTR.sub(fix, text))


# 4. Scripts and styles that only make sense with a WordPress backend.
SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>\s*", re.S)
DEAD_SRC = re.compile(
    r"plugins/(?:woocommerce/assets/js/|woocommerce-bookings/|tablentor/|instagram-feed/)"
)
DEAD_BODY = (
    "wc_add_to_cart_params", "woocommerce_params", "wc_order_attribution",
    "wc_single_product_params", "sbiajaxurl", "wp-emoji-settings",
    "wp-emoji-loader", "_wpemojiSettings",
)
DEAD_LINK = re.compile(
    r"<link\b[^>]*href=['\"][^'\"]*plugins/(?:instagram-feed|woocommerce-bookings|tablentor)/[^>]*>\s*"
)
DEAD_STYLE = re.compile(
    r'<style id="(?:wp-emoji-styles|classic-theme-styles|wp-img-auto-sizes-contain)-inline-css">.*?</style>\s*',
    re.S,
)
INSTAGRAM_NOTE = re.compile(r"<!-- Instagram Feed JS -->\s*")


def drop_script(m):
    attrs, body = m.group(1), m.group(2)
    if "speculationrules" in attrs:
        return ""
    src = re.search(r'\bsrc="([^"]*)"', attrs)
    if src and DEAD_SRC.search(src.group(1)):
        return ""
    if not src and any(t in body for t in DEAD_BODY):
        return ""
    return m.group(0)


# 5. Markup that only WordPress needs.
GENERATOR = re.compile(r"[ \t]*<meta\b[^>]*name=\"generator\"[^>]*>\s*", re.I)
TILE = re.compile(r"[ \t]*<meta\b[^>]*name=\"msapplication-TileImage\"[^>]*>\s*", re.I)
SOURCE_URL = re.compile(r"^[ \t]*/[/*]# sourceURL=[^\n]*?(?: \*/)?[ \t]*\n", re.M)
CART_LINK = re.compile(r"<a\b[^>]*\badd_to_cart_button\b[^>]*>")


def clean_cart_link(m):
    tag = m.group(0)
    tag = re.sub(r' (?:data-quantity|data-product_id|data-product_sku|aria-describedby)="[^"]*"', "", tag)
    tag = re.sub(r"\badd_to_cart_button\b ?", "", tag)
    tag = re.sub(r"\bproduct_type_booking\b ?", "", tag)
    return re.sub(r'class="\s*([^"]*?)\s*"', lambda c: f'class="{c.group(1)}"', tag)


# Config that holds nonces and WordPress URLs. Blank the values.
NONCE = re.compile(r'("[A-Za-z_]*nonce"):"[^"]*"')
AJAX = re.compile(r'(\\?"?ajaxurl\\?"?:)\\?"[^"]*admin-ajax\.php\\?"')
REST = re.compile(r'("rest"):"[^"]*"')
JSPATH = re.compile(r'(jspath":"[^"]*/assets/js/)index\.html"')


def clean_config(text):
    text = NONCE.sub(r'\1:""', text)
    text = REST.sub(r'\1:""', text)
    text = JSPATH.sub(r'\1"', text)
    return AJAX.sub(r'\1""', text)


unmapped_old = {}
for path in text_files():
    if not path.endswith(".html"):
        continue
    here = os.path.relpath(os.path.dirname(path), site).replace(os.sep, "/")
    text = read(path)
    text = SCRIPT.sub(drop_script, text)
    text = DEAD_LINK.sub("", text)
    text = DEAD_STYLE.sub("", text)
    text = INSTAGRAM_NOTE.sub("", text)
    text = GENERATOR.sub("", text)
    text = TILE.sub("", text)
    text = SOURCE_URL.sub("", text)
    text = CART_LINK.sub(clean_cart_link, text)
    text = clean_config(text)
    text = fix_links(text, here)
    write(path, text)

for old in MERGE:
    p = os.path.join(site, old)
    if os.path.exists(p):
        os.remove(p)

# 6. Move wp-content and wp-includes under assets/. Each path shows up in
# three forms: plain, JSON-escaped ("\/") and inside HTML-escaped JSON.
MOVES = [
    ("wp-content/plugins", "assets/plugins"),
    ("wp-content/themes", "assets/themes"),
    ("wp-content/uploads", "assets/uploads"),
    ("wp-includes", "assets/core"),
]
for old, new in MOVES:
    os.makedirs(os.path.join(site, os.path.dirname(new)), exist_ok=True)
    shutil.move(os.path.join(site, old), os.path.join(site, new))
leftover = os.path.join(site, "wp-content")
if os.path.isdir(leftover):
    for name in os.listdir(leftover):
        print("wp-content has an extra entry, moved to assets/:", name)
        os.makedirs(os.path.join(site, "assets"), exist_ok=True)
        shutil.move(os.path.join(leftover, name), os.path.join(site, "assets", name))
    os.rmdir(leftover)
MOVE_RES = []
for old, new in MOVES:
    MOVE_RES.append((re.compile(re.escape(old)), new))
    MOVE_RES.append((re.compile(re.escape(old).replace("/", r"\\/")), new.replace("/", r"\/")))
for path in text_files():
    text = read(path)
    new_text = text
    for rx, new in MOVE_RES:
        new_text = rx.sub(lambda _m, n=new: n, new_text)
    if new_text != text:
        write(path, new_text)

# 7. Delete files nothing names. Elementor loads chunks at run time, so
# only core files and WooCommerce are checked.
corpus = "".join(read(p) for p in text_files())
removed = size = 0
for base in ("assets/core", "assets/plugins/woocommerce"):
    for dirpath, _, files in os.walk(os.path.join(site, base)):
        for name in files:
            full = os.path.join(dirpath, name)
            if name not in corpus:
                size += os.path.getsize(full)
                os.remove(full)
                removed += 1
print(f"removed {removed} unused files ({size // 1024} KB)")

# 8. Report what is left.
left = {k: 0 for k in ("wp-content", "wp-includes", "wp-json", "admin-ajax", "aliassisi.it")}
for path in text_files():
    text = read(path)
    for k in left:
        left[k] += text.count(k)
print("left over:", left)
if unmapped_old:
    print("old-site links with no page here (left as is):")
    for p, n in sorted(unmapped_old.items(), key=lambda x: -x[1]):
        print(f"  {n:4d} {p}")
