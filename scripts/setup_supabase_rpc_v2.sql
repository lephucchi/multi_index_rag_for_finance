-- Enable pgvector extension
create extension if not exists vector;

-- Drop old function
drop function if exists match_documents;

-- Create new function with unique parameter names and conditional logic for glossary
create or replace function match_documents (
  _query_embedding vector(1024),
  _match_count int DEFAULT 10,
  _table_name text DEFAULT 'glossary_index'
) returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  -- Check if table is glossary_index which has different schema (term/definition)
  if _table_name = 'glossary_index' then
    return query execute format('
      select
        id,
        term || '': '' || definition as content,
        metadata,
        1 - (embedding <=> $1) as similarity
      from
        %I
      order by
        embedding <=> $1
      limit $2
    ', _table_name)
    using _query_embedding, _match_count;
  else
    -- Standard schema with content column (legal, financial, news)
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
    ', _table_name)
    using _query_embedding, _match_count;
  end if;
end;
$$;
