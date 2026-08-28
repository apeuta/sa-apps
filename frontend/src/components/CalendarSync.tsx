"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import { fetcher, apiRequest } from "@/lib/fetcher";

/**
 * Komponen Calendar Sync — sinkronisasi Google Calendar events
 *
 * Fitur:
 * - Tombol "Sync Calendar" untuk fetch events dari GCal
 * - Daftar events yang tersinkronisasi
 * - Tombol "Map ke Proyek" untuk setiap event → modal mapping
 * - Setelah mapping berhasil, event ditandai ✓
 *
 * Requirements: 13.1, 13.2
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

interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start: string;
  end: string;
  is_all_day: boolean;
  is_mapped?: boolean;
}

interface CalendarSyncProps {
  /** Daftar proyek untuk mapping */
  projects: Project[];
}

interface MapFormState {
  project_id: string;
  subtask_category: string;
  duration_hours: string;
  raw_notes: string;
}

export function CalendarSync({ projects }: CalendarSyncProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [mappedIds, setMappedIds] = useState<Set<string>>(new Set());
  const [mappingEventId, setMappingEventId] = useState<string | null>(null);
  const [mapForm, setMapForm] = useState<MapFormState>({
    project_id: "",
    subtask_category: "",
    duration_hours: "1",
    raw_notes: "",
  });
  const [isMapping, setIsMapping] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Auto-dismiss toast
  const showToast = useCallback((type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  }, []);

  /**
   * Check URL hash untuk gcal_token setelah redirect dari Google OAuth.
   * Format: #gcal_token=xxx atau #gcal_error=xxx
   */
  useState(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash;
    if (!hash) return;

    const tokenMatch = hash.match(/gcal_token=([^&]+)/);
    const errorMatch = hash.match(/gcal_error=([^&]+)/);

    if (tokenMatch) {
      localStorage.setItem("google_calendar_token", decodeURIComponent(tokenMatch[1]));
      // Bersihkan hash dari URL
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    } else if (errorMatch) {
      localStorage.removeItem("google_calendar_token");
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  });

  /**
   * Redirect ke Google OAuth untuk mendapatkan Calendar access token.
   */
  const redirectToGoogleAuth = useCallback(async () => {
    try {
      const result = await fetcher<{ auth_url: string }>("/calendar/auth-url");
      window.location.href = result.auth_url;
    } catch {
      showToast("error", "Gagal memulai otorisasi Google Calendar");
    }
  }, [showToast]);

  /**
   * Sync calendar — POST /calendar/sync dengan google_calendar_token dari localStorage.
   * Jika token belum ada, redirect ke Google OAuth dulu.
   */
  const handleSync = useCallback(async () => {
    let gcalToken = localStorage.getItem("google_calendar_token");

    if (!gcalToken) {
      // Belum ada token Google Calendar — redirect ke OAuth
      showToast("success", "Mengarahkan ke Google untuk otorisasi Calendar...");
      await redirectToGoogleAuth();
      return;
    }

    setIsSyncing(true);
    try {
      const result = await apiRequest<CalendarEvent[]>("/calendar/sync", {
        method: "POST",
        body: { access_token: gcalToken },
      });
      setEvents(Array.isArray(result) ? result : []);
      showToast("success", "Calendar berhasil disinkronisasi");
    } catch (err: unknown) {
      // Jika token expired/invalid, hapus dan minta re-auth
      const message = err instanceof Error ? err.message : "Gagal sync calendar";
      if (message.includes("401") || message.includes("403") || message.includes("invalid")) {
        localStorage.removeItem("google_calendar_token");
        showToast("error", "Token Google Calendar kedaluwarsa. Silakan coba sync ulang.");
      } else {
        showToast("error", message);
      }
    } finally {
      setIsSyncing(false);
    }
  }, [showToast, redirectToGoogleAuth]);

  /**
   * Buka modal mapping untuk event tertentu
   */
  const openMappingModal = (eventId: string) => {
    const event = events.find((e) => e.id === eventId);
    setMappingEventId(eventId);
    setMapForm({
      project_id: "",
      subtask_category: "",
      duration_hours: event ? calculateDuration(event.start, event.end) : "1",
      raw_notes: event?.description || "",
    });
  };

  /**
   * Hitung durasi dari start-end dalam jam
   */
  const calculateDuration = (start: string, end: string): string => {
    const diff = (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60 * 60);
    return diff > 0 ? Math.round(diff * 4) / 4 + "" : "1"; // Round ke 0.25
  };

  /**
   * Submit mapping — POST /calendar/map
   */
  const handleMap = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!mappingEventId || !mapForm.project_id || !mapForm.subtask_category) {
        showToast("error", "Proyek dan kategori wajib dipilih");
        return;
      }

      const event = events.find((ev) => ev.id === mappingEventId);
      if (!event) return;

      setIsMapping(true);
      try {
        await apiRequest("/calendar/map", {
          method: "POST",
          body: {
            gcal_event_id: mappingEventId,
            project_id: mapForm.project_id,
            subtask_category: mapForm.subtask_category,
            duration_hours: parseFloat(mapForm.duration_hours) || undefined,
            raw_notes: mapForm.raw_notes.trim() || undefined,
            event_title: event.title,
            event_description: event.description || undefined,
            is_all_day: event.is_all_day,
            event_start: event.start,
            event_end: event.end,
          },
        });

        setMappedIds((prev) => new Set(prev).add(mappingEventId));
        setMappingEventId(null);
        showToast("success", "Event berhasil di-mapping ke proyek");
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Gagal mapping event";
        showToast("error", message);
      } finally {
        setIsMapping(false);
      }
    },
    [mappingEventId, mapForm, events, showToast]
  );

  // Format waktu event
  const formatEventTime = (iso: string) => {
    return new Date(iso).toLocaleString("id-ID", {
      day: "numeric",
      month: "short",
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

      {/* Header: Tombol Sync */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-neutral-700">Google Calendar Events</h3>
        <button
          onClick={handleSync}
          disabled={isSyncing}
          className="px-4 py-2 text-sm font-medium rounded-lg min-h-[44px]
            bg-primary-600 text-white hover:bg-primary-700 
            disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSyncing ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Syncing...
            </span>
          ) : (
            "Sync Calendar"
          )}
        </button>
      </div>

      {/* Daftar events */}
      {events.length === 0 ? (
        <div className="p-6 text-center text-neutral-500 border border-neutral-200 rounded-lg">
          <p className="text-sm">Klik &quot;Sync Calendar&quot; untuk mengambil events terbaru</p>
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((event) => {
            const isMapped = mappedIds.has(event.id) || event.is_mapped;
            return (
              <div
                key={event.id}
                className={`p-4 border rounded-lg transition-colors ${
                  isMapped
                    ? "border-green-200 bg-green-50"
                    : "border-neutral-200 hover:border-neutral-300"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-medium text-neutral-800 truncate">
                        {event.title}
                      </h4>
                      {event.is_all_day && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-neutral-100 text-neutral-600 rounded">
                          All Day
                        </span>
                      )}
                      {isMapped && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-green-100 text-green-700 rounded">
                          ✓ Mapped
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-neutral-500">
                      {formatEventTime(event.start)} — {formatEventTime(event.end)}
                    </p>
                    {event.description && (
                      <p className="text-xs text-neutral-400 mt-1 truncate">{event.description}</p>
                    )}
                  </div>

                  {/* Tombol Map ke Proyek */}
                  {!isMapped && (
                    <button
                      onClick={() => openMappingModal(event.id)}
                      className="shrink-0 px-3 py-2 text-xs font-medium rounded-md min-h-[44px] min-w-[44px]
                        bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors"
                    >
                      Map ke Proyek
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Mapping */}
      {mappingEventId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold text-neutral-800 mb-4">Map Event ke Proyek</h3>
            <p className="text-sm text-neutral-500 mb-4">
              {events.find((e) => e.id === mappingEventId)?.title}
            </p>

            <form onSubmit={handleMap} className="space-y-4">
              {/* Pilih proyek */}
              <div>
                <label htmlFor="map-project" className="block text-sm font-medium text-neutral-700 mb-1">
                  Proyek <span className="text-red-500">*</span>
                </label>
                <select
                  id="map-project"
                  value={mapForm.project_id}
                  onChange={(e) => setMapForm((f) => ({ ...f, project_id: e.target.value }))}
                  className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm
                    focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Pilih proyek...</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.project_name}</option>
                  ))}
                </select>
              </div>

              {/* Kategori */}
              <div>
                <label htmlFor="map-category" className="block text-sm font-medium text-neutral-700 mb-1">
                  Kategori <span className="text-red-500">*</span>
                </label>
                <select
                  id="map-category"
                  value={mapForm.subtask_category}
                  onChange={(e) => setMapForm((f) => ({ ...f, subtask_category: e.target.value }))}
                  className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm
                    focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Pilih kategori...</option>
                  {SUBTASK_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              {/* Durasi */}
              <div>
                <label htmlFor="map-duration" className="block text-sm font-medium text-neutral-700 mb-1">
                  Durasi (jam)
                </label>
                <input
                  id="map-duration"
                  type="number"
                  min="0.25"
                  max="24"
                  step="0.25"
                  value={mapForm.duration_hours}
                  onChange={(e) => setMapForm((f) => ({ ...f, duration_hours: e.target.value }))}
                  className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm
                    focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Catatan */}
              <div>
                <label htmlFor="map-notes" className="block text-sm font-medium text-neutral-700 mb-1">
                  Catatan
                </label>
                <textarea
                  id="map-notes"
                  value={mapForm.raw_notes}
                  onChange={(e) => setMapForm((f) => ({ ...f, raw_notes: e.target.value }))}
                  rows={3}
                  placeholder="Catatan opsional..."
                  className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm resize-none
                    focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Tombol aksi */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setMappingEventId(null)}
                  disabled={isMapping}
                  className="flex-1 py-2.5 px-4 rounded-lg font-medium text-neutral-700
                    border border-neutral-300 hover:bg-neutral-50 min-h-[44px]
                    disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={isMapping}
                  className={`flex-1 py-2.5 px-4 rounded-lg font-medium text-white min-h-[44px]
                    transition-all ${
                      isMapping
                        ? "bg-neutral-400 cursor-not-allowed"
                        : "bg-primary-600 hover:bg-primary-700"
                    }`}
                >
                  {isMapping ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Mapping...
                    </span>
                  ) : (
                    "Simpan Mapping"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
