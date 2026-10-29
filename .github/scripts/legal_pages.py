#!/usr/bin/env python3
"""Build the legal pages: termini-e-condizioni, privacy-policy, note-legali.

Usage: python3 -I .github/scripts/legal_pages.py SITE_DIR

postprocess.py runs it after the text fixes (step 7o). Each page is a copy of
visa-information/index.html, so it has the site header, menu and footer. The
copy gets its own title, meta description and banner title. The banner
subtitle (7804f65) goes away and the block in .github/snippets replaces the
visa text (section ac5b436). Each block carries its own style, limited to
.ali-legal. Header, menu and footer stay as they are on the visa page.

It rebuilds the pages from the visa page each time, so it is safe to run again.
"""
import os
import re
import sys

site = sys.argv[1]
SNIPPETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snippets")
BASE = "visa-information/index.html"

# slug: (title, snippet, meta description)
PAGES = {
    "termini-e-condizioni": (
        "Termini e condizioni", "termini-e-condizioni-it.html",
        "Iscrizione, prezzi, pagamento, cancellazione, cambio di data e visto: "
        "le condizioni dei corsi dell’Accademia Lingua Italiana Assisi.",
    ),
    "privacy-policy": (
        "Privacy policy", "privacy-policy-it.html",
        "Come l’Accademia Lingua Italiana Assisi tratta i dati di chi visita il sito, "
        "chiede informazioni o si iscrive ai corsi, e quali sono i tuoi diritti.",
    ),
    "note-legali": (
        "Note legali", "note-legali-it.html",
        "Chi gestisce il sito dell’Accademia Lingua Italiana Assisi: dati della società, "
        "riconoscimenti, diritti su testi e immagini, hosting.",
    ),
}

SECTION_TAG = re.compile(r"<(/?)section\b")
SUBTITLE = re.compile(r'<div class="elementor-element elementor-element-7804f65 .*?</h2>\s*</div>\s*</div>\s*', re.S)


def read(path):
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(text)


def section_end(text, start):
    depth = 0
    for m in SECTION_TAG.finditer(text, start):
        depth += -1 if m.group(1) else 1
        if not depth:
            return text.index(">", m.end()) + 1
    sys.exit(f"{BASE}: a section is not closed")


def sub_once(pattern, repl, text, what):
    new, n = re.subn(pattern, repl, text, count=1)
    if not n:
        sys.exit(f"{BASE}: {what} not found")
    return new


base = read(os.path.join(site, BASE))
for slug, (title, snippet, description) in PAGES.items():
    text = sub_once(r"<title>Informazioni per il visto &#8211;",
                    lambda _m: f'<title>{title} &#8211;', base, "title")
    text = text.replace("</title>", f'</title>\n<meta name="description" content="{description}">', 1)
    text = sub_once(r'(<h1 class="elementor-heading-title elementor-size-default">)Informazioni per il visto(</h1>)',
                    lambda m: m.group(1) + title + m.group(2), text, "banner title")
    text = sub_once(SUBTITLE, "", text, "banner subtitle 7804f65")
    m = re.search(r'<section class="[^"]*elementor-element-ac5b436 ', text)
    if not m:
        sys.exit(f"{BASE}: section ac5b436 not found")
    text = text[:m.start()] + read(os.path.join(SNIPPETS, snippet)).strip() + text[section_end(text, m.start()):]
    os.makedirs(os.path.join(site, slug), exist_ok=True)
    write(os.path.join(site, slug, "index.html"), text)
print(f"legal pages: {', '.join(PAGES)}")
