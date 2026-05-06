const steps = [
  { name: "Tokens", detail: "Input stream", color: "border-signal-blue text-blue-200" },
  { name: "Jurisdiction", detail: "Grammar owned symbols", color: "border-signal-cyan text-cyan-200" },
  { name: "FSM", detail: "Deterministic transitions", color: "border-signal-green text-green-200" },
  { name: "Buffer", detail: "Bounded session state", color: "border-signal-amber text-amber-200" },
  { name: "Commit", detail: "SPACE or DONE", color: "border-signal-rose text-rose-200" },
  { name: "Reducer", detail: "Pure reduction", color: "border-signal-blue text-blue-200" },
  { name: "Output", detail: "Emitted result", color: "border-signal-green text-green-200" },
];

export function FlowDiagram() {
  return (
    <div className="terminal-grid rounded-xl border border-slate-800 bg-ink-900/74 p-4 sm:p-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
        {steps.map((step, index) => (
          <div key={step.name} className="relative">
            <div className={`min-h-28 rounded-lg border bg-ink-950/82 p-4 ${step.color}`}>
              <div className="font-mono text-xs text-slate-500">0{index + 1}</div>
              <div className="mt-4 text-base font-semibold text-white">{step.name}</div>
              <div className="mt-2 text-sm text-slate-400">{step.detail}</div>
            </div>
            {index < steps.length - 1 ? (
              <div className="hidden lg:block absolute left-[calc(100%-0.35rem)] top-1/2 z-10 h-px w-4 bg-slate-600" />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
