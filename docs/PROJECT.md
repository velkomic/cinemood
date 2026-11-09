# CineMood

Status: product interview and specification review complete. The specification and six implementation tickets are published; see `SPEC.md` and `plans/MVP.md`. T1 is implemented and accepted with real PostgreSQL/pgvector, deterministic integration tests, and a bounded live OpenAI embedding/browser check. The user accepted local verification instead of a required hosted CI run; GitHub Actions remains configured. T2 is implemented with 52 passing integration checks and the full 1,000-movie TMDB catalog loaded and verified through live OpenAI/Discover checks. The retained catalog is available locally on port 58000; operating instructions are in `ingestion.md`. See `progress.md` for evidence and limitations.

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
- Retrieve candidate movies with pgvector and use LangChain/OpenAI to explain up to three recommendations. Render title, release year, genres, runtime, and overview from database records. Preserve retrieved results with an explanation-unavailable message if generation fails.
- Treat progressive streamed responses as a priority for the recommendation experience; the event contract and validation approach remain to be agreed.
- Use a single English natural-language request containing visitor preferences and constraints. Extract included/excluded genres, maximum film length, release-year range, and original language into validated fields; use mood and thematic preferences for semantic matching. Flag unsupported factual requirements instead of implying they were checked.
- When the catalog has no matches, offer up to three catalog-backed suggestions, each changing one supported constraint. Rerun recommendations only after the visitor selects a suggestion, preserve the original request and explicit exclusions, and invite an edited request if no simple adjustment helps. Implement this inside the application without an additional model call.
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

## Planning workflow

Use wayfinder to resolve the open decisions, then synthesize an agreed specification and vertical implementation tickets. GitHub Issues are the tracker; see `agents/issue-tracker.md`.

Create architecture, roadmap, milestone plans, and ADRs as their contents are resolved. Record verified implementation separately in `progress.md`.
