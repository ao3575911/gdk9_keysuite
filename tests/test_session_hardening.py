import asyncio

import pytest
from fastapi.testclient import TestClient

from keysuite.api import create_app
from keysuite.config import RuntimeConfig
from keysuite.errors import RuntimeLimitError
from keysuite import AsyncRuntime, Runtime


def test_runtime_enforces_max_sessions_and_idle_cleanup():
    runtime = Runtime(
        config=RuntimeConfig(
            max_sessions=1,
            session_idle_ttl_seconds=1,
            session_cleanup_interval_seconds=0,
        )
    )

    session = runtime.create_session("one")
    with pytest.raises(RuntimeLimitError):
        runtime.create_session("two")

    session.last_accessed_at -= 10
    expired = runtime.cleanup_idle_sessions()

    assert expired == ["one"]
    assert runtime.sessions == {}


def test_async_runtime_keeps_sessions_and_macros_isolated_under_concurrency():
    async def run():
        runtime = AsyncRuntime(Runtime(config=RuntimeConfig(max_sessions=4)))
        left = await runtime.create_session("left")
        right = await runtime.create_session("right")
        left.register_macro("pair", ["C", "C"])

        first, second = await asyncio.gather(
            runtime.process(["pair", "SPACE"], "left"),
            runtime.process(["A", "B", "SPACE"], "right"),
        )
        return left, right, first, second

    left, right, first, second = asyncio.run(run())

    assert first["outputs"] == ["CC"]
    assert second["outputs"] == ["AB"]
    assert "pair" in left.macros
    assert "pair" not in right.macros


def test_api_key_auth_and_rate_limit_are_enforced():
    runtime = Runtime(
        config=RuntimeConfig(
            api_keys=["secret"],
            max_requests_per_window=1,
            rate_limit_window_seconds=60,
        )
    )
    client = TestClient(create_app(runtime))

    unauthorized = client.get("/v1/health")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "UNAUTHORIZED"

    allowed = client.get("/v1/health", headers={"X-API-Key": "secret"})
    assert allowed.status_code == 200

    limited = client.get("/v1/health", headers={"X-API-Key": "secret"})
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
