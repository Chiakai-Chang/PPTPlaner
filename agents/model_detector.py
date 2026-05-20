"""
Smart local model detection for PPTPlaner.

Automatically detects available local AI models:
- Ollama (port 11434)
- llama.cpp (port 8080)
- Other OpenAI-compatible endpoints
"""
import urllib.request
import urllib.error
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class DetectedModel:
    """Information about a detected model."""
    name: str
    source: str  # "ollama", "llamacpp", etc.
    endpoint: str
    details: Dict[str, Any] = None
    
    def __str__(self):
        return f"{self.name} ({self.source} @ {self.endpoint})"


@dataclass
class DetectedEndpoint:
    """Information about a detected endpoint."""
    url: str
    type: str  # "ollama", "llamacpp", "unknown"
    available: bool
    models: List[DetectedModel] = None
    error: Optional[str] = None
    props: Optional[Dict[str, Any]] = None


# Common local endpoints to check
DEFAULT_ENDPOINTS = [
    {"url": "http://localhost:11434", "type": "ollama"},
    {"url": "http://127.0.0.1:11434", "type": "ollama"},
    {"url": "http://localhost:8080", "type": "llamacpp"},
    {"url": "http://127.0.0.1:8080", "type": "llamacpp"},
]


class ModelDetector:
    """Detects and manages local AI model endpoints."""
    
    def __init__(self, endpoints: List[Dict[str, str]] = None):
        self.endpoints = endpoints or DEFAULT_ENDPOINTS
        self._cache: Dict[str, DetectedEndpoint] = {}
    
    def detect_endpoint(self, endpoint_url: str, endpoint_type: str = "unknown") -> DetectedEndpoint:
        """
        Detect if an endpoint is available and get its models.
        
        Args:
            endpoint_url: The URL to check (e.g., http://localhost:11434)
            endpoint_type: The type of endpoint (ollama, llamacpp, unknown)
        
        Returns:
            DetectedEndpoint with status and model information
        """
        # Check cache first
        cache_key = f"{endpoint_url}:{endpoint_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = DetectedEndpoint(
            url=endpoint_url,
            type=endpoint_type,
            available=False
        )
        
        try:
            if endpoint_type == "ollama":
                result = self._detect_ollama(endpoint_url)
            elif endpoint_type == "llamacpp":
                result = self._detect_llamacpp(endpoint_url)
            else:
                result = self._detect_generic(endpoint_url)
        except Exception as e:
            result.error = str(e)
        
        # Cache the result
        self._cache[cache_key] = result
        return result
    
    def _detect_ollama(self, url: str) -> DetectedEndpoint:
        """Detect Ollama instance and get available models."""
        result = DetectedEndpoint(url=url, type="ollama", available=False)
        
        try:
            # Try /api/tags endpoint
            req = urllib.request.Request(
                f"{url}/api/tags",
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    result.available = True
                    result.models = []
                    
                    # Extract models from response
                    for model in data.get("models", []):
                        detected = DetectedModel(
                            name=model.get("name", "unknown"),
                            source="ollama",
                            endpoint=url,
                            details=model
                        )
                        result.models.append(detected)
                    
                    return result
        except urllib.error.URLError:
            result.error = "Cannot connect to Ollama"
        except Exception as e:
            result.error = str(e)
        
        return result
    
    def _detect_llamacpp(self, url: str) -> DetectedEndpoint:
        """Detect llama.cpp instance and get model info."""
        result = DetectedEndpoint(url=url, type="llamacpp", available=False)
        
        try:
            # Try /props endpoint
            req = urllib.request.Request(
                f"{url}/props",
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    result.available = True
                    result.props = data
                    
                    # Extract model info
                    model_alias = data.get("model_alias", "unknown")
                    model_path = data.get("model_path", "")
                    
                    detected = DetectedModel(
                        name=model_alias,
                        source="llamacpp",
                        endpoint=url,
                        details={"path": model_path}
                    )
                    result.models = [detected]
                    
                    return result
        except urllib.error.URLError:
            result.error = "Cannot connect to llama.cpp"
        except Exception as e:
            result.error = str(e)
        
        return result
    
    def _detect_generic(self, url: str) -> DetectedEndpoint:
        """Generic detection for OpenAI-compatible endpoints."""
        result = DetectedEndpoint(url=url, type="unknown", available=False)
        
        try:
            # Try /v1/models endpoint
            req = urllib.request.Request(
                f"{url}/v1/models",
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    result.available = True
                    result.models = []
                    
                    # Extract models from response
                    for model in data.get("data", []):
                        detected = DetectedModel(
                            name=model.get("id", "unknown"),
                            source="generic",
                            endpoint=url,
                            details=model
                        )
                        result.models.append(detected)
                    
                    return result
        except Exception as e:
            result.error = str(e)
        
        return result
    
    def detect_all(self) -> List[DetectedEndpoint]:
        """Detect all configured endpoints."""
        results = []
        
        for endpoint in self.endpoints:
            result = self.detect_endpoint(
                endpoint["url"],
                endpoint.get("type", "unknown")
            )
            results.append(result)
        
        return results
    
    def get_available_endpoints(self) -> List[DetectedEndpoint]:
        """Get only available endpoints."""
        all_endpoints = self.detect_all()
        return [e for e in all_endpoints if e.available]
    
    def get_all_models(self) -> List[DetectedModel]:
        """Get all models from all available endpoints."""
        models = []
        
        for endpoint in self.get_available_endpoints():
            if endpoint.models:
                models.extend(endpoint.models)
        
        return models
    
    def get_first_available_endpoint(self) -> Optional[str]:
        """Get the first available endpoint URL."""
        for endpoint in self.get_available_endpoints():
            return endpoint.url
        return None
    
    def clear_cache(self):
        """Clear detection cache."""
        self._cache.clear()


# Global detector instance
default_detector = ModelDetector()
