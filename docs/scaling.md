# Scaling

KeySuite is still a local deterministic runtime, but the hardened architecture makes the state boundaries explicit so the same core can be deployed behind persistent APIs.

## Stateless Components

- `RuntimeConfig` loading
- grammar loading and schema validation
- reducer logic
- FSM transition generation
- event serialization

These pieces are safe to scale horizontally because they are deterministic and input-derived.

## Stateful Components

- `SessionManager`
- `RuntimeSession`
- `ConnectionManager`
- rate limiters
- persistence backend

These components require explicit isolation because they carry request history, macro context, websocket state, and lifecycle bookkeeping.

## Horizontal Scaling Model

The recommended model is:

1. Keep the reducer and grammar read-only.
2. Store session state in-memory for single-node deployments.
3. Move session persistence to Redis or another external store if you need cross-process recovery.
4. Use sticky routing or a session-aware gateway for websocket deployments.
5. Treat websocket connections as node-local resources and close them when the owning session is destroyed or expires.

## Backpressure

The async runtime can use a bounded `asyncio.Queue` to absorb burst traffic.

- `max_queue_size` bounds outstanding jobs.
- Overload raises a structured runtime limit error instead of blocking indefinitely.
- Per-connection message rate limiting prevents a single websocket from dominating the session.

## Performance Notes

- The kernel and reducer remain synchronous and deterministic.
- Session cleanup is periodic and bounded.
- Event publication is in-process and does not change the FSM result.
- Zero-copy optimizations should be limited to buffer handling paths that do not alter output ordering or token jurisdiction checks.
