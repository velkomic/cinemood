# CineMood

Status: product interview and specification review complete. The specification and six implementation tickets are published; see `SPEC.md` and `plans/MVP.md`. T1 is implemented and accepted with real PostgreSQL/pgvector, deterministic integration tests, and a bounded live OpenAI embedding/browser check. The user accepted local verification instead of a required hosted CI run; GitHub Actions remains configured. T2 is accepted and closed with 52 passing integration checks and the full 1,000-movie TMDB catalog loaded and verified through live OpenAI/Discover checks. T3 (#4) implements validated restrictions, nonblocking warnings for unsupported requirements, and catalog-derived single-change alternatives. The current implementation, including supported-runtime warning reconciliation and bounded opaque selection state, is verified with 120 local integration tests, desktop/mobile browser checks, and independent review; see `progress.md`. T3 is accepted by the owner and closed on GitHub with all acceptance criteria checked. T4 (#5) is complete, owner-accepted and closed on GitHub with 166 passing integration checks, browser/static checks, and a reconciled 17/20 evaluation assessment based on the owner's review plus verified fixes. Cases 13, 14 and 18 remain excluded; the known grounding/constraint limitations are preserved rather than counted as passes. T5 (#6), isolated personal collections, is implemented and locally verified with 187 passing integration checks, desktop/mobile browser flow, actual database/application restart persistence and independent review; it is owner-accepted and closed on GitHub. T6 (#7), the AWS demonstration, is the next slice and still requires explicit approval of its concrete paid-resource plan before provisioning. The retained catalog is available locally on port 58000; operating instructions are in `ingestion.md`. See `progress.md` for evidence and limitations.

## Agreed constraints

- Build an explainable movie discovery application as a portfolio and learning project.
- Recommendations use the visitor's current request and explicit preferences. Accounts, saved preference profiles, and viewing history are outside the first release.
- Target an MVP within four to five days of intensive work. Production readiness is not a release requirement.
- Plan for AWS deployment, with the application turned off by default and started for demonstrations or verification.
- Include one successful AWS demonstration in the four-to-five-day target after local checks pass. Prioritize a tested local application if the deployment work exceeds the time available.
- Provide a recommendation page with explanations and supporting movie details, plus a personal collection where visitors can save, view, and remove movies. Identify collections using an anonymous browser identifier, persist them in PostgreSQL, and support return visits in the same browser. Cross-device access is outside the MVP.
- Initially load 1,000 usable movies with English descriptions, ordered by descending TMDB vote count, excluding adult results and allowing any original language. Use a bounded, resumable ingestion job with manual and scheduled invocation, pacing, retries, and duplicate prevention; stop fetching when the target is reached. Expand the catalog after the MVP works.
- Use EUR 10 total as the provisional target for initial ingestion, OpenAI experiments, and a short AWS demonstration. This target is not an automatic billing cap or authorization to provision resources.
- Use a repeatable evaluation set of approximately 15–20 requests covering relevance, filter compliance where filters are supported, grounded explanations, and insufficient-match behavior.
- Test behavior through the REST API, ingestion command, and one browser smoke flow. Assess relevance on 20 fixed human-reviewed requests with an initial target of at least 16 acceptable results; automate collection isolation, persistence, resumability, duplicate prevention, and recommendation-ID validity checks.
- Retrieve candidate movies with pgvector and use LangChain/OpenAI to explain up to five recommendations. Render title, release year, genres, runtime, and overview from database records. Preserve retrieved results with an explanation-unavailable message if generation fails.
- Treat progressive streamed responses as a priority for the recommendation experience; the event contract and validation approach remain to be agreed.
- The owner-approved 2026-11-10 refinement allows a list of original languages
  with OR semantics (for example English or French), while retaining every
  other supported restriction. Explanation text should directly connect story
  details to the request, with brief specific caveats only when useful.
- Use a single English natural-language request containing visitor preferences and constraints. Extract included/excluded genres, maximum film length, release-year range, and original language into validated fields; use mood and thematic preferences for semantic matching. Continue searching with supported restrictions when factual requirements are unsupported, and prominently warn which requirements were not checked. Unsupported requirements alone do not require clarification (owner-approved T3 follow-up).
- When the catalog has no matches, offer up to three catalog-backed suggestions, each changing one supported constraint. Derive runtime/year boundaries from the nearest successful catalog facts, display exact before/after values and differences, and remove duplicate candidate sets; fixed increments are superseded by the owner-approved `plans/catalog-driven-relaxation.md` policy. Rerun recommendations only after the visitor selects a suggestion, preserve the original request and explicit exclusions, and invite an edited request if no simple adjustment helps. Implement this inside the application without an additional model call.
- LangSmith tracing is an optional enhancement, not a prerequisite for the MVP.
- Use LangChain for structured constraint extraction, OpenAI embeddings, and streamed context-grounded explanations; an autonomous agent or LangGraph workflow is unnecessary for the agreed sequence.
- Serve Discover and My collection views using a small HTML/CSS/JavaScript frontend within FastAPI.
- Run FastAPI and PostgreSQL/pgvector with Docker Compose locally and on one EC2 instance for the demonstration. Keep the database private to the application network. Manage database backups and recovery ourselves; use S3 for ingestion snapshots and recovery backups.
- Agree on MVP scope, architecture, evaluation, deployment strategy, and a milestone roadmap before application implementation.
- Creating paid AWS infrastructure requires explicit user approval.

## Technology choices

Python/FastAPI, PostgreSQL with pgvector, HTML/CSS/JavaScript, LangChain/OpenAI, TMDB, Docker Compose, EC2, and S3 are the architecture reflected in the agreed user journey. pytest and GitHub Actions are configured verification tools; executed checks are recorded in `progress.md`. Model snapshots and detailed deployment settings remain technical proposals in `SPEC.md` and the cited research.

## Remaining verification and deployment decisions

- Implement the accepted specification one published ticket at a time; `progress.md` identifies the next ticket and verified state.
- Proposed models: `text-embedding-3-small` and `gpt-5.4-mini-2026-03-17`; quality, latency, account access, and limits need implementation verification. See `research/models-and-api-budget.md`.
- Review the current TMDB account/API terms for caching, private snapshots/backups, and third-party processing before live ingestion; accessible docs did not settle those clauses. See `research/tmdb-data-use.md`.
- Proposed HTTPS and stable-origin solution: direct-IP certificate and Elastic IP retained through a seven-day demonstration window. Verify current regional pricing and local memory use before proposing paid provisioning. See `research/deployment-verification.md`.

## Frontend redesign

The owner selected **Screening lounge refined** on 2026-11-10 after reviewing
concrete sketches: the lounge logo and recommendation columns, compact request
entry, and text Details actions. The local implementation adds snapshot-derived
posters, title-led image fallback, responsive details, controlled initial poster
motion, and matching collection presentation while preserving the search and
collection contracts. `progress.md` records verification and review evidence.
Additional batches and contextual follow-ups remain separate specification work
in `plans/frontend-redesign-spec-work.md`; no such search extension is implemented
or published as a ticket. This work does not authorize T6 paid provisioning.

## Planning workflow

The owner requested two architecture-review follow-ups for later work on
2026-11-11: [shared movie-card lifecycle](https://github.com/velkomic/cinemood/issues/8)
and [browser recommendation-session state](https://github.com/velkomic/cinemood/issues/9).
The owner completed #8's design review and approved its `ready-for-agent`
publication. The accepted contract in `plans/movie-card-lifecycle.md` covers
shared card presentation/lifecycle, page-wide Details selection, collection
ordering safeguards, verification and concurrent #8/#9 module development with
sequential page integration. #9 remains `needs-triage` pending its own session
interface review. The frontend baseline is `8bf42e1`; both branches must use the
same documentation handoff commit above it. These follow-ups do not expand MVP
product scope or block T6. Implementation and push are outside this design task.

The 2026-11-10 frontend redesign interview is captured in
[`plans/frontend-redesign.md`](plans/frontend-redesign.md) and root `PRODUCT.md`.
The owner confirmed a wide dark cinematic direction, poster-led comparison,
controlled ambient motion, compact follow-ups, and desktop side-panel/mobile
full-screen film details. The owner has selected and authorized the refined lounge layout; extra result
batches and contextual follow-ups need a behavior specification and ticket plan
before implementation. These requirements are not verified capabilities.

Use wayfinder to resolve the open decisions, then synthesize an agreed specification and vertical implementation tickets. GitHub Issues are the tracker; see `agents/issue-tracker.md`.

Create architecture, roadmap, milestone plans, and ADRs as their contents are resolved. Record verified implementation separately in `progress.md`.


## Owner UX refinement — 2026-11-10

The owner requested and authorized four refreshable spotlight films with a browse
control, local search-field focus, Enter/Shift+Enter semantics, inline selected-card
synopsis/metadata/TMDB links replacing sidebar/modal details, up to five
recommendations with compact explanations, tighter desktop dimensions, adaptive
small result sets and polished save states. These refinements retain Screening
lounge refined. They supersede the earlier three-result and side-panel design
choices, while preserving supported restrictions, explicit relaxation, streaming
fallback and anonymous collection ownership. Extra recommendation batches and
contextual follow-ups remain separate specification work. See progress.md for
verified evidence and runtime limitations; no tracker publication or paid-resource
approval is implied.


## Owner UX refinement — 2026-11-11

The owner authorized five spotlight movies, stronger poster-derived background
color, stable Save transitions, and navigation that hides on downward scroll and
returns on upward scroll or pointer proximity to the viewport top. Keep the
existing lounge design, responsive layout and reduced-motion support. This
supersedes the four-film spotlight count; search and collection contracts remain.
