FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Debugging step: List contents of .next/standalone
RUN ls -la /app/.next/standalone

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Debugging step: List contents of /app
RUN ls -la /app

USER nextjs

EXPOSE 8081

ENV PORT 8081

# Ensure server.js is copied correctly and change ownership during copy
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone/server.js ./

# Set the working directory explicitly
WORKDIR /app

# Set correct permissions for server.js
RUN chmod 755 /app/server.js

# Debugging step: List contents of /app right before CMD
RUN ls -la /app


# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/next-config-js/output
CMD HOSTNAME="0.0.0.0" node server.js