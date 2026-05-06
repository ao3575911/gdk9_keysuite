# Codebase Review Draft

Repository: [ao3575911/gdk9_keysuite](https://github.com/ao3575911/gdk9_keysuite)

This document is a GitHub-ready draft for Issues, Discussions, Projects, and Insights. It is grounded in the current checkout.

## Executive Summary

The codebase is in good shape on the core deterministic runtime path, but the highest-risk gaps are operational:

- Session TTL cleanup does not account for WebSocket heartbeat activity, so a live socket can lose its session while it is still connected.
- The async API path still runs blocking persistence work on the event loop, which becomes risky as soon as a slow or remote backend is used.
- The Redis persistence path can silently downgrade to in-memory storage when misconfigured.
- The conformance runner treats an empty vector directory as success, which can hide a broken release gate.

The core reducer and grammar validation are well covered, but the release and lifecycle edges need hardening before this should be treated as fully production-ready.

## Issues

### 1. WebSocket heartbeat traffic does not refresh session idle time

Severity: high

Labels: `bug`, `websocket`, `lifecycle`, `release-risk`

Evidence:

- `keysuite/api.py:406-410` handles `"pong"` by touching the connection only.
- `keysuite/runtime.py:717-727` expires sessions based on `session.last_accessed_at`.
- `keysuite/runtime.py:163-165` shows `RuntimeSession.touch()` is the mechanism that updates session liveness.

Why this matters:

An active WebSocket that only exchanges heartbeat traffic can still be cleaned up as "idle". That means a healthy connection can suddenly lose its session and start returning `4404` / `SessionNotFoundError` behavior even though the client is still connected.

GitHub issue draft:

Title: `Heartbeat-only WebSocket sessions can expire while the connection is still alive`

Body:

The WebSocket handler updates the connection timestamp on `"pong"`, but it does not refresh the underlying session's `last_accessed_at`. Session cleanup uses that session timestamp, so a live socket that only sends heartbeats can still be removed by idle cleanup.

Expected behavior:

- A WebSocket heartbeat should either refresh the session TTL or the API should clearly document that heartbeat traffic does not keep a session alive.

Acceptance criteria:

- Heartbeat traffic keeps the session alive, or the behavior is explicitly documented and tested.
- Add a regression test for a connected session that only receives heartbeat traffic.

### 2. Async runtime performs blocking persistence work on the event loop

Severity: high

Labels: `bug`, `performance`, `async`, `persistence`

Evidence:

- `keysuite/runtime.py:879-895` runs queued jobs by calling `runner()` directly in the worker task.
- `keysuite/runtime.py:172-180` persists session state on every update.
- `keysuite/runtime.py:504-508` persists again in the `finally` path of each token.
- `keysuite/persistence.py:108-119` shows `RedisStore.save_session()` uses synchronous client calls.

Why this matters:

If the runtime is configured with a remote or slow persistence backend, every token can block the async worker task and stall other requests. The code currently looks async at the API layer, but the persistence path remains synchronous.

GitHub issue draft:

Title: `Async API blocks on synchronous persistence calls`

Body:

The async worker executes synchronous runtime jobs directly on the event loop. Because session persistence is called on every token and the Redis store uses blocking client calls, the async API can stall under a slow backend.

Expected behavior:

- Blocking persistence should be moved off the event loop, or the backend should be made async-safe.

Acceptance criteria:

- Async processing stays responsive with a slow persistence backend.
- Add a regression test or benchmark that exercises the async path with a deliberately slow store.

### 3. Redis persistence can silently fall back to in-memory storage

Severity: medium

Labels: `bug`, `configuration`, `persistence`, `release-risk`

Evidence:

- `keysuite/runtime.py:783-787` selects `InMemoryStore()` when `persistence_backend == "redis"` but `persistence_url` is missing.
- `docs/architecture.md:51-58` describes persistence as pluggable and `RedisStore` as the external backend scaffold.

Why this matters:

A deployment that thinks it is using Redis can boot successfully while actually running with ephemeral in-memory state. That is a silent data-loss failure mode, not a safe fallback.

GitHub issue draft:

Title: `Missing Redis URL silently downgrades persistence to in-memory`

Body:

When `persistence_backend` is set to `redis` but `persistence_url` is absent, the runtime silently creates an `InMemoryStore`. That hides misconfiguration and can drop session/job state unexpectedly.

Expected behavior:

- Misconfigured Redis persistence should fail fast, or the downgrade should be explicitly logged and documented.

Acceptance criteria:

- Add a test for the `redis` backend with no URL.
- Decide whether the runtime should raise `ConfigurationError` or emit an explicit warning.

### 4. Empty conformance directories pass as a success case

Severity: medium

Labels: `bug`, `quality-gate`, `conformance`, `release-blocker`

Evidence:

- `keysuite/conformance.py:58-69` yields no files if a directory is empty.
- `keysuite/conformance.py:119-126` returns an empty result list without validation.
- `keysuite/cli.py:795-809` treats conformance as successful when there are no failures, which means an empty set can print success.

Why this matters:

A broken or mispointed vector path can produce `0/0` and still look green. That defeats the purpose of the release gate and can let a bad conformance setup ship unnoticed.

GitHub issue draft:

Title: `Conformance should fail when the vector set is empty`

Body:

The conformance runner currently treats an empty directory as a passing suite. That can hide misconfigured paths and make a broken release gate look healthy.

Expected behavior:

- Empty conformance input should be a hard failure unless it is explicitly allowed.

Acceptance criteria:

- Add a regression test for an empty vector directory.
- Make the CLI exit nonzero and report a clear error when no vectors are found.

## Discussions

### 1. Should Redis remain a scaffold or become a supported backend?

Labels: `discussion`, `architecture`, `persistence`

Prompt:

The docs currently describe `RedisStore` as a scaffold, but the runtime already exposes `persistence_backend` configuration. We need a decision on whether Redis is intentionally experimental or whether it should be promoted to a supported backend with async-safe behavior and explicit misconfiguration errors.

Decision points:

- Keep Redis as a documented scaffold and remove the impression of full support.
- Or promote it to a supported backend and move the blocking I/O off the event loop.

### 2. Should heartbeat traffic extend session lifetime?

Labels: `discussion`, `lifecycle`, `websocket`

Prompt:

The current cleanup model expires sessions based on `last_accessed_at`, but WebSocket heartbeats only refresh the connection object. Decide whether a live socket should keep its session alive, or whether session TTL should be independent of connection health.

Decision points:

- Heartbeats keep sessions alive.
- Heartbeats only keep the socket alive, and session TTL is explicit/independent.

### 3. Should conformance be strict about empty input?

Labels: `discussion`, `quality-gate`, `release`

Prompt:

Right now, an empty conformance vector set can produce a success result. Decide whether release tooling should treat that as a hard error. The safest default is to fail loudly, but that should be confirmed as the project policy.

## Projects

### 1. Runtime lifecycle hardening

Goal:

Make session lifetime, heartbeat behavior, and persistence semantics explicit and safe.

Milestones:

- Define whether heartbeat messages refresh session TTL.
- Make session cleanup and WebSocket liveness consistent.
- Add tests for idle cleanup, heartbeat-only connections, and session expiry.

Dependencies:

- A policy decision on whether heartbeat activity should count as session activity.

### 2. Async persistence hardening

Goal:

Keep the async API responsive when persistence is slow or remote.

Milestones:

- Offload blocking store writes from the event loop.
- Decide whether the persistence layer should stay sync-only or gain an async path.
- Add a slow-store regression test for the async API path.

Dependencies:

- A decision on whether Redis remains scaffold-only or becomes supported.

### 3. Release gate reliability

Goal:

Prevent false-green release checks.

Milestones:

- Fail conformance when the vector set is empty.
- Add a smoke test for the module entrypoint and `make release-check`.
- Ensure the release script reports the first failing stage clearly.

Dependencies:

- None beyond the current test suite.

## Insights

- The core deterministic runtime is solid and well tested.
- The biggest risks are not reducer correctness; they are lifecycle, persistence, and release-gate semantics.
- The codebase has already moved beyond a pure CLI toy and now behaves like a small server stack, so blocking I/O and TTL semantics matter more than they did earlier.
- The conformance harness should be treated as a release safety net, not just another green command.
- The repository is close to production shape, but the optional backend path and session lifecycle need sharper failure modes before it is dependable under load.

## Files Reviewed

- `keysuite/cli.py`
- `keysuite/api.py`
- `keysuite/runtime.py`
- `keysuite/persistence.py`
- `keysuite/security.py`
- `keysuite/transport.py`
- `keysuite/conformance.py`
- `keysuite/grammar_loader.py`
- `keysuite/reducer.py`
- `keysuite/config.py`
- `keysuite/grammar.py`
- `keysuite/schema.py`
- `keysuite/events.py`
- `docs/architecture.md`
- `docs/api.md`
- `docs/security.md`
- `tests/test_rest_api.py`
- `tests/test_websocket_api.py`
- `tests/test_async_runtime.py`
- `tests/test_session_hardening.py`
- `tests/test_config.py`

## Verification Performed

- `python -m compileall -q keysuite reference tests`
- Targeted CLI smoke checks for `--tokens`, `--trace`, `--json`, `reduce`, `validate`, `inspect-grammar`, and invalid input handling
- `run_conformance()` probe against an empty temporary directory to confirm the empty-suite false-green behavior
- Prior full-suite verification in this checkout showed `65 passed in 0.52s`
