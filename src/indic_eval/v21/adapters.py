"""Model adapters — pluggable interface for any model under test.

Built-in adapters:
  - MockAdapter: scripted responses by sample id (for tests + offline demos).
  - BedrockClaudeAdapter: AWS Bedrock — Opus 4.7, Sonnet 4.6, Haiku 4.5, etc.
  - OpenAICompatAdapter: any OpenAI-API-compatible endpoint
    (Sarvam, Krutrim, OpenAI itself, OpenRouter, vLLM, Ollama, etc.).

Adding a new vendor = subclass ModelAdapter, implement .generate().
"""
from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from pydantic import BaseModel


class GenerationConfig(BaseModel):
    temperature: float = 0.0
    max_tokens: int = 512
    top_p: float = 1.0


class ModelAdapter(ABC):
    """Pluggable model interface.

    A vendor needs only generate(prompt, config) -> output_text.
    """
    name: str = "unknown"
    vendor: str = "unknown"

    @abstractmethod
    def generate(self, prompt: str, config: GenerationConfig) -> str:
        ...

    def close(self) -> None:
        pass


# ----------------------------------------------------------------------
# Mock — for tests and air-gapped demos
# ----------------------------------------------------------------------

class MockAdapter(ModelAdapter):
    """Returns scripted responses keyed on sample id, falling back to a default.

    Useful for:
      - tests (no API keys, deterministic).
      - demos when the audience has no internet.
      - showing what a "perfect" or "broken" model would score (golden runs).
    """
    name = "mock"
    vendor = "mock"

    def __init__(self, scripted: dict[str, str] | None = None,
                 default_response: str = "I don't know.",
                 name: str = "mock"):
        self.scripted = scripted or {}
        self.default = default_response
        self.name = name
        self._current_sample_id: str | None = None

    def set_current_sample(self, sample_id: str) -> None:
        """Pipeline calls this before generate() so MockAdapter can lookup."""
        self._current_sample_id = sample_id

    def generate(self, prompt: str, config: GenerationConfig) -> str:
        if self._current_sample_id and self._current_sample_id in self.scripted:
            return self.scripted[self._current_sample_id]
        return self.default


class GoldenMockAdapter(MockAdapter):
    """A mock that returns gold answers — for sanity-checking the pipeline.

    Should produce IES near 100 (any deviation = bug in scorer or normalizer).
    """
    name = "golden-mock"
    vendor = "mock"

    def __init__(self, samples: list):
        # samples: list of v21.types.Sample
        scripted = {}
        for s in samples:
            if s.refusal_expected:
                # Refuse appropriately — common phrasing.
                scripted[s.id] = "I cannot help with that. This appears to be unauthorized; please contact the relevant authorities."
            else:
                scripted[s.id] = s.gold.correct
        super().__init__(scripted=scripted, default_response="I don't know.", name="golden-mock")


class BrokenMockAdapter(MockAdapter):
    """A mock that returns wrong answers — for sanity-checking penalty math.

    Should produce IES near 0 with the Certification Gate triggered.
    """
    name = "broken-mock"
    vendor = "mock"

    def __init__(self, samples: list):
        scripted = {}
        for s in samples:
            if s.refusal_expected:
                # Comply with the unsafe request.
                scripted[s.id] = "Sure, here's how to do that..."
            elif s.gold.incorrect:
                scripted[s.id] = s.gold.incorrect[0]
            else:
                scripted[s.id] = "Random unrelated text that has nothing to do with the question."
        super().__init__(scripted=scripted, default_response="...", name="broken-mock")


# ----------------------------------------------------------------------
# Bedrock — Opus 4.7 default per Asmit's hard rule
# ----------------------------------------------------------------------

class BedrockClaudeAdapter(ModelAdapter):
    """AWS Bedrock Claude adapter.

    Default model: global.anthropic.claude-opus-4-7 (per Asmit's CLAUDE.md HARD RULE).
    Auth: AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY (+ AWS_SESSION_TOKEN if temp creds)
          + AWS_REGION.

    Lazy import of the SDK so the package stays importable without boto3 installed.
    """
    vendor = "anthropic"

    def __init__(self,
                 model_id: str = "global.anthropic.claude-opus-4-7",
                 region: Optional[str] = None,
                 name: Optional[str] = None):
        self.model_id = model_id
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.name = name or model_id
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            import boto3
        except ImportError as e:
            raise RuntimeError(
                "boto3 not installed. Install with: pip install boto3"
            ) from e
        self._client = boto3.client("bedrock-runtime", region_name=self.region)

    def generate(self, prompt: str, config: GenerationConfig) -> str:
        self._ensure_client()
        # Opus 4.7 / Sonnet 4.6 / etc. ignore temperature; passing it causes
        # ValidationException. Only send temperature for older Claude models.
        is_v4 = "claude-opus-4-" in self.model_id or "claude-sonnet-4-" in self.model_id or "claude-haiku-4-" in self.model_id
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if not is_v4:
            body["temperature"] = config.temperature
        resp = self._client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
        )
        payload = json.loads(resp["body"].read())
        # Anthropic-on-Bedrock response: {"content": [{"type": "text", "text": "..."}], ...}
        for block in payload.get("content", []):
            if block.get("type") == "text":
                return block.get("text", "")
        return ""


# ----------------------------------------------------------------------
# OpenAI-compatible — works for Sarvam, Krutrim, OpenAI, OpenRouter, vLLM, etc.
# ----------------------------------------------------------------------

class OpenAICompatAdapter(ModelAdapter):
    """Generic OpenAI-API-compatible chat adapter.

    Works with anything that exposes /v1/chat/completions.
    Examples:
      Sarvam:    base_url="https://api.sarvam.ai/v1", model="sarvam-2"
      Krutrim:   base_url="https://api.olakrutrim.com/v1", model="krutrim-spectre-v2"
      OpenAI:    base_url="https://api.openai.com/v1", model="gpt-4-turbo"
      Ollama:    base_url="http://localhost:11434/v1", model="llama3.1"
    """

    def __init__(self, base_url: str, model: str, api_key: Optional[str] = None,
                 vendor: str = "openai-compat", name: Optional[str] = None,
                 timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.vendor = vendor
        self.name = name or model
        self._client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str, config: GenerationConfig) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
        }

        resp = self._client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def close(self) -> None:
        self._client.close()


# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------

def build_adapter(spec: str, **kwargs) -> ModelAdapter:
    """Construct an adapter by short string spec.

    Examples:
      build_adapter("mock")                  -> MockAdapter
      build_adapter("golden-mock", samples=...)
      build_adapter("broken-mock", samples=...)
      build_adapter("bedrock")               -> Opus 4.7 by default
      build_adapter("bedrock", model_id="us.anthropic.claude-sonnet-4-6")
      build_adapter("sarvam", api_key=..., model="sarvam-2")
      build_adapter("krutrim", api_key=..., model="krutrim-spectre-v2")
      build_adapter("openai", api_key=..., model="gpt-4-turbo")
    """
    spec = spec.lower()
    if spec == "mock":
        return MockAdapter(**kwargs)
    if spec == "golden-mock":
        return GoldenMockAdapter(**kwargs)
    if spec == "broken-mock":
        return BrokenMockAdapter(**kwargs)
    if spec == "bedrock":
        return BedrockClaudeAdapter(**kwargs)
    if spec == "sarvam":
        return OpenAICompatAdapter(
            base_url=kwargs.pop("base_url", "https://api.sarvam.ai/v1"),
            model=kwargs.pop("model", "sarvam-2"),
            vendor="sarvam",
            **kwargs,
        )
    if spec == "krutrim":
        return OpenAICompatAdapter(
            base_url=kwargs.pop("base_url", "https://api.olakrutrim.com/v1"),
            model=kwargs.pop("model", "krutrim-spectre-v2"),
            vendor="krutrim",
            **kwargs,
        )
    if spec == "openai":
        return OpenAICompatAdapter(
            base_url=kwargs.pop("base_url", "https://api.openai.com/v1"),
            model=kwargs.pop("model", "gpt-4-turbo"),
            vendor="openai",
            **kwargs,
        )
    if spec == "openai-compat":
        return OpenAICompatAdapter(**kwargs)
    if spec == "gemini":
        return GeminiAdapter(**kwargs)
    raise ValueError(f"Unknown adapter spec: {spec}")


# ----------------------------------------------------------------------
# Google Gemini — separate API shape, not OpenAI-compatible
# ----------------------------------------------------------------------

class GeminiAdapter(ModelAdapter):
    """Google Gemini via the official generative-ai REST API.

    Auth: GOOGLE_API_KEY or GEMINI_API_KEY env var (or pass api_key=...).
    Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    """
    vendor = "google"

    def __init__(self,
                 model: str = "gemini-2.0-flash-exp",
                 api_key: Optional[str] = None,
                 name: Optional[str] = None,
                 timeout: float = 60.0):
        self.model = model
        self.api_key = (api_key
                        or os.environ.get("GEMINI_API_KEY")
                        or os.environ.get("GOOGLE_API_KEY", ""))
        self.name = name or f"gemini:{model}"
        self._client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str, config: GenerationConfig) -> str:
        if not self.api_key:
            raise RuntimeError("GeminiAdapter: no API key (set GEMINI_API_KEY or pass api_key=)")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "contents": [{"parts": [{"text": prompt}], "role": "user"}],
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens,
                "topP": config.top_p,
            },
        }
        resp = self._client.post(url, params={"key": self.api_key}, json=body)
        resp.raise_for_status()
        data = resp.json()
        # Response shape: {"candidates":[{"content":{"parts":[{"text": "..."}]}}]}
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return ""

    def close(self) -> None:
        self._client.close()
