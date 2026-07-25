# Investment Portfolio Tracker

Workbook Excel professionale per il monitoraggio del portafoglio multi-conto, basato esclusivamente su formule moderne (Microsoft 365).

## File

| File | Descrizione |
|------|-------------|
| `Portfolio_Tracker.xlsx` | Workbook pronto all'uso |
| `build_workbook.py` | Script di rigenerazione |
| `source/` | Estratti originali usati per popolare i dati iniziali |

## Conti configurati (da estratti reali)

| Conto | Fonte |
|-------|-------|
| **Barclays ISA** | `LoadDocstore.xls` — ID1901366-001 (Gabriele Palmieri) |
| **Intesa Sanpaolo** | Conferma operazioni 14/07/2026 — Dep. 06793 3100 03022395 |

## Struttura

| Foglio | Ruolo |
|--------|-------|
| **Config** (nascosto) | Registro conti (`tblAccounts`) + liste validazione |
| **Summary** | Vista consolidata stile report istituzionale |
| **Barclays ISA / Intesa Sanpaolo** | Report per conto + Master Investment Table |

## Design

Layout ispirato a report bancari istituzionali (Barclays-style):

- Header navy con titolo report
- **Portfolio Snapshot** — NAV, capitale investito, P/L, cash, income
- **Performance Breakdown by Asset Class** — market value, peso, cost basis, unrealized/realized, income, posizioni aperte
- **Performance by Reporting Period** — MTD, QTD, YTD, anno precedente, since inception (in parallelo)
- **Account Overview** — breakdown per conto con pesi

Ogni foglio conto replica la stessa struttura, filtrando sulla propria tabella master.

## Flusso dati

```
Config (tblAccounts)
    ↓
Summary ← aggrega via formule da tutte le tab tbl_<Conto>
    ↓
Foglio conto ← KPI filtrati da tbl_<Conto> locale (switcher Period / Asset Class)
    ↓
Master Investment Table ← unica fonte dati (input manuale)
```

## Manutenzione

1. **Prezzi** — aggiornare `Current Price`
2. **Nuovi investimenti** — nuova riga nella tabella master (espansione automatica)
3. **Chiusure** — compilare `Sale Date`, `Sale Price`, `Sale Fees`
4. **Redditi** — importi + `Income Date` per filtri temporali
5. **FX** — colonna `FX to EUR` per posizioni in GBP/USD (Barclays ISA)

### Aggiungere un conto

1. Aggiungere il nome in `tblAccounts` (Config)
2. Duplicare un foglio conto esistente
3. Rinominare il foglio **esattamente** come in Config
4. Cancellare i dati esempio — Summary si aggiorna da sola

## Requisiti

Microsoft 365 con array dinamici: `LET`, `FILTER`, `BYROW`, `LAMBDA`, `SWITCH`, `INDIRECT`.

## Rigenerare

```bash
pip install -r requirements.txt
python build_workbook.py
```

## Note sui dati Barclays

L'estratto XLS originale era parzialmente corrotto; posizioni e ISIN sono stati importati, ma **prezzi, quantità e FX vanno verificati/aggiornati** dall'estratto completo in Barclays Online Banking.
