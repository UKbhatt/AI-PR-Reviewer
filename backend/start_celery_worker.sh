#!/bin/bash
# Unix/Linux script to start Celery worker
echo "Starting Celery worker..."
cd "$(dirname "$0")"
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis

