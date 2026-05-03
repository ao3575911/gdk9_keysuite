from reference.keysuite.src.reducer import reduce_buffer

def test_reducer_simple():
    assert reduce_buffer(["A","B","C"]) == "ABC"

def test_reducer_implication():
    assert reduce_buffer(["A","B",".","C","D"]) == "AB→CD"

def test_reducer_mode():
    assert reduce_buffer(["A","B"], mode="X") == "X(AB)"
