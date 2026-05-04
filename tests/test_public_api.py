from keysuite import AsyncRuntime, Grammar, IMEKernel, Runtime, RuntimeSession, __version__, load_grammar, reduce_buffer


def test_public_api_exports_and_basic_runtime():
    grammar = load_grammar()

    assert isinstance(grammar, Grammar)
    assert __version__.startswith("1.1.0")

    runtime = Runtime(grammar)
    session = runtime.create_session()

    assert isinstance(session, RuntimeSession)
    assert runtime.get_session(session.session_id) is session

    kernel = IMEKernel(runtime.table, reduce_buffer)
    assert kernel.handle({"class": "CONTENT", "value": "C"}) is None
    assert kernel.handle({"class": "COMMIT", "value": "SPACE"}) == "C"


def test_async_runtime_is_constructible():
    runtime = AsyncRuntime()

    assert runtime.runtime.grammar["version"] == "1.0.0"
