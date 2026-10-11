# Mem0 self-hosted REST API (server/ in mem0ai/mem0) for Railway.
#
# Mem0 publishes no maintained image for the current server, so this builds the
# upstream source of one release tag, verified by checksum. Upgrade: change
# MEM0_VERSION and MEM0_SHA256 (sha256 of the codeload tarball) and redeploy.
ARG MEM0_VERSION=2.2.1
ARG MEM0_SHA256=2d203947596fbbfeaf06e5311c087a6b837566528016013aff15ad2a8a4103c5

FROM alpine:3.23 AS source
ARG MEM0_VERSION
ARG MEM0_SHA256
RUN apk add --no-cache ca-certificates curl tar && \
    curl -fsSL "https://codeload.github.com/mem0ai/mem0/tar.gz/refs/tags/v${MEM0_VERSION}" -o /tmp/mem0.tgz && \
    echo "${MEM0_SHA256}  /tmp/mem0.tgz" | sha256sum -c - && \
    mkdir /src && \
    tar -xzf /tmp/mem0.tgz -C /src --strip-components=1 "mem0-${MEM0_VERSION}/server"

FROM python:3.12.15-slim-trixie
ARG MEM0_VERSION
# spaCy model for Mem0's entity extraction and BM25 lemmatization (the
# "[nlp]" extra upstream recommends; without it search is semantic-only).
ARG SPACY_MODEL_URL=https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Upstream requirements, with the mem0ai library pinned to the same release as
# the server source (upstream only asks for mem0ai>=0.1.48).
COPY --from=source /src/server/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt \
        "mem0ai[nlp]==${MEM0_VERSION}" \
        "spacy>=3.8,<3.9" \
        "${SPACY_MODEL_URL}" && \
    python -c "import spacy; spacy.load('en_core_web_sm'); print('spaCy model OK')"

COPY --from=source /src/server/ ./
COPY railway/ ./railway/
RUN mkdir -p /app/history

EXPOSE 8000

# 0.0.0.0, not ::, because uvicorn on :: is IPv6-only and Railway's
# healthcheck uses IPv4. Proxy headers give rate limits the real client IP.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port \"${PORT:-8000}\" --proxy-headers --forwarded-allow-ips '*'"]
