from reference.keysuite.src.grammar_loader import load_grammar
from reference.keysuite.src.ime_runtime import IMEKernel
from reference.keysuite.src.main import token_to_event
from reference.keysuite.src.reducer import reduce_buffer
from reference.keysuite.src.symbols import LiteralSymbol
from reference.keysuite.src.transitions import generate_transition_table


def make_kernel(grammar=None):
    grammar = grammar or load_grammar("grammar/gdk9-v1.0.0.yaml")
    return IMEKernel(generate_transition_table(grammar), reduce_buffer)


def feed(kernel, events):
    output = None
    for event in events:
        result = kernel.handle(event)
        if result is not None:
            output = result
    return output


def test_rollback_removes_previous_content_before_commit():
    kernel = make_kernel()

    output = feed(
        kernel,
        [
            {"class": "CONTENT", "value": "A"},
            {"class": "CONTENT", "value": "B"},
            {"class": "ROLLBACK", "value": "BACKSPACE"},
            {"class": "COMMIT", "value": "SPACE"},
        ],
    )

    assert output == "A"


def test_abort_discards_buffer_without_emitting_output():
    kernel = make_kernel()

    output = feed(
        kernel,
        [
            {"class": "CONTENT", "value": "A"},
            {"class": "ABORT", "value": "ESC"},
            {"class": "COMMIT", "value": "SPACE"},
        ],
    )

    assert output is None
    assert kernel.state == "IDLE"
    assert kernel.buffer == []


def test_mode_shift_wraps_committed_content_in_mode_prefix():
    kernel = make_kernel()

    output = feed(
        kernel,
        [
            {"class": "CONTENT", "value": "X"},
            {"class": "MODE_SHIFT", "value": ":"},
            {"class": "CONTENT", "value": "A"},
            {"class": "CONTENT", "value": "B"},
            {"class": "COMMIT", "value": "SPACE"},
        ],
    )

    assert output == "X(AB)"


def test_timeout_event_class_commits_composed_buffer():
    kernel = make_kernel()

    output = feed(
        kernel,
        [
            {"class": "CONTENT", "value": "A"},
            {"class": "CONTENT", "value": "B"},
            {"class": "COMMIT", "value": "TIMEOUT"},
        ],
    )

    assert output == "AB"


def test_invalid_event_moves_kernel_to_error_state():
    kernel = make_kernel()

    output = kernel.handle({"class": "ROLLBACK", "value": "BACKSPACE"})

    assert output is None
    assert kernel.state == "ERROR"


def test_abort_recovers_kernel_from_error_state():
    kernel = make_kernel()

    kernel.handle({"class": "ROLLBACK", "value": "BACKSPACE"})
    kernel.handle({"class": "ABORT", "value": "ESC"})

    assert kernel.state == "IDLE"
    assert kernel.buffer == []


def test_multiple_bind_markers_use_first_marker_as_implication_boundary():
    kernel = make_kernel()

    output = feed(
        kernel,
        [
            {"class": "CONTENT", "value": "A"},
            {"class": "BIND", "value": "."},
            {"class": "CONTENT", "value": "B"},
            {"class": "BIND", "value": "."},
            {"class": "CONTENT", "value": "C"},
            {"class": "COMMIT", "value": "SPACE"},
        ],
    )

    assert output == "A→B.C"


def test_grammar_loader_returns_nested_gdk9_grammar_content():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")

    assert grammar["version"] == "1.0.0"
    assert grammar["symbols"]["commit"] == ["SPACE", "ENTER", "TAB", "TIMEOUT", "DONE"]
    assert grammar["states"] == ["IDLE", "COMPOSE", "MODE", "ERROR"]


def test_timeout_token_maps_to_commit_from_loaded_grammar():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")

    assert "TIMEOUT" in grammar["symbols"]["commit"]
    assert token_to_event("TIMEOUT", grammar) == {"class": "COMMIT", "value": "TIMEOUT"}


def test_unknown_token_maps_to_invalid_from_loaded_grammar():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")

    assert token_to_event("@", grammar) == {"class": "INVALID", "value": "@"}


def test_literal_token_maps_to_content_even_when_it_is_syntax():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")

    event = token_to_event(".", grammar, literal=True)

    assert event == {"class": "CONTENT", "value": LiteralSymbol(".")}


def test_transition_table_generation_rejects_missing_required_state():
    grammar = {
        "states": ["IDLE", "COMPOSE", "ERROR"],
        "symbols": {
            "content": ["A"],
            "syntax": {"bind": "."},
            "commit": ["DONE"],
            "control": {"rollback": "BACKSPACE", "abort": "ESC"},
        },
    }

    try:
        generate_transition_table(grammar)
    except ValueError as exc:
        assert "MODE" in str(exc)
    else:
        raise AssertionError("missing MODE state should be rejected")
