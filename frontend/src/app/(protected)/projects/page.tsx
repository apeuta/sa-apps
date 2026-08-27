"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import { useAuthStore } from "@/store/auth";
import { ProjectCard } from "@/components/ProjectCard";

/**
 * Halaman /projects — Daftar semua proyek sesuai role
 *
 * - Sales: melihat proyek miliknya
 * - SA: melihat proyek yang ditugaskan
 * - Lead_SA / Admin: melihat semua proyek
 */

interface ProjectItem {
  id_project: string;
  project_name: string;
  customer_name: string;
  status: string;
  dq_number: string | null;
  bant_score: number | null;
  use_case_tags: string[];
  target_submit: string | null;
  updated_at: string | null;
}

export default function ProjectsPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);

  // Tentukan endpoint berdasarkan role
  const getEndpoint = () => {
    if (!user) return null;
    switch (user.role) {
      case "Sales":
        return "/projects?sales_pic=me&sort=-updated_at";
      case "SA":
        return "/projects?assigned_to=me&sort=-updated_at";
      default:
        // Lead_SA dan Admin melihat semua
        return "/projects?sort=-updated_at";
    }
  };

  const { data: projects, isLoading } = useSWR<ProjectItem[]>(
    getEndpoint(),
    fetcher
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Proyek</h1>
          <p className="mt-1 text-neutral-500 text-sm">
            {user?.role === "Sales"
              ? "Daftar proyek yang Anda submit"
              : user?.role === "SA"
                ? "Proyek yang ditugaskan kepada Anda"
                : "Semua proyek aktif"}
          </p>
        </div>

        {/* Tombol buat proyek baru — hanya untuk Sales */}
        {user?.role === "Sales" && (
          <button
            onClick={() => router.push("/projects/new")}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600
                       rounded-lg hover:bg-primary-700 transition-colors duration-100
                       min-h-[44px]"
          >
            + Request Proyek Baru
          </button>
        )}
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="rounded-lg border border-neutral-200 bg-white p-4 animate-pulse"
            >
              <div className="h-4 w-36 bg-neutral-200 rounded mb-2" />
              <div className="h-3 w-28 bg-neutral-100 rounded mb-3" />
              <div className="flex justify-between">
                <div className="h-3 w-20 bg-neutral-100 rounded" />
                <div className="h-5 w-20 bg-neutral-200 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Konten */}
      {!isLoading && projects && (
        <>
          {projects.length === 0 ? (
            <div className="rounded-lg border border-neutral-200 bg-white p-12 text-center">
              <div className="mx-auto w-16 h-16 rounded-full bg-neutral-100 flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-neutral-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                Belum ada proyek
              </h3>
              <p className="text-sm text-neutral-500 mb-6">
                {user?.role === "Sales"
                  ? "Buat request proyek baru untuk memulai."
                  : "Belum ada proyek yang tersedia."}
              </p>
              {user?.role === "Sales" && (
                <button
                  onClick={() => router.push("/projects/new")}
                  className="px-5 py-2.5 text-sm font-medium text-white bg-primary-600
                             rounded-lg hover:bg-primary-700 transition-colors min-h-[44px]"
                >
                  Request Proyek Baru
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <ProjectCard
                  key={project.id_project}
                  id={project.id_project}
                  projectName={project.project_name}
                  customerName={project.customer_name}
                  status={project.status}
                  dqNumber={project.dq_number}
                  lastUpdated={project.updated_at || ""}
                  bantScore={project.bant_score}
                  onClick={() => router.push(`/projects/${project.id_project}`)}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
