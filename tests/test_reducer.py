from reference.keysuite.src.reducer import reduce_buffer
from reference.keysuite.src.symbols import LiteralSymbol

def test_reducer_simple():
    assert reduce_buffer(["A","B","C"]) == "ABC"

def test_reducer_implication():
    assert reduce_buffer(["A","B",".","C","D"]) == "AB→CD"

def test_reducer_mode():
    assert reduce_buffer(["A","B"], mode="X") == "X(AB)"


def test_reducer_does_not_treat_escaped_literal_dot_as_bind():
    assert reduce_buffer(["A", LiteralSymbol("."), "B"]) == "A.B"
