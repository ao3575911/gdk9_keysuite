import { FlowDiagram } from "@/components/FlowDiagram";
import { SiteShell } from "@/components/SiteShell";

const details = [
  {
    title: "Jurisdiction first",
    text: "The grammar declares which symbols belong to GDk9. Tokens outside jurisdiction fail clearly instead of drifting into ad hoc handling.",
  },
  {
    title: "FSM owned transitions",
    text: "The runtime maps token events to state transitions and actions. Trace rows expose from state, event class, action, and to state.",
  },
  {
    title: "Commit-bound emission",
    text: "The buffer may grow without output. Emission happens when a commit token causes reduce_and_emit.",
  },
  {
    title: "Pure reducer",
    text: "Reduction turns a committed buffer into output while remaining separate from session, API, websocket, and governance layers.",
  },
];

export default function ArchitecturePage() {
  return (
    <SiteShell>
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 max-w-3xl">
          <h1 className="text-4xl font-semibold text-white">Architecture</h1>
          <p className="mt-3 text-lg leading-8 text-slate-400">
            Tokens move through explicit jurisdiction, deterministic transitions, bounded state, and a commit boundary
            before reducer output is visible.
          </p>
        </div>
        <FlowDiagram />
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {details.map((detail) => (
            <article key={detail.title} className="panel rounded-xl p-5">
              <h2 className="text-lg font-semibold text-white">{detail.title}</h2>
              <p className="mt-3 leading-7 text-slate-400">{detail.text}</p>
            </article>
          ))}
        </div>
      </section>
    </SiteShell>
  );
}
