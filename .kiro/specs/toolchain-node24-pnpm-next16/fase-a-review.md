# Upgrade toolchain frontend ke Node 24 + pnpm 12 (Fase A)

Fase A overhaul toolchain menaikkan runtime frontend dari Node 20 ke Node 24 dan memindah package manager dari npm ke pnpm 12, keduanya di-pin via mise. Lockfile `package-lock.json` diganti `pnpm-lock.yaml` lewat `pnpm import` sehingga versi dependency yang sudah ter-resolve dipertahankan, dan `frontend/Dockerfile` dialihkan ke shape B (Alpine) dengan install pnpm eksplisit tanpa corepack. Next.js tetap di 14.2.3 — upgrade framework sengaja ditunda ke Fase B. Dokumentasi (AGENTS.md, CONTRIBUTING.md) dan checkbox tasks 1-6 disinkronkan di commit yang sama.

Watch for: `pnpm run lint` tidak lolos karena ESLint belum terkonfigurasi di repo (pre-existing, di luar scope — confirmed), dan `docker compose build frontend` tidak dapat dijalankan di environment coder karena Docker daemon mati sekaligus service frontend memakai image GHCR pre-built tanpa blok build (confirmed via commit message). Keduanya adalah keterbatasan verifikasi yang dicatat eksplisit, bukan kegagalan diam-diam.

**Verdict**: APPROVED

## High-level view

Perubahan mekanis dan terbatas persis pada scope Fase A. Tiga sumbu toolchain — `mise.toml` (node 24 + pnpm 12 dengan komentar header diselaraskan), lockfile frontend, dan `frontend/Dockerfile` — berubah bersama sehingga mise dan Docker tidak drift, sesuai aturan pasangan yang ditegaskan requirements.

Migrasi lockfile dieksekusi dengan benar: `pnpm-lock.yaml` (lockfileVersion 9.0) menyimpan next@14.2.3 dan react@18.3.1 identik dengan lockfile npm lama, `package-lock.json` dihapus, dan `package.json` tetap tanpa field `packageManager` — konsisten dengan keputusan menolak corepack.

Dockerfile shape B bersih: blok auto-deteksi lockfile multi-manager yang menjadi dead code dibuang, diganti jalur pnpm tunggal yang eksplisit (`npm i -g pnpm@12` + `COPY package.json pnpm-lock.yaml` + `pnpm install --frozen-lockfile`), build via `pnpm run build`. Stage runtime tidak memasang pnpm dan tetap menjalankan `node server.js` dari standalone output dengan user non-root — tidak ada regresi postur keamanan container.

Scope negatif terjaga penuh: tidak ada bump versi Next.js/React, tidak ada source aplikasi frontend yang disentuh, dan `.kiro/specs/sa-portal-mvp/` tidak diubah. Dua gap verifikasi (lint & docker build) didokumentasikan sebagai keterbatasan environment dengan sebab yang jelas; keduanya pre-existing atau infrastruktur, bukan akibat migrasi ini, sehingga tidak blocking untuk Fase A.

<details>
<summary>Issues (2)</summary>

1. **Lint gate belum hijau (non-blocking)** — `pnpm run lint` gagal karena ESLint belum terpasang/terkonfigurasi di repo (pre-existing). Tasks.md task 5 mencentang "pnpm run lint lolos" padahal tidak dijalankan; pertimbangkan menyesuaikan klaim task atau menambahkan ESLint sebagai pekerjaan terpisah di luar Fase A.
2. **Docker build belum terverifikasi (non-blocking)** — `docker compose build frontend` tidak dijalankan (daemon mati + service pakai image pre-built tanpa build block). Dockerfile sudah dibaca dan benar secara statis, tapi build end-to-end image belum dibuktikan; verifikasi saat daemon tersedia sebelum rilis.

</details>

<details>
<summary>Details</summary>

### Pasangan mise + Dockerfile naik bersama

`mise.toml` menaikkan `node = "20"` → `node = "24"` dan menambah `pnpm = "12"` di `[tools]`, dengan komentar header `node:20-alpine` → `node:24-alpine` ikut diperbarui. Blok `uv`, `[hooks]`, dan `[tasks]` tidak tersentuh. Aturan "mise.toml dan Dockerfile tidak boleh drift" terjaga: ketiga referensi `node:24-alpine` di Dockerfile selaras dengan pin mise, dan `pnpm@12` di Dockerfile selaras dengan `pnpm = "12"`.

### Migrasi lockfile mempertahankan versi ter-resolve

`pnpm-lock.yaml` (lockfileVersion 9.0) menyimpan next@14.2.3 serta react/react-dom@18.3.1 persis seperti isi `package-lock.json` lama — bukti bahwa `pnpm import` dipakai sebagaimana dirancang, bukan resolusi ulang yang bisa menggeser versi. `package-lock.json` dihapus (1722 baris) sehingga tidak ada dua sumber kebenaran lockfile. `package.json` tetap tanpa field `packageManager`, konsisten dengan keputusan tidak memakai corepack. Dependency `next`/`react` di `package.json` tidak berubah, menegaskan upgrade framework ditahan untuk Fase B.

### Dockerfile shape B: dead code dibuang, jalur pnpm eksplisit

Blok lama mengandung cabang auto-deteksi `yarn.lock`/`package-lock.json`/`pnpm-lock.yaml` dengan `corepack enable pnpm` di cabang pnpm. Setelah migrasi ke satu package manager, cabang-cabang itu dead code, dan `corepack` bertentangan dengan keputusan desain. Diff menggantinya dengan jalur tunggal:

```dockerfile
RUN npm i -g pnpm@12
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
```

`npm i -g pnpm@12` memakai npm bawaan base image hanya sebagai bootstrap sekali pakai untuk membawa pnpm ter-pin — tidak ada corepack di mana pun (grep hanya menemukan dua baris komentar yang menegaskan ketidakhadirannya). Stage builder juga memasang pnpm@12 (karena stage terpisah tidak mewarisi global dari deps) dan menjalankan `pnpm run build` menggantikan `npm run build`. `--frozen-lockfile` memastikan build gagal bila lockfile dan `package.json` tidak sinkron, properti reproducibility yang diinginkan untuk build produksi.

### Runtime stage: tidak ada regresi keamanan container

Stage runtime tetap `node:24-alpine`, tidak memasang pnpm (tidak dibutuhkan untuk menjalankan standalone output), dan menjalankan `CMD ["node", "server.js"]`. User non-root `nextjs:nodejs` (uid/gid 1001), `COPY --chown`, `EXPOSE 3000`, dan ENV runtime tidak berubah. Trust boundary container identik dengan sebelum migrasi — tidak ada permukaan baru yang terbuka oleh perpindahan package manager.

### Scope negatif terjaga

Daftar file yang berubah terbatas pada: `mise.toml`, `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/pnpm-lock.yaml` (baru), `frontend/package-lock.json` (dihapus), `AGENTS.md`, `CONTRIBUTING.md`, dan spec Fase A sendiri. Tidak ada file di bawah `frontend/src/`, `frontend/app/`, atau komponen aplikasi yang disentuh. `.kiro/specs/sa-portal-mvp/` tidak muncul di diff, sesuai perlakuan historis. `.dockerignore` hanya menyesuaikan dua komentar (`npm ci` → `pnpm install --frozen-lockfile`, `npm run build` → `pnpm run build`); isi ignore tidak berubah.

### Dokumentasi: Bahasa Indonesia, istilah teknis Inggris

Prosa Indonesia dengan istilah teknis (package manager, lockfile, corepack, build) tetap Inggris, sesuai konvensi repo. `CONTRIBUTING.md` menyelaraskan catatan verifikasi frontend ke `pnpm install` + `pnpm run lint` + `pnpm run build` — perhatikan bahwa catatan ini kini menyebut `pnpm run lint` padahal lint belum bisa dijalankan (lihat bagian verifikasi). `frontend/README.md` tidak ada di repo, jadi klausa "jika ada" pada task 6 benar dipenuhi dengan tanpa-perubahan.

### Verifikasi: bukti tercatat, dua gap didokumentasikan

Commit message mencatat bukti konkret: `mise install` memasang node v24.21.0 + pnpm 12.14.0; `pnpm import` + hapus lockfile lama + `pnpm install` sukses; `pnpm run build` Next 14 hijau dengan type-check bersih dan 16 route ter-generate. Dua keterbatasan dinyatakan eksplisit alih-alih diklaim selesai — sesuai Requirement 5.4. `pnpm run lint` gagal karena ESLint belum terpasang (kondisi pre-existing, bukan akibat migrasi; `next lint` memunculkan prompt setup interaktif). `docker compose build frontend` tidak dapat dijalankan karena daemon mati dan service memakai image GHCR pre-built. Keduanya non-blocking untuk Fase A: yang pertama di luar scope toolchain, yang kedua keterbatasan infrastruktur environment. Catatan kecil: task 5 di tasks.md tercentang dengan teks "pnpm run lint lolos" padahal lint tidak dijalankan — ketidakcocokan klaim yang layak dirapikan, tapi tidak menghalangi tujuan Fase A.

</details>

<details>
<summary>File map</summary>

- `mise.toml` — node 20→24, tambah pnpm 12, komentar header node:24-alpine.
- `frontend/Dockerfile` — ketiga stage node:24-alpine; pnpm@12 eksplisit di deps+builder; jalur pnpm menggantikan auto-deteksi+corepack; `pnpm run build`; runtime tetap `node server.js`.
- `frontend/.dockerignore` — dua komentar diselaraskan ke perintah pnpm.
- `frontend/pnpm-lock.yaml` — baru, hasil `pnpm import` (next@14.2.3, react@18.3.1 dipertahankan).
- `frontend/package-lock.json` — dihapus.
- `AGENTS.md` — baris toolchain Node 24 + pnpm 12.
- `CONTRIBUTING.md` — tabel toolchain, referensi alpine, paragraf pnpm, catatan verifikasi frontend.
- `.kiro/specs/toolchain-node24-pnpm-next16/tasks.md` — centang tasks 1-6.

Diff lengkap: `git diff main..HEAD` di branch `chore/toolchain-node24-pnpm`.

</details>
