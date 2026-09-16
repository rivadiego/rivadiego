# Knowledge base — Prj Stradebianche / OPAS Intesa Sanpaolo su MPS

## Front matter

**Scopo del documento.** Questo file è la base di conoscenza da fornire come input contestuale a un
agente AI che debba lavorare sul dossier "Prj Stradebianche". Non è un memo per un lettore umano che
segue un ragionamento: è organizzato per il consumo da parte di un agente, con separazione strutturale
fra ciò che è accertato, ciò che è concluso per via analitica e ciò che resta aperto.

**Data di riferimento: 16 settembre 2026.** Tutte le affermazioni fattuali sono riferite a questa data.

**Perimetro.** Analisi degli scenari alternativi (*what-if*) rispetto alle due assunzioni implicite
della timeline di integrazione post-OPAS: (a) il raggiungimento della soglia del 90% che apre lo
squeeze-out e quindi il delisting; (b) le dimissioni volontarie del Consiglio di Amministrazione della
target subito dopo il settlement. Non rientrano nel perimetro: la valutazione del corrispettivo, il
merito industriale dell'operazione, la modellistica finanziaria.

**Documento di dettaglio collegato.** `analisi/prj-stradebianche/nodi-what-if-timeline-opas.md` nello
stesso repository contiene la trattazione estesa, con il ragionamento completo e l'apparato di fonti.
Questo file ne è la riorganizzazione per uso agentico, non un duplicato.

### Istruzioni d'uso per l'agente destinatario

1. **Rispetta la tripartizione.** La Parte I contiene fatti verificati su fonte primaria o su fonte
   secondaria affidabile, con l'indicazione della fonte. La Parte II contiene conclusioni analitiche:
   sono difendibili ma sono ragionamenti, non fatti, e vanno presentate come tali. La Parte III elenca
   ciò che non è stato verificato: **non trattare quei punti come acquisiti** e non costruirci sopra
   raccomandazioni operative senza averli prima riscontrati.
2. **La data di riferimento è il 16 settembre 2026.** L'operazione è in corso e diversi elementi sono
   in movimento: l'approvazione Consob del documento di offerta, l'istruttoria AGCM, le autorizzazioni
   BCE, la delibera Consob di attuazione della riforma del TUF, l'assemblea MPS del 29 ottobre 2026.
   Qualsiasi informazione successiva a questa data **va cercata, non assunta**. Se ti trovi a operare
   in una data successiva, verifica per prima cosa lo stato di questi cinque procedimenti.
3. **Non ricalcolare da zero le conclusioni consolidate.** Le analisi della Parte II sono il prodotto
   di un lavoro di ricerca già svolto. Usale come punto di partenza e concentra lo sforzo sui punti
   aperti della Parte III e su ciò che il tuo compito specifico richiede in più.
4. **Materiale riservato, a uso interno.** Non diffondere, non pubblicare, non citare all'esterno. Non
   interagire con soggetti terzi (emittenti, autorità, controparti) sulla base di questo materiale.
5. **Attenzione alla distinzione fra soglie.** Nel dossier ricorrono quattro numeri diversi che è
   facile confondere: 30% (soglia OPA obbligatoria), 66,67% (Condizione Soglia dell'offerta e
   maggioranza per la fusione), 90% (squeeze-out e sell-out da flottante, **soglia nuova dal 2026**),
   95% (sell-out pieno ex art. 108 c. 1, soglia residua). Verifica sempre a quale ti stai riferendo.

---

## Glossario

### Soggetti

| Sigla | Denominazione | Ruolo nel dossier |
|---|---|---|
| **ISP** | Intesa Sanpaolo S.p.A. | Offerente. Banca quotata su Euronext Milan, *significant institution* vigilata BCE, già conglomerato finanziario |
| **MPS** / BMPS | Banca Monte dei Paschi di Siena S.p.A. | Emittente / target. Banca quotata su Euronext Milan, sede in Siena |
| **MB** | Mediobanca – Banca di Credito Finanziario S.p.A. | Controllata di MPS all'86,348%, ancora quotata; in corso la fusione per incorporazione in MPS |
| **AG** | Assicurazioni Generali S.p.A. | Partecipata al 13,2-13,3% tramite MB; nodo prudenziale dell'operazione (Danish Compromise) |
| **Unipol** | Unipol Assicurazioni S.p.A. | Acquirente del compendio oggetto del rimedio antitrust; detiene poco meno del 30% di BPER |
| **Delfin** | Delfin S.à r.l. | Primo azionista MPS (17,53%) |
| **AGCM** | Autorità Garante della Concorrenza e del Mercato | Antitrust italiana; istruttoria approfondita aperta il 14 settembre 2026 |
| **Consob** | Commissione Nazionale per le Società e la Borsa | Autorità di vigilanza sui mercati; approva il documento di offerta |
| **BCE** | Banca Centrale Europea | Vigilanza prudenziale diretta su ISP e MPS |
| **MEF** | Ministero dell'Economia e delle Finanze | Azionista MPS al 4,86%, posizione dichiarata neutrale |

### Termini tecnici

| Termine | Significato |
|---|---|
| **OPAS** | Offerta pubblica di acquisto e scambio: offerta con corrispettivo misto in titoli e denaro |
| **Squeeze-out** (diritto di acquisto) | Diritto dell'offerente di acquistare coattivamente i titoli residui, art. 111 TUF. Soglia **90%** dal 2026 |
| **Sell-out** (obbligo di acquisto) | Obbligo dell'offerente di comprare da chi ne faccia richiesta: art. 108 c. 1 TUF sopra il 95%; art. 108 c. 2 TUF sopra il 90%, salvo ripristino del flottante entro 90 giorni |
| **Procedura congiunta** | Procedura unica, concordata con Consob e Borsa Italiana, con cui si esercitano insieme il diritto di acquisto ex art. 111 e l'obbligo di acquisto ex art. 108, con esito il delisting |
| **Riapertura dei termini** | Riapertura del periodo di adesione per 5 giorni di borsa aperta dopo la data di pagamento, art. 40-bis Reg. Emittenti |
| **Condizione Soglia** | Condizione di efficacia dell'offerta legata al raggiungimento di una percentuale minima di adesioni; nel caso di specie 66,67%, rinunciabile |
| **Passivity rule** | Divieto per gli organi dell'emittente di compiere atti che contrastino gli obiettivi dell'offerta senza autorizzazione assembleare, art. 104 TUF; opera durante l'offerta |
| **Prorogatio** | Permanenza in carica degli amministratori dimissionari fino alla ricostituzione dell'organo, art. 2385 c.c. **Non si applica alla revoca** |
| **Simul stabunt simul cadent** | Clausola statutaria per cui la cessazione di alcuni amministratori determina la cessazione dell'intero consiglio |
| **Voto di lista** | Meccanismo obbligatorio di nomina degli organi nelle società quotate, art. 147-ter TUF, con riserva di seggi alle minoranze |
| **OPC** | Operazioni con parti correlate, disciplinate dal Regolamento Consob 17221/2010 e dall'art. 2391-bis c.c. |
| **Danish Compromise** | Regime prudenziale che consente di non dedurre dal CET1 le partecipazioni assicurative, ponderandole, previa autorizzazione dell'autorità competente: art. 49 CRR |
| **CET1** | *Common Equity Tier 1*, capitale primario di classe 1 |
| **RWA** | *Risk-weighted assets*, attività ponderate per il rischio |
| **Minority interests** | Interessi di terzi nel capitale di una controllata consolidata; riconoscimento limitato nel CET1 consolidato, artt. 81-88 CRR |
| **MREL** | Requisito minimo di fondi propri e passività ammissibili ai fini della risoluzione |
| **PPA** | *Purchase price allocation*, allocazione del prezzo di acquisizione, IFRS 3 |
| **Carve-out** | Estrazione di un perimetro aziendale da un'entità, in vista di una cessione o di una riorganizzazione |
| **Divestiture trustee** | Fiduciario nominato quando l'impegno di cessione antitrust non è eseguito nei termini; vende senza vincolo di prezzo minimo |

### Riferimenti normativi ricorrenti

| Norma | Contenuto rilevante |
|---|---|
| **D.Lgs. 58/1998 (TUF)** | Testo unico della finanza |
| **D.Lgs. 27 marzo 2026 n. 47** | Riforma organica del TUF in attuazione della L. 21/2024 "Legge Capitali"; in vigore dal 29 aprile 2026 |
| Art. 102 TUF | Comunicazione dell'intenzione di promuovere un'offerta; c. 8: *put up or shut up* |
| Art. 104 TUF | Passivity rule |
| Art. 106 TUF | OPA obbligatoria; soglia unica del 30%; c. 3 lett. b) OPA da consolidamento, innalzata al 10% |
| Art. 108 TUF | Obbligo di acquisto; c. 1 (95%), c. 2 (90% e flottante), cc. 3-4 (corrispettivo), c. 5 (forma del corrispettivo) |
| Art. 111 TUF | Diritto di acquisto; soglia portata al 90% dal D.Lgs. 47/2026 |
| Art. 112-bis TUF | Acquisto totalitario su autorizzazione dei soci; nuovo, attuazione Consob attesa entro il 29 aprile 2027 |
| Art. 125-bis TUF | Termini di convocazione dell'assemblea: 30 giorni, **40 giorni** per l'elezione degli organi con voto di lista |
| Art. 126-bis TUF | Integrazione dell'ordine del giorno da parte dei soci (un quarantesimo del capitale) |
| Art. 133 c. 1-bis TUF | Down-listing su MTF; nuovo, stessa attuazione attesa al 29 aprile 2027 |
| Art. 147-ter TUF | Voto di lista: deposito delle liste 25 giorni prima, riserva alle minoranze, quota di genere |
| Art. 147-ter.1 TUF | Lista del consiglio di amministrazione uscente; introdotto dalla L. 21/2024, attuato dalla Delibera Consob 23725/2025 |
| Art. 151 e 151.1 TUF | Poteri dell'organo di controllo; convocazione dell'assemblea da parte del collegio sindacale |
| Reg. Emittenti (Consob 11971/1999) | Artt. 39-bis, 40, 40-bis, 41, 42, 50, 50-bis, 50-quinquies, 144-sexies, 144-octies |
| Reg. OPC (Consob 17221/2010) | Operazioni con parti correlate; testo vigente dall'11 giugno 2026 |
| **D.Lgs. 385/1993 (TUB)** | Testo unico bancario |
| Art. 14 TUB | Autorizzazione all'attività bancaria |
| Art. 56 TUB | Accertamento preventivo sulle modifiche statutarie delle banche |
| Art. 57 TUB | Fusioni e scissioni bancarie; termine di opposizione dei creditori ridotto a 15 giorni |
| Art. 58 TUB | Cessione di aziende, rami d'azienda e rapporti giuridici individuabili in blocco |
| Art. 61 TUB | Ruolo della capogruppo; c. 1 dovere di direzione e coordinamento, c. 4 obbligo di collaborazione degli amministratori delle controllate |
| Art. 64 TUB | Iscrizione all'albo dei gruppi bancari |
| Art. 70 c. 7 TUB | Esclusione dell'art. 2409 c.c. per le banche, sostituito dalla denuncia alla Banca d'Italia |
| Codice civile | Artt. 2364, 2366, 2367, 2373, 2377, 2383, 2385, 2386, 2391-bis, 2392, 2393, 2393-bis, 2400, 2406, 2409, 2437-quinquies, 2497 e ss., 2501 e ss., 2504-quater |
| **CRR** (Reg. UE 575/2013), come modificato da **CRR3** (Reg. UE 2024/1623) | Artt. 36, 49, 81-88; applicazione dal 1° gennaio 2025 |
| TUIR (D.P.R. 917/1986) | Artt. 84, 117-129 (consolidato fiscale), 172 c. 7, 177-ter |

---

# PARTE I — FATTI ACCERTATI

> Tutto ciò che segue è verificato su fonte primaria (comunicati societari, testi normativi) o su fonte
> secondaria affidabile con indicazione esplicita. Dove un dato è incerto o discordante, è segnalato.

## 1. L'operazione e il suo stato al 16 settembre 2026

### 1.1 Cronologia

| Data | Evento |
|---|---|
| 24 gen 2025 | MPS annuncia l'OPS su Mediobanca |
| 8-22 set 2025 | Offerta MPS su MB: 62,3% in prima fase, 86,348% dopo la riapertura dei termini. Soglie di delisting **non** raggiunte |
| 10 mar 2026 | Approvato il progetto di fusione per incorporazione di MB in MPS; concambio 2,450 azioni MPS per azione MB |
| 15 apr 2026 | Assemblea MPS: nomina del CdA per gli esercizi 2026-2028; la lista del consiglio uscente è battuta |
| 29 apr 2026 | Entra in vigore il D.Lgs. 47/2026 di riforma del TUF |
| 7 giu 2026 | Banco BPM propone a MPS un'aggregazione tra pari |
| **8 giu 2026** | **ISP diffonde la comunicazione ex art. 102 c. 1 TUF**: OPAS volontaria totalitaria su MPS. Stesso giorno: accordo con Unipol e acquisto del 3,01% di AG con copertura in derivati |
| 26 giu 2026 | Istanza ISP a BCE e Banca d'Italia ex artt. 56 e 61 TUB |
| 27 giu 2026 | Deposito del documento di offerta in Consob; istanze a circa 40 autorità |
| 16 lug 2026 | Il CdA MPS diffonde "considerazioni preliminari" critiche sull'offerta |
| 21 ago 2026 | MPS annuncia due OPS difensive su Banco BPM e Banca Generali (delibera del CdA del 20 agosto, assunta a maggioranza) |
| 3 set 2026 | BCE autorizza la fusione MB-MPS e le riorganizzazioni connesse |
| 10 set 2026 | Assemblea straordinaria ISP approva la delega per l'aumento di capitale al servizio dell'offerta, con il 96,96% dei voti su un capitale presente del 63,88% |
| 14-15 set 2026 | AGCM avvia l'istruttoria approfondita |
| 16 set 2026 | IVASS rilascia il primo nullaosta (partecipazioni assicurative) |
| **29 ott 2026** | **Assemblea MPS convocata** su: fusione MB, autorizzazioni ex art. 104 TUF per le due OPS difensive, deleghe per i relativi aumenti, distribuzione straordinaria di 4 miliardi (1 in denaro, circa 3 in azioni AG) |

**Stato dell'offerta al 16 settembre 2026: non ancora avviata.** Il documento di offerta non è stato
approvato da Consob. Il periodo di adesione è atteso fra ottobre e novembre 2026, il perfezionamento
entro dicembre 2026.

### 1.2 Stato delle autorizzazioni

| Autorità | Stato al 16 settembre 2026 |
|---|---|
| IVASS (partecipazioni assicurative) | **Ottenuta** il 16 settembre 2026 |
| BCE (modifiche statutarie ISP, computabilità CET1) | **Ottenuta** |
| BCE / Banca d'Italia (partecipazione qualificata in MPS) | Pendente |
| BCE (Danish Compromise sulla quota AG) | Pendente |
| AGCM | **Istruttoria approfondita aperta** il 14 settembre 2026 |
| Consob (documento di offerta) | Pendente |
| Golden power | Notificato, nessuna decisione formale pubblica |
| Circa 40 autorità italiane ed estere | In corso |

## 2. Termini dell'offerta (comunicato ex art. 102 c. 1 TUF, 8 giugno 2026)

### 2.1 Corrispettivo e perimetro

- **Corrispettivo unitario**: 1,600 azioni ISP di nuova emissione + **1,000 euro in contanti** per
  ciascuna azione MPS.
- Valore implicito **10,091 euro per azione MPS** ai prezzi del 5 giugno 2026; controvalore complessivo
  circa **30,6 miliardi di euro**.
- Premi dichiarati: 12,5% sul prezzo ufficiale del 5 giugno (8,970 euro), 17,4% sul VWAP a tre mesi,
  18,7% sul VWAP a sei mesi.
- Oggetto: massime **3.036.151.673 azioni**, dedotte le 2.266.510 azioni MPS già detenute da ISP;
  estensione a massime 272.012.804 azioni MPS di nuova emissione se la fusione MB diventasse efficace
  prima della chiusura del periodo di adesione.
- **Periodo di adesione**: durata compresa fra 15 e 40 giorni di borsa aperta, concordata con Borsa
  Italiana, salvo proroga.

### 2.2 Condizioni di efficacia (verbatim, estratti)

> "(i) vengano rilasciate le Autorizzazioni Preventive **senza prescrizioni, condizioni o limitazioni,
> anche con riferimento all'applicazione del regime prudenziale noto come 'Danish Compromise'**;
> (ii) entro il secondo giorno di borsa aperta antecedente la Data di Pagamento vengano rilasciate le
> Altre Autorizzazioni senza prescrizioni, condizioni o limitazioni; (iii) all'esito dell'Offerta,
> l'Offerente venga a detenere, per effetto delle adesioni alla stessa e/o di acquisti eventualmente
> effettuati al di fuori dell'Offerta medesima ai sensi della normativa applicabile durante il Periodo
> di Adesione, una partecipazione pari ad almeno il **66,67%** dell'Emittente ('Condizione Soglia');
> l'Offerente si riserva di rinunciare, tra le altre, in tutto o in parte alla presente Condizione di
> Efficacia"

Le condizioni (iv) e (v) vietano a MPS, **fra la data del comunicato e la Data di Pagamento**, atti non
rientranti nell'*ordinary course of business* e atti che contrastino gli obiettivi dell'offerta,
"ancorché [...] autorizzati dall'assemblea ordinaria o straordinaria". La condizione (vii) protegge
l'esecuzione della fusione MB. La condizione (vi) è una clausola MAE di formulazione ampia.

> **Dato strutturale da tenere presente**: la protezione delle condizioni (iv) e (v) **si esaurisce
> alla Data di Pagamento**, così come la passivity rule dell'art. 104 TUF si esaurisce con la chiusura
> dell'offerta. Dopo il settlement ISP non ha più né leve contrattuali né il presidio della passivity.

### 2.3 Delisting, squeeze-out e sell-out (verbatim)

> "l'obiettivo dell'Offerta è acquisire l'intero capitale sociale dell'Emittente (o almeno una
> partecipazione pari al 66,67% [...] salvo rinuncia, anche parziale, da parte dell'Offerente) e
> conseguire la revoca delle relative azioni dalla quotazione sul mercato regolamentato Euronext Milan."

> "Nell'ottica di accelerare il raggiungimento degli obiettivi industriali [...] l'Offerente ha
> l'intenzione di procedere, nel minor tempo possibile, al delisting dell'Emittente, **se del caso
> mediante fusione tra l'Emittente e l'Offerente**, tenuto conto della gestione delle problematiche
> antitrust."

> "per il caso in cui, all'esito dell'Offerta - per effetto delle adesioni all'Offerta e/o di acquisti
> eventualmente effettuati al di fuori dell'Offerta medesima - l'Offerente venisse a detenere una
> partecipazione complessiva **pari o superiore al 90%** del capitale sociale dell'Emittente,
> l'Offerente dichiara sin d'ora la propria intenzione di esercitare il diritto di acquistare le residue
> Azioni dell'Emittente in circolazione ai sensi dell'articolo 111 del TUF [...] e, nel caso previsto
> dall'articolo 108, comma 2, del TUF, la propria intenzione di **non ripristinare un flottante
> sufficiente** ad assicurare il regolare andamento delle negoziazioni."

> "ai fini del calcolo della soglia prevista dall'art. 108, commi 1 o 2, e 111 del TUF, **le azioni
> proprie detenute dall'Emittente** (se non già portate in adesione all'Offerta) **saranno computate
> nella partecipazione complessiva detenuta** direttamente o indirettamente dall'Offerente (numeratore)
> **senza essere sottratte dal capitale sociale** dell'Emittente (denominatore)."

> "Sussistendone i presupposti [...] l'Offerente adempierà altresì all'obbligo di acquistare le rimanenti
> Azioni [...] **dando pertanto corso a un'unica procedura** (la 'Procedura Congiunta')." Il corrispettivo
> "sarà determinato ai sensi dell'articolo 108, commi 3, 4 e 5, del TUF, come richiamato dall'articolo
> 111". Il diritto di acquisto "sarà esercitato non appena possibile [...] secondo termini e modalità
> che saranno concordati con Consob e Borsa Italiana."

> **Riapertura dei termini (verbatim)**: "Si precisa che l'Offerta, essendo promossa da un soggetto
> diverso da quelli indicati nell'art. 39-bis, comma 1, lett. a), del Regolamento Emittenti, **non è
> soggetta alla riapertura obbligatoria** dei termini di adesione prevista dall'art. 40-bis del
> Regolamento Emittenti."
>
> **Nel comunicato non risulta dichiarato alcun assoggettamento volontario.** È un punto decisionale
> ancora aperto (Parte II, § 10).

> **Riserva sul diritto transitorio (verbatim)**: "In considerazione della recente entrata in vigore del
> d.lgs. 27 marzo 2026, n. 47 di riforma del TUF, e delle conseguenti modifiche agli articoli 108 e 111
> dello stesso, l'Offerente si riserva di integrare quanto sopra per tenere conto dell'eventuale
> disciplina attuativa che dovesse essere emanata dalla Consob, nonché degli eventuali orientamenti
> interpretativi, anche di diritto transitorio, che dovessero intervenire."

### 2.4 Accordo Unipol (verbatim)

> "L'Offerente ha stipulato, in data odierna, un accordo con Unipol Assicurazioni S.p.A. (l''Accordo
> Unipol'), la quale ha assunto l'impegno [...] di acquisire (a seguito del perfezionamento dell'Offerta
> e **dell'adesione dell'Emittente all'Accordo Unipol**, nonché subordinatamente all'ottenimento delle
> necessarie autorizzazioni) **l'intero capitale di una entità giuridica bancaria, eventualmente
> identificata nello stesso Emittente**, e comunque operante sotto il marchio e i segni distintivi di
> quest'ultimo, con un compendio aziendale costituito da un insieme di **635 filiali** dell'Emittente
> (con gli elementi patrimoniali e i rapporti giuridici connessi), e gran parte delle strutture/attività
> centrali dell'Emittente (con relative attività e passività) necessarie per operare come banca in modo
> indipendente. L'Accordo Unipol è funzionale a gestire proattivamente le tematiche antitrust."

Dati collegati: corrispettivo per cassa circa **3-3,5 miliardi di euro**; perfezionamento atteso nel
**secondo semestre 2027**; delle 635 filiali, **445 sono già identificate in via definitiva e 190 solo
in via preliminare** e potranno essere sostituite. Unipol ha ottenuto dall'assemblea del 30 luglio 2026
una delega per un aumento di capitale fino a 2,5 miliardi. Il progetto dichiarato è la successiva
combinazione con BPER, con ridenominazione in "Banca Monte dei Paschi".

## 3. Azionariato MPS

Capitale sociale: **3.038.418.183 azioni ordinarie** prive di valore nominale, un voto ciascuna.
**Non esistono patti parasociali dichiarati né soggetti che esercitino il controllo ex art. 93 TUF.**
Lo statuto non contiene *voting cap* generali, azioni a voto plurimo o maggiorato, né clausole di
gradimento; l'unica clausola limitativa (art. 14 c. 8) riguarda esclusivamente le fondazioni bancarie
ed è priva di rilievo per ISP.

| Azionista | Quota | Fonte e data |
|---|---|---|
| Delfin S.à r.l. | **17,53%** | Consob, data operazione 29 settembre 2025 |
| Gruppo Francesco Gaetano Caltagirone | **10,26%** notificato / **13,49%** | Consob (notifica 29 settembre 2025) / MPS al 20 maggio 2026. **Dato discordante: usare 13,49% come stima corrente e 10,26% come dato notificato** |
| MEF | 4,86% | Consob |
| BlackRock | 4,97% aggregato (4,665% azioni + 0,302% posizioni lunghe) | Mod. 120B del 30 aprile 2026 |
| Banco BPM (anche tramite Anima) | 3,74% (2,07% azioni + 1,67% strumenti) | Consob |
| Norges Bank | ~3,1% | Cronache assembleari |
| Vanguard | ~2,6% | Cronache assembleari |
| ISP (pre-offerta) | 0,075% (2.266.510 azioni) | Comunicato 102 dell'8 giugno 2026 |
| Flottante residuo | ~59% | — |

**Contenzioso rilevante**: la Procura di Milano indaga per aggiotaggio e ostacolo alla vigilanza,
ipotizzando un concerto non dichiarato fra Delfin, Caltagirone e i vertici MPS. In direzione opposta,
un documento della Divisione Vigilanza Emittenti Consob del 15 settembre 2025 concludeva che "non
sussiste il patto occulto" e "non sussiste il concerto". Indagine ancora aperta.

## 4. Organi sociali MPS

### 4.1 Consiglio di Amministrazione

Nominato dall'assemblea del **15 aprile 2026** per gli esercizi **2026-2027-2028**; scadenza con
l'assemblea di approvazione del bilancio 2028, primavera **2029**. **15 componenti.**

| Lista | Voti | Seggi |
|---|---|---|
| PLT Holding S.r.l. / PLT S.p.A. (1,0329% del capitale) | 49,953% | **8** |
| Lista del CdA uscente (art. 147-ter.1 TUF) | 38,795% | 6 |
| Assogestioni / investitori istituzionali (0,78%) | 6,945% | 1 |

Presidente **Cesare Bisoni**; vicepresidenti Flavia Mazzarella e Carlo Corradini; amministratore
delegato e direttore generale **Luigi Lovaglio**. Tutte le nomine approvate con **8 voti su 15**, con
5 contrari e 2 astenuti.

Fatti che documentano la frattura interna: il 25 marzo 2026 il consiglio allora in carica aveva revocato
le deleghe a Lovaglio; il 20 agosto 2026 la delibera sulle due OPS difensive è passata a maggioranza e
non all'unanimità; a inizio settembre 2026 sono stati cooptati Gianluca Brancadoro e Alessandro
Caltagirone in sostituzione di Fabrizio Palermo e Carlo Vivaldi, attingendo ai primi non eletti della
lista di minoranza come prescritto dall'art. 15 c. 10 lett. b) dello statuto.

> **Avvertenza per l'agente**: le linee di frattura del consiglio **non coincidono** con la linea
> pro/contro l'Offerta. Il conteggio dei consiglieri favorevoli o contrari va rifatto nominativamente e
> aggiornato, non dedotto dall'appartenenza alle liste dell'aprile 2026.

### 4.2 Collegio Sindacale

Nominato dalla stessa assemblea per gli esercizi 2026-2028. Presidente **Pierluigi Pace**, espresso
dalla **lista di minoranza** degli investitori istituzionali (33,391% dei presenti); sindaci effettivi
Monica Vecchiati (lista PLT) e Lavinia Linguanti (nominata a maggioranza su proposta formulata in
assemblea); supplenti Francesca Sandrolini e Alberto Sodini.

**I sindaci non sono revocabili ad nutum**: serve giusta causa e l'approvazione con decreto del
tribunale, sentito l'interessato (art. 2400 c. 2 c.c.; art. 25 c. 9 dello statuto). Il collegio resta
quindi in carica in tutti gli scenari.

### 4.3 Compensi (dato da riconciliare sulla Relazione ex art. 123-ter TUF)

Compensi rivisti al rialzo dall'assemblea del 15 aprile 2026, secondo la stampa specializzata:
presidente **830.000 euro**, consigliere **120.000 euro**, presidente del collegio 190.000 euro,
sindaco effettivo 140.000 euro. La remunerazione dell'amministratore delegato ex art. 2389 c. 3 c.c.
non è pubblicamente quantificata.

## 5. Statuto MPS: clausole rilevanti

Testo come modificato dall'assemblea straordinaria del 4 febbraio 2026, autorizzato dalla BCE il
4 marzo 2026 e iscritto il 5 marzo 2026. **Il testo consolidato non è stato riscontrato
documentalmente** (Parte III, punto 1).

| Articolo | Contenuto |
|---|---|
| Art. 12 c. 1 | Convocazione deliberata dal CdA e curata dal Presidente, "**fermi i poteri di convocazione previsti da specifiche disposizioni di legge**" (salvaguarda collegio sindacale e tribunale) |
| Art. 12 c. 2 | Assemblea in **unica convocazione** |
| Art. 12 c. 4 | L'assemblea è **presieduta dal Presidente del CdA** o da chi lo sostituisce |
| Art. 12 c. 5 | Il presidente accerta la legittimazione, regola la discussione, stabilisce le modalità di voto, proclama i risultati |
| Art. 14 c. 4-5 | Assemblea ordinaria valida qualunque sia il capitale rappresentato; delibera a maggioranza assoluta dei votanti, salvo le nomine |
| Art. 15 c. 1 | Da 9 a 15 amministratori, durata tre esercizi; divieto statutario di cariche in banche concorrenti non del gruppo, **a pena di decadenza immediata** |
| Art. 15 c. 3 | Liste dei soci depositate almeno **25 giorni** prima; lista del CdA uscente almeno **40 giorni** prima |
| Art. 15 c. 5 | Soglia di presentazione delle liste: 1% "ovvero la diversa percentuale applicabile"; **per il 2026 la soglia Consob è lo 0,5%** (determina dirigenziale n. 155 del 27 gennaio 2026) |
| Art. 15 c. 7.1 | Metodo dei quozienti; alla lista prima per voti almeno la metà più uno dei seggi; **alle liste di minoranza almeno 2 consiglieri** |
| Art. 15 c. 7.3 | **Almeno un amministratore** dalla lista di minoranza non collegata |
| **Art. 15 c. 10** | "**Qualora venga a cessare la maggioranza degli amministratori, deve intendersi dimissionario l'intero Consiglio di Amministrazione con effetto dal momento della sua ricostituzione.** Gli Amministratori possono essere revocati dall'Assemblea in qualunque momento, salvo il diritto dell'amministratore al risarcimento dei danni, se la revoca avviene senza giusta causa." |
| Art. 25 | Collegio sindacale di 3 effettivi e 2 supplenti; presidenza alla seconda lista per voti non collegata; revoca solo per giusta causa con decreto del tribunale |

## 6. Il quadro normativo vigente sulle soglie

### 6.1 La riforma: D.Lgs. 27 marzo 2026 n. 47

Pubblicato in GU n. 86 del 14 aprile 2026, **in vigore dal 29 aprile 2026**, attuativo della delega
dell'art. 19 della L. 5 marzo 2024 n. 21. **Non esistono norme transitorie per la materia OPA**: gli
artt. 106, 108, 111 modificati sono pienamente applicabili dal 29 aprile 2026.

**La Consob deve adottare la normativa secondaria di attuazione della Parte IV TUF entro il 29 gennaio
2027.** Consultazione aperta il 18 giugno 2026 e chiusa il 20 luglio 2026; al 16 settembre 2026 la
delibera conclusiva **non risulta pubblicata**. Cade esattamente nella finestra del settlement.

### 6.2 Art. 111 TUF, testo vigente (verbatim)

> "**1.** L'offerente che venga a detenere a seguito di offerta pubblica totalitaria **o di acquisto ai
> sensi dell'articolo 108, comma 2**, una partecipazione almeno pari al **90 per cento** del capitale
> rappresentato da titoli in una società italiana quotata ha diritto di acquistare i titoli residui
> entro tre mesi dalla scadenza del termine per l'accettazione dell'offerta **ovvero dall'acquisto ai
> sensi dell'articolo 108, comma 2**, se ha dichiarato nel documento d'offerta l'intenzione di avvalersi
> di tale diritto. [...]
> **1-bis.** Il comma 1 si applica anche nel caso in cui l'offerente, a seguito di offerta pubblica di
> acquisto totalitaria avente a oggetto strumenti finanziari diversi dai titoli, venga a detenere una
> percentuale almeno pari al 90 per cento di tali strumenti finanziari.
> **2.** Il corrispettivo e la forma che esso deve assumere sono determinati ai sensi dell'articolo 108,
> commi 3, 4 e 5.
> **3.** Il trasferimento ha efficacia dal momento della comunicazione dell'avvenuto deposito del prezzo
> di acquisto presso una banca alla società emittente [...]"

Tre novità: soglia dal 95% al 90%; nuovo presupposto oggettivo (anche il 90% raggiunto tramite il
sell-out); nuovo comma 1-bis per gli strumenti diversi dai titoli. **La dichiarazione nel documento di
offerta è condizione di esercizio, non un adempimento informativo**: se manca, il diritto non è
esercitabile a qualunque percentuale.

### 6.3 Art. 108 TUF, commi rilevanti

- **c. 1**: obbligo di acquisto a partire dal **95%** raggiunto a seguito di offerta totalitaria
  (invariato).
- **c. 2**: obbligo di acquisto per chi detiene **oltre il 90%** "se non ripristina entro novanta giorni
  un flottante sufficiente ad assicurare il regolare andamento delle negoziazioni" (invariato).
- **c. 3**: il corrispettivo è pari a quello dell'offerta se la soglia è raggiunta "**esclusivamente a
  seguito di offerta pubblica totalitaria**" e, per le offerte volontarie, se l'offerente ha acquistato
  titoli "non meno del **novanta per cento del capitale con diritto di voto compreso nell'offerta**"
  (invariato).
- **c. 4**: negli altri casi il corrispettivo è **determinato dalla Consob** (invariato).
- **c. 5** (**modificato dalla riforma**): il corrispettivo assume la stessa forma di quello
  dell'offerta; il diritto a esigere un corrispettivo integralmente in denaro sussiste solo "nel caso in
  cui in tale offerta siano offerti **strumenti finanziari diversi da titoli ammessi alla negoziazione
  su un mercato regolamentato dell'Unione europea**".

> **Conseguenza per il dossier**: poiché il corrispettivo ISP comprende azioni quotate su Euronext
> Milan, **gli oblati residui non possono pretendere l'uscita integralmente in denaro**. Nel precedente
> Banca Ifis/illimity del settembre 2025, sotto il regime previgente, il 53,6% delle azioni residue
> oggetto di procedura congiunta era accompagnato da richieste con opzione per il corrispettivo in
> denaro.

### 6.4 Art. 40-bis Reg. Emittenti (riapertura dei termini)

Durata: **5 giorni di borsa aperta** dal giorno successivo alla data di pagamento. Si applica
obbligatoriamente solo alle offerte promosse dai soggetti dell'art. 39-bis c. 1 lett. a) ("offerte da
insider": chi detiene già oltre il 30%, aderenti a patti, amministratori, concertisti). **ISP non
rientra** in quelle categorie. L'art. 40-bis c. 3 lett. b) esenta comunque l'offerente che al termine
del periodo di adesione raggiunga la soglia dell'art. 108 c. 1 o c. 2 avendo dichiarato di non
ripristinare il flottante.

**L'assoggettamento volontario è espressamente riconosciuto** dall'art. 50 c. 4 lett. c) Reg. Emittenti,
che ancora il corrispettivo del sell-out al prezzo d'offerta per l'offerta "soggetta" o "volontariamente
assoggettata", purché nella prima fase sia stato conferito almeno il 50% dei titoli oggetto dell'offerta.

### 6.5 Procedura congiunta

Base: art. 50-quinquies c. 1 Reg. Emittenti. Il periodo per le richieste di vendita è "concordata con il
gestore del mercato tra un minimo di **quindici** e un massimo di **venticinque giorni**" (giorni di
borsa aperta); la procedura per l'esercizio congiunto è "concordata con la Consob e il gestore del
mercato". **Disallineamento transitorio**: il testo vigente richiama ancora solo l'art. 108 c. 1; la
Consob propone di estenderlo al c. 2 proprio per la nuova soglia del 90%.

Delisting: art. 2.5.1 c. 6 del Regolamento dei Mercati di Borsa Italiana — i titoli sono revocati dalla
quotazione "a decorrere dal giorno di borsa aperta successivo all'ultimo giorno di pagamento del
corrispettivo".

## 7. La timeline di pagina 4 del deck ("Ipotesi settlement al 2027")

Il deck di riferimento è `20260913_ISP_Prj_Stradebianche_scenari_settlement_v.DRAFT (004).pptx`,
6 slide, datato settembre 2026, a uso interno. Pagina 3 rappresenta lo scenario di settlement 2026,
pagina 4 quello di settlement 2027, pagine 5-6 le implicazioni contabili, regolamentari e operative a
confronto fra i due scenari.

| Data | Evento (pag. 4) |
|---|---|
| 9 nov 2026 | Avvio periodo di offerta |
| 9 nov – 4 gen | Periodo di adesione (**37 giorni di borsa aperta**) |
| 4 gen 2027 | Termine periodo di offerta |
| **6 gen 2027** | **Settlement** e istanza di trasferimento della partecipazione AG |
| 13 gen (S+7) | Delibera di convocazione dell'assemblea MPS dopo eventuali dimissioni del CdA uscente |
| 14 gen | Pubblicazione dell'avviso di convocazione |
| 29 gen | Deposito delle liste dei soci |
| 4 feb | Pubblicazione delle liste e documentazione pre-assembleare |
| 5 feb | Approvazione schemi di bilancio MPS **da parte del CdA uscente** |
| 5–24 feb | Approvazione del bilancio MPS da parte dell'attuale CdA |
| 7/8 feb | Approvazione bilancio ISP e invio richiesta BCE per il dividendo |
| **25 feb 2027** | **Assemblea MPS e nomina del nuovo CdA** (t+50) |
| entro apr–mag | Finalizzazione del carve-out |
| Q3–Q4 2027 | Cessione dell'entità giuridica bancaria a Unipol |

Note del deck rilevanti: la convocazione "è deliberata dal CdA e curata dal Presidente"; "in caso di
totale inerzia, il Collegio Sindacale può convocare l'assemblea"; "**in mancanza di dimissioni, sarà
necessario procedere alla revoca in assemblea**"; nello scenario 2027 il bilancio FY2026 è approvato dal
CdA uscente e non è necessario il reporting package perché non c'è consolidamento; "possibilità di
nomina nuovo CdA a +40 [...] tuttavia tale opzione non dipende da ISP".

## 8. Precedenti di mercato

| Operazione | Anno | % prima fase | % dopo riapertura | Esito | Delisting | Mesi settlement → delisting | Settlement → nuovo board |
|---|---|---|---|---|---|---|---|
| ISP / UBI Banca | 2020-21 | 90,2% | nessuna riapertura (esenzione 40-bis c. 3 lett. b) | sell-out → 98,9%; procedura congiunta → 100% | 5 ott 2020 | 2,0 | ~71 giorni |
| CA Italia / Creval | 2021 | 91,167% | — | sell-out → 97,2%; procedura congiunta | 4 giu 2021 | ~1 | — |
| BPER / Carige | 2022 | ~80% (acquisto negoziato) | — | OPA obbligatoria e fusione | 2022 | — | **12 giorni** |
| Unipol / UnipolSai | 2024 | 94,916% | — | sell-out → 96,9%; procedura congiunta → 100% | 3 lug 2024 | 2,0 | — |
| Banco BPM Vita / Anima | 2025 | **89,949%** | nessuna | nessuna soglia raggiunta; nessuna fusione deliberata | **non delistata** | ≥17 | — |
| Banca Ifis / illimity | 2025 | >92% | — | sell-out → 95,4%; procedura congiunta → 100% | 19 set 2025 | ~2,5 | 83 giorni |
| BPER / Banca Popolare di Sondrio | 2025-26 | 58,49% | **80,69%** (+22,20 pp) | fusione in BPER | 20 apr 2026 | 8,6 | ~47 giorni, con **revoca in assemblea** del consigliere che non si era dimesso, senza ritardi |
| MPS / Mediobanca | 2025-26 | 62,3% | **86,348%** (+24,0 pp) | fusione in MPS, BCE 3 set 2026, assemblea 29 ott 2026 | **non delistata** | ≥11,5 (attesa ~15) | 42 giorni |
| TIM / Elliott / Vivendi | 2018 | n/a | n/a | conflitto assembleare; il Tribunale di Milano sospende la delibera del collegio sindacale | n/a | n/a | ~10 giorni di ritardo sul percorso contestato |

Tre letture che emergono dall'insieme: la riapertura dei termini muove molto (+22/+24 punti) ma
raramente abbasta; il vero discriminante è la percentuale della **prima fase** (nei casi con delisting
rapido era già ≥90%); **non esiste un precedente italiano in cui una prima fase sotto il 70% sia poi
arrivata al 90%**.

---

# PARTE II — ANALISI E CONCLUSIONI

> Quanto segue è il prodotto di ragionamento sui fatti della Parte I. È difendibile ma non è
> fatto accertato. Presentalo come analisi.

## 9. Nodo A — Le soglie di adesione

### 9.1 L'aritmetica del libro soci: il 90% dipende da due azionisti

Partendo da un capitale di 100 e da ISP allo 0,075%:

- Delfin (17,53%) + Caltagirone (13,49%) = **31,02%**. Se nessuno dei due aderisce, il massimo teorico
  è **68,98%**; aggiungendo Banco BPM (3,74%), **65,24%**.
- Con l'adesione del solo Delfin il massimo è **86,5%**; con il solo Caltagirone, **82,5%**. In entrambi
  i casi **il 90% è aritmeticamente inaccessibile**.
- Con l'adesione di entrambi restano da raccogliere 58,9 punti sui 68,9 detenuti da tutti gli altri
  soci, cioè **l'85,5% del resto del capitale**. Il margine per il residuo inerte (retail, tracker,
  dormienti) è di 14,5 punti di quel bucket, e i soli fondi indicizzati (BlackRock, Vanguard, Norges)
  ne pesano circa 15.
- Anche il **66,67%** non è scontato senza i due: richiederebbe il 96,7% di tutto il resto.

**Conclusione**: il ramo sotto-90% non è una coda di distribuzione, è **lo scenario centrale da
pianificare**; il 90% va trattato come upside da massimizzare. Il caso Banco BPM Vita/Anima, fermatosi
a 89,949% (5 punti base sotto la soglia) con l'emittente ancora quotato 17 mesi dopo, misura quanto sia
discontinua la soglia.

### 9.2 Il sotto-90% non è uno stallo: è un binario lento

**Ciò che ISP ottiene al settlement non dipende dal 90%.** Alla Data di Pagamento, anche solo al 67%,
ISP acquisisce il controllo di diritto e la maggioranza dell'assemblea ordinaria, **consolida** MPS
dalla data di acquisizione (IFRS 10.B35: rileva il *potere* di nominare la maggioranza dell'organo, non
il fatto che il rinnovo sia già avvenuto — nel precedente MPS/Mediobanca il controllo è stato
riconosciuto dal 15 settembre 2025 con il nuovo consiglio nominato il 28 ottobre), nomina il nuovo CdA
e, se sopra il 66,67%, dispone della maggioranza qualificata per deliberare la fusione.

**Ciò che non ottiene sono due cose sole**: le azioni residue e il delisting. Sotto il 90% non esiste
alcuno strumento coattivo: né l'art. 108 c. 2 né l'art. 111 sono azionabili, e il socio che non ha
aderito ha il diritto di restare.

**Lo strumento che elimina le minoranze senza il loro consenso è la fusione.** Con l'efficacia della
fusione le azioni MPS sono annullate e concambiate in azioni ISP per effetto di legge. Non serve il
consenso delle minoranze; **non spetta loro il diritto di recesso**, perché riceverebbero azioni ISP
quotate su Euronext Milan e quindi non opera l'art. 2437-quinquies c.c.; una volta iscritto l'atto di
fusione l'invalidità non è più pronunciabile (art. 2504-quater c.c.) e il contenzioso si sposta dal
piano dell'impugnativa a quello risarcitorio.

| | ≥90% | 67-89% |
|---|---|---|
| Controllo e consolidamento | dal settlement | **dal settlement, identico** |
| Nomina del nuovo CdA | sì | **sì, identico** |
| Passaggio al 100% | procedura congiunta, 4-8 settimane | fusione, 8-15 mesi |
| Delisting | feb–mar 2027 | set 2027 – mar 2028 |
| Strumento | artt. 111 e 108 TUF | artt. 2501 e ss. c.c. + art. 57 TUB |
| Consenso delle minoranze | non richiesto | non richiesto |
| Esborso di cassa aggiuntivo | corrispettivo in azioni + 1 euro, nessuna *cash alternative* | nessuno, nessun recesso |

### 9.3 La cascata degli esiti

**Ramo A1 — ≥90% alla chiusura.** Scattano insieme sell-out e squeeze-out; la riapertura non si
applicherebbe comunque per l'esenzione dell'art. 40-bis c. 3 lett. b). Sequenza: comunicato risultati
definitivi; settlement; 1-2 settimane per l'accordo con Consob e Borsa e i comunicati; 15-25 giorni di
borsa aperta di periodo per le richieste di vendita; regolamento, deposito del prezzo, trasferimento ex
art. 111 c. 3, sospensione e revoca dalla quotazione. **Stima 4-8 settimane dal settlement**, quindi
delisting fra la seconda metà di febbraio e la prima metà di marzo 2027. I precedenti (ISP/UBI 2 mesi,
Unipol/UnipolSai 2 mesi, Ifis/illimity 2,5 mesi) erano tutti sotto il vecchio regime a due gradini: il
nuovo art. 111 consente di saltare il sell-out intermedio.

> **Due trappole di pricing.** (1) Se il superamento del 90% dipende in parte da **acquisti successivi
> al settlement**, viene meno il requisito "esclusivamente a seguito di offerta pubblica totalitaria" e
> il corrispettivo passa alla determinazione Consob ex art. 108 c. 4, in via ordinaria in forma
> **monetaria**: su un residuo del 10% significa un'uscita di cassa non pianificata nell'ordine di
> **3 miliardi** e 4-6 settimane di ritardo. Gli acquisti effettuati **durante** il periodo di adesione
> sono invece computati nelle adesioni (art. 50 c. 9 lett. a) n. ii Reg. Emittenti): se si compra, si
> compra prima della chiusura. (2) Se il 90% si raggiunge grazie al criterio dichiarato sulle **azioni
> proprie**, il test dell'art. 108 c. 3 (≥90% del capitale *compreso nell'offerta*) può non essere
> soddisfatto, con lo stesso effetto. Entrambi i punti vanno riconciliati numericamente prima della
> chiusura.

**Ramo A2 — 85-89,9%.** Nessun delisting automatico. Leve residue in ordine di preferenza: riapertura
volontaria dei termini (+22/+24 punti nei precedenti); proroga del periodo di adesione (residuano ~3
giorni entro il tetto di 40); acquisti sul mercato post-settlement, con le trappole di pricing viste
sopra e con l'esercitabilità dell'art. 111 su un 90% raggiunto per soli acquisti di mercato non
testualmente pacifica; seconda OPA volontaria, con l'avvertenza del *put up or shut up* dell'art. 102
c. 8 TUF (silenzio o diniego dopo un termine fissato da Consob comporta il divieto di offerte per
dodici mesi).

**Ramo A3 — 66,67-84,9% (ramo probabile).** Delisting solo via fusione: progetto approvato dai due CdA;
autorizzazione BCE ex art. 57 TUB (6-13 settimane; per MPS/MB richiesta a metà luglio 2026 e
autorizzazione il 3 settembre 2026); deposito del progetto almeno 30 giorni prima dell'assemblea;
relazione dell'esperto ex art. 2501-sexies; doppio documento informativo OPC; assemblee straordinarie
con i due terzi del capitale rappresentato; opposizione dei creditori **ridotta a 15 giorni** per le
banche ex art. 57 TUB; consultazioni sindacali ex art. 47 L. 428/1990. **Durata 8-15 mesi**: delisting
fra settembre 2027 e marzo 2028.

> **Aritmetica dei due terzi, ed è la ragione d'essere della Condizione Soglia.** Se ISP detiene almeno
> il 66,67% del capitale, la maggioranza dei due terzi del capitale *rappresentato* in assemblea
> straordinaria è **garantita qualunque sia l'affluenza**, perché gli altri soci non possono
> rappresentare più del 33,33%. È per questo che la soglia è fissata lì e non al 50% più un'azione.
> Sotto il 66,67% la fusione diventa una funzione dell'affluenza: il break-even è la quota ISP divisa
> per 0,6667 (ISP al 60% → 90% di affluenza; ISP al 55% → 82,5%). All'assemblea MPS del 15 aprile 2026
> l'affluenza è stata di circa il 65% del capitale, ma un'assemblea di fusione contestata mobiliterebbe
> molto di più.

**Ramo A4 — sotto il 66,67%.** Solo se ISP rinuncia alla Condizione Soglia. Controllo ordinario sì,
maggioranza straordinaria non garantita, nessuna via certa al delisting, struttura con minoranze del
40%+ potenzialmente a tempo indeterminato, remedy Unipol da ridisegnare integralmente. **È qui che si
colloca il rischio di stallo vero.** L'OPA da consolidamento (art. 106 c. 3 lett. b), ora al 10%) non
scatta, perché presuppone che il soggetto non abbia la maggioranza in assemblea ordinaria.

**Strumenti non disponibili nella finestra temporale**: l'acquisto totalitario ex art. 112-bis TUF
(attuazione Consob attesa entro il 29 aprile 2027 e comunque soggetto a un whitewash che consegna un
veto alle minoranze) e il down-listing su MTF ex art. 133 c. 1-bis TUF (stessa attuazione, preavviso di
due mesi e diritto di recesso ex art. 2437-quinquies c.c.).

### 9.4 Su cosa variano gli scenari

| # | Dimensione | ≥90% | Sotto il 90% |
|---|---|---|---|
| 1 | Delisting | feb–mar 2027 | set 2027 – mar 2028, solo via fusione |
| 2 | Partecipazione finale | 100% | 67-89%, minoranze 11-33% |
| 3 | CET1 consolidato | nessuna minoranza | minority interests riconosciuti **solo entro il cap dell'art. 84 CRR**, RWA consolidati al 100%, avviamento dedotto al 100% |
| 4 | Danish Compromise su AG | catena pulita | condizione dell'art. 49(1)(e)(v) CRR soddisfatta (serve l'inclusione nel perimetro di consolidamento, non il 100%), ma **beneficio in bps diluito**. *Inferenza, v. Parte III* |
| 5 | Trasferimento quota AG a ISP Assicurazioni | atto infragruppo | **OPC di maggiore rilevanza con soglia al 2,5%** (All. 3 § 1.2 Reg. 17221/2010, perché la controparte è la controllante quotata); parere favorevole necessario di un comitato di soli indipendenti; l'esenzione infragruppo dell'art. 14 c. 2 **non è disponibile alla target**; prassi consigliata: eseguire dopo la fusione, il che **posticipa ulteriormente il beneficio Danish** |
| 6 | Remedy Unipol | eseguibile come disegnato | da ridisegnare (§ 11) |
| 7 | Composizione del nuovo CdA | lista unica ISP | **almeno 2 consiglieri** alle liste di minoranza (art. 15 c. 7.1) e **almeno 1** alla minoranza non collegata (c. 7.3); soglia di presentazione 0,5% |
| 8 | Collegio Sindacale | cessa con la fusione | **non sostituibile** in nessuno scenario |
| 9 | Revisori | allineamento deciso dal socio unico | delibera dell'assemblea MPS su proposta motivata del collegio sindacale, con le minoranze che votano |
| 10 | Consolidato fiscale e DTA | da FY2028 in entrambi i casi | in più: l'accordo di consolidamento diventa un'OPC |
| 11 | MREL | semplificazione con la fusione | MPS entità **non** di risoluzione con internal MREL; strumenti già sul mercato di norma non idonei |
| 12 | Dividendi | piena fungibilità | il 25-30% di ogni distribuzione esce dal gruppo |
| 13 | Costi di quotazione e MAR | cessano | doppio perimetro MAR, protocollo di disclosure congiunta, registri insider coordinati |
| 14 | Contenzioso minoranze | assente | **art. 2393-bis c.c. attivabile con il 2,5%**; art. 2373; art. 2497 con onere di provare vantaggi compensativi concreti, certi e quantificabili (Cass. 16707/2004) |

## 10. Nodo B — Il CdA MPS non si dimette

### 10.1 La clausola statutaria governa tutto

L'art. 15 c. 10 dello statuto è una *simul stabunt simul cadent* **attenuata e a effetto differito**:

- **presupposto**: cessazione di **8 amministratori su 15**, per qualunque causa;
- **effetto**: l'intero consiglio è dimissionario con effetto dalla ricostituzione, quindi nessun vuoto
  gestorio;
- **conseguenza procedurale**: art. 2386 c. 4 c.c., l'assemblea per la nomina del nuovo consiglio è
  convocata d'urgenza dagli amministratori rimasti in carica;
- **conseguenza sostanziale**: rinnovo **integrale** con **voto di lista** e termini pieni (40 giorni di
  avviso, 25 di deposito liste, 21 di pubblicazione). **Non esiste la via "revoco 8 e nomino 8 a
  maggioranza semplice"**: il punto è stato deciso nel precedente TIM (Trib. Milano 23 aprile 2018) e
  argomentato nel parere Marchetti;
- **ma la clausola vincola anche il consiglio ostile**: ottenute 8 cessazioni, i 7 superstiti hanno un
  obbligo di legge di convocare, la cui violazione integra "omissione o ingiustificato ritardo" ex art.
  2406 c. 1 c.c. e attiva il dovere del collegio sindacale.

### 10.2 Il collo di bottiglia è la convocazione, non la rimozione

Il vincolo che fissa la data del nuovo consiglio è il **preavviso di 40 giorni** dell'art. 125-bis c. 2
TUF, al cui interno corrono i 25 di deposito e i 21 di pubblicazione delle liste. Quel vincolo opera
**identico** sia con dimissioni sia con revoca, e in entrambi i casi gli amministratori restano in
carica fino all'assemblea. **Il differenziale di tempo fra i due scenari è quindi quasi nullo, a una
condizione: che qualcuno convochi.** Il ritardo dei percorsi ostruzionistici nasce interamente dal
tempo speso per ottenere la delibera di convocazione. È su quel singolo atto che va concentrata la
pressione negoziale e, se serve, il contenzioso.

### 10.3 I percorsi

| Percorso | Meccanismo | Nuovo CdA | Data indicativa | Costo | Rischio |
|---|---|---|---|---|---|
| **0** Convocazione anticipata pre-settlement | Assemblea elettiva convocata prima del settlement, con data e *record date* (7 giorni di borsa aperta ante) successive. Precedente: BPER/Carige, nuovo board 12 giorni dopo il cambio di controllo | t+15/20 | ~25 gen 2027 | basso | richiede collaborazione MPS |
| **A** Dimissioni concordate | Modello Mediobanca 18 settembre 2025: dimissioni a efficacia differita dalla data dell'assemblea, convocazione contestuale, assemblea a 40 giorni esatti | t+42/60 | 25 feb 2027 | *severance* entro i cap prudenziali | basso |
| **B** Revoca assembleare con CdA che convoca | Domanda ex art. 2367 c. 1 c.c. (soglia **5%** per le società che fanno ricorso al mercato del capitale di rischio); "senza ritardo"; revoca e nomina **contestuali** | t+55/80 | inizio mar 2027 | indennizzo (§ 10.5) | medio |
| **C1** Via del Collegio Sindacale | Art. 2406 c. 1 c.c. (obbligo in caso di omissione o ingiustificato ritardo) e **nuovo art. 151.1 c. 1 TUF**: il potere di convocare l'assemblea "può essere esercitato da almeno due componenti" → **2 sindaci su 3**. Precedente TIM 2018 | ~t+90 | apr 2027 | idem | medio |
| **C2** Ricorso al Tribunale delle Imprese | Art. 2367 c. 2 c.c.: decreto che ordina la convocazione e **designa chi deve presiederla**. Sindacato minimo del giudice (Trib. Milano 2 aprile 2016). Competenza: Firenze (*da verificare*) | ~t+120/160 | mag–giu 2027 | idem + spese | medio-alto, ma neutralizza il rischio della presidenza ostile |
| **D** Art. 126-bis TUF su assemblea già convocata | **Non funziona**: i termini del voto di lista (40/25/21) sono incompatibili con il preavviso di 30 giorni dell'assemblea di bilancio. Bloccato nel precedente TIM | — | — | — | da escludere |
| **E** Art. 2393 c. 5 c.c. | Revoca automatica per delibera di azione di responsabilità con un quinto del capitale. **Da evitare**: richiede addebiti nominativi, i revocati non godono di prorogatio (gestione al collegio sindacale con soli poteri ordinari), collide con l'art. 15 c. 10 dello statuto, segnala ingovernabilità a BCE e Banca d'Italia | teoricamente immediato | — | molto alto | **molto alto** |
| **F** Art. 2409 c.c. | **Non disponibile**: l'art. 70 c. 7 TUB lo esclude per le banche, sostituendolo con la denuncia alla Banca d'Italia | — | — | — | precluso |
| **G** Difesa asimmetrica del board | Il consiglio si dimette *per rallentare*, innescando la clausola statutaria e il rinnovo integrale con voto di lista, e presenta la propria lista ex art. 147-ter.1 TUF (delibera con i 2/3 dei componenti, deposito 40 giorni prima). È la mossa TIM 2018. Con ISP oltre il 66% l'esito non è in dubbio | — | — | — | da mettere in conto |

### 10.4 Il limite della direzione e coordinamento: non è una linea di comando sui dipendenti

È il punto operativo più importante del nodo B. Per la capogruppo di un gruppo bancario l'esercizio
della direzione e coordinamento **è un dovere e non solo un diritto** (art. 61 c. 1 TUB), e
l'assoggettamento va reso pubblico ex art. 2497-bis c.c. Ma il perimetro va distinto con precisione:

| Oggetto | L'art. 61 c. 4 TUB funziona? |
|---|---|
| Dati, flussi per il consolidato, reporting package, informativa di vigilanza, ICAAP/ILAAP, accesso delle funzioni di controllo di gruppo | **Sì.** È il contenuto testuale della norma: gli amministratori della controllata "sono tenuti a fornire ogni dato e informazione" e a prestare "la necessaria collaborazione per il rispetto delle norme sulla vigilanza su base consolidata" |
| Scelte di business, campagne commerciali, pricing, obiettivi di rete, decisioni sul personale | **No.** Il potere è funzionalmente circoscritto all'esecuzione delle istruzioni di vigilanza nell'interesse della stabilità del gruppo; la giurisprudenza ha censurato regolamenti di gruppo che ne ricavavano un potere di direzione più ampio |

**Conseguenza.** Finché il consiglio MPS è in carica, l'organo amministrativo e l'amministratore delegato
restano **l'unica fonte legittima di istruzioni** per i dipendenti e i dirigenti di MPS, e sono il datore
di lavoro. Un responsabile di rete che eseguisse istruzioni provenienti da ISP contro le direttive del
proprio consiglio non commetterebbe un illecito verso ISP — non ha alcun rapporto con ISP — ma
un'inadempienza verso il proprio datore di lavoro, con esposizione disciplinare e, nei casi gravi, a un
licenziamento **giuridicamente valido**. Il rischio ricadrebbe sulle persone di MPS, non su ISP.

Tre indicazioni operative: **non chiedere ai dirigenti MPS di bypassare il proprio consiglio** (ciò che
è gestione va chiesto al consiglio, non alla struttura; ciò che è dati e vigilanza è coperto dall'art.
61 c. 4); **tutelare e documentare** chi subisse conseguenze per aver collaborato, perché un atto
ritorsivo alimenta sia la responsabilità ex art. 2392 c.c. sia il dossier di giusta causa; **la leva
della finestra interinale è il dossier documentale, non il comando**.

**Distinzione connessa, facile da perdere**: se si dimette la maggioranza, il consiglio è in
*prorogatio* con poteri pieni (Cass. 8912/2003) ma con il dovere funzionale di adoperarsi per la
ricostituzione. **Se la maggioranza non si dimette non c'è prorogatio affatto**: il consiglio è in
carica a pieno titolo, con mandato fino al 2029 e senza alcuna attenuazione dei poteri né alcun dovere
di adoperarsi. Gli argomenti fondati sulla prorogatio non sono utilizzabili in quello scenario.

**Corollario di pianificazione**: l'asimmetria fra i due scenari non è nei tempi della nomina ma nella
**capacità di governare il business** fra il settlement e l'insediamento. Se il consiglio non si
dimette, ISP nella sostanza **non governa MPS per 50-90 giorni** pur avendone la proprietà.

### 10.5 La revoca: giusta causa e costo

La giusta causa **non è condizione di validità** della revoca (art. 2383 c. 3 c.c.): la revoca è sempre
efficace, e la giusta causa serve solo a escludere il risarcimento. Tre punti fermi:

1. **Il solo cambio di controllo non è giusta causa** (Cass. 21495/2020). **Ma le condotte concrete
   tenute nel corso dell'offerta sono un'altra cosa** e sono il terreno su cui la giusta causa può
   essere costruita: la nozione accolta è quella di "circostanze sopravvenute, anche non integranti
   inadempimento, che pregiudicano l'affidamento". Fatti candidati: misure difensive deliberate dopo il
   settlement, atti ritorsivi verso strutture che collaborano, rifiuto di fornire dati in violazione
   dell'art. 61 c. 4 TUB, ritardo ingiustificato nella convocazione richiesta.
2. **Non può essere addotta dopo** (Cass. 23557/2008, 2037/2018, 21495/2020): le ragioni devono essere
   esplicitate in assemblea e risultare a verbale. **È quindi una scelta binaria da fare prima
   dell'assemblea.**
3. **Il quantum**: Cass. 4586/2023 riconduce il rapporto al mandato e applica l'art. 1725 c. 1 c.c.,
   salvo deroga statutaria o convenzionale espressa, che lo statuto MPS non contiene. Il danno
   all'immagine non è automatico e richiede un *quid pluris* rispetto alla revoca in sé (Cass.
   2037/2018): argomento a favore di una revoca non motivata, in tensione con il punto 1.

**Ordine di grandezza**: la componente consiliare vale circa 2,5 milioni l'anno (presidente più 14
consiglieri), con ~2,2 esercizi residui, quindi 5-6 milioni, più la remunerazione dell'AD e l'eventuale
indennità di fine rapporto. **Su un'offerta da 30,6 miliardi il costo monetario è irrilevante: la
variabile critica è il tempo, non il denaro.** Vincolo da rispettare: politica di remunerazione ex art.
123-ter TUF e Circ. Banca d'Italia 285 (cap in annualità della remunerazione fissa, *malus/clawback*,
approvazione assembleare oltre soglia).

## 11. Il remedy Unipol e il carve-out nei due rami

**L'impegno di Unipol non è condizionato al 90%**: è subordinato al perfezionamento dell'Offerta,
all'adesione di MPS all'Accordo e alle autorizzazioni. Unipol quindi non esce. Cambia però l'oggetto
della compravendita.

**Ramo ≥90%.** MPS, delistata e interamente posseduta, conserva il marchio e può essere *essa stessa*
l'entità ceduta. Il carve-out va nella direzione opposta a quella intuitiva: **non si estrae ciò che si
vende, si estrae ciò che si trattiene** — le circa 625 filiali che restano a ISP, Mediobanca e il resto
del perimetro — lasciando dentro MPS le 635 filiali, le strutture centrali e il marchio; poi si cede il
100% delle azioni MPS. L'estrazione è **interamente infragruppo** in una società al 100%: nessuna
disciplina OPC, nessuna minoranza, nessun profilo ex art. 2497 c.c.

**Ramo sotto-90%.** La strada è preclusa per due ragioni indipendenti: l'"intero capitale" di MPS non è
nella disponibilità di ISP finché esistono minoranze; e cedere il solo pacchetto ISP farebbe superare a
Unipol il 30% di un emittente quotato, con **OPA obbligatoria** ex art. 106 c. 1 TUF sulle azioni
residue. Si ricade sulla struttura alternativa già contemplata dall'Accordo ("*eventualmente*
identificata nello stesso Emittente"): una **newco bancaria** in cui conferire le 635 filiali e le
strutture centrali, con il marchio, e di cui cedere il 100%.

**La newco non deve attendere la fusione**: può essere costituita e alimentata mentre MPS è ancora
quotata, purché il CdA MPS deliberi. Il ritardo è di mesi, non di un anno, **a condizione che la
governance collabori**. Anelli della catena: (1) delibera di adesione di MPS all'Accordo; (2)
autorizzazione all'attività bancaria per il veicolo, art. 14 TUB, iter pluri-mensile; (3) conferimento o
cessione del compendio con lo strumento dell'art. 58 TUB, o in alternativa scissione con assemblea
straordinaria; (4) consultazioni sindacali ex art. 47 L. 428/1990 su 635 filiali; (5) carve-out IT e
separazione operativa. **I punti 3, 4 e 5 esistono in entrambi i rami**, perché anche a ≥90% bisogna
estrarre le 625 filiali trattenute: il costo incrementale del sotto-90% è concentrato
nell'autorizzazione bancaria del veicolo, nell'esecuzione dentro una società quotata con minoranze e
nell'impossibilità di chiudere con una cessione di azioni, che obbliga a rinegoziare con Unipol
l'oggetto del contratto.

**Il vincolo dominante è la scadenza degli impegni antitrust.** Il calendario non lo decidono ISP e
Unipol ma la decisione dell'AGCM, la cui istruttoria approfondita è stata avviata il 14 settembre 2026.
Nella prassi dei remedy la cessione ha una scadenza vincolante e, in caso di sforamento, interviene un
*divestiture trustee* che vende senza vincolo di prezzo minimo. **La tempistica da negoziare va
costruita sullo scenario newco, non su quello semplice**, perché il sotto-90% è il ramo probabile; le
190 filiali ancora identificate solo in via preliminare sono la leva negoziale per allineare perimetro
e termini.

**Rischio prezzo nel ramo sotto-90%.** Conviene che il venditore sia MPS, perché la cessione a Unipol è
verso un terzo e quindi non è un'OPC, mentre far passare ISP come venditore intermedio la
trasformerebbe in un'OPC di maggiore rilevanza. Ma allora MPS incassa i 3-3,5 miliardi e **il 25-30% di
quel valore appartiene economicamente alle minoranze**. Il CdA MPS ha già messo a verbale pubblicamente,
nel comunicato del 16 luglio 2026, che la valorizzazione della rete ceduta è inferiore ai multipli medi
delle banche italiane e che la disaggregazione indebolirebbe il marchio: non è un veto, ma è materiale
documentale per un'azione ex art. 2497 o ex art. 2393-bis c.c. Presidio: processo competitivo
documentato o fairness opinion indipendente, più motivazione analitica ex art. 2497-ter c.c.

**Opzione alternativa da valutare**: cedere il compendio direttamente in un veicolo bancario già
esistente della controparte (BPER, dove Unipol è poco sotto il 30% e dove la banca acquisita è comunque
destinata ad approdare), evitando di autorizzare una banca standalone. Il vincolo è antitrust:
l'Autorità valuta l'idoneità dell'acquirente a ripristinare la concorrenza nei mercati locali, e
trasferire filiali a un operatore già forte negli stessi bacini può non rimediare la concentrazione.

**La voce "finalizzazione carve-out entro aprile-maggio"** del deck riguarda le analisi e la mappatura
del perimetro, e **non dipende dal nodo A ma dal nodo B**: dipende dall'accesso ai dati e alla
collaborazione delle strutture MPS. Conseguenza contabile: se al primo consolidato del 31 marzo 2027 il
veicolo non esiste e il perimetro non è definito, la classificazione **IFRS 5** difficilmente è
sostenibile (manca la disponibilità per la vendita immediata nelle condizioni attuali) e il carve-out
resta gestibile solo in *disclosure*. L'eccezione al termine dei dodici mesi di IFRS 5.9 e B1(a) copre
i ritardi imposti da **terzi**, non quelli riconducibili al venditore.

## 12. La matrice combinata

| | **CdA si dimette** | **CdA non si dimette** |
|---|---|---|
| **≥90%** | **Q1 — Scenario di pag. 4, migliorato.** Nuovo CdA 25 febbraio 2027, o t+20 con convocazione anticipata. Delisting e 100% fra fine febbraio e marzo 2027. Carve-out eseguibile come disegnato. Nessuna OPC, nessuna minoranza nel CET1, Danish pieno, un solo perimetro MAR | **Q2 — Gestibile, ma con un buco di governo.** Sui tempi della nomina cambia poco; il ritardo si materializza solo con ostruzionismo sulla convocazione (fino a t+90). Il costo vero è la finestra interinale. Il delisting **chiude il problema a valle**: al 100% gli organi si sostituiscono in giorni ex art. 2366 c. 4 c.c. |
| **Sotto il 90%** | **Q3 — Ramo probabile.** MPS quotata per 8-15 mesi. Nuovo CdA il 25 febbraio 2027 ma con 2-3 consiglieri di lista di minoranza, che siederanno nel comitato OPC. Delisting via fusione fra set 2027 e mar 2028. Remedy Unipol da ridisegnare | **Q4 — Da evitare attivamente.** Si cumulano consiglio ostile a poteri pieni, minoranze, comitato OPC non allineato e assenza di un delisting che chiuda il problema a valle. Nuovo CdA fra marzo e giugno 2027. Adesione all'Accordo Unipol e delibere di conferimento ostaggio della governance, con **rischio di sforamento degli impegni antitrust** |

| Dimensione | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| Nuovo CdA | 25 feb 2027 (o t+20) | 25 feb – apr 2027 | 25 feb 2027 | mar – giu 2027 |
| Composizione del CdA | interamente ISP | interamente ISP | 2-3 seggi di minoranza | 2-3 seggi di minoranza |
| Governo del business nell'interim | pieno | **assente per 50-90 gg** | pieno | **assente per 50-90 gg** |
| Delisting e 100% | feb–mar 2027 | feb–mar 2027 | set 2027 – mar 2028 | set 2027 – mar 2028 |
| Disciplina OPC | non applicabile | non applicabile | applicabile, soglia 2,5% | applicabile, comitato non allineato |
| Remedy Unipol | cessione del pacchetto MPS | cessione del pacchetto MPS | newco + licenza bancaria | newco, con delibere a rischio |
| Minoranze nel CET1 e Danish | nessun impatto | nessun impatto | cap art. 84 CRR, Danish diluito | idem |
| Rischio dominante | esecuzione | **perdita di governo** | **tempo e OPC** | **inadempimento antitrust** |

**Il collegamento fra i due nodi**: il 90% non è solo la condizione del delisting, è **anche il rimedio
più efficace al nodo B**. Raggiunto il 90% ed eseguita la procedura congiunta, ISP arriva al 100% e MPS
è revocata dalla quotazione: cadono gli obblighi di voto di lista del TUF (l'art. 147-ter si applica
agli emittenti quotati), la riserva statutaria di seggi diventa inoperante per assenza di liste, e con
il capitale interamente rappresentato l'assemblea è regolarmente costituita anche senza formale
convocazione (art. 2366 c. 4 c.c.). *Avvertenza di prudenza*: la clausola statutaria sul voto di lista
resta formalmente vincolante fino a una modifica dello statuto, che per una banca richiede
l'accertamento preventivo ex art. 56 TUB; nel precedente ISP/UBI la procedura da quotata fu svolta per
intero. Il beneficio del 90% sul nodo B è quindi soprattutto la certezza dell'esito e la libertà di ogni
sostituzione successiva, più che la compressione del calendario della prima assemblea.

## 13. Le leve decisionali

**Nel Documento di Offerta, prima dell'approvazione Consob:**

1. **Assoggettamento volontario alla riapertura dei termini ex art. 40-bis c. 1**: doppio beneficio
   (+22/+24 punti nei precedenti; ancoraggio del prezzo della procedura congiunta al corrispettivo
   d'offerta ex art. 50 c. 4 lett. c) se almeno il 50% è conferito in prima fase). Se si supera il 90%
   in prima fase opera comunque l'esenzione automatica. Nessuna controindicazione evidente.
2. **Dimensionamento del periodo di adesione**: 37 giorni su un massimo di 40 azzerano lo spazio di
   proroga; valutare 30-33 giorni.
3. **Riconciliazione del test dell'art. 108 c. 3** rispetto al criterio dichiarato sulle azioni proprie.
4. Conferma delle dichiarazioni ex artt. 111 e 108 c. 2 e della riserva sul diritto transitorio.
5. Valutare se dichiarare esplicitamente l'intenzione di procedere alla fusione nello scenario
   sotto-90%, pesando il *put up or shut up* dell'art. 102 c. 8 TUF.

**Sul remedy, durante l'istruttoria AGCM:** predisporre la struttura newco alternativa prima di
assumere impegni con scadenza; ottenere l'adesione di MPS all'Accordo Unipol come parte del pacchetto di
transizione negoziato con il consiglio uscente.

**Sulla governance, da subito con esecuzione al settlement:** negoziare dimissioni a efficacia differita
di almeno 8 consiglieri con convocazione contestuale; tentare la convocazione anticipata; predisporre il
pacchetto di uscita (severance entro i cap, manleve, D&O run-off a 6 anni) sul modello delle concessioni
fatte in UBI; decidere il numero dei componenti (9 riduce a 2 su 9 il peso statutario minimo delle
minoranze); preparare lista e dossier fit & proper con pre-filing IMAS; al giorno S depositare comunque
la domanda ex art. 2367 c. 1 c.c., inviare la lettera sui doveri al CdA e al collegio, chiedere
l'iscrizione di MPS nel gruppo bancario ex art. 64 TUB.

**Pre-filing con Consob e Borsa Italiana** sulla procedura congiunta a 90% nel periodo transitorio.

## 14. Verifiche di coerenza sulla timeline di pagina 4

- **Data di pagamento**: fra chiusura (4 gennaio) e settlement (6 gennaio) passano 2 giorni, mentre la
  prassi è il **quinto giorno di borsa aperta** (MPS/MB: 8 → 15 settembre 2025; BPER/Sondrio: 11 → 18
  luglio 2025). Se così fosse, il settlement slitta all'11 gennaio e tutta la cascata con esso:
  dimissioni 18 gennaio, avviso 19 gennaio, assemblea 2 marzo.
- **Assenza della riapertura e della procedura congiunta** nella rappresentazione grafica: sono i due
  blocchi che determinano la data effettiva del delisting.
- **Consolidato fiscale**: l'art. 120 c. 2 TUIR richiede che il controllo sussista sin dall'inizio
  dell'esercizio. Con settlement al 6 gennaio 2027 il consolidato decorre da **FY2028**; con settlement
  al 7 dicembre 2026 (scenario di pag. 3) da **FY2027**. Lo scenario 2027 costa quindi un anno intero di
  compensazione ai fini dell'utilizzo delle perdite e delle DTA, voce non presente fra i topic delle
  pagine 5-6. Mitigazione teorica (chiusura anticipata dell'esercizio MPS) esposta a sua volta ai due
  nodi.

---

# PARTE III — APERTO / DA VERIFICARE

> **Non trattare questi punti come acquisiti.** Sono elencati in ordine di rilevanza per le decisioni.

| # | Punto | Stato | Perché conta |
|---|---|---|---|
| 1 | **Testo statutario MPS consolidato** post-4 febbraio 2026 | L'art. 15 è ricostruito dal verbale assembleare; gli artt. 12, 14 e 25 dalla versione precedente, senza riscontro che siano stati modificati | L'art. 15 c. 10 è il perno dell'intero nodo B |
| 2 | **Esito della consultazione Consob** del 18 giugno 2026 | Delibera conclusiva non pubblicata al 16 settembre 2026; attesa fra novembre 2026 e gennaio 2027 | Cade nella finestra del settlement e riscriverà gli artt. 50, 50-bis, 50-ter, 50-quater, 50-quinquies Reg. Emittenti |
| 3 | **Gestione concreta della procedura congiunta a 90% nel transitorio** | L'art. 50-quinquies c. 1 richiama ancora solo l'art. 108 c. 1 | Incide direttamente sulla data del delisting; da chiarire in pre-filing |
| 4 | **Testo consolidato ufficiale del TUF** post-D.Lgs. 47/2026 su Normattiva | Artt. 108 e 111 ricostruiti combinando il decreto con fonti consolidate non ufficiali, fra loro coerenti | Base di tutto il nodo A |
| 5 | **Art. 70 c. 7 TUB** (esclusione dell'art. 2409 c.c. per le banche) | Non verificato sul testo vigente | Elimina un intero strumento dal ventaglio del nodo B |
| 6 | **Competenza territoriale** della Sezione Imprese di Firenze per MPS | Conclusione sistematica ex D.Lgs. 168/2003, non verificata su fonte istituzionale | Percorso C2 |
| 7 | **Lettura del nuovo art. 151.1 c. 1 TUF** (due sindaci, senza il presupposto dei "fatti censurabili di rilevante gravità") | Lettura del nuovo testo da confermare | È il presupposto del percorso C1, il più praticabile in caso di inerzia |
| 8 | **Interazione fra minority interests e Danish Compromise** | **Inferenza analitica**, costruita sul combinato degli artt. 49(1)(e)(v) e 84 CRR e del Report EBA di gennaio 2026. Non risultano Q&A EBA né passaggi della Guida BCE sul punto | Dimensione 4 della tabella § 9.4 |
| 9 | **Data di Pagamento effettiva** indicata nel Documento di Offerta | Non ancora pubblicato | Sposta l'intera cascata di pag. 4 |
| 10 | **Tempi effettivi del procedimento ex art. 2367 c. 2 c.c.** | Nessun dato statistico pubblico; la stima 30-90 giorni è basata sulla struttura del procedimento | Percorso C2 |
| 11 | **Remunerazione dell'AD e indennità di fine rapporto** MPS | Non pubblicamente quantificate; il dato sui compensi consiliari proviene dalla stampa | Stima del costo della revoca |
| 12 | **Computabilità degli acquisti fuori offerta** ex art. 50 c. 9 lett. a) n. ii Reg. Emittenti e coordinamento con le regole sul miglior prezzo (artt. 47-sexies e 47-septies) | Non verificato | Condiziona la strategia di acquisti sul mercato |
| 13 | **Quota Caltagirone**: 10,26% notificato vs 13,49% secondo MPS | Discordanza non risolta | Aritmetica del § 9.1 |
| 14 | **Disponibilità di un veicolo bancario già autorizzato in capo a Unipol** | Dopo la cessione di Unipol Banca a BPER nel 2019 il gruppo non dispone di una banca controllata; BPER è partecipata al ~30% ma non controllata | Tempi della struttura newco |
| 15 | **Orientamenti Consob sulla formula "esclusivamente a seguito di offerta pubblica totalitaria"** applicata ad acquisti post-settlement | Nessuna comunicazione pubblicata reperita | Trappola di pricing del § 9.3 |

---

## Appendice — Materiali e percorsi

| Materiale | Path / riferimento |
|---|---|
| Memo esteso di analisi | `analisi/prj-stradebianche/nodi-what-if-timeline-opas.md` |
| Deck originale (6 slide) | `~/.cursor/projects/workspace/uploads/20260913_ISP_Prj_Stradebianche_scenari_settlement_v.DRAFT__004__1e09.pptx` |
| Comunicato ISP ex art. 102 TUF, testo integrale | `group.intesasanpaolo.com/it/investor-relations/comunicati-stampa-price-sensitive/2026/06/20260608-102-it` |
| Pull request di lavoro | `github.com/rivadiego/rivadiego` PR #6 |

**Giurisprudenza citata**: Cass. 8912/2003 (poteri pieni in prorogatio); Cass. 16707/2004 (vantaggi
compensativi non generici); Cass. 23557/2008 e 2037/2018 (immodificabilità delle ragioni di revoca,
danno all'immagine come *quid pluris*); Cass. 29139/2017 (nessuna preventiva escussione della
eterodiretta); Cass. 24943/2019 (onere probatorio ex art. 2497); Cass. 21495/2020 (cambio di controllo
non è giusta causa); Cass. 4586/2023 (art. 1725 c. 1 c.c. e derogabilità); Trib. Milano 2 aprile 2016
(sindacato minimo sulla convocazione); Trib. Roma 13 novembre 2018 (niente prorogatio per il revocato);
Trib. Milano 23 aprile 2018 e parere Marchetti (inderogabilità del voto di lista nel rinnovo integrale).
