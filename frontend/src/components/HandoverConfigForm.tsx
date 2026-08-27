"use client";

import { useState, useCallback } from "react";
import { setHandoverConfig } from "@/lib/api/handover";

/**
 * Form Input Email PMO Lead dan Delivery Lead
 *
 * Ditampilkan sebelum handover bisa diproses jika email
 * PMO/Delivery Lead belum dikonfigurasi di sistem.
 *
 * Fitur:
 * - Dua input field email dengan validasi format
 * - Tombol submit dengan loading state
 * - Error display per-field
 *
 * Requirements: 17.6
 */

interface HandoverConfigFormProps {
  /** ID proyek yang membutuhkan konfigurasi */
  projectId: string;
  /** Email PMO yang sudah tersimpan (jika ada) */
  existingPmoEmail?: string | null;
  /** Email Delivery yang sudah tersimpan (jika ada) */
  existingDeliveryEmail?: string | null;
  /** Callback setelah konfigurasi berhasil disimpan */
  onSuccess: () => void;
  /** Callback untuk membatalkan */
  onCancel?: () => void;
}

interface FormErrors {
  pmo_email?: string;
  delivery_email?: string;
  general?: string;
}

/** Regex sederhana untuk validasi format email */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function HandoverConfigForm({
  projectId,
  existingPmoEmail,
  existingDeliveryEmail,
  onSuccess,
  onCancel,
}: HandoverConfigFormProps) {
  // State form
  const [pmoEmail, setPmoEmail] = useState(existingPmoEmail ?? "");
  const [deliveryEmail, setDeliveryEmail] = useState(existingDeliveryEmail ?? "");
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Validasi format email
   */
  const validateEmail = (email: string, fieldName: string): string | undefined => {
    if (!email.trim()) {
      return `${fieldName} wajib diisi`;
    }
    if (!EMAIL_REGEX.test(email.trim())) {
      return `Format email ${fieldName} tidak valid`;
    }
    return undefined;
  };

  /**
   * Validasi seluruh form
   */
  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    const pmoError = validateEmail(pmoEmail, "PMO Lead");
    if (pmoError) newErrors.pmo_email = pmoError;

    const deliveryError = validateEmail(deliveryEmail, "Delivery Lead");
    if (deliveryError) newErrors.delivery_email = deliveryError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [pmoEmail, deliveryEmail]);

  /**
   * Handle submit form
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validate()) return;

      setIsSubmitting(true);
      setErrors({});

      try {
        await setHandoverConfig(projectId, pmoEmail.trim(), deliveryEmail.trim());
        onSuccess();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Gagal menyimpan konfigurasi";
        setErrors({ general: message });
      } finally {
        setIsSubmitting(false);
      }
    },
    [projectId, pmoEmail, deliveryEmail, validate, onSuccess]
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5"
      aria-label="Form konfigurasi email handover"
    >
      {/* Penjelasan */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          Masukkan email PMO Lead dan Delivery Lead yang akan menerima 
          akses folder dan notifikasi handover.
        </p>
      </div>

      {/* Input PMO Lead Email */}
      <div>
        <label
          htmlFor="pmo-email"
          className="block text-sm font-medium text-neutral-700 mb-1"
        >
          Email PMO Lead <span className="text-red-500">*</span>
        </label>
        <input
          id="pmo-email"
          type="email"
          value={pmoEmail}
          onChange={(e) => {
            setPmoEmail(e.target.value);
            if (errors.pmo_email) setErrors((prev) => ({ ...prev, pmo_email: undefined }));
          }}
          disabled={isSubmitting}
          placeholder="pmo.lead@company.com"
          className={`
            w-full px-3 py-2.5 border rounded-lg text-sm
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
            disabled:opacity-50 disabled:bg-neutral-100
            ${errors.pmo_email ? "border-red-300 bg-red-50" : "border-neutral-300"}
          `}
          aria-invalid={!!errors.pmo_email}
          aria-describedby={errors.pmo_email ? "pmo-email-error" : undefined}
        />
        {errors.pmo_email && (
          <p id="pmo-email-error" className="text-xs text-red-600 mt-1" role="alert">
            {errors.pmo_email}
          </p>
        )}
      </div>

      {/* Input Delivery Lead Email */}
      <div>
        <label
          htmlFor="delivery-email"
          className="block text-sm font-medium text-neutral-700 mb-1"
        >
          Email Delivery Lead <span className="text-red-500">*</span>
        </label>
        <input
          id="delivery-email"
          type="email"
          value={deliveryEmail}
          onChange={(e) => {
            setDeliveryEmail(e.target.value);
            if (errors.delivery_email)
              setErrors((prev) => ({ ...prev, delivery_email: undefined }));
          }}
          disabled={isSubmitting}
          placeholder="delivery.lead@company.com"
          className={`
            w-full px-3 py-2.5 border rounded-lg text-sm
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
            disabled:opacity-50 disabled:bg-neutral-100
            ${errors.delivery_email ? "border-red-300 bg-red-50" : "border-neutral-300"}
          `}
          aria-invalid={!!errors.delivery_email}
          aria-describedby={errors.delivery_email ? "delivery-email-error" : undefined}
        />
        {errors.delivery_email && (
          <p id="delivery-email-error" className="text-xs text-red-600 mt-1" role="alert">
            {errors.delivery_email}
          </p>
        )}
      </div>

      {/* General error */}
      {errors.general && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700" role="alert">
            {errors.general}
          </p>
        </div>
      )}

      {/* Tombol aksi */}
      <div className="flex gap-3 pt-2">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1 py-2.5 px-4 rounded-lg font-medium text-neutral-700 
                       border border-neutral-300 hover:bg-neutral-50 
                       transition-colors duration-100 min-h-[44px]
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Batal
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className={`
            flex-1 py-2.5 px-4 rounded-lg font-medium text-white 
            transition-all duration-200 min-h-[44px]
            ${isSubmitting
              ? "bg-neutral-400 cursor-not-allowed"
              : "bg-primary-600 hover:bg-primary-700 active:bg-primary-800"
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {isSubmitting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
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
              Menyimpan...
            </span>
          ) : (
            "Simpan Konfigurasi"
          )}
        </button>
      </div>
    </form>
  );
}
