"""Unit tests for the FastAPI autosize service."""

import pytest
from fastapi.testclient import TestClient
from interior_signage.autosize_service import app


class TestAutosizeService:
    """Test cases for the FastAPI service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.valid_request = {
            "text": "CEO Office",
            "font": "Arial",
            "plate": {
                "width_mm": "200",
                "height_mm": "80",
                "thickness_mm": "3"
            },
            "bevel_mm": "0.5",
            "material": "brushed_metal",
            "finish": "satin",
            "color": "silver",
            "stand": "none",
            "text_style": "raised"
        }
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Interior Signage Validator"
        assert "endpoints" in data
        assert "/validate" in data["endpoints"]
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "interior-signage-validator"
    
    def test_validate_success(self):
        """Test successful validation."""
        response = self.client.post("/validate", json=self.valid_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert data["design_spec"] is not None
        assert data["issues"] is None
        assert "needs" in data
        
        # Check normalized values
        spec = data["design_spec"]
        assert spec["text"] == "CEO Office"
        assert spec["font"] == "Arial"
        assert spec["plate"]["width_mm"] == 200.0
        assert "font_size_pt" in spec
    
    def test_validate_missing_fields(self):
        """Test validation with missing required fields."""
        # Missing text field
        invalid_request = self.valid_request.copy()
        del invalid_request["text"]
        
        response = self.client.post("/validate", json=invalid_request)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_validate_constraint_violation(self):
        """Test validation with constraint violations."""
        # Thickness too small
        invalid_request = self.valid_request.copy()
        invalid_request["plate"]["thickness_mm"] = "1.5"
        
        response = self.client.post("/validate", json=invalid_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is False
        assert data["issues"] is not None
        assert "Thickness must be ≥ 2.0 mm" in data["issues"]
    
    def test_validate_minimal_request(self):
        """Test validation with minimal required fields only."""
        minimal_request = {
            "text": "Test",
            "font": "Arial",
            "plate": {
                "width_mm": "100",
                "height_mm": "50",
                "thickness_mm": "3"
            }
        }
        
        response = self.client.post("/validate", json=minimal_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        
        # Should have default values
        spec = data["design_spec"]
        assert spec["material"] == "brushed_metal"
        assert spec["bevel_mm"] == 0.5
    
    def test_validate_empty_request(self):
        """Test validation with empty request body."""
        response = self.client.post("/validate", json={})
        assert response.status_code == 422  # Pydantic validation error
    
    def test_validate_invalid_json(self):
        """Test validation with invalid JSON."""
        response = self.client.post(
            "/validate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_validate_extra_fields(self):
        """Test validation ignores extra fields."""
        request_with_extra = self.valid_request.copy()
        request_with_extra["extra_field"] = "should be ignored"
        
        response = self.client.post("/validate", json=request_with_extra)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        # Extra field should not appear in response
        assert "extra_field" not in data["design_spec"]
    
    def test_validate_long_text(self):
        """Test validation with overly long text."""
        long_text_request = self.valid_request.copy()
        long_text_request["text"] = "A" * 101  # Exceeds limit
        
        response = self.client.post("/validate", json=long_text_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is False
        assert "Text is too long" in str(data["issues"])
    
    def test_validate_bevel_constraint(self):
        """Test bevel constraint validation."""
        invalid_bevel_request = self.valid_request.copy()
        invalid_bevel_request["plate"]["thickness_mm"] = "4"
        invalid_bevel_request["bevel_mm"] = "2.5"  # > half thickness
        
        response = self.client.post("/validate", json=invalid_bevel_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is False
        assert "Bevel must be ≤ half the thickness" in data["issues"]
    
    def test_docs_endpoint(self):
        """Test that API documentation is accessible."""
        response = self.client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint(self):
        """Test that ReDoc documentation is accessible."""
        response = self.client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]