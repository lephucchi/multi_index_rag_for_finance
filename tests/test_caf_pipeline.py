"""
Full CAF Pipeline Test with Detailed Logging.

This script tests the complete Canonical Answer Framework pipeline
and saves all results to tests/test_result/.

Usage:
    python tests/test_caf_pipeline.py
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Set all loggers to DEBUG
for logger_name in ['src.pipeline', 'src.core', 'src.core.generator', 'src.core.retrieval']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


# Test queries - complex multi-domain queries
TEST_QUERIES = [
    "Muốn thành lập công ty xuất nhập khẩu xây dựng ở Việt Nam cần điều kiện gì, và cho tôi một số doanh nghiệp đi trước để tham khảo?"
]


def save_result(result: dict, query_index: int, output_dir: Path):
    """Save test result to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"test_result_{query_index}_{timestamp}.json"
    
    # Make result JSON serializable
    serializable_result = {
        "query": result.get("query", ""),
        "answer": result.get("answer", ""),
        "is_grounded": result.get("is_grounded", False),
        "routes": result.get("routes", []),
        "sub_queries": result.get("sub_queries", []),
        "is_complex": result.get("is_complex", False),
        "citations": result.get("citations", []),
        "citations_map": result.get("citations_map", []),
        "step_times": result.get("step_times", {}),
        "total_time_ms": result.get("total_time_ms", 0),
        "canonical_facts": result.get("canonical_facts", []),
        "sub_query_contexts": result.get("sub_query_contexts", {}),
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Result saved to: {filename}")
    return filename


def save_answer_markdown(result: dict, query_index: int, output_dir: Path):
    """Save answer as markdown file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"answer_{query_index}_{timestamp}.md"
    
    content = f"""# CAF Pipeline Test Result

## Query
{result.get('query', '')}

## Routes
{result.get('routes', [])}

## Sub-Queries
{result.get('sub_queries', [])}

## Canonical Facts Extracted
{json.dumps(result.get('canonical_facts', []), ensure_ascii=False, indent=2)}

## Answer
{result.get('answer', '')}

## Timing
- Total: {result.get('total_time_ms', 0):.2f}ms
- Steps: {json.dumps(result.get('step_times', {}), indent=2)}

## Citations Used
{result.get('citations', [])}
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Answer saved to: {filename}")
    return filename


async def run_test():
    """Run full CAF pipeline test."""
    output_dir = Path(__file__).parent / "test_result"
    output_dir.mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("CAF PIPELINE FULL TEST")
    logger.info("=" * 80)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Test queries: {len(TEST_QUERIES)}")
    logger.info(f"CAF_ENABLED: {os.getenv('CAF_ENABLED', 'true')}")
    logger.info("=" * 80)
    
    # Import pipeline
    try:
        from src.pipeline import run_rag_pipeline_async
        logger.info("Pipeline imported successfully")
    except Exception as e:
        logger.error(f"Failed to import pipeline: {e}")
        return
    
    results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"TEST {i}/{len(TEST_QUERIES)}")
        logger.info(f"Query: {query}")
        logger.info("=" * 80)
        
        try:
            # Run pipeline
            result = await run_rag_pipeline_async(query)
            
            # Log results
            logger.info("")
            logger.info("-" * 40)
            logger.info("RESULT SUMMARY")
            logger.info("-" * 40)
            logger.info(f"Routes: {result.get('routes', [])}")
            logger.info(f"Is Complex: {result.get('is_complex', False)}")
            logger.info(f"Sub-queries: {result.get('sub_queries', [])}")
            logger.info(f"Is Grounded: {result.get('is_grounded', False)}")
            logger.info(f"Total Time: {result.get('total_time_ms', 0):.2f}ms")
            
            # Log canonical facts
            facts = result.get('canonical_facts', [])
            logger.info(f"Canonical Facts: {len(facts)}")
            for j, fact in enumerate(facts, 1):
                logger.info(f"  [{j}] {fact.get('domain', 'N/A')}: {fact.get('statement', '')[:80]}...")
            
            # Log answer preview
            answer = result.get('answer', '')
            logger.info(f"Answer Preview ({len(answer)} chars):")
            for line in answer.split('\n')[:20]:
                logger.info(f"  {line}")
            if answer.count('\n') > 20:
                logger.info("  ... (truncated)")
            
            # Save results
            json_file = save_result(result, i, output_dir)
            md_file = save_answer_markdown(result, i, output_dir)
            
            results.append({
                "query": query,
                "success": True,
                "json_file": str(json_file),
                "md_file": str(md_file),
                "total_time_ms": result.get('total_time_ms', 0),
                "facts_count": len(facts),
            })
            
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
            results.append({
                "query": query,
                "success": False,
                "error": str(e),
            })
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    success_count = sum(1 for r in results if r.get('success', False))
    logger.info(f"Total: {len(results)}, Success: {success_count}, Failed: {len(results) - success_count}")
    
    for i, r in enumerate(results, 1):
        status = "✅" if r.get('success', False) else "❌"
        logger.info(f"  {status} Test {i}: {r.get('query', '')[:50]}...")
        if r.get('success'):
            logger.info(f"      Time: {r.get('total_time_ms', 0):.2f}ms, Facts: {r.get('facts_count', 0)}")
            logger.info(f"      Files: {r.get('json_file', '')}")
        else:
            logger.info(f"      Error: {r.get('error', 'Unknown')}")
    
    # Save summary
    summary_file = output_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"\nSummary saved to: {summary_file}")
    
    logger.info("=" * 80)
    logger.info("TEST COMPLETED")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_test())
