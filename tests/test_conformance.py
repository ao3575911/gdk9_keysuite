from pathlib import Path

from reference.keysuite.src.conformance import run_conformance
from reference.keysuite.src.grammar_loader import load_grammar
from reference.keysuite.src.main import _run_tokens, main
from reference.keysuite.src.transitions import generate_transition_table


ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_PATH = ROOT / "grammar" / "gdk9-v1.0.0.yaml"
VECTOR_DIR = ROOT / "conformance" / "vectors"


GRAMMAR = load_grammar(GRAMMAR_PATH)
TRANSITIONS = generate_transition_table(GRAMMAR)


def run_tokens(tokens: list[str]):
    return _run_tokens(tokens, GRAMMAR, TRANSITIONS)


def test_conformance_vectors():
    results = run_conformance(VECTOR_DIR, run_tokens)
    failures = [result for result in results if not result.passed]

    assert not failures, [
        {
            "id": failure.id,
            "expected": failure.expected,
            "actual": failure.actual,
            "error": failure.error,
        }
        for failure in failures
    ]


def test_cli_conformance_subcommand(capsys):
    assert main(["conformance", str(VECTOR_DIR)]) == 0

    captured = capsys.readouterr()
    assert "conformance ok:" in captured.out
