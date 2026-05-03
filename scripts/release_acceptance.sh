#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python3}
if [ -x .venv/bin/python ]; then
  PYTHON=.venv/bin/python
fi

KEYSUITE=("$PYTHON" -m reference.keysuite.src.main)

"$PYTHON" -m compileall -q reference tests
"$PYTHON" -m pytest -q

"${KEYSUITE[@]}" --version
"${KEYSUITE[@]}" --help
"${KEYSUITE[@]}" "C C . 3 3" | grep "CC→33"
"${KEYSUITE[@]}" --tokens "C C . 3 3" | grep "CC→33"
"${KEYSUITE[@]}" --trace --tokens "C C . 3 3"
"${KEYSUITE[@]}" --json --tokens "C C . 3 3"
"${KEYSUITE[@]}" validate grammar/gdk9-v1.0.0.yaml
"${KEYSUITE[@]}" inspect-grammar
"${KEYSUITE[@]}" conformance conformance/vectors
"${KEYSUITE[@]}" reduce "A . B" | grep "A→B"

set +e
"${KEYSUITE[@]}" --tokens "@"
test "$?" -ne 0
set -e
