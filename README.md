# CineMood

A small semantic movie discovery demo: FastAPI serves Discover and a REST API;
PostgreSQL/pgvector stores catalog facts and performs exact cosine retrieval.
Load the four **fictional CC0 films** for an independent fixture demo, or use the
[bounded, resumable TMDB importer](docs/ingestion.md) for real movies. Hard
constraints, generated explanations, and collections belong to later tickets.

## Start from a clean checkout

Requirements: Docker Engine/Desktop running Linux containers with Compose v2.
No AWS resources are needed. The database is private to the Compose network;
the application binds only to `127.0.0.1:8000`. Development database credentials
in Compose are local defaults, not deployment settings.

```bash
cp .env.example .env
# Optional: put your OpenAI API key in .env to load/search actual embeddings.
docker compose up --build -d --wait
# Migrations run automatically before the app starts.
docker compose exec app python -m cinemood load-fixtures --limit 4
```

Open <http://localhost:8000> and enter a mood or theme. Loading four films sends
one batch of at most four short documents to `text-embedding-3-small`, at 1,536
dimensions. Each search embeds one request. There are no model retries; network
operations time out after 15 seconds. The fixture loader never fetches TMDB data.
Without a key, the app still starts, `/health` works, and Discover reports an
empty catalog; loading requires a configured provider and exits with a useful
error otherwise. Unchanged fixture records are skipped on subsequent loads.
`--limit` accepts 1–4 and bounds the selected fixture prefix, not additional rows.

```bash
curl http://localhost:8000/health
curl -H 'Content-Type: application/json' \
  -d '{"request":"Something gentle about friendship"}' \
  http://localhost:8000/api/recommendations
docker compose logs app
docker compose down
```

`down` preserves the database volume. To **delete this local catalog**, use
`docker compose down --volumes`. Provider keys stay on the server; do not commit
`.env`. Changing the embedding provider endpoint, model, dimensions, or document
version requires reloading compatible catalog embeddings.

## API contract

- `POST /api/recommendations`, JSON `{"request":"..."}`: `200` with `movies`
  (0–3) and a message. Every card contains server ID, source ID, title, release
  year, sorted genres, runtime in minutes, and overview from PostgreSQL.
- Empty compatible catalog: `200`, empty movies, and an actionable message.
- Blank, non-string, missing, or over-2,000-character requests: `422`.
  HTTP bodies over 16 KiB, including chunked bodies: `413`.
- Missing/unavailable embedding provider or database/query failure: `503`
  with safe `detail`; no recommendations are claimed.
- `GET /health`: checks the database connection, not paid provider availability.

Similarity ranking is not a confidence score. A small catalog can produce weak
matches; no arbitrary similarity cutoff is applied. This slice does not parse
or enforce natural-language factual restrictions.

## Develop and verify

Use Python 3.12+ and uv 0.13.0. `uv.lock` pins the resolved dependencies.

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Tests require a disposable PostgreSQL database with the vector extension
available and a role allowed to create databases/extensions. Each case creates,
migrates, and drops its own database. No tests silently fall back to SQLite or
skip database verification. One way to provide it is a separate local container:

```bash
docker run --rm -d --name cinemood-test-db \
  -e POSTGRES_USER=cinemood -e POSTGRES_PASSWORD=cinemood \
  -e POSTGRES_DB=postgres -p 127.0.0.1:55432:5432 \
  pgvector/pgvector:0.8.2-pg16
# Wait for: docker exec cinemood-test-db pg_isready -U cinemood
export TEST_DATABASE_URL=postgresql://cinemood:cinemood@127.0.0.1:55432/postgres
uv run python -m pytest tests/test_discover.py -q
uv run python -m pytest tests/test_fixture_command.py -q
uv run python -m pytest tests/test_ingestion_command.py -q
uv run python -m pytest -q
docker stop cinemood-test-db
```

GitHub Actions runs the same correctness checks against a real pgvector service.
Tests exercise the REST API, fixture-loading and TMDB ingestion commands; the
external OpenAI and TMDB HTTP endpoints use deterministic fictional responses. They do not
establish real-provider availability or subjective semantic quality.

## Offline local demonstration

For a zero-provider-cost demo, run the test-only HTTP server in a terminal:

```bash
uv run python tests/provider_stub.py
```

In another terminal, with a disposable local PostgreSQL/pgvector database:

```bash
export DATABASE_URL=postgresql://cinemood:cinemood@127.0.0.1:55432/postgres
export OPENAI_BASE_URL=http://127.0.0.1:18080/v1
export OPENAI_API_KEY=test-only
uv run python -m cinemood migrate
uv run python -m cinemood load-fixtures
uv run uvicorn cinemood.app:app --host 127.0.0.1 --port 8000
```

Search `quiet comfort`, then `space rescue`; the first cards are The Lantern
Kitchen and Orbital Rescue respectively. These controlled vectors demonstrate
wiring and SQL ordering, **not measured AI relevance**. The test server is not
included in the application image. For a browser check, submit a request and
verify three cards, resize to a narrow viewport, then submit `provider failure`
and verify the useful error and enabled search button. The full journey smoke
with explanations/save/remove remains for its later slices.

## SQL and architecture decisions

`cinemood/catalog.py` owns explicit parameterized SQL. Versioned SQL migrations
are applied transactionally under an advisory lock and recorded with checksums;
modifying an applied migration is rejected. Future changes add a new migration.

`movies` has a unique source identity, while `genres` and `movie_genres` model a
many-to-many relationship with foreign keys and a composite primary key.
`movie_embeddings` holds one vector per movie plus content hash, model,
dimensions, document version, and a hashed provider-endpoint fingerprint.
A provider switch cannot silently compare synthetic vectors with real ones.

Retrieval joins movies to compatible embeddings, sorts exact cosine distance
(`embedding <=> query_vector`) ascending, breaks ties by movie ID, and limits to
three **before** aggregating genres. That avoids duplicate cards or fewer films
because a movie has several genres. No approximate vector index is used at this
scale. The vector literal and configuration values are bound SQL parameters;
visitor text never becomes SQL.

The bounded fixture loader acquires a separate transaction advisory lock,
embeds only changed/incompatible documents, and commits metadata, genre links,
and vectors atomically. An interrupted four-record batch rolls back and can be
rerun. The separate `ingest-tmdb` command implements resumable paginated acquisition;
see [its operating guide](docs/ingestion.md) for checkpoints, snapshots, SQL,
scheduling, limits, and the live-data preflight.

`cinemood/embeddings.py` uses LangChain's OpenAI integration. It validates count,
dimensions, finite coordinates, and nonzero vectors before database use. The
frontend uses text nodes to render catalog data safely and exposes loading,
empty, and failure states. [pgvector](https://github.com/pgvector/pgvector) and
[LangChain embeddings](https://docs.langchain.com/oss/python/integrations/embeddings/openai)
document the provider/query primitives.

See [progress](docs/progress.md) for verified results and remaining checks.
