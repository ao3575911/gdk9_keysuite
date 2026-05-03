import sys
from pathlib import Path
from .grammar_loader import load_grammar
from .transitions import generate_transition_table
from .ime_runtime import IMEKernel
from .reducer import reduce_buffer

GRAMMAR_FILE = Path("grammar") / "gdk9-v1.0.0.yaml"


def _in_range(token: str, range_spec: str) -> bool:
    return (
        len(token) == 1
        and len(range_spec) == 3
        and range_spec[1] == "-"
        and ord(range_spec[0]) <= ord(token) <= ord(range_spec[2])
    )


def token_to_event(token: str, grammar: dict) -> dict:
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


def main():
    grammar = load_grammar(str(grammar_path()))
    table = generate_transition_table(grammar)
    kernel = IMEKernel(table, reduce_buffer)

    raw = sys.argv[1].split() if len(sys.argv) > 1 else ["C", "C", ".", "3", "3"]

    for token in raw:
        output = kernel.handle(token_to_event(token, grammar))
        if output:
            print(output)

    output = kernel.handle({"class": "COMMIT", "value": "SPACE"})
    if output:
        print(output)


if __name__ == "__main__":
    main()
