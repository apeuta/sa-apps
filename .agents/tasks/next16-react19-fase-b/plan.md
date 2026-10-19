# Implementation Plan — Fase B: Next.js 16 + React 19

Branch: `chore/next16-react19` (stacked di atas Fase A, BUKAN dari main).
Worktree root (semua path absolut di bawah ini): `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19`

Scope: tasks.md Fase B tugas 8–13. Tugas 14 ("Buka PR") DI LUAR SCOPE run ini.
Jangan sentuh backend, Fase A branch, main, atau `.kiro/specs/sa-portal-mvp/`.

## Temuan eksplorasi (dasar keputusan tiap item)

Diverifikasi dengan membaca source nyata di `frontend/src`:

1. **Semua page adalah client component** (`"use client"`). Dynamic route (`projects/[id]/*`) dan auth page memakai client hook `useParams()` / `useSearchParams()` dari `next/navigation` — hook ini **tetap sinkron** di Next 16. Perubahan async request API Next 15+ TIDAK menyentuh page-page ini. Grep atas 17 `page.tsx`: semua `"use client"`.
2. **Satu-satunya server-side async API** di repo: handler `GET/POST/PUT/PATCH/DELETE` di `frontend/src/app/api/v1/[...path]/route.ts`. `{ params }` kini `Promise<{ path: string[] }>` → wajib `await`. Tidak ada `cookies()`/`headers()` server-side (grep bersih; `new Headers(...)` di route hanyalah Web API, bukan `next/headers`).
3. **Caching: tidak ada yang perlu dipulihkan.** Semua fetch client-side (`localStorage` token, guard `typeof window`) di `lib/fetcher.ts` dan `lib/api/*.ts`. Proxy route inheren dinamis (baca `request.text()`, header per-request). Perubahan default caching Next 15+ hanya menyentuh `fetch` server-side yang tidak ada di repo. Keputusan: BIARKAN di default baru, jangan tambah caching apa pun.
4. **React 19:** tidak ada `forwardRef`, tidak ada `useRef()` tanpa argumen (grep bersih). Risiko tersisa: namespace global `JSX.Element` (dipakai di `components/Toast.tsx` dan `(protected)/notifications/page.tsx`) yang di `@types/react@19` bergeser ke `React.JSX`; `skipLibCheck:true` di tsconfig meredam churn tipe lib. `next.config.js` sudah minimal (`output: 'standalone'` saja). `public/sw.js` adalah service worker tulisan tangan (bukan plugin next-pwa) → tak ada masalah kompatibilitas plugin.
5. **Dependency React 19:** `swr ^2.2.5` aman di patch 2.3.x (peer menerima react 19). `zustand ^4.5.2` punya peer-dependency mismatch dengan React 19 (lihat pmndrs/zustand diskusi #2943/#3075) → naik ke v5. Ketiga store (`store/auth.ts`, `store/sidebar.ts`, `store/toast.ts`) memakai API `create<T>((set) => ...)` standar tanpa middleware → migrasi v4→v5 nol-kode.

Versi target (pin exact saat install, resolve dari registry):
- `next`: 16.x stable terbaru (per riset: lini 16.3.x/16.4.x). Resolve via `pnpm view next version`.
- `react` / `react-dom`: 19.x stable terbaru.
- `@types/react` / `@types/react-dom`: 19.x.
- `swr`: 2.3.x terbaru. `zustand`: 5.x terbaru.

---

## Items

- [ ] 1. Bump dependency ke Next 16 + React 19 + zustand 5 di `frontend/package.json`, lalu regenerasi lockfile.
      Set `next`, `react`, `react-dom` ke versi stable terbaru (pin EXACT, tanpa `^`); `@types/react` + `@types/react-dom` ke 19.x; `swr` ke 2.3.x exact; `zustand` ke 5.x exact. Boleh pakai `npx @next/codemod@latest upgrade latest` sebagai titik awal LALU review manual tiap diff (jangan terima buta). Setelah edit versi, jalankan `pnpm install` untuk meng-generate ulang `pnpm-lock.yaml`. CONTRIBUTING mewajibkan pin exact.
      Files: `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/package.json`, `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/pnpm-lock.yaml`
      Verify: `cd /Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend && pnpm install` selesai tanpa error peer-dependency; `pnpm view` tidak perlu — cek `pnpm ls next react zustand swr` menampilkan versi 16/19/5/2.3.

- [ ] 2. Adaptasi async `params` di route handler proxy — satu-satunya file async request API.
      Ubah tipe argumen kedua kelima handler (`GET/POST/PUT/PATCH/DELETE`) dari `{ params }: { params: { path: string[] } }` menjadi `{ params }: { params: Promise<{ path: string[] }> }`, lalu di dalam tiap handler `const { path } = await params;` dan teruskan `path` ke `proxyRequest`. Signature `proxyRequest(request, pathSegments, method)` tidak berubah. Tidak ada perubahan caching (route tetap dinamis by default — sesuai keputusan temuan #3).
      Files: `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/src/app/api/v1/[...path]/route.ts`
      Verify: termasuk dalam type-check & build item 5 (tidak ada error "params ... Promise"). Tidak ada file page lain yang perlu diubah untuk async params (temuan #1).

- [ ] 3. Perbaiki breaking React 19 bila muncul: namespace `JSX.Element`.
      Jika type-check (item 5) mengeluh soal `JSX` global, ganti anotasi `JSX.Element` → `React.JSX.Element` di dua lokasi, dan pastikan `import type React from "react"` tersedia bila perlu. HANYA lakukan jika type-check gagal karenanya — dengan `skipLibCheck:true` kemungkinan tetap lolos; jangan ubah kalau sudah hijau.
      Files: `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/src/components/Toast.tsx`, `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/src/app/(protected)/notifications/page.tsx`
      Verify: bagian dari type-check item 5.

- [ ] 4. Tinjau `next.config.js` untuk opsi deprecated Next 16; pertahankan `output: 'standalone'`.
      Konfirmasi tak ada key yang di-rename/hapus di 16 (file saat ini hanya `output: 'standalone'` → aman). JANGAN hapus `output: 'standalone'` (Dockerfile runtime menjalankan `node server.js` dari `.next/standalone`). Jika codemod item 1 menambah key, review dan buang yang tak perlu.
      Files: `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/next.config.js`
      Verify: build item 5 menghasilkan `.next/standalone/server.js`.

- [ ] 5. Verifikasi statis: type-check + build menghasilkan standalone.
      Jalankan type-check dan production build. Catatan: `pnpm run lint` TIDAK dikonfigurasi (ESLint sengaja absen, didokumentasikan di Fase A) — lint gagal/absen BUKAN kegagalan Fase B dan ESLint config TIDAK boleh ditambah.
      Files: — (verifikasi saja)
      Verify: `cd /Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend && pnpm exec tsc --noEmit` lolos; `pnpm run build` hijau dan menghasilkan `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend/.next/standalone/server.js` (cek `ls .next/standalone/server.js`).

- [ ] 6. Verifikasi runtime via Docker: build image frontend + start container + HTTP checks.
      Build image frontend (Dockerfile sudah Node 24 + pnpm dari Fase A), jalankan container, cek endpoint. docker-compose.yml memakai `image:` prebuilt (bukan `build:`), jadi build image langsung lalu jalankan standalone. Jika Docker daemon tak tersedia, nyatakan keterbatasan eksplisit (jangan klaim selesai).
      Files: — (verifikasi saja)
      Verify (static server, tanpa backend): `cd /Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/frontend && docker build -t sa-portal-frontend:fase-b-test .` sukses; `docker run -d --name fe-faseb -p 3999:3000 sa-portal-frontend:fase-b-test`; tunggu `✓ Ready`; `curl -sf http://localhost:3999/manifest.json` → 200 + JSON; `curl -sf http://localhost:3999/login` → 200 HTML (route ter-render). Full stack (jika `.env` + backend image tersedia): `docker compose up -d`, cek `/health` healthy dan proxy `api/v1`. Bersihkan: `docker rm -f fe-faseb`.

- [ ] 7. Update checkbox roadmap/tasks: Fase B tugas 8–13 → `[x]`, tugas 14 TETAP `[ ]`.
      Centang tugas 8, 9, 10, 11, 12, 13 di tasks.md. Biarkan tugas 14 ("Buka PR") tidak tercentang — di luar scope run ini.
      Files: `/Users/nikki/workspace/berca/projects/internal/sa-apps/.worktrees/next16-react19/.kiro/specs/toolchain-node24-pnpm-next16/tasks.md`
      Verify: `grep -n '^- \[' .kiro/specs/toolchain-node24-pnpm-next16/tasks.md` menampilkan 8–13 sebagai `[x]` dan 14 sebagai `[ ]`.

## Prosedur verifikasi lengkap (ringkas)

- Statis: `pnpm exec tsc --noEmit` (type-check) + `pnpm run build` (hijau, `.next/standalone/server.js` ada). Lint di-skip (ESLint absen by design).
- Runtime: `docker build` image frontend → `docker run` → `curl /manifest.json` (200) + route server-rendered (`/login` 200). Full stack via `docker compose up` + `/health` bila env tersedia; telusuri login/auth-callback, dashboard, projects detail/edit/documents, create project, activity log + calendar, proxy `api/v1/[...path]`; pastikan console browser tanpa runtime error.
- Setiap breaking change yang ditemukan dicatat (file, apa yang berubah, perbaikan).

## Catatan / asumsi

- Versi exact Next/React/zustand/swr di-resolve dari registry saat `pnpm install` (lini stable terbaru 16/19/5/2.3). Jika registry memunculkan versi lebih baru dalam lini major yang sama, pakai itu (tetap pin exact).
- Tidak menambah test framework baru; verifikasi lewat build + runtime manual sesuai verification gate repo.
