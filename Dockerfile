# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.11.9
ARG NODE_VERSION=22.22.0
ARG PNPM_VERSION=11.9.0
ARG TORCH_VERSION=2.13.0+cpu

FROM python:${PYTHON_VERSION}-slim-bookworm AS backend-dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

ARG TORCH_VERSION
RUN python -m pip install \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch==${TORCH_VERSION}"

COPY routedeck /workspace/routedeck
RUN python -m pip install \
    -e "/workspace/routedeck[fastapi,persistence,testing]"

COPY agent-execution-runtime/pyproject.toml /workspace/agent-execution-runtime/pyproject.toml
COPY agent-execution-runtime/src /workspace/agent-execution-runtime/src
COPY agent-delivery-runtime/pyproject.toml /workspace/agent-delivery-runtime/pyproject.toml
COPY agent-delivery-runtime/src /workspace/agent-delivery-runtime/src
RUN python -m pip install \
    /workspace/agent-execution-runtime \
    /workspace/agent-delivery-runtime \
    && python -c "from importlib.metadata import version; assert version('agent-execution-runtime') == '0.1.0'; assert version('agent-delivery-runtime') == '0.1.0'"

COPY saastoagent-v0.1/backend /workspace/corpus/backend
RUN python -m pip install -e "/workspace/corpus/backend[testing]"

COPY saastoagent-v0.1/scripts /workspace/corpus/scripts
COPY saastoagent-v0.1/docs /workspace/corpus/docs

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41', device='cpu'); print('Pinned MiniLM embedding model cached in backend image.')"

WORKDIR /workspace/corpus

FROM node:${NODE_VERSION}-bookworm-slim AS frontend-dev

ARG PNPM_VERSION
ENV COREPACK_HOME=/opt/corepack

RUN corepack enable && corepack prepare "pnpm@11.7.0" --activate

WORKDIR /workspace

COPY routedeck /workspace/routedeck
RUN pnpm --dir /workspace/routedeck \
      --filter @routedeck/core \
      --filter @routedeck/react \
      install --frozen-lockfile \
    && pnpm --dir /workspace/routedeck --filter @routedeck/core build \
    && pnpm --dir /workspace/routedeck --filter @routedeck/react build

RUN corepack prepare "pnpm@${PNPM_VERSION}" --activate

COPY saastoagent-v0.1/frontend /workspace/corpus/frontend
RUN pnpm --dir /workspace/corpus/frontend install --frozen-lockfile

WORKDIR /workspace/corpus/frontend
