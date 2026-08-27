"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import { useAuthStore } from "@/store/auth";
import { HandoverModal } from "@/components/HandoverModal";
import { HandoverConfigForm } from "@/components/HandoverConfigForm";
import type { HandoverStatus } from "@/lib/api/handover";

/**
 * Halaman Detail Proyek
 *
 * Menampilkan informasi proyek dan status workflow.
 * Jika proyek berstatus "Closed-Win", menampilkan:
 * - Modal blocking instruksi HLD (requirement 17.1)
 * - Form konfigurasi email PMO/Delivery jika belum ada (requirement 17.6)
 *
 * Requirements: 17.1, 17.6
 */

/** Interface data proyek */
interface ProjectDetail {
  id_project: string;
  project_name: string;
  customer_name: string;
  status: string;
  dq_number: string | null;
  bant_score: number | null;
  use_case_tags: string[];
  assigned_sa: string | null;
  gdrive_folder_id: string | null;
  created_at: string;
  updated_at: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user } = useAuthStore();

  // State untuk modal/form handover
  const [showHandoverModal, setShowHandoverModal] = useState(true);
  const [showConfigForm, setShowConfigForm] = useState(false);

  // Fetch detail proyek
  const {
    data: project,
    error: projError,
    isLoading,
    mutate: mutateProject,
  } = useSWR<ProjectDetail>(`/projects/${projectId}`, fetcher);

  // Fetch handover status (hanya jika proyek Closed-Win)
  const {
    data: handoverStatus,
    mutate: mutateHandoverStatus,
  } = useSWR<HandoverStatus>(
    project?.status === "Closed-Win" ? `/projects/${projectId}/handover-status` : null,
    fetcher
  );

  /**
   * Handler setelah user acknowledge handover modal
   */
  const handleModalAcknowledge = useCallback(() => {
    setShowHandoverModal(false);
  }, []);

  /**
   * Handler setelah konfigurasi handover berhasil disimpan
   */
  const handleConfigSuccess = useCallback(() => {
    setShowConfigForm(false);
    mutateHandoverStatus();
  }, [mutateHandoverStatus]);

  // Tentukan apakah perlu tampilkan modal Closed-Win
  const shouldShowHandoverModal =
    project?.status === "Closed-Win" &&
    showHandoverModal &&
    user?.role === "SA";

  // Tentukan apakah perlu tampilkan form konfigurasi email
  const shouldShowConfigForm =
    project?.status === "Closed-Win" &&
    handoverStatus &&
    (!handoverStatus.pmo_email || !handoverStatus.delivery_email);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Loading skeleton */}
      {isLoading && (
        <div className="space-y-4 animate-pulse" aria-busy="true">
          <div className="h-8 bg-neutral-200 rounded w-1/3" />
          <div className="h-4 bg-neutral-100 rounded w-1/2" />
          <div className="h-32 bg-neutral-100 rounded" />
        </div>
      )}

      {/* Error state */}
      {projError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700" role="alert">
            Gagal memuat detail proyek. Silakan coba lagi.
          </p>
        </div>
      )}

      {/* Konten detail proyek */}
      {project && (
        <>
          {/* Page Header */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">
                {project.project_name}
              </h1>
              <p className="text-sm text-neutral-500 mt-1">
                {project.customer_name}
              </p>
            </div>

            {/* Status badge */}
            <span
              className={`
                inline-block px-3 py-1 rounded-full text-xs font-medium
                ${project.status === "Closed-Win"
                  ? "bg-green-100 text-green-700"
                  : project.status === "Lost"
                    ? "bg-red-100 text-red-700"
                    : "bg-blue-100 text-blue-700"
                }
              `}
            >
              {project.status}
            </span>
          </div>

          {/* Info proyek */}
          <div className="bg-white border border-neutral-200 rounded-lg p-5">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-neutral-500">DQ Number:</span>
                <span className="ml-2 font-medium text-neutral-800">
                  {project.dq_number || "—"}
                </span>
              </div>
              <div>
                <span className="text-neutral-500">BANT Score:</span>
                <span className="ml-2 font-medium text-neutral-800">
                  {project.bant_score ?? "—"}
                </span>
              </div>
              <div>
                <span className="text-neutral-500">Dibuat:</span>
                <span className="ml-2 font-medium text-neutral-800">
                  {new Date(project.created_at).toLocaleDateString("id-ID")}
                </span>
              </div>
              <div>
                <span className="text-neutral-500">Terakhir diubah:</span>
                <span className="ml-2 font-medium text-neutral-800">
                  {new Date(project.updated_at).toLocaleDateString("id-ID")}
                </span>
              </div>
            </div>

            {/* Use case tags */}
            {project.use_case_tags && project.use_case_tags.length > 0 && (
              <div className="mt-4 pt-4 border-t border-neutral-100">
                <span className="text-xs text-neutral-500">Use Case Tags:</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {project.use_case_tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-primary-50 text-primary-600 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section Konfigurasi Handover — tampil jika Closed-Win dan email belum dikonfigurasi */}
          {shouldShowConfigForm && (
            <div className="bg-white border border-amber-200 rounded-lg p-5">
              <h2 className="text-base font-semibold text-neutral-800 mb-3">
                Konfigurasi Handover
              </h2>
              <p className="text-sm text-neutral-600 mb-4">
                Email PMO Lead dan Delivery Lead belum dikonfigurasi.
                Lengkapi informasi berikut agar handover dapat diproses.
              </p>
              <HandoverConfigForm
                projectId={projectId}
                existingPmoEmail={handoverStatus?.pmo_email}
                existingDeliveryEmail={handoverStatus?.delivery_email}
                onSuccess={handleConfigSuccess}
              />
            </div>
          )}
        </>
      )}

      {/* Modal Blocking Closed-Win → Instruksi HLD */}
      {shouldShowHandoverModal && project && (
        <HandoverModal
          projectId={projectId}
          projectName={project.project_name}
          onAcknowledge={handleModalAcknowledge}
        />
      )}
    </div>
  );
}
