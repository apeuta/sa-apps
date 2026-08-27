/**
 * API Client untuk modul Projects
 *
 * Fungsi-fungsi untuk komunikasi dengan backend:
 * - createProject: Submit proyek baru (multipart/form-data)
 * - submitManualBANT: Input skor BANT manual
 * - getBANTResult: Ambil hasil scoring BANT
 */

import { ApiError } from "../fetcher";

// Base URL API backend
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/** Tipe response BANT Result dari backend */
export interface BANTResult {
  bant_score: number;
  bant_detail: {
    budget: number;
    authority: number;
    need: number;
    timeline: number;
  };
  use_case_tags: string[];
  status: string;
}

/** Tipe response setelah project dibuat */
export interface CreateProjectResponse {
  id_project: string;
  project_name: string;
  customer_name: string;
  status: string;
  bant_score: number | null;
}

/** Input untuk BANT manual */
export interface ManualBANTInput {
  budget: number;
  authority: number;
  need: number;
  timeline: number;
}

/** Metadata detail BANT (dikirim bersama skor) */
export interface BANTMetadataInput {
  budget_detail?: { mrr: number | null };
  authority_detail?: { name: string; position: string; email: string };
  need_detail?: string;
  timeline_detail?: string;
}

/**
 * Helper untuk mendapatkan auth token
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

/**
 * Submit proyek baru dengan file attachment
 * Menggunakan multipart/form-data karena ada file upload
 *
 * @param data - Form data berisi field proyek dan files
 * @returns Response berisi data proyek yang dibuat
 */
export async function createProject(
  data: FormData
): Promise<CreateProjectResponse> {
  const token = getAuthToken();

  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  // Jangan set Content-Type — browser akan set boundary untuk multipart/form-data

  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers,
    body: data,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      errorData?.message || `Gagal membuat proyek (status ${response.status})`,
      response.status,
      errorData
    );
  }

  const json = await response.json();
  return json.data ?? json;
}

/**
 * Submit skor BANT secara manual
 * Digunakan sebagai fallback ketika tidak ada file attachment
 *
 * @param projectId - ID proyek yang akan di-score
 * @param scores - Objek skor per kriteria BANT (masing-masing 0-25)
 * @returns Hasil BANT scoring
 */
export async function submitManualBANT(
  projectId: string,
  scores: ManualBANTInput,
  metadata?: BANTMetadataInput
): Promise<BANTResult> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Kirim skor + metadata (metadata opsional, backend tetap terima budget/authority/need/timeline)
  const body = metadata ? { ...scores, ...metadata } : scores;

  const response = await fetch(
    `${API_BASE_URL}/projects/${projectId}/score-manual`,
    {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      errorData?.message || `Gagal submit skor BANT (status ${response.status})`,
      response.status,
      errorData
    );
  }

  const json = await response.json();
  return json.data ?? json;
}

/**
 * Ambil hasil BANT scoring untuk proyek tertentu
 *
 * @param projectId - ID proyek
 * @returns Hasil BANT atau null jika belum tersedia
 */
export async function getBANTResult(
  projectId: string
): Promise<BANTResult | null> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/projects/${projectId}/bant-result`,
    { headers }
  );

  if (!response.ok) {
    // 404 berarti belum ada hasil
    if (response.status === 404) return null;

    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      errorData?.message || `Gagal mengambil hasil BANT (status ${response.status})`,
      response.status,
      errorData
    );
  }

  const json = await response.json();
  return json.data ?? json;
}
