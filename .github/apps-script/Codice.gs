/**
 * Iscrizioni ALIA.
 * Riceve le iscrizioni dal configuratore del sito, le scrive nel foglio
 * "Iscrizioni", salva il passaporto in una cartella Drive privata e manda
 * due email: la conferma allo studente e l'avviso allo staff.
 * Dal menu "ALIA" del foglio si creano i diplomi in PDF.
 *
 * Source: .github/apps-script/Codice.gs nel repository del sito.
 * Come installarlo: .github/apps-script/ISTRUZIONI.md.
 */

var EMAIL_STAFF = 'info@aliassisi.it';
// Il test d'ingresso per chi non è principiante (lo stesso link è in data/configuratore.json del sito).
var TEST_INGRESSO = 'https://docs.google.com/forms/d/e/1FAIpQLSdDSA9G7P8uD0zOkvdnI9DTULQdrmPseKHEYw3NdC8mrA7gxg/viewform';
var NOME_SCUOLA = 'Accademia Lingua Italiana Assisi';
var MAX_FILE = 5 * 1024 * 1024;
var TIPI_FILE = {'application/pdf': '.pdf', 'image/jpeg': '.jpg', 'image/png': '.png'};
var MAX_PER_ORA = 5;
var STATI = ['Nuova', 'Confermata', 'Pagata', 'In corso', 'Conclusa', 'Annullata'];
var MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
            'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];

/* Le colonne del foglio "Iscrizioni": [chiave, intestazione]. Le colonne dello
   staff (prezzo, pagato, livello raggiunto, diploma, note) si compilano a mano. */
var COLONNE = [
  ['id', 'N.'], ['ricevuta', 'Ricevuta il'], ['stato', 'Stato'],
  ['corso_nome', 'Corso'], ['tema', 'Tema'], ['formula', 'Formula'],
  ['settimane', 'Settimane'], ['lezioni_totali', 'Lezioni totali'],
  ['inizio', 'Inizio'], ['fine', 'Fine'],
  ['alloggio', 'Alloggio'], ['settimane_alloggio', 'Settimane alloggio'], ['extra', 'Extra'],
  ['totale', 'Totale stimato'], ['prezzo', 'Prezzo confermato'], ['pagato', 'Pagato'], ['residuo', 'Da pagare'],
  ['nome', 'Nome'], ['cognome', 'Cognome'], ['email', 'Email'], ['telefono', 'Telefono'],
  ['nascita', 'Data di nascita'], ['nazionalita', 'Cittadinanza'], ['livello', 'Livello'],
  ['visto', 'Visto'], ['luogo_nascita', 'Luogo di nascita'], ['passaporto', 'N. passaporto'],
  ['scadenza_passaporto', 'Scadenza passaporto'], ['file_passaporto', 'File passaporto'],
  ['pagamento', 'Pagamento preferito'],
  ['f_intestatario', 'Fattura a'], ['f_ente', 'Ente'], ['f_indirizzo', 'Indirizzo'], ['f_cap', 'CAP'],
  ['f_citta', 'Città'], ['f_paese', 'Paese'], ['f_cf', 'Codice fiscale'], ['f_piva', 'P. IVA / CF ente'],
  ['f_sdi', 'SDI / PEC'], ['f_email', 'Email fattura'],
  ['note', 'Note dello studente'], ['lingua', 'Lingua'],
  ['livello_finale', 'Livello raggiunto'], ['diploma', 'Diploma'], ['note_staff', 'Note dello staff']
];
var DATE = ['inizio', 'fine', 'nascita', 'scadenza_passaporto'];

function colonna(chiave) {
  for (var i = 0; i < COLONNE.length; i++) if (COLONNE[i][0] === chiave) return i + 1;
  throw new Error('Colonna sconosciuta: ' + chiave);
}
function props() { return PropertiesService.getScriptProperties(); }
function lettera(n) { var s = ''; while (n > 0) { var m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = (n - m - 1) / 26; } return s; }
function data(s) { if (!s) return ''; var p = String(s).split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
function dataTesto(d) { return d ? d.getDate() + ' ' + MESI[d.getMonth()] + ' ' + d.getFullYear() : ''; }
function euro(n) { return (n === null || n === undefined || n === '') ? '' : Number(n).toLocaleString('it-IT') + ' €'; }

/* ---------- RICEZIONE ---------- */

function doPost(e) {
  try {
    var x = JSON.parse(e.postData.contents);
    // Il campo "sito" è invisibile alle persone: se è pieno, l'ha compilato un programma.
    if (x.sito) return risposta({ok: true, id: ''});
    controlla(x);
    var id, link = '';
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      id = nuovoNumero('iscrizioni', 'ALI');
      if (x.file_passaporto) link = salvaPassaporto(id, x);
      scriviRiga(id, x, link);
    } finally {
      lock.releaseLock();
    }
    mandaEmail(id, x, link);
    return risposta({ok: true, id: id});
  } catch (err) {
    console.error(err);
    return risposta({ok: false, errore: String(err && err.message || err)});
  }
}

function doGet() {
  return risposta({ok: true, servizio: 'Iscrizioni ALIA'});
}

function risposta(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function controlla(x) {
  ['corso', 'nome', 'cognome', 'email', 'pagamento'].forEach(function (k) {
    if (!x[k] || typeof x[k] !== 'string') throw new Error('Manca: ' + k);
  });
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(x.email)) throw new Error('Email non valida');
  if (!x.fattura || !x.fattura.indirizzo || !x.fattura.paese) throw new Error('Mancano i dati per la fattura');
  Object.keys(x).forEach(function (k) {
    if (typeof x[k] === 'string' && x[k].length > 3000) throw new Error('Testo troppo lungo: ' + k);
  });
  // Al massimo MAX_PER_ORA iscrizioni all'ora dallo stesso indirizzo email.
  var cache = CacheService.getScriptCache(), chiave = 'n:' + x.email.toLowerCase();
  var n = +(cache.get(chiave) || 0);
  if (n >= MAX_PER_ORA) throw new Error('Troppe iscrizioni da questo indirizzo. Riprova più tardi.');
  cache.put(chiave, String(n + 1), 3600);
}

function nuovoNumero(nome, prefisso) {
  var anno = new Date().getFullYear(), chiave = 'contatore_' + nome + '_' + anno;
  var n = +(props().getProperty(chiave) || 0) + 1;
  props().setProperty(chiave, String(n));
  return prefisso + '-' + anno + '-' + ('000' + n).slice(-4);
}

function salvaPassaporto(id, x) {
  var f = x.file_passaporto, est = TIPI_FILE[f.tipo];
  if (!est) throw new Error('Il passaporto deve essere PDF, JPG o PNG');
  var byte = Utilities.base64Decode(f.dati);
  if (byte.length > MAX_FILE) throw new Error('Il file del passaporto supera 5 MB');
  var cartella = DriveApp.getFolderById(props().getProperty('cartella_passaporti'));
  var nome = id + ' ' + x.cognome + ' ' + x.nome + est;
  return cartella.createFile(Utilities.newBlob(byte, f.tipo, nome)).getUrl();
}

function scriviRiga(id, x, link) {
  var f = x.fattura || {};
  var v = {
    id: id, ricevuta: new Date(), stato: STATI[0],
    corso_nome: x.corso_nome, tema: x.tema, formula: x.formula,
    settimane: x.settimane, lezioni_totali: x.lezioni_totali,
    inizio: x.inizio, fine: x.fine,
    alloggio: x.alloggio, settimane_alloggio: x.settimane_alloggio, extra: (x.extra || []).join(', '),
    totale: x.totale,
    nome: x.nome, cognome: x.cognome, email: x.email, telefono: x.telefono,
    nascita: x.nascita, nazionalita: x.nazionalita, livello: x.livello,
    visto: x.visto, luogo_nascita: x.luogo_nascita, passaporto: x.passaporto,
    scadenza_passaporto: x.scadenza_passaporto, file_passaporto: link,
    pagamento: x.pagamento,
    f_intestatario: f.intestatario === 'ente' ? 'Ente' : 'Studente', f_ente: f.ente,
    f_indirizzo: f.indirizzo, f_cap: f.cap, f_citta: f.citta, f_paese: f.paese,
    f_cf: f.codice_fiscale, f_piva: f.piva, f_sdi: f.sdi, f_email: f.email,
    note: x.note, lingua: x.lingua
  };
  DATE.forEach(function (k) { v[k] = data(v[k]); });
  var foglio = SpreadsheetApp.getActive().getSheetByName('Iscrizioni');
  var r = foglio.getLastRow() + 1;
  var A = lettera(colonna('id')), P = lettera(colonna('prezzo')), T = lettera(colonna('totale')), G = lettera(colonna('pagato'));
  // Apps Script scrive le formule in inglese, con la virgola, in qualunque lingua sia il foglio.
  // Pagato: la somma dei pagamenti di questa iscrizione nel foglio "Pagamenti".
  v.pagato = '=SUMIF(Pagamenti!A:A,' + A + r + ',Pagamenti!C:C)';
  // Da pagare: prezzo confermato (o, se manca, il totale stimato) meno il pagato.
  v.residuo = '=IF(' + P + r + '="",' + T + r + ',' + P + r + ')-' + G + r;
  var riga = COLONNE.map(function (c) { var k = c[0]; return (v[k] === undefined || v[k] === null) ? '' : v[k]; });
  foglio.getRange(r, 1, 1, riga.length).setValues([riga]);
}

/* ---------- EMAIL ---------- */

function righeRiepilogo(x, en) {
  var r = [];
  r.push((en ? 'Course: ' : 'Corso: ') + x.corso_nome + (x.tema ? ' · ' + x.tema : '') + (x.formula ? ' · ' + x.formula : ''));
  if (x.inizio) r.push((en ? 'Start: ' : 'Inizio: ') + x.inizio + (x.fine ? (en ? ' · End: ' : ' · Fine: ') + x.fine : ''));
  (x.voci || []).forEach(function (v) {
    r.push('- ' + v[0] + (v[1] ? ' (' + v[1] + ')' : '') + (v[2] === null ? '' : ': ' + euro(v[2])));
  });
  r.push((en ? 'Estimated total: ' : 'Totale stimato: ') + euro(x.totale));
  return r;
}

function mandaEmail(id, x, link) {
  var en = x.lingua === 'en';
  try {
    var allo = en
      ? ['Dear ' + x.nome + ',', '', 'thank you for enrolling. We have received your enrolment ' + id + ':', '']
          .concat(righeRiepilogo(x, true),
            x.principiante === false ? ['', 'You are not a beginner: please take the entry test, so we can place you in the right class:', TEST_INGRESSO] : [],
            ['', 'We will write to you within a few days with the confirmation and the proforma invoice. You do not pay anything now.',
             '', 'Best wishes,', NOME_SCUOLA, EMAIL_STAFF])
      : ['Ciao ' + x.nome + ',', '', 'grazie per l’iscrizione. Abbiamo ricevuto la tua iscrizione ' + id + ':', '']
          .concat(righeRiepilogo(x, false),
            x.principiante === false ? ['', 'Non sei principiante: fai il test d’ingresso, così ti inseriamo nella classe giusta:', TEST_INGRESSO] : [],
            ['', 'Ti scriviamo entro pochi giorni con la conferma e la fattura proforma. Adesso non devi pagare niente.',
             '', 'A presto,', NOME_SCUOLA, EMAIL_STAFF]);
    MailApp.sendEmail({
      to: x.email, replyTo: EMAIL_STAFF, name: NOME_SCUOLA,
      subject: en ? 'We have received your enrolment (' + id + ')' : 'Abbiamo ricevuto la tua iscrizione (' + id + ')',
      body: allo.join('\n')
    });
  } catch (err) { console.error('Email allo studente non inviata', err); }
  try {
    var f = x.fattura || {};
    var staff = ['Nuova iscrizione ' + id, '', 'Foglio: ' + SpreadsheetApp.getActive().getUrl(), '',
      x.nome + ' ' + x.cognome + ' · ' + x.email + (x.telefono ? ' · ' + x.telefono : ''),
      'Livello: ' + (x.livello || '') + ' · Visto: ' + (x.visto || '') + ' · Pagamento: ' + x.pagamento];
    if (link) staff.push('Passaporto: ' + link);
    staff.push('Fattura a: ' + (f.intestatario === 'ente' ? f.ente : x.nome + ' ' + x.cognome) + ', ' +
      [f.indirizzo, f.cap, f.citta, f.paese].filter(String).join(', '));
    staff.push('');
    staff = staff.concat(righeRiepilogo(x, false));
    if (x.note) staff.push('', 'Note: ' + x.note);
    MailApp.sendEmail({
      to: EMAIL_STAFF, replyTo: x.email, name: 'Iscrizioni dal sito',
      subject: 'Nuova iscrizione ' + id + ': ' + x.corso_nome + ' – ' + x.nome + ' ' + x.cognome,
      body: staff.join('\n')
    });
  } catch (err) { console.error('Email allo staff non inviata', err); }
}

/* ---------- MENU E DIPLOMI ---------- */

function onOpen() {
  SpreadsheetApp.getUi().createMenu('ALIA')
    .addItem('Crea il diploma della riga selezionata', 'creaDiploma')
    .addSeparator()
    .addItem('Prepara il foglio (solo la prima volta)', 'configura')
    .addToUi();
}

function creaDiploma() {
  var ui = SpreadsheetApp.getUi(), foglio = SpreadsheetApp.getActiveSheet();
  if (foglio.getName() !== 'Iscrizioni') { ui.alert('Apri il foglio "Iscrizioni" e seleziona la riga dello studente.'); return; }
  var r = foglio.getActiveRange().getRow();
  if (r < 2) { ui.alert('Seleziona la riga dello studente.'); return; }
  var valori = foglio.getRange(r, 1, 1, COLONNE.length).getValues()[0], v = {};
  COLONNE.forEach(function (c, i) { v[c[0]] = valori[i]; });
  if (!v.livello_finale) { ui.alert('Scrivi prima il livello raggiunto nella colonna "Livello raggiunto".'); return; }
  var p = props(), numero = nuovoNumero('diplomi', 'D');
  var cartella = DriveApp.getFolderById(p.getProperty('cartella_diplomi'));
  var copia = DriveApp.getFileById(p.getProperty('modello_diploma')).makeCopy('Diploma ' + v.id, cartella);
  var doc = DocumentApp.openById(copia.getId()), corpo = doc.getBody();
  var sost = {
    nome: v.nome + ' ' + v.cognome, corso: v.corso_nome + (v.tema ? ' – ' + v.tema : ''),
    dal: v.inizio instanceof Date ? dataTesto(v.inizio) : String(v.inizio || ''),
    al: v.fine instanceof Date ? dataTesto(v.fine) : String(v.fine || ''),
    lezioni: String(v.lezioni_totali || ''), livello: String(v.livello_finale),
    numero: numero, data: dataTesto(new Date())
  };
  Object.keys(sost).forEach(function (k) { corpo.replaceText('\\{\\{' + k + '\\}\\}', sost[k]); });
  doc.saveAndClose();
  var pdf = cartella.createFile(copia.getAs('application/pdf')).setName('Diploma ' + v.id + ' ' + v.cognome + ' ' + v.nome + '.pdf');
  copia.setTrashed(true);
  foglio.getRange(r, colonna('diploma')).setValue(pdf.getUrl());
  ui.alert('Diploma ' + numero + ' creato. Il link è nella colonna "Diploma".');
}

/* ---------- PRIMA CONFIGURAZIONE ---------- */

/* Crea i fogli, le cartelle private su Drive e il modello del diploma.
   Si può rilanciare: non rifà quello che esiste già. */
function configura() {
  var ss = SpreadsheetApp.getActive(), p = props();
  ss.setSpreadsheetTimeZone('Europe/Rome');

  var isc = ss.getSheetByName('Iscrizioni') || ss.insertSheet('Iscrizioni', 0);
  isc.getRange(1, 1, 1, COLONNE.length).setValues([COLONNE.map(function (c) { return c[1]; })])
    .setFontWeight('bold').setBackground('#2b3a7a').setFontColor('#ffffff');
  isc.setFrozenRows(1);
  isc.setFrozenColumns(3);
  var righe = isc.getMaxRows() - 1;
  isc.getRange(2, colonna('stato'), righe, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(STATI, true).build());
  ['totale', 'prezzo', 'pagato', 'residuo'].forEach(function (k) {
    isc.getRange(2, colonna(k), righe, 1).setNumberFormat('#,##0.00 €');
  });
  DATE.forEach(function (k) { isc.getRange(2, colonna(k), righe, 1).setNumberFormat('dd/mm/yyyy'); });
  isc.getRange(2, colonna('ricevuta'), righe, 1).setNumberFormat('dd/mm/yyyy hh:mm');

  var pag = ss.getSheetByName('Pagamenti') || ss.insertSheet('Pagamenti', 1);
  pag.getRange(1, 1, 1, 5).setValues([['N. iscrizione', 'Data', 'Importo', 'Metodo', 'Note']])
    .setFontWeight('bold').setBackground('#2b3a7a').setFontColor('#ffffff');
  pag.setFrozenRows(1);
  pag.getRange(2, 2, pag.getMaxRows() - 1, 1).setNumberFormat('dd/mm/yyyy');
  pag.getRange(2, 3, pag.getMaxRows() - 1, 1).setNumberFormat('#,##0.00 €');

  if (!p.getProperty('cartella_passaporti')) p.setProperty('cartella_passaporti', DriveApp.createFolder('ALIA – Passaporti (privata)').getId());
  if (!p.getProperty('cartella_diplomi')) p.setProperty('cartella_diplomi', DriveApp.createFolder('ALIA – Diplomi').getId());
  if (!p.getProperty('modello_diploma')) {
    var doc = DocumentApp.create('ALIA – Modello del diploma');
    var b = doc.getBody();
    b.appendParagraph(NOME_SCUOLA).setHeading(DocumentApp.ParagraphHeading.TITLE).setAlignment(DocumentApp.HorizontalAlignment.CENTER);
    b.appendParagraph('Diploma').setHeading(DocumentApp.ParagraphHeading.HEADING1).setAlignment(DocumentApp.HorizontalAlignment.CENTER);
    b.appendParagraph('Si attesta che').setAlignment(DocumentApp.HorizontalAlignment.CENTER);
    b.appendParagraph('{{nome}}').setHeading(DocumentApp.ParagraphHeading.HEADING2).setAlignment(DocumentApp.HorizontalAlignment.CENTER);
    b.appendParagraph('ha frequentato il corso {{corso}} dal {{dal}} al {{al}}, per un totale di {{lezioni}} lezioni, raggiungendo il livello {{livello}}.').setAlignment(DocumentApp.HorizontalAlignment.CENTER);
    b.appendParagraph('Assisi, {{data}}          N. {{numero}}').setAlignment(DocumentApp.HorizontalAlignment.CENTER);
    doc.saveAndClose();
    p.setProperty('modello_diploma', doc.getId());
  }
  SpreadsheetApp.getUi().alert('Foglio pronto. Le cartelle "ALIA – Passaporti (privata)", "ALIA – Diplomi" e il documento "ALIA – Modello del diploma" sono nel tuo Drive.');
}
