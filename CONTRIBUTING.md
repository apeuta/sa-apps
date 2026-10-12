# Berkontribusi ke Portal SA

Panduan ini menjelaskan cara kita bekerja di repository ini: branching, commit, pull request, dan verifikasi yang diharapkan sebelum apa pun di-merge. Baca ini sebelum membuka PR.

Untuk *apa* yang sedang kita bangun dan dalam urutan apa, lihat [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Model Branching

- `main` adalah branch integrasi. `main` harus selalu bisa di-build dan deployable.
- **Dilarang commit langsung ke `main` — tanpa pengecualian.** Setiap perubahan, termasuk perubahan dokumentasi dan one-liner, masuk melalui feature branch dan pull request. Ini berlaku untuk semua contributor, baik manusia maupun agen AI.
- Buat feature branch dari `main` terbaru untuk setiap unit pekerjaan:

  ```
  feat/<slug-singkat>        # fitur baru
  fix/<slug-singkat>         # perbaikan bug
  refactor/<slug-singkat>    # perubahan internal, tanpa perubahan perilaku
  docs/<slug-singkat>        # dokumentasi saja
  ```

- Jaga satu branch tetap pada satu unit pekerjaan yang bisa di-review. Rebase atau merge `main` terbaru ke branch Anda sebelum membuka PR untuk meminimalkan conflict.

---

## Konvensi Commit

Kita memakai [Conventional Commits](https://www.conventionalcommits.org/). Setiap pesan commit diawali dengan tipe:

- `feat:` — fitur baru
- `fix:` — perbaikan bug
- `refactor:` — perubahan kode yang bukan perbaikan bug maupun penambahan fitur
- `docs:` — dokumentasi saja
- `chore:` — tooling, dependency, konfigurasi build

Tulis pesan dalam bentuk imperatif ("tambah", "perbaiki", "perbarui" — bukan "menambahkan"/"memperbaiki"). Jaga baris subjek tetap ringkas; gunakan body untuk menjelaskan alasan ketika tidak jelas.

Stage file secara spesifik daripada semuanya sekaligus, agar perubahan yang tidak terkait tidak ikut dalam satu commit. Jangan pernah commit secret — API key, credential OAuth, atau apa pun yang semestinya ada di `.env` (lihat `.env.example` untuk apa yang diharapkan dikonfigurasi per environment).

---

## Proses Pull Request

1. Push feature branch Anda dan buka PR yang menargetkan `main`.
2. Jaga judul PR tetap ringkas (gaya conventional-commit) dan gunakan deskripsi untuk meringkas:
   - apa yang berubah dan mengapa,
   - apa yang telah diverifikasi (build, test, pengecekan manual),
   - apa pun yang sengaja ditinggalkan atau terblokir.
3. Sebuah PR harus lolos verification gate (di bawah) sebelum ditandai siap di-review.
4. Minimal satu review sebelum merge. Tanggapi feedback review dengan commit baru (hindari force-push menimpa review yang sedang berjalan); squash saat merge jika history-nya noisy.
5. Hapus branch setelah merge.

---

## Verification Gate

Belum ada CI otomatis (**CI direncanakan** — lihat daftar lintas-fitur di [`docs/ROADMAP.md`](docs/ROADMAP.md)). Sampai itu ada, verifikasi dilakukan manual dan menjadi tanggung jawab author sebelum meminta review:

- **Backend** — test suite lolos dan app bisa di-import/start dengan bersih. Setup test dan dependency ada di `backend/pyproject.toml`; test ada di `backend/tests/`.
- **Frontend** — proyek lolos type-check dan build tanpa error. Script ada di `frontend/package.json`.
- **Full stack** — jika perubahan memengaruhi runtime wiring (migration, env var, service startup), konfirmasi stack bisa naik via Docker Compose dan endpoint `/health` melaporkan healthy.
- **Pengecekan sesuai scope** — verifikasi perubahan terhadap perilaku yang dimaksud, bukan sekadar command keluar tanpa error. Untuk perubahan UI, cek perilakunya di browser; untuk perubahan logika, jalankan code path terkait atau test-nya.

Sebuah perubahan belum "selesai" hanya karena command berjalan tanpa error. Perubahan selesai ketika terbukti memenuhi tujuannya.

---

## Migrasi Database

Perubahan schema melewati migration Alembic di `backend/alembic/versions/`. Ketika Anda mengubah model SQLAlchemy, tambahkan migration yang bersesuaian dalam PR yang sama agar schema dan model tetap sejalan. Jangan mengandalkan auto-create table saat startup sebagai mekanisme migration.

---

## Ekspektasi Keamanan

- Simpan semua secret di environment variable; jangan pernah hardcode. `.env` di-ignore git — perbarui `.env.example` (hanya key, tanpa nilai asli) ketika Anda menambah variable baru.
- Perlakukan apa pun yang menangani auth, token, CORS, atau credential eksternal sebagai security-sensitive: catat di deskripsi PR apa yang Anda verifikasi.
- Tandai setiap dependency pihak ketiga baru di PR, di-pin ke versi yang exact.

---

<!-- BEGIN: current-overhaul-workflow (sementara — hapus ketika overhaul MVP selesai) -->
## Workflow Overhaul Saat Ini (sementara)

_Ditambahkan 2026-10-12. Bagian ini mendokumentasikan proses untuk overhaul MVP yang sedang berjalan, dilacak di [`docs/ROADMAP.md`](docs/ROADMAP.md). Hapus bagian ini begitu overhaul mendarat._

Overhaul dikerjakan **satu fase roadmap per branch**:

- Nama branch: `feat/phase-<N>-<slug>` (mis. `feat/phase-0-security-hardening`), di-branch dari `main` terbaru.
- Scope: satu fase per branch — bisa di-review dan di-revert sebagai satu unit. Fase berikutnya di-branch hanya setelah fase sebelumnya di-merge ke `main`.
- Setiap fase diverifikasi terhadap **kriteria selesai**-nya di `docs/ROADMAP.md` sebelum PR dibuka.
- Checkbox roadmap (`- [ ]` → `- [x]`) di-update di branch yang sama dengan pekerjaan yang di-track-nya, agar roadmap tetap menjadi progress tracker yang hidup.
- Pacing: satu fase per waktu. Sebuah fase diselesaikan dan di-review sebelum fase berikutnya dimulai. Fase yang independen (sesuai diagram dependency di roadmap) hanya di-parallelize atas kesepakatan eksplisit.

Fase yang membuat perubahan besar atau runtime-sensitive (mis. perubahan default keamanan, model subtask, document comparison) dikembangkan secara terisolasi agar `main` tetap bisa dipakai sepanjang waktu.
<!-- END: current-overhaul-workflow -->
