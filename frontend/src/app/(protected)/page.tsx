"use client";

import { useAuthStore } from "@/store/auth";
import Link from "next/link";

/**
 * Halaman utama (Dashboard) Portal SA
 * Konten berubah berdasarkan role user yang login (Bug #3 fix)
 *
 * - Sales: overview proyek + tombol request proyek baru
 * - SA: overview proyek + activity log singkat
 * - Lead_SA: overview semua proyek + statistik assignment
 * - Admin: sama seperti Lead_SA (full access)
 */

// --- Dashboard untuk Sales ---
function SalesDashboard({ userName }: { userName: string }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Dashboard</h1>
          <p className="mt-1 text-neutral-500">
            Selamat datang, {userName} — Lihat status proyek Anda
          </p>
        </div>
        {/* Tombol Request Proyek Baru */}
        <Link
          href="/projects/new"
          className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5
                     min-h-[44px] text-sm font-medium text-white shadow-sm
                     hover:bg-primary-700 transition-colors duration-100
                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Request Proyek Baru
        </Link>
      </div>

      {/* Statistik singkat */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Proyek Aktif" value="—" description="Proyek yang sedang berjalan" />
        <StatCard title="Menunggu SA" value="—" description="Proyek belum di-assign SA" />
        <StatCard title="Selesai" value="—" description="Proyek yang sudah selesai" />
      </div>

      {/* Daftar proyek terbaru */}
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-neutral-900 mb-4">Proyek Terbaru</h2>
        <p className="text-sm text-neutral-500">Data proyek akan ditampilkan di sini setelah terhubung ke backend.</p>
      </div>
    </div>
  );
}

// --- Dashboard untuk SA ---
function SADashboard({ userName }: { userName: string }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">Dashboard</h1>
        <p className="mt-1 text-neutral-500">
          Selamat datang, {userName} — Overview proyek yang di-assign ke Anda
        </p>
      </div>

      {/* Statistik singkat */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Proyek Aktif" value="—" description="Di-assign ke Anda" />
        <StatCard title="Dokumen Pending" value="—" description="Perlu review/submit" />
        <StatCard title="Deadline Minggu Ini" value="—" description="Proyek deadline terdekat" />
      </div>

      {/* Activity log singkat */}
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-neutral-900 mb-4">Activity Terbaru</h2>
        <p className="text-sm text-neutral-500">Activity log akan ditampilkan di sini setelah terhubung ke backend.</p>
      </div>
    </div>
  );
}

// --- Dashboard untuk Lead SA / Admin ---
function LeadSADashboard({ userName }: { userName: string }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">Dashboard</h1>
        <p className="mt-1 text-neutral-500">
          Selamat datang, {userName} — Overview semua proyek dan tim
        </p>
      </div>

      {/* Statistik overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Proyek" value="—" description="Semua proyek aktif" />
        <StatCard title="Belum Di-assign" value="—" description="Perlu assign SA" />
        <StatCard title="SA Aktif" value="—" description="Tim SA yang available" />
        <StatCard title="Selesai Bulan Ini" value="—" description="Proyek completed" />
      </div>

      {/* Proyek perlu perhatian */}
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-neutral-900 mb-4">Proyek Perlu Perhatian</h2>
        <p className="text-sm text-neutral-500">Daftar proyek yang belum di-assign atau mendekati deadline akan ditampilkan di sini.</p>
      </div>

      {/* Activity log tim */}
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-neutral-900 mb-4">Activity Log Tim</h2>
        <p className="text-sm text-neutral-500">Activity terbaru dari semua anggota tim akan ditampilkan di sini.</p>
      </div>
    </div>
  );
}

// --- Komponen StatCard reusable ---
function StatCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-neutral-500">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-neutral-900">{value}</p>
      <p className="mt-1 text-xs text-neutral-400">{description}</p>
    </div>
  );
}

// --- Loading state ---
function DashboardLoading() {
  return (
    <div className="space-y-6">
      <div>
        <div className="h-7 w-48 rounded bg-neutral-200 animate-pulse" />
        <div className="mt-2 h-4 w-72 rounded bg-neutral-100 animate-pulse" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
            <div className="h-4 w-3/4 rounded bg-neutral-100 animate-pulse mb-3" />
            <div className="h-8 w-1/2 rounded bg-neutral-100 animate-pulse mb-4" />
            <div className="h-3 w-full rounded bg-neutral-100 animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Halaman utama Dashboard ---
export default function HomePage() {
  const { user, isLoading } = useAuthStore();

  // Tampilkan loading jika user belum terdeteksi
  if (isLoading || !user) {
    return <DashboardLoading />;
  }

  const userName = user.full_name || "User";

  // Render dashboard sesuai role
  switch (user.role) {
    case "Sales":
      return <SalesDashboard userName={userName} />;
    case "SA":
      return <SADashboard userName={userName} />;
    case "Lead_SA":
      return <LeadSADashboard userName={userName} />;
    case "Admin":
      // Admin bisa lihat semua — gunakan view Lead SA
      return <LeadSADashboard userName={userName} />;
    default:
      return <SADashboard userName={userName} />;
  }
}
