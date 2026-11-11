# MVP implementation slices

Status: reviewed and published on 2026-11-09 under [CineMood MVP specification](https://github.com/velkomic/cinemood/issues/1). T-identifiers are planning references, not GitHub issue numbers. The accepted product scope is in `../PROJECT.md`; the complete specification is in `../SPEC.md`.

| Slice | GitHub ticket | Blocking tickets |
| --- | --- | --- |
| T1 | [Discover movies from a small local semantic catalog](https://github.com/velkomic/cinemood/issues/2) | None |
| T2 | [Search a bounded, resumable TMDB catalog](https://github.com/velkomic/cinemood/issues/3) | T1 |
| T3 | [Interpret constraints and offer no-match alternatives](https://github.com/velkomic/cinemood/issues/4) | T1 |
| T4 | [Stream grounded explanations and evaluate recommendations](https://github.com/velkomic/cinemood/issues/5) | T2, T3 |
| T5 | [Keep an isolated personal collection](https://github.com/velkomic/cinemood/issues/6) | T1 |
| T6 | [Demonstrate the complete application on AWS](https://github.com/velkomic/cinemood/issues/7) | T4, T5; local checks and paid-resource approval |

## T1: Discover movies from a small local semantic catalog

**Blocked by:** accepted specification and required development access; no implementation-ticket blockers.

**Delivers:** a visitor enters a request and sees movie cards retrieved from a small independently licensed fixture catalog stored in PostgreSQL/pgvector.

- [ ] Docker Compose starts the application and database from a documented clean checkout; migrations create relational movie/genre records and compatible vectors.
- [ ] A bounded fixture-loading command prepares actual embeddings when provider access is available; deterministic external-provider fixtures support repeatable tests.
- [ ] A FastAPI endpoint and Discover view show up to three server-identified movie cards through exact semantic retrieval; this slice does not yet claim free-text hard-constraint extraction or generated explanations.
- [ ] Blank/oversized requests, unavailable providers, empty catalog, and query failures return useful observable outcomes.
- [ ] API and ingestion-command checks run with real PostgreSQL/pgvector integration in CI. SQL is parameterized, and a developer can explain the joins and vector ordering.

**Verification:** clean local startup; controlled known retrieval examples; provider-boundary failure cases; CI run; a short local demonstration. Record which checks used fixtures and which used live embeddings.

## T2: Search a bounded, resumable TMDB catalog

**Blocked by:** T1; TMDB credentials and applicable data-use preflight review.

**Delivers:** real movies enter the same searchable UI through a repeatable initial-load pipeline, stopping at 1,000 usable records.

- [ ] Descending vote-count acquisition excludes adult content, requests English metadata, allows all original languages, validates usability, and deduplicates by TMDB ID.
- [ ] Manual and scheduled invocation share durable checkpoints, a single-run lock, conservative request pacing, bounded retries, and a request/page ceiling.
- [ ] Interruption and rerun preserve committed progress without duplicate movies or unnecessary re-embedding; reaching the target causes subsequent runs to fetch nothing.
- [ ] Raw snapshots and provenance are retained locally until S3 is approved; the snapshot format and storage interface allow S3 verification in T6.
- [ ] New catalog movies are visible in Discover; required TMDB attribution is visible in the UI.

**Verification:** simulated pages, invalid records, duplicate/reordered IDs, 429/transient errors, interrupted runs, and target exhaustion through the ingestion boundary; then a bounded live load after preflight. Record accepted/skipped counts and source limitations.

## T3: Interpret constraints and offer no-match alternatives

**Blocked by:** T1. Real TMDB data is not required to verify this behavior.

**Delivers:** a natural-language request yields visible interpreted restrictions, SQL-filtered semantic results, and explicit optional relaxation when no movies meet the restrictions.

- [ ] Validate included/excluded genres, runtime comparison, year range, and original language; retain mood/themes for semantic search.
- [ ] Show interpreted constraints; handle ambiguous/conflicting/unsupported requirements and model refusal/incomplete output without silently broadening search.
- [ ] Apply deterministic parameterized SQL filters, including exclusion and missing-metadata behavior.
- [ ] Return at most three bounded single-change suggestions whose revised filters have catalog candidates; preserve explicit exclusions.
- [ ] Apply only a selected displayed change; the original request remains visible. Return a useful empty state when no suggestion helps.

**Verification:** API examples with independently expected movie IDs and boundary cases; no-match and explicit-selection browser behavior; no additional model call for relaxation suggestions.

## T4: Stream grounded explanations and evaluate recommendations

**Blocked by:** T2 and T3. Streaming can be developed on fixtures earlier, but full acceptance uses the real reviewed catalog.

**Delivers:** movie cards appear before complete generation, explanations stream progressively, and recommendation quality has recorded evidence.

- [ ] Define and document the POST stream event contract; the browser handles chunk boundaries, progress, metadata, text, and terminal states correctly.
- [ ] Generate explanations about server-selected movies using LangChain and retrieved context; render factual fields and save identities from catalog records.
- [ ] Preserve cards on explanation failure; discard invalid incomplete explanations and handle disconnect/cancellation and provider timeouts.
- [ ] Render model text safely, bound request/output/concurrency, and measure first status, first movie, first explanation text, and total completion separately.
- [ ] Record a fixed 20-request evaluation with predefined expected outcomes, at least 16 acceptable outcomes, and no unsupported facts or hard-constraint violations in accepted results.
- [ ] Optional LangSmith tracing may be enabled after core checks pass, with secrets/content/cost settings reviewed and a functioning untraced fallback.

**Verification:** deterministic API stream/error tests plus the agreed human review and a live latency/token-cost sample. Report failures and limitations rather than tuning acceptance examples after seeing results.

## T5: Keep an isolated personal collection

**Blocked by:** T1. Does not require ingestion completion or explanation generation.

**Delivers:** save, view, and remove catalog movies in My collection across same-browser revisits.

- [ ] Issue a high-entropy anonymous identifier and store ownership server-side with appropriate cookie settings.
- [ ] Every collection operation enforces ownership; repeated saves are idempotent and invalid movie IDs cannot create catalog records.
- [ ] Collection records survive application/database restart on persistent storage; different visitors cannot read or modify one another's collections.
- [ ] Provide useful empty, loading, and error states; document loss of access after browser-state deletion and the stable-origin requirement.

**Verification:** real-database API tests for two visitor identities, uniqueness/foreign-key behavior, and restart persistence; browser save/list/remove flow.

## T6: Demonstrate the complete application on AWS

**Blocked by:** T4 and T5; local checks pass; verified resource estimate and separate explicit paid-resource approval.

**Delivers:** the complete user journey works over public HTTPS, with proven recovery and an off-by-default lifecycle.

- [ ] Verify memory use and current Frankfurt prices, taxes/currency assumptions, retention dates, provider access, and total budget before asking to provision paid resources.
- [ ] Configure one EC2 host, private database, restricted administrative access, Standard CPU credits, private S3 snapshots/backups, least-privilege access, and server-side secrets.
- [ ] Maintain a stable origin during the approved demonstration window; proposed Elastic IP retention is seven days. Verify direct-IP trusted HTTPS, renewal, and startup after a stopped period.
- [ ] Verify actual S3 snapshot upload and database-backup restoration, including collection data, embeddings, and migration state.
- [ ] Perform request → streamed recommendations → save → collection; gracefully stop/start EC2 and confirm the same browser still accesses its collection.
- [ ] Verify rotated structured logs, health checks, request bounds, stop state, and retention/deletion instructions. Record actual costs/resources without implying budget alerts are a hard cap.
- [ ] Produce concise setup/runbook and portfolio evidence explaining SQL, ingestion, RAG, evaluation, deployment trade-offs, and known limitations.

**Verification:** documented local checks followed by one paid-approved AWS smoke, restore, and stop/start cycle; resource/retention inventory and recorded demonstration. Paid provisioning remains independently gated even if this ticket is approved.

## Scheduling and completion

Proposed day targets: T1 day 1; T2 and T3 day 2; T4 day 3; T5 and quality fixes day 4; T6 day 5. This is an aggressive target, not a claim that all work fits a measured duration.

Work blockers-first in fresh implementation sessions. Follow behavior-driven tests at the agreed boundaries, run the required checks, review the completed diff against standards and the originating spec, and update progress with evidence. Do not triage these authored tickets again. Parent and dependency relationships use the documented issue-body convention because the available GitHub connector does not expose native sub-issue/dependency mutations.
