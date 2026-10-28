#!/usr/bin/env python3
"""Text fixes on the Metodo pages and in the shared footer.

Usage: python3 -I .github/scripts/text_fixes.py SITE_DIR

postprocess.py runs it near the end (step 7n), after the book cards (7m).
It is safe to run again on a site it already fixed: no new text contains
the old text. It prints each fix it could not find.
"""
import os
import re
import sys

site = sys.argv[1]
IT = "method/index.html"
EN = "en/method/index.html"


def read(path):
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(text)


# (pages, old, new). Plain text, as it is in the HTML.
FIXES = [
    # Subtitle under the "Metodo" title: lowercase start, no subject.
    ([IT], "<h2>perfezionato in più di 30 anni di esperienza il metodo che abbiamo ideato aiuta a progredire rapidamente.\xa0</h2>",
     "<h2>Un metodo nato in aula, ad Assisi, in più di trent'anni di insegnamento.</h2>"),
    ([EN], "<h2>Refined over more than 30 years of experience, the method we have devised helps you make rapid progress</h2>",
     "<h2>A method born in the classroom, in Assisi, over more than thirty years of teaching.</h2>"),
    # "In italiano. Il corso"
    ([IT], "&#8220;narrare&#8221;..", "&#8220;narrare&#8221;."),
    ([IT], " target=&#8221;_blank</a>", "</a>"),
    ([EN], " target=&#8221;_blank&#8221; </a>", "</a>"),
    # Yidali
    ([IT, EN], "<p>译”大利》", "<p>《译大利》"),
    ([IT], ">Download the flyer (PDF)<", ">Scarica il volantino (PDF)<"),
    # An empty link to the old site, next to the Yidali 6 cover.
    ([IT, EN], '<a href="https://www.aliassisi.it/wp-content/uploads/2015/08/chiucchiu_yidali_6.jpg" target="_blank" rel="noopener">\xa0 </a>', ""),
    # Viva l'Italiano
    ([IT], "pernsato per bambini", "pensato per bambini"),
    ([IT], "si priviegia la scrittura", "si privilegia la scrittura"),
    ([IT], "Il videocorso è on line gratuitamente.", "Il videocorso è disponibile online, gratuitamente."),
    # Arte e Metodo / Italiano in
    ([IT], '<a href="http://www.aliassisi.it/arte-e-metodo/" target="_blank" rel="noopener noreferrer"><em>Arte e Metodo</em></a>',
     "<em>Arte e Metodo</em>"),
    ([IT], "contiene meteriali per", "contiene materiali per"),
    ([IT], "un vocabolario e graduato e vario", "un vocabolario graduato e vario"),
    ([IT], "attività e esercizi sulle preposizioni", "attività ed esercizi sulle preposizioni"),
    ([IT], "pensati per comprensione e la produzione", "pensati per la comprensione e la produzione"),
    ([IT, EN], ">Malta Indipendent<", ">Malta Independent<"),
    ([IT], ">Sample pdf<", ">Estratto (PDF)<"),
    ([IT], "parametri del Common European Framework of Reference.", "parametri del Quadro Comune Europeo di Riferimento per le Lingue."),
    ([IT], "capacità di comprendere i testi letterali", "capacità di comprendere i testi letterari"),
    ([IT], "dell’organizzazione gererchica", "dell’organizzazione gerarchica"),
    ([IT], "Le mire del libro sono state pensate relativamente alle aree delle preghiere",
     "Il libro copre le aree delle preghiere"),
    # Configurator box at the foot of the page (also on the Italian home).
    ([IT, "index.html"], "Course configurator<br>", "Configura il tuo corso<br>"),
    ([IT, "index.html"], "naviga fra i nostri corsi e non esitare a contattarci!", "Naviga fra i nostri corsi e non esitare a contattarci!"),
]

# Captions of the contrastive grammar covers. On the English page the gallery
# is a copy of the Italian one (postprocess 7i).
CAPTIONS = {
    IT: {"English": "Inglese", "French": "Francese", "Deutsch": "Tedesco", "Spanish": "Spagnolo",
         "Poruguese": "Portoghese", "Greek": "Greco", "Hungarian": "Ungherese", "Polish": "Polacco",
         "Russian": "Russo", "Turkish": "Turco", "Rumenian": "Romeno", "Serbian": "Serbo",
         "Korean": "Coreano", "Chinese": "Cinese", "Arab": "Arabo"},
    EN: {"Italiano": "Italian", "Deutsch": "German", "Poruguese": "Portuguese",
         "Rumenian": "Romanian", "Arab": "Arabic"},
}
CAPTION = re.compile(r"(gallery-caption'[^>]*>\s*)([^<]*?)(\s*</figcaption>)")

# Typos in the footer and the contact popup, on every page.
SITEWIDE = [
    ("WhatsAPP", "WhatsApp"),
    (">Adress<", ">Address<"),
]

missing = []
pages = {}


def page(rel):
    if rel not in pages:
        pages[rel] = read(os.path.join(site, rel))
    return pages[rel]


for rels, old, new in FIXES:
    for rel in rels:
        text = page(rel)
        if old in text:
            pages[rel] = text.replace(old, new)
        elif new not in text:
            missing.append(f"{rel}: {old[:60]!r}")

for rel, names in CAPTIONS.items():
    text = page(rel)
    found = set()

    def caption(m, names=names):
        if m.group(2) in names:
            found.add(m.group(2))
            return m.group(1) + names[m.group(2)] + m.group(3)
        return m.group(0)

    text = CAPTION.sub(caption, text)
    done = {g[1] for g in CAPTION.findall(text)}
    for name, new in names.items():
        if name not in found and new not in done:
            missing.append(f"{rel}: caption {name!r}")
    pages[rel] = text

for rel, text in pages.items():
    write(os.path.join(site, rel), text)

changed = 0
for dirpath, _, files in os.walk(site):
    if os.path.relpath(dirpath, site).split(os.sep)[0] in ("pagefind", ".git", ".github"):
        continue
    for name in files:
        if not name.endswith(".html"):
            continue
        path = os.path.join(dirpath, name)
        text = read(path)
        new = text
        for old, rep in SITEWIDE:
            new = new.replace(old, rep)
        if new != text:
            write(path, new)
            changed += 1

print(f"text fixes: {len(pages)} pages, footer typos in {changed} files")
for m in missing:
    print("  not found:", m)
