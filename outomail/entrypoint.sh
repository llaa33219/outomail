#!/bin/bash
set -e

mkdir -p /app/data/certs /app/data/dkim /app/data/mail

if [ ! -f /app/data/certs/cert.pem ] || [ ! -f /app/data/certs/key.pem ]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -newkey rsa:2048 -keyout /app/data/certs/key.pem -out /app/data/certs/cert.pem \
        -days 365 -nodes -subj "/CN=${DOMAIN:-localhost}"
    echo "Certificate generated."
fi

python3 -c "
import http.server, threading, ssl

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get('Host', '${DOMAIN:-localhost}').split(':')[0]
        self.send_response(301)
        self.send_header('Location', f'https://{host}:443{self.path}')
        self.end_headers()
    def log_message(self, format, *args):
        pass

server = http.server.HTTPServer(('0.0.0.0', 80), RedirectHandler)
print('HTTP redirect server started on port 80')
server.serve_forever()
" &

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 443 \
    --ssl-keyfile /app/data/certs/key.pem \
    --ssl-certfile /app/data/certs/cert.pem
