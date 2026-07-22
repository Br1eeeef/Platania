FROM node:22-alpine AS web
RUN corepack enable
WORKDIR /app/web
COPY web/package.json web/pnpm-lock.yaml* ./
RUN pnpm install --no-frozen-lockfile
COPY web/ ./
RUN pnpm build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PLATANIA_CACHE_DIR=/app/data/cache
WORKDIR /app
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt
COPY api/ api/
COPY scripts/ scripts/
COPY --from=web /app/web/dist web/dist
RUN mkdir -p data/cache
EXPOSE 8010
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8010", "--workers", "1"]

