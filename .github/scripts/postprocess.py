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

# 5b. Intensive course pages: the course cards in .github/snippets replace the
# course list section (4aecc96: a spacer and the WooCommerce products). The
# title banner above it stays.
SNIPPETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snippets")
COURSE_CARDS = {
    "product-category/intensivi/index.html": "intensivi-cards.html",
    "en/product-category/intensive-en/index.html": "intensive-en-cards.html",
}
COURSE_LIST = re.compile(r'<section class="[^"]*elementor-element-4aecc96 ')
SECTION_TAG = re.compile(r"<(/?)section\b")


def section_end(text, start, page="page"):
    # Course cards hold Elementor templates with sections of their own:
    # count open and close tags to find the end of this one.
    depth = 0
    for m in SECTION_TAG.finditer(text, start):
        depth += -1 if m.group(1) else 1
        if not depth:
            return text.index(">", m.end()) + 1
    sys.exit(f"{page}: a section is not closed")


for page, snippet in COURSE_CARDS.items():
    path = os.path.join(site, page)
    if not os.path.exists(path):
        continue
    # The page no longer lists thematic courses apart: drop it from the title.
    # The English banner names both course groups, like the Italian one.
    text = read(path).replace("Intensivi, Super Intensivi, Tematici", "Intensivi, Super Intensivi")
    text = text.replace('elementor-size-default">Intensive</h1>', 'elementor-size-default">Intensive, Superintensive</h1>')
    text = text.replace("<title>Intensive &#8211;", "<title>Intensive, Superintensive &#8211;")
    if 'class="ali-int"' not in text:
        m = COURSE_LIST.search(text)
        if not m:
            sys.exit(f"{page}: course list section 4aecc96 not found")
        cards = read(os.path.join(SNIPPETS, snippet))
        text = text[:m.start()] + cards + text[section_end(text, m.start(), page):]
    write(path, text)

# 5d. English Accademia page: the team cards in .github/snippets replace the
# "Meet Our Team" sections, from the heading (525cf6a) to the last person
# (a63c49f). The photos are in .github/files.
TEAM_CARDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snippets", "team-en.html")
path = os.path.join(site, "en/accademia/index.html")
if os.path.exists(path):
    text = read(path)
    if 'class="ali-team"' not in text:
        m = re.search(r'<section class="[^"]*elementor-element-525cf6a ', text)
        last = re.search(r'<section class="[^"]*elementor-element-a63c49f ', text)
        if not m or not last:
            sys.exit("en/accademia: team sections 525cf6a..a63c49f not found")
        text = text[:m.start()] + read(TEAM_CARDS) + text[section_end(text, last.start()):]
        write(path, text)

# 5e. Programs pages: the program cards in .github/snippets replace the
# 1, 2 and 4 week lists (f61fa66). The "Caratteristiche del corso" section
# (c2174f0, a2ccb96 in English) goes away, with the spacers above and below
# it (fc18919, 8e69e7b): the cards set their own top space.
PROGRAM_CARDS = {
    "product/programs/index.html": "programmi-cards.html",
    "en/product/programs/index.html": "programs-en-cards.html",
}
for page, snippet in PROGRAM_CARDS.items():
    path = os.path.join(site, page)
    if not os.path.exists(path):
        continue
    text = read(path)
    if 'id="prog-1"' not in text:
        m = re.search(r'<section class="[^"]*elementor-element-f61fa66 ', text)
        if not m:
            sys.exit(f"{page}: program section f61fa66 not found")
        text = text[:m.start()] + read(os.path.join(SNIPPETS, snippet)) + text[section_end(text, m.start(), page):]
    for gone in ("fc18919", "c2174f0", "a2ccb96", "8e69e7b"):
        m = re.search(r'<section class="[^"]*elementor-element-' + gone + " ", text)
        if m:
            text = text[:m.start()] + text[section_end(text, m.start(), page):]
    # The English banner text lost the "I" of "Italian".
    text = re.sub(r"(\s)talian language courses", r"\1Italian language courses", text)
    write(path, text)

# 5f. Neumann University runs a summer program, not four weeks: fix the
# caption of its logo box on the programs and packages pages.
for page in ("product/programs", "product/packages", "en/product/programs", "en/product/packages"):
    path = os.path.join(site, page, "index.html")
    if os.path.exists(path):
        text = read(path)
        write(path, text.replace(
            'description">Four weeks in Italy</p>', 'description">Summer Immersion Program</p>'))

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

# 7a. Method page, "In italiano. Il corso": the covers image sits in the same
# line as the text that follows it. Put the text in its own paragraph under
# the image, with some space between them.
CORSO_IMG = re.compile(r'<p>(<img [^>]*df335cb4-d762-4ee5-9da3-a04124bfb1eb[^>]*/>)(Il corso si articola)')
path = os.path.join(site, "method/index.html")
if os.path.exists(path):
    text, n = CORSO_IMG.subn(r'<p style="clear:left;margin-bottom:1.5em">\1</p><p>\2', read(path))
    if n:
        write(path, text)
    else:
        print('method/index.html: "In italiano. Il corso" image not found')

# 7b. The address block (effb67e) has the map at a fixed 610px, taller than
# the blue address box next to it. On desktop stretch both columns to the
# same height and let the map fill its column. On phones the map column
# (e39b086) is hidden: show it under the address box, 350px tall.
MAP_CSS = """<style id="address-map">
@media(min-width:1025px){
.elementor .elementor-section.elementor-element.elementor-element-effb67e > .elementor-container{align-items:stretch;min-height:0}
.elementor-section.elementor-element-effb67e .elementor-element.elementor-element-435ec0d,
.elementor-section.elementor-element-effb67e .elementor-element-435ec0d > .elementor-widget-container,
.elementor-section.elementor-element-effb67e .elementor-element-435ec0d .elementor-custom-embed{height:100%}
.elementor-section.elementor-element-effb67e .elementor-element.elementor-element-435ec0d iframe{height:100%;min-height:400px;display:block}
}
@media(max-width:767px){
.elementor-section.elementor-element-effb67e .elementor-element.elementor-element-435ec0d iframe{height:350px;display:block}
}
</style>
"""
MAP_COLUMN_HIDDEN = re.compile(r'(class="[^"]*elementor-element-e39b086) elementor-hidden-phone')
for path in text_files():
    if not path.endswith(".html"):
        continue
    text = read(path)
    if 'data-id="435ec0d"' not in text:
        continue
    text = MAP_COLUMN_HIDDEN.sub(r"\1", text)
    if 'id="address-map"' not in text:
        text = text.replace("</head>", MAP_CSS + "</head>", 1)
    write(path, text)

# 7b2. English Accademia page (994819) and Italian Location page (991146),
# "The Location": size the photo (column 2f629cb) like the carousel at the
# top of the page. Mirror its column: 80px (30px on tablets) between text
# and photo, and no spacer (c3275f7) above the photo, so it starts level
# with the text.
LOCATION_CSS = """<style id="location-photo">
@media(min-width:768px){
.elementor-POST .elementor-element.elementor-element-c3275f7{display:none}
.elementor-POST .elementor-element.elementor-element-2f629cb > .elementor-element-populated{padding-inline-start:30px}
}
@media(min-width:1025px){
.elementor-POST .elementor-element.elementor-element-8a05863 > .elementor-element-populated{margin-inline-end:0}
.elementor-POST .elementor-element.elementor-element-2f629cb > .elementor-element-populated{padding-inline-start:80px}
}
</style>
"""
for page, post in [("en/accademia/index.html", "994819"), ("location/index.html", "991146")]:
    path = os.path.join(site, page)
    if not os.path.exists(path):
        continue
    text = read(path)
    if 'id="location-photo"' not in text:
        write(path, text.replace("</head>", LOCATION_CSS.replace("POST", post) + "</head>", 1))

# 7c. The address is Via Santa Maria delle Rose, 17 - 06081 Assisi. Via Tiberio
# d'Assisi, 10 stays only in the "© ... | p.iva" footer line.
ADDRESS_FIXES = [
    ("Santa Maria delle Rose , 10 ", "Santa Maria delle Rose, 17 "),
    ("Rose, 17<br> 06181 Assisi", "Rose, 17<br> 06081 Assisi"),
    ("Sede sociale: Via Tiberio d’Assisi, 10. Ingresso e segreteria: Via Santa Maria", "Via Santa Maria"),
    (">Via Tiberio d'Assisi, 10 - 06081 Assisi Italy<", ">Via Santa Maria delle Rose, 17 - 06081 Assisi Italy<"),
    ("Via%20Tiberio%20d%27Assisis%2010%2005081", "Via%20Santa%20Maria%20delle%20Rose%2017%2006081"),
    ("Via Tiberio d&#039;Assisis 10 05081", "Via Santa Maria delle Rose 17 06081"),
    ("in via Tiberio d’Assisi, 10,", "in via Santa Maria delle Rose, 17,"),
    ("at 10 via Tiberio d’Assisi,", "at 17 via Santa Maria delle Rose,"),
]
for path in text_files():
    if not path.endswith(".html"):
        continue
    text = new = read(path)
    for old, fixed in ADDRESS_FIXES:
        new = new.replace(old, fixed)
    if new != text:
        write(path, new)

# 7d. Method page: the other books have a heading widget (like 9aadea0, ".it
# Italy To go") above a toggle with an empty title. Yidali has no heading: its
# toggle title holds the name and the course description. Give it a copy of
# that heading with "Yidali《译大利》", empty the toggle title and open the toggle
# text with the description.
YIDALI_HEADING = re.compile(
    r'[ \t]*<div class="elementor-element elementor-element-9aadea0 .*?</h2>\s*</div>\s*</div>\n', re.S
)
YIDALI_TOGGLE = re.compile(
    r'([ \t]*<div class="elementor-element elementor-element-(\w+) elementor-widget elementor-widget-toggle"'
    r'(?:(?!elementor-widget-toggle).)*?<a class="elementor-toggle-title" tabindex="0">)'
    r'Yidali《译大利》(Corso di lingua[^<]*)<br><br>\s*([^<]*)'
    r'(</a>.*?<div [^>]*class="elementor-tab-content[^"]*"[^>]*>)',
    re.S,
)
path = os.path.join(site, "method/index.html")
if os.path.exists(path):
    text = read(path)
    heading = YIDALI_HEADING.search(text)
    toggle = YIDALI_TOGGLE.search(text)
    if heading and toggle:
        new_heading = re.sub(r'data-id="9aadea0"', f'data-id="{toggle.group(2)}h"', heading.group(0))
        new_heading = re.sub(r"(<h2 [^>]*>).*?(</h2>)", r"\1Yidali《译大利》\2", new_heading, flags=re.S)
        text = (
            text[: toggle.start()]
            + new_heading
            + toggle.group(1)
            + toggle.group(5)
            + "<p>" + toggle.group(3).strip() + "<br>" + toggle.group(4).strip() + "</p>"
            + text[toggle.end():]
        )
        write(path, text)
    else:
        print("method/index.html: Yidali heading or toggle not found")
# The English page keeps every title in its toggle: there, shorten the title
# to "Yidali《译大利》" (it lacks the closing 》) and move the description.
YIDALI_TOGGLE_EN = re.compile(
    r'(<a class="elementor-toggle-title" tabindex="0">)Yidali《译大利》?\.?\s*(Corso di lingua[^<]*)<br><br>\s*([^<]*)'
    r'(</a>.*?<div [^>]*class="elementor-tab-content[^"]*"[^>]*>)',
    re.S,
)
path = os.path.join(site, "en/method/index.html")
if os.path.exists(path):
    text, n = YIDALI_TOGGLE_EN.subn(
        lambda m: m.group(1) + "Yidali《译大利》" + m.group(4)
        + "<p>" + m.group(2).strip() + "<br>" + m.group(3).strip() + "</p>",
        read(path),
        count=1,
    )
    if n:
        write(path, text)
    else:
        print("en/method/index.html: Yidali toggle title not found")

# 7e. English FAQ page: drop the old toggle lists under the FAQ block (83ae875).
# They are six sections, a heading and a list each (Courses, Housing,
# Activities), from 229e665 up to the address section e80c5ba.
OLD_FAQ = re.compile(
    r'[ \t]*<section class="elementor-section elementor-top-section [^>]*data-id="229e665".*?'
    r'(?=[ \t]*<section class="elementor-section elementor-top-section [^>]*data-id="e80c5ba")',
    re.S,
)
path = os.path.join(site, "en/faq/index.html")
if os.path.exists(path):
    text, n = OLD_FAQ.subn("", read(path), count=1)
    if n:
        write(path, text)
    else:
        print("en/faq/index.html: old FAQ lists not found")

# 7f. The footer (995424, in Italian 311) has two versions: one for desktop and
# an older one for tablet and mobile (975343b, 9e6616c, 0b39a43, 2ab78d6). Drop
# the older one and show the desktop version at every width. Below 1025px its five-column
# rows get their own layout: no empty columns, the contact form on its own
# row, the course, contact and social lists side by side on tablet.
OLD_FOOTER = re.compile(
    r'[ \t]*<(?:section|div) class="elementor-section elementor-inner-section [^>]*data-id="975343b".*?'
    r'(?=[ \t]*<(?:section|div) class="elementor-section elementor-inner-section [^>]*data-id="868692e")',
    re.S,
)
FOOTER_HIDDEN = re.compile(
    r'(<(?:section|div) class="[^"]*elementor-element-(?:868692e|a31bb48|045bb98|c77ad4f)[^"]*?)'
    r' elementor-hidden-tablet elementor-hidden-mobile'
)
FOOTER_CSS = """<style id="footer-narrow">
@media(max-width:1024px){
.elementor.elementor-location-footer .elementor-element.elementor-element-b81e2fe{padding:20px 0 0}
.elementor.elementor-location-footer .elementor-element.elementor-element-868692e,
.elementor.elementor-location-footer .elementor-element.elementor-element-a31bb48,
.elementor.elementor-location-footer .elementor-element.elementor-element-045bb98,
.elementor.elementor-location-footer .elementor-element.elementor-element-c77ad4f{margin:0;padding:0 30px}
.elementor.elementor-location-footer .elementor-element.elementor-element-b88c1ac,
.elementor.elementor-location-footer .elementor-element.elementor-element-4b38fc2,
.elementor.elementor-location-footer .elementor-element.elementor-element-67f41b2,
.elementor.elementor-location-footer .elementor-element.elementor-element-5ab1ac8,
.elementor.elementor-location-footer .elementor-element.elementor-element-e7544db{display:none}
.elementor.elementor-location-footer .elementor-element.elementor-element-7d37781,
.elementor.elementor-location-footer .elementor-element.elementor-element-796acb0,
.elementor.elementor-location-footer .elementor-element.elementor-element-2af153d{width:100%}
.elementor.elementor-location-footer .elementor-element.elementor-element-c9c2626 > .elementor-widget-container{margin:30px 0 20px;padding:0}
.elementor.elementor-location-footer .elementor-element.elementor-element-c9c2626 img{width:320px;max-width:100%}
.elementor.elementor-location-footer .elementor-element.elementor-element-2af153d > .elementor-element-populated{border-width:1px 0 0;margin-top:40px;padding:20px 0 40px}
.elementor.elementor-location-footer .elementor-element.elementor-element-8af0632 .elementor-heading-title{font-size:40px}
.elementor.elementor-location-footer .elementor-element-2af153d .elementor-element.elementor-widget-form{width:100%;max-width:560px;margin:0 auto}
.elementor.elementor-location-footer .elementor-element.elementor-element-c77ad4f > .elementor-container{padding:15px 0}
}
@media(min-width:768px) and (max-width:1024px){
.elementor.elementor-location-footer .elementor-element.elementor-element-2535570,
.elementor.elementor-location-footer .elementor-element.elementor-element-7679b42,
.elementor.elementor-location-footer .elementor-element.elementor-element-a0ae208{width:33.333%}
.elementor.elementor-location-footer .elementor-element.elementor-element-2535570 > .elementor-element-populated,
.elementor.elementor-location-footer .elementor-element.elementor-element-7679b42 > .elementor-element-populated,
.elementor.elementor-location-footer .elementor-element.elementor-element-a0ae208 > .elementor-element-populated{margin:0;--e-column-margin-left:0;padding:40px 20px 0 0}
.elementor.elementor-location-footer .elementor-element.elementor-element-c23143b{width:40%}
.elementor.elementor-location-footer .elementor-element.elementor-element-f3d334e,
.elementor.elementor-location-footer .elementor-element.elementor-element-b1b10e2,
.elementor.elementor-location-footer .elementor-element.elementor-element-4df85b2{width:20%}
}
@media(max-width:767px){
.elementor.elementor-location-footer .elementor-element.elementor-element-868692e,
.elementor.elementor-location-footer .elementor-element.elementor-element-a31bb48,
.elementor.elementor-location-footer .elementor-element.elementor-element-045bb98,
.elementor.elementor-location-footer .elementor-element.elementor-element-c77ad4f{padding:0 20px}
.elementor.elementor-location-footer .elementor-element.elementor-element-f3d334e,
.elementor.elementor-location-footer .elementor-element.elementor-element-b1b10e2,
.elementor.elementor-location-footer .elementor-element.elementor-element-4df85b2{width:33.333%}
}
</style>
"""
for path in text_files():
    if not path.endswith(".html"):
        continue
    text = read(path)
    if 'data-id="868692e"' not in text:
        continue
    text, n = OLD_FOOTER.subn("", text, count=1)
    text, m = FOOTER_HIDDEN.subn(r"\1", text)
    if n != 1 or m != 4:
        print(f"{path}: footer has {n} of 1 old part, {m} of 4 hidden parts")
    if 'id="footer-narrow"' not in text:
        text = text.replace("</head>", FOOTER_CSS + "</head>", 1)
    write(path, text)

# 7g. Files the crawl host does not have live in .github/files, at their path
# in the site. Copy them in.
extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files")
for dirpath, _, files in os.walk(extra):
    for name in files:
        src = os.path.join(dirpath, name)
        dst = os.path.join(site, os.path.relpath(src, extra))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)

# 7h. Method page, "In italiano" gallery: the first cover is a 150x150 square
# crop, bigger than the others and cut. Use the whole cover (c40.gif, from
# .github/files) at the others' height.
C40_IMG = re.compile(r'width="150" height="150" src="([^"]*/)c40-150x150\.gif"')
path = os.path.join(site, "method/index.html")
if os.path.exists(path):
    text, n = C40_IMG.subn(r'width="107" height="150" src="\1c40.gif"', read(path))
    if n:
        write(path, text)
    else:
        print("method/index.html: c40-150x150.gif cover not found")

# 7i. English method page, "In Italiano": in WordPress the gallery of covers is
# missing, leaving an empty paragraph after "The components of ... are:". Copy
# the Italian gallery there (after 7h, so it has the whole first cover). The
# English page is one folder deeper. Its title (4b4ff8c8) is set to 42px, the
# other toggle titles to 24px: make it 24px too.
GALLERY_EN_SPOT = re.compile(r"(The components of the multimedia method\s*<em>In italiano</em>\s*are:</p>)<p></p>")
it_path = os.path.join(site, "method/index.html")
en_path = os.path.join(site, "en/method/index.html")
if os.path.exists(it_path) and os.path.exists(en_path):
    it_text = read(it_path)
    start = it_text.find("<div id='gallery-1'")
    end = depth = 0
    if start >= 0:
        for m in re.finditer(r"<div\b|</div>", it_text[start:]):
            depth += 1 if m.group(0) == "<div" else -1
            if not depth:
                end = start + m.end()
                break
    if end:
        gallery = it_text[start:end].replace('"../assets/', '"../../assets/')
        text, n = GALLERY_EN_SPOT.subn(lambda m: m.group(1) + "<p>" + gallery + "\n</p>", read(en_path), count=1)
        if n:
            write(en_path, text)
        else:
            print("en/method/index.html: spot for the In Italiano gallery not found")
    else:
        print("method/index.html: In Italiano gallery not found")
path = os.path.join(site, "assets/uploads/elementor/css/post-994812.css")
if os.path.exists(path):
    old = '.elementor-element-4b4ff8c8 .elementor-toggle-title{font-family:"Cormorant Garamond", Sans-serif;font-size:42px;'
    text = read(path)
    if old in text:
        write(path, text.replace(old, old.replace("42px", "24px")))
    else:
        print("post-994812.css: 42px In Italiano title not found")

# 7j. Guestbook page (994884) and both testimonials pages (341): on desktop
# the empty section under the guestbook (c944fe1) has margin-top -491px, so
# the address and map block slide up over the guestbook. Use the tablet
# margins (0 and 70px) on desktop too.
for post in ("994884", "341"):
    path = os.path.join(site, f"assets/uploads/elementor/css/post-{post}.css")
    if not os.path.exists(path):
        continue
    old = f".elementor-{post} .elementor-element.elementor-element-c944fe1{{margin-top:-491px;margin-bottom:150px;"
    text = read(path)
    if old in text:
        write(path, text.replace(old, old.replace("-491px;margin-bottom:150px", "0px;margin-bottom:70px")))
    else:
        print(f"post-{post}.css: guestbook c944fe1 margin not found")

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
