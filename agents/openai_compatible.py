"""
OpenAI-Compatible API Adapter

Supports any service that exposes the OpenAI API format:
- Ollama (localhost:11434)
- llama.cpp server
- vLLM
- OpenRouter
- Other compatible endpoints

This is NOT the same as the OpenAI direct API adapter.
"""
import json
import logging
import socket
import time
from typing import Optional, List, Dict, Any
from .base import AgentInterface
from .exceptions import AgentExecutionError, AgentAuthenticationError

logger = logging.getLogger(__name__)


class OpenAICompatibleAdapter(AgentInterface):
    """OpenAI-compatible API adapter.
    
    Works with any service exposing the OpenAI API format.
    """
    
    NAME = "OpenAI-compatible API"
    COMMAND = "openai-compat"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        agent_config = config.get("agent_config", {})
        self.api_base = agent_config.get("api_base", "http://localhost:11434/v1")
        self.api_key = agent_config.get("api_key", "not-needed")
        self.model = agent_config.get("model", None)  # Will be set dynamically from endpoint
        self.max_retries = agent_config.get("max_retries", 3)
        self.retry_delay = agent_config.get("retry_delay", 5)
        self._detected_models = None
    
    @staticmethod
    def get_default_endpoints() -> List[str]:
        """Get list of default local endpoints to try."""
        return [
            "http://localhost:11434/v1",  # Ollama default
            "http://127.0.0.1:11434/v1", # Ollama alternative
            "http://localhost:8080/v1",   # llama.cpp default
            "http://127.0.0.1:8080/v1",  # llama.cpp alternative
        ]
    
    def _build_request(self, prompt: str, mode: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build API request payload."""
        return {
            "model": options.get("model", self.model) if options else self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": options.get("temperature", 0.7) if options else 0.7,
            "max_tokens": options.get("max_tokens", 4096) if options else 4096
        }
    
    def execute(
        self,
        prompt: str,
        mode: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute agent via OpenAI-compatible API."""
        import urllib.request
        import urllib.error
        import time
        
        # Use detected model if none specified
        actual_model = model or self.model
        if not actual_model:
            available = self.get_models()
            actual_model = available[0] if available else "llama3.1"
            logger.info(f"Using detected model: {actual_model}")
        
        request_data = self._build_request(prompt, mode, options)
        request_data["model"] = actual_model
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"🔹 [{self.NAME}] Calling {mode} (model={actual_model}, endpoint={self.api_base})")
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            try:
                logger.info(f"  ℹ Calling {self.NAME} for {mode}... (Attempt {attempt + 1}/{max_retries})")
                
                req = urllib.request.Request(
                    f"{self.api_base}/chat/completions",
                    data=json.dumps(request_data).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                # Local models need much longer timeout
                # Check if this is a local endpoint
                is_local = 'localhost' in self.api_base or '127.0.0.1' in self.api_base
                request_timeout = 600 if is_local else 120  # 10 minutes for local, 2 minutes for cloud
                
                logger.info(f"  ℹ Request timeout: {request_timeout}s ({'local' if is_local else 'cloud'})")
                
                # Add progress logging for long-running requests
                if is_local:
                    logger.info(f"  ℹ Waiting for local model response... (this may take several minutes)")
                
                with urllib.request.urlopen(req, timeout=request_timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"  ✅ [{self.NAME}] {mode} completed ({len(content)} characters)")
                    return content
                
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code == 401:
                    logger.error(f"  ❌ Authentication failed for {self.api_base}")
                    raise AgentAuthenticationError("Authentication failed", self.NAME)
                elif e.code == 429:
                    logger.warning(f"  ⚠️ Rate limited (429), retrying in {retry_delay}s...")
                else:
                    logger.warning(f"  ⚠️ HTTP {e.code}: {e.reason}")
                
            except TimeoutError as e:
                last_error = e
                logger.warning(f"  ⚠️ Request timed out after {request_timeout}s")
                logger.warning(f"  ℹ Local models may need more time. Retrying...")
                
            except socket.timeout as e:
                last_error = e
                logger.warning(f"  ⚠️ Socket timeout: {str(e)}")
                logger.warning(f"  ℹ Local models may need more time. Retrying...")
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if 'timed out' in error_str or 'timeout' in error_str:
                    logger.warning(f"  ⚠️ Timeout error: {str(e)}")
                    logger.warning(f"  ℹ Local models may need more time. Retrying...")
                else:
                    logger.warning(f"  ⚠️ Request failed: {str(e)}")
                
            attempt += 1
            
            if attempt < max_retries:
                logger.info(f"  🔄 Retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
        
        logger.error(f"  ❌ [{self.NAME}] {mode} failed after {max_retries} attempts")
        logger.error(f"  ℹ Last error: {str(last_error) if last_error else 'Unknown error'}")
        raise AgentExecutionError(
            f"Agent failed after {max_retries} attempts: {str(last_error) if last_error else 'Unknown error'}",
            self.NAME,
            max_retries
        )
    
    def _fetch_models_from_api(self) -> List[str]:
        """Fetch models from API endpoint with proper error handling."""
        import urllib.request
        import urllib.error
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            req = urllib.request.Request(
                f"{self.api_base}/models",
                headers=headers,
                method='GET'
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Handle both OpenAI format and llama.cpp format
                if "data" in result:
                    # OpenAI format
                    return [m["id"] for m in result["data"]]
                elif "models" in result:
                    # llama.cpp format
                    return [m["id"] for m in result["models"]]
                else:
                    return []
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP {e.code} fetching models from {self.api_base}")
            return []
        except Exception as e:
            logger.debug(f"Failed to fetch models from {self.api_base}: {e}")
            return []
    
    def get_models(self) -> List[str]:
        """Return list of available models, caching the result."""
        # Return cached result if available
        if self._detected_models is not None:
            return self._detected_models
        
        # Try to fetch from API
        models = self._fetch_models_from_api()
        
        if models:
            self._detected_models = models
            logger.info(f"Discovered {len(models)} models from {self.api_base}")
            return models
        
        # Fallback to detecting local endpoints
        from .model_detector import default_detector
        endpoints = default_detector.detect_all()
        for endpoint in endpoints:
            if endpoint.available and endpoint.models:
                model_names = [m.name for m in endpoint.models]
                self._detected_models = model_names
                logger.info(f"Using detected models from {endpoint.type}: {model_names}")
                return model_names
        
        # Final fallback
        fallback = ["llama3.1", "llama3.2", "mistral"]
        self._detected_models = fallback
        return fallback
    
    def is_available(self) -> bool:
        """Check if API endpoint is available."""
        try:
            import urllib.request
            import urllib.error
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            req = urllib.request.Request(
                f"{self.api_base}/models",
                headers=headers,
                method='GET'
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def get_installation_hint(self) -> str:
        """Return installation instructions."""
        return "Install Ollama: https://ollama.ai/ or run llama.cpp server"


# Auto-register
from .registry import AgentRegistry
AgentRegistry().register("openai-compatible", OpenAICompatibleAdapter)
AgentRegistry().register("ollama", OpenAICompatibleAdapter)  # Alias
AgentRegistry().register("llamacpp", OpenAICompatibleAdapter)  # Alias
