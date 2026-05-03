from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .conformance import ConformanceResult, run_conformance
from .grammar_loader import load_grammar
from .ime_runtime import IMEKernel
from .reducer import reduce_buffer
from .schema import EXPECTED_VERSION
from .symbols import LiteralSymbol
from .transitions import generate_transition_table

GRAMMAR_FILE = Path("grammar") / "gdk9-v1.0.0.yaml"
CONFORMANCE_DIR = Path("conformance") / "vectors"

COMMANDS = {
    "run",
    "validate",
    "inspect-grammar",
    "reduce",
    "conformance",
    "repl",
    "completion",
    "dump-fsm",
}
ROOT_OPTIONS_WITH_VALUES = {"--grammar", "--tokens", "--file", "--debug"}
EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_USAGE = 2
EXIT_GRAMMAR = 3
EXIT_INPUT = 4
EXIT_INTERNAL = 5

ROOT_EXAMPLES = """
Examples:
  keysuite run --tokens "C C . 3 3 SPACE"
  echo "C C . 3 3 SPACE" | keysuite run --stdin
  keysuite run --file examples/basic.tokens
  keysuite validate
  keysuite inspect-grammar --fsm
  keysuite conformance conformance/vectors
  keysuite repl
"""

RUN_EXAMPLES = """
Examples:
  keysuite run C C . 3 3 SPACE
  keysuite run --tokens "C C . 3 3 SPACE"
  echo "C C . 3 3 SPACE" | keysuite run --stdin
  keysuite run --file examples/basic.tokens
"""

REDUCE_EXAMPLES = """
Examples:
  keysuite reduce A . B
  keysuite reduce --tokens "A . B"
  cat examples/basic.tokens | keysuite reduce --stdin
"""

REPL_HELP = """
Interactive commands:
  :help         Show this help text
  :quit         Exit the REPL
  :state        Show the current runtime state
  :reset        Reset the runtime state and buffer
  :grammar      Show the loaded grammar summary
  :debug on     Enable trace-level debug output
  :debug off    Disable debug output
  :debug 0-3    Set an explicit debug level

Enter token streams on their own line. Empty lines are ignored.
"""


class CLIError(Exception):
    def __init__(self, message: str, exit_code: int = EXIT_USAGE):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class GrammarLoadError(CLIError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_GRAMMAR)


class InputSourceError(CLIError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_INPUT)


class RuntimeFailure(CLIError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_RUNTIME)


def _in_range(token: str, range_spec: str) -> bool:
    return (
        len(token) == 1
        and len(range_spec) == 3
        and range_spec[1] == "-"
        and ord(range_spec[0]) <= ord(token) <= ord(range_spec[2])
    )


def token_to_event(token: str, grammar: dict, literal: bool = False) -> dict:
    if literal:
        return {"class": "CONTENT", "value": LiteralSymbol(token)}

    symbols = grammar.get("symbols", {})
    syntax = symbols.get("syntax", {})
    control = symbols.get("control", {})

    exact = {
        syntax.get("bind"): "BIND",
        syntax.get("mode_shift"): "MODE_SHIFT",
        control.get("rollback"): "ROLLBACK",
        control.get("abort"): "ABORT",
    }
    exact.update({commit: "COMMIT" for commit in symbols.get("commit", [])})

    event_class = exact.get(token)
    if event_class is None and any(_in_range(token, spec) for spec in symbols.get("content", [])):
        event_class = "CONTENT"

    return {"class": event_class or "INVALID", "value": token}


def grammar_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / GRAMMAR_FILE,
        Path(sys.prefix) / "share" / "keysuite" / GRAMMAR_FILE,
        Path.cwd() / GRAMMAR_FILE,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    checked = ", ".join(str(candidate) for candidate in candidates)
    raise GrammarLoadError(f"Unable to locate GDk9 grammar. Checked: {checked}")


def conformance_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / CONFORMANCE_DIR,
        Path.cwd() / CONFORMANCE_DIR,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = ", ".join(str(candidate) for candidate in candidates)
    raise InputSourceError(f"Unable to locate GDk9 conformance vectors. Checked: {checked}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stringify_value(value) -> str:
    if isinstance(value, LiteralSymbol):
        return value.value
    return str(value)


def _stringify_buffer(buffer: list) -> list[str]:
    return [_stringify_value(symbol) for symbol in buffer]


def _normalize_tokens(tokens: list[str], token_string: str | None) -> list[str]:
    if token_string is not None:
        return token_string.split()
    if len(tokens) == 1 and any(character.isspace() for character in tokens[0]):
        return tokens[0].split()
    return tokens


def _read_input_file(path: str) -> list[str]:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputSourceError(f"Unable to read input file {file_path}: {exc}") from exc

    tokens = text.split()
    if not tokens:
        raise InputSourceError(f"Input file {file_path} did not contain any tokens")
    return tokens


def _read_stdin_tokens(stdin) -> list[str]:
    text = stdin.read()
    tokens = text.split()
    if not tokens:
        raise InputSourceError("Standard input did not contain any tokens")
    return tokens


def _legacy_run_insertion(argv: list[str]) -> list[str]:
    if not argv:
        return argv

    if any(flag in argv for flag in ("--help", "-h", "--version")):
        return argv

    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--":
            if index + 1 >= len(argv):
                return argv
            return argv[:index] + ["run"] + argv[index:]
        if token in ROOT_OPTIONS_WITH_VALUES:
            index += 2
            continue
        if any(token.startswith(option + "=") for option in ROOT_OPTIONS_WITH_VALUES):
            index += 1
            continue
        if token in COMMANDS:
            return argv
        if not token.startswith("-"):
            return argv[:index] + ["run"] + argv[index:]
        index += 1

    return argv


def _build_common_parent() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--grammar", help="path to a GDk9 grammar YAML file", default=argparse.SUPPRESS)
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="print machine-readable JSON",
    )
    parser.add_argument(
        "--debug",
        type=int,
        choices=range(0, 4),
        metavar="{0,1,2,3}",
        default=argparse.SUPPRESS,
        help="set debug verbosity (0-3)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        default=argparse.SUPPRESS,
        help="compatibility alias for --debug 2",
    )
    parser.add_argument(
        "--tokens",
        dest="token_string",
        default=argparse.SUPPRESS,
        help='quoted token string, for example "C C . 3 3 SPACE"',
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        default=argparse.SUPPRESS,
        help="read tokens from standard input",
    )
    parser.add_argument("--file", dest="input_file", default=argparse.SUPPRESS, help="read tokens from a file")
    parser.add_argument(
        "--no-auto-commit",
        action="store_true",
        default=argparse.SUPPRESS,
        help="do not append an automatic SPACE commit for runtime commands",
    )
    return parser


def _build_parser() -> argparse.ArgumentParser:
    common = _build_common_parent()
    parser = argparse.ArgumentParser(
        prog="keysuite",
        description="Run and inspect the GDk9 KeySuite reference runtime.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=ROOT_EXAMPLES.strip(),
        allow_abbrev=False,
        parents=[common],
    )
    parser.add_argument("--version", action="version", version=f"KeySuite {EXPECTED_VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser(
        "run",
        help="run the runtime with a token stream",
        description="Process a token stream through the GDk9 runtime.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=RUN_EXAMPLES.strip(),
        parents=[common],
        allow_abbrev=False,
    )
    run.add_argument("args", nargs="*", help="positional token array")

    validate = subparsers.add_parser(
        "validate",
        help="validate the loaded grammar",
        description="Load and validate the grammar schema and runtime metadata.",
        parents=[common],
        allow_abbrev=False,
    )
    validate.add_argument("grammar_path", nargs="?", help="optional grammar file path")

    inspect = subparsers.add_parser(
        "inspect-grammar",
        help="inspect grammar metadata",
        description="Print the loaded grammar metadata or the compiled FSM table.",
        parents=[common],
        allow_abbrev=False,
    )
    inspect.add_argument(
        "--fsm",
        action="store_true",
        help="dump the generated finite-state transition table",
    )

    dump_fsm = subparsers.add_parser(
        "dump-fsm",
        help="alias for inspect-grammar --fsm",
        description="Alias for inspect-grammar --fsm.",
        parents=[common],
        allow_abbrev=False,
    )
    dump_fsm.set_defaults(fsm=True)

    reduce_parser = subparsers.add_parser(
        "reduce",
        help="reduce a buffered token stream",
        description="Run the pure reducer directly on the supplied tokens.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=REDUCE_EXAMPLES.strip(),
        parents=[common],
        allow_abbrev=False,
    )
    reduce_parser.add_argument("args", nargs="*", help="positional token array")

    conformance = subparsers.add_parser(
        "conformance",
        help="run the conformance vectors",
        description="Execute the conformance vector suite against the loaded runtime.",
        parents=[common],
        allow_abbrev=False,
    )
    conformance.add_argument("vector_path", nargs="?", help="path to a conformance vector file or directory")

    repl = subparsers.add_parser(
        "repl",
        help="start an interactive runtime REPL",
        description="Enter token streams interactively and inspect the current runtime state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=REPL_HELP.strip(),
        parents=[common],
        allow_abbrev=False,
    )

    completion = subparsers.add_parser(
        "completion",
        help="print shell completion scripts",
        description="Generate completion scripts for supported shells.",
        parents=[common],
        allow_abbrev=False,
    )
    completion.add_argument("shell", choices=("bash", "zsh", "fish"), help="shell to generate")

    parser.set_defaults(command="run")
    run.set_defaults(command="run")
    validate.set_defaults(command="validate")
    inspect.set_defaults(command="inspect-grammar")
    dump_fsm.set_defaults(command="inspect-grammar")
    reduce_parser.set_defaults(command="reduce")
    conformance.set_defaults(command="conformance")
    repl.set_defaults(command="repl")
    completion.set_defaults(command="completion")

    return parser


@dataclass
class RuntimeStep:
    token: str
    event_class: str
    value: str
    from_state: str
    to_state: str
    action: str
    output: str | None
    literal: bool = False
    before: dict | None = None
    after: dict | None = None


@dataclass
class RuntimeSession:
    grammar: dict
    table: dict
    auto_commit: bool = True
    debug_level: int = 0
    kernel: IMEKernel | None = None
    trace: list[dict] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    error: dict | None = None
    escaped: bool = False

    def __post_init__(self) -> None:
        self.kernel = IMEKernel(self.table, reduce_buffer)

    @property
    def escape_token(self) -> str | None:
        return self.grammar.get("symbols", {}).get("escape", {}).get("literal")

    def snapshot(self) -> dict:
        assert self.kernel is not None
        return {
            "state": self.kernel.state,
            "buffer": _stringify_buffer(self.kernel.buffer),
            "mode": self.kernel.mode,
            "debug_level": self.debug_level,
            "escaped": self.escaped,
        }

    def _record_error(self, token: str, event_class: str, message: str) -> None:
        self.error = {
            "token": token,
            "event_class": event_class,
            "message": message,
        }

    def _handle_event(self, token: str, literal: bool = False) -> None:
        assert self.kernel is not None
        event = token_to_event(token, self.grammar, literal=literal)
        from_state = self.kernel.state
        rule = self.table.get(from_state, {}).get(event["class"])
        before = self.snapshot() if self.debug_level >= 3 else None
        output = self.kernel.handle(event)
        if output is not None:
            self.outputs.append(output)
        after = self.snapshot() if self.debug_level >= 3 else None
        step = {
            "from_state": from_state,
            "event_class": event["class"],
            "value": _stringify_value(event["value"]),
            "to_state": self.kernel.state,
            "action": rule[1] if rule else "error",
            "output": output,
            "literal": literal,
        }
        if before is not None:
            step["before"] = before
        if after is not None:
            step["after"] = after
        self.trace.append(step)
        if self.kernel.state == "ERROR":
            self._record_error(
                token,
                event["class"],
                "Token has no GDk9 jurisdiction or no valid transition",
            )
        else:
            self.error = None

    def feed(self, token: str) -> None:
        if self.escaped:
            self._handle_event(token, literal=True)
            self.escaped = False
            return

        escape_token = self.escape_token
        if escape_token and token == escape_token:
            self.trace.append(
                {
                    "from_state": self.kernel.state if self.kernel else "IDLE",
                    "event_class": "ESCAPE",
                    "value": token,
                    "to_state": self.kernel.state if self.kernel else "IDLE",
                    "action": "escape_next",
                    "output": None,
                    "literal": False,
                }
            )
            self.escaped = True
            return

        self._handle_event(token)

    def finalize(self) -> None:
        assert self.kernel is not None
        if self.error is None and self.escaped:
            self.kernel.state = "ERROR"
            self._record_error(
                self.escape_token or "_",
                "ESCAPE",
                "Escape marker must be followed by a literal token",
            )
            self.escaped = False
            return

        if self.auto_commit and self.error is None and self.kernel.state != "ERROR":
            self._handle_event("SPACE")

    def process(self, tokens: list[str], finalize: bool = True) -> dict:
        for token in tokens:
            self.feed(token)
        if finalize:
            self.finalize()
        return self.result()

    def result(self) -> dict:
        assert self.kernel is not None
        return {
            "status": "error" if self.kernel.state == "ERROR" else "ok",
            "state": self.kernel.state,
            "buffer": _stringify_buffer(self.kernel.buffer),
            "mode": self.kernel.mode,
            "outputs": list(self.outputs),
            "trace": list(self.trace),
            "error": self.error,
        }


def _run_tokens(
    tokens: list[str],
    grammar: dict,
    table: dict,
    auto_commit: bool = True,
    debug_level: int = 0,
) -> dict:
    session = RuntimeSession(grammar, table, auto_commit=auto_commit, debug_level=debug_level)
    return session.process(tokens, finalize=True)


def _trace_line(entry: dict) -> str:
    output = f" {entry['output']}" if entry.get("output") is not None else ""
    line = (
        f"{entry['from_state']} + {entry['event_class']}({entry['value']}) "
        f"-> {entry['to_state']} {entry['action']}{output}"
    )
    if entry.get("before") is not None and entry.get("after") is not None:
        line += f" | before={entry['before']} after={entry['after']}"
    return line


def _trace_debug_lines(result: dict, debug_level: int) -> list[str]:
    if debug_level <= 0:
        return []
    if debug_level == 1:
        return [f"final state: {result['state']}"]
    if debug_level == 2:
        return [_trace_line(entry) for entry in result["trace"]]

    lines = ["runtime detail:"]
    for index, entry in enumerate(result["trace"], start=1):
        lines.append(f"{index}: {_trace_line(entry)}")
    lines.append(f"final state: {result['state']}")
    lines.append(f"buffer: {result['buffer']}")
    lines.append(f"mode: {result['mode']}")
    return lines


def _print_result(result: dict, json_output: bool, debug_level: int, grammar_hash: str) -> None:
    if json_output:
        payload = {**result, "grammar_sha256": grammar_hash, "debug_level": debug_level}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    for output in result["outputs"]:
        print(output)

    for line in _trace_debug_lines(result, debug_level):
        print(line)

    if result["status"] == "error" and result["error"]:
        print(result["error"]["message"], file=sys.stderr)


def _conformance_payload(results: list[ConformanceResult], vector_path: Path, grammar_file: Path, grammar_hash: str) -> dict:
    failures = [result for result in results if not result.passed]
    return {
        "status": "ok" if not failures else "error",
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "total": len(results),
        "vectors": str(vector_path),
        "grammar": str(grammar_file),
        "grammar_sha256": grammar_hash,
        "failures": [
            {
                "id": failure.id,
                "expected": failure.expected,
                "actual": failure.actual,
                "error": failure.error,
            }
            for failure in failures
        ],
    }


def _print_conformance(payload: dict, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if payload["status"] == "ok":
        print(f"conformance ok: {payload['passed']}/{payload['total']} vectors passed")
        return

    print(f"conformance failed: {payload['failed']}/{payload['total']} vectors failed", file=sys.stderr)
    for failure in payload["failures"]:
        print(f"{failure['id']}: expected={failure['expected']} actual={failure['actual']}", file=sys.stderr)
        if failure["error"]:
            print(f"{failure['id']}: {failure['error']}", file=sys.stderr)


def _format_transition_table(table: dict) -> list[str]:
    lines = []
    for state in sorted(table):
        lines.append(f"{state}:")
        for event_class, (next_state, action) in sorted(table[state].items()):
            lines.append(f"  {event_class:<12} -> {next_state:<6} {action}")
    return lines


def _validate_runtime_options(command: str, ns: argparse.Namespace) -> None:
    json_output = getattr(ns, "json", False)
    no_auto_commit = getattr(ns, "no_auto_commit", False)
    token_string = getattr(ns, "token_string", None)
    stdin = getattr(ns, "stdin", False)
    input_file = getattr(ns, "input_file", None)

    if command in {"validate", "inspect-grammar", "conformance", "repl"}:
        if token_string or stdin or input_file or getattr(ns, "args", []):
            raise CLIError(f"{command} does not accept runtime token input flags", EXIT_USAGE)

    if command in {"validate", "inspect-grammar"} and no_auto_commit:
        raise CLIError(f"{command} does not use --no-auto-commit", EXIT_USAGE)

    if command == "conformance" and (token_string or stdin or input_file or getattr(ns, "args", [])):
        raise CLIError("conformance accepts only an optional vector path", EXIT_USAGE)

    if command == "repl" and (json_output or no_auto_commit or token_string or stdin or input_file):
        raise CLIError("repl does not accept JSON, input-source, or auto-commit flags", EXIT_USAGE)


def _resolve_runtime_tokens(ns: argparse.Namespace) -> list[str]:
    token_string = getattr(ns, "token_string", None)
    stdin = getattr(ns, "stdin", False)
    input_file = getattr(ns, "input_file", None)

    sources = []
    if token_string is not None:
        sources.append("tokens")
    if stdin:
        sources.append("stdin")
    if input_file is not None:
        sources.append("file")
    if getattr(ns, "args", []):
        sources.append("positional")

    if len(sources) > 1:
        raise CLIError("Choose only one token input source: positional tokens, --tokens, --stdin, or --file", EXIT_USAGE)

    if token_string is not None:
        return _normalize_tokens([], token_string)
    if stdin:
        return _read_stdin_tokens(sys.stdin)
    if input_file is not None:
        return _read_input_file(input_file)
    if getattr(ns, "args", []):
        return _normalize_tokens(list(ns.args), None)
    return ["C", "C", ".", "3", "3"]


def _grammar_context(grammar: dict, grammar_file: Path, grammar_hash: str) -> dict:
    return {
        "artifact": grammar["artifact"],
        "version": grammar["version"],
        "standard_version": grammar["standard_version"],
        "keysuite_runtime_version": grammar["keysuite_runtime_version"],
        "states": grammar["states"],
        "grammar_sha256": grammar_hash,
        "grammar": str(grammar_file),
    }


def _print_grammar_metadata(grammar: dict, grammar_file: Path, grammar_hash: str, json_output: bool) -> None:
    payload = _grammar_context(grammar, grammar_file, grammar_hash)
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _print_fsm(grammar: dict, table: dict, grammar_file: Path, grammar_hash: str, json_output: bool) -> None:
    payload = {
        **_grammar_context(grammar, grammar_file, grammar_hash),
        "fsm": table,
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for line in _format_transition_table(table):
        print(line)


def _completion_script(shell: str) -> str:
    commands = " ".join(sorted(COMMANDS - {"dump-fsm"}))
    if shell == "bash":
        return f"""# bash completion for keysuite
_keysuite_complete() {{
    local cur prev words cword
    _init_completion || return
    case "${{words[1]}}" in
        run|reduce)
            COMPREPLY=( $(compgen -W "--grammar --json --debug --trace --tokens --stdin --file --no-auto-commit --help" -- "$cur") )
            ;;
        validate|inspect-grammar|dump-fsm)
            COMPREPLY=( $(compgen -W "--grammar --json --debug --trace --fsm --help" -- "$cur") )
            ;;
        conformance)
            COMPREPLY=( $(compgen -W "--grammar --json --debug --trace --help" -- "$cur") )
            ;;
        repl)
            COMPREPLY=( $(compgen -W "--grammar --debug --trace --help" -- "$cur") )
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish --help" -- "$cur") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "{commands} --grammar --json --debug --trace --help" -- "$cur") )
            ;;
    esac
}}
complete -F _keysuite_complete keysuite
"""
    if shell == "zsh":
        return f"""# zsh completion for keysuite
#compdef keysuite
_keysuite() {{
  local -a commands
  commands=({commands})
  if (( CURRENT == 2 )); then
    _describe 'command' commands
    return
  fi
  case $words[2] in
    run|reduce)
      _arguments '--grammar[path to grammar file]' '--json[print JSON output]' '--debug[level 0-3]' '--trace[compatibility alias]' '--tokens[quoted token string]' '--stdin[read tokens from stdin]' '--file[read tokens from file]' '--no-auto-commit[disable automatic commit]' '--help[show help]'
      ;;
    validate|inspect-grammar|dump-fsm)
      _arguments '--grammar[path to grammar file]' '--json[print JSON output]' '--debug[level 0-3]' '--trace[compatibility alias]' '--fsm[dump transition table]' '--help[show help]'
      ;;
    conformance)
      _arguments '--grammar[path to grammar file]' '--json[print JSON output]' '--debug[level 0-3]' '--trace[compatibility alias]' '--help[show help]'
      ;;
    repl)
      _arguments '--grammar[path to grammar file]' '--debug[level 0-3]' '--trace[compatibility alias]' '--help[show help]'
      ;;
    completion)
      _arguments '1:shell:(bash zsh fish)'
      ;;
    *)
      _arguments '--grammar[path to grammar file]' '--json[print JSON output]' '--debug[level 0-3]' '--trace[compatibility alias]' '--help[show help]'
      ;;
  esac
}}
compdef _keysuite keysuite
"""
    if shell == "fish":
        return """# fish completion for keysuite
complete -c keysuite -f -a "run validate inspect-grammar reduce conformance repl completion"
complete -c keysuite -l grammar -r
complete -c keysuite -l json
complete -c keysuite -l debug -r
complete -c keysuite -l trace
complete -c keysuite -l tokens -r
complete -c keysuite -l stdin
complete -c keysuite -l file -r
complete -c keysuite -l no-auto-commit
complete -c keysuite -l fsm
"""
    raise CLIError(f"Unsupported shell: {shell}", EXIT_USAGE)


def _run_repl(grammar: dict, table: dict, grammar_file: Path, grammar_hash: str, debug_level: int) -> None:
    session = RuntimeSession(grammar, table, auto_commit=True, debug_level=debug_level)
    prompt = "keysuite> " if getattr(sys.stdin, "isatty", lambda: False)() else ""
    print("KeySuite REPL. Type :help for commands.")
    while True:
        try:
            if prompt:
                print(prompt, end="", flush=True)
            line = sys.stdin.readline()
            if line == "":
                print("bye")
                return
            line = line.rstrip("\n")
            if not line.strip():
                continue

            if line.startswith(":"):
                command = line.strip()
                if command in {":quit", ":q", ":exit"}:
                    print("bye")
                    return
                if command == ":help":
                    print(REPL_HELP.strip())
                    continue
                if command == ":state":
                    print(json.dumps(session.snapshot(), indent=2, sort_keys=True))
                    continue
                if command == ":reset":
                    session = RuntimeSession(grammar, table, auto_commit=True, debug_level=session.debug_level)
                    print("runtime reset")
                    continue
                if command == ":grammar":
                    print(json.dumps(_grammar_context(grammar, grammar_file, grammar_hash), indent=2, sort_keys=True))
                    continue
                if command.startswith(":debug"):
                    parts = command.split()
                    if len(parts) == 1:
                        print(f"debug level: {session.debug_level}")
                        continue
                    value = parts[1]
                    if value == "on":
                        session.debug_level = 2
                        print("debug level: 2")
                        continue
                    if value == "off":
                        session.debug_level = 0
                        print("debug level: 0")
                        continue
                    if value.isdigit() and int(value) in range(0, 4):
                        session.debug_level = int(value)
                        print(f"debug level: {session.debug_level}")
                        continue
                    print("debug level must be one of: off, on, 0, 1, 2, 3")
                    continue
                print(f"unknown REPL command: {command}")
                continue

            tokens = line.split()
            if not tokens:
                continue

            before_outputs = len(session.outputs)
            before_trace = len(session.trace)
            session.process(tokens, finalize=False)
            payload = session.result()
            for output in session.outputs[before_outputs:]:
                print(output)
            for extra_line in _trace_debug_lines(
                {
                    **payload,
                    "outputs": session.outputs[before_outputs:],
                    "trace": session.trace[before_trace:],
                },
                session.debug_level,
            ):
                print(extra_line)
            if payload["status"] == "error" and payload["error"]:
                print(payload["error"]["message"], file=sys.stderr)
        except KeyboardInterrupt:
            print("bye")
            return


def _load_runtime(grammar_file: Path) -> tuple[dict, dict, str]:
    try:
        grammar = load_grammar(str(grammar_file))
        table = generate_transition_table(grammar)
        grammar_hash = file_sha256(grammar_file)
        return grammar, table, grammar_hash
    except (OSError, ValueError) as exc:
        raise GrammarLoadError(str(exc)) from exc


def _dispatch(ns: argparse.Namespace, grammar: dict, table: dict, grammar_file: Path, grammar_hash: str) -> int:
    command = ns.command
    _validate_runtime_options(command, ns)
    json_output = getattr(ns, "json", False)
    debug_level = getattr(ns, "debug", None)
    trace_enabled = getattr(ns, "trace", False)
    no_auto_commit = getattr(ns, "no_auto_commit", False)

    if command in {"run", "reduce"}:
        tokens = _resolve_runtime_tokens(ns)
        if command == "reduce":
            output = reduce_buffer(tokens)
            if json_output:
                print(json.dumps({"status": "ok", "output": output, "input_tokens": tokens}, indent=2, sort_keys=True))
            else:
                print(output)
            return EXIT_OK

        active_debug = debug_level if debug_level is not None else (2 if trace_enabled else 0)
        result = _run_tokens(tokens, grammar, table, auto_commit=not no_auto_commit, debug_level=active_debug)
        _print_result(result, json_output, active_debug, grammar_hash)
        return EXIT_RUNTIME if result["status"] == "error" else EXIT_OK

    if command == "validate":
        grammar_override = getattr(ns, "grammar", None) or getattr(ns, "grammar_path", None)
        if grammar_override:
            grammar_file = Path(grammar_override)
            grammar, table, grammar_hash = _load_runtime(grammar_file)
        if json_output:
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "grammar": str(grammar_file),
                        "version": grammar["version"],
                        "grammar_sha256": grammar_hash,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"grammar valid: {grammar_file} sha256={grammar_hash}")
        return EXIT_OK

    if command in {"inspect-grammar", "dump-fsm"}:
        if getattr(ns, "fsm", False) or command == "dump-fsm":
            _print_fsm(grammar, table, grammar_file, grammar_hash, json_output)
        else:
            _print_grammar_metadata(grammar, grammar_file, grammar_hash, json_output)
        return EXIT_OK

    if command == "conformance":
        vector_path = Path(ns.vector_path) if getattr(ns, "vector_path", None) else conformance_path()
        results = run_conformance(
            vector_path,
            lambda tokens: _run_tokens(
                tokens,
                grammar,
                table,
                auto_commit=not no_auto_commit,
                debug_level=debug_level if debug_level is not None else (2 if trace_enabled else 0),
            ),
        )
        payload = _conformance_payload(results, vector_path, grammar_file, grammar_hash)
        _print_conformance(payload, json_output)
        return EXIT_OK if payload["status"] == "ok" else EXIT_RUNTIME

    if command == "repl":
        active_debug = debug_level if debug_level is not None else (2 if trace_enabled else 0)
        _run_repl(grammar, table, grammar_file, grammar_hash, active_debug)
        return EXIT_OK

    if command == "completion":
        print(_completion_script(ns.shell))
        return EXIT_OK

    raise CLIError(f"Unknown command: {command}", EXIT_USAGE)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = _build_parser()
    rewritten = _legacy_run_insertion(list(argv))
    try:
        return parser.parse_args(rewritten)
    except SystemExit:
        raise


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        ns = _parse_args(args)
        grammar_file = Path(getattr(ns, "grammar", None)) if getattr(ns, "grammar", None) else grammar_path()
        grammar, table, grammar_hash = _load_runtime(grammar_file)
        return _dispatch(ns, grammar, table, grammar_file, grammar_hash)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_OK
    except CLIError as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_RUNTIME
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"internal error: {exc!r}", file=sys.stderr)
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
