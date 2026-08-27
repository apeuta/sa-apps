"use client";

import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import { CalendarSync } from "@/components/CalendarSync";

/**
 * Halaman Calendar Sync
 *
 * Panel untuk:
 * - Sinkronisasi Google Calendar events
 * - Mapping events ke proyek
 *
 * Requirements: 13.1, 13.2
 */

interface Project {
  id: string;
  project_name: string;
}

export default function CalendarSyncPage() {
  // Fetch daftar proyek untuk mapping dropdown
  const { data: projects, isLoading: projectsLoading } = useSWR<Project[]>(
    "/projects",
    fetcher
  );

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Calendar Sync</h1>
          <p className="mt-1 text-neutral-500 text-sm">
            Sinkronisasi Google Calendar dan mapping ke proyek
          </p>
        </div>
        {/* Link kembali ke Activity Log */}
        <a
          href="/activity-logs"
          className="px-4 py-2.5 text-sm font-medium rounded-lg min-h-[44px]
            flex items-center gap-2
            bg-white border border-neutral-300 text-neutral-700
            hover:bg-neutral-50 transition-colors"
        >
          ← Activity Log
        </a>
      </div>

      {/* Calendar Sync Panel */}
      <section className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
        {projectsLoading ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-10 bg-neutral-200 rounded w-full" />
            <div className="h-32 bg-neutral-200 rounded w-full" />
          </div>
        ) : (
          <CalendarSync projects={projects || []} />
        )}
      </section>
    </div>
  );
}
