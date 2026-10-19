# Requirements — Upgrade Toolchain: Node 24 + pnpm 12 + Next.js 16

## Pendahuluan

Dokumen ini mendefinisikan scope untuk menaikkan toolchain frontend Portal SA ke versi current:

- **Node.js 20 → 24** (current LTS), di-pin via mise.
- **Package manager npm → pnpm 12**, di-pin via mise untuk development lokal.
- **Next.js 14.2.3 → 16** (current LTS), termasuk **React 18 → 19** yang menjadi syarat Next.js 15+.

Tiga perubahan ini saling bertautan: Next.js 16 menetapkan Node minimum yang lebih tinggi dan React 19, sementara switch ke pnpm mengubah lockfile dan jalur install di Dockerfile. Karena itu dikerjakan sebagai satu overhaul toolchain yang terdokumentasi, bukan beberapa edit terpisah.

**Ini adalah major breaking change.** Lompatan Next.js 14 → 16 melewati dua major version dengan perubahan perilaku runtime (async request API, default caching) dan upgrade React 19. Semua perubahan **wajib diverifikasi dengan menjalankan build dan aplikasi secara nyata**, bukan sekadar memastikan command keluar tanpa error.

### Konteks repo yang relevan

- `mise.toml` dan Dockerfile adalah pasangan yang **tidak boleh drift** (aturan AGENTS.md / CONTRIBUTING.md). Setiap kenaikan versi tool memperbarui keduanya bersamaan.
- Docker tetap **sumber kebenaran untuk build produksi**. mise tidak berjalan di dalam image Docker, jadi versi tool di-deklarasikan di dua tempat (mise untuk lokal, base image / install eksplisit untuk Docker) dengan versi yang sama.
- Frontend memakai Next.js App Router dengan route group `(auth)` / `(protected)`, dynamic route `projects/[id]`, dan catch-all route handler `api/v1/[...path]/route.ts` — titik-titik yang paling mungkin terdampak perubahan async request API Next.js 15+.
- Perubahan toolchain dikerjakan di feature branch lewat PR; dilarang commit langsung ke `main`.

### Keputusan desain yang sudah diambil

- **Docker memakai shape B (Alpine):** base `node:24-alpine`, pnpm dipasang via `npm i -g pnpm@12`. **Tidak memakai corepack** dan **tidak memakai field `packageManager`** di `package.json` — sesuai keinginan user agar seluruh toolchain diatur lewat mise, dengan Docker memakai install eksplisit yang di-pin ke versi sama. (Catatan: corepack secara teknis bisa jalan di Alpine karena ter-bundle dengan Node, tapi sengaja tidak dipakai agar tidak ada version manager paralel yang bersaing dengan mise.)
- **pnpm di-pin ke major 12** di `mise.toml` (`pnpm = "12"`) dan ke `pnpm@12` di Dockerfile.
- **Lockfile** `package-lock.json` diganti `pnpm-lock.yaml`, di-generate via `pnpm import` agar versi dependency yang sudah ter-resolve dipertahankan.

## Requirements

### Requirement 1 — Node 24 via mise

**User Story:** Sebagai contributor, saya ingin Node 24 di-pin via mise, agar environment lokal selaras dengan target LTS terbaru dan dengan image Docker.

#### Acceptance Criteria

1. WHEN contributor menjalankan `mise install` di root repo THEN mise SHALL memasang Node 24.
2. The `mise.toml` SHALL mem-pin `node = "24"` (major), menggantikan `node = "20"`.
3. Komentar di `mise.toml` yang menyebut `node:20-alpine` SHALL diperbarui ke `node:24-alpine`.
4. Semua Dockerfile frontend SHALL memakai base `node:24-alpine` di seluruh stage (deps, builder, runtime).

### Requirement 2 — pnpm 12 sebagai package manager via mise

**User Story:** Sebagai contributor, saya ingin pnpm 12 dikelola mise, agar install dependency konsisten lintas mesin tanpa corepack.

#### Acceptance Criteria

1. The `mise.toml` SHALL menambahkan `pnpm = "12"` di blok `[tools]`.
2. WHEN contributor menjalankan `mise install` THEN pnpm 12 SHALL tersedia di PATH.
3. The repo SHALL memiliki `frontend/pnpm-lock.yaml` dan **tidak lagi** memiliki `frontend/package-lock.json`.
4. The `pnpm-lock.yaml` SHALL di-generate dari dependency yang ada (via `pnpm import`) agar versi ter-resolve dipertahankan sejauh mungkin.
5. The `package.json` SHALL **tidak** memuat field `packageManager` (karena tidak memakai corepack).
6. WHEN contributor menjalankan `pnpm install` di `frontend/` THEN install SHALL berhasil dan menghasilkan `node_modules` yang bisa dipakai build.
7. IF ada script atau dokumentasi yang memanggil `npm ...` untuk frontend THEN perintah tersebut SHALL diubah ke padanan `pnpm ...`.

### Requirement 3 — pnpm di Docker (Alpine, tanpa corepack)

**User Story:** Sebagai maintainer deployment, saya ingin image frontend memasang pnpm 12 secara eksplisit dan ter-pin, agar build produksi reproducible dan selaras dengan versi lokal.

#### Acceptance Criteria

1. The `frontend/Dockerfile` SHALL memasang pnpm via `npm i -g pnpm@12` (atau mekanisme setara yang mem-pin major 12 tanpa corepack).
2. The Dockerfile SHALL **tidak** memakai `corepack enable` / `corepack prepare`.
3. The stage deps SHALL menginstall dependency dari `pnpm-lock.yaml` dengan `pnpm install --frozen-lockfile`.
4. The stage builder SHALL menjalankan build via `pnpm run build` (bukan `npm run build`).
5. The Dockerfile SHALL menghapus cabang auto-deteksi lockfile npm/yarn yang menjadi dead code setelah migrasi (install path pnpm yang eksplisit).
6. WHEN image frontend di-build THEN build SHALL selesai tanpa error dan menghasilkan Next.js standalone output yang bisa dijalankan.
7. The `frontend/.dockerignore` SHALL diperbarui agar komentar/isi selaras dengan install path pnpm.

### Requirement 4 — Upgrade Next.js 14 → 16 dan React 18 → 19

**User Story:** Sebagai pengguna aplikasi, saya ingin aplikasi tetap berfungsi penuh setelah upgrade ke Next.js 16, agar tidak ada regresi fitur.

#### Acceptance Criteria

1. The `frontend/package.json` SHALL mem-pin `next` ke versi 16 stable terbaru, `react` dan `react-dom` ke versi 19 yang kompatibel.
2. WHEN `pnpm run build` dijalankan THEN build SHALL selesai **tanpa error**.
3. WHEN `pnpm run lint` dan type-check dijalankan THEN keduanya SHALL lolos tanpa error.
4. The dynamic route API yang menjadi async di Next.js 15+ (`params`, `searchParams`, `cookies()`, `headers()`) SHALL di-adaptasi ke bentuk async di semua page/handler yang memakainya — khususnya `projects/[id]/**`, `api/v1/[...path]/route.ts`, dan page lain yang membaca params/searchparams.
5. The perubahan default caching Next.js 15+ (fetch, route handler, client router cache tidak lagi di-cache default) SHALL ditinjau; di mana perilaku lama diandalkan, caching eksplisit SHALL dipulihkan agar perilaku runtime tidak berubah tak sengaja.
6. The kode yang terdampak perubahan API React 19 SHALL diperbaiki sehingga aplikasi berjalan tanpa runtime error di console.
7. WHEN aplikasi dijalankan (via Docker Compose full stack) THEN alur inti SHALL berfungsi dan diverifikasi secara nyata: login/auth callback, daftar & detail project, dynamic route `projects/[id]`, activity log, dan proxy `api/v1/[...path]`.
8. IF `next.config.js` memakai opsi yang berubah/di-deprecate di 15/16 THEN konfigurasi SHALL disesuaikan.
9. The konfigurasi PWA / standalone output SHALL tetap berfungsi setelah upgrade (image runtime menjalankan `server.js` dari `.next/standalone`).

### Requirement 5 — Testing & verifikasi menyeluruh (wajib untuk breaking change)

**User Story:** Sebagai reviewer, saya ingin bukti bahwa upgrade telah diuji nyata, agar major breaking change ini aman di-merge.

#### Acceptance Criteria

1. The upgrade SHALL diverifikasi terhadap verification gate di CONTRIBUTING.md: frontend lolos type-check + build; full stack naik via Docker Compose dan `/health` healthy.
2. The verifikasi SHALL mencakup menjalankan aplikasi secara nyata (bukan hanya build sukses) dan menelusuri alur inti di browser/HTTP, mencatat apa yang diperiksa.
3. The setiap breaking change yang ditemukan selama upgrade SHALL didokumentasikan (apa yang berubah, file mana, bagaimana diperbaiki) di deskripsi PR.
4. IF suatu kriteria tidak bisa diverifikasi di environment dev THEN keterbatasan itu SHALL dinyatakan eksplisit, bukan diklaim selesai.

### Requirement 6 — Dokumentasi toolchain selaras

**User Story:** Sebagai contributor baru, saya ingin dokumentasi mencerminkan toolchain aktual, agar tidak ada instruksi yang usang.

#### Acceptance Criteria

1. The `AGENTS.md` SHALL diperbarui: "Node 20" → "Node 24", dan menyebut pnpm sebagai package manager frontend.
2. The `CONTRIBUTING.md` SHALL diperbarui: tabel toolchain (Node 20 → 24, tambah pnpm 12), referensi `node:20-alpine` → `node:24-alpine`, dan catatan verifikasi frontend (`npm` → `pnpm`).
3. The `frontend/README.md` (jika memuat perintah npm) SHALL diubah ke pnpm.
4. The dependency pihak ketiga baru / perubahan versi SHALL di-pin ke versi exact dan ditandai di PR, sesuai ekspektasi keamanan CONTRIBUTING.md.
5. The spec `.kiro/specs/sa-portal-mvp/` yang menyebut "Node 20" SHALL **dibiarkan** (diperlakukan historis sesuai AGENTS.md), tidak diubah oleh pekerjaan ini.

### Requirement 7 — Git workflow

**User Story:** Sebagai maintainer, saya ingin perubahan ini masuk lewat jalur yang benar, agar `main` tetap terlindungi.

#### Acceptance Criteria

1. The pekerjaan SHALL dilakukan di feature branch (mis. `chore/toolchain-node24-pnpm-next16`), bukan commit langsung ke `main`.
2. The commit SHALL mengikuti Conventional Commits dan men-stage file secara spesifik.
3. The perubahan Next.js major upgrade MAY dipecah ke branch/PR terpisah dari perubahan toolchain (Node/pnpm) jika itu memudahkan review — keputusan ini dicatat di design.
