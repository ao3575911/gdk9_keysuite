from __future__ import annotations

import io
import json
from pathlib import Path

from reference.keysuite.src.main import main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_cli_root_help_is_structured(capsys):
    assert main(["--help"]) == 0

    captured = capsys.readouterr()
    assert "{run,validate,inspect-grammar,dump-fsm,reduce,conformance,repl,completion}" not in captured.out
    assert "COMMAND" in captured.out
    assert "keysuite run --tokens" in captured.out


def test_cli_version(capsys):
    assert main(["--version"]) == 0

    captured = capsys.readouterr()
    assert "KeySuite" in captured.out


def test_cli_run_help_is_structured(capsys):
    assert main(["run", "--help"]) == 0

    captured = capsys.readouterr()
    assert "positional token array" in captured.out
    assert "keysuite run --file examples/basic.tokens" in captured.out


def test_cli_accepts_positional_token_array(capsys):
    assert main(["C", "C", ".", "3", "3"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "CC→33"


def test_cli_run_tokens_string(capsys):
    assert main(["run", "--tokens", "C C . 3 3 SPACE"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "CC→33"


def test_cli_run_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("C C . 3 3 SPACE\n"))

    assert main(["run", "--stdin"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "CC→33"


def test_cli_run_file_input(capsys):
    assert main(["run", "--file", str(EXAMPLES / "basic.tokens")]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "CC→33"


def test_cli_reports_invalid_input_as_error(capsys):
    assert main(["run", "--tokens", "@"]) == 1

    captured = capsys.readouterr()
    assert "Token has no GDk9 jurisdiction" in captured.err


def test_cli_json_error_contains_state_and_token(capsys):
    assert main(["--json", "@"]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["state"] == "ERROR"
    assert payload["error"]["token"] == "@"


def test_cli_trace_prints_transition_lines(capsys):
    assert main(["--trace", "C", "."]) == 0

    captured = capsys.readouterr()
    assert "IDLE + CONTENT(C) -> COMPOSE append" in captured.out
    assert "COMPOSE + BIND(.) -> COMPOSE mark_bind" in captured.out
    assert "COMPOSE + COMMIT(SPACE) -> IDLE reduce_and_emit C→" in captured.out


def test_cli_debug_level_one_prints_final_state(capsys):
    assert main(["run", "--debug", "1", "--tokens", "C C . 3 3 SPACE"]) == 0

    captured = capsys.readouterr()
    assert "CC→33" in captured.out
    assert "final state: IDLE" in captured.out


def test_cli_validate_reports_grammar_hash(capsys):
    assert main(["validate"]) == 0

    captured = capsys.readouterr()
    assert "grammar valid:" in captured.out
    assert "sha256=" in captured.out


def test_cli_validate_accepts_positional_grammar_path(capsys):
    assert main(["validate", "grammar/gdk9-v1.0.0.yaml"]) == 0

    captured = capsys.readouterr()
    assert "grammar valid:" in captured.out


def test_cli_inspect_grammar_fsm_dump(capsys):
    assert main(["inspect-grammar", "--fsm"]) == 0

    captured = capsys.readouterr()
    assert "IDLE:" in captured.out
    assert "COMMIT" in captured.out


def test_cli_dump_fsm_alias(capsys):
    assert main(["dump-fsm"]) == 0

    captured = capsys.readouterr()
    assert "IDLE:" in captured.out


def test_cli_repl_recovers_and_reports_state(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("C C . 3 3 SPACE\n:state\n:reset\n:quit\n"))

    assert main(["repl"]) == 0

    captured = capsys.readouterr()
    assert "KeySuite REPL" in captured.out
    assert "CC→33" in captured.out
    assert '"state": "IDLE"' in captured.out
    assert "runtime reset" in captured.out


def test_cli_completion_bash(capsys):
    assert main(["completion", "bash"]) == 0

    captured = capsys.readouterr()
    assert "complete -F _keysuite_complete keysuite" in captured.out


def test_cli_escape_treats_syntax_as_literal_content(capsys):
    assert main(["A", "_", ".", "B"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "A.B"
