# Iscrizioni e gestionale ALIA: come installare lo script Google

Lo script riceve le iscrizioni dal configuratore del sito e:
- scrive ogni iscrizione come riga nel foglio **Iscrizioni**;
- salva il passaporto (chi chiede il visto) nella cartella Drive privata **ALIA – Passaporti (privata)**;
- manda un'email di conferma allo studente e un avviso a info@aliassisi.it.

Il **gestionale** è una pagina per lo staff, sopra lo stesso foglio:
- **Oggi**: chi è in corso, chi arriva, chi non ha classe, chi finisce, pagamenti scaduti, compleanni;
- **Studenti**: tutte le iscrizioni, stato, prezzo, livello raggiunto, classi, fatture, documenti;
  si possono aggiungere iscrizioni arrivate per email o da agenzie;
- **Classi**: il planning per aula e per settimana (5 aule), chi è senza classe, l'email a una classe;
  i corsi individuali (privati, duo, online) hanno il loro calendario di lezioni;
- **Calendario**: la settimana giorno per giorno, classi e lezioni individuali, per insegnante o per
  aula; segna in rosso stesso insegnante o stessa aula alla stessa ora; mostra chiusure e laboratori;
- **Attività**: chiusure della scuola, laboratori e attività, con orario e luogo decisi di volta in
  volta, iscritti ed email ai partecipanti;
- **Registro**: le lezioni di ogni classe (le stesse colonne del vecchio registro) e le assenze;
  da qui si calcolano le ore per l'attestato;
- **Alloggi**: camere e appartamenti, chi sta dove notte per notte, chi ha chiesto un alloggio e
  non l'ha ancora, arrivi e partenze;
- **Pagamenti**: fatture e proforma lette da Fatture in Cloud, abbinate agli studenti, promemoria;
- **Diplomi e attestati**: un PDF con una pagina per studente, da un vostro modello;
- **Email**: promemoria di pagamento, auguri di compleanno, email prima dell'arrivo, riepilogo
  della mattina per lo staff.

I dati restano nel foglio Google (schede Iscrizioni, Pagamenti, Classi, Assegnazioni, Registro,
Fatture, Promemoria, Documenti, Alloggi, Soggiorni, Eventi, Partecipanti). Non costa niente.

Si fa con l'account **info@aliassisi.it**.

## 1. Crea il foglio (solo se non c'è già)
1. Entra in Google Drive con info@aliassisi.it.
2. Nuovo → Fogli Google → Foglio di lavoro vuoto. Chiamalo **ALIA – Iscrizioni**.

## 2. Incolla lo script
Nel foglio: menu **Estensioni → Apps Script**. Il progetto ha tre file:

| File in Apps Script | Contenuto (da questo repository) |
|---|---|
| `Codice.gs` | `.github/apps-script/Codice.gs` |
| `Gestionale.gs` | `.github/apps-script/Gestionale.gs` |
| `Pagina.html` | `.github/apps-script/Pagina.html` |

1. `Codice.gs` c'è già: cancella tutto e incolla il file nuovo.
2. Per gli altri due: **+** accanto a "File" → **Script** (nome `Gestionale`) e **HTML** (nome
   `Pagina`). Il nome deve essere esatto: `Pagina`, senza `.html`.
3. Incolla da GitHub con il pulsante "Copy raw file", non selezionando il testo. Se il browser
   traduce le pagine in automatico, spegni la traduzione prima: una volta ha rovinato il codice.
4. **Impostazioni progetto** (rotellina a sinistra) → Fuso orario: **(GMT+01:00) Roma**.
5. Premi il dischetto (Salva).

## 3. Prepara il foglio
1. Torna al foglio e ricarica la pagina. Dopo qualche secondo compare il menu **ALIA**.
2. **ALIA → Prepara il foglio (solo la prima volta)**. Si può rilanciare: non cancella niente.
3. Google chiede di autorizzare lo script: scegli info@aliassisi.it e consenti tutto (fogli, Drive,
   documenti, presentazioni, email, servizi esterni, trigger). Se compare "Google non ha verificato
   l'app", premi **Avanzate → Vai a Iscrizioni ALIA**: lo script è vostro, non di terzi.
4. Se si è fermato all'autorizzazione, rilancia **ALIA → Prepara il foglio**.
   Alla fine ci sono le schede nuove e, nella cartella **ALIA – Diplomi**, il documento
   **ALIA – Modello dell'attestato di frequenza**.

## 4. Aggiorna il deployment del sito
Il modulo del sito usa il deployment che c'è già. Va aggiornato, l'indirizzo non cambia:
**Esegui il deployment → Gestisci deployment → matita → Versione: Nuova versione → Esegui il deployment**.

(Prima installazione: **Nuovo deployment**, tipo **App web**, descrizione `Iscrizioni dal sito`,
**Esegui come: Me**, **Chi può accedere: Chiunque**. L'URL va in `data/configuratore.json`,
campo `"invio"`, poi `python3 -I .github/scripts/build_configuratore.py .`)

## 5. Il link del gestionale
Il gestionale è lo stesso deployment del sito (punto 4, **Chi può accedere: Chiunque**): il suo URL
`/exec` aperto nel browser mostra il gestionale. Salvalo nei preferiti. Il modulo del sito continua a
mandare le iscrizioni allo stesso indirizzo.

(Per una prova su una copia del foglio: nella copia, **Nuovo deployment → App web**, **Esegui come:
Me**, **Chi può accedere: Chiunque**, e si usa l'URL di quel deployment.)

**Come si entra:** si apre il link, si scrive la propria email e arriva un codice di 6 cifre (vale
10 minuti). Dopo il codice quel browser resta collegato 30 giorni; **Esci** in alto a destra lo
scollega. Il codice arriva solo agli indirizzi della lista dello staff: vanno bene anche Gmail e
altri indirizzi non aliassisi.it. info@aliassisi.it è sempre nella lista.

Chi non ha il codice non vede niente: la pagina chiede l'email e basta. Ogni funzione dello script
controlla l'accesso; senza accesso funzionano solo l'invio delle iscrizioni dal sito, i trigger
automatici e il menu ALIA del foglio (per chi apre il foglio).

## 6. Staff e aule
In **Impostazioni**: le email dello staff, separate da virgola (per esempio
`segreteria@aliassisi.it, laura.rossi@gmail.com`), e i nomi delle aule. Chi viene tolto dalla lista
non entra più, anche se era collegato. (La lista si può scrivere anche in Apps Script, Impostazioni
progetto → Proprietà script → `staff`.)

## 7. Collega Fatture in Cloud
Serve un token di Fatture in Cloud.
1. In Fatture in Cloud, sezione **Sviluppatore**: crea un'applicazione. Nella sua pagina c'è il
   **Client ID**.
2. **Impostazioni → Applicazioni collegate** (https://secure.fattureincloud.it/settings-apps) →
   **Collega una nuova applicazione** → incolla il Client ID → scegli l'azienda.
3. Permessi:
   - **Proforma: lettura e scrittura** (il gestionale crea le proforma);
   - **Clienti: lettura e scrittura** (crea il cliente se non c'è);
   - **Fatture: lettura** (pagamenti e promemoria);
   - **Impostazioni: lettura** (le aliquote IVA).
4. Copia il token. Nel gestionale: **Impostazioni → Fatture in Cloud**, incollalo e salva.
5. In **Pagamenti** premi **Aggiorna da Fatture in Cloud**.

I permessi si cambiano anche dopo: **Applicazioni collegate → Gestisci** accanto all'app →
**Modifica** nei permessi. Il token resta lo stesso.

Questi passaggi in Fatture in Cloud vengono dalla loro documentazione: non li abbiamo provati.
La documentazione non dice dove si crea l'applicazione: se non trovate "Sviluppatore", chiedete
all'assistenza di Fatture in Cloud un "token manuale" per la vostra azienda.

**La proforma dal gestionale.** Nella scheda dello studente: **Crea e invia la proforma…**
- Le righe vengono dal preventivo del modulo del sito (corso, extra), **senza l'alloggio**, che
  lo studente paga al proprietario. Per le iscrizioni vecchie o fatte a mano c'è una riga con il
  corso e il prezzo. Si possono cambiare, togliere, aggiungere.
- IVA per riga: proposta "Esente art. 10"; il menu mostra le aliquote del vostro Fatture in Cloud.
- Rata unica; la scadenza proposta è tra 15 giorni e si cambia (anche dopo l'inizio del corso).
- Il cliente si crea in Fatture in Cloud con i dati di fatturazione dell'iscrizione (studente o
  ente), o si usa quello che ha già la stessa email.
- "Mandala subito" usa l'email di Fatture in Cloud, con il PDF, nella lingua dello studente.
- La proforma compare subito in **Pagamenti**, abbinata, e i promemoria la seguono.
- Quando lo studente paga: in Fatture in Cloud **trasformate la proforma in fattura** e segnate il
  pagamento. Con "Aggiorna da Fatture in Cloud" il pagamento arriva nel gestionale.

Come funziona:
- legge fatture e proforma degli ultimi 400 giorni;
- abbina ogni documento a un'iscrizione: stessa email, se no nome e cognome nel nome del cliente.
  Se non trova, scegli lo studente a mano nella colonna "Iscrizione": la scelta resta;
- i pagamenti saldati delle **fatture** (non delle proforma) vanno da soli nella scheda Pagamenti:
  così "Pagato" e "Da pagare" in Iscrizioni sono giusti. Non scriverli anche a mano;
- il promemoria va all'email del cliente in Fatture in Cloud (lo studente, o l'agenzia o l'ente
  che riceve la fattura).

## 8. Email automatiche
In **Email**:
1. Premi **Attiva**: da quel momento lo script gira ogni mattina alle 8 (e ogni ora per i link
   delle lezioni online). Dopo questo aggiornamento premi **Attiva** di nuovo.
2. Metti ogni tipo di email su **Prova** per qualche giorno: le email vanno a info@ con il
   destinatario vero nell'oggetto. Controlla testi e destinatari.
3. Poi metti **Attive**.

- **Promemoria di pagamento**: N giorni prima della scadenza, 3 giorni dopo, 17 giorni dopo.
  Ognuno una volta sola. Scrivi in "Come pagare" IBAN e intestazione.
- **Compleanno**: solo a chi è in corso, o anche agli ex studenti.
- **Prima dell'arrivo**: N giorni prima dell'inizio, a chi è Confermato o Pagato.
  Controlla l'indirizzo e l'orario nel testo prima di attivarla.
- **Riepilogo per lo staff**: ogni mattina a info@, solo se c'è qualcosa da dire.

Ogni email mandata è una riga della scheda **Promemoria**.

## Diplomi e attestati
- I modelli sono un Documento Google o una Presentazione Google. Per un diploma grafico
  (orizzontale, con cornice e logo) usate una **Presentazione**: si stampa com'è.
- Il vostro modello in Word o PowerPoint: caricalo su Drive, aprilo con Google e scegli
  **File → Salva come Documenti/Presentazioni Google**. Incolla il link in **Impostazioni**.
- Scrivi i campi tra doppie graffe, nel testo del modello:
  `{{nome}}` `{{cognome}}` `{{periodo}}` (es. "dal 3 al 28 novembre 2026") `{{livello}}` (raggiunto)
  `{{livello_iniziale}}` `{{corso}}` `{{ore}}` (dal registro) `{{lezioni}}` `{{dal}}` `{{al}}`
  `{{nascita}}` `{{luogo_nascita}}` `{{nazionalita}}` `{{data}}` (di oggi) `{{numero}}`.
- In un Documento i campi nell'intestazione e nel piè di pagina non vengono sostituiti: mettili nel testo.
- **Diplomi e attestati**: scegli una classe o le date di fine corso, scrivi il livello raggiunto,
  premi **Crea**. Esce un PDF con una pagina per studente, nella cartella **ALIA – Diplomi**.
- Il diploma chiede il livello raggiunto. L'attestato no.
- Il primo modello del diploma usava `{{nome}}` per nome e cognome. "Prepara il foglio" lo ha
  cambiato in `{{nome}} {{cognome}}`.

## Corsi individuali (privati, duo, online)
Ogni corso individuale è una "classe" di tipo **Individuale o duo**, con le sue lezioni.
1. Lo studente compare in **Oggi → Corsi individuali da pianificare** (sono le iscrizioni dal sito
   con una formula, o con "privat", "individ", "immersion", "online" nel nome del corso).
2. Apri lo studente → **Crea il corso individuale**.
3. Nel corso, **Pianifica le lezioni**: dal… al…, i giorni della settimana, ora di inizio e di fine,
   aula, insegnante, quante lezioni (di solito quelle che restano dalle acquistate). Si possono
   pianificare in più volte, con orari diversi, o aggiungere una lezione sola.
4. **Manda il calendario** allo studente: un'email con le prossime lezioni e un file `.ics` che le
   mette nel calendario del telefono.
5. Dopo ogni lezione: apri la lezione (dal corso, dal **Calendario** o dal **Registro**), scrivi
   cosa si è fatto e salva: diventa **fatta**. Gli altri stati: **annullata** (non conta e
   si recupera, vedi sotto) e **persa** (lo studente non è venuto senza avvisare: conta come usata,
   non come frequentata).
6. Per un duo: nel corso, **Aggiungi un secondo studente**.

### Lezioni annullate
Una lezione annullata non si perde: si recupera.
1. Accanto alla lezione, **Annulla** (o stato "annullata"). Il gestionale chiede conferma.
2. **Fissa subito il recupero**: propone il primo giorno libero alla stessa ora (né lo studente né
   l'insegnante hanno altro). Cambialo se serve. Oppure togli la spunta e fissalo dopo con
   **Fissa il recupero**.
3. **Avvisa lo studente**: un'email con la lezione annullata e il recupero, e un file che toglie la
   lezione dal suo calendario (e aggiunge il recupero). Il file per togliere funziona se lo studente
   aveva aggiunto la lezione dal nostro file; con Google Calendar e Apple di solito sì, con altre app
   non è provato.
4. Le lezioni annullate senza recupero sono in **Oggi → Lezioni annullate da recuperare** e nel
   corso ("da recuperare").
5. Se il recupero cade dopo la fine del corso, il corso e le date dello studente si allungano da soli.

### Lezioni online
Sono corsi individuali con **Modalità: Online** (se il corso del sito ha "online" nel nome, il
gestionale lo crea già online).
1. Nel corso, **Modifica** → incolla il **Link Zoom** (la vostra stanza Zoom o una riunione
   ricorrente). Vale per tutte le lezioni del corso.
2. Una lezione con un link diverso: aprila e scrivi il suo link. Va anche per una lezione online
   dentro un corso in sede.
3. Il link parte da solo: in **Email → Link delle lezioni online**, scegli quante ore prima
   (di solito 24) e metti **Prova**, poi **Attive**. Lo script controlla ogni ora; ogni studente
   riceve il link una volta per lezione.
4. **Manda il link** accanto a una lezione lo manda subito.
5. **Manda il calendario** mette il link nell'email e nel file per il calendario.

Gli orari sono in ora italiana. Il file `.ics` li converte da solo sul telefono dello studente;
nelle email c'è scritto "ora italiana". Il gestionale non crea le riunioni Zoom: il link lo
scrivete voi.

Il riepilogo del corso mostra lezioni acquistate, previste, fatte e quante ne restano da pianificare.
Le ore dell'attestato contano solo le lezioni fatte.

## Alloggi
1. In **Alloggi → Nuovo alloggio** inserite ogni camera o appartamento: nome (es. "Via San
   Francesco 3 – camera 1"), tipo (singola, singola con bagno, doppia, doppia con bagno,
   appartamento indipendente), posti letto, indirizzo, contatto del proprietario (lo vede solo lo
   staff) e le **istruzioni per lo studente** (chiavi, wifi, come arrivare).
2. Chi ha chiesto un alloggio nel modulo del sito compare in **Da sistemare** (e in **Oggi**), con
   le date proposte: dal giorno prima del corso, per le settimane chieste. Il gestionale propone già
   il primo alloggio libero del tipo chiesto: **Assegna**. Per date diverse, apri lo studente →
   **Assegna un alloggio**.
3. La **partenza** è il giorno in cui lo studente lascia la camera: quella notte la camera è libera
   per chi arriva.
4. Se un alloggio è pieno anche una sola notte, il gestionale lo dice e chiede se prenotare lo
   stesso. Nella tabella le notti con troppe persone sono rosse.
5. **Manda i dettagli dell'alloggio** (dalla scheda dello studente): indirizzo, date e istruzioni.
   Anche l'email prima dell'arrivo li contiene, con `{{alloggio}}` nel testo.
6. Un alloggio che non usate più: mettetelo **non attivo** (le prenotazioni passate restano).

I prezzi degli alloggi restano nel totale dell'iscrizione e nelle fatture: il gestionale non li
calcola a parte.

## Chiusure, laboratori e attività
Sono le attività comprese in tutti i corsi di gruppo (pagina "Attività, facilities e laboratori"):
la lezione itinerante settimanale, la lezione di pronuncia settimanale, il laboratorio. Le date di
chiusura, le date dei laboratori e i nomi delle attività settimanali sono già nel sito:
`data/alia.json` (`chiusure`), `data/laboratori.json`, `data/configuratore.json`
(`attivita_settimanali`). Il gestionale le legge da lì, così non si scrivono due volte.
1. **Attività → Aggiorna dal sito**. Da rifare dopo ogni modifica di quei file nel sito.
   Orario, luogo, chi lo segue, posti e note scritti nel gestionale restano. Una data tolta dal sito
   sparisce anche qui, se nessuno è iscritto.
2. **Attività settimanali** (lezione fuori dalla classe, pronuncia): ogni classe di gruppo ne ha una
   per tipo ogni settimana, dentro le sue ore di lezione. In **Attività**, "Questa settimana" e
   "Settimana prossima" mostrano le classi che non l'hanno ancora: **Programma** → scegli giorno e
   orario (es. "10:50–12:30"). Più classi insieme: spuntale tutte nella stessa attività. Le
   attività di una classe compaiono nel suo **Registro**, quel giorno. In **Oggi** e nel riepilogo
   della mattina c'è cosa manca da programmare.
3. **Laboratori**: sono per tutti gli studenti dei corsi di gruppo in corso quel giorno. Orario e
   luogo si decidono di volta in volta: apri il laboratorio e scrivili (es. "15:00–17:00"). Finché
   manca, compare "orario da decidere".
4. Altre attività (cena, gita…) e chiusure in più: **Nuovo laboratorio o attività** o **Nuova
   chiusura**. "Chi partecipa": alcune classi, tutti gli studenti dei corsi di gruppo, o solo chi si
   iscrive (con i posti, se servono).
5. **Email**: ai partecipanti (le classi scelte, tutti, o gli iscritti), per esempio quando avete
   deciso l'orario. Gli studenti solo di lezioni individuali o online non sono "tutti": per loro
   usate "Solo chi si iscrive".

Nei giorni di chiusura:
- il calendario non mostra le classi di gruppo e segna "Chiuso";
- **Pianifica le lezioni** salta quei giorni (e dice quanti);
- il recupero di una lezione annullata non viene proposto in un giorno di chiusura;
- una lezione messa a mano in un giorno di chiusura chiede conferma.

Il sito si legge da `https://aliassisi.it` (si cambia in Impostazioni, "Indirizzo del sito").

## Come si lavora ogni giorno
- **Nuova iscrizione dal sito**: arriva un'email a info@ e la vedi in **Oggi** e in **Studenti**
  con lo stato "Nuova". Aprila, controlla, cambia lo stato in "Confermata".
- **Scheda dello studente**: in alto i dati di tutti i giorni (stato, date del corso, arrivo e
  partenza se diversi, livelli, prezzo confermato, **sconto**, note); in **Tutti i dati** il resto
  (corso, persona, passaporto, dati della fattura). Si cambia tutto e si salva con **Salva**.
  Non si cambiano il numero, la data di arrivo dell'iscrizione e il totale stimato dal sito.
  - **Sconto (€)**: si toglie dal prezzo (confermato o, se manca, stimato). "Da pagare" lo conta
    e nella proforma il prezzo del corso è già scontato.
  - **Arrivo / Partenza**: per un arrivo anticipato o una partenza diversa dal corso. L'alloggio
    proposto e "Arrivano nei prossimi giorni" usano queste date.
  - Dopo questo aggiornamento lanciate **ALIA → Prepara il foglio** una volta: aggiunge le colonne
    nuove e rifà le formule di "Da pagare" con lo sconto.
- **Classe**: in **Classi** crea la classe (aula, livello, insegnante, date). Mettici gli studenti
  dalla classe stessa, dalla scheda dello studente, o dalla riga "Senza classe" del planning.
  Uno studente può cambiare classe: nel planning **trascina il suo nome** su un'altra classe della stessa
  settimana (o su "Senza classe"). Lo sposta da quella settimana in poi (se è la settimana in corso, da
  oggi): prima resta nella classe di prima, con il suo registro.
- **Registro**: ogni insegnante apre **Registro**, sceglie la classe, **Nuova lezione**, segna
  le attività e gli assenti. Le ore si sommano da sole. **Periodo** (dal… al…, o "Questa
  settimana", "Settimana scorsa", "Questo mese") filtra lezioni e presenze: ore, lezioni e giorni
  di assenza di ogni studente in quelle date.
- **Pagamenti**: **Aggiorna da Fatture in Cloud** (lo fa anche da solo ogni mattina se i
  promemoria sono accesi).
- **Fine corso**: **Diplomi e attestati**.
- Il foglio Google resta: si può filtrare, ordinare, esportare. Non cambiare l'ordine delle
  colonne e non rinominare le schede.

## Dopo un aggiornamento dello script
Le schede Classi e Registro hanno colonne nuove (Tipo, Modalità, Link online; Ora inizio, Ora fine,
Aula, Stato, Link online, Recupero della lezione).
Ci sono anche schede nuove: Alloggi, Soggiorni, Eventi, Partecipanti. Il gestionale crea le schede e scrive le
intestazioni che mancano la prima volta che si apre. Le lezioni già scritte valgono come "fatte".
Il testo dell'email prima dell'arrivo, se l'avete già cambiato, non ha `{{alloggio}}`: aggiungetelo voi.

## Se cambi lo script
Dopo una modifica: incolla i file, salva, poi **Gestisci deployment** e fai una **Nuova versione**
di **tutti e due** i deployment (sito e gestionale). Gli URL restano gli stessi.

## Limiti
- Google Workspace: circa 1.500 email al giorno.
- Fatture in Cloud: 1.000 richieste all'ora. Un aggiornamento ne usa poche.
- Un PDF di diplomi o attestati: al massimo 60 studenti per volta.
- Il gestionale si apre con un codice via email, solo per chi è nella lista dello staff. Al massimo
  5 codici all'ora per indirizzo, 5 tentativi per codice.
- I trigger automatici (ogni mattina, ogni ora) partono solo da soli: lanciare `ogniGiorno` o
  `ogniOra` a mano dall'editor non fa niente.
- File del passaporto: PDF, JPG o PNG, al massimo 5 MB.
- Al massimo 5 iscrizioni all'ora dallo stesso indirizzo email (contro lo spam).
- Se lo script non risponde, il modulo del sito apre l'email già scritta, come prima.

## Privacy
- I passaporti sono dati personali. Decidete per quanto tempo tenerli e cancellateli dalla
  cartella dopo la pratica del visto.
- Auguri, email prima dell'arrivo e promemoria usano i dati dell'iscrizione. Scrivetelo
  nell'informativa privacy del sito. Gli auguri agli ex studenti e qualsiasi newsletter
  chiedono il consenso: il modulo del sito oggi non lo chiede.
- Il token di Fatture in Cloud è nelle proprietà dello script: la pagina non lo mostra.
