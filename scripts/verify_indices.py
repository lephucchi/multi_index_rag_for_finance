import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from src.config import INDEX_TABLE_MAP
from src.core.retrieval.parallel import ParallelRetriever

async def verify_indices():
    retriever = ParallelRetriever()
    print("--- Verifying Vector Indices ---")
    
    indices = ["glossary", "legal", "financial", "news"]
    results = {}
    
    for index in indices:
        print(f"Checking {index}...", end=" ", flush=True)
        try:
            # Search for a generic term
            docs, time_ms = await retriever.retrieve_async("query", index, k=1)
            status = "✅ OK" if docs else "⚠️ Empty"
            if docs:
                print(f"{status} ({len(docs)} docs, {time_ms:.0f}ms)")
            else:
                print(f"{status}")
            results[index] = True
        except Exception as e:
            print(f"❌ Failed: {str(e)[:100]}")
            results[index] = False
            
    return all(results.values())

if __name__ == "__main__":
    asyncio.run(verify_indices())
