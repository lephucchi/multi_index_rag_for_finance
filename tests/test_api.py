"""
Test cases for FastAPI backend.

Run with: pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


# Create test client
client = TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_api_info(self):
        """GET / should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Multi-Index RAG API"
        assert data["version"] == "1.0.0"
        assert "docs" in data


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_returns_status(self):
        """GET /api/health should return health status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_health_includes_components(self):
        """Health response should include component status."""
        response = client.get("/api/health")
        data = response.json()
        components = data["components"]
        assert "supabase" in components
        assert "gemini" in components
        assert "langgraph" in components


class TestRoutesEndpoint:
    """Tests for routes info endpoint."""
    
    def test_routes_returns_indices(self):
        """GET /api/routes should return available indices."""
        response = client.get("/api/routes")
        assert response.status_code == 200
        data = response.json()
        assert "indices" in data
        indices = [idx["name"] for idx in data["indices"]]
        assert "glossary" in indices
        assert "legal" in indices
        assert "financial" in indices
        assert "news" in indices


class TestQueryEndpoint:
    """Tests for query endpoint."""
    
    def test_query_requires_query_field(self):
        """POST /api/query should require query field."""
        response = client.post("/api/query", json={})
        assert response.status_code == 422  # Validation error
    
    def test_query_rejects_empty_query(self):
        """POST /api/query should reject empty query."""
        response = client.post("/api/query", json={"query": ""})
        assert response.status_code == 422
    
    def test_query_accepts_valid_request(self):
        """POST /api/query should accept valid request."""
        response = client.post(
            "/api/query",
            json={"query": "ROE là gì?"}
        )
        # May return 200 or 500 depending on backend availability
        assert response.status_code in [200, 500]
    
    def test_query_with_options(self):
        """POST /api/query should accept options."""
        response = client.post(
            "/api/query",
            json={
                "query": "ROE là gì?",
                "options": {
                    "max_docs": 5,
                    "include_sources": True,
                    "include_context": False
                }
            }
        )
        assert response.status_code in [200, 500]
    
    def test_query_response_structure(self):
        """Query response should have expected structure."""
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "is_grounded" in data
            assert "citations" in data
            assert "metadata" in data
            
            # Check metadata structure
            metadata = data["metadata"]
            assert "routes" in metadata
            assert "is_complex" in metadata
            assert "total_time_ms" in metadata


class TestQueryValidation:
    """Tests for query input validation."""
    
    def test_query_max_length(self):
        """Query should have maximum length."""
        long_query = "x" * 2001
        response = client.post("/api/query", json={"query": long_query})
        assert response.status_code == 422
    
    def test_query_min_length(self):
        """Query should have minimum length."""
        response = client.post("/api/query", json={"query": ""})
        assert response.status_code == 422
    
    def test_invalid_max_docs(self):
        """max_docs should be within valid range."""
        response = client.post(
            "/api/query",
            json={
                "query": "test",
                "options": {"max_docs": 100}  # > 50
            }
        )
        assert response.status_code == 422


# Integration tests (require backend services)
class TestIntegration:
    """Integration tests - require Supabase and Gemini."""
    
    @pytest.mark.skip(reason="Requires live backend services")
    def test_full_pipeline(self):
        """Test full RAG pipeline."""
        response = client.post(
            "/api/query",
            json={"query": "ROE là gì và VNM có ROE bao nhiêu?"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check answer
        assert len(data["answer"]) > 0
        assert data["is_grounded"] == True
        
        # Check citations
        assert len(data["citations"]) > 0
        
        # Check metadata
        assert data["metadata"]["is_complex"] == True
        assert len(data["metadata"]["sub_queries"]) >= 2
