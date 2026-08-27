"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher, apiRequest } from "@/lib/fetcher";

/**
 * Halaman Edit Proyek — memungkinkan update informasi proyek
 */

interface ProjectDetail {
  id_project: string;
  project_name: string;
  customer_name: string;
  status: string;
  dq_number: string | null;
  target_submit: string | null;
  bant_detail: Record<string, unknown> | null;
}

export default function EditProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const { data: project, isLoading, error } = useSWR<ProjectDetail>(
    `/projects/${projectId}`,
    fetcher
  );

  const [form, setForm] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // Inisialisasi form dari data proyek
  if (project && Object.keys(form).length === 0) {
    setForm({
      project_name: project.project_name || "",
      customer_name: project.customer_name || "",
      dq_number: project.dq_number || "",
      target_submit: project.target_submit || "",
      budget_mrr: String((project.bant_detail as any)?.budget_mrr || ""),
      pic_name: String((project.bant_detail as any)?.pic_name || ""),
      pic_position: String((project.bant_detail as any)?.pic_position || ""),
      pic_email: String((project.bant_detail as any)?.pic_email || ""),
      need_description: String((project.bant_detail as any)?.need_description || ""),
    });
  }

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await apiRequest(`/projects/${projectId}`, {
        method: "PATCH",
        body: {
          project_name: form.project_name,
          customer_name: form.customer_name,
          dq_number: form.dq_number || null,
          target_submit: form.target_submit || null,
          bant_detail: {
            budget_mrr: form.budget_mrr ? Number(form.budget_mrr) : null,
            pic_name: form.pic_name || null,
            pic_position: form.pic_position || null,
            pic_email: form.pic_email || null,
            need_description: form.need_description || null,
          },
        },
      });
      setToast({ type: "success", msg: "Proyek berhasil diupdate." });
      setTimeout(() => router.push(`/projects/${projectId}`), 1500);
    } catch (err) {
      setToast({ type: "error", msg: err instanceof Error ? err.message : "Gagal menyimpan." });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-neutral-200 rounded w-1/3" />
        <div className="h-48 bg-neutral-100 rounded" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-2xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-sm text-red-700">Gagal memuat data proyek.</p>
      </div>
    );
  }

  const updateField = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm ${
          toast.type === "success" ? "bg-green-50 text-green-800 border border-green-200" : "bg-red-50 text-red-800 border border-red-200"
        }`}>{toast.msg}</div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Edit Proyek</h1>
          <p className="text-sm text-neutral-500 mt-1">{project.id_project}</p>
        </div>
        <button
          onClick={() => router.back()}
          className="px-3 py-1.5 text-sm text-neutral-600 border border-neutral-300 rounded-lg hover:bg-neutral-50"
        >
          Batal
        </button>
      </div>

      {/* Form */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Nama Proyek</label>
          <input type="text" value={form.project_name || ""} onChange={(e) => updateField("project_name", e.target.value)}
            className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Nama Customer</label>
          <input type="text" value={form.customer_name || ""} onChange={(e) => updateField("customer_name", e.target.value)}
            className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">DQ Number</label>
            <input type="text" value={form.dq_number || ""} onChange={(e) => updateField("dq_number", e.target.value)} placeholder="DQ-2026-XXXXX"
              className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">Target Submit</label>
            <input type="date" value={form.target_submit || ""} onChange={(e) => updateField("target_submit", e.target.value)}
              className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
        </div>

        <hr className="border-neutral-100" />
        <h3 className="text-sm font-semibold text-neutral-700">Detail BANT</h3>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Budget MRR (IDR)</label>
          <input type="number" value={form.budget_mrr || ""} onChange={(e) => updateField("budget_mrr", e.target.value)} placeholder="50000000"
            className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">Nama PIC</label>
            <input type="text" value={form.pic_name || ""} onChange={(e) => updateField("pic_name", e.target.value)}
              className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">Jabatan PIC</label>
            <input type="text" value={form.pic_position || ""} onChange={(e) => updateField("pic_position", e.target.value)}
              className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">Email PIC</label>
            <input type="email" value={form.pic_email || ""} onChange={(e) => updateField("pic_email", e.target.value)}
              className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Kebutuhan Teknis</label>
          <textarea value={form.need_description || ""} onChange={(e) => updateField("need_description", e.target.value)} rows={3}
            className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm resize-y focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
      </div>

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="w-full py-3 px-4 rounded-lg font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
      >
        {isSaving ? "Menyimpan..." : "Simpan Perubahan"}
      </button>
    </div>
  );
}
