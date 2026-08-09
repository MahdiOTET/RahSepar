FROM node:24-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_CLI_RELEASE_URL=https://github.com/MahdiOTET/BSLM-Entry-Task/releases/tag/v1.0.0
ENV VITE_CLI_RELEASE_URL=${VITE_CLI_RELEASE_URL}
RUN npm run build

FROM python:3.11-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /application
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY migrations/ ./migrations/
COPY --from=frontend-build /build/frontend/dist/ ./frontend/dist/
COPY docker/entrypoint.sh /usr/local/bin/rahsepar-entrypoint
RUN chmod +x /usr/local/bin/rahsepar-entrypoint \
    && groupadd --system rahsepar \
    && useradd --system --gid rahsepar --home-dir /application rahsepar

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
USER rahsepar
ENTRYPOINT ["rahsepar-entrypoint"]
