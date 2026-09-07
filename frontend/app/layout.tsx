import type { Metadata } from "next";
import "./globals.css";

import { ThemeProvider } from "./components/theme-provider";

export const metadata: Metadata = {
  title: "PolarEMS 🧊⚡ | Industrial Antarctic Microgrid & Digital Twin",
  description: "Mission-critical Energy Management System & Digital Twin for Indian Antarctic Stations (Maitri & Bharati)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-50 dark:bg-[#070b13] text-slate-900 dark:text-slate-100 antialiased selection:bg-cyan-500 selection:text-white transition-colors">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
