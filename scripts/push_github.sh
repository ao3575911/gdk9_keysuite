#!/usr/bin/env bash
set -euo pipefail

REMOTE="${1:-}"

if [ -z "${REMOTE}" ]; then
  echo "Usage: ./scripts/push_github.sh git@github.com:USER/gdk9_keysuite.git"
  exit 2
fi

python3 -m compileall -q reference tests
pytest -q -p no:cacheprovider

if [ ! -d .git ]; then
  git init
fi

git add .

if ! git diff --cached --quiet; then
  git commit -m "Prepare GDk9 and KeySuite for public release" \
    -m "The release tree now carries synchronized standards, grammar, docs, packaging, and conformance evidence for the v1.0.0 public push." \
    -m "Constraint: Grammar remains the canonical runtime control surface" \
    -m "Confidence: high" \
    -m "Scope-risk: moderate" \
    -m "Tested: pytest -q -p no:cacheprovider; python3 -m compileall -q reference tests"
fi

git branch -M main

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

git push -u origin main
