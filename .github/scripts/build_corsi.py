#!/usr/bin/env python3
"""Build the group course pages from data/ali.json.

Usage:
  python3 -I .github/scripts/build_corsi.py SITE_DIR [--oggi YYYY-MM-DD]

SITE_DIR holds data/ali.json. For each course in it, the script fills
.github/templates/corso-gruppo.html and writes SITE_DIR/<page>/index.html.
A course with "contenitore": "wordpress" keeps the crawled WordPress page
(header, menu, footer, global CSS and JS). Only the content of its
<div id="main"> is replaced, with corso-contenuto.html, and the page head
links assets/ali/ali-course.css.
Start dates before today are left out, and so are closures that have ended.
--oggi sets "today", for tests.

It also points both configurators (configuratore/, en/configuratore/) at
data/ali.json. That step is safe to run again on a page it already changed.

Run it after every crawl and before every deploy. The deploy workflow also
runs it every night, so past start dates drop off the site.
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

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"]
NUMERI = {1: "una", 2: "due", 3: "tre", 4: "quattro", 5: "cinque", 6: "sei"}
SLOT_MATTINA = 4


def esc(s):
    return html.escape(s, quote=True)


def data(s):
    return datetime.date.fromisoformat(s)


def lezioni(n):
    return f"{n} lezione" if n == 1 else f"{n} lezioni"


def cella(giorno, n, slot, quando):
    if not n:
        return (f'<div class="pm" role="cell" aria-label="{giorno.capitalize()}: '
                f'{quando} libero">libero</div>')
    bars = '<i class="on"></i>' * n + "<i></i>" * (slot - n)
    tipo = " al mattino" if quando == "mattina" else " individuali al pomeriggio"
    return (f'<div class="am" role="cell" aria-label="{giorno.capitalize()}: '
            f'{lezioni(n)}{tipo}"><span class="bars">{bars}</span>'
            f'<span class="n">{lezioni(n)}</span></div>')


def riga(conti, quando):
    slot = max([SLOT_MATTINA if quando == "mattina" else 0] + conti)
    return "".join(cella(g, n, slot, quando) for g, n in zip(GIORNI, conti))


def giorni_frase(conti):
    """[4,4,4,4,2] -> 'quattro al giorno da lunedì a giovedì, due il venerdì'"""
    parti = []
    for n in dict.fromkeys(c for c in conti if c):
        idx = [i for i, c in enumerate(conti) if c == n]
        if len(idx) > 1 and idx == list(range(idx[0], idx[-1] + 1)):
            parti.append(f"{NUMERI[n]} al giorno da {GIORNI[idx[0]]} a {GIORNI[idx[-1]]}")
        else:
            parti.append(NUMERI[n] + " " + " e ".join("il " + GIORNI[i] for i in idx))
    return ", ".join(parti)


def date_inizio(date, oggi):
    anni = {}
    for d in date:
        if d >= oggi:
            anni.setdefault(d.year, []).append(f"<li>{d.day} {MESI[d.month - 1]}</li>")
    if not anni:
        return '          <p>Nuove date in arrivo. Scrivici per sapere quando inizia il prossimo corso.</p>'
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


def periodo(a, b):
    if a == b:
        return f"{a.day} {MESI[a.month - 1]}"
    if (a.year, a.month) == (b.year, b.month):
        return f"{a.day}–{b.day} {MESI[a.month - 1]}"
    if a.year == b.year:
        return f"{a.day} {MESI[a.month - 1]} – {b.day} {MESI[b.month - 1]}"
    return f"{a.day} {MESI[a.month - 1]} {a.year} – {b.day} {MESI[b.month - 1]} {b.year}"


def chiusure(lista, oggi):
    anni = {}
    for c in lista:
        a, b = data(c["dal"]), data(c["al"])
        if b >= oggi:
            anni.setdefault(a.year, []).append(f"{periodo(a, b)}, {esc(c['it'])}")
    righe = []
    for anno, voci in anni.items():
        righe.append(f"            <dt>{anno}</dt>")
        righe.append(f"            <dd>{'<br>'.join(voci)}</dd>")
    return "\n".join(righe)


def gruppo_e_individuali(c):
    ind = sum(c["pomeriggio"])
    return f"{sum(c['mattina'])} di gruppo + {ind} individuali" if ind else ""


def pagina(modello, ali, c, oggi):
    if sum(c["mattina"]) + sum(c["pomeriggio"]) != c["ore"]:
        sys.exit(f"{c['id']}: ore = {c['ore']}, ma mattina + pomeriggio fanno "
                 f"{sum(c['mattina']) + sum(c['pomeriggio'])}")
    tariffe = ali["tariffe"][c["tariffa"]]
    mix = gruppo_e_individuali(c)
    nota = f"{lezioni(c['ore'])} da 50 minuti: {giorni_frase(c['mattina'])}"
    if mix:
        nota = (f"{sum(c['mattina'])} lezioni di gruppo al mattino: {giorni_frase(c['mattina'])}. "
                f"{sum(c['pomeriggio'])} lezioni individuali al pomeriggio: "
                f"{giorni_frase(c['pomeriggio'])}. Ogni lezione dura 50 minuti")
    altri = []
    for o in ali["corsi"]:
        if o["id"] != c["id"]:
            altri.append((o["url_it"], o["nome"],
                          f"{o['ore']} lezioni a settimana<br>{gruppo_e_individuali(o) or 'di gruppo'}"))
    for o in ali["altri_corsi"]:
        altri.append((o["url"], o["nome"], esc(o["nota"])))
    corrente = ' aria-current="page"'
    valori = {
        "nome": esc(c["nome"]),
        "descrizione": esc(c["descrizione"]),
        "menu_standard": corrente if c["menu"] == "standard" else "",
        "menu_intensivi": corrente if c["menu"] == "intensivi" else "",
        "url_it": c["url_it"],
        "url_en": c["url_en"],
        "hero": esc(c["hero"]),
        "ore": str(c["ore"]),
        "durata_nota": f"{mix}, da 50 minuti" if mix else "ogni lezione dura 50 minuti",
        "livelli": esc(c["livelli"]),
        "studenti_min": str(c["studenti_min"]),
        "studenti_max": str(c["studenti_max"]),
        "studenti_media": esc(c["studenti_media"]),
        "riga_mattina": riga(c["mattina"], "mattina"),
        "riga_pomeriggio": riga(c["pomeriggio"], "pomeriggio"),
        "nota_settimana": nota + ".",
        "dettagli": "\n".join(f"          <p>{esc(p)}</p>" for p in c["dettagli"]),
        "date_inizio": date_inizio(sorted(data(d) for d in ali["date_inizio"]), oggi),
        "chiusure": chiusure(ali["chiusure"], oggi),
        "intestazione_prezzi": "".join(
            f'<th class="num">{t["from"]}{"" if t["from"] == t["to"] else "–" + str(t["to"])} sett.</th>'
            for t in tariffe),
        "nota_prezzi": f"{mix} · 50 minuti ciascuna" if mix else "di gruppo · 50 minuti ciascuna",
        "celle_prezzi": "".join(f'<td class="num">{t["ppw"]} €</td>' for t in tariffe),
        # One address, used by both enrolment buttons.
        "iscrizione": ali["modulo_iscrizione"] + quote(c["voce_modulo"], safe=""),
        "altri_corsi": "\n".join(
            f'        <li><a href="https://aliassisi.github.io/{u}/index.html">'
            f"<b>{esc(n)}</b><small>{s}</small></a></li>" for u, n, s in altri),
    }
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: valori[m.group(1)], modello)
    return out


def in_wordpress(s, contenuto, css_href, p):
    """Put contenuto in the WordPress page s, between header and footer.
    Safe to run again: later runs replace what is between the markers."""
    blocco = f"{INIZIO}\n{contenuto}{FINE}\n"
    if INIZIO in s:
        s = re.sub(re.escape(INIZIO) + r".*?" + re.escape(FINE) + r"\n",
                   lambda m: blocco, s, count=1, flags=re.S)
    else:
        s, n = re.subn(r'(<div id="main" role="main"[^>]*>\n).*?(?=</div><!-- #main -->)',
                       lambda m: m.group(1) + blocco, s, count=1, flags=re.S)
        if n != 1:
            sys.exit(f'{p}: no <div id="main"> found. Is it the crawled WordPress page?')
    if 'id="ali-course-css"' not in s:
        s = s.replace("</head>", f'<link rel="stylesheet" id="ali-course-css" href="{css_href}">\n</head>', 1)
    return s


def leggi_modello(nome):
    with open(os.path.join(TEMPLATES, nome), encoding="utf-8") as f:
        # The template starts with a comment for editors. Leave it out of the pages.
        return re.sub(r"\A<!--.*?-->\n", "", f.read(), flags=re.S)


# --- configurator -----------------------------------------------------------

def configuratore(s, radice):
    """Make the configurator read prices, start dates and closures from
    data/ali.json. Returns the page unchanged if it already does."""
    if "data/ali.json" in s:
        return s
    passi = [
        (r"<script>\n\(function\(\)\{\n(?=/\* ---------- PREZZI)",
         "<script>\nfetch('" + radice + "data/ali.json').then(function(r){return r.json();}).then(function(ALI){\n"),
        (r"var TIER_STD=\[.*?\];", "var TIER_STD=ALI.tariffe.standard;"),
        (r"var TIER_INT=\[.*?\];", "var TIER_INT=ALI.tariffe.intensivo;"),
        (r"var TIER_SINT=\[.*?\];", "var TIER_SINT=ALI.tariffe.super_intensivo;"),
        (r"var CL=\[.*?\n\];",
         "var CL=ALI.chiusure.map(function(c){var f=c.dal.split('-'),t=c.al.split('-');"
         "return {label:c.en,from:[+f[0],+f[1],+f[2]],to:[+t[0],+t[1],+t[2]]};});"),
        (r"(function sameDay\(a,b\)\{[^\n]*\n)",
         r"\1(function(){var oggi=iso(new Date()),sel=document.getElementById('cfg-startsel'),"
         r"altra=sel.querySelector('option[value=\"custom\"]');"
         r"ALI.date_inizio.forEach(function(s){if(s<oggi)return;"
         r"var o=document.createElement('option');o.value=s;o.textContent=fmtD(fromIso(s));"
         r"sel.insertBefore(o,altra);});})();\n"),
        (r"(\n[ \t]*<option value=\"\d{4}-\d\d-\d\d\">[^<]*</option>)+", ""),
        (r"cfgUpdate\(\);\n\}\)\(\);\n</script>", "cfgUpdate();\n});\n</script>"),
    ]
    for pat, new in passi:
        s, n = re.subn(pat, new, s, count=1, flags=re.S)
        if n != 1:
            sys.exit(f"configuratore: pattern not found: {pat[:60]}")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--oggi", type=data, default=datetime.date.today())
    args = ap.parse_args()

    with open(os.path.join(args.site, "data", "ali.json"), encoding="utf-8") as f:
        ali = json.load(f)
    modelli = {"pagina": leggi_modello("corso-gruppo.html"),
               "wordpress": leggi_modello("corso-contenuto.html")}

    css = os.path.join(args.site, CSS_OUT)
    os.makedirs(os.path.dirname(css), exist_ok=True)
    with open(os.path.join(TEMPLATES, "ali-course.css"), encoding="utf-8") as f:
        testo = f.read()
    with open(css, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)

    for c in ali["corsi"]:
        contenitore = c.get("contenitore", "pagina")
        out = pagina(modelli[contenitore], ali, c, args.oggi)
        for p in c["pagine"]:
            dest = os.path.join(args.site, p, "index.html")
            if contenitore == "wordpress":
                with open(dest, encoding="utf-8") as f:
                    wp = f.read()
                href = os.path.relpath(css, os.path.dirname(dest)).replace(os.sep, "/")
                scritto = in_wordpress(wp, out, href, p)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                scritto = out
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(scritto)
            print(f"wrote {p}/index.html ({contenitore})")

    for p, radice in (("configuratore", "../"), ("en/configuratore", "../../")):
        dest = os.path.join(args.site, p, "index.html")
        with open(dest, encoding="utf-8") as f:
            s = f.read()
        nuovo = configuratore(s, radice)
        if nuovo != s:
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(nuovo)
            print(f"pointed {p} at data/ali.json")


if __name__ == "__main__":
    main()
