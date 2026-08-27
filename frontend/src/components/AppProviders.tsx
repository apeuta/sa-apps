"use client";

/**
 * Provider global yang menginisialisasi:
 * - Toast notifications (Requirement 19.8, 19.9)
 * - Offline sync queue (Requirement 12.5)
 * - Offline indicator (Requirement 12.5)
 */

import { useEffect } from "react";
import { ToastContainer } from "@/components/Toast";
import { OfflineIndicator } from "@/components/OfflineIndicator";
import { initOfflineSync } from "@/lib/offline-queue";

export function AppProviders({ children }: { children: React.ReactNode }) {
  // Inisialisasi offline sync listener saat app mount
  useEffect(() => {
    const cleanup = initOfflineSync();
    return cleanup;
  }, []);

  return (
    <>
      {children}
      <ToastContainer />
      <OfflineIndicator />
    </>
  );
}

export default AppProviders;
