#!/bin/sh
# entrypoint.sh — Docker-only startup script
# This script runs migrations and collectstatic before starting gunicorn.
# It does NOT affect local development (manage.py runserver).

set -e

echo "⏳ Waiting for database..."
while ! python manage.py check --database default > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Database is ready."

echo "📦 Applying migrations..."
python manage.py migrate --noinput

echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting gunicorn..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000
