"""
Language Model service for LLM interactions
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

try:
    import google.genai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI as OpenAIClient
except ImportError:
    OpenAIClient = None

try:
    import anthropic
except ImportError:
    anthropic = None

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Abstract base class for LLM services"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def generate_with_history(self, messages: List[Dict], **kwargs) -> str:
        """Generate response with conversation history"""
        pass


class LLMService(BaseLLMService):
    """
    Main LLM Service
    Provides interface to multiple LLM providers, including Gemini.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 30,
    ):
        """
        Initialize LLM service
        
        Args:
            provider: LLM provider name
            api_key: API key for the provider
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens for generation
            timeout: Request timeout in seconds
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        logger.info(f"Initialized LLM service with provider: {self.provider}")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response from LLM
        """
        provider = kwargs.get("provider", self.provider).lower()
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        if provider == "gemini":
            return await asyncio.to_thread(
                self._generate_gemini,
                prompt,
                model,
                temperature,
                max_tokens,
            )

        if provider == "openai":
            return await asyncio.to_thread(
                self._generate_openai,
                prompt,
                model,
                temperature,
                max_tokens,
            )

        if provider == "anthropic":
            return await asyncio.to_thread(
                self._generate_anthropic,
                prompt,
                model,
                temperature,
                max_tokens,
            )

        raise RuntimeError(f"Provider '{provider}' is not implemented in LLMService")
    
    async def generate_with_history(self, messages: List[Dict], **kwargs) -> str:
        """
        Generate response with conversation history
        """
        prompt = self._build_prompt_from_history(messages)
        return await self.generate(prompt, **kwargs)

    def _generate_gemini(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Generate text using Google Gemini via google.genai."""
        if genai is None:
            raise RuntimeError(
                "google-genai is not installed. Install it with 'pip install google-genai'"
            )
        if not self.api_key:
            raise RuntimeError("Gemini provider requires an API key set in LLM_API_KEY")

        client = genai.Client(api_key=self.api_key)
        chat = client.chats.create(model=model)
        response = chat.send_message(
            prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return self._extract_gemini_response(response)

    def _extract_gemini_response(self, response: Any) -> str:
        """Extract text from a Gemini generate response."""
        if not response:
            return ""

        candidates = getattr(response, "candidates", None)
        if candidates:
            first = candidates[0]
            content = getattr(first, "content", None)
            if content is not None:
                parts = getattr(content, "parts", [])
                if parts:
                    text_parts = [getattr(part, "text", "") for part in parts if getattr(part, "text", None) is not None]
                    if text_parts:
                        return "".join(text_parts)
                raw = getattr(content, "text", None)
                if raw:
                    return raw
        return str(response)

    def _generate_openai(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Generate text using OpenAI."""
        if OpenAIClient is None:
            raise RuntimeError("OpenAI client is not installed. Install it with 'pip install openai'")
        if not self.api_key:
            raise RuntimeError("OpenAI provider requires an API key set in LLM_API_KEY")

        client = OpenAIClient(api_key=self.api_key)
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if hasattr(response, "output_text"):
            return response.output_text
        if isinstance(response, dict):
            return response.get("output_text", str(response))
        return str(response)

    def _generate_anthropic(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Generate text using Anthropic."""
        if anthropic is None:
            raise RuntimeError("Anthropic client is not installed. Install it with 'pip install anthropic'")
        if not self.api_key:
            raise RuntimeError("Anthropic provider requires an API key set in LLM_API_KEY")

        client = anthropic.Client(api_key=self.api_key)
        response = client.completions.create(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens_to_sample=max_tokens,
        )

        if hasattr(response, "completion"):
            return response.completion
        if isinstance(response, dict):
            return response.get("completion", str(response))
        return str(response)

    @staticmethod
    def _build_prompt_from_history(messages: List[Dict]) -> str:
        """Convert conversation history into a single prompt."""
        lines = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            lines.append(f"{role.capitalize()}: {content}")
        lines.append("Assistant:")
        return "\n".join(lines)
