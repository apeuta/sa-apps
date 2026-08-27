# Requirements Document

## Introduction

Portal SA adalah aplikasi Progressive Web App (PWA) pengganti Redmine yang menggabungkan manajemen proyek pre-sales (request Sales ke SA) dan manajemen aktivitas harian (Activity Log) dalam satu platform. Aplikasi ini ditenagai oleh Google Workspace (GDrive, Gmail, GCalendar) dan Google Gemini AI.

Dokumen ini mendefinisikan scope **MVP (Minimum Viable Product)** yang difokuskan pada workflow inti dengan pendekatan paling efisien untuk development dan deployment. MVP ini di-deploy menggunakan **Docker** agar portabel di berbagai environment.

### Rekomendasi Efisiensi untuk MVP

| Layer | Rekomendasi | Alasan |
|-------|-------------|--------|
| Backend | **FastAPI (Python)** | Rapid development, native async, auto-generate OpenAPI docs, ekosistem AI/ML Python kuat untuk integrasi Gemini |
| Frontend | **Next.js (React)** dengan PWA plugin | SSR/SSG, excellent DX, PWA capability built-in, large ecosystem |
| Database | **PostgreSQL** | Relational data yang solid, JSON support native, cocok untuk struktur data Portal SA |
| AI | **Google Gemini API** (langsung via REST) | Mulai dengan API call langsung, RAG bisa ditambahkan di iterasi berikutnya |
| Auth | **Google OAuth 2.0** | Sudah terintegrasi dengan Google Workspace, single sign-on |
| Containerization | **Docker + Docker Compose** | Multi-service orchestration sederhana, portabel |
| MVP Simplification | Mock email notification (log only), Skip RAG (iterasi 2), Calendar sync manual trigger (bukan real-time webhook) | Mengurangi kompleksitas infrastruktur untuk MVP |

### Scope MVP vs Iterasi Berikutnya

**Termasuk MVP (Full Scope):**
- Pre-Sales Request submission + AI BANT Scoring
- Project assignment & status workflow
- GDrive folder auto-provisioning
- Document tracking + DQ Number gating
- Activity log dengan AI note polishing
- Google Calendar sync & activity mapping
- Email notification (Gmail API) dengan graceful fallback ke in-app
- RAG template recommendation
- SLA DQ Number auto-lock/unlock
- PMO Handover automation post Closed-Win
- Docker deployment

**Implementasi Bertahap (masuk scope, tapi bisa incremental):**
- GCalendar sync (MVP: manual trigger, target: real-time webhook)
- Email notification (MVP: in-app + log, target: Gmail API automation)
- RAG template recommendation (MVP: basic keyword matching, target: full semantic search)
- SLA auto-lock/unlock (MVP: warning badge + manual lock, target: full automation)
- PMO Handover (MVP: semi-automated folder sharing, target: full automation)

## Glossary

- **Portal_SA**: Aplikasi web (PWA) pengganti Redmine untuk manajemen proyek pre-sales dan aktivitas harian Solutions Architect
- **Sales**: Pengguna dari tim penjualan yang mengajukan request proyek baru
- **SA (Solutions_Architect)**: Pengguna yang mengerjakan deliverables teknis (PropTek, BOQ, HLD)
- **Lead_SA**: SA senior yang menerima notifikasi dan melakukan penugasan SA ke proyek
- **BANT_Score**: Skor 0-100% hasil analisis AI terhadap 4 kriteria: Budget, Authority, Need, Timeline
- **DQ_Number**: Nomor Deal Qualification yang diinput Sales sebagai syarat rilis dokumen
- **Scoring_Engine**: Modul AI yang menganalisis dokumen dan menghitung BANT Score menggunakan LLM Provider yang dikonfigurasi (default: Google Gemini API)
- **LLM_Provider**: Abstraksi layer untuk komunikasi dengan Large Language Model, mendukung multiple provider (Gemini, OpenAI, Anthropic, dll.) melalui konfigurasi endpoint
- **Folder_Provisioner**: Modul yang membuat struktur folder otomatis di Google Drive
- **Activity_Logger**: Modul yang mencatat dan memproses aktivitas harian SA
- **Auth_Service**: Modul autentikasi dan otorisasi menggunakan Google OAuth 2.0
- **Container_Orchestrator**: Docker Compose setup yang menjalankan semua service aplikasi
- **Notification_Service**: Modul yang mengelola notifikasi in-app dan email (via Gmail API)
- **SLA_Timer**: Mekanisme penghitung waktu untuk DQ Number dengan threshold 3 hari (reminder) dan 5 hari (eskalasi + auto-lock)
- **PMO_Lead**: Person in charge dari tim Project Management Office yang menerima handover proyek Closed-Win
- **Delivery_Lead**: Person in charge dari tim Delivery/Implementation yang menerima handover proyek Closed-Win

## Requirements

### Requirement 1: Autentikasi via Google OAuth 2.0

**User Story:** Sebagai pengguna Portal SA, saya ingin login menggunakan akun Google Workspace saya, agar tidak perlu mengingat credential terpisah dan akses terkontrol berdasarkan domain organisasi.

#### Acceptance Criteria

1. WHEN pengguna mengakses Portal_SA tanpa session aktif, THE Auth_Service SHALL mengarahkan pengguna ke halaman Google OAuth 2.0 consent
2. WHEN pengguna berhasil autentikasi via Google OAuth, THE Auth_Service SHALL membuat session dan menyimpan token akses dengan masa berlaku maksimal 24 jam
3. IF domain email pengguna tidak terdaftar di whitelist organisasi yang dikonfigurasi melalui environment variable, THEN THE Auth_Service SHALL menolak akses dan menampilkan pesan error yang mengindikasikan domain tidak diizinkan
4. WHEN pengguna berhasil autentikasi dan lolos validasi domain, THE Auth_Service SHALL menyimpan atau memperbarui data profil pengguna (nama, email, role) ke dalam tabel Users di PostgreSQL, dengan role ditentukan berdasarkan mapping domain/email yang dikonfigurasi oleh admin (default role: SA jika tidak ada mapping)
5. WHEN token OAuth kedaluwarsa dan refresh token masih valid, THE Auth_Service SHALL melakukan refresh token secara otomatis tanpa memerlukan interaksi ulang dari pengguna
6. IF proses autentikasi Google OAuth gagal atau pengguna membatalkan consent, THEN THE Auth_Service SHALL mengarahkan pengguna kembali ke halaman login dan menampilkan pesan error yang mengindikasikan autentikasi dibatalkan atau gagal
7. IF refresh token kedaluwarsa atau di-revoke oleh Google, THEN THE Auth_Service SHALL mengakhiri session pengguna dan mengarahkan ke halaman login untuk autentikasi ulang

---

### Requirement 2: Submission Request Pre-Sales oleh Sales

**User Story:** Sebagai Sales, saya ingin mengajukan request proyek baru dengan mengunggah data customer dan dokumen referensi, agar SA bisa segera menganalisis kebutuhan teknis.

#### Acceptance Criteria

1. WHEN Sales mengisi form request baru, THE Portal_SA SHALL menerima input: nama proyek (maksimal 150 karakter), nama customer (maksimal 150 karakter), target submit date (tidak boleh tanggal di masa lalu), estimasi nilai proyek dalam mata uang IDR (rentang 0.01 hingga 999,999,999,999.00), dan file attachment (PDF/DOCX, maksimal 20MB per file)
2. WHEN form request disubmit dengan semua field wajib terisi, THE Portal_SA SHALL membuat record baru di tabel Projects dengan status "New" dan mencatat timestamp pembuatan serta ID Sales sebagai creator
3. IF field wajib (nama proyek, nama customer, target submit date, estimasi nilai proyek) tidak terisi lengkap, THEN THE Portal_SA SHALL menampilkan pesan validasi pada setiap field yang kosong dan mencegah submission
4. WHEN request berhasil dibuat dan minimal 1 file attachment tersedia, THE Portal_SA SHALL mengirim file attachment ke Scoring_Engine untuk analisis BANT dalam waktu kurang dari 5 detik setelah record tersimpan
5. THE Portal_SA SHALL mendukung upload maksimal 5 file attachment per satu request
6. IF file attachment gagal diunggah (timeout, format tidak valid, atau ukuran melebihi 20MB), THEN THE Portal_SA SHALL menampilkan pesan error yang mengindikasikan penyebab kegagalan pada file yang bermasalah dan mempertahankan file lain yang sudah berhasil diunggah
7. IF request dibuat tanpa file attachment, THEN THE Portal_SA SHALL menyimpan record dengan status "New" dan mengarahkan Sales ke opsi "Isi BANT Manual" untuk melanjutkan proses scoring

---

### Requirement 3: AI BANT Scoring via Google Gemini

**User Story:** Sebagai Lead SA, saya ingin setiap request baru dianalisis otomatis oleh AI untuk scoring BANT, agar saya bisa memprioritaskan penugasan berdasarkan kualitas opportunity.

#### Acceptance Criteria

1. WHEN file attachment diterima dari request baru, THE Scoring_Engine SHALL mengirim seluruh file attachment (maksimal 5 file sesuai batasan request) ke LLM_Provider untuk ekstraksi multimodal (PDF/DOCX ke structured data yang mencakup indikator Budget, Authority, Need, dan Timeline)
2. WHEN LLM_Provider mengembalikan hasil ekstraksi, THE Scoring_Engine SHALL menghitung BANT_Score (skala 0-100) dengan memberikan sub-skor 0-25 per kriteria berdasarkan apakah informasi terkait ditemukan secara eksplisit (25), parsial/implisit (10-20), atau tidak ditemukan sama sekali (0) dalam dokumen yang diekstrak
3. WHEN BANT_Score dihitung, THE Scoring_Engine SHALL menyimpan total skor ke field `bant_score`, menyimpan detail sub-skor per kriteria, dan meng-generate maksimal 5 `use_case_tags` pada record Projects berdasarkan konteks kebutuhan yang teridentifikasi dari dokumen
4. WHEN BANT_Score >= 60, THE Portal_SA SHALL mengubah status proyek menjadi "Pending Assignment" dan mengirim notifikasi in-app ke Lead_SA yang berisi nama proyek, BANT_Score, dan use_case_tags
5. WHEN BANT_Score < 60, THE Portal_SA SHALL mengubah status proyek menjadi "Need Clarification" dan menampilkan feedback ke Sales berupa daftar kriteria BANT yang mendapat sub-skor di bawah 15 beserta keterangan singkat apa informasi yang kurang
6. WHEN Sales memilih opsi "Isi BANT Manual" pada form request, THE Portal_SA SHALL menampilkan form input manual untuk 4 kriteria BANT (Budget, Authority, Need, Timeline) dengan skala 0-25 per kriteria (integer, increment 1)
7. WHEN Sales mensubmit BANT manual, THE Scoring_Engine SHALL menghitung total BANT_Score dari jumlah 4 kriteria dan menerapkan threshold gating yang sama (>= 60 lolos, < 60 perlu klarifikasi)
8. IF LLM_Provider tidak merespons dalam 30 detik, THEN THE Scoring_Engine SHALL menandai request sebagai "Scoring Pending" dan melakukan retry maksimal 3 kali dengan interval 10 detik
9. IF semua retry gagal, THEN THE Scoring_Engine SHALL menandai status "Manual Review Required" dan mengirim notifikasi ke Lead_SA untuk scoring manual
10. IF file attachment memiliki format selain PDF atau DOCX, THEN THE Scoring_Engine SHALL melewatkan file tersebut dari proses ekstraksi dan mencatat warning di application log
11. IF tidak ada file yang berformat valid (PDF/DOCX) dalam request, THEN THE Portal_SA SHALL menampilkan opsi "Isi BANT Manual" kepada Sales sebagai fallback

---

### Requirement 4: Penugasan SA oleh Lead SA

**User Story:** Sebagai Lead SA, saya ingin bisa menugaskan SA ke proyek yang sudah lolos scoring, agar ada kejelasan PIC teknis untuk setiap opportunity.

#### Acceptance Criteria

1. WHEN proyek berstatus "Pending Assignment", THE Portal_SA SHALL menampilkan proyek tersebut di dashboard Lead_SA dengan detail BANT_Score, use_case_tags, dan daftar SA yang tersedia beserta jumlah proyek aktif masing-masing SA
2. WHEN Lead_SA memilih SA dari daftar SA yang terdaftar di sistem dan mengkonfirmasi assignment, THE Portal_SA SHALL mengubah status proyek menjadi "Assigned", menyimpan `assigned_sa` dan `assigned_at` (timestamp) di record Projects
3. WHEN proyek di-assign ke SA, THE Portal_SA SHALL mengirim notifikasi in-app kepada SA yang ditugaskan berisi nama proyek, nama customer, BANT_Score, dan use_case_tags
4. WHEN status proyek berubah menjadi "Assigned", THE Portal_SA SHALL memicu Folder_Provisioner untuk membuat struktur folder proyek sesuai ketentuan di Requirement 5
5. WHEN Folder_Provisioner berhasil membuat folder, THE Portal_SA SHALL menyimpan `gdrive_folder_id` di record Projects dan menerapkan permission sesuai ketentuan di Requirement 5
6. IF Folder_Provisioner gagal membuat folder setelah assignment, THEN THE Portal_SA SHALL tetap mempertahankan status "Assigned", menampilkan badge "Folder Pending" pada project card, dan melakukan retry otomatis maksimal 3 kali dengan interval 30 detik

---

### Requirement 5: Google Drive Folder Auto-Provisioning

**User Story:** Sebagai SA, saya ingin folder proyek di Google Drive sudah otomatis tersedia saat saya ditugaskan, agar saya bisa langsung bekerja tanpa setup manual.

#### Acceptance Criteria

1. WHEN proyek berstatus "Assigned", THE Folder_Provisioner SHALL membuat folder master di Google Drive dengan nama format `[Customer_Name] - [Project_Name]`
2. WHEN folder master dibuat, THE Folder_Provisioner SHALL membuat 3 subfolder: "Inventory", "Diagram", dan "Solutions"
3. WHEN folder master dan seluruh subfolder berhasil dibuat, THE Folder_Provisioner SHALL menyimpan `gdrive_folder_id` dari folder master ke field di tabel Projects
4. WHEN folder master dan subfolder berhasil dibuat, THE Folder_Provisioner SHALL set permission Editor pada folder master (inherited ke seluruh subfolder) untuk SA yang ditugaskan dan Lead_SA, serta permission Viewer untuk Sales pada subfolder "Inventory" saja tanpa akses ke subfolder lain
5. IF Google Drive API mengembalikan error saat pembuatan folder, THEN THE Folder_Provisioner SHALL melakukan retry maksimal 3 kali dengan interval 5 detik antar percobaan dan mencatat setiap error di application log
6. IF seluruh retry gagal (3 kali percobaan habis), THEN THE Folder_Provisioner SHALL menandai proyek dengan flag "Provisioning Failed", mengirim notifikasi in-app ke Lead_SA, dan mempertahankan status proyek "Assigned" agar bisa di-trigger ulang
7. IF Customer_Name atau Project_Name mengandung karakter yang tidak valid untuk nama folder Google Drive (misalnya: `/`, `\`, `*`, `?`, `"`), THEN THE Folder_Provisioner SHALL mengganti karakter tersebut dengan underscore (`_`) sebelum membuat folder

---

### Requirement 6: DQ Number Input dan Document Gating (Simplified MVP)

**User Story:** Sebagai Sales, saya ingin bisa menginput DQ Number kapan saja, agar dokumen yang sudah siap bisa dirilis oleh sistem.

#### Acceptance Criteria

1. WHEN Sales menginput DQ Number pada proyek yang berstatus "Assigned" atau lebih, THE Portal_SA SHALL menyimpan nilai `dq_number` di record Projects dan mengubah status menjadi "Ready"
2. WHILE proyek belum memiliki DQ Number, THE Portal_SA SHALL menampilkan badge "Menunggu DQ" pada project card di dashboard
3. WHEN DQ Number sudah diinput dan dokumen berstatus "Reviewed", THE Portal_SA SHALL menampilkan link GDrive dokumen kepada Sales
4. WHILE DQ Number belum diinput, THE Portal_SA SHALL menyembunyikan link GDrive folder "Solutions" dari tampilan Sales
5. IF DQ Number diinput dengan format yang tidak valid (format valid: alfanumerik, panjang 5-20 karakter, boleh mengandung tanda hubung), THEN THE Portal_SA SHALL menampilkan pesan error "Format DQ Number tidak valid" dan menolak input
6. WHEN DQ Number sudah tersimpan pada record proyek, THE Portal_SA SHALL mencegah perubahan atau penghapusan DQ Number oleh Sales (hanya Lead_SA yang boleh mengedit DQ Number yang sudah tersimpan)

---

### Requirement 7: Document Tracking

**User Story:** Sebagai SA, saya ingin bisa melacak status deliverables proyek (PropTek, BOQ, Mandays), agar saya dan Lead SA tahu progres pengerjaan.

#### Acceptance Criteria

1. THE Portal_SA SHALL menampilkan daftar dokumen per proyek dengan kolom: tipe dokumen, status (Draft/Reviewed/Final), dan link GDrive
2. WHEN SA membuat entry dokumen baru, THE Portal_SA SHALL menerima input: tipe dokumen (dari daftar yang didukung), link GDrive, dan catatan opsional (maksimal 500 karakter), lalu menyimpan record di tabel Documents dengan status awal "Draft" dan timestamp pembuatan
3. WHEN SA mengubah status dokumen, THE Portal_SA SHALL mencatat timestamp perubahan status dan user yang mengubah di record Documents untuk setiap transisi status (Draft→Reviewed, Reviewed→Final)
4. THE Portal_SA SHALL mendukung tipe dokumen: PropTek, BOQ, Mandays, MoM, dan RFP
5. THE Portal_SA SHALL menerapkan alur transisi status dokumen secara berurutan: Draft → Reviewed → Final, tanpa memperbolehkan lompatan status (Draft langsung ke Final)
6. WHILE dokumen berstatus "Final", THE Portal_SA SHALL mencegah perubahan status oleh SA dan menampilkan indikasi bahwa hanya Lead_SA yang dapat mengubah status dokumen tersebut
7. IF SA mencoba mengubah status dokumen yang berstatus "Final", THEN THE Portal_SA SHALL menampilkan pesan error yang menjelaskan bahwa perubahan hanya dapat dilakukan oleh Lead_SA

---

### Requirement 8: Activity Log dan AI Note Polishing

**User Story:** Sebagai SA, saya ingin mencatat aktivitas harian saya pada proyek dan mendapatkan bantuan AI untuk merapikan catatan, agar project story terdokumentasi dengan baik.

#### Acceptance Criteria

1. WHEN SA membuat activity log baru, THE Activity_Logger SHALL menerima input: project ID, subtask category, durasi (jam, dalam rentang 0.25 hingga 24 dengan kelipatan 0.25), dan raw notes (teks bebas, maksimal 5000 karakter)
2. IF SA mensubmit activity log dengan field wajib kosong atau durasi di luar rentang 0.25–24 jam, THEN THE Activity_Logger SHALL menampilkan pesan validasi pada field yang tidak valid dan mencegah penyimpanan
3. WHEN raw notes disubmit, THE Activity_Logger SHALL mengirim teks ke LLM_Provider untuk di-polish menjadi structured format JSON yang berisi dua bagian: "discussion_points" (daftar poin diskusi) dan "action_items" (daftar item aksi dengan deskripsi dan PIC jika tersebut dalam notes)
4. WHEN LLM_Provider mengembalikan hasil, THE Activity_Logger SHALL menyimpan `raw_notes` dan `ai_polished_notes` (format JSON) ke tabel ActivityLogs
5. THE Portal_SA SHALL menampilkan project story sebagai timeline aktivitas yang bisa difilter berdasarkan subtask category dan rentang tanggal, dengan pagination maksimal 20 entry per halaman
6. IF LLM_Provider gagal memproses notes, THEN THE Activity_Logger SHALL tetap menyimpan raw_notes dan menandai `ai_polished_notes` sebagai null, serta menampilkan tombol "Polish Ulang" pada entry tersebut agar SA bisa memicu ulang proses polishing
7. THE Activity_Logger SHALL mendukung subtask category: Meeting Pre-Sales, Create PropTek, Create BOQ, Peer Review, Internal Discussion, dan Customer Workshop

---

### Requirement 9: Dashboard dan Project Status Workflow

**User Story:** Sebagai pengguna Portal SA (Sales, SA, Lead SA), saya ingin melihat dashboard yang menampilkan overview proyek sesuai role saya, agar saya bisa memantau status terkini.

#### Acceptance Criteria

1. WHEN Sales login, THE Portal_SA SHALL menampilkan dashboard berisi daftar proyek yang disubmit oleh Sales tersebut dengan informasi per proyek: nama proyek, nama customer, status terkini, dan tanggal terakhir perubahan status
2. WHEN SA login, THE Portal_SA SHALL menampilkan dashboard berisi daftar proyek yang ditugaskan kepada SA tersebut dengan informasi per proyek: nama proyek, nama customer, status, dan progres dokumen berupa rasio jumlah dokumen berstatus "Final" terhadap total dokumen proyek tersebut
3. WHEN Lead_SA login, THE Portal_SA SHALL menampilkan dashboard berisi semua proyek dengan status selain "Closed-Win", "Handover Complete", dan "Lost", antrian proyek berstatus "Pending Assignment", dan ringkasan utilisasi SA berupa jumlah proyek aktif yang ditangani per masing-masing SA
4. THE Portal_SA SHALL menerapkan workflow status proyek dengan transisi valid sebagai berikut: New → Pending Assignment → Assigned → Ready → Closed-Win → Handover Complete, dan status "Lost" hanya dapat diterapkan oleh Lead_SA dari status manapun kecuali "Handover Complete"
5. IF pengguna mencoba mengubah status proyek ke status yang bukan transisi valid berikutnya dalam workflow, THEN THE Portal_SA SHALL menolak perubahan dan menampilkan pesan error yang menunjukkan transisi yang diperbolehkan dari status saat ini
6. WHEN status proyek berubah, THE Portal_SA SHALL mencatat perubahan status beserta timestamp, status sebelumnya, status baru, dan user yang mengubah di audit log
7. WHEN Lead_SA mengakses dashboard, THE Portal_SA SHALL menampilkan tabel utilisasi SA per bulan yang menunjukkan total jam kerja (dari activity logs) setiap SA per bulan dalam tahun terpilih, dengan opsi filter per tahun dan per individu SA, serta baris ringkasan total jam kerja semua SA per bulan

---

### Requirement 10: Docker Deployment dan Portabilitas

**User Story:** Sebagai developer/ops, saya ingin aplikasi Portal SA bisa di-deploy menggunakan Docker di environment manapun, agar portabel dan konsisten antar environment (dev, staging, production).

#### Acceptance Criteria

1. THE Container_Orchestrator SHALL menyediakan file `docker-compose.yml` yang mendefinisikan minimal 3 service: frontend (Next.js), backend (FastAPI), dan database (PostgreSQL)
2. THE Container_Orchestrator SHALL memuat semua konfigurasi sensitif (API keys, OAuth credentials, database password) melalui environment variables, bukan hardcoded di source code
3. WHEN `docker-compose up` dijalankan pada mesin dengan Docker Engine 20.10+ dan Docker Compose V2+ terinstall, THE Container_Orchestrator SHALL menjalankan seluruh service dengan dependency order (database → backend → frontend) dan mencapai kondisi siap pakai (semua service merespons health check dengan status healthy dan frontend dapat diakses via browser) dalam waktu kurang dari 120 detik setelah image ter-build
4. THE Container_Orchestrator SHALL menyediakan named volume mount untuk data PostgreSQL agar data persisten antar restart container
5. THE Container_Orchestrator SHALL menyediakan health check endpoint pada path `/health` di backend service yang merespons dalam waktu kurang dari 5 detik dengan HTTP 200 dan body JSON berisi field `database` (bernilai "healthy" atau "unhealthy") serta field `api` (bernilai "healthy" atau "unhealthy")
6. THE Container_Orchestrator SHALL menyertakan Dockerfile terpisah untuk frontend dan backend dengan multi-stage build sehingga ukuran final image masing-masing tidak melebihi 500MB
7. THE Container_Orchestrator SHALL mengekspos port 3000 untuk frontend dan port 8000 untuk backend ke host machine, serta menyediakan file `.env.example` yang mendokumentasikan seluruh environment variables yang diperlukan beserta nilai default untuk environment development
8. IF salah satu service gagal start atau health check mengembalikan status unhealthy, THEN THE Container_Orchestrator SHALL menerapkan restart policy `on-failure` dengan maksimal 3 kali restart per service

---

### Requirement 11: API Design dan Data Validation

**User Story:** Sebagai developer frontend, saya ingin backend menyediakan REST API yang terdokumentasi dan memiliki validasi input yang konsisten, agar integrasi frontend-backend efisien.

#### Acceptance Criteria

1. THE Portal_SA SHALL menyediakan REST API dengan format response JSON yang konsisten: `{ "status": "success|error", "data": {...}, "message": "..." }` untuk seluruh endpoint termasuk error response
2. THE Portal_SA SHALL memvalidasi semua request body menggunakan schema validation (Pydantic) sebelum memproses request
3. IF validasi request body gagal, THEN THE Portal_SA SHALL mengembalikan HTTP 422 dengan response body mengikuti format standar dimana field `data` berisi array of objects yang masing-masing mencantumkan nama field dan alasan kegagalan validasi
4. THE Portal_SA SHALL meng-generate dokumentasi API otomatis melalui endpoint `/docs` (Swagger UI) dan `/redoc`
5. THE Portal_SA SHALL menerapkan rate limiting 100 request per menit per user yang dihitung berdasarkan authenticated user ID
6. IF user melebihi batas rate limiting, THEN THE Portal_SA SHALL mengembalikan HTTP 429 dengan response body mengikuti format standar dan menyertakan header `Retry-After` yang menunjukkan jumlah detik sebelum user dapat mengirim request kembali
7. IF request diterima tanpa token autentikasi yang valid, THEN THE Portal_SA SHALL mengembalikan HTTP 401 dengan response body mengikuti format standar dan field `message` yang menjelaskan alasan penolakan (token tidak ada, expired, atau invalid)

---

### Requirement 12: PWA Capability

**User Story:** Sebagai SA yang mobile, saya ingin mengakses Portal SA dari perangkat mobile dengan pengalaman seperti native app, agar saya bisa update activity log dari mana saja.

#### Acceptance Criteria

1. THE Portal_SA SHALL menyediakan Web App Manifest dengan field wajib: `name`, `short_name`, `start_url`, `display` (bernilai "standalone"), `icons` (minimal ukuran 192x192px dan 512x512px), dan `theme_color`, sehingga browser menampilkan prompt instalasi ke home screen
2. THE Portal_SA SHALL mengimplementasikan Service Worker yang meng-cache halaman statis (dashboard, navigation shell, dan form activity log) menggunakan cache-first strategy, sehingga halaman-halaman tersebut dapat dimuat dalam waktu kurang dari 3 detik pada koneksi 3G (RTT 300ms, throughput 400kbps)
3. WHEN pengguna mengakses Portal_SA dari mobile browser, THE Portal_SA SHALL menampilkan layout responsive untuk layar berukuran 320px hingga 1440px tanpa horizontal scroll, dengan touch target minimal 44x44px, dan teks body minimal 16px
4. THE Portal_SA SHALL mencapai skor Lighthouse PWA minimal 80 dari 100
5. IF pengguna mensubmit activity log saat perangkat offline atau koneksi terputus, THEN THE Portal_SA SHALL menyimpan data submission secara lokal dan melakukan sinkronisasi otomatis ke server saat koneksi kembali tersedia, dengan indikator visual status "Menunggu Sinkronisasi" pada entry yang belum tersinkron

---

### Requirement 13: Google Calendar Sync dan Activity Mapping

**User Story:** Sebagai SA, saya ingin menarik jadwal dari Google Calendar ke Portal SA dan memetakan event ke proyek tertentu, agar pencatatan aktivitas harian otomatis terhubung dengan project story.

#### Acceptance Criteria

1. WHEN SA mengklik tombol "Sync Calendar" pada halaman Activity, THE Portal_SA SHALL mengambil event dari Google Calendar API untuk rentang waktu 7 hari terakhir dan 7 hari ke depan, dengan batas maksimal 200 event, dan menampilkan jumlah event yang berhasil diambil sebagai konfirmasi
2. WHEN event berhasil diambil, THE Portal_SA SHALL menampilkan daftar event dengan judul, waktu mulai, waktu selesai, dan durasi (dalam jam) di panel Activity Mapping, diurutkan berdasarkan waktu mulai descending, dengan event all-day ditampilkan terpisah dengan durasi default 8 jam
3. WHEN SA memilih event dan memetakannya ke proyek tertentu, THE Activity_Logger SHALL membuat record ActivityLog dengan `gcal_event_id`, `id_project`, dan `duration_hours` (presisi 2 desimal, rentang 0.01–24.00) yang terisi otomatis dari data event
4. IF SA mencoba memetakan event yang sudah dipetakan ke proyek lain, THEN THE Portal_SA SHALL menampilkan pesan error yang menyebutkan nama proyek tujuan mapping yang sudah ada dan mencegah pembuatan record duplikat
5. WHERE Portal_SA di-deploy di environment dengan public endpoint, THE Portal_SA SHALL menyediakan konfigurasi Google Calendar webhook melalui environment variable (`GCAL_WEBHOOK_ENDPOINT`) untuk menerima push notification saat event dibuat atau diubah
6. IF Google Calendar API mengembalikan error atau tidak merespons dalam 15 detik, THEN THE Portal_SA SHALL menampilkan pesan error yang menyebutkan jenis kegagalan (timeout atau API error) dan mempertahankan seluruh data mapping yang sudah tersimpan sebelumnya

---

### Requirement 14: Email Notification via Gmail API

**User Story:** Sebagai pengguna Portal SA, saya ingin menerima notifikasi email otomatis untuk event penting (assignment, status update, eskalasi SLA), agar saya tidak melewatkan informasi kritis.

#### Acceptance Criteria

1. THE Portal_SA SHALL menyediakan notification service yang mencatat semua trigger notifikasi ke dalam tabel NotificationLogs dengan field: event_type, recipient_user_id, channel (in-app/email), status (pending/sent/failed/read), timestamp, dan reference_id (project atau document terkait)
2. WHEN event notifikasi terjadi (assignment, status change, SLA warning), THE Portal_SA SHALL menampilkan notifikasi in-app dalam waktu maksimal 5 detik kepada user penerima sesuai mapping berikut: assignment → SA yang ditugaskan, status change → Sales pemilik proyek dan SA terkait, SLA warning H+3 → Sales terkait, eskalasi H+5 → Sales Manager
3. WHERE Gmail API credentials sudah dikonfigurasi, THE Portal_SA SHALL mengirim email notifikasi menggunakan Gmail API dengan template HTML untuk trigger berikut: penugasan SA baru, dokumen siap review, peringatan SLA DQ Number (H+3), dan eskalasi ke Sales Manager (H+5)
4. WHEN email dikirim, THE Portal_SA SHALL mencatat status pengiriman (sent/failed) dan timestamp di NotificationLogs
5. IF pengiriman email gagal karena error sementara (timeout, rate limit), THEN THE Portal_SA SHALL melakukan retry maksimal 3 kali dengan interval 30 detik dan mencatat setiap percobaan beserta error detail di NotificationLogs
6. IF Gmail API tidak tersedia atau belum dikonfigurasi, THEN THE Portal_SA SHALL tetap berfungsi normal dengan notifikasi in-app saja tanpa menampilkan error kepada pengguna (graceful fallback)
7. THE Portal_SA SHALL menyediakan halaman Notification Center yang menampilkan riwayat notifikasi pengguna dengan status read/unread, diurutkan dari terbaru, dengan pagination 20 item per halaman
8. WHEN pengguna mengklik notifikasi di Notification Center, THE Portal_SA SHALL menandai notifikasi tersebut sebagai "read" dan mengarahkan pengguna ke halaman terkait (detail proyek atau dokumen)

---

### Requirement 15: RAG Template Recommendation

**User Story:** Sebagai SA, saya ingin mendapatkan rekomendasi template dan referensi dokumen dari proyek serupa sebelumnya saat membuat deliverables, agar saya bisa bekerja lebih efisien dengan memanfaatkan knowledge base yang sudah ada.

#### Acceptance Criteria

1. WHEN SA membuka halaman pembuatan dokumen baru (PropTek, BOQ, atau HLD), THE Portal_SA SHALL menampilkan panel "Referensi Serupa" di sidebar
2. WHEN panel Referensi Serupa dimuat, THE Scoring_Engine SHALL melakukan pencarian berdasarkan `use_case_tags` proyek saat ini terhadap metadata proyek-proyek Closed-Win sebelumnya, dengan kriteria kecocokan minimal 1 tag yang sama antara proyek saat ini dan proyek referensi
3. THE Portal_SA SHALL menampilkan maksimal 5 rekomendasi dokumen serupa, diurutkan berdasarkan jumlah tag yang cocok (descending), dengan informasi per item: nama proyek, tipe dokumen, use case tags, dan link GDrive
4. WHEN SA mengklik rekomendasi, THE Portal_SA SHALL membuka link GDrive dokumen tersebut di tab baru
5. WHERE LLM_Provider dengan embedding capability tersedia, THE Scoring_Engine SHALL melakukan semantic search menggunakan vector similarity pada deskripsi proyek dengan minimum similarity score 0.7, dan menggabungkan hasilnya dengan keyword matching untuk menghasilkan ranking rekomendasi akhir
6. IF tidak ada proyek Closed-Win dengan minimal 1 tag yang sama, THEN THE Portal_SA SHALL menampilkan pesan "Belum ada referensi serupa" pada panel Referensi
7. IF proyek saat ini belum memiliki `use_case_tags` (belum melalui BANT scoring), THEN THE Portal_SA SHALL menampilkan pesan "Rekomendasi akan tersedia setelah scoring selesai" pada panel Referensi dan menonaktifkan fitur pencarian

---

### Requirement 16: SLA DQ Number dengan Auto-Lock/Unlock

**User Story:** Sebagai Lead SA, saya ingin sistem otomatis mengontrol akses dokumen berdasarkan SLA DQ Number (5 hari), agar Sales termotivasi untuk segera memasukkan DQ Number dan proses tidak terhambat.

#### Acceptance Criteria

1. WHEN proyek berstatus "Assigned" dan DQ Number belum diinput, THE Portal_SA SHALL menjalankan SLA_Timer yang menghitung hari kalender (termasuk weekend dan hari libur) sejak tanggal assignment
2. WHEN SLA_Timer mencapai hari ke-3 (H+3) tanpa DQ Number, THE Portal_SA SHALL mengirim notifikasi reminder in-app kepada Sales yang bersangkutan dan mengirim email reminder jika Gmail API aktif
3. WHEN SLA_Timer mencapai hari ke-5 (H+5) tanpa DQ Number, THE Portal_SA SHALL mengirim notifikasi eskalasi in-app dan email (jika Gmail API aktif) ke Sales Manager yang dikonfigurasi pada level tim Sales, dan mengubah permission folder "Solutions" di GDrive menjadi "No Access" untuk Sales (auto-lock)
4. IF Google Drive API mengembalikan error saat proses auto-lock atau auto-unlock, THEN THE Portal_SA SHALL melakukan retry maksimal 3 kali dengan interval 5 detik dan mencatat error di application log, serta menampilkan status "Lock Pending" atau "Unlock Pending" pada project card hingga operasi berhasil
5. WHEN DQ Number diinput sebelum auto-lock terjadi (sebelum H+5), THE Portal_SA SHALL menghentikan SLA_Timer dan mengubah status proyek menjadi "Ready" tanpa memicu eskalasi
6. WHEN DQ Number diinput setelah auto-lock terjadi, THE Portal_SA SHALL mengembalikan permission folder "Solutions" menjadi Viewer untuk Sales (auto-unlock), menghentikan SLA_Timer, dan mencatat event unlock di audit log beserta durasi keterlambatan dalam hari
7. THE Portal_SA SHALL menampilkan indikator visual countdown SLA pada project card: badge hijau untuk 0-2 hari, badge kuning untuk 3-4 hari, dan badge merah untuk 5 hari atau lebih
8. WHILE proyek dalam status auto-lock, THE Portal_SA SHALL menampilkan banner peringatan pada halaman detail proyek yang menyatakan bahwa akses folder Solutions dikunci karena DQ Number belum diinput melebihi batas 5 hari, dan menginstruksikan Sales untuk menginput DQ Number untuk membuka akses kembali

---

### Requirement 17: Post-Sales PMO Handover Automation

**User Story:** Sebagai SA, saya ingin sistem otomatis memfasilitasi handover ke tim PMO dan Delivery setelah proyek Closed-Win, agar transisi berjalan lancar tanpa manual follow-up.

#### Acceptance Criteria

1. WHEN status proyek diubah menjadi "Closed-Win", THE Portal_SA SHALL menampilkan modal blocking kepada SA yang berisi instruksi untuk membuat dokumen HLD, dimana SA tidak dapat melakukan navigasi ke halaman lain pada proyek tersebut sampai modal di-acknowledge dengan klik tombol "Buat HLD"
2. WHEN SA mensubmit dokumen HLD dengan status "Final" pada proyek berstatus "Closed-Win", THE Portal_SA SHALL memicu proses handover otomatis yang terdiri dari: provisioning permission folder dan pengiriman notifikasi
3. WHEN proses handover dimulai, THE Folder_Provisioner SHALL membuat subfolder "Final_Deliverables" di dalam folder "Solutions" (jika belum ada) dan menambahkan permission Viewer pada folder "Solutions" beserta subfolder "Final_Deliverables" kepada PMO Lead dan Delivery Lead yang dikonfigurasi
4. WHEN permission berhasil diubah, THE Portal_SA SHALL mengirim notifikasi handover (in-app dan email jika Gmail API aktif) kepada PMO Lead dan Delivery Lead berisi: nama proyek, nama customer, link folder Solutions, daftar tipe dokumen berstatus "Final", dan use_case_tags proyek
5. WHEN permission folder berhasil diubah DAN notifikasi handover berhasil dikirim (minimal in-app), THE Portal_SA SHALL mengubah status proyek menjadi "Handover Complete" dan mencatat di audit log: timestamp, user yang memicu, PMO Lead email, dan Delivery Lead email
6. IF PMO Lead atau Delivery Lead belum dikonfigurasi di sistem, THEN THE Portal_SA SHALL menampilkan form input untuk Lead_SA mengisi email PMO Lead dan Delivery Lead dengan validasi format email, sebelum handover bisa diproses
7. IF Google Drive API mengembalikan error saat mengubah permission folder dalam proses handover, THEN THE Folder_Provisioner SHALL melakukan retry maksimal 3 kali dengan interval 5 detik, dan jika semua retry gagal, menandai handover sebagai "Handover Failed" serta mengirim notifikasi error kepada SA dan Lead_SA

---

### Requirement 18: LLM Provider Abstraction (Multi-Provider Support)

**User Story:** Sebagai admin/developer Portal SA, saya ingin bisa mengganti LLM provider (Gemini, OpenAI, Anthropic, AWS Bedrock, dll.) melalui konfigurasi API endpoint, agar aplikasi tidak tightly-coupled ke satu vendor AI dan bisa disesuaikan dengan kebutuhan atau budget.

#### Acceptance Criteria

1. THE LLM_Provider SHALL menyediakan abstraction layer berupa interface yang mendefinisikan operasi standar: text completion, document parsing (multimodal), dan text structuring
2. THE LLM_Provider SHALL mendukung konfigurasi provider melalui environment variables: `LLM_PROVIDER` (nama provider), `LLM_API_ENDPOINT` (base URL), `LLM_API_KEY` (credential), dan `LLM_MODEL_NAME` (model yang digunakan)
3. THE LLM_Provider SHALL menyediakan adapter bawaan untuk Google Gemini API sebagai default provider
4. WHEN admin mengubah konfigurasi provider di environment variables, THE LLM_Provider SHALL mendeteksi perubahan dan beralih ke provider baru dalam waktu maksimal 30 detik tanpa perubahan kode aplikasi dan tanpa restart container (hot-reload config)
5. THE LLM_Provider SHALL menstandarkan format request dan response internal sehingga Scoring_Engine dan Activity_Logger tidak perlu mengetahui detail implementasi provider spesifik, dengan response minimal mengandung: status operasi (success/error), hasil teks terstruktur, dan metadata (model yang digunakan, token usage)
6. IF LLM provider mengembalikan error atau format response tidak sesuai expected schema, THEN THE LLM_Provider SHALL melakukan retry dengan exponential backoff dimulai dari 1 detik (interval: 1s, 2s, 4s) maksimal 3 kali, dengan timeout per request 30 detik, dan mencatat error detail di application log
7. THE LLM_Provider SHALL mendukung penambahan adapter provider baru melalui implementasi interface standar tanpa mengubah kode modul yang sudah ada (Open-Closed Principle)
8. IF nilai `LLM_PROVIDER` tidak sesuai dengan adapter yang tersedia atau `LLM_API_ENDPOINT` tidak dapat dijangkau saat inisialisasi, THEN THE LLM_Provider SHALL mencatat error di application log dan tetap menggunakan konfigurasi provider terakhir yang valid (fallback to last known good config)
9. IF semua retry gagal setelah 3 percobaan, THEN THE LLM_Provider SHALL mengembalikan error response terstandar ke modul pemanggil (Scoring_Engine atau Activity_Logger) dengan indikasi jenis kegagalan (timeout, authentication error, atau invalid response) agar modul pemanggil dapat menangani sesuai kebutuhannya

---

### Requirement 19: UI/UX Design System — Minimalis dan Gegas

**User Story:** Sebagai pengguna Portal SA, saya ingin tampilan aplikasi yang bersih, minimalis, dan responsif dengan interaksi yang cepat (gegas), agar pengalaman kerja harian saya efisien dan tidak terganggu oleh UI yang lambat atau berantakan.

#### Acceptance Criteria

1. THE Portal_SA SHALL menggunakan font **Open Sans** sebagai typeface utama untuk seluruh teks UI (heading, body, label, dan button)
2. THE Portal_SA SHALL menerapkan design language minimalis dengan ketentuan: minimum padding 16px antar section, type scale ratio yang konsisten (heading minimal 1.25x lebih besar dari body), dan maksimal 5 elemen aksi (button/link) yang terlihat per layar tanpa scroll
3. THE Portal_SA SHALL menggunakan palet warna netral (putih, abu-abu, hitam) sebagai base dengan satu accent color untuk elemen aksi utama (button CTA, link aktif, badge status)
4. THE Portal_SA SHALL memastikan setiap interaksi UI (klik tombol, navigasi halaman, buka modal) memberikan feedback visual berupa perubahan state elemen (disabled state, highlight, atau loading indicator) dalam waktu kurang dari 100ms (perceived responsiveness)
5. WHEN data dari API belum tersedia dalam 200ms setelah request dimulai, THE Portal_SA SHALL menampilkan loading skeleton yang menyerupai layout konten final (bukan spinner) hingga data selesai dimuat
6. THE Portal_SA SHALL menggunakan transisi dan animasi yang berdurasi maksimal 200ms dan hanya diterapkan pada perubahan state fungsional (buka/tutup panel, navigasi halaman, tampil/hilang elemen), tanpa animasi dekoratif yang tidak terkait aksi pengguna
7. THE Portal_SA SHALL menerapkan layout yang konsisten: sidebar navigation tetap (collapsible, lebar 240px saat terbuka dan 64px saat collapsed), main content area minimal 60% viewport width, dan header dengan tinggi maksimal 64px
8. WHEN pengguna melakukan aksi utama (submit form, assign project, update status) dan aksi berhasil, THE Portal_SA SHALL menampilkan konfirmasi sukses berupa toast notification yang non-blocking dan auto-dismiss dalam 3 detik
9. IF aksi utama (submit form, assign project, update status) gagal, THEN THE Portal_SA SHALL menampilkan toast notification error yang non-blocking, berwarna berbeda dari toast sukses, dan auto-dismiss dalam 5 detik, disertai pesan yang menjelaskan penyebab kegagalan
10. WHILE Portal_SA dimuat pertama kali (initial page load), THE Portal_SA SHALL menampilkan first contentful paint dalam waktu kurang dari 1.5 detik pada koneksi 4G standar (RTT 50ms, throughput 10 Mbps)
