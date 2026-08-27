"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import { useAuthStore } from "@/store/auth";
import { HandoverModal } from "@/components/HandoverModal";
import { HandoverConfigForm } from "@/components/HandoverConfigForm";
import type { HandoverStatus } from "@/lib/api/handover";

/**
 * Halaman Detail Proyek
 *
 * Menampilkan informasi lengkap proyek:
 * - Header: nama proyek, customer, status
 * - Info PIC: Sales yang submit, SA yang ditugaskan
 * - Detail BANT: skor total + breakdown per kriteria
 * - Info proyek: DQ Number, target submit, use case tags
 * - Activity logs terkait proyek
 *
 * Requirements: 17.1, 17.6
 */

interface ProjectDetail {
  id_project: string;
  project_name: string;
  customer_name: string;
  status: string;
  dq_number: string | null;
  bant_score: number | null;
  bant_detail: {
    budget_mrr?: number | null;
    pic_name?: string | null;
    pic_position?: string | null;
    pic_email?: string | null;
    need_description?: string | null;
    timeline_target?: string | null;
    [key: string]: unknown;
  } | null;
  use_case_tags: string[];
  target_submit: string | null;
  sales_pic: { id: string | null; name: string | null; email: string | null };
  assigned_sa: { id: string | null; name: string | null; email: string | null } | null;
  gdrive_folder_id: string | null;
  created_at: string;
  updated_at: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { user } = useAuthStore();

  const [showHandoverModal, setShowHandoverModal] = useState(true);

  // Fetch detail proyek
  const { data: project, error: projError, isLoading } = useSWR<ProjectDetail>(
    `/projects/${projectId}`,
    fetcher
  );

  // Fetch handover status (hanya jika proyek Closed-Win)
  const { data: handoverStatus, mutate: mutateHandoverStatus } = useSWR<HandoverStatus>(
    project?.status === "Closed-Win" ? `/projects/${projectId}/handover-status` : null,
    fetcher
  );

  const shouldShowHandoverModal =
    project?.status === "Closed-Win" && showHandoverModal && user?.role === "SA";

  const shouldShowConfigForm =
    project?.status === "Closed-Win" &&
    handoverStatus &&
    (!handoverStatus.pmo_email || !handoverStatus.delivery_email);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Loading */}
      {isLoading && (
        <div className="space-y-4 animate-pulse">
          <div className="h-8 bg-neutral-200 rounded w-1/3" />
          <div className="h-4 bg-neutral-100 rounded w-1/2" />
          <div className="h-48 bg-neutral-100 rounded" />
        </div>
      )}

      {/* Error */}
      {projError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">Gagal memuat detail proyek. Silakan coba lagi.</p>
        </div>
      )}

      {/* Konten */}
      {project && (
        <>
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">
                {project.project_name}
              </h1>
              <p className="text-sm text-neutral-500 mt-1">{project.customer_name}</p>
              <p className="text-xs text-neutral-400 mt-0.5 font-mono">{project.id_project}</p>
            </div>
            <div className="flex items-center gap-2">
              {/* Tombol Edit */}
              <button
                onClick={() => router.push(`/projects/${projectId}/edit`)}
                className="px-3 py-1.5 text-sm font-medium text-neutral-700 border border-neutral-300
                           rounded-lg hover:bg-neutral-50 transition-colors min-h-[36px]"
              >
                Edit
              </button>
              <span
                className={`inline-block px-3 py-1 rounded-full text-xs font-medium shrink-0 ${
                  project.status === "Closed-Win" ? "bg-green-100 text-green-700"
                  : project.status === "Lost" ? "bg-red-100 text-red-700"
                  : project.status === "Ready" ? "bg-emerald-100 text-emerald-700"
                  : project.status === "Assigned" ? "bg-blue-100 text-blue-700"
                  : project.status === "Pending Assignment" ? "bg-yellow-100 text-yellow-700"
                  : "bg-neutral-100 text-neutral-700"
                }`}
              >
                {project.status}
              </span>
            </div>
          </div>

          {/* Section: PIC & Info Utama */}
          <div className="bg-white border border-neutral-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-neutral-700 mb-3">Informasi Proyek</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <InfoRow label="Sales PIC" value={project.sales_pic?.name || "—"} />
              <InfoRow label="SA Ditugaskan" value={project.assigned_sa?.name || "Belum di-assign"} />
              <InfoRow label="DQ Number" value={project.dq_number || "Belum diinput"} mono={!!project.dq_number} />
              <InfoRow
                label="Target Submit"
                value={project.target_submit
                  ? new Date(project.target_submit).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })
                  : "—"}
              />
              <InfoRow
                label="Dibuat"
                value={new Date(project.created_at).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })}
              />
              <InfoRow
                label="Terakhir Diubah"
                value={new Date(project.updated_at).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })}
              />
            </div>

            {/* Use case tags */}
            {project.use_case_tags.length > 0 && (
              <div className="mt-4 pt-4 border-t border-neutral-100">
                <span className="text-xs text-neutral-500">Use Case Tags:</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {project.use_case_tags.map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-primary-50 text-primary-600 text-xs rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section: Quick Actions — icon + text style sederhana */}
          <div className="flex gap-4">
            <a
              href={`/projects/${projectId}/documents`}
              className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-neutral-700 
                         border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors min-h-[44px]"
            >
              <svg className="w-4 h-4 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Dokumen
            </a>
            <a
              href="/activity-logs"
              className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-neutral-700 
                         border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors min-h-[44px]"
            >
              <svg className="w-4 h-4 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Activity Log
            </a>
          </div>

          {/* Section: Detail BANT (data deskriptif dari isian Sales) */}
          {project.bant_detail && (
            <div className="bg-white border border-neutral-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-neutral-700 mb-3">Detail BANT</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {/* Budget */}
                <div className="p-3 bg-neutral-50 rounded-lg">
                  <p className="text-xs font-medium text-neutral-500 mb-1">Budget (MRR)</p>
                  <p className="text-neutral-800 font-medium">
                    {project.bant_detail.budget_mrr
                      ? `Rp ${Number(project.bant_detail.budget_mrr).toLocaleString("id-ID")}`
                      : "Belum diinput"}
                  </p>
                </div>
                {/* PIC / Authority */}
                <div className="p-3 bg-neutral-50 rounded-lg">
                  <p className="text-xs font-medium text-neutral-500 mb-1">PIC Customer</p>
                  {project.bant_detail.pic_name ? (
                    <div>
                      <p className="text-neutral-800 font-medium">{project.bant_detail.pic_name}</p>
                      <p className="text-xs text-neutral-500">
                        {project.bant_detail.pic_position}
                        {project.bant_detail.pic_email && ` — ${project.bant_detail.pic_email}`}
                      </p>
                    </div>
                  ) : (
                    <p className="text-neutral-500">Belum diinput</p>
                  )}
                </div>
                {/* Need */}
                <div className="p-3 bg-neutral-50 rounded-lg md:col-span-2">
                  <p className="text-xs font-medium text-neutral-500 mb-1">Kebutuhan Teknis</p>
                  <p className="text-neutral-800">
                    {project.bant_detail.need_description || "Belum diinput"}
                  </p>
                </div>
                {/* Timeline */}
                <div className="p-3 bg-neutral-50 rounded-lg">
                  <p className="text-xs font-medium text-neutral-500 mb-1">Target Timeline</p>
                  <p className="text-neutral-800">
                    {project.bant_detail.timeline_target
                      ? new Date(project.bant_detail.timeline_target).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })
                      : project.target_submit
                        ? new Date(project.target_submit).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })
                        : "Belum diinput"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Section: Activity Log Proyek */}
          <ProjectActivitySection projectId={projectId} />

          {/* Section: Konfigurasi Handover */}
          {shouldShowConfigForm && (
            <div className="bg-white border border-amber-200 rounded-lg p-5">
              <h2 className="text-base font-semibold text-neutral-800 mb-3">Konfigurasi Handover</h2>
              <p className="text-sm text-neutral-600 mb-4">
                Email PMO Lead dan Delivery Lead belum dikonfigurasi.
              </p>
              <HandoverConfigForm
                projectId={projectId}
                existingPmoEmail={handoverStatus?.pmo_email}
                existingDeliveryEmail={handoverStatus?.delivery_email}
                onSuccess={() => mutateHandoverStatus()}
              />
            </div>
          )}
        </>
      )}

      {/* Modal Closed-Win */}
      {shouldShowHandoverModal && project && (
        <HandoverModal
          projectId={projectId}
          projectName={project.project_name}
          onAcknowledge={() => setShowHandoverModal(false)}
        />
      )}
    </div>
  );
}

// === Sub-komponen ===

function InfoRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <span className="text-neutral-500">{label}:</span>
      <span className={`ml-2 font-medium text-neutral-800 ${mono ? "font-mono text-sm" : ""}`}>
        {value}
      </span>
    </div>
  );
}

/** Section: Activity Log ringkasan per proyek + tombol Summarize */
function ProjectActivitySection({ projectId }: { projectId: string }) {
  const [showAll, setShowAll] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [isSummarizing, setIsSummarizing] = useState(false);

  const { data, isLoading } = useSWR<{
    items: {
      id: string;
      subtask_category: string;
      duration_hours: number;
      raw_notes: string;
      created_at: string;
    }[];
    total: number;
  }>(`/projects/${projectId}/story?page=1&page_size=${showAll ? 50 : 5}`, fetcher);

  // Hitung total jam
  const totalHours = data?.items.reduce((sum, log) => sum + log.duration_hours, 0) || 0;

  // Generate summary dari activity logs (client-side untuk MVP)
  const handleSummarize = () => {
    if (!data || data.items.length === 0) return;
    setIsSummarizing(true);

    // Generate ringkasan dari data yang ada (tanpa LLM untuk MVP)
    setTimeout(() => {
      const categories: Record<string, number> = {};
      let totalH = 0;
      data.items.forEach((log) => {
        categories[log.subtask_category] = (categories[log.subtask_category] || 0) + log.duration_hours;
        totalH += log.duration_hours;
      });

      const catSummary = Object.entries(categories)
        .sort((a, b) => b[1] - a[1])
        .map(([cat, hours]) => `${cat}: ${hours} jam`)
        .join(", ");

      const latestDate = data.items.length > 0
        ? new Date(data.items[0].created_at).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" })
        : "";

      setSummary(
        `Total ${data.total} aktivitas dengan ${totalH} jam kerja. ` +
        `Breakdown: ${catSummary}. ` +
        `Aktivitas terakhir: ${latestDate}.`
      );
      setIsSummarizing(false);
    }, 500);
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg p-5">
        <div className="h-5 bg-neutral-200 rounded w-1/4 mb-4 animate-pulse" />
        <div className="space-y-3 animate-pulse">
          <div className="h-10 bg-neutral-100 rounded" />
          <div className="h-10 bg-neutral-100 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-neutral-700">Project Story</h2>
          {data && data.total > 0 && (
            <p className="text-xs text-neutral-400 mt-0.5">
              {data.total} aktivitas — Total: {totalHours} jam
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {data && data.total > 0 && (
            <button
              onClick={handleSummarize}
              disabled={isSummarizing}
              className="px-3 py-1.5 text-xs font-medium text-primary-600 border border-primary-200
                         rounded-lg hover:bg-primary-50 transition-colors min-h-[36px]
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSummarizing ? "Generating..." : "Summarize"}
            </button>
          )}
          {data && data.total > 5 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="px-3 py-1.5 text-xs font-medium text-neutral-600 border border-neutral-200
                         rounded-lg hover:bg-neutral-50 transition-colors min-h-[36px]"
            >
              {showAll ? "Ringkas" : "Lihat Semua"}
            </button>
          )}
        </div>
      </div>

      {/* Summary result */}
      {summary && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs font-medium text-blue-700 mb-1">Ringkasan Proyek</p>
          <p className="text-sm text-blue-800">{summary}</p>
        </div>
      )}

      {(!data || data.items.length === 0) ? (
        <p className="text-sm text-neutral-500 text-center py-4">
          Belum ada activity log untuk proyek ini.
        </p>
      ) : (
        <div className="space-y-2">
          {data.items.map((log) => (
            <div key={log.id} className="flex items-start gap-3 p-3 bg-neutral-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                    {log.subtask_category}
                  </span>
                  <span className="text-xs text-neutral-400">{log.duration_hours}h</span>
                  <span className="text-xs text-neutral-300">
                    {new Date(log.created_at).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}
                  </span>
                </div>
                <p className="text-sm text-neutral-700 line-clamp-2">{log.raw_notes}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
