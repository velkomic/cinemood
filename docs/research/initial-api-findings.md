# Initial API findings

Checked 2026-11-09 against official documentation. These findings inform planning; no integration has been implemented or tested.

## TMDB rate limiting

[TMDB rate-limit guidance](https://developer.themoviedb.org/docs/rate-limiting) states that the legacy limit of 40 requests per 10 seconds was disabled. It describes a changeable upper limit around 40 requests per second and instructs clients to respect HTTP 429 responses.

Planning implication: request pacing, bounded retries, and resumable ingestion address rate limits directly. A schedule controls when batches run and is a separate product/operational choice; rate limits alone do not establish the need for scheduled ingestion.

Data licensing, caching rights, API access, and the actual catalog selection still need investigation.

## TMDB selection and attribution

[Discover movies](https://developer.themoviedb.org/reference/discover-movie) supports sorting, pagination, language selection, vote-count filters, and exclusion of adult results. Proposed selection is descending vote count, skipping unusable records until 1,000 qualifying movies are stored. This favors widely rated movies and does not establish mood or genre coverage; assess that in the evaluation set. Requesting English descriptions is distinct from restricting films to English original language.

[TMDB FAQ](https://developer.themoviedb.org/docs/faq) says non-commercial API use is free with attribution and requires an approved logo and its prescribed endorsement disclaimer in an About or Credits section. This does not by itself resolve permissions for every proposed use of cached data or embeddings; those remain to be checked against the applicable terms before ingestion.

## LangChain RAG

[LangChain retrieval documentation](https://docs.langchain.com/oss/python/deepagents/retrieval) describes a two-step approach that queries an existing knowledge base and supplies retrieved content to the model. It characterizes retrieval-before-generation as straightforward and predictable.

Proposed role: use LangChain to compose the retrieval-context-generation workflow while retaining explicit application SQL and data modeling. This is a recommendation, not an accepted architecture decision. Exact integrations and versions remain to be checked.

## Streaming, interpretation, and optional tracing

Checked 2026-11-09. [LangChain streaming](https://docs.langchain.com/oss/python/langchain/streaming) supports incremental model output and progress updates. Proposed application design: stream status and database-backed movie metadata, followed by explanation deltas over a POST response consumed by browser fetch. Streaming reduces waiting for the complete answer; it does not remove request interpretation or retrieval latency before generation starts.

[Structured output](https://docs.langchain.com/oss/python/langchain/structured-output) supports schema-shaped responses, including direct model usage without an agent. Proposed use is extracting a bounded set of movie constraints into a validated schema, then mapping allowed values to parameterized SQL. A valid schema does not guarantee correct interpretation; show parsed constraints and test ambiguity and unsupported requests.

[LangSmith tracing quickstart](https://docs.langchain.com/langsmith/observability-quickstart) describes capturing request steps and inputs/outputs, with account credentials and environment configuration. Optional tracing can cover application stages as well as model calls. Do not assume SQL or arbitrary Python code is automatically traced by enabling LangChain integration. Pricing and data-retention behavior have not been checked in this pass.
