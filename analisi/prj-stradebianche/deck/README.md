# Deck «Cantiere Salvezza» — catena di generazione

Script di editing del deck *Project Strade Bianche — Focus su gestione pre-settlement e transitorio
OPAS*. Le modifiche non sono fatte a mano sul file: sono descritte in due script `python-pptx`
eseguiti in sequenza sul deck originale, così che ogni versione sia riproducibile e la lista degli
interventi resti tracciata.

## Catena

```bash
pip install python-pptx lxml
python3 build_v2.py   # source/…_a238.pptx  →  output/…_v2.pptx
python3 build_v3.py   # output/…_v2.pptx    →  output/…_v3.pptx
```

Ogni script stampa a fine esecuzione l'elenco degli interventi applicati. `output/…_v3.pptx` è la
versione finale; l'intermedia `_v2` è rigenerabile e non è versionata.

### `build_v2.py` — dal deck originale alla v2

- **slide 13** — fascia «Filone trasversale»: action plan sulle prescrizioni regolamentari da
  completare entro 6 mesi dal settlement.
- **slide 16 (nuova)** — «3. Transitorio | Quattro principi guida orientano la gestione del periodo
  transitorio», su tre colonne (principio / cosa vuol dire / implicazioni).
- **slide 17** — «Policy: definizione…» → «attivazione…, definite nel pre-settlement»; la nota sul
  setup della macchina di integrazione è spostata al pre-settlement.
- **slide 18** — Consumer finance/Compass → TBD con nota sul possibile veicolo per il carve-out;
  Leasing/Factoring → Banca dei Territori (S. Barrese).
- **slide 2 (Agenda)** — allineamento definizione/attivazione e nuovo bullet sul setup della macchina
  di integrazione.

### `build_v3.py` — dalla v2 alla v3

- **slide 8** — nota sull'ampliamento della casistica delle dimissioni CEO/CdA (scenari intermedi fra
  i due estremi rappresentati), da chiudere a valle della call con i legali.
- **slide 19 (nuova)** — vista per legal entity su tre colonne (perimetro / contenuto e attività /
  proposta di presidio al Day 1), complementare alla slide gemella 18 che rappresenta gli stessi
  perimetri a schede. Le celle con assegnazione ancora aperta sono evidenziate in arancio.

## Convenzioni del template

Ricavate dalle slide native e replicate nelle slide generate, per non far «stonare» le aggiunte:

| Elemento | Convenzione |
| --- | --- |
| Titolo | `l=1.54 w=30.78`, 21,4–22 pt, capitolo in arancio (tema `accent2`) e resto in blu |
| Sottotitolo | 12 pt, subito sotto al titolo |
| Banda «ESEMPIO ILLUSTRATIVO» | piena larghezza, `h=0.61`, 11 pt bold bianco su arancio |
| Marcatore «PER DISCUSSIONE» | testo sottolineato con evidenziatore giallo, non riquadro |
| Font | Century Gothic; blu `003A79`, arancio `F18B40`, azzurro `C0CCE4` |

Il deck ha **due master**: le slide del capitolo 3 sui perimetri usano il layout `2_DEFAULT` del
secondo master, che non ha il numero di pagina in alto a destra e tiene logo e note a piè di pagina a
`t=17.44`. La slide 19 è costruita su quel layout per essere coerente con la gemella.

## Verifica

Le slide toccate sono state verificate a video convertendo il deck in PDF e rasterizzando le pagine:

```bash
soffice --headless --convert-to pdf output/20260918_SB_Cantiere_Salvezza_vONLINE_v3.pptx
pdftoppm -f 18 -l 18 -r 110 -png 20260918_SB_Cantiere_Salvezza_vONLINE_v3.pdf slide
```

Attenzione alla numerazione: la slide 7 è nascosta, quindi dalla slide 8 in poi la pagina PDF è pari
al numero di slide meno uno (la slide 19 è la pagina 18).
