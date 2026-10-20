#!/bin/sh
set -eu
cd "$(dirname "$0")"
. ./runtime.sh
exec "$PY" diagnose_jev.py
