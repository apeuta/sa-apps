#!/bin/bash
# ============================================
# Build & Push Frontend Image ke GitHub Container Registry
# ============================================
# Penggunaan: ./scripts/build-and-push-frontend.sh
# Prasyarat: Docker Desktop running, sudah login ke ghcr.io
# ============================================

set -e

GITHUB_USERNAME="apeuta"
IMAGE_NAME="ghcr.io/${GITHUB_USERNAME}/sa-portal-frontend"
IMAGE_TAG="latest"

echo "🔨 Building frontend image untuk linux/amd64..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:${IMAGE_TAG} ./frontend

echo ""
echo "📤 Pushing ke GitHub Container Registry..."
docker push ${IMAGE_NAME}:${IMAGE_TAG}

echo ""
echo "✅ Selesai! Image tersedia di: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "📋 Langkah selanjutnya:"
echo "1. Buka Portainer → Stacks → sa-portal → Editor"
echo "2. Ubah baris 'image: sa-portal-frontend:latest' menjadi:"
echo "   image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "3. Klik 'Update the stack'"
