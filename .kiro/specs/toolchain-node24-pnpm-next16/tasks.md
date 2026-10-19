# Tasks — Upgrade Toolchain: Node 24 + pnpm 12 + Next.js 16

Dikerjakan dalam dua fase/branch berurutan (lihat design.md). Fase B di-branch dari `main` setelah Fase A merge. Jangan commit langsung ke `main`.

## Fase A — Toolchain (Node 24 + pnpm 12) — branch `chore/toolchain-node24-pnpm`

- [x] 1. Pin Node 24 + pnpm 12 di mise
  - Ubah `node = "20"` → `node = "24"` dan tambah `pnpm = "12"` di `[tools]` pada `mise.toml`
  - Perbarui komentar header yang menyebut `node:20-alpine` → `node:24-alpine`
  - Jalankan `mise install` dan konfirmasi Node 24 + pnpm 12 aktif
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2_

- [x] 2. Migrasi lockfile npm → pnpm
  - Di `frontend/`: jalankan `pnpm import` untuk membuat `pnpm-lock.yaml` dari `package-lock.json`
  - Hapus `frontend/package-lock.json`
  - Jalankan `pnpm install` dan pastikan `node_modules` ter-materialisasi tanpa error
  - Pastikan `package.json` tidak memuat field `packageManager`
  - _Requirements: 2.3, 2.4, 2.5, 2.6_

- [x] 3. Perbarui Dockerfile frontend ke Alpine + pnpm (shape B)
  - Ganti base ketiga stage ke `node:24-alpine`
  - Tambah `RUN npm i -g pnpm@12` di stage deps dan builder; hapus blok auto-deteksi lockfile + `corepack`
  - COPY `package.json pnpm-lock.yaml ./`; stage deps pakai `pnpm install --frozen-lockfile`
  - Ganti `RUN npm run build` → `RUN pnpm run build`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Perbarui `.dockerignore` dan verifikasi build image (Fase A)
  - Selaraskan komentar `frontend/.dockerignore` ke install path pnpm
  - `docker build frontend/` sukses di Node 24 + pnpm 12 (image Next standalone, Node v24.22.0 di runtime); container start bersih (`✓ Ready`), `/manifest.json` → 200
  - FIX ditemukan saat verifikasi: `COPY /app/public` kehilangan `--chown=nextjs:nodejs` → runtime non-root gagal baca `public/icons` (EACCES). Pre-existing bug, diperbaiki di branch ini.
  - _Requirements: 3.6, 3.7, 5.1_

- [x] 5. Verifikasi build lokal Fase A (masih Next 14)
  - `pnpm run build` di `frontend/` hijau (16 route, Next 14 bersih)
  - CATATAN: `pnpm run lint` TIDAK hijau — ESLint belum terpasang/terkonfigurasi di repo (pre-existing, di luar scope Fase A). Ditangani sebagai pekerjaan terpisah, bukan di sini.
  - Konfirmasi perintah frontend lain (jika ada script) jalan di bawah pnpm
  - _Requirements: 2.6, 2.7, 5.1, 5.2_

- [x] 6. Perbarui dokumentasi toolchain (Fase A)
  - `AGENTS.md`: Node 20 → 24; sebut pnpm sebagai package manager frontend
  - `CONTRIBUTING.md`: tabel toolchain (Node 24 + pnpm 12); `node:20-alpine` → `node:24-alpine`; catatan verifikasi frontend npm → pnpm
  - `frontend/README.md`: perintah npm → pnpm (jika ada)
  - Jangan ubah spec `sa-portal-mvp` (historis)
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [ ] 7. Buka PR Fase A
  - Branch `chore/toolchain-node24-pnpm`, Conventional Commits, stage file spesifik
  - Deskripsi PR mencatat apa yang berubah dan apa yang diverifikasi (build + stack naik)
  - _Requirements: 7.1, 7.2, 5.3_

## Fase B — Next.js 16 + React 19 — branch `chore/next16-react19` (dari main setelah Fase A merge)

- [x] 8. Bump Next 16 + React 19 di package.json
  - `next` → 16 stable terbaru (pin exact); `react`/`react-dom` → 19; `@types/react(-dom)` menyesuaikan
  - Cek kompatibilitas `swr` & `zustand` dengan React 19; naikkan + pin exact bila perlu
  - Opsional: jalankan `npx @next/codemod@latest upgrade latest` sebagai titik awal, lalu review manual
  - `pnpm install` dan regenerasi `pnpm-lock.yaml`
  - _Requirements: 4.1, 6.4_

- [x] 9. Adaptasi async request API (params/searchParams/cookies/headers)
  - `projects/[id]/page.tsx`, `projects/[id]/edit/page.tsx`, `projects/[id]/documents/page.tsx`
  - `api/v1/[...path]/route.ts` (params async pada handler)
  - `auth/callback/page.tsx` dan page lain yang membaca `searchParams`
  - Ubah akses sync `cookies()`/`headers()` menjadi `await`
  - _Requirements: 4.4, 4.6_

- [x] 10. Tinjau perubahan default caching Next 15+
  - Audit `lib/fetcher.ts`, `lib/api/*.ts`, `api/v1/[...path]/route.ts`
  - Pulihkan caching eksplisit hanya di titik yang mengandalkan perilaku lama
  - _Requirements: 4.5_

- [x] 11. Perbaiki breaking React 19 & next.config.js
  - Periksa `forwardRef`/`ref`, `AppProviders.tsx`, `AuthGuard.tsx`, hook kustom
  - Sesuaikan `next.config.js` untuk opsi yang berubah; pastikan `output: 'standalone'` tetap ada
  - Konfirmasi konfigurasi PWA/standalone tetap menghasilkan `server.js`
  - _Requirements: 4.6, 4.8, 4.9_

- [x] 12. Verifikasi statis Fase B
  - `pnpm run lint` lolos; type-check lolos; `pnpm run build` hijau menghasilkan `.next/standalone`
  - _Requirements: 4.2, 4.3, 5.1_

- [x] 13. Verifikasi runtime nyata Fase B (full stack)
  - `docker compose up` → `/health` healthy
  - Telusuri nyata: login + `auth/callback`, dashboard (sa/lead-sa/sales), daftar→detail `projects/[id]`→edit→documents, buat project, activity log + calendar, proxy `api/v1/[...path]`
  - Pastikan tidak ada runtime error di console browser
  - Catat setiap breaking change yang ditemukan + perbaikannya
  - _Requirements: 4.7, 5.1, 5.2, 5.3, 5.4_

- [ ] 14. Buka PR Fase B
  - Branch `chore/next16-react19`, Conventional Commits, stage file spesifik
  - Deskripsi PR mendokumentasikan daftar breaking change + hasil verifikasi runtime
  - _Requirements: 7.1, 7.2, 7.3, 5.3_
