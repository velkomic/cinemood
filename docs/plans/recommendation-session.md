# Browser recommendation-session state (#9)

Status: design interview in progress. Q1–Q3 accepted on 2026-11-11.
Remaining decisions and final shared-understanding confirmation are pending;
#9 is not ready-for-agent and implementation has not started.

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

## Verified context and remaining branches

Read current #8/#9 and comments through GitHub MCP; Cupcake returned no additional
CineMood context. #8 implementation is in 445f3fc and 304efc3. Its implemented
card interface and ownership are recorded in movie-card-lifecycle.md.

Read-only inspection found that the current browser retains displayed results
until a result frame arrives, has an 80-second client timeout and ignores starts
while busy. It trusts server explanation completion, with evidence/schema checks
on the server. The browser currently permits some out-of-order shapes not sent
by the server (repeated result, complete before result and explanation updates
after explanation_error). These are facts to resolve, not accepted new behavior.

Next decisions: public controller/outcome shape; result retention/replacement;
concurrency, cancellation and disposal semantics; documented protocol strictness
versus extraction-only compatibility; focused test seam and integration gate.
The current residual-buffer limit is not a true maximum frame-size check.
No new ADR or glossary term has been justified for this reversible interface.
