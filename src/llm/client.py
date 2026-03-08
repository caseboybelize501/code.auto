"""LLM Client for AI-powered code generation and analysis

Supports:
- OpenAI (commercial - for customer deployments)
- Anthropic (commercial - for customer deployments)  
- llama.cpp server (local - owner use, no API key needed)
- Any OpenAI-compatible local server
"""

import json
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMClient(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client (commercial)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        system_prompt = (system_prompt or "") + "\n\nRespond ONLY with valid JSON. No markdown, no explanations."
        response_text = self.generate(prompt, system_prompt, **kwargs)
        
        # Clean up response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return json.loads(response_text.strip())


class AnthropicClient(LLMClient):
    """Anthropic API client (commercial)"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        client = self._get_client()
        
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        system_prompt = (system_prompt or "") + "\n\nRespond ONLY with valid JSON. No markdown, no explanations."
        response_text = self.generate(prompt, system_prompt, **kwargs)
        
        # Clean up response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return json.loads(response_text.strip())


class LlamaCppClient(LLMClient):
    """Local llama.cpp server client (no API key needed)
    
    Works with:
    - llama.cpp server
    - koboldcpp
    - Any OpenAI-compatible local server
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", model: str = "local-model", context_length: int = 8192):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.context_length = context_length
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using llama.cpp server"""
        
        # Try OpenAI-compatible endpoint first
        url = f"{self.base_url}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            # Try legacy llama.cpp endpoint
            return self._generate_legacy(prompt, system_prompt, **kwargs)
        except Exception as e:
            raise RuntimeError(f"llama.cpp request failed: {e}")
    
    def _generate_legacy(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Fallback for older llama.cpp server versions"""
        url = f"{self.base_url}/completion"
        
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\n"
        full_prompt += f"User: {prompt}\nAssistant:"
        
        payload = {
            "prompt": full_prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "n_predict": kwargs.get("max_tokens", 4096),
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("content", "")
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        system_prompt = (system_prompt or "") + "\n\nRespond ONLY with valid JSON. No markdown, no explanations."
        response_text = self.generate(prompt, system_prompt, **kwargs)
        
        # Clean up response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return json.loads(response_text.strip())
    
    def health_check(self) -> bool:
        """Check if llama.cpp server is running"""
        try:
            for endpoint in ["/health", "/v1/models", "/"]:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    if response.status_code < 500:
                        return True
                except:
                    continue
            return False
        except:
            return False


def create_llm_client(provider: str, **kwargs) -> LLMClient:
    """
    Factory function to create LLM client.
    
    Providers:
    - "openai": OpenAI API (commercial - for customers)
    - "anthropic": Anthropic API (commercial - for customers)
    - "llama-cpp": llama.cpp server (local - owner use)
    - "local": Alias for llama-cpp
    """
    
    if provider == "openai":
        api_key = kwargs.get("api_key")
        model = kwargs.get("model", "gpt-4o-mini")
        if not api_key:
            raise ValueError("OpenAI API key required")
        return OpenAIClient(api_key, model)
    
    elif provider == "anthropic":
        api_key = kwargs.get("api_key")
        model = kwargs.get("model", "claude-3-5-sonnet-20241022")
        if not api_key:
            raise ValueError("Anthropic API key required")
        return AnthropicClient(api_key, model)
    
    elif provider in ["llama-cpp", "local"]:
        base_url = kwargs.get("base_url", "http://localhost:8080")
        model = kwargs.get("model", "local-model")
        context_length = kwargs.get("context_length", 8192)
        return LlamaCppClient(base_url, model, context_length)
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use: openai, anthropic, or llama-cpp")


def check_llama_cpp_available(base_url: str = "http://localhost:8080") -> bool:
    """Check if llama.cpp server is available"""
    client = LlamaCppClient(base_url)
    return client.health_check()
