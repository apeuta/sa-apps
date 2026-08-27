"use client";

/**
 * Komponen Toast Notification global (Requirement 19.8, 19.9)
 *
 * - Posisi: bottom-right, non-blocking
 * - Sukses: hijau, auto-dismiss 3 detik
 * - Error: merah, auto-dismiss 5 detik
 * - Animasi masuk/keluar max 200ms (Requirement 19.6)
 */

import { useEffect, useState } from "react";
import { useToastStore, type Toast as ToastItem } from "@/store/toast";

// Ikon SVG inline agar tidak perlu dependency tambahan
function SuccessIcon() {
  return (
    <svg
      className="w-5 h-5 text-green-600 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg
      className="w-5 h-5 text-red-600 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg
      className="w-5 h-5 text-primary-600 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

// Style per tipe toast
const TOAST_STYLES: Record<string, string> = {
  success: "bg-green-50 border-green-200 text-green-800",
  error: "bg-red-50 border-red-200 text-red-800",
  info: "bg-primary-50 border-primary-200 text-primary-800",
};

const TOAST_ICONS: Record<string, () => JSX.Element> = {
  success: SuccessIcon,
  error: ErrorIcon,
  info: InfoIcon,
};

/** Item toast individual dengan animasi */
function ToastItem({ toast }: { toast: ToastItem }) {
  const { dismissToast } = useToastStore();
  const [isVisible, setIsVisible] = useState(false);

  // Animasi masuk (fade + slide dari kanan)
  useEffect(() => {
    // Trigger animasi setelah mount — delay minimal untuk CSS transition
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  const Icon = TOAST_ICONS[toast.type];

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`
        flex items-start gap-3 px-4 py-3 rounded-lg border shadow-lg
        transition-all duration-200 ease-out
        ${TOAST_STYLES[toast.type]}
        ${isVisible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-4"}
      `}
    >
      <Icon />
      <p className="text-sm font-medium flex-1 min-w-0 break-words">
        {toast.message}
      </p>
      <button
        onClick={() => dismissToast(toast.id)}
        className="shrink-0 p-1 rounded hover:bg-black/5 transition-colors duration-100 min-w-[28px] min-h-[28px] flex items-center justify-center"
        aria-label="Tutup notifikasi"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}

/** Container toast — dipasang di root layout */
export function ToastContainer() {
  const { toasts } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div
      aria-label="Notifikasi"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} />
        </div>
      ))}
    </div>
  );
}

export default ToastContainer;
