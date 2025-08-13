#!/bin/sh
set -e

# Use the PORT environment variable if it's set, otherwise default to 5000
APP_PORT=${PORT:-5000}

# Execute the Gunicorn server
exec gunicorn \
    --bind "0.0.0.0:${APP_PORT}" \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 120 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    "src.main:app"
