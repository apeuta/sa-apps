"use client";

import { useState, useCallback, useMemo } from "react";

/**
 * Komponen BANTManualForm — Form input BANT deskriptif
 *
 * Fitur:
 * - Budget: input MRR (number)
 * - Authority: input PIC (nama, jabatan, email)
 * - Need: textarea kebutuhan server
 * - Timeline: date picker target submit
 * - Real-time total score display (auto-calculated)
 * - Visual indicator: hijau (>=60), merah (<60)
 *
 * Requirements: 3.6, 3.7
 */

/** Skor BANT per kriteria (0-25 per item, total 0-100) */
export interface BANTScores {
  budget: number;
  authority: number;
  need: number;
  timeline: number;
}

/** Detail metadata yang dikirim bersama skor */
export interface BANTMetadata {
  budget_detail: { mrr: number | null };
  authority_detail: { name: string; position: string; email: string };
  need_detail: string;
  timeline_detail: string;
}

interface BANTManualFormProps {
  /** Callback saat form disubmit — kirim skor + metadata */
  onSubmit: (scores: BANTScores, metadata?: BANTMetadata) => void;
  /** Loading state saat submit */
  isSubmitting?: boolean;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Menentukan warna berdasarkan skor
 * - >= 60: hijau (lolos threshold)
 * - < 60: merah (perlu klarifikasi)
 */
function getScoreColor(score: number): string {
  if (score >= 60) return "text-green-600";
  return "text-red-600";
}

function getScoreBgColor(score: number): string {
  if (score >= 60) return "bg-green-50 border-green-200";
  return "bg-red-50 border-red-200";
}

function getScoreLabel(score: number): string {
  if (score >= 60) return "Lolos Threshold";
  return "Perlu Klarifikasi";
}

export function BANTManualForm({
  onSubmit,
  isSubmitting = false,
  disabled = false,
}: BANTManualFormProps) {
  // State form deskriptif
  const [mrr, setMrr] = useState<string>("");
  const [picName, setPicName] = useState("");
  const [picPosition, setPicPosition] = useState("");
  const [picEmail, setPicEmail] = useState("");
  const [needDescription, setNeedDescription] = useState("");
  const [targetDate, setTargetDate] = useState("");

  // Hitung skor otomatis per kriteria
  const budgetScore = useMemo(() => {
    const value = parseFloat(mrr);
    return !isNaN(value) && value > 0 ? 25 : 0;
  }, [mrr]);

  const authorityScore = useMemo(() => {
    const filled = [picName, picPosition, picEmail].filter(
      (v) => v.trim().length > 0
    ).length;
    if (filled === 3) return 25;
    if (filled === 2) return 17;
    if (filled === 1) return 8;
    return 0;
  }, [picName, picPosition, picEmail]);

  const needScore = useMemo(() => {
    const len = needDescription.trim().length;
    if (len > 100) return 25;
    if (len > 50) return 17;
    if (len > 10) return 8;
    return 0;
  }, [needDescription]);

  const timelineScore = useMemo(() => {
    return targetDate.trim().length > 0 ? 25 : 0;
  }, [targetDate]);

  // Total score
  const totalScore = budgetScore + authorityScore + needScore + timelineScore;

  // Handle submit
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      const scores: BANTScores = {
        budget: budgetScore,
        authority: authorityScore,
        need: needScore,
        timeline: timelineScore,
      };

      const metadata: BANTMetadata = {
        budget_detail: { mrr: mrr ? parseFloat(mrr) : null },
        authority_detail: {
          name: picName,
          position: picPosition,
          email: picEmail,
        },
        need_detail: needDescription,
        timeline_detail: targetDate,
      };

      onSubmit(scores, metadata);
    },
    [
      budgetScore,
      authorityScore,
      needScore,
      timelineScore,
      mrr,
      picName,
      picPosition,
      picEmail,
      needDescription,
      targetDate,
      onSubmit,
    ]
  );

  const inputDisabled = disabled || isSubmitting;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-neutral-800">
            Input BANT Manual
          </h3>
          <p className="text-sm text-neutral-500 mt-0.5">
            Isi informasi proyek — skor dihitung otomatis
          </p>
        </div>
      </div>

      {/* Total Score Display */}
      <div
        className={`rounded-lg border p-4 ${getScoreBgColor(totalScore)}`}
        role="status"
        aria-live="polite"
        aria-label={`Total BANT Score: ${totalScore} dari 100`}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-neutral-600">
              Total BANT Score
            </p>
            <p className={`text-3xl font-bold ${getScoreColor(totalScore)}`}>
              {totalScore}
              <span className="text-base font-normal text-neutral-400">
                /100
              </span>
            </p>
          </div>
          <div className="text-right">
            <span
              className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                totalScore >= 60
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {getScoreLabel(totalScore)}
            </span>
            <p className="text-xs text-neutral-500 mt-1">Threshold: ≥ 60</p>
          </div>
        </div>

        {/* Progress bar visual */}
        <div className="mt-3 h-2 bg-neutral-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-200 ${
              totalScore >= 60 ? "bg-green-500" : "bg-red-400"
            }`}
            style={{ width: `${totalScore}%` }}
          />
        </div>

        {/* Sub-score breakdown */}
        <div className="mt-3 grid grid-cols-4 gap-2 text-xs text-neutral-600">
          <div className="text-center">
            <p className="font-medium">Budget</p>
            <p className="font-bold">{budgetScore}/25</p>
          </div>
          <div className="text-center">
            <p className="font-medium">Authority</p>
            <p className="font-bold">{authorityScore}/25</p>
          </div>
          <div className="text-center">
            <p className="font-medium">Need</p>
            <p className="font-bold">{needScore}/25</p>
          </div>
          <div className="text-center">
            <p className="font-medium">Timeline</p>
            <p className="font-bold">{timelineScore}/25</p>
          </div>
        </div>
      </div>

      {/* ===== 1. BUDGET ===== */}
      <fieldset className="space-y-2 border border-neutral-200 rounded-lg p-4">
        <legend className="text-sm font-semibold text-neutral-700 px-2">
          💰 Ekspektasi MRR (Monthly Recurring Revenue)
        </legend>
        <p className="text-xs text-neutral-500">
          Masukkan estimasi pendapatan bulanan dari proyek ini.
          {budgetScore > 0 && (
            <span className="ml-2 text-green-600 font-medium">
              ✓ Skor: {budgetScore}/25
            </span>
          )}
        </p>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-neutral-500">
            IDR
          </span>
          <input
            type="number"
            value={mrr}
            onChange={(e) => setMrr(e.target.value)}
            placeholder="Contoh: 50000000"
            disabled={inputDisabled}
            min={0}
            className="w-full pl-12 pr-4 py-2.5 border border-neutral-300 rounded-md text-sm
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
              disabled:opacity-50 disabled:bg-neutral-100
              placeholder:text-neutral-400"
            aria-label="Ekspektasi MRR dalam Rupiah"
          />
        </div>
      </fieldset>

      {/* ===== 2. AUTHORITY ===== */}
      <fieldset className="space-y-3 border border-neutral-200 rounded-lg p-4">
        <legend className="text-sm font-semibold text-neutral-700 px-2">
          👤 Informasi PIC (Person in Charge)
        </legend>
        <p className="text-xs text-neutral-500">
          Data kontak pengambil keputusan di sisi customer.
          {authorityScore > 0 && (
            <span className="ml-2 text-green-600 font-medium">
              ✓ Skor: {authorityScore}/25
            </span>
          )}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label
              htmlFor="pic-name"
              className="block text-xs font-medium text-neutral-600 mb-1"
            >
              Nama PIC
            </label>
            <input
              id="pic-name"
              type="text"
              value={picName}
              onChange={(e) => setPicName(e.target.value)}
              placeholder="Nama lengkap"
              disabled={inputDisabled}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                disabled:opacity-50 disabled:bg-neutral-100
                placeholder:text-neutral-400"
            />
          </div>
          <div>
            <label
              htmlFor="pic-position"
              className="block text-xs font-medium text-neutral-600 mb-1"
            >
              Jabatan
            </label>
            <input
              id="pic-position"
              type="text"
              value={picPosition}
              onChange={(e) => setPicPosition(e.target.value)}
              placeholder="Contoh: VP Engineering"
              disabled={inputDisabled}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                disabled:opacity-50 disabled:bg-neutral-100
                placeholder:text-neutral-400"
            />
          </div>
          <div>
            <label
              htmlFor="pic-email"
              className="block text-xs font-medium text-neutral-600 mb-1"
            >
              Email
            </label>
            <input
              id="pic-email"
              type="email"
              value={picEmail}
              onChange={(e) => setPicEmail(e.target.value)}
              placeholder="email@perusahaan.co.id"
              disabled={inputDisabled}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                disabled:opacity-50 disabled:bg-neutral-100
                placeholder:text-neutral-400"
            />
          </div>
        </div>
      </fieldset>

      {/* ===== 3. NEED ===== */}
      <fieldset className="space-y-2 border border-neutral-200 rounded-lg p-4">
        <legend className="text-sm font-semibold text-neutral-700 px-2">
          🖥️ Kebutuhan Server & Spesifikasi
        </legend>
        <p className="text-xs text-neutral-500">
          Jelaskan kebutuhan teknis customer.
          {needScore > 0 && (
            <span className="ml-2 text-green-600 font-medium">
              ✓ Skor: {needScore}/25
            </span>
          )}
        </p>
        <textarea
          value={needDescription}
          onChange={(e) => setNeedDescription(e.target.value)}
          placeholder="Jelaskan kebutuhan server, spesifikasi teknis, dan kapasitas yang dibutuhkan"
          disabled={inputDisabled}
          rows={4}
          className="w-full px-3 py-2.5 border border-neutral-300 rounded-md text-sm resize-y
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
            disabled:opacity-50 disabled:bg-neutral-100
            placeholder:text-neutral-400"
          aria-label="Deskripsi kebutuhan server dan spesifikasi"
        />
        <p className="text-xs text-neutral-400">
          {needDescription.trim().length} karakter
          {needDescription.trim().length <= 10 && " — minimal 10 karakter untuk skor"}
          {needDescription.trim().length > 10 &&
            needDescription.trim().length <= 50 &&
            " — >50 untuk skor lebih tinggi"}
          {needDescription.trim().length > 50 &&
            needDescription.trim().length <= 100 &&
            " — >100 untuk skor maksimal"}
          {needDescription.trim().length > 100 && " — skor maksimal ✓"}
        </p>
      </fieldset>

      {/* ===== 4. TIMELINE ===== */}
      <fieldset className="space-y-2 border border-neutral-200 rounded-lg p-4">
        <legend className="text-sm font-semibold text-neutral-700 px-2">
          📅 Target Submit Dokumen
        </legend>
        <p className="text-xs text-neutral-500">
          Kapan dokumen proposal harus diserahkan ke customer?
          {timelineScore > 0 && (
            <span className="ml-2 text-green-600 font-medium">
              ✓ Skor: {timelineScore}/25
            </span>
          )}
        </p>
        <input
          type="date"
          value={targetDate}
          onChange={(e) => setTargetDate(e.target.value)}
          disabled={inputDisabled}
          className="w-full px-3 py-2.5 border border-neutral-300 rounded-md text-sm
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
            disabled:opacity-50 disabled:bg-neutral-100"
          aria-label="Target tanggal submit dokumen"
        />
      </fieldset>

      {/* Submit button */}
      <button
        type="submit"
        disabled={disabled || isSubmitting}
        className={`
          w-full py-3 px-4 rounded-lg font-medium text-white transition-all duration-200
          ${
            isSubmitting
              ? "bg-neutral-400 cursor-not-allowed"
              : "bg-primary-600 hover:bg-primary-700 active:bg-primary-800"
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          min-h-touch
        `}
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
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
            Mengirim skor...
          </span>
        ) : (
          "Submit Skor BANT"
        )}
      </button>
    </form>
  );
}
