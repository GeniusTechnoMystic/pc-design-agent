#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

DB_URL="${DATABASE_URL:-postgresql://pcagent:pcagent@localhost:5432/pcagent}"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required but not installed. Please install PostgreSQL client tools."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not installed."
  exit 1
fi

DB_NAME="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.path.lstrip('/'))
PY
)"

DB_HOST="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.hostname or 'localhost')
PY
)"

DB_USER="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.username or 'pcagent')
PY
)"

DB_PASS="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.password or 'pcagent')
PY
)"

DB_PORT="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', 'postgresql://pcagent:pcagent@localhost:5432/pcagent')
parsed = urlparse(url)
print(parsed.port or 5432)
PY
)"

PGPASSWORD="$DB_PASS" export PGPASSWORD

echo "Checking database connectivity at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  echo "Postgres not ready yet; retrying in 2 seconds..."
  sleep 2
done

echo "Ensuring database '${DB_NAME}' exists..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1; then
  createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
fi

if [ -d schemas ] && find schemas -maxdepth 1 -type f -name '*.sql' | grep -q .; then
  echo "Found SQL schema files. Running entrypoint scripts if available..."
  for sql_file in schemas/*.sql; do
    echo "Applying ${sql_file}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
  done
else
  echo "No SQL schema files were found under schemas/."
  echo "This project is still in design / bootstrap phase. The database is initialized and ready for the next schema or migration pass."
fi

echo "Database bootstrap complete."
