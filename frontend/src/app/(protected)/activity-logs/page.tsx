"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import { ActivityLogForm } from "@/components/ActivityLogForm";
import { ProjectStory } from "@/components/ProjectStory";

/**
 * Halaman Activity Log
 *
 * Struktur:
 * - Bagian atas: Form input activity log baru
 * - Bagian bawah: Project Story timeline dengan filter dan pagination
 * - Link ke halaman Calendar Sync
 *
 * Requirements: 8.1, 8.5
 */

interface Project {
  id: string;
  project_name: string;
}

export default function ActivityLogsPage() {
  // Fetch daftar proyek untuk dropdown
  const { data: projects, isLoading: projectsLoading } = useSWR<Project[]>(
    "/projects",
    fetcher
  );

  // Key untuk trigger refresh ProjectStory setelah submit form
  const [refreshKey, setRefreshKey] = useState(0);

  const handleFormSuccess = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header halaman */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Activity Log</h1>
          <p className="mt-1 text-neutral-500 text-sm">
            Catat aktivitas harian dan lihat story proyek
          </p>
        </div>
        {/* Link ke Calendar Sync */}
        <a
          href="/activity-logs/calendar"
          className="px-4 py-2.5 text-sm font-medium rounded-lg min-h-[44px] 
            flex items-center gap-2
            bg-white border border-neutral-300 text-neutral-700 
            hover:bg-neutral-50 transition-colors"
        >
          📅 Calendar Sync
        </a>
      </div>

      {/* Form Input Activity Log */}
      <section className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-neutral-800 mb-4">Tambah Activity Log</h2>

        {projectsLoading ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-10 bg-neutral-200 rounded w-full" />
            <div className="h-10 bg-neutral-200 rounded w-full" />
            <div className="h-10 bg-neutral-200 rounded w-1/2" />
            <div className="h-24 bg-neutral-200 rounded w-full" />
          </div>
        ) : (
          <ActivityLogForm
            projects={projects || []}
            onSuccess={handleFormSuccess}
          />
        )}
      </section>

      {/* Project Story Timeline */}
      <section className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-neutral-800 mb-4">Project Story</h2>

        {projectsLoading ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-10 bg-neutral-200 rounded w-full" />
            <div className="h-32 bg-neutral-200 rounded w-full" />
          </div>
        ) : (
          <ProjectStory key={refreshKey} projects={projects || []} />
        )}
      </section>
    </div>
  );
}
