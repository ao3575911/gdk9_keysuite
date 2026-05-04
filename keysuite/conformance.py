from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class ConformanceVector:
    id: str
    tokens: list[str]
    output: str | None
    outputs: list[str] | None
    final_state: str
    exit_code: int


@dataclass(frozen=True)
class ConformanceResult:
    id: str
    passed: bool
    expected: dict[str, Any]
    actual: dict[str, Any]
    error: str | None = None


def load_vectors(path: str | Path) -> list[ConformanceVector]:
    path = Path(path)
    vectors: list[ConformanceVector] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc

            vectors.append(
                ConformanceVector(
                    id=str(raw["id"]),
                    tokens=list(raw["tokens"]),
                    output=raw.get("output"),
                    outputs=list(raw["outputs"]) if "outputs" in raw else None,
                    final_state=str(raw["final_state"]),
                    exit_code=int(raw["exit_code"]),
                )
            )

    return vectors


def iter_vector_files(path: str | Path) -> Iterable[Path]:
    path = Path(path)

    if path.is_file():
        yield path
        return

    if not path.is_dir():
        raise FileNotFoundError(f"Conformance vector path not found: {path}")

    yield from sorted(path.glob("*.jsonl"))


RuntimeRunner = Callable[[list[str]], dict[str, Any]]


def _expected(vector: ConformanceVector) -> dict[str, Any]:
    expected: dict[str, Any] = {
        "output": vector.output,
        "final_state": vector.final_state,
        "exit_code": vector.exit_code,
    }
    if vector.outputs is not None:
        expected["outputs"] = vector.outputs
    return expected


def _actual(runtime_result: dict[str, Any]) -> dict[str, Any]:
    outputs = list(runtime_result.get("outputs", []))
    actual: dict[str, Any] = {
        "output": outputs[-1] if outputs else None,
        "final_state": str(runtime_result.get("state")),
        "exit_code": 1 if runtime_result.get("status") == "error" else 0,
    }
    if "outputs" in runtime_result:
        actual["outputs"] = outputs
    return actual


def run_vector(vector: ConformanceVector, runner: RuntimeRunner) -> ConformanceResult:
    try:
        expected = _expected(vector)
        actual = {key: value for key, value in _actual(runner(vector.tokens)).items() if key in expected}

        return ConformanceResult(
            id=vector.id,
            passed=actual == expected,
            expected=expected,
            actual=actual,
        )

    except Exception as exc:
        return ConformanceResult(
            id=vector.id,
            passed=False,
            expected=_expected(vector),
            actual={},
            error=repr(exc),
        )


def run_conformance(path: str | Path, runner: RuntimeRunner) -> list[ConformanceResult]:
    results: list[ConformanceResult] = []

    for file_path in iter_vector_files(path):
        for vector in load_vectors(file_path):
            results.append(run_vector(vector, runner))

    return results

