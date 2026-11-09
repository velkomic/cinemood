CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE movies (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id text NOT NULL UNIQUE,
    title text NOT NULL CHECK (length(trim(title)) > 0),
    overview text NOT NULL CHECK (length(trim(overview)) > 0),
    release_year integer NOT NULL CHECK (release_year BETWEEN 1800 AND 2200),
    original_language text NOT NULL,
    runtime_minutes integer NOT NULL CHECK (runtime_minutes > 0),
    provenance text NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE genres (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);
CREATE TABLE movie_genres (
    movie_id bigint NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    genre_id bigint NOT NULL REFERENCES genres(id),
    PRIMARY KEY (movie_id, genre_id)
);
CREATE TABLE movie_embeddings (
    movie_id bigint PRIMARY KEY REFERENCES movies(id) ON DELETE CASCADE,
    model text NOT NULL,
    provider_fingerprint text NOT NULL,
    dimensions integer NOT NULL CHECK (dimensions = 1536),
    document_version text NOT NULL,
    content_hash text NOT NULL,
    embedding vector(1536) NOT NULL CHECK (vector_norm(embedding) > 0)
);
