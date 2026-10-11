# Deploy and Host Mem0 with Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/mem0-v2-ai-memory-layer?referralCode=20H68q)

Mem0 is an open-source memory layer for AI agents and assistants. It extracts durable facts from conversations, stores them as embeddings in Postgres with pgvector, and returns the relevant ones for each user, agent or session. This template deploys Mem0's self-hosted REST API, its web dashboard and a pgvector database, ready for your agents to call.

## About Hosting Mem0

The self-hosted Mem0 server is a FastAPI application with authentication, per-user API keys and a request log, plus a Next.js dashboard. It needs Postgres with the pgvector extension, a second database for users and settings, migrations before start, an LLM and embedding provider, and periodic cleanup of request logs. This community template builds the API and dashboard from the pinned Mem0 v2.2.1 release, creates both databases and runs migrations before each deploy, creates the dashboard admin from generated credentials so no one else can claim the setup page, and adds a daily cron job for log retention. It also installs Mem0's recommended NLP extra, which enables hybrid keyword, semantic and entity search.

## Common Use Cases

- Long-term memory for chatbots and support agents that remember user preferences across sessions
- Shared memory for multi-agent systems, scoped by `user_id`, `agent_id` and `run_id`
- Personalising LLM apps with facts recalled through `POST /search`
- Auditing what your agents store and recall through the dashboard's Memories, Entities and Requests views

## Dependencies for Mem0 Hosting

- An OpenAI API key, or a key for any OpenAI-compatible endpoint set through `OPENAI_BASE_URL` (required)
- Postgres with pgvector (included)
- Optional: Anthropic or Google keys to switch models in the dashboard's Configuration page

### Deployment Dependencies

- Mem0 repository: https://github.com/mem0ai/mem0
- Self-hosted server README (v2.2.1): https://github.com/mem0ai/mem0/tree/v2.2.1/server
- REST API documentation: https://docs.mem0.ai/open-source/features/rest-api
- pgvector: https://github.com/pgvector/pgvector

### Implementation Details

| Service | Source | Purpose |
|---|---|---|
| Mem0 API | Dockerfile, upstream `server/` at v2.2.1 | REST API on port 8000, healthcheck `/docs`, history volume `/app/history`; pre-deploy creates databases, migrates and bootstraps the admin |
| Mem0 Dashboard | Dockerfile, upstream `server/dashboard/` at v2.2.1 | Web UI on port 3000, healthcheck `/api/health` |
| Mem0 Log Pruner | same image as the API, cron `30 3 * * *` | Deletes API request logs older than `REQUEST_LOG_RETENTION_DAYS` (30) |
| Postgres | `pgvector/pgvector:0.8.7-pg17` | Memory and entity vectors (`mem0`) and app data (`mem0_app`) |

**First login**

1. Paste your `OPENAI_API_KEY` when deploying.
2. Open the Mem0 Dashboard URL and sign in with `MEM0_ADMIN_EMAIL` (default `admin@example.com`) and `MEM0_ADMIN_PASSWORD` from the Mem0 API service's Variables tab. Change both under Settings.
3. Create an API key under API Keys, or use `ADMIN_API_KEY` from the API service.
4. Store a memory: `curl -X POST https://{api-domain}/memories -H "X-API-Key: {key}" -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "I prefer Python."}], "user_id": "alex"}'`. Recall it with `POST /search` and `{"query": "language preference", "filters": {"user_id": "alex"}}`. Interactive docs are at `https://{api-domain}/docs`.

**MCP**: Mem0's official MCP server is a hosted service for the Mem0 Platform; the self-hosted OpenMemory MCP server was removed upstream in 2026. Connect agents to this deployment through the REST API or the Mem0 SDKs.

**Scaling**: the API keeps memory history in SQLite on its volume, so it runs as one replica; give it more RAM or CPU if extraction traffic grows. The dashboard is stateless. Postgres can be resized vertically.

**Pinning and upgrades**: the Mem0 release and its source checksum are build arguments in both Dockerfiles. Change them together, back up the Postgres and history volumes, and redeploy; migrations run automatically before the new version starts.

### Why Deploy Mem0 on Railway?

Railway runs the API, dashboard, database and cron job together with private networking, persistent volumes and HTTPS, so your agents get a memory service you own within minutes. You pay for the small amount of RAM and CPU it uses, and your memories stay in your own database.
