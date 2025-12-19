# -*- coding: utf-8 -*-
"""Test Decomposer with JSON output to file."""
import sys
sys.path.insert(0, ".")

import json
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from src.core.decomposition import QueryDecomposer

query = "Muon thanh lap cong ty xuat nhap khau xay dung o Viet Nam can dieu kien gi, va cho toi mot so doanh nghiep di truoc de tham khao?"

print("Testing QueryDecomposer...")

try:
    d = QueryDecomposer()
    result = d.decompose(query)
    
    output = {
        "success": True,
        "is_decomposed": result.is_decomposed,
        "method": result.method,
        "reasoning": result.reasoning,
        "sub_queries": [
            {"query": sq.query, "type": sq.query_type, "order": sq.order}
            for sq in result.sub_queries
        ]
    }
except Exception as e:
    output = {
        "success": False,
        "error": str(e)
    }

# Write to file
with open("tests/test_result/decompose_test.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Result saved to tests/test_result/decompose_test.json")
print(f"Success: {output.get('success', False)}")
if output.get("success"):
    print(f"Method: {output['method']}")
    print(f"Sub-queries: {len(output['sub_queries'])}")
else:
    print(f"Error: {output.get('error', 'Unknown')}")
