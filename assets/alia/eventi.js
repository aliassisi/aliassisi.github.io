/* "Cosa succede ad Assisi e dintorni" / "What's on in and around Assisi" on
   vivere-ad-assisi/ and en/life-in-assisi/. Reads data/eventi-assisi.json
   (edited by hand) and shows the next 6 events that have not ended, as cards.
   Each event: inizio, fine (YYYY-MM-DD), ora ("" if all day), titolo, luogo,
   descrizione_it, descrizione_en, link, and optional immagine (path from the
   site root, e.g. "assets/uploads/eventi/x.jpg"), nota_it, nota_en (a short
   label such as "Sold out"). With no upcoming event, or when the JSON does
   not load, the fixed block .ali-ev-anno already in the page stays visible. */
(function () {
  var box = document.querySelector('.ali-ev[data-src]');
  if (!box) return;
  var en = box.getAttribute('data-lang') === 'en';
  var MAX = 6, MIN = 1, ONGOING = 2;
  var root = box.getAttribute('data-src').replace(/data\/eventi-assisi\.json$/, '');
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

  function card(ev, now) {
    var c = el('article', 'ali-ev-c');
    // Already started (an exhibition): the badge shows the end date.
    var going = ev.inizio < now && ev.fine && ev.fine !== ev.inizio;
    var s = parts(going ? ev.fine : ev.inizio);
    var ph = el('div', 'ali-ev-ph');
    if (ev.immagine) {
      var img = el('img');
      img.src = /^https?:\/\//.test(ev.immagine) ? ev.immagine : root + ev.immagine.replace(/^\//, '');
      img.alt = '';
      img.loading = 'lazy';
      ph.appendChild(img);
    } else {
      ph.className += ' ali-ev-noimg';
    }
    var date = el('div', 'ali-ev-d');
    if (going) date.appendChild(el('span', 'ali-ev-f', T.until));
    date.appendChild(el('span', 'ali-ev-g', String(s.d)));
    date.appendChild(el('span', 'ali-ev-m', MONTHS[s.m]));
    ph.appendChild(date);
    var nota = en ? ev.nota_en : ev.nota_it;
    if (nota) ph.appendChild(el('span', 'ali-ev-nt', nota));
    c.appendChild(ph);
    var bd = el('div', 'ali-ev-bd');
    bd.appendChild(el('h3', '', ev.titolo));
    var when = ev.ora || '';
    if (!going && ev.fine && ev.fine !== ev.inizio) {
      var f = parts(ev.fine);
      when = (T.until + ' ' + f.d + ' ' + MONTHS[f.m] + (when ? ' · ' + when : ''));
    }
    var meta = [ev.luogo, when].filter(Boolean).join(' · ');
    if (meta) bd.appendChild(el('p', 'ali-ev-meta', meta));
    var desc = en ? ev.descrizione_en : ev.descrizione_it;
    if (desc) bd.appendChild(el('p', 'ali-ev-ds', desc));
    if (/^https?:\/\//.test(ev.link || '')) {
      var a = el('a', 'ali-ev-go', T.details + ' →');
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
      // Started events sort as if they started today.
      var key = function (ev) { return ev.inizio < now ? now : ev.inizio; };
      var list = (data.eventi || []).filter(function (ev) { return (ev.fine || ev.inizio) >= now; })
        .sort(function (a, b) { return (key(a) + (a.ora || '99')).localeCompare(key(b) + (b.ora || '99')); });
      // At most ONGOING started events (those ending first), so dated events keep their place.
      var started = list.filter(function (ev) { return ev.inizio < now; })
        .sort(function (a, b) { return a.fine.localeCompare(b.fine); }).slice(0, ONGOING);
      list = list.filter(function (ev) { return ev.inizio >= now || started.indexOf(ev) >= 0; }).slice(0, MAX);
      if (data.aggiornato && note) note.textContent = T.updated + longDate(data.aggiornato) + '. ' + T.check;
      if (list.length < MIN) return;
      var grid = box.querySelector('.ali-ev-g6');
      list.forEach(function (ev) { grid.appendChild(card(ev, now)); });
      grid.hidden = false;
      box.querySelector('.ali-ev-anno').hidden = true;
    })
    .catch(function () { /* keep the fixed block */ });
})();
