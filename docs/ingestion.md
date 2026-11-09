# TMDB initial catalog ingestion

Ticket: [#3](https://github.com/velkomic/cinemood/issues/3). This is an initial
bounded acquisition job, not a continuously refreshed catalog.

## Preflight and manual invocation

Review the applicable TMDB account/API terms for metadata storage, snapshot
retention, and sending text to OpenAI before using real data. The project owner
confirmed this review and authorized a bounded live verification on 2026-11-09.
This confirmation does not specify a general retention policy or authorize S3
provisioning. Account-specific obligations remain the operator's responsibility.
See [the recorded source limitations](research/tmdb-data-use.md).

Put an API **Read Access Token** in local `.env` as `TMDB_READ_TOKEN` (Bearer token,
not a v3 API key), alongside `OPENAI_API_KEY`. Do not put tokens on command lines.
Compose reads `.env`; the host Python CLI reads exported environment variables,
not `.env` automatically. Recreate the app after changing Compose credentials.

```bash
docker compose up --build -d --wait
docker compose exec -T app python -m cinemood ingest-tmdb \
  --target 1000 --max-pages 5 --max-requests 150
```

Defaults are exactly those limits: target 1,000 unique **TMDB** movies (fixture
movies do not count), five newly fetched pages and 150 HTTP attempts per run.
Repeat to continue. For a small verification use `--target 5 --max-pages 1
--max-requests 12`. Valid ranges are target 1–1,000, pages 1–500 and requests
1–2,000. Raising the target within that envelope explicitly expands a smaller
initial load; no automatic refresh or reset is performed.

Each success prints one JSON report: `status` (`complete` or `incomplete`),
`total`, `target`, and per-invocation `accepted`, `skipped`, `duplicates`,
`embedded`, `requests`, and `pages`. An incomplete report gives a `reason`:
`request_budget`, `page_budget`, or `source_exhausted`. Budget/source exhaustion
exits zero with an honest incomplete result. Provider, storage, lock and database
failures exit nonzero with a safe error; rerun to resume. Counts for an invocation
that crashes are not a durable audit ledger; committed catalog/cursor state is.

## Scheduled invocation

Install this in the operator's crontab if desired, replacing the path with the
checkout's absolute path. Installing/enabling a schedule is an operator action;
implementation does not silently enable external API spending.

```cron
# Daily bounded batch; Compose must already be running.
0 6 * * * cd /absolute/path/to/cinemood && /usr/bin/docker compose exec -T app python -m cinemood ingest-tmdb --target 1000 --max-pages 5 --max-requests 150 >> /absolute/path/to/cinemood/var/ingestion.log 2>&1
```

Create the private log directory first (`mkdir -p var && chmod 700 var`). Keep
logs rotated. A PostgreSQL session advisory lock covers the entire run and is
shared with fixture loading. An overlapping invocation fails without provider
calls; process death releases its lock. Once the TMDB target is reached with compatible vectors,
subsequent normal manual/scheduled runs perform **zero TMDB and embedding calls**.

## Acquisition, usability and limits

Discover requests `sort_by=vote_count.desc`, `include_adult=false`, `language=en-US`
and successive page numbers. No original-language filter is sent. Details are
also requested in English, and `adult` must be explicitly false. Pagination is
not an atomic ranking snapshot; the saved page preserves its observed order,
and SQL uniqueness prevents duplicate movies across changing pages.

A usable movie needs a matching positive TMDB identity; nonblank title (at most
500 characters); overview of 40–10,000 characters; valid release date in
1800–2200; positive integer runtime up to 1,440 minutes; two lowercase-letter
original language; nonnegative 32-bit integer vote count; and 1–30 nonblank genre
names (each at most 100 characters). The overview must be classified English
with probability at least 0.8 by `langdetect` 1.0.9 with seed zero. This heuristic
can reject short/ambiguous English text or misclassify text; requesting an English
localization does not guarantee a translation. No original language is excluded.
Invalid/missing details are skipped. HTTP 404 details are retained as a missing
record snapshot and skipped; other permanent HTTP errors stop the run.

Requests are spaced at least 250 ms apart within a run, time out after 15 seconds,
and permit at most three attempts, all charged to the request ceiling. Connection
errors and HTTP 429/500/502/503/504 retry with exponential backoff. `Retry-After`
seconds and HTTP dates are honored; a delay over 30 seconds stops the run for a
later invocation rather than retrying early or sleeping without a bound.
Embedding requests have their existing 15-second timeout and no automatic retry.
An interruption between external embedding success and SQL commit may require
repeating that one embedding; committed records are not re-embedded unchanged.

## Persistence and SQL

`ingestion_checkpoints` stores the discovery page, next index, origin, and any
pending fetched detail in JSONB. JSON is source state, never executable SQL. Each
movie, its genre links, compatible embedding, and cursor advance commit in one
transaction. A restart uses the saved page even if the source page changes;
a failed embedding reuses the fetched detail. A new migration adds release date,
vote count and snapshot key to `movies`; existing fixture records remain valid.

`movies.source_id` stays unique (`tmdb:<id>`), independent of the generated local
ID. `ON CONFLICT` updates metadata while preserving that ID. Repeated IDs may
update changed content as encountered during acquisition. The content hash
covers normalized searchable facts, excluding vote count and full release date
(the searchable year remains included). Metadata-only changes reuse vectors;
changed searchable facts/configuration replace the vector atomically with facts.
Once the target is reached the job stops before any refresh; expanding targets
or encountering repeated IDs is not a general catalog refresh mechanism.

Changing the embedding endpoint/model/document configuration makes existing
vectors incompatible. Normal ingestion fails with an actionable message instead
of reporting a searchable completed catalog. Explicitly rebuild from stored facts:

```bash
docker compose exec -T app python -m cinemood ingest-tmdb --reindex --target 1000
```

This mode scans at most `--target` stored TMDB movies in stable local-ID order,
embeds only incompatible/changed documents, and makes no TMDB calls or acquisition
checkpoint changes. Each repaired movie commits separately; interruptions can
resume with another `--reindex`. It may make up to `--target` embedding calls
(default maximum 1,000), so select a smaller bound for experiments. It reports
`complete` only when the existing catalog reaches the target and all its records
were scanned; otherwise `incomplete`/`reindex_only` does not claim acquisition.
Use the normal command afterward to continue toward the acquisition target.

## Snapshots and recovery boundary

`SnapshotStore.put` accepts a versioned envelope and returns a relative key. The
local implementation writes JSON to `tmdb/v1/<sha256>.json` under
`TMDB_SNAPSHOT_DIR` (host default `var/snapshots`; Compose `/data/snapshots` in the
`tmdb-snapshots` named volume). Files are mode 0600, atomically renamed after
fsync, and the parent directory is synced before a key is persisted in SQL.
An interrupted write cannot replace an existing complete file. A crash after
snapshot persistence can leave an unreferenced snapshot; automatic deletion is
not part of this initial-load job.

Envelope fields: `version: 1`, `provider: tmdb`, credential-free `origin`,
`endpoint`, `parameters`, UTC `fetched_at`, `http_status`, and the raw decoded JSON
`response`. Headers and credentials are never retained. The snapshot preserves
JSON data, not byte-for-byte whitespace. Successful discovery and detail responses
are saved, including rejected records. Metadata points to its detail snapshot;
page snapshots preserve acquisition order/vote counts. Protect the snapshot root
and preserve both named volumes. `docker compose down` retains them;
`docker compose down --volumes` deletes both catalog and snapshots.

T6 can implement the same storage interface with private S3 object keys after
separate resource approval. No AWS SDK, bucket, upload, or S3 verification is
included here. Snapshots cannot restore vectors, checkpoints or future
collections alone; a database backup and snapshots must be preserved together.

## Attribution

Discover includes a Credits section, TMDB's required notice and a local unchanged
[approved TMDB logo](https://www.themoviedb.org/about/logos-attribution), downloaded
from TMDB's attribution page on 2026-11-09. The logo links to TMDB and is less
prominent than CineMood branding. Source asset:
`https://www.themoviedb.org/assets/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg`.
See the [official attribution requirements](https://developer.themoviedb.org/docs/faq).
