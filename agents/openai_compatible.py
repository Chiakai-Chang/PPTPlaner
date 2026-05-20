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
        self.model = agent_config.get("model", "llama3.1")
        self.max_retries = agent_config.get("max_retries", 3)
        self.retry_delay = agent_config.get("retry_delay", 5)
    
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
        
        request_data = self._build_request(prompt, mode, options)
        if model:
            request_data["model"] = model
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        attempt = 0
        while attempt < max_retries:
            try:
                logger.info(f"Calling {self.NAME} for {mode}... (Attempt {attempt + 1}/{max_retries})")
                
                req = urllib.request.Request(
                    f"{self.api_base}/chat/completions",
                    data=json.dumps(request_data).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=120) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result["choices"][0]["message"]["content"]
                
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    raise AgentAuthenticationError("Authentication failed", self.NAME)
                elif e.code == 429:
                    logger.warning("Rate limited, retrying...")
                    attempt += 1
                    if attempt < max_retries:
                        import time
                        time.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"HTTP error: {e.code}")
                    attempt += 1
            except Exception as e:
                logger.warning(f"Request failed: {str(e)}")
                attempt += 1
            
            if attempt < max_retries:
                import time
                time.sleep(retry_delay)
        
        raise AgentExecutionError(
            f"Agent failed after {max_retries} attempts",
            self.NAME,
            max_retries
        )
    
    def get_models(self) -> List[str]:
        """Return list of available models."""
        # Try to fetch from API
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
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return [m["id"] for m in result.get("data", [])]
        except Exception:
            # Fallback defaults
            return ["llama3.1", "llama3.2", "mistral"]
    
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


# Auto-register
from .registry import AgentRegistry
AgentRegistry().register("openai-compatible", OpenAICompatibleAdapter)
