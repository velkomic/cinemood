# Frontend redesign brief

Owner refinement (2026-11-10): the latest UX request supersedes the earlier
three-result/sidebar composition. Current implementation targets up to five
recommendations, four refreshable spotlight films and inline card details on all
screen sizes. Additional recommendation batches and contextual follow-ups remain
separate behavior specifications. `docs/progress.md` records current verification.

Status: interview consolidated on 2026-11-10; owner selected **Screening lounge
refined** after reviewing concrete sketches. Implementation uses the lounge logo
and recommendation layout, a compact request band, and underlined Details actions.
Verification and review evidence is recorded in `../progress.md`. Additional
batches and contextual follow-ups remain specification work identified in
`frontend-redesign-spec-work.md`; no tracker publication has occurred.

## Job and audience

Desktop-first movie discovery for individuals and friends choosing a film based
on a mood, theme, or motive that ordinary filters cannot express. Success means
choosing a film tonight and saving other interesting films for later. The
Discover surface operates as a task-focused application; film imagery and
movement support the choice.

## Confirmed direction

- Use a dark cinematic background, a deliberate accent, and color from movie
  posters. Use the available desktop width. Avoid the prototype's bland palette,
  constrained central composition, motivational headlines, and scattered
  low-value helper copy. The selected world uses blue-black surfaces, periwinkle
  actions, Manrope headings/logo and DM Sans body/controls; see root `DESIGN.md`.
- Begin with a free-text request and optional help. Before searching, a gently
  moving poster display gives the page life; after searching, three stable
  poster-led recommendations support comparison. Ambient motion pauses during
  typing, reading, hover, or keyboard focus. Reduced-motion preferences keep it
  still. Switching result sets uses a short transition.
- Each recommendation shows a poster, title, year, runtime, a concise specific
  explanation, and a save action. Synopsis and fuller details open on demand in
  a desktop side panel or a full-screen mobile detail view. Keep results usable
  beside the panel; another film selection updates its contents. Include close,
  Escape, and focus return behavior.
- Provide three more films without repeats, navigation to earlier sets, and an
  understandable end state. Keep existing results visible while new ones load.
  A compact follow-up field accepts changes such as “less bleak” while retaining
  the original request and restrictions unless explicitly changed. Do not show
  a full conversation transcript.
- Preserve anonymous collections, catalog-grounded facts, streamed explanation
  fallback, prominent unchecked-requirement warnings, explicit selection of
  restriction changes, and required TMDB attribution.

## Selected page structure and future extensions

A compact header contains CineMood, Discover, and My collection. A prominent
request field starts discovery without a large introductory headline. Results
use a wide three-column composition, with explanations below the poster imagery.
Future follow-up and result-set controls belong near the results after their
behavior specification is agreed and implemented.
Opening details reflows or sizes the comparison area so it remains usable.

My collection inherits the same poster, metadata, save/remove feedback, and
detail presentation. Mobile stacks films in one column with native full-screen
modal details. Desktop details share the comparison width; intermediate desktop
widths use two result columns alongside the panel.

## Material states and boundaries

Design for the initial display, request entry, loading, one to three results,
streaming and failed explanations, unsupported requirements, no matches,
suggested restriction changes, cancellation, retry, saved state, empty
collection, open details, and exhausted recommendations. Keep useful current
content available during loading and recoverable failures. Avoid crowding the
page while keeping decision-relevant limitations visible.

Use real catalog posters with a considered missing-image fallback; the initial
display must not imply those films already match an unsubmitted request.
Recommendation facts and explanations must remain readable and operable with
keyboard access and reduced motion.

## Remaining implementation decisions

Additional result batches and contextual follow-ups are new capabilities,
not CSS-only changes. Before implementation, specify stable result ordering,
duplicate prevention, eligibility/exhaustion rules, prior-set retention, and how
refinements relate to earlier sets. Poster sourcing is now a read-only projection
of retained TMDB snapshot paths, with fixed-host image redirects and a title-led
fallback. No ingestion, backfill or re-embedding is needed. Selected composition
and responsive details are implemented; verification is recorded in `../progress.md`.
Do not imply an existing global popularity or quality ranking from the owner's
phrase “top movies”; any new ranking rule requires a separate specification.

This brief does not authorize paid infrastructure or replace the accepted MVP
specification and tracker workflow. It captures the interview and selected direction. Additional search behavior
requires separate specification agreement and ticket planning.

## Reference evidence

The owner named IMDb, Rotten Tomatoes, and AniList as positive references, and
NothingToWatch (`https://nothing-to-watch.port80.ch/`) for minimalist composition
and dynamic poster interaction. Letterboxd's UI placement is useful, but its
constrained width and faded gray palette are negative references.

Prototype inspection used current HTML/CSS/JavaScript and saved desktop/mobile
browser captures matching the current layout. Fresh Chromium capture was blocked
by the local sandbox. Automated access to the supplied reference and other
reference sites failed; reference qualities above are the owner's observations,
not a claimed live visual audit.
