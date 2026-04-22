import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mini Langfuse Dashboard",
  description: "A lightweight LLM observability dashboard built for interview prep."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

