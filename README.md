Per fare il deploy
Aggiorna il .env con i valori di produzione (ALLOWED_HOSTS, SECRET_KEY, CORS ecc.)

Poi lancia:
docker compose -f docker-compose-fullstack.yml up --build -d

Per sviluppare in locale (invariato):
make dev
