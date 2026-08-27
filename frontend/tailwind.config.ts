import type { Config } from "tailwindcss";

/**
 * Konfigurasi Tailwind CSS untuk Portal SA
 *
 * Design System:
 * - Font: Open Sans (Requirement 19.1)
 * - Warna: Netral + Primary accent (Requirement 19.3)
 * - Touch targets: 44px minimum (Requirement 12.3)
 * - Transisi: max 200ms (Requirement 19.6)
 * - Responsive: 320px–1440px (Requirement 12.3)
 */
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Font utama: Open Sans (Requirement 19.1)
      fontFamily: {
        sans: ['"Open Sans"', "system-ui", "-apple-system", "sans-serif"],
      },
      // Palet warna netral + accent (Requirement 19.3)
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6", // Accent color utama
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
        neutral: {
          50: "#fafafa",
          100: "#f5f5f5",
          200: "#e5e5e5",
          300: "#d4d4d4",
          400: "#a3a3a3",
          500: "#737373",
          600: "#525252",
          700: "#404040",
          800: "#262626",
          900: "#171717",
          950: "#0a0a0a",
        },
      },
      // Spacing konsisten (Requirement 19.2, 19.7)
      spacing: {
        "sidebar-open": "240px",
        "sidebar-collapsed": "64px",
        "header-h": "64px",
        "touch": "44px", // Touch target minimum (Requirement 12.3)
        "section": "16px", // Minimum padding antar section (Requirement 19.2)
      },
      // Transisi maksimal 200ms (Requirement 19.6)
      transitionDuration: {
        "fast": "100ms",
        "normal": "200ms",
        "feedback": "50ms", // Feedback visual < 100ms (Requirement 19.4)
      },
      // Touch target minimal 44x44px (Requirement 12.3)
      minWidth: {
        "touch": "44px",
      },
      minHeight: {
        "touch": "44px",
      },
      // Max width untuk responsive layout
      maxWidth: {
        "content": "1440px",
      },
      // Font size scale — body min 16px, heading 1.25x+ (Requirement 12.3, 19.2)
      fontSize: {
        "body": ["16px", { lineHeight: "1.5" }],
        "sm": ["14px", { lineHeight: "1.5" }],
        "lg": ["18px", { lineHeight: "1.5" }],
        "xl": ["20px", { lineHeight: "1.4" }],
        "2xl": ["24px", { lineHeight: "1.3" }],
        "3xl": ["30px", { lineHeight: "1.2" }],
      },
      // Animasi (Requirement 19.6)
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "slide-out-right": {
          "0%": { opacity: "1", transform: "translateX(0)" },
          "100%": { opacity: "0", transform: "translateX(16px)" },
        },
      },
      animation: {
        "fade-in": "fade-in 200ms ease-out",
        "slide-in-right": "slide-in-right 200ms ease-out",
        "slide-out-right": "slide-out-right 200ms ease-out",
      },
      // Screens — responsive breakpoints (Requirement 12.3: 320px–1440px)
      screens: {
        "xs": "320px",
        // Default sm/md/lg/xl sudah cukup
      },
    },
  },
  plugins: [],
};

export default config;
