#!/usr/bin/env python3
"""Fill the workshop dates on the activities page from data/laboratori.json.

Usage:
  python3 -I .github/scripts/build_laboratori.py SITE_DIR [--oggi YYYY-MM-DD]

Pages: attivita-facilities-e-laboratori/index.html (it) and
en/school-activity/index.html (en).

For each workshop row (Elementor section "sezione") the date column gets one
heading per year with the dates still to come. Each date is a
<span class="ali-lab" data-data="YYYY-MM-DD">, and the page carries a small
script, so after a date has passed the browser hides it without a rebuild.
A row with no dates left shows "Nuove date in arrivo".

The "Scegli le date" box (var ACTIVITIES) gets the same dates.

Safe to run again on a page it already changed.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

MESI = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}
PAGINE = {
    "it": os.path.join("attivita-facilities-e-laboratori", "index.html"),
    "en": os.path.join("en", "school-activity", "index.html"),
}
VUOTO = {"it": "Nuove date in arrivo", "en": "New dates coming soon"}
SCRIPT_START, SCRIPT_END = "<!-- laboratori:start -->", "<!-- laboratori:end -->"
TOP = '<section class="elementor-section elementor-top-section'

SCRIPT = SCRIPT_START + """
<style>
.ali-lab { white-space: nowrap; }
.ali-lab + .ali-lab::before { content: "/ "; }
html[lang^="en"] .ali-lab { display: block; }
html[lang^="en"] .ali-lab + .ali-lab::before { content: none; }
</style>
<script>
/* Hides workshop dates that have passed. Built by .github/scripts/build_laboratori.py. */
(function () {
  var d = new Date();
  var oggi = d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  document.querySelectorAll(".ali-lab").forEach(function (s) {
    if (s.getAttribute("data-data") < oggi) s.parentNode.removeChild(s);
  });
  document.querySelectorAll(".ali-lab-anno").forEach(function (a) {
    if (!a.querySelector(".ali-lab")) a.parentNode.removeChild(a);
  });
  document.querySelectorAll(".ali-lab-col").forEach(function (c) {
    var v = c.querySelector(".ali-lab-vuoto");
    if (v && !c.querySelector(".ali-lab")) v.removeAttribute("hidden");
  });
  ["ali-from", "ali-to"].forEach(function (id) {
    var i = document.getElementById(id);
    if (i && i.min < oggi) i.min = oggi;
  });
})();
</script>
""" + SCRIPT_END


def giorno(d, lang):
    m = MESI[lang][d.month - 1]
    if lang == "it":
        return f"{d.day} {m}"
    suf = "th" if 11 <= d.day % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d.day % 10, "th")
    return f"{m} {d.day}{suf}"


def fine_div(s, a):
    """Index just after the </div> that closes the <div ...> starting at a."""
    livello = 0
    for m in re.compile(r"<div\b|</div>").finditer(s, a):
        livello += 1 if m.group(0) == "<div" else -1
        if livello == 0:
            return m.end()
    sys.exit("div non chiuso")


def widget(wid, cls, contenuto, nascosto=False):
    h = " hidden" if nascosto else ""
    return (f'<div class="elementor-element elementor-element-{wid} elementor-widget elementor-widget-heading {cls}"'
            f' data-id="{wid}" data-element_type="widget" data-e-type="widget" data-widget_type="heading.default"{h}>\n'
            f'\t\t\t\t<div class="elementor-widget-container">\n'
            f'\t\t\t\t\t<h6 class="elementor-heading-title elementor-size-default">{contenuto}</h6>\t\t\t\t</div>\n'
            f'\t\t\t\t</div>\n')


def colonna_date(pagina, lab, lang, oggi):
    a = pagina.find(f'data-id="{lab["sezione"]}"')
    if a < 0:
        sys.exit(f"sezione {lab['sezione']} non trovata")
    fine_sez = pagina.find(TOP, a)
    colonne = [m.start() for m in re.finditer(r'<div class="elementor-column ', pagina[a:fine_sez])]
    if len(colonne) != 5:
        sys.exit(f"sezione {lab['sezione']}: {len(colonne)} colonne, attese 5")
    w = pagina.find('<div class="elementor-widget-wrap', a + colonne[2])
    w_fine = fine_div(pagina, w)
    vecchio = pagina[w:w_fine]
    ids = [i for i in re.findall(r'data-id="(\w+)" data-element_type="widget"', vecchio)]
    if not ids:
        sys.exit(f"sezione {lab['sezione']}: colonna date vuota")

    date = sorted(datetime.date.fromisoformat(x) for x in lab["date"])
    anni = {}
    for d in date:
        if d >= oggi:
            anni.setdefault(d.year, []).append(d)
    corpo = ""
    for n, (anno, dd) in enumerate(sorted(anni.items())):
        spans = " ".join(f'<span class="ali-lab" data-data="{d.isoformat()}">{giorno(d, lang)}</span>' for d in dd)
        corpo += "\t\t\t\t\t\t" + widget(ids[n % len(ids)], "ali-lab-anno", f"<b>{anno}</b><br>{spans}")
    corpo += "\t\t\t\t\t\t" + widget(ids[-1] if anni else ids[0], "ali-lab-vuoto",
                                     html.escape(VUOTO[lang]), nascosto=bool(anni))
    nuovo = ('<div class="elementor-widget-wrap elementor-element-populated ali-lab-col">\n'
             + corpo + "\t\t\t\t\t</div>")
    return pagina[:w] + nuovo + pagina[w_fine:]


def calcolatore(pagina, dati, lang, oggi):
    voci = {lab[f"nome_{lang}"]: sorted(lab["date"]) for lab in dati}
    js = "{\n" + ",\n".join(f"      {json.dumps(k, ensure_ascii=False)}: {json.dumps(v)}"
                            for k, v in voci.items()) + "\n    }"
    pagina, n = re.subn(r"var ACTIVITIES = \{.*?\n    \};", lambda m: f"var ACTIVITIES = {js};",
                        pagina, count=1, flags=re.S)
    if n != 1:
        sys.exit("var ACTIVITIES non trovato")
    ultimo = max(d for v in voci.values() for d in v)[:4] + "-12-31"
    for id_ in ("ali-from", "ali-to"):
        pagina, n = re.subn(rf'id="{id_}" min="[^"]*" max="[^"]*"',
                            f'id="{id_}" min="{oggi.isoformat()}" max="{ultimo}"', pagina)
        if n != 1:
            sys.exit(f"{id_} non trovato")
    return pagina


def script(pagina):
    a, b = pagina.find(SCRIPT_START), pagina.find(SCRIPT_END)
    if a >= 0 and b > a:
        return pagina[:a] + SCRIPT + pagina[b + len(SCRIPT_END):]
    i = pagina.rfind("</body>")
    return pagina[:i] + SCRIPT + "\n" + pagina[i:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--oggi")
    a = ap.parse_args()
    oggi = datetime.date.fromisoformat(a.oggi) if a.oggi else datetime.date.today()
    with open(os.path.join(a.site, "data", "laboratori.json"), encoding="utf-8") as f:
        dati = json.load(f)["laboratori"]
    for lang, rel in PAGINE.items():
        p = os.path.join(a.site, rel)
        with open(p, encoding="utf-8") as f:
            pagina = f.read()
        for lab in dati:
            pagina = colonna_date(pagina, lab, lang, oggi)
        pagina = calcolatore(pagina, dati, lang, oggi)
        pagina = script(pagina)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(pagina)
        print("ok", rel)


if __name__ == "__main__":
    main()
