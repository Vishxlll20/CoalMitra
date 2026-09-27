#!/usr/bin/env bash
# Idempotent PostgreSQL setup for CoalMitra.
# Creates (or resets) a dedicated `coalmitra` role + database using the postgres
# OS user's peer auth (sudo -u postgres). Single sudo prompt — run once from repo root.
set -eo pipefail

sudo -u postgres psql -v ON_ERROR_STOP=0 <<'SQL'
-- Role: create if missing, else reset its password — keeps local dev deterministic
-- and recovers from a half-configured cluster.
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'coalmitra') THEN
    CREATE ROLE coalmitra LOGIN PASSWORD 'coalmitra';
  ELSE
    ALTER ROLE coalmitra WITH LOGIN PASSWORD 'coalmitra';
  END IF;
END $$;

-- Database: CREATE DATABASE has no IF NOT EXISTS, so emit it only when missing.
SELECT format('CREATE DATABASE coalmitra OWNER coalmitra')
  FROM pg_database
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'coalmitra')
  LIMIT 1
\gexec
SQL

echo "Done. App connects via TCP (localhost:5432) with password auth."
echo "Next:  DATABASE_URL=\"postgresql+psycopg2://coalmitra:coalmitra@localhost:5432/coalmitra\" DEMO_MODE=1 uvicorn app.main:app --port 8000"