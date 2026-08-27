"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import { fetcher, apiRequest } from "@/lib/fetcher";

/**
 * Komponen Project Story — timeline activity logs per proyek
 *
 * Fitur:
 * - Pilih proyek untuk melihat story/timeline
 * - Filter berdasarkan kategori dan tanggal
 * - Pagination (20 per halaman)
 * - Tampilkan AI polished notes (expandable)
 * - Tombol "Polish Ulang" jika ai_polished_notes null
 *
 * Requirements: 8.1, 8.5
 */

// Kategori subtask
const SUBTASK_CATEGORIES = [
  "Meeting Pre-Sales",
  "Create PropTek",
  "Create BOQ",
  "Peer Review",
  "Internal Discussion",
  "Customer Workshop",
] as const;

interface Project {
  id: string;
  project_name: string;
}

interface ActivityLogEntry {
  id: string;
  subtask_category: string;
  duration_hours: number;
  raw_notes: string;
  ai_polished_notes: string | null;
  created_at: string;
  gcal_event_id?: string | null;
}

interface StoryResponse {
  items: ActivityLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

interface ProjectStoryProps {
  /** Daftar proyek yang tersedia */
  projects: Project[];
}

/**
 * Warna badge berdasarkan kategori
 */
function getCategoryBadgeStyle(category: string): string {
  switch (category) {
    case "Meeting Pre-Sales":
      return "bg-blue-100 text-blue-700";
    case "Create PropTek":
      return "bg-purple-100 text-purple-700";
    case "Create BOQ":
      return "bg-orange-100 text-orange-700";
    case "Peer Review":
      return "bg-green-100 text-green-700";
    case "Internal Discussion":
      return "bg-yellow-100 text-yellow-700";
    case "Customer Workshop":
      return "bg-pink-100 text-pink-700";
    default:
      return "bg-neutral-100 text-neutral-700";
  }
}

export function ProjectStory({ projects }: ProjectStoryProps) {
  const [selectedProject, setSelectedProject] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [polishingIds, setPolishingIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const PAGE_SIZE = 20;

  // Build URL query params untuk SWR
  const buildQueryUrl = useCallback(() => {
    if (!selectedProject) return null;
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));
    if (filterCategory) params.set("category", filterCategory);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    return `/projects/${selectedProject}/story?${params.toString()}`;
  }, [selectedProject, page, filterCategory, dateFrom, dateTo]);

  // Fetch project story data
  const { data, error, isLoading, mutate } = useSWR<StoryResponse>(
    buildQueryUrl(),
    fetcher
  );

  // Toggle expand AI notes
  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Auto-dismiss toast
  const showToast = useCallback((type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // Polish ulang — POST /activity-logs/{id}/polish
  const handlePolish = useCallback(
    async (logId: string) => {
      setPolishingIds((prev) => new Set(prev).add(logId));
      try {
        await apiRequest(`/activity-logs/${logId}/polish`, { method: "POST" });
        showToast("success", "AI polishing berhasil");
        mutate(); // Refresh data
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Gagal melakukan polishing";
        showToast("error", message);
      } finally {
        setPolishingIds((prev) => {
          const next = new Set(prev);
          next.delete(logId);
          return next;
        });
      }
    },
    [mutate, showToast]
  );

  // Hitung total halaman
  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  // Format tanggal
  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-4">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
            toast.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
          role="alert"
        >
          {toast.message}
        </div>
      )}

      {/* Pilih proyek */}
      <div>
        <label htmlFor="story-project" className="block text-sm font-medium text-neutral-700 mb-1">
          Pilih Proyek
        </label>
        <select
          id="story-project"
          value={selectedProject}
          onChange={(e) => {
            setSelectedProject(e.target.value);
            setPage(1); // Reset pagination saat ganti proyek
          }}
          className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Pilih proyek untuk melihat story...</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.project_name}
            </option>
          ))}
        </select>
      </div>

      {/* Filter bar — hanya tampil jika proyek dipilih */}
      {selectedProject && (
        <div className="flex flex-wrap gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-200">
          {/* Filter kategori */}
          <div className="flex-1 min-w-[150px]">
            <label htmlFor="filter-category" className="block text-xs text-neutral-500 mb-1">
              Kategori
            </label>
            <select
              id="filter-category"
              value={filterCategory}
              onChange={(e) => {
                setFilterCategory(e.target.value);
                setPage(1);
              }}
              className="w-full px-2 py-2 border border-neutral-300 rounded-md text-sm
                focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">Semua</option>
              {SUBTASK_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Filter tanggal dari */}
          <div className="min-w-[140px]">
            <label htmlFor="filter-date-from" className="block text-xs text-neutral-500 mb-1">
              Dari
            </label>
            <input
              id="filter-date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(1);
              }}
              className="w-full px-2 py-2 border border-neutral-300 rounded-md text-sm
                focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>

          {/* Filter tanggal sampai */}
          <div className="min-w-[140px]">
            <label htmlFor="filter-date-to" className="block text-xs text-neutral-500 mb-1">
              Sampai
            </label>
            <input
              id="filter-date-to"
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(1);
              }}
              className="w-full px-2 py-2 border border-neutral-300 rounded-md text-sm
                focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
        </div>
      )}

      {/* Konten: Loading / Error / Empty / Timeline */}
      {selectedProject && (
        <div>
          {isLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse p-4 border border-neutral-200 rounded-lg">
                  <div className="h-4 bg-neutral-200 rounded w-1/4 mb-2" />
                  <div className="h-3 bg-neutral-200 rounded w-3/4 mb-1" />
                  <div className="h-3 bg-neutral-200 rounded w-1/2" />
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              Gagal memuat data: {error.message}
            </div>
          )}

          {data && data.items.length === 0 && (
            <div className="p-6 text-center text-neutral-500 border border-neutral-200 rounded-lg">
              <p className="text-sm">Belum ada activity log untuk proyek ini</p>
            </div>
          )}

          {/* Timeline list */}
          {data && data.items.length > 0 && (
            <div className="space-y-3">
              {data.items.map((log) => (
                <div
                  key={log.id}
                  className="p-4 border border-neutral-200 rounded-lg hover:border-neutral-300 transition-colors"
                >
                  {/* Header: badge kategori + tanggal + durasi */}
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${getCategoryBadgeStyle(
                        log.subtask_category
                      )}`}
                    >
                      {log.subtask_category}
                    </span>
                    <span className="text-xs text-neutral-500">{formatDate(log.created_at)}</span>
                    <span className="text-xs text-neutral-400">•</span>
                    <span className="text-xs text-neutral-600 font-medium">
                      {log.duration_hours} jam
                    </span>
                  </div>

                  {/* Raw notes */}
                  <p className="text-sm text-neutral-700 whitespace-pre-wrap">{log.raw_notes}</p>

                  {/* AI Polished Notes */}
                  {log.ai_polished_notes ? (
                    <div className="mt-3">
                      <button
                        onClick={() => toggleExpand(log.id)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium 
                          min-h-[44px] min-w-[44px] flex items-center gap-1"
                      >
                        <svg
                          className={`w-3 h-3 transition-transform ${expandedIds.has(log.id) ? "rotate-90" : ""}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        AI Polished Notes
                      </button>
                      {expandedIds.has(log.id) && (
                        <div className="mt-2 p-3 bg-blue-50 border border-blue-100 rounded-md text-sm text-neutral-700 whitespace-pre-wrap">
                          {log.ai_polished_notes}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3">
                      <button
                        onClick={() => handlePolish(log.id)}
                        disabled={polishingIds.has(log.id)}
                        className="text-xs font-medium px-3 py-1.5 rounded-md min-h-[44px] min-w-[44px]
                          bg-primary-50 text-primary-700 hover:bg-primary-100 
                          disabled:opacity-50 disabled:cursor-not-allowed
                          transition-colors"
                      >
                        {polishingIds.has(log.id) ? (
                          <span className="flex items-center gap-1">
                            <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Memproses...
                          </span>
                        ) : (
                          "Polish Ulang"
                        )}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {data && totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-xs text-neutral-500">
                Halaman {page} dari {totalPages} ({data.total} item)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-2 text-sm border border-neutral-300 rounded-md min-h-[44px] min-w-[44px]
                    hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  ← Sebelumnya
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-2 text-sm border border-neutral-300 rounded-md min-h-[44px] min-w-[44px]
                    hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Selanjutnya →
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
