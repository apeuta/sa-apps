/**
 * Helper autentikasi — logout.
 *
 * Logout melakukan:
 * 1. POST /auth/logout (best-effort revoke session di backend)
 * 2. Hapus token dari localStorage
 * 3. Redirect ke /login (hard redirect agar seluruh state ter-reset)
 *
 * clearUser pada Zustand store dipanggil oleh pemanggil (komponen) sebelum
 * memanggil ini, atau di-reset otomatis karena hard redirect.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export async function logout(): Promise<void> {
  if (typeof window === "undefined") return;

  const token = localStorage.getItem("access_token");

  // Best-effort revoke session di backend — jangan blokir logout bila gagal
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
    } catch {
      // Abaikan error jaringan — tetap lanjut membersihkan sesi lokal
    }
  }

  // Bersihkan token lokal
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  // Hard redirect ke login (reset seluruh in-memory state)
  window.location.href = "/login";
}
