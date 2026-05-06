export function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-black/45 p-4 text-sm leading-6 text-slate-200">
      <code>{children}</code>
    </pre>
  );
}
