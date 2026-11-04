#!/usr/bin/env python3
"""Add search engine tags to every page, and write sitemap.xml and robots.txt.

Usage:
    python3 -I .github/scripts/build_seo.py SITE_DIR

The deploy and preview workflows run it on their copy of the site. It does not
need to run on the repo, and its output is not committed.

Per page it writes, between <!-- seo:start --> and <!-- seo:end --> at the end
of <head>:
- canonical: the page's own URL on the site in data/seo.json ("sito"), or the
  page named in "canonical" for duplicate pages;
- hreflang links to the Italian and English versions, taken from the language
  switcher, when the two pages point at each other;
- meta description: from data/seo.json, else the course "hero" in
  data/alia.json, else the one already on the page;
- Open Graph and Twitter tags (title, description, url, image);
- on the two home pages, the school's JSON-LD (name, address, phone).
It also replaces the <title> when data/seo.json gives one, and sets
noindex on the pages in "noindex".

sitemap.xml lists every page that is not noindex and not a duplicate.
Running it twice gives the same result.
"""
import html
import json
import os
import posixpath
import re
import sys

site = sys.argv[1]
seo = json.load(open(os.path.join(site, "data", "seo.json"), encoding="utf-8"))
ali = json.load(open(os.path.join(site, "data", "alia.json"), encoding="utf-8"))

BASE = seo["sito"].rstrip("/")
NAME = seo["nome"]
IMAGE = f"{BASE}/{seo['immagine']}"
NOINDEX = set(seo["noindex"])
DUPLICATE = seo["canonical"]
PAGES = seo["pagine"]
HOMES = {"": "it", "en/home/": "en"}
SKIP_TOP = ("assets/", "pagefind/", "pr-preview/", "data/", ".github/", ".claude/", ".git/")
LOCALE = {"it": "it_IT", "en": "en_GB"}

BLOCK = re.compile(r"\s*<!-- seo:start -->.*?<!-- seo:end -->", re.S)
OLD_TAGS = re.compile(
    r"\s*<(?:link rel=[\"']canonical[\"']|link rel=[\"']alternate[\"'] hreflang"
    r"|meta property=[\"']og:|meta name=[\"']twitter:)[^>]*>",
    re.I,
)
DESC = re.compile(r"<meta name=[\"']description[\"'] content=[\"']([^\"']*)[\"'][^>]*>", re.I)
ROBOTS = re.compile(r"<meta name=[\"']robots[\"'] content=[\"'][^\"']*[\"'][^>]*>", re.I)
REFRESH = re.compile(r"http-equiv=[\"']refresh", re.I)


def short(text, limit=160):
    """Plain text, cut at a word before limit."""
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def attr(text):
    return html.escape(text, quote=True)


# Course pages: description from the hero line.
hero = {}
for course in ali["corsi"].values() if isinstance(ali["corsi"], dict) else ali["corsi"]:
    for page in course.get("pagine", []):
        hero[page.strip("/") + "/"] = course.get("hero", "")
    en = course.get("en") or {}
    for page in en.get("pagine", []):
        hero[page.strip("/") + "/"] = en.get("hero", "")

# Read every page.
pages = {}
for dirpath, dirnames, filenames in os.walk(site):
    rel_dir = os.path.relpath(dirpath, site).replace(os.sep, "/")
    rel_dir = "" if rel_dir == "." else rel_dir + "/"
    if rel_dir.startswith(SKIP_TOP):
        dirnames[:] = []
        continue
    if "index.html" not in filenames:
        continue
    text = open(os.path.join(dirpath, "index.html"), encoding="utf-8").read()
    head = text.split("</head>", 1)[0]
    if REFRESH.search(head):
        continue
    lang = re.search(r"<html[^>]*\blang=\"(\w\w)", text)
    pages[rel_dir] = {"text": text, "lang": lang.group(1) if lang else "it"}


def other_version(path, page):
    """The page the language switcher points at, as a site path, or None."""
    other = "en" if page["lang"] == "it" else "it"
    m = re.search(r'<a href="([^"#?]*)" lang="' + other + r'[^"]*" hreflang', page["text"])
    if not m or m.group(1).startswith(("http:", "https:", "/")):
        return None
    target = posixpath.normpath(posixpath.join(path, m.group(1)))
    target = re.sub(r"(^|/)index\.html$", r"\1", target)
    if target in (".", ""):
        target = ""
    elif not target.endswith("/"):
        target += "/"
    return target if target in pages else None


def url(path):
    return f"{BASE}/{path}"


alternates = {}
for path, page in pages.items():
    other = other_version(path, page)
    if (
        other is not None
        and other_version(other, pages[other]) == path
        and path not in NOINDEX | set(DUPLICATE)
        and other not in NOINDEX | set(DUPLICATE)
    ):
        alternates[path] = {page["lang"]: path, pages[other]["lang"]: other}

school = {
    "@context": "https://schema.org",
    "@type": ["EducationalOrganization", "LocalBusiness"],
    "name": NAME,
    "alternateName": "ALIA",
    "url": f"{BASE}/",
    "logo": f"{BASE}/assets/uploads/2026/03/logo-school-ok.png",
    "image": IMAGE,
    "foundingDate": "1993",
    "email": "info@aliassisi.it",
    "telephone": "+39 075 815281",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "Via Santa Maria delle Rose, 17",
        "postalCode": "06081",
        "addressLocality": "Assisi",
        "addressRegion": "PG",
        "addressCountry": "IT",
    },
}

sitemap = []
for path in sorted(pages):
    page = pages[path]
    old = DESC.search(page["text"].split("</head>", 1)[0])
    text = BLOCK.sub("", page["text"])
    head, body = text.split("</head>", 1)
    head = OLD_TAGS.sub("", head)
    info = PAGES.get(path, {})

    if info.get("title"):
        head = re.sub(r"<title>.*?</title>", f"<title>{html.escape(info['title'], quote=False)}</title>", head, count=1, flags=re.S)
    title = re.search(r"<title>(.*?)</title>", head, re.S)
    title = short(title.group(1), 200) if title else NAME

    description = info.get("description") or short(hero.get(path, "")) or (html.unescape(old.group(1)) if old else "")
    head = DESC.sub("", head)

    if path in NOINDEX:
        head = ROBOTS.sub("", head)

    tags = []
    if path in NOINDEX:
        tags.append('<meta name="robots" content="noindex, follow">')
    if description:
        tags.append(f'<meta name="description" content="{attr(description)}">')
    canonical = url(DUPLICATE.get(path, path))
    tags.append(f'<link rel="canonical" href="{canonical}">')
    for lang, alt in sorted(alternates.get(path, {}).items()):
        tags.append(f'<link rel="alternate" hreflang="{lang}" href="{url(alt)}">')
    if path in alternates:
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{url(alternates[path]["it"])}">')
    tags += [
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{attr(NAME)}">',
        f'<meta property="og:locale" content="{LOCALE.get(page["lang"], "it_IT")}">',
        f'<meta property="og:title" content="{attr(title)}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{IMAGE}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if description:
        tags.append(f'<meta property="og:description" content="{attr(description)}">')
    if path in HOMES:
        data = dict(school, description=description, inLanguage=HOMES[path])
        tags.append('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>")

    head = head.rstrip() + "\n<!-- seo:start -->\n" + "\n".join(tags) + "\n<!-- seo:end -->\n"
    new = head + "</head>" + body
    if new != page["text"]:
        open(os.path.join(site, path, "index.html"), "w", encoding="utf-8", newline="\n").write(new)

    if path not in NOINDEX and path not in DUPLICATE:
        links = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{lang}" href="{url(alt)}"/>'
            for lang, alt in sorted(alternates.get(path, {}).items())
        )
        sitemap.append(f"  <url>\n    <loc>{url(path)}</loc>{links}\n  </url>")

open(os.path.join(site, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    ' xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(sitemap) + "\n</urlset>\n"
)
open(os.path.join(site, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
    f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n"
)
print(f"seo: {len(pages)} pages, {len(sitemap)} in sitemap.xml, {len(alternates)} with hreflang")
