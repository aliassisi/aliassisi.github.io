/* Comparatore dei corsi (pagina Calendario e costi).
   Source: .github/templates/comparatore.js. build_configuratore.py copies it
   to assets/alia/ and writes the data into <script id="cmp-dati">: the same
   start dates, closures, rates and activities as the configurator.
   Each button opens the configurator with ?corso=&inizio=&settimane=&da=calendario. */
(function(){
var D=JSON.parse(document.getElementById('cmp-dati').textContent);
var IT=D.lingua==='it',LOC=IT?'it-IT':'en-GB';
var T=IT?{
  titolo:'Confronta i corsi per le tue date',
  sottotitolo:'Scegli quando vuoi iniziare e per quanto tempo. Vedi le date, cosa è incluso nel periodo e il costo di ogni corso, poi configura e iscriviti a quello che preferisci.',
  inizio:'Data di inizio',altra_data:'Un altro lunedì…',lunedi:'Un altro lunedì',durata:'Durata',
  settimana:'settimana',settimane:'settimane',meno:'Una settimana in meno',piu:'Una settimana in più',n_sett:'Numero di settimane',
  il_corso:'Il tuo corso',feriali:'dal lunedì al venerdì',scegli_lunedi:'Scegli un lunedì',solo_lunedi:'I corsi iniziano il lunedì.',
  chiusure:'Chiusure della scuola nel periodo',nessuna:'Nessuna: lezioni tutti i giorni feriali.',
  giorno:'giorno senza lezioni',giorni:'giorni senza lezioni',non_prolungato:'Il corso non viene prolungato per i giorni di chiusura.',
  incluso:'Incluso nel tuo periodo',ogni_sett:'ogni settimana',nessun_lab:'In queste date non ci sono laboratori speciali.',
  gruppi:{18:'Standard',22:'Intensivi',26:'Super intensivi'},
  a_sett_gruppo:'{n} lezioni a settimana',solo_gruppo:'{g} lezioni di gruppo al mattino',gruppo_ind:'{g} di gruppo + {i} individuali',
  totale:'Totale corso',a_sett:'a settimana',cta:'Configura e iscriviti',
  privati_std:'Puoi aggiungere lezioni private al pomeriggio',
  privati:'Solo lezioni private? Si pagano a lezione e gli orari si concordano con te: <a href="#corsi-privati">vedi i corsi privati</a>.',
  nota:'Prezzi indicativi del solo corso, senza alloggio ed extra, che scegli nel passo successivo. Vale il costo confermato all’iscrizione.',
  corsi:'Corsi'
}:{
  titolo:'Compare courses for your dates',
  sottotitolo:'Choose when you’d like to start and for how long. You’ll see your dates, what’s included in that period and the cost of every course. Then configure and enrol in the one you prefer.',
  inizio:'Start date',altra_data:'Another Monday…',lunedi:'Another Monday',durata:'Duration',
  settimana:'week',settimane:'weeks',meno:'One week less',piu:'One week more',n_sett:'Number of weeks',
  il_corso:'Your course',feriali:'Monday to Friday',scegli_lunedi:'Choose a Monday',solo_lunedi:'Courses start on Monday.',
  chiusure:'School closures in this period',nessuna:'None: lessons every weekday.',
  giorno:'day without lessons',giorni:'days without lessons',non_prolungato:'The course is not extended for closure days.',
  incluso:'Included in your period',ogni_sett:'weekly',nessun_lab:'No special workshops in these dates.',
  gruppi:{18:'Standard',22:'Intensive',26:'Super intensive'},
  a_sett_gruppo:'{n} lessons a week',solo_gruppo:'{g} group lessons in the morning',gruppo_ind:'{g} group + {i} one-on-one lessons',
  totale:'Course total',a_sett:'per week',cta:'Configure &amp; enrol',
  privati_std:'Private lessons can be added in the afternoon',
  privati:'Only private lessons? They’re priced per lesson and scheduled with you: <a href="#corsi-privati">see private courses</a>.',
  nota:'Indicative prices for the course only, before accommodation and extras, which you choose in the next step. Final cost confirmed on enrolment.',
  corsi:'Courses'
};

function $(id){return document.getElementById(id);}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function fmt(s,v){return s.replace(/\{(\w)\}/g,function(m,k){return v[k];});}
function eur(n){return n.toLocaleString(LOC,{useGrouping:'always'})+' €';}
function iso(d){var m=d.getMonth()+1,g=d.getDate();return d.getFullYear()+'-'+(m<10?'0':'')+m+'-'+(g<10?'0':'')+g;}
function fromIso(s){var p=s.split('-');return new Date(+p[0],+p[1]-1,+p[2]);}
function data(d,anno){return d.toLocaleDateString(LOC,anno?{day:'numeric',month:'long',year:'numeric'}:{day:'numeric',month:'long'});}
function breve(d){return d.toLocaleDateString(LOC,{day:'numeric',month:'short'});}
function settimane(n){return n+' '+(n===1?T.settimana:T.settimane);}
function maiuscola(s){return s.charAt(0).toUpperCase()+s.slice(1);}
function tariffa(t,w){for(var i=0;i<t.length;i++)if(w>=t[i].from&&w<=t[i].to)return t[i].ppw;return t[t.length-1].ppw;}
var OGGI=new Date();OGGI.setHours(0,0,0,0);

var wrap=$('cmp-wrap');
wrap.innerHTML=
  '<header><h2>'+T.titolo+'</h2><p class="cmp-sub">'+T.sottotitolo+'</p></header>'+
  '<div class="cmp-controls">'+
    '<div class="cmp-field"><label class="cmp-lbl" for="cmp-start">'+T.inizio+'</label><select id="cmp-start"></select></div>'+
    '<div class="cmp-field" id="cmp-cw" hidden><label class="cmp-lbl" for="cmp-custom">'+T.lunedi+'</label><input type="date" id="cmp-custom" min="'+iso(OGGI)+'"></div>'+
    '<div class="cmp-field"><span class="cmp-lbl" id="cmp-wklbl">'+T.durata+'</span>'+
      '<div class="cmp-step" role="group" aria-labelledby="cmp-wklbl">'+
        '<button type="button" id="cmp-minus" aria-label="'+T.meno+'">−</button>'+
        '<input type="number" id="cmp-weeks" min="1" max="48" value="4" inputmode="numeric" aria-label="'+T.n_sett+'">'+
        '<span class="cmp-wk" id="cmp-wkword"></span>'+
        '<button type="button" id="cmp-plus" aria-label="'+T.piu+'">+</button>'+
      '</div></div>'+
  '</div>'+
  '<section class="cmp-period" aria-label="'+T.il_corso+'">'+
    '<div class="cmp-pbox"><span class="cmp-lbl">'+T.il_corso+'</span><div class="cmp-dates" id="cmp-dates"></div><div class="cmp-small" id="cmp-dur"></div></div>'+
    '<div class="cmp-pbox"><span class="cmp-lbl">'+T.chiusure+'</span><ul class="cmp-closures" id="cmp-closures"></ul><div class="cmp-small" id="cmp-cnote"></div></div>'+
    '<div class="cmp-pbox"><span class="cmp-lbl">'+T.incluso+'</span><ul class="cmp-acts" id="cmp-acts"></ul></div>'+
  '</section>'+
  '<section class="cmp-courses" id="cmp-courses" aria-label="'+T.corsi+'"></section>'+
  '<p class="cmp-foot">'+T.nota+'</p>'+
  '<p class="cmp-priv">'+T.privati+'</p>';

var sel=$('cmp-start'),custom=$('cmp-custom'),wk=$('cmp-weeks');
sel.innerHTML=D.date_inizio.filter(function(s){return fromIso(s)>=OGGI;}).map(function(s){return '<option value="'+s+'">'+esc(data(fromIso(s),true))+'</option>';}).join('')+
  '<option value="altra">'+T.altra_data+'</option>';

function inizio(){
  if(sel.value!=='altra')return fromIso(sel.value);
  if(!custom.value)return null;
  var d=fromIso(custom.value);return d.getDay()===1&&d>=OGGI?d:null;
}
function nSett(){var w=parseInt(wk.value,10);return isNaN(w)?1:Math.max(1,Math.min(48,w));}

/* Le chiusure nei giorni feriali del periodo, unite per nome (Natale va da dicembre a gennaio). */
function chiusure(s,e){
  var out=[];
  D.chiusure.forEach(function(c){
    var a=fromIso(c.dal),b=fromIso(c.al);if(a<s)a=new Date(s);if(b>e)b=new Date(e);
    for(var d=new Date(a);d<=b;d.setDate(d.getDate()+1)){
      var g=d.getDay();if(g===0||g===6)continue;
      var u=out[out.length-1];
      if(!u||u.nome!==c.nome){u={nome:c.nome,dal:new Date(d),n:0};out.push(u);}
      u.al=new Date(d);u.n++;
    }
  });
  return out;
}

function render(){
  $('cmp-cw').hidden=sel.value!=='altra';
  var s=inizio(),w=nSett(),cl=$('cmp-closures'),acts=$('cmp-acts');
  $('cmp-wkword').textContent=w===1?T.settimana:T.settimane;
  if(!s){
    $('cmp-dates').innerHTML='<span>'+T.scegli_lunedi+'</span>';
    $('cmp-dur').textContent=T.solo_lunedi;
    cl.innerHTML='';acts.innerHTML='';$('cmp-cnote').textContent='';
  } else {
    /* Fine corso: il venerdì dell'ultima settimana. */
    var e=new Date(s);e.setDate(e.getDate()+w*7-3);
    $('cmp-dates').innerHTML=esc(data(s,s.getFullYear()!==e.getFullYear()))+' <span>→</span> '+esc(data(e,true));
    $('cmp-dur').textContent=settimane(w)+', '+T.feriali;
    var ch=chiusure(s,e);
    cl.innerHTML=ch.length?ch.map(function(x){
      return '<li>'+esc(maiuscola(x.nome))+': '+esc(iso(x.dal)===iso(x.al)?breve(x.dal):breve(x.dal)+' – '+breve(x.al))+' ('+x.n+' '+(x.n===1?T.giorno:T.giorni)+')</li>';
    }).join(''):'<li class="cmp-none">'+T.nessuna+'</li>';
    $('cmp-cnote').textContent=ch.length?T.non_prolungato:'';
    var a=iso(s),b=iso(e),lab=[];
    D.attivita.forEach(function(x){x.date.forEach(function(d){if(d>=a&&d<=b)lab.push({d:d,nome:x.nome});});});
    lab.sort(function(x,y){return x.d<y.d?-1:x.d>y.d?1:0;});
    acts.innerHTML=D.attivita_settimanali.map(function(x){return '<li><time>'+T.ogni_sett+'</time><span>'+esc(x)+'</span></li>';}).join('')+
      (lab.length?lab.map(function(x){return '<li><time datetime="'+x.d+'">'+esc(breve(fromIso(x.d)))+'</time><span>'+esc(x.nome)+'</span></li>';}).join('')
        :'<li><time></time><span>'+T.nessun_lab+'</span></li>');
  }
  var q=(s?'&inizio='+iso(s):'')+'&settimane='+w+'&da=calendario';
  $('cmp-courses').innerHTML=D.gruppi.map(function(g){
    var r=tariffa(g.tariffe,w);
    return '<article class="cmp-course"><div class="cmp-chead"><span class="cmp-lpw">'+fmt(T.a_sett_gruppo,{n:g.ore})+'</span>'+
      '<h3 class="cmp-cname">'+T.gruppi[g.ore]+'</h3><span class="cmp-mix">'+fmt(g.individuali?T.gruppo_ind:T.solo_gruppo,{g:g.gruppo,i:g.individuali})+'</span></div>'+
      '<div class="cmp-price"><span class="cmp-lbl">'+T.totale+'</span><span class="cmp-total">'+eur(r*w)+'</span><span class="cmp-rate">'+eur(r)+' '+T.a_sett+' × '+w+'</span></div>'+
      '<div class="cmp-variants">'+g.varianti.map(function(v){
        var nota=v.id==='standard'?'<a href="#corsi-privati">'+T.privati_std+'</a>':(v.nota?esc(v.nota):'');
        return '<div class="cmp-var"><span class="cmp-vname">'+esc(v.nome)+(nota?'<small>'+nota+'</small>':'')+'</span>'+
          '<a class="cmp-cta" href="'+D.configuratore+'?corso='+v.id+q+'">'+T.cta+'</a></div>';
      }).join('')+'</div></article>';
  }).join('');
}
sel.addEventListener('change',function(){if(sel.value==='altra')custom.focus();render();});
custom.addEventListener('change',render);
wk.addEventListener('input',render);
wk.addEventListener('change',function(){wk.value=nSett();render();});
$('cmp-minus').addEventListener('click',function(){wk.value=Math.max(1,nSett()-1);render();});
$('cmp-plus').addEventListener('click',function(){wk.value=Math.min(48,nSett()+1);render();});
render();
})();
