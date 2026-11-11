# Frontend redesign: specification work

Owner refinement (2026-11-10): the latest UX request supersedes the earlier
three-result/sidebar composition. Current implementation targets up to five
recommendations, four refreshable spotlight films and inline card details on all
screen sizes. Additional recommendation batches and contextual follow-ups remain
separate behavior specifications. `docs/progress.md` records current verification.

Status: proposals and open decisions, 2026-11-10. The completed interview in
`frontend-redesign.md` remains the source of owner requirements. No new search
behavior is approved or implemented by this document.

## Preserve during the visual redesign

Keep Discover, streamed explanations, catalog facts, interpreted restrictions,
unchecked-requirement warnings, explicit single-restriction suggestions,
cancellation and recovery, and anonymous collection save/list/remove behavior.
Keep the existing ownership/cookie safeguards and TMDB attribution. Preserve
useful movie facts when explanations fail. Exercise these states on desktop
and mobile after implementation, including keyboard details dismissal and
focus return, reduced motion, failed requests, and missing imagery.

The current application accepts a request and an optional relaxation selection;
it retrieves up to three films. It has no batch cursor, exclusion history, or
contextual refinement contract. The original frontend rendered title, facts
and overview with no poster field. The redesigned UI reads posters from retained
snapshots through a display endpoint, without extending the search payload. These are implementation observations,
not a claim that the requested extensions exist.

## Additional result batches

Decide and publish the following before extending retrieval:

- **Eligibility and ordering:** define whether exhaustion means every SQL-eligible
  movie, a bounded semantic shortlist, or a relevance-qualified pool. Specify
  deterministic similarity ordering and an identity tie-break. SQL eligibility
  alone does not establish relevance; catalog acquisition by vote count does
  not establish a recommendation quality ranking.
- **Session consistency:** decide whether a search freezes ordered movie IDs or
  uses a catalog/version-aware cursor, and how catalog changes affect it.
  Bound retention, session capacity, cursor expiry, and restart behavior.
- **No repeats:** define identity across batches, retries, and refinements;
  enforce exclusions server-side. Decide whether already-saved films are eligible.
- **Navigation:** define previous-set retention and whether revisiting a set
  reuses facts and explanations without fresh provider work. Specify final sets
  with one or two films, an explicit exhausted state, and expired-session recovery.
- **Transactions and failures:** define double clicks, concurrent requests,
  cancelled and failed batches, retry idempotence, and when a cursor advances.
  Keep the current set visible and usable until replacement facts are ready.
- **API and stream contract:** specify bounded opaque session/cursor fields,
  batch identity, previous/next availability, terminal state and error events;
  preserve the current request API or explicitly version it.

Acceptance examples must cover 0/1/2/3/4/7 eligible films, tied distances,
no duplicates through forward/back/retry, catalog changes, expired cursors,
concurrent clicks, cancellation before/after metadata, and explanation failure.

## Contextual follow-ups

The accepted MVP excludes conversational memory. Compact refinements reopen
that boundary; update `docs/SPEC.md` explicitly after agreement rather than
silently treating the input as an independent new request.

- **State:** retain original request, effective semantic intent, validated
  restrictions, explicit selected relaxations, and unsupported requirements.
  Decide whether refinements are cumulative or replace only the last refinement,
  and whether undo restores the earlier result branch.
- **Constraint changes:** define how an explicit phrase changes a field, how
  conflicts are clarified, and whether confirmation is needed. A mood-only
  change such as “less bleak” must preserve runtime, years, language lists,
  inclusions and exclusions. Never silently relax a restriction.
- **Result history:** decide whether a refinement starts a new batch sequence,
  which previous IDs remain excluded, whether previous sets stay reachable,
  and how an exhausted refinement differs from a zero-match restriction search.
- **Visible context:** specify a compact effective-request summary and a way to
  reset to a new search; keep unchecked requirements visible without presenting
  a full transcript. Define input length, submission and loading behavior.
- **Provider and lifecycle bounds:** specify context size, extraction schema,
  validation, latency/cost accounting, request capacity, expiry and privacy.
  Preserve the last usable results if interpretation or generation fails.

Acceptance examples must include “less bleak” retaining English OR French and
runtime/exclusions, an explicit runtime increase changing only runtime,
contradictory changes, unsupported factual follow-ups, empty refinements,
reset/undo, refinement after relaxation, cancellation, provider failure,
and session expiry. Evaluate relevance separately from deterministic compliance.

## Poster and detail implementation resolution

Retained TMDB detail snapshots contain usable poster paths. The implementation
validates catalog identity, content-addressed snapshot keys and image paths, then
redirects to fixed HTTPS `image.tmdb.org` sizes. No new ingestion, backfill, schema
migration or re-embedding occurs. Missing or failed images use a title-led
fallback. `/api/catalog-preview` reads at most 12 catalog records in stable ID
order; the UI presents up to eight and labels them as catalog browsing, not
recommendations or a popularity ranking. Ambient movement pauses on interaction,
hover, focus and page hiding; reduced motion disables it. Model prompts and
search result payloads stay unchanged.

Implemented detail presentation uses existing catalog facts: nonmodal desktop side panel
with a usable comparison area, full-screen mobile view, explicit close,
Escape, selected-film updates, focus return and appropriate focus management.
No invented cast, ratings, streaming availability or external facts.

## Proposed work sequence

1. Choose a visual direction; implement and verify the existing journey with
   posters, responsive details and collection styling under that direction.
2. Agree the batch decisions and API/stream acceptance cases; prepare a vertical
   tracker ticket for no-repeat next/previous sets and exhaustion.
3. Agree refinement semantics and its MVP scope amendment; prepare a dependent
   vertical ticket covering interpretation, preserved restrictions and UI.

These are proposed slices, not published tickets. Read the tracker instructions
before publication and obtain agreement on the specification/ticket breakdown.
AWS provisioning remains separately gated by the concrete resource/cost plan.
