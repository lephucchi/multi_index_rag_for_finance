import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import RetrieverConfig, INDEX_TABLE_MAP
from src.core.retrieval.parallel import ParallelRetriever, SupabaseVectorDB, SentenceTransformerEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync_connection():
    print("\n--- Testing Sync Connection ---")
    config = RetrieverConfig.from_env()
    
    if not config.supabase_url or not config.supabase_key:
        print("❌ Error: Supabase credentials not found in env.")
        return False
        
    print(f"Supabase URL: {config.supabase_url}")
    print(f"Supabase Key: {config.supabase_key[:10]}...")
    
    try:
        db = SupabaseVectorDB(config.supabase_url, config.supabase_key)
        # Try a dummy search
        dummy_embedding = [0.1] * 1024 # Assuming 1024 dim, but RPC might fail if dim mismatch. 
        # Actually better to use encoder if available to get correct dim.
        
        encoder = SentenceTransformerEncoder(config.encoder_model)
        embedding = encoder.encode("test query")
        print(f"Embedding generated. Dim: {len(embedding)}")
        
        # Test with 'glossary' index
        table = INDEX_TABLE_MAP["glossary"]
        print(f"Searching table: {table}")
        
        results = db.search(table, embedding, k=1)
        print(f"✅ Sync Search Success! Found {len(results)} results.")
        return True
    except Exception as e:
        print(f"\n❌ Sync Search Failed!")
        print(f"Error Type: {type(e)}")
        print(f"Error Args: {e.args}")
        if hasattr(e, 'message'):
            print(f"Message: {e.message}")
        if hasattr(e, 'details'):
            print(f"Details: {e.details}")
        if hasattr(e, 'hint'):
            print(f"Hint: {e.hint}")
        if hasattr(e, 'code'):
            print(f"Code: {e.code}")
        # print full dict if possible
        try:
            print(f"Full Dict: {e.__dict__}")
        except:
            pass
        return False

async def test_async_retrieval():
    print("\n--- Testing Async Retrieval ---")
    retriever = ParallelRetriever()
    
    try:
        # Test single retrieve_async
        print("Testing retrieve_async...")
        docs, time_ms = await retriever.retrieve_async("ROE", "glossary", k=1)
        print(f"✅ retrieve_async result: {len(docs)} docs in {time_ms:.2f}ms")
        
        # Test retrieve_all_async (parallel)
        print("Testing retrieve_all_async...")
        result = await retriever.retrieve_all_async(
            sub_queries=["ROE", "VNM"], 
            routes=["glossary", "financial"],
            k_per_index=1
        )
        print(f"✅ retrieve_all_async result: {len(result.documents)} total docs")
        print(f"Sub-query results: {result.sub_query_results.keys()}")
        return True
    except Exception as e:
        print(f"❌ Async Retrieval Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_sync_connection():
        asyncio.run(test_async_retrieval())
