"use client";

import { useMemo, useState } from "react";
import { examples, parseTokens, type RuntimeResult } from "@/lib/runtime";
import { TraceTable } from "@/components/TraceTable";

const initialInput = examples[0].tokens;

export function RuntimePlayground() {
  const [input, setInput] = useState(initialInput);
  const [result, setResult] = useState<RuntimeResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  const tokens = useMemo(() => parseTokens(input), [input]);

  async function runTokens() {
    setIsRunning(true);
    setRequestError(null);
    try {
      const response = await fetch("/api/runtime", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tokens }),
      });
      const payload = (await response.json()) as RuntimeResult;
      setResult(payload);
      if (!response.ok) {
        setRequestError(payload.error?.message ?? "Runtime request failed.");
      }
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : "Runtime request failed.");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
      <section className="panel rounded-xl p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-white">Runtime Playground</h2>
            <p className="mt-1 text-sm text-slate-400">Token streams run through the FastAPI server when configured.</p>
          </div>
          <span className="rounded border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-300">
            {tokens.length} tokens
          </span>
        </div>

        <label className="mt-6 block text-sm font-medium text-slate-300" htmlFor="token-stream">
          Token stream
        </label>
        <textarea
          id="token-stream"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          className="mt-2 min-h-36 w-full resize-y rounded-lg border-slate-700 bg-black/45 font-mono text-base text-slate-100 placeholder:text-slate-600 focus:border-signal-blue focus:ring-signal-blue"
          spellCheck={false}
        />

        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {examples.map((example) => (
            <button
              key={example.label}
              type="button"
              onClick={() => setInput(example.tokens)}
              className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-left transition hover:border-signal-blue hover:bg-slate-800/80"
            >
              <span className="block text-sm font-semibold text-white">{example.label}</span>
              <span className="mt-1 block font-mono text-xs text-slate-400">{example.tokens}</span>
              <span className="mt-2 block text-xs text-slate-500">{example.description}</span>
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={runTokens}
          disabled={isRunning || tokens.length === 0}
          className="mt-5 inline-flex w-full items-center justify-center rounded-md bg-signal-blue px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-950/40 transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-55"
        >
          {isRunning ? "Running..." : "Run token stream"}
        </button>

        {requestError ? (
          <div className="mt-4 rounded-lg border border-rose-500/40 bg-rose-950/30 p-3 text-sm text-rose-100">
            {requestError}
          </div>
        ) : null}
      </section>

      <section className="space-y-6">
        <div className="panel rounded-xl p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-white">Output</h2>
            <span
              className={`rounded border px-2.5 py-1 font-mono text-xs ${
                result?.source === "api"
                  ? "border-green-500/40 bg-green-950/30 text-green-200"
                  : "border-amber-500/40 bg-amber-950/30 text-amber-200"
              }`}
            >
              {result?.sourceLabel ?? "Not run"}
            </span>
          </div>
          <div className="mt-4 rounded-lg border border-slate-800 bg-black/45 p-4">
            <div className="font-mono text-2xl text-green-200">
              {result?.outputs.length ? result.outputs.join(" ") : "No output emitted"}
            </div>
            <div className="mt-3 text-sm text-slate-400">
              KeySuite emits only at the commit boundary. Empty output can be valid before commit.
            </div>
          </div>
          {result?.error ? (
            <div className="mt-4 rounded-lg border border-rose-500/40 bg-rose-950/30 p-4">
              <div className="font-mono text-sm text-rose-100">{result.error.type ?? "RuntimeError"}</div>
              <div className="mt-1 text-sm text-rose-100">{result.error.message}</div>
            </div>
          ) : null}
        </div>

        <div className="panel rounded-xl p-5">
          <h2 className="text-xl font-semibold text-white">State</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {[
              ["status", result?.status ?? "-"],
              ["state", result?.state ?? "-"],
              ["mode", result?.mode ?? "-"],
              ["cursor", result?.cursor ?? "-"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-slate-800 bg-slate-950/54 p-3">
                <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
                <div className="mt-1 font-mono text-sm text-slate-100">{String(value)}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/54 p-3">
            <div className="text-xs uppercase tracking-wide text-slate-500">buffer</div>
            <div className="mt-1 font-mono text-sm text-slate-100">
              {result?.buffer.length ? result.buffer.join(" ") : "[]"}
            </div>
          </div>
        </div>
      </section>

      <section className="panel rounded-xl p-5 lg:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-white">Transition Trace</h2>
          <span className="font-mono text-xs text-slate-500">{result?.trace.length ?? 0} entries</span>
        </div>
        <div className="mt-4">
          <TraceTable trace={result?.trace ?? []} />
        </div>
      </section>
    </div>
  );
}
