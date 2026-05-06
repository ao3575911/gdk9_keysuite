import { ButtonLink } from "@/components/Buttons";
import { CodeBlock } from "@/components/CodeBlock";
import { SiteShell } from "@/components/SiteShell";

export default function DocsPage() {
  return (
    <SiteShell>
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-semibold text-white">API and Docs</h1>
            <p className="mt-3 text-lg leading-8 text-slate-400">
              Developer entry points for CLI use, Python imports, and the local FastAPI surface.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <ButtonLink href="https://github.com/ao3575911/gdk9_keysuite/tree/main/docs" external>
              Existing Docs
            </ButtonLink>
            <ButtonLink href="https://github.com/ao3575911/gdk9_keysuite/tree/main/site" external>
              Site Docs
            </ButtonLink>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          <article className="panel rounded-xl p-5">
            <h2 className="text-xl font-semibold text-white">CLI</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Install editable and run the canonical smoke stream.</p>
            <div className="mt-4">
              <CodeBlock>{`python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
keysuite run --tokens "C C . 3 3 SPACE"`}</CodeBlock>
            </div>
          </article>

          <article className="panel rounded-xl p-5">
            <h2 className="text-xl font-semibold text-white">Python API</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Use the package runtime directly from application code.</p>
            <div className="mt-4">
              <CodeBlock>{`from keysuite import Runtime, load_grammar

runtime = Runtime(load_grammar())
session = runtime.create_session()
result = session.process(["C", "C", ".", "3", "3", "SPACE"])
print(result["outputs"])`}</CodeBlock>
            </div>
          </article>

          <article className="panel rounded-xl p-5">
            <h2 className="text-xl font-semibold text-white">REST API</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Run the local FastAPI app and post token arrays.</p>
            <div className="mt-4">
              <CodeBlock>{`uvicorn keysuite.api:create_app --factory --reload

curl -X POST http://127.0.0.1:8000/v1/process \\
  -H 'Content-Type: application/json' \\
  -d '{"tokens":["C","C",".","3","3","SPACE"]}'`}</CodeBlock>
            </div>
          </article>
        </div>
      </section>
    </SiteShell>
  );
}
