import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AppProviders } from "@/components/AppProviders";

// Metadata untuk PWA (Requirement 12.1)
export const metadata: Metadata = {
  title: "Portal SA — Manajemen Proyek Pre-Sales",
  description:
    "Progressive Web App untuk manajemen proyek pre-sales dan aktivitas harian Solutions Architect",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Portal SA",
  },
};

// Viewport config untuk responsive (Requirement 12.3)
export const viewport: Viewport = {
  themeColor: "#3b82f6",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

/**
 * Root Layout — Layout minimal, hanya menyediakan html/body shell.
 *
 * Layout spesifik (sidebar/header untuk protected routes, atau centered
 * layout untuk auth pages) didelegasikan ke route group masing-masing:
 * - (auth)/layout.tsx  → halaman login, callback (tanpa sidebar/header)
 * - (protected)/layout.tsx → halaman app utama (dengan sidebar/header + AuthGuard)
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        {/* Preconnect untuk font Open Sans */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        {/* Icon placeholders */}
        <link rel="icon" href="/icons/icon-192x192.png" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
      </head>
      <body className="min-h-screen bg-neutral-50">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
