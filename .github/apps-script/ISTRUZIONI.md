# Iscrizioni dal sito: come installare lo script Google

Lo script riceve le iscrizioni dal configuratore del sito e:
- scrive ogni iscrizione come riga nel foglio **Iscrizioni**;
- salva il passaporto (chi chiede il visto) nella cartella Drive privata **ALIA – Passaporti (privata)**;
- manda un'email di conferma allo studente e un avviso a info@aliassisi.it;
- dal menu **ALIA** del foglio crea i diplomi in PDF.

Si fa una volta sola, con l'account **info@aliassisi.it**. Ci vogliono circa 10 minuti.

## 1. Crea il foglio
1. Entra in Google Drive con info@aliassisi.it.
2. Nuovo → Fogli Google → Foglio di lavoro vuoto. Chiamalo **ALIA – Iscrizioni**.

## 2. Incolla lo script
1. Nel foglio: menu **Estensioni → Apps Script**.
2. Cancella tutto quello che c'è nel file `Codice.gs` e incolla il contenuto di
   `.github/apps-script/Codice.gs` (da questo repository).
3. In alto, chiama il progetto **Iscrizioni ALIA**. Premi l'icona del dischetto (Salva).

## 3. Prepara il foglio
1. Torna al foglio e ricarica la pagina. Dopo qualche secondo compare il menu **ALIA**.
2. **ALIA → Prepara il foglio (solo la prima volta)**.
3. Google chiede di autorizzare lo script: scegli info@aliassisi.it e consenti l'accesso a fogli,
   Drive, documenti ed email. Se compare "Google non ha verificato l'app", premi
   **Avanzate → Vai a Iscrizioni ALIA**: lo script è vostro, non di terzi.
4. Rilancia **ALIA → Prepara il foglio** se la prima volta si è fermato all'autorizzazione.
   Alla fine compaiono i fogli **Iscrizioni** e **Pagamenti**, e nel Drive le cartelle
   **ALIA – Passaporti (privata)**, **ALIA – Diplomi** e il documento **ALIA – Modello del diploma**.

## 4. Pubblica lo script
1. In Apps Script: **Esegui il deployment → Nuovo deployment**.
2. Tipo (rotellina): **App web**.
3. Descrizione: `Iscrizioni dal sito`. **Esegui come: Me (info@aliassisi.it)**.
   **Chi può accedere: Chiunque**. (Serve perché il modulo del sito possa inviare. Chi visita
   l'indirizzo può solo inviare iscrizioni: non può leggere niente.)
4. **Esegui il deployment** e copia l'**URL dell'app web** (finisce con `/exec`).
5. Manda l'URL a chi cura il sito: va in `data/configuratore.json`, campo `"invio"`, poi
   `python3 -I .github/scripts/build_configuratore.py .`.

## Come si lavora ogni giorno
- **Nuova iscrizione**: arriva un'email a info@ e una riga nel foglio, con lo stato "Nuova".
- **Stato**: cambialo dal menu a tendina (Nuova, Confermata, Pagata, In corso, Conclusa, Annullata).
- **Prezzo confermato**: scrivilo se è diverso dal totale stimato.
- **Pagamenti**: ogni pagamento è una riga nel foglio **Pagamenti** (numero dell'iscrizione,
  data, importo, metodo). Le colonne **Pagato** e **Da pagare** si aggiornano da sole.
- **Passaporto**: il link è nella colonna "File passaporto". La cartella è privata: la vede solo
  chi ha accesso al Drive di info@.
- **Diploma**: scrivi il livello nella colonna "Livello raggiunto", seleziona la riga e scegli
  **ALIA → Crea il diploma della riga selezionata**. Il PDF va nella cartella **ALIA – Diplomi**
  e il link nella colonna "Diploma".
- **Modello del diploma**: apri **ALIA – Modello del diploma** e cambialo come vuoi (logo,
  caratteri, testo). Lascia le parole tra doppie graffe: `{{nome}}`, `{{corso}}`, `{{dal}}`,
  `{{al}}`, `{{lezioni}}`, `{{livello}}`, `{{data}}`, `{{numero}}`.
- **Filtri**: nel foglio Iscrizioni usa Dati → Crea un filtro, per esempio per stato o per corso.
- **Staff**: condividi il foglio con le persone dello staff. Non condividere la cartella dei
  passaporti se non serve.

## Se cambi lo script
Dopo una modifica a `Codice.gs`: **Esegui il deployment → Gestisci deployment → modifica (matita)
→ Versione: Nuova versione → Esegui il deployment**. L'URL resta lo stesso.

## Limiti
- Google Workspace: circa 1.500 email al giorno. Ogni iscrizione ne usa due.
- File del passaporto: PDF, JPG o PNG, al massimo 5 MB.
- Al massimo 5 iscrizioni all'ora dallo stesso indirizzo email (contro lo spam).
- Se lo script non risponde, il modulo del sito apre l'email già scritta, come prima.

## Privacy
I passaporti sono dati personali. Decidete per quanto tempo tenerli e cancellateli dalla
cartella dopo la pratica del visto. Aggiornate l'informativa privacy del sito: dati per il visto,
passaporto, dove sono conservati (Google Workspace) e per quanto.
