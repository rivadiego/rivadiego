# Coach Connect

App personale per il mio allenamento ibrido (palestra + corsa) sui dati Garmin:

- **Attività**: le corse e le attività registrate da Garmin insieme agli allenamenti di palestra registrati nell'app, con il bottone **Aggiorna**.
- **+**: registra un allenamento di palestra (esercizi, peso, ripetizioni, serie), già precompilato con i carichi della scheda.
- **Scheda**: la scheda Hybrid Athlete con il prossimo allenamento (Workout A o B) e i carichi da fare la prossima volta.
- **Coach**: chat da personal trainer che vede scheda, allenamenti e parametri vitali (sonno, HRV, Body Battery, readiness…) degli ultimi 14 giorni. Gratis con Ollama sul tuo computer, oppure dentro Cursor.

## Avvio rapido

Servono Python 3.12+ ([python.org](https://www.python.org/downloads/), consigliato 3.13; su Windows anche dal Microsoft Store), Node.js 22+ ([nodejs.org](https://nodejs.org)) e l'app **Expo Go** sull'iPhone. Poi, dalla cartella del repository:

```bash
python3 coach-connect/start.py          # con i tuoi dati Garmin (Windows: python coach-connect\start.py)
python3 coach-connect/start.py --demo   # per provare con dati finti
```

Su Windows, dopo aver installato Python o Node.js chiudi e riapri PowerShell, e quando Windows Firewall lo chiede consenti l'accesso sulle reti private: serve perché l'iPhone raggiunga il computer.

Lo script prepara backend e app, la prima volta ti chiede nome, altezza, peso e il login Garmin (con il codice di verifica se attivo), scarica attività e parametri vitali e mostra un QR code: inquadralo con la Fotocamera dell'iPhone e l'app si apre in Expo Go. iPhone e computer devono essere sulla stessa rete Wi-Fi. Ctrl+C chiude tutto; le volte successive basta rilanciare lo stesso comando.

## Come funziona

```
Orologio Garmin → app Garmin Connect (iPhone) → cloud Garmin Connect
                                                     │  python-garminconnect (token, MFA)
                                                     ▼
       backend/  Python + FastAPI ──► SQLite: attività, parametri vitali, allenamenti registrati, chat
          │  scheda + regole di progressione → carichi suggeriti
          │  coach → Ollama sul tuo computer (gratis) · server MCP per Cursor
          ▼  API HTTP
       mobile/   Expo ──► iPhone (Expo Go, poi TestFlight) · sito web
```

- **Perché un backend**: Garmin non offre API pubbliche ai privati (il Developer Program è chiuso ai nuovi richiedenti). L'accesso usa lo stesso login dell'app Garmin Connect tramite la libreria non ufficiale [`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect). I token restano sul server, mai nell'app.
- **Perché SQLite**: l'app legge dal database locale, quindi è veloce e funziona anche se Garmin è giù. Ogni attività e ogni giornata sono salvate anche con il JSON completo di Garmin.
- **Sync**: la prima volta importa tutto lo storico, poi ogni "Aggiorna" legge solo le novità e i parametri vitali dei giorni non ancora chiusi (di solito 5-6 richieste).
- **Feed misto**: se registri un allenamento nell'app e l'orologio ha registrato la stessa sessione di forza, compaiono come una sola card con le tue serie più FC, durata e calorie dell'orologio.

## Provala subito in modalità demo

Non serve l'account Garmin: dati finti che seguono la settimana della scheda, con allenamenti di palestra che progrediscono secondo le regole RPT.

Requisiti: Python 3.12+, Node.js 22+, l'app **Expo Go** sull'iPhone (App Store).

```bash
# Terminale 1: backend
cd coach-connect/backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m coach_connect serve --demo

# Terminale 2: app
cd coach-connect/mobile
npm install
npx expo start
```

- **iPhone**: inquadra il QR code con la Fotocamera e si apre in Expo Go. iPhone e computer devono stare sulla stessa rete Wi-Fi; quando Expo Go chiede l'accesso alla **rete locale**, consentilo. L'app trova da sola il backend sul computer (porta 8000).
- **Browser**: premi `w` nel terminale di Expo.

## Collega il tuo account Garmin

```bash
cd coach-connect/backend
source .venv/bin/activate
cp .env.example .env           # poi compila nome, altezza, peso e (se vuoi) il coach AI
python -m coach_connect login  # email, password e codice MFA (se attivo)
python -m coach_connect sync   # la prima volta importa tutto lo storico: può richiedere qualche minuto
python -m coach_connect serve  # senza --demo
```

- La password non viene salvata: in `~/.garminconnect/garmin_tokens.json` finiscono solo i token, che si rinnovano da soli. Se un giorno scadono, l'app mostra "Garmin non collegato": basta rifare `login`.
- Non scrivere la password in chat o nel repository. Per un login non interattivo (per esempio un agente Cursor nel cloud), `login` legge `GARMIN_EMAIL` e `GARMIN_PASSWORD` dall'ambiente: in Cursor vanno nei Secrets (Dashboard → Cloud Agents → Secrets).
- `python -m coach_connect status` mostra token, numero di attività e ultimo sync.
- È un'API non ufficiale: se Garmin cambia il login (è successo a marzo 2026) può smettere di funzionare finché la libreria non si aggiorna (`pip install -U garminconnect`). I dati già scaricati restano nel database.

## La scheda e i carichi suggeriti

La scheda è in `backend/coach_connect/plan.py`: Workout A (Push) e B (Pull) a giorni alterni, con circuito addominali, regole e alimentazione. Non ci sono settimane né date da impostare: il prossimo allenamento è sempre l'opposto dell'ultimo registrato, quindi una sessione saltata non sballa nulla. Il backend calcola i carichi della prossima volta con le regole della scheda:

- **RPT**: la prima serie è la più pesante, poi −10% del carico di punta a ogni serie; quando chiudi tutte le ripetizioni, +1,25 kg (+2 kg sui manubri).
- **Complementari**: si sale quando arrivi al massimo del range in tutte le serie.
- **Chin-up zavorrati**: il 10% si calcola su peso corporeo + zavorra (peso da Garmin o `ATHLETE_WEIGHT_KG`).
- **Riscaldamento** prima del primo esercizio: 50% × 5, 75% × 3, 90% × 1.

## Il coach nell'app (gratis con Ollama)

Ogni domanda arriva al modello insieme a un riepilogo calcolato dal backend: scheda, prossimo allenamento, ultimi 7 giorni rispetto all'obiettivo (3 palestra + 2 corse), parametri vitali degli ultimi 14 giorni, attività e serie registrate, e i carichi già calcolati con le regole della scheda. Le conversazioni restano salvate nel database; "Nuova chat" ricomincia da zero.

1. Installa [Ollama](https://ollama.com) sul computer dove gira il backend (Mac, Windows o Linux). Nessun account.
2. Scarica un modello: `ollama pull qwen3:8b` con 16 GB di RAM, oppure `ollama pull qwen3:4b` con 8 GB.
3. Fine: il backend trova da solo Ollama e il modello installato, e nella tab Coach compare "Coach AI locale".

- I dati non escono dal tuo computer. Su un portatile senza scheda video la risposta può richiedere 10-60 secondi.
- Per scegliere un modello preciso imposta `OLLAMA_MODEL` in `backend/.env`.
- Senza Ollama il coach è in modalità offline: risponde con regole automatiche (carichi, recupero, riepilogo della settimana) usando i tuoi dati.
- In alternativa, a pagamento: un servizio compatibile con le API OpenAI (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`); in quel caso i dati vengono inviati al provider.

## Il coach in Cursor (MCP)

Il repository contiene `.cursor/mcp.json`, che avvia `python -m coach_connect mcp`: un server MCP con i tuoi dati (contesto per il coach, prossimo allenamento con i carichi, parametri vitali, attività, dettaglio allenamenti). Così puoi chiedere a Cursor, per esempio, "che carichi faccio oggi?" o "com'è andata la settimana?", usando il tuo account Cursor senza altre chiavi.

1. Installa il backend come sopra (serve `coach-connect/backend/.venv`).
2. Apri il repository con Cursor e attiva `coach-connect` in **Cursor Settings → Tools & MCP**.
3. Chiedi in chat. La regola `.cursor/rules/coach-connect.mdc` fa rispondere l'agente come un personal trainer.

- Su Windows cambia `command` in `.cursor/mcp.json` con `${workspaceFolder}/coach-connect/backend/.venv/Scripts/python.exe`.
- Per provarlo con i dati demo aggiungi `"--demo"` agli `args`.
- Funziona in Cursor sul computer dove c'è il database, non negli agenti cloud di cursor.com/agents.

## Usarla sull'iPhone

| Modo | Costo | Com'è |
|------|-------|-------|
| **Expo Go** | gratis | Per lo sviluppo: l'app gira finché sul computer sono accesi `npx expo start` e il backend. |
| **TestFlight** | Apple Developer Program, 99 $/anno | App vera con icona, sempre disponibile. La build si fa nel cloud con EAS (`npx eas-cli@latest build -p ios`, poi `submit`): non serve un Mac. Richiede il backend raggiungibile in HTTPS. |
| **Sito web (PWA)** | gratis | `npx expo export -p web` genera `mobile/dist/`, da pubblicare su Netlify, Vercel o Cloudflare Pages. Su Safari: Condividi → "Aggiungi alla schermata Home". |

Widget, HealthKit e notifiche push richiedono la build installata (TestFlight), non Expo Go.

### Backend sempre acceso

Per usare l'app fuori casa il backend deve restare raggiungibile:

- **Tailscale** (consigliato all'inizio): backend su un computer di casa (o un Raspberry Pi), iPhone nella stessa rete Tailscale. Niente esposto su internet, HTTPS con `tailscale serve`.
- **Cloud** (Fly.io, Railway, un piccolo VPS): imposta `API_TOKEN` e HTTPS. Conviene fare il `login` da casa e copiare sul server la cartella dei token.

Poi nell'app imposta `EXPO_PUBLIC_API_URL` (ed `EXPO_PUBLIC_API_TOKEN`) in `mobile/.env.local`.

## Configurazione

`backend/.env` (parti da `backend/.env.example`, dove ogni variabile è spiegata):

| Variabile | Default | A cosa serve |
|-----------|---------|--------------|
| `GARMIN_DEMO` | `0` | `1` = dati finti (database separato `data/demo.db`) |
| `GARMIN_TOKEN_DIR` | `~/.garminconnect` | Cartella dei token, fuori dal repo |
| `API_TOKEN` | vuoto | Se impostato, l'app deve mandare `Authorization: Bearer <token>` |
| `ATHLETE_NAME`, `ATHLETE_HEIGHT_CM`, `ATHLETE_WEIGHT_KG` | vuoti | Profilo per il coach e peso per i chin-up zavorrati |
| `WELLNESS_DAYS` / `WELLNESS_MAX_DAYS_PER_SYNC` | `14` / `6` | Giorni di parametri vitali per il coach e giorni mancanti scaricati per ogni "Aggiorna" |
| `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX` | `http://localhost:11434`, vuoto, `8192` | Coach gratuito con Ollama (modello vuoto = il primo installato) |
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | OpenAI, vuoti | Alternativa a pagamento; se impostata ha la precedenza |
| `SYNC_PAGE_SIZE` / `SYNC_MAX_PAGES` | `50` / `20` | Attività per richiesta e richieste massime per ogni "Aggiorna" |

`mobile/.env.local` (parti da `mobile/.env.example`): `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_API_TOKEN`.

## API

| Metodo | Percorso | Cosa fa |
|--------|----------|---------|
| `POST` | `/api/sync` | Scarica attività e parametri vitali da Garmin |
| `GET` | `/api/feed` | Attività Garmin e allenamenti registrati, dal più recente |
| `GET` | `/api/plan` | Scheda, prossimo allenamento (A o B), ultimo fatto e carichi suggeriti |
| `GET` | `/api/exercises` | Catalogo esercizi |
| `POST` / `GET` / `DELETE` | `/api/workouts`, `/api/workouts/{id}` | Registra, leggi, elimina un allenamento |
| `GET` | `/api/wellness?days=14` | Parametri vitali giornalieri |
| `GET` / `POST` / `DELETE` | `/api/chat` | Conversazione con il coach |
| `GET` | `/api/activities`, `/api/status` | Solo attività Garmin; stato del collegamento |

Documentazione interattiva: <http://localhost:8000/docs>.

## Struttura

```
coach-connect/
├── backend/
│   ├── coach_connect/
│   │   ├── sources.py      # Garmin Connect reale e generatore demo
│   │   ├── sync.py         # sync incrementale, storico, parametri vitali
│   │   ├── wellness.py     # sonno, HRV, Body Battery, readiness…
│   │   ├── workouts.py     # allenamenti registrati e feed misto
│   │   ├── plan.py         # la scheda come dati
│   │   ├── progression.py  # regole di progressione (RPT, complementari, zavorra)
│   │   ├── planner.py      # prossimo allenamento e carichi suggeriti
│   │   ├── coach.py        # chat: contesto, Ollama, risposte offline
│   │   ├── mcp_server.py   # server MCP per Cursor
│   │   ├── exercises.py    # catalogo esercizi
│   │   ├── api.py          # API FastAPI
│   │   └── cli.py          # login · sync · status · serve · mcp
│   └── tests/
└── mobile/
    └── src/
        ├── app/(tabs)/     # Attività · Scheda · Coach
        ├── app/log.tsx     # registra allenamento (+)
        ├── app/workout/    # dettaglio allenamento registrato
        ├── components/     # card, editor esercizi, selettore, chat…
        └── lib/            # client API, formattazione, bozza allenamento
```

## Test

```bash
cd coach-connect/backend && pip install -r requirements-dev.txt && pytest
cd coach-connect/mobile && npx tsc --noEmit && npx expo lint
```

## Privacy

Questo repository è **pubblico** su GitHub: il codice è visibile a tutti, i tuoi dati no. `.env`, `backend/data/` (database con attività, parametri vitali, allenamenti e chat) e i token sono esclusi da git: non aggiungerli a mano. Con Ollama anche il coach resta sul tuo computer. Il PDF del Greek God Program è protetto da copyright e va tenuto solo in locale.
