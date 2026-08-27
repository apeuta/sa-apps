"use client";

import { useSidebarStore } from "@/store/sidebar";
import { useAuthStore } from "@/store/auth";

/**
 * Sidebar Navigation — collapsible (Requirement 19.7)
 *
 * Lebar:
 * - Terbuka: 240px
 * - Collapsed: 64px
 *
 * Fitur:
 * - Toggle collapse/expand
 * - Navigation links sesuai role user
 * - Menu "Settings" hanya tampil untuk Admin
 * - Touch target min 44x44px (Requirement 12.3)
 */

// Item navigasi utama
const navItems = [
  { label: "Dashboard", href: "/", icon: "📊" },
  { label: "Proyek", href: "/projects", icon: "📁" },
  { label: "Activity Log", href: "/activity-logs", icon: "📝" },
  { label: "Dokumen", href: "/documents", icon: "📄" },
  { label: "Notifikasi", href: "/notifications", icon: "🔔" },
];

// Item navigasi khusus Admin
const adminNavItems = [
  { label: "Settings", href: "/admin/settings", icon: "⚙️" },
];

export function Sidebar() {
  const { isOpen, toggle } = useSidebarStore();
  const { user } = useAuthStore();

  return (
    <aside
      className={`
        flex flex-col bg-white border-r border-neutral-200 
        transition-all duration-200 ease-in-out
        h-screen shrink-0
        ${isOpen ? "w-[240px]" : "w-[64px]"}
      `}
    >
      {/* Logo dan toggle */}
      <div className="flex items-center justify-between h-[64px] px-4 border-b border-neutral-100">
        {isOpen && (
          <span className="text-lg font-semibold text-primary-600 truncate">
            Portal SA
          </span>
        )}
        <button
          onClick={toggle}
          className="flex items-center justify-center w-[44px] h-[44px] rounded-lg 
                     hover:bg-neutral-100 transition-colors duration-100"
          aria-label={isOpen ? "Tutup sidebar" : "Buka sidebar"}
          title={isOpen ? "Tutup sidebar" : "Buka sidebar"}
        >
          <svg
            className={`w-5 h-5 text-neutral-600 transition-transform duration-200 ${
              isOpen ? "" : "rotate-180"
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
            />
          </svg>
        </button>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => (
            <li key={item.href}>
              <a
                href={item.href}
                className={`
                  flex items-center gap-3 rounded-lg px-3 
                  min-h-[44px] min-w-[44px]
                  text-neutral-700 hover:bg-neutral-100 hover:text-primary-600
                  transition-colors duration-100
                  ${isOpen ? "" : "justify-center"}
                `}
                title={item.label}
              >
                <span className="text-xl shrink-0">{item.icon}</span>
                {isOpen && (
                  <span className="text-sm font-medium truncate">
                    {item.label}
                  </span>
                )}
              </a>
            </li>
          ))}

          {/* Admin-only menu items */}
          {user?.role === "Admin" && (
            <>
              <li className="pt-3 mt-3 border-t border-neutral-100">
                {isOpen && (
                  <span className="px-3 text-xs font-semibold text-neutral-400 uppercase">
                    Admin
                  </span>
                )}
              </li>
              {adminNavItems.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    className={`
                      flex items-center gap-3 rounded-lg px-3 
                      min-h-[44px] min-w-[44px]
                      text-neutral-700 hover:bg-neutral-100 hover:text-primary-600
                      transition-colors duration-100
                      ${isOpen ? "" : "justify-center"}
                    `}
                    title={item.label}
                  >
                    <span className="text-xl shrink-0">{item.icon}</span>
                    {isOpen && (
                      <span className="text-sm font-medium truncate">
                        {item.label}
                      </span>
                    )}
                  </a>
                </li>
              ))}
            </>
          )}
        </ul>
      </nav>

      {/* Footer — info user (placeholder) */}
      <div className="border-t border-neutral-100 p-3">
        <div
          className={`flex items-center gap-3 ${isOpen ? "" : "justify-center"}`}
        >
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
            <span className="text-sm font-medium text-primary-600">U</span>
          </div>
          {isOpen && (
            <div className="truncate">
              <p className="text-sm font-medium text-neutral-700 truncate">
                User
              </p>
              <p className="text-xs text-neutral-400 truncate">SA</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
