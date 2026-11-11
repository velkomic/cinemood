## Status and intent

Design decisions Q1–Q10 accepted on 2026-11-11. This draft awaits final owner
confirmation before publication as ready-for-agent. Implementation is a later
session. Related: #8 (implemented, owner-accepted and closed). No open issue
blocker; neither follow-up blocks the AWS demonstration #7.

## Problem

Recommendation stream decoding, lifecycle, explanation validity and page rendering
are mixed in discover.js (consumeEvents, search and showResult). The card interface
from #8 is implemented. Consolidate protocol/session ownership behind one public
controller so the page only renders outcomes. Preserve working MVP behavior with
the explicitly accepted malformed-protocol fixes below.

## Accepted decisions

- Q1: Keep this a behavior-preserving MVP refactor. Get the current MVP working
  first; extra batches, conversational follow-ups and other features are later
  extensions. Keep current search, explicit relaxation and collection contracts.
- Q2: One session module owns HTTP streaming, decoding, protocol/session
  validation, accumulated explanation text, cancellation and timeout. Discover
  owns DOM rendering, forms, interpretation and suggestion controls. It consumes
  presentation outcomes and passes explanation presentation through #8's card
  interface; it does not inspect raw frames or decide tentative-text retention.
- Q3: #8 is already implemented, locally verified, owner-accepted and closed.
  Establish a new committed common baseline including #8 and the current
  approved refinements. Independent module/test work may proceed concurrently
  after this design is accepted; one integration owner handles discover.js,
  script loading and shared browser suites. Keep combined verification.
- Q4: One controller per Discover page exposes start(request, selection), cancel()
  and dispose(), and emits result, explanation, status and busy-state outcomes.
  HTTP transport remains internal; Discover renders through existing card groups.
- Q5: Retain current cards and interpretation until a result arrives. Early
  failure/cancel preserves them; a new result replaces them, including empty
  results. Later interruption preserves catalog cards and completed explanations,
  discarding unfinished explanation text.
- Q6: Ignore additional starts while busy. Retain the 80-second client timeout
  and release the active run after cancellation cleanup. Disposal aborts the run
  and prevents subsequent presentation callbacks.
- Q7: Explicitly fix invalid event ordering: reject repeated result frames,
  complete before result, and updates after a movie's explanation_error. Enforce
  a genuine frame-size limit. Valid server streams remain unchanged. Add focused
  regressions; protocol failure preserves catalog cards and completed text.

- Q8: The controller publishes result payloads, accumulated explanation updates
  {movieId, phase, text, message}, user-facing status and busy state. start()
  settles after cleanup; expected search failures appear as outcomes. Keep #8's
  phases; evidence validation remains on the server, protocol/identity checks in
  the browser.
- Q9: Require stable nonempty string request_id, consecutive integer sequences
  starting at 1, one result before successful completion, unique movie IDs, and
  explanation events only for known unfinished movies. Terminal error may occur
  before or after result. Reject unknown events, malformed payloads, events after
  termination and premature EOF. Each frame is bounded to 65,536 decoded
  characters regardless of chunking. Explanation completion/error ends updates
  for that movie. Failure retains cards/completed text and discards unfinished
  text. Frame length uses JavaScript string length, excluding the LF-LF delimiter.
- Q10: Focused checks exercise the public controller in a real browser with
  controlled HTTP streams and no PostgreSQL/live models. Cover fragmentation,
  validation, retention, cancel/timeout/disposal and repeated-search recovery.
  Module and focused-test authoring may proceed concurrently against the agreed
  interface; a single integration owner handles page wiring. Retain all three
  existing browser suites, affected server integration and static checks. Use
  one common committed handoff with the final accepted design and record actual
  verification and limits in progress.md.

## Interface and integration contract

Create one controller per Discover page with presentation callbacks (or a single
callback for tagged outcomes). The public operations are start(request,
selection), cancel() and dispose(). Callback packaging and method spelling may
be refined without changing the accepted semantics; module and test authors
must agree one concrete signature before concurrent work begins.

Outcomes describe busy state, user-facing status, the accepted result payload
and explanation presentation. They never expose raw frames, reader objects,
AbortControllers, internal maps or DOM nodes. Deliver the result before its
explanation outcomes so Discover can replace the recommendation group and retain
its generation-bound updater. Deliver accumulated/replacement explanation text,
not deltas that require the page to maintain validity or accumulation state.
The page derives control visibility/disabled/aria-busy from busy outcomes and
renders existing messages/interpretation/suggestion controls. start() settles
only after reader/timer/controller cleanup. Ignore starts while busy; after
disposal no operation may restart the controller or publish presentation.

Use cancel() on Cancel and pagehide to preserve the existing lifecycle. Dispose
when the controller's page owner is actually torn down; pagehide cancellation
must not make a restored page permanently unusable. A disposed controller emits
no later outcomes. Completed explanations remain authoritative replacements;
server-side evidence/schema validation is not semantic proof of grounding.

Keep current request/selection serialization, HTTP status handling, content-type
checks, safe text presentation, fatal UTF-8 decoding and LF-separated SSE format.
Validate payload fields needed by protocol and presentation before publishing
result/explanation outcomes. Do not duplicate the whole backend schema or add a
second evidence-validation system. A result is accepted at most once, including
empty/no-match/clarification. An error can terminate without a result; complete
cannot. No explanation event precedes the result or follows that movie's terminal
explanation outcome. Every connected stream requires complete/error and valid
EOF; reject post-terminal events or non-whitespace trailing data. Per-frame
bounds must be enforced both for buffered incomplete frames and complete frames,
not on the size of an arbitrary network chunk containing many valid frames.

## Verification and concurrent work

Start from the same final accepted documentation handoff descending from
`ea62bb1`, which includes #8 implementation (445f3fc and 304efc3) and current MVP
refinements. Local commits have not been pushed; a remote-only checkout needs
these commits before starting. #8 is accepted and closed, so its implementation
is already available rather than a concurrent task.

The module author owns a separate session implementation file. The focused-test
author owns a separate session test file using the public controller and
controlled HTTP responses, not private helper mocks. Agree the callable signature
before branching. One integration owner handles discover.js, script loading,
stream documentation and shared-suite edits after module/tests converge. Merge
only compatible, passing work; run the combined verification gate afterward.

Focused matrix: arbitrary UTF-8/JSON/frame delimiter splits; many valid frames in
one chunk; exact frame boundary and one-character overflow with/without delimiter;
valid completion replacing tentative text; wrong request/movie identity; invalid
sequence and payload; duplicate movie IDs/results; premature complete; unknown
event; updates after explanation complete/error; terminal stream error; events
or nonempty data after terminal; truncated EOF; HTTP/network errors; cancel and
80-second timeout; busy starts; disposal suppression; cleanup and successful retry.
Use controlled browser time for timeout verification where supported.

Browser integration must preserve progressive rendering, completed-text/card
fallback, previous-display retention before replacement, empty replacement,
explicit relaxation, Cancel/pagehide and recovered submit/Cancel/aria-busy state.
Run browser_stream_smoke.py, browser_ux_smoke.py, browser_cards_smoke.py, affected
stream/server integration tests, Ruff lint/format, strict mypy, JavaScript syntax
and whitespace checks. Use real PostgreSQL for affected server checks; the focused
controller suite must not require it. No paid calls are needed and deterministic
fixtures do not establish live relevance, latency or cost.

## Scope and tradeoffs

Keep plain JavaScript, existing server payloads, ranking, collection ownership,
restrictions and relaxation behavior. This is a behavior-preserving refactor
except the explicit malformed-protocol fixes in Q7/Q9. No extra result batches,
conversational state, general transport abstraction, backend orchestration,
framework migration or infrastructure. Neither this ticket nor #8 blocks #7.
ADR-0001 remains unchanged. No new ADR is justified for this reversible interface;
no new domain term is needed in GLOSSARY.md. This plan records the decisions.
Deleting the session module should force protocol, interruption and tentative-text
rules back into the page; extracting only the decoder is insufficient.

## Acceptance criteria

- [x] Owner reviewed Q1–Q10, ownership, public seam, failure semantics and concurrent-work gate (final shared-understanding confirmation precedes publication).
- [ ] One session owner controls HTTP, framing, identities, lifecycle and explanation validity; Discover only renders outcomes through #8's card interface.
- [ ] Implement start/cancel/dispose and presentation outcomes, one active run, 80-second timeout, reader/timer cleanup and safe cancellation/disposal/retry.
- [ ] Preserve prior display until result, atomic replacement including empty results, authoritative completion and completed-text/card retention on interruption.
- [ ] Enforce accepted protocol ordering, payload/identity validation, frame bounds and terminal/EOF rules with regression evidence.
- [ ] Preserve progress, HTTP failures, selection payloads, explicit relaxation, Cancel/pagehide and submit/Cancel/aria-busy recovery.
- [ ] Focused browser/controller checks exercise the full accepted matrix without PostgreSQL/live models or private-helper mocks.
- [ ] Pass all three retained browser suites, affected server integration and static checks on the combined result; preserve safe text rendering and current visual/collection behavior.
- [ ] Record actual verification and limits in docs/progress.md and update docs/streaming.md for ownership and explicit protocol fixes.

Before implementation read docs/PROJECT.md, docs/progress.md,
docs/ARCHITECTURE.md, ADR-0001, docs/plans/movie-card-lifecycle.md and
 docs/plans/recommendation-session.md. No implementation or push is authorized
by completing this design review.
