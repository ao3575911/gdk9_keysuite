# Grammar Specification

Symbols are classified as CONTENT, SYNTAX, CONTROL, COMMIT, or ESCAPE.

The canonical machine-readable grammar is `grammar/gdk9-v1.0.0.yaml`. It
declares artifact metadata, symbol jurisdiction, states, event classes, actions,
transitions, and conformance flags.

The transition compiler must reject unknown states, unknown actions, malformed
entries, and event classes without declared symbol jurisdiction.

The grammar loader also performs strict schema validation for required keys,
supported versions, unknown fields, duplicate exact tokens, transition shape,
and state reachability.

`symbols.escape.literal` declares the literal escape marker. KeySuite v1.0.0
consumes `_` before event dispatch and treats the following token as literal
`CONTENT`.

Normative source: `standards/grammar/GDk9-Grammar-Spec-v1.0.0.md`.
