# Progress

## Active milestone

T2 ([#3: Search a bounded, resumable TMDB catalog](https://github.com/velkomic/cinemood/issues/3)) is implemented locally and undergoing final verification/review. Only this slice is in scope. The T1 blocker is closed. Detailed evidence and remaining live-verification prerequisites are recorded below.

T1 complete, published, and closed with accepted local verification: [Discover movies from a small local semantic catalog](https://github.com/velkomic/cinemood/issues/2). All 25 integration tests, Compose startup/retrieval, and deterministic plus live-OpenAI browser demonstrations passed. Standards and Spec reviews found no required code changes. The user accepted local verification instead of requiring a hosted GitHub Actions run; the workflow remains configured.

## Verified state

- Repository contains a README and agent setup instructions.
- T1 local implementation is present; verification evidence is recorded below. T2 implementation and its verification status are recorded below; T3–T6 have not been implemented.
- GitHub issue search returned no open issues at the start of planning.
- Cupcake search returned no CineMood context at the start of planning.
- The `gh` CLI is unavailable in this environment. Connected GitHub tools verified `velkomic/cinemood` and created the specification and six implementation issues, all labelled `ready-for-agent`. Relationship metadata uses the documented issue-body fallback because native relationship tools are unavailable.
- Product interview Q1–Q20 is complete. Supported constraints, explicit-selection relaxation, anonymous collections, streaming priority, local test boundaries, and the single-host architecture are agreed.
- The user accepted the specification after review. Published [CineMood MVP specification](https://github.com/velkomic/cinemood/issues/1) and the six implementation issues indexed in `plans/MVP.md`; roadmap and navigation reflect publication.
- Official-source research records model prices, TMDB API behavior and source-verification gaps, and AWS lifecycle/HTTPS findings. During planning, no live provider calls, application tests, deployment, certificate issuance, or infrastructure changes were performed; T1 local verification is recorded below.

## Outstanding external checks

- Before live TMDB ingestion: review applicable account/API terms covering stored metadata, snapshots, retention, and third-party processing; verify credentials and actual response usability. Licensed fixtures allow T1 and T3 to proceed independently.
- Before paid AWS provisioning: verify local sizing, current Frankfurt compute/gp3/S3 prices, tax/currency assumptions, account billing configuration, and the explicit resource/retention plan. The retained Elastic IP is a proposal for collection continuity, not an approved resource.
- During implementation: verify model access/compatibility, latency, generation quality, stream cancellation, HTTPS issuance/renewal, backup restoration, and stop/start collection continuity at their relevant milestones.

## T1 implementation evidence — 2026-11-09

- Refetched issues #1 and #2 and #2 comments through connected GitHub tools before coding; #2 is open, `ready-for-agent`, and has no blockers/comments. Cupcake search again returned no CineMood context.
- Implemented FastAPI Discover and `POST /api/recommendations`, transactional versioned SQL migrations, relational movies/genres, exact cosine retrieval with a stable ID tie break, and a bounded `python -m cinemood load-fixtures --limit 1..4` command.
- Four original fictional CC0 films avoid TMDB account/data-use dependencies. Stored vectors identify model, 1,536 dimensions, document version, provider-endpoint fingerprint, and content hash. Switching provider endpoints cannot silently reuse incompatible vectors.
- Agreed test boundaries: REST API and fixture-loading command; real temporary PostgreSQL databases, with only the external OpenAI HTTP service replaced. Verified input limits, empty catalog, deterministic ordering and catalog facts, provider/configuration/malformed-vector failures, database/query errors, bounded/repeated loads, safe failed-load retry, and migration reruns. No private-helper tests or mocked database were added.
- Native verification used PostgreSQL 16.15 and pgvector 0.6.0 unpacked under `/tmp`, after the initially stopped Docker daemon prevented container startup. Individual API and fixture-command test runs passed. The final full suite used the pinned Docker image below.
- Chromium desktop/mobile demonstration passed against a fresh database: `quiet comfort` → The Lantern Kitchen, `space rescue` → Orbital Rescue, three cards, no horizontal mobile overflow, provider failure feedback, re-enabled submit button, and no browser JavaScript errors. Screenshots: `/tmp/cinemood-desktop.png` and `/tmp/cinemood-mobile.png` (session artifacts, not committed).
- Final complete suite: **25 passed in 39.04s** with `TEST_DATABASE_URL=postgresql://cinemood:cinemood@127.0.0.1:55433/postgres .venv/bin/python -m pytest -q`, against the same `pgvector/pgvector:0.8.2-pg16` image configured in CI (PostgreSQL 16.14, pgvector 0.8.2). Every case used its own real temporary database.
- Ruff lint, Ruff formatting check, strict mypy (7 application source files), JavaScript syntax, and git whitespace checks passed.
- Started Docker Desktop after finding its daemon stopped. `docker compose -p cinemood-t1-check up --build -d --wait` succeeded with a fresh named volume, automatic migrations, and both containers healthy. `/health`, the empty-catalog API response, and the safe missing-key CLI failure were verified. A test-only provider attached to the private Compose network then loaded four films and returned Orbital Rescue, River Workshop, and Garden Letters for `space rescue`. Database had no published host port; web bound only to loopback. Temporary test containers, test volume/network, and native PostgreSQL server were removed/stopped afterward.
- Two independent reviews compared the implementation against starting commit `7246ba5a78ee39176376543cdb0eb7b73931cbb4`. Standards: zero documented breaches, one optional Data Clumps suggestion for repeated embedding-compatibility fields; retained explicit SQL parameters for this slice. Spec: zero actionable implementation gaps, wrong behavior, or scope creep; hosted CI/live verification limits confirmed. No required code changes.
- During the initial implementation session no OpenAI key was available. That session used deterministic HTTP fixtures and made no paid provider, TMDB, or AWS calls. The later authorized live verification is recorded separately below.
- GitHub Actions is configured for lint, formatting, type checking, and API/CLI tests against a real pgvector service. Hosted execution was not required for T1 closure after the user accepted the local-verification substitution. No hosted pass is claimed; pushing may trigger the configured workflow automatically.

## T1 live verification and acceptance — 2026-11-09

- The user supplied a key in local `.env` and authorized live verification and publication. Verified that `.env` is ignored and not tracked; the key was not printed, committed, or sent to GitHub.
- `docker compose up --build -d --wait` passed with both containers healthy. Confirmed the app uses the official `https://api.openai.com/v1` endpoint and `text-embedding-3-small`, 1,536 dimensions.
- The existing catalog was already loaded: the bounded loader reported `embedded: 0`. To independently verify actual loading without modifying that catalog, created a temporary database in the same PostgreSQL service, ran migrations, and loaded all four CC0 fixture films: `embedded: 4`. A repeat load reported `embedded: 0`. Removed the temporary database afterward.
- Chromium made two live API requests through Discover. A gentle neighborhood-kitchen comedy request returned The Lantern Kitchen first (IDs 1, 2, 3); a tense orbital rescue request returned Orbital Rescue first (IDs 4, 3, 1). Both returned three database-backed cards and rendered successfully. Browser-observed response/render times were 0.324 s and 0.356 s; these two samples are not a latency distribution or the later 20-request relevance evaluation.
- Desktop and 390-pixel mobile checks passed with no browser JavaScript errors or horizontal overflow. Session artifacts: `/tmp/cinemood-live-verification.json`, `/tmp/cinemood-live-desktop.png`, `/tmp/cinemood-live-mobile.png`.
- Live calls were bounded to one four-document embedding batch and two query embeddings, with no model retries. Actual token usage and billing were not metered; no generation, TMDB, or AWS calls were made. The existing 25-test deterministic integration suite remains the correctness evidence; this verification added live access/compatibility and a small semantic smoke check. No application code changed.
- Ruff lint/format, strict mypy, JavaScript syntax, and whitespace checks passed again before publication. GitHub Actions remains configured, but the user accepted the completed local checks as the T1 completion gate. This is an explicit change from the ticket's original hosted-CI-run requirement.
- Local application and catalog remain available at `http://localhost:8000`; the temporary verification database was removed.

## Next step

Implementation commit `bd20424` and live-verification commit `5472d97` were pushed to `origin/main`. Issue #2 is closed as completed, with its acceptance checklist and completion comment recording the local-CI substitution. Start one of T2 (#3), T3 (#4), or T5 (#6) in a fresh chat; do not implement another slice in this session. T2 requires credential/data-use preflight before live TMDB ingestion. T3 (constraints) and T5 (collections) can proceed on the fixture catalog.

## Session handoff

The repository documentation and published ticket are the durable context; the planning transcript need not be pasted into a new implementation chat. Use one implementation ticket per fresh chat. After T1 acceptance, choose an open ticket whose blockers are completed. Keep `plans/MVP.md` as the ticket index and update this progress file after each slice. Complete acceptance checks before reporting or closing a ticket as done.

## T2 implementation evidence — 2026-11-09

- Refetched the complete parent issue #1, ticket #3 and its comments, and blocker #2 through the connected GitHub tools before coding. #3 is open and `ready-for-agent`, with no comments; #2 is closed. Cupcake search returned no CineMood context.
- Added `ingest-tmdb`: descending-vote-count English-localized discovery without an original-language restriction, explicit adult/usability validation, durable page/detail checkpoints, a single PostgreSQL session advisory lock shared with fixture loading, source-ID upserts, per-movie transactional metadata/vector/cursor commits, 250 ms pacing, bounded retries honoring Retry-After, and page/request ceilings. The initial target defaults to 1,000 unique TMDB movies; fixtures do not count.
- Persisted release date, vote count and raw-detail snapshot keys in a new migration. Searchable-content changes replace facts and vector atomically while keeping local movie identity. Vote-count-only changes reuse embeddings. Saved pages survive remote reordering; saved details survive embedding failures. Target completion causes zero provider calls, including without credentials. The job is bounded initial acquisition, not a general refresh facility.
- Local versioned JSON snapshots use atomic, fsynced mode-0600 files and relative content-addressed keys behind a storage interface suitable for a later S3 adapter. Compose retains snapshots in a named volume writable by the non-root app user. No S3/AWS infrastructure or SDK was added. Manual/cron instructions, usability thresholds, storage format, counts, and recovery limitations are in `docs/ingestion.md`.
- Discover now identifies its local catalog accurately and includes Credits, the required TMDB notice, and the unchanged approved logo downloaded from TMDB's official attribution page.
- Applied TDD at the pre-agreed ingestion-command and REST API boundaries, with real disposable PostgreSQL/pgvector and only external TMDB/OpenAI HTTP services replaced. Initial command and attribution acceptance checks failed before implementation. The ingestion file then passed **26 tests in 77.76s**, covering import visibility, snapshots, target stop, SIGKILL/resume, concurrent exclusion, remote reorder, duplicates, unusable/adult/non-English metadata, 429/503, ceilings, source exhaustion, changed content/embedding reuse, provider failure/detail reuse, snapshot failure, and CLI bounds. Subsequent verification of the strengthened credential-free target-repeat assertion is pending the final suite.
- Ruff lint/format and strict mypy (9 application source files) passed. Compose, browser, independent review, and final full-suite results are pending below; no hosted CI result is claimed.
- The user confirmed the applicable terms review and authorized bounded live verification in this session. At initial credential inspection, `.env` contained OpenAI configuration but no `TMDB_READ_TOKEN`; no secrets were printed. Planned live verification is capped at five accepted movies, one new discovery page and 12 TMDB HTTP attempts, followed by one query embedding and a zero-fetch repeat. No live TMDB run or completed 1,000-movie catalog is claimed here.
