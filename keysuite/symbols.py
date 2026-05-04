from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteralSymbol:
    value: str


BufferedSymbol = str | LiteralSymbol


def symbol_text(symbol: BufferedSymbol) -> str:
    if isinstance(symbol, LiteralSymbol):
        return symbol.value
    return symbol


def is_bind_marker(symbol: BufferedSymbol) -> bool:
    return not isinstance(symbol, LiteralSymbol) and symbol == "."

