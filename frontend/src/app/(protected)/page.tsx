"use client";

import { useAuthStore } from "@/store/auth";
import dynamic from "next/dynamic";

/**
 * Halaman utama (/) — redirect ke dashboard sesuai role
 *
 * Menggunakan dynamic import untuk menghindari loading semua dashboard sekaligus.
 * Setiap role punya dashboard fungsional sendiri:
 * - Sales: listing proyek miliknya
 * - SA: listing proyek assigned + activity
 * - Lead_SA: overview + utilisasi SA + effort per proyek
 * - Admin: sama dengan Lead_SA
 */

const SalesDashboard = dynamic(
  () => import("./dashboard/sales/page"),
  { loading: () => <DashboardSkeleton /> }
);

const SADashboard = dynamic(
  () => import("./dashboard/sa/page"),
  { loading: () => <DashboardSkeleton /> }
);

const LeadSADashboard = dynamic(
  () => import("./dashboard/lead-sa/page"),
  { loading: () => <DashboardSkeleton /> }
);

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-neutral-200 rounded w-1/3" />
      <div className="h-4 bg-neutral-100 rounded w-1/2" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-neutral-100 rounded-lg" />
        ))}
      </div>
      <div className="h-48 bg-neutral-100 rounded-lg" />
    </div>
  );
}

export default function HomePage() {
  const { user, isLoading } = useAuthStore();

  if (isLoading || !user) {
    return <DashboardSkeleton />;
  }

  switch (user.role) {
    case "Sales":
      return <SalesDashboard />;
    case "SA":
      return <SADashboard />;
    case "Lead_SA":
      return <LeadSADashboard />;
    case "Admin":
      return <LeadSADashboard />;
    default:
      return <SADashboard />;
  }
}
