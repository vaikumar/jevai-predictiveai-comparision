#!/bin/sh
# Source from the application directory.
if [ -x ../../work/venv/bin/python ]; then
  PY=../../work/venv/bin/python
else
  if [ ! -d .venv ]; then python3 -m venv .venv; fi
  PY=.venv/bin/python
  "$PY" -m pip install -r requirements.txt
fi
OMP_DIR=$("$PY" -c 'import importlib.util,pathlib; print(pathlib.Path(importlib.util.find_spec("sklearn").origin).parent / ".dylibs")')
export DYLD_LIBRARY_PATH="$OMP_DIR${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
