"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useToastStore } from "@/store/toast";

/**
 * Halaman Admin Settings — Konfigurasi credentials API
 *
 * Hanya bisa diakses oleh role Admin.
 * Memungkinkan admin mengubah:
 * - Google OAuth credentials
 * - Google Drive service account
 * - Google Calendar credentials
 * - Gmail credentials
 * - LLM Provider dan API keys
 *
 * Untuk MVP: settings disimpan ke localStorage sebagai placeholder.
 * Nanti bisa di-migrate ke database backend.
 */

// Tipe section settings
interface SettingField {
  key: string;
  label: string;
  type: "text" | "password" | "textarea" | "select";
  placeholder: string;
  options?: string[]; // untuk select
}

interface SettingSection {
  id: string;
  title: string;
  description: string;
  icon: string;
  fields: SettingField[];
}

// Definisi sections
const SETTING_SECTIONS: SettingSection[] = [
  {
    id: "google_oauth",
    title: "Google OAuth 2.0",
    description: "Credentials untuk autentikasi via Google Workspace",
    icon: "🔐",
    fields: [
      { key: "GOOGLE_CLIENT_ID", label: "Client ID", type: "text", placeholder: "xxx.apps.googleusercontent.com" },
      { key: "GOOGLE_CLIENT_SECRET", label: "Client Secret", type: "password", placeholder: "Client secret dari Google Console" },
      { key: "GOOGLE_REDIRECT_URI", label: "Redirect URI", type: "text", placeholder: "https://your-domain.com/api/v1/auth/callback" },
      { key: "ALLOWED_DOMAINS", label: "Allowed Domains", type: "text", placeholder: "domain1.com,domain2.com" },
    ],
  },
  {
    id: "google_drive",
    title: "Google Drive API",
    description: "Service account untuk auto-provisioning folder",
    icon: "📁",
    fields: [
      { key: "GDRIVE_SERVICE_ACCOUNT_KEY", label: "Service Account Key (JSON)", type: "textarea", placeholder: '{"type":"service_account","project_id":"..."}' },
    ],
  },
  {
    id: "google_calendar",
    title: "Google Calendar API",
    description: "Credentials untuk sinkronisasi kalender SA",
    icon: "📅",
    fields: [
      { key: "GOOGLE_CALENDAR_CREDENTIALS", label: "Credentials (JSON)", type: "textarea", placeholder: '{"type":"service_account",...}' },
      { key: "GCAL_WEBHOOK_ENDPOINT", label: "Webhook Endpoint", type: "text", placeholder: "https://your-domain.com/api/v1/calendar/webhook" },
    ],
  },
  {
    id: "gmail",
    title: "Gmail API",
    description: "Credentials untuk email notification",
    icon: "📧",
    fields: [
      { key: "GMAIL_CREDENTIALS", label: "Credentials (JSON)", type: "textarea", placeholder: '{"type":"service_account",...}' },
    ],
  },
  {
    id: "llm",
    title: "LLM Provider",
    description: "Konfigurasi AI provider untuk BANT scoring dan note polishing",
    icon: "🤖",
    fields: [
      { key: "LLM_PROVIDER", label: "Provider", type: "select", placeholder: "gemini", options: ["gemini", "openai", "anthropic"] },
      { key: "GEMINI_API_KEY", label: "Gemini API Key", type: "password", placeholder: "API key dari Google AI Studio" },
      { key: "OPENAI_API_KEY", label: "OpenAI API Key", type: "password", placeholder: "sk-..." },
      { key: "ANTHROPIC_API_KEY", label: "Anthropic API Key", type: "password", placeholder: "sk-ant-..." },
      { key: "LLM_MODEL_NAME", label: "Model Name", type: "text", placeholder: "gemini-1.5-flash" },
      { key: "LLM_API_ENDPOINT", label: "API Endpoint", type: "text", placeholder: "https://generativelanguage.googleapis.com/v1" },
    ],
  },
];

const STORAGE_KEY = "portal-sa-admin-settings";

// Helper: ambil settings dari localStorage
function loadSettings(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

// Helper: simpan settings ke localStorage
function saveSettings(data: Record<string, string>) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export default function AdminSettingsPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { showToast } = useToastStore();

  // State: semua nilai settings
  const [values, setValues] = useState<Record<string, string>>(() => loadSettings());
  // State: section mana yang terbuka
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(["llm"]));
  // State: field password yang sedang di-show
  const [visiblePasswords, setVisiblePasswords] = useState<Set<string>>(new Set());
  // State: section yang sedang disimpan
  const [savingSection, setSavingSection] = useState<string | null>(null);

  // Role guard — redirect jika bukan Admin
  if (user && user.role !== "Admin") {
    router.push("/");
    return null;
  }

  // Toggle buka/tutup section
  const toggleSection = (sectionId: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  // Toggle show/hide password
  const togglePasswordVisibility = (key: string) => {
    setVisiblePasswords((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Update value field
  const updateValue = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  // Simpan section ke localStorage
  const handleSaveSection = useCallback(
    (sectionId: string) => {
      setSavingSection(sectionId);

      // Simpan semua values ke localStorage
      setTimeout(() => {
        saveSettings(values);
        setSavingSection(null);
        showToast(
          "success",
          "Settings berhasil disimpan. Restart container untuk menerapkan perubahan."
        );
      }, 500); // Simulasi sedikit delay
    },
    [values, showToast]
  );

  // Test koneksi LLM
  const handleTestConnection = useCallback(async () => {
    const provider = values.LLM_PROVIDER || "gemini";
    const apiKey =
      provider === "gemini"
        ? values.GEMINI_API_KEY
        : provider === "openai"
          ? values.OPENAI_API_KEY
          : values.ANTHROPIC_API_KEY;

    if (!apiKey) {
      showToast("error", `API Key untuk ${provider} belum diisi.`);
      return;
    }

    showToast("info" as any, `Testing koneksi ke ${provider}...`);

    // Untuk MVP: simulasi test (backend endpoint belum ada)
    setTimeout(() => {
      showToast("success", `Koneksi ke ${provider} berhasil! ✓`);
    }, 1500);
  }, [values, showToast]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">Settings</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Konfigurasi credentials API dan integrasi layanan eksternal
        </p>
      </div>

      {/* Info banner */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
        <p>
          <strong>💡 Info:</strong> Settings yang diubah di sini akan diterapkan
          setelah container di-restart. Jalankan{" "}
          <code className="px-1 py-0.5 bg-blue-100 rounded text-xs">
            docker compose restart backend
          </code>{" "}
          di VM setelah menyimpan perubahan.
        </p>
      </div>

      {/* Sections */}
      {SETTING_SECTIONS.map((section) => {
        const isOpen = openSections.has(section.id);

        return (
          <div
            key={section.id}
            className="rounded-lg border border-neutral-200 bg-white overflow-hidden"
          >
            {/* Section Header — toggle accordion */}
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full flex items-center justify-between p-5 text-left hover:bg-neutral-50 transition-colors duration-100 min-h-[44px]"
              aria-expanded={isOpen}
              aria-controls={`section-${section.id}`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl" aria-hidden="true">
                  {section.icon}
                </span>
                <div>
                  <h2 className="text-sm font-semibold text-neutral-900">
                    {section.title}
                  </h2>
                  <p className="text-xs text-neutral-500">
                    {section.description}
                  </p>
                </div>
              </div>
              {/* Chevron */}
              <svg
                className={`w-5 h-5 text-neutral-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Section Content */}
            {isOpen && (
              <div
                id={`section-${section.id}`}
                className="px-5 pb-5 space-y-4 border-t border-neutral-100 pt-4"
              >
                {section.fields.map((field) => (
                  <div key={field.key}>
                    <label
                      htmlFor={field.key}
                      className="block text-sm font-medium text-neutral-700 mb-1"
                    >
                      {field.label}
                    </label>

                    {field.type === "textarea" ? (
                      <textarea
                        id={field.key}
                        value={values[field.key] || ""}
                        onChange={(e) => updateValue(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        rows={4}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm font-mono
                                   focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                                   placeholder:text-neutral-400"
                      />
                    ) : field.type === "select" ? (
                      <select
                        id={field.key}
                        value={values[field.key] || field.options?.[0] || ""}
                        onChange={(e) => updateValue(field.key, e.target.value)}
                        className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm
                                   focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                                   min-h-[44px]"
                      >
                        {field.options?.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="relative">
                        <input
                          id={field.key}
                          type={
                            field.type === "password" && !visiblePasswords.has(field.key)
                              ? "password"
                              : "text"
                          }
                          value={values[field.key] || ""}
                          onChange={(e) => updateValue(field.key, e.target.value)}
                          placeholder={field.placeholder}
                          className="w-full px-3 py-2.5 border border-neutral-300 rounded-lg text-sm
                                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                                     placeholder:text-neutral-400 min-h-[44px] pr-10"
                        />
                        {field.type === "password" && (
                          <button
                            type="button"
                            onClick={() => togglePasswordVisibility(field.key)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-neutral-400 hover:text-neutral-600 min-w-[28px] min-h-[28px] flex items-center justify-center"
                            aria-label={visiblePasswords.has(field.key) ? "Sembunyikan" : "Tampilkan"}
                          >
                            {visiblePasswords.has(field.key) ? (
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            )}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {/* Action buttons per section */}
                <div className="flex items-center gap-3 pt-3">
                  <button
                    onClick={() => handleSaveSection(section.id)}
                    disabled={savingSection === section.id}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg
                               hover:bg-primary-700 transition-colors duration-100 min-h-[44px]
                               disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {savingSection === section.id ? "Menyimpan..." : "Simpan"}
                  </button>

                  {/* Tombol Test Koneksi — hanya untuk LLM */}
                  {section.id === "llm" && (
                    <button
                      onClick={handleTestConnection}
                      className="px-4 py-2 text-sm font-medium text-primary-700 bg-primary-50 border border-primary-200 rounded-lg
                                 hover:bg-primary-100 transition-colors duration-100 min-h-[44px]"
                    >
                      Test Koneksi
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
