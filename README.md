# Relazione Tecnica: Piattaforma di Annotazione “Cospiracy Fullstack”


## Guida all’Avvio (Quickstart)

### Prerequisiti

- Python 3.10+
- Node.js 18+
- PostgreSQL (o SQLite per default)

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows
./venv/Scripts/Activate
# Installazione dipendenze
pip install -r requirements.txt
# Migrazioni DB
python manage.py migrate
# Creazione Superuser
python manage.py createsuperuser
# Avvio Server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Accesso alla Piattaforma

Per simulare un utente Prolific sul Progetto #1:
`http://localhost:5173/?PROLIFIC_PID=TEST_USER_001&project_id=1`

---


## 1. Introduzione e Obiettivi

Il progetto consiste nello sviluppo di una piattaforma web fullstack per la raccolta di annotazioni testuali (es. sentiment analysis, NER, classificazione di teorie del complotto). L’obiettivo è fornire un’interfaccia intuitiva per gli annotatori (reclutati ad esempio via Prolific) e un pannello di controllo potente per i ricercatori.

La piattaforma è progettata per essere **agnostica rispetto al task**:

la configurazione dell'interfaccia (etichette, colori, tipo di domande) è definita dinamicamente a livello di **Progetto** tramite JSON nel backend. Questo permette di gestire campagne di annotazione diverse (es. una per NER, una per Classificazione) semplicemente creando nuovi progetti, senza dover modificare una riga di codice nel frontend.

---

## 2. Architettura del Sistema

### 2.1 Backend (Django & Django REST Framework)

Il cuore del sistema è un’applicazione Django che espone API RESTful.

### Modelli Principali (`backend/annotation/models.py`)

1. **`Project`**: Definisce il contenitore per un set di documenti. Con i seguenti campi.

   ```json
   name
   description
   configuration
   configuration_file
   STRATEGY_CHOICES
   distribution_strategy
   min_annotations_per_doc
   max_annotations_per_doc
   prioritize_unannotated
   dataset_file
   created_at
   ```

   - **Configurazione Dinamica**: Un campo `JSONField` (`configuration`) controlla l'interfaccia utente (etichette, colori, istruzioni).
   - **Nota**: La configurazione è legata al Progetto, quindi tutti i documenti di un progetto condividono lo stesso task (es. tutti NER o tutti Classificazione).
   - **Strategia di Distribuzione**
     **Validazione Preliminare:**
     - Verifica esistenza di `prolific_pid` e `project_id`.
     - **Check Ban/Esclusione:** Se l'annotatore ha il flag `exclude_from_distribution` attivo (es. bannato per scarsa qualità), il sistema restituisce immediatmente lo status `stopped`.
     - **Check Quota Personale:** Verifica se l'utente ha già raggiunto il suo `target_tasks` (es. 20 documenti). Se sì, restituisce lo status `completed` con il link di completamento per Prolific.
     Il sistema supporta diverse modalità (`STANDARD`, `FULL_OVERLAP`, `METADATA_MATCH`) per assegnare i documenti agli utenti.
     **1. `STANDARD` (Pool Pubblico - Default)**
     Questa è la modalità classica di crowdsourcing
     - **Obiettivo:** Raggiungere un target di annotazioni per ogni documento (es. 3 persone diverse).
     - **Funzionamento:**
       1. Il sistema cerca tutti i documenti che **NON** hanno ancora raggiunto il numero massimo di annotazioni `max_annotations_per_doc`.
       2. Esclude quelli che l'utente corrente ha già fatto.
       3. Se è attiva l'opzione  (**`Prioritize unannotated`**), sceglie prima i documenti che hanno **0 annotazioni**.
       4. Altrimenti, pesca casualmente dal pool disponibile.
     **2. `FULL_OVERLAP` (Alta Ridondanza)**
     Questa modalità ignora i contatori di quante persone hanno visto un documento. È utile per studi pilota o test di accordo tra annotatori (Inter-Annotator Agreement).
     - **Obiettivo:** Far sì che ogni documento venga visto dal maggior numero possibile di persone, senza limiti.
     - **Funzionamento:**
       1. Il sistema considera **tutti** i documenti del progetto.
       2. L'unico filtro applicato è escludere quelli che l'utente corrente ha già annotato (per non fargli rifare lo stesso lavoro).
       3. Sceglie un documento a caso tra quelli rimanenti.
     **3. `METADATA_MATCH` (Assegnazione per Gruppi)**
     Questa è la modalità più avanzata e permette di segmentare la forza lavoro in base a caratteristiche specifiche.
     - **Obiettivo:** Assegnare specifici sotto-insiemi di documenti a specifici gruppi di utenti.
     - **Funzionamento:**
       1. Il sistema legge i metadati dell'annotatore, passati _si presuppone_ da prolific stesso, oppure un nostro appunto per premiare qualificatori bravi.

          ```
          {"group": "expert"}
          ```

       2. Filtra i documenti che hanno lo stesso tag nei loro metadati (es. ).

          ```
          metadata__group="expert"
          ```

       3. Tra questi, applica la logica standard (rispettando i limiti di annotazioni massime).
     - **Uso Tipico:** riservare documenti difficili solo ad annotatori esperti/qualificati.
     ***
     ### **Nota Importante: Le "Gold Units"**
     Indipendentemente dalla strategia scelta, il sistema ha una direttiva da rispettare sempre:
     - Prima di applicare qualsiasi logica sopra descritta, il sistema controlla se ci sono **Gold Units** (documenti di controllo qualità) che l'utente non ha ancora visto.
     - Se ce ne sono, queste vengono assegnate con **priorità assoluta**. Questo garantisce che tu possa misurare la qualità dell'annotatore fin dalle prime fasi della sessione.
   - **Gestione della concorrenza**
     **3.2 Gestione della Concorrenza: Pattern "Fetch-then-Lock"**
     La gestione della concorrenza è critica per evitare che due utenti ricevano lo stesso documento contemporaneamente, sforando il limite `max_annotations_per_doc`.
     Il codice risolve il problema delle limitazioni di PostgreSQL/Django (che non permettono `select_for_update` su query contenenti aggregazioni come `Count` o `Group By`) adottando un approccio a due fasi:
     1. **Identificazione (No Lock):** Si esegue la query complessa (con i filtri `annotate` e `order_by`) solo per recuperare la chiave primaria (`id`) del documento candidato. Questa query è leggera e non blocca la tabella.
     2. **Lock Chirurgico:** Una volta ottenuto l'`id`, si esegue una seconda query puntuale:Python

        `Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()`

        L'uso di `skip_locked=True` è fondamentale per la User Experience: se il documento `target_id` è oggetto di scrittura da parte di un altro processo in quel micro-secondo, il sistema non mette l'utente in attesa (che causerebbe latenza), ma ignora il record.

2. **`Document`**: Il singolo task che contiene il testo da annotare.

   ```json
   id
   project
   text
   external_id
   metadata
   is_gold_unit
   gold_solution
   min_annotations_required
   current_annotations_count
   ```

   - **Gold Units**: Flag `is_gold_unit` per identificare documenti di controllo qualità (con risposta nota).

3. **`Annotator`**: Rappresenta l’utente (identificato dal `prolific_pid`).

   ```json
   prolific_pid
   metadata
   consent_accepted
   onboarding_completed
   target_tasks
   created_at
   ```

   - Traccia lo stato del workflow: `consent_accepted`, `onboarding_completed`.

4. **`Annotation`**: Memorizza il risultato dell’annotazione.

   ```json
   id
   document
   annotator
   result
   milliseconds_to_complete
   created_at
   ```

   - Salva i dati in formato JSON flessibile.
   - Registra i tempi di esecuzione (`milliseconds_to_complete`) per filtrare bot o annotatori disattenti.
   - Spiegazione tecnica
     Quando un utente invia un'annotazione che include evidenziazioni (NER/Span tasks), il salvataggio avviene in questo formato standardizzato all'interno di `result`:
     ```json
     {
       "classification": "Yes",
       "spans": [
         {
           "start": 10, // Indice carattere inizio (inclusive)
           "end": 25, // Indice carattere fine (exclusive)
           "label": "Actor", // L'etichetta semantica (es. "Actor", "Action")
           "text": "The government" // Il testo esatto evidenziato (per controllo/debug)
         },
         {
           "start": 45,
           "end": 52,
           "label": "Victim",
           "text": "citizens"
         }
       ]
     }
     ```
     ### **2. Ruolo della Configurazione del Progetto**
     Nel backend, il campo configuration del progetto definisce quali etichette sono disponibili. Esempio di configurazione JSON
     ```json
     {
       "task_type": "hybrid",
       "span_labels": [
         { "name": "Actor", "color": "#FF5733" },
         { "name": "Action", "color": "#33FF57" },
         { "name": "Victim", "color": "#3357FF" },
         { "name": "Threat", "color": "#FF33F6" },
         { "name": "Evidence", "color": "#FFA500" }
       ],
       "class_labels": [
         { "label": "Conspiracy", "value": "Yes" },
         { "label": "Not Conspiracy", "value": "No" },
         { "label": "Ambiguous", "value": "Can't tell" }
       ]
     }
     ```
     ### **3. Flusso Tecnico Frontend -> Backend**
     1. **Frontend ()**:

        `TextHighlighter.vue`
        - Quando l'utente seleziona del testo, il componente calcola gli indici **start** e **end** relativi al testo originale del documento.
        - Associa a questa selezione l'etichetta correntemente attiva (es. "Actor").
        - Crea un oggetto JavaScript: .
          ```
          { start: 10, end: 25, label: "Actor", text: "..." }
          ```
        - Questo oggetto viene aggiunto all'array  nello stato locale (**AnnotatorView.js**).

     2. **Invio (AnnotatorView.js -> SubmitAnnotation)**:
        - Al click su "Submit", l'intero array  viene impacchettato dentro  e inviato via POST all'API .
     3. **Salvataggio (SubmitAnnotation in views.py)**:
        - Il backend riceve il JSON grezzo.
        - **Non fa validazione profonda** sul contenuto degli span (es. non controlla se gli indici sono validi rispetto al testo) per performance, ma si fida del frontend.
        - Salva il JSON nel campo  del modello **Annotation**.

### Admin Interface (`django-unfold`)

Il pannello di amministrazione è stato personalizzato con `django-unfold` per offrire una UI moderna e “premium”. Include dashboard per il monitoraggio del progresso e strumenti di import/export dei dati.

### Flusso Utente

1. **Login Automatico**: Il sistema rileva parametri URL (`PROLIFIC_PID`, `project_id`) ed esegue l’auto-login/registrazione.
2. **Consenso Informato**: Pagina obbligatoria per nuovi utenti.
3. **Istruzioni/Onboarding**: Tutorial specifico per il task.
4. **Interfaccia di Annotazione (`AnnotatorView`)**:
   - Renderizza dinamicamente gli input (Radio, Checkbox, Text Highlighting) in base alla configurazione JSON del progetto ricevuta dal backend.
   - Include un **Timer** invisibile che calcola i millisecondi impiegati per ogni annotazione.
5. **Submit & Next**: Invio dei dati e caricamento immediato del prossimo documento.
6. **Completamento**: Redirect automatico alla piattaforma di reclutamento (es. Prolific) al raggiungimento del target.

---

## 3. Peculiarità e Dettagli Implementativi

### 3.1 Configurazione “No-Code” dei Task

Il file `default_project_config.json` o il campo nel DB permettono di definire:

- `task_type`: “classification”, “ner”, “hybrid”.
- `span_labels`: Etichette per l’evidenziatore (nome e colore).
- `class_labels`: Opzioni per domande a scelta multipla.
- `scale`: Configurazione per domande di tipo Likert (scale 1-5, 1-7, ecc.).

---
