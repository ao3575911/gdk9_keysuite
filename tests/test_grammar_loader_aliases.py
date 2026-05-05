from pathlib import Path

import pytest

from reference.keysuite.src.grammar_loader import load_grammar
from reference.keysuite.src.schema import validate_grammar


ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_DIR = ROOT / "grammar"


@pytest.mark.parametrize(
    "filename",
    [
        "gdk9-v1.0.0.yaml",
        "gdk9-v1.0.0-2.yaml",
        "gdk9-v1.0.0-3.yaml",
    ],
)
def test_loader_accepts_compliant_grammar_aliases(filename):
    grammar_path = GRAMMAR_DIR / filename

    grammar = load_grammar(grammar_path)
    validated = validate_grammar(grammar)

    assert grammar["artifact"] == filename
    assert validated["version"] == "1.0.0"
    assert validated["standard_version"] == "1.0.0"
