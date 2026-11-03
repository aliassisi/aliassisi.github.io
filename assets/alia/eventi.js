/* "Cosa succede ad Assisi" / "What's on in Assisi" on vivere-ad-assisi/ and
   en/life-in-assisi/. Reads data/eventi-assisi.json (built every day by
   .github/workflows/eventi-assisi.yml) and shows the next 6 events as cards.
   With fewer than 2 events, or when the JSON does not load, the fixed block
   .ali-ev-anno already in the page stays visible. */
(function () {
  var box = document.querySelector('.ali-ev[data-src]');
  if (!box) return;
  var en = box.getAttribute('data-lang') === 'en';
  var MAX = 6, MIN = 2;
  var MONTHS = en
    ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    : ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'];
  var T = en
    ? { details: 'Details', until: 'until', updated: 'Updated ', check: 'Please check dates and times with the organisers.' }
    : { details: 'Dettagli', until: 'fino al', updated: 'Aggiornato al ', check: 'Verifica date e orari sul sito degli organizzatori.' };

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }
  function parts(iso) {
    var p = iso.split('-');
    return { y: +p[0], m: +p[1] - 1, d: +p[2] };
  }
  function longDate(iso) {
    var p = parts(iso);
    return p.d + ' ' + MONTHS[p.m] + ' ' + p.y;
  }
  function today() {
    try {
      return new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    } catch (e) {
      return new Date().toISOString().slice(0, 10);
    }
  }

  function card(ev) {
    var c = el('article', 'ali-ev-c');
    var s = parts(ev.inizio);
    var date = el('div', 'ali-ev-d');
    date.appendChild(el('span', 'ali-ev-g', String(s.d)));
    date.appendChild(el('span', 'ali-ev-m', MONTHS[s.m]));
    if (ev.fine && ev.fine !== ev.inizio) {
      var f = parts(ev.fine);
      date.appendChild(el('span', 'ali-ev-f', T.until + ' ' + f.d + ' ' + MONTHS[f.m]));
    }
    c.appendChild(date);
    var bd = el('div', 'ali-ev-bd');
    bd.appendChild(el('h3', '', ev.titolo));
    var meta = [ev.luogo, ev.ora].filter(Boolean).join(' · ');
    if (meta) bd.appendChild(el('p', 'ali-ev-meta', meta));
    var desc = en ? ev.descrizione_en : ev.descrizione_it;
    if (desc) bd.appendChild(el('p', 'ali-ev-ds', desc));
    if (/^https?:\/\//.test(ev.link || '')) {
      var a = el('a', 'ali-ev-go', T.details);
      a.href = ev.link;
      a.target = '_blank';
      a.rel = 'noopener';
      bd.appendChild(a);
    }
    c.appendChild(bd);
    return c;
  }

  var note = box.querySelector('.ali-ev-nota');
  fetch(box.getAttribute('data-src'), { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var now = today();
      var list = (data.eventi || []).filter(function (ev) { return (ev.fine || ev.inizio) >= now; }).slice(0, MAX);
      if (data.aggiornato && note) note.textContent = T.updated + longDate(data.aggiornato) + '. ' + T.check;
      if (list.length < MIN) return;
      var grid = box.querySelector('.ali-ev-g6');
      list.forEach(function (ev) { grid.appendChild(card(ev)); });
      grid.hidden = false;
      box.querySelector('.ali-ev-anno').hidden = true;
    })
    .catch(function () { /* keep the fixed block */ });
})();
