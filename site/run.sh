#!/usr/bin/env bash
# Run the fictional BBS SG Bank demo site (localhost only, standard library only).
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required (3.10+)." >&2
  exit 1
fi

exec python3 backend/app.py "$@"
