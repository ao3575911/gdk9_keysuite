# Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
keysuite run --tokens "C C . 3 3 SPACE"
```

Expected:

```text
CC→33
```

Follow-up checks:

```bash
keysuite validate
keysuite inspect-grammar --fsm
keysuite repl
```
