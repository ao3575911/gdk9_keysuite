from copy import deepcopy

import pytest

from reference.keysuite.src.grammar_loader import load_grammar
from reference.keysuite.src.ime_runtime import IMEKernel
from reference.keysuite.src.reducer import reduce_buffer
from reference.keysuite.src.transitions import generate_transition_table


def test_yaml_transition_table_controls_runtime_actions():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    table = generate_transition_table(grammar)

    assert table["COMPOSE"]["COMMIT"] == ("IDLE", "reduce_and_emit")
    assert table["ERROR"]["ABORT"] == ("IDLE", "clear")


def test_transition_spec_rejects_unknown_action():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    grammar = deepcopy(grammar)
    grammar["transitions"]["COMPOSE"]["COMMIT"]["action"] = "emit_early"

    with pytest.raises(ValueError, match="unknown action"):
        generate_transition_table(grammar)


def test_transition_spec_rejects_undeclared_symbol_jurisdiction():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    grammar = deepcopy(grammar)
    grammar["transitions"]["COMPOSE"]["MAGIC"] = {"next": "COMPOSE", "action": "append"}

    with pytest.raises(ValueError, match="no declared symbol jurisdiction"):
        generate_transition_table(grammar)


def test_no_output_before_commit_boundary():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    kernel = IMEKernel(generate_transition_table(grammar), reduce_buffer)

    for event in [
        {"class": "CONTENT", "value": "C"},
        {"class": "BIND", "value": "."},
        {"class": "CONTENT", "value": "3"},
    ]:
        assert kernel.handle(event) is None

    assert kernel.handle({"class": "COMMIT", "value": "SPACE"}) == "C→3"
