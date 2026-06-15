"""Model adapters that conform to ModelAdapter (model_id, provider, generate())."""
from __future__ import annotations
import os
from typing import Any, Optional


class EchoAdapter:
    """Trivial adapter — returns the prompt. Useful for harness self-test."""
    model_id = "echo-test"
    provider = "test"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return prompt


class ScriptedAdapter:
    """Returns deterministic outputs keyed by example_id-or-prompt prefix.

    Used to test the harness without burning model tokens. Pass a dict
    keyed by prompt-substring -> response.
    """
    provider = "test"

    def __init__(self, model_id: str, scripted: dict[str, str], default: str = ""):
        self.model_id = model_id
        self._scripted = dict(scripted)
        self._default = default

    def generate(self, prompt: str, **kwargs: Any) -> str:
        for key, val in self._scripted.items():
            if key in prompt:
                return val
        return self._default


class BedrockClaudeAdapter:
    """Claude on AWS Bedrock — Opus 4.7 by default per Asmit's CLAUDE.md model policy."""
    provider = "bedrock"

    def __init__(self, model_id: str = "global.anthropic.claude-opus-4-7",
                  region: Optional[str] = None, max_tokens: int = 256):
        from anthropic import AnthropicBedrock
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.client = AnthropicBedrock(aws_region=region or os.getenv("BEDROCK_REGION", "ap-south-1"))

    def generate(self, prompt: str, **kwargs: Any) -> str:
        resp = self.client.messages.create(
            model=self.model_id, max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
