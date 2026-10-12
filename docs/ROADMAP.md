# Portal SA — Roadmap Fitur MVP

Dokumen pelacakan untuk 11 fitur yang dibutuhkan agar mencapai MVP yang layak. Status dinilai berdasarkan kode aktual (bukan klaim spec) pada **2026-10-12**.

> **Asumsi yang dipakai menyusun roadmap ini** (dipilih sebagai default; ubah fase terkait jika ada yang keliru):
> - **Form pertanyaan awal** = hybrid: kuesioner kualifikasi statis yang diisi Sales saat membuat opportunity, dengan opsi pertanyaan klarifikasi yang di-generate AI untuk area BANT yang lemah.
> - **Subtask** = subtask yang benar-benar bisa ditugaskan: Lead SA (atau template proyek) membuat subtask per proyek; SA melihatnya sebagai to-do list dengan status (open → in progress → done) dan mencatat aktivitas terhadap subtask tertentu.
> - **BoQ compare vs Requirement** = analisis gap AI **+ skor coverage**: pilih dokumen Requirement dan dokumen BoQ, Gemini mengembalikan item yang covered / missing / extra beserta persentase coverage.
> - **Guardrails** = hardening auth/keamanan dulu (default yang tidak aman untuk produksi), baru keamanan input/output LLM.
> - **Urutan pengerjaan** = keamanan dulu, lalu menutup fitur yang partial, baru fitur baru.

---

## Legenda Status

| Simbol | Arti |
|--------|------|
| ✅ Selesai | Terimplementasi dan berfungsi |
| 🟡 Partial | Ada tapi belum lengkap, masih stub, atau bug |
| 🔴 Belum ada | Belum diimplementasikan dalam bentuk apa pun |

---

## Ringkasan Status Fitur

| # | Fitur | Status | Gap utama |
|---|-------|--------|-----------|
| 1 | Halaman login | 🟡 Partial | Demo bypass aktif secara default; token OAuth lewat URL; default produksi tidak aman |
| 2 | Request Sales / buat opportunity | ✅ Selesai | `estimasi_nilai` divalidasi tapi tidak dipersist |
| 3 | Form pertanyaan awal | 🔴 Belum ada | Tidak ada konsep kuesioner intake |
| 4 | BANT scoring | ✅ Selesai | AI + manual keduanya berfungsi |
| 5 | Kualifikasi & assignment oleh Lead SA | 🟡 Partial | Folder provisioner masih stub (`pass` + TODO); tidak ada step qualify terpisah |
| 6 | Staff mengikuti subtask / respons subtask via activity log | 🟡 Partial | "Subtask" hanya string enum; tidak ada entity subtask yang bisa di-assign |
| 7 | Input dokumen (Requirement, BoQ, Mandays, PropTek, HLD) | 🟡 Partial | Tipe "Requirement" belum ada (hanya RFP/PropTek/BOQ/Mandays/MoM/HLD) |
| 8 | Due date + integrasi calendar | 🟡 Partial | `target_submit` ada; calendar read-only, tidak ada push due date |
| 9 | Edit due date / ikon pensil edit | 🟡 Partial | Alur edit berfungsi; masih tombol teks, bukan ikon pensil |
| 10 | BoQ compare vs Requirement | 🔴 Belum ada | Tidak ada fitur perbandingan; tipe "Requirement" belum ada |
| 11 | Guardrails | 🔴 Belum ada | Konten user dikirim mentah ke Gemini; default auth tidak aman |

---

## Bug yang Harus Diperbaiki (terlepas dari fitur)

Ditemukan saat asesmen dan sebaiknya diperbaiki lebih awal — ini merusak fungsionalitas yang sudah ada.

- [ ] **B1. Crash `metadata=` pada `NotificationLog`** — `backend/app/services/scoring_engine.py` ~line 623 mengirim `metadata=` ke constructor model, padahal atributnya `notification_metadata` (`metadata` reserved oleh SQLAlchemy). Ini raise saat runtime, merusak notifikasi scoring ke Lead SA dan jalur notifikasi manual-review. _Fix: ganti jadi `notification_metadata=`._
- [ ] **B2. Folder provisioner tidak pernah dipanggil** — `backend/app/api/assignment.py` `_trigger_folder_provisioner` (~line 54) adalah stub `pass` dengan TODO, padahal response melaporkan `folder_provisioning_triggered=True`. Service `FolderProvisioner` sudah diimplementasikan penuh tapi tidak pernah di-wire. (Ditangani di Fase 2 / fitur 5.)
- [ ] **B3. `/health` melaporkan status DB palsu** — `backend/app/main.py` mengembalikan `"database": "healthy"` yang di-hardcode, bukan memanggil `check_database_health()` yang sudah ada. Membatalkan fungsi Docker health check.
- [ ] **B4. `estimasi_nilai` tidak dipersist** — `create_project` memvalidasi dan mengembalikannya tapi tidak ada kolom di model `Project`, jadi nilai opportunity hilang. (Ditangani di Fase 1 / fitur 2.)
- [ ] **B5. `create_all` saat startup melewati Alembic** — `main.py` membuat tabel otomatis, bersaing dengan migrasi Alembic. Pilih satu mekanisme untuk menghindari schema drift.

---

## Fase 0 — Hardening Keamanan & Correctness (bagian dari Guardrails, fitur 11)

**Tujuan:** membuat app aman untuk di-deploy secara nyata dan memperbaiki bug yang merusak fungsionalitas. Ini adalah interpretasi "guardrails auth" dan menjadi prasyarat untuk MVP produksi mana pun.

- [ ] 0.1 Default `DEMO_MODE` menjadi `False`; cegah `/auth/demo-login` agar tidak mungkin aktif di build produksi. (`backend/app/core/config.py`, `backend/app/api/auth.py`)
- [ ] 0.2 Hapus default `JWT_SECRET_KEY` yang tidak aman; fail fast saat startup jika belum di-set. Selaraskan penamaan `SECRET_KEY` (README) vs `JWT_SECRET_KEY` (kode). (`config.py`, `README.md`)
- [ ] 0.3 Berhenti mengirim JWT access/refresh token sebagai query param URL di redirect OAuth callback; pindah ke URL hash (seperti flow calendar yang sudah ada) atau httpOnly cookie. (`frontend/src/app/api/v1/[...path]/route.ts`)
- [ ] 0.4 Kunci default CORS dari `*` menjadi allow-list yang digerakkan env. (`config.py`, `main.py`)
- [ ] 0.5 Fix bug **B1** (notifikasi `metadata=`), **B3** (health check DB sungguhan), **B5** (putuskan Alembic vs `create_all`).

**Kriteria selesai:** app menolak start dengan default tidak aman; token tidak pernah muncul di URL/log; jalur notifikasi scoring berfungsi; health check mencerminkan status DB sebenarnya.

---

## Fase 1 — Menutup Partial yang Mudah (quick wins)

**Tujuan:** menyelesaikan fitur yang sudah 80% jadi dengan perubahan kecil dan berisiko rendah.

- [ ] 1.1 **Fitur 2:** persist `estimasi_nilai` — tambah column + migration ke `Project`, simpan saat create, tampilkan di detail/edit. (fix **B4**)
- [ ] 1.2 **Fitur 7:** tambahkan `Requirement` ke `DocTypeEnum` dan constraint `CHECK` di DB; perbarui dropdown tipe dokumen di frontend. (`backend/app/schemas/document.py`, `backend/app/models/document.py`, migration, `frontend/src/components/DocumentForm.tsx`)
- [ ] 1.3 **Fitur 9:** ganti tombol teks "Edit" dengan ikon pensil/edit di halaman detail proyek, mempertahankan alur edit yang ada. (`frontend/src/app/(protected)/projects/[id]/page.tsx`)

**Kriteria selesai:** nilai opportunity tersimpan dan tampil; Requirement bisa dipilih sebagai tipe dokumen; entry point edit proyek berupa ikon pensil.

---

## Fase 2 — Folder Provisioning & Assignment (fitur 5)

**Tujuan:** men-wire provisioner yang sudah dibangun dan memperjelas alur Lead SA.

- [ ] 2.1 Ganti stub `_trigger_folder_provisioner` dengan pemanggilan nyata ke `FolderProvisioner.provision_project_folder`, termasuk handling retry/`Provisioning Failed` yang sudah didukung service. (fix **B2**)
- [ ] 2.2 Hanya laporkan `folder_provisioning_triggered=True` saat provisioning benar-benar di-schedule; ekspos status provisioning di proyek agar badge "Folder Pending" berfungsi.
- [ ] 2.3 **Perlu keputusan:** konfirmasi apakah Lead SA butuh step "qualify" terpisah sebelum assignment, atau BANT ≥ 60 sebagai gate kualifikasi (perilaku saat ini). Asumsi default: BANT adalah gate-nya, tanpa step terpisah. Jika step qualify manual diinginkan, tambah status + endpoint.
- [ ] 2.4 Verifikasi end-to-end: assign → folder Drive dibuat dengan permission yang benar (Editor SA/Lead, Viewer Sales di Inventory) → `gdrive_folder_id` tersimpan.

**Kriteria selesai:** meng-assign SA benar-benar membuat tree folder Drive dengan permission yang benar, dengan state pending/failed yang terlihat.

---

## Fase 3 — Integrasi Due Date dengan Calendar (fitur 8)

**Tujuan:** menghubungkan `target_submit` dengan Google Calendar (saat ini calendar read-only, hanya untuk pull event ke logging).

- [ ] 3.1 **Perlu keputusan:** push satu arah (buat/update event Calendar saat `target_submit` di-set/edit) vs sync dua arah. Asumsi default: push satu arah due date proyek ke calendar SA yang di-assign.
- [ ] 3.2 Perluas `CalendarService` dengan create/update event memakai OAuth token user; simpan event id hasilnya di proyek.
- [ ] 3.3 Saat due date di-edit (fitur 9), update event Calendar yang tertaut; saat proyek close/lost, hapus atau tandai.
- [ ] 3.4 Handle kasus tanpa token calendar dengan baik (fitur tetap jalan tanpa Calendar terhubung).

**Kriteria selesai:** meng-set atau meng-edit due date proyek tercermin di Google Calendar yang terhubung; ketiadaan token degrade dengan baik.

---

## Fase 4 — Subtask yang Bisa Di-assign (fitur 6)

**Tujuan:** mengubah "subtask" dari kategori activity-log bebas pilih menjadi work item yang nyata dan bisa di-track. **Ini perubahan model** — effort lebih besar.

- [ ] 4.1 Tambah entity `Subtask`: `id`, `id_project`, `title`/`category`, `assigned_sa`, `status` (open → in_progress → done), timestamp. Migration + model + schema.
- [ ] 4.2 Endpoint: buat subtask (Lead SA / template), list per proyek, update status, assign/reassign ke SA.
- [ ] 4.3 Tautkan `ActivityLog` ke subtask (FK `id_subtask` opsional) agar mencatat aktivitas bisa memajukan/menutup subtask ("respons subtask").
- [ ] 4.4 **Perlu keputusan:** apakah meng-assign proyek otomatis men-seed checklist subtask default (mis. Requirement → BoQ → PropTek → HLD)? Asumsi default: ya, seed dari template.
- [ ] 4.5 Frontend: tampilan to-do list subtask yang di-assign ke SA; UX mencatat aktivitas terhadap subtask; manajemen subtask untuk Lead SA.

**Kriteria selesai:** SA melihat to-do list subtask, mencatat aktivitas terhadap salah satunya, dan subtask berubah status.

---

## Fase 5 — Form Pertanyaan Awal (fitur 3)

**Tujuan:** intake kualifikasi terstruktur saat pembuatan opportunity.

- [ ] 5.1 **Perlu keputusan:** set pertanyaan tetap vs template yang bisa dikonfigurasi admin. Asumsi default: hybrid — kuesioner inti tetap dulu, bisa dikonfigurasi admin nanti.
- [ ] 5.2 Definisikan schema pertanyaan; simpan jawaban sebagai structured data di proyek (JSONB) atau tabel khusus.
- [ ] 5.3 Frontend: render kuesioner sebagai step dalam flow "opportunity baru" Sales (`projects/new`).
- [ ] 5.4 (Opsional AI) kirim jawaban + dokumen upload ke Gemini untuk men-generate pertanyaan klarifikasi area BANT yang lemah, ditampilkan ke Sales (terhubung dengan status "Need Clarification" yang sudah ada).

**Kriteria selesai:** Sales menjawab kuesioner terstruktur saat membuat opportunity; jawaban tersimpan dan terlihat di proyek.

---

## Fase 6 — BoQ Compare vs Requirement (fitur 10)

**Tujuan:** analisis gap bertenaga AI antara dokumen Requirement dan dokumen BoQ. **Fitur baru dengan kompleksitas tertinggi** — bergantung pada Fase 1.2 (tipe dokumen Requirement) dan guardrails dari Fase 7.

- [ ] 6.1 Service: diberi dokumen Requirement dan dokumen BoQ sebuah proyek (link Drive atau upload), kirim keduanya ke Gemini via path multimodal `parse_document` / `structure_text` yang sudah ada.
- [ ] 6.2 Definisikan schema output terstruktur: `covered[]`, `missing[]`, `extra[]`, dan `coverage_percentage`.
- [ ] 6.3 Endpoint `GET/POST /projects/{id}/boq-compare`; persist hasil comparison terbaru untuk proyek.
- [ ] 6.4 Frontend: tampilan comparison yang menunjukkan item covered/missing/extra dan skor coverage, dengan tombol run ulang.
- [ ] 6.5 Handle edge case: Requirement atau BoQ tidak ada, LLM gagal (pakai ulang pola retry scoring engine).

**Kriteria selesai:** memilih Requirement + BoQ untuk sebuah proyek mengembalikan analisis gap terstruktur dengan skor coverage, dirender di UI.

---

## Fase 7 — Guardrails LLM (fitur 11, sisanya)

**Tujuan:** lapisan keamanan di sekitar semua pemanggilan Gemini. (Hardening auth sudah dikerjakan di Fase 0.) Sebaiknya mendarat sebelum/bersama Fase 6 karena fitur itu mengirim dokumen utuh ke LLM.

- [ ] 7.1 Input safety: batas ukuran/konten dan mitigasi prompt-injection sebelum pemanggilan di `gemini_adapter.py` / `scoring_engine.py` / `activity_logger.py`.
- [ ] 7.2 Output validation: paksa schema JSON yang diharapkan pada response terstruktur; tolak/retry pada output malformed atau di luar kontrak.
- [ ] 7.3 **Perlu keputusan:** cakupan handling PII — flag vs redact data personal di dokumen upload dan notes. Asumsi default: flag-and-log untuk MVP, redaction nanti.
- [ ] 7.4 Sentralisasi guardrails dalam satu module agar setiap entry point LLM melewatinya (package `utils/` saat ini kosong — tempat yang pas untuk ini).

**Kriteria selesai:** tidak ada konten user yang sampai ke Gemini tanpa melewati guardrail input; semua output terstruktur tervalidasi schema.

---

## Usulan Urutan Pengerjaan (urutan dependensi)

```
Fase 0 (keamanan + bug fix)      ← kerjakan dulu; membuka deployment yang aman
      │
Fase 1 (partial mudah)           ← quick win, termasuk tipe dokumen Requirement
      │
Fase 2 (folder provisioning)     ← men-wire kode yang sudah ada
      │
Fase 3 (due date calendar)   ──┐
Fase 4 (subtask assignable)  ──┤  ← independen, bisa diparalelkan
Fase 5 (form pertanyaan awal)──┘
      │
Fase 7 (guardrails LLM)          ← sebelum Fase 6 (penggunaan LLM yang berat dokumen)
      │
Fase 6 (BoQ vs Requirement)      ← terakhir; bergantung pada tipe Requirement + guardrails
```

---

## Rekomendasi Lintas-Fitur (tidak memblokir MVP, tapi layak dilacak)

- [ ] Tambah CI (lint + test backend) — belum ada hari ini.
- [ ] Tambah test frontend — belum ada hari ini.
- [ ] Perluas coverage test backend ke auth, state machine dokumen, handover, notifikasi (saat ini condong ke AI/provisioning/SLA/scoring).
- [ ] Implementasikan stub email Gmail (`notification_service.send_email`) atau hapus klaim "email" dari README sampai benar-benar nyata.
- [ ] Selaraskan gap README-vs-realita (email Gmail, httpOnly cookie, penamaan `SECRET_KEY`, status DB `/health`).
- [ ] Pecah router besar (`projects.py` ~702 line, `assignment.py` ~681 line).
- [ ] Ekstrak helper generator ID yang terduplikasi ke package `utils/` yang kosong.

---

## Keputusan yang Dibutuhkan dari Product Owner

Asumsi default berikut menggerakkan roadmap; konfirmasi atau koreksi:

1. **Form pertanyaan awal (Fase 5):** set tetap vs bisa dikonfigurasi admin? _(diasumsikan: hybrid, tetap dulu)_
2. **Subtask (Fase 4):** subtask yang benar-benar bisa ditugaskan vs tetap model kategori? _(diasumsikan: subtask nyata)_
3. **Seeding subtask (4.4):** auto-seed checklist default saat assignment? _(diasumsikan: ya)_
4. **BoQ compare (Fase 6):** analisis gap AI dengan skor coverage vs side-by-side biasa? _(diasumsikan: AI + skor)_
5. **Step qualify (2.3):** step qualify Lead SA terpisah vs BANT sebagai gate? _(diasumsikan: BANT sebagai gate)_
6. **Calendar (3.1):** push due date satu arah vs sync dua arah? _(diasumsikan: push satu arah)_
7. **PII (7.3):** flag vs redact? _(diasumsikan: flag untuk MVP)_
