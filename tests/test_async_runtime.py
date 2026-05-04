import asyncio

from keysuite import AsyncRuntime, Runtime


def test_async_runtime_processes_sessions_independently():
    async def run():
        runtime = AsyncRuntime(Runtime())
        await runtime.create_session("one")
        await runtime.create_session("two")

        first, second = await asyncio.gather(
            runtime.process(["C", "C", "SPACE"], "one"),
            runtime.process(["A", "B", "SPACE"], "two"),
        )
        return first, second

    first, second = asyncio.run(run())

    assert first["outputs"] == ["CC"]
    assert second["outputs"] == ["AB"]
