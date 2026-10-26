#!/usr/bin/env python3
"""Strip WordPress leftovers from the cleaned static site.

Usage: python3 -I .github/scripts/postprocess.py SITE_DIR

Run it after cleanup.py, on the folder cleanup.py wrote. It edits SITE_DIR in
place. Steps: drop junk pages, merge wget duplicates, remove backend-only
scripts, scrub WordPress config, map old links, split the course lists, move wp-content and
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
OLD_SITE = re.compile(r"https?://(?:(?:www\.)?aliassisi\.it|alia\.evonove\.webfactional\.com)(/[^\s\"'<>)\\]*)?")
OLD_MAP = {
    "/en/method/": "en/method/index.html",
    "/angelo-chiuchiu/": "method/index.html",
    "/method/": "method/index.html",
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

# Pages that are gone for good. Keep the text, drop the link.
UNLINK = re.compile(
    r'<a\b[^>]*\bhref="(?:[^"]*/)?(?:gaia-chiuchiu|experience-qrc-queenstown|intensivi-tematici'
    r'|calendar-courses|en/courses/italian-language-courses/standard)/(?:index\.html)?"[^>]*>(.*?)</a>',
    re.S,
)

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
        if target == "angelo-chiuchiu/index.html":
            new = "en/method/index.html" if here.split("/")[0] == "en" else "method/index.html"
            return f'{attr}="{posixpath.relpath(new, here)}{tail}"'
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
            # The evonove host is dead. Keep the path, use the real domain.
            return "https://aliassisi.it" + path if "evonove" in m.group(0) else m.group(0)
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
    text = UNLINK.sub(r"\1", text)
    text = fix_links(text, here)
    write(path, text)

for old in MERGE:
    p = os.path.join(site, old)
    if os.path.exists(p):
        os.remove(p)

# 5b. Split the course lists into 22 and 26 hour groups. Each group has four
# courses. Courses are matched by the slug in their link. Every card gets the
# same body: the lessons per week, then the group and one-on-one lessons.
GROUPS_CSS = """<style id="intensivi-groups">
.elementor-widget .intensivi-group-title{color:#2c3a7c !important;margin:2.5rem 0 .5rem;font-size:2rem}
html{scroll-behavior:smooth}
.elementor-3986 .elementor-element.elementor-element-e1ce8d4{--spacer-size:0px !important}
.elementor-3986 .elementor-element.elementor-element-4aecc96{margin-top:1.5rem !important}
.intensivi-menu{display:flex;justify-content:center;gap:1rem;margin:0 0 1rem}
.intensivi-menu a.button{min-width:0}
.elementor-widget .intensivi-menu a.button{flex:0 1 14rem;text-align:center;padding:.7rem 1rem;border:2px solid #2c3a7c;border-radius:999px;background:transparent;color:#2c3a7c;text-decoration:none;transition:background .2s,color .2s}
.elementor-widget .intensivi-menu a.button:hover,.elementor-widget .intensivi-menu a.button:focus-visible{background:#2c3a7c !important;color:#fff !important}
.intensivi-group-title{scroll-margin-top:7rem}
.intensivi-group-subtitle{color:#2c3a7c;margin:0 0 1.25rem;font-size:1.1rem}
.elementor-widget-woocommerce-products ul.products.elementor-grid{grid-template-columns:repeat(4,minmax(0,1fr));align-items:stretch}
.elementor-widget-woocommerce-products ul.products li.product{display:flex;flex-direction:column}
.elementor-widget-woocommerce-products ul.products li.product>a{flex:1}
.elementor-widget-woocommerce-products ul.products li.product .woocommerce-loop-product__title{min-height:7.2em !important}
@media(max-width:1024px){.elementor-widget-woocommerce-products ul.products.elementor-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.elementor-widget .intensivi-menu{gap:.5rem}.elementor-widget .intensivi-menu a.button{padding:.8rem .4rem;font-size:.9rem}.elementor-widget-woocommerce-products ul.products.elementor-grid{grid-template-columns:minmax(0,1fr)}.elementor-widget-woocommerce-products ul.products li.product .woocommerce-loop-product__title{min-height:0}}
</style>
"""
PRODUCT_LIST = '<ul class="products elementor-grid vamtam-wc columns-3">'
PRICE_LIST = re.compile(r'<ul class="elementor-price-list">.*?</ul>', re.S)
CARD_BODY = (
    '<ul class="elementor-price-list">\n'
    '<li class="elementor-price-list-item">\n<div class="elementor-price-list-text">\n'
    '<div class="elementor-price-list-header">\n'
    '<span class="elementor-price-list-title">{week}</span>\n'
    '<span class="elementor-price-list-separator"></span>\n</div>\n'
    '<p class="elementor-price-list-description">{detail}</p>\n'
    '</div>\n</li>\n</ul>'
)
IT_SLUGS_22 = [
    "corsi-di-preparazione-per-la-certificazione", "intensive-italian",
    "religious-student-program-24", "thematic-24",
]
IT_SLUGS_26 = [
    "super-intensive-certification-exam-preparation-cours", "super-intensive-italian",
    "religious-student-program-28", "thematic-28",
]
EN_SLUGS_22 = [
    "intensive-italian", "corsi-di-preparazione-per-la-certificazione",
    "religious-student-program-22", "thematic-22",
]
EN_SLUGS_26 = [
    "super-intensive-italian", "super-intensive-certification-exam-preparation-cours",
    "religious-student-program-28", "thematic-26",
]
# (anchor id, menu label, group title, subtitle, card week line, card detail line, slugs)
COURSE_GROUPS = {
    "product-category/intensivi/index.html": [
        ("corsi-intensivi", "Corsi intensivi", "Corsi intensivi · 22 ore", "22 lezioni a settimana: 18 di gruppo al mattino e 4 individuali al pomeriggio",
         "22 lezioni alla settimana", "18 lezioni di gruppo + 4 lezioni individuali", IT_SLUGS_22),
        ("corsi-superintensivi", "Corsi superintensivi", "Corsi superintensivi · 26 ore", "26 lezioni a settimana: 18 di gruppo al mattino e 8 individuali al pomeriggio",
         "26 lezioni alla settimana", "18 lezioni di gruppo + 8 lezioni individuali", IT_SLUGS_26),
    ],
    "product-category/intensive-en/index.html": [
        ("intensive-courses", "Intensive courses", "Intensive courses · 22 hours", "22 lessons per week: 18 group lessons in the morning and 4 one-on-one lessons in the afternoon",
         "22 lessons per week", "18 group lessons + 4 one-on-one lessons", EN_SLUGS_22),
        ("super-intensive-courses", "Super intensive courses", "Super intensive courses · 26 hours", "26 lessons per week: 18 group lessons in the morning and 8 one-on-one lessons in the afternoon",
         "26 lessons per week", "18 group lessons + 8 one-on-one lessons", EN_SLUGS_26),
    ],
}


def split_courses(text, groups):
    if PRODUCT_LIST not in text or "intensivi-group-title" in text:
        return text
    start = text.index(PRODUCT_LIST)
    body = start + len(PRODUCT_LIST)
    starts = [body + m.start() for m in re.finditer(r'<li class="product ', text[body:])]
    # The last course ends with its hidden "describedby" span, then </li>.
    # Course bodies hold lists too, so do not stop at the first </ul>.
    tail = re.compile(r'screen-reader-text">.*?</span>\s*</li>', re.S).search(text, starts[-1])
    end_li = tail.end()
    close = text.index("</ul>", end_li)
    if text[end_li:close].strip():
        sys.exit("course list: unexpected markup before </ul>")
    chunks = {}
    for a, z in zip(starts, starts[1:] + [end_li]):
        slug = re.search(r'href="[^"]*/product/([^/"]+)/', text[a:z]).group(1)
        chunks[slug] = text[a:z].rstrip() + "\n"
    wanted = [slug for *_, slugs in groups for slug in slugs]
    if sorted(chunks) != sorted(wanted):
        sys.exit(f"course list: courses do not match the groups: {sorted(chunks)}")
    menu = "".join(f'<a class="button" href="#{gid}">{label}</a>' for gid, label, *_ in groups)
    html = f'<nav class="intensivi-menu">{menu}</nav>\n'
    for gid, _label, title, subtitle, week, detail, slugs in groups:
        body_html = CARD_BODY.format(week=week, detail=detail)
        html += f'<h2 id="{gid}" class="elementor-heading-title elementor-size-default intensivi-group-title">{title}</h2>\n'
        html += f'<p class="intensivi-group-subtitle">{subtitle}</p>\n'
        html += PRODUCT_LIST + "\n"
        for slug in slugs:
            if not PRICE_LIST.search(chunks[slug]):
                sys.exit(f"course list: no price list in {slug}")
            html += PRICE_LIST.sub(lambda _m: body_html, chunks[slug], count=1)
        html += "</ul>\n"
    text = text[:start] + html.rstrip("\n") + text[close + 5:]
    return text.replace("</head>", GROUPS_CSS + "</head>", 1)


for page, groups in COURSE_GROUPS.items():
    path = os.path.join(site, page)
    if os.path.exists(path):
        # The page no longer lists thematic courses apart: drop it from the title.
        new_text = split_courses(read(path), groups).replace(
            "Intensivi, Super Intensivi, Tematici", "Intensivi, Super Intensivi"
        )
        write(path, new_text)

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
    # Skip links to the old site. Its files still live under wp-content.
    MOVE_RES.append((re.compile(r"(?<!aliassisi\.it/)" + re.escape(old)), new))
    MOVE_RES.append(
        (re.compile(r"(?<!aliassisi\.it\\/)" + re.escape(old).replace("/", r"\\/")), new.replace("/", r"\/"))
    )
for path in text_files():
    text = read(path)
    new_text = text
    for rx, new in MOVE_RES:
        new_text = rx.sub(lambda _m, n=new: n, new_text)
    if new_text != text:
        write(path, new_text)

# 7. Both homes play one video, main-video1.mp4. On desktop the section behind
# the slider (24dca05) plays it, so the slides lose their own videos and the
# carousel runs over it. The English section has no video set: add it. The
# mobile slider has no such section: its slides play main-video1.mp4 themselves.
HOME_MP4 = "/assets/uploads/2026/10/main-video1.mp4"
HOME_VIDEO = re.compile(r'(<rs-bgvideo\b[^>]*?data-mp4=")[^"]*(")', re.S)
HOME_BGVIDEO = re.compile(r"[ \t]*<rs-bgvideo\b[^>]*>\s*</rs-bgvideo>\n?")
HOME_DESKTOP = re.compile(r"<!-- START Home desktop .*?<!-- END REVOLUTION SLIDER -->", re.S)
HOME_SECTION = re.compile(
    r'(<section\b[^>]*data-id="24dca05"[^>]*data-settings="\{&quot;background_background&quot;:&quot;video&quot;)(\}">)'
)
HOME_SECTION_VIDEO = (
    r"\1,&quot;background_video_link&quot;:&quot;" + HOME_MP4.replace("/", r"\\/") + r"&quot;\2"
    "\n\t\t\t\t\t\t\t\t<div class=\"elementor-background-video-container elementor-hidden-mobile\">"
    "\n\t\t\t\t\t\t\t\t\t\t\t\t\t<video class=\"elementor-background-video-hosted\" role=\"presentation\" autoplay muted playsinline loop></video>"
    "\n\t\t\t\t\t\t\t\t\t\t\t</div>"
)
# main-video1.mp4 has a few black rows at the top and bottom: zoom it a little
# so they fall outside the section. Elementor centers the video with
# translate(-50%,-50%), so the zoom goes in the same transform: the "scale"
# property alone would zoom around another point and push the video up. The news bar under it (2c917f6) drops its
# side padding to be as wide as the video.
HOME_CSS = """<style id="home-hero">
.elementor-section.elementor-element-24dca05 .elementor-background-video-hosted{transform:translate(-50%,-50%) scale(1.02)}
.elementor-section.elementor-element-2c917f6{padding-left:0;padding-right:0}
</style>
"""
for page in ("index.html", "en/home/index.html"):
    path = os.path.join(site, page)
    if not os.path.exists(path):
        continue
    text = read(path)
    if 'id="home-hero"' not in text:
        text = text.replace("</head>", HOME_CSS + "</head>", 1)
    text = HOME_SECTION.sub(lambda m: m.expand(HOME_SECTION_VIDEO), text, count=1)
    if "background_video_link&quot;:&quot;" + HOME_MP4.replace("/", "\\/") not in text:
        print(f"{page}: main-video1.mp4 is not the desktop section background")
    text = HOME_DESKTOP.sub(lambda m: HOME_BGVIDEO.sub("", m.group(0)), text, count=1)
    text, n = HOME_VIDEO.subn(lambda m: m.group(1) + HOME_MP4 + m.group(2), text)
    if not n:
        print(f"{page}: no mobile slider video found, main-video1.mp4 not set")
    write(path, text)

# 8. Delete files nothing names. Elementor loads chunks at run time, so
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

# 9. Report what is left.
left = {k: 0 for k in ("wp-content", "wp-includes", "wp-json", "admin-ajax", "aliassisi.it", "evonove")}
for path in text_files():
    text = read(path)
    for k in left:
        left[k] += text.count(k)
print("left over:", left)
if left["evonove"]:
    sys.exit("the evonove host must not appear in the site")
if unmapped_old:
    print("old-site links with no page here (left as is):")
    for p, n in sorted(unmapped_old.items(), key=lambda x: -x[1]):
        print(f"  {n:4d} {p}")
