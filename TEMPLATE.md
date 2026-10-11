# Mem0 v2 AI Memory Layer: Railway template spec

## Listing

| Field | Value |
|---|---|
| Name | **Mem0 v2 AI Memory Layer** (changed from the LISTINGS_ROUND2 base "Mem0 OpenMemory AI Memory Layer", see below; `v2` = pinned release v2.2.1, project tags use `v`) |
| Description | Persistent memory for AI agents: REST API, dashboard and pgvector storage. (74 chars) |
| Category | AI/ML |
| Tags | mem0, memory, ai-agents, llm, rag, pgvector, embeddings, openai |
| Icon | `https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/mem0.svg` (200 OK) |

**Listing changes and why.** The listing in LISTINGS_ROUND2 promised "OpenMemory" and "MCP-ready". Upstream facts as of 2026-10-11:

- OpenMemory (the MCP server + UI) was removed from the mem0 monorepo on 2026-07-29 (commit `ea2ee07`, "remove OpenMemory from the monorepo", PR #6530). `mem0ai/openmemory` is now an unrelated CLI/TUI for porting coding sessions. The last `mem0/openmemory-mcp` image is from 2025-06.
- The only official Mem0 MCP server is the hosted one for the Mem0 Platform (`mcp.mem0.ai`, docs `platform/mem0-mcp.mdx`); the self-hostable `mem0ai/mem0-mcp` repo is archived.
- The current self-host path is `server/` (FastAPI REST API with auth, API keys, request log) plus `server/dashboard/` (Next.js), backed by Postgres + pgvector.
- External graph stores (Neo4j, Memgraph, Kuzu, Apache AGE) were removed in mem0 v2.0.0 (2026-04-14). Graph-style memory is now built-in entity linking stored in the same vector store, so no Neo4j service exists to add.

So the template ships the official server stack and the description drops "OpenMemory" and "MCP-ready" instead of promising features upstream no longer offers for self-hosting. An MCP bridge to this REST API would be custom code; see Open questions.

## Base market template

- **Base: `mem0-memory-api-pgvector`** "Mem0 Memory API + pgvector" (5 recent projects, 2026-09). Closest to the official stack: REST API + dashboard + pgvector, auth on, CORS limited to the dashboard, history volume. Problems fixed: built from upstream `main` (every redeploy pulls unreviewed code), `pip install` at container start, app tables in the vector database instead of upstream's separate `mem0_app` database, migrations in the start command, API_INTERNAL_URL over the public internet, open setup wizard on a public URL (first visitor becomes admin), telemetry on by default, no request-log pruning, semantic-only search (no `[nlp]` extra).
- `mem0` (11 active, image `mem0/mem0-api-server:latest`, last pushed 2025-09): stale image, `pip install` at start, placeholder `sk-your-openai-api-key` as default, no dashboard. Nothing taken.
- `mem0-self-hosted-1` (`tech-progress/railway-template-mem0`): **no license file (NOASSERTION) → all rights reserved, read only, nothing copied.** It confirmed the same approach (pinned upstream source, app database creation before migrations) which was re-implemented from upstream's own `init-db.sh` and docs.
- No README text was reused.

## Pinned versions

| Service | Image / source | Version | Released | Checked |
|---|---|---|---|---|
| Mem0 API | Dockerfile `services/api`: `python:3.12.15-slim-trixie` + upstream `server/` from tag `v2.2.1` (tarball sha256 `2d203947…4103c5`) + `mem0ai[nlp]==2.2.1` + `en_core_web_sm` 3.8.0 | 2.2.1 | 2026-09-25 | 2026-10-11 |
| Mem0 Dashboard | Dockerfile `services/dashboard`: `node:22.23.3-alpine3.23` + upstream `server/dashboard/` from tag `v2.2.1` (Next.js 15.5.24, pnpm 10.34.2 via corepack) | 2.2.1 | 2026-09-25 | 2026-10-11 |
| Mem0 Log Pruner | same image as Mem0 API | 2.2.1 | | 2026-10-11 |
| Postgres | `pgvector/pgvector:0.8.7-pg17` (upstream compose uses `pgvector/pgvector:pg17`) | pgvector 0.8.7 / PostgreSQL 17 | 2026-10-01 | 2026-10-11 |

Upgrade: set the same `MEM0_VERSION` and `MEM0_SHA256` in both Dockerfiles (`curl -L https://codeload.github.com/mem0ai/mem0/tar.gz/refs/tags/v{version} | sha256sum`), read the server's alembic migrations and the release notes, back up Postgres and the history volume together, redeploy. Alembic runs in the API pre-deploy step.

## Architecture

```
 Browser ── HTTPS ──► Mem0 Dashboard :3000 (Next.js) ──┐ server-side: http://mem0-api.railway.internal:8000
    │                                                   │ (setup status, token refresh)
    └── HTTPS (CORS: dashboard origin only) ──► Mem0 API :8000 (FastAPI, public) ◄── agents / apps (X-API-Key)
                                                   │  pre-deploy: prepare_db → alembic → bootstrap_admin
                                                   │  volume /app/history (SQLite memory history)
                                                   ▼
                                    Postgres + pgvector (volume)
                                    ├─ db "mem0": memories + entity vectors
                                    └─ db "mem0_app": users, api_keys, request_logs, settings
                                                   ▲
                       Mem0 Log Pruner (cron 03:30 UTC daily) ── deletes request_logs older than N days
```

## Services

### Mem0 API

| Setting | Value |
|---|---|
| Source | repo `baranberkay96/mem0-railway`, root `/services/api` (Dockerfile) |
| Pre-deploy | `cd /app && python railway/prepare_db.py && alembic upgrade head && python railway/bootstrap_admin.py` (timeout 600 s) |
| Start | image CMD: `uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips '*'` |
| Healthcheck | `/docs` (OpenAPI UI, unauthenticated; the app imports and connects to pgvector before serving), timeout 300 s |
| Public domain | yes, port 8000 (agents and the browser dashboard call it) |
| Volume | `/app/history` (SQLite history + telemetry state) |
| Restart | ON_FAILURE, 10 |

Files in `services/api/`:
- `Dockerfile`: downloads the tagged upstream source, verifies the checksum, installs upstream `requirements.txt` plus `mem0ai[nlp]==2.2.1` (pins the library to the server's release; upstream's file only says `mem0ai>=0.1.48`) and the spaCy model, so Mem0's hybrid search (semantic + BM25 + entity matching) is active. Upstream docs: without `[nlp]` Mem0 "falls back to semantic-only search". `PYTHONPATH=/app` so upstream's `scripts/*.py` run as documented. Upstream's own Dockerfile runs `uvicorn --reload` (development mode); this one does not.
- `railway/prepare_db.py`: waits up to 300 s for Postgres (services start in parallel), `CREATE EXTENSION IF NOT EXISTS vector`, creates `APP_DB_NAME` if missing (what upstream's `init-db.sh` does inside the Postgres container, which Railway cannot mount).
- `railway/bootstrap_admin.py`: while the users table is empty, creates the admin from `MEM0_ADMIN_EMAIL`/`MEM0_ADMIN_PASSWORD` with upstream's `models.User` and `auth.hash_password` (the agent-first `make bootstrap` path). Never modifies an existing account. Empty email or password restores the browser wizard.

### Mem0 Dashboard

| Setting | Value |
|---|---|
| Source | repo `baranberkay96/mem0-railway`, root `/services/dashboard` (Dockerfile) |
| Healthcheck | `/api/health`, timeout 300 s |
| Public domain | yes, port 3000 |
| Entrypoint | upstream `entrypoint.sh` (replaces `NEXT_PUBLIC_*` placeholders in `.next` with the variables at start) |

### Mem0 Log Pruner (cron)

Same image as the API, start command `python scripts/prune_request_logs.py` (upstream script), `cronSchedule` `30 3 * * *`, restart NEVER. Upstream README: "The request_logs table is append-only and grows with traffic … Wire the command into cron … in production."

### Postgres

`pgvector/pgvector:0.8.7-pg17` with the Railway base Postgres variables (service name `Postgres`, volume `/var/lib/postgresql/data`, `PGDATA` subdirectory, generated password). `POSTGRES_DB=mem0`. `SSL_CERT_DAYS` dropped (the pgvector image has no Railway SSL setup).

## Required input

- `OPENAI_API_KEY` (Mem0 API): the server builds its OpenAI LLM and embedder at import and does not start without a key. Any OpenAI-compatible provider works with `OPENAI_BASE_URL`. This is the only required input.

## First login

1. Open the **Mem0 Dashboard** URL. Log in with `MEM0_ADMIN_EMAIL` (default `admin@example.com`) and `MEM0_ADMIN_PASSWORD` from the Mem0 API service's Variables tab.
2. Settings → change the email to yours and set a new password.
3. API Keys → create a key per app/agent, or use `ADMIN_API_KEY` as `X-API-Key`.
4. Test: `curl -X POST https://{api-domain}/memories -H "X-API-Key: {key}" -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"I prefer Python."}],"user_id":"alex"}'`, then `POST /search` with `{"query":"language preference","filters":{"user_id":"alex"}}`.

## Improvements over market templates

1. **Pinned, verified upstream release** (tag v2.2.1 + checksum) for API and dashboard instead of `main` or a 2025 image; library pinned to the same release.
2. **Full v2 retrieval**: `mem0ai[nlp]` + spaCy model baked in (hybrid semantic + BM25 + entity search, built-in graph-style entity linking). Market templates run semantic-only.
3. **Upstream database layout**: separate `mem0_app` database created in pre-deploy, migrations in pre-deploy (Rule 8.6), Postgres wait loop (Rule 8.5).
4. **No open setup wizard**: admin created from generated credentials before the API serves traffic.
5. **Request-log retention cron** as upstream recommends for production.
6. **Private networking** for dashboard → API server-side calls; CORS limited to the dashboard origin; client IPs from proxy headers so auth rate limits work per client.
7. **Telemetry off** by default (opt-in variable), production `uvicorn` (no `--reload`), healthchecks and `PORT` on every web service.

## Resource estimate

Railway prices: RAM $10/GB-month, vCPU $20/vCPU-month, volume $0.15/GB-month.

| Service | Idle RAM / CPU | Typical RAM / CPU | Notes |
|---|---|---|---|
| Mem0 API | 0.25 GB / 0.01 (measured 217 MB after start) | 0.5 GB / 0.1 | spaCy model loads on first write (~+100 MB); LLM/embedding work happens at OpenAI |
| Mem0 Dashboard | 0.1 GB / ~0 (measured 97 MB) | 0.15 GB / 0.02 | |
| Postgres (pgvector) | 0.08 GB / 0.01 (measured 71 MB) | 0.3 GB / 0.05 | grows with memory count and HNSW indexes |
| Mem0 Log Pruner | 0 (runs ~10 s/day) | 0 | |
| Volumes | Postgres 0.2 GB, history 0.05 GB | 2 GB + 0.2 GB | |

Estimated monthly cost: **idle ≈ $5** (0.43 GB × $10 + 0.02 vCPU × $20), **typical ≈ $14** (0.95 GB × $10 + 0.17 vCPU × $20 + 2.2 GB × $0.15). OpenAI usage is billed by OpenAI.

Minimum plan: **Trial** fits the RAM (every service < 1 GB), but Hobby is recommended for always-on use.

## Verification checklist

Local (done 2026-10-11, `linux/amd64` builds, containers on one Docker network): API and dashboard images built; pre-deploy chain run while Postgres was still starting (waited, created `mem0_app`, applied alembic 001–006, created the admin) and re-run idempotently; API started (`Uvicorn running on http://0.0.0.0:8000`), `/docs` 200, `/auth/setup-status` → `needsSetup:false`, login with the bootstrap admin returned a JWT, `GET /memories` with `X-API-Key: ADMIN_API_KEY` 200 and without 401; dashboard `/api/health` 200, `/` → `/login`, API URL substituted into `.next/static`; pruner ran and deleted 0 rows. A real memory write/search was not run (needs a real OpenAI key).

On first Railway deploy:

- [ ] All four services build; API pre-deploy log shows `prepare_db`, alembic and `bootstrap_admin: created admin`.
- [ ] API healthy on `/docs`; dashboard healthy on `/api/health`.
- [ ] Dashboard login with the generated admin; Requests page lists calls.
- [ ] `POST /memories` then `POST /search` with a real key return the stored fact; dashboard Memories and Entities pages show it.
- [ ] Redeploy the API: memories and history (`GET /memories/{id}/history`) are still there.
- [ ] Trigger the Log Pruner manually once (Railway cron "Run now"): exits 0.

## Open questions

- **MCP**: no maintained self-hosted Mem0 MCP server exists upstream any more. A small MCP-to-REST bridge service could be added later as custom code; it was not added here to avoid shipping unofficial software under the Mem0 name.
- The private URL from dashboard to API relies on Railway resolving private hostnames to IPv4 in new environments (uvicorn binds `0.0.0.0`; Rule 8.2). In a legacy IPv6-only environment set `API_INTERNAL_URL` to the API's public HTTPS URL.
- `admin@example.com` is a placeholder login; users should change it in Settings. pydantic accepted it (tested); the account is created only while no user exists.
- First image build of the API takes a few minutes (spaCy, blis, thinc wheels); the Log Pruner builds the same Dockerfile again.
