import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecoverX | Revenue Recovery Command Center",
  description: "Autonomous AI Revenue Recovery Layer for Digital Merchants",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-[#f8fafc] text-slate-900 min-h-screen">
        {children}
      </body>
    </html>
  );
}
