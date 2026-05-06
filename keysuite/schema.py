from __future__ import annotations

from packaging.version import InvalidVersion, Version

from .version import __version__


TOP_LEVEL_KEYS = {
    "version",
    "artifact",
    "standard",
    "standard_version",
    "keysuite_runtime_version",
    "purpose",
    "symbols",
    "states",
    "event_classes",
    "actions",
    "transitions",
    "conformance",
}
REQUIRED_TOP_LEVEL_KEYS = {
    "version",
    "artifact",
    "standard_version",
    "keysuite_runtime_version",
    "symbols",
    "states",
    "event_classes",
    "actions",
    "transitions",
    "conformance",
}
SYMBOL_KEYS = {"content", "syntax", "commit", "control", "escape"}
SYNTAX_KEYS = {"mode_shift", "bind"}
CONTROL_KEYS = {"rollback", "abort"}
ESCAPE_KEYS = {"literal"}
EVENT_CLASSES = {"CONTENT", "BIND", "MODE_SHIFT", "COMMIT", "ROLLBACK", "ABORT"}
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
VERSION_POLICIES = {"strict", "latest-compatible"}


def _require_mapping(value, name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def _require_string(value, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _reject_unknown_keys(value: dict, allowed: set[str], name: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        keys = ", ".join(sorted(unknown))
        raise ValueError(f"{name} has unsupported keys: {keys}")


def _parse_version(value: str, name: str) -> Version:
    try:
        return Version(value)
    except InvalidVersion as exc:
        raise ValueError(f"{name} must be a semantic version: {value!r}") from exc


def _validate_symbol_ranges(content: object) -> None:
    if not isinstance(content, list) or not content:
        raise ValueError("symbols.content must be a non-empty list")
    for index, range_spec in enumerate(content):
        _require_string(range_spec, f"symbols.content[{index}]")
        if len(range_spec) != 3 or range_spec[1] != "-":
            raise ValueError(f"symbols.content[{index}] must use single-character range syntax")
        if ord(range_spec[0]) > ord(range_spec[2]):
            raise ValueError(f"symbols.content[{index}] range start must not exceed range end")


def _validate_exact_symbol_sets(symbols: dict) -> None:
    syntax = _require_mapping(symbols.get("syntax"), "symbols.syntax")
    control = _require_mapping(symbols.get("control"), "symbols.control")
    escape = _require_mapping(symbols.get("escape", {}), "symbols.escape")
    _reject_unknown_keys(syntax, SYNTAX_KEYS, "symbols.syntax")
    _reject_unknown_keys(control, CONTROL_KEYS, "symbols.control")
    _reject_unknown_keys(escape, ESCAPE_KEYS, "symbols.escape")

    exact_sets = {
        "symbols.syntax.bind": [_require_string(syntax.get("bind"), "symbols.syntax.bind")],
        "symbols.syntax.mode_shift": [
            _require_string(syntax.get("mode_shift"), "symbols.syntax.mode_shift")
        ],
        "symbols.control.rollback": [
            _require_string(control.get("rollback"), "symbols.control.rollback")
        ],
        "symbols.control.abort": [_require_string(control.get("abort"), "symbols.control.abort")],
        "symbols.commit": symbols.get("commit"),
    }
    if escape:
        exact_sets["symbols.escape.literal"] = [
            _require_string(escape.get("literal"), "symbols.escape.literal")
        ]
    if not isinstance(exact_sets["symbols.commit"], list) or not exact_sets["symbols.commit"]:
        raise ValueError("symbols.commit must be a non-empty list")

    seen: dict[str, str] = {}
    for name, values in exact_sets.items():
        if not isinstance(values, list):
            raise ValueError(f"{name} must be a list")
        for value in values:
            _require_string(value, name)
            if value in seen:
                raise ValueError(f"symbol token {value!r} is declared by both {seen[value]} and {name}")
            seen[value] = name


def _validate_event_classes(grammar: dict) -> None:
    event_classes = _require_mapping(grammar.get("event_classes"), "event_classes")
    unknown = set(event_classes) - EVENT_CLASSES
    missing = EVENT_CLASSES - set(event_classes)
    if unknown:
        raise ValueError(f"event_classes has unsupported keys: {', '.join(sorted(unknown))}")
    if missing:
        raise ValueError(f"event_classes is missing required keys: {', '.join(sorted(missing))}")


def _validate_states(grammar: dict) -> None:
    states = grammar.get("states")
    if not isinstance(states, list) or not all(isinstance(state, str) for state in states):
        raise ValueError("states must be a list of strings")
    missing = REQUIRED_STATES - set(states)
    if missing:
        raise ValueError(f"states is missing required keys: {', '.join(sorted(missing))}")


def _validate_actions(grammar: dict) -> None:
    actions = _require_mapping(grammar.get("actions"), "actions")
    unknown = set(actions) - ALLOWED_ACTIONS
    missing = ALLOWED_ACTIONS - set(actions)
    if unknown:
        raise ValueError(f"actions has unsupported keys: {', '.join(sorted(unknown))}")
    if missing:
        raise ValueError(f"actions is missing required keys: {', '.join(sorted(missing))}")


def _validate_transitions(grammar: dict) -> None:
    states = set(grammar["states"])
    transitions = _require_mapping(grammar.get("transitions"), "transitions")
    for state, rules in transitions.items():
        if state not in states:
            raise ValueError(f"transitions uses unknown state: {state}")
        rules = _require_mapping(rules, f"transitions.{state}")
        for event_class, spec in rules.items():
            if event_class not in EVENT_CLASSES:
                raise ValueError(f"transitions.{state} uses unsupported event class: {event_class}")
            spec = _require_mapping(spec, f"transitions.{state}.{event_class}")
            _reject_unknown_keys(spec, {"next", "action"}, f"transitions.{state}.{event_class}")
            if spec.get("next") not in states:
                raise ValueError(
                    f"transitions.{state}.{event_class} uses unknown next state: {spec.get('next')}"
                )
            if spec.get("action") not in ALLOWED_ACTIONS:
                raise ValueError(
                    f"transitions.{state}.{event_class} uses unknown action: {spec.get('action')}"
                )


def _validate_reachability(grammar: dict) -> None:
    transitions = grammar["transitions"]
    reachable = {"IDLE"}
    changed = True
    while changed:
        changed = False
        for state in list(reachable):
            for spec in transitions.get(state, {}).values():
                next_state = spec["next"]
                if next_state not in reachable:
                    reachable.add(next_state)
                    changed = True

    missing = (set(grammar["states"]) - {"ERROR"}) - reachable
    if missing:
        raise ValueError(f"states are unreachable from IDLE: {', '.join(sorted(missing))}")


def _check_version_policy(grammar_version: Version, runtime_version: Version, policy: str) -> None:
    if policy not in VERSION_POLICIES:
        raise ValueError(f"unsupported version policy: {policy}")

    if policy == "strict":
        if grammar_version.release != runtime_version.release:
            raise ValueError(f"unsupported grammar version: {grammar_version}")
        return

    runtime_major = runtime_version.release[0] if runtime_version.release else 0
    grammar_major = grammar_version.release[0] if grammar_version.release else 0
    if runtime_major != grammar_major:
        raise ValueError(f"unsupported grammar version: {grammar_version}")
    if runtime_version.release < grammar_version.release:
        raise ValueError(f"unsupported grammar version: {grammar_version}")


def validate_grammar(
    grammar: dict,
    *,
    runtime_version: str | None = None,
    version_policy: str = "latest-compatible",
) -> dict:
    grammar = _require_mapping(grammar, "GDk9 grammar")
    _reject_unknown_keys(grammar, TOP_LEVEL_KEYS, "GDk9 grammar")
    missing = REQUIRED_TOP_LEVEL_KEYS - set(grammar)
    if missing:
        raise ValueError(f"GDk9 grammar is missing required keys: {', '.join(sorted(missing))}")

    grammar_version = _parse_version(_require_string(grammar.get("version"), "version"), "version")
    standard_version = _parse_version(
        _require_string(grammar.get("standard_version"), "standard_version"), "standard_version"
    )
    runtime_floor = _parse_version(
        _require_string(grammar.get("keysuite_runtime_version"), "keysuite_runtime_version"),
        "keysuite_runtime_version",
    )
    runtime_version = runtime_version or __version__
    runtime_version_parsed = _parse_version(runtime_version, "runtime_version")

    _check_version_policy(grammar_version, runtime_version_parsed, version_policy)
    if runtime_version_parsed.release < runtime_floor.release:
        raise ValueError(
            f"unsupported KeySuite runtime version: {grammar.get('keysuite_runtime_version')}"
        )
    if standard_version.release != grammar_version.release:
        # Keep the check flexible, but surface clearly if the grammar and standard diverge.
        raise ValueError(
            f"grammar version {grammar_version} does not match standard version {standard_version}"
        )

    symbols = _require_mapping(grammar.get("symbols"), "symbols")
    _reject_unknown_keys(symbols, SYMBOL_KEYS, "symbols")
    _validate_symbol_ranges(symbols.get("content"))
    _validate_exact_symbol_sets(symbols)
    _validate_event_classes(grammar)
    _validate_states(grammar)
    _validate_actions(grammar)
    _validate_transitions(grammar)
    _validate_reachability(grammar)
    return grammar
