# Mem0 self-hosted dashboard (server/dashboard in mem0ai/mem0) for Railway.
#
# Built from the same upstream release as the API (keep MEM0_VERSION and
# MEM0_SHA256 identical in both Dockerfiles). Follows upstream's
# server/dashboard/Dockerfile: Next.js standalone build with NEXT_PUBLIC_*
# placeholders that upstream's entrypoint.sh replaces with the container's
# real values at start, so the API URL is set by a Railway variable.
ARG MEM0_VERSION=2.2.1
ARG MEM0_SHA256=2d203947596fbbfeaf06e5311c087a6b837566528016013aff15ad2a8a4103c5
ARG NODE_IMAGE=node:22.23.3-alpine3.23

FROM alpine:3.23 AS source
ARG MEM0_VERSION
ARG MEM0_SHA256
RUN apk add --no-cache ca-certificates curl tar && \
    curl -fsSL "https://codeload.github.com/mem0ai/mem0/tar.gz/refs/tags/v${MEM0_VERSION}" -o /tmp/mem0.tgz && \
    echo "${MEM0_SHA256}  /tmp/mem0.tgz" | sha256sum -c - && \
    mkdir /src && \
    tar -xzf /tmp/mem0.tgz -C /src --strip-components=1 "mem0-${MEM0_VERSION}/server/dashboard"

FROM ${NODE_IMAGE} AS base
RUN apk add --no-cache libc6-compat
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS deps
COPY --from=source /src/server/dashboard/package.json /src/server/dashboard/pnpm-lock.yaml /src/server/dashboard/pnpm-workspace.yaml ./
# pnpm version comes from "packageManager" in package.json (via corepack).
RUN corepack enable && pnpm install --frozen-lockfile

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY --from=source /src/server/dashboard/ ./
ENV NEXT_PUBLIC_API_URL=NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_INSTANCE_NAME=NEXT_PUBLIC_INSTANCE_NAME
RUN corepack enable && pnpm build

FROM base AS runner
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=source --chown=nextjs:nodejs /src/server/dashboard/entrypoint.sh /home/nextjs/entrypoint.sh
RUN chmod 0555 /home/nextjs/entrypoint.sh

USER nextjs
EXPOSE 3000
ENTRYPOINT ["/home/nextjs/entrypoint.sh"]
CMD ["node", "server.js"]
