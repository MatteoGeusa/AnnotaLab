Per fare il deploy
Aggiorna il .env con i valori di produzione (ALLOWED_HOSTS, SECRET_KEY, CORS ecc.)

Poi lancia:
docker compose -f docker-compose-fullstack.yml up --build -d

Per sviluppare in locale (invariato)

Per eseguire comandi Django dentro Docker usa docker exec:

Creare un superuser:
docker exec -it annotalab-backend-1 python manage.py createsuperuser

Applicare migrazioni:
docker exec -it annotalab-backend-1 python manage.py migrate

Creare nuove migrazioni:
docker exec -it annotalab-backend-1 python manage.py makemigrations

Shell Django:
docker exec -it annotalab-backend-1 python manage.py shell

Entrare nel container con bash:
docker exec -it annotalab-backend-1 bash

Il -it serve per i comandi interattivi (come createsuperuser che chiede username e password).
