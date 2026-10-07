import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Intraday Trading Agent India | Financial Terminal",
  description: "Production-grade AI Intraday Trading & Paper Execution Platform for Indian Stock Market",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090c10] text-[#e6edf3] min-h-screen flex flex-col antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
