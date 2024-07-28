#!/bin/bash

# Start the Gunicorn server in the background
gunicorn app:app --bind 0.0.0.0:$PORT &

# Start the Celery worker
celery --app tasks.celery_app worker --loglevel info --concurrency 4