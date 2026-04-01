# FULL CODEBASE CONTEXT

## DIRECTORY STRUCTURE
- cospiracy-fullstack/
  - .dockerignore
  - .env
  - .env.example
  - .gitignore
  - docker-compose-fullstack.yml
  - docker-compose-only-db.yaml
  - docker-compose-supabase-setup.yml
  - Dockerfile.backend
  - Dockerfile.frontend
  - full_codebase_context.md
  - README.md
  - backend/
    - manage.py
    - requests.http
    - requirements.txt
    - test_mace_script.py
    - annotation/
      - apps.py
      - gold_strategies.py
      - mace.py
      - mace_service.py
      - models.py
      - serializers.py
      - services.py
      - signals.py
      - tests.py
      - urls.py
      - views.py
      - __init__.py
      - admin/
        - annotation.py
        - annotator.py
        - document.py
        - enrollment.py
        - project.py
        - utils.py
        - __init__.py
      - management/
        - __init__.py
        - commands/
          - seed_demo.py
          - __init__.py
      - migrations/
        - 0001_initial.py
        - 0002_remove_project_is_active.py
        - 0003_remove_project_gold_config_and_more.py
        - 0004_remove_project_continuous_exclusion_and_more.py
        - 0005_project_enable_practice_task.py
        - __init__.py
      - static/
        - css/
          - admin_project.css
        - js/
          - admin_project.js
    - backend/
      - asgi.py
      - settings.py
      - urls.py
      - wsgi.py
      - __init__.py
    - config_defaults/
      - codebook_somiglianza_item.md
      - config_example.yaml
      - default_gold_config.json
      - default_instructions_content.md
      - default_practice_task.json
      - default_project_config.json
      - default_screening_config.json
    - config_tests_files/
      - default_project_config.json
      - default_screening_config.json
  - frontend/
    - .env.development
    - .env.production
    - .gitignore
    - index.html
    - nginx.conf
    - package.json
    - README.md
    - tsconfig.app.json
    - tsconfig.json
    - tsconfig.node.json
    - vite.config.ts
    - public/
      - vite.svg
    - src/
      - App.vue
      - axios.js
      - main.ts
      - router.js
      - style.css
      - assets/
        - shared.css
        - vue.svg
      - components/
        - HelloWorld.vue
        - TextHighlighter.vue
      - composables/
        - useMarkdownRenderer.js
        - useProjectContext.js
      - views/
        - AnnotatorView.vue
        - CodebookView.vue
        - ConsensFullPage.vue
        - ConsentView.vue
        - InstructionsView.vue
        - LoginView.vue
        - ScreeningView.vue
  - tmp/
    - create_context.py

---

## FILE CONTENTS

### FILE: .dockerignore
```
# Ignora le cartelle degli ambienti virtuali locali
venv/
.venv/
env/

# Ignora i file compilati di Python
__pycache__/
*.pyc
*.pyo

# Ignora le cartelle del frontend inutili per il backend
frontend/node_modules/
frontend/dist/

# Ignora i file di sistema e IDE
.git/
.vscode/
.idea/
.DS_Store
```

---

### FILE: .env
```
# Backend - General settings
DEBUG=1
SECRET_KEY=django-insecure-your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# CORS & CSRF Settings
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080,http://localhost:80
CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://localhost:80

# Database Settings
POSTGRES_HOST=127.0.0.1
POSTGRES_DB=db
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_PORT=5432

```

---

### FILE: .env.example
```
# Backend - General settings
DEBUG=1
SECRET_KEY=django-insecure-your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# CORS & CSRF Settings
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080,http://localhost:80
CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://localhost:80

# Database Settings
POSTGRES_HOST=127.0.0.1
POSTGRES_DB=db
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_PORT=5432

```

---

### FILE: docker-compose-fullstack.yml
```
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    volumes:
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
    expose:
      - 8000
    depends_on:
      - db

  nginx:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    volumes:
      - static_volume:/app/staticfiles
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_PORT=${POSTGRES_PORT}
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}" ]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  static_volume:
  postgres_data:

```

---

### FILE: docker-compose-only-db.yaml
```
services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_PORT=${POSTGRES_PORT}
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}" ]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

```

---

### FILE: docker-compose-supabase-setup.yml
```
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    volumes:
      - static_volume:/app/staticfiles
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
    expose:
      - 8000

  nginx:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    volumes:
      - static_volume:/app/staticfiles
    depends_on:
      - backend

volumes:
  static_volume:
```

---

### FILE: Dockerfile.backend
```
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

### FILE: Dockerfile.frontend
```
# -----------------------------------------------------------
# Stage 1: Build (Compilation)
# -----------------------------------------------------------
FROM node:lts-alpine AS builder

WORKDIR /app

COPY frontend/ .

RUN npm install

RUN npm run build

# -----------------------------------------------------------
# Stage 2: Runtime (Nginx Server)
# -----------------------------------------------------------
FROM nginx:stable-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

### FILE: full_codebase_context.md
```

```

---

### FILE: README.md
```
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

```

---

### FILE: backend\manage.py
```
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv

def main():
    """Run administrative tasks."""
    load_dotenv()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

---

### FILE: backend\test_mace_script.py
```
import os
import sys
import django
from dotenv import load_dotenv

# Setup Django environment
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from annotation.models import Project, Annotator, Document, Annotation, ProjectEnrollment
from annotation.mace_service import run_mace_for_project

def run():
    print("=== SETUP MACE TEST ===")
    
    # 1. Clean up old test data if exists
    Project.objects.filter(name="MACE Test Project").delete()
    Annotator.objects.filter(prolific_pid__in=["EXPERT_A", "AVERAGE_B", "SPAMMER_C"]).delete()

    # 2. Create a dummy project
    project = Project.objects.create(name="MACE Test Project", description="Testing MACE")
    
    # 3. Create 15 documents
    docs = []
    # Arbitrary ground truth (hidden from MACE naturally)
    true_labels = [
        "Yes", "No", "Yes", "Yes", "No", 
        "Ambiguous", "Yes", "No", "Ambiguous", "Yes",
        "No", "No", "Yes", "Ambiguous", "No"
    ]
    
    for i in range(15):
        doc = Document.objects.create(project=project, text=f"Document {i}", external_id=f"doc_{i}")
        docs.append(doc)
        
    # 4. Create annotators
    # A is an EXPERT (always agrees with truth)
    # B is AVERAGE (makes some mistakes, maybe 70% accuracy)
    # C is a SPAMMER (always answers "Yes" regardless of the text)
    annotator_a = Annotator.objects.create(prolific_pid="EXPERT_A")
    annotator_b = Annotator.objects.create(prolific_pid="AVERAGE_B")
    annotator_c = Annotator.objects.create(prolific_pid="SPAMMER_C")
    
    ProjectEnrollment.objects.create(project=project, annotator=annotator_a)
    ProjectEnrollment.objects.create(project=project, annotator=annotator_b)
    ProjectEnrollment.objects.create(project=project, annotator=annotator_c)
    
    # 5. Create annotations
    for i, doc in enumerate(docs):
        truth = true_labels[i]
        
        # Expert A is basically 100% correct
        a_label = truth
        Annotation.objects.create(document=doc, annotator=annotator_a, result={"classification": a_label})
        
        # Average B makes some mistakes
        b_label = truth if i % 3 != 0 else "Yes" 
        Annotation.objects.create(document=doc, annotator=annotator_b, result={"classification": b_label})
        
        # Spammer C always says "Yes" 
        Annotation.objects.create(document=doc, annotator=annotator_c, result={"classification": "Yes"})
        
    # 6. Run MACE
    print(f"\nCreated {len(docs)} documents and 3 annotators.")
    print("Running MACE algorithm...")
    result = run_mace_for_project(project.id)
    print("Result:", result)
    
    # 7. Check results
    print("\n=== MACE EVALUATION RESULTS ===")
    print("\n--- Annotator Competence ---")
    for pid in ["EXPERT_A", "AVERAGE_B", "SPAMMER_C"]:
        enrollment = ProjectEnrollment.objects.get(project=project, annotator__prolific_pid=pid)
        score = enrollment.mace_competence_score or 0.0
        bias = enrollment.mace_spam_bias.get("strategy", {})
        print(f"Annotator {pid:10}: Competence = {score:.3f}")
        # Show what they do when they guess
        if "Yes" in bias:
            print(f"  -> When guessing, probability of saying 'Yes': {bias['Yes']:.2f}")

    print("\n--- Document Predictions ---")
    correct_predictions = 0
    for i, doc in enumerate(docs):
        doc.refresh_from_db()
        mace_pred = doc.mace_gold_label
        truth = true_labels[i]
        conf = doc.mace_confidence or 0.0
        is_correct = mace_pred == truth
        if is_correct:
            correct_predictions += 1
            
        mark = "✅" if is_correct else "❌"
        print(f"Doc {i:2} [Truth: {truth:9}] | MACE: {mace_pred:9} (Conf: {conf:.2f}) {mark}")
        
    print(f"\nFinal Accuracy of MACE relative to Ground Truth: {correct_predictions}/{len(docs)} ({(correct_predictions/len(docs))*100:.1f}%)")
    print("Notice how MACE filters out the Spammer C (who gets low competence) and mostly trusts A and B!")

if __name__ == '__main__':
    run()

```

---

### FILE: backend\annotation\apps.py
```
from django.apps import AppConfig


class AnnotationConfig(AppConfig):
    name = 'annotation'

    def ready(self):
        import annotation.signals

```

---

### FILE: backend\annotation\gold_strategies.py
```
"""
Gold Unit Evaluation Strategies
================================
Implements the Strategy pattern for evaluating annotator quality
based on their gold unit performance.

Each strategy is a pure function:
    (enrollment, gold_config, is_correct) -> (should_exclude, reason)

The system ships with default strategies but researchers can configure
which one to use per-project via `gold_config.evaluation_strategy`.
"""


def evaluate_percentage(enrollment, gold_config, is_correct):
    """
    Percentage-based evaluation.
    Excludes the annotator if their cumulative gold accuracy drops
    below `min_accuracy_required` after at least `min_gold_before_eval` gold tasks.
    
    Config keys used:
        - min_accuracy_required: float (default 0.6)
        - min_gold_before_eval: int (default 3)
    """
    min_accuracy = gold_config.get('min_accuracy_required', 0.6)
    min_gold = gold_config.get('min_gold_before_eval', 3)

    # Update cumulative accuracy
    total = enrollment.gold_tasks_completed
    prev_acc = enrollment.gold_accuracy or 0.0
    prev_correct = prev_acc * (total - 1) if total > 1 else 0
    current_correct = prev_correct + (1 if is_correct else 0)
    new_acc = current_correct / total if total > 0 else 0.0

    enrollment.gold_accuracy = new_acc

    # Evaluate: Always exclude if below threshold after min gold tasks
    if total >= min_gold and new_acc < min_accuracy:
        return True, f"Accuracy {new_acc:.1%} below threshold {min_accuracy:.0%} after {total} gold tasks."
    
    return False, None


# --- STRATEGY REGISTRY ---

STRATEGIES = {
    'percentage': evaluate_percentage,
}


def get_strategy(strategy_name='percentage'):
    """
    Returns the evaluation function for the given strategy name.
    Now only supports 'percentage'.
    
    Usage:
        strategy = get_strategy()
        should_exclude, reason = strategy(enrollment, gold_config, is_correct)
    """
    return evaluate_percentage


def check_gold_correctness(annotation_result, gold_solution):
    """
    Compares the annotator's result against the gold solution.
    Currently checks classification match. Can be extended for span-level evaluation.
    
    Returns: bool (True if correct)
    """
    if not gold_solution:
        return False
    
    user_class = annotation_result.get('classification')
    gold_class = gold_solution.get('classification')
    
    if user_class is None or gold_class is None:
        return False
    
    return user_class == gold_class

```

---

### FILE: backend\annotation\mace.py
```
#!/usr/bin/env python3
"""
MACE: Multi-Annotator Competence Estimation

MACE is an Expectation-Maximization (EM) algorithm that simultaneously:
- Learns the most likely true labels for items from multiple annotators
- Estimates the competence (reliability) of each annotator

The algorithm models annotators as either "knowing" the correct answer or "guessing"
according to a spamming strategy. It uses EM to iteratively:
1. E-step: Compute expected counts of knowing vs. guessing for each annotator
2. M-step: Update competence estimates and spamming strategies

Features:
- Supports discrete categorical labels (default) and continuous numeric values
- Can incorporate control items (known ground truth) for semi-supervised learning
- Provides confidence estimates via entropy calculations
- Handles missing annotations (empty cells in CSV)

Input Format:
- CSV file with one instance per line
- Each column represents one annotator
- Empty cells indicate missing annotations

Output:
- Predictions: Consensus labels or weighted averages (continuous mode)
- Competence scores: Reliability estimate for each annotator (0-1, higher = more reliable)
- Entropies: Uncertainty measure for each instance (optional)

Original Version: Natural Language Group, April 2013
Current Version: Natural Language Group, April 2013

Copyright (c) 2013 by the University of Southern California
All rights reserved.

Python port of the Java implementation via Cursor, modified to work with Python 3.14, 16 Jan 2026.

Reference:
    Hovy, D., Berg-Kirkpatrick, T., Vaswani, A., & Hovy, E. (2013).
    Learning Whom to Trust With MACE. In: Proceedings of NAACL-HLT.
"""

import sys
import argparse
import time
import numpy as np
from scipy.special import digamma

VERSION = "0.5"

# Defaults
DEFAULT_RR = 10
DEFAULT_ITERATIONS = 50
DEFAULT_NOISE = 0.5
DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.5


class MACE:
    """
    Multi-Annotator Competence Estimation using EM algorithm.
    
    This class implements the MACE algorithm for aggregating annotations from
    multiple sources while estimating the reliability of each annotator.
    
    Attributes:
        num_instances (int): Number of items/instances to label
        num_annotators (int): Number of annotators
        num_labels (int): Number of unique labels
        spamming (np.ndarray): [num_annotators, 2] probability of guessing vs knowing
        thetas (np.ndarray): [num_annotators, num_labels] spamming strategy distribution
        gold_label_marginals (np.ndarray): [num_instances, num_labels] posterior label probabilities
        log_marginal_likelihood (float): Log likelihood of the data under current model
    
    Example:
        >>> mace = MACE('annotations.csv')
        >>> mace.initialize(0.5)
        >>> mace.run(iterations=50, smoothing=0.01, num_restarts=10, ...)
        >>> predictions = mace.decode(threshold=1.0)
    """
    
    def __init__(self, csv_file, continuous=False):
        """
        Initialize MACE model from CSV file.
        
        Reads annotation data from a CSV file where:
        - Each row represents one instance/item
        - Each column represents one annotator
        - Values are annotations (labels or numeric values)
        - Empty cells indicate missing annotations
        
        Args:
            csv_file (str): Path to CSV file with annotations
            continuous (bool): If True, interpret values as continuous numeric.
                              Returns weighted averages instead of discrete labels.
                              All values must be valid numbers.
        
        Raises:
            IOError: If file cannot be read or has invalid format
            IOError: If continuous=True but non-numeric values found
        
        Example:
            >>> # Discrete labels
            >>> mace = MACE('labels.csv')
            >>> # Continuous values
            >>> mace = MACE('scores.csv', continuous=True)
        """
        self.continuous = continuous
        self.num_instances = self._file_line_count(csv_file)
        
        self.labels = [None] * self.num_instances
        self.who_labeled = [None] * self.num_instances
        # For continuous mode: store original numeric values
        self.continuous_values = [None] * self.num_instances if continuous else None
        
        # Hash stuff
        self.string2int = {}
        self.int2string = []
        self.hash_counter = 0
        
        # Initialize num_annotators before reading file
        self.num_annotators = 0
        
        # Read in CSV file to get all basic information
        self._read_file_data(csv_file)
        
        self.num_labels = len(self.int2string)
        
        if self.num_annotators == 0:
            raise IOError("No annotators found in CSV file!")
        if self.num_labels == 0:
            raise IOError("No labels found in CSV file!")
        
        self.gold_label_marginals = np.zeros((self.num_instances, self.num_labels))
        self.strategy_expected_counts = np.zeros((self.num_annotators, self.num_labels))
        self.knowing_expected_counts = np.zeros((self.num_annotators, 2))
        
        # Parameters
        self.spamming = None
        self.thetas = None
        
        # Priors
        self.theta_priors = None
        self.strategy_priors = None
        self.label_priors = None  # Prior probabilities for labels (normalized)
        
        self.log_marginal_likelihood = 0.0
    
    def _compute_weighted_stats(self, d):
        """
        Compute weighted statistics for continuous mode instance.
        
        Args:
            d (int): Instance index
        
        Returns:
            tuple: (weighted_mean, weighted_std, min_val, max_val, n_annotators)
                   or None if instance has no annotations
        """
        if self.continuous_values[d] is None or len(self.continuous_values[d]) == 0:
            return None
        
        annotators = self.who_labeled[d]
        values = self.continuous_values[d]
        competences = self.spamming[annotators, 1]
        
        weighted_sum = np.sum(values * competences)
        total_weight = np.sum(competences)
        
        if total_weight > 0:
            weighted_mean = weighted_sum / total_weight
            weighted_variance = np.sum(competences * (values - weighted_mean)**2) / total_weight
            weighted_std = np.sqrt(weighted_variance) if weighted_variance > 0 else 0.0
        else:
            weighted_mean = np.mean(values)
            weighted_std = np.std(values)
        
        return (weighted_mean, weighted_std, np.min(values), np.max(values), len(values))
    
    def initialize(self, init_noise, alpha=None, beta=None):
        """
        Initialize model parameters with random values.
        
        Initializes the spamming probabilities and strategy distributions for each
        annotator. Parameters are randomly initialized with noise to break symmetry
        and then normalized to be valid probability distributions.
        
        Args:
            init_noise (float): Amount of random noise to add (typically 0.5).
                              Higher values create more diverse initializations.
            alpha (float, optional): First hyperparameter for beta prior on knowing
                                    probability. Used for variational inference (default mode).
            beta (float, optional): Second hyperparameter for beta prior on knowing
                                   probability. Used for variational inference (default mode).
        
        Note:
            Variational inference (with alpha and beta) is the default mode.
            If both alpha and beta are None, standard maximum likelihood estimation is used.
        """
        # Vectorized initialization with random noise
        self.spamming = 1.0 + init_noise * np.random.random((self.num_annotators, 2))
        self.thetas = 1.0 + init_noise * np.random.random((self.num_annotators, self.num_labels))
        
        # Normalize rows
        self.spamming /= self.spamming.sum(axis=1, keepdims=True)
        self.thetas /= self.thetas.sum(axis=1, keepdims=True)
        
        if alpha is not None and beta is not None:
            self.theta_priors = np.empty((self.num_annotators, 2))
            self.theta_priors[:, 0] = alpha
            self.theta_priors[:, 1] = beta
            self.strategy_priors = np.full((self.num_annotators, self.num_labels), 10.0)
    
    def e_step(self, controls=None):
        """
        Expectation step: compute expected counts for model parameters.
        
        Computes the posterior probabilities over true labels and expected counts
        of annotator behaviors (knowing vs. guessing) given current parameter estimates.
        This is the E-step of the EM algorithm.
        
        Args:
            controls (dict, optional): Dictionary mapping instance index to known
                                      ground truth label. Used for semi-supervised
                                      learning. Keys are instance indices (0-based),
                                      values are label indices.
        
        Updates:
            - gold_label_marginals: Posterior probability of each label for each instance
            - strategy_expected_counts: Expected counts for each annotator's strategy
            - knowing_expected_counts: Expected counts for knowing vs. guessing
            - log_marginal_likelihood: Log likelihood of data under current model
        """
        # Reset counts
        self.gold_label_marginals.fill(0.0)
        self.knowing_expected_counts.fill(0.0)
        self.strategy_expected_counts.fill(0.0)
        
        # Compute marginals
        self.log_marginal_likelihood = 0.0
        has_controls = controls is not None and len(controls) > 0
        # Cache label priors check and uniform prior
        use_label_priors = self.label_priors is not None
        uniform_prior = 1.0 / self.num_labels
        
        for d in range(self.num_instances):
            labels_d = self.labels[d]
            if labels_d is None:
                continue
                
            who_labeled_d = self.who_labeled[d]
            num_annotators_d = len(labels_d)
            instance_marginal = 0.0
            d_in_controls = has_controls and d in controls
            control_label = controls[d] if d_in_controls else -1
            
            # Compute gold label marginals for each possible label
            for l in range(self.num_labels):
                # Use label priors if available, otherwise uniform prior
                gold_label_marginal = self.label_priors[l] if use_label_priors else uniform_prior
                
                for ai in range(num_annotators_d):
                    a = who_labeled_d[ai]
                    label_ai = labels_d[ai]
                    prob = self.spamming[a, 0] * self.thetas[a, label_ai]
                    if l == label_ai:
                        prob += self.spamming[a, 1]
                    gold_label_marginal *= prob
                
                # Check controls
                if not d_in_controls or l == control_label:
                    instance_marginal += gold_label_marginal
                    self.gold_label_marginals[d, l] = gold_label_marginal
            
            if instance_marginal > 0:
                self.log_marginal_likelihood += np.log(instance_marginal)
            else:
                self.log_marginal_likelihood = float('-inf')
                continue
            
            inv_instance_marginal = 1.0 / instance_marginal
            
            # Update expected counts
            for ai in range(num_annotators_d):
                a = who_labeled_d[ai]
                label_ai = labels_d[ai]
                spamming_a0 = self.spamming[a, 0]
                spamming_a1 = self.spamming[a, 1]
                theta_a_label = self.thetas[a, label_ai]
                
                # Cache frequently used computations
                base_prob = spamming_a0 * theta_a_label
                denom_knowing = base_prob + spamming_a1
                
                if d_in_controls:
                    if label_ai == control_label:
                        l = control_label
                        strategy_marginal = self.gold_label_marginals[d, l] / denom_knowing
                        strategy_marginal *= base_prob
                        norm_strategy = strategy_marginal * inv_instance_marginal
                        self.strategy_expected_counts[a, label_ai] += norm_strategy
                        self.knowing_expected_counts[a, 0] += norm_strategy
                        self.knowing_expected_counts[a, 1] += (
                            self.gold_label_marginals[d, label_ai] * spamming_a1 / denom_knowing
                        ) * inv_instance_marginal
                    else:
                        self.strategy_expected_counts[a, label_ai] += 1.0
                        self.knowing_expected_counts[a, 0] += 1.0
                else:
                    strategy_marginal = 0.0
                    for l in range(self.num_labels):
                        denom = base_prob + (spamming_a1 if l == label_ai else 0.0)
                        strategy_marginal += self.gold_label_marginals[d, l] / denom
                    strategy_marginal *= base_prob
                    norm_strategy = strategy_marginal * inv_instance_marginal
                    self.strategy_expected_counts[a, label_ai] += norm_strategy
                    self.knowing_expected_counts[a, 0] += norm_strategy
                    self.knowing_expected_counts[a, 1] += (
                        self.gold_label_marginals[d, label_ai] * spamming_a1 / denom_knowing
                    ) * inv_instance_marginal
    
    def m_step(self, smoothing):
        """
        Maximization step: update model parameters from expected counts.
        
        Updates the spamming probabilities and strategy distributions based on
        the expected counts computed in the E-step. This is the M-step of the
        EM algorithm using maximum likelihood estimation with smoothing.
        
        Args:
            smoothing (float): Smoothing parameter added to counts before normalization.
                              Prevents zero probabilities. Typically 0.01/num_labels.
        
        Updates:
            - spamming: Probability of knowing vs. guessing for each annotator
            - thetas: Spamming strategy distribution for each annotator
        """
        # Vectorized normalization with smoothing
        smoothed = self.knowing_expected_counts + smoothing
        self.spamming = smoothed / smoothed.sum(axis=1, keepdims=True)
        
        smoothed = self.strategy_expected_counts + smoothing
        self.thetas = smoothed / smoothed.sum(axis=1, keepdims=True)
    
    def variational_m_step(self):
        """
        Variational maximization step: update parameters using Bayesian priors.
        
        Updates model parameters using variational inference with beta priors
        on the knowing probability. Uses the digamma function for proper
        normalization in the variational framework.
        
        Requires:
            - theta_priors: Beta prior parameters for knowing probability
            - strategy_priors: Prior parameters for spamming strategies
        
        Updates:
            - spamming: Variational posterior for knowing vs. guessing
            - thetas: Variational posterior for spamming strategies
        """
        # Vectorized variational normalization
        combined = self.knowing_expected_counts + self.theta_priors
        norm = np.exp(digamma(combined.sum(axis=1, keepdims=True)))
        self.spamming = np.exp(digamma(combined)) / norm
        
        combined = self.strategy_expected_counts + self.strategy_priors
        norm = np.exp(digamma(combined.sum(axis=1, keepdims=True)))
        self.thetas = np.exp(digamma(combined)) / norm
    
    def decode(self, threshold):
        """
        Decode predictions: find most likely label for each instance.
        
        For discrete mode: returns the label with highest posterior probability.
        For continuous mode: returns weighted average of annotator values,
        weighted by their competence scores.
        
        Args:
            threshold (float): Entropy threshold (0.0-1.0) to filter uncertain instances.
                             0.0 = only most certain, 1.0 = all instances.
                             Instances with entropy above threshold return empty string.
        
        Returns:
            list: Predictions for each instance. Empty strings for filtered instances
                  or instances with no annotations.
        
        Example:
            >>> predictions = mace.decode(threshold=0.8)
            >>> # predictions[0] = "cat" (most likely label for instance 0)
        """
        entropies = self.get_label_entropies()
        entropy_threshold = self.get_entropy_for_threshold(threshold, entropies)
        
        result = [""] * self.num_instances
        # Pre-compute valid mask for efficiency
        valid_mask = (entropies <= entropy_threshold) & (entropies != float('-inf'))
        
        if self.continuous:
            # For continuous mode: compute weighted average
            for d in range(self.num_instances):
                if valid_mask[d]:
                    stats = self._compute_weighted_stats(d)
                    if stats is not None:
                        result[d] = str(stats[0])  # weighted_mean
        else:
            # Discrete mode: original behavior
            for d in range(self.num_instances):
                if valid_mask[d]:
                    best_label = np.argmax(self.gold_label_marginals[d])
                    result[d] = self.int2string[best_label]
        
        return result
    
    def decode_distribution(self, threshold):
        """
        Decode predictions with full distribution information.
        
        Returns full probability distributions over labels or statistical summaries
        for continuous values, rather than just the most likely prediction.
        
        Args:
            threshold (float): Entropy threshold (0.0-1.0) to filter uncertain instances.
        
        Returns:
            list: For each instance, returns:
                - Discrete mode: Tab-separated "label probability" pairs, sorted by
                  probability descending (e.g., "cat 0.8\tdog 0.15\tbird 0.05")
                - Continuous mode: Tab-separated stats "mean\tstd\tmin\tmax\tn_annotators"
                - Empty strings for filtered instances
        
        Example:
            >>> dists = mace.decode_distribution(threshold=1.0)
            >>> # dists[0] = "cat 0.8\tdog 0.15\tbird 0.05"
        """
        entropies = self.get_label_entropies()
        entropy_threshold = self.get_entropy_for_threshold(threshold, entropies)
        
        result = [""] * self.num_instances
        # Pre-compute valid mask for efficiency
        valid_mask = (entropies <= entropy_threshold) & (entropies != float('-inf'))
        
        if self.continuous:
            # For continuous mode: return weighted mean, std, and individual values with weights
            for d in range(self.num_instances):
                if valid_mask[d]:
                    stats = self._compute_weighted_stats(d)
                    if stats is not None:
                        # Format: mean, std, min, max, n_annotators
                        result[d] = f"{stats[0]}\t{stats[1]}\t{stats[2]}\t{stats[3]}\t{stats[4]}"
        else:
            # Discrete mode: normalize marginals to probability distribution
            for d in range(self.num_instances):
                if valid_mask[d]:
                    marginals = self.gold_label_marginals[d]
                    # Normalize to probability distribution (sum to 1.0)
                    norm = marginals.sum()
                    if norm > 0:
                        probabilities = marginals / norm
                    else:
                        # If all marginals are zero, use uniform distribution
                        probabilities = np.ones(self.num_labels) / self.num_labels
                    # Sort indices by probability descending
                    sorted_indices = np.argsort(probabilities)[::-1]
                    output = [f"{self.int2string[i]} {probabilities[i]}" for i in sorted_indices]
                    result[d] = "\t".join(output)
        
        return result
    
    def get_label_entropies(self):
        """
        Compute entropy of label distribution for each instance.
        
        Entropy measures uncertainty in the predicted label distribution.
        Higher entropy indicates more uncertainty (annotators disagree).
        Lower entropy indicates high confidence (annotators agree).
        
        Returns:
            np.ndarray: Entropy values for each instance.
                      Returns -inf for instances with no annotations.
        
        Example:
            >>> entropies = mace.get_label_entropies()
            >>> # entropies[0] = 0.45  (moderate uncertainty)
            >>> # entropies[1] = 0.12  (high confidence)
        """
        result = np.full(self.num_instances, float('-inf'))
        
        for d in range(self.num_instances):
            if self.labels[d] is not None:
                marginals = self.gold_label_marginals[d]
                norm = marginals.sum()
                if norm > 0:
                    p = marginals / norm
                    # Avoid log(0) by masking zeros
                    mask = p > 0
                    result[d] = -np.sum(p[mask] * np.log(p[mask]))
        
        return result
    
    def run(self, num_iters, smoothing, num_restarts, alpha, beta, use_em, controls_file):
        """
        Run the EM algorithm to learn annotator competences and true labels.
        
        Performs multiple random restarts of the EM algorithm and selects the model
        with highest log marginal likelihood. Each restart:
        1. Randomly initializes parameters
        2. Alternates E-step and M-step for specified iterations
        3. Tracks the best model across all restarts
        
        Args:
            num_iters (int): Number of EM iterations per restart (typically 50)
            smoothing (float): Smoothing parameter for M-step (typically 0.01/num_labels)
            num_restarts (int): Number of random restarts (typically 10)
            alpha (float): First hyperparameter for beta prior (used in Variational Bayes EM, default)
            beta (float): Second hyperparameter for beta prior (used in Variational Bayes EM, default)
            use_em (bool): If True, use regular EM (MLE). If False, use Variational Bayes EM (default)
            controls_file (str, optional): Path to file with control items (known labels)
        
        Updates:
            - spamming: Best competence estimates found across all restarts
            - thetas: Best strategy distributions found across all restarts
            - gold_label_marginals: Posterior probabilities for best model
            - log_marginal_likelihood: Log likelihood of best model
        
        Note:
            Prints progress information to stderr including which restart produced
            the best model.
        """
        controls = self._read_controls(controls_file) if controls_file else {}
        
        best_thetas = None
        best_strategies = None
        best_log_marginal_likelihood = float('-inf')
        rr_best_model_occurred_at = 0
        
        print("Running training with the following settings:", file=sys.stderr)
        print(f"\t{num_iters} iterations", file=sys.stderr)
        print(f"\t{num_restarts} restarts", file=sys.stderr)
        if use_em:
            print(f"\tMethod: EM (Maximum Likelihood)", file=sys.stderr)
            print(f"\tsmoothing = {smoothing}", file=sys.stderr)
        else:
            print(f"\tMethod: Variational Bayes EM", file=sys.stderr)
            print(f"\talpha = {alpha}", file=sys.stderr)
            print(f"\tbeta = {beta}", file=sys.stderr)
        
        start = time.time()
        for rr in range(num_restarts):
            print(f"\n============\nRestart {rr + 1}\n============", file=sys.stderr)
            
            # Initialize
            if use_em:
                self.initialize(DEFAULT_NOISE)
            else:
                self.initialize(DEFAULT_NOISE, alpha, beta)
            
            # Run first E-Step to get counts
            self.e_step(controls)
            print(f"initial log marginal likelihood = {self.log_marginal_likelihood}", file=sys.stderr)
            
            # Iterate
            for _ in range(num_iters):
                if use_em:
                    self.m_step(smoothing)
                else:
                    self.variational_m_step()
                self.e_step(controls)
            
            print(f"final log marginal likelihood = {self.log_marginal_likelihood}", file=sys.stderr)
            
            if self.log_marginal_likelihood > best_log_marginal_likelihood:
                rr_best_model_occurred_at = rr + 1
                best_log_marginal_likelihood = self.log_marginal_likelihood
                best_thetas = self.spamming.copy()
                best_strategies = self.thetas.copy()
        
        elapsed = time.time() - start
        print(f"\nTraining completed in {elapsed:.2f}sec", file=sys.stderr)
        print(f"Best model came from random restart number {rr_best_model_occurred_at} "
              f"(log marginal likelihood: {best_log_marginal_likelihood})", file=sys.stderr)
        self.log_marginal_likelihood = best_log_marginal_likelihood
        self.spamming = best_thetas
        self.thetas = best_strategies
        
        # Run E-step to get marginals of latest model
        self.e_step(controls)
    
    def _read_controls(self, file_name):
        """
        Read control items (known ground truth labels) from file.
        
        Control items are used for semi-supervised learning. They provide
        known labels for specific instances, which helps guide the EM algorithm.
        
        Args:
            file_name (str): Path to file with control labels, one per line.
                           Empty lines indicate no control for that instance.
                           Must have same number of lines as input CSV.
        
        Returns:
            dict: Mapping from instance index (0-based) to label index.
                 Only includes entries for non-empty lines.
        
        Raises:
            IOError: If file cannot be read
        """
        controls = {}
        
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                print(f"Reading controls file {file_name}", file=sys.stderr)
                
                for line_number, line in enumerate(f):
                    line = line.strip()
                    if line:
                        if line not in self.string2int:
                            self.string2int[line] = self.hash_counter
                            self.int2string.append(line)
                            self.hash_counter += 1
                        controls[line_number] = self.string2int[line]
            
            return controls
        
        except Exception as e:
            raise IOError(f"Problem reading file: {str(e)}")
    
    def _read_label_priors(self, file_name):
        """
        Read label priors from file.
        
        Reads a file with tab-separated label and weight pairs, one per line.
        Validates that all labels in the data are present, normalizes weights,
        and stores as prior probabilities for labels.
        
        Args:
            file_name (str): Path to file with label priors. Format: "label\\tweight"
        
        Raises:
            IOError: If file cannot be read
            IOError: If not all labels are present in priors file
            IOError: If weights cannot be parsed as floats
        
        Updates:
            - label_priors: Normalized prior probabilities for each label
        """
        label_weights = {}
        
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                print(f"Reading label priors file {file_name}", file=sys.stderr)
                
                for line_number, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) != 2:
                        raise IOError(f"Line {line_number} in priors file must have exactly 2 tab-separated values (label\\tweight)")
                    
                    label = parts[0].strip()
                    try:
                        weight = float(parts[1].strip())
                        if weight < 0:
                            raise IOError(f"Line {line_number} in priors file: weight must be non-negative")
                        label_weights[label] = weight
                    except ValueError:
                        raise IOError(f"Line {line_number} in priors file: weight '{parts[1]}' is not a valid number")
            
            # Validate that all labels are present
            missing_labels = set(self.int2string) - set(label_weights.keys())
            if missing_labels:
                raise IOError(f"Priors file missing labels: {sorted(missing_labels)}. All labels in data must be present.")
            
            # Check for extra labels (warn but don't error)
            extra_labels = set(label_weights.keys()) - set(self.int2string)
            if extra_labels:
                print(f"Warning: Priors file contains extra labels not in data: {sorted(extra_labels)}", file=sys.stderr)
            
            # Normalize weights to probabilities
            self.label_priors = np.array([label_weights.get(label, 0.0) for label in self.int2string])
            total_weight = self.label_priors.sum()
            
            if total_weight > 0:
                self.label_priors /= total_weight
            else:
                # If all weights are zero, use uniform prior
                print("Warning: All priors are zero, using uniform prior", file=sys.stderr)
                self.label_priors.fill(1.0 / self.num_labels)
            
            print(f"Label priors loaded and normalized: {dict(zip(self.int2string, self.label_priors))}", file=sys.stderr)
        
        except Exception as e:
            raise IOError(f"Problem reading priors file: {str(e)}")
    
    def _read_file_data(self, file_name):
        """
        Read annotation data from CSV file.
        
        Parses CSV file where each row is an instance and each column is an annotator.
        Empty cells indicate missing annotations. In continuous mode, validates
        that all values are numeric.
        
        Args:
            file_name (str): Path to CSV file with annotations
        
        Raises:
            IOError: If file cannot be read
            IOError: If continuous mode but non-numeric values found
            IOError: If number of columns varies between rows
        
        Updates:
            - labels: Label indices for each instance
            - who_labeled: Annotator indices for each annotation
            - continuous_values: Original numeric values (if continuous mode)
            - string2int, int2string: Mappings between labels and indices
            - num_annotators: Number of annotators (columns)
        """
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                print(f"Reading CSV file '{file_name}'", file=sys.stderr)
                
                for line_number, line in enumerate(f):
                    if line_number > 0 and line_number % 5 == 0:
                        print(".", end="", file=sys.stderr, flush=True)
                    if line_number > 0 and line_number % 100 == 0:
                        print(f"\n{line_number}", file=sys.stderr)
                    
                    # Handle empty lines
                    if not line.strip():
                        self.labels[line_number] = None
                        self.who_labeled[line_number] = None
                        if self.continuous:
                            self.continuous_values[line_number] = None
                        continue
                    
                    tokens = line.rstrip('\n').split(',')
                    num_annotators_this_line = len(tokens)
                    
                    if self.num_annotators > 0 and num_annotators_this_line != self.num_annotators:
                        raise IOError(f"number of annotations in line {line_number + 1} differs from previous line!")
                    self.num_annotators = num_annotators_this_line
                    
                    annotators_on_item = []
                    item_values = []
                    continuous_vals = [] if self.continuous else None
                    
                    for annotator_number, token in enumerate(tokens):
                        item = token.strip()
                        if item:
                            annotators_on_item.append(annotator_number)
                            
                            if self.continuous:
                                # Validate that it's a number
                                try:
                                    numeric_value = float(item)
                                    continuous_vals.append(numeric_value)
                                except ValueError:
                                    raise IOError(f"Line {line_number + 1}, column {annotator_number + 1}: '{item}' is not a valid number (--continuous mode requires numeric values)")
                                
                                # Still use string representation for discrete model
                                item_str = item
                            else:
                                item_str = item
                            
                            if item_str not in self.string2int:
                                self.string2int[item_str] = self.hash_counter
                                self.int2string.append(item_str)
                                self.hash_counter += 1
                            item_values.append(self.string2int[item_str])
                    
                    # Store as arrays for faster access
                    self.labels[line_number] = np.array(item_values, dtype=np.int32) if item_values else None
                    self.who_labeled[line_number] = np.array(annotators_on_item, dtype=np.int32) if annotators_on_item else None
                    if self.continuous:
                        self.continuous_values[line_number] = np.array(continuous_vals, dtype=np.float64) if continuous_vals else None
            
            print(f"\nstats:\n\t{self.num_instances} instances,\n\t{len(self.int2string)} labels {self.int2string},\n\t{self.num_annotators} annotators\n", file=sys.stderr)
            if self.continuous:
                print(f"\tMode: Continuous (numeric values)", file=sys.stderr)
        
        except Exception as e:
            raise IOError(f"Problem reading file: {str(e)}")
    
    def _file_line_count(self, filename):
        """
        Count the number of lines in a file.
        
        Used to pre-allocate arrays before reading the file.
        
        Args:
            filename (str): Path to file to count lines in
        
        Returns:
            int: Number of lines in the file
        
        Raises:
            IOError: If file cannot be read
        """
        try:
            with open(filename, 'rb') as f:
                return sum(1 for _ in f)
        except Exception as e:
            raise IOError(f"Problem reading file: {str(e)}")
    
    def write_array_to_file(self, array, file_name, delimiter, header=None):
        """
        Write an array to a file with optional header.
        
        Writes array elements separated by the specified delimiter. If header
        is provided, writes it as the first line.
        
        Args:
            array (list): Array of values to write
            file_name (str): Output file path
            delimiter (str): String to separate elements (e.g., "\\n", "\\t", ",")
            header (str, optional): Header line to write before data
        
        Raises:
            IOError: If file cannot be written
        
        Example:
            >>> mace.write_array_to_file([1, 2, 3], "out.txt", "\\n", header="values")
            >>> # Writes: "values\\n1\\n2\\n3\\n"
        """
        try:
            print(f"writing to file '{file_name}'...", end="", file=sys.stderr)
            with open(file_name, 'w', encoding='utf-8') as f:
                if header:
                    f.write(header + "\n")
                f.write(delimiter.join(str(item) for item in array))
                f.write("\n")
            print("done", file=sys.stderr)
        except Exception as e:
            raise IOError(f"Problem writing file: {str(e)}")
    
    def get_entropy_for_threshold(self, threshold, entropy_array=None):
        """
        Get entropy value corresponding to threshold percentile.
        
        Sorts all entropy values and returns the value at the specified percentile.
        Used to filter instances: only instances with entropy <= this value are
        included in predictions.
        
        Args:
            threshold (float): Percentile threshold (0.0-1.0).
                             0.0 = minimum entropy (most certain)
                             1.0 = maximum entropy (all instances)
            entropy_array (np.ndarray, optional): Precomputed entropy array.
                                                 If None, computes it.
        
        Returns:
            float: Entropy value at the specified percentile
        
        Example:
            >>> # Get entropy threshold for top 80% most certain instances
            >>> threshold_val = mace.get_entropy_for_threshold(0.8)
        """
        if threshold == 0.0:
            pivot = 0
        elif threshold == 1.0:
            pivot = self.num_instances - 1
        else:
            pivot = int(self.num_instances * threshold)
        
        if entropy_array is None:
            entropy_array = self.get_label_entropies()
        return np.partition(entropy_array, pivot)[pivot]
    
    def test(self, test_file, predictions, distribution_format=False):
        """
        Evaluate model predictions against gold standard labels.
        
        Compares predictions to ground truth labels from a test file and computes
        evaluation metrics. Only evaluates instances that have predictions (not
        filtered by threshold).
        
        Args:
            test_file (str): Path to file with gold standard labels, one per line.
                           Must have same number of lines as input CSV.
            predictions (list): Model predictions from decode() or decode_distribution()
            distribution_format (bool): If True, predictions are in distribution format
                                      (tab-separated). Extracts best prediction automatically.
        
        Returns:
            float: Evaluation metric:
                  - Discrete mode: Accuracy (proportion of correct predictions)
                  - Continuous mode: RMSE (Root Mean Squared Error)
        
        Raises:
            IOError: If test file cannot be read or has wrong number of lines
            IOError: If continuous mode but non-numeric values in test file
        
        Note:
            Prints coverage (proportion of instances with predictions) to stdout.
        """
        num_lines_in_test = self._file_line_count(test_file)
        if num_lines_in_test != self.num_instances:
            raise IOError("Number of lines in test file does not match!")
        
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                print("Reading test file", file=sys.stderr)
                
                if self.continuous:
                    # Continuous mode: compute RMSE
                    squared_errors = []
                    total = 0
                    
                    for line_number, line in enumerate(f):
                        if predictions[line_number]:
                            total += 1
                            try:
                                actual = float(line.strip())
                                pred_str = predictions[line_number]
                                
                                # If distribution format, extract first value (weighted mean)
                                if distribution_format:
                                    pred_str = pred_str.split('\t')[0]
                                
                                predicted = float(pred_str)
                                squared_errors.append((predicted - actual) ** 2)
                            except (ValueError, IndexError) as e:
                                raise IOError(f"Line {line_number + 1}: could not parse prediction '{predictions[line_number]}' (continuous mode requires numeric values)")
                    
                    coverage = total / self.num_instances
                    print(f"Coverage: {coverage}\t", end="")
                    
                    if total > 0:
                        mse = np.mean(squared_errors)
                        rmse = np.sqrt(mse)
                        return rmse
                    else:
                        return float('inf')
                else:
                    # Discrete mode: compute accuracy
                    correct = 0
                    total = 0
                    
                    for line_number, line in enumerate(f):
                        if predictions[line_number]:
                            total += 1
                            pred_str = predictions[line_number]
                            actual_str = line.strip()
                            
                            # If distribution format, extract first label (highest probability)
                            if distribution_format:
                                # Format is "label prob\tlabel prob\t..."
                                first_pair = pred_str.split('\t')[0]
                                # Extract label (everything before the last space)
                                pred_str = first_pair.rsplit(' ', 1)[0]
                            
                            if actual_str == pred_str:
                                correct += 1
                    
                    coverage = total / self.num_instances
                    print(f"Coverage: {coverage}\t", end="")
                    return correct / total if total > 0 else 0.0
        
        except Exception as e:
            raise IOError(f"Problem reading test file: {str(e)}")


def main():
    """
    Main entry point for MACE command-line interface.
    
    Parses command-line arguments, runs the MACE algorithm, and writes results
    to output files. Supports both discrete categorical labels and continuous
    numeric values.
    
    Output Files:
        - {prefix}.prediction: Consensus predictions (or distributions if --distribution)
        - {prefix}.competence: Competence scores for each annotator
        - {prefix}.entropies: Entropy values for each instance (if --entropies)
    
    Exit Codes:
        0: Success
        1: File error or argument error
    
    Example:
        >>> # Basic usage with discrete labels
        >>> python mace.py example.csv
        >>> 
        >>> # Continuous values with test evaluation
        >>> python mace.py --continuous --test gold.txt scores.csv
        >>> 
        >>> # With control items and custom prefix
        >>> python mace.py --controls controls.txt --prefix results example.csv
    """
    parser = argparse.ArgumentParser(
        description="MACE: Multi-Annotator Competence Estimation - EM algorithm for learning true labels and annotator reliability from multiple annotations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage with discrete labels:
    %(prog)s annotations.csv
  
  Continuous numeric values with test evaluation:
    %(prog)s --continuous --test gold_standard.txt scores.csv
  
  With control items and custom output prefix:
    %(prog)s --controls known_labels.txt --prefix results annotations.csv
  
  Distribution output with headers:
    %(prog)s --distribution --headers --prefix output annotations.csv

Input Format:
  CSV file with one instance per line, each column is one annotator.
  Empty cells indicate missing annotations. In continuous mode, all values must be numeric.

Output Files:
  {prefix}.prediction    - Consensus predictions (or distributions if --distribution)
  {prefix}.competence    - Competence scores for each annotator (0-1, higher = more reliable)
  {prefix}.entropies     - Uncertainty measure for each instance (if --entropies)

Citation:
  Dirk Hovy, Taylor Berg-Kirkpatrick, Ashish Vaswani and Eduard Hovy (2013): 
  Learning Whom to Trust With MACE. In: Proceedings of NAACL-HLT. 
  Association for Computational Linguistics.

This is research software that is not actively maintained.
        """
    )
    
    parser.add_argument('--version', action='version', version=f'MACE {VERSION}')
    # Arguments sorted alphabetically (excluding --version and csv_file)
    parser.add_argument('--alpha', type=float, default=DEFAULT_ALPHA, metavar='FLOAT',
                       help=f'First hyperparameter of beta prior for Variational Bayes EM (default method). If alpha > beta, then we assume most annotators are unreliable. '
                            f'Default: {DEFAULT_ALPHA}')
    parser.add_argument('--beta', type=float, default=DEFAULT_BETA, metavar='FLOAT',
                       help=f'Second hyperparameter of beta prior for Variational Bayes EM (default method). If beta > alpha, then we assume most annotators are reliable. '
                            f'Default: {DEFAULT_BETA}')
    parser.add_argument('--continuous', action='store_true',
                       help='Interpret input values as continuous numeric. Returns weighted averages '
                            'weighted by annotator competence scores. All values must be valid numbers. '
                            'Test evaluation uses RMSE instead of accuracy.')
    parser.add_argument('--controls', type=str, metavar='FILE',
                       help='File with control items (known ground truth labels) for semi-supervised learning. '
                            'One label per line, empty lines indicate no control. Must match number of instances.')
    parser.add_argument('--distribution', action='store_true',
                       help='Output full probability distributions instead of single predictions. '
                            'Discrete: tab-separated "label probability" pairs sorted by probability. '
                            'Continuous: tab-separated stats "mean\\tstd\\tmin\\tmax\\tn_annotators".')
    parser.add_argument('--em', action='store_true',
                       help='Use regular EM (Maximum Likelihood Estimation) instead of Variational Bayes EM. '
                            'Variational Bayes EM is the default method.')
    parser.add_argument('--entropies', action='store_true',
                       help='Write entropy values (uncertainty measure) for each instance to a separate file. '
                            'Higher entropy indicates more disagreement among annotators.')
    parser.add_argument('--headers', action='store_true',
                       help='Add header rows to output files describing column contents.')
    parser.add_argument('--iterations', type=int, default=DEFAULT_ITERATIONS, metavar='N',
                       help=f'Number of EM iterations per random restart. More iterations may improve '
                            f'convergence but increase runtime. Default: {DEFAULT_ITERATIONS}')
    parser.add_argument('--prefix', type=str, metavar='PREFIX',
                       help='Prefix for output filenames. If not specified, uses default names '
                            '(prediction, competence, entropies). Output: {prefix}.prediction, etc.')
    parser.add_argument('--priors', type=str, metavar='FILE',
                       help='File with label priors (one tab-separated "label\\tweight" pair per line). '
                            'All labels in data must be present. Weights are automatically normalized to probabilities. '
                            'Used as prior likelihoods for labels in the E-step.')
    parser.add_argument('--restarts', type=int, default=DEFAULT_RR, metavar='N',
                       help=f'Number of random restarts to perform. Multiple restarts help avoid '
                            f'local optima. Best model (highest likelihood) is selected. Default: {DEFAULT_RR}')
    parser.add_argument('--smoothing', type=float, metavar='FLOAT',
                       help='Smoothing parameter added to expected counts before normalization (regular EM only). '
                            'Prevents zero probabilities. If not specified, defaults to 0.01/num_labels. '
                            'Higher values = more conservative updates.')
    parser.add_argument('--test', type=str, metavar='FILE',
                       help='Test file with gold standard labels for evaluation. One label per line, '
                            'must match number of instances. Reports accuracy (discrete) or RMSE (continuous).')
    parser.add_argument('--threshold', type=float, default=1.0, metavar='FLOAT',
                       help='Entropy threshold (0.0-1.0) to filter uncertain instances. '
                            '0.0 = only most certain, 1.0 = all instances. '
                            'Instances above threshold are not predicted (empty in output). Default: 1.0')
    parser.add_argument('csv_file', metavar='CSV_FILE',
                       help='Input CSV file with annotations. Each row is an instance, each column is an annotator.')
    
    args = parser.parse_args()
    
    try:
        em = MACE(args.csv_file, continuous=args.continuous)
        
        # Read label priors if provided
        if args.priors:
            em._read_label_priors(args.priors)
        
        smoothing = args.smoothing if args.smoothing is not None else 0.01 / em.num_labels
        use_em = args.em  # If --em flag is set, use regular EM, otherwise use Variational Bayes EM (default)
        
        # Validate arguments
        if smoothing < 0.0:
            raise ValueError("smoothing less than 0.0")
        if not 0.0 <= args.threshold <= 1.0:
            raise ValueError("threshold not between 0.0 and 1.0")
        if not 1 <= args.restarts <= 1000:
            raise ValueError("restarts not between 1 and 1000")
        if not 1 <= args.iterations <= 1000:
            raise ValueError("iterations not between 1 and 1000")
        
        # Run with configuration
        em.run(args.iterations, smoothing, args.restarts, args.alpha, args.beta, use_em, args.controls)
        
        # Write results to files
        predictions = em.decode_distribution(args.threshold) if args.distribution else em.decode(args.threshold)
        
        prefix = args.prefix
        prediction_name = f"{prefix}.prediction" if prefix else "prediction"
        
        # Generate header for prediction file
        pred_header = None
        if args.headers:
            if args.distribution:
                if args.continuous:
                    pred_header = "weighted_mean\tweighted_std\tmin\tmax\tn_annotators"
                else:
                    # For discrete distribution, create header with actual label names
                    # Note: output is sorted by probability, but header shows all labels
                    header_parts = []
                    for i in range(em.num_labels):
                        header_parts.append(f"{em.int2string[i]}\tprob_{em.int2string[i]}")
                    pred_header = "\t".join(header_parts)
            else:
                pred_header = "prediction"
        
        em.write_array_to_file(predictions, prediction_name, "\n", header=pred_header)
        
        # Generate competence scores
        competence = em.spamming[:, 1].tolist()
        competence_name = f"{prefix}.competence" if prefix else "competence"
        
        # Generate header for competence file
        comp_header = None
        if args.headers:
            # Tab-separated annotator IDs
            comp_header = "\t".join(f"annotator_{i}" for i in range(em.num_annotators))
        
        em.write_array_to_file(competence, competence_name, "\t", header=comp_header)
        
        # Generate entropies
        if args.entropies:
            entropy_array = em.get_label_entropies()
            # Filter out empty lines (instances with no annotations)
            entropy = [str(entropy_array[d]) if entropy_array[d] != float('-inf') else "" 
                      for d in range(em.num_instances)]
            entropy_name = f"{prefix}.entropies" if prefix else "entropies"
            
            # Generate header for entropy file
            entropy_header = "entropy" if args.headers else None
            
            em.write_array_to_file(entropy, entropy_name, "\n", header=entropy_header)
        
        if args.test:
            result = em.test(args.test, predictions, distribution_format=args.distribution)
            metric_name = "RMSE" if args.continuous else "Accuracy"
            print(f"{metric_name} on test set: {result}")
    
    except IOError as e:
        print("\n*****************************************************************", file=sys.stderr)
        print("\tFILE ERROR:", file=sys.stderr)
        print(f"\t{str(e)}", file=sys.stderr)
        print("*****************************************************************", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print("\n*****************************************************************", file=sys.stderr)
        print("\tARGUMENT ERROR:", file=sys.stderr)
        print(f"\t{str(e)}", file=sys.stderr)
        print("*****************************************************************", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

```

---

### FILE: backend\annotation\mace_service.py
```
import logging
import os
import tempfile
import csv
import numpy as np
from collections import defaultdict
from django.core.exceptions import ObjectDoesNotExist
from .models import Project, Annotation, ProjectEnrollment, Document

logger = logging.getLogger(__name__)

def run_mace_for_project(project_id):
    """
    Extracts annotations for a project, runs the MACE algorithm,
    and updates the models with the computed metrics.
    
    If the official MACE python package is installed, it uses it.
    Otherwise, it shows how the data should be structured and provides a mock/fallback logic.
    """
    project = Project.objects.get(id=project_id)
    
    # 1. Fetch Annotations
    # Exclude gold units, we only use unsupervised MACE on standard instances.
    annotations = Annotation.objects.filter(
        document__project=project,
        document__is_gold_unit=False
    ).select_related('document', 'annotator')
    
    if not annotations.exists():
        return {"status": "error", "message": "No annotations found to run MACE."}

    # 2. Build the Data Matrix (Documents x Annotators)
    # Rows = Document IDs, Columns = Annotator Prolific PIDs
    # Value = The classification label
    
    doc_ids = set()
    annotator_pids = set()
    data_dict = defaultdict(dict) # {doc_id: {annotator_pid: label}}
    
    for ann in annotations:
        doc_id = str(ann.document.id)
        annotator_pid = ann.annotator.prolific_pid
        label = ann.result.get('classification')
        
        # Only process if there is a classification label
        if label:
            doc_ids.add(doc_id)
            annotator_pids.add(annotator_pid)
            data_dict[doc_id][annotator_pid] = label

    from_doc_ids = sorted(list(doc_ids))
    from_annotators = sorted(list(annotator_pids))
    
    if len(from_annotators) < 2:
        return {"status": "error", "message": "Need at least 2 distinct annotators to estimate competence."}

    # 3. Use actual MACE python package
    mace_results = None
    try:
        from .mace import MACE
        
        # Write to a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            temp_file_name = f.name
            writer = csv.writer(f)
            for doc_id in from_doc_ids:
                row = []
                for pid in from_annotators:
                    row.append(data_dict[doc_id].get(pid, ""))
                writer.writerow(row)
        
        try:
            mace_model = MACE(temp_file_name, continuous=False)
            mace_model.initialize(init_noise=0.5)
            # Run Variational Bayes EM
            mace_model.run(num_iters=50, smoothing=0.01, num_restarts=10, alpha=0.5, beta=0.5, use_em=False, controls_file=None)
            
            # Extract results
            predictions_list = mace_model.decode(threshold=1.0)
            entropies_list = mace_model.get_label_entropies()
            
            competence = {}
            spam_bias = {}
            predictions = {}
            confidence = {}
            
            spamming = mace_model.spamming
            thetas = mace_model.thetas
            
            if spamming is None or thetas is None:
                raise ValueError("MACE training failed to update internal probability distributions.")
            
            # MACE indexes annotators based on column order (from_annotators)
            for j, pid in enumerate(from_annotators):
                comp_score = float(spamming[j, 1])  # probability of knowing
                guess_prob = float(spamming[j, 0])  # probability of guessing
                
                # Format the spamming strategy distribution
                bias_dict = {}
                for k, label_name in enumerate(mace_model.int2string):
                    bias_dict[label_name] = float(thetas[j, k])
                    
                competence[pid] = comp_score
                spam_bias[pid] = {
                    "guess_probability": guess_prob,
                    "strategy": bias_dict
                }
                
            # MACE indexes documents based on row order (from_doc_ids)
            for i, doc_id in enumerate(from_doc_ids):
                pred = predictions_list[i]
                ent = float(entropies_list[i]) if entropies_list[i] != float('-inf') else 0.0
                
                # Convert entropy to a simple 0-1 confidence score (lower entropy = higher confidence)
                # Max entropy for N labels is ln(N)
                max_entropy = np.log(mace_model.num_labels) if mace_model.num_labels > 1 else 1.0
                conf_score = max(0.0, 1.0 - (ent / max_entropy)) if max_entropy > 0 else 1.0
                
                predictions[doc_id] = pred
                confidence[doc_id] = conf_score
                
            mace_results = {
                "competence": competence,
                "spam_bias": spam_bias,
                "predictions": predictions,
                "confidence": confidence
            }
            
        finally:
            if os.path.exists(temp_file_name):
                os.remove(temp_file_name)
        
    except Exception as e:
        logger.error(f"Error running MACE: {e}", exc_info=True)
        return {"status": "error", "message": f"MACE execution failed: {str(e)}"}

    # 4. Save Results to Database
    # Update Enrollments
    updated_enrollments = 0
    for pid, score in mace_results.get("competence", {}).items():
        try:
            enrollment = ProjectEnrollment.objects.get(
                project=project,
                annotator__prolific_pid=pid
            )
            enrollment.mace_competence_score = score
            enrollment.mace_spam_bias = mace_results.get("spam_bias", {}).get(pid, {})
            enrollment.save(update_fields=["mace_competence_score", "mace_spam_bias"])
            updated_enrollments += 1
        except ObjectDoesNotExist:
            continue
            
    # Update Documents
    updated_docs = 0
    for doc_id, label in mace_results.get("predictions", {}).items():
        try:
            doc = Document.objects.get(id=doc_id)
            doc.mace_gold_label = label
            doc.mace_confidence = mace_results.get("confidence", {}).get(doc_id, 0.0)
            doc.save(update_fields=["mace_gold_label", "mace_confidence"])
            updated_docs += 1
        except ObjectDoesNotExist:
            continue
            
    return {
        "status": "success", 
        "message": f"MACE estimation complete. Updated {updated_enrollments} annotators and {updated_docs} documents."
    }

```

---

### FILE: backend\annotation\models.py
```
from django.db import models
from django.core.exceptions import ValidationError

from django.db.models import JSONField 
from django.utils import timezone
import uuid
import os
from django.conf import settings
import json

def get_default_configuration_for_task_type():
    config_path = os.path.join(settings.BASE_DIR, 'config_defaults', 'default_project_config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"task_type": "classification", "class_labels": []}
            
    return {
        "task_type": "hybrid",
        "span_labels": [
                {
                "name": "Actor",
                "color": "#FF5733",
                "hover_hint": "Who is allegedly responsible for a malicious action or agenda?"
                },
                {
                "name": "Action",
                "color": "#33FF57",
                "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
                },
                {
                "name": "Victim",
                "color": "#3357FF",
                "hover_hint": "Who is negatively affected by the actor's agenda?"
                },
                {
                "name": "Threat",
                "color": "#FF33F6",
                "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
                },
                {
                "name": "Evidence",
                "color": "#FFA500",
                "hover_hint": "Which arguments or expressions does the writer of the text use to support his claims?"
                }
            ],
            "class_labels": [
                { "label": "Conspiracy", "value": "Yes" },
                { "label": "Not Conspiracy", "value": "No" },
                { "label": "Ambiguous", "value": "Can't tell" }
            ]
    }

def get_default_gold_config():
    return {
        "min_accuracy_required": 0.6,
        "gold_injection_frequency": 5,
        "continuous_exclusion": False,
        "evaluation_strategy": "percentage",
        "max_strikes": 3,
        "min_gold_before_eval": 3
    }

def get_default_screening_config():
    config_path = os.path.join(settings.BASE_DIR, 'config_defaults', 'default_screening_config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return [
        {"id": "age", "type": "number", "label": "How old are you?", "required": True, "min": 18, "max": 99},
        {"id": "gender", "type": "select", "label": "Gender?", "required": True, "options": ["Male", "Female", "Non-binary", "Prefer not to say"]},
        {"id": "native_language", "type": "text", "label": "Native language?", "required": True}
    ]

def get_default_configuration_for_informed_consent():
    return """
    [EXAMPLE SCRIPT]
    Welcome to the study!
    
    Your task: You will be asked to [describe the task in half a line, e.g., read and classify 20 sentences]. The estimated time is approximately [X] minutes. The goal is [very brief purpose, e.g., to improve an artificial intelligence system].
    
    Your data and privacy: This task is anonymous. We do not collect any personally identifiable information. We will only save your responses and your Prolific ID, which we need exclusively to confirm your completion of the task and authorize your payment on the platform.
    
    Your rights: Participation is voluntary. You may stop participating at any time. If you decide not to finish, simply close this page and click on "Return submission" on Prolific. In this case, your partial data will not be used, but we will not be able to process your payment.
    
    By clicking the button below, you confirm that you are at least 18 years old, that you have read this information, and that you consent to participate.
    """

def get_default_codebook_content():
    config_path = os.path.join(settings.BASE_DIR, 'config_defaults', 'codebook_somiglianza_item.md')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError:
            pass
    
    return """
            # Codebook

            ## Overview
            Describe the annotation task here. This content supports **Markdown** formatting.

            ## Definitions
            - **Label 1**: Description of label 1
            - **Label 2**: Description of label 2

            ## Examples
            Provide worked examples here to help annotators understand the task.

            ## Guidelines
            Any additional rules or edge cases the annotator should know.
        """

def get_default_instructions_content():
    config_path = os.path.join(settings.BASE_DIR, 'config_defaults', 'default_instructions_content.md')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError:
            pass
    
    return """
        # Task Instructions

        ## The Goal
        Read the items and complete the annotation tasks as described in the codebook.

        ## How to Use the Interface
        1. Read the text carefully
        2. Select the appropriate classification
        3. Submit your annotation
    """

def get_default_practice_task():
    config_path = os.path.join(settings.BASE_DIR, 'config_defaults', 'default_practice_task.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return {}

class Project(models.Model):
    """
    Represents an annotation 'campaign' or 'batch'.
    Example: 'Sentiment Analysis Batch 1'
    """
    name = models.CharField(max_length=200, help_text="Project name")
    slug = models.SlugField(max_length=250, unique=True, blank=True, help_text="Unique Identifier for the URL (e.g., 'nome-studio')")
    description = models.TextField(blank=True, help_text="Project description")
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('LIVE', 'Live'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT',
        help_text="Current lifecycle state of the project."
    )
    
    launched_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the project was first set to LIVE.")

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        
        # On creation, if status is LIVE, it's technically a launch
        if not self.pk:
            if self.status == 'LIVE':
                self.launched_at = timezone.now()
            elif self.status == 'DRAFT':
                # Initial default status for new projects
                pass
        else:
            old_instance = Project.objects.get(pk=self.pk)
            # If manually changing status to LIVE, ensure we have a launch timestamp
            if old_instance.status != self.status:
                if self.status == 'LIVE' and not self.launched_at:
                    self.launched_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def can_accept_annotations(self):
        return self.status == 'LIVE'
    
    # CONFIGURATION
    
    informed_consent_config = models.TextField(
        default=get_default_configuration_for_informed_consent, 
        help_text="Informed Consent Configuration: accept a string can be showed to the annotator before starting the task"
    )
    
    task_type_config = models.JSONField(
        default=get_default_configuration_for_task_type, 
        help_text="Task Configuration (labels, colors, questions)"
    )

    # --- QUALITY CONTROL / GOLD UNITS ---
    enable_gold_units = models.BooleanField(
        default=True,
        help_text="If True, gold units will be injected for quality control during annotation."
    )

    min_accuracy_required = models.FloatField(
        default=0.6, 
        help_text="Minimum accuracy required for gold tasks (0.0 to 1.0)."
    )
    
    gold_injection_frequency = models.IntegerField(
        default=5, 
        help_text="Frequency of gold task injection (e.g., 1 every 5 tasks)."
    )
    
    min_gold_before_eval = models.IntegerField(
        default=3, 
        help_text="Min gold units completed before starting evaluation."
    )
    
    gold_units_file = models.FileField(
        upload_to='datasets/gold/', 
        null=True,
        blank=True,
        help_text="Upload a .jsonl file for GOLD units (Quality Control Injection)."
    )

    # --- TOGGLE SWITCHES ---
    enable_screening = models.BooleanField(
        default=True,
        help_text="If True, annotators will see the screening questionnaire before the task."
    )

    screening_config = models.JSONField(
        default=get_default_screening_config,
        blank=True,
        help_text="Screening questionnaire: JSON list of questions shown to annotators before the task. Empty list = skip screening."
    )

    # --- CODEBOOK (BACKGROUND TEORICO-PRATICO) ---
    enable_codebook = models.BooleanField(
        default=True,
        help_text="If True, annotators will see the codebook/instructions before the task."
    )
    
    codebook_content = models.TextField(
        default=get_default_codebook_content,
        blank=True,
        help_text="Codebook content in Markdown format. Shown to annotators as theoretical/practical background."
    )

    # --- INSTRUCTIONS / ONBOARDING ---
    enable_instructions = models.BooleanField(
        default=True,
        help_text="If True, annotators will see task instructions and optional practice task before annotating."
    )

    instructions_content = models.TextField(
        default=get_default_instructions_content,
        blank=True,
        help_text="Instructions content in Markdown format. Shown to annotators as task instructions before the practice."
    )

    enable_practice_task = models.BooleanField(
        default=True,
        help_text="If True, annotators will see a practice task before starting the real task."
    )

    practice_task_config = models.JSONField(
        default=get_default_practice_task,
        blank=True,
        help_text="Practice task config: { text, gold_solution: {classification, spans[]}, hints[] }. Empty = no practice."
    )

    practice_task_required = models.BooleanField(
        default=False,
        help_text="If True, annotators must pass the practice task correctly before starting. If False, they can skip after attempting."
    )

    # --- DISTRIBUTION CONSTRAINTS ---

    STRATEGY_CHOICES = [
        ('STANDARD', 'Standard - Randomly assign documents to annotators'),
        ('FULL_OVERLAP', 'Everyone sees everything (High Redundancy) - All annotators see all documents'),
        ('SAME_ANNOTATORS', 'Same k annotators view the same document (Low Redundancy) - the annotators are assigned to blocks of documents')
    ]
    
    distribution_strategy = models.CharField(
        max_length=20, 
        choices=STRATEGY_CHOICES, 
        default='STANDARD',
        help_text="Defines how documents are assigned to annotators."
    )

    min_annotations_per_doc = models.IntegerField(
        default=3, 
        help_text="Target: How many people must annotate each document."
    )
    
    max_annotations_per_doc = models.IntegerField(
        default=5, 
        help_text="Hard Cap: Stop serving the document if it reaches this number (prevents waste)."
    )

    # If a document has 2 annotations and others have 0, should unannotated ones be prioritized?
    prioritize_unannotated = models.BooleanField(
        default=True,
        help_text="If True, the system will try to finish unannotated documents first."
    )

    # BLOCK SETTINGS FOR SAME_ANNOTATORS
    block_size = models.IntegerField(
        default=10,
        help_text="SAME_ANNOTATORS strategy: Number of documents injected into each block."
    )
    
    annotators_per_block = models.IntegerField(
        default=3,
        help_text="SAME_ANNOTATORS strategy: Number of distinct annotators assigned to each block."
    )

    dataset_text_key = models.CharField(
        max_length=100, 
        default='text',
        help_text="The JSON key containing the text to be annotated (e.g., 'text', 'body', 'content')."
    )
    
    dataset_id_key = models.CharField(
        max_length=100, 
        default='_id',
        blank=True,
        help_text="The JSON key for the ID. If empty or not found, it will use the row number."
    )

    # If a document has 2 annotations and others have 0, should unannotated ones be prioritized?
    prioritize_unannotated = models.BooleanField(
        default=True,
        help_text="If True, the system will try to finish unannotated documents first."
    )

    documents_file = models.FileField(
        upload_to='datasets/documents/', 
        help_text="Upload a .jsonl file for REAL documents to be annotated."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    def __str__(self):
        return self.name

class ProjectLogEntry(models.Model):
    """
    Tracks significant events in a project's lifecycle.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, help_text="The event type (e.g., 'Project Launched', 'Status Changed', 'Data Imported')")
    details = models.TextField(blank=True, help_text="Optional details or message.")
    
    objects = models.Manager()
    
    class Meta:
        verbose_name = "Project Log Entry"
        verbose_name_plural = "Project Log Entries"
        ordering = ['-timestamp']

    def __str__(self):
        if self.timestamp:
            return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action}"
        return f"[No Date] {self.action}"

class Annotator(models.Model):
    prolific_pid = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict, blank=True)
    consent_accepted = models.BooleanField(default=False)
    screening_completed = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    
    objects = models.Manager()

    def __str__(self):
        return f"{self.prolific_pid} (Consent: {self.consent_accepted})"

class ProjectEnrollment(models.Model):
    """
    Tracks the status of an annotator for a specific project (Screening/Training phase).
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='enrollments')
    annotator = models.ForeignKey(Annotator, on_delete=models.CASCADE, related_name='enrollments')
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),       # Pre-annotation phases not completed
        ('ACTIVE', 'Active'),         # Annotating documents
        ('EXCLUDED', 'Excluded'),     # Removed for low quality
        ('COMPLETED', 'Completed'),   # Target tasks reached
    ]

    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="PENDING = pre-task phases incomplete. ACTIVE = annotating. EXCLUDED = low quality. COMPLETED = done."
    )
    
    # Gold Unit Quality Metrics
    gold_tasks_completed = models.IntegerField(default=0)
    gold_accuracy = models.FloatField(null=True, blank=True)
    gold_strikes = models.IntegerField(default=0, help_text="Consecutive wrong gold answers (for strike-based evaluation).")
    
    # Per-project phase tracking
    codebook_completed = models.BooleanField(default=False)
    
    exclude_from_distribution = models.BooleanField(default=False)
    
    assigned_block_id = models.IntegerField(null=True, blank=True, help_text="The document block assigned to this annotator (for SAME_ANNOTATORS).")
    
    # MACE Quality Estimation
    mace_competence_score = models.FloatField(null=True, blank=True, help_text="MACE estimated reliability (0.0 to 1.0)")
    mace_spam_bias = models.JSONField(default=dict, blank=True, help_text="Estimated bias distribution when guessing")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    
    class Meta:
        unique_together = ('project', 'annotator')
        verbose_name = "Enrollment & Assignment"
        verbose_name_plural = "Enrollments & Assignments"

    def __str__(self):
        return f"{self.annotator} -> {self.project} ({self.status})"

class Document(models.Model):
    """
    The text unit to be annotated.
    """
    # Unique document ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link the document to a batch
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    
    # The actual text content.
    # Since the source dataset is redacted, this field might need to be populated 
    text = models.TextField()
    
    # External ID (e.g. ID from the original dataset)
    external_id = models.CharField(max_length=100, blank=True, null=True)

    # Metadata for context (e.g., {"subreddit": "conspiracy", "thread_id": "..."})
    metadata = JSONField(default=dict, blank=True)
    
    # GOLD UNITS MANAGEMENT (Quality Control)
    # If True, this document has a known correct answer and is used for injection.
    is_gold_unit = models.BooleanField(default=False)
    # The correct answer (in JSON format) for automatic comparison
    gold_solution = JSONField(default=dict, blank=True, null=True)

    # MACE Inference Results
    mace_gold_label = models.CharField(max_length=50, null=True, blank=True)
    mace_confidence = models.FloatField(null=True, blank=True, help_text="Certainty of the MACE prediction (entropy)")

    # REDUNDANCY MANAGEMENT (CRITICAL)
    # BUSINESS LOGIC: REDUNDANCY
    # ---------------------------------------------------------
    # Controls the number of distinct annotators required for each document.
    # - 1 = Single annotation (High risk of noise).
    # - 3 = Standard for majority voting.
    # - 5+ = High precision required.
    min_annotations_required = models.IntegerField(default=3)
    
    # Denormalized counter. 
    # Every time an annotation arrives, we increment this number.
    # Used for very fast queries like: "Get all docs with count < 3"
    current_annotations_count = models.IntegerField(default=0, db_index=True)

    # GROUPING/BLOCK FOR 'SAME_ANNOTATORS' STRATEGY
    block_id = models.IntegerField(null=True, blank=True, db_index=True, help_text="Used to group documents into blocks for the SAME_ANNOTATORS strategy")

    objects = models.Manager()

    def __str__(self):
        return f"Doc {self.id} ({self.current_annotations_count}/{self.min_annotations_required})"

class Annotation(models.Model):
    """
    Links an Annotator to a Document.
    """
    # Unique annotation ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link the annotation to a document
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='annotations')
    # Link the annotation to an annotator
    annotator = models.ForeignKey(Annotator, on_delete=models.PROTECT, related_name='annotations')
    
    # THE RESULT PAYLOAD
    # Expected structure for PsyCoMark:
    # {
    #   "classification": "Yes",
    #   "spans": [
    #       {"start": 10, "end": 20, "label": "Actor", "text": "The government"}
    #   ]
    # }
    result = JSONField()
    
    # How long it took (useful to discard those taking 2 seconds = bot/spam)
    milliseconds_to_complete = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        # An annotator cannot annotate the same document twice, the DB will raise an error if they try.
        unique_together = ('document', 'annotator')

    def __str__(self):
        return f"Annotation {self.id} by {self.annotator}"

class DocumentProxy(Document):
    """Proxy model for standard Documents."""
    class Meta:
        proxy = True
        verbose_name = "Annotation Document"
        verbose_name_plural = "Annotation Documents"

class GoldUnitProxy(Document):
    """Proxy model for Quality Control Units (Gold Injection)."""
    class Meta:
        proxy = True
        verbose_name = "Gold Unit"
        verbose_name_plural = "Gold Units"
```

---

### FILE: backend\annotation\serializers.py
```
from rest_framework import serializers
from .models import Project, Document, Annotation, Annotator
import json


class DocumentSerializer(serializers.ModelSerializer):
    """
    The document serializer sends the text and the project configuration to the frontend.
    The default config is already set in models.py at project creation time (single source of truth).
    """
    project_config = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'text', 'project_config']

    def get_project_config(self, obj):
        config = obj.project.task_type_config or {}

        # Handle string case (bug fix for some DBs)
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}

        if not isinstance(config, dict):
            config = {}

        # Remove internal/sensitive fields before sending to frontend
        config.pop('task_type', None)

        return config

class AnnotationSerializer(serializers.ModelSerializer):
    """ 
    The annotation serializer receives the annotation result from the frontend
    """
    class Meta:
        model = Annotation
        fields = ['document', 'result', 'milliseconds_to_complete']
```

---

### FILE: backend\annotation\services.py
```
import json
from .models import Document

def process_uploaded_dataset(project, file_obj):
    """
    DATASET IMPORT LOGIC
    Reads a JSONL file and imports documents.
    """
    count = 0
    warnings = []

    # Extract valid classification values from the project's task config
    task_config = project.task_type_config or {}
    valid_class_values = {
        label.get('value') 
        for label in task_config.get('class_labels', []) 
        if label.get('value')
    }

    with file_obj.open() as f:
        text_key = project.dataset_text_key
        id_key = project.dataset_id_key
        
        current_regular_docs_count = Document.objects.filter(project=project, is_gold_unit=False).count()
        regular_docs_added_in_this_batch = 0

        try:
            for idx, line in enumerate(f, start=1):
                try:
                    line_str = line.decode('utf-8').strip()
                except AttributeError:
                    line_str = line.strip()
                
                if not line_str: continue 

                try:
                    data = json.loads(line_str)
                except json.JSONDecodeError:
                    warnings.append(f"Row {idx}: Invalid JSON, skipped.")
                    continue
                
                text = data.get(text_key)
                # Identify solution
                gold_sol = data.get('gold_solution', None)
                # A document is a gold unit if and only if it has a gold_solution
                is_gold_final = bool(gold_sol and isinstance(gold_sol, dict))

                if id_key and id_key in data:
                    external_id = str(data.get(id_key))
                else:
                    # Prefix based on detected gold status
                    prefix = "G" if is_gold_final else "D"
                    external_id = f"{prefix}-{idx}"

                # DYNAMIC METADATA
                # Special keys that are not metadata
                special_keys = {text_key, id_key, 'is_gold_unit', 'gold_solution'}
                metadata = {k: v for k, v in data.items() if k not in special_keys}

                if not text:
                    text = f"[CONTENT REDACTED]\nID: {external_id}"

                # VALIDATE GOLD UNIT CONSISTENCY (ONLY IF DETECTED AS GOLD)
                if is_gold_final and valid_class_values:
                    gold_class = gold_sol.get('classification')
                    if gold_class and gold_class not in valid_class_values:
                        warnings.append(
                            f"Row {idx}: Gold solution classification '{gold_class}' "
                            f"is not in project's class_labels {sorted(valid_class_values)}. "
                            f"Skipped."
                        )
                        continue
                    elif not gold_class:
                        warnings.append(f"Row {idx}: Gold solution is missing 'classification' key. Skipped.")
                        continue

                # Calculate block_id for SAME_ANNOTATORS strategy
                block_id = None
                if not is_gold_final and project.distribution_strategy == 'SAME_ANNOTATORS' and project.block_size > 0:
                    block_id = (current_regular_docs_count + regular_docs_added_in_this_batch) // project.block_size

                # Upsert Document
                obj, created = Document.objects.update_or_create(
                    project=project,
                    external_id=external_id,
                    defaults={
                        'text': text,
                        'metadata': metadata,
                        'is_gold_unit': is_gold_final, 
                        'gold_solution': gold_sol if is_gold_final else None,
                        'min_annotations_required': project.min_annotations_per_doc,
                        'block_id': block_id,
                    }
                )
                if not is_gold_final:
                    regular_docs_added_in_this_batch += 1
                count += 1     
        except Exception as e:
            raise e
    
    return count, warnings

def parse_json_upload(file_obj):
    """
    Reads a Django UploadedFile (or InMemoryUploadedFile) and returns
    the parsed JSON content as a Python dict/list.
    Raises ValueError on invalid JSON.
    """
    content = file_obj.read()
    try:
        text = content.decode('utf-8')
    except AttributeError:
        text = content
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

```

---

### FILE: backend\annotation\signals.py
```
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Annotation


'''
The system implements a self-healing mechanism for data validation. 
When a researcher manually deletes a rejected annotation (e.g., from a spammer), 
the post_delete signal triggers an automatic update of the document's completion status. 
By decrementing the annotation count, the system recognizes the document as 'incomplete' 
and places it back into the assignment pool, guaranteeing that every document eventually 
receives the target number of valid annotations.
'''

#Execute this function AFTER (post) an Annotation has been saved
@receiver(post_save, sender=Annotation)
def update_annotation_count_on_save(sender, instance, created, **kwargs):
    """
    Triggered when an Annotation is saved.
    Increments the 'current_annotations_count' on the parent Document.
    """
    if created:
        doc = instance.document
        # We count the actual records in the DB to ensure consistency
        # (Safer than blindly incrementing +1)
        doc.current_annotations_count = doc.annotations.count()
        # We only update the specific field to optimize performance
        doc.save(update_fields=['current_annotations_count'])

@receiver(post_delete, sender=Annotation)
def update_annotation_count_on_delete(sender, instance, **kwargs):
    """
    Triggered when an Annotation is deleted (e.g., removing spam).
    Decrements the 'current_annotations_count'.
    
    This effectively 're-opens' the task if the count drops below 
    the 'min_annotations_required' threshold.
    """
    doc = instance.document
    doc.current_annotations_count = doc.annotations.count()
    doc.save(update_fields=['current_annotations_count'])
```

---

### FILE: backend\annotation\tests.py
```

```

---

### FILE: backend\annotation\urls.py
```
# backend/core/urls.py

from django.urls import path
from .views import (
    InitializeSession, GetNextTask, SubmitAnnotation, 
    AcceptConsent, CompleteOnboarding, GetConsent,
    GetScreening, SubmitScreening,
    GetCodebook, CompleteCodebook,
    GetInstructions
)

urlpatterns = [
    path('session/', InitializeSession.as_view(), name='session'),
    path('consent/', AcceptConsent.as_view(), name='consent'),
    path('get-consent/', GetConsent.as_view(), name='get_consent'),
    path('screening/', SubmitScreening.as_view(), name='screening'),
    path('get-screening/', GetScreening.as_view(), name='get_screening'),
    path('get-codebook/', GetCodebook.as_view(), name='get_codebook'),
    path('codebook/', CompleteCodebook.as_view(), name='codebook'),
    path('get-instructions/', GetInstructions.as_view(), name='get_instructions'),
    path('onboarding/', CompleteOnboarding.as_view(), name='onboarding'),
    path('next-task/', GetNextTask.as_view(), name='next_task'),
    path('submit/', SubmitAnnotation.as_view(), name='submit'),
]
```

---

### FILE: backend\annotation\views.py
```
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
from .models import Document, Annotator, Annotation, Project, ProjectEnrollment
from .serializers import DocumentSerializer, AnnotationSerializer
from .gold_strategies import get_strategy, check_gold_correctness
from django.db.models import Count

PROLIFIC_COMPLETION_URL = "https://app.prolific.co/submissions/complete?cc=TUO_CODICE_PROLIFIC"

class InitializeSession(APIView):
    """
    RETURNS USER STATE / RESTITUISCE STATO UTENTE
    ---------------------------------------------------------
    Determines which page the frontend should display based on the user's progress.
    Pipeline: CONSENT -> SCREENING -> ONBOARDING -> ANNOTATION -> COMPLETED
    """
    def post(self, request):
        pid = request.data.get('prolific_pid')
        project_id = request.data.get('project_id')
        project_slug = request.data.get('project_slug')

        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        if not project_id and not project_slug:
            return Response({"error": "Missing Project ID or Slug"}, status=400)
            
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)

        if not project.can_accept_annotations:
            if project.status == 'DRAFT':
                return Response({"error": "This project is still in DRAF phase and not yet open."}, status=404)
            return Response({"error": f"Project is currently {project.status.lower()}"}, status=404)

        # Metadata extraction (e.g. STUDY_ID, SESSION_ID from Prolific)
        metadata = request.data.get('metadata', {})
        metadata.pop('project_id', None)
        metadata.pop('prolific_pid', None)
        metadata.pop('PROLIFIC_PID', None)
        
        annotator, created = Annotator.objects.get_or_create(prolific_pid=pid)
        
        if metadata:
            annotator.metadata.update(metadata)
            annotator.save()

        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator
        )

        # Determine current step based on pipeline progression
        # Pipeline: CONSENT -> SCREENING -> CODEBOOK -> ONBOARDING -> ANNOTATION -> COMPLETED
        current_step = 'CONSENT'
        if annotator.consent_accepted:
            # Check if project has a survey and annotator hasn't completed it
            has_screening = project.enable_screening and project.screening_config and len(project.screening_config) > 0
            if has_screening and not annotator.screening_completed:
                current_step = 'SCREENING'
            elif project.enable_codebook and not enrollment.codebook_completed:
                current_step = 'CODEBOOK'
            elif project.enable_instructions and not annotator.onboarding_completed:
                current_step = 'INSTRUCTIONS'
            else:
                current_step = 'ONBOARDING'
        if annotator.onboarding_completed:
            current_step = 'ANNOTATION'
            
        # To check completion universally, rely on GetNextTask logic when it actually loads
        # Here we just assume they are annotating if in ANNOTATION phase, 
        # actual completion is detected when `GetNextTask` returns no more valid docs.
        # However, to avoid showing the 'ANNOTATION' loop indefinitely on refresh if there are literally 0 items,
        # we still flag 'COMPLETED' if `status` was set to completed by `GetNextTask`
        if enrollment.status == 'COMPLETED':
            current_step = 'COMPLETED'

        return Response({
            "status": "ok",
            "step": current_step,
            "completion_url": PROLIFIC_COMPLETION_URL if current_step == 'COMPLETED' else None
        })

class AcceptConsent(APIView):
    """ Saves that the user accepted the consent """
    def post(self, request):
        pid = request.data.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        annotator.consent_accepted = True
        annotator.save()
        return Response({"status": "ok", "next_step": "SCREENING"})

class GetCodebook(APIView):
    """
    Returns the codebook content for a project.
    GET /api/v1/get-codebook/?pid=XX&project_slug=XX
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_slug = request.query_params.get('project_slug')
        project_id = request.query_params.get('project_id')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_codebook:
            return Response({"content": "", "skip": True})

        return Response({
            "content": project.codebook_content or "",
            "skip": False
        })

class CompleteCodebook(APIView):
    """
    Marks the codebook as completed for this annotator+project.
    POST /api/v1/codebook/
    Body: { pid, project_slug }
    """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')

        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        elif project_id:
            project = get_object_or_404(Project, id=project_id)
        else:
            return Response({"error": "Missing Project identification"}, status=400)
        
        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project,
            annotator=annotator
        )
        
        enrollment.codebook_completed = True
        enrollment.save()
        
        return Response({"status": "ok", "next_step": "INSTRUCTIONS"})

class GetInstructions(APIView):
    """
    Returns instructions content and practice task config for a project.
    GET /api/v1/get-instructions/?pid=XX&project_slug=XX
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_slug = request.query_params.get('project_slug')
        project_id = request.query_params.get('project_id')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_instructions:
            return Response({"content": "", "skip": True})

        practice = project.practice_task_config or {}
        has_practice = bool(practice and practice.get('text'))

        # Read `required` from inside the JSON first, fallback to the dedicated field
        practice_required = practice.get('required', project.practice_task_required) if has_practice else False

        return Response({
            "content": project.instructions_content or "",
            "practice_task": practice if has_practice else None,
            "practice_task_required": practice_required,
            "task_config": project.task_type_config or {},
            "skip": False
        })


class GetScreening(APIView):
    """
    Returns the screening questionnaire configuration for a project.
    GET /api/v1/get-screening/?pid=XX&project_slug=XX
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')
        project_slug = request.query_params.get('project_slug')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if annotator.screening_completed:
            return Response({"error": "Screening already completed"}, status=400)

        if not project.enable_screening:
            return Response({"questions": [], "skip": True})

        screening_config = project.screening_config or []
        
        if not screening_config:
            return Response({"questions": [], "skip": True})

        return Response({
            "questions": screening_config,
            "skip": False
        })

class SubmitScreening(APIView):
    """
    Saves screening responses from an annotator.
    POST /api/v1/screening/
    Body: { pid, project_slug, responses: { question_id: answer, ... } }
    """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')
        responses = request.data.get('responses', {})

        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        # Get project to validate required fields
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        elif project_id:
            project = get_object_or_404(Project, id=project_id)
        else:
            return Response({"error": "Missing Project identification"}, status=400)

        # Validate required fields
        screening_config = project.screening_config or []
        for question in screening_config:
            if question.get('required', False):
                q_id = question.get('id')
                if q_id not in responses or responses[q_id] is None or responses[q_id] == '':
                    return Response(
                        {"error": f"Required field '{question.get('label', q_id)}' is missing."},
                        status=400
                    )

        # Save responses into annotator metadata
        annotator.metadata['screening_responses'] = responses
        annotator.screening_completed = True
        annotator.save()

        return Response({"status": "ok", "next_step": "ONBOARDING"})

class CompleteOnboarding(APIView):
    """ 
    Saves that the user completed instructions/training.
    Also transitions enrollment to ACTIVE if all pre-task phases are complete.
    """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        annotator.onboarding_completed = True
        annotator.save()
        
        # Transition enrollment PENDING -> ACTIVE if all phases complete
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        elif project_id:
            project = get_object_or_404(Project, id=project_id)
        else:
            # Fallback: try to find any pending enrollment
            project = None

        if project:
            enrollment, _ = ProjectEnrollment.objects.get_or_create(
                project=project,
                annotator=annotator
            )
            
            # Check all pre-task phases
            screening_ok = annotator.screening_completed or not project.enable_screening or not project.screening_config or len(project.screening_config) == 0
            all_phases_complete = (
                annotator.consent_accepted and 
                screening_ok and 
                annotator.onboarding_completed
            )
            
            if all_phases_complete and enrollment.status == 'PENDING':
                enrollment.status = 'ACTIVE'
                enrollment.save()

        return Response({"status": "ok", "next_step": "ANNOTATION"})

class SubmitAnnotation(APIView):
    """
    Endpoint: POST /api/v1/submit/
    Saves the user's work.
    """
    def post(self, request):
        pid = request.data.get('pid')
        if not pid:
            return Response({"error": "Missing PID"}, status=status.HTTP_400_BAD_REQUEST)
            
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        data = request.data.copy()
        serializer = AnnotationSerializer(data=data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    annotation = serializer.save(annotator=annotator)
                    
                    # --- QUALITY CONTROL / GOLD UNIT LOGIC ---
                    document = annotation.document
                    project = document.project
                    
                    enrollment, _ = ProjectEnrollment.objects.get_or_create(
                        project=project,
                        annotator=annotator
                    )
                    
                    if document.is_gold_unit:
                        enrollment.gold_tasks_completed += 1
                        
                        # Evaluate correctness using strategy pattern
                        annotation_result = data.get('result', {})
                        is_correct = check_gold_correctness(annotation_result, document.gold_solution)
                        
                        # Pack configuration into a dict for strategy compatibility (now hardcoded to percentage)
                        strategy = get_strategy()
                        gold_cfg = {
                            'min_accuracy_required': project.min_accuracy_required,
                            'min_gold_before_eval': project.min_gold_before_eval,
                        }
                        
                        # Execute strategy — updates enrollment fields internally
                        should_exclude, reason = strategy(enrollment, gold_cfg, is_correct)
                        
                        if should_exclude:
                            enrollment.status = 'EXCLUDED'
                        
                        enrollment.save()

                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetNextTask(APIView):
    """
    DETERMINES THE NEXT TASK FOR THE ANNOTATOR
    ---------------------------------------------------------
    Logic:
    1. Check enrollment status (must be ACTIVE).
    2. Check if target tasks reached.
    3. Gold Injection logic OR Normal document selection.
    4. Concurrent safe selection using SKIP LOCKED.
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')
        project_slug = request.query_params.get('project_slug')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing 'pid' or 'project' identification"}, status=400)

        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)

        if not project.can_accept_annotations:
            return Response({"status": "stopped", "message": f"This project is currently {project.status.lower()} and not accepting annotations."})

        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator
        )

        if enrollment.exclude_from_distribution:
            return Response({"status": "stopped", "message": "Access denied for this project."})

        # Check enrollment status
        if enrollment.status == 'EXCLUDED':
            return Response({"status": "stopped", "message": "You have been excluded from this project due to quality issues."})
        
        if enrollment.status == 'COMPLETED':
            return self._completed_response()

        # Current count is still useful for gold injection frequency calculation
        done_count = annotator.annotations.filter(document__project=project).count()
        
        if enrollment.status == 'PENDING':
            # User hasn't completed pre-task phases yet
            return Response({"status": "stopped", "message": "Please complete all pre-task steps first."})

        # TASK SELECTION (Concurrency Safe)
        with transaction.atomic():
            target_id = self._get_candidate_id(project, annotator, enrollment, done_count)
            
            if not target_id:
                # No more candidates found meaning they actually completed everything
                if enrollment.status != 'COMPLETED':
                    enrollment.status = 'COMPLETED'
                    enrollment.save()
                return self._completed_response()

            final_doc = Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()

        if final_doc:
            return self._task_response(final_doc, enrollment)
        
        return self._completed_response()

    def _get_candidate_id(self, project, annotator, enrollment, done_count):
        """ Internal logic to find the 'next' candidate ID """
        
        # A. QUALITY CONTROL (GOLD INJECTION)
        if self._should_inject_gold(project, done_count):
             gold_id = self._find_gold_candidate(project, annotator)
             if gold_id:
                 return gold_id

        # B. REGULAR PHASE - NORMAL DOCUMENTS
        return self._find_normal_candidate(project, annotator, enrollment)

    def _should_inject_gold(self, project, done_count):
        """ Determines if a Gold Unit should be injected based on frequency settings """
        if not project.enable_gold_units:
            return False
        injection_freq = project.gold_injection_frequency or 0
        return injection_freq > 0 and (done_count + 1) % injection_freq == 0

    def _find_gold_candidate(self, project, annotator):
        """ Finds a Gold Unit the annotator hasn't seen yet """
        return Document.objects.filter(
            project=project,
            is_gold_unit=True
        ).exclude(
            annotations__annotator=annotator
        ).values_list('id', flat=True).first()

    def _find_normal_candidate(self, project, annotator, enrollment):
        """ Finds a regular document based on the distribution strategy """
        base_qs = Document.objects.filter(
            project=project,
            is_gold_unit=False
        )
        
        if project.distribution_strategy == 'SAME_ANNOTATORS':
            if enrollment.assigned_block_id is None:
                # Find the first available block with less than <max_capacity> active users
                max_capacity = project.annotators_per_block
                existing_blocks = Document.objects.filter(
                    project=project, 
                    is_gold_unit=False, 
                    block_id__isnull=False
                ).values_list('block_id', flat=True).distinct().order_by('block_id')
                
                assigned = False
                for block in existing_blocks:
                    enrolled_in_block = ProjectEnrollment.objects.filter(
                        project=project, 
                        assigned_block_id=block
                    ).count()
                    
                    if enrolled_in_block < max_capacity:
                        enrollment.assigned_block_id = block
                        enrollment.save(update_fields=['assigned_block_id'])
                        assigned = True
                        break
                
                if not assigned:
                     # No available blocks with space left -> return None
                     return None

            base_qs = base_qs.filter(block_id=enrollment.assigned_block_id)

        base_qs = base_qs.exclude(
            annotations__annotator=annotator
        ).annotate(
            num_anns=Count('annotations')
        )

        candidates = base_qs
        
        if project.distribution_strategy in ['STANDARD', 'SAME_ANNOTATORS']:
            candidates = candidates.filter(num_anns__lt=project.max_annotations_per_doc)
            order = 'num_anns' if project.prioritize_unannotated else '?'
            candidates = candidates.order_by(order)
            
        elif project.distribution_strategy == 'FULL_OVERLAP':
            candidates = candidates.order_by('?')
        
        return candidates.values_list('id', flat=True).first()

    def _task_response(self, doc, enrollment):
        """ Prepares the final Response JSON """
        serializer = DocumentSerializer(doc)
        data = serializer.data 
        
        data.update({
            'is_gold': doc.is_gold_unit,
            'feedback_enabled': False  # Gold feedback can be enabled per-project if needed
        })
            
        return Response(data)

    def _completed_response(self):
        """ Standard response when no more tasks are available or target is reached """
        return Response({
            "status": "completed", 
            "completion_url": PROLIFIC_COMPLETION_URL
        })

class GetConsent(APIView):
    def get(self, request):
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')
        project_slug = request.query_params.get('project_slug')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if annotator.consent_accepted:
            return Response({"error": "Already consented"}, status=400)

        return Response({
            "consent_text": project.informed_consent_config
        })
```

---

### FILE: backend\annotation\__init__.py
```

```

---

### FILE: backend\annotation\admin\annotation.py
```
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html, mark_safe, escape
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
import json
from ..models import Annotation


class HideGoldFilter(admin.SimpleListFilter):
    title = 'Task Category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return (
            ('regular', 'Regular Tasks'),
            ('gold', 'Gold Tasks'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'regular':
            return queryset.filter(document__is_gold_unit=False)
        if val == 'gold':
            return queryset.filter(document__is_gold_unit=True)
        return queryset


@admin.register(Annotation)
class AnnotationAdmin(ModelAdmin):
    list_display = ('short_id', 'annotation_type', 'document_link', 'annotator_link', 'created_at', 'seconds_to_complete')
    list_filter = (HideGoldFilter, 'document__project', 'created_at', 'annotator')
    search_fields = ('document__text', 'annotator__prolific_pid', 'result')
    readonly_fields = ('created_at', 'formatted_result')
    exclude = ('result',)

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8] + '...'

    @admin.display(description="Type", ordering='document__is_gold_unit')
    def annotation_type(self, obj):
        if obj.document and obj.document.is_gold_unit:
            return mark_safe(
                '<span style="background:#fbbf24; color:#1f2937; padding:2px 8px; '
                'border-radius:4px; font-size:11px; font-weight:600;">'
                '🏆 Gold Task</span>'
            )
        return mark_safe(
            '<span style="background:#059669; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:11px; font-weight:600;">'
            '📝 Regular</span>'
        )

    @admin.display(description="Document")
    def document_link(self, obj):
        if not obj.document:
            return "-"
        if obj.document.is_gold_unit:
            url = reverse("admin:annotation_goldunitproxy_change", args=[obj.document.id])
        else:
            url = reverse("admin:annotation_documentproxy_change", args=[obj.document.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.document))

    @admin.display(description="Annotator")
    def annotator_link(self, obj):
        if not obj.annotator:
            return "-"
        url = reverse("admin:annotation_annotator_change", args=[obj.annotator.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.annotator))

    @admin.display(description="Time")
    def seconds_to_complete(self, obj):
        if not obj.milliseconds_to_complete:
            return "-"
        if obj.milliseconds_to_complete < 5000:
            return format_html(
                '<span style="color: #ef4444; font-weight:600;">{}ms</span>',
                obj.milliseconds_to_complete
            )
        return format_html(
            '<span style="color: #22c55e;">{}ms</span>',
            obj.milliseconds_to_complete
        )

    @admin.display(description="Annotated Results Visualization")
    def formatted_result(self, obj):
        if not obj.result:
            return "-"
            
        text = obj.document.text if obj.document else ""
        spans = obj.result.get('spans', [])
        classification = obj.result.get('classification', 'N/A')
        
        # Sort spans by starting index
        spans = sorted(spans, key=lambda x: x.get('start', 0))
        
        # Get colors from project configuration
        try:
            project_labels = obj.document.project.task_type_config.get('span_labels', [])
            color_map = {label['name']: label.get('color', '#fbbf24') for label in project_labels}
        except Exception:
            color_map = {}
            
        last_idx = 0
        html_parts = []
        
        # Add CSS styles for dark mode compatibility
        html_parts.append(
            '<style>'
            '.annot-class-box { margin-bottom: 20px; padding: 12px 16px; background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 8px; font-size: 14px; color: #0369a1; }'
            '.annot-class-val { background: white; padding: 4px 10px; border-radius: 6px; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }'
            '.annot-container { line-height: 2.2; font-size: 16px; padding: 24px; border: 1px solid #e5e7eb; border-radius: 8px; background: white; color: #374151; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }'
            '.annot-details { margin-top: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }'
            '.annot-summary { cursor: pointer; padding: 12px 16px; background: #f9fafb; color: #4b5563; font-size: 14px; font-weight: 500; user-select: none; }'
            '.annot-label { display: inline-block; font-size: 0.70rem; font-weight: 700; margin-left: 6px; text-transform: uppercase; background: white; padding: 2px 6px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); position: relative; top: -1px; }'
            'html[data-theme="dark"] .annot-class-box, .dark .annot-class-box { background: #0c4a6e; border-color: #075985; color: #bae6fd; }'
            'html[data-theme="dark"] .annot-class-val, .dark .annot-class-val { background: #082f49; color: #e0f2fe; }'
            'html[data-theme="dark"] .annot-container, .dark .annot-container { background: #1f2937; border-color: #374151; color: #d1d5db; box-shadow: none; }'
            'html[data-theme="dark"] .annot-details, .dark .annot-details { border-color: #374151; }'
            'html[data-theme="dark"] .annot-summary, .dark .annot-summary { background: #111827; color: #9ca3af; }'
            'html[data-theme="dark"] .annot-label, .dark .annot-label { background: #374151; color: #e5e7eb; box-shadow: none; border: 1px solid #4b5563 !important; }'
            'html[data-theme="dark"] mark, .dark mark { color: #f9fafb !important; }'
            '</style>'
        )

        # Add Classification Badge
        html_parts.append(
            f'<div class="annot-class-box">'
            f'<strong style="margin-right: 8px;">Classification:</strong>'
            f'<span class="annot-class-val">{escape(str(classification))}</span>'
            f'</div>'
        )
        
        # Start Document Text Box
        html_parts.append('<div class="annot-container">')
        
        for span in spans:
            start = span.get('start', 0)
            end = span.get('end', 0)
            label = span.get('label', 'Unknown')
            color = color_map.get(label, '#fbbf24')
            hex_color = color if str(color).startswith('#') else '#fbbf24'
            
            # Add unannotated text before this span
            if start > last_idx:
                html_parts.append(escape(text[last_idx:start]))
                
            # Add annotated text
            span_text = text[start:end]
            html_parts.append(
                f'<mark style="background-color: {hex_color}33; border-bottom: 3px solid {hex_color}; padding: 4px 6px; border-radius: 4px; margin: 0 2px;" title="{escape(label)}">'
                f'{escape(span_text)}'
                f'<span class="annot-label" style="color: {hex_color}; border: 1px solid {hex_color}33;">{escape(label)}</span>'
                f'</mark>'
            )
            last_idx = end
            
        # Add remaining text
        if last_idx < len(text):
            html_parts.append(escape(text[last_idx:]))
            
        html_parts.append('</div>')
        
        # Add raw JSON toggle
        raw_json = json.dumps(obj.result, indent=2)
        html_parts.append(
            f'<details class="annot-details">'
            f'<summary class="annot-summary">View Raw JSON Payload</summary>'
            f'<div style="padding: 16px; background: #111827; overflow-x: auto;">'
            f'<pre style="color: #6ee7b7; font-size: 13px; font-family: monospace; margin: 0;">{escape(raw_json)}</pre>'
            f'</div>'
            f'</details>'
        )
        
        return mark_safe("".join(html_parts))

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'document__project__id__exact' not in request.GET and 'document__project__id' not in request.GET:
            self.message_user(request, "Select a project first to view its annotations.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        """Hides this model from the sidebar/index."""
        return False

```

---

### FILE: backend\annotation\admin\annotator.py
```
from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.db.models import ProtectedError
import json
from ..models import Annotator
from .utils import HighlightMedia

@admin.register(Annotator)
class AnnotatorAdmin(ModelAdmin):
    list_display = ('prolific_pid', 'created_at', 'view_work_link')
    search_fields = ('prolific_pid',)
    
    # created_at is read-only to prevent editing
    readonly_fields = ('created_at', 'formatted_metadata')

    fieldsets = (
        ("Annotator Profile", {
            "fields": ("prolific_pid", "created_at")
        }),
        ("Onboarding Status", {
            "fields": ("consent_accepted", "screening_completed", "onboarding_completed"),
            "description": "Manage annotator's progression status."
        }),
        ("Metadata", {
            "fields": ("formatted_metadata",),
            "description": "JSON metadata associated with this worker (e.g. Group, Demographics)."
        }),
    )
    
    # CSS/JS for Highlight.js syntax highlighting
    Media = HighlightMedia

    @admin.display(description="Metadata (JSON)")
    def formatted_metadata(self, obj):
        if not obj or not obj.metadata:
            return format_html('<em style="color:#999">{}</em>', "No metadata present.")
        
        try:
            json_str = json.dumps(obj.metadata, indent=4, sort_keys=True)
            return format_html(
                '''
                <div style="border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden;">
                    <pre style="margin: 0;"><code class="json" style="padding: 15px; display: block; overflow-x: auto; max-height: 400px;">{}</code></pre>
                </div>
                ''',
                json_str
            )
        except Exception:
            return "-"

    @admin.display(description="History")
    def view_work_link(self, obj):
        # Safety check: don't show link if the object has no ID yet (e.g. during creation)
        if not obj or not obj.id:
            return "-"
            
        count = obj.annotations.count()
        
        # Generazione URL sicura
        base_url = reverse("admin:annotation_annotation_changelist")
        query_string = urlencode({"annotator__id": f"{obj.id}"})
        full_url = f"{base_url}?{query_string}"
        
        return format_html('<a href="{}" style="font-weight:bold;">View {} Tasks</a>', full_url, count)

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except ProtectedError:
            count = obj.annotations.count()
            messages.error(
                request,
                f'Cannot delete "{obj.prolific_pid}": '
                f'this annotator has {count} annotation(s). '
                f'Delete the annotations first, then retry.'
            )

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)

```

---

### FILE: backend\annotation\admin\document.py
```
from django.contrib import admin
from import_export import resources
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..models import Document, DocumentProxy, GoldUnitProxy

class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        fields = ('id', 'text', 'external_id', 'project')

class BaseDocumentAdmin(ModelAdmin, ImportExportModelAdmin):
    """Base logic for Document administration."""
    resource_class = DocumentResource
    search_fields = ('text', 'external_id', 'metadata')
    
    @admin.display(description="Text Preview")
    def short_text(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text

    @admin.display(description="External ID", ordering="external_id")
    def external_id_display(self, obj):
        return obj.external_id

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'project__id__exact' not in request.GET and 'project__id' not in request.GET:
            self.message_user(request, "Select a project first to view its records.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        return False

@admin.register(DocumentProxy)
class DocumentProxyAdmin(BaseDocumentAdmin):
    list_display = ('external_id_display', 'short_text', 'project', 'current_annotations_count', 'is_completed', 'mace_gold_display', 'mace_confidence_display')
    list_filter = ('project',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_gold_unit=False)

    @admin.display(boolean=True, description="Completed?")
    def is_completed(self, obj):
        return obj.current_annotations_count >= obj.min_annotations_required

    @admin.display(description="MACE Label")
    def mace_gold_display(self, obj):
        if obj.mace_gold_label:
            return obj.mace_gold_label
        return "-"
        
    @admin.display(description="MACE Confidence", ordering="mace_confidence")
    def mace_confidence_display(self, obj):
        if obj.mace_confidence is None:
            return "-"
        
        score = obj.mace_confidence
        if score >= 0.8:
            color = "#10b981" # Green
        elif score >= 0.5:
            color = "#f59e0b" # Orange
        else:
            color = "#ef4444" # Red
            
        formatted_score = f"{score:.2f}"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, formatted_score
        )

    fieldsets = (
        ("Document Content", {"fields": ("external_id", "text")}),
        ("Context & Metadata", {"fields": ("project", "metadata")}),
        ("MACE Estimations", {"fields": ("mace_gold_label", "mace_confidence")}),
        ("Annotation Strategy", {"fields": ("min_annotations_required",)})
    )

@admin.register(GoldUnitProxy)
class GoldUnitProxyAdmin(BaseDocumentAdmin):
    list_display = ('external_id_display', 'short_text', 'project', 'gold_preview')
    list_filter = ('project',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_gold_unit=True)

    @admin.display(description="Gold Solution")
    def gold_preview(self, obj):
        if not obj.gold_solution: return "-"
        return obj.gold_solution.get('classification', 'N/A')

    fieldsets = (
        ("Gold Unit Content", {"fields": ("external_id", "text")}),
        ("Context", {"fields": ("project", "metadata")}),
        ("Quality Control", {"fields": ("gold_solution",)})
    )


```

---

### FILE: backend\annotation\admin\enrollment.py
```
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..models import ProjectEnrollment
from .utils import HighlightMedia


@admin.register(ProjectEnrollment)
class ProjectEnrollmentAdmin(ModelAdmin):
    list_display = (
        'annotator',
        'project',
        'status_badge',
        'gold_tasks_completed_display',
        'gold_accuracy_display',
        'mace_competence_display',
        'exclude_from_distribution',
        'created_at',
    )
    list_filter = ('status', 'project', 'exclude_from_distribution')
    search_fields = ('annotator__prolific_pid', 'project__name')
    list_select_related = ('annotator', 'project')

    readonly_fields = (
        'annotator',
        'project',
        'created_at',
        'updated_at',
        'gold_tasks_completed_display',
        'mace_competence_score',
        'mace_spam_bias',
    )

    fieldsets = (
        ("Enrollment", {
            "fields": ("annotator", "project", "status", "exclude_from_distribution"),
        }),
        ("Workload", {
            "fields": ("target_tasks",),
            "description": "How many tasks this specific user must complete for this project.",
        }),
        ("MACE Reliability Evaluation", {
            "fields": ("mace_competence_score", "mace_spam_bias"),
            "description": "Quality metrics estimated by the MACE algorithm based on consensus patterns (unsupervised).",
        }),
        ("Gold Task Metrics", {
            "fields": ("gold_tasks_completed_display", "gold_accuracy"),
            "description": "Quality metrics based on Gold Units (supervised).",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # CSS/JS for Highlight.js syntax highlighting
    Media = HighlightMedia

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f0ad4e',   # amber
            'ACTIVE': '#5cb85c',    # green
            'EXCLUDED': '#d9534f',  # red
            'COMPLETED': '#5bc0de', # blue
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; '
            'border-radius:4px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.status
        )

    @admin.display(description="Gold Accuracy")
    def gold_accuracy_display(self, obj):
        if obj.gold_accuracy is None:
            return "-"
        return f"{obj.gold_accuracy:.0%}"

    @admin.display(description="Gold Tasks Completed")
    def gold_tasks_completed_display(self, obj):
        return obj.gold_tasks_completed

    @admin.display(description="MACE Score", ordering="mace_competence_score")
    def mace_competence_display(self, obj):
        if obj.mace_competence_score is None:
            return "-"
        
        # Color code: red for < 0.3, orange for < 0.6, green for >= 0.6
        score = obj.mace_competence_score
        if score >= 0.6:
            color = "#10b981" # Green
        elif score >= 0.3:
            color = "#f59e0b" # Orange
        else:
            color = "#ef4444" # Red
            
        formatted_score = f"{score:.2f}"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, formatted_score
        )

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'project__id__exact' not in request.GET and 'project__id' not in request.GET:
            self.message_user(request, "Select a project first to view assignments.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        """Hides this model from the sidebar/index."""
        return False

```

---

### FILE: backend\annotation\admin\project.py
```
from django.contrib import admin
from django import forms
from unfold.admin import ModelAdmin, TabularInline
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse
from django.contrib import messages
import json
import re
from ..models import Project, Annotation, ProjectLogEntry
from ..services import parse_json_upload, process_uploaded_dataset
from ..mace_service import run_mace_for_project

class ProjectAdminForm(forms.ModelForm):
    """
    Custom form that adds non-model file inputs for uploading JSON configs.
    The uploaded file is parsed and stored directly into the JSONField on save.
    """
    upload_task_config = forms.FileField(
        required=False,
        label="Upload Task Config (JSON)",
        help_text="Upload a JSON file to overwrite the Task configuration (Labels, Questions)."
    )
    upload_screening_config = forms.FileField(
        required=False,
        label="Upload Screening Config (JSON)",
        help_text="Upload a JSON file to configure the screening questionnaire (demographics, etc.)."
    )
    upload_codebook_content = forms.FileField(
        required=False,
        label="Upload Codebook (Markdown)",
        help_text="Upload a .md file to overwrite the theoretical/practical background."
    )
    upload_instructions_content = forms.FileField(
        required=False,
        label="Upload Instructions (Markdown)",
        help_text="Upload a .md file for task instructions shown before the practice task."
    )
    upload_practice_task_config = forms.FileField(
        required=False,
        label="Upload Practice Task (JSON)",
        help_text="Upload a JSON file with the practice task (text, gold_solution, hints)."
    )

    class Meta:
        model = Project
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        documents_file = cleaned_data.get('documents_file')
        
        # We need to know if the project ALREADY has documents in the database
        has_existing_docs = False
        if self.instance.pk:
            has_existing_docs = self.instance.documents.filter(is_gold_unit=False).exists()

        # If the user tries to set the project to LIVE
        if cleaned_data.get('status') == 'LIVE':
            # It's valid ONLY if:
            # 1. It already has documents in the DB
            # 2. OR it's being provided a new document file right now
            if not has_existing_docs and not documents_file:
                self.add_error('status', "❌ Cannot Set to LIVE: No dataset found. Please upload a .jsonl file in 'Task Configuration' before setting the project status to Live.")
        
        return cleaned_data

class ProjectLogInline(TabularInline):
    model = ProjectLogEntry
    extra = 0
    readonly_fields = ('timestamp', 'action', 'details')
    can_delete = False
    tab = True

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Columns visible in the project list view
    list_display = ('name', 'status_badge', 'documents_link', 'gold_units_link', 'enrollments_link', 'annotations_link', 'link_prolific','export_list_button')
    
    actions = ['run_mace_analysis']

    @admin.action(description="Run MACE Reliability Analysis on selected projects")
    def run_mace_analysis(self, request, queryset):
        for project in queryset:
            try:
                result = run_mace_for_project(project.id)
                if result.get("status") == "success":
                    self.message_user(request, f"{project.name}: {result['message']}", messages.SUCCESS)
                else:
                    self.message_user(request, f"{project.name}: {result.get('message', 'Error')}", messages.WARNING)
            except Exception as e:
                self.message_user(request, f"Error running MACE on {project.name}: {str(e)}", messages.ERROR)

    form = ProjectAdminForm
    readonly_fields = (
        'status_badge',
        'formatted_task_type_config', 
        'formatted_screening_config',
        'formatted_codebook_content',
        'formatted_instructions_content',
        'formatted_practice_task_config',
    )
    
    tabs = [
        ("details", "Project Details"),
        ("config", "Task Configuration"),
        ("training", "Training & Instructions"),
        ("quality", "Quality / Monitoring"),
        ("distribution", "Distribution & Launch"),
        ("log", "Activity Log"),
    ]

    inlines = [ProjectLogInline]

    
    fieldsets = (
        ("Project Details", {
            "fields": (("name", "slug"), "status", "description", "informed_consent_config",),
            "classes": ("tab", "details"),
        }),

        ("Task Configuration", {
            "classes": ("tab", "config"),
            "fields": (
                "formatted_task_type_config",
                "upload_task_config",
                "documents_file",
                ("dataset_text_key", "dataset_id_key"),
            ),
            "description": """
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 15px; border-left: 4px solid #3B82F6; color: #ddd; border-radius: 4px;">
                        <b style="color: #60a5fa; font-size: 1.1em;">⚙️ Task Design</b><br>
                        Configure the labeling interface (labels, questions, layout).
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 15px; border-left: 4px solid #10B981; color: #ddd; border-radius: 4px;">
                        <b style="color: #34d399; font-size: 1.1em;">📊 Data Import</b><br>
                        Upload your <b>.jsonl</b> dataset. Each line must be a JSON object with at least a text field.
                    </div>
                </div>
            """
        }),

        ("Participant Training", {
            "classes": ("tab", "training"),
            "fields": (
                "enable_screening",
                "formatted_screening_config",
                "upload_screening_config",
                "enable_codebook",
                "formatted_codebook_content",
                "upload_codebook_content",
            ),
            "description": """
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #10B981; color: #ddd;">
                        <b>📋 Screening:</b><br>Initial questionnaire for demographics and metadata.
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #A78BFA; color: #ddd;">
                        <b>📖 Codebook:</b><br>Theoretical/practical background instructions (Markdown).
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #F59E0B; color: #ddd;">
                        <b>📝 Instructions:</b><br>Task instructions + optional guided practice task.
                    </div>
                </div>
            """
        }),

        ("Instructions & Practice", {
            "classes": ("tab", "training"),
            "fields": (
                "enable_instructions",
                "formatted_instructions_content",
                "upload_instructions_content",
                "enable_practice_task",
                "formatted_practice_task_config",
                "upload_practice_task_config",
                "practice_task_required",
            ),
            "description": """
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #F59E0B; color: #ddd;">
                        <b>📝 Instructions:</b><br>Markdown content shown to annotators before the task.
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #EC4899; color: #ddd;">
                        <b>🎯 Practice Task:</b><br>Optional guided practice with correct solution and hints.
                    </div>
                </div>
            """
        }),

        ("Quality / Monitoring", {
            "classes": ("tab", "quality"),
            "fields": (
                "enable_gold_units",
                "gold_injection_frequency",
                ("min_accuracy_required", "min_gold_before_eval"),
                "gold_units_file",
            ),
            "description": """
                <div style="display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px;">
                    <div style="background: #1e293b; padding: 15px; border-left: 4px solid #8b5cf6; color: #e2e8f0; border-radius: 4px;">
                        <b style="color: #a78bfa; font-size: 1.1em;">🤖 MACE (Multi-Annotator Competence Estimation)</b><br>
                        Use MACE to estimate annotator reliability and infer the most likely "true" labels even without gold units. 
                        <i>Run this analysis from the project list 'Actions' menu once you have gathered annotations.</i>
                    </div>

                    <div style="background: #1e293b; padding: 15px; border-left: 4px solid #f59e0b; color: #e2e8f0; border-radius: 4px;">
                        <b style="color: #fbbf24; font-size: 1.1em;">🛡️ Gold Units (Ground Truth)</b><br>
                        Manually verified units used to "test" annotators in real-time. 
                        Configure the strategy above and upload the Gold dataset below.
                    </div>
                </div>
            """
        }),

        ("Distribution & Launch", {
            "classes": ("tab", "distribution"),
            "fields": (
                "distribution_strategy",
                ("min_annotations_per_doc", "max_annotations_per_doc"),
                ("block_size", "annotators_per_block"),
                "prioritize_unannotated"
            ),
            "description": "Configure how documents are served to workers."
        }),
    )

    class Media:
        css = {
            'all': ('css/admin_project.css',)
        }
        js = ('js/admin_project.js',)

    def _colorize_json(self, json_str):
        """Apply simple syntax highlighting to a JSON string for HTML display."""
        # Escape HTML first
        from django.utils.html import escape
        escaped = escape(json_str)
        # Highlight keys ("key":)
        escaped = re.sub(
            r'&quot;([^&]+?)&quot;(?=\s*:)',
            r'<span class="json-key">&quot;\1&quot;</span>',
            escaped
        )
        # Highlight string values (: "value")
        escaped = re.sub(
            r':\s*&quot;([^&]*?)&quot;',
            r': <span class="json-string">&quot;\1&quot;</span>',
            escaped
        )
        # Highlight numbers
        escaped = re.sub(
            r':\s*(\d+\.?\d*)',
            r': <span class="json-number">\1</span>',
            escaped
        )
        # Highlight booleans
        escaped = re.sub(
            r'\b(true|false|null)\b',
            r'<span class="json-bool">\1</span>',
            escaped
        )
        return escaped

    def _render_config_block(self, config_data, title, icon):
        """Render a JSON config as a styled HTML block."""
        if not config_data:
            return format_html(
                '<div class="config-empty">'
                '<span class="empty-icon">{}</span>'
                '<span>No {} configured yet. Upload a JSON file above.</span>'
                '</div>',
                icon, title.lower()
            )

        # Ensure important keys are on top if it's a dictionary
        if isinstance(config_data, dict):
            priority_keys = ["task_type", "min_accuracy_required", "gold_injection_frequency", "continuous_exclusion"]
            ordered_data = {k: config_data[k] for k in priority_keys if k in config_data}
            for k, v in config_data.items():
                if k not in ordered_data:
                    ordered_data[k] = v
            config_data = ordered_data

        json_str = json.dumps(config_data, indent=4)
        colorized = self._colorize_json(json_str)

        return format_html(
            '<div class="json-config-display break-words max-w-none py-3 text-sm bg-base-50 border border-base-200 font-medium px-4 rounded-default shadow-xs dark:border-base-700 dark:bg-base-800">'
            '  <div class="config-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.05); color: #64748b;">'
            '    <span class="config-icon">{icon}</span> <strong>{title}</strong>'
            '  </div>'
            '  <pre style="margin: 0; background: transparent; border: none; padding: 0; font-family: \'JetBrains Mono\', monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: inherit;">{code}</pre>'
            '</div>',
            icon=icon,
            title=title,
            code=mark_safe(colorized)
        )

    @admin.display(description="Task Config")
    def formatted_task_type_config(self, obj):
        return self._render_config_block(obj.task_type_config, 'Task Configuration', '⚙️')

    @admin.display(description="Screening Config")
    def formatted_screening_config(self, obj):
        return self._render_config_block(obj.screening_config, 'Screening Configuration', '📋')

    def _render_markdown_block(self, md_text, title, icon):
        """Convert Markdown text to styled HTML for admin display."""
        from django.utils.html import escape
        
        if not md_text or not md_text.strip():
            return format_html(
                '<div class="config-empty">'
                '<span class="empty-icon">{}</span>'
                '<span>No {} configured yet. Upload a Markdown file above.</span>'
                '</div>',
                icon, title.lower()
            )

        text = escape(md_text)

        # Headers
        text = re.sub(r'^### (.+)$', r'<h4 style="font-size:14px;font-weight:600;color:#64748b;margin:16px 0 6px;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h3 style="font-size:16px;font-weight:600;color:#306ee8;margin:20px 0 8px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h2 style="font-size:18px;font-weight:700;color:inherit;margin:24px 0 10px;padding-bottom:6px;border-bottom:1px solid rgba(128,128,128,0.2);">\1</h2>', text, flags=re.MULTILINE)

        # Bold + italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic with underscores (_text_) and asterisks (*text*)
        text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Inline code
        text = re.sub(r'`(.+?)`', r'<code style="background:rgba(128,128,128,0.15);padding:1px 5px;border-radius:3px;font-size:0.9em;">\1</code>', text)

        # Blockquotes
        text = re.sub(
            r'^&gt; (.+)$',
            r'<div style="border-left:3px solid #306ee8;padding:6px 12px;margin:8px 0;background:rgba(48,110,232,0.06);border-radius:0 6px 6px 0;font-size:0.92em;">\1</div>',
            text, flags=re.MULTILINE
        )

        # Horizontal rules
        text = re.sub(r'^---$', r'<hr style="border:none;border-top:1px solid rgba(128,128,128,0.2);margin:20px 0;">', text, flags=re.MULTILINE)

        # Unordered list items (handle nested with 2+ spaces)
        text = re.sub(
            r'^  - (.+)$',
            r'<div style="padding-left:28px;margin:3px 0;"><span style="color:#306ee8;margin-right:6px;">◦</span>\1</div>',
            text, flags=re.MULTILINE
        )
        text = re.sub(
            r'^- (.+)$',
            r'<div style="padding-left:8px;margin:4px 0;"><span style="color:#306ee8;margin-right:6px;">•</span>\1</div>',
            text, flags=re.MULTILINE
        )

        # Paragraphs — wrap remaining non-tag lines
        lines = text.split('\n')
        processed = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('<'):
                processed.append(f'<p style="margin:6px 0;line-height:1.7;">{stripped}</p>')
            else:
                processed.append(line)
        text = '\n'.join(processed)

        # Remove empty paragraphs
        text = re.sub(r'<p[^>]*>\s*</p>', '', text)

        return format_html(
            '<div class="json-config-display break-words max-w-none py-3 text-sm bg-base-50 border border-base-200 font-medium px-4 rounded-default shadow-xs dark:border-base-700 dark:bg-base-800">'
            '  <div class="config-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.05); color: #64748b;">'
            '    <span class="config-icon">{icon}</span> <strong>{title}</strong>'
            '  </div>'
            '  <div style="font-family: \'Outfit\', \'Inter\', sans-serif; font-size: 13px; line-height: 1.7; color: inherit;">{content}</div>'
            '</div>',
            icon=icon,
            title=title,
            content=mark_safe(text)
        )

    @admin.display(description="Codebook Content")
    def formatted_codebook_content(self, obj):
        return self._render_markdown_block(obj.codebook_content, 'Codebook Materials', '📖')

    @admin.display(description="Instructions Content")
    def formatted_instructions_content(self, obj):
        return self._render_markdown_block(obj.instructions_content, 'Task Instructions', '📝')

    @admin.display(description="Practice Task Config")
    def formatted_practice_task_config(self, obj):
        return self._render_config_block(obj.practice_task_config, 'Practice Task', '🎯')

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        my_urls = [
            path(
                '<path:object_id>/export/', 
                self.admin_site.admin_view(self.download_export_view), 
                name='project_export_jsonl'
            ),
        ]
        return my_urls + urls

    def download_export_view(self, request, object_id):
        project = self.get_object(request, object_id)
        
        response = HttpResponse(content_type='application/x-jsonlines')
        filename = f"{project.name.replace(' ', '_').lower()}_annotations.jsonl"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        annotations = Annotation.objects.filter(
            document__project=project,
            document__is_gold_unit=False  # Exclude gold units
        ).select_related('document', 'annotator')

        for ann in annotations:
            raw_result = ann.result
            formatted_markers = []
            raw_spans = raw_result.get('spans', [])
            
            if isinstance(raw_spans, list):
                for span in raw_spans:
                    formatted_markers.append({
                        "startIndex": span.get('start'),
                        "endIndex": span.get('end'),
                        "type": span.get('label'),
                        "text": span.get('text')
                    })

            output_obj = {
                "_id": ann.document.external_id,
                "conspiracy": raw_result.get('classification'),
                "markers": formatted_markers,
                "subreddit": ann.document.metadata.get('subreddit', 'unknown'),
                "annotator": ann.annotator.prolific_pid
            }
            response.write(json.dumps(output_obj) + '\n')

        return response


    @admin.display(description="Export")
    def export_list_button(self, obj):
        url = reverse('admin:project_export_jsonl', args=[obj.pk])
        return format_html(
            '''
            <a href="{}" 
               class="bg-primary-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-primary-700 transition inline-block whitespace-nowrap text-center"
               title="Download .jsonl">
               ⬇ JSONL
            </a>
            ''',
            url
        )


    @admin.display(description="Status", ordering='status')
    def status_badge(self, obj):
        colors = {
            'DRAFT': ('#4b5563', '#f3f4f6'), # Gray
            'LIVE': ('#065f46', '#6ee7b7'),  # Green
            'PAUSED': ('#92400e', '#fde68a'), # Amber/Yellow
            'COMPLETED': ('#1e40af', '#bfdbfe'), # Blue
        }
        bg, fg = colors.get(obj.status, ('#7f1d1d', '#fca5a5'))
        
        return mark_safe(
            f'<span style="display:inline-block;padding:4px 12px;border-radius:20px;'
            f'font-size:11px;font-weight:700;letter-spacing:0.5px;white-space:nowrap;'
            f'background:{bg};color:{fg};">● {obj.status}</span>'
        )

    @admin.display(description="Documents")
    def documents_link(self, obj):
        count = obj.documents.filter(is_gold_unit=False).count()
        url = (
            reverse("admin:annotation_documentproxy_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}", "o": "1"})
        )
        return format_html(
            '''
            <a href="{}" 
               class="bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold hover:bg-blue-700 transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Real Documents">
               -> ({}) Manage Docs
            </a>
            ''',
            url, count
        )

    @admin.display(description="Gold Units")
    def gold_units_link(self, obj):
        count = obj.documents.filter(is_gold_unit=True).count()
        url = (
            reverse("admin:annotation_goldunitproxy_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}", "o": "1"})
        )
        return format_html(
            '''
            <a href="{}" 
               class="bg-amber-500 text-white px-3 py-1 rounded text-xs font-bold hover:bg-amber-600 transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Gold Units">
               -> ({}) Manage Gold
            </a>
            ''',
            url, count
        )

    @admin.display(description="Annotations", ordering='-created_at')
    def annotations_link(self, obj):
        count = Annotation.objects.filter(document__project=obj).count()
        url = (
            reverse("admin:annotation_annotation_changelist")
            + "?"
            + urlencode({
                "document__project__id": f"{obj.id}", 
                "o": "1",
                "category": "regular"
            })
        )
        
        bg_class = "bg-green-600 hover:bg-green-700" if count > 0 else "bg-gray-400 hover:bg-gray-500"
        
        return format_html(
            '''
            <a href="{}" 
               class="{} text-white px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Annotations">
               -> ({}) Manage Annotations
            </a>
            ''',
            url, bg_class, count
        )

    @admin.display(description="Workers")
    def enrollments_link(self, obj):
        count = obj.enrollments.count()
        url = (
            reverse("admin:annotation_projectenrollment_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}"})
        )
        return format_html(
            '''
            <a href="{}" 
               style="background: #fbbf24; color: #1f2937;"
               class="px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Workers">
               -> ({}) Manage Workers
            </a>
            ''',
            url, count
        )
    
    @admin.display(description="Link (Prolific)")
    def link_prolific(self, obj):
        # Format: http://localhost:5173/nome-studio?PROLIFIC_PID=
        display_url = f"http://localhost:5173/{obj.slug}?PROLIFIC_PID="
        test_url = f"http://localhost:5173/{obj.slug}?PROLIFIC_PID=TEST_USER_001"
        return format_html(
            '''
            <div style="display:flex; align-items:center; gap:8px; min-width:250px;">
                <code style="
                    background:#1e1e1e; color:#60a5fa;
                    padding:4px 8px; border-radius:4px;
                    font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
                    border:1px solid #333; flex:1;
                ">{}</code>
                <a href="{}" target="_blank"
                   style="flex-shrink:0; background:#2563eb; color:white; padding:3px 8px;
                          border-radius:4px; font-size:11px; text-decoration:none; font-weight:bold;"
                   title="Open with TEST_USER_001">
                   ↗ Test
                </a>
            </div>
            ''',
            display_url,
            test_url,
        )


    def save_model(self, request, obj, form, change):
        is_new = not obj.pk
        old_status = None
        if not is_new:
            old_status = Project.objects.get(pk=obj.pk).status

        super(ProjectAdmin, self).save_model(request, obj, form, change)

        # --- Logging ---
        if is_new:
            ProjectLogEntry.objects.create(
                project=obj,
                action="Project Created",
                details=f"Project '{obj.name}' initialized as Draft."
            )
        elif old_status != obj.status:
            ProjectLogEntry.objects.create(
                project=obj,
                action="Status Changed",
                details=f"Project changed from {old_status} to {obj.status}."
            )

        # --- Process uploaded Task Config JSON ---
        task_config_file = form.cleaned_data.get('upload_task_config')
        if task_config_file:
            try:
                obj.task_type_config = parse_json_upload(task_config_file)
                obj.save(update_fields=['task_type_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Config Updated",
                    details="Task Configuration (labels/questions) uploaded via JSON file."
                )
                messages.success(request, "Task Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Task Config Error: {str(e)}")

        # --- Process uploaded Screening Config JSON ---
        screening_config_file = form.cleaned_data.get('upload_screening_config')
        if screening_config_file:
            try:
                parsed = parse_json_upload(screening_config_file)
                if not isinstance(parsed, list):
                    raise ValueError("Screening config must be a JSON array of questions.")
                obj.screening_config = parsed
                obj.save(update_fields=['screening_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Screening Updated",
                    details=f"Screening questionnaire updated ({len(parsed)} questions)."
                )
                messages.success(request, f"Screening Configuration updated! {len(parsed)} question(s) loaded.")
            except Exception as e:
                messages.error(request, f"Screening Config Error: {str(e)}")

        # --- Process uploaded Codebook Markdown ---
        codebook_file = form.cleaned_data.get('upload_codebook_content')
        if codebook_file:
            try:
                content = codebook_file.read().decode('utf-8')
                obj.codebook_content = content
                obj.save(update_fields=['codebook_content'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Codebook Updated",
                    details="Theoretical background (Codebook) updated via Markdown file."
                )
                messages.success(request, "Codebook content updated from file!")
            except Exception as e:
                messages.error(request, f"Codebook Upload Error: {str(e)}")

        # --- Process uploaded Instructions Markdown ---
        instructions_file = form.cleaned_data.get('upload_instructions_content')
        if instructions_file:
            try:
                content = instructions_file.read().decode('utf-8')
                obj.instructions_content = content
                obj.save(update_fields=['instructions_content'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Instructions Updated",
                    details="Task instructions updated via Markdown file."
                )
                messages.success(request, "Instructions content updated from file!")
            except Exception as e:
                messages.error(request, f"Instructions Upload Error: {str(e)}")

        # --- Process uploaded Practice Task JSON ---
        practice_file = form.cleaned_data.get('upload_practice_task_config')
        if practice_file:
            try:
                obj.practice_task_config = parse_json_upload(practice_file)
                obj.save(update_fields=['practice_task_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Practice Task Updated",
                    details="Guided practice task configuration updated via JSON file."
                )
                messages.success(request, "Practice Task configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Practice Task Config Error: {str(e)}")

        # --- Process Documents File ---
        if 'documents_file' in form.changed_data and obj.documents_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.documents_file)
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Dataset Imported",
                    details=f"Successfully imported {count} regular documents."
                )
                messages.success(request, f"Regular documents import successful! Created {count} documents.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Documents import error: {str(e)}")

        # --- Process Gold Units File ---
        if 'gold_units_file' in form.changed_data and obj.gold_units_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.gold_units_file)
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Gold Units Imported",
                    details=f"Successfully imported {count} gold units."
                )
                messages.success(request, f"Gold units import successful! Created {count} units.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Gold units import error: {str(e)}")
```

---

### FILE: backend\annotation\admin\utils.py
```

class HighlightMedia:
    """
    Utility class to provide Highlight.js assets to the admin.
    """
    css = {
        'all': ('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/stackoverflow-light.min.css',)
    }
    js = (
        'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
        'js/admin_highlight_init.js',
    )
```

---

### FILE: backend\annotation\admin\__init__.py
```
from .project import ProjectAdmin
from .document import DocumentProxyAdmin, GoldUnitProxyAdmin
from .annotator import AnnotatorAdmin
from .annotation import AnnotationAdmin
from .enrollment import ProjectEnrollmentAdmin
from django.contrib.auth.models import Group
from django.contrib import admin


admin.site.unregister(Group)
```

---

### FILE: backend\annotation\management\__init__.py
```

```

---

### FILE: backend\annotation\management\commands\seed_demo.py
```
"""
Django Management Command: seed_demo
-------------------------------------
Creates two demo projects:
  1. PROJECT_DRAFT  - ready to be configured, status=DRAFT
  2. PROJECT_LIVE   - active, with documents, annotators and annotations

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # deletes all existing demo data first
"""

import random
import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from annotation.models import (
    Project, Document, Annotator, Annotation,
    ProjectEnrollment, ProjectLogEntry
)

# ---------------------------------------------------------------------------
# Sample texts (short conspiracy-style sentences for demo)
# ---------------------------------------------------------------------------
SAMPLE_TEXTS = [
    "Scientists claim that 5G towers are designed to suppress the immune system of the population.",
    "A leaked document reveals that the moon landing was staged in a Hollywood studio.",
    "The government adds fluoride to water supplies to make people docile and easier to control.",
    "Big Pharma is hiding the cure for cancer to keep profits from chemotherapy treatments high.",
    "Chemtrails left by aircraft are actually chemical agents used to manipulate the weather.",
    "The Illuminati controls world governments through a network of secret societies.",
    "Microchips hidden in vaccines are used to track and monitor every citizen.",
    "The media blackout on this story proves that someone powerful wants it suppressed.",
    "A whistleblower revealed that elections are rigged through voting machine software.",
    "Ancient pyramids were built by an advanced alien civilization, not humans.",
    "Banks create money out of thin air and charge interest to enslave entire nations.",
    "The deep state orchestrates terror attacks to justify expanding surveillance powers.",
    "A secret cabal of elites meets annually to decide the fate of world economies.",
    "Satellites in orbit are actually weapons platforms disguised as communication relays.",
    "The real flat earth is hidden behind an Antarctic ice wall guarded by the military.",
    "COVID-19 was engineered in a laboratory as a population control mechanism.",
    "The federal reserve is a private bank that profits from wars it secretly funds.",
    "Reptilian shapeshifters have infiltrated the highest levels of government worldwide.",
    "Mind control signals are broadcast through television sets during prime time hours.",
    "The cure for Alzheimer's was discovered decades ago but suppressed by pharmaceutical companies.",
]

GOLD_TEXTS = [
    {
        "text": "The government is putting chips in the water to control us and nobody seems to care.",
        "gold_solution": {
            "classification": "Yes",
            "spans": [
                {"start": 0, "end": 14, "label": "Actor", "text": "The government"},
                {"start": 18, "end": 47, "label": "Action", "text": "putting chips in the water to"},
                {"start": 48, "end": 58, "label": "Victim", "text": "control us"},
            ]
        }
    },
    {
        "text": "This article is simply reporting on record rainfall levels observed this month.",
        "gold_solution": {
            "classification": "No",
            "spans": []
        }
    },
]

# Classification labels for fake annotations
LABELS = ["Yes", "No", "Can't tell"]

TASK_CONFIG = {
    "task_type": "hybrid",
    "question": "Does this text describe or promote a conspiracy theory?",
    "instruction": "Read the text carefully and: (1) highlight the key elements using the span labels, (2) select the overall classification.",
    "span_labels": [
        {"name": "Actor", "color": "#ef4444", "hover_hint": "Who is allegedly responsible?"},
        {"name": "Action", "color": "#3b82f6", "hover_hint": "What are they doing?"},
        {"name": "Victim", "color": "#8b5cf6", "hover_hint": "Who is being harmed?"},
        {"name": "Evidence", "color": "#f59e0b", "hover_hint": "What proof is cited?"},
    ],
    "class_labels": [
        {"label": "Conspiracy", "value": "Yes"},
        {"label": "Not a Conspiracy", "value": "No"},
        {"label": "Ambiguous", "value": "Can't tell"},
    ]
}

# Gold Default Values for Demo
DEMO_GOLD_SETTINGS = {
    "min_accuracy_required": 0.6,
    "gold_injection_frequency": 5,
    "min_gold_before_eval": 2
}


class Command(BaseCommand):
    help = "Seeds the database with demo projects for development/presentation."

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing demo projects before creating new ones.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        self.stdout.write(self.style.WARNING("\n🌱 Seeding demo data...\n"))
        self._create_draft_project()
        self._create_live_project()
        self.stdout.write(self.style.SUCCESS("\n✅ Done! Demo data created successfully.\n"))

    # -----------------------------------------------------------------------
    def _flush(self):
        self.stdout.write("🗑️  Flushing existing demo projects...")
        Project.objects.filter(slug__startswith="demo-").delete()
        Annotator.objects.filter(prolific_pid__startswith="DEMO_").delete()
        self.stdout.write(self.style.SUCCESS("   Flush complete.\n"))

    # -----------------------------------------------------------------------
    def _create_draft_project(self):
        self.stdout.write("📋 Creating DRAFT project...")

        project, created = Project.objects.get_or_create(
            slug="demo-draft-study",
            defaults={
                "name": "[DEMO] Climate Narratives Study",
                "description": (
                    "A study examining how conspiracy narratives appear in online discussions "
                    "about climate change. This project is configured but not yet launched."
                ),
                "status": "DRAFT",
                "task_type_config": TASK_CONFIG,
                "min_accuracy_required": DEMO_GOLD_SETTINGS["min_accuracy_required"],
                "gold_injection_frequency": DEMO_GOLD_SETTINGS["gold_injection_frequency"],
                "min_gold_before_eval": DEMO_GOLD_SETTINGS["min_gold_before_eval"],
                "enable_gold_units": True,
                "enable_screening": True,
                "enable_codebook": True,
                "enable_instructions": True,
                "enable_practice_task": True,
                "distribution_strategy": "STANDARD",
                "min_annotations_per_doc": 3,
                "max_annotations_per_doc": 5,
                "prioritize_unannotated": True,
                "dataset_text_key": "text",
                "dataset_id_key": "_id",
                "documents_file": "",
            }
        )

        if not created:
            self.stdout.write(self.style.WARNING("   ⚠️  Draft project already exists, skipping."))
            return

        # Add a few draft documents (not yet live)
        for i, text in enumerate(SAMPLE_TEXTS[:5]):
            Document.objects.create(
                project=project,
                text=text,
                external_id=f"DRAFT_DOC_{i+1:03d}",
                metadata={"source": "demo", "batch": "draft"},
                is_gold_unit=False,
                min_annotations_required=3,
            )

        # Log
        ProjectLogEntry.objects.create(
            project=project,
            action="Project Created",
            details="[DEMO] Draft project initialized with 5 sample documents."
        )

        self.stdout.write(self.style.SUCCESS(
            f"   ✅ '{project.name}' created (DRAFT, 5 documents, not launched)"
        ))

    # -----------------------------------------------------------------------
    def _create_live_project(self):
        self.stdout.write("🟢 Creating LIVE project with annotations...")

        project, created = Project.objects.get_or_create(
            slug="demo-live-conspiracy",
            defaults={
                "name": "[DEMO] Conspiracy Theory Detection",
                "description": (
                    "Active annotation campaign for detecting conspiracy theories in social media posts. "
                    "Annotators highlight key spans and classify each post."
                ),
                "status": "LIVE",
                "launched_at": timezone.now(),
                "task_type_config": TASK_CONFIG,
                "min_accuracy_required": DEMO_GOLD_SETTINGS["min_accuracy_required"],
                "gold_injection_frequency": DEMO_GOLD_SETTINGS["gold_injection_frequency"],
                "min_gold_before_eval": DEMO_GOLD_SETTINGS["min_gold_before_eval"],
                "enable_gold_units": True,
                "enable_screening": True,
                "enable_codebook": True,
                "enable_instructions": True,
                "enable_practice_task": True,
                "distribution_strategy": "STANDARD",
                "min_annotations_per_doc": 3,
                "max_annotations_per_doc": 5,
                "prioritize_unannotated": True,
                "dataset_text_key": "text",
                "dataset_id_key": "_id",
                "documents_file": "",
            }
        )

        if not created:
            self.stdout.write(self.style.WARNING("   ⚠️  Live project already exists, skipping."))
            return

        # --- Create regular documents ---
        docs = []
        for i, text in enumerate(SAMPLE_TEXTS):
            doc = Document.objects.create(
                project=project,
                text=text,
                external_id=f"LIVE_DOC_{i+1:03d}",
                metadata={"source": "reddit", "subreddit": random.choice(["conspiracy", "worldnews", "science"])},
                is_gold_unit=False,
                min_annotations_required=3,
            )
            docs.append(doc)

        # --- Create gold units ---
        gold_docs = []
        for i, g in enumerate(GOLD_TEXTS):
            gdoc = Document.objects.create(
                project=project,
                text=g["text"],
                external_id=f"LIVE_GOLD_{i+1:03d}",
                metadata={"source": "gold"},
                is_gold_unit=True,
                gold_solution=g["gold_solution"],
                min_annotations_required=3,
            )
            gold_docs.append(gdoc)

        # --- Create fake annotators ---
        annotator_specs = [
            {"pid": "DEMO_EXPERT_001",  "accuracy": 0.95, "n_docs": 18, "status": "ACTIVE"},
            {"pid": "DEMO_EXPERT_002",  "accuracy": 0.90, "n_docs": 15, "status": "ACTIVE"},
            {"pid": "DEMO_AVERAGE_001", "accuracy": 0.70, "n_docs": 12, "status": "ACTIVE"},
            {"pid": "DEMO_AVERAGE_002", "accuracy": 0.65, "n_docs": 10, "status": "ACTIVE"},
            {"pid": "DEMO_SPAMMER_001", "accuracy": 0.30, "n_docs":  8, "status": "EXCLUDED"},
            {"pid": "DEMO_NEW_001",     "accuracy": 0.80, "n_docs":  2, "status": "ACTIVE"},
        ]

        annotators = []
        for spec in annotator_specs:
            pid = spec["pid"]
            accuracy = spec["accuracy"]
            n_docs = spec["n_docs"]
            status = spec["status"]

            ann, _ = Annotator.objects.get_or_create(
                prolific_pid=pid,
                defaults={
                    "consent_accepted": True,
                    "screening_completed": True,
                    "onboarding_completed": True,
                    "metadata": {"source": "demo", "reliability": accuracy},
                }
            )
            annotators.append((ann, spec))

            # Enrollment
            gold_tasks = 1 if n_docs >= 5 else 0  # type: ignore[unsupported-operator]
            gold_acc = accuracy if n_docs >= 5 else None  # type: ignore[unsupported-operator]

            ProjectEnrollment.objects.get_or_create(
                project=project,
                annotator=ann,
                defaults={
                    "status": status,
                    "gold_tasks_completed": gold_tasks,
                    "gold_accuracy": gold_acc,
                    "codebook_completed": True,
                }
            )

        # --- Create fake annotations ---
        annotation_count = 0
        for ann, spec in annotators:
            # Pick a random subset of docs this annotator has already annotated
            subset = random.sample(docs, min(spec["n_docs"], len(docs)))
            for doc in subset:
                # Skip if already annotated (unique_together constraint)
                if Annotation.objects.filter(document=doc, annotator=ann).exists():
                    continue

                # Expert annotators give correct-ish labels, spammers give random ones
                if spec["accuracy"] > 0.6:
                    label = random.choices(LABELS, weights=[0.6, 0.3, 0.1])[0]
                else:
                    label = random.choice(LABELS)

                result = {"classification": label, "spans": []}

                Annotation.objects.create(
                    document=doc,
                    annotator=ann,
                    result=result,
                    milliseconds_to_complete=random.randint(8000, 45000),
                )
                doc.current_annotations_count += 1
                doc.save(update_fields=["current_annotations_count"])
                annotation_count += 1

        # --- Log lifecycle events ---
        ProjectLogEntry.objects.create(
            project=project,
            action="Project Created",
            details="[DEMO] Live project initialized."
        )
        ProjectLogEntry.objects.create(
            project=project,
            action="Dataset Imported",
            details=f"Successfully imported {len(docs)} regular documents and {len(gold_docs)} gold units."
        )
        ProjectLogEntry.objects.create(
            project=project,
            action="Status Changed",
            details="Project changed from DRAFT to LIVE."
        )

        total_annotators = len(annotators)
        self.stdout.write(self.style.SUCCESS(
            f"   ✅ '{project.name}' created:\n"
            f"      - Status: LIVE\n"
            f"      - Documents: {len(docs)} regular + {len(gold_docs)} gold units\n"
            f"      - Annotators: {total_annotators} ({sum(1 for _, s in annotators if s['status'] == 'ACTIVE')} active, "
            f"{sum(1 for _, s in annotators if s['status'] == 'EXCLUDED')} excluded)\n"
            f"      - Annotations created: {annotation_count}\n"
            f"      - Admin link: http://localhost:8000/admin/annotation/project/{project.id}/change/"
        ))

```

---

### FILE: backend\annotation\management\commands\__init__.py
```

```

---

### FILE: backend\annotation\migrations\0001_initial.py
```
# Generated by Django 6.0.2 on 2026-03-25 09:02

import annotation.models
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Annotator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prolific_pid', models.CharField(db_index=True, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('consent_accepted', models.BooleanField(default=False)),
                ('screening_completed', models.BooleanField(default=False)),
                ('onboarding_completed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('external_id', models.CharField(blank=True, max_length=100, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('is_gold_unit', models.BooleanField(default=False)),
                ('gold_solution', models.JSONField(blank=True, default=dict, null=True)),
                ('mace_gold_label', models.CharField(blank=True, max_length=50, null=True)),
                ('mace_confidence', models.FloatField(blank=True, help_text='Certainty of the MACE prediction (entropy)', null=True)),
                ('min_annotations_required', models.IntegerField(default=3)),
                ('current_annotations_count', models.IntegerField(db_index=True, default=0)),
                ('block_id', models.IntegerField(blank=True, db_index=True, help_text='Used to group documents into blocks for the SAME_ANNOTATORS strategy', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Project name', max_length=200)),
                ('slug', models.SlugField(blank=True, help_text="Unique Identifier for the URL (e.g., 'nome-studio')", max_length=250, unique=True)),
                ('description', models.TextField(blank=True, help_text='Project description')),
                ('is_active', models.BooleanField(default=False, help_text='If False, the project will not accept new annotations (Pause mode).')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('LIVE', 'Live'), ('PAUSED', 'Paused'), ('COMPLETED', 'Completed')], default='DRAFT', help_text='Current lifecycle state of the project.', max_length=20)),
                ('launched_at', models.DateTimeField(blank=True, help_text='Timestamp when the project was first set to LIVE.', null=True)),
                ('informed_consent_config', models.TextField(default=annotation.models.get_default_configuration_for_informed_consent, help_text='Informed Consent Configuration: accept a string can be showed to the annotator before starting the task')),
                ('task_type_config', models.JSONField(default=annotation.models.get_default_configuration_for_task_type, help_text='Task Configuration (labels, colors, questions)')),
                ('gold_config', models.JSONField(blank=True, default=annotation.models.get_default_gold_config, help_text="Gold Units QC config: { 'min_accuracy_required': float, 'gold_injection_frequency': int, 'continuous_exclusion': bool }")),
                ('enable_screening', models.BooleanField(default=True, help_text='If True, annotators will see the screening questionnaire before the task.')),
                ('screening_config', models.JSONField(blank=True, default=annotation.models.get_default_screening_config, help_text='Screening questionnaire: JSON list of questions shown to annotators before the task. Empty list = skip screening.')),
                ('enable_codebook', models.BooleanField(default=True, help_text='If True, annotators will see the codebook/instructions before the task.')),
                ('codebook_content', models.TextField(blank=True, default=annotation.models.get_default_codebook_content, help_text='Codebook content in Markdown format. Shown to annotators as theoretical/practical background.')),
                ('enable_instructions', models.BooleanField(default=True, help_text='If True, annotators will see task instructions and optional practice task before annotating.')),
                ('instructions_content', models.TextField(blank=True, default=annotation.models.get_default_instructions_content, help_text='Instructions content in Markdown format. Shown to annotators as task instructions before the practice.')),
                ('practice_task_config', models.JSONField(blank=True, default=annotation.models.get_default_practice_task, help_text='Practice task config: { text, gold_solution: {classification, spans[]}, hints[] }. Empty = no practice.')),
                ('practice_task_required', models.BooleanField(default=False, help_text='If True, annotators must pass the practice task correctly before starting. If False, they can skip after attempting.')),
                ('distribution_strategy', models.CharField(choices=[('STANDARD', 'Standard - Randomly assign documents to annotators'), ('FULL_OVERLAP', 'Everyone sees everything (High Redundancy) - All annotators see all documents'), ('SAME_ANNOTATORS', 'Same k annotators view the same document (Low Redundancy) - the annotators are assigned to blocks of documents')], default='STANDARD', help_text='Defines how documents are assigned to annotators.', max_length=20)),
                ('min_annotations_per_doc', models.IntegerField(default=3, help_text='Target: How many people must annotate each document.')),
                ('max_annotations_per_doc', models.IntegerField(default=5, help_text='Hard Cap: Stop serving the document if it reaches this number (prevents waste).')),
                ('block_size', models.IntegerField(default=10, help_text='SAME_ANNOTATORS strategy: Number of documents injected into each block.')),
                ('annotators_per_block', models.IntegerField(default=3, help_text='SAME_ANNOTATORS strategy: Number of distinct annotators assigned to each block.')),
                ('dataset_text_key', models.CharField(default='text', help_text="The JSON key containing the text to be annotated (e.g., 'text', 'body', 'content').", max_length=100)),
                ('dataset_id_key', models.CharField(blank=True, default='_id', help_text='The JSON key for the ID. If empty or not found, it will use the row number.', max_length=100)),
                ('prioritize_unannotated', models.BooleanField(default=True, help_text='If True, the system will try to finish unannotated documents first.')),
                ('documents_file', models.FileField(help_text='Upload a .jsonl file for REAL documents to be annotated.', upload_to='datasets/documents/')),
                ('enable_gold_units', models.BooleanField(default=True, help_text='If True, gold units will be injected for quality control during annotation.')),
                ('gold_units_file', models.FileField(blank=True, help_text='Upload a .jsonl file for GOLD units (Quality Control Injection).', null=True, upload_to='datasets/gold/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Annotation Document',
                'verbose_name_plural': 'Annotation Documents',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('annotation.document',),
        ),
        migrations.CreateModel(
            name='GoldUnitProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Gold Unit',
                'verbose_name_plural': 'Gold Units',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('annotation.document',),
        ),
        migrations.AddField(
            model_name='document',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='annotation.project'),
        ),
        migrations.CreateModel(
            name='ProjectLogEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(help_text="The event type (e.g., 'Project Launched', 'Status Changed', 'Data Imported')", max_length=100)),
                ('details', models.TextField(blank=True, help_text='Optional details or message.')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='annotation.project')),
            ],
            options={
                'verbose_name': 'Project Log Entry',
                'verbose_name_plural': 'Project Log Entries',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('result', models.JSONField()),
                ('milliseconds_to_complete', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('annotator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='annotations', to='annotation.annotator')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='annotation.document')),
            ],
            options={
                'unique_together': {('document', 'annotator')},
            },
        ),
        migrations.CreateModel(
            name='ProjectEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACTIVE', 'Active'), ('EXCLUDED', 'Excluded'), ('COMPLETED', 'Completed')], default='PENDING', help_text='PENDING = pre-task phases incomplete. ACTIVE = annotating. EXCLUDED = low quality. COMPLETED = done.', max_length=20)),
                ('gold_tasks_completed', models.IntegerField(default=0)),
                ('gold_accuracy', models.FloatField(blank=True, null=True)),
                ('gold_strikes', models.IntegerField(default=0, help_text='Consecutive wrong gold answers (for strike-based evaluation).')),
                ('codebook_completed', models.BooleanField(default=False)),
                ('exclude_from_distribution', models.BooleanField(default=False)),
                ('assigned_block_id', models.IntegerField(blank=True, help_text='The document block assigned to this annotator (for SAME_ANNOTATORS).', null=True)),
                ('mace_competence_score', models.FloatField(blank=True, help_text='MACE estimated reliability (0.0 to 1.0)', null=True)),
                ('mace_spam_bias', models.JSONField(blank=True, default=dict, help_text='Estimated bias distribution when guessing')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annotator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='annotation.annotator')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='annotation.project')),
            ],
            options={
                'verbose_name': 'Enrollment & Assignment',
                'verbose_name_plural': 'Enrollments & Assignments',
                'unique_together': {('project', 'annotator')},
            },
        ),
    ]

```

---

### FILE: backend\annotation\migrations\0002_remove_project_is_active.py
```
# Generated by Django 6.0.2 on 2026-03-25 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotation', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='is_active',
        ),
    ]

```

---

### FILE: backend\annotation\migrations\0003_remove_project_gold_config_and_more.py
```
# Generated by Django 6.0.2 on 2026-03-25 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotation', '0002_remove_project_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='gold_config',
        ),
        migrations.AddField(
            model_name='project',
            name='continuous_exclusion',
            field=models.BooleanField(default=False, help_text='If True, the annotator is excluded as soon as they drop below the threshold.'),
        ),
        migrations.AddField(
            model_name='project',
            name='evaluation_strategy',
            field=models.CharField(choices=[('percentage', 'Percentage Based - use cumulative accuracy'), ('strikes', 'Strike Based - use consecutive wrong answers'), ('hybrid', 'Hybrid - use both percentage and strikes')], default='percentage', help_text='The strategy used to evaluate annotator quality.', max_length=20),
        ),
        migrations.AddField(
            model_name='project',
            name='gold_injection_frequency',
            field=models.IntegerField(default=5, help_text='Frequency of gold task injection (e.g., 1 every 5 tasks).'),
        ),
        migrations.AddField(
            model_name='project',
            name='max_strikes',
            field=models.IntegerField(default=3, help_text="For 'strikes' or 'hybrid' strategy: max consecutive wrong answers."),
        ),
        migrations.AddField(
            model_name='project',
            name='min_accuracy_required',
            field=models.FloatField(default=0.6, help_text='Minimum accuracy required for gold tasks (0.0 to 1.0).'),
        ),
        migrations.AddField(
            model_name='project',
            name='min_gold_before_eval',
            field=models.IntegerField(default=3, help_text='Min gold units completed before starting evaluation.'),
        ),
    ]

```

---

### FILE: backend\annotation\migrations\0004_remove_project_continuous_exclusion_and_more.py
```
# Generated by Django 6.0.2 on 2026-03-25 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotation', '0003_remove_project_gold_config_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='continuous_exclusion',
        ),
        migrations.RemoveField(
            model_name='project',
            name='evaluation_strategy',
        ),
        migrations.RemoveField(
            model_name='project',
            name='max_strikes',
        ),
    ]

```

---

### FILE: backend\annotation\migrations\0005_project_enable_practice_task.py
```
# Generated by Django 6.0.2 on 2026-03-25 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotation', '0004_remove_project_continuous_exclusion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='enable_practice_task',
            field=models.BooleanField(default=True, help_text='If True, annotators will see a practice task before starting the real task.'),
        ),
    ]

```

---

### FILE: backend\annotation\migrations\__init__.py
```

```

---

### FILE: backend\annotation\static\css\admin_project.css
```
/* =============================================================
   Custom Admin Styles for Project Configuration Section
   ============================================================= */

/* --- JSON Config Display (readonly) --- */
.json-config-display {
    background: #1a1a2e;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    overflow: hidden;
    margin-top: 4px;
}

/* Force parent container (Django/Unfold readonly wrapper) to be full width */
div:has(> .json-config-display) {
    min-width: stretch !important;
    max-width: none !important;
    width: 100% !important;
}

.json-config-display .config-header {
    background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #2d2d44;
    font-size: 12px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.json-config-display .config-header .config-icon {
    font-size: 14px;
}

.json-config-display pre {
    margin: 0;
    padding: 16px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.6;
    color: #e2e8f0;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
    background: transparent;
}

.json-config-display pre::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

.json-config-display pre::-webkit-scrollbar-track {
    background: #1a1a2e;
}

.json-config-display pre::-webkit-scrollbar-thumb {
    background: #3b3b5c;
    border-radius: 3px;
}

.json-config-display pre::-webkit-scrollbar-thumb:hover {
    background: #4f4f7a;
}

/* Syntax-like coloring for JSON */
.json-config-display .json-key {
    color: #7dd3fc;
}

.json-config-display .json-string {
    color: #86efac;
}

.json-config-display .json-number {
    color: #fbbf24;
}

.json-config-display .json-bool {
    color: #c084fc;
}

/* --- Empty config placeholder --- */
.config-empty {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 20px;
    background: #1a1a2e;
    border: 1px dashed #2d2d44;
    border-radius: 8px;
    color: #64748b;
    font-size: 13px;
    font-style: italic;
}

.config-empty .empty-icon {
    font-size: 18px;
    opacity: 0.6;
}

/* --- Upload File Widget Enhancement --- */
.file-upload-wrapper {
    position: relative;
    margin-top: 4px;
}

.file-upload-wrapper .upload-zone {
    border: 2px dashed #3b3b5c;
    border-radius: 8px;
    padding: 16px 16px;
    text-align: center;
    transition: all 0.2s ease;
    background: #12121f;
    cursor: pointer;
}

.file-upload-wrapper .upload-zone:hover {
    border-color: #60a5fa;
    background: #161630;
}

.file-upload-wrapper .upload-zone.dragover {
    border-color: #3b82f6;
    background: #1e1e3f;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
}

.file-upload-wrapper .upload-icon {
    font-size: 22px;
    margin-bottom: 4px;
    opacity: 0.7;
}

.file-upload-wrapper .upload-label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 2px;
}

.file-upload-wrapper .upload-hint {
    font-size: 11px;
    color: #64748b;
}

.file-upload-wrapper .upload-hint code {
    background: #2d2d44;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    color: #93c5fd;
}

.file-upload-wrapper input[type="file"] {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
    z-index: 2;
}

.file-upload-wrapper .file-selected {
    display: none;
    margin-top: 8px;
    padding: 8px 12px;
    background: #1e3a5f;
    border: 1px solid #2563eb;
    border-radius: 6px;
    font-size: 12px;
    color: #93c5fd;
    align-items: center;
    gap: 6px;
}

.file-upload-wrapper .file-selected.visible {
    display: flex;
}

/* --- FULL_OVERLAP Warning Banner --- */
.full-overlap-warning {
    display: none;
    background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
    color: #fef3c7;
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 4px solid #f59e0b;
    font-size: 13px;
    line-height: 1.5;
    margin-bottom: 12px;
    animation: fadeIn 0.3s ease;
}

.full-overlap-warning strong {
    color: #fde68a;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-8px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* --- Style Step Indicators in Tabs --- */
/* Target all buttons in the tablist within the unfold admin */
.unfold [role="tablist"] button {
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    font-weight: 600 !important;
    color: #64748b !important;
    border: none !important;
    padding: 10px 20px !important;
    background: transparent !important;
    position: relative;
}

.unfold [role="tablist"] {
    background: #f1f5f9 !important;
    /* Slightly darker background to make active tab pop more */
    padding: 6px;
    border-radius: 12px;
    margin-bottom: 24px;
    display: flex;
    gap: 8px;
    border: 1px solid #e2e8f0;
    width: fit-content;
    /* Make it look more like a navbar */
}

.unfold [role="tablist"] button:hover {
    background: rgba(0, 0, 0, 0.05) !important;
    color: #1e293b !important;
}

.unfold [role="tablist"] button[aria-selected="true"] {
    background: #3b82f6 !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    transform: translateY(-1px);
}

/* Subtle indicator dot below active tab */
.unfold [role="tablist"] button[aria-selected="true"]::after {
    content: "";
    position: absolute;
    bottom: 4px;
    left: 50%;
    transform: translateX(-50%);
    width: 4px;
    height: 4px;
    background: white;
    border-radius: 50%;
}
```

---

### FILE: backend\annotation\static\js\admin_project.js
```
/**
 * admin_project.js
 * Optimized field visibility and drag-and-drop for Project Admin
 */
document.addEventListener("DOMContentLoaded", function () {

    function forceVisibility(fieldName, shouldShow) {
        const field = document.getElementById(`id_${fieldName}`) || 
                      document.querySelector(`input[name="${fieldName}"]`) || 
                      document.querySelector(`select[name="${fieldName}"]`);
        
        const container = document.querySelector(`.field-${fieldName}`) || 
                          (field ? field.closest('.fieldBox') : null) ||
                          (field ? field.closest('.flex-col, .form-row') : null);

        if (!container) return;
        container.style.display = shouldShow ? '' : 'none';
        
        const row = container.parentElement;
        if (row && (row.classList.contains('form-row') || row.classList.contains('flex') || row.classList.contains('grid'))) {
            const hasVisibleContent = Array.from(row.children).some(child => {
                 return child.style.display !== 'none' && 
                        (child.classList.contains('fieldBox') || child.className.includes('field-'));
            });
            row.style.display = hasVisibleContent ? '' : 'none';
        }
    }

    function sync() {
        // A. Distribution Strategy
        const distVal = (document.getElementById('id_distribution_strategy') || {}).value;
        if (distVal) {
            forceVisibility('min_annotations_per_doc', distVal !== 'FULL_OVERLAP');
            forceVisibility('max_annotations_per_doc', distVal !== 'FULL_OVERLAP');
            forceVisibility('prioritize_unannotated', distVal !== 'FULL_OVERLAP');
            forceVisibility('block_size', distVal === 'SAME_ANNOTATORS');
            forceVisibility('annotators_per_block', distVal === 'SAME_ANNOTATORS');
        }
    }

    ['id_distribution_strategy'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', sync);
    });

    // Capture potential late renders (Unfold characteristics)
    sync();
    [50, 200, 500, 1000].forEach(delay => setTimeout(sync, delay));

    // Drag and Drop (Compact)
    document.querySelectorAll('input[type="file"]').forEach(input => {
        if (input.name.includes('upload_')) {
            const p = input.closest('.flex-col, div');
            if (p && !p.querySelector('.dd-zone')) {
                const zone = document.createElement('div');
                zone.className = "dd-zone";
                zone.style.padding = "10px"; zone.style.border = "2px dashed #444"; zone.style.cursor = "pointer";
                zone.style.textAlign = "center"; zone.style.borderRadius = "6px"; zone.style.marginBottom = "5px";
                zone.innerHTML = "📂 Upload File";
                input.style.display = 'none';
                p.prepend(zone);
                zone.onclick = () => input.click();
                input.onchange = () => zone.innerHTML = `✅ ${input.files[0].name}`;
            }
        }
    });
});

```

---

### FILE: backend\backend\asgi.py
```
"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_asgi_application()

```

---

### FILE: backend\backend\settings.py
```
"""
Django settings for backend project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#  ENVIRONMENT VARIABLES CONFIGURATION

SECRET_KEY = os.environ.get('SECRET_KEY')


DEBUG = int(os.environ.get('DEBUG', 0))


ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'annotation': { 
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

UNFOLD = {
    # Titolo nella barra laterale
    "SITE_TITLE": "Annotation Portal",
    
    # Sottotitolo o header
    "SITE_HEADER": "Pannel Admin",
    
    # Link quando clicchi sul logo/titolo (di solito la homepage del sito o la dashboard)
    "SITE_URL": "/",

    # Colori della sidebar (opzionale)
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
        },
    },

    # Sidebar configuration
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Annotation",
                "items": [
                    {
                        "title": "Projects",
                        "link": "/admin/annotation/project/",
                        "icon": "folder",
                    },
                    {
                        "title": "Annotators",
                        "link": "/admin/annotation/annotator/",
                        "icon": "group",
                    },
                ],
            },
            {
                "title": "Auth",
                "items": [
                    {
                        "title": "Users",
                        "link": "/admin/auth/user/",
                        "icon": "person",
                    },
                ],
            },
        ],
    },
}

INSTALLED_APPS = [
    'unfold',
    "unfold.contrib.filters",       
    "unfold.contrib.forms",         
    "unfold.contrib.import_export", 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'import_export',
    'annotation',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

#  CORS & CSRF CONFIGURATION

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 
    'http://localhost:80,http://127.0.0.1:80,http://localhost:5173,http://localhost:8080'
).split(',')

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 
    'http://localhost:8080,http://127.0.0.1:8080'
).split(',')

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# =========================================================
#  DATABASE
# =========================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'), 
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

---

### FILE: backend\backend\urls.py
```
"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import RedirectView

def healthcheck(request):
    return JsonResponse({"message": "OK"})

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/v1/healthcheck', healthcheck),
    path('api/v1/', include('annotation.urls')),
]

```

---

### FILE: backend\backend\wsgi.py
```
"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()

```

---

### FILE: backend\backend\__init__.py
```

```

---

### FILE: backend\config_defaults\codebook_somiglianza_item.md
```
# Codebook — Valutazione della somiglianza tra item

## 1. SINONIMIA / ANTINOMIA

### Sinonimia

**Definizione:** Due item sono sinonimi quando hanno lo stesso o quasi lo stesso significato linguistico.

**Esempi:**

- "Mi sento felice" e "Sono molto contento"
- "Prendo una decisione" e "Faccio una scelta"
- "Sono triste" e "Sono giù di morale"
- "Sto bene con i miei colleghi" e "Mi sento a mio agio con le persone con cui lavoro"

### Antonimia

**Definizione:** Due item che hanno significati linguistici opposti o quasi opposti.

**Esempi:**

- "Sono una persona di successo" e "Sono un fallito"
- "Tendo a dormire bene" e "Spesso ho difficoltà a riposarmi la notte"
- "Sono una persona allegra" e "Sono una persona che tende a deprimersi"
- "Amo profondamente la musica classica" e "Non sopporto la musica classica"

### Codificatore

Due cose possono avere lo stesso (o quasi lo stesso) significato o un significato opposto o quasi. Vedi se ti sembra ci sia questo tipo di relazione.

**[Scelta forzata di una delle tre alternative]**

- Item A è sinonimo di item B
- Item A è il contrario di item B
- Non c'è questo tipo di relazione tra item A e item B

> **Nota:** Molte scale psicometriche si basano su variazioni sintattiche di item che hanno approssimativamente lo stesso significato. Item con significato opposto sono utilizzati per misurare uno stesso costrutto psicologico.

---

## 2. RELAZIONI DI INCLUSIONE

### Sottoinsieme

**Definizione:** Quello che è descritto in un item è (approssimativamente) un sottoinsieme di quello che è descritto in un altro item. Quello che è descritto in un item può naturalmente far parte di altri insiemi oltre a quelli oggetto di valutazione. Due item condividono quindi almeno una stessa "scala di astrazione", una tematica, ma un item è più specifico dall'altro. Gli insiemi vanno intesi in termini sfumati, fuzzy, non precisamente definiti. Insieme/sottoinsieme. Generale/specifico. Livelli di astrazione. Relazioni gerarchiche.

**Esempi:**

- "Mi piace fare jogging nel parco" (specifico, sottoinsieme) e "fare attività fisica" (generale, insieme)
- "Sono una persona emotiva" e "Sono spesso ansioso"
- "Fare degli esercizi di matematica" e "Studiare"
- "Sono depresso" e "Sto male"
- "Gioco a calcio per diventare ricco e famoso" e "Pratico uno sport"

### Codificatore

Una cosa, un'attività, un'azione può essere più generale di un'altra e includerla. Vedi se ti sembra ci sia questo tipo di relazione.

**[Scelta forzata di una delle tre alternative]**

- A è più specifico ed è incluso in B
- B è più specifico ed è incluso in A
- Non c'è questo tipo di relazione

> **Nota:** Gli item di scala psicometrica "dovrebbero" avere grossomodo lo stesso grado di astrazione. Individuare asimmetria nei diversi livelli di astrazione dei diversi contenuti/item di un costrutto è interessante.

### Sovrainsieme comune (Genitore comune)

**Definizione:** Due item, che non sono in relazioni di sinonimia o antinomia, fanno parte di un sovrainsieme comune prossimo a entrambi. Il sovrainsieme non è distante dai due item, è la cosa immediatamente più generale che li include entrambi. La relazione, metaforicamente, è quella tra fratelli/sorelle: figli di uno stesso genitore. Possono naturalmente esistere più sovrainsiemi comuni oltre a quelli considerati dal codificatore. Anche qui gli insiemi vanno intesi in termini sfumati, non precisamente definiti.

**Esempi:**

- "Sono arrabbiato" e "Mi sento triste" → un sovrainsieme comune è essere di cattivo umore o "provare un'emozione"
- "Faccio spesso colazione fuori" e "Spesso ceno fuori" → un sovrainsieme comune è "mangiare fuori"
- "Mi impegno nello studio perché mi piace" e "Mi impegno nello studio per fare contenti i miei genitori" → impegnarsi nello studio
- "Abbraccio spesso il mio partner" e "Do spesso una carezza al mio partner" → amore, gesti di affetto verso il partner

### Codificatore

Due cose, due attività, due azioni, possono far parte di una categoria comune. Vedi se ti sembra ci sia questo tipo di relazione.

**[Scelta forzata di una delle due alternative e una risposta aperta filtrata]**

- A e B fanno parte di una stessa categoria di cose/attività un po' più generale.
  - Se sì, quale? _(domanda aperta)_
- Non c'è una categoria comune ad A e B

> **Nota:** Spesso gli item di una scala sono considerati come elementi che condividono un sovrainsieme comune (il costrutto). Quindi i diversi item starebbero coprendo i diversi contenuti/aspetti del costrutto che non è rappresentato esplicitamente in nessun item, ma li include. Rilevante distinguere questa relazione di inclusione da quella di sinonimia/antinomia.

---

## 3. RELAZIONI CAUSALI

### Relazioni causali probabilistiche

**Definizione:** Sulla base della sua conoscenza del mondo, il codificatore si aspetta una relazione causale (probabilistica) con una direzione prevalente tra i due item. Una relazione causale si riferisce qui a una connessione tra due variabili, in cui un cambiamento in una variabile (la causa) porta direttamente o indirettamente (attraverso dei passaggi intermedi) a un cambiamento in un'altra variabile (l'effetto). La relazione è intesa in termini probabilistici, non è necessario che si verifichi il 100% delle volte ma è sufficiente la percezione di una relazione statisticamente significativa. Il giudizio sulla direzione della causa è in termini di prevalenza percepita, sono naturalmente possibili ma non codificate relazioni inverse o feedback loop.

**Esempi:**

- "Ho perso una persona cara recentemente" aumenta la probabilità di "Sono triste"
- "Nell'ultimo periodo ho difficoltà a dormire" aumenta la probabilità di "Mi sento stanco ultimamente"
- "Vado spesso a delle feste" aumenta la probabilità di "Conosco spesso nuove persone"
- "Recentemente ho ricevuto complimenti al lavoro" aumenta la probabilità di "Nell'ultimo periodo mi sento bene quando vado a lavorare"

### Codificatore

Una cosa aumenta la probabilità di un'altra quando l'accadere della prima porta frequentemente (anche se non necessariamente sempre) alla seconda cosa. La prima cosa può portare, in modo diretto o indiretto, all'altra cosa come risultato. Ad esempio, fumare molto e per un lungo periodo, porta frequentemente a una malattia polmonare.

**[Scelta forzata di una delle tre alternative]**
Scegli quella che secondo te è la situazione più frequente.

- A aumenta la probabilità di B
- B aumenta la probabilità di A
- Non c'è questo tipo di relazione tra A e B

> **Nota:** In psicometria gli item vengono spesso visti come effetti di un costrutto (modelli riflessivi), come cause (modelli formativi), o in interazione causale diretta tra di loro (modelli network). Sebbene queste relazioni vadano stabilite su un piano empirico e non di percezione soggettiva, il punto di vista di un potenziale rispondente al questionario o di un esperto è interessante.

```

---

### FILE: backend\config_defaults\config_example.yaml
```
### CONFIG Hybrid: CLASSIFICATION and Named Entity Recognition

{
  "task_type": "hybrid",
  "instruction": "seleziona le entità nominate nel testo ed assegna una etichetta alla frase.",
  "span_labels": [
    { "name": "Actor", "color": "#FF5733" },
    { "name": "Action", "color": "#33FF57" },
    { "name": "Victim", "color": "#3357FF" },
    { "name": "Threat", "color": "#FF33F6" },
    { "name": "Evidence", "color": "#FFA500" }
  ],
  "multi_select": true,
  "class_labels": [
    { "label": "Conspiracy", "value": "Yes" },
    { "label": "Not Conspiracy", "value": "No" },
    { "label": "Ambiguous", "value": "Can't tell" }
  ]
}

### CONFIG CLASSIFICATION

{
  "task_type": "classification",
  "instruction": "Il commento è offensivo?",
  "span_labels": [], 
  "class_labels": [
    {"value": "Hate", "label": "Hate Speech"},
    {"value": "Offensive", "label": "Offensive"},
    {"value": "Safe", "label": "Safe / Neutral"}
  ]
}

### CONFIG CLASSIFICATION MULTILABEL
{
  "task_type": "multilabel", 
  "instruction": "Seleziona tutte le categorie applicabili.",
  "multi_select": true,  
  "span_labels": [],
  "class_labels": [
    {"value": "racism", "label": "Razzismo"},
    {"value": "sexism", "label": "Sessismo"},
    {"value": "politics", "label": "Politica"},
    {"value": "spam", "label": "Spam"}
  ]
}


### CONFIG Named Entity Recognition
{
  "task_type": "ner",
  "instruction": "Evidenzia tutte le entità nominate nel testo.",
  "span_labels": [
    {"name": "Person", "color": "#FF0000"},
    {"name": "Location", "color": "#00FF00"},
    {"name": "Organization", "color": "#0000FF"}
  ],
  "class_labels": []
}




```

---

### FILE: backend\config_defaults\default_gold_config.json
```
{
  "min_accuracy_required": 0.6,
  "gold_injection_frequency": 5,
  "continuous_exclusion": false,
  "evaluation_strategy": "percentage",
  "max_strikes": 3,
  "min_gold_before_eval": 3
}
```

---

### FILE: backend\config_defaults\default_instructions_content.md
```
# Task Instructions

## The Goal

Read the items presented to you and complete the annotation tasks as described in the codebook.

## How to Use the Interface

1. **Read the text** carefully
2. **Select the appropriate classification** from the options provided
3. **Highlight relevant spans** in the text (if applicable) by selecting a label and then highlighting the text
4. **Submit** your annotation and proceed to the next task

## Tips

- Take your time reading each item
- If unsure, refer back to the codebook (you can revisit it anytime)
- Be consistent in your annotations
- Quality is more important than speed

```

---

### FILE: backend\config_defaults\default_practice_task.json
```
{
  "required": true,
  "text": "The government is putting chips in the water to control us and nobody seems to care about it.",
  "gold_solution": {
    "classification": "Yes",
    "spans": [
      { "start": 0, "end": 14, "label": "Actor", "text": "The government" },
      {
        "start": 18,
        "end": 49,
        "label": "Action",
        "text": "putting chips in the water to"
      },
      { "start": 50, "end": 60, "label": "Victim", "text": "control us" }
    ]
  },
  "hints": [
    "Start by reading the full text. Does it describe a hidden plot or conspiracy?",
    "Look for WHO is allegedly doing something — that is the Actor.",
    "What are they DOING? That is the Action.",
    "Who is being AFFECTED or harmed? That is the Victim."
  ]
}

```

---

### FILE: backend\config_defaults\default_project_config.json
```
{
  "task_type": "hybrid",
  "span_labels": [
    {
      "name": "Actor",
      "color": "#FF5733",
      "hover_hint": "Who is allegedly responsible for a malicious action or agenda?"
    },
    {
      "name": "Action",
      "color": "#33FF57",
      "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
    },
    {
      "name": "Victim",
      "color": "#3357FF",
      "hover_hint": "Who is negatively affected by the actor's agenda?"
    },
    {
      "name": "Threat",
      "color": "#FF33F6",
      "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
    },
    {
      "name": "Evidence",
      "color": "#FFA500",
      "hover_hint": "Which arguments or expressions does the writer of the text use to support his claims?"
    }
  ],
  "class_labels": [
    { "label": "Conspiracy", "value": "Yes" },
    { "label": "Not Conspiracy", "value": "No" },
    { "label": "Ambiguous", "value": "Can't tell" }
  ]
}

```

---

### FILE: backend\config_defaults\default_screening_config.json
```
[
  {
    "id": "age",
    "type": "number",
    "label": "How old are you?",
    "required": true,
    "min": 18,
    "max": 99
  },
  {
    "id": "gender",
    "type": "select",
    "label": "Gender?",
    "required": true,
    "options": ["Male", "Female", "Non-binary", "Prefer not to say"]
  },
  {
    "id": "native_language",
    "type": "select",
    "label": "Native language?",
    "required": true,
    "options": ["English", "Italian", "Spanish", "French", "German", "Other"]
  }
]

```

---

### FILE: backend\config_tests_files\default_project_config.json
```
{
  "task_type": "hybrid",
  "span_labels": [
    {
      "name": "Actor",
      "color": "#FF5733",
      "hover_hint": "Who is allegedly responsible for a malicious action or agenda?"
    },
    {
      "name": "Action",
      "color": "#33FF57",
      "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
    },
    {
      "name": "Victim",
      "color": "#3357FF",
      "hover_hint": "Who is negatively affected by the actor's agenda?"
    },
    {
      "name": "Threat",
      "color": "#FF33F6",
      "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
    },
    {
      "name": "Evidence",
      "color": "#FFA500",
      "hover_hint": "Which arguments or expressions does the writer of the text use to support his claims?"
    }
  ],
  "class_labels": [
    { "label": "Conspiracy", "value": "Yes" },
    { "label": "Not Conspiracy", "value": "No" },
    { "label": "Ambiguous", "value": "Can't tell" }
  ]
}

```

---

### FILE: backend\config_tests_files\default_screening_config.json
```
{
  "min_accuracy_required": 0.6,
  "gold_injection_frequency": 20,
  "continuous_screening": false
}

```

---

### FILE: frontend\.env.development
```
VITE_API_BASE_URL=http://localhost:8000/api/v1/
```

---

### FILE: frontend\.env.production
```
VITE_API_BASE_URL=/api/v1/
```

---

### FILE: frontend\index.html
```
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Annotation Task</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>

```

---

### FILE: frontend\package.json
```
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.13.4",
    "vue": "^3.5.24",
    "vue-router": "^5.0.2"
  },
  "devDependencies": {
    "@types/node": "^24.10.1",
    "@vitejs/plugin-vue": "^6.0.1",
    "@vue/tsconfig": "^0.8.1",
    "typescript": "~5.9.3",
    "vite": "npm:rolldown-vite@7.2.5",
    "vue-tsc": "^3.1.4"
  },
  "overrides": {
    "vite": "npm:rolldown-vite@7.2.5"
  }
}

```

---

### FILE: frontend\README.md
```
# Vue 3 + TypeScript + Vite

This template should help get you started developing with Vue 3 and TypeScript in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about the recommended Project Setup and IDE Support in the [Vue Docs TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup).

```

---

### FILE: frontend\tsconfig.app.json
```
{
  "extends": "@vue/tsconfig/tsconfig.dom.json",
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "types": [
      "vite/client"
    ],
    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noImplicitAny": false,
    "allowJs": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": [
    "src/**/*.ts",
    "src/**/*.tsx",
    "src/**/*.vue"
  ]
}
```

---

### FILE: frontend\tsconfig.json
```
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}

```

---

### FILE: frontend\tsconfig.node.json
```
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "ESNext",
    "types": ["node"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}

```

---

### FILE: frontend\vite.config.ts
```
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
})

```

---

### FILE: frontend\src\App.vue
```
<script setup>
</script>

<template>
  <router-view />
</template>

<style>
/* Global styles if needed */
body {
  margin: 0;
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
}
</style>

```

---

### FILE: frontend\src\axios.js
```
import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});


api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);


api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        const status = error.response ? error.response.status : null;

        if (status === 401) {
            console.error("Session expired, redirecting to login...");
            window.location.href = '/login';
        } else if (status === 404) {
            console.error("Resource not found");
        } else {
            console.error("API Error:", error.response?.data?.message || error.message);
        }

        return Promise.reject(error);
    }
);

export default api;
```

---

### FILE: frontend\src\main.ts
```
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

createApp(App)
    .use(router)
    .mount('#app')
```

---

### FILE: frontend\src\router.js
```
import { createRouter, createWebHistory } from "vue-router";
import LoginView from "./views/LoginView.vue";
import ConsentView from "./views/ConsentView.vue";
import ScreeningView from "./views/ScreeningView.vue";
import CodebookView from "./views/CodebookView.vue";
import InstructionsView from "./views/InstructionsView.vue";
import AnnotatorView from "./views/AnnotatorView.vue";
import ConsentFullPage from "./views/ConsensFullPage.vue";

const routes = [
  { path: "/", component: LoginView },
  { path: "/:projectSlug", component: LoginView },
  { path: "/:projectSlug/consent", component: ConsentView },
  { path: "/:projectSlug/screening", component: ScreeningView },
  { path: "/:projectSlug/codebook", component: CodebookView },
  { path: "/:projectSlug/instructions", component: InstructionsView },
  { path: "/:projectSlug/annotate", component: AnnotatorView },
  { path: "/consent-form", component: ConsentFullPage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;


```

---

### FILE: frontend\src\style.css
```

```

---

### FILE: frontend\src\assets\shared.css
```
/* =====================================================
   shared.css — Stili comuni a tutte le views
   Importa questo file nelle views con:
   @import '../assets/shared.css';
   ===================================================== */

@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* ── PAGE CONTAINER ── */
.page-container {
    min-height: 100vh;
    padding: 40px 20px;
    background: linear-gradient(135deg, #f0f2f5 0%, #e8ecf1 100%);
    font-family: 'Outfit', sans-serif;
}

/* ── CARDS ── */
.card {
    background: white;
    max-width: 820px;
    margin: 0 auto;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.card.wide {
    max-width: 900px;
}

.center-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 40px;
}

.card-header {
    padding: 32px 40px 20px;
    border-bottom: 2px solid #e3e8ee;
    background: #f8fafc;
}

.card-header h1 {
    margin: 0 0 6px;
    font-size: 1.8rem;
    color: #1a1f36;
    font-weight: 700;
}

.subtitle {
    color: #666;
    margin: 0;
    font-size: 0.95rem;
}

.card-body {
    padding: 30px;
}

.card-footer {
    padding: 20px 30px;
    background: #f8fafc;
    border-top: 1px solid #e3e8ee;
    display: flex;
    justify-content: flex-end;
    gap: 15px;
}

/* ── LOADING ── */
.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 0;
}

.loader {
    width: 48px;
    height: 48px;
    border: 5px solid #e3e8ee;
    border-bottom-color: #306ee8;
    border-radius: 50%;
    animation: rotation 1s linear infinite;
    margin-bottom: 20px;
}

/* ── STATES ── */
.state-text {
    color: #999;
    font-style: italic;
}

.error {
    color: #dc3545;
    padding: 20px 40px;
}

.error-toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: #fee2e2;
    color: #dc2626;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #dc2626;
}

/* ── ACTIONS AREA ── */
.actions {
    padding: 24px 40px 32px;
    border-top: 2px solid #e3e8ee;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    color: #444;
    margin-bottom: 18px;
    cursor: pointer;
    font-weight: 500;
}

.checkbox-label input {
    width: 18px;
    height: 18px;
    cursor: pointer;
    flex-shrink: 0;
    accent-color: #306ee8;
}

/* ── BUTTONS ── */
.actions button,
.feedback-actions button {
    width: 100%;
    padding: 14px;
    background: #306ee8;
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s;
    font-family: 'Outfit', sans-serif;
    box-shadow: 0 4px 14px rgba(48, 110, 232, 0.3);
}

.actions button:hover:not(:disabled),
.feedback-actions button:hover:not(:disabled) {
    background: #1a4ab9;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(48, 110, 232, 0.4);
}

.actions button:disabled,
.feedback-actions button:disabled {
    background: #ccc;
    cursor: not-allowed;
    box-shadow: none;
}

.action-btn {
    padding: 12px 24px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    font-family: 'Outfit', sans-serif;
}

.clear-btn {
    background: #f1f5f9;
    color: #475569;
}

.clear-btn:hover {
    background: #e2e8f0;
}

.submit-btn {
    padding: 14px 32px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 1.05rem;
    cursor: pointer;
    border: none;
    transition: all 0.3s;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
    font-family: 'Outfit', sans-serif;
    width: auto;
}

.primary-submit {
    background: #306ee8;
    color: white;
    flex-grow: 1;
    max-width: 300px;
}

.primary-submit:hover:not(:disabled) {
    background: #1a4ab9;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(48, 110, 232, 0.4);
}

.submit-btn:disabled {
    background: #e3e8ee;
    color: #a0aec0;
    box-shadow: none;
    cursor: not-allowed;
}

/* ── CLASSIFICATION ── */
.classification-section {
    margin-top: 30px;
    padding-top: 30px;
    border-top: 2px dashed #e3e8ee;
}

.question-title {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 20px;
    color: #1a1f36;
}

.options-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.option-label {
    background: #f8fafc;
    border: 2px solid #e3e8ee;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
}

.option-label:hover {
    border-color: #cbd5e1;
    background: #fff;
}

.option-label.active {
    background: #306ee8;
    color: white;
    border-color: #1a4ab9;
    box-shadow: 0 4px 12px rgba(48, 110, 232, 0.3);
}

.option-label input {
    display: none;
}

/* ── DOC TEXT PREVIEW ── */
.doc-text-preview {
    font-size: 1.2rem;
    line-height: 1.8;
    color: #334155;
    background: #f8fafc;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}

/* ── MARKDOWN CONTENT (deep styles riusabili) ── */
.markdown-body {
    padding: 32px 40px;
    color: #1a1f36;
    line-height: 1.8;
    font-size: 1rem;
}

.markdown-body :deep(h1) {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1a1f36;
    margin: 28px 0 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e3e8ee;
}

.markdown-body :deep(h2) {
    font-size: 1.3rem;
    font-weight: 600;
    color: #306ee8;
    margin: 24px 0 10px;
}

.markdown-body :deep(h3) {
    font-size: 1.1rem;
    font-weight: 600;
    color: #475569;
    margin: 20px 0 8px;
}

.markdown-body :deep(p) {
    margin: 8px 0;
    color: #334155;
}

.markdown-body :deep(ul) {
    padding-left: 20px;
    margin: 8px 0;
}

.markdown-body :deep(li) {
    margin: 6px 0;
    color: #334155;
}

.markdown-body :deep(strong) {
    color: #1a1f36;
    font-weight: 700;
}

.markdown-body :deep(code) {
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    color: #306ee8;
}

.markdown-body :deep(hr) {
    border: none;
    border-top: 2px solid #e3e8ee;
    margin: 24px 0;
}

/* ── ANIMATIONS ── */
@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes rotation {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

```

---

### FILE: frontend\src\components\HelloWorld.vue
```
<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ msg: string }>()

const count = ref(0)
</script>

<template>
  <h1>{{ msg }}</h1>

  <div class="card">
    <button type="button" @click="count++">count is {{ count }}</button>
    <p>
      Edit
      <code>components/HelloWorld.vue</code> to test HMR
    </p>
  </div>

  <p>
    Check out
    <a href="https://vuejs.org/guide/quick-start.html#local" target="_blank"
      >create-vue</a
    >, the official Vue + Vite starter
  </p>
  <p>
    Learn more about IDE Support for Vue in the
    <a
      href="https://vuejs.org/guide/scaling-up/tooling.html#ide-support"
      target="_blank"
      >Vue Docs Scaling up Guide</a
    >.
  </p>
  <p class="read-the-docs">Click on the Vite and Vue logos to learn more</p>
</template>

<style scoped>
.read-the-docs {
  color: #888;
}
</style>

```

---

### FILE: frontend\src\components\TextHighlighter.vue
```
<template>
    <div class="highlighter-container">
        <div class="toolbar" v-if="labels.length > 0">
            <div class="toolbar-brand">
                <span class="toolbar-icon">🖋️</span>
                <span class="toolbar-text">Highlighter</span>
            </div>
            <div class="label-chips">
                <button v-for="(label, idx) in labels" :key="label.name" :style="{
                    backgroundColor: selectedLabel === label.name ? label.color : 'white',
                    color: selectedLabel === label.name ? 'white' : '#4f566b',
                    borderColor: selectedLabel === label.name ? 'transparent' : '#e3e8ee'
                }" class="label-chip" @click="selectedLabel = label.name"
                    :class="{ active: selectedLabel === label.name }" :title="label.hover_hint">
                    <span class="chip-name">{{ label.name }}</span>
                    <span class="chip-key">{{ idx + 1 }}</span>
                </button>
            </div>
        </div>

        <div class="text-card-area" ref="textRef" @mouseup="handleSelection">
            <template v-for="(chunk, index) in renderChunks" :key="index">
                <span class="chunk-span" :class="{ 'has-highlights': chunk.spans.length > 0 }">
                    <span class="chunk-text" :style="getChunkTextStyle(chunk)">{{ chunk.text }}</span>
                    <div class="chunk-highlights" v-if="chunk.spans.length > 0"
                        :style="{ height: (maxLevels * 18) + 'px' }">
                        <div v-for="level in maxLevels" :key="level" class="highlight-level">
                            <template v-for="span in chunk.spansByLevel[level - 1]" :key="span.id">
                                <div class="span-bar" :style="{
                                    backgroundColor: getLabelColor(span.label),
                                    opacity: hoveredSpanId && hoveredSpanId !== span.id ? 0.3 : 1
                                }" @mouseover="hoveredSpanId = span.id" @mouseleave="hoveredSpanId = null">
                                    <span class="span-label-hint" v-if="chunk.isStartOfSpan[span.id]">
                                        {{ span.label }}
                                        <button class="remove-chip-btn-mini"
                                            @click.stop="removeSpan(span.id)">×</button>
                                    </span>
                                </div>
                            </template>
                        </div>
                    </div>
                </span>
            </template>
        </div>

        <div v-if="showPopup" class="popup-overlay" @click.self="closePopup">
            <div class="popup-modal">
                <div class="popup-icon">⚠️</div>
                <p class="popup-message">{{ popupMessage }}</p>
                <button class="popup-btn" @click="closePopup">Understood</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({
    text: String,
    labels: Array,
    spans: {
        type: Array,
        default: () => []
    }
});

const emit = defineEmits(['update:spans']);

const selectedLabel = ref(null);
const textRef = ref(null);

// Popup State
const showPopup = ref(false);
const popupMessage = ref("");
const hoveredSpanId = ref(null);

const openPopup = (msg) => {
    popupMessage.value = msg;
    showPopup.value = true;
};

const closePopup = () => {
    showPopup.value = false;
};

// Keydown listener for labels 1-9
const handleKeydown = (e) => {
    // Ignore if user is typing in an input, textarea or contenteditable
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
        return;
    }

    const key = parseInt(e.key);
    if (!isNaN(key) && key > 0 && key <= props.labels.length) {
        selectedLabel.value = props.labels[key - 1].name;
    }
};

onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});

watch(() => props.labels, (newLabels) => {
    if (newLabels && newLabels.length > 0 && !selectedLabel.value) {
        selectedLabel.value = newLabels[0].name;
    }
}, { immediate: true });


const getGlobalOffset = (root, targetNode, targetOffset) => {
    let offset = 0;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
            if (node.parentNode && node.parentNode.classList.contains('chunk-text')) {
                return NodeFilter.FILTER_ACCEPT;
            }
            return NodeFilter.FILTER_REJECT;
        }
    });

    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node === targetNode) {
            return offset + targetOffset;
        }
        offset += node.nodeValue.length;
    }
    return -1;
};

const handleSelection = () => {
    const selection = window.getSelection();
    if (selection.rangeCount === 0 || selection.isCollapsed) return;

    const range = selection.getRangeAt(0);
    const container = textRef.value;

    if (!container.contains(range.commonAncestorContainer)) {
        selection.removeAllRanges();
        return;
    }

    const start = getGlobalOffset(container, range.startContainer, range.startOffset);
    const end = getGlobalOffset(container, range.endContainer, range.endOffset);

    if (start === -1 || end === -1) {
        selection.removeAllRanges();
        return;
    }

    let realStart = Math.min(start, end);
    let realEnd = Math.max(start, end);

    let tempSegment = props.text.slice(realStart, realEnd);
    const leadingSpaces = tempSegment.length - tempSegment.trimStart().length;
    const trailingSpaces = tempSegment.length - tempSegment.trimEnd().length;

    realStart += leadingSpaces;
    realEnd -= trailingSpaces;

    while (realStart > 0 && !/\s/.test(props.text[realStart - 1])) {
        realStart--;
    }
    while (realEnd < props.text.length && !/\s/.test(props.text[realEnd])) {
        realEnd++;
    }

    let textSegment = props.text.slice(realStart, realEnd);

    if (!textSegment.trim()) {
        selection.removeAllRanges();
        return;
    }

    textSegment = textSegment.trim();

    if (!selectedLabel.value) {
        openPopup("Please select a label first!");
        selection.removeAllRanges();
        return;
    }

    // Strict redundancy check (same label): prevent ANY overlap (fully contained, containing, or partial)
    const hasAnySameLabelOverlap = props.spans.some(span =>
        span.label === selectedLabel.value && (
            realStart < span.end && realEnd > span.start
        )
    );

    if (hasAnySameLabelOverlap) {
        selection.removeAllRanges();
        return;
    }

    // Overlap check removed to allow nested/overlapping spans
    /*
    const hasOverlap = props.spans.some(span => {
        return (realStart < span.end && realEnd > span.start);
    });

    if (hasOverlap) {
        openPopup("Warning: Overlapping highlights are not allowed. Please remove the existing one first.");
        selection.removeAllRanges();
        return;
    }
    */

    const newSpan = {
        start: realStart,
        end: realEnd,
        label: selectedLabel.value,
        text: textSegment,
        id: `span-${Date.now()}-${Math.floor(Math.random() * 1000)}`
    };

    emit('update:spans', [...props.spans, newSpan]);
    selection.removeAllRanges();
};

const removeSpan = (spanId) => {
    const filtered = props.spans.filter(s => s.id !== spanId);
    emit('update:spans', filtered);
};

const getLabelColor = (labelName) => {
    const l = props.labels.find(x => x.name === labelName);
    return l ? l.color : '#cbd5e1';
};

const getChunkTextStyle = (chunk) => {
    if (!hoveredSpanId.value) return {};
    const activeSpan = chunk.spans.find(s => s.id === hoveredSpanId.value);
    if (!activeSpan) return { transition: 'background-color 0.2s' };

    return {
        backgroundColor: getLabelColor(activeSpan.label) + '44', // ~25% opacity
        borderRadius: '2px',
        transition: 'background-color 0.2s'
    };
};

const spansWithLevels = computed(() => {
    // Sort spans by start position, then by end position (longer spans first)
    const sortedSpans = [...props.spans].sort((a, b) => a.start - b.start || (b.end - a.end));
    const levels = []; // stores the right-most end position of each level

    return sortedSpans.map(span => {
        let assignedLevel = -1;
        for (let i = 0; i < levels.length; i++) {
            // Check if this span fits in level i (current start >= last end in that level)
            if (span.start >= levels[i]) {
                assignedLevel = i;
                levels[i] = span.end;
                break;
            }
        }
        if (assignedLevel === -1) {
            assignedLevel = levels.length;
            levels.push(span.end);
        }
        return { ...span, level: assignedLevel };
    });
});

const maxLevels = computed(() => {
    if (props.spans.length === 0) return 0;
    const levels = [];
    spansWithLevels.value.forEach(s => {
        if (!levels.includes(s.level)) levels.push(s.level);
    });
    return Math.max(0, ...levels) + 1;
});

const renderChunks = computed(() => {
    if (!props.text) return [];

    // 1. Collect all boundaries
    const boundaries = new Set([0, props.text.length]);
    spansWithLevels.value.forEach(s => {
        boundaries.add(s.start);
        boundaries.add(s.end);
    });

    // 2. Sort boundaries to create atomic segments
    const sortedBoundaries = Array.from(boundaries).sort((a, b) => a - b);
    const chunks = [];

    for (let i = 0; i < sortedBoundaries.length - 1; i++) {
        const start = sortedBoundaries[i];
        const end = sortedBoundaries[i + 1];
        const text = props.text.slice(start, end);

        if (text === "") continue;

        // 3. Find which spans cover this atomic chunk
        const coveringSpans = spansWithLevels.value.filter(s => s.start <= start && s.end >= end);

        // Track if this chunk is the start of any span (to render the label/button)
        const isStartOfSpan = {};
        const spansByLevel = {};

        coveringSpans.forEach(s => {
            isStartOfSpan[s.id] = (s.start === start);
            if (!spansByLevel[s.level]) spansByLevel[s.level] = [];
            spansByLevel[s.level].push(s);
        });

        chunks.push({
            text,
            start,
            end,
            spans: coveringSpans,
            spansByLevel,
            isStartOfSpan
        });
    }

    return chunks;
});
</script>

<style scoped>
.highlighter-container {
    display: flex;
    flex-direction: column;
    gap: 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e3e8ee;
    background: white;
}

.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background-color: #e3effb;
    border-bottom: 1px solid #d1d9e6;
}

.toolbar-brand {
    display: flex;
    align-items: center;
    gap: 8px;
}

.toolbar-icon {
    font-size: 1.2rem;
}

.toolbar-text {
    font-weight: 700;
    font-size: 0.9rem;
    color: #1a1f36;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.label-chips {
    display: flex;
    gap: 8px;
}

.label-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 50px;
    border: 1px solid;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.2s;
    background: white;
}

.chip-key {
    background: rgba(0, 0, 0, 0.1);
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    font-size: 0.7rem;
}

.label-chip.active {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
}

.label-chip.active .chip-key {
    background: rgba(255, 255, 255, 0.3);
}

.text-card-area {
    font-size: 1.3rem;
    line-height: 3.0;
    /* Balanced line height for labels and readability */
    padding: 35px;
    min-height: 250px;
    white-space: pre-wrap;
    cursor: text;
    background-color: #fdfdfd;
    color: #1e293b;
    /* Darker, higher contrast text */
}

.normal-text {
    color: inherit;
}

/* ATOMIC CHUNK STYLES */
.chunk-span {
    position: relative;
    display: inline;
}

.chunk-text {
    position: relative;
    z-index: 5;
}

.chunk-highlights {
    position: absolute;
    top: 100%;
    left: 0;
    width: 100%;
    display: flex;
    flex-direction: column;
    z-index: 10;
    pointer-events: none;
    margin-top: 4px;
}

.highlight-level {
    height: 18px;
    width: 100%;
    display: flex;
    position: relative;
    align-items: center;
}

.span-bar {
    height: 4px;
    width: 100%;
    position: relative;
    pointer-events: auto;
    cursor: pointer;
    transition: all 0.2s;
    border-radius: 2px;
}

.span-label-hint {
    position: absolute;
    top: 0;
    left: 0;
    font-size: 0.65rem;
    font-weight: 700;
    color: white;
    background: inherit;
    padding: 0 6px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    height: 16px;
    line-height: 16px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
    transform: translateY(-3px);
    letter-spacing: 0.4px;
    font-family: '__robotoCondensed_9f41a4', '__robotoCondensed_Fallback_9f41a4', 'Arial Narrow', 'Arial', sans-serif;
}

.remove-chip-btn-mini {
    background: rgba(0, 0, 0, 0.25);
    border: none;
    color: white;
    border-radius: 50%;
    width: 12px;
    height: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 9px;
    padding: 0;
    transition: background 0.2s;
}

.remove-chip-btn-mini:hover {
    background: rgba(0, 0, 0, 0.5);
}

.chunk-span.has-highlights {
    border-radius: 2px;
}

/* POPUP MODAL (Premium Look) */
.popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(26, 31, 54, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
}

.popup-modal {
    background: white;
    padding: 32px;
    border-radius: 20px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
    text-align: center;
    max-width: 400px;
    width: 90%;
    animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.popup-icon {
    font-size: 3rem;
    margin-bottom: 16px;
}

.popup-message {
    font-size: 1.1rem;
    color: #4f566b;
    margin-bottom: 24px;
    line-height: 1.5;
}

.popup-btn {
    padding: 10px 30px;
    background: #306ee8;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
}

.popup-btn:hover {
    background: #1a4ab9;
    transform: scale(1.05);
}

@keyframes popIn {
    from {
        opacity: 0;
        transform: scale(0.8);
    }

    to {
        opacity: 1;
        transform: scale(1);
    }
}
</style>

```

---

### FILE: frontend\src\composables\useMarkdownRenderer.js
```
import { computed } from 'vue';

/**
 * Composable che converte un testo Markdown in HTML.
 * @param {import('vue').Ref<string>} rawText - ref contenente il testo Markdown grezzo
 * @returns {{ rendered: import('vue').ComputedRef<string> }}
 */
export function useMarkdownRenderer(rawText) {
    const rendered = computed(() => {
        let text = rawText.value;
        if (!text) return '';

        // Escape HTML entities
        text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

        // Headers
        text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Bold and italic
        text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/(?<!\w)_(.+?)_(?!\w)/g, '<em>$1</em>');
        text = text.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

        // Inline code
        text = text.replace(/`(.+?)`/g, '<code>$1</code>');

        // Unordered lists
        text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        // Ordered lists
        text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Horizontal rules
        text = text.replace(/^---$/gm, '<hr>');

        // Paragraphs (lines not already wrapped in tags)
        text = text.replace(/^(?!<[hulo]|<li|<hr)(.+)$/gm, '<p>$1</p>');

        // Clean up empty paragraphs
        text = text.replace(/<p>\s*<\/p>/g, '');

        return text;
    });

    return { rendered };
}

```

---

### FILE: frontend\src\composables\useProjectContext.js
```
import { useRoute } from 'vue-router';

/**
 * Composable che espone pid, projectSlug e projectId
 * letti da localStorage e dai parametri della rotta.
 */
export function useProjectContext() {
    const route = useRoute();
    const pid = localStorage.getItem('prolific_pid');
    const projectSlug = route.params.projectSlug ?? localStorage.getItem('project_slug');
    const projectId = localStorage.getItem('project_id');
    return { pid, projectSlug, projectId };
}

```

---

### FILE: frontend\src\views\AnnotatorView.vue
```
<template>
    <div class="main-container">
        <div v-if="loading" class="loading-container">
            <div class="loader"></div>
            <p>Loading next task...</p>
        </div>

        <div v-else-if="!currentDoc && !stopped" class="finished-card">
            <div class="confetti">🎉</div>
            <h2>All tasks completed!</h2>
            <div class="debrief-text">
                <p>The texts you annotated were obtained from social media and may include false information and
                    conspiracy theories. The authors of this task do not endorse them.</p>
                <p>You may take this task multiple times. Thank you for your work!</p>
            </div>
            <p class="redirect-notice">Redirecting to provider in <strong>{{ countdown }}</strong> seconds...</p>
        </div>

        <div v-else-if="stopped" class="finished-card">
            <div class="icon">🛑</div>
            <h2>Session Ended</h2>
            <p>{{ stopMessage || "Thank you for your contribution." }}</p>
        </div>

        <div v-else class="task-card">
            <div v-if="isGold" class="training-banner">
                QUALITY CONTROL TASK (This is a gold unit used to verify annotation quality)
            </div>

            <div class="card-header highlight-header">
                <div class="instruction-box">
                    <h3>Task Instruction</h3>
                    <p>{{ config.instruction || "Read the text below and complete the tasks." }}</p>
                </div>
            </div>

            <div class="card-body">
                <div class="section" v-if="hasHighlighter">
                    <TextHighlighter :text="currentDoc.text" :labels="spanLabels" v-model:spans="spans" />
                </div>

                <div class="doc-text-preview" v-else>
                    {{ currentDoc.text }}
                </div>

                <div class="section classification-section" v-if="classOptions.length > 0">
                    <div class="question-title">
                        {{ config.question || "Classify this text:" }}
                    </div>

                    <div class="options-grid">
                        <label v-for="opt in classOptions" :key="opt.value" class="option-label"
                            :class="{ active: isSelected(opt.value) }" :title="opt.hover_hint">
                            <input v-if="config.multi_select" type="checkbox" :value="opt.value"
                                v-model="classification">
                            <input v-else type="radio" :value="opt.value" v-model="classification">
                            <span class="check-icon"></span>
                            {{ opt.label }}
                        </label>
                    </div>
                </div>
            </div>

            <div class="card-footer actions">
                <button class="action-btn clear-btn" @click="clearForm">Clear</button>
                <button class="submit-btn primary-submit" @click="submitTask" :disabled="!canSubmit">
                    Submit &amp; Next
                </button>
            </div>

            <p v-if="errorMsg" class="error-toast">{{ errorMsg }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import TextHighlighter from '../components/TextHighlighter.vue';
import { useProjectContext } from '../composables/useProjectContext';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

// STATO
const loading = ref(true);
const currentDoc = ref(null);
const errorMsg = ref('');
const config = ref({});
const startTime = ref(0);
const countdown = ref(10);
let redirectTimer = null;
const stopped = ref(false);
const stopMessage = ref('');
const isTraining = ref(false);
const isGold = ref(false);

onUnmounted(() => {
    if (redirectTimer) clearInterval(redirectTimer);
});

// RISPOSTE DELL'UTENTE
const classification = ref(null);
const spans = ref([]);

// OPZIONI ESTRATTE DAL CONFIG
const spanLabels = ref([]);
const classOptions = ref([]);

const hasHighlighter = computed(() => spanLabels.value.length > 0);

onMounted(() => {
    if (!pid) router.push('/');
    fetchNextTask();
});

const clearForm = () => {
    spans.value = [];
    if (config.value.multi_select) {
        classification.value = [];
    } else {
        classification.value = null;
    }
};

const fetchNextTask = async () => {
    loading.value = true;
    currentDoc.value = null;
    errorMsg.value = '';
    spans.value = [];
    stopped.value = false;

    if (!projectId && !projectSlug) {
        errorMsg.value = "Fatal Error: No Project ID/Slug found.";
        loading.value = false;
        return;
    }

    try {
        const res = await api.get('next-task/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.status === 'completed') {
            loading.value = false;
            redirectTimer = setInterval(() => {
                countdown.value--;
                if (countdown.value <= 0) {
                    clearInterval(redirectTimer);
                    window.location.href = res.data.completion_url;
                }
            }, 1000);
            return;
        } else if (res.data.status === 'stopped') {
            loading.value = false;
            stopped.value = true;
            stopMessage.value = res.data.message;
            return;
        }

        isTraining.value = !!res.data.feedback_enabled;
        isGold.value = !!res.data.is_gold;

        currentDoc.value = res.data;
        config.value = res.data.project_config || {};

        spanLabels.value = config.value.span_labels || [];
        classOptions.value = config.value.class_labels || [];

        if (config.value.multi_select) {
            classification.value = [];
        } else {
            classification.value = null;
        }

        startTime.value = Date.now();
    } catch (err) {
        errorMsg.value = "Error fetching task. Please refresh.";
    } finally {
        loading.value = false;
    }
};

const isSelected = (val) => {
    if (Array.isArray(classification.value)) {
        return classification.value.includes(val);
    }
    return classification.value === val;
};

const canSubmit = computed(() => {
    if (classOptions.value.length > 0) {
        if (Array.isArray(classification.value)) {
            return classification.value.length > 0;
        }
        return classification.value !== null;
    }
    return true;
});

const submitTask = async () => {
    if (!canSubmit.value) return;

    const duration = (Date.now() - startTime.value);
    loading.value = true;

    const payload = {
        pid: pid,
        document: currentDoc.value.id,
        result: {
            classification: classification.value,
            spans: spans.value
        },
        milliseconds_to_complete: duration
    };

    try {
        await api.post('submit/', payload);
        fetchNextTask();
    } catch (err) {
        errorMsg.value = "Error saving. Try again.";
        loading.value = false;
    }
};
</script>

<style scoped>
@import '../assets/shared.css';

.main-container {
    max-width: 1000px;
    margin: 0px auto;
    padding: 37px;
    font-family: 'Outfit', sans-serif;
    color: #1a1f36;
}

/* CARDS */
.task-card,
.finished-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.highlight-header {
    background-color: #f8fafc;
}

.instruction-box h3 {
    margin: 0 0 8px 0;
    color: #1a1f36;
    font-size: 1.25rem;
}

.instruction-box p {
    margin: 0;
    color: #4f566b;
    line-height: 1.5;
}

/* TRAINING BANNER */
.training-banner {
    background: #fef3c7;
    color: #92400e;
    padding: 12px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9rem;
    border-bottom: 1px solid #fde68a;
}

/* FINISHED STATE */
.finished-card {
    text-align: center;
    padding: 60px 40px;
    background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
}

.confetti {
    font-size: 4rem;
    margin-bottom: 20px;
}

.finished-card h2 {
    color: #1a1f36;
    margin-bottom: 20px;
    font-size: 2.5rem;
}

.debrief-text {
    background: white;
    border-radius: 12px;
    padding: 24px;
    max-width: 600px;
    margin: 0 auto 30px;
    border-left: 6px solid #306ee8;
    text-align: left;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
}
</style>

```

---

### FILE: frontend\src\views\CodebookView.vue
```
<template>
    <div class="page-container">
        <div class="card">
            <div class="card-header">
                <h1>📖 Study Materials</h1>
                <p class="subtitle">Please read the following materials carefully before proceeding to the task.</p>
            </div>

            <div v-if="loading" class="state-text" style="padding: 40px;">Loading codebook...</div>
            <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
            <div v-else-if="shouldSkip" class="state-text" style="padding: 40px;">No codebook for this project. Redirecting...</div>

            <div v-else class="markdown-body" v-html="rendered"></div>

            <div v-if="!loading && !shouldSkip && rendered" class="actions">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="hasRead">
                    I have read and understood the materials above.
                </label>
                <button @click="completeCodebook" :disabled="!hasRead || submitting">
                    {{ submitting ? 'Saving...' : 'Continue to Instructions' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import { useProjectContext } from '../composables/useProjectContext';
import { useMarkdownRenderer } from '../composables/useMarkdownRenderer';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const submitting = ref(false);
const hasRead = ref(false);
const rawContent = ref('');

const { rendered } = useMarkdownRenderer(rawContent);

const fetchCodebook = async () => {
    try {
        const res = await api.get('get-codebook/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            setTimeout(() => router.push(`/${slug}/instructions`), 500);
            return;
        }

        rawContent.value = res.data.content || '';
    } catch (err) {
        errorMsg.value = "Error loading codebook. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (!pid) {
        router.push('/');
        return;
    }
    fetchCodebook();
});

const completeCodebook = async () => {
    submitting.value = true;
    try {
        await api.post('codebook/', {
            pid,
            project_slug: projectSlug,
            project_id: projectId
        });
        const slug = projectSlug || projectId;
        router.push(`/${slug}/instructions`);
    } catch (err) {
        errorMsg.value = err.response?.data?.error || "Error saving. Please try again.";
    } finally {
        submitting.value = false;
    }
};
</script>

<style scoped>
@import '../assets/shared.css';
</style>

```

---

### FILE: frontend\src\views\ConsensFullPage.vue
```
<template>
    <div class="page-container">
        <div class="card">
            <button class="back-btn" @click="router.back()">← Back</button>

            <h1>Informed Consent</h1>
            <p class="subtitle">Full informed consent document. Please read carefully.</p>

            <div class="scroll-box">
                <p v-if="loading" class="state-text">Loading...</p>
                <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
                <p v-else class="consent-body">{{ consentText }}</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../axios';

const route = useRoute();
const router = useRouter();

const pid = localStorage.getItem('prolific_pid');
const projectId = route.query.project_id ?? localStorage.getItem('project_id');
const projectSlug = route.query.project_slug ?? localStorage.getItem('project_slug');

const consentText = ref('');
const loading = ref(true);
const errorMsg = ref('');

const getConsent = async () => {
    try {
        const res = await api.get('get-consent/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });
        consentText.value = res.data.consent_text;
    } catch (err) {
        errorMsg.value = "Error getting consent. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(getConsent);
</script>

<style scoped>
.page-container {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    height: 100vh;
    overflow: hidden;
    padding: 50px 20px;
    box-sizing: border-box;
    background-color: #f0f2f5;
}

.card {
    background: white;
    padding: 40px;
    width: 100%;
    max-width: 760px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.back-btn {
    background: none;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 0.88rem;
    color: #555;
    margin-bottom: 24px;
    transition: background 0.2s, border-color 0.2s;
}

.back-btn:hover {
    background: #f5f5f5;
    border-color: #bbb;
}

h1 {
    margin: 0 0 6px;
    font-size: 1.6rem;
    color: #1a1a2e;
}

.subtitle {
    color: #666;
    margin: 0 0 20px;
    font-size: 0.95rem;
}

.scroll-box {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 20px 24px;
    background: #fafafa;
    max-height: 70vh;
    overflow-y: auto;
}

.consent-body {
    margin: 0;
    line-height: 1.8;
    color: #333;
    font-size: 0.95rem;
    white-space: pre-wrap;
}

.state-text {
    margin: 0;
    color: #999;
    font-style: italic;
}

.error {
    color: #dc3545;
}
</style>

```

---

### FILE: frontend\src\views\ConsentView.vue
```
<template>
    <div class="page-container">
        <div class="card">
            <h1>Informed Consent</h1>
            <p class="subtitle">Please read the following information carefully before proceeding.</p>

            <div class="scroll-box">
                <p v-if="loading" class="state-text">Loading...</p>
                <p v-else-if="errorMsg" class="error">{{ errorMsg }}</p>
                <p v-else class="consent-body">{{ truncatedConsent }}</p>
            </div>

            <a v-if="isLong" class="read-more-link" @click="full_consent_form_url">
                Read the full consent form →
            </a>

            <div class="actions">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="accepted">
                    I have read and understood the information above.
                </label>
                <button @click="submitConsent" :disabled="!accepted">I Agree</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';

const router = useRouter();
const route = useRoute();

const accepted = ref(false);
const pid = localStorage.getItem('prolific_pid');
const projectId = route.query.project_id ?? localStorage.getItem('project_id');
const projectSlug = route.params.projectSlug ?? localStorage.getItem('project_slug');

const consentText = ref('');
const loading = ref(true);
const errorMsg = ref('');

const TRUNCATE_LIMIT = 500;
const isLong = computed(() => consentText.value.length > TRUNCATE_LIMIT);
const truncatedConsent = computed(() =>
    isLong.value ? consentText.value.slice(0, TRUNCATE_LIMIT) + '…' : consentText.value
);

const getConsent = async () => {
    try {
        const res = await api.get('get-consent/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });
        consentText.value = res.data.consent_text;
    } catch (err) {
        errorMsg.value = "Error getting consent. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(getConsent);

const full_consent_form_url = () => {
    router.push({ path: '/consent-form', query: { project_id: projectId, project_slug: projectSlug } });
};

const submitConsent = async () => {
    await api.post('consent/', { pid });
    const slug = projectSlug || projectId;
    router.push(`/${slug}/screening`);
};
</script>

<style scoped>
.page-container {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    height: 100vh;
    overflow: hidden;
    padding: 50px 20px;
    box-sizing: border-box;
    background-color: #f0f2f5;
}

.card {
    background: white;
    padding: 40px;
    width: 100%;
    max-width: 640px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

h1 {
    margin: 0 0 6px;
    font-size: 1.6rem;
    color: #1a1a2e;
}

.subtitle {
    color: #666;
    margin: 0 0 20px;
    font-size: 0.95rem;
}

.scroll-box {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 16px 20px;
    background: #fafafa;
    min-height: 120px;
}

.consent-body {
    margin: 0;
    line-height: 1.7;
    color: #333;
    font-size: 0.95rem;
    white-space: pre-wrap;
}

.state-text {
    margin: 0;
    color: #999;
    font-style: italic;
}

.read-more-link {
    display: inline-block;
    margin-top: 10px;
    font-size: 0.88rem;
    color: #007bff;
    cursor: pointer;
    text-decoration: none;
}

.read-more-link:hover {
    text-decoration: underline;
}

.actions {
    margin-top: 28px;
    border-top: 1px solid #eee;
    padding-top: 20px;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    color: #444;
    margin-bottom: 18px;
    cursor: pointer;
}

.checkbox-label input {
    width: 16px;
    height: 16px;
    cursor: pointer;
    flex-shrink: 0;
}

button {
    width: 100%;
    padding: 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
}

button:hover:not(:disabled) {
    background-color: #0069d9;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.error {
    color: #dc3545;
    margin: 0;
}
</style>
```

---

### FILE: frontend\src\views\InstructionsView.vue
```
<template>
    <div class="page-container">
        <!-- LOADING -->
        <div v-if="loading" class="card wide center-content">
            <div class="loader"></div>
            <p class="state-text">Loading instructions...</p>
        </div>

        <!-- ERROR -->
        <div v-else-if="errorMsg" class="card wide">
            <p class="error">{{ errorMsg }}</p>
        </div>

        <!-- SKIP -->
        <div v-else-if="shouldSkip" class="card wide center-content">
            <p class="state-text">No instructions for this project. Redirecting...</p>
        </div>

        <!-- PHASE 1: READ INSTRUCTIONS -->
        <div v-else-if="phase === 'instructions'" class="card wide">
            <div class="card-header">
                <h1>📝 Task Instructions</h1>
                <p class="subtitle">Please read the following instructions carefully before starting.</p>
            </div>

            <div class="markdown-body" v-html="rendered"></div>

            <div class="actions">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="hasReadInstructions">
                    I have read and understood the instructions above.
                </label>
                <button @click="goToPracticeOrFinish" :disabled="!hasReadInstructions">
                    {{ hasPractice ? 'Continue to Practice Task' : 'Start Task' }}
                </button>
            </div>
        </div>

        <!-- PHASE 2: PRACTICE TASK -->
        <div v-else-if="phase === 'practice'" class="task-card">
            <div class="practice-banner" :class="practiceTaskRequired ? 'practice-banner-required' : ''">
                🎯 PRACTICE TASK — {{ practiceTaskRequired ? '⚠️ You must pass this task to proceed' : 'Try annotating this example before starting the real task' }}
            </div>

            <div class="card-header highlight-header">
                <div class="instruction-box flex-guide">
                    <div class="task-instructions-text">
                        <h3>Practice Task</h3>
                        <p>{{ taskConfig.instruction || `Read the text below and complete the tasks, then submit to see
                            feedback.` }}
                        </p>
                    </div>

                    <div class="technical-mini-guide">
                        <h5>How to annotate:</h5>
                        <ul>
                            <li><span class="step-icon">1</span> <strong>Highlight:</strong> Click &amp; drag over text</li>
                            <li><span class="step-icon">2</span> <strong>Label:</strong> Click a colored button</li>
                            <li><span class="step-icon">3</span> <strong>Remove:</strong> Click an existing highlight
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="card-body">
                <!-- Text Highlighter or plain text -->
                <div class="section" v-if="spanLabels.length > 0">
                    <TextHighlighter :text="practiceTask.text" :labels="spanLabels" v-model:spans="practiceSpans" />
                </div>
                <div class="doc-text-preview" v-else>
                    {{ practiceTask.text }}
                </div>

                <!-- Classification -->
                <div class="section classification-section" v-if="classOptions.length > 0">
                    <div class="question-title">
                        {{ taskConfig.question || "Classify this text:" }}
                    </div>
                    <div class="options-grid">
                        <label v-for="opt in classOptions" :key="opt.value" class="option-label"
                            :class="{ active: practiceClassification === opt.value }">
                            <input type="radio" :value="opt.value" v-model="practiceClassification">
                            <span class="check-icon"></span>
                            {{ opt.label }}
                        </label>
                    </div>
                </div>
            </div>

            <!-- ACTIONS -->
            <div class="card-footer actions" v-if="!showFeedback">
                <button class="action-btn clear-btn" @click="clearPractice">Clear</button>
                <button class="submit-btn primary-submit" @click="checkPractice" :disabled="!canSubmitPractice">
                    Submit Practice
                </button>
            </div>

            <!-- FEEDBACK -->
            <div v-if="showFeedback" class="feedback-container">
                <div class="feedback-header" :class="feedbackCorrect ? 'feedback-success' : 'feedback-error'">
                    <span class="feedback-icon">{{ feedbackCorrect ? '✅' : '❌' }}</span>
                    <span class="feedback-title">{{ feedbackCorrect ? `Correct! Well done.` : `Not quite right. Review
                        the feedback below.` }}</span>
                </div>

                <div class="feedback-details">
                    <!-- Classification feedback -->
                    <div v-if="classOptions.length > 0" class="feedback-item">
                        <strong>Classification:</strong>
                        <span v-if="classificationCorrect" class="correct-text">✅ Your answer "{{ practiceClassification
                        }}" is correct.</span>
                        <span v-else class="wrong-text">❌ You selected "{{ practiceClassification || `nothing` }}" — the
                            correct answer is
                            "{{ goldSolution.classification }}".</span>
                    </div>

                    <!-- Spans feedback -->
                    <div v-if="spanLabels.length > 0" class="feedback-item">
                        <strong>Highlights:</strong>
                        <div class="spans-feedback">
                            <div v-for="(gs, i) in (goldSolution.spans || [])" :key="i" class="span-feedback-row">
                                <span class="badge" :style="{ background: getLabelColor(gs.label) }">{{ gs.label
                                }}</span>
                                <span v-if="matchedSpans[i]" class="correct-text">✅ "{{ gs.text }}"</span>
                                <span v-else class="wrong-text">❌ Missing: "{{ gs.text }}"</span>
                            </div>
                        </div>
                    </div>

                    <!-- Hints -->
                    <div v-if="practiceTask.hints && practiceTask.hints.length > 0" class="hints-section">
                        <strong>💡 Hints:</strong>
                        <ul class="hints-list">
                            <li v-for="(hint, i) in practiceTask.hints" :key="i">{{ hint }}</li>
                        </ul>
                    </div>
                </div>

                <div class="feedback-actions">
                    <button v-if="!feedbackCorrect" class="action-btn retry-btn" @click="retryPractice">
                        🔄 Try Again
                    </button>
                    <!-- Skip only shown if practice is NOT required, or if they got it correct -->
                    <button
                        v-if="!practiceTaskRequired || feedbackCorrect"
                        class="submit-btn primary-submit"
                        @click="finishInstructions"
                        :disabled="practiceTaskRequired && !feedbackCorrect"
                    >
                        {{ feedbackCorrect ? '🚀 Start Real Task' : 'Skip & Start Task Anyway' }}
                    </button>
                    <p v-if="practiceTaskRequired && !feedbackCorrect" class="required-notice">
                        🔒 This practice task is mandatory. Please try again until you get it right.
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import TextHighlighter from '../components/TextHighlighter.vue';
import { useProjectContext } from '../composables/useProjectContext';
import { useMarkdownRenderer } from '../composables/useMarkdownRenderer';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

// State
const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const phase = ref('instructions'); // 'instructions' | 'practice'
const practiceTaskRequired = ref(false);
const hasReadInstructions = ref(false);

// Instructions content
const rawInstructions = ref('');
const practiceTask = ref(null);
const taskConfig = ref({});

// Practice state
const practiceSpans = ref([]);
const practiceClassification = ref(null);
const showFeedback = ref(false);
const feedbackCorrect = ref(false);
const classificationCorrect = ref(false);
const matchedSpans = ref([]);

// Derived from config
const spanLabels = computed(() => taskConfig.value.span_labels || []);
const classOptions = computed(() => taskConfig.value.class_labels || []);
const hasPractice = computed(() => practiceTask.value && practiceTask.value.text);
const goldSolution = computed(() => (practiceTask.value && practiceTask.value.gold_solution) || {});

const canSubmitPractice = computed(() => {
    if (classOptions.value.length > 0) {
        return practiceClassification.value !== null;
    }
    return true;
});

const { rendered } = useMarkdownRenderer(rawInstructions);

// Fetch data
const fetchInstructions = async () => {
    try {
        const res = await api.get('get-instructions/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            await api.post('onboarding/', { pid, project_slug: projectSlug, project_id: projectId });
            setTimeout(() => router.push(`/${slug}/annotate`), 500);
            return;
        }

        rawInstructions.value = res.data.content || '';
        practiceTask.value = res.data.practice_task || null;
        practiceTaskRequired.value = res.data.practice_task_required || false;
        taskConfig.value = res.data.task_config || {};
    } catch (err) {
        errorMsg.value = "Error loading instructions. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (!pid) {
        router.push('/');
        return;
    }
    fetchInstructions();
});

// Navigation
const goToPracticeOrFinish = () => {
    if (hasPractice.value) {
        phase.value = 'practice';
    } else {
        finishInstructions();
    }
};

const getLabelColor = (labelName) => {
    const l = spanLabels.value.find(x => x.name === labelName);
    return l ? l.color : '#cbd5e1';
};

// Practice evaluation
const checkPractice = () => {
    const gold = goldSolution.value;

    classificationCorrect.value = !classOptions.value.length || practiceClassification.value === gold.classification;

    const goldSpans = gold.spans || [];
    matchedSpans.value = goldSpans.map(gs => {
        return practiceSpans.value.some(ps =>
            ps.label === gs.label &&
            Math.abs(ps.start - gs.start) <= 5 &&
            Math.abs(ps.end - gs.end) <= 5
        );
    });

    const allSpansCorrect = matchedSpans.value.every(m => m);
    feedbackCorrect.value = classificationCorrect.value && (goldSpans.length === 0 || allSpansCorrect);
    showFeedback.value = true;
};

const clearPractice = () => {
    practiceSpans.value = [];
    practiceClassification.value = null;
};

const retryPractice = () => {
    clearPractice();
    showFeedback.value = false;
    feedbackCorrect.value = false;
};

const finishInstructions = async () => {
    try {
        await api.post('onboarding/', {
            pid,
            project_slug: projectSlug,
            project_id: projectId
        });
        const slug = projectSlug || projectId;
        router.push(`/${slug}/annotate`);
    } catch (err) {
        errorMsg.value = "Error saving. Please try again.";
    }
};
</script>

<style scoped>
@import '../assets/shared.css';

/* ── TASK CARD (più larga della card standard) ── */
.task-card {
    background: white;
    max-width: 1000px;
    margin: 0 auto;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.highlight-header {
    background-color: #f8fafc;
}

.flex-guide {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 30px;
}

.task-instructions-text {
    flex: 1;
}

.technical-mini-guide {
    background: #fff;
    border: 1px solid #e2e8f0;
    padding: 15px;
    border-radius: 12px;
    width: 280px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.technical-mini-guide h5 {
    margin: 0 0 10px 0;
    font-size: 0.9rem;
    color: #1a1f36;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.technical-mini-guide ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.technical-mini-guide li {
    font-size: 0.85rem;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #4f566b;
}

.step-icon {
    background: #306ee8;
    color: white;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    flex-shrink: 0;
}

/* ── PRACTICE BANNER ── */
.practice-banner {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 14px;
    text-align: center;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
}

.practice-banner-required {
    background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
}

.required-notice {
    margin: 12px 0 0;
    padding: 10px 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    color: #991b1b;
    font-size: 0.9rem;
    font-weight: 500;
    text-align: center;
    width: 100%;
}

/* ── FEEDBACK ── */
.feedback-container {
    border-top: 2px solid #e3e8ee;
    animation: slideUp 0.4s ease-out;
}

.feedback-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 30px;
    font-weight: 700;
    font-size: 1.05rem;
}

.feedback-success {
    background: #ecfdf5;
    color: #065f46;
    border-bottom: 2px solid #a7f3d0;
}

.feedback-error {
    background: #fef2f2;
    color: #991b1b;
    border-bottom: 2px solid #fecaca;
}

.feedback-icon {
    font-size: 1.4rem;
}

.feedback-details {
    padding: 24px 30px;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.feedback-item {
    font-size: 0.95rem;
    line-height: 1.6;
}

.correct-text { color: #065f46; }
.wrong-text { color: #991b1b; }

.spans-feedback {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.span-feedback-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.badge {
    color: white;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    min-width: 60px;
    text-align: center;
}

.hints-section {
    margin-top: 8px;
    padding: 16px;
    background: #fffbeb;
    border-radius: 10px;
    border-left: 4px solid #f59e0b;
}

.hints-list {
    margin: 8px 0 0 0;
    padding-left: 20px;
}

.hints-list li {
    margin: 6px 0;
    color: #78350f;
    font-size: 0.9rem;
}

.feedback-actions {
    padding: 20px 30px;
    background: #f8fafc;
    display: flex;
    justify-content: flex-end;
    gap: 15px;
}

.retry-btn {
    background: #fef3c7;
    color: #92400e;
    font-weight: 700;
}

.retry-btn:hover {
    background: #fde68a;
}
</style>
```

---

### FILE: frontend\src\views\LoginView.vue
```
<template>
    <div class="login-container">
        <div class="card">
            <h1>Annotation Task</h1>
            <p class="subtitle">Please join from your Prolific account with ID and project ID in the URL to start the
                annotation task.
            </p>
            <p v-if="(!projectId && !projectSlug) || !prolificPid" class="error-text">⚠️ Warning: Missing Parameters in URL</p>
            <p v-if="!projectId && !projectSlug" class="error-text small">No Project ID or Slug found</p>
            <p v-if="!prolificPid" class="error-text small">No Prolific ID found</p>
            <p v-if="prolificPid && prolificPid.length <= 3" class="error-text small">⚠️ Prolific ID is too short
                (minimum 4 characters)</p>

            <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';

const router = useRouter();
const route = useRoute();

const prolificPid = ref('');
const projectId = ref(null);

const isLoading = ref(false);
const projectSlug = ref(null);
const errorMessage = ref('');

const startSession = async () => {
    if (!isValid.value) return;

    isLoading.value = true;
    errorMessage.value = '';

    try {
        // Collect all query parameters as metadata, but exclude internal/redundant keys
        const metadata = { ...route.query };
        delete metadata.project_id;
        delete metadata.project_slug;
        delete metadata.PROLIFIC_PID;

        const response = await api.post('session/', {
            prolific_pid: prolificPid.value,
            project_id: projectId.value,
            project_slug: projectSlug.value,
            metadata: metadata
        });

        // Salvataggio dati critici
        localStorage.setItem('prolific_pid', prolificPid.value);
        if (projectId.value) localStorage.setItem('project_id', projectId.value);
        if (projectSlug.value) localStorage.setItem('project_slug', projectSlug.value);

        // Routing
        const step = response.data.step;
        const slug = projectSlug.value || projectId.value; // Fallback if no slug

        if (step === 'CONSENT') router.push(`/${slug}/consent`);
        else if (step === 'SCREENING') router.push(`/${slug}/screening`);
        else if (step === 'CODEBOOK') router.push(`/${slug}/codebook`);
        else if (step === 'INSTRUCTIONS') router.push(`/${slug}/instructions`);
        else if (step === 'ONBOARDING') router.push(`/${slug}/instructions`);
        else if (step === 'ANNOTATION') router.push(`/${slug}/annotate`);
        else if (step === 'COMPLETED') router.push(`/${slug}/annotate`);

    } catch (err) {
        if (err.response && err.response.status === 404) {
            errorMessage.value = "Project not found or inactive. Please contact the administrator.";
        } else if (err.response && err.response.data && err.response.data.error) {
            errorMessage.value = err.response.data.error;
        } else {
            errorMessage.value = "Connection error. Please check your internet or retry later.";
        }
        console.error("Login Error:", err);
    } finally {
        isLoading.value = false;
    }
};

onMounted(() => {
    // 1. Cerca il projectSlug nei parametri del percorso (es. /nome-studio)
    if (route.params.projectSlug) {
        projectSlug.value = route.params.projectSlug;
        localStorage.setItem('project_slug', projectSlug.value);
    } else if (route.query.project_id) {
        // Fallback: cerca il project_id nella query string (es. ?project_id=1)
        projectId.value = route.query.project_id;
        localStorage.setItem('project_id', projectId.value);
    } else {
        // Fallback: prova a vedere se erano salvati in precedenza
        const savedSlug = localStorage.getItem('project_slug');
        if (savedSlug) projectSlug.value = savedSlug;

        const savedId = localStorage.getItem('project_id');
        if (savedId) projectId.value = savedId;
    }

    // Auto-fill PID se presente nell'URL (comodo per Prolific)
    if (route.query.PROLIFIC_PID) {
        prolificPid.value = route.query.PROLIFIC_PID;
    }

    // Auto-login if we have everything
    if (isValid.value) {
        startSession();
    }
});

const isValid = computed(() => {
    return prolificPid.value.length > 3 && (projectId.value || projectSlug.value);
});

</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #f0f2f5;
}

.card {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
    text-align: center;
}

.subtitle {
    color: #666;
    margin-bottom: 2rem;
}

.form-group {
    margin-bottom: 1.5rem;
    text-align: left;
}

input {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    box-sizing: border-box;
    /* Important for padding */
}

button {
    width: 100%;
    padding: 12px;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

button:hover:not(:disabled) {
    background-color: #3aa876;
}

.error {
    color: red;
    margin-top: 10px;
    font-size: 0.9rem;
}
</style>
```

---

### FILE: frontend\src\views\ScreeningView.vue
```
<template>
    <div class="page-container">
        <div class="card wide">
            <div class="card-header">
                <h1>About You</h1>
                <p class="subtitle">Please answer the following questions before starting the task.</p>
            </div>

            <div v-if="loading" class="state-text" style="padding: 30px 40px;">Loading screening...</div>
            <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
            <div v-else-if="shouldSkip" class="state-text" style="padding: 30px 40px;">No screening required. Redirecting...</div>

            <div v-else class="questions-container">
                <div v-for="(q, index) in questions" :key="q.id" class="question-block">
                    <label class="question-label">
                        <span class="question-number">{{ index + 1 }}.</span>
                        {{ q.label }}
                        <span v-if="q.required" class="required-star">*</span>
                    </label>

                    <!-- TEXT -->
                    <input v-if="q.type === 'text'" type="text" v-model="responses[q.id]"
                        :placeholder="q.placeholder || ''" class="input-field" />

                    <!-- NUMBER -->
                    <input v-if="q.type === 'number'" type="number" v-model.number="responses[q.id]" :min="q.min"
                        :max="q.max" :placeholder="q.placeholder || ''" class="input-field" />

                    <!-- TEXTAREA -->
                    <textarea v-if="q.type === 'textarea'" v-model="responses[q.id]" :placeholder="q.placeholder || ''"
                        class="input-field textarea-field" rows="3"></textarea>

                    <!-- SELECT -->
                    <select v-if="q.type === 'select'" v-model="responses[q.id]" class="input-field">
                        <option value="" disabled>Select an option...</option>
                        <option v-for="opt in q.options" :key="opt" :value="opt">{{ opt }}</option>
                    </select>

                    <!-- RADIO -->
                    <div v-if="q.type === 'radio'" class="options-group">
                        <label v-for="opt in q.options" :key="opt" class="radio-label"
                            :class="{ active: responses[q.id] === opt }">
                            <input type="radio" :value="opt" v-model="responses[q.id]" />
                            {{ opt }}
                        </label>
                    </div>

                    <!-- MULTI_SELECT -->
                    <div v-if="q.type === 'multi_select'" class="options-group">
                        <label v-for="opt in q.options" :key="opt" class="checkbox-label-option"
                            :class="{ active: (responses[q.id] || []).includes(opt) }">
                            <input type="checkbox" :value="opt" v-model="responses[q.id]" />
                            {{ opt }}
                        </label>
                    </div>

                    <!-- LIKERT -->
                    <div v-if="q.type === 'likert'" class="likert-container">
                        <span class="likert-anchor">{{ (q.anchors && q.anchors[0]) || '1' }}</span>
                        <div class="likert-scale">
                            <label v-for="n in (q.scale || 5)" :key="n" class="likert-option"
                                :class="{ active: responses[q.id] === n }">
                                <input type="radio" :value="n" v-model="responses[q.id]" />
                                {{ n }}
                            </label>
                        </div>
                        <span class="likert-anchor">{{ (q.anchors && q.anchors[1]) || (q.scale || 5) }}</span>
                    </div>
                </div>
            </div>

            <div v-if="!loading && !shouldSkip && questions.length > 0" class="actions">
                <p v-if="validationError" class="validation-error">{{ validationError }}</p>
                <button @click="submitScreening" :disabled="submitting">
                    {{ submitting ? 'Saving...' : 'Continue' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import { useProjectContext } from '../composables/useProjectContext';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const submitting = ref(false);
const validationError = ref('');

const questions = ref([]);
const responses = reactive({});

const fetchScreening = async () => {
    try {
        const res = await api.get('get-screening/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            setTimeout(() => router.push(`/${slug}/instructions`), 500);
            return;
        }

        questions.value = res.data.questions || [];

        for (const q of questions.value) {
            if (q.type === 'multi_select') {
                responses[q.id] = [];
            } else {
                responses[q.id] = q.type === 'number' ? null : '';
            }
        }
    } catch (err) {
        if (err.response?.status === 400 && err.response?.data?.error === 'Screening already completed') {
            const slug = projectSlug || projectId;
            router.push(`/${slug}/codebook`);
            return;
        }
        errorMsg.value = "Error loading screening. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (!pid) {
        router.push('/');
        return;
    }
    fetchScreening();
});

const submitScreening = async () => {
    validationError.value = '';

    for (const q of questions.value) {
        if (q.required) {
            const val = responses[q.id];
            if (val === null || val === undefined || val === '') {
                validationError.value = `Please answer: "${q.label}"`;
                return;
            }
            if (Array.isArray(val) && val.length === 0) {
                validationError.value = `Please select at least one option for: "${q.label}"`;
                return;
            }
        }
    }

    submitting.value = true;

    try {
        await api.post('screening/', {
            pid,
            project_slug: projectSlug,
            project_id: projectId,
            responses: { ...responses }
        });

        const slug = projectSlug || projectId;
        router.push(`/${slug}/codebook`);
    } catch (err) {
        validationError.value = err.response?.data?.error || "Error saving screening. Please try again.";
    } finally {
        submitting.value = false;
    }
};
</script>

<style scoped>
@import '../assets/shared.css';

/* ── QUESTIONS ── */
.questions-container {
    display: flex;
    flex-direction: column;
    gap: 28px;
    padding: 30px 40px;
}

.question-block {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.question-label {
    font-weight: 600;
    font-size: 1rem;
    color: #1a1f36;
    display: flex;
    align-items: baseline;
    gap: 6px;
}

.question-number {
    color: #306ee8;
    font-weight: 700;
    min-width: 20px;
}

.required-star {
    color: #dc2626;
    font-weight: 700;
}

/* ── INPUT FIELDS ── */
.input-field {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e3e8ee;
    border-radius: 10px;
    font-size: 0.95rem;
    font-family: 'Outfit', sans-serif;
    transition: all 0.2s;
    box-sizing: border-box;
    background: #f8fafc;
    color: #1a1f36;
}

.input-field:focus {
    outline: none;
    border-color: #306ee8;
    background: white;
    box-shadow: 0 0 0 3px rgba(48, 110, 232, 0.1);
}

.textarea-field {
    resize: vertical;
    min-height: 80px;
}

select.input-field {
    appearance: auto;
    cursor: pointer;
}

/* ── RADIO & CHECKBOX OPTIONS ── */
.options-group {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.radio-label,
.checkbox-label-option {
    background: #f8fafc;
    border: 2px solid #e3e8ee;
    padding: 10px 20px;
    border-radius: 10px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
    font-size: 0.9rem;
}

.radio-label:hover,
.checkbox-label-option:hover {
    border-color: #cbd5e1;
    background: white;
}

.radio-label.active,
.checkbox-label-option.active {
    background: #306ee8;
    color: white;
    border-color: #1a4ab9;
    box-shadow: 0 4px 12px rgba(48, 110, 232, 0.25);
}

.radio-label input,
.checkbox-label-option input {
    display: none;
}

/* ── LIKERT SCALE ── */
.likert-container {
    display: flex;
    align-items: center;
    gap: 12px;
}

.likert-anchor {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
    min-width: 60px;
    text-align: center;
}

.likert-scale {
    display: flex;
    gap: 8px;
    flex: 1;
    justify-content: center;
}

.likert-option {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #e3e8ee;
    border-radius: 50%;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    background: #f8fafc;
    color: #475569;
}

.likert-option:hover {
    border-color: #306ee8;
    background: #eff6ff;
}

.likert-option.active {
    background: #306ee8;
    color: white;
    border-color: #1a4ab9;
    box-shadow: 0 4px 12px rgba(48, 110, 232, 0.3);
    transform: scale(1.1);
}

.likert-option input {
    display: none;
}

/* ── VALIDATION ── */
.validation-error {
    color: #dc2626;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 12px;
    padding: 10px 16px;
    background: #fef2f2;
    border-radius: 8px;
    border-left: 4px solid #dc2626;
}
</style>

```

---

### FILE: tmp\create_context.py
```
import os

def create_context_file(root_dir, output_file):
    exclude_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', '.next', '.gemini', '.vscode', 'config_uploads', 'datasets'}
    exclude_files = {'package-lock.json', 'yarn.lock', 'db.sqlite3', 'mace_test_out.txt', 'train_redacted.jsonl'}
    allowed_extensions = {'.py', '.js', '.ts', '.tsx', '.vue', '.html', '.css', '.scss', '.md', '.yml', '.yaml', '.json', '.sh', '.bat', '.env', '.dockerignore', 'Dockerfile'}

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# FULL CODEBASE CONTEXT\n\n")
        f.write("## DIRECTORY STRUCTURE\n")
        
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            level = root.replace(root_dir, '').count(os.sep)
            indent = '  ' * level
            f.write(f"{indent}- {os.path.basename(root)}/\n")
            sub_indent = '  ' * (level + 1)
            for file in files:
                if file not in exclude_files:
                    f.write(f"{sub_indent}- {file}\n")
        
        f.write("\n---\n\n")
        f.write("## FILE CONTENTS\n\n")

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files:
                    continue
                
                ext = os.path.splitext(file)[1].lower()
                if ext not in allowed_extensions and file not in allowed_extensions: # handle Dockerfile etc
                     if not any(file.startswith(p) for p in ['Dockerfile', '.env']):
                         continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as content_file:
                        content = content_file.read()
                    
                    f.write(f"### FILE: {rel_path}\n")
                    f.write(f"```\n{content}\n```\n\n")
                    f.write("---\n\n")
                except Exception as e:
                    f.write(f"### FILE: {rel_path} (ERROR READING: {e})\n\n---\n\n")

if __name__ == "__main__":
    root = r"c:\Users\magut\Desktop\github-repos\cospiracy-fullstack"
    output = os.path.join(root, "full_codebase_context.md")
    create_context_file(root, output)
    print(f"Context file created at: {output}")

```

---

