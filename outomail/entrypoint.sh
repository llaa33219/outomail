#!/bin/bash
set -e

mkdir -p /app/data/certs /app/data/dkim /app/data/mail

if [ ! -f /app/data/certs/cert.pem ] || [ ! -f /app/data/certs/key.pem ]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -newkey rsa:2048 -keyout /app/data/certs/key.pem -out /app/data/certs/cert.pem \
        -days 365 -nodes -subj "/CN=${DOMAIN:-localhost}"
    echo "Certificate generated."
fi

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 443 \
    --ssl-keyfile /app/data/certs/key.pem \
    --ssl-certfile /app/data/certs/cert.pem
