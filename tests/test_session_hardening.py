import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from keysuite.api import create_app
from keysuite.config import RuntimeConfig
from keysuite.errors import ConfigurationError, RuntimeLimitError
from keysuite.persistence import InMemoryStore
from keysuite import AsyncRuntime, Runtime


class SlowStore(InMemoryStore):
    def __init__(self, delay_seconds: float = 0.15) -> None:
        super().__init__()
        self.delay_seconds = delay_seconds

    def save_session(self, *args, **kwargs) -> None:
        time.sleep(self.delay_seconds)
        super().save_session(*args, **kwargs)


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


def test_redis_backend_without_url_fails_fast():
    with pytest.raises(ConfigurationError, match="persistence_backend='redis' requires persistence_url"):
        Runtime(config=RuntimeConfig(persistence_backend="redis"))


def test_redis_backend_allows_explicit_store_without_url():
    runtime = Runtime(config=RuntimeConfig(persistence_backend="redis"), store=InMemoryStore())

    assert isinstance(runtime.store, InMemoryStore)


def test_async_runtime_offloads_blocking_store_work_from_event_loop():
    async def run():
        runtime = AsyncRuntime(Runtime(store=SlowStore(delay_seconds=0.2)))
        await runtime.create_session("slow")

        started = time.perf_counter()
        task = asyncio.create_task(runtime.process(["C", "SPACE"], "slow"))
        await asyncio.sleep(0.02)
        elapsed = time.perf_counter() - started
        result = await task
        return elapsed, result

    elapsed, result = asyncio.run(run())

    assert elapsed < 0.1
    assert result["outputs"] == ["C"]
