"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

/**
 * Halaman Login Portal SA
 *
 * Menampilkan tombol "Login dengan Google" dan menangani error states
 * dari OAuth redirect yang gagal.
 */

const ERROR_MESSAGES: Record<string, string> = {
  domain_not_allowed:
    "Domain email Anda tidak diizinkan untuk mengakses sistem ini.",
  auth_cancelled: "Login dibatalkan.",
  auth_failed: "Login gagal. Silakan coba lagi.",
};

function LoginContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  const errorMessage =
    error && (ERROR_MESSAGES[error] || "Terjadi kesalahan. Silakan coba lagi.");

  const handleLogin = () => {
    // Redirect ke backend OAuth endpoint yang akan forward ke Google
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    window.location.href = `${apiUrl}/auth/login`;
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo / App Name */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-primary-600">Portal SA</h1>
          <p className="mt-2 text-sm text-neutral-500">
            Manajemen Proyek Pre-Sales
          </p>
        </div>

        {/* Error message */}
        {errorMessage && (
          <div
            className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            role="alert"
          >
            {errorMessage}
          </div>
        )}

        {/* Login card */}
        <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <p className="mb-6 text-center text-sm text-neutral-600">
            Masuk menggunakan akun Google organisasi Anda
          </p>

          <button
            onClick={handleLogin}
            className="flex w-full items-center justify-center gap-3 rounded-lg border border-neutral-300 
                       bg-white px-4 py-3 min-h-[44px] text-sm font-medium text-neutral-700 
                       shadow-sm transition-colors duration-100 
                       hover:bg-neutral-50 hover:border-neutral-400
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            {/* Google Logo SVG */}
            <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
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
            Login dengan Google
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-neutral-400">
          Hanya akun dengan domain yang diizinkan yang dapat mengakses sistem
          ini.
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
