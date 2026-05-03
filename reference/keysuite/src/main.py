import argparse
import hashlib
import json
import sys
from pathlib import Path
from .conformance import ConformanceResult, run_conformance
from .grammar_loader import load_grammar
from .transitions import generate_transition_table
from .ime_runtime import IMEKernel
from .reducer import reduce_buffer
from .schema import EXPECTED_VERSION
from .symbols import LiteralSymbol

GRAMMAR_FILE = Path("grammar") / "gdk9-v1.0.0.yaml"
CONFORMANCE_DIR = Path("conformance") / "vectors"


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
    raise FileNotFoundError(f"Unable to locate GDk9 grammar. Checked: {checked}")


def conformance_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / CONFORMANCE_DIR,
        Path.cwd() / CONFORMANCE_DIR,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Unable to locate GDk9 conformance vectors. Checked: {checked}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stringify_value(value) -> str:
    if isinstance(value, LiteralSymbol):
        return value.value
    return str(value)


def _normalize_tokens(tokens: list[str], token_string: str | None) -> list[str]:
    if token_string is not None:
        return token_string.split()
    if len(tokens) == 1 and any(character.isspace() for character in tokens[0]):
        return tokens[0].split()
    return tokens


def _trace_line(entry: dict) -> str:
    output = f" {entry['output']}" if entry.get("output") is not None else ""
    return (
        f"{entry['from_state']} + {entry['event_class']}({entry['value']}) "
        f"-> {entry['to_state']} {entry['action']}{output}"
    )


def _run_tokens(tokens: list[str], grammar: dict, table: dict, auto_commit: bool = True) -> dict:
    kernel = IMEKernel(table, reduce_buffer)
    trace = []
    outputs = []
    escaped = False
    escape_token = grammar.get("symbols", {}).get("escape", {}).get("literal")
    error = None

    def handle_event(token: str, literal: bool = False) -> None:
        nonlocal error
        event = token_to_event(token, grammar, literal=literal)
        from_state = kernel.state
        rule = table.get(from_state, {}).get(event["class"])
        output = kernel.handle(event)
        if output is not None:
            outputs.append(output)
        trace.append(
            {
                "from_state": from_state,
                "event_class": event["class"],
                "value": _stringify_value(event["value"]),
                "to_state": kernel.state,
                "action": rule[1] if rule else "error",
                "output": output,
                "literal": literal,
            }
        )
        if kernel.state == "ERROR":
            error = {
                "token": token,
                "event_class": event["class"],
                "message": "Token has no GDk9 jurisdiction or no valid transition",
            }

    for token in tokens:
        if escaped:
            handle_event(token, literal=True)
            escaped = False
            continue
        if escape_token and token == escape_token:
            trace.append(
                {
                    "from_state": kernel.state,
                    "event_class": "ESCAPE",
                    "value": token,
                    "to_state": kernel.state,
                    "action": "escape_next",
                    "output": None,
                    "literal": False,
                }
            )
            escaped = True
            continue
        handle_event(token)

    if escaped:
        kernel.state = "ERROR"
        error = {
            "token": escape_token,
            "event_class": "ESCAPE",
            "message": "Escape marker must be followed by a literal token",
        }

    if auto_commit and kernel.state != "ERROR":
        handle_event("SPACE")

    return {
        "status": "error" if kernel.state == "ERROR" else "ok",
        "state": kernel.state,
        "outputs": outputs,
        "trace": trace,
        "error": error,
    }


def _print_result(result: dict, json_output: bool, trace_output: bool, grammar_hash: str) -> None:
    if json_output:
        payload = {**result, "grammar_sha256": grammar_hash}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if trace_output:
        for entry in result["trace"]:
            print(_trace_line(entry))
    elif result["outputs"]:
        for output in result["outputs"]:
            print(output)
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
        print(
            f"{failure['id']}: expected={failure['expected']} actual={failure['actual']}",
            file=sys.stderr,
        )
        if failure["error"]:
            print(f"{failure['id']}: {failure['error']}", file=sys.stderr)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="keysuite",
        description="Run and validate the GDk9 KeySuite reference runtime.",
    )
    parser.add_argument("args", nargs="*", help="tokens or command followed by tokens")
    parser.add_argument("--tokens", help="quoted token string to process")
    parser.add_argument("--grammar", help="path to a GDk9 grammar YAML file")
    parser.add_argument("--trace", action="store_true", help="print state-transition trace")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--no-auto-commit", action="store_true", help="do not append SPACE commit")
    parser.add_argument("--version", action="version", version=f"KeySuite {EXPECTED_VERSION}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    grammar_file = Path(ns.grammar) if ns.grammar else grammar_path()
    grammar = load_grammar(str(grammar_file))
    table = generate_transition_table(grammar)
    command = "run"
    args = list(ns.args)
    if args and args[0] in {"run", "validate", "trace", "reduce", "inspect-grammar", "conformance"}:
        command = args.pop(0)
    if command == "trace":
        ns.trace = True

    grammar_hash = file_sha256(grammar_file)

    if command == "validate":
        if ns.json:
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
        return 0

    if command == "inspect-grammar":
        payload = {
            "artifact": grammar["artifact"],
            "version": grammar["version"],
            "standard_version": grammar["standard_version"],
            "keysuite_runtime_version": grammar["keysuite_runtime_version"],
            "states": grammar["states"],
            "grammar_sha256": grammar_hash,
        }
        if ns.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for key, value in payload.items():
                print(f"{key}: {value}")
        return 0

    if command == "conformance":
        vector_path = Path(args[0]) if args else conformance_path()
        results = run_conformance(
            vector_path,
            lambda tokens: _run_tokens(tokens, grammar, table, auto_commit=not ns.no_auto_commit),
        )
        payload = _conformance_payload(results, vector_path, grammar_file, grammar_hash)
        _print_conformance(payload, ns.json)
        return 0 if payload["status"] == "ok" else 1

    raw = _normalize_tokens(args, ns.tokens)
    if not raw:
        raw = ["C", "C", ".", "3", "3"]

    if command == "reduce":
        output = reduce_buffer(raw)
        if ns.json:
            print(json.dumps({"status": "ok", "output": output}, indent=2, sort_keys=True))
        else:
            print(output)
        return 0

    result = _run_tokens(raw, grammar, table, auto_commit=not ns.no_auto_commit)
    _print_result(result, ns.json, ns.trace, grammar_hash)
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
