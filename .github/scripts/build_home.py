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
next start date from "date_inizio" in SITE_DIR/data/alia.json, the two dates
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
    return raggruppa(s, num, chiave)


GRUPPO_XY = "xo:80px,50px,30px,20px;yo:300px,140px,114px,127px;"
GRUPPO_SPAZIO = "t:40px"


def raggruppa(s, num, chiave):
    """Title and button in one Slider Revolution group, stacked (data-pos="r").
    A longer title pushes the button down. Safe on a slide that is already grouped."""
    s = re.sub(r"<rs-group\b[^>]*>\n?|\n?</rs-group>", "", s)
    dim = re.search(r'<rs-layer[^>]*data-type="text"[^>]*data-dim="([^"]*)"', s).group(1)

    def relativo(m, extra=""):
        tag = re.sub(r'\s+data-(xy|pos|margin)="[^"]*"', "", m.group(0))
        return tag[:-1] + ' data-pos="r"' + extra + ">"

    s = re.sub(r'<rs-layer[^>]*data-type="text"[^>]*>', relativo, s, count=1)
    s = re.sub(r'<rs-layer[^>]*class="rev-btn[^"]*"[^>]*>',
               lambda m: relativo(m, f' data-margin="{GRUPPO_SPAZIO};"'), s, count=1)
    ini = s.index("<rs-layer")
    fine = s.index("</rs-layer>", s.index('class="rev-btn')) + len("</rs-layer>")
    gruppo = (f'<rs-group id="slider-{num}-slide-{chiave}-group" data-type="group" data-rsp_ch="on" '
              f'data-xy="{GRUPPO_XY}" data-dim="{dim.rstrip(";")};h:auto;" '
              f'data-frame_1="sp:1;" data-frame_999="o:0;st:w;sR:7800;" style="z-index:28;">\n')
    return s[:ini] + gruppo + s[ini:fine] + "\n</rs-group>" + s[fine:]


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
        sys.exit("nessuna data d'inizio futura in data/alia.json")
    primo, dopo = prossime[0], prossime[1:3]
    poi = f'{t["poi"]} {elenco(dopo, lang)}.' if dopo else ""
    span = lambda ruolo, testo: f'<span data-ali-ni="{ruolo}">{testo}</span>'
    # "NON-BEGINNERS" in the same yellow capitals as "Next start", then "any Monday"
    lab = f'<span class="ali-ni-lab">{html.escape(t["non_principianti"])}</span>'
    q = f'<span class="ali-ni-q">{html.escape(t["ogni_lunedi"])}</span>'
    # mobile card: three lines under the date
    riga = lambda testo, cl="": f'<span class="ali-ni-r{cl}">{testo}</span>'
    righe = (riga(span("poi", poi))
             + riga(lab + " " + q, " ali-ni-blocco")
             + riga(t["altre_date"], " ali-ni-small"))
    # desktop bar: the next dates go under the date; then a "non-beginners"
    # block and an "other dates" block, each with its own column line
    barra = (f'<span class="ali-ni-np">{lab}{q}</span>'
             f'<span class="ali-ni-altre">{t["altre_date"]}</span>')

    # mobile card
    pagina = sostituisci_widget(pagina, "7d1ae85", html.escape(t["titolo"].upper()))
    pagina = sostituisci_widget(pagina, "d5f16a7", span("lungo", lungo(primo, lang)))
    pagina = testimonial(pagina, "bad613d", righe)
    pagina = pulsante(pagina, "0bcf9eb", t["pulsante"], t["url"])
    # desktop bar
    pagina = sostituisci_widget(pagina, "b259213",
                                '<span style="font-size:.58em">' + html.escape(t["titolo"].upper()) + "</span>")
    pagina = sostituisci_widget(pagina, "38f8ffd", span("breve", primo.strftime("%d.%m.%Y"))
                                + f'<span class="ali-ni-poi">{span("poi", poi)}</span>')
    pagina = sostituisci_widget(pagina, "139c2fa", barra)
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
           # breathing room: same side padding in every column, smaller label and date;
           # the sentence wraps when it does not fit
           ".elementor-element-2c917f6 .elementor-column>.elementor-widget-wrap{padding:20px clamp(18px,2.4vw,44px)!important}"
           ".elementor-element-2c917f6 .elementor-element-b259213 .elementor-heading-title{letter-spacing:.16em}"
           # the label ("Prossimo inizio per principianti") may take two lines
           ".elementor-element-2c917f6 .elementor-element-b259213 .elementor-heading-title{white-space:normal;max-width:11em;line-height:1.1}"
           ".elementor-element-2c917f6 .elementor-element-38f8ffd .elementor-heading-title{font-size:30px!important}"
           ".elementor-element-2c917f6 .elementor-element-139c2fa .elementor-heading-title{font-size:24px!important}"
           # "Non principianti" looks like the "Prossimo inizio" label
           ".ali-ni-lab{font-family:'Cormorant Garamond',serif;font-weight:300;font-size:21px;letter-spacing:.27em;"
           "text-transform:uppercase;color:#fec15f;white-space:nowrap}"
           # desktop: next dates under the date
           ".elementor-element-38f8ffd{width:auto!important}"
           ".elementor-element-38f8ffd .ali-ni-poi{display:block;margin-top:6px;font-size:17px;line-height:1.3;letter-spacing:.02em}"
           # desktop: the text column holds two blocks, split by a line like the other columns
           ".elementor-element-2c917f6 .elementor-element-15f1e8c>.elementor-widget-wrap{padding:0!important;align-items:stretch;align-content:stretch!important}"
           ".elementor-element-139c2fa>.elementor-widget-container{padding:0!important}"
           ".elementor-element-139c2fa,.elementor-element-139c2fa>.elementor-widget-container{width:100%;height:100%}"
           ".elementor-element-2c917f6 .elementor-element-139c2fa .elementor-heading-title{display:flex;height:100%;align-items:stretch}"
           ".ali-ni-np,.ali-ni-altre{display:flex;flex-direction:column;justify-content:center;padding:20px clamp(18px,2.4vw,44px)}"
           ".ali-ni-np{flex:none;align-items:center;gap:6px;border-right:1px solid #f0eae5}"
           ".ali-ni-np .ali-ni-q{font-size:30px;font-weight:200;line-height:1.2}"
           ".ali-ni-altre{display:block;align-self:center;flex:1 1 200px;min-width:200px;font-size:20px;line-height:1.4}"
           ".elementor-element-2c917f6 .elementor-element-b259213 .elementor-heading-title{max-width:270px}"
           # mobile card: three lines, the label on its own line
           ".ali-ni-r{display:block}.ali-ni-r+.ali-ni-r{margin-top:6px}"
           ".ali-ni-small{font-size:.8em;opacity:.85}"
           # mobile card: a line, then "NON PRINCIPIANTI" in the same type as the card title
           # and "Ogni lunedì" in the same type as the date
           ".elementor-element-bad613d .ali-ni-blocco{border-top:1px solid #f0eae5;margin:22px -10px 0!important;padding:20px 10px 0}"
           ".elementor-element-bad613d .ali-ni-lab{display:block;margin:0;font-family:'Cormorant Garamond',serif;"
           "font-size:20px;font-weight:400;line-height:32px;letter-spacing:4.5px;color:#f0eae5}"
           ".elementor-element-bad613d .ali-ni-q{display:block;margin:6px 0 4px;font-family:'Cormorant Garamond',serif;"
           "font-size:29px;font-weight:100;line-height:1.2;letter-spacing:.2px;text-transform:uppercase;color:#fec15f}"
           # narrow desktops (the bar is hidden below 1025px): less padding, smaller type
           "@media(max-width:1365px){"
           ".elementor-element-2c917f6 .elementor-column>.elementor-widget-wrap,.ali-ni-np,.ali-ni-altre{padding:16px 18px!important}"
           ".elementor-element-2c917f6 .elementor-element-15f1e8c>.elementor-widget-wrap{padding:0!important}"
           ".elementor-element-2c917f6 .elementor-element-b259213 .elementor-heading-title{max-width:210px}"
           ".elementor-element-2c917f6 .elementor-element-fa2ccb2>.elementor-widget-wrap{padding:16px 14px!important}"
           ".elementor-element-38f8ffd .ali-ni-poi{white-space:normal;max-width:150px;margin-left:auto;margin-right:auto}"
           ".elementor-element-139c2fa .ali-ni-lab{letter-spacing:.15em}"
           ".elementor-element-2c917f6 .elementor-element-38f8ffd .elementor-heading-title,.ali-ni-np .ali-ni-q{font-size:24px!important}"
           ".elementor-element-38f8ffd .ali-ni-poi{font-size:15px}"
           ".elementor-element-139c2fa .ali-ni-lab{font-size:17px}"
           ".ali-ni-altre{font-size:16px;flex-basis:140px;min-width:140px}}"
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
    with open(os.path.join(a.site, "data", "alia.json"), encoding="utf-8") as f:
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
