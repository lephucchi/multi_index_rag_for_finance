"""
Test script for Step 7 optimizations.
Run: python -m scripts.test_step7_optimizations
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

# Force CPU
os.environ['CUDA_VISIBLE_DEVICES'] = ''


def test_persona_rewriter():
    """Test the PersonaRewriter module."""
    print("="*60)
    print("TEST 1: PersonaRewriter")
    print("="*60)
    
    from src.core.generator import PersonaRewriter, Persona
    
    rewriter = PersonaRewriter()
    
    # Test auto-detection
    test_cases = [
        ("Tôi là startup founder, hướng dẫn khởi nghiệp BĐS", Persona.STARTUP_FOUNDER),
        ("Đầu tư vào cổ phiếu nào tốt", Persona.INVESTOR),
        ("Luật doanh nghiệp quy định gì", Persona.LEGAL_PROFESSIONAL),
        ("ROE là gì, giải thích cho em", Persona.STUDENT),
    ]
    
    print("\n1.1 Auto-detection tests:")
    for query, expected in test_cases:
        detected = rewriter.detect_persona(query)
        status = "✓" if detected == expected else "✗"
        print(f"  {status} Query: '{query[:40]}...'")
        print(f"    Expected: {expected.value}, Got: {detected.value}")
    
    # Test rewriting
    print("\n1.2 Rewriting test:")
    sample_answer = """Dựa trên tài liệu, Luật Kinh doanh BĐS quy định [1]:
- Điều kiện kinh doanh BĐS [1]
- Nghĩa vụ công khai thông tin [2]
- Các loại hợp đồng [3]"""
    
    sample_query = "Tôi là doanh nhân khởi nghiệp, tư vấn về BĐS"
    
    result = rewriter.rewrite(sample_answer, sample_query, Persona.STARTUP_FOUNDER)
    
    print(f"  Original length: {len(sample_answer)}")
    print(f"  Rewritten length: {len(result.rewritten_answer)}")
    print(f"  Success: {result.success}")
    print(f"  Latency: {result.latency_ms:.2f}ms")
    
    if result.success and result.rewritten_answer != sample_answer:
        print(f"  Preview (first 200 chars):")
        print(f"    {result.rewritten_answer[:200]}...")
    
    return result.success


def test_embedding_cache():
    """Test the EmbeddingCache module."""
    print("\n" + "="*60)
    print("TEST 2: EmbeddingCache")
    print("="*60)
    
    from src.core.retrieval import EmbeddingCache, get_embedding_cache
    
    cache = EmbeddingCache(maxsize=10)
    
    # Test basic operations
    print("\n2.1 Basic cache operations:")
    
    # Mock encoder
    class MockEncoder:
        def encode(self, query, **kwargs):
            import numpy as np
            # Simulate encoding delay
            time.sleep(0.01)
            return np.random.rand(768)
    
    encoder = MockEncoder()
    
    # First call - cache miss
    start = time.time()
    _ = cache.get_or_compute("test query 1", encoder)
    first_time = (time.time() - start) * 1000
    print(f"  First call (miss): {first_time:.2f}ms")
    
    # Second call - cache hit
    start = time.time()
    _ = cache.get_or_compute("test query 1", encoder)
    second_time = (time.time() - start) * 1000
    print(f"  Second call (hit): {second_time:.2f}ms")
    
    print(f"  Speedup: {first_time/second_time:.1f}x")
    print(f"  Stats: {cache.stats.to_dict()}")
    
    # Test global cache
    print("\n2.2 Global cache singleton:")
    global_cache1 = get_embedding_cache()
    global_cache2 = get_embedding_cache()
    print(f"  Same instance: {global_cache1 is global_cache2}")
    
    return True


async def test_full_pipeline_with_persona():
    """Test the full pipeline with persona rewriting."""
    print("\n" + "="*60)
    print("TEST 3: Full Pipeline with Persona Rewriting")
    print("="*60)
    
    # Use the same complex query
    query = "Toi la doanh nhan khoi nghiep trong linh vuc bat dong san, tu van cho toi ve cac cong ty BDS niem yet va luat lien quan"
    
    print(f"\nQuery: {query}")
    
    from src.core.decomposition import QueryComplexityClassifier
    from src.core.router import HybridRouter
    from src.core.retrieval import ParallelRetriever, ResultFusion
    from src.core.generator import GroundedGenerator, PersonaRewriter, Persona
    
    step_times = {}
    
    # Step 1: Classification
    start = time.time()
    classifier = QueryComplexityClassifier()
    classification = classifier.classify(query)
    step_times['classification'] = (time.time() - start) * 1000
    print(f"\n1. Classification: {classification.is_complex} ({step_times['classification']:.0f}ms)")
    
    # Step 2: Routing
    start = time.time()
    router = HybridRouter()
    routes, scores = router.route(query)
    step_times['routing'] = (time.time() - start) * 1000
    print(f"2. Routing: {routes} ({step_times['routing']:.0f}ms)")
    
    # Step 3: Retrieval (simplified)
    print("3. Retrieval...")
    start = time.time()
    retriever = ParallelRetriever()
    
    # Warm up
    _ = retriever.retrieve("warmup", "financial", k=1)
    
    retrieval = await retriever.retrieve_all_async([query], routes[:2])
    step_times['retrieval'] = (time.time() - start) * 1000
    print(f"   Retrieved: {len(retrieval.documents)} docs ({step_times['retrieval']:.0f}ms)")
    
    # Step 4: Fusion
    start = time.time()
    fusion = ResultFusion()
    fused = fusion.merge(retrieval.documents)
    step_times['fusion'] = (time.time() - start) * 1000
    print(f"4. Fusion: {len(fused.documents)} docs ({step_times['fusion']:.0f}ms)")
    
    # Step 5: Generation
    start = time.time()
    generator = GroundedGenerator()
    gen_result = generator.generate(
        query=query,
        context=fused.formatted_context,
        citations_map=fused.citations
    )
    step_times['generation'] = (time.time() - start) * 1000
    print(f"5. Generation: grounded={gen_result.is_grounded} ({step_times['generation']:.0f}ms)")
    
    # Step 6: Persona Rewriting (NEW!)
    start = time.time()
    rewriter = PersonaRewriter()
    rewrite_result = rewriter.rewrite(
        gen_result.answer,
        query,
        Persona.STARTUP_FOUNDER
    )
    step_times['persona_rewrite'] = (time.time() - start) * 1000
    print(f"6. Persona Rewrite: success={rewrite_result.success} ({step_times['persona_rewrite']:.0f}ms)")
    
    # Summary
    total = sum(step_times.values())
    print(f"\n" + "="*40)
    print(f"TOTAL TIME: {total:.0f}ms")
    print("="*40)
    print("Time breakdown:")
    for step, ms in step_times.items():
        pct = (ms / total * 100) if total > 0 else 0
        print(f"  {step:20s}: {ms:6.0f}ms ({pct:4.1f}%)")
    
    print("\n" + "="*40)
    print("REWRITTEN ANSWER (for Startup Founder)")
    print("="*40)
    if rewrite_result.success:
        print(rewrite_result.rewritten_answer[:1000] + "..." if len(rewrite_result.rewritten_answer) > 1000 else rewrite_result.rewritten_answer)
    else:
        print("(Rewriting failed, showing original)")
        print(gen_result.answer[:500] + "...")
    
    return True


def main():
    """Run all tests."""
    print("="*60)
    print("STEP 7 OPTIMIZATION TESTS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # Test 1: PersonaRewriter
    try:
        results['persona_rewriter'] = test_persona_rewriter()
    except Exception as e:
        print(f"  ERROR: {e}")
        results['persona_rewriter'] = False
    
    # Test 2: EmbeddingCache
    try:
        results['embedding_cache'] = test_embedding_cache()
    except Exception as e:
        print(f"  ERROR: {e}")
        results['embedding_cache'] = False
    
    # Test 3: Full Pipeline
    try:
        results['full_pipeline'] = asyncio.run(test_full_pipeline_with_persona())
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        results['full_pipeline'] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test:25s}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
