@echo off
REM Windows batch script to start Celery worker with solo pool
echo Starting Celery worker for Windows...
cd /d %~dp0
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis --pool=solo
pause

