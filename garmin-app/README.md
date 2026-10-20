# Garmin Hub

App personale sui miei dati Garmin. Per ora: la lista delle attività con un bottone **Aggiorna** che scarica le novità da Garmin Connect. È la base su cui costruire dashboard, piano di allenamento e coach con chat.

## Come funziona

```
Orologio Garmin → app Garmin Connect (iPhone) → cloud Garmin Connect
                                                     │  python-garminconnect (token, MFA)
                                                     ▼
                              backend/  Python + FastAPI ──► SQLite (backend/data/garmin.db)
                                                     │  API HTTP (/api/activities, /api/sync)
                                                     ▼
                              mobile/   Expo ──► iPhone (Expo Go, poi TestFlight) · sito web
```

- **Perché un backend**: Garmin non offre API pubbliche ai privati (il Developer Program è chiuso ai nuovi richiedenti). L'accesso usa lo stesso login dell'app Garmin Connect tramite la libreria non ufficiale [`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect). I token restano sul server, mai nell'app.
- **Perché SQLite**: l'app legge dal database locale, quindi è veloce e funziona anche se Garmin è giù. Ogni attività è salvata anche con il JSON completo di Garmin, base per analisi e chat future senza riscaricare nulla.
- **Sync**: la prima volta importa tutto lo storico, poi ogni "Aggiorna" legge solo le attività nuove (di solito 1-2 richieste).

## Provala subito in modalità demo

Non serve l'account Garmin: i dati sono finti ma seguono la settimana della scheda Hybrid Athlete.

Requisiti: Python 3.12+, Node.js 22+, l'app **Expo Go** sull'iPhone (App Store).

```bash
# Terminale 1: backend
cd garmin-app/backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m garmin_hub serve --demo

# Terminale 2: app
cd garmin-app/mobile
npm install
npx expo start
```

- **iPhone**: inquadra il QR code con la Fotocamera e si apre in Expo Go. iPhone e computer devono stare sulla stessa rete Wi-Fi; quando Expo Go chiede l'accesso alla **rete locale**, consentilo. L'app trova da sola il backend sul computer (porta 8000).
- **Browser**: premi `w` nel terminale di Expo.

## Collega il tuo account Garmin

```bash
cd garmin-app/backend
source .venv/bin/activate
python -m garmin_hub login     # email, password e codice MFA (se attivo)
python -m garmin_hub sync      # la prima volta importa tutto lo storico: può richiedere qualche minuto
python -m garmin_hub serve     # senza --demo
```

- La password non viene salvata: in `~/.garminconnect/garmin_tokens.json` finiscono solo i token, che si rinnovano da soli. Se un giorno scadono, l'app mostra "Garmin non collegato": basta rifare `login`.
- `python -m garmin_hub status` mostra token, numero di attività e ultimo sync.
- È un'API non ufficiale: se Garmin cambia il login (è successo a marzo 2026) può smettere di funzionare finché la libreria non si aggiorna (`pip install -U garminconnect`). I dati già scaricati restano nel database.

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

`backend/.env` (parti da `backend/.env.example`):

| Variabile | Default | A cosa serve |
|-----------|---------|--------------|
| `GARMIN_DEMO` | `0` | `1` = dati finti (database separato `data/demo.db`) |
| `GARMIN_TOKEN_DIR` | `~/.garminconnect` | Cartella dei token, fuori dal repo |
| `DB_PATH` | `data/garmin.db` | Database SQLite |
| `API_TOKEN` | vuoto | Se impostato, l'app deve mandare `Authorization: Bearer <token>` |
| `CORS_ORIGINS` | `*` | Origini ammesse per la versione web |
| `SYNC_PAGE_SIZE` / `SYNC_MAX_PAGES` | `50` / `20` | Attività per richiesta e richieste massime per ogni "Aggiorna" |

`mobile/.env.local` (parti da `mobile/.env.example`): `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_API_TOKEN`.

## API

| Metodo | Percorso | Cosa fa |
|--------|----------|---------|
| `GET` | `/api/status` | Modalità, token Garmin presenti, numero di attività, ultimo sync |
| `GET` | `/api/activities?limit=50&offset=0&sport=run` | Attività dalla più recente (`sport`: run, bike, swim, walk, hike, strength, cardio, …) |
| `POST` | `/api/sync` | Scarica le novità da Garmin |

Documentazione interattiva: <http://localhost:8000/docs>.

## Struttura

```
garmin-app/
├── backend/
│   ├── garmin_hub/
│   │   ├── sources.py     # Garmin Connect reale e generatore demo
│   │   ├── sync.py        # sync incrementale e recupero dello storico
│   │   ├── db.py          # SQLite: attività + JSON Garmin completo
│   │   ├── normalize.py   # tipi Garmin → categorie (corsa, forza, …)
│   │   ├── api.py         # API FastAPI
│   │   └── cli.py         # login · sync · status · serve
│   └── tests/
└── mobile/
    └── src/
        ├── app/index.tsx  # schermata attività
        ├── components/    # card, bottone Aggiorna, banner, stati vuoti
        └── lib/           # client API, formattazione, sport
```

## Test

```bash
cd garmin-app/backend && pip install -r requirements-dev.txt && pytest
cd garmin-app/mobile && npx tsc --noEmit && npx expo lint
```

## Privacy

Questo repository è **pubblico**. `.env`, `backend/data/` e i token sono già esclusi da git: non aggiungerli a mano. Quando entreranno scheda, note, peso e chat, conviene spostare il progetto in un repository privato. Il PDF del Greek God Program è protetto da copyright e va tenuto solo in locale.
