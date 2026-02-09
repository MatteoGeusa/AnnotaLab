# Django REST API + Vue 3 Frontend (Full Stack)

FORK da [https://github.com/MatteoGeusa/Django-REST-full](https://github.com/MatteoGeusa/Django-REST-full) creata da Matteo Geusa.

Questo repository contiene un'applicazione full-stack moderna composta da:

- **Backend**: Django REST Framework (Python)
- **Frontend**: Vue 3 + TypeScript + Vite
- **Database**: PostgreSQL
- **Infrastruttura**: Docker & Docker Compose

## 📂 Struttura del Progetto

- `/backend`: Codice sorgente Django.
- `/frontend`: Codice sorgente Vue.js.
- `docker-compose-*.yml`: File di configurazione per i vari scenari di avvio con Docker.
- `.env`: Variabili d'ambiente per la configurazione.

---

## 🚀 Prerequisiti

Assicurati di avere installato:

1. **Docker Desktop** (per il database e containerizzazione)
2. **Python 3.10+** (per il backend locale)
3. **Node.js 18+ & npm** (per il frontend)

---

## ⚙️ Configurazione Iniziale

### 1. File `.env`

Assicurati di avere un file `.env` nella root del progetto. Puoi usare `.env.example` come base.
Assicurati che `POSTGRES_HOST=127.0.0.1` se esegui il backend in locale (fuori da Docker), oppure `POSTGRES_HOST=db` se il backend gira dentro Docker.

### 2. Configurazione Backend (Locale)

Se vuoi sviluppare con l'hot-reload sul backend:

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Su Windows
# source venv/bin/activate  # Su Mac/Linux

pip install -r requirements.txt
python manage.py migrate
```

### 3. Configurazione Frontend (Locale)

Per installare le dipendenze del frontend:

```bash
cd frontend
npm install
```

---

## 🛠️ Modalità di Sviluppo (Consigliata)

Questa modalità ti permette di avere **Hot Reload** sia su Backend che su Frontend, usando Docker solo per il Database.

### Passo 1: Avvia il Database (Docker)

Dalla cartella principale:

```powershell
# Avvia solo il database PostgreSQL
docker compose -f docker-compose-only-db.yaml up -d
```

*Nota: Assicurati che nel backend `.env` sia impostato `POSTGRES_HOST=127.0.0.1`.*

### Passo 2: Avvia il Backend (Terminale 1)

```powershell
cd backend
.\venv\Scripts\activate
python manage.py runserver
```

Il backend sarà attivo su `http://localhost:8000`.

### Passo 3: Avvia il Frontend (Terminale 2)

```powershell
cd frontend
npm run dev
```

Il frontend sarà accessibile (di solito) su `http://localhost:5173`.

---

## 🐳 Altre Modalità di Avvio con Docker

### Scenario B: Backend in Docker + Frontend Locale

Utile se non vuoi installare Python/librerie localmente ma vuoi lavorare sul frontend.

1. Assicurati che nel `.env` sia impostato `POSTGRES_HOST=db`.
2. Avvia Backend + DB:

    ```powershell
    docker compose -f docker-compose-only-backend.yaml up --build -d
    ```

3. Avvia il Frontend localmente:

    ```powershell
    cd frontend
    npm run dev
    ```

### Scenario C: Full Stack in Docker (Produzione/Test)

Avvia tutto (DB, Backend, Frontend compilato servito da Nginx) dentro i container.

1. Assicurati che nel `.env` sia impostato `POSTGRES_HOST=db`.
2. Avvia tutto:

    ```powershell
    docker compose -f docker-compose-selfthosted-db.yml up --build -d
    ```

3. L'applicazione sarà accessibile su `http://localhost` (porta 80).

---

## 📝 Comandi Utili

### Backend

- **Creare Migrazioni**: `python manage.py makemigrations`
- **Applicare Migrazioni**: `python manage.py migrate`
- **Creare Superuser**: `python manage.py createsuperuser`

### Docker

- **Fermare i container**: `docker compose down`
- **Vedere i log**: `docker compose logs -f`
- **Riavviare un servizio**: `docker compose restart <nome_servizio>`
