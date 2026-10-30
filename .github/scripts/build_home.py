#!/usr/bin/env python3
"""Fill the home page carousel and the "Prossimo inizio" box.

Usage:
  python3 -I .github/scripts/build_home.py SITE_DIR [--oggi YYYY-MM-DD]

Pages: index.html (it) and en/home/index.html (en).

Carousel: the home has two Slider Revolution modules, one for desktop/tablet
(rev_slider_9_1) and one for mobile (rev_slider_8_2). Both get the same slides,
from "slide" in SITE_DIR/data/home.json. Each module keeps its first slide as
the template, so the look (font, colours, video) stays as it is.

"Prossimo inizio": the old NEWS bar (desktop) and NEWS card (mobile) show the
next start date from "date_inizio" in SITE_DIR/data/ali.json, the two dates
after it, and a line saying other start dates can be asked for. The page also
carries the full date list and a small script, so after a start date has passed
the browser shows the next one without a rebuild.

Safe to run again on a page it already changed.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

MODULI = {"rev_slider_9_1": "9", "rev_slider_8_2": "8"}
MESI = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}
PAGINE = {"it": "index.html", "en": os.path.join("en", "home", "index.html")}
SCRIPT_START, SCRIPT_END = "<!-- prossimo-inizio:start -->", "<!-- prossimo-inizio:end -->"


def lungo(d, lang, anno=True):
    m = MESI[lang][d.month - 1]
    s = f"{m} {d.day}" if lang == "en" else f"{d.day} {m}"
    if anno:
        s += (", " if lang == "en" else " ") + str(d.year)
    return s


def elenco(date, lang):
    """'1 febbraio · 1 marzo 2027', or with both years when they differ."""
    stesso = len({d.year for d in date}) == 1
    parti = [lungo(d, lang, anno=(not stesso or i == len(date) - 1)) for i, d in enumerate(date)]
    return " · ".join(parti)


def future(date, oggi):
    return [d for d in date if d >= oggi]


# ---------- carousel ----------

def slide_da_modello(modello, chiave, num, testo, url, pulsante):
    s = modello
    s = re.sub(r'data-key="rs-\d+"', f'data-key="rs-{chiave}"', s)
    s = re.sub(rf'slider-{num}-slide-\d+-layer', f'slider-{num}-slide-{chiave}-layer', s)
    # text layer
    s = re.sub(r'(<rs-layer[^>]*data-type="text"[^>]*>)(.*?)(</rs-layer>)',
               lambda m: m.group(1) + testo + " " + m.group(3), s, count=1, flags=re.S)
    # button layer
    s = re.sub(r'(<rs-layer[^>]*class="rev-btn"[^>]*>)(.*?)(</rs-layer>)',
               lambda m: m.group(1) + html.escape(pulsante) + " " + m.group(3), s, count=1, flags=re.S)
    s = re.sub(r"url:[^;']*;", f"url:{url};", s, count=1)
    return s


def carosello(pagina, dati, lang):
    for modulo, num in MODULI.items():
        a = pagina.find(f'<rs-module id="{modulo}"')
        if a < 0:
            sys.exit(f"{modulo} non trovato")
        b = pagina.find("<rs-slides", a)
        b = pagina.find(">", b) + 1
        c = pagina.find("</rs-slides>", b)
        primo = re.search(r"<rs-slide\b.*?</rs-slide>", pagina[b:c], re.S)
        modello = primo.group(0)
        nuove = []
        for i, sl in enumerate(dati["slide"], 1):
            v = sl[lang]
            nuove.append(slide_da_modello(modello, f"{num}0{i}", num, v["testo"], v["url"],
                                          dati["pulsante"][lang]))
        pagina = pagina[:b] + "\n" + "\n".join(nuove) + "\n" + pagina[c:]
    return pagina


# ---------- prossimo inizio ----------

def sostituisci_widget(pagina, data_id, nuovo_interno, tag_re=r"h\d"):
    """Replace the inner HTML of the heading inside the widget with data-id."""
    a = pagina.find(f'data-id="{data_id}"')
    if a < 0:
        sys.exit(f"widget {data_id} non trovato")
    m = re.compile(rf'(<({tag_re})[^>]*class="elementor-heading-title[^"]*"[^>]*>)(.*?)(</\2>)', re.S).search(pagina, a)
    return pagina[:m.start(3)] + nuovo_interno + pagina[m.end(3):]


def testimonial(pagina, data_id, nuovo):
    a = pagina.find(f'data-id="{data_id}"')
    m = re.compile(r'(<div class="elementor-testimonial-content">)(.*?)(</div>)', re.S).search(pagina, a)
    return pagina[:m.start(2)] + nuovo + pagina[m.end(2):]


def pulsante(pagina, data_id, testo, url):
    a = pagina.find(f'data-id="{data_id}"')
    m = re.compile(r'(<a class="elementor-button[^"]*" href=")([^"]*)(")', re.S).search(pagina, a)
    pagina = pagina[:m.start(2)] + url + pagina[m.end(2):]
    m = re.compile(r'(<span class="elementor-button-text">)(.*?)(</span>)', re.S).search(pagina, a)
    return pagina[:m.start(2)] + html.escape(testo) + pagina[m.end(2):]


def prossimo_inizio(pagina, dati, date, oggi, lang):
    t = dati["prossimo_inizio"][lang]
    prossime = future(date, oggi)
    if not prossime:
        sys.exit("nessuna data d'inizio futura in data/ali.json")
    primo, dopo = prossime[0], prossime[1:3]
    poi = f'{t["poi"]} {elenco(dopo, lang)}.' if dopo else ""
    span = lambda ruolo, testo: f'<span data-ali-ni="{ruolo}">{testo}</span>'

    # mobile card
    pagina = sostituisci_widget(pagina, "7d1ae85", html.escape(t["titolo"].upper()))
    pagina = sostituisci_widget(pagina, "d5f16a7", span("lungo", lungo(primo, lang)))
    pagina = testimonial(pagina, "bad613d",
                         span("poi", poi) + "<br>" + t["altre_date"])
    pagina = pulsante(pagina, "0bcf9eb", t["pulsante"], t["url"])
    # desktop bar
    pagina = sostituisci_widget(pagina, "b259213",
                                '<span style="font-size:.7em">' + html.escape(t["titolo"].upper()) + "</span>")
    pagina = sostituisci_widget(pagina, "38f8ffd", span("breve", primo.strftime("%d.%m.%Y")))
    pagina = sostituisci_widget(pagina, "139c2fa",
                                span("poi", poi) + " " + t["altre_date"])
    pagina = pulsante(pagina, "d4e7e8d", t["pulsante"], t["url"])

    # runtime update: the date list and the month names go with the page
    css = ("<style>.elementor-element-bad613d .elementor-testimonial-content a,"
           ".elementor-element-139c2fa .elementor-heading-title a{font:inherit!important;letter-spacing:inherit!important;"
           "color:#fec15f!important;text-decoration:underline!important;text-decoration-thickness:1px!important;"
           "text-underline-offset:.18em}"
           # desktop bar on one line: columns as wide as their content, the text takes the rest
           ".elementor-element-2c917f6 .elementor-column{width:auto!important;flex:0 0 auto}"
           ".elementor-element-2c917f6 .elementor-element-15f1e8c{flex:1 1 auto;min-width:0}"
           ".elementor-element-2c917f6 .elementor-heading-title,.elementor-element-2c917f6 .elementor-button{white-space:nowrap}"
           ".elementor-element-2c917f6 .elementor-element-139c2fa .elementor-heading-title{white-space:normal}"
           "</style>\n")
    js = SCRIPT_START + "\n" + css + "<script>(function(){var D=" + json.dumps([d.isoformat() for d in date]) \
        + ",M=" + json.dumps(MESI[lang], ensure_ascii=False) + ",L=" + json.dumps(lang) \
        + ",P=" + json.dumps(t["poi"], ensure_ascii=False) + r""";
var t=new Date(),o=t.getFullYear()+'-'+('0'+(t.getMonth()+1)).slice(-2)+'-'+('0'+t.getDate()).slice(-2);
var f=D.filter(function(d){return d>=o;});if(!f.length)return;
function p(s){var a=s.split('-');return{y:+a[0],m:+a[1],d:+a[2]};}
function lg(x,y){var s=L=='en'?M[x.m-1]+' '+x.d:x.d+' '+M[x.m-1];return y?s+(L=='en'?', ':' ')+x.y:s;}
var a=p(f[0]),n=f.slice(1,3).map(p),same=n.length&&n.every(function(x){return x.y==n[0].y;});
var poi=n.length?P+' '+n.map(function(x,i){return lg(x,!same||i==n.length-1);}).join(' · ')+'.':'';
function set(r,v){document.querySelectorAll('[data-ali-ni="'+r+'"]').forEach(function(e){e.textContent=v;});}
set('lungo',lg(a,true));set('breve',('0'+a.d).slice(-2)+'.'+('0'+a.m).slice(-2)+'.'+a.y);set('poi',poi);
})();</script>
""" + SCRIPT_END
    if SCRIPT_START in pagina:
        a = pagina.find(SCRIPT_START)
        b = pagina.find(SCRIPT_END) + len(SCRIPT_END)
        pagina = pagina[:a] + js + pagina[b:]
    else:
        pagina = pagina.replace("</body>", js + "\n</body>", 1)
    return pagina


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--oggi")
    a = ap.parse_args()
    oggi = datetime.date.fromisoformat(a.oggi) if a.oggi else datetime.date.today()
    with open(os.path.join(a.site, "data", "home.json"), encoding="utf-8") as f:
        dati = json.load(f)
    with open(os.path.join(a.site, "data", "ali.json"), encoding="utf-8") as f:
        date = sorted(datetime.date.fromisoformat(d) for d in json.load(f)["date_inizio"])
    for lang, rel in PAGINE.items():
        p = os.path.join(a.site, rel)
        with open(p, encoding="utf-8") as f:
            pagina = f.read()
        pagina = carosello(pagina, dati, lang)
        pagina = prossimo_inizio(pagina, dati, date, oggi, lang)
        with open(p, "w", encoding="utf-8") as f:
            f.write(pagina)
        print("ok", rel)


if __name__ == "__main__":
    main()
