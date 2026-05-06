from pathlib import Path

import pytest

from reference.keysuite.src.conformance import ConformanceVectorError, run_conformance
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


def test_conformance_empty_directory_fails(tmp_path):
    with pytest.raises(ConformanceVectorError, match="No conformance vector files"):
        run_conformance(tmp_path, run_tokens)


def test_cli_conformance_empty_directory_exits_nonzero(tmp_path, capsys):
    assert main(["conformance", str(tmp_path)]) == 1

    captured = capsys.readouterr()
    assert "No conformance vector files" in captured.err


def test_conformance_missing_path_fails(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="Conformance vector path not found"):
        run_conformance(missing, run_tokens)


def test_cli_conformance_missing_path_exits_nonzero(tmp_path, capsys):
    missing = tmp_path / "missing"

    assert main(["conformance", str(missing)]) == 1

    captured = capsys.readouterr()
    assert "Conformance vector path not found" in captured.err
