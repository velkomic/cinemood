# Roadmap

Status: reviewed implementation sequence with published tickets; four-to-five-day targets are not a delivery guarantee. Complete acceptance criteria, links, and blocking edges are in `plans/MVP.md`; active status and verification evidence live in `progress.md`.

Planning and acceptance criteria have been reviewed. Each slice includes behavior tests at agreed boundaries, a runnable demonstration, and updated progress notes. No slice has been implemented yet.

| Slice | Target | Independently verifiable outcome | Dependencies |
| --- | --- | --- | --- |
| T1: Semantic discovery | Day 1 | A small fixture catalog in PostgreSQL/pgvector produces semantic results through the API and Discover page; clean local startup and CI checks work. | Agreed spec, required credentials |
| T2: Real catalog ingestion | Day 2 | TMDB data replaces fixtures; resumable manual/scheduled runs reach the bounded target without duplicates, retain snapshots, and make imported movies searchable. | T1; credentials and data-use checks |
| T3: Constraints and relaxation | Day 2 | Interpret supported natural-language constraints, display SQL-filtered results, and offer bounded explicit-selection alternatives for no-match requests. | T1 |
| T4: Streamed grounded recommendations | Day 3 | Stream explanations about selected movies; verify failure behavior, the fixed evaluation set, and database-backed factual details. | T2 and T3 |
| T5: Personal collection | Day 4 | Save, list, and remove work across browser revisits, persist through application restart, and isolate different anonymous visitors. | T1 |
| T6: AWS demonstration | Day 5 | HTTPS deployment works; backup restoration, stable-origin stop/start, and a recorded end-to-end demonstration are verified. | T4 and T5; local checks pass; explicit paid-resource approval |

T2, T3, and T5 can each proceed after T1 if that improves scheduling; they do not block each other. Day targets are not dependencies. Use the published tickets as the unit of implementation.

If the timebox tightens, preserve the tested local user journey, collection, SQL evidence, and evaluation results; report any incomplete deployment work explicitly. Expand the catalog after the initial MVP succeeds.
