"""
Smart local model detection for PPTPlaner.

Automatically detects available local AI models:
- Ollama (default port 11434)
- llama.cpp (default port 8080)
- Any OpenAI-compatible endpoint

Key features:
- Tries all server types for each URL (no port assumptions)
- Verbose logging for debugging
- Supports custom endpoint detection
- Caches results to avoid repeated network calls
"""
import urllib.request
import urllib.error
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DetectedModel:
    """Information about a detected model."""
    name: str
    source: str  # "ollama", "llamacpp", "generic"
    endpoint: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.name} ({self.source} @ {self.endpoint})"


@dataclass
class DetectedEndpoint:
    """Information about a detected endpoint."""
    url: str
    type: str  # "ollama", "llamacpp", "generic", "unknown"
    available: bool
    models: List[DetectedModel] = field(default_factory=list)
    error: Optional[str] = None
    props: Optional[Dict[str, Any]] = None
    detection_details: List[str] = field(default_factory=list)


# Default endpoints to check - ordered by likelihood
# Try localhost:11434 first (most common Ollama setup)
# Then localhost:8080 (common llama.cpp setup)
# 127.0.0.1 variants are fallbacks
DEFAULT_ENDPOINTS = [
    "http://localhost:11434",  # Ollama default - most common
    "http://localhost:8080",   # llama.cpp default - second most common
    "http://127.0.0.1:11434",  # Ollama fallback
    "http://127.0.0.1:8080",   # llama.cpp fallback
]


class ModelDetector:
    """Detects and manages local AI model endpoints."""
    
    def __init__(self, endpoints: List[str] = None, verbose: bool = True):
        """
        Initialize the model detector.
        
        Args:
            endpoints: List of endpoint URLs to check (or dicts with 'url' and 'type' keys)
            verbose: If True, print detailed detection information
        """
        # Handle both old format (dicts) and new format (strings)
        if endpoints:
            processed = []
            for ep in endpoints:
                if isinstance(ep, dict):
                    processed.append(ep.get("url", ""))
                else:
                    processed.append(ep)
            self.endpoints = processed
        else:
            self.endpoints = DEFAULT_ENDPOINTS
        self.verbose = verbose
        self._cache: Dict[str, DetectedEndpoint] = {}
        
    def _log(self, message: str):
        """Log a detection message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ModelDetector] {message}")
        logger.debug(message)
    
    def detect_endpoint(self, endpoint_url: str) -> DetectedEndpoint:
        """
        Detect what type of server is running at the given URL and get its models.
        
        This method tries ALL server types for each URL because:
        - Ollama could be running on port 8080
        - llama.cpp could be running on port 11434
        - Custom endpoints could be any type
        
        Args:
            endpoint_url: The URL to check (e.g., http://localhost:11434)
        
        Returns:
            DetectedEndpoint with status and model information
        """
        # Check cache first
        if endpoint_url in self._cache:
            self._log(f"Using cached result for {endpoint_url}")
            return self._cache[endpoint_url]
        
        self._log(f"Testing endpoint: {endpoint_url}")
        
        # Try each detection method
        detection_results = []
        
        # Try Ollama detection
        self._log(f"  → Testing Ollama (/api/tags)...")
        ollama_result = self._try_ollama(endpoint_url)
        detection_results.append(("Ollama", ollama_result))
        
        # Try llama.cpp detection
        self._log(f"  → Testing llama.cpp (/props)...")
        llama_result = self._try_llamacpp(endpoint_url)
        detection_results.append(("llama.cpp", llama_result))
        
        # Try generic OpenAI API detection
        self._log(f"  → Testing OpenAI API (/v1/models)...")
        generic_result = self._try_generic(endpoint_url)
        detection_results.append(("Generic", generic_result))
        
        # Find the first successful detection
        for name, result in detection_results:
            if result.available:
                self._log(f"  ✅ Detected as: {name}")
                self._log(f"  ✅ Found {len(result.models)} model(s)")
                self._cache[endpoint_url] = result
                return result
        
        # No detection succeeded
        error_msg = f"No server detected at {endpoint_url}"
        self._log(f"  ❌ {error_msg}")
        
        result = DetectedEndpoint(
            url=endpoint_url,
            type="unknown",
            available=False,
            error=error_msg,
            detection_details=[f"{name}: {r.error}" for name, r in detection_results]
        )
        self._cache[endpoint_url] = result
        return result
    
    def _try_ollama(self, url: str) -> DetectedEndpoint:
        """Try to detect an Ollama instance."""
        result = DetectedEndpoint(url=url, type="ollama", available=False)
        
        try:
            req = urllib.request.Request(
                f"{url}/api/tags",
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
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
        except urllib.error.URLError as e:
            result.error = f"Cannot connect to Ollama: {e.reason}"
        except Exception as e:
            result.error = f"Ollama detection failed: {str(e)}"
        
        return result
    
    def _try_llamacpp(self, url: str) -> DetectedEndpoint:
        """Try to detect a llama.cpp instance."""
        result = DetectedEndpoint(url=url, type="llamacpp", available=False)
        
        try:
            req = urllib.request.Request(
                f"{url}/props",
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
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
        except urllib.error.URLError as e:
            result.error = f"Cannot connect to llama.cpp: {e.reason}"
        except Exception as e:
            result.error = f"llama.cpp detection failed: {str(e)}"
        
        return result
    
    def _try_generic(self, url: str) -> DetectedEndpoint:
        """Try to detect a generic OpenAI-compatible endpoint."""
        result = DetectedEndpoint(url=url, type="generic", available=False)
        
        try:
            req = urllib.request.Request(
                f"{url}/v1/models",
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    result.available = True
                    result.models = []
                    
                    # Handle both OpenAI format and llama.cpp format
                    models_data = data.get("data", data.get("models", []))
                    
                    for model in models_data:
                        detected = DetectedModel(
                            name=model.get("id", model.get("name", "unknown")),
                            source="generic",
                            endpoint=url,
                            details=model
                        )
                        result.models.append(detected)
                    
                    return result
        except Exception as e:
            result.error = f"Generic API detection failed: {str(e)}"
        
        return result
    
    def detect_quick(self) -> Optional[DetectedEndpoint]:
        """Quick detection - tries only the most common endpoint first.
        
        Returns immediately if the first endpoint responds.
        Useful for fast startup check.
        """
        if not self.endpoints:
            return None
        
        # Try only the first (most common) endpoint
        url = self.endpoints[0]
        self._log(f"Quick check: {url}")
        
        result = self.detect_endpoint(url)
        if result.available:
            self._log(f"  ✅ Found {result.type} at {url}")
            return result
        
        self._log(f"  ❌ Not available")
        return None
    
    def detect_all(self) -> List[DetectedEndpoint]:
        """Detect all configured endpoints."""
        self._log(f"Starting detection of {len(self.endpoints)} endpoints...")
        results = []
        
        for i, endpoint_url in enumerate(self.endpoints, 1):
            self._log(f"\n[{i}/{len(self.endpoints)}] Testing {endpoint_url}")
            result = self.detect_endpoint(endpoint_url)
            results.append(result)
        
        # Summary
        available = [r for r in results if r.available]
        self._log(f"\n{'='*50}")
        self._log(f"Detection complete:")
        self._log(f"  Total endpoints: {len(results)}")
        self._log(f"  Available: {len(available)}")
        if available:
            for ep in available:
                self._log(f"    - {ep.type} at {ep.url}: {len(ep.models)} model(s)")
        else:
            self._log(f"  No available endpoints found")
        self._log(f"{'='*50}")
        
        return results
    
    def detect_custom_endpoint(self, url: str) -> DetectedEndpoint:
        """Detect a custom endpoint specified by the user."""
        self._log(f"Detecting custom endpoint: {url}")
        
        # Remove trailing slash if present
        url = url.rstrip('/')
        
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            self._log(f"Added http:// scheme: {url}")
        
        return self.detect_endpoint(url)
    
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


# Global detector instance with verbose output enabled
default_detector = ModelDetector(verbose=True)
