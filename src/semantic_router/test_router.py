"""
Test script for the Semantic Router.

Run from project root:
    python -m src.semantic_router.test_router
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.semantic_router import HybridRouter, RouterConfig
from src.semantic_router.utils import format_route_result, Timer


def test_single_label_routing():
    """Test single-label routing for clear queries."""
    print("\n" + "="*60)
    print("TEST 1: Single-label Routing")
    print("="*60)
    
    # Use single-label config
    config = RouterConfig(enable_multi_label=False)
    router = HybridRouter(config)
    
    test_cases = [
        ("ROE là gì", "glossary"),
        ("Điều 10 Luật Doanh nghiệp 2020", "legal"),
        ("P/E của VNM năm 2024", "financial"),
        ("VN-Index hôm nay thế nào", "news"),
    ]
    
    passed = 0
    for query, expected in test_cases:
        with Timer():
            routes, scores = router.route(query)
        
        actual = routes[0]
        status = "✓" if actual == expected else "✗"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected}, Got: {actual} (conf: {scores[actual]:.3f})")
        
        if actual == expected:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_multi_label_routing():
    """Test multi-label routing for complex queries."""
    print("\n" + "="*60)
    print("TEST 2: Multi-label Routing")
    print("="*60)
    
    router = HybridRouter()  # Multi-label enabled by default
    
    test_cases = [
        ("ROE là gì và VNM có ROE bao nhiêu", ["glossary", "financial"]),
        ("Quy định IPO là gì và điều kiện niêm yết", ["glossary", "legal"]),
        ("FPT công bố gì hôm nay và P/E hiện tại", ["news", "financial"]),
    ]
    
    passed = 0
    for query, expected_routes in test_cases:
        with Timer():
            routes, scores = router.route(query)
        
        # Check if expected routes are in selected
        matched = all(r in routes for r in expected_routes[:2])
        status = "✓" if matched else "✗"
        
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_routes}, Got: {routes}")
        print(f"   Scores: {dict((k, f'{v:.3f}') for k, v in sorted(scores.items(), key=lambda x: -x[1]))}")
        
        if matched:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_rule_based_patterns():
    """Test rule-based pattern matching."""
    print("\n" + "="*60)
    print("TEST 3: Rule-based Patterns")
    print("="*60)
    
    router = HybridRouter()
    
    # These should trigger rule-based routing
    test_cases = [
        # Glossary patterns
        ("vốn điều lệ là gì", "glossary", "là gì"),
        ("định nghĩa công ty cổ phần", "glossary", "định nghĩa"),
        
        # Legal patterns
        ("Điều 15 Luật Chứng khoán", "legal", "Điều + Luật"),
        ("quy định về niêm yết", "legal", "quy định về"),
        
        # News patterns
        ("thị trường hôm nay", "news", "hôm nay"),
        ("tin tức chứng khoán mới nhất", "news", "mới nhất"),
    ]
    
    passed = 0
    for query, expected, pattern in test_cases:
        routes, scores = router.route(query)
        actual = routes[0]
        
        # For rule-based, confidence should be 0.95
        is_rule_based = scores[actual] >= 0.95
        status = "✓" if actual == expected and is_rule_based else "✗"
        
        print(f"{status} Pattern '{pattern}': '{query}'")
        print(f"   Route: {actual} (conf: {scores[actual]:.3f})")
        
        if actual == expected:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_fallback():
    """Test fallback for ambiguous queries."""
    print("\n" + "="*60)
    print("TEST 4: Fallback Behavior")
    print("="*60)
    
    router = HybridRouter()
    
    # Very short/ambiguous queries
    test_queries = [
        "VNM",  # Just a ticker
        "thông tin",  # Very generic
    ]
    
    for query in test_queries:
        routes, scores = router.route(query)
        should_search_all = router.should_search_all_indices(query, scores)
        
        print(f"Query: '{query}'")
        print(f"   Routes: {routes}")
        print(f"   Should search all: {should_search_all}")
        print(f"   Max confidence: {max(scores.values()):.3f}")


def test_batch_routing():
    """Test batch routing performance."""
    print("\n" + "="*60)
    print("TEST 5: Batch Routing Performance")
    print("="*60)
    
    router = HybridRouter()
    
    queries = [
        "ROE là gì",
        "Điều 10 Luật Doanh nghiệp",
        "P/E của VNM",
        "VN-Index hôm nay",
        "Quy định về IPO",
    ] * 10  # 50 queries
    
    with Timer("Batch routing 50 queries"):
        results = router.batch_route(queries)
    
    print(f"Routed {len(results)} queries")
    print(f"Average: {50 / (results and 1):.2f} queries/call")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SEMANTIC ROUTER TEST SUITE")
    print("="*60)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_single_label_routing()
    all_passed &= test_multi_label_routing()
    all_passed &= test_rule_based_patterns()
    test_fallback()  # No pass/fail, just observation
    test_batch_routing()
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
