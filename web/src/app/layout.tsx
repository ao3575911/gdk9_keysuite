import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "GDk9 KeySuite",
  description: "Deterministic symbolic implication runtime playground and developer guide.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="min-h-screen bg-ink-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
