#!/usr/bin/env python3
"""Rebuild the main menu on every page from data/menu.json.

Usage:
  python3 -I .github/scripts/build_menu.py SITE_DIR

Each page has two main menu widgets: 985225e (desktop header) and 7062eec4
(mobile sticky header). Each widget has two lists: the horizontal menu
(menu-1-*) and the burger dropdown (menu-2-*, links with tabindex="-1").
All four get the same items. The page language comes from the language
switcher item marked "current-lang".

Kept as they are: the language switcher items, the arrow icon of each widget,
everything outside the <ul>. The button ("pulsante") comes before the
language switcher in the horizontal menu, and last in the burger dropdown.
Its look is in assets/alia/menu.css, linked after footer.css.

Safe to run again on a page it already changed.
"""
import html
import json
import os
import re
import subprocess
import sys

WIDGETS = ("985225e", "7062eec4")
UL = re.compile(r'<ul id="menu-([12])-(%s)" class="elementor-nav-menu">' % "|".join(WIDGETS))
LANG_ITEM = re.compile(r'<li class="lang-item .*?</li>', re.S)
ARROW = re.compile(r'<span class="sub-arrow">.*?</span>', re.S)
CSS_LINK = "<link rel='stylesheet' id='ali-menu-css' href='%sassets/alia/menu.css' media='all' />"
FOOTER_LINK = re.compile(r"<link rel='stylesheet' id='ali-footer-css' href='([^']*)assets/alia/footer\.css' media='all' />")


def href(url, page_dir):
    target = url.rstrip("/") + "/index.html" if url else "index.html"
    return os.path.relpath(target, page_dir or ".").replace(os.sep, "/")


def link(voce, page_dir, sub, dropdown, extra_li=""):
    h = href(voce["url"], page_dir)
    current = h == "index.html"
    li = "menu-item menu-item-type-post_type menu-item-object-page"
    a_cls = "elementor-sub-item" if sub else "elementor-item"
    aria = ""
    if current:
        li += " current-menu-item current_page_item"
        a_cls += " elementor-item-active"
        aria = ' aria-current="page"'
    tab = ' tabindex="-1"' if dropdown else ""
    return current, '<li class="%s%s"><a href="%s"%s class="%s"%s>%s</a></li>' % (
        li, extra_li, h, aria, a_cls, tab, html.escape(voce["titolo"], quote=False))


def items(menu, page_dir, arrow, dropdown):
    out = []
    tab = ' tabindex="-1"' if dropdown else ""
    for voce in menu["voci"]:
        if "sotto" not in voce:
            out.append(link(voce, page_dir, False, dropdown)[1])
            continue
        subs = [link(s, page_dir, True, dropdown) for s in voce["sotto"]]
        li = "menu-item menu-item-type-custom menu-item-object-custom"
        if any(c for c, _ in subs):
            li += " current-menu-ancestor current-menu-parent"
        out.append(
            '<li class="%s menu-item-has-children"><a href="#" class="elementor-item elementor-item-anchor"%s>%s%s</a>\n'
            '<ul class="sub-menu elementor-nav-menu--dropdown">\n%s\n</ul>\n</li>'
            % (li, tab, html.escape(voce["titolo"], quote=False), arrow,
               "\n".join("\t" + s for _, s in subs)))
    return out


def build(text, page_dir, menus):
    parts, pos, count = [], 0, 0
    for m in UL.finditer(text):
        end = text.index("</nav>", m.end())
        close = text.rindex("</ul>", m.end(), end)
        body = text[m.end():close]
        langs = LANG_ITEM.findall(body)
        if len(langs) != 2:
            raise SystemExit("%s: menu %s has %d language items" % (page_dir, m.group(0), len(langs)))
        lang = "en" if "lang-item-en current-lang" in body else "it"
        arrow = ARROW.search(body)
        if not arrow:
            raise SystemExit("%s: menu %s has no sub-arrow" % (page_dir, m.group(0)))
        menu = menus[lang]
        dropdown = m.group(1) == "2"
        new = items(menu, page_dir, arrow.group(0), dropdown)
        cta = link(menu["pulsante"], page_dir, False, dropdown, " ali-menu-cta")[1]
        new += langs + [cta] if dropdown else [cta] + langs
        parts += [text[pos:m.end()], "\n".join(new) + "\n"]
        pos = close
        count += 1
    parts.append(text[pos:])
    return "".join(parts), count


def main():
    site = sys.argv[1]
    with open(os.path.join(site, "data", "menu.json"), encoding="utf-8") as f:
        menus = json.load(f)
    files = subprocess.run(["git", "-C", site, "ls-files", "*index.html"],
                           capture_output=True, text=True, check=True).stdout.split()
    changed = 0
    for rel in files:
        if rel.startswith(("pagefind/", ".github/", "assets/")):
            continue
        path = os.path.join(site, rel)
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        page_dir = os.path.dirname(rel)
        new, count = build(text, page_dir, menus)
        if count == 0:
            continue
        if count != 4:
            raise SystemExit("%s: %d main menus, expected 4" % (rel, count))
        if "id='ali-menu-css'" not in new:
            m = FOOTER_LINK.search(new)
            if not m:
                raise SystemExit("%s: no footer.css link" % rel)
            new = new[:m.end()] + "\n" + CSS_LINK % m.group(1) + new[m.end():]
        if new != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            changed += 1
    print("menu: %d pages changed" % changed)


if __name__ == "__main__":
    main()
