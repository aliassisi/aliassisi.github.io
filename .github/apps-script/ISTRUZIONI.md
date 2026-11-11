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
- **Registro**: le lezioni di ogni classe (le stesse colonne del vecchio registro) e le assenze;
  da qui si calcolano le ore per l'attestato;
- **Pagamenti**: fatture e proforma lette da Fatture in Cloud, abbinate agli studenti, promemoria;
- **Diplomi e attestati**: un PDF con una pagina per studente, da un vostro modello;
- **Email**: promemoria di pagamento, auguri di compleanno, email prima dell'arrivo, riepilogo
  della mattina per lo staff.

I dati restano nel foglio Google (schede Iscrizioni, Pagamenti, Classi, Assegnazioni, Registro,
Fatture, Promemoria, Documenti). Non costa niente.

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

## 5. Pubblica il gestionale
Un secondo deployment dello stesso script, aperto solo agli account aliassisi.it:
1. **Esegui il deployment → Nuovo deployment → App web**.
2. Descrizione `Gestionale`. **Esegui come: Me (info@aliassisi.it)**.
   **Chi può accedere: Chiunque all'interno di aliassisi.it**.
3. **Esegui il deployment** e copia l'URL (finisce con `/exec`). Salvalo nei preferiti.
4. Apri l'URL. Vai in **Impostazioni** e incollalo in "Link di questo gestionale".

Chi apre il link deve essere nella lista dello staff (punto 6), se no vede solo una riga di testo.
info@aliassisi.it è sempre nella lista.

## 6. Staff e aule
In **Impostazioni**: le email dello staff (per esempio `segreteria@aliassisi.it, laura@aliassisi.it`)
e i nomi delle aule. Devono essere account aliassisi.it.

## 7. Collega Fatture in Cloud
Serve un token di Fatture in Cloud che può solo leggere.
1. In Fatture in Cloud apri l'area sviluppatori e crea un'app privata (serve il suo Client ID).
2. **Impostazioni → Applicazioni collegate** (https://secure.fattureincloud.it/settings-apps) →
   **Collega una nuova applicazione** → incolla il Client ID → scegli l'azienda.
3. Permessi: **solo lettura** per Fatture, Proforma e Clienti.
4. Copia il token. Nel gestionale: **Impostazioni → Fatture in Cloud**, incollalo e salva.
5. In **Pagamenti** premi **Aggiorna da Fatture in Cloud**.

Questi passaggi in Fatture in Cloud vengono dalla loro documentazione: non li abbiamo provati.

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
1. Premi **Attiva**: da quel momento lo script gira ogni mattina alle 8.
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

## Come si lavora ogni giorno
- **Nuova iscrizione dal sito**: arriva un'email a info@ e la vedi in **Oggi** e in **Studenti**
  con lo stato "Nuova". Aprila, controlla, cambia lo stato in "Confermata".
- **Classe**: in **Classi** crea la classe (aula, livello, insegnante, date). Mettici gli studenti
  dalla classe stessa, dalla scheda dello studente, o dalla riga "Senza classe" del planning.
  Uno studente può cambiare classe: togli e metti, con le date.
- **Registro**: ogni insegnante apre **Registro**, sceglie la classe, **Nuova lezione**, segna
  le attività e gli assenti. Le ore si sommano da sole.
- **Pagamenti**: **Aggiorna da Fatture in Cloud** (lo fa anche da solo ogni mattina se i
  promemoria sono accesi).
- **Fine corso**: **Diplomi e attestati**.
- Il foglio Google resta: si può filtrare, ordinare, esportare. Non cambiare l'ordine delle
  colonne e non rinominare le schede.

## Se cambi lo script
Dopo una modifica: incolla i file, salva, poi **Gestisci deployment** e fai una **Nuova versione**
di **tutti e due** i deployment (sito e gestionale). Gli URL restano gli stessi.

## Limiti
- Google Workspace: circa 1.500 email al giorno.
- Fatture in Cloud: 1.000 richieste all'ora. Un aggiornamento ne usa poche.
- Un PDF di diplomi o attestati: al massimo 60 studenti per volta.
- Il gestionale si apre con un account aliassisi.it nella lista dello staff.
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
