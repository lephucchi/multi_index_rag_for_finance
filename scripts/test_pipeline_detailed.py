"""
Detailed Pipeline Test Script with Step-by-Step Logging.

Run from project root: python -m scripts.test_pipeline_detailed

This script executes the RAG pipeline step-by-step and logs detailed
information at each stage for debugging and improvement purposes.
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("pipeline_test")


# ============================================
# TEST QUERIES - Complex Vietnamese queries
# ============================================
TEST_QUERIES = [
    # Complex multi-domain query
    "ROE là gì và VNM có ROE bao nhiêu trong năm 2023?",
    
    # Legal + Financial composite
    "Quy định về công bố thông tin của công ty đại chúng là gì và VIC có tuân thủ không?",
    
    # Multi-entity comparison
    "So sánh chỉ số P/E của VNM, MSN và VIC trong quý 3/2023",
    
    # Simple single-domain query (for comparison)
    "EPS là gì?",
    
    # Long complex query with multiple intents
    "Phân tích tình hình tài chính của Vinamilk bao gồm doanh thu, lợi nhuận, và các chỉ số ROE, ROA. "
    "Đồng thời cho biết quy định về tỷ lệ sở hữu nước ngoài tại doanh nghiệp sữa Việt Nam.",
]


def print_separator(title: str = "", char: str = "=", length: int = 80):
    """Print a visual separator."""
    if title:
        padding = (length - len(title) - 2) // 2
        print(f"\n{char * padding} {title} {char * padding}")
    else:
        print(f"\n{char * length}")


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


async def test_step_1_classification(query: str) -> Dict[str, Any]:
    """Step 1: Query Complexity Classification."""
    print_separator("STEP 1: QUERY COMPLEXITY CLASSIFICATION")
    
    from src.core.decomposition import QueryComplexityClassifier
    
    classifier = QueryComplexityClassifier()
    result = classifier.classify(query)
    
    print(f"📝 Query: {query}")
    print(f"\n🎯 Classification Result:")
    print(f"   • Is Complex: {'✅ YES' if result.is_complex else '❌ NO'}")
    print(f"   • Complexity Score: {result.complexity_score:.2f}")
    print(f"   • Reason: {result.reason}")
    
    return {
        "is_complex": result.is_complex,
        "complexity_score": result.complexity_score,
        "reason": result.reason
    }


async def test_step_2_routing(query: str) -> Dict[str, Any]:
    """Step 2: Query Routing."""
    print_separator("STEP 2: QUERY ROUTING")
    
    from src.core.router import HybridRouter
    
    router = HybridRouter()
    routes, scores = router.route(query)
    
    print(f"📝 Query: {query}")
    print(f"\n🎯 Routing Result:")
    print(f"   • Selected Routes: {routes}")
    print(f"\n📊 All Scores:")
    for index, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(score * 20)
        print(f"   • {index:12s}: {score:.3f} {bar}")
    
    return {
        "routes": routes,
        "scores": scores
    }


async def test_step_3_decomposition(query: str, is_complex: bool) -> Dict[str, Any]:
    """Step 3: Query Decomposition."""
    print_separator("STEP 3: QUERY DECOMPOSITION")
    
    if not is_complex:
        print(f"⏭️  Skipping decomposition - query is simple")
        return {"sub_queries": [query], "sub_query_types": ["UNKNOWN"]}
    
    from src.core.decomposition import QueryDecomposer
    
    decomposer = QueryDecomposer()
    result = decomposer.decompose(query)
    
    print(f"📝 Original Query: {query}")
    print(f"\n🔀 Decomposition Result:")
    print(f"   • Is Decomposed: {'✅ YES' if result.is_decomposed else '❌ NO'}")
    print(f"   • Number of Sub-queries: {len(result.sub_queries)}")
    print(f"   • Method: {result.method}")
    print(f"   • Latency: {result.latency_ms:.2f}ms")
    
    print(f"\n📋 Sub-queries Detail:")
    for i, sq in enumerate(result.sub_queries, 1):
        print(f"   [{i}] Type: {sq.query_type}")
        print(f"       Query: {sq.query}")
        print(f"       Order: {sq.order}")
        print()
    
    if result.reasoning:
        print(f"💭 Reasoning: {result.reasoning}")
    
    return {
        "sub_queries": [sq.query for sq in result.sub_queries],
        "sub_query_types": [sq.query_type for sq in result.sub_queries],
        "method": result.method,
        "reasoning": result.reasoning
    }


async def test_step_4_retrieval(
    sub_queries: List[str], 
    routes: List[str],
    sub_query_types: List[str]
) -> Dict[str, Any]:
    """Step 4: Document Retrieval."""
    print_separator("STEP 4: DOCUMENT RETRIEVAL")
    
    from src.core.retrieval import ParallelRetriever
    
    retriever = ParallelRetriever()
    
    # Map sub-queries to routes based on types
    query_routes = []
    for i, sq_type in enumerate(sub_query_types):
        if sq_type and sq_type != "UNKNOWN":
            query_routes.append(sq_type.lower())
        elif i < len(routes):
            query_routes.append(routes[i])
        else:
            query_routes.append(routes[0] if routes else "financial")
    
    # Pad routes if needed
    while len(query_routes) < len(sub_queries):
        query_routes.append(query_routes[0] if query_routes else "financial")
    
    print(f"🔍 Retrieval Plan:")
    for i, (sq, route) in enumerate(zip(sub_queries, query_routes), 1):
        print(f"   [{i}] Query: {truncate_text(sq, 60)}")
        print(f"       → Index: {route}")
    
    # Execute retrieval
    result = await retriever.retrieve_all_async(sub_queries, query_routes[:len(sub_queries)])
    
    print(f"\n📚 Retrieval Results:")
    print(f"   • Total Documents Retrieved: {len(result.documents)}")
    print(f"   • Retrieval Time: {result.total_time_ms:.2f}ms")
    
    print(f"\n📄 Documents Preview (top 5):")
    for i, doc in enumerate(result.documents[:5], 1):
        print(f"   [{i}] Source: {doc.index} | Score: {doc.score:.3f}")
        print(f"       Content: {truncate_text(doc.content, 150)}")
        print()
    
    return {
        "documents": [doc.to_dict() for doc in result.documents],
        "num_documents": len(result.documents),
        "retrieval_time_ms": result.retrieval_time_ms
    }


async def test_step_5_fusion(documents: List[Dict]) -> Dict[str, Any]:
    """Step 5: Result Fusion."""
    print_separator("STEP 5: RESULT FUSION")
    
    from src.core.retrieval import ResultFusion, RetrievedDocument
    
    fusion = ResultFusion()
    
    # Convert dicts back to documents
    docs = [
        RetrievedDocument(
            content=d["content"],
            metadata=d.get("metadata", {}),
            score=d["score"],
            index=d["index"]
        ) for d in documents
    ]
    
    result = fusion.merge(docs)
    
    print(f"📊 Fusion Result:")
    print(f"   • Documents Before: {len(documents)}")
    print(f"   • Documents After:  {len(result.documents)}")
    print(f"   • Context Length:   {len(result.formatted_context)} chars")
    
    print(f"\n🏷️  Citations Map ({len(result.citations)} entries):")
    for cit in result.citations[:5]:
        print(f"   [{cit['number']}] {cit['source']} (score: {cit['score']:.3f})")
    if len(result.citations) > 5:
        print(f"   ... and {len(result.citations) - 5} more")
    
    return {
        "formatted_context": result.formatted_context,
        "citations_map": result.citations,
        "num_fused": len(result.documents)
    }


async def test_step_6_generation(
    query: str, 
    context: str, 
    citations_map: List[Dict]
) -> Dict[str, Any]:
    """Step 6: Answer Generation."""
    print_separator("STEP 6: ANSWER GENERATION")
    
    from src.core.generator import GroundedGenerator
    
    generator = GroundedGenerator()
    
    print(f"📝 Query: {query}")
    print(f"📖 Context Length: {len(context)} chars")
    print(f"🏷️  Available Citations: {len(citations_map)}")
    
    result = generator.generate(
        query=query,
        context=context,
        citations_map=citations_map
    )
    
    print(f"\n✨ Generation Result:")
    print(f"   • Is Grounded: {'✅ YES' if result.is_grounded else '⚠️ NO'}")
    print(f"   • Citations Used: {result.citations_used}")
    
    print(f"\n📝 Answer Preview:")
    print(f"   {truncate_text(result.answer, 500)}")
    
    return {
        "answer": result.answer,
        "is_grounded": result.is_grounded,
        "citations_used": result.citations_used
    }


async def run_full_pipeline_test(query: str, query_index: int):
    """Run full pipeline test for a single query."""
    print_separator(f"TESTING QUERY #{query_index + 1}", char="*")
    print(f"📝 Query: {query}")
    
    step_times = {}
    
    try:
        import time
        
        # Step 1: Classification
        start = time.time()
        classification = await test_step_1_classification(query)
        step_times["classification"] = (time.time() - start) * 1000
        
        # Step 2: Routing
        start = time.time()
        routing = await test_step_2_routing(query)
        step_times["routing"] = (time.time() - start) * 1000
        
        # Step 3: Decomposition
        start = time.time()
        decomposition = await test_step_3_decomposition(
            query, 
            classification["is_complex"]
        )
        step_times["decomposition"] = (time.time() - start) * 1000
        
        # Step 4: Retrieval
        start = time.time()
        retrieval = await test_step_4_retrieval(
            decomposition["sub_queries"],
            routing["routes"],
            decomposition["sub_query_types"]
        )
        step_times["retrieval"] = (time.time() - start) * 1000
        
        # Step 5: Fusion
        start = time.time()
        fusion = await test_step_5_fusion(retrieval["documents"])
        step_times["fusion"] = (time.time() - start) * 1000
        
        # Step 6: Generation
        start = time.time()
        generation = await test_step_6_generation(
            query,
            fusion["formatted_context"],
            fusion["citations_map"]
        )
        step_times["generation"] = (time.time() - start) * 1000
        
        # Summary
        print_separator("SUMMARY")
        total_time = sum(step_times.values())
        print(f"⏱️  Total Time: {total_time:.2f}ms")
        print(f"\n📊 Time Breakdown:")
        for step, time_ms in step_times.items():
            bar = "█" * int(time_ms / total_time * 30) if total_time > 0 else ""
            print(f"   • {step:15s}: {time_ms:8.2f}ms {bar}")
        
        print(f"\n✅ Final Answer:")
        print(f"   Grounded: {'Yes' if generation['is_grounded'] else 'No'}")
        print(f"   Citations: {generation['citations_used']}")
        print(f"   Answer: {truncate_text(generation['answer'], 300)}")
        
        return {
            "query": query,
            "success": True,
            "classification": classification,
            "routing": routing,
            "decomposition": decomposition,
            "retrieval_count": retrieval["num_documents"],
            "generation": generation,
            "step_times": step_times,
            "total_time_ms": total_time
        }
        
    except Exception as e:
        print_separator("ERROR")
        print(f"❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "query": query,
            "success": False,
            "error": str(e)
        }


async def main():
    """Main test runner."""
    print_separator("RAG PIPELINE DETAILED TEST", char="=")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Test Queries: {len(TEST_QUERIES)}")
    
    # Check configuration
    from src.config import settings
    print(f"\n⚙️  Configuration:")
    print(f"   • GEMINI_MODEL: {settings.GEMINI_MODEL}")
    print(f"   • SUPABASE configured: {'✅' if settings.SUPABASE_URL else '❌'}")
    print(f"   • GEMINI configured: {'✅' if settings.GEMINI_API_KEY else '❌'}")
    
    if not settings.validate():
        print("\n❌ Configuration validation failed!")
        return
    
    results = []
    
    # Run tests
    for i, query in enumerate(TEST_QUERIES):
        result = await run_full_pipeline_test(query, i)
        results.append(result)
        
        # Pause between queries to avoid rate limiting
        if i < len(TEST_QUERIES) - 1:
            print("\n⏳ Waiting 2 seconds before next query...")
            await asyncio.sleep(2)
    
    # Final summary
    print_separator("FINAL SUMMARY", char="=")
    success_count = sum(1 for r in results if r.get("success"))
    print(f"✅ Successful: {success_count}/{len(results)}")
    
    if success_count > 0:
        avg_time = sum(r.get("total_time_ms", 0) for r in results if r.get("success")) / success_count
        print(f"⏱️  Average Time: {avg_time:.2f}ms")
    
    # Save results to JSON
    output_file = f"pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📁 Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
