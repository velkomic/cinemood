# Catalog-derived no-match alternatives

Status: accepted by the owner on 2026-11-09; implemented and locally verified
with 105 passing integration tests, browser checks, and independent review. Requested after the owner observed that `under 1 minute` produces
no clickable alternative. This replaces the fixed +15/+30-minute and +/-10-year
probing policy.
It retains the accepted single-change, explicit-selection, preserved-exclusion
behavior. Unsupported factual requirements remain nonblocking warnings.

## Product rules

1. Search with all supported restrictions first. Generate alternatives only when
   SQL eligibility is zero. Weak semantic similarity does not trigger relaxation.
2. Keep exclusions, adult-content acquisition rules, embedding compatibility,
   mood/themes, and every restriction except the proposed change intact.
3. Derive the nearest successful numeric boundary from eligible catalog facts,
   rather than trying fixed increments. Numeric distance is meaningful within
   the same restriction; it is not a universal relevance score.
4. Every displayed option must have at least one candidate under the exact revised
   filters. Show the original restriction, revised restriction, and candidate
   count. State that counts describe filter eligibility, not semantic relevance.
5. Never describe a large change as a small adjustment. Always show both values
   and the numeric difference; no arbitrary magnitude threshold hides an option.
6. Apply only an explicitly selected, previously displayed change. Preserve the
   original request and unsupported warnings. No extra LLM call is needed.
7. If no single change helps, say so and invite manual editing. Do not silently
   combine changes, relax exclusions, or manufacture a recommendation.

## Deriving each alternative

For each active restriction, query the compatible catalog with only that
restriction removed. Continue enforcing all other predicates, including metadata
requirements relevant to the remaining restrictions.

| Restriction | Derived change |
| --- | --- |
| Maximum runtime | Find the shortest known runtime satisfying all other restrictions. For `<= N`, offer that runtime. For `< N`, offer one minute above it, respecting validated bounds. |
| Earliest release year | Find the greatest release year satisfying all other restrictions, including the upper year bound. Lower the earliest year to that value. |
| Latest release year | Find the smallest release year satisfying all other restrictions, including the lower year bound. Raise the latest year to that value. |
| Original language | Offer any original language only if removing that restriction creates candidates. |
| Each included genre | Offer removal of that one required genre only if every other requirement still has candidates. |
| Excluded genres | Never relax. |

Do not suggest a boundary outside the supported schema or a change that fails
validation. Unknown metadata cannot establish a nearest boundary. Recount each
proposed revision using the same shared eligibility predicate as retrieval.

## Selecting a small set

Produce at most one nearest-boundary option per numeric restriction, one
language-removal option, and one option per removable required genre. There are
at most 23 active restrictions in the current schema: runtime, two year bounds,
language, and 19 required genres. Queries are bounded by this schema, not by
incrementally scanning minutes/years until something happens to work.

Keep at most three options. Prefer adjustments that retain a numeric restriction
over removing a language/genre requirement. Use a documented stable presentation
order: runtime, earliest year, latest year, language, then genre name. Do not call
this order a ranking of semantic quality or compare minutes with language changes
using an invented score. Eliminate duplicate candidate sets before the three-option
cap so repeated routes to the same movies do not crowd out distinct choices.

## Example verified against the retained catalog

Read-only query on 2026-11-09 found the shortest compatible movie is Dumbo,
64 minutes. For `A movie under 1 minute`, the proposed option would say:

> No movies meet your runtime limit. The shortest catalog movie is 64 minutes.
> Change “under 1 minute” to “under 65 minutes” (a 64-minute increase): 1 eligible movie.

This count is for the currently observed catalog and no additional restrictions;
implementation must compute it from current data, never hard-code this example.
Dumbo is a large departure from the request and must remain an explicit choice.

## SQL and selection architecture

Keep the existing parameterized eligibility predicate as the common source of
filter behavior. Use `MIN`/`MAX` aggregates over the catalog with one restriction
removed, then revalidate/count the resulting exact revision. No generated SQL,
vector-index change, schema migration, external service or model call is needed.
The existing exact vector ranking runs only after selection with the preserved
semantic query.

Catalog-derived changes can move when the catalog changes. The selection token
must bind the exact displayed change (original interpretation, field/value and
request), not an index recomputed against current data. The closure audit replaced
the self-contained signed payload with a fixed-size opaque reference to bounded
server-side state, avoiding oversized tokens for valid long interpretations.
See `../constraints.md` for expiry, capacity, and the single-process boundary. Validate
that exactly one allowed restriction changed and exclusions did not, and retain
expiry. Recheck eligibility on selection. If no candidates remain, report that
this displayed option is no longer available and ask for a new search; never
substitute a different boundary automatically.

## Verification at agreed seams

Use REST integration tests with real disposable PostgreSQL/pgvector and external
HTTP provider fixtures, plus the existing browser smoke flow:

- `under 1 minute` on licensed fixtures offers `under 89 minutes` for River
  Workshop (88), with no movies returned before selection.
- Adding an Adventure exclusion makes the nearest runtime `under 93 minutes`
  for The Lantern Kitchen (92), preserving the exclusion.
- Strict versus inclusive runtime comparisons preserve their exact semantics;
  the same applies at inclusive release-year boundaries.
- Year alternatives use the nearest successful catalog year even when the gap
  exceeds ten years; language/genre removal changes only the displayed requirement.
- Multiple independently blocking restrictions can yield no single-change
  alternative; return an honest edit invitation without violating any filter.
- Unknown metadata, incompatible embeddings and excluded movies cannot support
  suggestions. Every count must match the same exact revised filters.
- Stable ordering, duplicate-set removal and the three-option cap are verified
  without inventing cross-dimension closeness scores.
- Selection applies the originally displayed bound even after catalog changes;
  stale options become unavailable rather than silently changing their meaning.
- Warnings, original request, exclusions and semantic query survive selection,
  and no extra extraction call occurs. Browser rendering shows both values,
  numeric differences, counts, and a clear explicit-selection action.

Verification evidence for this accepted replacement is recorded in `../progress.md`.
The earlier 89-test evidence covers the preceding fixed-increment implementation.
