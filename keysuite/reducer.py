from __future__ import annotations

from .symbols import BufferedSymbol, is_bind_marker, symbol_text


def _join_symbols(buffer: list[BufferedSymbol]) -> str:
    return "".join(symbol_text(symbol) for symbol in buffer)


def reduce_buffer(buffer: list[BufferedSymbol], mode: str | None = None) -> str:
    bind_index = next((index for index, symbol in enumerate(buffer) if is_bind_marker(symbol)), None)
    if bind_index is not None:
        result = _join_symbols(buffer[:bind_index]) + "→" + _join_symbols(buffer[bind_index + 1 :])
    else:
        result = _join_symbols(buffer)
    return f"{mode}({result})" if mode else result

