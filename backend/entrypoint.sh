#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time
import urllib.parse

url = os.environ.get("DATABASE_URL", "")
parsed = urllib.parse.urlparse(url.replace("postgresql+psycopg", "postgresql"))
host = parsed.hostname or "postgres"
port = parsed.port or 5432

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"database {host}:{port} is up")
            break
    except OSError:
        print(f"waiting for database {host}:{port} ...")
        time.sleep(2)
else:
    raise SystemExit("database never became reachable")
PY

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
