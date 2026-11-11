# CineMood MVP specification

Status: accepted for MVP implementation planning on 2026-11-09 and published as [CineMood MVP specification](https://github.com/velkomic/cinemood/issues/1). No application implementation has been verified. Technical defaults require the stated runtime checks; paid AWS provisioning requires separate explicit approval.

## Owner-approved UI amendment — 2026-11-10

The owner's six-item UX request supersedes the initial three-film limit: retrieve
up to five distinct catalog films using the same validated restrictions and stable
similarity/ID ordering. Shorter explanations target 20–35 words with a 420-character
validation ceiling and retain catalog-fact fallback. Additional result batches
and contextual conversation state remain outside this amendment.

The four-film spotlight refreshes on homepage/history return and explicit Shuffle
films. Available unseen records precede previous IDs; a small catalog may repeat
records and must disclose exhausted alternatives. Shuffle errors retain the prior
selection and permit retry. Preview sampling is not relevance/popularity ranking.

Input focus stays local; Enter submits except during composition, Shift+Enter adds
a newline. Film details expand inline in one selected card with accessible toggle
state, Escape/close and focus return. TMDB links come only from catalog TMDB IDs.
Cards keep their columns, shrink responsively and adapt to fewer results. Save
shows busy, retry and persistent Saved feedback without changing collection
ownership or idempotence. This is direct owner authorization, not a claim that the
original published GitHub specification has been edited.

## Problem Statement

Visitors know the mood or constraints of a film they want but cannot easily translate that into a useful shortlist. The project owner needs a small, demonstrable AI application showing Python, SQL, ingestion, grounded generation, testing, and AWS operations within four to five intensive days.

## Solution

A visitor describes a film in English. CineMood shows its interpretation, retrieves from a bounded catalog, displays up to three movies with database-backed facts, and progressively explains their relevance. Visitors can save choices to a same-browser collection. If no catalog movies meet the supported constraints, it offers specific optional changes rather than silently changing the request.

## User Stories

1. As a visitor, I want to describe a desired film naturally, so that I do not need to know its title.
2. As a visitor, I want mood and thematic preferences to influence retrieval, so that suggestions reflect the experience I want.
3. As a visitor, I want genre inclusions/exclusions, film length, release years, and original language interpreted, so that supported restrictions are respected.
4. As a visitor, I want to see interpreted restrictions, so that I can correct a misunderstanding.
5. As a visitor, I want unsupported factual requirements identified, so that I know what the system has checked.
6. As a visitor, I want conflicting restrictions clarified, so that the application does not guess silently.
7. As a visitor, I want a shortlist of up to three catalog movies, so that choosing remains manageable.
8. As a visitor, I want title, year, genres, runtime, and overview from catalog records, so that movie facts are independent of generated prose.
9. As a visitor, I want visible progress and streamed explanations, so that I can begin reading before the complete answer arrives.
10. As a visitor, I want explanations supported by retrieved details, so that I can understand why each movie was suggested.
11. As a visitor, I want retrieved cards retained when generation fails, so that a model failure does not discard useful search results.
12. As a visitor, I want optional catalog-backed suggestions when no movies meet my restrictions, so that I can broaden the request knowingly.
13. As a visitor, I want relaxation applied only after I select it, so that my original preferences remain under my control.
14. As a visitor, I want explicit exclusions preserved, so that a suggestion does not override something I ruled out.
15. As a visitor, I want to save, view, and remove movies, so that I can return to promising choices.
16. As a visitor, I want saved choices to persist in the same browser through application restarts, so that I can use them later.
17. As a visitor, I want my collection isolated from other visitors, so that anonymous access does not expose saved choices.
18. As the project owner, I want repeatable, resumable ingestion, so that interruptions do not duplicate movies or waste work.
19. As the project owner, I want scheduled and manual batches to stop at the target, so that catalog acquisition is bounded.
20. As the project owner, I want snapshots and embedding metadata, so that I can explain the data's origin and reproduce indexing.
21. As the project owner, I want automated behavior checks and a fixed human-reviewed evaluation, so that correctness and recommendation quality have separate evidence.
22. As the project owner, I want a public HTTPS demonstration after local validation, so that others can try the application.
23. As the project owner, I want tested backup restoration and explicit startup/shutdown procedures, so that I can operate the self-managed database.
24. As the project owner, I want an off-by-default deployment with a documented retention budget, so that demonstration infrastructure has a controlled lifecycle.
25. As the project owner, I want concise progress and decision records, so that future implementation sessions continue from verified facts.

## Implementation Decisions

### Application and ownership

- FastAPI serves a small HTML/CSS/JavaScript interface and REST endpoints; Discover and My collection are views of the same application. PostgreSQL with pgvector runs alongside it under Docker Compose.
- A high-entropy anonymous browser cookie identifies a collection. Use HttpOnly, Secure in HTTPS environments, and an appropriate SameSite policy; enforce ownership in every collection query and validate request origin on mutations. Development configuration must be explicit rather than weaken hosted cookies.
- Repeated saves are idempotent; removal affects only the visitor's collection. Clearing browser state loses access; cross-device access and account recovery are outside scope. The hosted origin must remain stable during the demonstration window.
- Keep SQL explicit, parameterized, and migration-managed. Proposed relational records cover movies, genres and their join, embedding metadata/vectors, ingestion checkpoints, anonymous collections, and collection items. Enforce primary/foreign keys and uniqueness rather than relying solely on application checks.

### Catalog and ingestion

- Target 1,000 unique usable movies, discovered by descending TMDB vote count, with adult results excluded, English descriptions requested, and no original-language restriction. Ranking is a paginated acquisition order, not a claim of an atomic global snapshot.
- Required records include source ID, localized title/overview, original language, release date/year, genres, runtime, vote count, and provenance/fetch time. Validate missing or unusable metadata, report skips, and define the usability rule before the live run. Unknown values must not satisfy a hard constraint that requires them.
- Perform conservative paced requests, bounded retry/backoff, and durable checkpoints. Honor Retry-After when supplied. Set a per-run request/page budget and report an incomplete catalog if the source or budget prevents reaching the target.
- Manual and scheduled invocation call the same bounded job. Use a single active ingestion run/lock; deduplicate by source ID, resume safely, and do not fetch more once the target is reached. Expansion is a later explicit target change, not continuous ingestion by default.
- Store private raw snapshots in S3 once the applicable data-use terms are reviewed. Local runs may retain a filesystem snapshot using the same documented format until AWS resources are approved; verify S3 operation in the deployment slice. Keep credentials out of snapshots and logs.
- Produce one searchable document per movie; embed only new or changed content. Persist content hash and embedding configuration, and use compatible catalog/query embeddings. Backups must include both data and embedding metadata.
- Include TMDB's required approved attribution assets and notice. Before live ingestion/storage/third-party processing, review the applicable account/API terms and record retention/processing obligations. Accessible documentation did not resolve all of these clauses; this is an unresolved preflight check, not an assertion that the design is prohibited. Independently licensed fixtures support initial work.

### Retrieval, generation, and relaxation

- Extract supported constraints into a validated schema, then map whitelisted values to parameterized SQL predicates. Included/excluded genres, maximum runtime, year range, and original language are hard constraints; mood and thematic preferences guide semantic retrieval. Define boundary semantics such as “under 90 minutes” versus “at most 90 minutes” in acceptance examples.
- Surface interpreted constraints. Invalid, contradictory, ambiguous, refused, or incomplete extraction must not silently become an unconstrained search. Ask for a corrected request and identify unsupported factual requirements such as current provider availability.
- Proposed defaults: `text-embedding-3-small` with 1,536 dimensions and `gpt-5.4-mini-2026-03-17` with reasoning disabled, through LangChain's OpenAI integration. Verify account access, pin compatible dependency versions, and evaluate quality/latency before treating these choices as verified.
- Start with exact cosine search and a deterministic tie break. Rank eligible candidates and return up to three. Approximate vector indexing, hybrid search, a learned reranker, agent orchestration, and LangGraph are outside the initial design.
- Choose movie identities on the server before explanation generation. Stream explanatory text about the fixed selected set; generated text never creates a catalog card or controls a save identity. Catalog facts come from the database. Prompt grounding and output validation do not by themselves prove every generated claim; the evaluation must assess support.
- With zero eligible catalog records, evaluate a bounded set of single-constraint changes. Offer at most three that actually produce candidates. Preserve exclusions and adult-content rules. Counts describe filter eligibility, not semantic relevance. Apply only the displayed change after explicit visitor selection, then rerun retrieval.
- Do not invent a similarity cutoff as a confidence measure. Use the fixed evaluation set to document insufficient-relevance behavior and the limitations of the small catalog. Return a useful empty state if no safe bounded relaxation helps.

### Streaming and failures

- Proposed transport: POST request with a streamed response carrying server-sent events, consumed using browser fetch. Define the event schema before implementation: request ID, stage/status, interpreted constraints or clarification, selected movie metadata, explanation deltas, relaxation suggestions where relevant, and a terminal complete/error event.
- Emit actual stage progress promptly; do not expose internal model reasoning. The browser renders structured metadata and generated text safely, without interpreting model output as HTML.
- The stream terminates explicitly. On explanation failure or final validation failure, discard unusable explanation text and keep selected movie cards with a clear fallback. On retrieval/extraction failure, do not claim valid recommendations. Handle a visitor cancelling or disconnecting without leaving an unbounded generation task running.
- Measure request-to-first-status, first movie metadata, first explanation text, and total completion, plus individual stage durations. No latency target is claimed as measured before tests on the chosen setup.
- Bound request size, output tokens, generation time, retries, and concurrent requests. Add basic request limiting before public exposure. Keep provider credentials on the server and keep detailed errors out of browser responses.

### Deployment and cost

- Local validation precedes AWS. Proposed resources: one Frankfurt Linux x86 `t3.small`, Standard CPU credits, 20 GiB baseline gp3, private S3 data under 1 GB initially, and an Elastic IP retained for a seven-day demonstration window. Verify local memory use before committing to 2 GiB.
- Public entry is HTTPS through a reverse proxy. Proposed direct-IP certificates avoid a new domain, but short certificate lifetime requires verified issuance/renewal and startup handling after shutdown. Expose only necessary web ports; keep PostgreSQL private, use restricted administrative access, and apply least-privilege IAM/S3 permissions.
- Retain the public address through stop/start to preserve browser collection identity. Releasing it may lose visitor access at a future origin; document the retention boundary and charge. A stable existing domain/subdomain is an alternative if available.
- Back up PostgreSQL privately to S3, document retention/deletion, and test restoration once. Raw movie snapshots alone are not a backup of collections, schema state, or embedding metadata.
- Keep rotated structured logs with request IDs, stage durations, and actionable errors; verify a health endpoint. Optional CloudWatch shipping and LangSmith tracing are enhancements whose costs and data handling need explicit configuration, not baseline dependencies.
- GitHub Actions runs local correctness checks on contributions. Deployment may be manual and documented for this MVP; automated CD is optional. Avoid building large images on a CPU-credit-limited demonstration host where possible.
- The EUR 10 target covers initial AWS and OpenAI experiments. Exact Frankfurt prices, applicable taxes/currency conversion, account access, and billing settings remain to be checked before provisioning. Written estimates are not hard billing caps. Paid AWS resources require separate explicit approval of the concrete resource and retention plan.

## Testing Decisions

The user accepted tests at REST API and ingestion-command boundaries, one browser smoke flow, and a separate 20-request human-reviewed recommendation evaluation. No pre-existing application tests were found.

- Test externally observable behavior and outcomes, not private helpers or mocked internal call order. Use a real ephemeral PostgreSQL/pgvector database for API/ingestion integration behavior, licensed fixed metadata, and deterministic provider responses at external service boundaries. Keep live provider checks optional and explicitly cost-bounded.
- Cover SQL boundary semantics, exclusion handling, missing metadata, conflicting/unsupported requests, malformed extraction, streaming partial data and terminal failures, unknown movie IDs, duplicate saves, collection isolation, and persistence after restart.
- Ingestion verification must demonstrate bounded progress, restart after interruption, duplicate prevention, one active run, changed-content behavior, and zero additional fetches after reaching the target. Simulate 429 and transient errors at the external TMDB boundary.
- Relaxation tests verify unchanged original constraints until selection, single displayed changes only, preserved exclusions, catalog-backed suggestions, and a useful no-suggestion state.
- The browser smoke flow covers request → streamed cards/explanation → save → collection → remove. Include one deployed stop/start collection-continuity check and one backup-restoration check in deployment verification.
- The 20-request set includes mood requests, hard-constraint boundaries, exclusions, unsupported/ambiguous requests, no-match relaxation, and failure behavior. Define expected outcomes in advance. Target at least 16 acceptable outcomes, with no hard-constraint violations, fabricated catalog facts, or unsupported explanation claims in accepted results. Clarification/empty outcomes count as correct where predeclared, rather than requiring a movie for every prompt.
- Record evaluation judgments, actual tokens/cost, timing distributions, environment/model version, and limitations. CI does not claim subjective relevance is deterministic or that provider uptime is tested by fixture-based runs.

## Out of Scope

Accounts, cross-device collections/recovery, viewing history, feedback-driven personalization, conversational memory, streaming-provider availability, automatic silent constraint relaxation, multilingual query support, a large continuously refreshed catalog, autonomous agents, reranking without evidence, production availability guarantees, ECS/Kubernetes/ALB/RDS, and mandatory automated deployment.

## Further Notes

The six reviewed vertical slices and blocking edges are published as GitHub issues and indexed in the MVP implementation plan. The first slice uses licensed fixtures while credential and data-use preflight checks proceed. The five-day schedule is a target and has little slack; optional tracing and CD should yield to verified core behavior. Research findings document sources, estimate assumptions, and outstanding external checks; no paid API calls or AWS resources were created during planning.
