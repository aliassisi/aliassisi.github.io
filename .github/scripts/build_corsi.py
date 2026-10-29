#!/usr/bin/env python3
"""Fill the main content of the course pages from data/ali.json.

Usage:
  python3 -I .github/scripts/build_corsi.py SITE_DIR [--oggi YYYY-MM-DD]

Each course page keeps its crawled WordPress page: header, menu, footer,
language links, global CSS and JS. Only the content of <div id="main"> is
replaced, with a template filled from the course's block in
SITE_DIR/data/ali.json:
  Italian pages ("pagine"):       .github/templates/corso-contenuto.html
  English pages ("en"."pagine"):  .github/templates/corso-contenuto-en.html
Fields in a course's "en" block replace the Italian ones for English pages.
The private and online lessons pages come from the "privati" and "online"
blocks. Their "modello" names the template: corso-privato.html and
corso-privato-en.html, corso-online.html and corso-online-en.html.
The page head gets a link to assets/ali/ali-course.css
(source: .github/templates/ali-course.css).

Start dates before today are left out, and so are closures that have ended.
--oggi sets "today", for tests.

Safe to run again on a page it already changed. Run it after every crawl.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "..", "templates")
CSS_OUT = os.path.join("assets", "ali", "ali-course.css")
INIZIO, FINE = "<!-- ali-course -->", "<!-- /ali-course -->"
SLOT_MATTINA = 4

LINGUE = {
    "it": {
        "modello": "corso-contenuto.html",
        "iscriviti": "Iscriviti", "formula": "Formula",
        "mesi": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
                 "agosto", "settembre", "ottobre", "novembre", "dicembre"],
        "giorni": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"],
        "lezione": "lezione", "lezioni": "lezioni",
        "libero": "libero", "mattina": "mattina", "pomeriggio": "pomeriggio",
        "al_mattino": " al mattino", "ind_pomeriggio": " individuali al pomeriggio",
        "mix": "{g} di gruppo + {i} individuali",
        "durata": "ogni lezione dura 50 minuti", "durata_mix": "{mix}, da 50 minuti",
        "prezzi": "di gruppo · 50 minuti ciascuna", "prezzi_mix": "{mix} · 50 minuti ciascuna",
        "sett": "sett.", "sett_plur": "sett.",
        "nessuna_data": "Nuove date in arrivo. Scrivici per sapere quando inizia il prossimo corso.",
        "libro_titolo": "Materiale didattico", "copertina": "Copertina di {t}",
        "temi_titolo": "I temi", "iscriviti_tema": "Iscriviti con questo tema",
    },
    "en": {
        "modello": "corso-contenuto-en.html",
        "iscriviti": "Enrol", "formula": "Format",
        "mesi": ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"],
        "giorni": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "lezione": "lesson", "lezioni": "lessons",
        "libero": "free", "mattina": "morning", "pomeriggio": "afternoon",
        "al_mattino": " in the morning", "ind_pomeriggio": " (one-to-one) in the afternoon",
        "mix": "{g} group + {i} one-to-one",
        "durata": "each lesson lasts 50 minutes", "durata_mix": "{mix}, 50 minutes each",
        "prezzi": "group · 50 minutes each", "prezzi_mix": "{mix} · 50 minutes each",
        "sett": "wk", "sett_plur": "wks",
        "nessuna_data": "New dates coming soon. Write to us to find out when the next course starts.",
        "libro_titolo": "Course materials", "copertina": "Cover of {t}",
        "temi_titolo": "The themes", "iscriviti_tema": "Enrol with this theme",
    },
}


def esc(s):
    return html.escape(s, quote=True)


def data(s):
    return datetime.date.fromisoformat(s)


def lezioni(n, L):
    return f"{n} {L['lezione'] if n == 1 else L['lezioni']}"


def cella(giorno, n, slot, quando, L):
    if not n:
        return (f'<div class="pm" role="cell" aria-label="{giorno[0].upper() + giorno[1:]}: '
                f'{L[quando]} {L["libero"]}">{L["libero"]}</div>')
    bars = '<i class="on"></i>' * n + "<i></i>" * (slot - n)
    tipo = L["al_mattino"] if quando == "mattina" else L["ind_pomeriggio"]
    return (f'<div class="am" role="cell" aria-label="{giorno[0].upper() + giorno[1:]}: '
            f'{lezioni(n, L)}{tipo}"><span class="bars">{bars}</span>'
            f'<span class="n">{lezioni(n, L)}</span></div>')


def riga(conti, quando, L):
    slot = max([SLOT_MATTINA if quando == "mattina" else 0] + conti)
    return "".join(cella(g, n, slot, quando, L) for g, n in zip(L["giorni"], conti))



def date_inizio(date, oggi, L):
    anni = {}
    for d in date:
        if d >= oggi:
            anni.setdefault(d.year, []).append(f"<li>{d.day} {L['mesi'][d.month - 1]}</li>")
    if not anni:
        return f"          <p>{L['nessuna_data']}</p>"
    righe = []
    for anno, li in anni.items():
        righe.append(f"          <h3>{anno}</h3>")
        if len(li) == 1:
            righe.append(f'          <ul class="dates">{li[0]}</ul>')
        else:
            righe.append('          <ul class="dates">')
            for i in range(0, len(li), 6):
                righe.append("            " + "".join(li[i:i + 6]))
            righe.append("          </ul>")
    return "\n".join(righe)


def periodo(a, b, L):
    M = L["mesi"]
    if a == b:
        return f"{a.day} {M[a.month - 1]}"
    if (a.year, a.month) == (b.year, b.month):
        return f"{a.day}–{b.day} {M[a.month - 1]}"
    if a.year == b.year:
        return f"{a.day} {M[a.month - 1]} – {b.day} {M[b.month - 1]}"
    return f"{a.day} {M[a.month - 1]} {a.year} – {b.day} {M[b.month - 1]} {b.year}"


def libro(b, L):
    """The section on a course's own book, or nothing if the course has none.
    b: {"titolo", "copertina", "testo": [...], "voci": [...], "dopo": [...]}"""
    if not b:
        return ""
    righe = ['  <section id="libro">', '    <div class="wrap">',
             f'      <h2>{L["libro_titolo"]}</h2>', '      <div class="book">',
             f'        <img src="{b["copertina"]}" alt="{esc(L["copertina"].format(t=b["titolo"]))}"'
             ' width="768" height="1024" loading="lazy">',
             '        <div>', f'          <h3>{esc(b["titolo"])}</h3>']
    righe += [f"          <p>{esc(p)}</p>" for p in b["testo"]]
    if b.get("voci"):
        righe.append("          <ul>" + "".join(f"<li>{esc(v)}</li>" for v in b["voci"]) + "</ul>")
    righe += [f"          <p>{esc(p)}</p>" for p in b.get("dopo", [])]
    righe += ["        </div>", "      </div>", "    </div>", "  </section>", "", ""]
    return "\n".join(righe)


def temi(t, ali, L):
    """The section on the themes a course offers, or nothing if it has none.
    t: {"intro", "voci": [{"titolo", "testo": [...], "link": {"testo", "url"},
    "voce_modulo"}]}. "link" and "voce_modulo" are optional; a theme with
    "voce_modulo" gets its own enrolment link."""
    if not t:
        return ""
    righe = ['  <section id="temi">', '    <div class="wrap">',
             f'      <h2>{L["temi_titolo"]}</h2>', f'      <p class="narrow-l">{esc(t["intro"])}</p>',
             '      <div class="themes">']
    for v in t["voci"]:
        righe += ["        <div>", f'          <h3>{esc(v["titolo"])}</h3>']
        righe += [f"          <p>{esc(p)}</p>" for p in v["testo"]]
        if v.get("link"):
            righe.append(f'          <p><a class="inl" href="{esc(v["link"]["url"])}">{esc(v["link"]["testo"])}</a></p>')
        if v.get("voce_modulo"):
            url = ali["modulo_iscrizione"] + quote(v["voce_modulo"], safe="")
            righe.append(f'          <p><a class="btn small" href="{esc(url)}">{L["iscriviti_tema"]}</a></p>')
        righe.append("        </div>")
    righe += ["      </div>", "    </div>", "  </section>", "", ""]
    return "\n".join(righe)


def chiusure(lista, oggi, lingua):
    L = LINGUE[lingua]
    anni = {}
    for c in lista:
        a, b = data(c["dal"]), data(c["al"])
        if b >= oggi:
            anni.setdefault(a.year, []).append(f"{periodo(a, b, L)}, {esc(c[lingua])}")
    righe = []
    for anno, voci in anni.items():
        righe.append(f"            <dt>{anno}</dt>")
        righe.append(f"            <dd>{'<br>'.join(voci)}</dd>")
    return "\n".join(righe)


def contenuto(modello, ali, c, oggi, lingua):
    L = LINGUE[lingua]
    if sum(c["mattina"]) + sum(c["pomeriggio"]) != c["ore"]:
        sys.exit(f"{c['id']}: ore = {c['ore']}, ma mattina + pomeriggio fanno "
                 f"{sum(c['mattina']) + sum(c['pomeriggio'])}")
    tariffe = ali["tariffe"][c["tariffa"]]
    ind = sum(c["pomeriggio"])
    mix = L["mix"].format(g=sum(c["mattina"]), i=ind) if ind else ""
    valori = {
        "ore": str(c["ore"]),
        "durata_nota": L["durata_mix"].format(mix=mix) if mix else L["durata"],
        "livelli": esc(c["livelli"]),
        "studenti_min": str(c["studenti_min"]),
        "studenti_max": str(c["studenti_max"]),
        "studenti_media": esc(c["studenti_media"]),
        "materiale": esc(c["materiale"]),
        "materiale_nota": esc(c["materiale_nota"]),
        "riga_mattina": riga(c["mattina"], "mattina", L),
        "riga_pomeriggio": riga(c["pomeriggio"], "pomeriggio", L),
        "dettagli": "\n".join(f"          <p>{esc(p)}</p>" for p in c["dettagli"]),
        "libro": libro(c.get("libro"), L),
        "temi": temi(c.get("temi"), ali, L),
        "date_inizio": date_inizio(sorted(data(d) for d in ali["date_inizio"]), oggi, L),
        "chiusure": chiusure(ali["chiusure"], oggi, lingua),
        "intestazione_prezzi": "".join(
            f'<th class="num">{t["from"]}{"" if t["from"] == t["to"] else "–" + str(t["to"])} '
            f'{L["sett"] if t["to"] == 1 else L["sett_plur"]}</th>'
            for t in tariffe),
        "n_tariffe": str(len(tariffe)),
        "nota_prezzi": L["prezzi_mix"].format(mix=mix) if mix else L["prezzi"],
        "celle_prezzi": "".join(f'<td class="num">{t["ppw"]} €</td>' for t in tariffe),
        # One address, used by both enrolment buttons.
        "iscrizione": ali["modulo_iscrizione"] + quote(c["voce_modulo"], safe=""),
        "altri_corsi": altri_corsi(ali, c["pagine"], lingua),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: valori[m.group(1)], modello)


def altri_corsi(ali, pagine, lingua):
    altri = [{**o, **o.get(lingua, {})} if lingua != "it" else o for o in ali["altri_corsi"]]
    # A course page does not list itself.
    return "\n".join(
        f'        <li><a href="https://aliassisi.github.io/{o["url"]}/index.html">'
        f'<b>{esc(o["nome"])}</b><small>{"<br>".join(esc(x) for x in o["nota"])}</small></a></li>'
        for o in altri if o["url"] not in pagine)


def contenuto_lezioni(modello, ali, it, c, lingua):
    """A page of lessons sold by the lesson ("privati", "online").
    it: the Italian block; c: the same block, with its "en" fields merged in
    for English. Each entry of "formule" is a row of the price table, with
    "prezzi" {number of lessons: price}; in the "en" block, "formule" holds
    only the texts, in the same order. A row with "voce_modulo" gets its own
    enrolment link to the main form; a block with "modulo" uses that form instead."""
    L = LINGUE[lingua]
    formule = it["formule"]
    if lingua != "it":
        formule = [{**f, **e} for f, e in zip(formule, c["formule"])]
    colonne = sorted({int(n) for f in formule for n in f["prezzi"]})
    if "modulo" in c:
        url = [c["modulo"]] * len(formule)
    else:
        url = [ali["modulo_iscrizione"] + quote(f["voce_modulo"], safe="") for f in formule]
    bottoni = "modulo" not in c
    testa = (f'<th>{L["formula"]}</th>'
             + "".join(f'<th class="num">{lezioni(n, L)}</th>' for n in colonne)
             + (f'<th>{L["iscriviti"]}</th>' if bottoni else ""))
    righe = "\n".join(
        f'            <tr><td>{esc(f["nome"])}<small>{esc(f["nota"])}</small></td>'
        + "".join(f'<td class="num">{f["prezzi"][str(n)]} €</td>' if str(n) in f["prezzi"]
                  else '<td class="num">–</td>' for n in colonne)
        + (f'<td><a class="btn small" href="{esc(u)}">{L["iscriviti"]}</a></td>' if bottoni else "")
        + "</tr>"
        for f, u in zip(formule, url))
    valori = {
        "intestazione_prezzi": testa,
        "righe_prezzi": righe,
        # The main button opens the form of the first row.
        "iscrizione": esc(url[0]),
        "altri_corsi": altri_corsi(ali, c["pagine"], lingua),
    }
    if "dal" in c:
        dal, al = data(c["dal"]), data(c["al"])
        valori["anno"] = str(dal.year) if dal.year == al.year else f"{dal.year}–{al.year}"
        valori["periodo"] = periodo(dal, al, L)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: valori[m.group(1)], modello)


def testata_wordpress(main):
    """The page's own top section (title over the background video), with the
    Elementor wrapper it needs, closed right after it."""
    w = re.search(r'<div data-elementor-type="product"[^>]*>', main)
    if not w:
        return None
    inizio = main.index("<section", w.end())
    fine = main.index("</section>", inizio) + len("</section>")
    return w.group(0) + main[inizio:fine] + "\n</div>\n"


def in_wordpress(s, blocco_html, css_href, p, hero):
    """Put blocco_html in the WordPress page s, below the page's own top
    section with the video. Header, top section and footer stay as they are;
    only the line under the title comes from the data ("hero").
    Later runs replace what is between the markers."""
    blocco = f"{INIZIO}\n{blocco_html}{FINE}\n"
    if INIZIO in s:
        s = re.sub(re.escape(INIZIO) + r".*?" + re.escape(FINE) + r"\n",
                   lambda m: blocco, s, count=1, flags=re.S)
    else:
        m = re.search(r'(<div id="main" role="main"[^>]*>\n)(.*?)(?=[ \t]*</div><!-- #main -->)', s, re.S)
        if not m:
            sys.exit(f'{p}: no <div id="main"> found. Is it the crawled WordPress page?')
        testata = testata_wordpress(m.group(2))
        if not testata:
            sys.exit(f"{p}: no Elementor top section found in <div id=\"main\">.")
        s = s[:m.start(2)] + testata + blocco + s[m.end(2):]
    s = re.sub(r'(data-id="192f165"[^>]*>\s*<div class="elementor-widget-container">\s*).*?(\s*</div>)',
               lambda m: m.group(1) + esc(hero) + m.group(2), s, count=1, flags=re.S)
    if 'id="ali-course-css"' not in s:
        s = s.replace("</head>", f'<link rel="stylesheet" id="ali-course-css" href="{css_href}">\n</head>', 1)
    return s


def leggi_modello(nome):
    with open(os.path.join(TEMPLATES, nome), encoding="utf-8") as f:
        # The template starts with a comment for editors. Leave it out of the pages.
        return re.sub(r"\A<!--.*?-->\n", "", f.read(), flags=re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--oggi", type=data, default=datetime.date.today())
    args = ap.parse_args()

    with open(os.path.join(args.site, "data", "ali.json"), encoding="utf-8") as f:
        ali = json.load(f)
    modelli = {lingua: leggi_modello(L["modello"]) for lingua, L in LINGUE.items()}

    css = os.path.join(args.site, CSS_OUT)
    os.makedirs(os.path.dirname(css), exist_ok=True)
    with open(os.path.join(TEMPLATES, "ali-course.css"), encoding="utf-8") as f:
        testo = f.read()
    with open(css, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)

    a_lezione = [ali["privati"], ali["online"]]
    for c in ali["corsi"] + a_lezione:
        versioni = [("it", c)]
        if "en" in c:
            versioni.append(("en", {**c, **c["en"]}))
        for lingua, corso in versioni:
            if any(c is b for b in a_lezione):
                nome = c["modello"] + ("" if lingua == "it" else "-" + lingua) + ".html"
                blocco = contenuto_lezioni(leggi_modello(nome), ali, c, corso, lingua)
            else:
                blocco = contenuto(modelli[lingua], ali, corso, args.oggi, lingua)
            for p in corso["pagine"]:
                dest = os.path.join(args.site, p, "index.html")
                with open(dest, encoding="utf-8") as f:
                    s = f.read()
                href = os.path.relpath(css, os.path.dirname(dest)).replace(os.sep, "/")
                with open(dest, "w", encoding="utf-8", newline="\n") as f:
                    f.write(in_wordpress(s, blocco, href, p, corso["hero"]))
                print(f"wrote {p}/index.html ({lingua})")


if __name__ == "__main__":
    main()
