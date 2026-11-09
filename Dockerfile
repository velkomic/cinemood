FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY cinemood ./cinemood
COPY migrations ./migrations
COPY fixtures ./fixtures
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
CMD ["sh", "-c", "python -m cinemood migrate && uvicorn cinemood.app:app --host 0.0.0.0 --port 8000 --limit-concurrency 16"]
