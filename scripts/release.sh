#!/bin/bash
# ============================================
# Build & Push Backend + Frontend ke GHCR
# ============================================
# Penggunaan:
#   ./scripts/release.sh <version>
#   ./scripts/release.sh v4.81
#   ./scripts/release.sh v4.81 --backend-only
#   ./scripts/release.sh v4.81 --frontend-only
#
# ATURAN PENOMORAN VERSI (WAJIB):
#   Format: vMAJOR.MINOR dengan MINOR selalu DUA digit.
#   - Increment per rilis: +0.01 (mis. v4.81 -> v4.82 -> v4.83 ...).
#   - Saat MINOR mencapai 89 lanjut ke 90 (v4.89 -> v4.90), bukan v4.9.
#   - Saat MINOR mencapai 99 naik major & reset (v4.99 -> v5.00).
#   Contoh valid: v4.81, v4.90, v4.99, v5.00, v5.01
#   Contoh TIDAK valid: v4.9 (minor satu digit), v4.100 (minor tiga digit)
#
# Prasyarat:
#   - Docker Desktop running
#   - Sudah login: echo <TOKEN> | docker login ghcr.io -u aputea --password-stdin
# ============================================

set -e

# --- Konfigurasi ---
GITHUB_USERNAME="apeuta"
BACKEND_IMAGE="ghcr.io/${GITHUB_USERNAME}/sa-portal-backend"
FRONTEND_IMAGE="ghcr.io/${GITHUB_USERNAME}/sa-portal-frontend"
COMPOSE_FILE="docker-compose.portainer.yml"

# --- Parse argumen ---
VERSION=""
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
  case $arg in
    --backend-only)
      BACKEND_ONLY=true
      ;;
    --frontend-only)
      FRONTEND_ONLY=true
      ;;
    v*)
      VERSION="$arg"
      ;;
    *)
      echo "❌ Argumen tidak dikenal: $arg"
      echo "Penggunaan: ./scripts/release.sh <version> [--backend-only|--frontend-only]"
      exit 1
      ;;
  esac
done

if [ -z "$VERSION" ]; then
  echo "❌ Version belum ditentukan."
  echo ""
  echo "Penggunaan: ./scripts/release.sh <version> [--backend-only|--frontend-only]"
  echo ""
  echo "Contoh:"
  echo "  ./scripts/release.sh v4.81              # Build backend + frontend"
  echo "  ./scripts/release.sh v4.81 --backend-only   # Hanya backend"
  echo "  ./scripts/release.sh v4.81 --frontend-only  # Hanya frontend"
  exit 1
fi

# --- Validasi format versi: vMAJOR.MINOR dengan MINOR dua digit ---
# Lihat "ATURAN PENOMORAN VERSI" di header. Minor WAJIB dua digit (00-99).
if ! echo "$VERSION" | grep -Eq '^v[0-9]+\.[0-9]{2}$'; then
  echo "❌ Format versi tidak valid: $VERSION"
  echo ""
  echo "Format wajib: vMAJOR.MINOR dengan MINOR dua digit (contoh: v4.81, v4.90, v5.00)."
  echo "Aturan: increment +0.01 per rilis; v4.89 -> v4.90; v4.99 -> v5.00."
  echo "Contoh tidak valid: v4.9 (minor satu digit), v4.100 (tiga digit)."
  exit 1
fi

# Root directory project (parent dari scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "========================================"
echo "🚀 Release SA Portal — ${VERSION}"
echo "========================================"
echo ""

# --- Cek Docker ---
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker Desktop belum running. Silakan start dulu."
  exit 1
fi

# --- Build Backend ---
if [ "$FRONTEND_ONLY" = false ]; then
  echo "📦 [1/2] Building backend image..."
  docker build --platform linux/amd64 -t "${BACKEND_IMAGE}:${VERSION}" ./backend

  echo "📤 Pushing backend ke GHCR..."
  docker push "${BACKEND_IMAGE}:${VERSION}"

  echo "✅ Backend done: ${BACKEND_IMAGE}:${VERSION}"
  echo ""
else
  echo "⏭️  Skipping backend (--frontend-only)"
  echo ""
fi

# --- Build Frontend ---
if [ "$BACKEND_ONLY" = false ]; then
  echo "📦 [2/2] Building frontend image (no-cache)..."
  docker build --platform linux/amd64 --no-cache -t "${FRONTEND_IMAGE}:${VERSION}" ./frontend

  echo "📤 Pushing frontend ke GHCR..."
  docker push "${FRONTEND_IMAGE}:${VERSION}"

  echo "✅ Frontend done: ${FRONTEND_IMAGE}:${VERSION}"
  echo ""
else
  echo "⏭️  Skipping frontend (--backend-only)"
  echo ""
fi

# --- Update docker-compose.portainer.yml ---
if [ -f "$COMPOSE_FILE" ]; then
  echo "📝 Updating ${COMPOSE_FILE}..."

  if [ "$FRONTEND_ONLY" = false ]; then
    sed -i '' "s|image: ${BACKEND_IMAGE}:.*|image: ${BACKEND_IMAGE}:${VERSION}|" "$COMPOSE_FILE"
    echo "   Backend → ${VERSION}"
  fi

  if [ "$BACKEND_ONLY" = false ]; then
    sed -i '' "s|image: ${FRONTEND_IMAGE}:.*|image: ${FRONTEND_IMAGE}:${VERSION}|" "$COMPOSE_FILE"
    echo "   Frontend → ${VERSION}"
  fi

  echo ""
fi

echo "========================================"
echo "✅ Release ${VERSION} selesai!"
echo "========================================"
echo ""
echo "📋 Langkah selanjutnya:"
echo "1. Commit & push perubahan ${COMPOSE_FILE}:"
echo "   git add ${COMPOSE_FILE} && git commit -m 'chore: bump to ${VERSION}' && git push"
echo ""
echo "2. Deploy di Portainer:"
echo "   - Buka Portainer → Stacks → sa-portal"
echo "   - Pastikan image tag sudah ${VERSION}"
echo "   - Klik 'Update the stack' (Force pull image)"
echo ""
echo "3. Cleanup image lama di local (opsional):"
echo "   docker image prune -f"
echo ""
