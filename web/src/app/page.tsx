import { ButtonLink } from "@/components/Buttons";
import { CodeBlock } from "@/components/CodeBlock";
import { FlowDiagram } from "@/components/FlowDiagram";
import { SiteShell } from "@/components/SiteShell";

const principles = [
  "Symbols enter explicit jurisdiction before the runtime accepts them.",
  "A finite state machine processes token events deterministically.",
  "Output is emitted only at the commit boundary.",
  "The reducer remains pure and owns symbolic reduction.",
];

export default function Home() {
  return (
    <SiteShell>
      <section className="relative overflow-hidden border-b border-slate-900">
        <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
          <div>
            <div className="mb-6 inline-flex rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1 font-mono text-xs text-cyan-200">
              GDk9 symbolic implication infrastructure
            </div>
            <h1 className="max-w-4xl text-5xl font-semibold tracking-normal text-white sm:text-6xl lg:text-7xl">
              GDk9 KeySuite
            </h1>
            <p className="mt-6 max-w-2xl text-xl leading-8 text-slate-300">
              Deterministic symbolic implication runtime for developers building against the GDk9 reference stack.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/playground" variant="primary">
                Try Runtime
              </ButtonLink>
              <ButtonLink href="/docs">Read Docs</ButtonLink>
              <ButtonLink href="https://github.com/ao3575911/gdk9_keysuite" external>
                View GitHub
              </ButtonLink>
            </div>
          </div>

          <div className="panel rounded-xl p-5">
            <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="font-mono text-sm text-slate-400">runtime trace</span>
              <span className="rounded border border-green-500/30 bg-green-950/30 px-2 py-1 font-mono text-xs text-green-200">
                deterministic
              </span>
            </div>
            <CodeBlock>{`$ keysuite run --tokens "C C . 3 3 SPACE"
CC→33

CONTENT C      IDLE    -> COMPOSE
BIND    .      COMPOSE -> COMPOSE
COMMIT  SPACE  COMPOSE -> IDLE`}</CodeBlock>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {principles.map((principle) => (
                <div key={principle} className="panel-muted rounded-lg p-4 text-sm leading-6 text-slate-300">
                  {principle}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-8 max-w-3xl">
          <h2 className="text-3xl font-semibold text-white">Runtime Architecture</h2>
          <p className="mt-3 text-slate-400">
            KeySuite keeps token jurisdiction, state transitions, buffered composition, commit behavior, and pure
            reduction separate so conformance remains inspectable.
          </p>
        </div>
        <FlowDiagram />
      </section>
    </SiteShell>
  );
}
