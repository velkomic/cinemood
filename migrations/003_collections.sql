CREATE TABLE collections (
    token_hash text PRIMARY KEY CHECK (length(token_hash) = 64),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE collection_items (
    collection_hash text NOT NULL REFERENCES collections(token_hash) ON DELETE CASCADE,
    movie_id bigint NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    saved_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (collection_hash, movie_id)
);
