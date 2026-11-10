# Personal collections

Discover cards have a Save to collection action. My collection lists current
catalog facts and lets the visitor remove choices. Saves and removals are
idempotent. Collection operations do not call OpenAI or copy movie records.

An anonymous collection belongs to a persistent, host-only browser cookie,
valid for one year from issuance. Clearing cookies/browser data, cookie expiry,
or deleting the database loses access. There is no recovery or device transfer.
Return using the same browser and site address. Cookies are not port-isolated;
the separate local demos use separate databases and should not be treated as
independent security origins. Changing host or scheme can lose access. A stable
HTTPS origin is required for the later hosted demonstration, including stop/start.

## Configuration

The application defaults to `COLLECTION_ORIGIN=https://localhost`. Configure the
exact public origin (scheme, host, optional port, no trailing slash). HTTPS uses
`__Host-cinemood_collection`, with Secure, HttpOnly, SameSite=Strict, Path=/,
and no Domain attribute. The host prefix prevents parent-domain cookie injection.
Do not log or share cookie values: possession grants access to that collection.

Local Compose explicitly enables development HTTP at `http://localhost:8000`;
the retained-catalog override uses `http://localhost:58000`. For a direct local
uvicorn invocation, set:

```bash
export COLLECTION_ORIGIN=http://localhost:8000
export COLLECTION_ALLOW_HTTP=true
```

Use the configured address in the browser: `127.0.0.1` and `localhost` differ.
HTTP uses the distinct `cinemood_collection_dev` cookie without Secure. Hosted
configuration must set its exact HTTPS origin and `COLLECTION_ALLOW_HTTP=false`.
HTTP origins are rejected at startup unless the explicit development override is
enabled. The configured origin is independent of untrusted Host/forwarding headers.

## REST contract and ownership

- `GET /api/collection`: `200`, `{"movies": [...]}`, including a useful empty
  list. Issues an identity if the cookie is missing, malformed, or unknown.
- `PUT /api/collection/{movie_id}`: save an existing catalog movie; `204` even
  when already saved. Unknown catalog IDs return `404`.
- `DELETE /api/collection/{movie_id}`: remove only the caller's saved reference;
  `204` even when absent. It never deletes the catalog movie.
- Mutation requests must include an Origin exactly equal to `COLLECTION_ORIGIN`;
  missing, `null`, and mismatched origins return `403` before database changes.
  Browsers supply this header on same-origin PUT/DELETE fetches.
- Requests marked `Sec-Fetch-Site: cross-site` return `403`, including reads.
  This prevents a direct cross-site API navigation from replacing a Strict
  cookie that the browser withheld. Navigate to the My collection view instead.
- IDs must be positive PostgreSQL bigint values (`422` otherwise). Database
  failures return a safe `503` message. Successful responses use `Cache-Control:
  no-store`; no identity is returned in JSON or accepted as a URL/body owner ID.

The server creates a random 256-bit token and stores only its SHA-256 digest in
`collections`. An unknown submitted token is replaced with a server-issued one;
clients cannot choose a collection identity. Every item query binds the digest
derived from the cookie. No endpoint accepts another visitor's collection ID.

Migration `003_collections.sql` adds `collections` and `collection_items`.
The composite primary key `(collection_hash, movie_id)` enforces uniqueness,
including concurrent saves using `ON CONFLICT DO NOTHING`. Foreign keys require
an existing owner and movie; catalog deletion cascades to saved references. A
key-share lock keeps a movie from disappearing between the existence check and
save commit. Listing joins movies and aggregates sorted genres in a correlated
subquery, preventing duplicate cards. Results are ordered by latest save then
movie ID. Saves commit before a success response; application processes keep no
ownership state. Existing persistent PostgreSQL volumes retain both tables
through application/database restart. `docker compose down --volumes` deletes
collections along with the catalog.

The browser serializes identity requests across tabs with Web Locks, so a
delayed first-visit response cannot replace the identity after another tab saves.
This requires a current browser in a secure context (HTTPS, or localhost for
local development). Unsupported contexts show an error and do not save using
an unsafe fallback. API clients must retain their cookie between requests.

## Verification

`tests/test_collections.py` exercises REST with disposable real PostgreSQL,
including two visitors, duplicate/concurrent saves, catalog-reference deletion,
invalid IDs, origin/cookie rules, application recreation, browser-state loss, and
safe failures. `tests/browser_stream_smoke.py` includes streamed discovery → save
→ revisit → collection → remove, another browser context, mobile layout and
error/retry states. External model responses are deterministic HTTP fixtures.
Actual database restart evidence and final suite results are in `progress.md`.
AWS stop/start and backup restoration remain ticket #7 work.
