@echo off
start "Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe manage.py runserver"
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
