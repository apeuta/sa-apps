# Design — Upgrade Toolchain: Node 24 + pnpm 12 + Next.js 16

## Ikhtisar

Overhaul toolchain frontend dalam tiga sumbu yang bertautan: runtime (Node 24), package manager (pnpm 12 via mise), dan framework (Next.js 16 + React 19). Dokumen ini menjelaskan pendekatan, keputusan, titik risiko, dan strategi verifikasi.

Referensi versi (per riset 19 Okt 2026):
- Next.js **16** = current LTS (rilis terbaru 16.4.2). Next.js 15 maintenance LTS berakhir 21 Okt 2026; 14 sudah EOL (26 Okt 2025). Sumber: endoflife.date/nextjs.
- pnpm **12** = current stable line (Rust rewrite); mise bisa mem-pin. Sumber: pnpm.io.
- Node **24** = current LTS.

## Strategi branching: pisah atau satu PR

Dua perubahan punya profil risiko berbeda:

- **Toolchain (Node 24 + pnpm 12)** — mekanis, risiko rendah, mudah diverifikasi (install + build hijau).
- **Next.js 16 + React 19** — major breaking, butuh adaptasi kode dan verifikasi runtime menyeluruh.

**Keputusan:** pisah menjadi dua fase berurutan di dua branch/PR:

1. **Fase A — `chore/toolchain-node24-pnpm`**: Node 24, pnpm 12 via mise, migrasi lockfile, Dockerfile Alpine + pnpm, docs. Masih di Next.js 14. Diverifikasi: `pnpm install` + `pnpm run build` + stack naik.
2. **Fase B — `chore/next16-react19`** (di-branch dari main setelah Fase A merge): upgrade Next 16 + React 19, adaptasi async API & caching, verifikasi runtime penuh.

Alasan: memisahkan variabel. Jika build pecah di Fase B, penyebabnya pasti upgrade framework, bukan tercampur dengan perpindahan package manager. Ini juga menjaga tiap PR tetap bisa di-review sebagai satu unit (sesuai workflow overhaul di CONTRIBUTING.md).

> Catatan: urutan ini sengaja menaruh pnpm lebih dulu agar Fase B memakai pnpm sejak awal (upgrade Next dijalankan & diuji di bawah pnpm, bukan npm yang nanti dibuang).

## Fase A — Toolchain (Node 24 + pnpm 12)

### A1. mise.toml

```toml
[tools]
python = "3.11"
node = "24"
pnpm = "12"
uv = "0.13"
```

Perbarui komentar header yang menyebut `node:20-alpine` → `node:24-alpine`. Blok `[hooks]` dan `[tasks.setup-hooks]` tidak berubah.

### A2. Migrasi lockfile

Langkah (dijalankan di `frontend/`):
1. `pnpm import` — membaca `package-lock.json` dan menghasilkan `pnpm-lock.yaml` dengan versi ter-resolve yang setara.
2. Hapus `package-lock.json`.
3. `pnpm install` — materialisasi `node_modules` dari lockfile baru, memastikan konsistensi.

Tidak menambah field `packageManager` di `package.json` (lihat keputusan corepack di bawah). Boleh menambah `"engines": { "node": ">=24" }` sebagai dokumentasi intent (opsional, non-blocking).

### A3. Dockerfile frontend (shape B — Alpine, tanpa corepack)

Base ketiga stage: `node:24-alpine`.

Stage deps — ganti blok auto-deteksi lockfile dengan jalur pnpm eksplisit:

```dockerfile
FROM node:24-alpine AS deps
WORKDIR /app
RUN npm i -g pnpm@12
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
```

Stage builder — build via pnpm:

```dockerfile
FROM node:24-alpine AS builder
WORKDIR /app
RUN npm i -g pnpm@12
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm run build
```

Stage runtime: tetap `node:24-alpine`, menjalankan `node server.js` dari `.next/standalone` (tidak butuh pnpm di runtime). Bagian user non-root, EXPOSE, ENV runtime tidak berubah.

Hapus baris lama:
- `COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./` (ganti ke COPY pnpm-only).
- Blok `if [ -f yarn.lock ] ... elif ... corepack enable pnpm ...` (dead code + corepack).
- `RUN npm run build` → `RUN pnpm run build`.

### A4. Keputusan corepack (ditegaskan)

corepack **bisa** jalan di Alpine (ter-bundle dengan Node ≥16.9 di `node:24-alpine`), jadi secara teknis bukan penghalang. Tetap **tidak dipakai** karena:
- Bertentangan dengan keinginan eksplisit user: seluruh toolchain lewat mise, bukan corepack.
- corepack adalah version manager paralel yang bersaing dengan mise untuk kepemilikan pnpm → risiko drift.
- corepack mem-pin lewat field `packageManager`, menambah sumber kebenaran kedua yang bisa bentrok dengan mise.
- Jalur distribusi corepack (bundling dengan Node, signature keys) historisnya kurang stabil di CI.

`npm i -g pnpm@12` membawa pnpm 12 secara eksplisit dan ter-pin, memakai npm yang sudah ada di base image hanya sebagai bootstrap sekali pakai. mise tetap pemilik tunggal versi untuk dev lokal.

### A5. Dokumentasi (Fase A)

- `AGENTS.md`: "Python 3.11, Node 20 (di-pin major)" → "Python 3.11, Node 24, pnpm 12 (di-pin major)"; sebut pnpm sebagai package manager frontend.
- `CONTRIBUTING.md`: tabel toolchain (Node 20 → 24; tambah baris pnpm 12); `node:20-alpine` → `node:24-alpine`; catatan "Frontend — script di `package.json`" perjelas pakai pnpm.
- `frontend/.dockerignore`: komentar `npm ci` / `npm run build` → padanan pnpm.
- `frontend/README.md`: perintah `npm ...` → `pnpm ...` (jika ada).

### A6. Verifikasi Fase A

- `mise install` memasang Node 24 + pnpm 12.
- `pnpm install` di `frontend/` sukses; `pnpm run build` (masih Next 14) hijau.
- `docker compose build frontend` sukses; `docker compose up` → `/health` healthy; frontend tersaji di :3000.

## Fase B — Next.js 16 + React 19

### B1. Bump dependency

`frontend/package.json`:
- `next`: `14.2.3` → `^16.x` (versi stable terbaru, di-pin).
- `react` / `react-dom`: `18.3.1` → `^19.x`.
- `@types/react` / `@types/react-dom`: ke versi React 19.
- `eslint-config-next` / konfigurasi lint: samakan dengan 16 (jika ada).
- Dependency lain (`swr`, `zustand`) dicek kompatibilitas React 19; naikkan jika perlu, pin exact.

Boleh pakai codemod resmi `npx @next/codemod@latest upgrade latest` sebagai titik awal, lalu review manual tiap perubahan.

### B2. Area breaking yang harus diperiksa (file konkret)

Berdasarkan inventaris frontend:

1. **Async request APIs (Next 15+):** `params` & `searchParams` kini async (Promise).
   - `app/(protected)/projects/[id]/page.tsx`
   - `app/(protected)/projects/[id]/edit/page.tsx`
   - `app/(protected)/projects/[id]/documents/page.tsx`
   - `app/api/v1/[...path]/route.ts` (catch-all handler — params async; cek signature `GET/POST/...(req, { params })`)
   - `app/(auth)/auth/callback/page.tsx` (kemungkinan membaca `searchParams`/code OAuth)
   - Page lain yang membaca `searchParams`.
   - `cookies()` / `headers()` jika dipakai di server component / route handler → kini async (`await`).

2. **Default caching berubah:** `fetch` tidak lagi auto-cache; route handler `GET` tidak lagi static default; client router cache `staleTime` default berubah. Tinjau `lib/fetcher.ts`, `lib/api/*.ts`, dan `api/v1/[...path]/route.ts`. Pulihkan caching eksplisit hanya di tempat yang memang mengandalkannya.

3. **React 19:** perubahan pada tipe, `ref` sebagai prop, `useRef` butuh argumen, penghapusan API lama. Periksa komponen dengan `forwardRef`, context providers (`AppProviders.tsx`, `AuthGuard.tsx`), dan hook kustom.

4. **next.config.js:** opsi yang di-deprecate/pindah di 15/16; pastikan `output: 'standalone'` tetap ada (dipakai Dockerfile runtime).

5. **PWA:** jika ada plugin PWA, cek kompatibilitas dengan Next 16; standalone output harus tetap menghasilkan `server.js`.

### B3. Verifikasi Fase B (wajib, runtime nyata)

Build & statis:
- `pnpm run lint` lolos.
- type-check (`tsc --noEmit` / `next build` type pass) lolos.
- `pnpm run build` hijau, menghasilkan `.next/standalone`.

Runtime (via Docker Compose full stack, `/health` healthy), telusuri nyata:
- Login + `auth/callback` (OAuth flow).
- Dashboard (sa / lead-sa / sales).
- Daftar project → detail `projects/[id]` → edit → documents (dynamic params).
- Buat project baru.
- Activity log + calendar.
- Proxy `api/v1/[...path]` meneruskan ke backend dengan benar.
- Tidak ada runtime error di console browser.

Setiap breaking change yang ditemukan dicatat di deskripsi PR (file, apa yang berubah, perbaikannya).

## Risiko & mitigasi

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Next 14→16 melewati 2 major sekaligus | Banyak perubahan perilaku tak terlihat saat compile | Pakai codemod resmi + review manual + verifikasi runtime penuh, bukan hanya build hijau |
| React 19 memecah dependency (swr/zustand) | Runtime error / tipe gagal | Cek matriks kompatibilitas; naikkan & pin exact; uji di browser |
| Default caching berubah diam-diam | Data stale/segar tak sesuai ekspektasi | Audit `fetcher.ts` + `lib/api/*`; pulihkan caching eksplisit di titik yang mengandalkannya |
| mise tak jalan di Docker | pnpm absen di image | Install eksplisit `npm i -g pnpm@12` di Dockerfile (pin sama dengan mise) |
| standalone output rusak setelah upgrade | Image runtime gagal start | Pastikan `output: 'standalone'`; uji `node server.js` di container |
| Alur OAuth callback pakai searchParams sync | Login pecah di 16 | Adaptasi ke async searchParams; uji login end-to-end |

## Yang TIDAK termasuk

- Backend (Python/uv) tidak disentuh.
- PostgreSQL 15 tidak berubah.
- Spec `sa-portal-mvp` (historis) tidak diedit meski menyebut Node 20.
- Tidak menambah test framework baru ke frontend kecuali diminta; verifikasi via build + runtime manual sesuai verification gate repo.
