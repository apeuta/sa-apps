"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import {
  PendingProject,
  AvailableSA,
} from "@/lib/api/assignment";
import { AssignmentModal } from "@/components/AssignmentModal";

/**
 * Dashboard Lead_SA
 *
 * Tiga section utama:
 * 1. Antrian Assignment — proyek berstatus "Pending Assignment"
 * 2. Overview Proyek Aktif — count proyek per status
 * 3. Utilisasi SA — daftar SA dengan jumlah proyek aktif
 *
 * Requirements: 4.1, 9.3
 */

/** Tipe ringkasan proyek per status */
interface StatusCount {
  status: string;
  count: number;
}

/** Warna badge per status proyek */
const STATUS_BADGE_COLORS: Record<string, string> = {
  "Pending Assignment": "bg-yellow-100 text-yellow-700",
  Assigned: "bg-blue-100 text-blue-700",
  Ready: "bg-green-100 text-green-700",
  "Closed-Win": "bg-emerald-100 text-emerald-700",
  "Need Clarification": "bg-orange-100 text-orange-700",
  New: "bg-neutral-100 text-neutral-700",
  Lost: "bg-red-100 text-red-700",
  "Scoring Pending": "bg-purple-100 text-purple-700",
  "Manual Review Required": "bg-pink-100 text-pink-700",
  "Handover Complete": "bg-teal-100 text-teal-700",
};

export default function LeadSADashboard() {
  // State untuk modal assignment
  const [assigningProject, setAssigningProject] =
    useState<PendingProject | null>(null);
  // State untuk toast notification
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

  // Fetch proyek pending assignment
  const {
    data: pendingProjects,
    isLoading: isLoadingPending,
    mutate: mutatePending,
  } = useSWR<PendingProject[]>("/projects/pending-assignment", fetcher);

  // Fetch overview proyek aktif (count per status)
  const { data: statusSummary, isLoading: isLoadingStatus } = useSWR<
    StatusCount[]
  >("/projects/status-summary", fetcher);

  // Fetch utilisasi SA
  const { data: saUtilization, isLoading: isLoadingSA } = useSWR<
    AvailableSA[]
  >("/sa/available", fetcher);

  /**
   * Callback setelah assignment berhasil
   * Refresh data dan tampilkan toast
   */
  const handleAssignmentSuccess = useCallback(() => {
    setAssigningProject(null);
    mutatePending(); // Refresh daftar pending
    setToast({ message: "SA berhasil ditugaskan ke proyek!", type: "success" });

    // Auto-dismiss toast setelah 3 detik (Requirement 19.3)
    setTimeout(() => setToast(null), 3000);
  }, [mutatePending]);

  return (
    <div className="space-y-6">
      {/* Header halaman */}
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">
          Dashboard Lead SA
        </h1>
        <p className="mt-1 text-neutral-500">
          Kelola assignment proyek dan pantau utilisasi tim SA.
        </p>
      </div>

      {/* Toast notification */}
      {toast && (
        <div
          className={`
            fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg
            transition-all duration-200 flex items-center gap-2
            ${
              toast.type === "success"
                ? "bg-green-50 border border-green-200 text-green-700"
                : "bg-red-50 border border-red-200 text-red-700"
            }
          `}
          role="alert"
        >
          {toast.type === "success" ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          )}
          <span className="text-sm font-medium">{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="ml-2 text-current opacity-60 hover:opacity-100"
            aria-label="Tutup notifikasi"
          >
            ×
          </button>
        </div>
      )}

      {/* Section 1: Antrian Assignment */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-neutral-800">
            Antrian Assignment
          </h2>
          {pendingProjects && (
            <span className="px-2.5 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">
              {pendingProjects.length} menunggu
            </span>
          )}
        </div>

        {/* Loading skeleton */}
        {isLoadingPending && <PendingListSkeleton />}

        {/* Daftar proyek pending */}
        {!isLoadingPending && pendingProjects && (
          <>
            {pendingProjects.length === 0 ? (
              <div className="rounded-lg border border-neutral-200 bg-white p-8 text-center">
                <p className="text-neutral-500 text-sm">
                  Tidak ada proyek yang menunggu assignment saat ini.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {pendingProjects.map((project) => (
                  <ProjectCard
                    key={project.id_project}
                    project={project}
                    onAssign={() => setAssigningProject(project)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </section>

      {/* Section 2 & 3: Grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 2: Overview Proyek Aktif */}
        <section>
          <h2 className="text-lg font-semibold text-neutral-800 mb-4">
            Overview Proyek Aktif
          </h2>

          {isLoadingStatus && <StatusSummarySkeleton />}

          {!isLoadingStatus && statusSummary && (
            <div className="rounded-lg border border-neutral-200 bg-white p-5">
              {statusSummary.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-4">
                  Belum ada data proyek.
                </p>
              ) : (
                <div className="space-y-3">
                  {statusSummary.map((item) => (
                    <div
                      key={item.status}
                      className="flex items-center justify-between"
                    >
                      <span
                        className={`
                          px-2.5 py-1 text-xs font-medium rounded-full
                          ${STATUS_BADGE_COLORS[item.status] || "bg-neutral-100 text-neutral-600"}
                        `}
                      >
                        {item.status}
                      </span>
                      <span className="text-lg font-semibold text-neutral-900">
                        {item.count}
                      </span>
                    </div>
                  ))}
                  {/* Total */}
                  <div className="flex items-center justify-between pt-3 border-t border-neutral-100">
                    <span className="text-sm font-medium text-neutral-600">
                      Total Aktif
                    </span>
                    <span className="text-lg font-bold text-neutral-900">
                      {statusSummary.reduce((acc, s) => acc + s.count, 0)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Section 3: Utilisasi SA */}
        <section>
          <h2 className="text-lg font-semibold text-neutral-800 mb-4">
            Utilisasi SA
          </h2>

          {isLoadingSA && <SAUtilizationSkeleton />}

          {!isLoadingSA && saUtilization && (
            <div className="rounded-lg border border-neutral-200 bg-white p-5">
              {saUtilization.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-4">
                  Belum ada SA terdaftar.
                </p>
              ) : (
                <div className="space-y-3">
                  {saUtilization.map((sa) => (
                    <div
                      key={sa.id}
                      className="flex items-center gap-3"
                    >
                      {/* Avatar */}
                      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                        {sa.avatar_url ? (
                          <img
                            src={sa.avatar_url}
                            alt={sa.name}
                            className="w-8 h-8 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-xs font-medium text-primary-600">
                            {sa.name.charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>

                      {/* Nama */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-800 truncate">
                          {sa.name}
                        </p>
                      </div>

                      {/* Workload bar + count */}
                      <div className="flex items-center gap-2 shrink-0">
                        <div className="w-16 h-2 bg-neutral-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-200 ${
                              sa.active_project_count <= 2
                                ? "bg-green-400"
                                : sa.active_project_count <= 4
                                  ? "bg-yellow-400"
                                  : "bg-red-400"
                            }`}
                            style={{
                              width: `${Math.min((sa.active_project_count / 6) * 100, 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs font-medium text-neutral-600 w-6 text-right">
                          {sa.active_project_count}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      {/* Modal Assignment */}
      {assigningProject && (
        <AssignmentModal
          project={assigningProject}
          onClose={() => setAssigningProject(null)}
          onSuccess={handleAssignmentSuccess}
        />
      )}
    </div>
  );
}

// === Sub-komponen ===

/**
 * Card proyek dalam antrian assignment
 * Menampilkan detail proyek + tombol Assign + badge Folder Pending
 */
function ProjectCard({
  project,
  onAssign,
}: {
  project: PendingProject;
  onAssign: () => void;
}) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-5 hover:shadow-sm transition-shadow duration-200">
      {/* Header card */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-neutral-900 truncate">
            {project.project_name}
          </h3>
          <p className="text-xs text-neutral-500 truncate mt-0.5">
            {project.customer_name}
          </p>
        </div>

        {/* BANT Score badge */}
        <span
          className={`
            shrink-0 px-2.5 py-1 text-xs font-semibold rounded-full
            ${
              project.bant_score >= 80
                ? "bg-green-100 text-green-700"
                : project.bant_score >= 60
                  ? "bg-blue-100 text-blue-700"
                  : "bg-yellow-100 text-yellow-700"
            }
          `}
        >
          BANT {project.bant_score}
        </span>
      </div>

      {/* Tags */}
      {project.use_case_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {project.use_case_tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-neutral-100 text-neutral-600 text-xs rounded"
            >
              {tag}
            </span>
          ))}
          {project.use_case_tags.length > 3 && (
            <span className="px-2 py-0.5 text-neutral-400 text-xs">
              +{project.use_case_tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Info tambahan */}
      <div className="flex items-center gap-3 text-xs text-neutral-500 mb-4">
        <span>Sales: {project.sales_pic.name}</span>
        <span>•</span>
        <span>
          Target: {new Date(project.target_submit).toLocaleDateString("id-ID")}
        </span>
      </div>

      {/* Footer: Badge Folder Pending + Tombol Assign */}
      <div className="flex items-center justify-between">
        {/* Badge Folder Pending — ditampilkan jika gdrive_folder_id null setelah assigned */}
        {project.status === "Assigned" && !project.gdrive_folder_id && (
          <span className="px-2.5 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">
            Folder Pending
          </span>
        )}

        {/* Spacer jika tidak ada badge */}
        {(project.status !== "Assigned" || project.gdrive_folder_id) && (
          <span />
        )}

        {/* Tombol Assign */}
        <button
          onClick={onAssign}
          className="px-3 py-1.5 text-xs font-medium text-white bg-primary-600
                     rounded-lg hover:bg-primary-700 transition-colors duration-100
                     min-h-[36px] min-w-[44px]"
        >
          Assign SA
        </button>
      </div>
    </div>
  );
}

// === Loading Skeletons (Requirement 19.5) ===

/** Skeleton untuk daftar proyek pending */
function PendingListSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="rounded-lg border border-neutral-200 bg-white p-5"
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="h-4 w-40 bg-neutral-200 rounded animate-pulse mb-1.5" />
              <div className="h-3 w-28 bg-neutral-100 rounded animate-pulse" />
            </div>
            <div className="h-6 w-16 bg-neutral-200 rounded-full animate-pulse" />
          </div>
          <div className="flex gap-1.5 mb-3">
            <div className="h-5 w-16 bg-neutral-100 rounded animate-pulse" />
            <div className="h-5 w-20 bg-neutral-100 rounded animate-pulse" />
          </div>
          <div className="h-3 w-48 bg-neutral-100 rounded animate-pulse mb-4" />
          <div className="flex justify-end">
            <div className="h-8 w-20 bg-neutral-200 rounded-lg animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Skeleton untuk ringkasan status */
function StatusSummarySkeleton() {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-5">
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center justify-between">
            <div className="h-6 w-28 bg-neutral-200 rounded-full animate-pulse" />
            <div className="h-6 w-8 bg-neutral-100 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Skeleton untuk utilisasi SA */
function SAUtilizationSkeleton() {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-5">
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-neutral-200 animate-pulse" />
            <div className="flex-1">
              <div className="h-4 w-24 bg-neutral-200 rounded animate-pulse" />
            </div>
            <div className="h-2 w-16 bg-neutral-100 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
