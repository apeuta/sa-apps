# WORKFLOW — Alur Domain Backend Portal SA

Dokumen ini menjelaskan alur bisnis end-to-end backend Portal SA: dari pembuatan opportunity oleh requester, BANT scoring, assignment oleh Lead SA, folder provisioning, lifecycle dokumen, SLA tracking DQ Number, hingga handover ke PMO/Delivery. Diagram dibuat dari kode aktual di `backend/app/api/` dan `backend/app/services/`.

## 1. State Machine Status Proyek

Transisi status proyek ditegakkan di dua tempat: endpoint `PATCH /projects/{id}/status` (`workflow.py`, transisi manual oleh user) dan `scoring_engine.apply_threshold` (transisi otomatis hasil scoring).

```mermaid
stateDiagram-v2
    [*] --> New : create_project (requester)

    New --> Scoring_Pending : trigger scoring async
    New --> Pending_Assignment : forward (manual)

    Scoring_Pending --> Pending_Assignment : BANT >= 60 (apply_threshold)
    Scoring_Pending --> Need_Clarification : BANT < 60 (apply_threshold)
    Scoring_Pending --> Manual_Review_Required : semua file gagal diekstrak

    Need_Clarification --> Pending_Assignment : score ulang >= 60
    Manual_Review_Required --> Pending_Assignment : score manual >= 60
    New --> Need_Clarification : score manual < 60

    Pending_Assignment --> Assigned : assign_sa_to_project (Lead_SA)
    Assigned --> Ready : input DQ Number pertama (Sales/Lead_SA)
    Ready --> Closed_Win : forward (manual)
    Closed_Win --> Handover_Complete : trigger_handover

    New --> Lost : Lead_SA/Admin
    Pending_Assignment --> Lost : Lead_SA/Admin
    Assigned --> Lost : Lead_SA/Admin
    Ready --> Lost : Lead_SA/Admin
    Closed_Win --> Lost : Lead_SA/Admin
    Need_Clarification --> Lost : Lead_SA/Admin
    Scoring_Pending --> Lost : Lead_SA/Admin
    Manual_Review_Required --> Lost : Lead_SA/Admin

    Handover_Complete --> [*]
    Lost --> [*]
```

### Catatan state machine proyek

- **Jalur forward manual** (`workflow.py`, `VALID_FORWARD_TRANSITIONS`) bersifat **linear ketat**: `New → Pending Assignment → Assigned → Ready → Closed-Win → Handover Complete`. Endpoint ini hanya mengizinkan satu langkah maju per transisi.
- **Jalur otomatis** dari scoring engine: `apply_threshold` menetapkan `Pending Assignment` (skor ≥ 60, memicu notifikasi Lead_SA) atau `Need Clarification` (skor < 60). Jika semua file gagal diekstrak LLM setelah retry, status menjadi `Manual Review Required`.
- **Perbedaan jalur**: transisi `Assigned → Ready` **tidak** terjadi via `workflow.py` dalam praktik — ia dipicu di `dq_number.py` saat DQ Number pertama diinput (dan status saat ini `Assigned`). Transisi `Pending Assignment → Assigned` dipicu di `assignment.py`, bukan oleh endpoint workflow.
- **`Lost`** hanya bisa diset oleh `Lead_SA`/`Admin`, dari status mana pun kecuali `Handover Complete` dan `Lost` sendiri.
- **Status `Scoring Pending`** terdaftar di `CheckConstraint` tetapi tidak pernah di-set secara eksplisit oleh kode scoring (scoring langsung menuju `Pending Assignment`/`Need Clarification`/`Manual Review Required`). Diagram menampilkannya sebagai fase konseptual "sedang di-score".
- Tidak ada step "qualify" terpisah — gate kualifikasi secara de-facto adalah ambang BANT ≥ 60 (lihat roadmap keputusan 2.3).

## 2. State Machine Status Dokumen

Ditegakkan di `PATCH /documents/{id}/status` (`documents.py`).

```mermaid
stateDiagram-v2
    [*] --> Draft : create_document
    Draft --> Reviewed : maju (SA / Lead_SA)
    Reviewed --> Final : maju (SA / Lead_SA)
    Final --> Reviewed : mundur (HANYA Lead_SA)
    Reviewed --> Draft : mundur (HANYA Lead_SA)
    Final --> [*]
```

### Catatan state machine dokumen

- **Maju** (`Draft → Reviewed → Final`): boleh oleh `SA` dan `Lead_SA`.
- **Mundur** (`Final → Reviewed`, `Reviewed → Draft`): hanya `Lead_SA`.
- **Loncat** (`Draft → Final`): ditolak untuk semua role.
- Dokumen berstatus `Final` hanya bisa diubah oleh `Lead_SA` (proteksi tambahan).
- Dokumen `HLD` berstatus `Final` adalah salah satu prasyarat handover.

## 3. Alur End-to-End (Lintas Service)

```mermaid
flowchart TD
    A["Requester membuat opportunity<br/>POST /projects (status=New)"] --> B{Ada file PDF/DOCX valid?}
    B -- Ya --> C["Background task:<br/>scoring_engine.score_documents"]
    B -- Tidak --> M["Arahkan ke BANT manual<br/>POST /projects/id/score-manual"]

    C --> D["LLM parse_document per file<br/>retry 3x, guardrail size"]
    D --> E["Agregasi sub-skor BANT<br/>(ambil skor tertinggi per kriteria)"]
    M --> E
    E --> F{"apply_threshold<br/>total >= 60?"}

    F -- "Ya" --> G["status=Pending Assignment<br/>notifikasi ke Lead_SA (B1)"]
    F -- "Tidak" --> H["status=Need Clarification<br/>feedback ke requester"]
    D -- "Semua file gagal" --> I["status=Manual Review Required<br/>notifikasi Lead_SA (B1)"]

    G --> J["Lead_SA: assign SA<br/>POST /projects/id/assign"]
    J --> K["status=Assigned, assigned_at di-set<br/>notifikasi ke SA (B1)"]
    K --> L["Background: _trigger_folder_provisioner<br/>(STUB — tidak memanggil service, B2)"]
    K --> N["(seharusnya) SLA timer start<br/>saat Assigned"]

    K --> O["Sales/Lead_SA input DQ Number<br/>PATCH /projects/id/dq-number"]
    O --> P["status=Ready (DQ pertama)<br/>sla_timer.stop_timer + auto-unlock"]

    K --> Q["SA mencatat aktivitas<br/>POST /activity-logs (AI polish)"]
    K --> R["SA kelola dokumen<br/>POST /projects/id/documents<br/>PATCH /documents/id/status"]

    P --> S["Forward ke Closed-Win<br/>PATCH /projects/id/status"]
    S --> T{"handover readiness?<br/>Closed-Win + HLD Final<br/>+ PMO/Delivery email + folder"}
    T -- "Siap" --> U["POST /projects/id/handover<br/>provision Final_Deliverables + permission"]
    U --> V["status=Handover Complete<br/>notifikasi PMO+Delivery, audit log"]
    T -- "Belum" --> W["Tolak: daftar missing_items"]
```

## 4. Alur SLA Timer DQ Number

```mermaid
sequenceDiagram
    participant Lead as Lead_SA
    participant API as assignment.py
    participant SLA as sla_timer
    participant Cron as POST /sla/process
    participant GDrive as folder_provisioner
    participant Sales

    Lead->>API: assign SA ke proyek
    Note over API,SLA: start_timer dibuat saat Assigned (SLATracking status=green)
    loop Cron harian (manual/trigger)
        Cron->>SLA: process_sla_actions()
        Note over SLA: H+3 jadi yellow, reminder ke Sales
        Note over SLA: H+5 jadi red, eskalasi ke Lead_SA/Admin, auto-lock folder Solutions
        SLA->>GDrive: lock_solutions_folder (hapus akses Sales)
    end
    Sales->>API: input DQ Number
    API->>SLA: stop_timer()
    Note over SLA: stopped_at di-set, jika terkunci lakukan unlock_solutions_folder dan audit log

```

### Catatan SLA

- Threshold: `green` 0-2 hari, `yellow` 3-4 hari, `red` 5+ hari (`sla_timer.py`).
- `process_sla_actions` tidak dijadwalkan otomatis di dalam app — harus dipanggil lewat `POST /api/v1/sla/process` (hanya `Admin`/`Lead_SA`), biasanya oleh cron eksternal.
- `start_timer` **ada dan idempotent**, tetapi perlu dicatat: pemanggilannya saat assignment bergantung pada wiring provisioning; karena `_trigger_folder_provisioner` masih stub (B2), `gdrive_folder_id` tidak pernah terisi, sehingga auto-lock/unlock folder Solutions tidak akan berjalan di runtime nyata (service-nya sendiri lengkap, hanya tidak ter-wire).

## 5. Pemicu Transisi (ringkasan)

| Transisi | Pemicu | Endpoint / Service | Role |
|----------|--------|--------------------|------|
| `-` → `New` | Requester buat opportunity | `POST /projects` | Sales/SA/Lead_SA |
| `New` → `Pending Assignment` / `Need Clarification` / `Manual Review Required` | Hasil BANT scoring | `scoring_engine.apply_threshold` (async) atau `POST /projects/{id}/score-manual` | otomatis / Sales |
| `Pending Assignment` → `Assigned` | Assign SA | `POST /projects/{id}/assign` | Lead_SA/Admin |
| `Assigned` → `Ready` | Input DQ Number pertama | `PATCH /projects/{id}/dq-number` | Sales/Lead_SA/Admin |
| `Ready` → `Closed-Win` | Forward manual | `PATCH /projects/{id}/status` | sesuai akses proyek |
| `Closed-Win` → `Handover Complete` | Trigger handover | `POST /projects/{id}/handover` | SA ditugaskan/Lead_SA/Admin |
| `* ` → `Lost` | Set Lost | `PATCH /projects/{id}/status` | Lead_SA/Admin |
| doc `Draft`→`Reviewed`→`Final` | Update status dokumen | `PATCH /documents/{id}/status` | SA/Lead_SA (mundur: Lead_SA) |
| SLA start | Saat proyek `Assigned` | `sla_timer.start_timer` | otomatis |
| SLA stop + unlock | Input DQ Number | `sla_timer.stop_timer` | otomatis |
| SLA lock + eskalasi | H+5 tanpa DQ | `sla_timer.process_sla_actions` | cron (Admin/Lead_SA) |

> Content was rephrased for compliance with licensing restrictions.
