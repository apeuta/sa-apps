# Portal SA — Solutions Architect Management Platform

Portal SA adalah Progressive Web App (PWA) untuk manajemen proyek pre-sales dan pencatatan aktivitas harian Solutions Architect. Aplikasi ini menggantikan Redmine dengan fitur AI-powered scoring, integrasi Google Workspace, dan deployment Docker yang portabel.

---

## Fitur Utama

| Modul | Deskripsi |
|-------|-----------|
| **Pre-Sales Request** | Sales submit request proyek + file attachment (MoM/RFP) |
| **AI BANT Scoring** | Gemini AI menganalisis dokumen dan menghitung skor BANT (Budget, Authority, Need, Timeline) |
| **Project Assignment** | Lead SA menugaskan SA ke proyek berdasarkan scoring dan workload |
| **GDrive Auto-Provisioning** | Folder proyek otomatis dibuat di Google Drive dengan permission yang tepat |
| **Document Tracking** | Tracking status deliverables (PropTek, BOQ, Mandays, HLD) dengan state machine |
| **DQ Number Gating** | Akses dokumen dikontrol berdasarkan input DQ Number oleh Sales |
| **SLA Timer** | Countdown 5 hari untuk DQ Number dengan auto-lock folder dan eskalasi |
| **Activity Logger** | Pencatatan aktivitas harian + AI note polishing (discussion points & action items) |
| **Calendar Sync** | Sinkronisasi Google Calendar untuk mapping aktivitas ke proyek |
| **Notification** | In-app notification + email (Gmail API) untuk semua event penting |
| **RAG Recommendation** | Rekomendasi template dari proyek Closed-Win serupa |
| **PMO Handover** | Automasi handover folder + notifikasi ke PMO/Delivery setelah Closed-Win |
| **Dashboard per Role** | Tampilan berbeda untuk Sales, SA, dan Lead SA (termasuk utilisasi SA per bulan) |
| **PWA + Offline** | Installable, offline-capable, auto-sync saat kembali online |

---

## Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, Zustand, SWR |
| Backend | FastAPI (Python 3.11+), SQLAlchemy async, Pydantic |
| Database | PostgreSQL 15+ |
| AI | Google Gemini API (via LLM Provider abstraction — multi-provider ready) |
| Auth | Google OAuth 2.0 + JWT |
| Integration | Google Drive API, Google Calendar API, Gmail API |
| Deployment | Docker + Docker Compose |

---

## Struktur Project

```
SA Application/                 # Root aplikasi Portal SA
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routers (endpoints)
│   │   ├── core/              # Config, database, middleware
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   └── main.py            # FastAPI app entry point
│   ├── alembic/               # Database migrations
│   ├── scripts/               # Seed data & utilities
│   ├── tests/                 # Unit tests
│   ├── Dockerfile             # Multi-stage build
│   └── requirements.txt
├── frontend/                   # Next.js PWA frontend
│   ├── src/
│   │   ├── app/               # Pages (App Router)
│   │   ├── components/        # Reusable UI components
│   │   ├── lib/               # API clients, utilities
│   │   └── store/             # Zustand stores
│   ├── public/                # PWA manifest, service worker, icons
│   ├── Dockerfile             # Multi-stage build
│   └── package.json
├── Portal Activity Mapping & Report.pdf  # Dokumen referensi
├── Spesifikasi_Teknis_Portal_SA.md       # Spesifikasi teknis
├── docker-compose.yml          # Orchestration (3 services)
├── deploy.sh                   # Script deployment otomatis
├── .env.example                # Template environment variables
└── README.md
```

---

## Quick Start (Lokal dengan Docker)

```bash
# 1. Clone repo
git clone git@github.com:apeuta/sa-apps.git
cd sa-apps/SA\ Application

# 2. Konfigurasi environment
cp .env.example .env
# Edit .env — isi minimal: POSTGRES_PASSWORD, SECRET_KEY, GOOGLE_CLIENT_ID/SECRET, GEMINI_API_KEY

# 3. Build dan jalankan
docker compose up -d --build

# 4. Verifikasi
curl http://localhost:8000/health
# Output: {"status":"success","data":{"api":"healthy","database":"healthy"}}
```

Akses:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Deployment di Ubuntu VM

### Prasyarat
- Ubuntu 22.04+, minimal 2 vCPU / 4GB RAM / 30GB disk
- Domain atau IP publik (untuk akses dari luar)
- Port 80 dan 443 terbuka di firewall/security group

### Step-by-step

```bash
# 1. Install Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git

# 2. Buat user deployment
sudo adduser sa-portal --gecos ""
sudo usermod -aG docker sa-portal
sudo su - sa-portal

# 3. Clone dan konfigurasi
git clone git@github.com:apeuta/sa-apps.git ~/sa-portal
cd ~/sa-portal
cp .env.example .env
nano .env  # Isi semua credentials

# 4. Jalankan aplikasi
docker compose up -d --build

# 5. Setup Nginx reverse proxy (agar bisa diakses via port 80/443)
# Lihat section "Setup Nginx" di bawah
```

### Setup Nginx (Akses dari Luar VM)

```bash
# Install Nginx
sudo apt-get install -y nginx

# Buat konfigurasi
sudo nano /etc/nginx/sites-available/sa-portal
```

Isi file konfigurasi:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Ganti dengan domain atau IP publik VM

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;  # Untuk file upload max 20MB x 5 files
    }

    # Swagger / ReDoc
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

Aktifkan konfigurasi:

```bash
sudo ln -s /etc/nginx/sites-available/sa-portal /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Setup SSL dengan Let's Encrypt (HTTPS)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Generate SSL certificate (ganti dengan domain Anda)
sudo certbot --nginx -d your-domain.com

# Auto-renewal sudah diatur otomatis oleh certbot
sudo certbot renew --dry-run  # Test renewal
```

### Buka Firewall

```bash
# UFW (Ubuntu default firewall)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
sudo ufw status

# Jika pakai AWS Security Group:
# - Buka Inbound Rule port 80 (HTTP) dan 443 (HTTPS) dari 0.0.0.0/0
# - Port 22 (SSH) dari IP Anda saja
```

### Update .env untuk Produksi

Setelah Nginx dan SSL aktif, update `.env`:

```env
# Ganti localhost dengan domain/IP publik
GOOGLE_REDIRECT_URI=https://your-domain.com/api/v1/auth/callback
NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1
FRONTEND_URL=https://your-domain.com
```

Restart aplikasi:
```bash
docker compose down
docker compose up -d --build
```

---

## Update Deployment

```bash
ssh sa-portal@your-vm-ip
cd ~/sa-portal/SA\ Application
git pull origin main
docker compose down
docker compose up -d --build
docker compose logs -f --tail=50  # Monitor startup
```

Atau gunakan script otomatis:
```bash
./deploy.sh
```

---

## Environment Variables

Lihat `.env.example` untuk daftar lengkap. Yang **wajib** dikonfigurasi:

| Variable | Deskripsi |
|----------|-----------|
| `POSTGRES_PASSWORD` | Password database PostgreSQL |
| `SECRET_KEY` | JWT signing key (random string 32+ karakter) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL |
| `ALLOWED_DOMAINS` | Domain email yang diizinkan login |
| `GEMINI_API_KEY` | Google Gemini API key |
| `NEXT_PUBLIC_API_URL` | URL backend API (dari sisi browser) |

---

## Seed Demo Data

Untuk mengisi data contoh (users, projects, documents, activity logs):

```bash
docker compose exec backend python -m scripts.seed_demo_data
```

Script ini idempotent — aman dijalankan berkali-kali. Data demo mencakup:
- 4 users (Sales, SA, Lead_SA, Admin)
- 5 proyek dengan berbagai status (termasuk DQ Number untuk proyek Ready dan Closed-Win)
- 4 dokumen (PropTek, BOQ)
- 5 activity logs

---

## API Documentation

Setelah aplikasi berjalan:
- **Swagger UI**: `/docs` — Interactive API explorer
- **ReDoc**: `/redoc` — Readable API documentation
- **OpenAPI Spec**: `/openapi.json` — Machine-readable spec

---

## Status

MVP Ready — Semua fitur inti sudah terimplementasi dan siap deploy.

---

## Changelog Terbaru

- **Utilisasi SA per Bulan** — Dashboard Lead SA sekarang menampilkan tabel jam kerja per SA per bulan dengan filter tahun dan per individu
- **DQ Number di Seed Data** — Proyek demo "Ready" dan "Closed-Win" sudah punya DQ Number sejak awal
- **Cleanup Emoji** — Semua emoji dekoratif di UI diganti dengan SVG icons/teks untuk konsistensi tampilan

---

## Kontributor

- Solutions Architect Team
