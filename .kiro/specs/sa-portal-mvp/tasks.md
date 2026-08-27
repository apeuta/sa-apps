# Implementation Plan: Portal SA MVP

## Overview

Portal SA adalah PWA pengganti Redmine untuk manajemen proyek pre-sales dan pencatatan aktivitas harian Solutions Architect. Implementasi menggunakan arsitektur decoupled: Next.js 14+ (frontend), FastAPI Python 3.11+ (backend), dan PostgreSQL 15+ (database), di-deploy via Docker Compose di **Ubuntu VM**.

**Deployment Strategy:** Code di-generate di workspace lokal (macOS), lalu dipush ke GitHub. Dari VM Ubuntu, code di-pull dan di-deploy menggunakan Docker Compose. VM harus sudah di-setup dengan Docker, Git, dan user khusus untuk menjalankan service.

---

## Panduan Setup Ubuntu VM untuk Deployment

### Prasyarat VM
- Ubuntu 22.04 LTS atau lebih baru
- Minimal 2 vCPU, 4GB RAM, 30GB disk
- Akses SSH dan port 3000, 8000 terbuka (atau di-reverse-proxy via Nginx)

### Langkah Setup User dan Environment

```bash
# 1. Login ke VM sebagai root atau user dengan sudo
ssh your-user@your-vm-ip

# 2. Buat user khusus untuk deployment (dengan password)
sudo adduser sa-portal --gecos ""
# Sistem akan meminta Anda memasukkan password untuk user sa-portal
# Masukkan password yang kuat (min 12 karakter, kombinasi huruf/angka/simbol)
sudo usermod -aG sudo sa-portal

# 3. Install Docker Engine
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Tambahkan user sa-portal ke group docker (tanpa sudo untuk docker)
sudo usermod -aG docker sa-portal

# 5. Switch ke user sa-portal
sudo su - sa-portal

# 6. Verifikasi Docker
docker --version
docker compose version

# 7. Install Git
sudo apt-get install -y git

# 8. Setup SSH key untuk GitHub
#
# Langkah A: Generate SSH key pair di VM
ssh-keygen -t ed25519 -C "sa-portal@vm"
# Tekan Enter untuk lokasi default (~/.ssh/id_ed25519)
# Masukkan passphrase (opsional, tambahan keamanan) atau Enter untuk skip

# Langkah B: Tampilkan public key
cat ~/.ssh/id_ed25519.pub
# Output akan terlihat seperti:
# ssh-ed25519 AAAAC3Nza...panjang...random sa-portal@vm
# COPY seluruh baris output ini

# Langkah C: Tambahkan public key ke GitHub
# 1. Buka browser → https://github.com/settings/keys
# 2. Klik tombol hijau "New SSH key"
# 3. Title: isi "SA Portal VM" (atau nama apapun untuk identifikasi)
# 4. Key type: biarkan "Authentication Key"
# 5. Key: PASTE public key yang sudah di-copy dari langkah B
# 6. Klik "Add SSH key"
# 7. GitHub akan minta konfirmasi password akun GitHub Anda

# Langkah D: Verifikasi koneksi SSH ke GitHub dari VM
ssh -T git@github.com
# Jika berhasil, output: "Hi apeuta! You've been authenticated..."
# Jika pertama kali, akan muncul fingerprint confirmation → ketik "yes"

# Langkah E: Konfigurasi Git identity di VM
git config --global user.name "SA Portal Deploy"
git config --global user.email "your-email@domain.com"

# 9. Clone repository
git clone git@github.com:apeuta/sa-apps.git ~/sa-portal
# atau HTTPS:
# git clone https://github.com/apeuta/sa-apps.git ~/sa-portal

# 10. Buat file .env dari template
cd ~/sa-portal
cp .env.example .env
nano .env  # Isi semua credentials (Google OAuth, Gemini API key, dll.)

# 11. Jalankan aplikasi
docker compose up -d --build

# 12. Verifikasi semua service running
docker compose ps
curl http://localhost:8000/health
curl http://localhost:3000
```

### Setup Nginx Reverse Proxy (Opsional — untuk akses via domain)

```bash
sudo apt-get install -y nginx

# Buat config Nginx
sudo tee /etc/nginx/sites-available/sa-portal <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Ganti dengan domain/IP

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 100M;  # Untuk file upload
    }

    # Swagger docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
    }
    location /redoc {
        proxy_pass http://localhost:8000/redoc;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/sa-portal /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Setup SSL dengan Let's Encrypt (Opsional — jika ada domain)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Update Deployment (Setelah Code Baru di-Push)

```bash
# Login ke VM sebagai sa-portal
ssh sa-portal@your-vm-ip

cd ~/sa-portal
git pull origin main
docker compose down
docker compose up -d --build
docker compose logs -f  # Monitor startup
```

---

## Tasks

- [x] 1. Setup project structure, Docker, dan database schema
  - [x] 1.1 Buat project root structure dengan Docker Compose
    - Buat `docker-compose.yml` dengan 3 services: frontend (Next.js), backend (FastAPI), database (PostgreSQL 15)
    - Buat `Dockerfile` multi-stage untuk backend (Python 3.11 slim) dan frontend (Node 20 Alpine)
    - Buat `.env.example` dengan seluruh environment variables yang didokumentasikan (termasuk VM IP/domain)
    - Setup named volume `pgdata` untuk PostgreSQL persistence
    - Konfigurasi health check endpoints, restart policy `on-failure:3`, dan dependency order
    - Tambahkan `deploy.sh` script untuk automasi deployment di VM (git pull + docker compose up)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.6, 10.7, 10.8_

  - [x] 1.2 Setup backend FastAPI project structure
    - Buat struktur folder: `backend/app/{api,services,models,schemas,core,utils}`
    - Setup `main.py` dengan FastAPI app, CORS, rate limiter (100 req/min/user), dan auto-docs (`/docs`, `/redoc`)
    - Implementasi health check endpoint `/health` yang return `{"database": "healthy|unhealthy", "api": "healthy|unhealthy"}`
    - Buat `requirements.txt` / `pyproject.toml` dengan dependencies (fastapi, uvicorn, asyncpg, sqlalchemy, pydantic, python-jose, hypothesis)
    - _Requirements: 10.5, 11.4, 11.5_

  - [x] 1.3 Setup frontend Next.js project structure
    - Inisialisasi Next.js 14+ dengan App Router dan TypeScript
    - Konfigurasi PWA plugin (next-pwa), Service Worker, Web App Manifest
    - Setup Zustand untuk state management
    - Setup SWR untuk data fetching dan caching
    - Buat layout dasar: sidebar navigation (collapsible 240px/64px), header (max 64px), main content area (min 60% viewport)
    - _Requirements: 12.1, 12.2, 12.3, 19.7_

  - [x] 1.4 Buat database schema dan migrations
    - Implementasi SQLAlchemy models untuk semua tabel: Users, Projects, Documents, ActivityLogs, NotificationLogs, AuditLogs, SLATracking
    - Buat SQL migration scripts sesuai DDL di design document
    - Setup Alembic untuk migration management
    - Implementasi semua constraints, indexes, dan CHECK validations sesuai design
    - _Requirements: 2.2, 6.5, 7.2, 8.1, 9.6, 14.1_

- [x] 2. Implementasi Auth_Service dan middleware
  - [x] 2.1 Implementasi Google OAuth 2.0 flow di backend
    - Buat `AuthService` class dengan methods: `initiate_oauth`, `handle_callback`, `validate_domain`, `refresh_token`, `get_or_create_user`, `revoke_session`
    - Implementasi domain whitelist validation dari environment variable `ALLOWED_DOMAINS`
    - Implementasi role mapping berdasarkan konfigurasi `ROLE_MAPPING` (default role: SA)
    - Implementasi JWT session creation dengan TTL 24 jam
    - Implementasi auto-refresh token saat expired
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ]* 2.2 Write property tests untuk Auth_Service
    - **Property 1: Domain Whitelist Validation** — Verifikasi bahwa email diterima iff domain ada di whitelist
    - **Property 2: User Upsert Idempotence** — Verifikasi tepat 1 record per google_id setelah multiple upserts
    - **Validates: Requirements 1.3, 1.4**

  - [x] 2.3 Implementasi auth middleware dan API response format
    - Buat middleware JWT validation yang return 401 untuk token invalid/expired/absent
    - Implementasi standard response format: `{"status": "success|error", "data": {...}, "message": "..."}`
    - Implementasi Pydantic schema validation yang return 422 dengan detail per-field
    - Implementasi rate limiter middleware (100 req/min/user) dengan header `Retry-After`
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6, 11.7_

  - [ ]* 2.4 Write property test untuk API Response Format
    - **Property 16: API Response Format Consistency** — Verifikasi semua response mengikuti format standar
    - **Validates: Requirements 11.1**

  - [x] 2.5 Implementasi login page dan OAuth redirect di frontend
    - Buat halaman login dengan tombol "Login dengan Google"
    - Handle OAuth callback dan simpan token di client
    - Implementasi auth guard untuk protected routes
    - Handle error states: domain tidak diizinkan, autentikasi dibatalkan/gagal
    - _Requirements: 1.1, 1.3, 1.6_

- [x] 3. Checkpoint — Pastikan auth flow end-to-end berfungsi
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implementasi LLM_Provider abstraction layer
  - [x] 4.1 Buat LLM Provider interface dan factory
    - Buat `LLMProviderInterface` protocol dengan methods: `complete_text`, `parse_document`, `structure_text`
    - Buat `LLMProviderFactory` dengan registry pattern dan `get_provider`, `register_adapter`, `reload_config`
    - Implementasi standardized response format: status, hasil teks terstruktur, metadata (model, token usage)
    - _Requirements: 18.1, 18.2, 18.5, 18.7_

  - [x] 4.2 Implementasi GeminiAdapter sebagai default provider
    - Buat `GeminiAdapter` class yang implement `LLMProviderInterface`
    - Implementasi multimodal document parsing (PDF/DOCX)
    - Implementasi text completion dan text structuring
    - Implementasi retry dengan exponential backoff (1s → 2s → 4s), timeout 30s per request
    - Implementasi hot-reload config (maks 30 detik switch tanpa restart)
    - Implementasi fallback ke last known good config jika config baru gagal
    - _Requirements: 18.3, 18.4, 18.6, 18.8, 18.9_

  - [ ]* 4.3 Write property tests untuk LLM Provider
    - **Property 21: LLM Provider Response Standardization** — Verifikasi format response internal konsisten dari adapter manapun
    - **Property 22: LLM Retry Exponential Backoff** — Verifikasi interval retry sesuai spesifikasi (1s, 2s, 4s)
    - **Validates: Requirements 18.5, 18.6, 18.9**

- [x] 5. Implementasi Scoring_Engine dan Pre-Sales Request flow
  - [x] 5.1 Implementasi API endpoint submission request pre-sales
    - Buat endpoint `POST /api/v1/projects` dengan validasi: project_name ≤ 150 chars, customer_name ≤ 150 chars, target_submit bukan masa lalu, estimasi_nilai 0.01–999,999,999,999.00
    - Implementasi file upload (PDF/DOCX, max 20MB/file, max 5 files)
    - Buat record Projects dengan status "New", timestamp, dan sales_pic
    - Trigger Scoring_Engine async dalam < 5 detik setelah record tersimpan
    - Handle partial file upload failure (file valid disimpan, file gagal dilaporkan)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ]* 5.2 Write property tests untuk project form validation
    - **Property 3: Project Form Input Validation** — Verifikasi acceptance/rejection berdasarkan constraints
    - **Property 4: Project Record Creation Invariant** — Verifikasi record baru selalu memiliki status "New", timestamp, dan sales_pic
    - **Property 5: File Upload Partial Failure Isolation** — Verifikasi file valid tersimpan meskipun ada file gagal
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.6**

  - [x] 5.3 Implementasi Scoring_Engine — BANT scoring via LLM
    - Buat `ScoringEngine` class dengan methods: `score_documents`, `score_manual`, `apply_threshold`, `search_similar_projects`
    - Implementasi multimodal file parsing (PDF/DOCX only, skip format lain)
    - Implementasi BANT score calculation: sub-skor 0-25 per kriteria, total 0-100
    - Implementasi threshold gating: >= 60 → "Pending Assignment" + notif Lead_SA, < 60 → "Need Clarification" + feedback ke Sales
    - Implementasi BANT manual form (4 kriteria, skala 0-25 per integer)
    - Implementasi retry: timeout 30s, retry 3x interval 10s, fallback ke "Manual Review Required"
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11_

  - [ ]* 5.4 Write property tests untuk Scoring_Engine
    - **Property 6: BANT Score Calculation Correctness** — Verifikasi total = sum sub-skor, range 0-100
    - **Property 7: BANT Threshold Gating** — Verifikasi >= 60 → "Pending Assignment", < 60 → "Need Clarification"
    - **Property 8: File Type Filtering** — Verifikasi hanya PDF/DOCX yang diproses
    - **Validates: Requirements 3.2, 3.4, 3.5, 3.7, 3.10**

  - [x] 5.5 Implementasi frontend form submission request
    - Buat halaman form request baru untuk Sales: input fields + file upload drag-and-drop
    - Implementasi client-side validation (field wajib, format, ukuran file)
    - Implementasi BANT manual form sebagai fallback
    - Tampilkan feedback BANT score dan status perubahan
    - _Requirements: 2.1, 2.3, 2.7, 3.6_

- [x] 6. Checkpoint — Pastikan scoring flow end-to-end berfungsi
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implementasi Project Assignment dan Folder Provisioning
  - [x] 7.1 Implementasi endpoint assignment SA oleh Lead_SA
    - Buat endpoint `POST /api/v1/projects/{id}/assign` (Lead_SA only)
    - Tampilkan daftar SA dengan jumlah proyek aktif masing-masing
    - Update status → "Assigned", simpan `assigned_sa` dan `assigned_at`
    - Trigger notifikasi ke SA yang ditugaskan
    - Trigger Folder_Provisioner async setelah assignment
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 7.2 Implementasi Folder_Provisioner — Google Drive integration
    - Buat `FolderProvisioner` class dengan methods: `provision_project_folder`, `lock_solutions_folder`, `unlock_solutions_folder`, `provision_handover`, `sanitize_folder_name`
    - Implementasi folder creation: master folder `[Customer_Name] - [Project_Name]` + 3 subfolder (Inventory, Diagram, Solutions)
    - Implementasi permission setting: Editor untuk SA + Lead_SA, Viewer untuk Sales pada Inventory saja
    - Implementasi folder name sanitization (ganti `/\*?"` dengan `_`)
    - Implementasi retry 3x interval 5s, flag "Provisioning Failed" jika gagal
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 7.3 Write property test untuk Folder_Provisioner
    - **Property 9: Folder Name Sanitization** — Verifikasi output tidak mengandung karakter invalid
    - **Validates: Requirements 5.7**

  - [x] 7.4 Implementasi frontend dashboard Lead_SA dan assignment UI
    - Buat dashboard Lead_SA: antrian "Pending Assignment", overview semua proyek aktif, utilisasi SA
    - Buat modal assignment dengan daftar SA dan workload masing-masing
    - Tampilkan badge "Folder Pending" jika provisioning gagal
    - _Requirements: 4.1, 9.3_

- [x] 8. Implementasi DQ Number, Document Tracking, dan Project Workflow
  - [x] 8.1 Implementasi DQ Number input dan document gating
    - Buat endpoint `PATCH /api/v1/projects/{id}/dq-number` untuk input DQ Number
    - Implementasi validasi format DQ Number (alfanumerik + hyphen, 5-20 karakter)
    - Implementasi gating: sembunyikan link Solutions dari Sales jika belum ada DQ, tampilkan jika DQ ada + dokumen "Reviewed"
    - Implementasi proteksi: Sales tidak bisa edit/hapus DQ yang sudah tersimpan (hanya Lead_SA)
    - Update status → "Ready" saat DQ diinput
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 8.2 Write property test untuk DQ Number validation
    - **Property 10: DQ Number Format Validation** — Verifikasi acceptance/rejection sesuai regex `^[A-Za-z0-9\-]{5,20}$`
    - **Validates: Requirements 6.5**

  - [x] 8.3 Implementasi Document Tracking CRUD dan state machine
    - Buat endpoints: `POST /api/v1/projects/{id}/documents`, `PATCH /api/v1/documents/{id}/status`
    - Implementasi tipe dokumen: PropTek, BOQ, Mandays, MoM, RFP, HLD
    - Implementasi status state machine: Draft → Reviewed → Final (tidak boleh loncat)
    - Proteksi: SA tidak bisa ubah status "Final", hanya Lead_SA
    - Catat timestamp dan user pada setiap transisi
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 8.4 Write property test untuk Document Status State Machine
    - **Property 11: Document Status State Machine** — Verifikasi hanya transisi Draft→Reviewed dan Reviewed→Final yang valid
    - **Validates: Requirements 7.3, 7.5**

  - [x] 8.5 Implementasi Project Status Workflow dan audit log
    - Implementasi transisi status: New → Pending Assignment → Assigned → Ready → Closed-Win → Handover Complete
    - Implementasi status "Lost" (hanya Lead_SA, dari status manapun kecuali "Handover Complete")
    - Tolak transisi tidak valid dengan error message
    - Catat setiap perubahan status di audit_logs (timestamp, old_value, new_value, performed_by)
    - _Requirements: 9.4, 9.5, 9.6_

  - [ ]* 8.6 Write property tests untuk Project Workflow
    - **Property 14: Project Workflow State Machine** — Verifikasi hanya transisi valid yang diizinkan per role
    - **Property 15: Audit Log Completeness on Status Change** — Verifikasi setiap status change menghasilkan audit log
    - **Validates: Requirements 9.4, 9.5, 9.6**

  - [x] 8.7 Implementasi frontend document tracking dan DQ Number UI
    - Buat halaman daftar dokumen per proyek dengan kolom: tipe, status, link GDrive
    - Buat form tambah dokumen baru (tipe, link GDrive, catatan max 500 chars)
    - Buat input DQ Number dengan validasi format
    - Tampilkan badge "Menunggu DQ" pada project card
    - _Requirements: 6.2, 7.1, 7.2_

- [x] 9. Checkpoint — Pastikan workflow proyek end-to-end berfungsi
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implementasi Activity Logger dan Google Calendar Sync
  - [x] 10.1 Implementasi Activity_Logger backend
    - Buat `ActivityLogger` class dengan methods: `create_log`, `polish_notes`, `retry_polish`, `sync_calendar`, `map_event_to_project`, `get_project_story`
    - Buat endpoint `POST /api/v1/activity-logs` dengan validasi: project_id valid, subtask_category dari daftar, duration 0.25–24.00 (kelipatan 0.25), raw_notes max 5000 chars
    - Implementasi AI note polishing via LLM: raw_notes → JSON `{discussion_points: [], action_items: []}`
    - Handle LLM failure: simpan raw_notes, ai_polished_notes = null, tampilkan "Polish Ulang"
    - Implementasi project story endpoint dengan filter category/tanggal dan pagination (20/page)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [ ]* 10.2 Write property tests untuk Activity Logger
    - **Property 12: Activity Log Input Validation** — Verifikasi acceptance/rejection berdasarkan constraints input
    - **Property 13: Project Story Filtering Correctness** — Verifikasi filter menghasilkan subset yang sesuai
    - **Validates: Requirements 8.1, 8.2, 8.5**

  - [x] 10.3 Implementasi Google Calendar sync dan event mapping
    - Buat endpoint `POST /api/v1/calendar/sync` — fetch events 7 hari lalu + 7 hari depan (max 200 events)
    - Buat endpoint `POST /api/v1/calendar/map` — map event ke project
    - Implementasi unique constraint: 1 gcal_event_id hanya bisa di-map ke 1 project
    - Handle all-day events dengan durasi default 8 jam
    - Handle Calendar API timeout (15s) dengan error message
    - Konfigurasi webhook endpoint via env `GCAL_WEBHOOK_ENDPOINT` (opsional)
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ]* 10.4 Write property test untuk Calendar Event Mapping
    - **Property 17: Calendar Event Mapping Uniqueness** — Verifikasi duplicate mapping ditolak
    - **Validates: Requirements 13.4**

  - [x] 10.5 Implementasi frontend Activity Log dan Calendar UI
    - Buat halaman Activity Log: form input (project, category, durasi, notes) + project story timeline
    - Buat panel Calendar Sync: tombol sync, daftar events, mapping ke project
    - Tampilkan AI polished notes dan tombol "Polish Ulang"
    - Implementasi filter (category, tanggal) dan pagination
    - _Requirements: 8.1, 8.5, 13.1, 13.2_

- [x] 11. Implementasi Notification_Service dan SLA_Timer
  - [x] 11.1 Implementasi Notification_Service backend
    - Buat `NotificationService` class dengan methods: `send_notification`, `send_email`, `get_user_notifications`, `mark_as_read`
    - Implementasi in-app notification (selalu aktif) + email via Gmail API (graceful fallback)
    - Implementasi event types: assignment, status_change, sla_reminder, sla_escalation, handover, doc_ready
    - Log semua notifikasi ke NotificationLogs (event_type, recipient, channel, status, timestamp, reference_id)
    - Implementasi email retry: 3x interval 30s
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [ ]* 11.2 Write property test untuk Notification_Service
    - **Property 18: Notification Log Completeness** — Verifikasi setiap event trigger menghasilkan record lengkap di NotificationLogs
    - **Validates: Requirements 14.1**

  - [x] 11.3 Implementasi SLA_Timer dan auto-lock/unlock
    - Buat `SLATimer` class dengan methods: `start_timer`, `check_sla_status`, `process_sla_actions`, `stop_timer`
    - Implementasi cron job (atau scheduled task) untuk pengecekan SLA harian
    - Implementasi logic: hari 0-2 hijau, H+3 kuning + reminder, H+5 merah + eskalasi + auto-lock folder Solutions
    - Implementasi stop timer saat DQ Number diinput
    - Implementasi auto-unlock saat DQ diinput setelah lock
    - Implementasi retry 3x interval 5s untuk GDrive lock/unlock operations
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8_

  - [ ]* 11.4 Write property test untuk SLA Timer
    - **Property 20: SLA Timer Day-Based Actions** — Verifikasi badge dan actions sesuai hari elapsed
    - **Validates: Requirements 16.2, 16.3, 16.7**

  - [x] 11.5 Implementasi frontend Notification Center dan SLA badges
    - Buat halaman Notification Center: riwayat notifikasi, read/unread, pagination 20/page
    - Implementasi click-to-navigate (notif → halaman terkait) + mark as read
    - Tampilkan SLA countdown badge (hijau/kuning/merah) pada project card
    - Tampilkan banner peringatan auto-lock pada detail proyek
    - _Requirements: 14.7, 14.8, 16.7, 16.8_

- [x] 12. Implementasi RAG Recommendation dan PMO Handover
  - [x] 12.1 Implementasi RAG template recommendation
    - Implementasi `search_similar_projects` di ScoringEngine: cari proyek Closed-Win berdasarkan use_case_tags
    - Kriteria: minimal 1 tag sama, urut descending berdasarkan jumlah tag cocok, max 5 results
    - Buat endpoint `GET /api/v1/projects/{id}/recommendations`
    - Handle edge cases: belum ada proyek Closed-Win, proyek belum punya tags
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [ ]* 12.2 Write property test untuk RAG Recommendation
    - **Property 19: RAG Recommendation Tag Matching and Ordering** — Verifikasi results hanya berisi proyek dengan min 1 tag cocok, ordered descending, max 5 items
    - **Validates: Requirements 15.2, 15.3**

  - [x] 12.3 Implementasi PMO Handover automation
    - Implementasi trigger handover saat HLD "Final" + status "Closed-Win"
    - Buat subfolder "Final_Deliverables" di Solutions, tambah permission Viewer untuk PMO Lead + Delivery Lead
    - Kirim notifikasi handover (in-app + email) dengan detail proyek
    - Update status → "Handover Complete" + audit log
    - Handle konfigurasi PMO/Delivery Lead belum ada: form input email
    - Handle GDrive error: retry 3x interval 5s, flag "Handover Failed"
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

  - [x] 12.4 Implementasi frontend RAG panel dan Handover modal
    - Buat panel "Referensi Serupa" di sidebar halaman pembuatan dokumen
    - Tampilkan max 5 rekomendasi dengan nama proyek, tipe dokumen, tags, link GDrive
    - Buat modal blocking Closed-Win → instruksi HLD
    - Buat form input PMO/Delivery Lead email jika belum dikonfigurasi
    - _Requirements: 15.1, 15.3, 15.4, 17.1, 17.6_

- [x] 13. Implementasi Dashboard per Role dan UI/UX polish
  - [x] 13.1 Implementasi dashboard Sales
    - Tampilkan daftar proyek yang disubmit Sales: nama proyek, nama customer, status, tanggal perubahan terakhir
    - Implementasi search bar dan dropdown filter status pada listing proyek
    - Implementasi loading skeleton (bukan spinner) untuk data fetching > 200ms
    - _Requirements: 9.1, 9.9, 19.5_

  - [x] 13.2 Implementasi dashboard SA
    - Tampilkan daftar proyek yang ditugaskan ke SA: nama proyek, customer, status, progres dokumen (rasio Final/total)
    - Implementasi search bar dan filter status
    - _Requirements: 9.2, 9.9_

  - [x] 13.3 Implementasi dashboard Lead SA (extended)
    - Tampilkan antrian proyek "Pending Assignment" + overview proyek per status
    - Tampilkan section utilisasi SA (jumlah proyek aktif per SA)
    - Implementasi tabel utilisasi SA per bulan (jam kerja) — endpoint GET /sa/utilization
    - Filter tahun dan filter per individu SA
    - Baris ringkasan total jam per bulan
    - Implementasi section effort per proyek — endpoint GET /utilization/projects
    - Tabel total jam + personel SA per proyek
    - _Requirements: 9.3, 9.7, 9.8_

  - [x] 13.4 Implementasi UI/UX design system dan PWA polish
    - Terapkan font Open Sans, palet warna netral + accent color
    - Implementasi toast notifications: sukses (auto-dismiss 3s), error (auto-dismiss 5s, warna berbeda)
    - Implementasi responsive layout 320px–1440px, touch targets min 44x44px, teks body min 16px
    - Implementasi transisi/animasi max 200ms, feedback visual < 100ms
    - Implementasi offline support: queue submission saat offline, sync otomatis saat online, indikator "Menunggu Sinkronisasi"
    - Hapus semua emoji dari UI
    - Target Lighthouse PWA score minimal 80
    - _Requirements: 12.3, 12.4, 12.5, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10, 21.3_

  - [x] 13.5 Implementasi halaman detail proyek (enhanced)
    - Tampilkan data BANT deskriptif (nominal MRR, PIC, kebutuhan teknis, timeline) — BUKAN skor numerik
    - Tampilkan Project Story langsung di halaman detail (bukan halaman terpisah)
    - Tombol "Lihat Semua" untuk expand timeline lengkap
    - Tombol Edit untuk mengedit informasi proyek
    - _Requirements: 9.10, 9.11, 9.12_

- [x] 15. Implementasi Admin Settings
  - [x] 15.1 Implementasi backend Admin endpoints
    - Endpoint GET /admin/users — daftar semua users (Admin only)
    - Endpoint PATCH /admin/users/{id}/role — ubah role user (Admin only)
    - Validasi role: Sales, SA, Lead_SA, Admin
    - _Requirements: 20.6, 20.7, 20.8_

  - [x] 15.2 Implementasi frontend halaman Admin Settings
    - Buat halaman Admin Settings dengan 2 section
    - Section "Kategori Aktivitas": list, tambah, edit, hapus subtask categories
    - Section "User & Role Management": list users, ubah role via dropdown
    - Proteksi akses: hanya role Admin yang bisa lihat menu dan halaman ini
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [x] 15.3 Update navigasi dan sidebar
    - Hapus menu "Dokumen" dari sidebar
    - Tambah menu "Admin Settings" (hanya visible untuk Admin)
    - _Requirements: 21.1, 21.2_

- [x] 16. Implementasi routing dashboard per role
  - [x] 16.1 Halaman / render dashboard sesuai role
    - Sales → SalesDashboard (listing proyek + search/filter)
    - SA → SADashboard (proyek assigned)
    - Lead_SA/Admin → LeadSADashboard (overview + utilisasi + effort)
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 17. Seed data demo diperkaya
  - [x] 17.1 Update seed script
    - 7 users (Sales, SA, Lead_SA, Admin)
    - 8 proyek dengan berbagai status
    - 21 activity logs tersebar Jun-Aug 2026
    - bant_detail berisi data deskriptif (bukan skor numerik)
    - DQ Number terisi di beberapa proyek

- [x] 18. Final checkpoint — Pastikan semua fitur terintegrasi dan berfungsi

## Notes

- Tasks marked dengan `*` adalah optional dan bisa di-skip untuk delivery MVP lebih cepat
- Setiap task mereferensikan requirements spesifik untuk traceability
- Backend ditulis dalam Python (FastAPI), frontend dalam TypeScript (Next.js)
- Property-based tests menggunakan Hypothesis (Python) dengan minimum 100 iterations
- Checkpoints memastikan validasi inkremental setiap beberapa fase
- Docker Compose menjalankan seluruh stack: frontend (port 3000), backend (port 8000), database (port 5432)
- **Deployment target: Ubuntu VM** — Code di-generate di workspace lokal, push ke GitHub, pull dari VM
- **Workflow:** Generate code (lokal) → Push ke GitHub → SSH ke VM → `git pull` → `docker compose up -d --build`
- Tidak perlu install Python/Node di VM — semua berjalan di container Docker

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["1.4"] },
    { "id": 2, "tasks": ["2.1", "2.3"] },
    { "id": 3, "tasks": ["2.2", "2.4", "2.5"] },
    { "id": 4, "tasks": ["4.1"] },
    { "id": 5, "tasks": ["4.2"] },
    { "id": 6, "tasks": ["4.3", "5.1"] },
    { "id": 7, "tasks": ["5.2", "5.3"] },
    { "id": 8, "tasks": ["5.4", "5.5", "7.1"] },
    { "id": 9, "tasks": ["7.2", "7.4"] },
    { "id": 10, "tasks": ["7.3", "8.1", "8.3", "8.5"] },
    { "id": 11, "tasks": ["8.2", "8.4", "8.6", "8.7"] },
    { "id": 12, "tasks": ["10.1", "10.3"] },
    { "id": 13, "tasks": ["10.2", "10.4", "10.5"] },
    { "id": 14, "tasks": ["11.1", "11.3"] },
    { "id": 15, "tasks": ["11.2", "11.4", "11.5"] },
    { "id": 16, "tasks": ["12.1", "12.3"] },
    { "id": 17, "tasks": ["12.2", "12.4"] },
    { "id": 18, "tasks": ["13.1", "13.2", "13.3", "13.4", "13.5"] },
    { "id": 19, "tasks": ["15.1", "15.2", "15.3"] },
    { "id": 20, "tasks": ["16.1", "17.1"] }
  ]
}
```
