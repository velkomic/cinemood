# Interpreted restrictions and explicit alternatives

`POST /api/recommendations` accepts `{"request":"..."}` (1–2,000 characters).
It interprets the English request through LangChain structured output using
`gpt-5.4-mini-2026-03-17`, reasoning disabled, a 1,500-token output limit,
15-second provider timeout, and no retries. Mood/themes become `semantic_query`;
eligible movies are ranked using its embedding. Selection reuses that same query.
No explanation generation or streaming is implemented in this slice.

## Semantics

- All included genres must be present. No excluded genre may be present, including
  on a movie that also has an included genre. Names use the 19 TMDB movie genres.
  Genre OR requests require clarification rather than guessing AND semantics.
- “Under 92 minutes” means `< 92`; “at most 92 minutes” means `<= 92`.
  Hours are interpreted as minutes. Only a maximum runtime is supported.
- Year limits are inclusive: `year_min <= release_year <= year_max`.
  Strict before/after phrases normalize to the preceding/following year.
- Original language is an ISO 639-1 code, not subtitles or dubbing.
- Unknown metadata cannot prove a required restriction. The existing schema
  rejects missing runtime/year/language at ingestion; language equality rejects
  empty/unknown codes, and genre-filtered queries require at least one genre.
- Mood and themes influence vector ranking; they are not factual guarantees.
  Streaming availability, cast, awards, minimum runtime, and other unsupported
  factual requirements are surfaced as unchecked warnings. Search continues using
  supported restrictions and mood/themes; it does not claim the unchecked facts.

The model must return every interpretation field. Strict application validation
rejects extra fields, bad types, unrecognized genres/languages, reversed year
bounds, overlapping included/excluded genres, and incomplete runtime comparisons.
Malformed, truncated, refused, ambiguous, or conflicting interpretation never
falls back to an unrestricted search. Natural-language extraction accuracy still
needs the later human-reviewed evaluation; schema validation cannot prove the
model captured every restriction in the visitor's prose.

## Response and selection contract

Successful responses contain `movies` (0–3), `message`, `original_request`,
`original_interpretation`, current `interpretation`, `applied_change` (null until
selection), `status` (`matches` or `no_match`), and `suggestions` (0–3).
Interpretation fields are `semantic_query`, `included_genres`, `excluded_genres`,
`runtime_minutes`, `runtime_operator` (`lt`/`lte`), `year_min`, `year_max`,
`original_language`, `unsupported_requirements`, and `clarification`.

Unsupported requirements alone do not block search: `matches` responses keep
`interpretation.unsupported_requirements`, include a warning in `message`, and
the UI highlights every unchecked requirement above the movie cards. Warnings
also persist on no-match responses and after explicit relaxation selection.

A `clarification` response has no movies; ambiguous supported restrictions
include their questions and any separate unchecked requirements. Invalid or
refused output returns a generic invitation to edit without claiming a valid
interpretation. An empty compatible catalog returns an actionable empty response
without calling providers. Provider or catalog failures return safe `503` details.
Request validation/body-size failures remain `422`/`413`.

Only zero SQL-eligible movies triggers optional alternatives. The application
tries, in order, maximum runtime +15/+30 minutes (capped at 1,440, retaining the
original comparator), earliest year -10, latest year +10 (within 1800–2200), any
original language, and removal of each required genre individually. This is at
most 24 fixed probes, stopping after three successful suggestions. No probe
changes exclusions or acquisition's adult-content exclusion. Multiple simultaneous
changes and semantic-similarity thresholds are outside this policy.

Each suggestion has `label`, `field`, `candidate_count`, revised `interpretation`,
and opaque `selection`. Counts use the same eligible-catalog SQL as retrieval,
including compatible embeddings; counts describe filter eligibility, not relevance.
If no bounded change helps, the response invites an edited request.

After an explicit click, POST `{"request":"<original>","selection":"<token>"}`
to the same endpoint. A server-authenticated token binds the original request,
interpretation and one displayed change. The client cannot supply revised filters.
No new extraction call is made; SQL rechecks eligibility, and only then is the
unchanged semantic query embedded for retrieval. If the catalog has changed so
no candidates remain, return an empty state without further automatic changes.
The original request and restrictions remain in the response and UI.

Tokens expire after 15 minutes and use an ephemeral per-application signing key.
Tampering, a different request, expiry or application restart returns `400` and
asks for a new search. This is deliberately a single-process demo; multiple
workers/replicas would need shared key configuration or durable selection state.
The token is authenticated, not encrypted, and is not a visitor identity.

## SQL and verification

No schema migration is needed: the existing normalized movie/genre/embedding
schema already holds these facts. Parameterized predicates run before exact
cosine ordering and the stable movie-ID tie break. `NOT EXISTS` over required
names enforces all included genres; a separate `NOT EXISTS` rejects any excluded
genre. These correlated predicates avoid multiplying movie rows in a genre join.
The final three movies receive their sorted genre arrays afterward.

Only a fixed `<` or `<=` operator enters SQL text. All values, arrays, language
codes and query vectors are bound parameters. Candidate counts and retrieval
share this predicate, preventing divergent filtering policies.

REST integration tests use disposable real PostgreSQL/pgvector databases and
fictional licensed metadata. Only external OpenAI HTTP responses are simulated;
no database or internal collaborator is mocked. Browser verification exercises
visible restrictions, no-match, explicit selection, preserved original/exclusions,
unsupported requirements, empty state, provider failure and mobile layout.
See `progress.md` for executed evidence and limits; deterministic extraction
fixtures do not establish live-model compatibility or interpretation quality.
