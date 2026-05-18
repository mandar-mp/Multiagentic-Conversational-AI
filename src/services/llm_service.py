"""
Language Model service for LLM interactions
"""

import logging
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

try:
    import google.generativeai as genai
except ImportError:
    genai = None

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
            return self._generate_gemini(prompt, model, temperature, max_tokens)

        logger.info("Generating response from LLM")
        raise RuntimeError(f"Provider '{provider}' is not implemented in LLMService")
    
    async def generate_with_history(self, messages: List[Dict], **kwargs) -> str:
        """
        Generate response with conversation history
        """
        prompt = self._build_prompt_from_history(messages)
        return await self.generate(prompt, **kwargs)

    def _generate_gemini(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Generate text using Google Gemini via google-generativeai."""
        if genai is None:
            raise RuntimeError(
                "google-generativeai is not installed. Install it with 'pip install google-generativeai'"
            )
        if not self.api_key:
            raise RuntimeError("Gemini provider requires an API key set in LLM_API_KEY")

        genai.configure(api_key=self.api_key)

        response = genai.generate_text(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if hasattr(response, "text"):
            return response.text
        return str(response)

    @staticmethod
    def _build_prompt_from_history(messages: List[Dict]) -> str:
        """Convert conversation history into a single Gemini prompt."""
        lines = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            lines.append(f"{role.capitalize()}: {content}")
        lines.append("Assistant:")
        return "\n".join(lines)
