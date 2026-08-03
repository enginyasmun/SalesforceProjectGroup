#!/usr/bin/env bash
set -Eeuo pipefail

REPO="/home/enginproject/SalesforceProjectGroup"
DATA="/home/enginproject/project-group-data"
BACKUPS="/home/enginproject/project-group-backups"
VENV="/home/enginproject/.virtualenvs/projectgroup-env"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUPS" "$DATA/uploads" "$DATA/avatars"

if [[ -f "$DATA/project_group.db" ]]; then
  SOURCE_DB="$DATA/project_group.db" \
  BACKUP_DB="$BACKUPS/project_group_${STAMP}.db" \
  python - <<'PYBACKUP'
import os
import sqlite3

source = sqlite3.connect(os.environ["SOURCE_DB"])
target = sqlite3.connect(os.environ["BACKUP_DB"])
try:
    source.backup(target)
finally:
    target.close()
    source.close()
PYBACKUP
fi

tar -czf "$BACKUPS/files_${STAMP}.tar.gz" -C "$DATA" uploads avatars

cd "$REPO"
git status --short
git fetch origin
git pull --ff-only origin main

if [[ ! -f "$VENV/bin/activate" ]]; then
  echo "Virtual environment not found: $VENV" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$VENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m py_compile app.py curriculum_content.py project_content.py seed.py smoke_test.py email_test.py
python smoke_test.py
python seed.py

echo
echo "Deployment validation completed."
echo "Backup stamp: $STAMP"
echo "Reload the web app from the PythonAnywhere Web tab, then check /health."
