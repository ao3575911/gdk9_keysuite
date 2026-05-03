from reference.keysuite.src.ime_runtime import IMEKernel
from reference.keysuite.src.grammar_loader import load_grammar
from reference.keysuite.src.transitions import generate_transition_table
from reference.keysuite.src.reducer import reduce_buffer

def test_basic_implication():
    grammar = load_grammar("grammar/gdk9-v1.0.0.yaml")
    kernel = IMEKernel(generate_transition_table(grammar), reduce_buffer)

    seq = [
        {"class": "CONTENT", "value": "C"},
        {"class": "CONTENT", "value": "C"},
        {"class": "BIND", "value": "."},
        {"class": "CONTENT", "value": "3"},
        {"class": "CONTENT", "value": "3"},
        {"class": "COMMIT", "value": "SPACE"},
    ]

    out = None
    for e in seq:
        result = kernel.handle(e)
        if result:
            out = result

    assert out == "CC→33"
