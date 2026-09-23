#!/bin/sh
# Start the BBS SG Bank operations terminal (synthetic demo) on localhost.
#
#   legacy-ui/run.sh              # http://127.0.0.1:8792/
#   PORT=9000 legacy-ui/run.sh    # a different loopback port
#
# Standard library only. The helper server compiles legacy/bank.cob with the
# isolated GnuCOBOL build from scripts/get_cobc.sh and runs it as a real
# subprocess; all account data is generated locally for the demo.

set -eu

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required (3.10+)." >&2
    exit 1
fi

PORT="${PORT:-8792}"

if [ -z "${COBC:-}" ]; then
    for candidate in /tmp/gcb-build/install/bin/cobc "$HOME/.local/gnucobol/bin/cobc"; do
        if [ -x "$candidate" ]; then
            COBC="$candidate"
            export COBC
            break
        fi
    done
fi

if [ -z "${COBC:-}" ] && ! command -v cobc >/dev/null 2>&1; then
    echo "note: no cobc found; the terminal will run in labelled SIMULATED mode." >&2
    echo "      run scripts/get_cobc.sh first for the real COBOL batch." >&2
fi

echo "BBS SG Bank operations terminal -> http://127.0.0.1:${PORT}/"
exec python3 server.py --port "$PORT"
