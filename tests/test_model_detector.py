"""
Unit tests for model detection.
"""
import pytest
from agents.model_detector import ModelDetector, DetectedEndpoint, DetectedModel


class TestModelDetector:
    """Test model detection functionality."""
    
    def test_create_detector(self):
        """Test creating a detector instance."""
        detector = ModelDetector()
        assert detector is not None
        assert len(detector.endpoints) > 0
    
    def test_create_detector_with_custom_endpoints(self):
        """Test creating a detector with custom endpoints."""
        endpoints = [
            "http://custom:9999"
        ]
        detector = ModelDetector(endpoints)
        assert len(detector.endpoints) == 1
        assert detector.endpoints[0] == "http://custom:9999"
    
    def test_detect_unavailable_endpoint(self):
        """Test detecting an unavailable endpoint."""
        detector = ModelDetector()
        result = detector.detect_endpoint("http://localhost:9999")
        
        assert not result.available
    
    def test_detected_model_str(self):
        """Test DetectedModel string representation."""
        model = DetectedModel(
            name="llama3.1",
            source="ollama",
            endpoint="http://localhost:11434"
        )
        
        assert "llama3.1" in str(model)
        assert "ollama" in str(model)
    
    def test_clear_cache(self):
        """Test clearing detection cache."""
        detector = ModelDetector()
        
        # Add something to cache
        detector.detect_endpoint("http://localhost:9999")
        
        # Clear cache
        detector.clear_cache()
        
        # Should be empty
        assert len(detector._cache) == 0
    
    def test_get_first_available_endpoint_returns_none_when_none_available(self):
        """Test that get_first_available_endpoint returns None when no endpoints available."""
        detector = ModelDetector([
            "http://localhost:9999"
        ])
        
        result = detector.get_first_available_endpoint()
        assert result is None
    
    def test_detected_endpoint_creation(self):
        """Test creating DetectedEndpoint."""
        endpoint = DetectedEndpoint(
            url="http://localhost:11434",
            type="ollama",
            available=True
        )
        
        assert endpoint.available
        assert endpoint.type == "ollama"
        assert endpoint.url == "http://localhost:11434"
