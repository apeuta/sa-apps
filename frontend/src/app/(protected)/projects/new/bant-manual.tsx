"use client";

import { useState, useCallback } from "react";

/**
 * Komponen BANTManualForm — Form input BANT manual sebagai fallback
 *
 * Fitur:
 * - 4 slider/input untuk Budget, Authority, Need, Timeline (0-25)
 * - Real-time total score display
 * - Visual indicator: hijau (>=60), merah (<60)
 * - Submit button
 *
 * Requirements: 3.6, 3.7
 */

/** Skor BANT per kriteria */
export interface BANTScores {
  budget: number;
  authority: number;
  need: number;
  timeline: number;
}

interface BANTManualFormProps {
  /** Callback saat form disubmit */
  onSubmit: (scores: BANTScores) => void;
  /** Loading state saat submit */
  isSubmitting?: boolean;
  /** Disabled state */
  disabled?: boolean;
}

/** Label dan deskripsi untuk setiap kriteria BANT */
const BANT_CRITERIA = [
  {
    key: "budget" as const,
    label: "Budget",
    description: "Apakah customer memiliki anggaran yang jelas?",
  },
  {
    key: "authority" as const,
    label: "Authority",
    description: "Apakah PIC memiliki wewenang pengambilan keputusan?",
  },
  {
    key: "need" as const,
    label: "Need",
    description: "Apakah kebutuhan teknis sudah terdefinisi?",
  },
  {
    key: "timeline" as const,
    label: "Timeline",
    description: "Apakah ada timeline implementasi yang jelas?",
  },
];

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
  const [scores, setScores] = useState<BANTScores>({
    budget: 0,
    authority: 0,
    need: 0,
    timeline: 0,
  });

  // Hitung total score
  const totalScore = scores.budget + scores.authority + scores.need + scores.timeline;

  // Update skor per kriteria
  const updateScore = useCallback(
    (key: keyof BANTScores, value: number) => {
      // Clamp value antara 0-25
      const clamped = Math.max(0, Math.min(25, value));
      setScores((prev) => ({ ...prev, [key]: clamped }));
    },
    []
  );

  // Handle submit
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      onSubmit(scores);
    },
    [scores, onSubmit]
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-neutral-800">
            Input BANT Manual
          </h3>
          <p className="text-sm text-neutral-500 mt-0.5">
            Isi skor untuk setiap kriteria BANT (skala 0-25)
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
            <p className="text-sm font-medium text-neutral-600">Total BANT Score</p>
            <p className={`text-3xl font-bold ${getScoreColor(totalScore)}`}>
              {totalScore}
              <span className="text-base font-normal text-neutral-400">/100</span>
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
            <p className="text-xs text-neutral-500 mt-1">
              Threshold: ≥ 60
            </p>
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
      </div>

      {/* Kriteria BANT */}
      <div className="space-y-5">
        {BANT_CRITERIA.map((criteria) => (
          <div key={criteria.key} className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <label
                  htmlFor={`bant-${criteria.key}`}
                  className="text-sm font-medium text-neutral-700"
                >
                  {criteria.label}
                </label>
                <p className="text-xs text-neutral-500">{criteria.description}</p>
              </div>
              {/* Tampilkan nilai numerik */}
              <span className="text-sm font-semibold text-neutral-800 min-w-[40px] text-right">
                {scores[criteria.key]}/25
              </span>
            </div>

            {/* Slider + Input number */}
            <div className="flex items-center gap-3">
              <input
                id={`bant-${criteria.key}`}
                type="range"
                min={0}
                max={25}
                step={1}
                value={scores[criteria.key]}
                onChange={(e) => updateScore(criteria.key, parseInt(e.target.value))}
                disabled={disabled || isSubmitting}
                className="flex-1 h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-primary-500 disabled:opacity-50"
                aria-valuemin={0}
                aria-valuemax={25}
                aria-valuenow={scores[criteria.key]}
                aria-label={`Skor ${criteria.label}: ${scores[criteria.key]} dari 25`}
              />
              <input
                type="number"
                min={0}
                max={25}
                step={1}
                value={scores[criteria.key]}
                onChange={(e) => updateScore(criteria.key, parseInt(e.target.value) || 0)}
                disabled={disabled || isSubmitting}
                className="w-16 px-2 py-1 border border-neutral-300 rounded-md text-center text-sm
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                  disabled:opacity-50 disabled:bg-neutral-100"
                aria-label={`Input numerik skor ${criteria.label}`}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Submit button */}
      <button
        type="submit"
        disabled={disabled || isSubmitting}
        className={`
          w-full py-3 px-4 rounded-lg font-medium text-white transition-all duration-200
          ${isSubmitting
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
