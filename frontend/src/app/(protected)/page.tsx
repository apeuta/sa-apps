/**
 * Halaman utama (Dashboard) Portal SA
 * Konten akan diisi sesuai role user di task berikutnya
 */
export default function HomePage() {
  return (
    <div className="space-y-6">
      {/* Header halaman */}
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">Dashboard</h1>
        <p className="mt-1 text-neutral-500">
          Selamat datang di Portal SA — Manajemen Proyek Pre-Sales
        </p>
      </div>

      {/* Placeholder konten dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Card placeholder - akan diisi per role */}
        <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
          <div className="skeleton h-4 w-3/4 mb-3" />
          <div className="skeleton h-8 w-1/2 mb-4" />
          <div className="skeleton h-3 w-full" />
        </div>

        <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
          <div className="skeleton h-4 w-3/4 mb-3" />
          <div className="skeleton h-8 w-1/2 mb-4" />
          <div className="skeleton h-3 w-full" />
        </div>

        <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
          <div className="skeleton h-4 w-3/4 mb-3" />
          <div className="skeleton h-8 w-1/2 mb-4" />
          <div className="skeleton h-3 w-full" />
        </div>
      </div>
    </div>
  );
}
