# Recommendation stream

`POST /api/recommendations/stream` accepts the same JSON as the existing
`POST /api/recommendations` endpoint (which remains available for catalog-only
clients). UTF-8 SSE is consumed with fetch, not EventSource. Request size/schema errors use normal HTTP JSON responses (413/422); capacity
returns 429. Invalid or expired selections produce a terminal stream error.
After HTTP 200, failures use stream events, never a second HTTP response.

Each frame is `event: NAME\ndata: JSON\n\n`. Every JSON object contains
`request_id`, `sequence` (starting at 1), and `elapsed_ms` since stream generation starts.
Network chunks are unrelated to frames or UTF-8 character boundaries.

Ordered events:

- `status`: `stage` = interpretation, retrieval, or explanation.
- `result`: the existing catalog response (interpretation, original request,
  applied change, suggestions, message, movies). Emitted before generation.
  Empty, clarification and no-match results go directly to complete.
- `explanation_delta`: catalog `movie_id`, appended `text`. Tentative until
  validated; show an explicit generating label.
- `explanation_complete`: `movie_id`, validated full `text`, and exact overview
  `evidence` quotes. Replace tentative text with this authoritative text.
- `explanation_error`: `movie_id`, safe `message`; discard this movie's tentative
  explanation, retain its card and show explanation unavailable.
- `complete`: terminal `status` (matches/no_match/clarification/empty),
  `timings_ms` (first_status, first_movie, first_explanation, total; null when
  absent), `stages_ms`, and explanation `usage` totals. Explanation usage is null if any explanation call lacks final accounting;
  `provider_calls` records per-stage model and token usage, including rejected
  explanations when final usage was received. Failed extraction records unknown
  usage explicitly. Interrupted calls may incur charges.
- `error`: terminal safe `message`, timings and stages; retain cards, discard
  explanations that have no explanation_complete. Extraction/retrieval errors never emit a successful catalog result.

Exactly one complete/error terminates a connected stream. EOF before it is a
failure: keep cards, discard tentative explanations. Abort on navigation or
Cancel. Generation is cancelled with the response task and closes provider
streams. Sync retrieval work has bounded provider/SQL timeouts and completes in
its worker before releasing admission capacity; cancellation cannot kill a
Python worker thread.

Bounds: 16 KiB body, 2,000 request characters, four admitted requests per app
process (no queue), 75 seconds total, 30 seconds per explanation, zero retries,
400 output tokens per movie, 5 movies, 6,000 streamed JSON characters per movie,
420 explanation characters and 1–3 numbered overview references. The server
splits the overview into literal excerpts, sends numbered excerpts with the movie,
and constrains the provider JSON Schema to that movie ID and those reference IDs.
The application validates the final schema, finish reason, movie ID and reference
bounds again, then resolves references to exact catalog text in the public
`evidence` field. Copied quotation strings, invented/out-of-range references,
extra fields, refused/truncated/malformed output and oversized responses fail.
The former copied-quotation matching contract is superseded by this 2026-11-10
reliability fix; the public event shape is unchanged.
These structural checks cannot prove semantic grounding; the fixed human review
assesses every claim. Model text uses textContent only. No database migration,
ranking change, extra retrieval, automatic relaxation, or generated save ID.
Admission bounds apply to both recommendation routes; use one app worker for the
MVP. Public per-client request limiting remains T6 work.

The OpenAI finish-reason and final usage handling follows the
[official streaming reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events).
Measurements describe server emission; the evaluation runner separately records
client reception. Initial status is progress, not model time to first token.

The explanation JSON Schema follows the [official structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs).
Schema-constrained references establish source identity and format; they do not
prove that every sentence is entailed by its selected excerpt. Human grounding
review remains necessary.


The 2026-11-10 owner refinement raises retrieval to up to five films and requests
compact explanations (20–35 words, at most 420 validated characters). Calls remain
sequential and independently validated; the unchanged total timeout still bounds
the request. Five films can therefore require five explanation calls, rather than
three. Provider latency can still cause explanation fallback while catalog facts
remain visible. Deterministic tests establish behavior, not live relevance or a
new latency/cost measurement.

## Browser session ownership (#9)

`recommendation-session.js` exposes `createRecommendationSession(onOutcome)`.
One controller per Discover page provides `start(request, selection = null)`,
`cancel()` and `dispose()`. `start` settles after reader/timer cleanup; starts
while busy or after disposal are ignored. The client timeout remains 80 seconds.
Cancel/pagehide abort the current run; pagehide does not dispose a restorable
page. Disposal aborts and suppresses all subsequent presentation callbacks.

The callback receives `{type: 'busy', busy}`, `{type: 'status', message, quiet}`,
`{type: 'result', result}`, or `{type: 'explanation', movieId, phase, text, message}`.
Explanation text is accumulated/replaced by the controller; message is optional.
Discover retains form, interpretation, suggestions and DOM rendering, passing
explanation outcomes through the generation-bound card updater from #8. It owns
no raw frames, decoding, cancellation controller or explanation-validity map.

A new search retains the previous display until one validated result replaces it,
including an empty result. Failures before result leave that display intact.
Interruption after result retains catalog cards and completed explanations while
discarding unfinished text. Completion text replaces tentative text. Server-side
evidence validation remains authoritative; browser checks establish protocol and
identity validity, not semantic grounding.

The browser requires a stable nonempty string request ID, consecutive integer
sequences starting at one, unique positive integer movie IDs and a single result
before complete. Explanation events require a known unfinished movie; both
explanation_complete and explanation_error end updates for that movie. Error may
terminate before or after result. Unknown events, malformed consumed fields,
repeated result, premature complete, post-terminal events, malformed UTF-8,
truncated EOF and non-whitespace trailing data fail safely. Whitespace after the
terminal event is allowed. Successful completion status is published only after
valid EOF. Frames are limited to 65,536 JavaScript string characters excluding
the LF-LF delimiter, for complete and incomplete frames independently of chunk
size. A chunk containing many small valid frames is allowed. These ordering and
frame-size checks deliberately tighten malformed-stream handling; valid server
payloads and HTTP/selection contracts are unchanged.

Focused verification: `.venv/bin/python tests/browser_session_smoke.py` uses
Chromium and controlled local HTTP streams with no database or provider calls.
It complements the retained stream, UX and shared-card browser suites and real
PostgreSQL server integration checks.
