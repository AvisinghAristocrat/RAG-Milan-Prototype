-- migrations/001_schema.sql
-- Ensure pgvector extension exists
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT,
  url TEXT,
  content_hash TEXT,
  canonical_text TEXT,
  meta JSONB,
  last_modified TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (source, external_id)
);

-- Chunks table with vector and tsvector
-- NOTE: change vector(384) to your model dimension if needed
CREATE TABLE IF NOT EXISTS chunks (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  embedding vector(384),
  meta JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  chunk_tsv tsvector
);

-- FTS trigger function
CREATE OR REPLACE FUNCTION chunks_tsv_trigger() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.chunk_tsv := to_tsvector('english', COALESCE(NEW.chunk_text, ''));
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tsvectorupdate ON chunks;
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_tsv_trigger();

-- GIN index for FTS
CREATE INDEX IF NOT EXISTS chunks_chunk_tsv_idx ON chunks USING GIN (chunk_tsv);

-- HNSW index for dense vectors (pgvector)
-- Tweak m and ef_construction later when tuning
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx ON chunks USING hnsw (embedding) WITH (m = 16, ef_construction = 200);

-- Ingest jobs / audit table
CREATE TABLE IF NOT EXISTS ingest_jobs (
  id SERIAL PRIMARY KEY,
  source TEXT,
  external_key TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status TEXT,
  summary JSONB,
  logs TEXT
);

-- Backfill chunk_tsv for existing rows, if any
UPDATE chunks SET chunk_tsv = to_tsvector('english', COALESCE(chunk_text, '')) WHERE chunk_tsv IS NULL;
