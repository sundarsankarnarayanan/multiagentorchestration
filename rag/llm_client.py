"""
LLM client supporting both Anthropic Claude and Ollama.
"""

import logging
import os
from typing import AsyncIterator, Optional, List, Dict, Any
import httpx
import json

logger = logging.getLogger(__name__)


class AnthropicClient:
    """
    Client for Anthropic Claude API.

    Supports streaming responses with Claude models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 120.0
    ):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (from env if not provided)
            model: Model name
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1"

        logger.info(f"Initialized Anthropic client with model: {model}")

    async def check_connection(self) -> bool:
        """
        Check if Anthropic API is accessible.

        Returns:
            True if connected, False otherwise
        """
        try:
            # Try a simple request to verify API key
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "test"}]
                    },
                    timeout=5.0
                )
                return response.status_code in [200, 400]  # 400 is ok, means API is reachable
        except Exception as e:
            logger.error(f"Failed to connect to Anthropic: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        payload = {
            "model": self.model,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get('content', [])
                    if content and len(content) > 0:
                        return content[0].get('text', '')
                    return ""
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    return ""

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they're generated
        """
        payload = {
            "model": self.model,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
            "stream": True,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])  # Remove 'data: ' prefix

                                    # Handle different event types
                                    event_type = data.get('type')

                                    if event_type == 'content_block_delta':
                                        delta = data.get('delta', {})
                                        if delta.get('type') == 'text_delta':
                                            text = delta.get('text', '')
                                            if text:
                                                yield text

                                    elif event_type == 'message_stop':
                                        break

                                except json.JSONDecodeError:
                                    continue
                    else:
                        logger.error(f"Anthropic API error: {response.status_code}")
                        yield ""

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"Error: {str(e)}"


class OllamaClient:
    """
    Client for Ollama local LLM API.

    Supports streaming responses and multiple models.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        timeout: float = 120.0
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
            model: Model name (llama2, mistral, etc.)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout

        logger.info(f"Initialized Ollama client with model: {model}")

    async def check_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.

        Returns:
            True if connected, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False

    async def list_models(self) -> List[str]:
        """
        List available models.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")

        return []

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '')
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return ""

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they're generated
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if 'response' in data:
                                        yield data['response']

                                    # Check if done
                                    if data.get('done', False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        logger.error(f"Ollama API error: {response.status_code}")
                        yield ""

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"Error: {str(e)}"


# Global LLM client instance
_llm_client = None


def get_llm_client(provider: str = "ollama", model: Optional[str] = None):
    """
    Get the global LLM client instance.

    Args:
        provider: 'anthropic' or 'ollama'
        model: Optional model name override

    Returns:
        LLM client instance
    """
    global _llm_client

    if _llm_client is None:
        provider = provider.lower()

        if provider == "anthropic":
            model = model or "claude-3-5-sonnet-20241022"
            _llm_client = AnthropicClient(model=model)
            logger.info("Using Anthropic Claude for LLM")
        elif provider == "ollama":
            model = model or "llama2"
            _llm_client = OllamaClient(model=model)
            logger.info("Using Ollama for LLM")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    return _llm_client


# Backwards compatibility
def get_ollama_client(model: str = "llama2") -> OllamaClient:
    """Get the global Ollama client instance."""
    return OllamaClient(model=model)
