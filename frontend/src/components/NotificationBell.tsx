"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";

/**
 * Komponen NotificationBell — Bell icon dengan badge unread count
 *
 * Fitur:
 * - Menampilkan ikon bell di header
 * - Badge merah dengan jumlah notifikasi belum dibaca
 * - Klik → navigasi ke halaman /notifications
 * - Poll unread count dengan SWR (revalidateOnFocus + interval 30 detik)
 *
 * Requirements: 14.7
 */

/** Response dari endpoint unread-count */
interface UnreadCountData {
  count: number;
}

export function NotificationBell() {
  const router = useRouter();

  // Ambil unread count dengan polling setiap 30 detik
  const { data } = useSWR<UnreadCountData>(
    "/notifications/unread-count",
    fetcher,
    {
      refreshInterval: 30000, // Poll setiap 30 detik
      revalidateOnFocus: true,
    }
  );

  const unreadCount = data?.count ?? 0;

  return (
    <button
      onClick={() => router.push("/notifications")}
      className="flex items-center justify-center w-[44px] h-[44px] rounded-lg
                 hover:bg-neutral-100 transition-colors duration-100 relative"
      aria-label={`Notifikasi${unreadCount > 0 ? `, ${unreadCount} belum dibaca` : ""}`}
    >
      {/* Ikon Bell */}
      <svg
        className="w-5 h-5 text-neutral-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>

      {/* Badge unread count */}
      {unreadCount > 0 && (
        <span
          className="absolute top-1.5 right-1.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center
                     bg-red-500 text-white text-[10px] font-bold rounded-full leading-none"
          aria-hidden="true"
        >
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      )}
    </button>
  );
}
