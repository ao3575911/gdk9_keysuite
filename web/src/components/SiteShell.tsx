import Image from "next/image";
import Link from "next/link";

const navItems = [
  { href: "/playground", label: "Playground" },
  { href: "/architecture", label: "Architecture" },
  { href: "/docs", label: "API" },
  { href: "/conformance-security", label: "Conformance" },
];

export function SiteShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-ink-950/88 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <Link href="/" className="flex min-w-0 items-center gap-3">
            <Image src="/keysuite-logo.svg" alt="KeySuite" width={158} height={36} className="h-9 w-auto rounded-md" />
          </Link>
          <nav className="flex items-center gap-1 overflow-x-auto text-sm text-slate-300">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="whitespace-nowrap rounded-md px-3 py-2 transition hover:bg-slate-800 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
