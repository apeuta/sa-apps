#!/bin/bash
# ============================================
# Script Deployment Portal SA MVP
# ============================================
# Gunakan script ini untuk deploy/update aplikasi di VM Ubuntu.
# Workflow: git pull → docker compose down → docker compose up -d --build
#
# Prasyarat:
#   - Docker Engine 20.10+ dan Docker Compose V2+ terinstall
#   - File .env sudah dikonfigurasi (cp .env.example .env)
#   - User memiliki akses ke docker group
#
# Penggunaan:
#   chmod +x deploy.sh
#   ./deploy.sh
# ============================================

set -e

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fungsi untuk log dengan timestamp
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Pindah ke direktori script (root project)
cd "$(dirname "$0")"

log "=== Memulai deployment Portal SA MVP ==="

# Cek prasyarat
log "Memeriksa prasyarat..."

if ! command -v docker &> /dev/null; then
    error "Docker tidak ditemukan. Install terlebih dahulu."
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose V2 tidak ditemukan. Install terlebih dahulu."
fi

if [ ! -f ".env" ]; then
    error "File .env tidak ditemukan. Jalankan: cp .env.example .env dan isi konfigurasi."
fi

# Step 1: Pull perubahan terbaru dari repository
log "Step 1/4: Menarik perubahan terbaru dari Git..."
if git rev-parse --is-inside-work-tree &> /dev/null; then
    git pull origin "$(git branch --show-current)" || warn "Git pull gagal, melanjutkan dengan kode lokal."
else
    warn "Bukan git repository, skip git pull."
fi

# Step 2: Hentikan service yang sedang berjalan
log "Step 2/4: Menghentikan service yang sedang berjalan..."
docker compose down --remove-orphans || true

# Step 3: Build dan jalankan service
log "Step 3/4: Build dan menjalankan service..."
docker compose up -d --build

# Step 4: Verifikasi deployment
log "Step 4/4: Memverifikasi deployment..."
echo ""

# Tunggu beberapa detik agar service startup
sleep 5

# Cek status container
log "Status container:"
docker compose ps

echo ""
log "=== Deployment selesai ==="
log "Frontend : http://localhost:${FRONTEND_PORT:-3000}"
log "Backend  : http://localhost:${BACKEND_PORT:-8000}"
log "API Docs : http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
log "Gunakan 'docker compose logs -f' untuk melihat log realtime."
log "Gunakan 'docker compose down' untuk menghentikan semua service."
