import json

from reference.keysuite.src.main import main


def test_cli_accepts_positional_token_array(capsys):
    assert main(["C", "C", ".", "3", "3"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "CC→33"


def test_cli_reports_invalid_input_as_error(capsys):
    assert main(["@"]) == 1

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


def test_cli_validate_reports_grammar_hash(capsys):
    assert main(["validate"]) == 0

    captured = capsys.readouterr()
    assert "grammar valid:" in captured.out
    assert "sha256=" in captured.out


def test_cli_escape_treats_syntax_as_literal_content(capsys):
    assert main(["A", "_", ".", "B"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "A.B"
