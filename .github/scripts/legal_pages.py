#!/usr/bin/env python3
"""Build the legal pages, in Italian and English.

Usage: python3 -I .github/scripts/legal_pages.py SITE_DIR

postprocess.py runs it after the text fixes (step 7o). Each page is a copy of
the visa page in its language (visa-information/index.html or
en/visa-information/index.html), so it has the site header, menu and footer.
The copy gets its own title, meta description and banner title. The banner
subtitle (7804f65) goes away and the block in .github/snippets replaces the
visa text (section ac5b436). Each block carries its own style, limited to
.ali-legal. Header, menu and footer stay as they are on the visa page, except
the language links: they go to the same legal page in the other language.

It rebuilds the pages from the visa pages each time, so it is safe to run again.
"""
import os
import re
import sys

site = sys.argv[1]
SNIPPETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snippets")

# The visa page each language copies: its folder, its title, its language links
# (lang attribute of the link to the other language, and where that link points).
BASES = {
    "it": ("visa-information", "Informazioni per il visto", "en-GB", "../en/{other}/index.html"),
    "en": ("en/visa-information", "Visa information", "it-IT", "../../{other}/index.html"),
}

# (Italian slug, English slug): {language: (title, snippet, meta description)}
PAGES = {
    ("termini-e-condizioni", "terms-and-conditions"): {
        "it": ("Termini e condizioni", "termini-e-condizioni-it.html",
               "Iscrizione, prezzi, pagamento, cancellazione, cambio di data e visto: "
               "le condizioni dei corsi dell’Accademia Lingua Italiana Assisi."),
        "en": ("Terms and conditions", "terms-and-conditions-en.html",
               "Enrolment, prices, payment, cancellation, date changes and visa: "
               "the terms of the courses at Accademia Lingua Italiana Assisi."),
    },
    ("privacy-policy", "privacy-policy"): {
        "it": ("Privacy policy", "privacy-policy-it.html",
               "Come l’Accademia Lingua Italiana Assisi tratta i dati di chi visita il sito, "
               "chiede informazioni o si iscrive ai corsi, e quali sono i tuoi diritti."),
        "en": ("Privacy policy", "privacy-policy-en.html",
               "How Accademia Lingua Italiana Assisi processes the data of website visitors, "
               "people asking for information and students, and what your rights are."),
    },
    ("note-legali", "legal-notice"): {
        "it": ("Note legali", "note-legali-it.html",
               "Chi gestisce il sito dell’Accademia Lingua Italiana Assisi: dati della società, "
               "riconoscimenti, diritti su testi e immagini, hosting."),
        "en": ("Legal notice", "legal-notice-en.html",
               "Who runs the Accademia Lingua Italiana Assisi website: company details, "
               "recognitions, rights on texts and images, hosting."),
    },
}

SECTION_TAG = re.compile(r"<(/?)section\b")
SUBTITLE = re.compile(r'<div class="elementor-element elementor-element-7804f65 .*?</h2>\s*</div>\s*</div>\s*', re.S)


def read(path):
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(text)


def section_end(text, start, page):
    depth = 0
    for m in SECTION_TAG.finditer(text, start):
        depth += -1 if m.group(1) else 1
        if not depth:
            return text.index(">", m.end()) + 1
    sys.exit(f"{page}: a section is not closed")


def sub_once(pattern, repl, text, page, what):
    new, n = re.subn(pattern, repl, text, count=1)
    if not n:
        sys.exit(f"{page}: {what} not found")
    return new


built = []
for lang, (folder, visa_title, other_lang, other_href) in BASES.items():
    page = folder + "/index.html"
    base = read(os.path.join(site, page))
    for (it_slug, en_slug), texts in PAGES.items():
        title, snippet, description = texts[lang]
        slug, other = (it_slug, en_slug) if lang == "it" else (en_slug, it_slug)
        text = sub_once(r"<title>" + re.escape(visa_title) + " &#8211;",
                        lambda _m: f"<title>{title} &#8211;", base, page, "title")
        text = text.replace("</title>", f'</title>\n<meta name="description" content="{description}">', 1)
        text = sub_once(r'(<h1 class="elementor-heading-title elementor-size-default">)' + re.escape(visa_title) + "(</h1>)",
                        lambda m: m.group(1) + title + m.group(2), text, page, "banner title")
        text = sub_once(SUBTITLE, "", text, page, "banner subtitle 7804f65")
        m = re.search(r'<section class="[^"]*elementor-element-ac5b436 ', text)
        if not m:
            sys.exit(f"{page}: section ac5b436 not found")
        text = text[:m.start()] + read(os.path.join(SNIPPETS, snippet)).strip() + text[section_end(text, m.start(), page):]
        href = other_href.format(other=other)
        text = re.sub(r'<a href="[^"]*"( lang="' + other_lang + '" hreflang)', f'<a href="{href}"\\1', text)
        dest = os.path.join(site, os.path.dirname(folder), slug) if lang == "en" else os.path.join(site, slug)
        os.makedirs(dest, exist_ok=True)
        write(os.path.join(dest, "index.html"), text)
        built.append(os.path.relpath(dest, site).replace(os.sep, "/"))
print(f"legal pages: {', '.join(built)}")
