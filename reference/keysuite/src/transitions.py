REQUIRED_STATES = {"IDLE", "COMPOSE", "MODE", "ERROR"}
ALLOWED_ACTIONS = {
    "append",
    "clear",
    "mark_bind",
    "noop",
    "pop",
    "reduce_and_emit",
    "set_mode",
}


def _has_symbol_class(grammar: dict, event_class: str) -> bool:
    symbols = grammar.get("symbols", {})
    syntax = symbols.get("syntax", {})
    control = symbols.get("control", {})

    checks = {
        "CONTENT": bool(symbols.get("content")),
        "BIND": bool(syntax.get("bind")),
        "MODE_SHIFT": bool(syntax.get("mode_shift")),
        "COMMIT": bool(symbols.get("commit")),
        "ROLLBACK": bool(control.get("rollback")),
        "ABORT": bool(control.get("abort")),
    }
    return checks.get(event_class, False)


def _require_states(grammar: dict) -> None:
    states = set(grammar.get("states", []))
    missing = REQUIRED_STATES - states
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"GDk9 grammar missing required states: {names}")


def _transition_from_spec(state: str, event_class: str, spec: dict, states: set[str]) -> tuple[str, str]:
    if not isinstance(spec, dict):
        raise ValueError(f"Transition {state}.{event_class} must be a mapping")

    next_state = spec.get("next")
    action = spec.get("action")

    if next_state not in states:
        raise ValueError(f"Transition {state}.{event_class} uses unknown next state: {next_state}")
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Transition {state}.{event_class} uses unknown action: {action}")

    return next_state, action


def _generate_from_transition_spec(grammar: dict) -> dict:
    states = set(grammar.get("states", []))
    table = {state: {} for state in grammar["states"]}

    for state, rules in grammar.get("transitions", {}).items():
        if state not in states:
            raise ValueError(f"GDk9 grammar transition uses unknown state: {state}")
        if not isinstance(rules, dict):
            raise ValueError(f"GDk9 grammar transitions for {state} must be a mapping")

        for event_class, spec in rules.items():
            if not _has_symbol_class(grammar, event_class):
                raise ValueError(f"Transition {state}.{event_class} has no declared symbol jurisdiction")
            table[state][event_class] = _transition_from_spec(state, event_class, spec, states)

    return table


def generate_transition_table(grammar: dict) -> dict:
    _require_states(grammar)

    if "transitions" in grammar:
        return _generate_from_transition_spec(grammar)

    table = {"IDLE": {}, "COMPOSE": {}, "MODE": {}, "ERROR": {}}

    if _has_symbol_class(grammar, "CONTENT"):
        table["IDLE"]["CONTENT"] = ("COMPOSE", "append")
        table["COMPOSE"]["CONTENT"] = ("COMPOSE", "append")
        table["MODE"]["CONTENT"] = ("MODE", "append")

    if _has_symbol_class(grammar, "COMMIT"):
        table["IDLE"]["COMMIT"] = ("IDLE", "noop")
        table["COMPOSE"]["COMMIT"] = ("IDLE", "reduce_and_emit")
        table["MODE"]["COMMIT"] = ("IDLE", "reduce_and_emit")

    if _has_symbol_class(grammar, "ABORT"):
        table["IDLE"]["ABORT"] = ("IDLE", "noop")
        table["COMPOSE"]["ABORT"] = ("IDLE", "clear")
        table["MODE"]["ABORT"] = ("IDLE", "clear")
        table["ERROR"]["ABORT"] = ("IDLE", "clear")

    if _has_symbol_class(grammar, "BIND"):
        table["COMPOSE"]["BIND"] = ("COMPOSE", "mark_bind")

    if _has_symbol_class(grammar, "MODE_SHIFT"):
        table["COMPOSE"]["MODE_SHIFT"] = ("MODE", "set_mode")

    if _has_symbol_class(grammar, "ROLLBACK"):
        table["COMPOSE"]["ROLLBACK"] = ("COMPOSE", "pop")
        table["MODE"]["ROLLBACK"] = ("MODE", "pop")

    return table
