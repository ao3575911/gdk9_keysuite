#!/usr/bin/env bash
set -e

mkdir -p site/{getting-started,standards,architecture,reference,governance,assets}

cat > site/index.md <<'EOF'
# GDk9 Documentation

GDk9 is deterministic symbolic implication infrastructure.

## Start Here

- [Overview](getting-started/overview.md)
- [Quickstart](getting-started/quickstart.md)
- [Concepts](getting-started/concepts.md)

## Standards

- [Core Standard](standards/core-standard.md)
- [Grammar Specification](standards/grammar-specification.md)

## Reference

- [KeySuite](reference/keysuite.md)
- [CLI Usage](reference/cli.md)
EOF

cat > site/getting-started/overview.md <<'EOF'
# Overview

GDk9 defines deterministic symbolic input and implication.

KeySuite is the reference runtime.
EOF

cat > site/getting-started/quickstart.md <<'EOF'
# Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
keysuite "C C . 3 3"

Expected:

CC→33
EOF

cat > site/getting-started/concepts.md <<'EOF'

Concepts
GDk9 uses:

symbol jurisdiction

finite-state execution

atomic commit

pure reduction
EOF

cat > site/standards/core-standard.md <<'EOF'

Core Standard
GDk9 requires deterministic execution, explicit symbol classes, and pure reduction.
EOF

cat > site/standards/grammar-specification.md <<'EOF'

Grammar Specification
Symbols are classified as CONTENT, SYNTAX, CONTROL, COMMIT, or ESCAPE.
EOF

cat > site/reference/keysuite.md <<'EOF'

KeySuite
KeySuite is the reference runtime implementing GDk9.
EOF

cat > site/reference/cli.md <<'EOF'

CLI Usage
keysuite "C C . 3 3"
EOF

echo "Docs created."
