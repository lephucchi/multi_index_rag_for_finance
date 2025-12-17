"""
Query Decomposer using LLM (Gemini).

Decomposes complex queries into atomic sub-queries for better retrieval.
Follows SOLID principles:
- Single Responsibility: Only handles decomposition logic
- Open/Closed: Extensible via config, closed for modification
- Dependency Inversion: Depends on abstractions (config, classifier interface)
"""
import json
import time
import os
import logging
from typing import List, Optional, Protocol
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

from src.config import DecomposerConfig, QueryType
from .classifier import QueryComplexityClassifier, ClassificationResult

# Setup logging
logger = logging.getLogger(__name__)


# Optional Gemini import
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed. LLM decomposition disabled.")


@dataclass
class SubQuery:
    """
    A decomposed sub-query with type and order.
    
    Attributes:
        query: The sub-query text
        query_type: Type classification (GLOSSARY, LEGAL, FINANCIAL, NEWS)
        order: Execution order (for dependent queries)
    """
    query: str
    query_type: str = QueryType.UNKNOWN
    order: int = 1
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "type": self.query_type,
            "order": self.order
        }
    
    def __str__(self) -> str:
        return f"[{self.query_type}] {self.query}"


@dataclass
class DecompositionResult:
    """
    Result of query decomposition.
    
    Attributes:
        original_query: The original user query
        is_decomposed: Whether decomposition was performed
        sub_queries: List of atomic sub-queries
        reasoning: Explanation of decomposition logic
        latency_ms: Processing time in milliseconds
        method: How decomposition was done (classifier, llm, fallback)
    """
    original_query: str
    is_decomposed: bool
    sub_queries: List[SubQuery]
    reasoning: str = ""
    latency_ms: float = 0.0
    method: str = "unknown"
    
    def to_dict(self) -> dict:
        return {
            "original_query": self.original_query,
            "is_decomposed": self.is_decomposed,
            "sub_queries": [sq.to_dict() for sq in self.sub_queries],
            "reasoning": self.reasoning,
            "latency_ms": round(self.latency_ms, 2),
            "method": self.method
        }
    
    @property
    def query_count(self) -> int:
        return len(self.sub_queries)
    
    def get_queries_by_type(self, query_type: str) -> List[SubQuery]:
        """Get sub-queries filtered by type."""
        return [sq for sq in self.sub_queries if sq.query_type == query_type]


class LLMClientProtocol(Protocol):
    """Protocol for LLM client (Dependency Inversion)."""
    
    def generate(self, prompt: str) -> str:
        """Generate response from prompt."""
        ...


class GeminiClient:
    """Gemini API client implementation."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai not installed")
        
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=1024
        )
    
    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.config
        )
        return response.text


class QueryDecomposer:
    """
    Decompose complex queries into atomic sub-queries.
    
    Uses a two-stage approach:
    1. Fast classifier to detect if decomposition is needed
    2. LLM (Gemini) for actual decomposition
    
    Example:
        >>> decomposer = QueryDecomposer()
        >>> result = decomposer.decompose("ROE là gì và VNM có ROE bao nhiêu")
        >>> for sq in result.sub_queries:
        ...     print(sq)
        [GLOSSARY] ROE là gì
        [FINANCIAL] VNM có ROE bao nhiêu
    """
    
    def __init__(
        self,
        config: DecomposerConfig = None,
        classifier: QueryComplexityClassifier = None,
        llm_client: LLMClientProtocol = None,
        use_classifier: bool = True
    ):
        """
        Initialize the decomposer.
        
        Args:
            config: Decomposer configuration
            classifier: Query complexity classifier (injected)
            llm_client: LLM client for decomposition (injected)
            use_classifier: Whether to use classifier as first-pass filter
        """
        self.config = config or DecomposerConfig()
        self.classifier = classifier if use_classifier else None
        self.llm_client = llm_client
        
        # Lazy init LLM client if not provided
        if self.llm_client is None and GEMINI_AVAILABLE:
            try:
                self.llm_client = GeminiClient(self.config.model_name)
            except (ImportError, ValueError) as e:
                logger.warning(f"Could not initialize Gemini: {e}")
    
    def decompose(self, query: str) -> DecompositionResult:
        """
        Decompose a query into sub-queries.
        
        Args:
            query: User query string
            
        Returns:
            DecompositionResult with sub-queries
        """
        start = time.time()
        query = query.strip()
        
        # Step 1: Quick check with classifier
        if self.classifier:
            classification = self.classifier.classify(query)
            if not classification.is_complex:
                return DecompositionResult(
                    original_query=query,
                    is_decomposed=False,
                    sub_queries=[SubQuery(query=query)],
                    reasoning=f"Simple query: {classification.reason}",
                    latency_ms=(time.time() - start) * 1000,
                    method="classifier"
                )
        
        # Step 2: Use LLM for complex queries
        if self.llm_client:
            try:
                result = self._llm_decompose(query)
                result.latency_ms = (time.time() - start) * 1000
                result.method = "llm"
                return result
            except Exception as e:
                logger.warning(f"LLM decomposition failed: {e}")
        
        # Fallback: Return original query
        return DecompositionResult(
            original_query=query,
            is_decomposed=False,
            sub_queries=[SubQuery(query=query)],
            reasoning="Decomposition unavailable, using original query",
            latency_ms=(time.time() - start) * 1000,
            method="fallback"
        )
    
    def _llm_decompose(self, query: str) -> DecompositionResult:
        """Use LLM to decompose the query."""
        from .prompts import build_few_shot_prompt
        
        prompt = build_few_shot_prompt(query)
        response_text = self.llm_client.generate(prompt)
        
        # Parse JSON response with robust fallback
        data = self._try_parse_json_response(response_text, query)
        
        # Convert to SubQuery objects
        sub_queries = [
            SubQuery(
                query=sq["query"],
                query_type=sq.get("type", QueryType.UNKNOWN),
                order=sq.get("order", i + 1)
            )
            for i, sq in enumerate(data.get("sub_queries", [])[:self.config.max_sub_queries])
        ]
        
        if not sub_queries:
            sub_queries = [SubQuery(query=query)]
        
        return DecompositionResult(
            original_query=data.get("original_query", query),
            is_decomposed=data.get("is_decomposed", len(sub_queries) > 1),
            sub_queries=sub_queries,
            reasoning=data.get("reasoning", "")
        )
    
    def _try_parse_json_response(self, text: str, query: str) -> dict:
        """
        Try to parse JSON response with multiple fallback strategies.
        
        Strategies:
        1. Direct JSON parse after cleaning markdown
        2. Fix common JSON errors (unterminated strings, trailing commas)
        3. Regex extraction of sub_queries
        """
        import re
        
        # Strategy 1: Clean and parse directly
        cleaned = self._clean_json_response(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")
        
        # Strategy 2: Fix common JSON errors
        fixed = self._fix_json_errors(cleaned)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            logger.debug(f"Fixed JSON parse failed: {e}")
        
        # Strategy 3: Regex extraction fallback
        try:
            return self._regex_extract_decomposition(text, query)
        except Exception as e:
            logger.debug(f"Regex extraction failed: {e}")
        
        # Final fallback: return minimal valid structure
        logger.warning(f"All JSON parsing strategies failed for response: {text[:200]}...")
        raise ValueError(f"Could not parse LLM response as JSON")
    
    @staticmethod
    def _fix_json_errors(text: str) -> str:
        """Fix common JSON errors from LLM responses."""
        import re
        
        # Remove trailing commas before ] or }
        text = re.sub(r',\s*([}\]])', r'\1', text)
        
        # Fix unterminated strings - try to close them at line boundaries
        lines = text.split('\n')
        fixed_lines = []
        for line in lines:
            # Count quotes
            quote_count = line.count('"') - line.count('\\"')
            if quote_count % 2 == 1:
                # Odd number of quotes - try to fix
                line = line.rstrip()
                if not line.endswith('"'):
                    line += '"'
            fixed_lines.append(line)
        text = '\n'.join(fixed_lines)
        
        return text
    
    def _regex_extract_decomposition(self, text: str, original_query: str) -> dict:
        """Extract decomposition info using regex as last resort."""
        import re
        
        # Try to extract sub_queries array
        sub_queries = []
        
        # Pattern to match {"query": "...", "type": "...", "order": N}
        pattern = r'\{"query"\s*:\s*"([^"]+)"\s*,\s*"type"\s*:\s*"([A-Z]+)"\s*,\s*"order"\s*:\s*(\d+)\}'
        matches = re.findall(pattern, text)
        
        for match in matches:
            sub_queries.append({
                "query": match[0],
                "type": match[1],
                "order": int(match[2])
            })
        
        if not sub_queries:
            # Try simpler pattern
            simple_pattern = r'"query"\s*:\s*"([^"]+)".*?"type"\s*:\s*"([A-Z]+)"'
            matches = re.findall(simple_pattern, text, re.DOTALL)
            for i, match in enumerate(matches):
                sub_queries.append({
                    "query": match[0],
                    "type": match[1],
                    "order": i + 1
                })
        
        if sub_queries:
            logger.info(f"Regex extracted {len(sub_queries)} sub-queries")
            return {
                "original_query": original_query,
                "is_decomposed": len(sub_queries) > 1,
                "sub_queries": sub_queries,
                "reasoning": "Extracted via regex fallback"
            }
        
        raise ValueError("No sub-queries found via regex")
    
    @staticmethod
    def _clean_json_response(text: str) -> str:
        """Remove markdown code blocks from LLM response."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)
        return text
    
    def decompose_batch(self, queries: List[str]) -> List[DecompositionResult]:
        """Decompose multiple queries."""
        return [self.decompose(q) for q in queries]
