# AnnotaLab: Advanced Textual Annotation Platform

A fullstack solution designed for researchers to collect textual annotations from annotators (e.g., Prolific).

---

## 🚀 Quickstart

### Prerequisites

- **Docker & Docker Compose** (Recommended)
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** (Supabase or local)

### 🐳 Docker Configuration

The project provides multiple Docker setups depending on your environment:

```bash
# Local Development (Database Only)
docker compose -f 'docker-compose-only-db.yaml' up -d --build 'db'

# Fullstack (Database + Backend + Frontend)
docker compose -f 'docker-compose-fullstack.yaml' up -d --build

# Backend + Frontend (Connected to External/Supabase DB)
docker compose -f 'docker-compose-supabase-setup.yml' up -d --build
```

### 🐍 Backend Setup (Local Development)

```bash
cd backend
python -m venv venv
# Activate on Windows: .\venv\Scripts\Activate
# Activate on Unix: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### ⚛️ Frontend Setup (Local Development)

```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 System Overview

The platform enables researchers to manage complex annotation tasks (Sentiment, NER, Conspiracy Theories) without manual code changes. Interface configuration, labels, and distribution logic are defined dynamically per **Project** via the Admin Panel.

### Annotator Pipeline

The system guides participants through a structured workflow:

1.  **Informed Consent**: Mandatory legal agreement page.
2.  **Screening (Demographics)**: Real-time validation of participant profile and metadata collection.
3.  **Codebook**: Theoretical training material and definitions (Markdown supported).
4.  **Instructions & Practice**: Hands-on guide with immediate feedback on pilot tasks.
5.  **Real Annotation**: Continuous document stream with integrated **Gold Units** for quality control.
6.  **Completion**: Automatic redirection to Prolific with completion verification codes.

---

## 🛠️ Advanced Features & Architecture

### 1. "No-Code" Task Configuration

Researchers can configure projects directly from the Admin to define:

- **Task Type**: Support for Classification, NER, or Hybrid tasks.
- **Dynamic Interface**: Custom labels, color palettes, hover hints, and multiple-choice questions.
- **Modular Workflow**: Enable or disable screening, codebook, or practice phases independently for each project.

### 2. Distribution Strategies (Redundant Management)

Three assignment modes to optimize for cost, speed, or reliability:

- **STANDARD**: Documents are pseudo-randomly assigned to annotators until reaching the `max_annotations_per_doc` limit.
- **FULL_OVERLAP**: Every annotator sees every document in the project. Ideal for inter-annotator agreement (IAA) calculations.
- **SAME_ANNOTATORS (Block-based)**: Documents are divided into blocks. Each block is assigned to exactly _k_ fixed annotators. Essential for controlled reliability studies.

### 3. Quality Control (QC) & Bayesian Inferencing

State-of-the-art tools to ensure data integrity and manage noise:

- **Gold Units Injection**: Automatic injection of documents with known solutions. Annotators falling below the accuracy threshold (e.g., 60%) are automatically excluded from the pool.
- **MACE (Multi-Annotator Competence Estimation)**: Integrated Bayesian algorithm that estimates individual competence and deduces the most likely "ground truth" by weighting responses from the most reliable participants.
- **Time Tracking**: Millisecond-level precision tracking for each annotation to identify bots, "click-spamming," or low-effort contributors.

### 4. High-Concurrency Management

To prevent redundancy violations and "double-assignment" in high-traffic scenarios (e.g., hundreds of workers starting simultaneously), the backend implements a **Fetch-then-Lock** pattern using `select_for_update(skip_locked=True)`. This ensures data consistency and high performance under heavy load.

---

## 📊 Core Data Models (`backend/annotation/models.py`)

- **`Project`**: The central campaign container (UI config, distribution strategy, dataset metadata).
- **`Annotator`**: Global participant profile and metadata (e.g., Prolific PID).
- **`ProjectEnrollment`**: Tracks individual progress, gold accuracy, and MACE competence scores per project.
- **`Document`**: The atomic unit of text. Supports **Proxies** to distinguish between Standard Items and Gold Units.
- **`Annotation`**: The final JSON payload containing spans, labels, and execution metrics.

---

## 🔗 Quick Access

- **Admin Panel**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- **Testing Link (Project #1)**: [http://localhost:5173/?PROLIFIC_PID=TEST_USER&project_id=1](http://localhost:5173/?PROLIFIC_PID=TEST_USER&project_id=1)
- **Results Export**: Available directly in the Project List via the `⬇ JSONL` button.
