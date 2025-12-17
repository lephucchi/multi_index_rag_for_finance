"""
Test script for complex real estate entrepreneur query.
Run: python -m scripts.test_realestate_query
"""
import sys
import os
import asyncio
import json
import time
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Force CPU to avoid tensor issues
os.environ['CUDA_VISIBLE_DEVICES'] = ''


async def run_test():
    # User's complex query (Vietnamese without diacritics for safety)
    query = "Toi la mot doanh nhan khoi nghiep trong linh vuc bat dong san, hay tu van cho toi ve mot so cong ty bat dong san da duoc niem yet de toi co the hoc tap va cac bo luat co the cho toi dua vao do phat trien doanh nghiep cua minh."
    
    print("="*80)
    print("RAG PIPELINE DETAILED TEST - REAL ESTATE ENTREPRENEUR QUERY")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Query: {query}")
    print()
    
    step_times = {}
    
    # Step 1: Classification
    print("="*40 + " STEP 1: CLASSIFICATION " + "="*16)
    start = time.time()
    from src.core.decomposition import QueryComplexityClassifier
    classifier = QueryComplexityClassifier()
    classification = classifier.classify(query)
    step_times['classification'] = (time.time() - start) * 1000
    
    print(f"Is Complex: {classification.is_complex}")
    print(f"Complexity Score: {classification.complexity_score:.2f}")
    print(f"Reason: {classification.reason}")
    print()
    
    # Step 2: Routing
    print("="*40 + " STEP 2: ROUTING " + "="*23)
    start = time.time()
    from src.core.router import HybridRouter
    router = HybridRouter()
    routes, scores = router.route(query)
    step_times['routing'] = (time.time() - start) * 1000
    
    print(f"Selected Routes: {routes}")
    print("All Scores:")
    for idx, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {idx}: {score:.3f}")
    print()
    
    # Step 3: Decomposition
    print("="*40 + " STEP 3: DECOMPOSITION " + "="*17)
    start = time.time()
    
    if classification.is_complex:
        from src.core.decomposition import QueryDecomposer
        decomposer = QueryDecomposer()
        decomp = decomposer.decompose(query)
        sub_queries = [sq.query for sq in decomp.sub_queries]
        sub_query_types = [sq.query_type for sq in decomp.sub_queries]
        
        print(f"Is Decomposed: {decomp.is_decomposed}")
        print(f"Method: {decomp.method}")
        print(f"Latency: {decomp.latency_ms:.2f}ms")
        print("Sub-queries:")
        for i, sq in enumerate(decomp.sub_queries, 1):
            print(f"  [{i}] Type: {sq.query_type}")
            print(f"      Query: {sq.query}")
        if decomp.reasoning:
            print(f"Reasoning: {decomp.reasoning}")
    else:
        sub_queries = [query]
        sub_query_types = ['UNKNOWN']
        print("Query is simple - no decomposition needed")
    
    step_times['decomposition'] = (time.time() - start) * 1000
    print()
    
    # Step 4: Retrieval
    print("="*40 + " STEP 4: RETRIEVAL " + "="*21)
    start = time.time()
    from src.core.retrieval import ParallelRetriever
    retriever = ParallelRetriever()
    
    # IMPORTANT: Warm up encoder in main thread before async calls
    # This fixes the "Cannot copy out of meta tensor" error
    print("Warming up encoder...")
    _ = retriever.retrieve("warmup query", "financial", k=1)
    print("Encoder ready!")
    
    # Map sub-queries to routes
    query_routes = []
    for i, sq_type in enumerate(sub_query_types):
        if sq_type and sq_type != 'UNKNOWN':
            query_routes.append(sq_type.lower())
        elif i < len(routes):
            query_routes.append(routes[i])
        else:
            query_routes.append(routes[0] if routes else 'financial')
    
    while len(query_routes) < len(sub_queries):
        query_routes.append(query_routes[0] if query_routes else 'financial')
    
    print("Retrieval Plan:")
    for i, (sq, rt) in enumerate(zip(sub_queries, query_routes), 1):
        sq_preview = sq[:60] + "..." if len(sq) > 60 else sq
        print(f"  [{i}] {sq_preview} -> {rt}")
    
    retrieval = await retriever.retrieve_all_async(sub_queries, query_routes[:len(sub_queries)])
    step_times['retrieval'] = (time.time() - start) * 1000
    
    print(f"Total Documents: {len(retrieval.documents)}")
    print(f"Retrieval Time: {retrieval.total_time_ms:.2f}ms")
    print()
    print("=" * 80)
    print("RETRIEVED DOCUMENTS TABLE")
    print("=" * 80)
    print(f"{'#':>3} | {'ID':>6} | {'Table':>15} | {'Score':>6} | Content Preview")
    print("-" * 80)
    for i, doc in enumerate(retrieval.documents[:15], 1):
        content_preview = doc.content[:100].replace('\n', ' ').replace('\r', '')
        doc_id = doc.doc_id if doc.doc_id else "N/A"
        table_name = f"{doc.source_index}_index"
        print(f"{i:>3} | {str(doc_id):>6} | {table_name:>15} | {doc.similarity:.4f} | {content_preview}...")
    print("=" * 80)
    print()
    
    # Step 5: Fusion
    print("="*40 + " STEP 5: FUSION " + "="*24)
    start = time.time()
    from src.core.retrieval import ResultFusion
    fusion = ResultFusion()
    fused = fusion.merge(retrieval.documents)
    step_times['fusion'] = (time.time() - start) * 1000
    
    print(f"Documents Before: {len(retrieval.documents)}")
    print(f"Documents After: {len(fused.documents)}")
    print(f"Context Length: {len(fused.formatted_context)} chars")
    print(f"Citations: {len(fused.citations)} entries")
    print()
    
    # Step 6: Generation
    print("="*40 + " STEP 6: GENERATION " + "="*20)
    start = time.time()
    from src.core.generator import GroundedGenerator
    generator = GroundedGenerator()
    
    result = generator.generate(
        query=query,
        context=fused.formatted_context,
        citations_map=fused.citations
    )
    step_times['generation'] = (time.time() - start) * 1000
    
    print(f"Is Grounded: {result.is_grounded}")
    print(f"Citations Used: {result.citations_used}")
    print()
    
    # Summary
    print("="*40 + " FINAL SUMMARY " + "="*25)
    total_time = sum(step_times.values())
    print(f"Total Time: {total_time:.2f}ms")
    print("Time Breakdown:")
    for step, ms in step_times.items():
        pct = (ms / total_time * 100) if total_time > 0 else 0
        print(f"  {step:15s}: {ms:8.2f}ms ({pct:5.1f}%)")
    print()
    
    print("="*40 + " FINAL ANSWER " + "="*26)
    print(result.answer)
    print()
    
    # Save output
    output = {
        'query': query,
        'success': True,
        'classification': {
            'is_complex': classification.is_complex, 
            'score': classification.complexity_score,
            'reason': classification.reason
        },
        'routing': {'routes': routes, 'scores': scores},
        'decomposition': {'sub_queries': sub_queries, 'types': sub_query_types},
        'retrieval': {'num_docs': len(retrieval.documents)},
        'generation': {
            'is_grounded': result.is_grounded, 
            'citations': result.citations_used, 
            'answer': result.answer
        },
        'step_times': step_times,
        'total_time_ms': total_time
    }
    
    outfile = f"pipeline_test_realestate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Results saved to: {outfile}")


if __name__ == "__main__":
    asyncio.run(run_test())
