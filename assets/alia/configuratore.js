/* Configuratore del corso e modulo d'iscrizione.
   Source: .github/templates/configuratore.js. build_configuratore.py copies it
   to assets/alia/ and writes the data into <script id="cfg-dati">.
   ?corso=<id> shows only that course; &tema=N and &formula=N preselect. */
(function(){
var D=JSON.parse(document.getElementById('cfg-dati').textContent);
var IT=D.lingua==='it',LOC=IT?'it-IT':'en-GB';
var T=IT?{
  titolo:'Calcola date e costi / Iscriviti',
  sottotitolo:'Scegli date, durata e alloggio: vedi subito il costo totale e poi invia l’iscrizione.',
  titolo_info:'Calcola date e costi',sottotitolo_info:'Scegli corso, date, durata e alloggio: vedi subito il costo totale. Per domande, scrivici.',
  corso:'Corso',tutti:'Vedi tutti i corsi',
  gruppi:{18:'Standard',22:'Intensivi',26:'Superintensivi',lezioni:'Lezioni private e online',pacchetto:'Pacchetti'},
  a_sett_gruppo:'{n} lezioni a settimana',
  solo_gruppo:'{g} lezioni in piccolo gruppo al mattino',
  gruppo_ind:'{g} lezioni in piccolo gruppo al mattino + {i} lezioni individuali',tema:'Tema',formula:'Formula',
  n_lezioni:'Numero di lezioni',lezione:'lezione',lezioni:'lezioni',a_lezione:'a lezione',da:'da',
  a_studente:'{p} a studente',prezzo_gruppo:'Il prezzo è per tutto il gruppo.',
  inizio:'Data di inizio',inizio_prev:'Prossimi inizi',scegli:'— Scegli —',altra_data:'Un altro lunedì…',
  lunedi:'Lunedì di inizio',solo_lunedi:'Scegli un lunedì: i corsi iniziano il lunedì.',
  data_pref:'Data di inizio preferita',
  orari:'Gli orari delle lezioni si concordano dopo la conferma dell’iscrizione.',
  disponibili_dal:'Lezioni dal {a} al {b}.',
  durata:'Durata',settimana:'settimana',settimane:'settimane',
  tariffa_1:'tariffa per 1 settimana',tariffa_da:'tariffa da {a} settimane in su',tariffa_ab:'tariffa per {a}–{b} settimane',
  a_sett:'a settimana',mostra_tariffe:'Mostra le tariffe',nascondi_tariffe:'Nascondi le tariffe',
  col_durata:'Durata',col_tariffa:'A settimana',col_totale:'Totale',
  alloggio:'Alloggio',sett_alloggio:'Settimane di alloggio',tipo_camera:'Tipo di camera',stima:'stima',
  stima_nota:'Stima per {n}. Prezzi di riferimento per 2 e 4 settimane, calcolati in proporzione per le altre durate.',
  indip_nota:'Appartamento per una persona. Per un appartamento adatto a due persone scrivici.',
  alloggio_giorno_prima:'L’alloggio è disponibile dal giorno prima dell’inizio del corso.',
  extra:'Servizi extra: trascinali nella tua selezione (o toccali per aggiungerli)',
  disponibili:'Disponibili',scelti:'Scelti',trascina:'Trascina qui i servizi',togli:'Togli',
  chiusure:'Giorni di chiusura della scuola nel periodo',giorno_chiuso:'giorno senza lezioni',giorni_chiusi:'giorni senza lezioni',
  incluse:'Incluso ogni settimana del corso',speciali:'Attività speciali durante il soggiorno',
  nessuna_attivita:'In queste date non ci sono attività speciali.',
  riepilogo:'Riepilogo dei costi',fine:'Fine',scegli_data:'Scegli una data di inizio',
  nessun_alloggio:'Nessun alloggio',totale:'Totale stimato',
  nota_prezzi:'I prezzi sono indicativi. Vale il costo confermato all’iscrizione.',
  continua:'Continua con l’iscrizione',contatta:'Contattaci per informazioni',
  oggetto_info:'Richiesta di informazioni',info_intro:'Vorrei informazioni su questa configurazione:',info_domanda:'La mia domanda:',
  dati:'I tuoi dati',nome:'Nome',cognome:'Cognome',email:'Email',telefono:'Telefono o WhatsApp',
  nascita:'Data di nascita',livello:'Il tuo italiano',
  principiante:'Sono principiante',studiato:'Ho già studiato italiano',
  visto:'Ti serve il visto di studio?',si:'Sì',no:'No',
  pagamento:'Come preferisci pagare?',
  pagamento_nota:'Non paghi adesso. Dopo la conferma ti mandiamo la fattura proforma; il pagamento va fatto prima dell’inizio del corso.',
  note:'Note',facoltativo:'facoltativo',
  fattura:'Dati per la fattura',fattura_nota:'Ci servono per la fattura proforma.',
  intestata:'A chi intestiamo la fattura?',a_me:'A me',a_ente:'A un ente o istituzione (diocesi, congregazione, università, azienda…)',
  ente:'Nome dell’ente',indirizzo:'Indirizzo (via e numero)',cap:'CAP',citta:'Città',paese:'Paese',
  cf:'Codice fiscale',cf_nota:'solo se risiedi in Italia',
  piva:'Partita IVA o codice fiscale dell’ente',sdi:'Codice destinatario (SDI) o PEC',sdi_nota:'solo per enti italiani',
  email_fattura:'Email per la fattura',
  accetto:'Ho letto e accetto i <a href="{t}" target="_blank">termini e condizioni</a> e l’<a href="{p}" target="_blank">informativa sulla privacy</a>.',
  invia:'Invia l’iscrizione',manca:'Compila i campi segnati.',email_errata:'Controlla l’indirizzo email.',
  manca_data:'Scegli la data di inizio.',
  grazie_t:'Ci siamo quasi',
  grazie:'Si apre il tuo programma di posta con l’iscrizione già scritta: invia l’email. Ti rispondiamo entro pochi giorni con la conferma e la fattura proforma.',
  non_si_apre:'Se il programma di posta non si apre, copia questo testo e mandalo a {e}.',
  copia:'Copia il testo',copiato:'Copiato',modifica:'Torna al configuratore',
  oggetto:'Iscrizione',
  pacchetto_passato:'Le date della prossima edizione non sono ancora disponibili. Scrivici a {e}.',
  dal_al:'Dal {a} al {b}'
}:{
  titolo:'Dates, costs and enrolment',
  sottotitolo:'Choose dates, length and accommodation: see the total cost at once, then send your enrolment.',
  titolo_info:'Dates and costs',sottotitolo_info:'Choose course, dates, length and accommodation: see the total cost at once. For questions, write to us.',
  corso:'Course',tutti:'See all courses',
  gruppi:{18:'Standard',22:'Intensive',26:'Super intensive',lezioni:'Private and online lessons',pacchetto:'Packages'},
  a_sett_gruppo:'{n} lessons a week',
  solo_gruppo:'{g} small-group lessons in the morning',
  gruppo_ind:'{g} small-group lessons in the morning + {i} individual lessons',tema:'Theme',formula:'Format',
  n_lezioni:'Number of lessons',lezione:'lesson',lezioni:'lessons',a_lezione:'per lesson',da:'from',
  a_studente:'{p} per student',prezzo_gruppo:'The price is for the whole group.',
  inizio:'Start date',inizio_prev:'Next start dates',scegli:'— Select —',altra_data:'Another Monday…',
  lunedi:'Start Monday',solo_lunedi:'Please select a Monday: courses start on Monday.',
  data_pref:'Preferred start date',
  orari:'We agree the lesson times after confirming your enrolment.',
  disponibili_dal:'Lessons from {a} to {b}.',
  durata:'Duration',settimana:'week',settimane:'weeks',
  tariffa_1:'1 week rate',tariffa_da:'{a}+ weeks rate',tariffa_ab:'{a}–{b} weeks rate',
  a_sett:'per week',mostra_tariffe:'Show pricing tiers',nascondi_tariffe:'Hide pricing tiers',
  col_durata:'Duration',col_tariffa:'Per week',col_totale:'Total',
  alloggio:'Accommodation',sett_alloggio:'Weeks of accommodation',tipo_camera:'Room type',stima:'est.',
  stima_nota:'Estimate for {n}. Reference prices for 2 and 4 weeks, worked out in proportion for other lengths.',
  indip_nota:'Flat for one person. For a flat for two people, write to us.',
  alloggio_giorno_prima:'Accommodation is available from the day before the course starts.',
  extra:'Extra services: drag them into your selection (or tap to add)',
  disponibili:'Available',scelti:'Selected',trascina:'Drag services here',togli:'Remove',
  chiusure:'School closure days in your stay',giorno_chiuso:'day without lessons',giorni_chiusi:'days without lessons',
  incluse:'Included every week of your course',speciali:'Special activities during your stay',
  nessuna_attivita:'No special activities are scheduled in these dates.',
  riepilogo:'Cost summary',fine:'End',scegli_data:'Select a start date',
  nessun_alloggio:'No accommodation',totale:'Total estimate',
  nota_prezzi:'Prices are indicative. The cost confirmed on enrolment applies.',
  continua:'Continue to enrolment',contatta:'Contact us for information',
  oggetto_info:'Information request',info_intro:'I would like information about this configuration:',info_domanda:'My question:',
  dati:'Your details',nome:'First name',cognome:'Last name',email:'Email',telefono:'Phone or WhatsApp',
  nascita:'Date of birth',livello:'Your Italian',
  principiante:'I am a beginner',studiato:'I have studied Italian before',
  visto:'Do you need a study visa?',si:'Yes',no:'No',
  pagamento:'How would you like to pay?',
  pagamento_nota:'You do not pay now. After confirming we send you the proforma invoice; payment is due before the course starts.',
  note:'Notes',facoltativo:'optional',
  fattura:'Invoice details',fattura_nota:'We need them for the proforma invoice.',
  intestata:'Who should the invoice be made out to?',a_me:'To me',a_ente:'To an organisation or institution (diocese, congregation, university, company…)',
  ente:'Name of the organisation',indirizzo:'Address (street and number)',cap:'Postcode',citta:'City',paese:'Country',
  cf:'Italian tax code (codice fiscale)',cf_nota:'only if you live in Italy',
  piva:'VAT number or tax code of the organisation',sdi:'SDI code or PEC',sdi_nota:'only for Italian organisations',
  email_fattura:'Email for the invoice',
  accetto:'I have read and accept the <a href="{t}" target="_blank">terms and conditions</a> and the <a href="{p}" target="_blank">privacy policy</a>.',
  invia:'Send enrolment',manca:'Please fill in the marked fields.',email_errata:'Please check the email address.',
  manca_data:'Please choose the start date.',
  grazie_t:'Almost done',
  grazie:'Your email program opens with the enrolment already written: send the email. We reply within a few days with the confirmation and the proforma invoice.',
  non_si_apre:'If your email program does not open, copy this text and send it to {e}.',
  copia:'Copy the text',copiato:'Copied',modifica:'Back to the configurator',
  oggetto:'Enrolment',
  pacchetto_passato:'The dates of the next edition are not available yet. Write to us at {e}.',
  dal_al:'From {a} to {b}'
};

/* ---------- UTILITÀ ---------- */
function $(id){return document.getElementById(id);}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function fmt(s,v){return s.replace(/\{(\w)\}/g,function(m,k){return v[k];});}
function eur(n){return n.toLocaleString(LOC,{maximumFractionDigits:2,useGrouping:'always'})+' €';}
function iso(d){var m=d.getMonth()+1,g=d.getDate();return d.getFullYear()+'-'+(m<10?'0':'')+m+'-'+(g<10?'0':'')+g;}
function fromIso(s){var p=s.split('-');return new Date(+p[0],+p[1]-1,+p[2]);}
function giorno(d){return d.toLocaleDateString(LOC,{weekday:'long',day:'numeric',month:'long',year:'numeric'});}
function breve(d){return d.toLocaleDateString(LOC,{day:'numeric',month:'long'});}
function settimane(n){return n+' '+(n===1?T.settimana:T.settimane);}
function lezioni(n){return n+' '+(n===1?T.lezione:T.lezioni);}
var OGGI=new Date();OGGI.setHours(0,0,0,0);

/* ---------- PREZZI ---------- */
function tariffa(c,w){for(var i=0;i<c.tariffe.length;i++){var t=c.tariffe[i];if(w>=t.from&&w<=t.to)return t;}return c.tariffe[c.tariffe.length-1];}
function nomeTariffa(t){return t.from===t.to?T.tariffa_1:(t.to>=48?fmt(T.tariffa_da,{a:t.from}):fmt(T.tariffa_ab,{a:t.from,b:t.to}));}
/* Lezioni a pacchetti: prima i pacchetti più grandi, il resto a lezione singola. */
function prezzoLezioni(f,n){
  var tagli=Object.keys(f.prezzi).map(Number).sort(function(a,b){return b-a;}),tot=0;
  tagli.forEach(function(t){var k=Math.floor(n/t);tot+=k*f.prezzi[t];n-=k*t;});
  return tot;
}
/* Il prezzo più basso a lezione della prima formula (lezioni individuali). */
function minimoLezione(c){
  var f=c.formule[0];
  return Math.min.apply(null,Object.keys(f.prezzi).map(function(n){return Math.round(f.prezzi[n]/n*100)/100;}));
}
/* Alloggio: prezzi di riferimento per 2 e 4 settimane, in proporzione per le altre. */
function prezzoAlloggio(map,w){
  var k=Object.keys(map).map(Number).sort(function(a,b){return a-b;});
  if(w<=k[0])return Math.round(map[k[0]]*w/k[0]);
  if(w>=k[k.length-1])return Math.round(map[k[k.length-1]]*w/k[k.length-1]);
  for(var i=0;i<k.length-1;i++)if(w>=k[i]&&w<=k[i+1])return Math.round(map[k[i]]+(map[k[i+1]]-map[k[i]])*(w-k[i])/(k[i+1]-k[i]));
  return 0;
}

/* ---------- STATO ---------- */
var Q=new URLSearchParams(location.search);
function trova(id){return D.corsi.filter(function(c){return c.id===id;})[0];}
function passato(c){return c.tipo==='pacchetto'&&fromIso(c.al)<OGGI;}
var BLOCCATO=!!trova(Q.get('corso'));
/* Ci si iscrive solo arrivando da una pagina corso; dal menu si chiedono informazioni. */
var DA_CORSO=BLOCCATO;
var S={
  corso:BLOCCATO?Q.get('corso'):'standard',
  tema:+Q.get('tema')||0, formula:+Q.get('formula')||0,
  inizio:null, settimane:2, lezioni:10,
  alloggio:'nessuno', camera:'singola', settAlloggio:2, extra:[]
};
function C(){return trova(S.corso);}
function alloggio(){return D.alloggi.filter(function(a){return a.id===S.alloggio;})[0];}
function camera(){return alloggio().camere.filter(function(r){return r.id===S.camera;})[0];}
function inSede(c){return c.tipo!=='lezioni'||c.in_sede;}

/* ---------- STRUTTURA ---------- */
function sezione(id,label,dentro){return '<div class="cfg-section" id="'+id+'"><div class="cfg-section-label">'+label+'</div>'+dentro+'</div>';}
function campo(id,label,input,fac){return '<div class="cfg-field" id="f-'+id+'"><label for="'+id+'">'+label+(fac?' <span class="cfg-opt">('+T.facoltativo+')</span>':'')+'</label>'+input+'</div>';}
var opzioniDate=D.date_inizio.filter(function(d){return fromIso(d)>=OGGI;}).map(function(d){return '<option value="'+d+'">'+esc(giorno(fromIso(d)))+'</option>';}).join('');
var wrap=$('cfg-wrap');
wrap.innerHTML=
  '<h3>'+(DA_CORSO?T.titolo:T.titolo_info)+'</h3><p class="cfg-subtitle">'+(DA_CORSO?T.sottotitolo:T.sottotitolo_info)+'</p>'+
  '<div id="cfg-config">'+
  sezione('s-corso',T.corso,'<div id="cfg-courses"></div>'+
    (BLOCCATO?'<a href="#" id="cfg-tutti" class="price-table-toggle"><i class="ti ti-list" style="font-size:14px"></i> '+T.tutti+'</a>':'')+
    '<div id="cfg-tema-box" class="date-field cfg-tema"><label for="cfg-tema">'+T.tema+'</label><select id="cfg-tema"></select></div>'+
    '<div><div id="ptoggle" class="price-table-toggle"></div><div id="price-table" class="price-table"></div></div>')+
  sezione('s-formula',T.formula,'<div id="cfg-formule" class="cfg-sub-opts"></div><p id="cfg-formula-nota" class="accom-note"></p>')+
  sezione('s-lezioni',T.n_lezioni,'<div class="week-row"><input id="cfg-nlez" type="range" min="1" max="60" step="1" value="10"><div class="week-display"><span id="cfg-nlez-num" class="week-num">10</span><span id="cfg-nlez-lbl" class="week-lbl"></span></div></div><div id="cfg-nlez-hint" class="tier-hint"></div>')+
  sezione('s-data',T.inizio,
    '<div class="date-row" id="cfg-data-sett">'+
      '<div class="date-field"><label for="cfg-startsel">'+T.inizio_prev+'</label><select id="cfg-startsel"><option value="">'+T.scegli+'</option>'+opzioniDate+'<option value="altra">'+T.altra_data+'</option></select></div>'+
      '<div class="date-field" id="cfg-cf" style="display:none"><label for="cfg-cd">'+T.lunedi+'</label><input type="date" id="cfg-cd" min="'+iso(OGGI)+'"></div>'+
    '</div>'+
    '<div class="date-row" id="cfg-data-lez"><div class="date-field"><label for="cfg-dpref">'+T.data_pref+'</label><input type="date" id="cfg-dpref"></div></div>'+
    '<p id="cfg-data-pac" class="cfg-fixed"></p>'+
    '<div id="cfg-range" class="tier-hint"></div>')+
  sezione('s-durata',T.durata,'<div class="week-row"><input id="cfg-dur" type="range" min="1" max="48" step="1" value="2"><div class="week-display"><span id="cfg-dur-num" class="week-num">2</span><span id="cfg-dur-lbl" class="week-lbl"></span></div></div><div id="cfg-tier-hint" class="tier-hint"></div>')+
  '<div id="cfg-stay" class="cfg-stay cfg-section"></div>'+
  sezione('s-alloggio',T.alloggio,'<div id="cfg-housing" class="cfg-cards"></div>'+
    '<div id="cfg-sett-alloggio" class="cfg-sub-opts"><div class="cfg-sub-opts-label">'+T.sett_alloggio+'</div><div class="week-row"><input id="cfg-salloggio" type="range" min="1" max="24" step="1" value="2"><div class="week-display"><span id="cfg-salloggio-num" class="week-num">2</span><span id="cfg-salloggio-lbl" class="week-lbl"></span></div></div></div>'+
    '<div id="cfg-accom-sub"></div><p id="cfg-accom-note" class="accom-note"></p>')+
  sezione('s-extra',T.extra,'<div class="cfg-drag-zone">'+
    '<div class="cfg-drag-col"><div class="cfg-drag-col-label"><i class="ti ti-packages" style="font-size:14px"></i> '+T.disponibili+'</div><div id="cfg-avail-list"></div></div>'+
    '<div class="cfg-drag-col"><div class="cfg-drag-col-label"><i class="ti ti-basket" style="font-size:14px"></i> '+T.scelti+'</div><div id="cfg-drop-zone" class="cfg-drop-area"><div id="cfg-sel-list"></div></div></div></div>')+
  '<div class="cfg-summary"><div class="cfg-summary-title"><i class="ti ti-receipt" style="font-size:18px;color:#888"></i> '+T.riepilogo+'</div>'+
    '<div id="cfg-sum-lines"></div><hr class="cfg-divider">'+
    '<div class="cfg-total-row"><div class="cfg-total-label">'+T.totale+'</div><div id="cfg-total" class="cfg-total-val">0 €</div></div>'+
    '<p class="cfg-note">'+T.nota_prezzi+'</p>'+
    '<p id="cfg-passato" class="cfg-err"></p>'+
    '<div class="cfg-ctas">'+(DA_CORSO?'<button type="button" class="cfg-cta" id="cfg-cta"><i class="ti ti-arrow-down"></i> '+T.continua+'</button>':'')+
    '<button type="button" class="cfg-cta cfg-cta-sec" id="cfg-info"><i class="ti ti-mail"></i> '+T.contatta+'</button></div></div>'+
  '</div>'+
  '<form id="cfg-form" class="cfg-form" novalidate hidden>'+
    '<h4>'+T.dati+'</h4>'+
    '<div class="cfg-grid">'+
      campo('cfg-nome',T.nome+' *','<input id="cfg-nome" autocomplete="given-name" required>')+
      campo('cfg-cognome',T.cognome+' *','<input id="cfg-cognome" autocomplete="family-name" required>')+
      campo('cfg-email',T.email+' *','<input id="cfg-email" type="email" autocomplete="email" required>')+
      campo('cfg-tel',T.telefono,'<input id="cfg-tel" type="tel" autocomplete="tel">',true)+
      campo('cfg-nascita',T.nascita,'<input id="cfg-nascita" type="date">',true)+
    '</div>'+
    '<div class="cfg-field" id="f-cfg-livello"><span class="cfg-flabel">'+T.livello+' *</span>'+
      '<label class="cfg-radio"><input type="radio" name="cfg-livello" value="'+esc(T.principiante)+'"> '+T.principiante+'</label>'+
      '<label class="cfg-radio"><input type="radio" name="cfg-livello" value="'+esc(T.studiato)+'"> '+T.studiato+'</label></div>'+
    '<div class="cfg-field" id="f-cfg-visto"><span class="cfg-flabel">'+T.visto+' *</span>'+
      '<label class="cfg-radio"><input type="radio" name="cfg-visto" value="'+T.si+'"> '+T.si+'</label>'+
      '<label class="cfg-radio"><input type="radio" name="cfg-visto" value="'+T.no+'"> '+T.no+'</label></div>'+
    '<div class="cfg-field" id="f-cfg-pag"><span class="cfg-flabel">'+T.pagamento+' *</span>'+
      D.pagamenti.map(function(p){return '<label class="cfg-radio"><input type="radio" name="cfg-pag" value="'+esc(p.nome)+'"> '+esc(p.nome)+'</label>';}).join('')+
      '<p class="accom-note">'+T.pagamento_nota+'</p></div>'+
    '<h4 class="cfg-h4-sez">'+T.fattura+'</h4><p class="accom-note cfg-sez-nota">'+T.fattura_nota+'</p>'+
    '<div class="cfg-field" id="f-cfg-int"><span class="cfg-flabel">'+T.intestata+' *</span>'+
      '<label class="cfg-radio"><input type="radio" name="cfg-int" value="persona" checked> '+T.a_me+'</label>'+
      '<label class="cfg-radio"><input type="radio" name="cfg-int" value="ente"> '+T.a_ente+'</label></div>'+
    '<div class="cfg-grid cfg-grid-fatt">'+
      campo('cfg-ente',T.ente+' *','<input id="cfg-ente" autocomplete="organization">')+
      campo('cfg-ind',T.indirizzo+' *','<input id="cfg-ind" autocomplete="street-address">')+
      campo('cfg-cap',T.cap+' *','<input id="cfg-cap" autocomplete="postal-code">')+
      campo('cfg-citta',T.citta+' *','<input id="cfg-citta" autocomplete="address-level2">')+
      campo('cfg-paese',T.paese+' *','<input id="cfg-paese" autocomplete="country-name">')+
      campo('cfg-codfisc',T.cf+' <span class="cfg-opt">('+T.cf_nota+')</span>','<input id="cfg-codfisc">')+
      campo('cfg-piva',T.piva+' *','<input id="cfg-piva">')+
      campo('cfg-sdi',T.sdi+' <span class="cfg-opt">('+T.sdi_nota+')</span>','<input id="cfg-sdi">')+
      campo('cfg-emailf',T.email_fattura,'<input id="cfg-emailf" type="email">',true)+
    '</div>'+
    campo('cfg-note',T.note,'<textarea id="cfg-note" rows="3"></textarea>',true)+
    '<div class="cfg-field" id="f-cfg-ok"><label class="cfg-radio"><input type="checkbox" id="cfg-ok"> '+fmt(T.accetto,{t:D.link.termini,p:D.link.privacy})+' *</label></div>'+
    '<p id="cfg-form-err" class="cfg-err" role="alert"></p>'+
    '<button type="submit" class="cfg-cta"><i class="ti ti-send"></i> '+T.invia+'</button>'+
  '</form>'+
  '<div id="cfg-done" class="cfg-summary" hidden><div class="cfg-summary-title"><i class="ti ti-mail-forward" style="font-size:18px;color:#888"></i> '+T.grazie_t+'</div>'+
    '<p>'+T.grazie+'</p><p class="accom-note">'+fmt(T.non_si_apre,{e:'<a href="mailto:'+D.email+'">'+D.email+'</a>'})+'</p>'+
    '<textarea id="cfg-testo" class="cfg-testo" rows="12" readonly></textarea>'+
    '<p class="cfg-done-btns"><button type="button" class="cfg-link" id="cfg-copia">'+T.copia+'</button> <button type="button" class="cfg-link" id="cfg-modifica">'+T.modifica+'</button></p></div>';

function mostra(id,si){$(id).style.display=si?'':'none';}

/* ---------- CORSI ---------- */
function prezzoScheda(c){
  if(c.tipo==='settimane')return eur(tariffa(c,S.settimane).ppw)+' '+T.a_sett;
  if(c.tipo==='lezioni')return T.da+' '+eur(minimoLezione(c))+' '+T.a_lezione;
  return eur(c.prezzo);
}
function descScheda(c){
  if(c.tipo==='settimane')return c.ore+' '+T.lezioni+' '+T.a_sett+(BLOCCATO?'<span class="cfg-card-mix">'+fmt(c.individuali?T.gruppo_ind:T.solo_gruppo,{g:c.gruppo,i:c.individuali})+'</span>':'');
  if(c.tipo==='pacchetto')return esc(fmt(T.dal_al,{a:breve(fromIso(c.dal)),b:giorno(fromIso(c.al))}));
  return c.formule.map(function(f){return esc(f.nome);}).join(' · ');
}
/* I corsi divisi per gruppo: Standard (18 lezioni), Intensivi (22), Superintensivi (26), poi lezioni e pacchetti.
   Il titolo del gruppo dice quante lezioni sono di gruppo e quante individuali; con un corso solo lo dice la scheda. */
function gruppo(c){return c.tipo==='settimane'?c.ore:c.tipo;}
function renderCorsi(){
  var box=$('cfg-courses'),griglie={};box.innerHTML='';
  D.corsi.forEach(function(c){
    if(BLOCCATO&&c.id!==S.corso)return;
    if(!BLOCCATO&&passato(c))return;
    var g=gruppo(c);
    if(!griglie[g]){
      if(!BLOCCATO){
        var t=document.createElement('div');t.className='cfg-group-title';
        t.innerHTML=esc(T.gruppi[g]||g)+(c.tipo==='settimane'?' <span>'+fmt(T.a_sett_gruppo,{n:c.ore})+'</span>'+
          '<small>'+fmt(c.individuali?T.gruppo_ind:T.solo_gruppo,{g:c.gruppo,i:c.individuali})+'</small>':'');
        box.appendChild(t);
      }
      griglie[g]=document.createElement('div');griglie[g].className='cfg-cards';box.appendChild(griglie[g]);
    }
    var sel=c.id===S.corso,d=document.createElement('div');
    d.className='cfg-card'+(sel?' selected':'');
    d.setAttribute('role','button');d.tabIndex=0;
    d.onclick=function(){if(S.corso!==c.id){S.corso=c.id;S.tema=0;S.formula=0;S.inizio=null;resetDate();}aggiorna();};
    d.onkeydown=function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();d.onclick();}};
    d.innerHTML=(sel?'<div class="cfg-badge-sel"><i class="ti ti-check"></i></div>':'')+
      '<div class="cfg-card-icon"><i class="ti '+c.icona+'"></i></div>'+
      '<div class="cfg-card-name">'+esc(c.nome)+'</div>'+
      '<div class="cfg-card-desc">'+descScheda(c)+'</div>'+
      '<div class="cfg-card-price">'+prezzoScheda(c)+'</div>'+
      (c.livelli?'<div class="cfg-card-note">'+esc(c.livelli)+'</div>':'');
    griglie[g].appendChild(d);
  });
}
var tabellaAperta=false;
function renderTariffe(){
  var c=C(),righe='';
  c.tariffe.forEach(function(t){
    var cur=S.settimane>=t.from&&S.settimane<=t.to,top=t.to>=48;
    var dur=t.from===t.to?settimane(t.from):(top?t.from+'+ '+T.settimane:t.from+'–'+t.to+' '+T.settimane);
    righe+='<tr'+(cur?' class="current-tier"':'')+'><td>'+dur+'</td><td>'+eur(t.ppw)+'</td><td>'+eur(t.ppw*t.from)+(t.from===t.to?'':' – '+eur(t.ppw*(top?t.from:t.to))+(top?'+':''))+'</td></tr>';
  });
  $('price-table').innerHTML='<table><thead><tr><th>'+T.col_durata+'</th><th>'+T.col_tariffa+'</th><th>'+T.col_totale+'</th></tr></thead><tbody>'+righe+'</tbody></table>';
  $('price-table').className='price-table'+(tabellaAperta?' open':'');
  $('ptoggle').innerHTML=tabellaAperta?'<i class="ti ti-chevron-up" style="font-size:14px"></i> '+T.nascondi_tariffe:'<i class="ti ti-table-down" style="font-size:14px"></i> '+T.mostra_tariffe;
}
$('ptoggle').addEventListener('click',function(){tabellaAperta=!tabellaAperta;renderTariffe();});
if(BLOCCATO)$('cfg-tutti').addEventListener('click',function(e){
  e.preventDefault();BLOCCATO=false;this.style.display='none';
  history.replaceState(null,'',location.pathname);aggiorna();
});
$('cfg-tema').addEventListener('change',function(){S.tema=+this.value;aggiorna();});

function renderFormule(){
  var c=C(),box=$('cfg-formule');box.innerHTML='';
  if(S.formula>=c.formule.length)S.formula=0;
  c.formule.forEach(function(f,i){
    var r=document.createElement('label'),on=i===S.formula,p=prezzoLezioni(f,S.lezioni);
    r.className='cfg-sub-row'+(on?' active':'');
    r.innerHTML='<input type="radio" name="cfg-formula"'+(on?' checked':'')+'>'+
      '<span class="cfg-sub-row-name">'+esc(f.nome)+' <span style="font-size:12px;color:#999">('+esc(f.nota)+')</span></span>'+
      '<span class="cfg-sub-row-price">'+eur(p)+'</span>';
    r.querySelector('input').addEventListener('change',function(){S.formula=i;aggiorna();});
    box.appendChild(r);
  });
  var f=c.formule[S.formula];
  $('cfg-formula-nota').textContent=f.studenti>1?T.prezzo_gruppo:'';
}

/* ---------- DATE ---------- */
function resetDate(){$('cfg-startsel').value='';$('cfg-cd').value='';$('cfg-cf').style.display='none';$('cfg-dpref').value='';}
$('cfg-startsel').addEventListener('change',function(){
  var v=this.value;$('cfg-cf').style.display=v==='altra'?'flex':'none';
  S.inizio=v&&v!=='altra'?fromIso(v):null;if(v==='altra'&&$('cfg-cd').value)S.inizio=fromIso($('cfg-cd').value);
  aggiorna();
});
$('cfg-cd').addEventListener('change',function(){
  var v=this.value;S.inizio=null;
  if(v){var d=fromIso(v);if(d.getDay()!==1){alert(T.solo_lunedi);this.value='';}else S.inizio=d;}
  aggiorna();
});
$('cfg-dpref').addEventListener('change',function(){S.inizio=this.value?fromIso(this.value):null;aggiorna();});

/* Fine corso = venerdì dell'ultima settimana. Le chiusure non spostano la data. */
function periodo(inizio,fine){
  var chiuse=[];
  D.chiusure.forEach(function(c){
    var a=fromIso(c.dal),b=fromIso(c.al);if(a<inizio)a=inizio;if(b>fine)b=fine;
    var primo=null,ultimo=null,n=0;
    for(var d=new Date(a);d<=b;d.setDate(d.getDate()+1)){var g=d.getDay();if(g>=1&&g<=5){n++;if(!primo)primo=new Date(d);ultimo=new Date(d);}}
    if(n)chiuse.push({nome:c.nome,dal:primo,al:ultimo,n:n});
  });
  var s=iso(inizio),e=iso(fine),att=[];
  D.attivita.forEach(function(a){a.date.forEach(function(d){if(d>=s&&d<=e)att.push({d:d,nome:a.nome});});});
  att.sort(function(x,y){return x.d<y.d?-1:x.d>y.d?1:0;});
  return {chiuse:chiuse,attivita:att};
}
function fineCorso(){
  var c=C();
  if(c.tipo==='pacchetto')return fromIso(c.al);
  if(c.tipo!=='settimane'||!S.inizio)return null;
  var f=new Date(S.inizio);f.setDate(f.getDate()+(S.settimane-1)*7+4);return f;
}
function inizio(){var c=C();return c.tipo==='pacchetto'?fromIso(c.dal):S.inizio;}
function settAlloggio(){
  var c=C();
  if(c.tipo==='settimane')return S.settimane;
  if(c.tipo==='pacchetto')return Math.max(1,Math.round(((fromIso(c.al)-fromIso(c.dal))/864e5+1)/7));
  return S.settAlloggio;
}
function renderSoggiorno(){
  var c=C(),a=inizio(),b=fineCorso(),st=$('cfg-stay');st.innerHTML='';
  $('cfg-range').innerHTML=a&&b?'<i class="ti ti-calendar-event" style="font-size:13px;vertical-align:-2px"></i> '+esc(giorno(a))+' → '+esc(giorno(b)):'';
  if(!a||!b||c.tipo!=='settimane'){st.style.display='none';return;}
  st.style.display='';
  var p=periodo(a,b),h='';
  if(p.chiuse.length){
    h+='<div class="cfg-warn"><div class="cfg-warn-t"><i class="ti ti-alert-triangle" style="font-size:13px"></i> '+T.chiusure+'</div><ul>';
    p.chiuse.forEach(function(x){h+='<li>· '+esc(x.nome)+': '+esc(iso(x.dal)===iso(x.al)?breve(x.dal):breve(x.dal)+' – '+breve(x.al))+' ('+x.n+' '+(x.n===1?T.giorno_chiuso:T.giorni_chiusi)+')</li>';});
    h+='</ul></div>';
  }
  h+='<h4>'+T.incluse+'</h4><div class="cfg-weekly"><ul class="cfg-act-list">';
  D.attivita_settimanali.forEach(function(w){h+='<li>1 × '+esc(w)+'</li>';});
  h+='</ul></div><h4>'+T.speciali+'</h4>';
  if(p.attivita.length){
    h+='<ul class="cfg-act-list">';
    p.attivita.forEach(function(x){h+='<li><span class="ad">'+esc(giorno(fromIso(x.d)))+'</span><span>'+esc(x.nome)+'</span></li>';});
    h+='</ul>';
  } else h+='<p class="cfg-empty-msg">'+T.nessuna_attivita+'</p>';
  st.innerHTML=h;
}

/* ---------- ALLOGGIO ---------- */
function prezzoAlloggioScelto(w){
  var a=alloggio();
  if(a.camere.length)return prezzoAlloggio(camera().prezzi,w);
  return a.prezzi?prezzoAlloggio(a.prezzi,w):0;
}
function renderAlloggi(){
  var w=settAlloggio(),box=$('cfg-housing');box.innerHTML='';
  D.alloggi.forEach(function(a){
    var pl='—';
    if(a.camere.length){var r=a.id===S.alloggio?camera():a.camere[0];pl=eur(prezzoAlloggio(r.prezzi,w))+' '+T.stima;}
    else if(a.prezzi)pl=eur(prezzoAlloggio(a.prezzi,w))+' '+T.stima;
    var sel=a.id===S.alloggio,d=document.createElement('div');
    d.className='cfg-card'+(sel?' selected':'');d.setAttribute('role','button');d.tabIndex=0;
    d.onclick=function(){S.alloggio=a.id;if(a.camere.length&&!a.camere.some(function(r){return r.id===S.camera;}))S.camera=a.camere[0].id;aggiorna();};
    d.onkeydown=function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();d.onclick();}};
    d.innerHTML=(sel?'<div class="cfg-badge-sel"><i class="ti ti-check"></i></div>':'')+
      '<div class="cfg-card-icon"><i class="ti '+a.icona+'"></i></div>'+
      '<div class="cfg-card-name">'+esc(a.nome)+'</div><div class="cfg-card-desc">'+esc(a.nota)+'</div>'+
      '<div class="cfg-card-price">'+pl+'</div>';
    box.appendChild(d);
  });
  var c=C(),a=alloggio(),sub=$('cfg-accom-sub'),nota=$('cfg-accom-note');
  mostra('cfg-sett-alloggio',c.tipo==='lezioni'&&a.id!=='nessuno');
  sub.innerHTML='';nota.textContent='';
  if(a.camere.length){
    var box2=document.createElement('div');box2.className='cfg-sub-opts';
    box2.innerHTML='<div class="cfg-sub-opts-label">'+T.tipo_camera+'</div>';
    a.camere.forEach(function(r){
      var on=r.id===S.camera,row=document.createElement('label');
      row.className='cfg-sub-row'+(on?' active':'');
      row.innerHTML='<input type="radio" name="cfg-camera"'+(on?' checked':'')+'>'+
        '<span class="cfg-sub-row-name">'+esc(r.nome)+(r.nota?' <span style="font-size:12px;color:#999">('+esc(r.nota)+')</span>':'')+'</span>'+
        '<span class="cfg-sub-row-price">'+eur(prezzoAlloggio(r.prezzi,w))+'</span>';
      row.querySelector('input').addEventListener('change',function(){S.camera=r.id;aggiorna();});
      box2.appendChild(row);
    });
    sub.appendChild(box2);
  }
  if(a.id!=='nessuno')nota.textContent=fmt(T.stima_nota,{n:settimane(w)})+(a.id==='indipendente'?' '+T.indip_nota:'')+' '+T.alloggio_giorno_prima;
}

/* ---------- EXTRA ---------- */
var trascinato=null;
function aggiungiExtra(id){if(S.extra.indexOf(id)<0)S.extra.push(id);aggiorna();}
function extra(id){return D.extra.filter(function(e){return e.id===id;})[0];}
function chip(e,togli){
  var ch=document.createElement('div');ch.className='cfg-chip';
  ch.innerHTML='<i class="ti '+e.icona+' chip-icon"></i><span class="chip-name">'+esc(e.nome)+'</span><span class="chip-price">'+eur(e.prezzo)+'</span>'+
    (togli?'<button type="button" class="chip-rm" title="'+T.togli+'" aria-label="'+T.togli+'"><i class="ti ti-x"></i></button>':'');
  return ch;
}
function renderExtra(){
  var disp=$('cfg-avail-list');disp.innerHTML='';
  D.extra.forEach(function(e){
    if(S.extra.indexOf(e.id)>=0)return;
    var ch=chip(e,false);ch.draggable=true;ch.tabIndex=0;ch.setAttribute('role','button');
    ch.addEventListener('dragstart',function(ev){trascinato=e.id;ch.classList.add('dragging');ev.dataTransfer.effectAllowed='move';try{ev.dataTransfer.setData('text/plain',e.id);}catch(x){}});
    ch.addEventListener('dragend',function(){ch.classList.remove('dragging');});
    ch.addEventListener('click',function(){aggiungiExtra(e.id);});
    ch.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();aggiungiExtra(e.id);}});
    disp.appendChild(ch);
  });
  var sel=$('cfg-sel-list');sel.innerHTML='';
  if(!S.extra.length){sel.innerHTML='<div class="cfg-drag-empty"><i class="ti ti-drag-drop" style="font-size:22px;display:block;margin-bottom:4px"></i>'+T.trascina+'</div>';return;}
  S.extra.forEach(function(id){
    var ch=chip(extra(id),true);
    ch.querySelector('.chip-rm').addEventListener('click',function(){S.extra=S.extra.filter(function(x){return x!==id;});aggiorna();});
    sel.appendChild(ch);
  });
}
var dz=$('cfg-drop-zone');
dz.addEventListener('dragover',function(ev){ev.preventDefault();dz.classList.add('over');});
dz.addEventListener('dragleave',function(){dz.classList.remove('over');});
dz.addEventListener('drop',function(ev){
  ev.preventDefault();dz.classList.remove('over');
  var id=trascinato;if(!id){try{id=ev.dataTransfer.getData('text/plain');}catch(x){}}
  trascinato=null;if(id&&extra(id))aggiungiExtra(id);
});

/* ---------- RIEPILOGO ---------- */
/* Le voci del preventivo: [etichetta, dettaglio, importo]. Servono al riepilogo e all'email. */
function voci(){
  var c=C(),v=[],w=settAlloggio();
  if(c.tipo==='settimane'){
    var t=tariffa(c,S.settimane);
    v.push([c.nome+(c.temi.length?' · '+c.temi[S.tema]:''),settimane(S.settimane)+' × '+eur(t.ppw),t.ppw*S.settimane]);
  } else if(c.tipo==='lezioni'){
    var f=c.formule[S.formula],p=prezzoLezioni(f,S.lezioni);
    v.push([c.nome+' · '+f.nome,lezioni(S.lezioni)+(f.studenti>1?', '+fmt(T.a_studente,{p:eur(Math.round(p/f.studenti*100)/100)}):''),p]);
  } else v.push([c.nome,'',c.prezzo]);
  if(inSede(c)){
    var a=alloggio();
    if(a.id==='nessuno')v.push([T.nessun_alloggio,'',null]);
    else v.push([a.nome+(a.camere.length?' · '+camera().nome:''),settimane(w)+', '+T.stima,prezzoAlloggioScelto(w)]);
    S.extra.forEach(function(id){var e=extra(id);v.push([e.nome,'',e.prezzo]);});
  }
  return v;
}
function totale(){return voci().reduce(function(s,x){return s+(x[2]||0);},0);}
function renderRiepilogo(){
  var c=C(),a=inizio(),b=fineCorso(),h='';
  function riga(l,d,val){return '<div class="cfg-sum-row"><span class="slbl">'+esc(l)+(d?' <span class="stier">('+esc(d)+')</span>':'')+'</span><span class="sv">'+val+'</span></div>';}
  if(a){h+=riga(T.inizio,'',esc(giorno(a)));if(b)h+=riga(T.fine,'',esc(giorno(b)));}
  else h+='<div class="cfg-sum-row"><span class="slbl">'+T.inizio+'</span><span class="sv" style="color:#999;font-weight:400">'+T.scegli_data+'</span></div>';
  if(c.tipo==='settimane')h+=riga(T.durata,'',settimane(S.settimane));
  voci().forEach(function(x){h+=riga(x[0],x[1],x[2]===null?'—':eur(x[2]));});
  $('cfg-sum-lines').innerHTML=h;
  $('cfg-total').textContent=eur(totale());
  var chiuso=passato(c);
  $('cfg-passato').innerHTML=chiuso?fmt(T.pacchetto_passato,{e:'<a href="mailto:'+D.email+'">'+D.email+'</a>'}):'';
  if(DA_CORSO){$('cfg-cta').disabled=chiuso;if(chiuso)$('cfg-form').hidden=true;}
}

/* ---------- AGGIORNAMENTO ---------- */
function aggiorna(){
  var c=C(),sett=c.tipo==='settimane',lez=c.tipo==='lezioni',pac=c.tipo==='pacchetto';
  renderCorsi();
  mostra('cfg-tema-box',sett&&c.temi.length>0);
  if(sett&&c.temi.length){
    if(S.tema>=c.temi.length)S.tema=0;
    $('cfg-tema').innerHTML=c.temi.map(function(t,i){return '<option value="'+i+'"'+(i===S.tema?' selected':'')+'>'+esc(t)+'</option>';}).join('');
  }
  mostra('ptoggle',sett);mostra('price-table',sett);if(sett)renderTariffe();
  mostra('s-formula',lez);mostra('s-lezioni',lez);
  if(lez){
    $('cfg-nlez-num').textContent=S.lezioni;$('cfg-nlez-lbl').textContent=S.lezioni===1?T.lezione:T.lezioni;
    renderFormule();
    var f=c.formule[S.formula];
    $('cfg-nlez-hint').innerHTML='<i class="ti ti-tag" style="font-size:13px;vertical-align:-2px"></i> '+esc(f.nome)+': '+eur(prezzoLezioni(f,S.lezioni))+
      (f.studenti>1?' · '+fmt(T.a_studente,{p:eur(Math.round(prezzoLezioni(f,S.lezioni)/f.studenti*100)/100)}):'');
    var dp=$('cfg-dpref'),min=c.dal&&fromIso(c.dal)>OGGI?c.dal:iso(OGGI);
    dp.min=min;if(c.al)dp.max=c.al;else dp.removeAttribute('max');
  }
  mostra('cfg-data-sett',sett);mostra('cfg-data-lez',lez);mostra('cfg-data-pac',pac);
  $('cfg-data-pac').textContent=pac?fmt(T.dal_al,{a:giorno(fromIso(c.dal)),b:giorno(fromIso(c.al))}):'';
  if(lez)$('cfg-range').textContent='';
  mostra('s-durata',sett);
  if(sett){
    $('cfg-dur-num').textContent=S.settimane;$('cfg-dur-lbl').textContent=S.settimane===1?T.settimana:T.settimane;
    var t=tariffa(c,S.settimane);
    $('cfg-tier-hint').innerHTML='<i class="ti ti-tag" style="font-size:13px;vertical-align:-2px"></i> '+nomeTariffa(t)+' · '+eur(t.ppw)+' '+T.a_sett;
  }
  renderSoggiorno();
  if(lez)$('cfg-range').innerHTML=(c.dal&&c.al?esc(fmt(T.disponibili_dal,{a:giorno(fromIso(c.dal)),b:giorno(fromIso(c.al))}))+' ':'')+T.orari;
  mostra('s-alloggio',inSede(c));mostra('s-extra',inSede(c));
  if(!inSede(c)){S.alloggio='nessuno';S.extra=[];}
  $('cfg-salloggio-num').textContent=S.settAlloggio;$('cfg-salloggio-lbl').textContent=S.settAlloggio===1?T.settimana:T.settimane;
  if(inSede(c)){renderAlloggi();renderExtra();}
  renderRiepilogo();
}
$('cfg-dur').addEventListener('input',function(){S.settimane=+this.value;aggiorna();});
$('cfg-nlez').addEventListener('input',function(){S.lezioni=+this.value;aggiorna();});
$('cfg-salloggio').addEventListener('input',function(){S.settAlloggio=+this.value;aggiorna();});

/* ---------- ISCRIZIONE ---------- */
if(DA_CORSO)$('cfg-cta').addEventListener('click',function(){
  $('cfg-form').hidden=false;
  $('cfg-form').scrollIntoView({behavior:'smooth',block:'start'});
  setTimeout(function(){$('cfg-nome').focus({preventScroll:true});},400);
});
function valore(id){return $(id).value.trim();}
function scelta(nome){var r=document.querySelector('input[name="'+nome+'"]:checked');return r?r.value:'';}
function segna(id,male){$(id).classList.toggle('cfg-bad',male);return male;}
/* L'iscrizione come dati: è quello che un domani riceverà il gestionale. */
function iscrizione(){
  var c=C(),a=inizio(),b=fineCorso();
  return {
    corso:c.id,corso_nome:c.nome,
    tema:c.tipo==='settimane'&&c.temi.length?c.temi[S.tema]:null,
    formula:c.tipo==='lezioni'?c.formule[S.formula].nome:null,
    lezioni:c.tipo==='lezioni'?S.lezioni:null,
    settimane:c.tipo==='settimane'?S.settimane:null,
    inizio:a?iso(a):null,fine:b?iso(b):null,
    alloggio:inSede(c)&&S.alloggio!=='nessuno'?alloggio().nome+(alloggio().camere.length?' · '+camera().nome:''):null,
    settimane_alloggio:inSede(c)&&S.alloggio!=='nessuno'?settAlloggio():null,
    extra:S.extra.map(function(id){return extra(id).nome;}),
    voci:voci(),totale:totale(),
    nome:valore('cfg-nome'),cognome:valore('cfg-cognome'),email:valore('cfg-email'),
    telefono:valore('cfg-tel'),nascita:valore('cfg-nascita'),
    livello:scelta('cfg-livello'),visto:scelta('cfg-visto'),pagamento:scelta('cfg-pag'),
    fattura:fattura(),
    note:valore('cfg-note'),lingua:D.lingua
  };
}
/* Dati per la fattura: a nome dello studente o di un ente. */
function enteScelto(){return scelta('cfg-int')==='ente';}
function campiFattura(){
  var e=enteScelto();
  ['f-cfg-ente','f-cfg-piva','f-cfg-sdi','f-cfg-emailf'].forEach(function(id){mostra(id,e);});
  mostra('f-cfg-codfisc',!e);
}
function fattura(){
  var e=enteScelto();
  return {
    intestatario:e?'ente':'persona',ente:e?valore('cfg-ente'):'',
    indirizzo:valore('cfg-ind'),cap:valore('cfg-cap'),citta:valore('cfg-citta'),paese:valore('cfg-paese'),
    codice_fiscale:e?'':valore('cfg-codfisc'),piva:e?valore('cfg-piva'):'',sdi:e?valore('cfg-sdi'):'',email:e?valore('cfg-emailf'):''
  };
}
document.querySelectorAll('input[name="cfg-int"]').forEach(function(r){r.addEventListener('change',campiFattura);});
campiFattura();
function testoEmail(x){
  var r=[];
  function l(k,v){if(v)r.push(k+': '+v);}
  l(T.nome,x.nome+' '+x.cognome);l(T.email,x.email);l(T.telefono,x.telefono);
  l(T.nascita,x.nascita?giorno(fromIso(x.nascita)):'');
  l(T.livello,x.livello);l(T.visto,x.visto);l(T.pagamento,x.pagamento);
  var f=x.fattura;
  r.push('');r.push(T.fattura+': '+(f.intestatario==='ente'?f.ente:x.nome+' '+x.cognome));
  l(T.indirizzo,f.indirizzo);l(T.cap,f.cap);l(T.citta,f.citta);l(T.paese,f.paese);
  l(T.cf,f.codice_fiscale);l(T.piva,f.piva);l(T.sdi,f.sdi);l(T.email_fattura,f.email);
  r.push('');
  r=r.concat(testoConfig(x));
  if(x.note){r.push('');l(T.note,x.note);}
  return r.join('\n');
}
/* Il corso scelto, le date e i costi: righe per l'email. */
function testoConfig(x){
  var r=[];
  function l(k,v){if(v)r.push(k+': '+v);}
  l(T.corso,x.corso_nome+' ['+x.corso+']');l(T.tema,x.tema);
  l(T.inizio,x.inizio?giorno(fromIso(x.inizio)):'');l(T.fine,x.fine?giorno(fromIso(x.fine)):'');
  r.push('');
  x.voci.forEach(function(v){r.push('- '+v[0]+(v[1]?' ('+v[1]+')':'')+(v[2]===null?'':': '+eur(v[2])));});
  l(T.totale,eur(x.totale));
  return r;
}
/* Richiesta di informazioni: un'email con la configurazione, senza i dati dello studente. */
$('cfg-info').addEventListener('click',function(){
  var x=iscrizione(),testo=[T.info_intro,''].concat(testoConfig(x),['',T.info_domanda,'']).join('\n');
  location.href='mailto:'+D.email+'?subject='+encodeURIComponent(T.oggetto_info+': '+x.corso_nome)+'&body='+encodeURIComponent(testo);
});
/* Invio. Per ora un'email a info@: quando ci sarà il gestionale, qui si salverà l'iscrizione. */
function invia(x){
  var testo=testoEmail(x);
  $('cfg-testo').value=testo;
  location.href='mailto:'+D.email+'?subject='+encodeURIComponent(T.oggetto+': '+x.corso_nome+' – '+x.nome+' '+x.cognome)+'&body='+encodeURIComponent(testo);
}
$('cfg-form').addEventListener('submit',function(e){
  e.preventDefault();
  var err=[],x=iscrizione();
  if(segna('f-cfg-nome',!x.nome)|segna('f-cfg-cognome',!x.cognome)|segna('f-cfg-email',!x.email)|
     segna('f-cfg-livello',!x.livello)|segna('f-cfg-visto',!x.visto)|segna('f-cfg-pag',!x.pagamento)|
     segna('f-cfg-ind',!x.fattura.indirizzo)|segna('f-cfg-cap',!x.fattura.cap)|segna('f-cfg-citta',!x.fattura.citta)|
     segna('f-cfg-paese',!x.fattura.paese)|
     segna('f-cfg-ente',enteScelto()&&!x.fattura.ente)|segna('f-cfg-piva',enteScelto()&&!x.fattura.piva)|
     segna('f-cfg-ok',!$('cfg-ok').checked))err.push(T.manca);
  if(x.email&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(x.email)){segna('f-cfg-email',true);err.push(T.email_errata);}
  if(!x.inizio){err.push(T.manca_data);}
  $('cfg-form-err').textContent=err.join(' ');
  if(err.length){var bad=this.querySelector('.cfg-bad input,.cfg-bad textarea');if(bad)bad.focus();else if(!x.inizio)$('s-data').scrollIntoView({behavior:'smooth'});return;}
  invia(x);
  $('cfg-config').hidden=true;this.hidden=true;$('cfg-done').hidden=false;
  wrap.scrollIntoView({behavior:'smooth',block:'start'});
});
$('cfg-copia').addEventListener('click',function(){
  var b=this,t=$('cfg-testo');t.select();
  function ok(){b.textContent=T.copiato;}
  if(navigator.clipboard)navigator.clipboard.writeText(t.value).then(ok,function(){document.execCommand('copy');ok();});
  else{document.execCommand('copy');ok();}
});
$('cfg-modifica').addEventListener('click',function(){$('cfg-done').hidden=true;$('cfg-config').hidden=false;$('cfg-form').hidden=false;});

aggiorna();
})();
