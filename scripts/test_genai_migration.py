"""
Pipeline Test Script for google-genai Migration Verification.

Tests 2 queries:
1. Simple query (glossary index): "ROE là gì?"
2. Complex query (glossary + finance + legal): "ROE là gì, VNM có ROE bao nhiêu và quy định nào về công bố thông tin tài chính?"
"""
import os
import sys
import json
import time
import logging

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test queries
SIMPLE_QUERY = "ROE là gì?"
COMPLEX_QUERY = "ROE là gì, VNM có ROE bao nhiêu và quy định nào về công bố thông tin tài chính?"


def test_imports():
    """Test that all modules import correctly with new SDK."""
    print("\n" + "="*60)
    print("STEP 1: TESTING IMPORTS")
    print("="*60)
    
    results = {}
    
    # Test google-genai import
    try:
        from google import genai
        from google.genai import types
        results["google-genai"] = {"status": "✅ OK", "version": "1.x"}
        print(f"✅ google-genai: Imported successfully")
    except ImportError as e:
        results["google-genai"] = {"status": "❌ FAILED", "error": str(e)}
        print(f"❌ google-genai: {e}")
        return results, False
    
    # Test decomposer
    try:
        from src.core.decomposition.decomposer import QueryDecomposer, GEMINI_AVAILABLE
        results["decomposer"] = {"status": "✅ OK", "gemini_available": GEMINI_AVAILABLE}
        print(f"✅ decomposer: GEMINI_AVAILABLE={GEMINI_AVAILABLE}")
    except ImportError as e:
        results["decomposer"] = {"status": "❌ FAILED", "error": str(e)}
        print(f"❌ decomposer: {e}")
    
    # Test generator
    try:
        from src.core.generator.grounded import GroundedGenerator, GEMINI_AVAILABLE
        results["generator"] = {"status": "✅ OK", "gemini_available": GEMINI_AVAILABLE}
        print(f"✅ generator: GEMINI_AVAILABLE={GEMINI_AVAILABLE}")
    except ImportError as e:
        results["generator"] = {"status": "❌ FAILED", "error": str(e)}
        print(f"❌ generator: {e}")
    
    # Test translator
    try:
        from src.core.retrieval.translator import QueryTranslator, GEMINI_AVAILABLE
        results["translator"] = {"status": "✅ OK", "gemini_available": GEMINI_AVAILABLE}
        print(f"✅ translator: GEMINI_AVAILABLE={GEMINI_AVAILABLE}")
    except ImportError as e:
        results["translator"] = {"status": "❌ FAILED", "error": str(e)}
        print(f"❌ translator: {e}")
    
    # Test router
    try:
        from src.core.router.router import HybridRouter
        results["router"] = {"status": "✅ OK"}
        print(f"✅ router: HybridRouter loaded")
    except ImportError as e:
        results["router"] = {"status": "❌ FAILED", "error": str(e)}
        print(f"❌ router: {e}")
    
    # Test pipeline fallback
    try:
        from src.pipeline.graph import run_rag_pipeline_fallback
        results["pipeline"] = {"status": "✅ OK (fallback)"}
        print(f"✅ pipeline: run_rag_pipeline_fallback loaded")
    except ImportError as e:
        results["pipeline"] = {"status": "❌ FAILED", "error": str(e)}
        print(f"❌ pipeline: {e}")
    
    all_ok = all(r.get("status", "").startswith("✅") for r in results.values())
    return results, all_ok


def test_routing(query: str):
    """Test semantic routing step."""
    print(f"\n{'='*60}")
    print(f"STEP 2: SEMANTIC ROUTING")
    print(f"Query: {query}")
    print("="*60)
    
    try:
        from src.core.router.router import HybridRouter
        
        router = HybridRouter()
        start = time.time()
        routes, scores = router.route(query)
        latency = (time.time() - start) * 1000
        
        result = {
            "status": "✅ OK",
            "routes": routes,
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "latency_ms": round(latency, 2)
        }
        
        print(f"✅ Routes selected: {routes}")
        print(f"   Scores: {result['scores']}")
        print(f"   Latency: {result['latency_ms']}ms")
        
        return result
        
    except Exception as e:
        import traceback
        print(f"❌ Routing failed: {e}")
        traceback.print_exc()
        return {"status": "❌ FAILED", "error": str(e)}


def test_decomposition(query: str):
    """Test query decomposition step."""
    print(f"\n{'='*60}")
    print(f"STEP 3: QUERY DECOMPOSITION")
    print(f"Query: {query}")
    print("="*60)
    
    try:
        from src.core.decomposition.decomposer import QueryDecomposer
        
        decomposer = QueryDecomposer()
        start = time.time()
        result = decomposer.decompose(query)
        latency = (time.time() - start) * 1000
        
        output = {
            "status": "✅ OK",
            "is_decomposed": result.is_decomposed,
            "sub_queries": [{"query": sq.query, "type": sq.query_type} for sq in result.sub_queries],
            "reasoning": result.reasoning,
            "method": result.method,
            "latency_ms": round(latency, 2)
        }
        
        print(f"✅ Decomposed: {result.is_decomposed}")
        print(f"   Method: {result.method}")
        print(f"   Sub-queries ({len(result.sub_queries)}):")
        for sq in result.sub_queries:
            print(f"      - [{sq.query_type}] {sq.query}")
        print(f"   Reasoning: {result.reasoning}")
        print(f"   Latency: {output['latency_ms']}ms")
        
        return output
        
    except Exception as e:
        import traceback
        print(f"❌ Decomposition failed: {e}")
        traceback.print_exc()
        return {"status": "❌ FAILED", "error": str(e)}


def test_retrieval(query: str, routes: list):
    """Test retrieval step."""
    print(f"\n{'='*60}")
    print(f"STEP 4: RETRIEVAL")
    print(f"Query: {query}")
    print(f"Routes: {routes}")
    print("="*60)
    
    try:
        from src.core.retrieval.retriever import ParallelRetriever
        import asyncio
        
        async def do_retrieve():
            retriever = ParallelRetriever()
            all_docs = []
            for route in routes:
                docs = await retriever.retrieve(query, route, k=3)
                all_docs.extend(docs)
                print(f"   [{route.upper()}] Retrieved {len(docs)} documents")
            return all_docs
        
        start = time.time()
        all_docs = asyncio.run(do_retrieve())
        latency = (time.time() - start) * 1000
        
        result = {
            "status": "✅ OK",
            "total_documents": len(all_docs),
            "latency_ms": round(latency, 2)
        }
        
        print(f"✅ Total documents: {len(all_docs)}")
        print(f"   Latency: {result['latency_ms']}ms")
        
        # Preview first document from each route
        for route in routes:
            route_docs = [d for d in all_docs if d.get("source") == route]
            if route_docs:
                preview = route_docs[0].get("content", "")[:100]
                print(f"   [{route.upper()}] Preview: {preview}...")
        
        return result, all_docs
        
    except Exception as e:
        import traceback
        print(f"❌ Retrieval failed: {e}")
        traceback.print_exc()
        return {"status": "❌ FAILED", "error": str(e)}, []


def test_generation(query: str, context: str):
    """Test grounded generation step."""
    print(f"\n{'='*60}")
    print(f"STEP 5: GROUNDED GENERATION")
    print(f"Query: {query}")
    print(f"Context length: {len(context)} chars")
    print("="*60)
    
    try:
        from src.core.generator.grounded import GroundedGenerator
        
        generator = GroundedGenerator()
        start = time.time()
        result = generator.generate(query=query, context=context, citations_map=[])
        latency = (time.time() - start) * 1000
        
        output = {
            "status": "✅ OK",
            "answer_length": len(result.answer),
            "citations_used": result.citations_used,
            "is_grounded": result.is_grounded,
            "latency_ms": round(latency, 2)
        }
        
        print(f"✅ Answer generated ({len(result.answer)} chars)")
        print(f"   Citations used: {result.citations_used}")
        print(f"   Is grounded: {result.is_grounded}")
        print(f"   Latency: {output['latency_ms']}ms")
        print(f"\n   --- ANSWER ---")
        # Print first 1000 chars
        answer_preview = result.answer[:1000]
        if len(result.answer) > 1000:
            answer_preview += "..."
        print(f"   {answer_preview}")
        
        return output, result.answer
        
    except Exception as e:
        import traceback
        print(f"❌ Generation failed: {e}")
        traceback.print_exc()
        return {"status": "❌ FAILED", "error": str(e)}, ""


def run_full_pipeline_test(query: str, query_name: str):
    """Run full pipeline test for a query."""
    print("\n" + "#"*80)
    print(f"# FULL PIPELINE TEST: {query_name}")
    print(f"# Query: {query}")
    print("#"*80)
    
    total_start = time.time()
    report = {
        "query": query,
        "query_name": query_name,
        "steps": {}
    }
    
    # Step 2: Routing
    routing_result = test_routing(query)
    report["steps"]["routing"] = routing_result
    routes = routing_result.get("routes", ["glossary"])
    
    # Step 3: Decomposition
    decomp_result = test_decomposition(query)
    report["steps"]["decomposition"] = decomp_result
    
    # Step 4: Retrieval
    retrieval_result, docs = test_retrieval(query, routes)
    report["steps"]["retrieval"] = retrieval_result
    
    # Format context for generation
    context = "\n\n".join([
        f"[{i+1}] ({d.get('source', 'unknown').upper()}) {d.get('content', '')[:500]}"
        for i, d in enumerate(docs[:10])
    ])
    
    # Step 5: Generation
    gen_result, answer = test_generation(query, context)
    report["steps"]["generation"] = gen_result
    report["answer"] = answer
    
    # Total time
    total_time = (time.time() - total_start) * 1000
    report["total_time_ms"] = round(total_time, 2)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {query_name}")
    print("="*60)
    print(f"Total time: {report['total_time_ms']}ms")
    print(f"Routes: {routes}")
    print(f"Sub-queries: {len(decomp_result.get('sub_queries', []))}")
    print(f"Documents retrieved: {retrieval_result.get('total_documents', 0)}")
    print(f"Answer length: {gen_result.get('answer_length', 0)} chars")
    print(f"Is grounded: {gen_result.get('is_grounded', False)}")
    
    return report


def main():
    """Main test function."""
    print("\n" + "="*80)
    print(" PIPELINE VERIFICATION TEST - google-genai SDK Migration")
    print("="*80)
    
    # Step 1: Test imports
    import_results, all_ok = test_imports()
    
    if not all_ok:
        print("\n❌ Some critical imports failed. Aborting pipeline test.")
        return None, None
    
    # Test 1: Simple query (glossary)
    print("\n\n" + "="*80)
    print(" TEST 1: SIMPLE QUERY (GLOSSARY INDEX)")
    print("="*80)
    simple_report = run_full_pipeline_test(SIMPLE_QUERY, "Simple Query (Glossary)")
    
    # Test 2: Complex query (multi-index)
    print("\n\n" + "="*80)
    print(" TEST 2: COMPLEX QUERY (MULTI-INDEX)")
    print("="*80)
    complex_report = run_full_pipeline_test(COMPLEX_QUERY, "Complex Query (Multi-Index)")
    
    # Final summary
    print("\n\n" + "="*80)
    print(" FINAL SUMMARY")
    print("="*80)
    
    simple_ok = simple_report['steps']['generation'].get('status', '').startswith('✅') if simple_report else False
    complex_ok = complex_report['steps']['generation'].get('status', '').startswith('✅') if complex_report else False
    
    print(f"\n📊 Simple Query:")
    print(f"   - Total time: {simple_report['total_time_ms'] if simple_report else 'N/A'}ms")
    print(f"   - Routes: {simple_report['steps']['routing'].get('routes', []) if simple_report else 'N/A'}")
    print(f"   - Status: {'✅ SUCCESS' if simple_ok else '❌ FAILED'}")
    
    print(f"\n📊 Complex Query:")
    print(f"   - Total time: {complex_report['total_time_ms'] if complex_report else 'N/A'}ms")
    print(f"   - Routes: {complex_report['steps']['routing'].get('routes', []) if complex_report else 'N/A'}")
    print(f"   - Sub-queries: {len(complex_report['steps']['decomposition'].get('sub_queries', [])) if complex_report else 0}")
    print(f"   - Status: {'✅ SUCCESS' if complex_ok else '❌ FAILED'}")
    
    print(f"\n{'='*80}")
    print(f" OVERALL: {'✅ ALL TESTS PASSED' if (simple_ok and complex_ok) else '❌ SOME TESTS FAILED'}")
    print("="*80)
    
    return simple_report, complex_report


if __name__ == "__main__":
    main()
