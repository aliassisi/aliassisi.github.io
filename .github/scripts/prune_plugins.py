#!/usr/bin/env python3
"""Delete plugin code and files the site does not use.

Usage: python3 -I .github/scripts/prune_plugins.py SITE_DIR

Safe to run twice. Run it after postprocess.py (it needs the assets/ layout).
Steps:
1. Delete plugins no page uses.
2. Keep one font format (woff2) in plugin CSS. Delete the other font files.
3. Delete script chunks for widgets no page uses, and editor-only chunks.
4. Delete WooCommerce files only the admin or the checkout page needs.

Check the result with runtime_check.py. Static scans miss files that scripts
load at run time.
"""
import os
import re
import sys

site = sys.argv[1]
plugins = os.path.join(site, "assets", "plugins")
DROP_PLUGINS = ["tablentor", "instagram-feed", "woocommerce-bookings"]
FONT_EXT = (".eot", ".ttf", ".woff", ".svg", ".otf")
# Chunk names (the part before ".<hash>.bundle.min.js") that no page needs.
# Names not listed here stay, so do the unnamed shared chunks.
DENY_CHUNKS = {
    "elementor": [
        "accordion", "alert", "contact-buttons", "container-editor-handlers",
        "counter", "floating-bars", "nested-accordion", "nested-tabs",
        "nested-title-keyboard-handler", "progress", "section-editor-handlers",
        "shared-editor-handlers", "tabs", "text-path", "wp-audio",
    ],
    "pro-elements": [
        "ajax-pagination", "animated-headline", "archive-posts", "code-highlight",
        "contact-buttons-var-10", "contact-buttons", "countdown",
        "floating-bars-var-2", "floating-bars-var-3", "gallery", "hotspot",
        "loop-carousel", "loop", "lottie", "media-carousel", "mega-menu-stretch-content",
        "mega-menu", "nested-carousel", "off-canvas", "paypal-button", "portfolio",
        "product-add-to-cart", "progress-tracker", "search", "slides", "social",
        "stripe-button", "table-of-contents", "taxonomy-filter", "video-playlist",
        "woocommerce-cart", "woocommerce-checkout-page", "woocommerce-menu-cart",
        "woocommerce-my-account", "woocommerce-notices", "woocommerce-purchase-summary",
    ],
}
# WooCommerce files the site has no use for: the admin script, and the card
# icons that only checkout styles use. Paths are under assets/plugins.
DROP_FILES = [
    "woocommerce/assets/client/admin/sanitize/index.js",
]
DROP_DIRS = ["woocommerce/assets/images/icons/credit-cards"]
CARD_RULE = re.compile(r"[^{}]*\{[^{}]*credit-cards/[^{}]*\}")
CHUNK = re.compile(r"^(?P<name>.+)\.[0-9a-f]{20}\.bundle\.min\.js$")
FONT_FACE = re.compile(r"@font-face\s*\{[^}]*\}")
SRC_DECL = re.compile(r"\bsrc\s*:[^;}]*;?", re.I)
URL = re.compile(r"url\(\s*['\"]?([^)'\"]*?)['\"]?\s*\)")

saved = {}


def drop(path, plugin):
    saved[plugin] = saved.get(plugin, 0) + os.path.getsize(path)
    os.remove(path)


def plugin_of(path):
    return os.path.relpath(path, plugins).split(os.sep)[0]


# 1. Plugins no page uses.
for name in DROP_PLUGINS:
    folder = os.path.join(plugins, name)
    for dp, _, files in os.walk(folder):
        for f in files:
            drop(os.path.join(dp, f), name)
    if os.path.isdir(folder):
        import shutil
        shutil.rmtree(folder)

# 2. One font format. Rewrite each @font-face to point at its woff2 file.
no_woff2 = []


def one_format(match):
    block = match.group(0)
    urls = URL.findall(block)
    woff2 = [u for u in urls if re.search(r"\.woff2(?:$|[?#])", u)]
    if not woff2:
        no_woff2.append(re.sub(r"\s+", " ", block)[:90])
        return block
    block = SRC_DECL.sub("", block)
    body = block[:-1].rstrip()
    if not body.endswith((";", "{")):
        body += ";"
    return body + f'src:url({woff2[0]}) format("woff2");' + "}"


for dp, _, files in os.walk(plugins):
    for f in files:
        if not f.endswith(".css"):
            continue
        path = os.path.join(dp, f)
        text = open(path, encoding="utf-8", errors="surrogateescape").read()
        new = FONT_FACE.sub(one_format, text)
        if new != text:
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as out:
                out.write(new)

# Names that any page, style or script still mentions.
tokens = set()
for dp, dirs, files in os.walk(site):
    if os.path.relpath(dp, site) == ".":
        dirs[:] = [d for d in dirs if d not in {".git", ".github", ".claude", "pagefind"}]
    for f in files:
        if f.endswith((".html", ".css", ".js")):
            text = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
            tokens.update(re.findall(r"[\w.\-%@]+", text))
for dp, _, files in os.walk(plugins):
    for f in files:
        if f.endswith(FONT_EXT) and f not in tokens:
            drop(os.path.join(dp, f), plugin_of(os.path.join(dp, f)))

# 3. Chunks for widgets no page uses.
for plugin, names in DENY_CHUNKS.items():
    folder = os.path.join(plugins, plugin, "assets", "js")
    if not os.path.isdir(folder):
        continue
    for f in os.listdir(folder):
        m = CHUNK.match(f)
        if m and m.group("name") in names:
            drop(os.path.join(folder, f), plugin)

# 4. WooCommerce admin and checkout leftovers.
for rel in DROP_FILES:
    path = os.path.join(plugins, rel)
    if os.path.isfile(path):
        drop(path, rel.split("/")[0])
for rel in DROP_DIRS:
    for dp, _, files in os.walk(os.path.join(plugins, rel)):
        for f in files:
            drop(os.path.join(dp, f), rel.split("/")[0])

# Drop the CSS rules that point at the deleted card icons, so no link is left dangling.
wc_css = os.path.join(plugins, "woocommerce", "assets", "css", "woocommerce.css")
if os.path.isfile(wc_css):
    text = open(wc_css, encoding="utf-8", errors="surrogateescape").read()
    new = CARD_RULE.sub("", text)
    if new != text:
        with open(wc_css, "w", encoding="utf-8", errors="surrogateescape") as out:
            out.write(new)

total = sum(saved.values())
for plugin, size in sorted(saved.items(), key=lambda x: -x[1]):
    print(f"  {plugin}: removed {size // 1024} KB")
print(f"pruned {total // 1024} KB")
for b in no_woff2:
    print("font without woff2, left as is:", b)
