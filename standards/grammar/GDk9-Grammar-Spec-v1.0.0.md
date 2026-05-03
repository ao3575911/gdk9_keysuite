<img src="../../branding/logos/gdk9-logo.svg" width="180"/>

# GDk9 Grammar Specification v1.0.0

## Status

Normative for GDk9 v1.0.0.

## Canonical File

The machine-readable grammar is `grammar/gdk9-v1.0.0.yaml`. It is the control surface for KeySuite transition generation.

## Required Top-Level Fields

The grammar MUST provide:

- `version`
- `artifact`
- `standard_version`
- `keysuite_runtime_version`
- `symbols`
- `states`
- `event_classes`
- `actions`
- `transitions`
- `conformance`

## Symbol Jurisdiction

Every runtime event class MUST map to declared symbol jurisdiction:

- `CONTENT` maps to `symbols.content`
- `BIND` maps to `symbols.syntax.bind`
- `MODE_SHIFT` maps to `symbols.syntax.mode_shift`
- `COMMIT` maps to `symbols.commit`
- `ROLLBACK` maps to `symbols.control.rollback`
- `ABORT` maps to `symbols.control.abort`

Undeclared event classes MUST NOT be accepted into the transition table.

## States

GDk9 v1.0.0 requires:

- `IDLE`
- `COMPOSE`
- `MODE`
- `ERROR`

Transitions MUST reference only declared states.

## Actions

GDk9 v1.0.0 permits only these transition actions:

- `append`
- `mark_bind`
- `set_mode`
- `pop`
- `clear`
- `reduce_and_emit`
- `noop`

Unknown actions MUST be rejected before runtime execution.

## Transition Table

Each transition entry MUST define:

```yaml
EVENT_CLASS:
  next: STATE
  action: ACTION
```

The transition compiler MUST reject unknown states, unknown actions, malformed entries, and event classes without declared symbol jurisdiction.
