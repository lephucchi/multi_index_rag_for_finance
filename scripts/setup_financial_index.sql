-- Create financial_index table
create table if not exists financial_index (
  id bigserial primary key,
  chunk_uid text,
  article_id text,
  title text,
  chunk_index int,
  content text,
  metadata jsonb,
  embedding vector(1024),
  created_at timestamptz default now()
);

-- Create HNSW index for faster similarity search
create index on financial_index using hnsw (embedding vector_cosine_ops);
