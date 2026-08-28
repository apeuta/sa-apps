# ============================================
# Multi-stage Dockerfile untuk Next.js Frontend
# Target: Node 20 Alpine, image < 500MB
# ============================================

# --- Stage 1: Dependencies ---
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies berdasarkan lockfile
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./
RUN \
    if [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm install --frozen-lockfile; \
    else npm install; \
    fi

# --- Stage 2: Builder ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies dari stage sebelumnya
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build argument untuk API URL (tersedia saat build time)
ARG NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Disable telemetry saat build
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js application
RUN npm run build

# --- Stage 3: Runtime ---
FROM node:20-alpine AS runtime

WORKDIR /app

# Buat user non-root untuk keamanan
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy hanya file yang diperlukan untuk production
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Gunakan user non-root
USER nextjs

# Expose port frontend
EXPOSE 3000

# Environment variables runtime
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1

# Jalankan Next.js standalone server
CMD ["node", "server.js"]
