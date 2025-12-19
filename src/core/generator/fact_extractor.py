"""
Canonical Fact Extractor (CAF Pass 1).

Extracts structured facts from retrieved documents into CanonicalFact schema.
This is the first pass of the Canonical Answer Framework.

SOLID Principles:
- Single Responsibility: Only handles fact extraction
- Open/Closed: Uses prompts from prompts.py, config from config.py
- Dependency Inversion: Depends on abstractions (GeneratorConfig)
"""
import json
import re
import logging
from typing import List, Dict, Optional, Protocol

from .canonical_types import (
    CanonicalFact, 
    CanonicalFactList, 
    FactDomain, 
    FactType, 
    Relevance
)
from .config import GeneratorConfig
from .prompts import build_caf_extraction_prompt

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM client - enables dependency injection."""
    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        ...


class GeminiClientAdapter:
    """
    Adapter for Gemini client.
    
    Encapsulates Gemini-specific logic and provides a clean interface.
    Config is loaded from environment via GeneratorConfig.
    """
    
    def __init__(self, config: GeneratorConfig = None):
        """
        Initialize with config from environment.
        
        Args:
            config: GeneratorConfig instance (defaults to from_env())
        """
        self.config = config or GeneratorConfig.from_env()
        self._client = None
        self._available = False
        self._init_client()
    
    def _init_client(self):
        """Initialize Gemini client from environment config."""
        try:
            from google import genai
            import os
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not set in environment")
                return
            
            self._client = genai.Client(api_key=api_key)
            self._available = True
            logger.info(f"Gemini client initialized with model: {self.config.model_name}")
            
        except ImportError:
            logger.warning("google-genai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def generate(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """
        Generate content using Gemini.
        
        Args:
            prompt: Full prompt text
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text
        """
        if not self._available:
            raise RuntimeError("Gemini client not available")
        
        from google.genai import types
        
        config = types.GenerateContentConfig(
            temperature=temperature or 0.1,  # Low for extraction
            max_output_tokens=max_tokens or 4096
        )
        
        response = self._client.models.generate_content(
            model=self.config.model_name,
            contents=prompt,
            config=config
        )
        
        return response.text


class CanonicalFactExtractor:
    """
    Pass 1 of CAF: Extract structured facts from documents.
    
    Takes retrieved documents organized by sub-query and extracts
    CanonicalFact objects that follow a standardized schema.
    
    Example:
        >>> extractor = CanonicalFactExtractor()
        >>> facts = extractor.extract(
        ...     sub_query_contexts={"Điều kiện XNK": "[1] (LEGAL) ..."},
        ...     citations_map=[{"number": 1, "source": "legal", ...}]
        ... )
        >>> print(len(facts))
        5
    """
    
    def __init__(self, llm_client: LLMClient = None, config: GeneratorConfig = None):
        """
        Initialize the fact extractor.
        
        Args:
            llm_client: LLM client for generation (default: GeminiClientAdapter)
            config: Generator configuration (default: from environment)
        """
        self.config = config or GeneratorConfig.from_env()
        self._llm_client = llm_client
    
    @property
    def llm_client(self) -> LLMClient:
        """Lazy-load LLM client."""
        if self._llm_client is None:
            self._llm_client = GeminiClientAdapter(self.config)
        return self._llm_client
    
    def extract(
        self,
        sub_query_contexts: Dict[str, str],
        citations_map: List[Dict] = None
    ) -> CanonicalFactList:
        """
        Extract canonical facts from sub-query contexts.
        
        Args:
            sub_query_contexts: Dict mapping sub-query -> formatted context
            citations_map: List of citation metadata
            
        Returns:
            CanonicalFactList containing extracted facts
        """
        if not sub_query_contexts:
            logger.warning("No sub_query_contexts provided")
            return CanonicalFactList()
        
        if not self.llm_client.is_available:
            logger.error("LLM client not available")
            return CanonicalFactList()
        
        # Format contexts for prompt
        formatted_contexts = self._format_contexts_for_prompt(sub_query_contexts)
        
        # Build prompt using prompts.py
        prompt = build_caf_extraction_prompt(formatted_contexts)
        
        try:
            # Call LLM with low temperature for factual extraction
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=4096
            )
            
            # Parse response
            facts = self._parse_response(response)
            
            logger.info(f"[CFE] Extracted {len(facts)} canonical facts")
            return facts
            
        except Exception as e:
            logger.error(f"[CFE] Extraction error: {e}")
            return CanonicalFactList()
    
    def _format_contexts_for_prompt(self, sub_query_contexts: Dict[str, str]) -> str:
        """Format sub-query contexts into a structured string for the prompt."""
        parts = []
        for i, (sub_query, context) in enumerate(sub_query_contexts.items(), 1):
            parts.append(f"=== SUB-QUERY {i}: {sub_query} ===\n{context}")
        return "\n\n".join(parts)
    
    def _parse_response(self, response: str) -> CanonicalFactList:
        """Parse LLM response into CanonicalFactList."""
        # Try multiple parsing strategies
        
        # Strategy 1: Direct parse
        try:
            data = json.loads(response)
            if isinstance(data, list):
                facts = [CanonicalFact.from_dict(d) for d in data]
                return CanonicalFactList(facts=facts)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*\n([\s\S]*?)\n```', response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, list):
                    facts = [CanonicalFact.from_dict(d) for d in data]
                    return CanonicalFactList(facts=facts)
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Find array in response
        array_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', response)
        if array_match:
            try:
                data = json.loads(array_match.group(0))
                if isinstance(data, list):
                    facts = [CanonicalFact.from_dict(d) for d in data]
                    return CanonicalFactList(facts=facts)
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"[CFE] Failed to parse response: {response[:200]}...")
        return CanonicalFactList()
    
    def extract_from_formatted_context(
        self,
        formatted_context: str,
        sub_queries: List[str]
    ) -> CanonicalFactList:
        """
        Alternative extraction method when sub_query_contexts is not available.
        
        Creates a single context block and extracts facts from it.
        """
        if not sub_queries:
            sub_queries = ["general"]
        
        # Create synthetic sub_query_contexts
        sub_query_contexts = {
            sub_queries[0]: formatted_context
        }
        
        return self.extract(sub_query_contexts)
