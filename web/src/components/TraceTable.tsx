import type { TraceStep } from "@/lib/runtime";

function valueOrDash(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

export function TraceTable({ trace }: { trace: TraceStep[] }) {
  if (trace.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-700 bg-slate-950/40 p-6 text-sm text-slate-400">
        No trace steps yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-800">
      <div className="max-h-[34rem] overflow-auto">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-ink-900 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-3 py-3">Token</th>
              <th className="px-3 py-3">Event</th>
              <th className="px-3 py-3">From</th>
              <th className="px-3 py-3">Action</th>
              <th className="px-3 py-3">To</th>
              <th className="px-3 py-3">Output</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-ink-950/64">
            {trace.map((step, index) => (
              <tr key={`${step.cursor ?? index}-${step.token ?? step.type}-${index}`} className="align-top">
                <td className="px-3 py-3 font-mono text-slate-100">{valueOrDash(step.token ?? step.value)}</td>
                <td className="px-3 py-3">
                  <span className="rounded border border-slate-700 bg-slate-900 px-2 py-1 font-mono text-xs text-cyan-200">
                    {valueOrDash(step.event_class ?? step.type)}
                  </span>
                </td>
                <td className="px-3 py-3 font-mono text-slate-300">{valueOrDash(step.from_state)}</td>
                <td className="px-3 py-3 font-mono text-slate-300">{valueOrDash(step.action ?? step.message)}</td>
                <td className="px-3 py-3 font-mono text-slate-300">{valueOrDash(step.to_state ?? step.state)}</td>
                <td className="px-3 py-3 font-mono text-green-200">{valueOrDash(step.output)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
