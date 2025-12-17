-- Enable pgvector extension
create extension if not exists vector;

-- Dynamic match_documents function for multi-index RAG
-- Supports querying different tables based on 'table_name' argument
create or replace function match_documents (
  query_embedding vector(1024),
  match_count int DEFAULT 10,
  table_name text DEFAULT 'glossary_index'
) returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query execute format('
    select
      id,
      content,
      metadata,
      1 - (embedding <=> $1) as similarity
    from
      %I
    order by
      embedding <=> $1
    limit $2
  ', table_name)
  using query_embedding, match_count;
end;
$$;
