#!/bin/sh
set -eu
cd "$(dirname "$0")"
. ./runtime.sh
exec "$PY" launch.py "$@"
