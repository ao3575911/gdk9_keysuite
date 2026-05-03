# Scripts

## `push_github.sh`

Runs compile and test checks, creates a Lore-style release commit when staged changes exist, configures `origin`, and pushes `main`.

Usage:

```bash
./scripts/push_github.sh git@github.com:USER/gdk9_keysuite.git
```

Review `git status --short` before running the script.
