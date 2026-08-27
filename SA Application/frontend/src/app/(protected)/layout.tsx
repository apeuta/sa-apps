"use client";

import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { AuthGuard } from "@/components/AuthGuard";

/**
 * Layout untuk halaman yang memerlukan autentikasi (protected routes)
 *
 * Struktur (Requirement 19.7):
 * - AuthGuard: validasi token sebelum render
 * - Sidebar navigation: collapsible (240px terbuka / 64px collapsed)
 * - Header: tinggi maksimal 64px
 * - Main content area: minimal 60% viewport width
 */
export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar Navigation — collapsible 240px/64px */}
        <Sidebar />

        {/* Area konten utama */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Header — tinggi maks 64px */}
          <Header />

          {/* Main Content — min 60% viewport width */}
          <main className="flex-1 overflow-y-auto p-4 md:p-6 min-w-[60vw]">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
