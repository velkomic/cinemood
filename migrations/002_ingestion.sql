ALTER TABLE movies ADD COLUMN release_date date;
ALTER TABLE movies ADD COLUMN vote_count integer CHECK (vote_count >= 0);
ALTER TABLE movies ADD COLUMN snapshot_key text;

-- The page and cursor are committed together with each movie's searchable state.
CREATE TABLE ingestion_checkpoints (
    name text PRIMARY KEY,
    state jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
