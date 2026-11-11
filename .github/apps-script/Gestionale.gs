/**
 * Gestionale ALIA.
 * La pagina (Pagina.html) e le funzioni che legge e scrive.
 * I dati stanno nello stesso foglio delle iscrizioni, in schede nuove:
 * Classi, Assegnazioni, Registro, Fatture, Promemoria, Documenti.
 *
 * Source: .github/apps-script/Gestionale.gs nel repository del sito.
 * Come installarlo: .github/apps-script/ISTRUZIONI.md.
 */

var FIC_API = 'https://api-v2.fattureincloud.it';
var LIVELLI = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
/* Lo stato di una lezione. Le lezioni dei gruppi si scrivono già fatte; quelle dei privati si pianificano
   (prevista) e poi diventano fatta, annullata (non si conta) o persa (lo studente non è venuto senza avvisare:
   la lezione si conta come usata ma non frequentata). */
var STATI_LEZIONE = ['prevista', 'fatta', 'annullata', 'persa'];
var GIORNI = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato'];

/* Le schede del gestionale: [chiave, intestazione]. */
var SCHEMI = {
  Classi: [['id', 'ID'], ['nome', 'Nome'], ['aula', 'Aula'], ['livello', 'Livello'],
    ['insegnante', 'Insegnante'], ['inizio', 'Inizio'], ['fine', 'Fine'], ['orario', 'Orario'], ['note', 'Note'], ['tipo', 'Tipo'],
    ['modalita', 'Modalità'], ['link', 'Link online']],
  Assegnazioni: [['iscrizione', 'N. iscrizione'], ['classe', 'Classe'], ['dal', 'Dal'], ['al', 'Al']],
  Registro: [['id', 'ID'], ['classe', 'Classe'], ['data', 'Data'], ['orario', 'Orario'], ['ore', 'Ore'],
    ['volume', 'Volume/Capitolo'], ['novita', 'Novità'], ['ascolto', 'Attività ascolto'],
    ['lettura', 'Attività lettura'], ['scritta', 'Attività prod. scritta'], ['orale', 'Attività prod. orale'],
    ['ripetuto', 'Ripetuto'], ['da_ripetere', 'Da ripetere'], ['note', 'Note'], ['assenti', 'Assenti'],
    ['insegnante', 'Insegnante'], ['modificato', 'Modificato'],
    ['ora_inizio', 'Ora inizio'], ['ora_fine', 'Ora fine'], ['aula', 'Aula'], ['stato', 'Stato'], ['link', 'Link online'],
    ['recupero_di', 'Recupero della lezione']],
  Fatture: [['fic_id', 'ID Fatture in Cloud'], ['tipo', 'Tipo'], ['numero', 'Numero'], ['data', 'Data'],
    ['cliente', 'Cliente'], ['email', 'Email'], ['importo', 'Importo'], ['da_pagare', 'Da pagare'],
    ['scadenza', 'Prossima scadenza'], ['iscrizione', 'N. iscrizione'], ['abbinata', 'Abbinata'], ['aggiornata', 'Aggiornata']],
  Promemoria: [['data', 'Inviato il'], ['tipo', 'Tipo'], ['chiave', 'Riferimento'], ['iscrizione', 'N. iscrizione'],
    ['email', 'Email'], ['esito', 'Esito']],
  Documenti: [['data', 'Creato il'], ['tipo', 'Tipo'], ['numero', 'Numero'], ['iscrizione', 'N. iscrizione'],
    ['studente', 'Studente'], ['link', 'PDF']],
  /* Gli alloggi: una riga per camera (o appartamento), con i posti letto. */
  Alloggi: [['id', 'ID'], ['nome', 'Nome'], ['tipo', 'Tipo'], ['posti', 'Posti letto'], ['indirizzo', 'Indirizzo'],
    ['contatto', 'Proprietario / contatto'], ['istruzioni', 'Istruzioni per lo studente'], ['note', 'Note dello staff'], ['attivo', 'Attivo']],
  /* Chi sta dove: arrivo e partenza (il giorno in cui lascia la camera). */
  Soggiorni: [['id', 'ID'], ['iscrizione', 'N. iscrizione'], ['alloggio', 'Alloggio'], ['arrivo', 'Arrivo'], ['partenza', 'Partenza'],
    ['note', 'Note'], ['modificato', 'Modificato']]
};
/* Chiusure della scuola, laboratori e attività. L'orario si decide di volta in volta (testo libero). */
SCHEMI.Eventi = [['id', 'ID'], ['tipo', 'Tipo'], ['nome', 'Nome'], ['nome_en', 'Nome (inglese)'], ['dal', 'Dal'], ['al', 'Al'],
  ['ora', 'Orario'], ['luogo', 'Luogo'], ['responsabile', 'Chi lo segue'], ['posti', 'Posti'], ['note', 'Note'], ['origine', 'Origine']];
SCHEMI.Partecipanti = [['evento', 'Evento'], ['iscrizione', 'N. iscrizione']];
var TIPI_EVENTO = [['chiusura', 'Chiusura'], ['laboratorio', 'Laboratorio'], ['attivita', 'Attività']];
var TIPI_ALLOGGIO = [['singola', 'Camera singola'], ['singola_bagno', 'Camera singola con bagno'], ['doppia', 'Camera doppia'],
  ['doppia_bagno', 'Camera doppia con bagno'], ['indipendente', 'Appartamento indipendente']];
var CHIAVI_DATA = ['inizio', 'fine', 'dal', 'al', 'data', 'arrivo', 'partenza', 'scadenza', 'nascita', 'scadenza_passaporto', 'ricevuta', 'modificato', 'aggiornata'];

/* Le impostazioni che la pagina può leggere e cambiare (il token di Fatture in Cloud si scrive ma non si rilegge). */
var IMPOSTAZIONI = {
  staff: '', aule: 'Aula 1, Aula 2, Aula 3, Aula 4, Aula 5',
  modello_diploma: '', modello_attestato: '',
  fic_azienda: '',
  promemoria: 'no', promemoria_giorni: '7', dati_pagamento: '',
  compleanni: 'no', compleanni_chi: 'in_corso',
  testo_compleanno_it: 'Ciao {{nome}},\n\ntanti auguri di buon compleanno da tutti noi dell’Accademia!\n\nA presto,\nAccademia Lingua Italiana Assisi',
  testo_compleanno_en: 'Dear {{nome}},\n\nhappy birthday from all of us at the Accademia!\n\nBest wishes,\nAccademia Lingua Italiana Assisi',
  benvenuto: 'no', benvenuto_giorni: '7',
  testo_benvenuto_it: 'Ciao {{nome}},\n\nil tuo corso comincia il {{inizio}}. Ti aspettiamo il primo giorno alle 8:45 in via Giotto 1, Assisi.\n\n{{alloggio}}\n\nA presto,\nAccademia Lingua Italiana Assisi',
  testo_benvenuto_en: 'Dear {{nome}},\n\nyour course starts on {{inizio}}. We expect you on the first day at 8:45 in via Giotto 1, Assisi.\n\n{{alloggio}}\n\nBest wishes,\nAccademia Lingua Italiana Assisi',
  riepilogo: 'si', url_gestionale: '', url_sito: 'https://aliassisi.it',
  link_online: 'no', link_ore: '24',
  testo_link_it: 'Ciao {{nome}},\n\nla tua lezione online è {{quando}} (ora italiana).\n\nEntra da qui: {{link}}\n\nA presto,\nAccademia Lingua Italiana Assisi',
  testo_link_en: 'Dear {{nome}},\n\nyour online lesson is on {{quando}} (Italian time).\n\nJoin here: {{link}}\n\nBest wishes,\nAccademia Lingua Italiana Assisi'
};

/* ---------- ACCESSO ---------- */

function utente() { return String(Session.getActiveUser().getEmail() || '').toLowerCase(); }

function staff() {
  var l = String(props().getProperty('staff') || '').toLowerCase().split(/[\s,;]+/).filter(String);
  l.push(EMAIL_STAFF.toLowerCase());
  try { l.push(String(Session.getEffectiveUser().getEmail()).toLowerCase()); } catch (e) {}
  return l;
}

function autorizzato() {
  var u = utente();
  if (!u || staff().indexOf(u) < 0) throw new Error('Non autorizzato. Apri il gestionale con un account dello staff (' + (u || 'nessun account') + ').');
  return u;
}

/* Chiamata da doGet in Codice.gs: la pagina solo allo staff, agli altri niente. */
function paginaGestionale() {
  var u = utente();
  if (!u || staff().indexOf(u) < 0) return null;
  return HtmlService.createHtmlOutputFromFile('Pagina')
    .setTitle('Gestionale ALIA')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/* ---------- SCHEDE ---------- */

function fusoOrario() { return SpreadsheetApp.getActive().getSpreadsheetTimeZone() || 'Europe/Rome'; }
function iso(v) {
  if (!(v instanceof Date)) return v === null || v === undefined ? '' : v;
  return Utilities.formatDate(v, fusoOrario(), 'yyyy-MM-dd');
}
function isoOra(v) { return v instanceof Date ? Utilities.formatDate(v, fusoOrario(), 'yyyy-MM-dd HH:mm') : (v || ''); }
/* Le date scritte da qui sono a mezzogiorno: così un fuso diverso non cambia il giorno. */
function giorno(s) {
  if (!s) return '';
  if (s instanceof Date) return s;
  var p = String(s).split('-');
  return new Date(+p[0], +p[1] - 1, +p[2], 12);
}
function oggiIso() { return Utilities.formatDate(new Date(), fusoOrario(), 'yyyy-MM-dd'); }
function piuGiorni(isoData, n) {
  var d = giorno(isoData); d.setDate(d.getDate() + n);
  return Utilities.formatDate(d, fusoOrario(), 'yyyy-MM-dd');
}
function giorniTra(a, b) { return Math.round((giorno(b) - giorno(a)) / 86400000); }

function scheda(nome) {
  var s = SpreadsheetApp.getActive().getSheetByName(nome);
  if (!s) throw new Error('Manca la scheda "' + nome + '". Lancia ALIA → Prepara il foglio.');
  return s;
}

function schema(nome) { return nome === 'Iscrizioni' ? COLONNE : SCHEMI[nome]; }

/* Tutte le righe di una scheda come oggetti {chiave: valore, _r: numero di riga}. Date in formato aaaa-mm-gg. */
function leggi(nome) {
  var s = scheda(nome), cols = schema(nome), n = s.getLastRow() - 1;
  if (n < 1) return [];
  return s.getRange(2, 1, n, cols.length).getValues().map(function (riga, i) {
    var o = {_r: i + 2};
    cols.forEach(function (c, j) {
      var v = riga[j];
      o[c[0]] = (c[0] === 'ricevuta' || c[0] === 'modificato' || c[0] === 'aggiornata' || (nome === 'Promemoria' || nome === 'Documenti') && c[0] === 'data') ? isoOra(v) : iso(v);
    });
    return o;
  }).filter(function (o) { return o[cols[0][0]] !== ''; });
}

function valoreCella(k, v) {
  if (v === undefined || v === null) return '';
  if (CHIAVI_DATA.indexOf(k) >= 0 && typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)) return giorno(v);
  return v;
}

function aggiungi(nome, o) {
  var cols = schema(nome);
  scheda(nome).appendRow(cols.map(function (c) { return valoreCella(c[0], o[c[0]]); }));
}

function aggiorna(nome, r, o) {
  var s = scheda(nome), cols = schema(nome);
  cols.forEach(function (c, j) {
    if (Object.prototype.hasOwnProperty.call(o, c[0])) s.getRange(r, j + 1).setValue(valoreCella(c[0], o[c[0]]));
  });
}

function trova(nome, chiave, valore) {
  var righe = leggi(nome);
  for (var i = 0; i < righe.length; i++) if (String(righe[i][chiave]) === String(valore)) return righe[i];
  return null;
}

function conBlocco(f) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try { return f(); } finally { lock.releaseLock(); }
}

function testo(v, max) {
  v = v === undefined || v === null ? '' : String(v);
  if (v.length > (max || 5000)) throw new Error('Testo troppo lungo');
  // Un testo che comincia con = + - @ diventerebbe una formula nel foglio.
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

/* ---------- CARICAMENTO ---------- */

function impostazioni() {
  var p = props().getProperties(), o = {};
  Object.keys(IMPOSTAZIONI).forEach(function (k) { o[k] = p[k] !== undefined ? p[k] : IMPOSTAZIONI[k]; });
  return o;
}

/* Le colonne aggiunte dopo l'installazione: scrive le intestazioni che mancano. */
function intestazioni() {
  var ss = SpreadsheetApp.getActive();
  Object.keys(SCHEMI).forEach(function (nome) {
    var s = ss.getSheetByName(nome), cols = SCHEMI[nome];
    if (!s) { s = ss.insertSheet(nome); s.setFrozenRows(1); }
    if (s.getRange(1, cols.length).getValue() === cols[cols.length - 1][1]) return;
    s.getRange(1, 1, 1, cols.length).setValues([cols.map(function (c) { return c[1]; })])
      .setFontWeight('bold').setBackground('#3d5570').setFontColor('#ffffff');
  });
}

/* Tutto quello che serve alla pagina, in una chiamata. */
function carica() {
  var u = autorizzato();
  intestazioni();
  var imp = impostazioni(), p = props();
  return {
    utente: u, oggi: oggiIso(),
    iscrizioni: leggi('Iscrizioni'),
    classi: leggi('Classi'),
    assegnazioni: leggi('Assegnazioni'),
    registro: leggi('Registro'),
    fatture: leggi('Fatture'),
    promemoria: leggi('Promemoria').slice(-300),
    documenti: leggi('Documenti'),
    alloggi: leggi('Alloggi'), soggiorni: leggi('Soggiorni'), tipi_alloggio: TIPI_ALLOGGIO,
    eventi: leggi('Eventi'), partecipanti: leggi('Partecipanti'), tipi_evento: TIPI_EVENTO,
    impostazioni: imp,
    fic_token: !!p.getProperty('fic_token'),
    invii_attivi: ['ogniGiorno', 'ogniOra'].every(function (h) { return ScriptApp.getProjectTriggers().some(function (t) { return t.getHandlerFunction() === h; }); }),
    foglio: SpreadsheetApp.getActive().getUrl(),
    stati: STATI, livelli: LIVELLI, stati_lezione: STATI_LEZIONE
  };
}

/* ---------- ISCRIZIONI ---------- */

var CAMPI_STAFF = ['stato', 'prezzo', 'livello_finale', 'note_staff', 'inizio', 'fine', 'livello', 'telefono', 'email', 'settimane', 'lezioni_totali'];

function salvaIscrizione(id, campi) {
  autorizzato();
  return conBlocco(function () {
    var r = trova('Iscrizioni', 'id', id);
    if (!r) throw new Error('Iscrizione non trovata: ' + id);
    var o = {};
    Object.keys(campi || {}).forEach(function (k) {
      if (CAMPI_STAFF.indexOf(k) < 0) throw new Error('Campo non modificabile: ' + k);
      if (k === 'stato' && STATI.indexOf(campi[k]) < 0) throw new Error('Stato non valido');
      o[k] = k === 'prezzo' && campi[k] !== '' ? Number(campi[k]) : testo(campi[k], 3000);
    });
    aggiorna('Iscrizioni', r._r, o);
    return carica();
  });
}

/* Un'iscrizione arrivata per email, da un'agenzia o di persona. */
function nuovaIscrizione(x) {
  autorizzato();
  ['nome', 'cognome', 'corso_nome'].forEach(function (k) { if (!x[k]) throw new Error('Manca: ' + k); });
  Object.keys(x).forEach(function (k) { x[k] = typeof x[k] === 'string' ? testo(x[k], 3000) : x[k]; });
  x.pagamento = x.pagamento || '';
  x.fattura = {};
  return conBlocco(function () {
    var id = nuovoNumero('iscrizioni', 'ALI');
    scriviRiga(id, x, '');
    if (x.stato) aggiorna('Iscrizioni', scheda('Iscrizioni').getLastRow(), {stato: x.stato});
    return carica();
  });
}

/* ---------- CLASSI ---------- */

function salvaClasse(c) {
  autorizzato();
  if (!c.nome) throw new Error('Manca il nome della classe');
  if (!c.inizio || !c.fine || c.fine < c.inizio) throw new Error('Controlla le date della classe');
  var o = {nome: testo(c.nome, 200), aula: testo(c.aula, 50), livello: testo(c.livello, 50), insegnante: testo(c.insegnante, 200),
    inizio: c.inizio, fine: c.fine, orario: testo(c.orario, 200), note: testo(c.note, 2000),
    tipo: c.tipo === 'privato' ? 'privato' : 'gruppo', modalita: c.modalita === 'online' ? 'online' : 'in sede', link: link(c.link)};
  return conBlocco(function () {
    if (c.id) {
      var r = trova('Classi', 'id', c.id);
      if (!r) throw new Error('Classe non trovata');
      aggiorna('Classi', r._r, o);
    } else {
      o.id = nuovoNumero('classi', 'C');
      aggiungi('Classi', o);
    }
    return carica();
  });
}

function eliminaClasse(id) {
  autorizzato();
  return conBlocco(function () {
    if (leggi('Registro').some(function (l) { return l.classe === id; })) throw new Error('La classe ha lezioni nel registro: non si può eliminare.');
    var r = trova('Classi', 'id', id);
    if (r) scheda('Classi').deleteRow(r._r);
    leggi('Assegnazioni').filter(function (a) { return a.classe === id; }).reverse()
      .forEach(function (a) { scheda('Assegnazioni').deleteRow(a._r); });
    return carica();
  });
}

/* Mette uno studente in una classe dal giorno "dal" al giorno "al". Se c'è già, cambia le date. */
function assegna(iscrizione, classe, dal, al) {
  autorizzato();
  if (!dal || !al || al < dal) throw new Error('Controlla le date');
  return conBlocco(function () {
    if (!trova('Iscrizioni', 'id', iscrizione)) throw new Error('Iscrizione non trovata');
    if (!trova('Classi', 'id', classe)) throw new Error('Classe non trovata');
    var esiste = leggi('Assegnazioni').filter(function (a) { return a.iscrizione === iscrizione && a.classe === classe; })[0];
    if (esiste) aggiorna('Assegnazioni', esiste._r, {dal: dal, al: al});
    else aggiungi('Assegnazioni', {iscrizione: iscrizione, classe: classe, dal: dal, al: al});
    return carica();
  });
}

function togliAssegnazione(iscrizione, classe) {
  autorizzato();
  return conBlocco(function () {
    leggi('Assegnazioni').filter(function (a) { return a.iscrizione === iscrizione && a.classe === classe; }).reverse()
      .forEach(function (a) { scheda('Assegnazioni').deleteRow(a._r); });
    return carica();
  });
}

/* ---------- REGISTRO ---------- */

var CAMPI_LEZIONE = ['volume', 'novita', 'ascolto', 'lettura', 'scritta', 'orale', 'ripetuto', 'da_ripetere', 'note', 'insegnante', 'aula'];

function ora(s) {
  if (!s) return '';
  var m = String(s).match(/^(\d{1,2})[:.](\d{2})$/);
  if (!m || +m[1] > 23 || +m[2] > 59) throw new Error('Ora non valida: ' + s);
  return ('0' + (+m[1])).slice(-2) + ':' + m[2];
}
function minuti(hhmm) { var p = String(hhmm).split(':'); return +p[0] * 60 + +p[1]; }

/* Un link per le lezioni online (Zoom, Meet…): solo https. */
function link(s) {
  s = String(s || '').trim();
  if (!s) return '';
  if (!/^https:\/\/[^\s<>"']+$/.test(s) || s.length > 500) throw new Error('Il link deve cominciare con https:// e non avere spazi');
  return s;
}

/* I campi di una lezione, controllati. Se mancano le ore, si calcolano da inizio e fine. */
function lezioneDa(l) {
  var o = {classe: l.classe, data: l.data, assenti: (l.assenti || []).join(', '), modificato: new Date()};
  CAMPI_LEZIONE.forEach(function (k) { o[k] = testo(l[k], 2000); });
  o.ora_inizio = ora(l.ora_inizio); o.ora_fine = ora(l.ora_fine);
  if (o.ora_inizio && o.ora_fine && minuti(o.ora_fine) <= minuti(o.ora_inizio)) throw new Error('L’ora di fine viene prima dell’inizio');
  o.orario = o.ora_inizio && o.ora_fine ? o.ora_inizio + '–' + o.ora_fine : testo(l.orario, 200);
  var ore = l.ore === '' || l.ore === undefined || l.ore === null
    ? (o.ora_inizio && o.ora_fine ? (minuti(o.ora_fine) - minuti(o.ora_inizio)) / 60 : NaN) : Number(l.ore);
  if (!(ore >= 0 && ore <= 12)) throw new Error('Ore non valide');
  o.ore = Math.round(ore * 100) / 100;
  o.stato = l.stato || 'fatta';
  o.link = link(l.link);
  if (STATI_LEZIONE.indexOf(o.stato) < 0) throw new Error('Stato della lezione non valido');
  return o;
}

function salvaLezione(l) {
  var u = autorizzato();
  if (!l.classe || !l.data) throw new Error('Mancano classe o data');
  var o = lezioneDa(l);
  return conBlocco(function () {
    var c = trova('Classi', 'id', l.classe);
    if (!c) throw new Error('Classe non trovata');
    if (!o.insegnante) o.insegnante = c.insegnante || '';
    estendiCorso(l.classe, o.data, o.data);
    if (l.id) {
      var r = trova('Registro', 'id', l.id);
      if (!r) throw new Error('Lezione non trovata');
      aggiorna('Registro', r._r, o);
    } else {
      o.id = nuovoNumero('lezioni', 'L');
      aggiungi('Registro', o);
    }
    return carica();
  });
}

function eliminaLezione(id) {
  autorizzato();
  return conBlocco(function () {
    var r = trova('Registro', 'id', id);
    if (r) scheda('Registro').deleteRow(r._r);
    return carica();
  });
}

/* Un corso individuale si allunga se una lezione (un recupero, per esempio) cade fuori dalle sue date:
   si spostano la fine (o l'inizio) del corso e le date degli studenti che arrivavano fino lì. */
function estendiCorso(classe, dal, al) {
  var c = trova('Classi', 'id', classe);
  if (!c || c.tipo !== 'privato' || (dal >= c.inizio && al <= c.fine)) return;
  leggi('Assegnazioni').forEach(function (a) {
    if (a.classe !== classe) return;
    var o = {};
    if (al > c.fine && a.al >= c.fine) o.al = al;
    if (dal < c.inizio && a.dal <= c.inizio) o.dal = dal;
    if (o.al || o.dal) aggiorna('Assegnazioni', a._r, o);
  });
  aggiorna('Classi', c._r, {inizio: dal < c.inizio ? dal : c.inizio, fine: al > c.fine ? al : c.fine});
}

/* Un corso privato (o per due) per uno studente: la classe e l'assegnazione insieme. */
function creaPrivato(iscrizione) {
  autorizzato();
  return conBlocco(function () {
    var v = trova('Iscrizioni', 'id', iscrizione);
    if (!v) throw new Error('Iscrizione non trovata');
    var dal = v.inizio || oggiIso(), al = v.fine || piuGiorni(dal, 27);
    var id = nuovoNumero('classi', 'C');
    var online = /online/i.test(String(v.corso_nome) + ' ' + String(v.formula) + ' ' + String(v.tema));
    aggiungi('Classi', {id: id, nome: (online ? 'Online – ' : 'Privato – ') + v.cognome + ' ' + v.nome, aula: '', livello: v.livello, insegnante: '',
      inizio: dal, fine: al, orario: '', note: v.formula ? String(v.formula) : '', tipo: 'privato', modalita: online ? 'online' : 'in sede', link: ''});
    aggiungi('Assegnazioni', {iscrizione: v.id, classe: id, dal: dal, al: al});
    var d = carica();
    d.creata = id;
    return d;
  });
}

/* Crea le lezioni previste di un corso nei giorni della settimana scelti, dal ... al ..., al massimo "quante". */
function pianificaLezioni(p) {
  autorizzato();
  if (!p.dal || !p.al || p.al < p.dal) throw new Error('Controlla le date');
  var giorni = (p.giorni || []).map(Number).filter(function (g) { return g >= 0 && g <= 6; });
  if (!giorni.length) throw new Error('Scegli almeno un giorno della settimana');
  if (giorniTra(p.dal, p.al) > 370) throw new Error('Al massimo un anno');
  var quante = p.quante ? Math.min(+p.quante, 300) : 300;
  return conBlocco(function () {
    if (!trova('Classi', 'id', p.classe)) throw new Error('Classe non trovata');
    var gia = {};
    leggi('Registro').forEach(function (l) { if (l.classe === p.classe && l.stato !== 'annullata') gia[l.data + ' ' + (l.ora_inizio || '')] = true; });
    var nuove = [], g = p.dal, chiusi = 0, chiusure = leggi('Eventi').filter(function (e) { return e.tipo === 'chiusura'; });
    while (g <= p.al && nuove.length < quante) {
      if (chiusure.some(function (e) { return e.dal <= g && e.al >= g; })) {
        if (giorni.indexOf(giorno(g).getDay()) >= 0) chiusi++;
        g = piuGiorni(g, 1);
        continue;
      }
      var o = lezioneDa({classe: p.classe, data: g, ora_inizio: p.ora_inizio, ora_fine: p.ora_fine, ore: p.ore,
        aula: p.aula, insegnante: p.insegnante, link: p.link, stato: 'prevista'});
      if (giorni.indexOf(giorno(g).getDay()) >= 0 && !gia[g + ' ' + o.ora_inizio]) {
        o.id = nuovoNumero('lezioni', 'L');
        nuove.push(SCHEMI.Registro.map(function (c) { return valoreCella(c[0], o[c[0]]); }));
      }
      g = piuGiorni(g, 1);
    }
    if (!nuove.length) throw new Error('Nessuna lezione nuova in quei giorni');
    var s = scheda('Registro');
    s.getRange(s.getLastRow() + 1, 1, nuove.length, SCHEMI.Registro.length).setValues(nuove);
    var date = nuove.map(function (r) { return iso(r[2]); }).sort();
    estendiCorso(p.classe, date[0], date[date.length - 1]);
    var d = carica();
    d.create = nuove.length;
    d.chiusi = chiusi;
    return d;
  });
}

/* Le prossime lezioni di uno studente per email, con un file .ics per il calendario del telefono. */
function mandaCalendario(iscrizione) {
  autorizzato();
  var v = trova('Iscrizioni', 'id', iscrizione);
  if (!v || !v.email) throw new Error('Manca l’email dello studente');
  var oggi = oggiIso(), en = v.lingua === 'en', classi = {};
  leggi('Classi').forEach(function (c) { classi[c.id] = c; });
  var mie = leggi('Assegnazioni').filter(function (a) { return a.iscrizione === v.id; });
  var lez = leggi('Registro').filter(function (l) {
    return l.data >= oggi && l.stato === 'prevista' && mie.some(function (a) { return a.classe === l.classe && l.data >= a.dal && l.data <= a.al; });
  }).sort(function (a, b) { return (a.data + a.ora_inizio) < (b.data + b.ora_inizio) ? -1 : 1; });
  if (!lez.length) throw new Error('Nessuna lezione in programma');
  lez.forEach(function (l) { l.online = linkDi(l, classi[l.classe]); });
  var unico = lez.every(function (l) { return l.online && l.online === lez[0].online; });
  var righe = lez.map(function (l) {
    var d = giorno(l.data);
    return '- ' + (en ? Utilities.formatDate(d, fusoOrario(), 'EEE d MMM yyyy') : GIORNI[d.getDay()] + ' ' + dataTesto(d)) +
      (l.orario ? ', ' + l.orario : '') + (l.online ? ', online' + (unico ? '' : ': ' + l.online) : (l.aula ? ', ' + l.aula : '')) +
      (l.insegnante ? (en ? ', teacher ' : ', insegnante ') + l.insegnante : '');
  });
  if (lez.some(function (l) { return l.online; })) righe.push('', en ? 'Times are Italian time (Europe/Rome).' : 'Gli orari sono in ora italiana.');
  if (unico) righe.push('', (en ? 'Link for the online lessons: ' : 'Link per le lezioni online: ') + lez[0].online);
  var corpo = (en ? ['Dear ' + v.nome + ',', '', 'here are your next lessons:', ''] : ['Ciao ' + v.nome + ',', '', 'ecco le tue prossime lezioni:', ''])
    .concat(righe, ['', en ? 'The attached file adds them to your calendar.' : 'Il file allegato le aggiunge al tuo calendario.',
      '', en ? 'Best wishes,' : 'A presto,', NOME_SCUOLA, EMAIL_STAFF]).join('\n');
  MailApp.sendEmail({to: v.email, replyTo: EMAIL_STAFF, name: NOME_SCUOLA,
    subject: en ? 'Your lessons at ALIA' : 'Le tue lezioni all’ALIA', body: corpo,
    attachments: [Utilities.newBlob(ics(lez, en), 'text/calendar', 'lezioni-alia.ics')]});
  registra('calendario', 'calendario:' + v.id + ':' + oggi, v.id, v.email, 'inviato');
  return carica();
}

/* Un file iCalendar: gli orari in UTC, così ogni telefono li mette all'ora giusta. */
/* annulla: true fa un file che toglie le lezioni dal calendario (stesso UID, METHOD:CANCEL). */
function ics(lez, en, annulla) {
  var utc = function (data, hhmm) {
    var d = giorno(data), m = minuti(hhmm);
    d.setHours(Math.floor(m / 60), m % 60, 0, 0);
    return Utilities.formatDate(d, 'UTC', "yyyyMMdd'T'HHmmss'Z'");
  };
  var r = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ALIA//Gestionale//IT', 'CALSCALE:GREGORIAN', annulla ? 'METHOD:CANCEL' : 'METHOD:PUBLISH'];
  lez.forEach(function (l) {
    var inizio = l.ora_inizio || '09:00', fine = l.ora_fine;
    if (!fine) { var m = minuti(inizio) + Math.round((Number(l.ore) || 1) * 60); fine = Math.floor(m / 60) + ':' + ('0' + m % 60).slice(-2); }
    r.push('BEGIN:VEVENT', 'UID:' + l.id + '@aliassisi.it', 'DTSTAMP:' + Utilities.formatDate(new Date(), 'UTC', "yyyyMMdd'T'HHmmss'Z'"),
      'DTSTART:' + utc(l.data, inizio), 'DTEND:' + utc(l.data, fine),
      'SUMMARY:' + (en ? 'Italian lesson – ALIA' : 'Lezione di italiano – ALIA'),
      'LOCATION:' + (l.online ? l.online : ((l.aula ? l.aula + ' - ' : '') + NOME_SCUOLA + ' - Assisi').replace(/[;,\r\n]/g, ' ')));
    if (l.online) r.push('URL:' + l.online, 'DESCRIPTION:' + (en ? 'Online lesson: ' : 'Lezione online: ') + l.online.replace(/([,;\\])/g, '\\$1'));
    if (annulla) r.push('STATUS:CANCELLED', 'SEQUENCE:1');
    r.push('END:VEVENT');
  });
  r.push('END:VCALENDAR');
  return r.join('\r\n');
}

/* Il link di una lezione: il suo, o quello del corso se il corso è online. */
function linkDi(l, c) { return l.link || (c && c.modalita === 'online' ? c.link : '') || ''; }

/* Gli studenti di una lezione: quelli assegnati alla classe quel giorno. */
function studentiDi(l, ass, isc) {
  return ass.filter(function (a) { return a.classe === l.classe && a.dal <= l.data && a.al >= l.data; })
    .map(function (a) { return isc[a.iscrizione]; }).filter(function (v) { return v && v.email && v.stato !== 'Annullata'; });
}

function inizioLezione(l) {
  var d = giorno(l.data), m = minuti(l.ora_inizio || '09:00');
  d.setHours(Math.floor(m / 60), m % 60, 0, 0);
  return d;
}

function emailLink(l, v, url) {
  var imp = impostazioni(), en = v.lingua === 'en', d = giorno(l.data);
  var quando = en ? Utilities.formatDate(d, fusoOrario(), 'EEEE d MMMM') + (l.ora_inizio ? ' at ' + l.ora_inizio : '')
    : GIORNI[d.getDay()] + ' ' + dataTesto(d) + (l.ora_inizio ? ' alle ' + l.ora_inizio : '');
  return {
    oggetto: en ? 'Your online lesson: ' + quando : 'La tua lezione online: ' + quando,
    corpo: riempi(en ? imp.testo_link_en : imp.testo_link_it, {nome: v.nome, cognome: v.cognome, quando: quando, data: en ? l.data : dataTesto(d), ora: l.ora_inizio || '', link: url})
  };
}

/* Ogni ora: il link a chi ha una lezione online nelle prossime N ore. Una volta per lezione e studente. */
function linkLezioni(modo) {
  var ore = +impostazioni().link_ore || 24, ora = new Date(), fino = new Date(ora.getTime() + ore * 3600000);
  var classi = {}, isc = {}, ass = leggi('Assegnazioni'), prom = leggi('Promemoria'), n = 0;
  leggi('Classi').forEach(function (c) { classi[c.id] = c; });
  leggi('Iscrizioni').forEach(function (v) { isc[v.id] = v; });
  leggi('Registro').forEach(function (l) {
    var url = linkDi(l, classi[l.classe]);
    if (!url || l.stato !== 'prevista') return;
    var t = inizioLezione(l);
    if (t < ora || t > fino) return;
    studentiDi(l, ass, isc).forEach(function (v) {
      var chiave = 'link:' + l.id + ':' + v.id;
      if (giaInviato(prom, chiave)) return;
      var e = emailLink(l, v, url);
      try { invia(modo, v.email, e.oggetto, e.corpo); registra('link', chiave, v.id, v.email, modo === 'prova' ? 'prova' : 'inviato'); n++; }
      catch (err) { registra('link', chiave, v.id, v.email, 'errore'); }
    });
  });
  return n;
}

/* Dal gestionale: manda subito il link di una lezione ai suoi studenti. */
function mandaLink(idLezione) {
  autorizzato();
  var l = trova('Registro', 'id', idLezione);
  if (!l) throw new Error('Lezione non trovata');
  var c = trova('Classi', 'id', l.classe), url = linkDi(l, c);
  if (!url) throw new Error('Manca il link: scrivilo nel corso o nella lezione');
  var isc = {}; leggi('Iscrizioni').forEach(function (v) { isc[v.id] = v; });
  var st = studentiDi(l, leggi('Assegnazioni'), isc);
  if (!st.length) throw new Error('Nessuno studente con email in questa lezione');
  conBlocco(function () {
    st.forEach(function (v) {
      var e = emailLink(l, v, url);
      MailApp.sendEmail({to: v.email, replyTo: EMAIL_STAFF, name: NOME_SCUOLA, subject: e.oggetto, body: e.corpo});
      registra('link', 'link:' + l.id + ':' + v.id + ':manuale', v.id, v.email, 'inviato');
    });
  });
  var d = carica();
  d.inviate = st.length;
  return d;
}

function quandoTesto(l, en) {
  var d = giorno(l.data);
  return en ? Utilities.formatDate(d, fusoOrario(), 'EEEE d MMMM') + (l.ora_inizio ? ' at ' + l.ora_inizio : '')
    : GIORNI[d.getDay()] + ' ' + dataTesto(d) + (l.ora_inizio ? ' alle ' + l.ora_inizio : '');
}

/* Annulla una lezione. Non si perde: si recupera. Con "nuova" ({data, ora_inizio, ora_fine}) crea subito il
   recupero; con "avvisa" manda allo studente l'email con un file che toglie la lezione dal calendario
   (e, se c'è, uno che aggiunge il recupero). */
function recuperaLezione(id, nuova, avvisa) {
  if (!nuova || !nuova.data) throw new Error('Scrivi la data del recupero');
  return annullaLezione(id, nuova, avvisa, true);
}

/* gia: la lezione è già annullata e si fissa solo il recupero. */
function annullaLezione(id, nuova, avvisa, gia) {
  autorizzato();
  var esito = conBlocco(function () {
    var l = trova('Registro', 'id', id);
    if (!l) throw new Error('Lezione non trovata');
    if (!gia && l.stato === 'fatta') throw new Error('La lezione risulta già fatta');
    if (gia && l.stato !== 'annullata') throw new Error('La lezione non è annullata');
    if (gia && leggi('Registro').some(function (x) { return x.recupero_di === l.id && x.stato !== 'annullata'; })) throw new Error('Il recupero di questa lezione c’è già');
    var c = trova('Classi', 'id', l.classe), rec = null;
    if (nuova && nuova.data) {
      rec = lezioneDa({classe: l.classe, data: nuova.data, ora_inizio: nuova.ora_inizio || l.ora_inizio, ora_fine: nuova.ora_fine || l.ora_fine,
        ore: (nuova.ora_inizio || nuova.ora_fine) ? '' : l.ore, aula: l.aula, insegnante: l.insegnante, link: l.link, stato: 'prevista'});
      rec.id = nuovoNumero('lezioni', 'L');
      rec.recupero_di = l.id;
      aggiungi('Registro', rec);
      estendiCorso(l.classe, rec.data, rec.data);
    }
    if (!gia) aggiorna('Registro', l._r, {stato: 'annullata', modificato: new Date()});
    return {l: l, c: c, rec: rec};
  });
  var inviate = 0;
  if (avvisa) {
    var isc = {}; leggi('Iscrizioni').forEach(function (v) { isc[v.id] = v; });
    var l = esito.l, rec = esito.rec, url = linkDi(l, esito.c);
    l.online = url;
    if (rec) rec.online = linkDi(rec, esito.c);
    studentiDi(l, leggi('Assegnazioni'), isc).forEach(function (v) {
      var en = v.lingua === 'en';
      // (gli studenti sono quelli della lezione annullata)
      var corpo = (en
        ? ['Dear ' + v.nome + ',', '', gia ? 'about your cancelled lesson of ' + quandoTesto(l, true) + ':' : 'your lesson on ' + quandoTesto(l, true) + ' (Italian time) is cancelled.', '',
           rec ? 'We will make it up on ' + quandoTesto(rec, true) + '.' : 'We will make it up: we will write to you with the new date.']
        : ['Ciao ' + v.nome + ',', '', gia ? 'per la lezione annullata di ' + quandoTesto(l, false) + ':' : 'la lezione di ' + quandoTesto(l, false) + ' è annullata.', '',
           rec ? 'La recuperiamo ' + quandoTesto(rec, false) + '.' : 'La recuperiamo: ti scriviamo con la nuova data.']);
      if (rec && rec.online) corpo.push((en ? 'Link: ' : 'Link: ') + rec.online);
      corpo.push('', en ? 'The attached file updates your calendar.' : 'Il file allegato aggiorna il tuo calendario.', '', en ? 'Best wishes,' : 'A presto,', NOME_SCUOLA, EMAIL_STAFF);
      var allegati = gia ? [] : [Utilities.newBlob(ics([l], en, true), 'text/calendar', 'lezione-annullata.ics')];
      if (rec) allegati.push(Utilities.newBlob(ics([rec], en), 'text/calendar', 'recupero.ics'));
      MailApp.sendEmail({to: v.email, replyTo: EMAIL_STAFF, name: NOME_SCUOLA, body: corpo.join('\n'), attachments: allegati,
        subject: gia ? (en ? 'Make-up lesson: ' + quandoTesto(rec, true) : 'Recupero della lezione: ' + quandoTesto(rec, false))
          : (en ? 'Lesson cancelled: ' + quandoTesto(l, true) : 'Lezione annullata: ' + quandoTesto(l, false))});
      registra(gia ? 'recupero' : 'annullata', (gia ? 'recupero:' : 'annullata:') + l.id + ':' + v.id, v.id, v.email, 'inviato');
      inviate++;
    });
  }
  var d = carica();
  d.inviate = inviate;
  d.recupero = esito.rec ? esito.rec.id : '';
  return d;
}

function ogniOra() {
  var imp = impostazioni();
  if (imp.link_online === 'no') return;
  try { conBlocco(function () { linkLezioni(imp.link_online); }); } catch (err) { console.error(err); }
}

/* Ore e lezioni frequentate da uno studente: le lezioni delle sue classi, nei suoi giorni, meno le assenze. */
function frequenza(id, ass, reg) {
  var ore = 0, lezioni = 0, totOre = 0;
  ass.filter(function (a) { return a.iscrizione === id; }).forEach(function (a) {
    reg.forEach(function (l) {
      if (l.classe !== a.classe || l.data < a.dal || l.data > a.al) return;
      if (l.stato === 'prevista' || l.stato === 'annullata') return;
      totOre += Number(l.ore) || 0;
      if (l.stato === 'persa') return;
      var assenti = String(l.assenti || '').split(/\s*,\s*/);
      if (assenti.indexOf(id) >= 0) return;
      ore += Number(l.ore) || 0; lezioni++;
    });
  });
  return {ore: ore, lezioni: lezioni, ore_previste: totOre};
}

/* ---------- ALLOGGI ---------- */

function salvaAlloggio(a) {
  autorizzato();
  if (!a.nome) throw new Error('Manca il nome dell’alloggio');
  var posti = Number(a.posti);
  if (!(posti >= 1 && posti <= 10)) throw new Error('Posti letto: da 1 a 10');
  if (!TIPI_ALLOGGIO.some(function (t) { return t[0] === a.tipo; })) throw new Error('Tipo di alloggio sconosciuto');
  var o = {nome: testo(a.nome, 200), tipo: a.tipo, posti: posti, indirizzo: testo(a.indirizzo, 500), contatto: testo(a.contatto, 500),
    istruzioni: testo(a.istruzioni, 3000), note: testo(a.note, 3000), attivo: a.attivo === 'no' ? 'no' : 'si'};
  return conBlocco(function () {
    if (a.id) {
      var r = trova('Alloggi', 'id', a.id);
      if (!r) throw new Error('Alloggio non trovato');
      aggiorna('Alloggi', r._r, o);
    } else {
      o.id = nuovoNumero('alloggi', 'AL');
      aggiungi('Alloggi', o);
    }
    return carica();
  });
}

function eliminaAlloggio(id) {
  autorizzato();
  return conBlocco(function () {
    if (leggi('Soggiorni').some(function (x) { return x.alloggio === id; })) throw new Error('L’alloggio ha delle prenotazioni: mettilo “non attivo” invece di eliminarlo.');
    var r = trova('Alloggi', 'id', id);
    if (r) scheda('Alloggi').deleteRow(r._r);
    return carica();
  });
}

/* Le notti in cui un alloggio ha più persone dei posti letto, contando anche "nuovo". */
function troppePersone(alloggio, arrivo, partenza, soggiorni, escludi) {
  var n = Number(alloggio.posti) || 1, pieni = [];
  for (var g = arrivo; g < partenza; g = piuGiorni(g, 1)) {
    var dentro = soggiorni.filter(function (x) { return x.alloggio === alloggio.id && x.id !== escludi && x.arrivo <= g && x.partenza > g; }).length;
    if (dentro + 1 > n) pieni.push(g);
  }
  return pieni;
}

/* Mette uno studente in un alloggio. Se l'alloggio è pieno in qualche notte si ferma, a meno di "forza". */
function prenotaAlloggio(x, forza) {
  autorizzato();
  if (!x.arrivo || !x.partenza || x.partenza <= x.arrivo) throw new Error('La partenza deve venire dopo l’arrivo');
  if (giorniTra(x.arrivo, x.partenza) > 370) throw new Error('Al massimo un anno');
  return conBlocco(function () {
    if (!trova('Iscrizioni', 'id', x.iscrizione)) throw new Error('Iscrizione non trovata');
    var a = trova('Alloggi', 'id', x.alloggio);
    if (!a) throw new Error('Alloggio non trovato');
    var sog = leggi('Soggiorni'), pieni = troppePersone(a, x.arrivo, x.partenza, sog, x.id);
    if (pieni.length && !forza) throw new Error('PIENO: ' + a.nome + ' è già pieno ' + (pieni.length === 1 ? 'la notte del ' : 'per ' + pieni.length + ' notti, dal ') + dataTesto(giorno(pieni[0])) + '.');
    var o = {iscrizione: x.iscrizione, alloggio: x.alloggio, arrivo: x.arrivo, partenza: x.partenza, note: testo(x.note, 2000), modificato: new Date()};
    if (x.id) {
      var r = sog.filter(function (y) { return y.id === x.id; })[0];
      if (!r) throw new Error('Prenotazione non trovata');
      aggiorna('Soggiorni', r._r, o);
    } else {
      o.id = nuovoNumero('soggiorni', 'S');
      aggiungi('Soggiorni', o);
    }
    return carica();
  });
}

function togliSoggiorno(id) {
  autorizzato();
  return conBlocco(function () {
    var r = trova('Soggiorni', 'id', id);
    if (r) scheda('Soggiorni').deleteRow(r._r);
    return carica();
  });
}

/* Indirizzo e date dell'alloggio di uno studente, per le email ("" se non ne ha). */
function testoAlloggio(iscrizione, en) {
  var alloggi = {}; leggi('Alloggi').forEach(function (a) { alloggi[a.id] = a; });
  return leggi('Soggiorni').filter(function (x) { return x.iscrizione === iscrizione && alloggi[x.alloggio]; })
    .sort(function (a, b) { return a.arrivo < b.arrivo ? -1 : 1; }).map(function (x) {
      var a = alloggi[x.alloggio];
      return (en ? 'Accommodation: ' : 'Alloggio: ') + [a.nome, a.indirizzo].filter(String).join(', ') +
        (en ? ', from ' + x.arrivo + ' to ' + x.partenza : ', dal ' + dataTesto(giorno(x.arrivo)) + ' al ' + dataTesto(giorno(x.partenza))) +
        (a.istruzioni ? '\n' + a.istruzioni : '');
    }).join('\n\n');
}

/* L'email allo studente con l'alloggio: indirizzo, date, istruzioni. */
function mandaAlloggio(iscrizione) {
  autorizzato();
  var v = trova('Iscrizioni', 'id', iscrizione);
  if (!v || !v.email) throw new Error('Manca l’email dello studente');
  var en = v.lingua === 'en', t = testoAlloggio(v.id, en);
  if (!t) throw new Error('Lo studente non ha ancora un alloggio');
  var corpo = (en ? ['Dear ' + v.nome + ',', '', 'here are the details of your accommodation in Assisi:', '']
    : ['Ciao ' + v.nome + ',', '', 'ecco i dettagli del tuo alloggio ad Assisi:', '']).concat([t, '',
    en ? 'If you arrive late or your plans change, please let us know.' : 'Se arrivi tardi o cambi programma, scrivici.',
    '', en ? 'Best wishes,' : 'A presto,', NOME_SCUOLA, EMAIL_STAFF]).join('\n');
  MailApp.sendEmail({to: v.email, replyTo: EMAIL_STAFF, name: NOME_SCUOLA, subject: en ? 'Your accommodation in Assisi' : 'Il tuo alloggio ad Assisi', body: corpo});
  registra('alloggio', 'alloggio:' + v.id + ':' + oggiIso(), v.id, v.email, 'inviato');
  return carica();
}

/* ---------- CHIUSURE, LABORATORI E ATTIVITÀ ---------- */

function chiave(e) { return e.tipo + '|' + normale(e.nome) + '|' + e.dal; }

/* Legge dal sito le chiusure (data/alia.json) e le date dei laboratori (data/laboratori.json).
   Tiene orario, luogo, chi lo segue, posti e note già scritti; toglie le date che il sito non ha più
   (se nessuno è iscritto). */
function importaDalSito() {
  autorizzato();
  var base = String(impostazioni().url_sito || 'https://aliassisi.it').replace(/\/+$/, '');
  var leggiJson = function (f) {
    var r = UrlFetchApp.fetch(base + '/data/' + f, {muteHttpExceptions: true, followRedirects: true});
    if (r.getResponseCode() !== 200) throw new Error('Non riesco a leggere ' + base + '/data/' + f + ' (' + r.getResponseCode() + ')');
    return JSON.parse(r.getContentText());
  };
  var sito = [];
  (leggiJson('alia.json').chiusure || []).forEach(function (c) {
    sito.push({tipo: 'chiusura', nome: c.it || 'Chiusura', nome_en: c.en || '', dal: c.dal, al: c.al || c.dal});
  });
  (leggiJson('laboratori.json').laboratori || []).forEach(function (l) {
    (l.date || []).forEach(function (g) { sito.push({tipo: 'laboratorio', nome: l.nome_it, nome_en: l.nome_en || '', dal: g, al: g}); });
  });
  sito = sito.filter(function (e) { return /^\d{4}-\d{2}-\d{2}$/.test(e.dal) && /^\d{4}-\d{2}-\d{2}$/.test(e.al); });
  return conBlocco(function () {
    var ora = leggi('Eventi'), part = leggi('Partecipanti'), per = {}, nuove = 0, tolte = 0;
    ora.forEach(function (e) { per[chiave(e)] = e; });
    var visti = {};
    sito.forEach(function (e) {
      var k = chiave(e); visti[k] = true;
      if (per[k]) return;
      e.id = nuovoNumero('eventi', 'E'); e.origine = 'sito'; e.nome = testo(e.nome, 300); e.nome_en = testo(e.nome_en, 300);
      aggiungi('Eventi', e); nuove++;
    });
    ora.filter(function (e) { return e.origine === 'sito' && !visti[chiave(e)] && !part.some(function (p) { return p.evento === e.id; }); })
      .reverse().forEach(function (e) { scheda('Eventi').deleteRow(e._r); tolte++; });
    var d = carica();
    d.nuove = nuove; d.tolte = tolte;
    return d;
  });
}

function salvaEvento(e) {
  autorizzato();
  if (!TIPI_EVENTO.some(function (t) { return t[0] === e.tipo; })) throw new Error('Tipo sconosciuto');
  if (!e.nome) throw new Error('Manca il nome');
  if (!e.dal) throw new Error('Manca la data');
  var al = e.al || e.dal;
  if (al < e.dal) throw new Error('La fine viene prima dell’inizio');
  var posti = e.posti === '' || e.posti === undefined ? '' : Number(e.posti);
  if (posti !== '' && !(posti >= 1)) throw new Error('Posti non validi');
  var o = {tipo: e.tipo, nome: testo(e.nome, 300), nome_en: testo(e.nome_en, 300), dal: e.dal, al: al, ora: testo(e.ora, 200),
    luogo: testo(e.luogo, 300), responsabile: testo(e.responsabile, 200), posti: posti, note: testo(e.note, 3000)};
  return conBlocco(function () {
    if (e.id) {
      var r = trova('Eventi', 'id', e.id);
      if (!r) throw new Error('Evento non trovato');
      aggiorna('Eventi', r._r, o);
    } else {
      o.id = nuovoNumero('eventi', 'E'); o.origine = 'manuale';
      aggiungi('Eventi', o);
    }
    var d = carica();
    d.evento = e.id || o.id;
    return d;
  });
}

function eliminaEvento(id) {
  autorizzato();
  return conBlocco(function () {
    leggi('Partecipanti').filter(function (p) { return p.evento === id; }).reverse().forEach(function (p) { scheda('Partecipanti').deleteRow(p._r); });
    var r = trova('Eventi', 'id', id);
    if (r) scheda('Eventi').deleteRow(r._r);
    return carica();
  });
}

/* Gli iscritti a un laboratorio o un'attività: sostituisce l'elenco con "ids". */
function iscriviEvento(evento, ids) {
  autorizzato();
  return conBlocco(function () {
    var e = trova('Eventi', 'id', evento);
    if (!e || e.tipo === 'chiusura') throw new Error('Evento non trovato');
    ids = (ids || []).filter(function (x, i, a) { return a.indexOf(x) === i; });
    if (e.posti && ids.length > Number(e.posti)) throw new Error('Posti: ' + e.posti + '. Iscritti scelti: ' + ids.length);
    var isc = {}; leggi('Iscrizioni').forEach(function (v) { isc[v.id] = v; });
    ids.forEach(function (x) { if (!isc[x]) throw new Error('Iscrizione non trovata: ' + x); });
    leggi('Partecipanti').filter(function (p) { return p.evento === evento; }).reverse().forEach(function (p) { scheda('Partecipanti').deleteRow(p._r); });
    ids.forEach(function (x) { aggiungi('Partecipanti', {evento: evento, iscrizione: x}); });
    return carica();
  });
}

/* Un'email sull'evento: agli iscritti, o a tutti gli studenti in corso quel giorno. */
function emailEvento(evento, chi, oggetto, corpo) {
  autorizzato();
  if (!oggetto || !corpo) throw new Error('Scrivi oggetto e testo');
  var e = trova('Eventi', 'id', evento);
  if (!e) throw new Error('Evento non trovato');
  var isc = leggi('Iscrizioni'), dest = {};
  if (chi === 'iscritti') {
    var ids = leggi('Partecipanti').filter(function (p) { return p.evento === evento; }).map(function (p) { return p.iscrizione; });
    isc.forEach(function (v) { if (ids.indexOf(v.id) >= 0 && v.email) dest[String(v.email).toLowerCase()] = v; });
  } else {
    isc.forEach(function (v) { if (v.email && v.stato !== 'Annullata' && v.stato !== 'Nuova' && v.inizio && v.fine && v.inizio <= e.dal && v.fine >= e.dal) dest[String(v.email).toLowerCase()] = v; });
  }
  var n = 0;
  Object.keys(dest).forEach(function (m) {
    MailApp.sendEmail({to: m, replyTo: EMAIL_STAFF, name: NOME_SCUOLA, subject: String(oggetto).slice(0, 200),
      body: riempi(String(corpo).slice(0, 10000), {nome: dest[m].nome})});
    registra('evento', 'evento:' + evento + ':' + oggiIso(), dest[m].id, m, 'inviato');
    n++;
  });
  if (!n) throw new Error('Nessun destinatario');
  var d = carica();
  d.inviate = n;
  return d;
}

/* ---------- DIPLOMI E ATTESTATI ---------- */

function idDaLink(s) {
  var m = String(s || '').match(/[-\w]{25,}/);
  return m ? m[0] : '';
}

function periodoTesto(dal, al) {
  if (!dal) return '';
  var a = giorno(dal), b = giorno(al || dal);
  if (a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth())
    return 'dal ' + a.getDate() + ' al ' + dataTesto(b);
  if (a.getFullYear() === b.getFullYear())
    return 'dal ' + a.getDate() + ' ' + MESI[a.getMonth()] + ' al ' + dataTesto(b);
  return 'dal ' + dataTesto(a) + ' al ' + dataTesto(b);
}

/* Crea un PDF con una pagina per studente (tipo: "diploma" o "attestato"). */
function creaDocumenti(tipo, ids) {
  autorizzato();
  if (tipo !== 'diploma' && tipo !== 'attestato') throw new Error('Tipo di documento sconosciuto');
  if (!ids || !ids.length) throw new Error('Scegli almeno uno studente');
  if (ids.length > 60) throw new Error('Al massimo 60 studenti per volta');
  var p = props(), modello = p.getProperty('modello_' + tipo);
  if (!modello) throw new Error('Manca il modello del ' + tipo + ': impostalo in Impostazioni.');
  var tutte = leggi('Iscrizioni'), ass = leggi('Assegnazioni'), reg = leggi('Registro');
  var studenti = ids.map(function (id) {
    var v = tutte.filter(function (r) { return r.id === id; })[0];
    if (!v) throw new Error('Iscrizione non trovata: ' + id);
    if (tipo === 'diploma' && !v.livello_finale) throw new Error('Manca il livello raggiunto di ' + v.nome + ' ' + v.cognome);
    return v;
  });
  return conBlocco(function () {
    var oggi = dataTesto(new Date());
    var sost = studenti.map(function (v) {
      var f = frequenza(v.id, ass, reg);
      return {
        v: v, numero: nuovoNumero(tipo === 'diploma' ? 'diplomi' : 'attestati', tipo === 'diploma' ? 'D' : 'A'),
        campi: {
          nome: v.nome, cognome: v.cognome, studente: v.nome + ' ' + v.cognome,
          corso: v.corso_nome + (v.tema ? ' – ' + v.tema : ''),
          periodo: periodoTesto(v.inizio, v.fine),
          dal: v.inizio ? dataTesto(giorno(v.inizio)) : '', al: v.fine ? dataTesto(giorno(v.fine)) : '',
          livello: String(v.livello_finale || ''), livello_iniziale: String(v.livello || ''),
          ore: String(f.ore), lezioni: String(v.lezioni_totali || f.lezioni),
          nazionalita: String(v.nazionalita || ''),
          nascita: v.nascita ? dataTesto(giorno(v.nascita)) : '', luogo_nascita: String(v.luogo_nascita || ''),
          data: oggi
        }
      };
    });
    sost.forEach(function (s) { s.campi.numero = s.numero; });
    var nome = (tipo === 'diploma' ? 'Diplomi ' : 'Attestati ') + Utilities.formatDate(new Date(), fusoOrario(), 'yyyy-MM-dd HH.mm') +
      (sost.length === 1 ? ' ' + sost[0].v.cognome + ' ' + sost[0].v.nome : ' (' + sost.length + ')');
    var link = generaPdf(modello, sost.map(function (s) { return s.campi; }), nome);
    sost.forEach(function (s) {
      aggiungi('Documenti', {data: new Date(), tipo: tipo, numero: s.numero, iscrizione: s.v.id,
        studente: s.v.nome + ' ' + s.v.cognome, link: link});
      if (tipo === 'diploma') aggiorna('Iscrizioni', s.v._r, {diploma: link});
    });
    var d = carica();
    d.creato = link;
    return d;
  });
}

function sostituisci(el, campi) {
  Object.keys(campi).forEach(function (k) { el.replaceText('\\{\\{' + k + '\\}\\}', campi[k]); });
}

/* Copia il modello (Documenti o Presentazioni Google), una pagina per studente, e lo salva in PDF. */
function generaPdf(modelloId, elenco, nome) {
  var cartella = DriveApp.getFolderById(props().getProperty('cartella_diplomi'));
  var file = DriveApp.getFileById(modelloId), tipo = file.getMimeType();
  var copia = file.makeCopy(nome, cartella);
  if (tipo === MimeType.GOOGLE_SLIDES) {
    var pres = SlidesApp.openById(copia.getId()), base = pres.getSlides();
    elenco.forEach(function (campi) {
      base.forEach(function (sl) {
        var nuova = sl.duplicate();
        nuova.move(pres.getSlides().length);
        Object.keys(campi).forEach(function (k) { nuova.replaceAllText('{{' + k + '}}', campi[k]); });
      });
    });
    base.forEach(function (sl) { sl.remove(); });
    pres.saveAndClose();
  } else if (tipo === MimeType.GOOGLE_DOCS) {
    var doc = DocumentApp.openById(copia.getId()), corpo = doc.getBody(), originali = [];
    for (var i = 0; i < corpo.getNumChildren(); i++) originali.push(corpo.getChild(i).copy());
    elenco.slice(1).forEach(function (campi) {
      corpo.appendPageBreak();
      originali.forEach(function (el) {
        var t = el.getType(), nuovo;
        if (t === DocumentApp.ElementType.PARAGRAPH) nuovo = corpo.appendParagraph(el.copy());
        else if (t === DocumentApp.ElementType.TABLE) nuovo = corpo.appendTable(el.copy());
        else if (t === DocumentApp.ElementType.LIST_ITEM) nuovo = corpo.appendListItem(el.copy());
        if (nuovo) sostituisci(nuovo, campi);
      });
    });
    for (var j = 0; j < originali.length; j++) sostituisci(corpo.getChild(j), elenco[0]);
    doc.saveAndClose();
  } else {
    copia.setTrashed(true);
    throw new Error('Il modello deve essere un Documento o una Presentazione Google.');
  }
  var pdf = cartella.createFile(copia.getAs('application/pdf')).setName(nome + '.pdf');
  copia.setTrashed(true);
  return pdf.getUrl();
}

/* Dal menu del foglio: il diploma della riga selezionata (come prima). */
function creaDiploma() { creaDaRiga('diploma'); }
function creaAttestato() { creaDaRiga('attestato'); }
function creaDaRiga(tipo) {
  var ui = SpreadsheetApp.getUi(), foglio = SpreadsheetApp.getActiveSheet();
  if (foglio.getName() !== 'Iscrizioni') { ui.alert('Apri il foglio "Iscrizioni" e seleziona la riga dello studente.'); return; }
  var r = foglio.getActiveRange().getRow();
  if (r < 2) { ui.alert('Seleziona la riga dello studente.'); return; }
  var id = foglio.getRange(r, colonna('id')).getValue();
  try {
    var d = creaDocumenti(tipo, [String(id)]);
    ui.alert('Fatto. Il PDF è nella cartella "ALIA – Diplomi":\n' + d.creato);
  } catch (err) { ui.alert(String(err.message || err)); }
}

/* ---------- FATTURE IN CLOUD ---------- */

function fic(percorso) {
  var token = props().getProperty('fic_token');
  if (!token) throw new Error('Manca il token di Fatture in Cloud: impostalo in Impostazioni.');
  for (var tentativo = 0; tentativo < 3; tentativo++) {
    var r = UrlFetchApp.fetch(FIC_API + percorso, {
      headers: {Authorization: 'Bearer ' + token, Accept: 'application/json'}, muteHttpExceptions: true
    });
    var c = r.getResponseCode();
    if (c === 200) return JSON.parse(r.getContentText());
    if (c === 429) { Utilities.sleep(5000 * (tentativo + 1)); continue; }
    throw new Error('Fatture in Cloud ha risposto ' + c + ': ' + r.getContentText().slice(0, 300));
  }
  throw new Error('Fatture in Cloud: troppe richieste, riprova tra qualche minuto.');
}

function aziendaFic() {
  var p = props(), id = p.getProperty('fic_azienda');
  if (id) return id;
  var l = ((fic('/user/companies').data || {}).companies) || [];
  if (!l.length) throw new Error('Fatture in Cloud: nessuna azienda collegata al token.');
  p.setProperty('fic_azienda', String(l[0].id));
  return String(l[0].id);
}

function documentiFic(azienda, tipo, dal) {
  var tutti = [], pagina = 1, ultima = 1;
  do {
    var r = fic('/c/' + azienda + '/issued_documents?type=' + tipo + '&fieldset=detailed&per_page=100&page=' + pagina +
      '&sort=-date&q=' + encodeURIComponent("date >= '" + dal + "'"));
    tutti = tutti.concat(r.data || []);
    ultima = r.last_page || 1;
    pagina++;
  } while (pagina <= ultima && pagina <= 20);
  return tutti;
}

function normale(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z]/g, ' ').replace(/\s+/g, ' ').trim(); }

/* L'iscrizione di una fattura: stessa email (studente o fattura), se no nome e cognome nel nome del cliente. */
function abbina(doc, iscrizioni) {
  var e = doc.entity || {}, email = String(e.email || '').toLowerCase(), nome = ' ' + normale(e.name) + ' ';
  var cand = iscrizioni.filter(function (v) {
    return email && (String(v.email).toLowerCase() === email || String(v.f_email).toLowerCase() === email);
  });
  if (!cand.length) cand = iscrizioni.filter(function (v) {
    return v.cognome && nome.indexOf(' ' + normale(v.cognome) + ' ') >= 0 && nome.indexOf(' ' + normale(v.nome).split(' ')[0] + ' ') >= 0;
  });
  cand = cand.filter(function (v) { return v.stato !== 'Annullata'; });
  if (!cand.length) return '';
  // La più recente arrivata prima della fattura (o, se nessuna, la più recente).
  cand.sort(function (a, b) { return a.ricevuta < b.ricevuta ? 1 : -1; });
  var prima = cand.filter(function (v) { return v.ricevuta.slice(0, 10) <= piuGiorni(doc.date, 1); });
  return (prima[0] || cand[0]).id;
}

/* Legge fatture e proforma dell'ultimo anno, aggiorna la scheda Fatture
   e scrive in Pagamenti i pagamenti saldati delle fatture (non delle proforma). */
function sincronizzaFIC() {
  autorizzato();
  aggiornaFIC();
  return carica();
}

function aggiornaFIC() {
  var azienda = aziendaFic(), dal = piuGiorni(oggiIso(), -400);
  var docs = documentiFic(azienda, 'invoice', dal).concat(documentiFic(azienda, 'proforma', dal));
  conBlocco(function () {
    var iscrizioni = leggi('Iscrizioni'), vecchie = {};
    leggi('Fatture').forEach(function (f) { vecchie[f.fic_id] = f; });
    var pagate = {};
    leggiPagamenti().forEach(function (p) { pagate[p.note] = true; });
    var righe = docs.map(function (d) {
      var pag = d.payments_list || [];
      var daPagare = pag.length ? pag.filter(function (p) { return p.status === 'not_paid'; })
        .reduce(function (s, p) { return s + Number(p.amount || 0); }, 0) : (d.next_due_date ? Number(d.amount_gross || 0) : 0);
      var v = vecchie[String(d.id)], manuale = v && v.abbinata === 'manuale';
      var o = {
        fic_id: String(d.id), tipo: d.type === 'proforma' ? 'proforma' : 'fattura',
        numero: String(d.number || '') + (d.numeration || ''), data: d.date,
        cliente: testo((d.entity || {}).name, 300), email: testo((d.entity || {}).email, 300),
        importo: Number(d.amount_gross || 0), da_pagare: Math.round(daPagare * 100) / 100,
        scadenza: d.next_due_date || '',
        iscrizione: manuale ? v.iscrizione : abbina(d, iscrizioni),
        abbinata: manuale ? 'manuale' : 'auto', aggiornata: new Date()
      };
      if (o.tipo === 'fattura' && o.iscrizione) pag.forEach(function (p) {
        var chiave = 'fic:' + d.id + ':' + p.id;
        if (p.status === 'paid' && !pagate[chiave]) {
          scheda('Pagamenti').appendRow([o.iscrizione, giorno(p.paid_date || d.date), Number(p.amount || 0), 'Fatture in Cloud', chiave]);
          pagate[chiave] = true;
        }
      });
      return o;
    });
    var s = scheda('Fatture'), n = s.getLastRow() - 1;
    if (n > 0) s.getRange(2, 1, n, SCHEMI.Fatture.length).clearContent();
    if (righe.length) s.getRange(2, 1, righe.length, SCHEMI.Fatture.length).setValues(righe.map(function (o) {
      return SCHEMI.Fatture.map(function (c) { return valoreCella(c[0], o[c[0]]); });
    }));
  });
}

/* I pagamenti già scritti (la scheda Pagamenti è di Codice.gs e non ha chiavi). */
function leggiPagamenti() {
  var s = scheda('Pagamenti'), n = s.getLastRow() - 1;
  if (n < 1) return [];
  return s.getRange(2, 1, n, 5).getValues().map(function (r) {
    return {iscrizione: String(r[0]), data: iso(r[1]), importo: r[2], metodo: r[3], note: String(r[4])};
  });
}

function abbinaFattura(ficId, iscrizione) {
  autorizzato();
  return conBlocco(function () {
    var f = trova('Fatture', 'fic_id', ficId);
    if (!f) throw new Error('Fattura non trovata');
    if (iscrizione && !trova('Iscrizioni', 'id', iscrizione)) throw new Error('Iscrizione non trovata');
    aggiorna('Fatture', f._r, {iscrizione: iscrizione || '', abbinata: 'manuale'});
    return carica();
  });
}

/* ---------- EMAIL AUTOMATICHE ---------- */

function riempi(t, campi) {
  return String(t).replace(/\{\{(\w+)\}\}/g, function (m, k) { return campi[k] !== undefined ? campi[k] : m; });
}

/* modo: "si" manda allo studente, "prova" manda allo staff con il destinatario nell'oggetto. */
function invia(modo, a, oggetto, corpo) {
  if (modo === 'prova') MailApp.sendEmail({to: EMAIL_STAFF, name: NOME_SCUOLA, subject: '[PROVA → ' + a + '] ' + oggetto, body: corpo});
  else MailApp.sendEmail({to: a, replyTo: EMAIL_STAFF, name: NOME_SCUOLA, subject: oggetto, body: corpo});
}

function giaInviato(prom, chiave) { return prom.some(function (p) { return p.chiave === chiave && p.esito !== 'errore'; }); }

function registra(tipo, chiave, iscrizione, email, esito) {
  aggiungi('Promemoria', {data: new Date(), tipo: tipo, chiave: chiave, iscrizione: iscrizione, email: email, esito: esito});
}

/* altro: true se l'email va a chi riceve la fattura (un'agenzia, un ente) e non allo studente. */
function testoPromemoria(f, v, scaduta, en, altro) {
  var imp = impostazioni(), scad = en ? f.scadenza : dataTesto(giorno(f.scadenza));
  var r = en
    ? ['Dear ' + (altro ? f.cliente : v.nome) + ',', '',
       scaduta ? 'our records show that the payment for ' + (f.tipo === 'proforma' ? 'proforma invoice ' : 'invoice ') + f.numero + ' (' + euro(f.da_pagare) + ') was due on ' + scad + '.'
               : 'this is a reminder that the payment for ' + (f.tipo === 'proforma' ? 'proforma invoice ' : 'invoice ') + f.numero + ' (' + euro(f.da_pagare) + ') is due on ' + scad + '.']
    : [(altro ? 'Gentile ' + f.cliente : 'Ciao ' + v.nome) + ',', '',
       scaduta ? 'risulta ancora da pagare ' + (f.tipo === 'proforma' ? 'la proforma ' : 'la fattura ') + f.numero + ' (' + euro(f.da_pagare) + '), scaduta il ' + scad + '.'
               : 'ricordiamo che il pagamento ' + (f.tipo === 'proforma' ? 'della proforma ' : 'della fattura ') + f.numero + ' (' + euro(f.da_pagare) + ') scade il ' + scad + '.'];
  if (altro) r.push(en ? 'Student: ' + v.nome + ' ' + v.cognome + ' (' + v.corso_nome + ').' : 'Studente: ' + v.nome + ' ' + v.cognome + ' (' + v.corso_nome + ').');
  if (imp.dati_pagamento) r.push('', imp.dati_pagamento);
  r.push('', en ? 'If you have already paid, please ignore this message. Thank you!' : 'Se hai già pagato, ignora questo messaggio. Grazie!',
    '', en ? 'Best wishes,' : 'A presto,', NOME_SCUOLA, EMAIL_STAFF);
  return {
    oggetto: en ? (scaduta ? 'Payment overdue: ' : 'Payment reminder: ') + f.numero : (scaduta ? 'Pagamento scaduto: ' : 'Promemoria di pagamento: ') + f.numero,
    corpo: r.join('\n')
  };
}

/* Promemoria: N giorni prima della scadenza, 3 giorni dopo, 17 giorni dopo. Una volta sola ciascuno. */
function promemoriaPagamenti(modo, solo) {
  var oggi = oggiIso(), giorniPrima = +impostazioni().promemoria_giorni || 7;
  var isc = {}; leggi('Iscrizioni').forEach(function (v) { isc[v.id] = v; });
  var prom = leggi('Promemoria'), fatti = 0;
  leggi('Fatture').forEach(function (f) {
    if (solo && f.fic_id !== solo) return;
    var v = isc[f.iscrizione];
    if (!(f.da_pagare > 0) || !f.scadenza || !v || v.stato === 'Annullata') return;
    // L'email del cliente della fattura (in Fatture in Cloud) se c'è, se no quella dello studente.
    var a = String(f.email || v.email || '').trim(), altro = a.toLowerCase() !== String(v.email).toLowerCase();
    if (!a) return;
    // Una proforma non serve più se l'iscrizione risulta già pagata.
    if (f.tipo === 'proforma' && !(Number(v.residuo) > 0)) return;
    var g = giorniTra(oggi, f.scadenza), tipo = '';
    if (solo) tipo = g >= 0 ? 'manuale-prima' : 'manuale-scaduta';
    else if (g < -17) tipo = 'sollecito';
    else if (g <= -3) tipo = 'scaduta';
    else if (g >= 0 && g <= giorniPrima) tipo = 'prima';
    if (!tipo) return;
    var base = 'pag:' + f.fic_id + ':' + f.scadenza + ':';
    // Il sollecito parte solo dopo l'avviso di scadenza.
    if (tipo === 'sollecito' && !giaInviato(prom, base + 'scaduta')) tipo = 'scaduta';
    var chiave = base + tipo + (solo ? ':' + oggi : '');
    if (giaInviato(prom, chiave)) return;
    var t = testoPromemoria(f, v, g < 0, v.lingua === 'en', altro);
    try { invia(modo, a, t.oggetto, t.corpo); registra('pagamento', chiave, v.id, a, modo === 'prova' ? 'prova' : 'inviato'); fatti++; }
    catch (err) { registra('pagamento', chiave, v.id, a, 'errore'); }
  });
  return fatti;
}

function mandaPromemoria(ficId) {
  autorizzato();
  var modo = impostazioni().promemoria === 'si' ? 'si' : 'prova';
  conBlocco(function () { if (!promemoriaPagamenti(modo, ficId)) throw new Error('Nessun promemoria da mandare per questo documento (già pagato o senza scadenza?).'); });
  return carica();
}

function inCorso(v, oggi) { return v.inizio && v.fine && v.inizio <= oggi && v.fine >= oggi && v.stato !== 'Annullata'; }

function compleanni(modo, chi) {
  var oggi = oggiIso(), md = oggi.slice(5), anno = oggi.slice(0, 4), imp = impostazioni(), prom = leggi('Promemoria'), visti = {};
  leggi('Iscrizioni').forEach(function (v) {
    if (!v.nascita || v.nascita.slice(5) !== md || !v.email || v.stato === 'Annullata' || v.stato === 'Nuova') return;
    if (chi === 'in_corso' && !inCorso(v, oggi)) return;
    var email = String(v.email).toLowerCase(), chiave = 'compleanno:' + email + ':' + anno;
    if (visti[email] || giaInviato(prom, chiave)) return;
    visti[email] = true;
    var en = v.lingua === 'en';
    var corpo = riempi(en ? imp.testo_compleanno_en : imp.testo_compleanno_it, {nome: v.nome, cognome: v.cognome});
    try { invia(modo, v.email, en ? 'Happy birthday, ' + v.nome + '!' : 'Buon compleanno, ' + v.nome + '!', corpo); registra('compleanno', chiave, v.id, v.email, modo === 'prova' ? 'prova' : 'inviato'); }
    catch (err) { registra('compleanno', chiave, v.id, v.email, 'errore'); }
  });
}

function benvenuti(modo) {
  var oggi = oggiIso(), imp = impostazioni(), giorni = +imp.benvenuto_giorni || 7, prom = leggi('Promemoria');
  leggi('Iscrizioni').forEach(function (v) {
    if (!v.inizio || !v.email || ['Confermata', 'Pagata'].indexOf(v.stato) < 0) return;
    var g = giorniTra(oggi, v.inizio);
    if (g < 1 || g > giorni) return;
    var chiave = 'benvenuto:' + v.id;
    if (giaInviato(prom, chiave)) return;
    var en = v.lingua === 'en';
    var corpo = riempi(en ? imp.testo_benvenuto_en : imp.testo_benvenuto_it,
      {nome: v.nome, cognome: v.cognome, corso: v.corso_nome, inizio: en ? v.inizio : dataTesto(giorno(v.inizio)), fine: en ? v.fine : (v.fine ? dataTesto(giorno(v.fine)) : ''),
       alloggio: testoAlloggio(v.id, en)});
    try { invia(modo, v.email, en ? 'See you soon in Assisi!' : 'Ci vediamo presto ad Assisi!', corpo); registra('benvenuto', chiave, v.id, v.email, modo === 'prova' ? 'prova' : 'inviato'); }
    catch (err) { registra('benvenuto', chiave, v.id, v.email, 'errore'); }
  });
}

/* Ogni mattina allo staff: arrivi, partenze, compleanni in classe, pagamenti scaduti, iscrizioni nuove. */
function riepilogoStaff() {
  var oggi = oggiIso(), fra7 = piuGiorni(oggi, 7), isc = leggi('Iscrizioni'), r = [];
  var attivi = isc.filter(function (v) { return v.stato !== 'Annullata'; });
  var arrivi = attivi.filter(function (v) { return v.inizio >= oggi && v.inizio <= fra7; });
  var partenze = attivi.filter(function (v) { return v.fine >= oggi && v.fine <= fra7; });
  var nuove = isc.filter(function (v) { return v.stato === 'Nuova'; });
  var auguri = attivi.filter(function (v) { return inCorso(v, oggi) && v.nascita && v.nascita.slice(5) === oggi.slice(5); });
  var scadute = leggi('Fatture').filter(function (f) { return f.da_pagare > 0 && f.scadenza && f.scadenza < oggi; });
  var nome = function (v) { return '- ' + v.nome + ' ' + v.cognome + ' (' + v.corso_nome + ', ' + v.inizio + ' → ' + v.fine + ')'; };
  if (auguri.length) r.push('Compleanni oggi in classe:', auguri.map(nome).join('\n'), '');
  if (arrivi.length) r.push('Arrivi nei prossimi 7 giorni:', arrivi.map(nome).join('\n'), '');
  if (partenze.length) r.push('Finiscono nei prossimi 7 giorni (diplomi e attestati):', partenze.map(nome).join('\n'), '');
  if (nuove.length) r.push('Iscrizioni ancora "Nuova": ' + nuove.length, '');
  var ev = leggi('Eventi').filter(function (e) { return e.tipo !== 'chiusura' && e.dal >= oggi && e.dal <= fra7; });
  if (ev.length) r.push('Laboratori e attività della settimana:', ev.map(function (e) { return '- ' + dataTesto(giorno(e.dal)) + ': ' + e.nome + (e.ora ? ', ' + e.ora : ' (orario da decidere)'); }).join('\n'), '');
  var ch = leggi('Eventi').filter(function (e) { return e.tipo === 'chiusura' && e.dal >= oggi && e.dal <= fra7; });
  if (ch.length) r.push('Chiusure: ' + ch.map(function (e) { return e.nome + ' (' + dataTesto(giorno(e.dal)) + (e.al !== e.dal ? ' – ' + dataTesto(giorno(e.al)) : '') + ')'; }).join(', '), '');
  if (scadute.length) r.push('Fatture o proforma scadute e non pagate: ' + scadute.length + ' (' + euro(scadute.reduce(function (s, f) { return s + Number(f.da_pagare); }, 0)) + ')', '');
  if (!r.length) return;
  var url = impostazioni().url_gestionale;
  r.push(url ? 'Gestionale: ' + url : 'Foglio: ' + SpreadsheetApp.getActive().getUrl());
  MailApp.sendEmail({to: EMAIL_STAFF, name: 'Gestionale ALIA', subject: 'ALIA, oggi ' + dataTesto(giorno(oggi)), body: r.join('\n')});
}

/* Il trigger di ogni mattina. Ogni parte va avanti anche se un'altra si ferma. */
function ogniGiorno() {
  var imp = impostazioni();
  [
    function () { if (imp.promemoria !== 'no' && props().getProperty('fic_token')) { aggiornaFIC(); conBlocco(function () { promemoriaPagamenti(imp.promemoria); }); } },
    function () { if (imp.compleanni !== 'no') conBlocco(function () { compleanni(imp.compleanni, imp.compleanni_chi); }); },
    function () { if (imp.benvenuto !== 'no') conBlocco(function () { benvenuti(imp.benvenuto); }); },
    function () { if (imp.riepilogo === 'si') riepilogoStaff(); }
  ].forEach(function (f) { try { f(); } catch (err) { console.error(err); } });
}

function attivaInvii() {
  autorizzato();
  ScriptApp.getProjectTriggers().forEach(function (t) { if (['ogniGiorno', 'ogniOra'].indexOf(t.getHandlerFunction()) >= 0) ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('ogniGiorno').timeBased().everyDays(1).atHour(8).inTimezone(fusoOrario()).create();
  ScriptApp.newTrigger('ogniOra').timeBased().everyHours(1).create();
  return carica();
}

/* Un messaggio a tutti gli studenti di una classe (per esempio: "domani lezione in città"). */
function emailClasse(classe, oggetto, corpo) {
  autorizzato();
  if (!oggetto || !corpo) throw new Error('Scrivi oggetto e testo');
  var c = trova('Classi', 'id', classe);
  if (!c) throw new Error('Classe non trovata');
  var oggi = oggiIso(), isc = {}, n = 0;
  leggi('Iscrizioni').forEach(function (v) { isc[v.id] = v; });
  var dest = {};
  leggi('Assegnazioni').forEach(function (a) {
    var v = isc[a.iscrizione];
    if (a.classe === classe && a.al >= oggi && v && v.email && v.stato !== 'Annullata') dest[String(v.email).toLowerCase()] = v;
  });
  Object.keys(dest).forEach(function (e) {
    MailApp.sendEmail({to: e, replyTo: EMAIL_STAFF, name: NOME_SCUOLA, subject: String(oggetto).slice(0, 200),
      body: riempi(String(corpo).slice(0, 10000), {nome: dest[e].nome})});
    registra('classe', 'classe:' + classe + ':' + oggi, dest[e].id, e, 'inviato');
    n++;
  });
  var d = carica();
  d.inviate = n;
  return d;
}

/* ---------- IMPOSTAZIONI ---------- */

function salvaImpostazioni(o) {
  autorizzato();
  var p = props();
  Object.keys(o || {}).forEach(function (k) {
    if (k === 'fic_token') { if (o[k]) { p.setProperty('fic_token', String(o[k]).trim()); p.deleteProperty('fic_azienda'); } return; }
    if (!Object.prototype.hasOwnProperty.call(IMPOSTAZIONI, k)) throw new Error('Impostazione sconosciuta: ' + k);
    var v = String(o[k] === undefined || o[k] === null ? '' : o[k]).slice(0, 5000);
    if (k === 'modello_diploma' || k === 'modello_attestato') {
      v = idDaLink(v);
      if (v) {
        var mime = DriveApp.getFileById(v).getMimeType();
        if (mime !== MimeType.GOOGLE_DOCS && mime !== MimeType.GOOGLE_SLIDES) throw new Error('Il modello deve essere un Documento o una Presentazione Google (apri il file Word o PowerPoint con Google e salvalo come file Google).');
      }
    }
    p.setProperty(k, v);
  });
  return carica();
}

/* Le schede del gestionale e il modello dell'attestato. Chiamata da configura() in Codice.gs. */
function configuraGestionale() {
  var ss = SpreadsheetApp.getActive(), p = props();
  Object.keys(SCHEMI).forEach(function (nome) {
    var s = ss.getSheetByName(nome) || ss.insertSheet(nome);
    s.getRange(1, 1, 1, SCHEMI[nome].length).setValues([SCHEMI[nome].map(function (c) { return c[1]; })])
      .setFontWeight('bold').setBackground('#3d5570').setFontColor('#ffffff');
    s.setFrozenRows(1);
    SCHEMI[nome].forEach(function (c, j) {
      if (['inizio', 'fine', 'dal', 'al', 'data', 'scadenza', 'arrivo', 'partenza'].indexOf(c[0]) >= 0) s.getRange(2, j + 1, s.getMaxRows() - 1, 1).setNumberFormat('dd/mm/yyyy');
      if (['importo', 'da_pagare'].indexOf(c[0]) >= 0) s.getRange(2, j + 1, s.getMaxRows() - 1, 1).setNumberFormat('#,##0.00 €');
    });
  });
  ['Promemoria', 'Documenti'].forEach(function (n) { ss.getSheetByName(n).getRange(2, 1, ss.getSheetByName(n).getMaxRows() - 1, 1).setNumberFormat('dd/mm/yyyy hh:mm'); });
  // Il primo modello del diploma usava {{nome}} per nome e cognome insieme: ora sono due campi.
  var dip = p.getProperty('modello_diploma');
  if (dip && !p.getProperty('modello_diploma_v2')) {
    try {
      var corpo = DocumentApp.openById(dip).getBody();
      if (corpo.getText().indexOf('{{cognome}}') < 0) corpo.replaceText('\\{\\{nome\\}\\}', '{{nome}} {{cognome}}');
      corpo.replaceText('dal \\{\\{dal\\}\\} al \\{\\{al\\}\\}', '{{periodo}}');
    } catch (e) {}
    p.setProperty('modello_diploma_v2', '1');
  }
  if (!p.getProperty('modello_attestato')) {
    var doc = DocumentApp.create('ALIA – Modello dell’attestato di frequenza');
    var b = doc.getBody(), C = DocumentApp.HorizontalAlignment.CENTER;
    b.appendParagraph(NOME_SCUOLA).setHeading(DocumentApp.ParagraphHeading.TITLE).setAlignment(C);
    b.appendParagraph('Attestato di frequenza').setHeading(DocumentApp.ParagraphHeading.HEADING1).setAlignment(C);
    b.appendParagraph('Si attesta che').setAlignment(C);
    b.appendParagraph('{{nome}} {{cognome}}').setHeading(DocumentApp.ParagraphHeading.HEADING2).setAlignment(C);
    b.appendParagraph('nato/a a {{luogo_nascita}} il {{nascita}}, ha frequentato il corso {{corso}} {{periodo}}, per un totale di {{ore}} ore di lezione.').setAlignment(C);
    b.appendParagraph('Assisi, {{data}}          N. {{numero}}').setAlignment(C);
    doc.saveAndClose();
    DriveApp.getFileById(doc.getId()).moveTo(DriveApp.getFolderById(p.getProperty('cartella_diplomi')));
    p.setProperty('modello_attestato', doc.getId());
  }
}
