# Relazione Tecnica: Piattaforma di Annotazione “Cospiracy Fullstack”

Una soluzione avanzata, flessibile e fullstack per la raccolta di annotazioni testuali di alta qualità, progettata per ricercatori e annotatori professionisti (es. Prolific).

---

## 🚀 Guida all’Avvio Rapido (Quickstart)

### Prerequisiti

- **Docker & Docker Compose** (scelta consigliata)
- Python 3.10+
- Node.js 18+
- PostgreSQL (Supabase o locale)

### 🐳 Configurazione Docker

Il progetto include diversi setup Docker in base al tuo ambiente:

```bash
# Sviluppo Locale (Solo Database)
docker compose -f 'docker-compose-only-db.yaml' up -d --build 'db'

# Fullstack (Database + Backend + Frontend)
docker compose -f 'docker-compose-fullstack.yaml' up -d --build

# Backend + Frontend (Collegamento a Database Esterno/Supabase)
docker compose -f 'docker-compose-supabase-setup.yml' up -d --build
```

### 🐍 Backend Setup (Sviluppo Locale)

```bash
cd backend
python -m venv venv
./venv/Scripts/Activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### ⚛️ Frontend Setup (Sviluppo Locale)

```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 Panoramica del Sistema

La piattaforma è progettata per gestire diversi tipi di annotazione (Sentiment, NER, Teorie del Complotto) senza dover modificare il codice sorgente. La configurazione dell'interfaccia, delle etichette e della logica di distribuzione avviene dinamicamente a livello di **Progetto** tramite l'Admin Panel.

### Pipeline dell'Annotatore

Il sistema guida l'utente attraverso un flusso prestabilito:

1. **Consenso Informato**: Pagina legale obbligatoria.
2. **Screening (Demographics)**: Raccolta di dati anagrafici e metadati.
3. **Codebook**: Studio del materiale teorico e delle definizioni (formato Markdown).
4. **Istruzioni & Practice**: Guida pratica con feedback immediato su task di esempio.
5. **Annotazione Reale**: Ciclo continuo di documenti con iniezione di **Gold Units** per il controllo qualità.
6. **Completamento**: Reindirizzamento automatico a Prolific con codice di completamento.

---

## 🛠️ Architettura e Tecniche Avanzate

### 1. Configurazione "No-Code" dei Task

I ricercatori possono caricare file JSON o Markdown direttamente dall'Admin per definire:

- **Task Type**: `classification`, `ner`, o `hybrid`.
- **Interfaccia Dinamica**: Etichette, colori, hover hints e domande a scelta multipla.
- **Workflow Modulare**: Possibilità di abilitare/disabilitare screening, codebook o training per ogni singolo progetto.

### 2. Strategie di Distribuzione (Redundancy Management)

Il sistema supporta tre modalità di assegnazione dei documenti:

- **STANDARD (Crowdsourcing)**: I documenti vengono pescati casualmente fino al raggiungimento del limite `max_annotations_per_doc`. Ottimo per ottimizzare i costi.
- **FULL_OVERLAP (Pilot Study)**: Ogni annotatore vede ogni documento del progetto. Ideale per calcolare l'accordo tra esperti.
- **SAME_ANNOTATORS (Block-based)**: I documenti vengono divisi in blocchi (es. 10 doc). Un blocco viene assegnato a _k_ annotatori fissi. Essenziale per studi di affidabilità controllata.

### 3. Controllo Qualità (QC) & MACE

La piattaforma integra strumenti d'avanguardia per gestire il rumore dei dati:

- **Gold Units Injection**: Iniezione automatica di documenti con soluzione nota per testare l'accuratezza in tempo reale. Se un annotatore scende sotto una soglia (es. 60%), viene automaticamente escluso.
- **MACE (Multi-Annotator Competence Estimation)**: Algoritmo di inferenza bayesiana che stima la competenza di ogni annotatore e deduce il "vero" label pesando le risposte dei partecipanti più affidabili.
- **Time Tracking**: Ogni annotazione registra i millisecondi impiegati per identificare bot o "clickers" compulsivi.

### 4. Gestione della Concorrenza (Fetch-then-Lock)

Per evitare che più utenti ricevano lo stesso documento sforando i limiti di ridondanza, il backend adotta un pattern `select_for_update(skip_locked=True)`. Questo garantisce alte prestazioni e coerenza dei dati anche con centinaia di annotatori simultanei.

---

## 📊 Modelli Dati Principali (`backend/annotation/models.py`)

- **`Project`**: Il container della campagna (configurazione UI, strategia, file .jsonl).
- **`Annotator`**: L'utente (Prolific PID), traccia lo stato globale (consent, screening).
- **`ProjectEnrollment`**: Traccia il progresso del singolo utente su uno specifico progetto (accuratezza gold, strikes, ranking MACE).
- **`Document`**: L'unità testuale. Supporta proxy per distinguere tra `Standard Items` e `Gold Units`.
- **`Annotation`**: Il payload JSON dell'annotazione, inclusi spans (start/end) e tempi di esecuzione.

---

## 🎨 Admin Interface (Premium experience)

Grazie a `django-unfold`, l'interfaccia di amministrazione offre:

- **Dashboard Organizzate per Tab**: Dettagli, Training, Task Config, Quality, Log e Launch.
- **Visualizzatore Config**: Rendering colorato dei JSON di configurazione direttamente nel browser.
- **Inline Statistics**: Visualizzazione immediata di avanzamento, numero di lavoratori attivi e accuratezza media.
- **Quick Import/Export**: Caricamento dataset via `.jsonl` e download dei risultati pronti per l'analisi.

---

## 🔗 Accesso Rapido (Link Utili)

- **Admin Panel**: `http://localhost:8000/admin/`
- **Link di Test (Project #1)**: `http://localhost:5173/?PROLIFIC_PID=TEST_USER&project_id=1`
- **Esportazione Risultati**: Disponibile direttamente dalla lista progetti nell'Admin via pulsante `⬇ JSONL`.

---
