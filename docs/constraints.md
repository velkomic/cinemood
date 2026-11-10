# Interpreted restrictions and explicit alternatives

`POST /api/recommendations` accepts `{"request":"..."}` (1–2,000 characters).
It interprets the English request through LangChain structured output using
`gpt-5.4-mini-2026-03-17`, reasoning disabled, a 1,500-token output limit,
15-second provider timeout, and no retries. Mood/themes become `semantic_query`;
eligible movies are ranked using its embedding. Selection reuses that same query.
The streaming endpoint uses the same interpretation and selection rules; see
[streaming.md](streaming.md).

## Semantics

- All included genres must be present. No excluded genre may be present, including
  on a movie that also has an included genre. Names use the 19 TMDB movie genres.
  Genre OR requests require clarification rather than guessing AND semantics.
- “Under 92 minutes” means `< 92`; “at most 92 minutes” means `<= 92`.
  Hours are interpreted as minutes. Only a maximum runtime is supported.
- Year limits are inclusive: `year_min <= release_year <= year_max`.
  Strict before/after phrases normalize to the preceding/following year.
- `original_languages` is a list of up to 20 distinct ISO 639-1 codes, not
  subtitles or dubbing. `[]` means unrestricted; `["fr"]` means French;
  `["en", "fr"]` means English OR French. Explicit language alternatives do
  not require clarification, even when the visitor has not chosen between them.
  This owner-approved 2026-11-10 refinement replaces the singular request field.
  The movie record still has one `original_language`; no catalog migration is needed.
- Unknown metadata cannot prove a required restriction. The existing schema
  rejects missing runtime/year/language at ingestion; language-list membership rejects
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
`original_languages`, `unsupported_requirements`, and `clarification`.

A maximum-runtime restriction remains supported even when no catalog movie can
meet it. The extraction prompt forbids listing supported restrictions as unchecked.
After validation, interpretation removes a complete literal runtime warning only
when its comparator and numeric bound exactly match the extracted runtime (with
exact minute/hour conversion). This reconciliation happens once, before response
and selection-token creation. It never strips mixed factual claims, minimum-runtime
requirements, mismatched comparisons, or a runtime not present in validated fields.
Unrecognized wording remains visible rather than being silently discarded.

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

Only zero SQL-eligible movies triggers optional alternatives. For each active
restriction, remove only that restriction and query the compatible catalog:

- Runtime: use the shortest remaining runtime, plus one minute for a strict `<`
  comparison (or the runtime itself for `<=`), within the 1–1,440 schema bounds.
- Earliest year: lower to the greatest remaining release year, keeping the upper
  bound. Latest year: raise to the smallest remaining year, keeping the lower bound.
- Language: remove the complete allowed-language list only after an explicit
  selection, if allowing any original language produces candidates. Other
  suggestions preserve the full original list.
- Genres: remove one required genre, trying names in alphabetical order.

Every exact revision is validated and checked with the shared eligibility SQL.
Numeric options show before/after values and the difference, even for large
changes. Keep at most three distinct candidate sets in runtime, earliest-year,
latest-year, language, then genre-name order. This is presentation order, not a
semantic-quality score. There are at most 23 active restrictions; generation uses
at most 26 aggregate queries (two per numeric restriction, one per categorical
option), and stops when three distinct options have been found. All aggregates
run in one read-only REPEATABLE READ transaction so boundaries and counts refer
to a consistent catalog snapshot. No minutes/years are scanned incrementally.
Exclusions and adult-content acquisition rules are never relaxed. Multiple
simultaneous changes and semantic-similarity thresholds remain outside this policy.

Each suggestion has `label`, `field`, `candidate_count`, revised `interpretation`,
and opaque `selection`. Counts use the same eligible-catalog SQL as retrieval,
including compatible embeddings; counts describe filter eligibility, not relevance.
If no single-constraint change helps, the response explicitly says so and invites
an edited request.

After an explicit click, POST `{"request":"<original>","selection":"<token>"}`
to the same endpoint. A server-authenticated token binds the original request,
interpretation and the exact field/value displayed. It does not store an index
that could acquire a different meaning after catalog changes. The client cannot supply revised filters.
No new extraction call is made; SQL rechecks eligibility, and only then is the
unchanged semantic query embedded for retrieval. If the catalog has changed so
no candidates remain, report that the displayed option is no longer available
and ask for a new search. Do not substitute a newly computed bound.
The original request and restrictions remain in the response and UI.

Tokens are 43-character opaque identifiers with 256 bits of random entropy;
request/interpretation text is kept in bounded per-application memory rather than
encoded into the token. Thus a displayed option remains selectable even with a
maximum-length Unicode request or long unchecked-requirement descriptions.
Each stored selection binds the original request and exact field/value and is
validated again before use. Client-supplied revised filters are still forbidden.

Selections expire after 15 minutes or an application restart. A locked store
holds at most 128 pending displayed options; expired entries are pruned lazily.
Complete responses reserve their slots atomically. Capacity exhaustion returns
safe `503` feedback asking the visitor to retry; it never silently evicts an
unexpired option already displayed. This is deliberately a single-process demo;
multiple workers/replicas would need shared selection storage. Invalid, expired,
wrong-request or previous-instance tokens return `400` and ask for a new search.
The token is a bearer reference to a proposed change, not a visitor identity.

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
