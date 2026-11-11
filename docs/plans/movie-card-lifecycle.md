# Shared movie-card lifecycle (#8)

Status: accepted on 2026-11-11. The owner confirmed shared understanding of
Q1–Q11, including the concurrent-work handoff, and authorized documentation and
tracker publication with #8 marked `ready-for-agent`. Implementation has not
started. #9's internal session design remains a separate review.

## Accepted decisions

- The shared movie-card module owns markup, Details and focus behavior,
  explanation presentation, Save/Remove presentation and cleanup. Callers do not
  inspect its internal markup or selection state.
- Collection behavior owns saved membership, requests, bootstrap locking and
  mutation outcomes. Recommendation-session behavior owns the validity of
  tentative, validated and discarded explanation text.
- One displayed card may have expanded Details across the page. Selection is
  specific to that displayed card, even when a movie appears in multiple groups.
  Replacing a group clears selection only when it contains the selected card.
- Target concurrent implementation of #8 and #9 after agreeing their shared
  interface, distinct responsibilities and integration verification. Use one
  shared starting revision containing the current frontend rework. Keep #8 one
  cohesive ticket; concurrency does not imply splitting its lifecycle ownership.
- The owner requested committing the existing frontend rework before starting
  implementation of these architecture follow-ups.
- Callers manage groups through replacement, removal and presentation updates;
  the module automatically owns selection cleanup. Explanation updates carry
  presentation state/text rather than exposing internal DOM nodes.
- Pending collection mutations survive card removal/replacement. Collection
  behavior applies outcomes to membership and currently displayed copies;
  disposed cards receive no rendering or focus updates from late callbacks.
- Explicit removal selects the next card's focus target, then the previous
  card's, then collection status if empty. Wholesale replacement preserves focus
  outside the group; if focus was inside it, use the caller's stable fallback.
  Never focus detached content or steal focus from an obsolete callback.
- Include narrowly scoped collection load/mutation ordering safeguards in #8:
  obsolete loads must not overwrite newer membership or resurrect a successful
  removal. Collection behavior owns ordering; cards consume presentation state.

The frontend baseline is local commit `8bf42e1` (32 files). It passed 144 affected
integration checks, both deterministic browser suites and static checks. It has
not been pushed. The documentation handoff adds the agreed design records and
required existing project instructions/context on top of that application
baseline. Both implementation branches must start from that handoff commit (or
the same descendant), not from a remote branch missing the frontend rework.

## Accepted interface (Q8)

Create a group with its container, context (spotlight, recommendations or
collection), collection-action callback, a reader for initial collection state
and a stable focus fallback. Context determines existing presentation, not new
product behavior. Collection supplies projected state; cards derive labels,
icons, feedback, disabled and accessibility attributes in one implementation.

- `replace(movies)` replaces cards and returns an explanation-update function
  bound to that displayed generation. Replacement invalidates the old updater.
- `setCollectionState(movieId, state)` updates currently displayed copies from
  `{saved, pending, error}`. Collection behavior publishes state to active groups;
  initial cards read the same state before attachment.
- `remove(movieId)` removes the current card with selection/focus cleanup.
- `dispose()` invalidates explanation updates and unregisters/releases the group.

Explanation presentation phases are `pending`, `tentative`, `complete` and
`unavailable`, with text/message. The group renders supplied text safely and
replaces it on each update. Old-generation updates do nothing. Session behavior
owns accumulation of deltas, validation, completion, fallback and cancellation;
cards never infer validity from a phase or inspect stream frames. No caller
receives internal DOM nodes. Within one group movie IDs are unique; the same ID
may occur in different groups. Method spelling and argument packaging may be
refined during implementation if these semantics remain intact.

## Accepted collection synchronization (Q9)

All displayed copies of a movie share saved, pending and error state. Collection
behavior permits at most one mutation in flight per movie. Mutations survive
display disposal and publish outcomes to current groups, not obsolete handles.
A successful removal removes any current collection copy; it does not remove
the movie from spotlight or recommendations.

Accept only the latest collection load. Discard its snapshot if a mutation was
pending when it started or began afterward. If a requested reload becomes
obsolete, refresh after pending mutations settle. Preserve the existing Web
Locks bootstrap and anonymous-identity/HTTP contracts. Async removal moves focus
only if focus is still inside the current card being removed; otherwise preserve
the visitor's newer focus. Selection and focus belong to displayed cards, not IDs.

## Accepted verification gate (Q10)

Use real browser DOM and controlled HTTP responses for:

- Duplicate movie appearances: exclusive Details and synchronized Save state.
- Replacement/removal: stable focus, cleanup and harmless stale explanations.
- Pending Save/Remove during replacement: outcomes reach current copies without
  rendering or focusing disposed cards.
- Overlapping reloads/mutations: no stale membership or resurrected removals.
- Existing desktop/mobile appearance, poster fallback, safe text rendering,
  accessibility, streaming and collection behavior.

Retain both existing browser suites, affected integration checks and static
checks. No live model calls are required. Record executed results and limits in
`docs/progress.md`; agreeing this gate is not evidence the refactor passes it.

## Accepted concurrent-work handoff (Q11)

- Keep #8 cohesive. It owns the shared card implementation, Collection behavior
  and ordering guards, and migration of all three card contexts to the interface.
  It owns card-related integration edits to `discover.js`, script loading and
  any necessary preservation of existing CSS/HTML presentation.
- #9 owns a separate recommendation-session implementation and its focused
  protocol/session tests. It consumes presentation outcomes through the agreed
  card interface; it does not implement card markup or collection behavior.
- Develop the two modules and focused tests concurrently in isolated branches
  from the same committed baseline. Do not simultaneously edit the shared page
  wiring. Integrate #8 first, then adapt #9's page wiring once on top, resolving
  `discover.js` and script-loading changes in that integration step.
- #8 adds focused card/collection browser coverage; #9 adds focused session
  coverage. Preserve existing browser suites, assigning shared-suite edits to
  the integration step where needed. Verify each ticket and rerun both browser
  suites plus affected integration/static checks on the combined result.
- Commit the agreed plan and required existing project instructions/context as
  a documentation handoff, so a fresh checkout has
  the same instructions and accepted design as this workspace. Keep local caches
  and hook configuration outside the handoff. No push is implied.
- Update #8's full issue body and mark it `ready-for-agent`.
  Record the shared contract on #9 without claiming its remaining internal
  session design is reviewed or changing its readiness automatically.

No architecture refactor, #9 implementation, infrastructure or paid calls are
authorized by completing this design interview. No new ADR is required for this
reversible in-process interface; this plan is the decision record.

## Evidence

Refreshed GitHub issues #8 and #9 and #8 comments before this interview; #8 has
no comments and both issues were open with `needs-triage` before publication.
Reverified repository identity and refreshed both issues before publication.
Cupcake search returned
no additional CineMood context. Read-only inspection confirmed callers insert
nodes using `.movie-actions`, consult shared selection globals and manually
coordinate cleanup. Async collection callbacks can outlive their displayed card;
that is an identified scenario to specify, not a reproduced bug claim.
