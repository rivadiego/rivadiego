# Coach Connect: guida per agenti

Leggi questo file prima di lavorare su `coach-connect/`. Il README spiega l'app all'utente; qui ci sono stato, architettura, pubblicazione, vincoli e lezioni già imparate. Il repository è **pubblico**: niente dati personali, token o database nei commit, nei log o nelle descrizioni delle PR.

## In breve

- **Cos'è**: app personale di allenamento ibrido (palestra + corsa) sui dati Garmin. Tre tab (Attività, Scheda, Coach) e un "+" per registrare gli allenamenti di palestra. Tutto in italiano.
- **Dove gira**: sito online gratuito su Render, <https://coach-connect-bwra.onrender.com>, aperto dall'iPhone in Safari e aggiunto alla schermata Home. In alternativa l'app gira in locale con `start.py` ed Expo Go.
- **Codice**: ramo `cursor/garmin-app-scaffold-46f9`, PR aperta [rivadiego/rivadiego#9](https://github.com/rivadiego/rivadiego/pull/9). `main` non contiene ancora Coach Connect.
- **Stato a novembre 2026**:
  - online funzionano sito, codice di accesso, collegamento a Garmin (fatto dall'utente dal sito) e salvataggio dei dati;
  - il coach AI è ancora in modalità offline, perché il secret `GH_MODELS_TOKEN` non è stato usato in nessuna pubblicazione (vedi "Lavori aperti").

## Utente

- Parla italiano: rispondi in italiano, con frasi chiare e numeri concreti quando parli di allenamento.
- Ha un iPhone e un portatile Windows aziendale senza permessi di amministratore. Ollama non è approvato dall'IT e la rete aziendale blocca i tunnel (ngrok): **non proporre di aggirare blocchi o regole IT** (VPN spenta, tunnel alternativi, software non approvato).
- Sul portatile Python 3.12 funziona; il Node installato (20) è troppo vecchio, per questo `start.py` scarica una copia portatile.
- Il suo programma di allenamento è modellato in `backend/coach_connect/plan.py` (Workout A · Push e B · Pull a giorni alterni, RPT). I PDF originali non sono nel repository, e uno è protetto da copyright: non aggiungerli.

## Architettura

```
Orologio → Garmin Connect ──(python-garminconnect 0.3.x, token)──► backend FastAPI + SQLite
                                                                   │  scheda, regole di progressione, coach
iPhone (Safari, sito) ◄──── stesso indirizzo: sito + /api ─────────┘
                                 │
     online: Render (piano free) │ dati: dataset privato Hugging Face (backup/ripristino)
                                 │ coach AI: GitHub Models (API compatibile OpenAI), facoltativo
```

- **Backend** (`backend/coach_connect/`, Python 3.12, FastAPI, SQLite):
  - `sources.py`: sorgente Garmin reale e generatore demo; `sync.py`: sync incrementale e storico; `wellness.py`: sonno, HRV, Body Battery, readiness;
  - `workouts.py`: allenamenti registrati e feed misto; `plan.py`, `progression.py`, `planner.py`: scheda, regole RPT e carichi suggeriti;
  - `coach.py`: contesto del coach e scelta del modello: API configurata, altrimenti Ollama, altrimenti risposte offline a regole;
  - `garmin_auth.py`: login Garmin dall'app, con il codice di verifica in due passaggi (`return_on_mfa` / `resume_login`);
  - `backup.py`: database e token Garmin nel dataset privato Hugging Face;
  - `api.py`: API, sito servito da `WEB_DIR`, codice di accesso (`API_TOKEN`), limite ai codici sbagliati;
  - `cli.py`: `login`, `sync`, `status`, `serve`, `mcp`; `mcp_server.py`: server MCP per Cursor.
- **App** (`mobile/`, Expo SDK 58, Expo Router, React Native Web):
  - `src/app/(tabs)/`: Attività, Scheda, Coach; `src/app/log.tsx`: registrazione (+); `src/app/garmin.tsx`: Collega Garmin;
  - `src/components/access-gate.tsx`: richiesta del codice di accesso quando l'API risponde 401;
  - `src/lib/api.ts`: client API. Sul web l'API è sempre allo stesso indirizzo del sito; il codice di accesso sta in `localStorage`;
  - `public/index.html`: modello HTML con i meta tag per la schermata Home e uno script che legge un link `#codice=…` prima dell'avvio del router;
  - `metro.config.js`: in sviluppo inoltra `/api` al backend, così all'iPhone basta la porta 8081.
- **Locale**: `start.py` (su Windows `start.cmd`, che trova Python da solo) prepara ambienti e dipendenze, collega Garmin, accende il backend su `127.0.0.1` e Expo.
- **Cursor**: `.cursor/mcp.json` e `.cursor/rules/coach-connect.mdc`, per avere il coach dentro Cursor con i dati locali.

## Pubblicazione online

Lo fa la GitHub Action `.github/workflows/coach-connect-online.yml`, a ogni push sul ramo (o su `main`) che tocca `coach-connect/**` o il workflow stesso.

1. Il job **build** fa girare `pytest` e `npx expo export -p web`, poi salva il sito come artifact. Gira sempre, anche senza secret.
2. Il job **publish** parte solo se ci sono i secret `HF_TOKEN`, `RENDER_API_KEY` e `COACH_ACCESS_CODE`:
   - `deploy/deploy.py --stage` prepara Dockerfile, backend e sito già costruito, e il workflow li scrive (force push) nel ramo generato **`deploy/coach-connect`**;
   - `deploy/deploy.py --publish`:
     - crea il dataset privato `<utente-hf>/coach-connect-data`;
     - se c'è `GH_MODELS_TOKEN`, sceglie il modello dal catalogo di GitHub Models;
     - crea o aggiorna il servizio Render `coach-connect` (piano free, Francoforte, Docker) con le variabili d'ambiente, e lo pubblica;
     - aspetta che sia `live`, poi verifica che online ci sia la nuova build, che l'API risponda 401 senza codice e 200 con il codice, e che `POST /api/backup` salvi sul dataset.

**Secret del repository** (Settings → Secrets and variables → Actions):

| Nome | A cosa serve |
|------|--------------|
| `HF_TOKEN` | token Hugging Face "write": dataset dei dati (anche il backend lo usa) |
| `RENDER_API_KEY` | chiave API di Render per creare e aggiornare il servizio |
| `COACH_ACCESS_CODE` | codice di accesso dell'app (diventa `API_TOKEN` su Render) |
| `GH_MODELS_TOKEN` | facoltativo: token GitHub fine-grained con permesso **Models: Read-only**, per il coach AI |
| `LLM_API_KEY` + variables `LLM_BASE_URL`, `LLM_MODEL` | facoltativi: un altro servizio compatibile OpenAI, che ha la precedenza su GitHub Models |

**Variabili su Render**, impostate da `deploy.py`, che con `PUT env-vars` le sostituisce tutte: `API_TOKEN`, `HF_TOKEN`, `HF_DATA_REPO`, più `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` e `CHAT_HISTORY_MESSAGES=12` quando il coach AI è attivo. Il Dockerfile (`deploy/Dockerfile`) imposta `WEB_DIR`, `DB_PATH` e `GARMIN_TOKEN_DIR` e ascolta su `$PORT`.

**Come lavorarci**:
- Ogni push che tocca `coach-connect/**` ripubblica e **riavvia il server**. Se l'utente sta collegando Garmin, il passaggio del codice di verifica vive in memoria e andrebbe perso. Quando non vuoi ripubblicare, metti `[skip ci]` nel messaggio di commit.
- Per verificare usa i log delle Actions: `gh run list -R rivadiego/rivadiego --workflow coach-connect-online.yml` e `gh run view <id> --log`. `gh` è in sola lettura: non puoi rilanciare un workflow, ma un push lo fa partire. L'utente può premere **Re-run all jobs**. **Run workflow** compare solo quando il workflow è su `main`.
- I log delle Actions sono pubblici: stampa solo informazioni non personali, come fa già `deploy.py`.

## Dati e privacy

- Il database (`backend/data/`), `.env` e i token Garmin (`~/.garminconnect/`) sono esclusi da git e così devono restare.
- Online il disco di Render si azzera a ogni riavvio, deploy o sospensione:
  - all'avvio `backup.restore()` scarica database e token dal dataset;
  - dopo ogni richiesta che modifica dati, una copia coerente del database (backup SQLite) viene salvata qualche secondo dopo;
  - allo spegnimento (SIGTERM) viene salvata subito.
- Se il ripristino fallisce per un motivo diverso da "non c'è ancora niente", l'app **non parte** apposta: un database vuoto sovrascriverebbe quello salvato.
- Il sito è pubblico e l'indirizzo compare nei log: l'unica protezione è il codice di accesso. Il backend rifiuta con 429 i codici sbagliati oltre 30 in 10 minuti; il codice giusto passa sempre, e le richieste senza codice non contano.
- Coach AI: con GitHub Models scheda, allenamenti e parametri vitali vanno a GitHub, che nelle condizioni dei servizi AI si impegna a non usarli per addestrare i modelli. L'utente lo sa.

## Sviluppo e verifiche

```bash
cd coach-connect/backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q                 # 87 test
cd ../mobile && npm ci && npm run typecheck && npm run lint
python3 coach-connect/start.py --demo         # app completa in locale con dati finti
```

- **Rotte tipizzate**: dopo aver aggiunto una rotta in `src/app/`, avvia `expo start` una volta per rigenerare i tipi, altrimenti `tsc` segnala `router.push('/nuova')`.
- **Sito come online**: `npx expo export -p web`, poi il backend con `WEB_DIR=<dist> API_TOKEN=<codice>` (con `WEB_DIR` impostato, `API_TOKEN` è obbligatorio).
- **Prove dell'interfaccia**: in questa VM ci sono `playwright-core` in `/tmp/pw` (se la VM è stata ricreata, reinstallalo) e Google Chrome in `/usr/local/bin/google-chrome`. Usa viewport 390 × 844 per simulare un iPhone; per simulare Garmin puoi intercettare `/api/garmin/*` con `page.route`.
- **Rete della VM degli agenti cloud**: Render, Hugging Face, Garmin, GitHub Models e ngrok non sono raggiungibili; GitHub, npm e PyPI sì. Le verifiche online passano quindi dalle Actions (log) o dalle risposte dell'utente.

## Lezioni già imparate

- **Hugging Face Spaces**: dal 2026 gli Space Docker o Gradio sul piano gratuito richiedono PRO (errore 402). Restano gratuiti gli Space statici e i dataset privati, usati qui per i dati.
- **Render free**:
  - niente carta di credito, ma si sospende dopo 15 minuti senza visite (la riapertura richiede circa un minuto) e non ha disco persistente;
  - subito dopo il primo deploy ha risposto 404 sull'API per qualche istante, per questo `deploy.py` riprova il controllo per 3 minuti.
- **Garmin**: il login dai server di Render funziona (provato dall'utente). La libreria tiene lo stato del codice di verifica dentro l'istanza del client, quindi `garmin_auth.py` la conserva tra le due richieste.
- **GitHub Models (piano gratuito)**:
  - 8000 token di input per richiesta (il contesto del coach pesa circa 1800 token) e circa 50 richieste al giorno per i modelli "high" come GPT-4.1 (150 per quelli "low");
  - i nomi dei secret non possono iniziare con `GITHUB_`, per questo il secret è `GH_MODELS_TOKEN`.
- **Expo**:
  - SDK 58 vuole Node `^22.13 || ^24.3 || >=26`, ed Expo Go dell'App Store apre solo l'ultimo SDK;
  - in SDK 58 `--tunnel` senza account Expo va usato come `--tunnel ngrok` (`@expo/ngrok` è tra le dipendenze di sviluppo);
  - npm 11.19 blocca gli script di installazione non approvati: `unrs-resolver` è approvato in `allowScripts` nel `package.json`.
- **Windows**:
  - nelle cartelle OneDrive (Desktop e Documenti aziendali) rinominare file appena estratti fallisce (`WinError 5`), per questo `start.py` si rifiuta di lavorare lì e mette Node in `%LOCALAPPDATA%\coach-connect`;
  - `start.cmd` va salvato con fine riga CRLF (`.gitattributes`).

## Lavori aperti

1. **Coach AI online**: guida l'utente a creare il token fine-grained con **Models: Read-only**, salvarlo come `GH_MODELS_TOKEN` e rilanciare la pubblicazione. Nel log deve comparire "Coach AI: openai/gpt-4.1 con GitHub Models, domanda di prova ok" e "Coach: api (…)".
2. **Chest press a macchina**: l'utente ha chiesto della chest press per la massa. Aggiungere in `backend/coach_connect/exercises.py` la chest press a macchina e la versione inclinata (gruppo Petto, attrezzo `machine`), da registrare con il "+" (gliel'ho proposto, non ha ancora risposto).
3. **Check-in settimanale di peso e vita**: la scheda chiede peso e circonferenza vita una volta a settimana ("peso su e vita stabile = muscolo"). Manca una schermata per registrarli e un grafico, da passare anche al coach.
4. **Facoltativo, da chiedere all'utente**:
  - una "sveglia" che visiti il sito nelle ore del giorno, per evitare il minuto di attesa dopo la sospensione di Render (con una schedule di GitHub Actions; il piano free ha 750 ore al mese);
  - il merge della PR su `main`;
  - TestFlight (richiede l'Apple Developer Program, a pagamento).
