#!/usr/bin/env python3
"""Build the course configurator pages from data/alia.json and data/configuratore.json.

Usage:
  python3 -I .github/scripts/build_configuratore.py SITE_DIR

The configurator is configuratore/index.html (Italian) and
en/configuratore/index.html (English). Each page keeps its crawled WordPress
page; only the HTML widget with the configurator is replaced by:
  - a link to assets/alia/configuratore.css (source: .github/templates/configuratore.css)
  - <div id="cfg-wrap">, filled by assets/alia/configuratore.js
    (source: .github/templates/configuratore.js)
  - the data, as JSON in <script id="cfg-dati">.
Courses, prices, start dates and closures come from alia.json. Accommodation,
extra services, activities and payment methods come from configuratore.json.

A course page opens the configurator with ?corso=<id> (the course id in
alia.json, or "privati", "online", "calendimaggio"). The configurator then
shows only that course. &tema=N picks a theme, &formula=N a row of the
private or online lessons price table. &inizio=YYYY-MM-DD (a Monday) and
&settimane=N fill in the start and length. With &da=calendario (links from
the comparator) the course, start and length show as one summary line.

The course comparator is on calendar-and-fees/index.html and
en/calendar-and-fees/index.html, in <!-- comparatore --> ... <!-- /comparatore -->:
assets/alia/comparatore.css and .js (sources in .github/templates/) and the
data in <script id="cmp-dati">, from the same sources as the configurator.
Its buttons open the configurator with ?corso=&inizio=&settimane=&da=calendario.

Safe to run again on a page it already changed.
"""
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "..", "templates")
INIZIO, FINE = "<!-- configuratore -->", "<!-- /configuratore -->"
PAGINE = {"it": "configuratore", "en": "en/configuratore"}
ICONE = {
    "standard": "ti-book", "intensivo": "ti-books", "super_intensivo": "ti-bolt",
    "esame_intensivo": "ti-certificate", "esame_super": "ti-rosette",
    "religiosi_22": "ti-building-church", "religiosi_26": "ti-building-church",
    "tematico_22": "ti-palette", "tematico_26": "ti-photo",
    "privati": "ti-user", "online": "ti-device-laptop", "calendimaggio": "ti-flag",
}
# The course comparator on the Calendar and fees pages. It replaces the old
# "#dw-wrap" calculator, and the page's own menu links to it.
INIZIO_CMP, FINE_CMP = "<!-- comparatore -->", "<!-- /comparatore -->"
PAGINE_CMP = {"it": "calendar-and-fees", "en": "en/calendar-and-fees"}
ANCORA_CMP = "cmp-wrap"
VOCE_MENU_CMP = {
    "it": ("Calcola il costo", "Confronta i corsi"),
    "en": ("Cost calculator", "Compare courses"),
}
# The three columns (by rate) and their courses, in this order.
GRUPPI_CMP = [
    ("standard", ["standard"]),
    ("intensivo", ["intensivo", "esame_intensivo", "tematico_22", "religiosi_22"]),
    ("super_intensivo", ["super_intensivo", "esame_super", "tematico_26", "religiosi_26"]),
]
# Short names in the comparator: (name, note). A note of None lists the course's themes.
VARIANTI_CMP = {
    "it": {
        "standard": ("Standard", ""),
        "intensivo": ("Intensivo", ""), "super_intensivo": ("Super intensivo", ""),
        "esame_intensivo": ("Preparazione all’esame", "CILS, Roma Tre"),
        "esame_super": ("Preparazione all’esame", "CILS, Roma Tre"),
        "tematico_22": ("Tematico", None), "tematico_26": ("Tematico", None),
        "religiosi_22": ("Corso per religiosi", ""), "religiosi_26": ("Corso per religiosi", ""),
    },
    "en": {
        "standard": ("Standard", ""),
        "intensivo": ("Intensive", ""), "super_intensivo": ("Super intensive", ""),
        "esame_intensivo": ("Certification exam prep.", "CILS, Roma Tre"),
        "esame_super": ("Certification exam prep.", "CILS, Roma Tre"),
        "tematico_22": ("Thematic", None), "tematico_26": ("Thematic", None),
        "religiosi_22": ("Course for religious students", ""), "religiosi_26": ("Course for religious students", ""),
    },
}
# Links of the enrolment form to the conditions the student accepts.
LINK = {
    "it": {"termini": "../termini-e-condizioni/index.html", "privacy": "../privacy-policy/index.html"},
    "en": {"termini": "../terms-and-conditions/index.html", "privacy": "../privacy-policy/index.html"},
}


def testo(v, lingua):
    """A text that is either one string or {"it": ..., "en": ...}."""
    return v if isinstance(v, str) else v[lingua]


def in_lingua(blocco, lingua):
    """A course block with its "en" fields merged in for English."""
    return {**blocco, **blocco["en"]} if lingua != "it" and "en" in blocco else blocco


def corsi(ali, lingua):
    out = []
    for c in ali["corsi"]:
        t = in_lingua(c, lingua)
        out.append({
            "id": c["id"], "tipo": "settimane", "icona": ICONE[c["id"]],
            "nome": t["nome"], "livelli": t["livelli"], "ore": c["ore"],
            "gruppo": sum(c["mattina"]), "individuali": sum(c["pomeriggio"]),
            "tariffe": ali["tariffe"][c["tariffa"]],
            "temi": [v["titolo"] for v in t.get("temi", {}).get("voci", [])],
        })
    for chiave in ("privati", "online"):
        c = ali[chiave]
        t = in_lingua(c, lingua)
        formule = c["formule"]
        if lingua != "it":
            formule = [{**f, **e} for f, e in zip(formule, t["formule"])]
        out.append({
            "id": chiave, "tipo": "lezioni", "icona": ICONE[chiave], "nome": t["nome"],
            "dal": c.get("dal"), "al": c.get("al"),
            "in_sede": chiave == "privati",
            "formule": [{"nome": f["nome"], "nota": f["nota"], "studenti": f.get("studenti", 1),
                         "prezzi": {int(n): p for n, p in f["prezzi"].items()}} for f in formule],
        })
    c = ali["calendimaggio"]
    out.append({
        "id": "calendimaggio", "tipo": "pacchetto", "icona": ICONE["calendimaggio"],
        "nome": in_lingua(c, lingua)["nome"], "dal": c["dal"], "al": c["al"], "prezzo": c["prezzo"],
    })
    return out


def dati(ali, cfg, lingua):
    return {
        "lingua": lingua,
        "email": cfg["email"],
        # The address of the Google Apps Script that receives enrolments. Empty: email only.
        "invio": cfg.get("invio", ""),
        # The entry test for students who are not beginners.
        "test_ingresso": cfg["test_ingresso"],
        "link": LINK[lingua],
        "corsi": corsi(ali, lingua),
        "date_inizio": sorted(ali["date_inizio"]),
        "chiusure": [{"dal": c["dal"], "al": c["al"], "nome": c[lingua]} for c in ali["chiusure"]],
        "alloggi": [{
            "id": a["id"], "icona": a["icona"], "prezzi": a.get("prezzi"), **a[lingua],
            "camere": [{"id": r["id"], "prezzi": r["prezzi"], **r[lingua]} for r in a.get("camere", [])],
        } for a in cfg["alloggi"]],
        "extra": [{"id": e["id"], "icona": e["icona"], "prezzo": e["prezzo"], "nome": e[lingua]}
                  for e in cfg["extra"]],
        "attivita_settimanali": [testo(a, lingua) for a in cfg["attivita_settimanali"]],
        "attivita": [{"nome": a[lingua], "date": a["date"]} for a in cfg["attivita"]],
        "pagamenti": [{"id": p["id"], "nome": p[lingua]} for p in cfg["pagamenti"]],
    }


def dati_comparatore(ali, cfg, lingua):
    """The data of the course comparator: the same sources as the configurator."""
    d = dati(ali, cfg, lingua)
    per_id = {c["id"]: c for c in ali["corsi"]}
    gruppi = []
    for tariffa, ids in GRUPPI_CMP:
        primo = per_id[ids[0]]
        varianti = []
        for i in ids:
            c = in_lingua(per_id[i], lingua)
            nome, nota = VARIANTI_CMP[lingua][i]
            if nota is None and c.get("temi"):
                # The themes of the course, as "Letteratura, cinema, arte, …".
                temi = [v["titolo"] for v in c["temi"]["voci"]]
                nota = ", ".join([temi[0]] + [t[0].lower() + t[1:] for t in temi[1:]])
            varianti.append({"id": i, "nome": nome, "nota": nota})
        gruppi.append({"ore": primo["ore"], "gruppo": sum(primo["mattina"]),
                       "individuali": sum(primo["pomeriggio"]),
                       "tariffe": ali["tariffe"][tariffa], "varianti": varianti})
    return {"lingua": lingua, "configuratore": "../configuratore/index.html",
            "date_inizio": d["date_inizio"], "chiusure": d["chiusure"],
            "attivita_settimanali": d["attivita_settimanali"], "attivita": d["attivita"],
            "gruppi": gruppi}


def blocco_comparatore(d, css, js):
    j = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (f"{INIZIO_CMP}\n"
            f'<link rel="stylesheet" href="{css}">\n'
            f'<div id="{ANCORA_CMP}" class="ali-ancora"></div>\n'
            f'<script id="cmp-dati" type="application/json">{j}</script>\n'
            f'<script src="{js}"></script>\n'
            f"{FINE_CMP}")


def blocco(d, css, js):
    j = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (f"{INIZIO}\n"
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.10.0/tabler-icons.min.css">\n'
            f'<link rel="stylesheet" href="{css}">\n'
            '<div id="cfg-wrap"></div>\n'
            f'<script id="cfg-dati" type="application/json">{j}</script>\n'
            f'<script src="{js}"></script>\n'
            f"{FINE}")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    site = sys.argv[1]
    with open(os.path.join(site, "data", "alia.json"), encoding="utf-8") as f:
        ali = json.load(f)
    with open(os.path.join(site, "data", "configuratore.json"), encoding="utf-8") as f:
        cfg = json.load(f)

    out = os.path.join(site, "assets", "alia")
    os.makedirs(out, exist_ok=True)
    versione = {}
    for nome in ("configuratore.css", "configuratore.js", "comparatore.css", "comparatore.js"):
        shutil.copyfile(os.path.join(TEMPLATES, nome), os.path.join(out, nome))
        # ?v= changes with the file, so browsers do not keep an old copy.
        with open(os.path.join(out, nome), "rb") as f:
            versione[nome] = hashlib.sha256(f.read()).hexdigest()[:8]

    for lingua, p in PAGINE.items():
        dest = os.path.join(site, p, "index.html")
        with open(dest, encoding="utf-8") as f:
            s = f.read()
        rel = os.path.relpath(out, os.path.dirname(dest)).replace(os.sep, "/")
        nuovo = blocco(dati(ali, cfg, lingua),
                       f"{rel}/configuratore.css?v={versione['configuratore.css']}",
                       f"{rel}/configuratore.js?v={versione['configuratore.js']}")
        if INIZIO in s:
            s = re.sub(re.escape(INIZIO) + r".*?" + re.escape(FINE), lambda m: nuovo, s, count=1, flags=re.S)
        else:
            # First run: the crawled widget, from the icons stylesheet to the end of its script.
            m = re.search(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/@tabler/[^"]*">'
                          r'.*?<div id="cfg-wrap">.*?\}\)\(\);\s*</script>', s, re.S)
            if not m:
                sys.exit(f"{dest}: configurator widget not found.")
            s = s[:m.start()] + nuovo + s[m.end():]
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
        print(f"wrote {p}/index.html ({lingua})")

    for lingua, p in PAGINE_CMP.items():
        dest = os.path.join(site, p, "index.html")
        with open(dest, encoding="utf-8") as f:
            s = f.read()
        rel = os.path.relpath(out, os.path.dirname(dest)).replace(os.sep, "/")
        nuovo = blocco_comparatore(dati_comparatore(ali, cfg, lingua),
                                   f"{rel}/comparatore.css?v={versione['comparatore.css']}",
                                   f"{rel}/comparatore.js?v={versione['comparatore.js']}")
        if INIZIO_CMP in s:
            s = re.sub(re.escape(INIZIO_CMP) + r".*?" + re.escape(FINE_CMP), lambda m: nuovo, s, count=1, flags=re.S)
        else:
            # First run: the old calculator, from the icons stylesheet to the end of its script.
            m = re.search(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/@tabler/[^"]*">\s*<style>\s*#dw-wrap'
                          r'.*?<div id="dw-wrap">.*?\}\)\(\);\s*</script>', s, re.S)
            if not m:
                sys.exit(f"{dest}: old calculator (#dw-wrap) not found.")
            s = s[:m.start()] + nuovo + s[m.end():]
            # The page's own menu: the calculator link becomes "Compare courses".
            vecchia, nuova = VOCE_MENU_CMP[lingua]
            voce = f'<a href="#dw-wrap">{vecchia}</a>'
            if voce not in s:
                sys.exit(f"{dest}: menu link to #dw-wrap not found.")
            s = s.replace(voce, f'<a href="#{ANCORA_CMP}">{nuova}</a>')
            s = s.replace(".ali-ancora, #dw-wrap {", ".ali-ancora {")
        if "dw-wrap" in s:
            sys.exit(f"{dest}: still links to the old calculator (#dw-wrap).")
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
        print(f"wrote {p}/index.html (comparator, {lingua})")


if __name__ == "__main__":
    main()
