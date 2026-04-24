import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mini Langfuse Observability Dashboard",
  description: "Hierarchical LLM tracing, prompt versioning, and NLP evaluation for interview prep."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
