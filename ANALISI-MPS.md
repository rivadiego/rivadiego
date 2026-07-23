# MPS sotto assedio: Intesa vs Banco BPM

> **Come vedere questa pagina in Cursor:** apri questo file → tasto destro → **Open Preview** (oppure `Ctrl+Shift+V` / `Cmd+Shift+V`)

![Mappa operazioni MPS](mps-deal-map.png)

---

## Situazione (23 lug 2026)

| Operazione | Data | Struttura |
|---|---|---|
| **OPAS Intesa** | 8 giu 2026 | 1,6 azioni ISP + €1 cash per azione MPS |
| **Fusione BPM** | 7 giu 2026 | Merger of equals, concambio 0,75–0,77 BPM/MPS |

- CDA MPS: **bocciatura preliminare** OPAS Intesa
- Proposta BPM: **in valutazione**

---

## Mappa delle operazioni

```mermaid
flowchart TB
    ISP["Intesa Sanpaolo<br/>€111 mld"]
    BPM["Banco BPM<br/>€23,3 mld"]
    MPS["Monte dei Paschi<br/>€33,5 mld · TARGET"]
    GEN["Generali<br/>€53,5 mld"]
    CA["Crédit Agricole<br/>29,3% BPM"]
    MB["Mediobanca"]

    ISP -->|"OPAS · €11,14/az<br/>1,6 ISP + €1"| MPS
    BPM -->|"Fusione · €11,72/az<br/>0,76 BPM/MPS"| MPS
    GEN -.->|"~13% via"| MB
    MB -.-> MPS
    CA -.-> BPM

    style MPS fill:#c62828,color:#fff
    style ISP fill:#00855a,color:#fff
    style BPM fill:#1565c0,color:#fff
    style GEN fill:#b71c1c,color:#fff
```

---

## Corrispettivo per azione MPS

Prezzi al **15 lug 2026**: ISP €6,34 · MPS €11,41 · BPM €15,42

| Scenario | Valore | vs mercato |
|---|---:|---:|
| Prezzo di mercato | **€11,41** | — |
| OPAS Intesa | **€11,14** | **-2,4%** |
| Fusione BPM (0,76) | **€11,72** | **+2,7%** |

```mermaid
xychart-beta
    title "Corrispettivo implicito €/azione MPS"
    x-axis ["Mercato", "Intesa OPAS", "BPM Fusione"]
    y-axis "Euro" 10.8 --> 12.0
    bar [11.41, 11.14, 11.72]
```

---

## Verdetto per azionista MPS

| | Intesa OPAS | BPM Fusione |
|---|---|---|
| **Corrispettivo** | €11,14 (-2,4%) | €11,72 (+2,7%) |
| **Brand MPS** | Perso (~635 filiali → Unipol) | Preservato |
| **Sinergie/anno** | €2,9 mld (2029) | €1,1 mld |
| **Generali** | A concorrente (Intesa vita) | Asset strategico nel gruppo |
| **Rischio** | Medio-alto (antitrust, DC) | Medio (assenso CA) |
| **Verdetto** | Neutro / leggermente negativo | **Preferibile se ≥0,76** |

---

## Scorecard (1–10) — azionisti MPS

```mermaid
---
config:
  themeVariables:
    quadrantPointFill: '#00855a'
---
quadrantChart
    title Scorecard comparativa
    x-axis Basso --> Alto
    y-axis Basso --> Alto
    quadrant-1 Leader
    quadrant-2 Upside
    quadrant-3 Debole
    quadrant-4 Rischio
    Intesa OPAS: [0.55, 0.75]
    BPM Fusione: [0.65, 0.55]
```

| Dimensione | Intesa | BPM |
|---|:---:|:---:|
| Corrispettivo | 5 | **7** |
| Upside industriale | **8** | 5 |
| Preservazione identità | 4 | **9** |
| Rischio esecuzione | 7 | 6 |
| Governance | 5 | **7** |

---

## Generali (~13% via Mediobanca)

| Scenario Intesa | Scenario BPM |
|---|---|
| Controllo Generali + 3,01% diretto | Quota resta nel nuovo gruppo |
| Danish Compromise (+60–70 bp CET1) | CET1 pro-forma ~16% |
| Generali finisce a **concorrente** | Partner bancassicurazione: **Crédit Agricole** |
| Approvazione regolamentare incerta | Nessuno smembramento |

---

## Versione interattiva (browser in Cursor)

Se vuoi la versione **animata con canvas**:

1. `Ctrl+Shift+P` / `Cmd+Shift+P`
2. Cerca **Simple Browser: Show**
3. Incolla: `http://localhost:8765/mps-deal-comparison.html`

*(Il server locale parte automaticamente quando apri il workspace — vedi sotto)*

---

*Analisi a scopo informativo, non consulenza finanziaria.*
