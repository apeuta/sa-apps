# Simpan id folder Solutions secara eksplisit, terpisah dari id folder master

Operasi auto-lock/unlock SLA dan handover semuanya bekerja pada subfolder **Solutions**, tetapi `provision_project_folder()` sebelumnya hanya mengembalikan id folder **master** dan `Project` hanya punya satu kolom `gdrive_folder_id`. Akibatnya setiap consumer (`sla_timer.py`, `documents.py`, `handover_service.py`) memanggil `lock_solutions_folder(solutions_folder_id=project.gdrive_folder_id, ...)` dengan id master — folder yang salah — sehingga seluruh Flow 2 auto-lock dan handover secara laten rusak begitu provisioner nyata menyala.

**Keputusan (sesi grill, 2026-10-26):** `provision_project_folder()` mengembalikan semua id folder yang dibuat (master, inventory, diagram, solutions). `Project` mendapat kolom baru `gdrive_solutions_folder_id` (migration) di samping `gdrive_folder_id` (master). Ketiga consumer dipindahkan untuk membaca `gdrive_solutions_folder_id` untuk operasi Solutions, dan ini dikerjakan dalam PR yang sama dengan wiring provisioner agar tidak ada window di mana id tersimpan tapi consumer masih menyasar master.

## Considered Options

- **Lookup Solutions by-name on-demand** (query Drive `files().list` parent=master, name="Solutions" tiap lock/unlock): tanpa migration, tapi menambah call Drive di jalur panas dan rapuh bila folder di-rename. Ditolak.
- **Simpan struktur JSON `{master, inventory, diagram, solutions}` di satu kolom JSONB**: menyembunyikan struktur dari query/constraint SQL. Ditolak demi kolom eksplisit.

## Consequences

Kolom `gdrive_folder_id` tetap menyimpan id master (dipakai sebagai proxy "sudah ter-provision?"); operasi Solutions tidak boleh lagi memakainya. Test Fase 2A (`test_flow2_e2e.py`) yang meng-assert kontrak lama dikoreksi di PR yang sama.
