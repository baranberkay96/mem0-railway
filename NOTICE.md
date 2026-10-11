# NOTICE: Mem0 v2 AI Memory Layer template

## Software used

| Component | Source | License | How it is used |
|---|---|---|---|
| Mem0 self-hosted server and dashboard | https://github.com/mem0ai/mem0 tag `v2.2.1` (`server/`, `server/dashboard/`), downloaded at build time and checksum-verified | Apache-2.0, "Copyright [2023] [Taranjeet Singh]" as stated in upstream LICENSE | Built unmodified from source. `services/dashboard/Dockerfile` follows the build steps of upstream's `server/dashboard/Dockerfile` (Apache-2.0) and runs upstream's `entrypoint.sh` unchanged. Upstream's `scripts/prune_request_logs.py` runs as the cron job. |
| mem0ai Python library | PyPI `mem0ai[nlp]==2.2.1` | Apache-2.0 | Installed unmodified |
| spaCy and `en_core_web_sm` 3.8.0 | PyPI / github.com/explosion/spacy-models | MIT | Installed unmodified |
| pgvector Postgres image | `pgvector/pgvector:0.8.7-pg17` | PostgreSQL License (pgvector), PostgreSQL License (Postgres) | Run unmodified |
| Python, Node.js base images | `python:3.12.15-slim-trixie`, `node:22.23.3-alpine3.23`, `alpine:3.23` | PSF, MIT and distribution licenses | Base images |

`services/api/railway/prepare_db.py` re-implements what upstream's `server/init-db.sh` does (create the `mem0_app` database) for Railway, where files cannot be mounted into the Postgres image. `services/api/railway/bootstrap_admin.py` does what upstream's `make bootstrap` / `scripts/seed.sh` does for the admin account, using upstream's `models.User` and `auth.hash_password`. Both were written for this template.

Product names belong to their owners. This is a community template, not affiliated with Mem0.

## Upstream files and docs checked (2026-10-11)

- `mem0ai/mem0` tag `v2.2.1` (commit `94c3fe9f238f3dbf29c9ce98643bd71eb13077cd`, latest Python SDK release, 2026-09-25): `server/README.md`, `Dockerfile`, `docker-compose.yaml`, `.env.example`, `requirements.txt`, `init-db.sh`, `main.py`, `auth.py`, `db.py`, `models.py`, `server_state.py`, `rate_limit.py`, `telemetry.py`, `alembic/env.py` and versions 001–006, `routers/auth.py`, `scripts/prune_request_logs.py`, `scripts/reset_admin_password.py`, `scripts/seed.sh`, `server/dashboard/{Dockerfile,entrypoint.sh,next.config.mjs,package.json,src/lib/server-api-url.ts,src/app/api/auth/refresh/route.ts}`, `pyproject.toml` (extras), `mem0/vector_stores/pgvector.py`, `mem0/utils/spacy_models.py`, `docs/migration/oss-v2-to-v3.mdx` (`[nlp]` recommendation), `docs/platform/mem0-mcp.mdx` (hosted MCP only), `docs/changelog/highlights.mdx` (external graph stores removed in v2.0.0).
- Commit `ea2ee07586` (2026-07-29): "chore: remove OpenMemory from the monorepo (#6530)". `mem0ai/mem0-mcp` is archived.
- Docker Hub: `mem0/mem0-api-server:latest` last pushed 2025-09-10 (not used); `pgvector/pgvector` tags.

## Market templates and repositories reviewed

| Template / repo | License | Use |
|---|---|---|
| `mem0-memory-api-pgvector` (builds from `mem0ai/mem0` main) | n/a (template config) | Base for the service split and variable set; configuration rewritten. |
| `mem0` (image `mem0/mem0-api-server:latest`) | n/a | Reviewed, nothing taken. |
| `mem0-self-hosted-1` / `tech-progress/railway-template-mem0` | **no license (NOASSERTION): all rights reserved** | Read only. No files or text copied. |

All files in this package (Dockerfiles, `railway/*.py` and the docs) were written for this template. No README text from other templates was reused.
