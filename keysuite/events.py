from __future__ import annotations

from .symbols import LiteralSymbol


def _in_range(token: str, range_spec: str) -> bool:
    return (
        len(token) == 1
        and len(range_spec) == 3
        and range_spec[1] == "-"
        and ord(range_spec[0]) <= ord(token) <= ord(range_spec[2])
    )


def token_to_event(token: str, grammar: dict, literal: bool = False) -> dict:
    if literal:
        return {"class": "CONTENT", "value": LiteralSymbol(token)}

    symbols = grammar.get("symbols", {})
    syntax = symbols.get("syntax", {})
    control = symbols.get("control", {})

    exact = {
        syntax.get("bind"): "BIND",
        syntax.get("mode_shift"): "MODE_SHIFT",
        control.get("rollback"): "ROLLBACK",
        control.get("abort"): "ABORT",
    }
    exact.update({commit: "COMMIT" for commit in symbols.get("commit", [])})

    event_class = exact.get(token)
    if event_class is None and any(_in_range(token, spec) for spec in symbols.get("content", [])):
        event_class = "CONTENT"

    return {"class": event_class or "INVALID", "value": token}

