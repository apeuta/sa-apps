/**
 * API Client untuk Admin Settings
 *
 * Untuk MVP: semua data disimpan ke localStorage sebagai placeholder.
 * Nanti akan diganti dengan backend API setelah endpoint tersedia.
 */

// Key localStorage untuk menyimpan settings
const SETTINGS_STORAGE_KEY = "sa_portal_admin_settings";

// Tipe data settings per kategori
export interface GoogleOAuthSettings {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  allowedDomains: string;
}

export interface GoogleDriveSettings {
  serviceAccountKey: string;
}

export interface GoogleCalendarSettings {
  credentials: string;
  webhookEndpoint: string;
}

export interface GmailSettings {
  credentials: string;
}

export interface LLMProviderSettings {
  provider: "gemini" | "openai" | "anthropic";
  apiKey: string;
  modelName: string;
  endpoint: string;
}

export interface AdminSettings {
  googleOAuth: GoogleOAuthSettings;
  googleDrive: GoogleDriveSettings;
  googleCalendar: GoogleCalendarSettings;
  gmail: GmailSettings;
  llmProvider: LLMProviderSettings;
}

// Default values untuk settings kosong
const DEFAULT_SETTINGS: AdminSettings = {
  googleOAuth: {
    clientId: "",
    clientSecret: "",
    redirectUri: "",
    allowedDomains: "",
  },
  googleDrive: {
    serviceAccountKey: "",
  },
  googleCalendar: {
    credentials: "",
    webhookEndpoint: "",
  },
  gmail: {
    credentials: "",
  },
  llmProvider: {
    provider: "gemini",
    apiKey: "",
    modelName: "",
    endpoint: "",
  },
};

/**
 * Ambil semua settings dari localStorage
 * Nanti diganti dengan GET /api/v1/admin/settings
 */
export function getSettings(): AdminSettings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;

  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!stored) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

/**
 * Simpan settings per kategori ke localStorage
 * Nanti diganti dengan PUT /api/v1/admin/settings
 */
export async function updateSettings<K extends keyof AdminSettings>(
  category: K,
  data: AdminSettings[K]
): Promise<{ success: boolean; message: string }> {
  // Simulasi network delay untuk UX realistis
  await new Promise((resolve) => setTimeout(resolve, 500));

  try {
    const current = getSettings();
    const updated = { ...current, [category]: data };
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(updated));
    return { success: true, message: "Settings berhasil disimpan" };
  } catch {
    return { success: false, message: "Gagal menyimpan settings" };
  }
}

/**
 * Test koneksi ke LLM Provider (mock untuk MVP)
 * Nanti diganti dengan POST /api/v1/admin/settings/test-connection
 */
export async function testConnection(
  provider: string,
  apiKey: string
): Promise<{ success: boolean; message: string }> {
  // Simulasi network delay
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Mock: berhasil jika API key tidak kosong
  if (!apiKey.trim()) {
    return { success: false, message: "API Key tidak boleh kosong" };
  }

  return {
    success: true,
    message: `Koneksi ke ${provider} berhasil (mock response)`,
  };
}
