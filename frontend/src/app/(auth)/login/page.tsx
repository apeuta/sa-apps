"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import { useAuthStore } from "@/store/auth";

/**
 * Halaman Login Portal SA — Demo Mode
 *
 * Menampilkan tombol demo login per role (Sales, SA, Lead SA, Admin)
 * dan tombol Google OAuth yang dinonaktifkan.
 * Klik tombol demo → POST ke /auth/demo-login → simpan token → redirect dashboard
 */

const ERROR_MESSAGES: Record<string, string> = {
  domain_not_allowed:
    "Domain email Anda tidak diizinkan untuk mengakses sistem ini.",
  auth_cancelled: "Login dibatalkan.",
  auth_failed: "Login gagal. Silakan coba lagi.",
};

// Konfigurasi tombol demo login per role
const DEMO_ROLES = [
  {
    role: "Sales",
    label: "Login sebagai Sales",
    color: "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500",
  },
  {
    role: "SA",
    label: "Login sebagai SA",
    color: "bg-green-600 hover:bg-green-700 focus:ring-green-500",
  },
  {
    role: "Lead_SA",
    label: "Login sebagai Lead SA",
    color: "bg-purple-600 hover:bg-purple-700 focus:ring-purple-500",
  },
  {
    role: "Admin",
    label: "Login sebagai Admin",
    color: "bg-red-600 hover:bg-red-700 focus:ring-red-500",
  },
] as const;

function LoginContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { setUser } = useAuthStore();
  const error = searchParams.get("error");
  const [loadingRole, setLoadingRole] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [oauthConfigured, setOauthConfigured] = useState(false);

  // Fetch auth config dari backend saat mount
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    fetch(`${apiUrl}/auth/config`)
      .then((res) => res.json())
      .then((data) => {
        if (data.oauth_configured) setOauthConfigured(true);
      })
      .catch(() => {});
  }, []);

  const handleGoogleLogin = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    window.location.href = `${apiUrl}/auth/login`;
  };

  const errorMessage =
    error && (ERROR_MESSAGES[error] || "Terjadi kesalahan. Silakan coba lagi.");

  /**
   * Handler demo login — POST ke backend lalu simpan token dan user info
   */
  const handleDemoLogin = async (role: string) => {
    setLoadingRole(role);
    setLoginError(null);

    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

      const response = await fetch(`${apiUrl}/auth/demo-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.message || `Login gagal (${response.status})`
        );
      }

      const data = await response.json();

      // Handle berbagai struktur response dari backend:
      // Struktur 1: { access_token, refresh_token, user }
      // Struktur 2: { tokens: { access_token, refresh_token }, user }
      // Struktur 3: { data: { tokens: {...}, user: {...} } }
      const tokens = data.tokens || data.data?.tokens || data;
      const userData = data.user || data.data?.user;

      // Simpan token ke localStorage
      const accessToken = tokens.access_token;
      const refreshToken = tokens.refresh_token;

      if (accessToken) {
        localStorage.setItem("access_token", accessToken);
      }
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }

      // Simpan user info ke Zustand auth store
      if (userData) {
        setUser({
          id: userData.id,
          email: userData.email,
          full_name: userData.name || userData.full_name,
          role: userData.role,
          avatar_url: userData.avatar_url,
        });
      }

      // Redirect ke dashboard
      router.push("/");
    } catch (err) {
      setLoginError(
        err instanceof Error ? err.message : "Login gagal. Silakan coba lagi."
      );
    } finally {
      setLoadingRole(null);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo / App Name */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-primary-600">Portal SA</h1>
          <p className="mt-2 text-sm text-neutral-500">
            Manajemen Proyek Pre-Sales
          </p>
        </div>

        {/* Banner Demo Mode */}
        <div
          className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 text-center"
          role="status"
        >
          Demo Mode — Login tanpa Google OAuth
        </div>

        {/* Error messages */}
        {(errorMessage || loginError) && (
          <div
            className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            role="alert"
          >
            {loginError || errorMessage}
          </div>
        )}

        {/* Demo Login Buttons */}
        <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm space-y-3">
          <p className="mb-4 text-center text-sm text-neutral-600">
            Pilih role untuk demo login
          </p>

          {DEMO_ROLES.map(({ role, label, color }) => (
            <button
              key={role}
              onClick={() => handleDemoLogin(role)}
              disabled={loadingRole !== null}
              className={`
                flex w-full items-center justify-center rounded-lg px-4 py-3 
                min-h-[44px] text-sm font-medium text-white shadow-sm
                transition-colors duration-100
                focus:outline-none focus:ring-2 focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed
                ${color}
              `}
            >
              {loadingRole === role ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="w-4 h-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Memproses...
                </span>
              ) : (
                label
              )}
            </button>
          ))}
        </div>

        {/* Google OAuth — aktif jika backend mengembalikan oauth_configured=true */}
        <div className={`rounded-xl border border-neutral-200 bg-white p-6 shadow-sm ${oauthConfigured ? "" : "opacity-60"}`}>
          <button
            disabled={!oauthConfigured}
            onClick={handleGoogleLogin}
            className={`flex w-full items-center justify-center gap-3 rounded-lg border px-4 py-3 min-h-[44px] text-sm font-medium transition-colors ${
              oauthConfigured
                ? "border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50 cursor-pointer"
                : "border-neutral-300 bg-neutral-100 text-neutral-400 cursor-not-allowed"
            }`}
          >
            {/* Google Logo SVG */}
            <svg className={`h-5 w-5 ${oauthConfigured ? "" : "grayscale"}`} viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            {oauthConfigured ? "Login dengan Google" : "Google OAuth (Belum dikonfigurasi)"}
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-neutral-400">
          Mode demo aktif — semua data bersifat sementara.
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-neutral-50">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
