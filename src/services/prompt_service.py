"""Prompt loading and rendering utilities."""

from pathlib import Path
from typing import Any
import string


class SafePromptTemplate(string.Template):
    """Template that uses ${name} placeholders for prompt files."""


class PromptService:
    """Loads prompt templates from the repository prompt directory."""

    def __init__(self, prompt_dir: str = "prompts"):
        self.prompt_dir = Path(prompt_dir)
        self._cache: dict[str, str] = {}

    def load(self, prompt_name: str) -> str:
        """Load a prompt template by file name."""
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        prompt_path = self.prompt_dir / prompt_name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        content = prompt_path.read_text(encoding="utf-8")
        self._cache[prompt_name] = content
        return content

    def render(self, prompt_name: str, **variables: Any) -> str:
        """Render a prompt template with safe string substitution."""
        template = SafePromptTemplate(self.load(prompt_name))
        rendered_variables = {
            key: value if isinstance(value, str) else str(value)
            for key, value in variables.items()
        }
        return template.safe_substitute(rendered_variables)
