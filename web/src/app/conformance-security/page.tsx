import { CodeBlock } from "@/components/CodeBlock";
import { SiteShell } from "@/components/SiteShell";

const features = [
  "Conformance vectors exercise valid, invalid, escape, rollback, and abort behavior.",
  "API keys are optional and enforced on /v1 routes when configured.",
  "Rate limiting caps request volume and websocket message flow.",
  "Session isolation keeps runtime state, history, macros, and outputs separated.",
  "WebSocket governance applies handshake, payload, heartbeat, and frame limits.",
  "Release checks preserve CLI, conformance, and runtime compatibility.",
];

export default function ConformanceSecurityPage() {
  return (
    <SiteShell>
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 max-w-3xl">
          <h1 className="text-4xl font-semibold text-white">Conformance and Security</h1>
          <p className="mt-3 text-lg leading-8 text-slate-400">
            The web app presents runtime behavior without modifying grammar, reducer, CLI, API, or compatibility shims.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
          <article className="panel rounded-xl p-5">
            <h2 className="text-xl font-semibold text-white">Verification Commands</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Keep these checks green before shipping changes.</p>
            <div className="mt-4">
              <CodeBlock>{`pytest -q
keysuite conformance conformance/vectors
keysuite run --tokens "C C . 3 3 SPACE"
cd web && npm run lint && npm run typecheck && npm run build`}</CodeBlock>
            </div>
          </article>

          <article className="panel rounded-xl p-5">
            <h2 className="text-xl font-semibold text-white">Hardened Runtime Features</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {features.map((feature) => (
                <div key={feature} className="panel-muted rounded-lg p-4 text-sm leading-6 text-slate-300">
                  {feature}
                </div>
              ))}
            </div>
          </article>
        </div>
      </section>
    </SiteShell>
  );
}
