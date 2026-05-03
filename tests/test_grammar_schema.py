from copy import deepcopy

import pytest

from reference.keysuite.src.grammar_loader import load_grammar
from reference.keysuite.src.schema import validate_grammar


def test_schema_accepts_current_grammar():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")

    assert validate_grammar(grammar)["version"] == "1.0.0"


def test_schema_rejects_unknown_top_level_key():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    grammar = deepcopy(grammar)
    grammar["surprise"] = True

    with pytest.raises(ValueError, match="unsupported keys"):
        validate_grammar(grammar)


def test_schema_rejects_unsupported_version():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    grammar = deepcopy(grammar)
    grammar["version"] = "2.0.0"

    with pytest.raises(ValueError, match="unsupported grammar version"):
        validate_grammar(grammar)


def test_schema_rejects_duplicate_exact_tokens():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    grammar = deepcopy(grammar)
    grammar["symbols"]["commit"].append("ESC")

    with pytest.raises(ValueError, match="declared by both"):
        validate_grammar(grammar)


def test_schema_rejects_unreachable_state():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    grammar = deepcopy(grammar)
    grammar["states"].append("DEAD")

    with pytest.raises(ValueError, match="unreachable"):
        validate_grammar(grammar)
