"use client";

import { useState, useCallback } from "react";
import { apiRequest } from "@/lib/fetcher";

/**
 * Form untuk mencatat Activity Log
 *
 * Field:
 * - Proyek (dropdown)
 * - Kategori subtask (dropdown 6 opsi)
 * - Durasi (0.25–24 jam, step 0.25)
 * - Catatan (textarea max 5000 karakter)
 *
 * Requirements: 8.1, 8.5
 */

// Kategori subtask yang tersedia
const SUBTASK_CATEGORIES = [
  "Meeting Pre-Sales",
  "Create PropTek",
  "Create BOQ",
  "Peer Review",
  "Internal Discussion",
  "Customer Workshop",
] as const;

type SubtaskCategory = (typeof SUBTASK_CATEGORIES)[number];

interface Project {
  id: string;
  project_name: string;
}

interface ActionItem {
  description: string;
  pic?: string | null;
}

interface AiPolishedNotes {
  discussion_points: string[];
  action_items: ActionItem[];
}

interface ActivityLogFormProps {
  /** Daftar proyek yang tersedia untuk dipilih */
  projects: Project[];
  /** Callback setelah berhasil submit */
  onSuccess?: () => void;
}

interface FormErrors {
  id_project?: string;
  subtask_category?: string;
  duration_hours?: string;
  raw_notes?: string;
}

const MAX_NOTES_LENGTH = 5000;

export function ActivityLogForm({ projects, onSuccess }: ActivityLogFormProps) {
  const [idProject, setIdProject] = useState("");
  const [category, setCategory] = useState<SubtaskCategory | "">("");
  const [duration, setDuration] = useState<string>("1");
  const [rawNotes, setRawNotes] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [polishedNotes, setPolishedNotes] = useState<AiPolishedNotes | null>(null);

  // Auto-dismiss toast setelah 3 detik
  const showToast = useCallback((type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  }, []);

  /**
   * Validasi form sebelum submit
   */
  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!idProject) {
      newErrors.id_project = "Proyek wajib dipilih";
    }
    if (!category) {
      newErrors.subtask_category = "Kategori wajib dipilih";
    }

    const dur = parseFloat(duration);
    if (isNaN(dur) || dur < 0.25 || dur > 24) {
      newErrors.duration_hours = "Durasi harus antara 0.25 - 24 jam";
    }

    if (!rawNotes.trim()) {
      newErrors.raw_notes = "Catatan tidak boleh kosong";
    } else if (rawNotes.length > MAX_NOTES_LENGTH) {
      newErrors.raw_notes = `Catatan maksimal ${MAX_NOTES_LENGTH} karakter`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [idProject, category, duration, rawNotes]);

  /**
   * Handle submit form — POST ke /api/v1/activity-logs
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validate()) return;

      setIsSubmitting(true);
      try {
        const result = await apiRequest<{ ai_polished_notes?: AiPolishedNotes }>("/activity-logs", {
          method: "POST",
          body: {
            id_project: idProject,
            subtask_category: category,
            duration_hours: parseFloat(duration),
            raw_notes: rawNotes.trim(),
          },
        });

        // Tampilkan action items dari AI polishing jika ada
        if (result.ai_polished_notes?.action_items?.length) {
          setPolishedNotes(result.ai_polished_notes);
        } else {
          setPolishedNotes(null);
        }

        showToast("success", "Activity log berhasil disimpan");
        // Reset form
        setIdProject("");
        setCategory("");
        setDuration("1");
        setRawNotes("");
        setErrors({});
        onSuccess?.();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Gagal menyimpan activity log";
        showToast("error", message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [idProject, category, duration, rawNotes, validate, onSuccess, showToast]
  );

  return (
    <div className="relative">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all duration-300 ${
            toast.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
          role="alert"
        >
          {toast.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5" aria-label="Form activity log">
        {/* Pilih Proyek */}
        <div>
          <label htmlFor="log-project" className="block text-sm font-medium text-neutral-700 mb-1">
            Proyek <span className="text-red-500">*</span>
          </label>
          <select
            id="log-project"
            value={idProject}
            onChange={(e) => {
              setIdProject(e.target.value);
              if (errors.id_project) setErrors((prev) => ({ ...prev, id_project: undefined }));
            }}
            disabled={isSubmitting}
            className={`w-full px-3 py-2.5 border rounded-lg text-sm
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              disabled:opacity-50 disabled:bg-neutral-100
              ${errors.id_project ? "border-red-300 bg-red-50" : "border-neutral-300"}`}
            aria-invalid={!!errors.id_project}
          >
            <option value="">Pilih proyek...</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_name}
              </option>
            ))}
          </select>
          {errors.id_project && (
            <p className="text-xs text-red-600 mt-1" role="alert">{errors.id_project}</p>
          )}
        </div>

        {/* Kategori Subtask */}
        <div>
          <label htmlFor="log-category" className="block text-sm font-medium text-neutral-700 mb-1">
            Kategori <span className="text-red-500">*</span>
          </label>
          <select
            id="log-category"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value as SubtaskCategory);
              if (errors.subtask_category) setErrors((prev) => ({ ...prev, subtask_category: undefined }));
            }}
            disabled={isSubmitting}
            className={`w-full px-3 py-2.5 border rounded-lg text-sm
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              disabled:opacity-50 disabled:bg-neutral-100
              ${errors.subtask_category ? "border-red-300 bg-red-50" : "border-neutral-300"}`}
            aria-invalid={!!errors.subtask_category}
          >
            <option value="">Pilih kategori...</option>
            {SUBTASK_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          {errors.subtask_category && (
            <p className="text-xs text-red-600 mt-1" role="alert">{errors.subtask_category}</p>
          )}
        </div>

        {/* Durasi */}
        <div>
          <label htmlFor="log-duration" className="block text-sm font-medium text-neutral-700 mb-1">
            Durasi (jam) <span className="text-red-500">*</span>
          </label>
          <input
            id="log-duration"
            type="number"
            min="0.25"
            max="24"
            step="0.25"
            value={duration}
            onChange={(e) => {
              setDuration(e.target.value);
              if (errors.duration_hours) setErrors((prev) => ({ ...prev, duration_hours: undefined }));
            }}
            disabled={isSubmitting}
            className={`w-full px-3 py-2.5 border rounded-lg text-sm
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              disabled:opacity-50 disabled:bg-neutral-100
              ${errors.duration_hours ? "border-red-300 bg-red-50" : "border-neutral-300"}`}
            aria-invalid={!!errors.duration_hours}
          />
          {errors.duration_hours && (
            <p className="text-xs text-red-600 mt-1" role="alert">{errors.duration_hours}</p>
          )}
        </div>

        {/* Catatan */}
        <div>
          <label htmlFor="log-notes" className="block text-sm font-medium text-neutral-700 mb-1">
            Catatan <span className="text-red-500">*</span>
          </label>
          <textarea
            id="log-notes"
            value={rawNotes}
            onChange={(e) => {
              setRawNotes(e.target.value);
              if (errors.raw_notes) setErrors((prev) => ({ ...prev, raw_notes: undefined }));
            }}
            disabled={isSubmitting}
            maxLength={MAX_NOTES_LENGTH}
            rows={4}
            placeholder="Tuliskan catatan aktivitas..."
            className={`w-full px-3 py-2.5 border rounded-lg text-sm resize-none
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              disabled:opacity-50 disabled:bg-neutral-100
              ${errors.raw_notes ? "border-red-300 bg-red-50" : "border-neutral-300"}`}
            aria-invalid={!!errors.raw_notes}
          />
          <div className="flex justify-between items-center mt-1">
            {errors.raw_notes ? (
              <p className="text-xs text-red-600" role="alert">{errors.raw_notes}</p>
            ) : (
              <span />
            )}
            <p className={`text-xs ${rawNotes.length > MAX_NOTES_LENGTH ? "text-red-600" : "text-neutral-400"}`}>
              {rawNotes.length}/{MAX_NOTES_LENGTH}
            </p>
          </div>
        </div>

        {/* Tombol Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-2.5 px-4 rounded-lg font-medium text-white 
            transition-all duration-200 min-h-[44px]
            ${isSubmitting
              ? "bg-neutral-400 cursor-not-allowed"
              : "bg-primary-600 hover:bg-primary-700 active:bg-primary-800"
            }`}
        >
          {isSubmitting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Menyimpan...
            </span>
          ) : (
            "Simpan Activity Log"
          )}
        </button>
      </form>

      {/* Action Items dari AI polishing */}
      {polishedNotes && polishedNotes.action_items.length > 0 && (
        <div className="mt-5 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 className="text-sm font-semibold text-amber-800 mb-2">Action Items</h3>
          <ul className="space-y-1.5">
            {polishedNotes.action_items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-amber-900">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>
                  {item.description}
                  {item.pic && (
                    <span className="text-amber-600 ml-1">(PIC: {item.pic})</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
          <button
            onClick={() => setPolishedNotes(null)}
            className="mt-3 text-xs text-amber-600 hover:text-amber-800 underline"
          >
            Tutup
          </button>
        </div>
      )}
    </div>
  );
}
