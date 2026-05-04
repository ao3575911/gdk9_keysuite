import pytest

from keysuite.config import RuntimeConfig
from keysuite.errors import HistoryError, MacroExpansionError
from keysuite import Runtime, load_grammar


def make_runtime(**config_overrides):
    grammar = load_grammar()
    config = RuntimeConfig(**config_overrides)
    return Runtime(grammar, config=config)


def test_oversized_buffer_is_rejected():
    runtime = make_runtime(max_buffer_size=1)
    session = runtime.create_session()

    result = session.process(["C", "D"])

    assert result["status"] == "error"
    assert result["error"]["type"] == "RuntimeLimitError"


def test_invalid_token_sequence_is_rejected():
    runtime = make_runtime()
    session = runtime.create_session()

    result = session.process(["bad token"])

    assert result["status"] == "error"
    assert result["error"]["type"] == "TokenValidationError"


def test_macro_registration_and_expansion():
    runtime = make_runtime()
    session = runtime.create_session()
    session.register_macro("pair", ["C", "C"])

    result = session.process(["pair", "SPACE"])

    assert result["status"] == "ok"
    assert result["outputs"] == ["CC"]
    assert any(entry["type"] == "macro_expansion" for entry in result["trace"])


def test_recursive_macro_expansion_is_rejected():
    runtime = make_runtime(max_macro_expansion_depth=2)
    session = runtime.create_session()
    session.register_macro("macro_b", ["C"])
    session.register_macro("macro_a", ["macro_b"])
    session.register_macro("macro_b", ["macro_a"])

    result = session.process(["macro_a"])

    assert result["status"] == "error"
    assert result["error"]["type"] == "MacroExpansionError"


def test_macro_validation_rejects_invalid_tokens():
    runtime = make_runtime()
    session = runtime.create_session()

    with pytest.raises(MacroExpansionError):
        session.register_macro("bad", ["@"])


def test_undo_and_redo_restore_state_and_output():
    runtime = make_runtime()
    session = runtime.create_session()

    session.process(["C", "C", "SPACE"])
    after_commit = session.result()
    assert after_commit["outputs"] == ["CC"]

    undone = session.undo()
    assert undone["state"] == "COMPOSE"
    assert undone["outputs"] == []

    redone = session.redo()
    assert redone["state"] == "IDLE"
    assert redone["outputs"] == ["CC"]

    session.clear_history()
    with pytest.raises(HistoryError):
        session.undo()
