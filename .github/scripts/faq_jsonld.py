"""Write the FAQPage JSON-LD of the FAQ pages from the questions on the page.

Run it after you change a question or an answer:
    python3 -I .github/scripts/faq_jsonld.py .

Each answer is the plain text of its .faq-body: paragraphs and list items
joined by a space (with a full stop added when one is missing), table rows as "first cell (second cell)" joined by "; ".
The block goes at the end of <head>, as <script id="faq-jsonld">.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

PAGES = {
    "frequently-asked-questions/index.html": "it",
    "en/faq/index.html": "en",
}
BLOCKS = {"p", "li"}


class FAQParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []      # [question, [answer parts]]
        self.in_item = 0     # <details> depth inside a .faq-item
        self.in_summary = False
        self.buf = None      # text of the current p / li / td
        self.row = None      # cells of the current body table row
        self.rows = None     # rows of the current table
        self.in_thead = False

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        if tag == "details" and "faq-item" in cls.split():
            self.in_item = 1
            self.items.append(["", []])
            return
        if not self.in_item:
            return
        if tag == "details":
            self.in_item += 1
        elif tag == "summary":
            self.in_summary = True
        elif tag in BLOCKS or tag in ("td", "th"):
            self.buf = []
        elif tag == "thead":
            self.in_thead = True
        elif tag == "tr":
            self.row = []
        elif tag == "table":
            self.rows = []

    def handle_endtag(self, tag):
        if not self.in_item:
            return
        if tag == "details":
            self.in_item -= 1
        elif tag == "summary":
            self.in_summary = False
        elif tag in BLOCKS and self.buf is not None:
            self.items[-1][1].append(clean("".join(self.buf)))
            self.buf = None
        elif tag in ("td", "th") and self.buf is not None:
            if self.row is not None:
                self.row.append(clean("".join(self.buf)))
            self.buf = None
        elif tag == "thead":
            self.in_thead = False
        elif tag == "tr":
            if self.row and not self.in_thead and self.rows is not None:
                first, rest = self.row[0], ", ".join(self.row[1:])
                self.rows.append(f"{first} ({rest})" if rest else first)
            self.row = None
        elif tag == "table":
            if self.rows:
                self.items[-1][1].append("; ".join(self.rows) + ".")
            self.rows = None

    def handle_data(self, data):
        if not self.in_item:
            return
        if self.in_summary:
            self.items[-1][0] += data
        elif self.buf is not None:
            self.buf.append(data)


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def sentence(text):
    # "In treno: trenitalia.com" is a paragraph of its own on the page.
    return text if text[-1:] in ".!?" else text + "."


def jsonld(html, lang):
    parser = FAQParser()
    parser.feed(html)
    entities = [{
        "@type": "Question",
        "name": clean(q),
        "acceptedAnswer": {"@type": "Answer", "text": " ".join(sentence(x) for x in a if x)},
    } for q, a in parser.items]
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": lang,
        "mainEntity": entities,
    }
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json" id="faq-jsonld">\n{body}\n</script>\n', len(entities)


site = sys.argv[1] if len(sys.argv) > 1 else "."
for page, lang in PAGES.items():
    path = os.path.join(site, page)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    block, n = jsonld(text, lang)
    if not n:
        sys.exit(f"{page}: no .faq-item found")
    text = re.sub(r'<script type="application/ld\+json" id="faq-jsonld">.*?</script>\n', "", text, flags=re.S)
    text = text.replace("</head>", block + "</head>", 1)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"{page}: {n} questions")
