import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { LangProvider } from "@/components/layout/LangProvider";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Hybrid Trading — Neobrutalism Dashboard",
  description: "Real-time trading dashboard with Neobrutalism design",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased`} suppressHydrationWarning>
        {/* Strip browser extension injected attributes that cause hydration mismatch */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                var clean = function() {
                  document.querySelectorAll('[bis_skin_checked]').forEach(function(el) {
                    el.removeAttribute('bis_skin_checked');
                  });
                };
                clean();
                var obs = new MutationObserver(clean);
                obs.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['bis_skin_checked'] });
              })();
            `,
          }}
        />
        {/* Strip browser extension injected attributes that cause hydration mismatch */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                var clean = function() {
                  document.querySelectorAll('[bis_skin_checked]').forEach(function(el) {
                    el.removeAttribute('bis_skin_checked');
                  });
                };
                clean();
                var obs = new MutationObserver(clean);
                obs.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['bis_skin_checked'] });
              })();
            `,
          }}
        />
        {/* Strip browser extension injected attributes that cause hydration mismatch */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                var clean = function() {
                  document.querySelectorAll('[bis_skin_checked]').forEach(function(el) {
                    el.removeAttribute('bis_skin_checked');
                  });
                };
                clean();
                var obs = new MutationObserver(clean);
                obs.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['bis_skin_checked'] });
              })();
            `,
          }}
        />
        {/* Strip browser extension injected attributes that cause hydration mismatch */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                var clean = function() {
                  document.querySelectorAll('[bis_skin_checked]').forEach(function(el) {
                    el.removeAttribute('bis_skin_checked');
                  });
                };
                clean();
                var obs = new MutationObserver(clean);
                obs.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['bis_skin_checked'] });
              })();
            `,
          }}
        />
        <ThemeProvider attribute="data-theme" defaultTheme="light" enableSystem={false}>
          <LangProvider>
            <div className="min-h-screen flex flex-col">
              <Header />
              <div className="flex flex-1">
                <Sidebar />
                <main className="flex-1 p-6 overflow-auto">
                  {children}
                </main>
              </div>
            </div>
          </LangProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
