# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

People searching for a movie based on their current mood and wants, alone or
with friends agreeing on a theme. Primarily used on a desktop computer;
mobile web remains supported.

## Product Purpose

Help visitors choose a film to watch tonight and save interesting alternatives
for later. Natural-language requests let people express motives, themes, and
feelings that conventional movie filters cannot capture.

## Operating Context

Visitors begin by describing what they want in their own words, with optional
help. They compare recommendations and can save films to My collection.

## Capabilities and Constraints

- Existing implementation: FastAPI with HTML/CSS/JavaScript, PostgreSQL/pgvector,
  and model-assisted request interpretation and streamed explanations.
- Search the retained catalog of 1,000 movies and return up to five recommendations.
  Catalog size is a current implementation boundary, not a permanent product promise.
- Supported restrictions include genres and exclusions, runtime, release years,
  and original languages. Mood and thematic requests drive semantic matching.
- Clearly disclose requirements that could not be checked. Relax a supported
  restriction only after the visitor explicitly selects a suggested change.
- Movie facts come from catalog records. Preserve available movie details when
  explanation generation fails.
- Collections persist in the same browser without accounts. Cross-device access
  and viewing-history personalization are outside the agreed MVP.
- Preserve required TMDB attribution.

## Brand Commitments

The product name is CineMood. Replace the prototype's visual design with a
desktop-first, dark, cinematic interface that uses the available width.
The owner prefers a deliberate accent and color from movie posters over the
prototype's bland palette. The owner approved **Screening lounge refined**: blue-black surfaces,
periwinkle actions, the lounge logo and recommendation layout, a compact request
band, and underlined text Details actions. Manrope headings/logo and DM Sans
body/controls are self-hosted. See `DESIGN.md` for the implemented tokens.

Reference qualities named by the owner:

- IMDb and Rotten Tomatoes: familiar movie-site character.
- AniList: a positive interface reference.
- NothingToWatch (`https://nothing-to-watch.port80.ch/`): minimalist composition,
  interactive movie movement, and a lively experience.
- Letterboxd: useful UI placement, but avoid its constrained central layout
  and faded gray palette.

Use direct, useful wording. Avoid motivational headlines, artificial-sounding
phrases, and scattered low-value helper text.

## Requested Redesign Behavior

These are owner-requested design requirements. The selected visual redesign is
implemented; verification evidence and remaining boundaries are in
`docs/progress.md`. Additional result batches and contextual follow-ups below
remain unimplemented specification work:

- Compare up to five poster-led recommendations with title, year, runtime, and a
  brief, specific explanation connecting each film to the request.
- Keep synopses available on demand and avoid crowding posters with information.
- Offer another three recommendations without repeats, with navigation back to
  previous sets and a clear end when eligible recommendations are exhausted.
- Support a compact follow-up field, such as “less bleak,” while retaining the
  original request. Do not present a full conversation transcript.
- Keep current results visible while replacements load, and preserve supported
  restrictions unless the visitor explicitly changes them.
- Before searching, show a gently moving poster display. Settle into up to five
  stable results after searching, with brief transitions between result sets.
  Pause ambient movement during typing, reading, hover, or keyboard focus;
  respect reduced-motion preferences.
- Reveal synopsis and full metadata inline in the selected card on every screen
  size. Highlight and slightly enlarge its poster without changing neighbouring
  columns. Selecting another card closes the previous disclosure. Keep Escape,
  visible close controls and focus return; link to TMDB when catalog identity permits.
- Show five refreshed spotlight films before searching, with Shuffle films and
  refresh on homepage/history return. Prefer unseen available films; explain when
  the catalog has no alternatives. These are browsing examples, not recommendations.
- Keep input focus local and subtle. Enter submits; Shift+Enter inserts a line.
- Keep desktop dimensions compact enough for five-film comparison at normal zoom,
  adapt smaller result counts, and preserve readability on narrower screens.
- Give Save a bookmark icon and distinct hover, active, busy, error and Saved states.


Refinement history and the meaning of eligible recommendation exhaustion remain
specification decisions. Additional batches and contextual follow-ups extend
the current implementation; they are not existing capabilities. See
`docs/plans/frontend-redesign.md` for the consolidated design brief.

## Evidence on Hand

- Agreed scope and implementation constraints: `docs/PROJECT.md`.
- Verified behavior and limitations: `docs/progress.md`.
- Recommendation evaluation and human feedback: `evaluation/`.
- Existing prototype: `cinemood/static/`.

## Product Principles

- Make the visitor's own words the starting point for discovery.
- Help people compare films and reach a viewing decision.
- Support saving promising alternatives without interrupting discovery.
- Explain recommendations through concrete movie details and keep unchecked
  requirements visible.
