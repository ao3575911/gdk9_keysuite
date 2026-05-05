# GDk9 - Symbolic Implication Infrastructure
<img width="240" height="64" alt="image" src="https://github.com/user-attachments/assets/c8ac739a-e058-45f4-afcc-763d16ff3cc9" />

GDk9 is a deterministic symbolic implication architecture. KeySuite is the
reference runtime for GDk9 v1.0.0 and an importable Python package.

The runtime is intentionally narrow: symbols enter explicit jurisdiction, move
through a finite state machine, and emit output only at a commit boundary after
pure reduction.

## Current Release

- GDk9 Standard: 1.0.0
- KeySuite Runtime: 1.1.0.dev0
- Grammar: `grammar/gdk9-v1.0.0.yaml`
- Package: `keysuite` 1.1.0.dev0

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Verify the install:

```bash
keysuite --help
keysuite validate
keysuite run --tokens "C C . 3 3 SPACE"
```

Expected output:

```text
CC→33
```

## Python API

```python
from keysuite import Runtime, Grammar, load_grammar

grammar = load_grammar()
runtime = Runtime(grammar)
session = runtime.create_session()
print(session.process(["C", "C", ".", "3", "3", "SPACE"])["outputs"])
```

The package also exposes `AsyncRuntime`, `RuntimeSession`, `IMEKernel`,
`load_grammar`, and `reduce_buffer`.

## CLI Reference
<img width="280" height="64" alt="image" src="https://github.com/user-attachments/assets/b3443385-1189-4285-8ea7-2ff552af32c7" />

### `keysuite run`

Process a token stream through the runtime.

```bash
keysuite run C C . 3 3 SPACE
keysuite run --tokens "C C . 3 3 SPACE"
echo "C C . 3 3 SPACE" | keysuite run --stdin
keysuite run --file examples/basic.tokens
```

### `keysuite validate`

Load and validate the grammar.

```bash
keysuite validate
keysuite validate grammar/gdk9-v1.0.0.yaml
keysuite --grammar grammar/gdk9-v1.0.0.yaml validate
```

### `keysuite inspect-grammar`

Inspect grammar metadata or dump the compiled FSM.

```bash
keysuite inspect-grammar
keysuite inspect-grammar --fsm
keysuite dump-fsm
```

### `keysuite reduce`

Run the pure reducer directly on a token buffer.

```bash
keysuite reduce A . B
keysuite reduce --tokens "A . B"
```

### `keysuite conformance`

Run the conformance vector suite.

```bash
keysuite conformance conformance/vectors
make conformance
```

### `keysuite repl`

Start an interactive runtime session.

```bash
keysuite repl
```

### `keysuite completion`

Print a shell completion script.

```bash
keysuite completion bash
keysuite completion zsh
keysuite completion fish
```

## Input Forms

- Positional tokens: `keysuite run C C . 3 3 SPACE`
- Quoted token string: `keysuite run --tokens "C C . 3 3 SPACE"`
- Standard input: `echo "C C . 3 3 SPACE" | keysuite run --stdin`
- File input: `keysuite run --file examples/basic.tokens`

The grammar-declared escape token `_` makes the next token literal content.
For example:

```bash
keysuite run A _ . B
```

emits:

```text
A.B
```

## Debug Levels

- `--debug 0`: no extra debug output
- `--debug 1`: emitted output plus final state
- `--debug 2`: transition trace
- `--debug 3`: full trace with buffer and mode snapshots

`--trace` remains available as an alias for `--debug 2`.

## Exit Codes

- `0`: success
- `1`: runtime or conformance failure
- `2`: CLI usage error
- `3`: grammar or schema validation error
- `4`: stdin or file input error
- `5`: internal runtime exception

## Shell Completions

Generate a completion script with:

```bash
keysuite completion bash > /tmp/keysuite.bash
keysuite completion zsh > /tmp/_keysuite
keysuite completion fish > ~/.config/fish/completions/keysuite.fish
```

Install it for your shell:

```bash
# bash
mkdir -p ~/.local/share/bash-completion/completions
keysuite completion bash > ~/.local/share/bash-completion/completions/keysuite
source ~/.local/share/bash-completion/completions/keysuite

# zsh
mkdir -p ~/.zsh/completions
keysuite completion zsh > ~/.zsh/completions/_keysuite
fpath+=(~/.zsh/completions)
autoload -Uz compinit && compinit

# fish
mkdir -p ~/.config/fish/completions
keysuite completion fish > ~/.config/fish/completions/keysuite.fish
```

## Cookbook

### Basic implication

```bash
keysuite run --tokens "C C . 3 3 SPACE"
```

### Mode shift

```bash
keysuite run --tokens "X : A B SPACE"
```

### Rollback

```bash
keysuite run --tokens "A B BACKSPACE SPACE"
```

### Abort

```bash
keysuite run --tokens "A ESC"
```

### Invalid input

```bash
keysuite run --tokens "@"
echo $?
```

### Conformance

```bash
keysuite validate
keysuite conformance conformance/vectors
```

### REPL

```bash
keysuite repl
```

Inside the REPL:

```text
keysuite> C C . 3 3 SPACE
keysuite> :state
keysuite> :reset
keysuite> :quit
```

### CI and release check

```bash
pytest
make release-check
```

## Grammar and Runtime

- `grammar/gdk9-v1.0.0.yaml` is the canonical machine-readable control file.
- `keysuite/grammar_loader.py` loads and validates grammar.
- `keysuite/transitions.py` compiles the FSM table.
- `keysuite/runtime.py` executes the runtime state machine.
- `keysuite/reducer.py` performs pure reduction at commit.

## Tests

```bash
pytest
make conformance
make release-check
```

## Documentation

- Runtime reference: `reference/README.md`
- CLI reference: `site/reference/cli.md`
- Runtime conformance: `docs/RUNTIME_CONFORMANCE.md`
- Conformance vectors: `docs/CONFORMANCE_VECTORS.md`
- Site index: `site/index.md`
