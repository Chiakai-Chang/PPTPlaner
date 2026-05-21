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


# Known default endpoints - ordered by priority
# We test these with their EXPECTED API type only (fast)
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_LLAMACPP_URL = "http://localhost:8080"

# API endpoints to try for brute-force detection
API_SUFFIXES = [
    ("/api/tags", "Ollama"),
    ("/props", "llama.cpp"),
    ("/v1/models", "OpenAI-compatible"),
]


class ModelDetector:
    """Detects and manages local AI model endpoints."""
    
    def __init__(self, endpoints: List[str] = None, verbose: bool = True):
        """
        Initialize the model detector.
        
        Detection strategy:
        1. Test Ollama default URL with Ollama API
        2. Test llama.cpp default URL with llama.cpp API
        3. If neither works → ask user for URL
        4. If user URL fails → try all API suffixes (brute force)
        
        Args:
            endpoints: Custom endpoints to check (optional)
            verbose: If True, print detailed detection information
        """
        self.endpoints = endpoints or []
        self.verbose = verbose
        self._cache: Dict[str, DetectedEndpoint] = {}
        
    def _log(self, message: str):
        """Log a detection message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ModelDetector] {message}")
        logger.debug(message)
    
    def _test_with_suffix(self, base_url: str, suffix: str, api_name: str) -> DetectedEndpoint:
        """Test a URL with a specific API suffix."""
        result = DetectedEndpoint(url=base_url, type="unknown", available=False)
        
        try:
            test_url = f"{base_url.rstrip('/')}{suffix}"
            req = urllib.request.Request(
                test_url,
                headers={"Accept": "application/json"},
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    result.available = True
                    result.models = []
                    
                    # Extract models based on API type
                    if suffix == "/api/tags":
                        # Ollama
                        result.type = "ollama"
                        for model in data.get("models", []):
                            result.models.append(DetectedModel(
                                name=model.get("name", "unknown"),
                                source="ollama",
                                endpoint=base_url,
                                details=model
                            ))
                    elif suffix == "/props":
                        # llama.cpp
                        result.type = "llamacpp"
                        result.props = data
                        model_alias = data.get("model_alias", "unknown")
                        result.models.append(DetectedModel(
                            name=model_alias,
                            source="llamacpp",
                            endpoint=base_url,
                            details={"path": data.get("model_path", "")}
                        ))
                    elif suffix == "/v1/models":
                        # OpenAI-compatible
                        result.type = "generic"
                        models_data = data.get("data", data.get("models", []))
                        for model in models_data:
                            result.models.append(DetectedModel(
                                name=model.get("id", model.get("name", "unknown")),
                                source="generic",
                                endpoint=base_url,
                                details=model
                            ))
                    
                    return result
        except Exception:
            pass
        
        return result
    
    def detect_endpoint(self, endpoint_url: str, is_user_provided: bool = False) -> DetectedEndpoint:
        """
        Detect what type of server is running at the given URL and get its models.
        
        Detection strategy:
        - Default URLs: Test only the expected API (fast)
        - User-provided URLs: Try all API suffixes (brute force)
        
        Args:
            endpoint_url: The URL to check (e.g., http://localhost:11434)
            is_user_provided: If True, try all API suffixes for brute-force detection
        
        Returns:
            DetectedEndpoint with status and model information
        """
        # Check cache first
        if endpoint_url in self._cache:
            self._log(f"Using cached result for {endpoint_url}")
            return self._cache[endpoint_url]
        
        self._log(f"Testing endpoint: {endpoint_url}")
        
        # Determine which suffixes to try
        if is_user_provided:
            # User-provided URL that failed - try all suffixes
            self._log(f"  → User-provided URL, testing all API suffixes...")
            suffixes = API_SUFFIXES
        else:
            # Default URL - determine expected suffix
            if endpoint_url == DEFAULT_OLLAMA_URL:
                suffixes = [("/api/tags", "Ollama")]
            elif endpoint_url == DEFAULT_LLAMACPP_URL:
                suffixes = [("/props", "llama.cpp")]
            else:
                # Unknown URL - try all suffixes
                suffixes = API_SUFFIXES
        
        # Try detection methods
        detection_results = []
        
        for suffix, api_name in suffixes:
            self._log(f"  → Testing {api_name} ({suffix})...")
            result = self._test_with_suffix(endpoint_url, suffix, api_name)
            detection_results.append((api_name, result))
            
            if result.available:
                self._log(f"  ✅ Detected as: {api_name}")
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
    
    def detect_quick(self) -> Optional[DetectedEndpoint]:
        """Quick detection - tries default endpoints with their expected API.
        
        Flow:
        1. Test Ollama default (localhost:11434/api/tags)
        2. Test llama.cpp default (localhost:8080/props)
        3. If both fail → return None (user should specify)
        
        Returns immediately if any endpoint responds.
        Useful for fast startup check.
        """
        # Step 1: Test Ollama default
        self._log(f"Quick check: {DEFAULT_OLLAMA_URL}")
        result = self.detect_endpoint(DEFAULT_OLLAMA_URL)
        if result.available:
            self._log(f"  ✅ Found {result.type} at {DEFAULT_OLLAMA_URL}")
            return result
        self._log(f"  ❌ Not available")
        
        # Step 2: Test llama.cpp default
        self._log(f"Quick check: {DEFAULT_LLAMACPP_URL}")
        result = self.detect_endpoint(DEFAULT_LLAMACPP_URL)
        if result.available:
            self._log(f"  ✅ Found {result.type} at {DEFAULT_LLAMACPP_URL}")
            return result
        self._log(f"  ❌ Not available")
        
        # Both failed
        self._log(f"  ❌ No server found in quick check")
        self._log(f"  ℹ Please specify your local model URL or click '偵測' to scan")
        return None
    
    def detect_all(self) -> List[DetectedEndpoint]:
        """Full detection - tests default endpoints and any custom ones.
        
        Flow:
        1. Test Ollama default (localhost:11434/api/tags)
        2. Test llama.cpp default (localhost:8080/props)
        3. Test any custom endpoints (with brute-force if needed)
        """
        self._log(f"Starting full detection...")
        results = []
        
        # Step 1: Test Ollama default
        self._log(f"\n[1] Testing {DEFAULT_OLLAMA_URL}")
        result = self.detect_endpoint(DEFAULT_OLLAMA_URL)
        results.append(result)
        
        # Step 2: Test llama.cpp default
        self._log(f"\n[2] Testing {DEFAULT_LLAMACPP_URL}")
        result = self.detect_endpoint(DEFAULT_LLAMACPP_URL)
        results.append(result)
        
        # Step 3: Test any custom endpoints
        for i, endpoint_url in enumerate(self.endpoints, 3):
            self._log(f"\n[{i}] Testing custom endpoint: {endpoint_url}")
            result = self.detect_endpoint(endpoint_url, is_user_provided=True)
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
            self._log(f"  ℹ Please check:")
            self._log(f"    - Is Ollama running? (default: {DEFAULT_OLLAMA_URL})")
            self._log(f"    - Is llama.cpp running? (default: {DEFAULT_LLAMACPP_URL})")
            self._log(f"    - Or specify a custom URL in the UI")
        self._log(f"{'='*50}")
        
        return results
    
    def detect_custom_endpoint(self, url: str) -> DetectedEndpoint:
        """Detect a custom endpoint specified by the user.
        
        Flow:
        1. Try the user-provided URL as-is
        2. If it fails, try all API suffixes (brute force)
        """
        self._log(f"Detecting custom endpoint: {url}")
        
        # Remove trailing slash if present
        url = url.rstrip('/')
        
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            self._log(f"Added http:// scheme: {url}")
        
        # Step 1: Try the user-provided URL as-is
        self._log(f"  → Trying {url} as-is...")
        result = self.detect_endpoint(url, is_user_provided=False)
        
        if result.available:
            self._log(f"  ✅ Connected to {url}")
            return result
        
        # Step 2: Try all API suffixes (brute force)
        self._log(f"  → URL didn't work, trying all API suffixes...")
        result = self.detect_endpoint(url, is_user_provided=True)
        
        return result
    
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
    
    def ask_user_for_url(self) -> str:
        """Ask the user for a custom URL."""
        return input(f"Please enter your local model URL (e.g., {DEFAULT_OLLAMA_URL} or {DEFAULT_LLAMACPP_URL}): ")
    
    def clear_cache(self):
        """Clear detection cache."""
        self._cache.clear()


# Global detector instance with verbose output enabled
default_detector = ModelDetector(verbose=True)
