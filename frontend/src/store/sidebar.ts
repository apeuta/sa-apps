import { create } from "zustand";

/**
 * Zustand store untuk state sidebar navigation
 *
 * State:
 * - isOpen: apakah sidebar sedang terbuka (240px) atau collapsed (64px)
 *
 * Actions:
 * - toggle: toggle buka/tutup sidebar
 * - open: paksa buka sidebar
 * - close: paksa tutup sidebar
 */

interface SidebarState {
  isOpen: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isOpen: true,
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}));
