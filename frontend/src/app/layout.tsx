import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinSight AI — Agentic Financial Intelligence",
  description:
    "Multi-agent AI platform for financial research, analysis, and citation-backed report generation. Analyze companies, compare financials, and generate equity research reports.",
  keywords: [
    "financial analysis",
    "AI research",
    "equity research",
    "RAG",
    "agentic AI",
    "fintech",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
