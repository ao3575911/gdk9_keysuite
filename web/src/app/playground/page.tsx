import { RuntimePlayground } from "@/components/RuntimePlayground";
import { SiteShell } from "@/components/SiteShell";

export default function PlaygroundPage() {
  return (
    <SiteShell>
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 max-w-3xl">
          <h1 className="text-4xl font-semibold text-white">Runtime Playground</h1>
          <p className="mt-3 text-lg leading-8 text-slate-400">
            Run GDk9 token streams, inspect output, and read the transition trace without changing the Python runtime.
          </p>
        </div>
        <RuntimePlayground />
      </section>
    </SiteShell>
  );
}
