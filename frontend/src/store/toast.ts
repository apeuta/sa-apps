/**
 * Zustand store untuk toast notifications (Requirement 19.8, 19.9)
 *
 * Toast sukses: auto-dismiss 3 detik
 * Toast error: auto-dismiss 5 detik, warna berbeda
 */

import { create } from "zustand";

export type ToastType = "success" | "error" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  createdAt: number;
}

interface ToastState {
  toasts: Toast[];
  showToast: (type: ToastType, message: string) => void;
  dismissToast: (id: string) => void;
  clearAll: () => void;
}

// Durasi auto-dismiss berdasarkan tipe (dalam milidetik)
const DISMISS_DURATION: Record<ToastType, number> = {
  success: 3000, // 3 detik (Requirement 19.8)
  error: 5000, // 5 detik (Requirement 19.9)
  info: 4000,
};

// Map untuk menyimpan timeout IDs agar bisa dibersihkan
const dismissTimers = new Map<string, ReturnType<typeof setTimeout>>();

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  showToast: (type, message) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const toast: Toast = { id, type, message, createdAt: Date.now() };

    set((state) => ({
      toasts: [...state.toasts, toast],
    }));

    // Auto-dismiss setelah durasi tertentu
    const timer = setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
      dismissTimers.delete(id);
    }, DISMISS_DURATION[type]);

    dismissTimers.set(id, timer);
  },

  dismissToast: (id) => {
    // Bersihkan timer jika ada
    const timer = dismissTimers.get(id);
    if (timer) {
      clearTimeout(timer);
      dismissTimers.delete(id);
    }

    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  clearAll: () => {
    // Bersihkan semua timer
    dismissTimers.forEach((timer) => clearTimeout(timer));
    dismissTimers.clear();

    set({ toasts: [] });
  },
}));
