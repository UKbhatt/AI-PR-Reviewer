@echo off
REM Script to force restart Celery worker by clearing all tasks first
echo Stopping any running Celery workers...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq celery*" 2>nul
timeout /t 2 /nobreak >nul

echo Clearing Celery queue...
python clear_celery_queue.py

echo Cleaning up corrupted tasks...
python cleanup_corrupted_tasks.py

echo.
echo Starting Celery worker...
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis --pool=solo
pause

