"use client";

/**
 * Komponen SLA Lock Banner — Peringatan auto-lock folder Solutions
 *
 * Ditampilkan di halaman detail proyek ketika:
 * - DQ Number belum diinput
 * - SLA sudah melewati 5 hari (auto-lock aktif)
 *
 * Memberikan instruksi ke Sales untuk input DQ Number
 * agar akses folder dikembalikan.
 *
 * Requirements: 16.8
 */

/** Props untuk SLALockBanner */
export interface SLALockBannerProps {
  /** Callback saat tombol "Input DQ Number" diklik */
  onInputDQ?: () => void;
}

export function SLALockBanner({ onInputDQ }: SLALockBannerProps) {
  return (
    <div
      className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg mb-4"
      role="alert"
      aria-live="polite"
    >
      {/* Ikon peringatan */}
      <div className="shrink-0 mt-0.5">
        <svg
          className="w-5 h-5 text-red-600"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      {/* Konten peringatan */}
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-red-800 mb-1">
          Akses Folder Solutions Dikunci
        </h4>
        <p className="text-sm text-red-700">
          Akses folder Solutions dikunci karena DQ Number belum diinput lebih
          dari 5 hari. Silakan input DQ Number untuk membuka akses kembali.
        </p>
      </div>

      {/* Tombol CTA */}
      {onInputDQ && (
        <button
          onClick={onInputDQ}
          className="shrink-0 px-3 py-1.5 bg-red-600 text-white text-sm font-medium rounded-md
                     hover:bg-red-700 transition-colors duration-100
                     min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label="Input DQ Number untuk membuka akses folder"
        >
          Input DQ Number
        </button>
      )}
    </div>
  );
}
