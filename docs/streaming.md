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
400 output tokens per movie, 3 movies, 6,000 streamed JSON characters per movie,
1,200 explanation characters and 1–3 numbered overview references. The server
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
