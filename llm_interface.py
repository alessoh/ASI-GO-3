"""
LLM Interface supporting multiple providers (OpenAI, Google, Anthropic)
- No direct 'proxies=' kwargs to SDKs.
- Optional proxy via httpx.Client when env proxy is set.
"""
import os
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv

# Load .env early
load_dotenv()
logger = logging.getLogger("ASI-GO.LLM")


class LLMInterface:
    """Unified interface for different LLM providers"""

    def __init__(self):
        # Provider from env (support both names)
        self.provider = (os.getenv("PROVIDER") or os.getenv("LLM_PROVIDER") or "openai").strip().lower()
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))
        self.model: Optional[str] = None

        # Optional proxy taken from env
        self._proxy = (
            os.getenv("OPENAI_PROXY")
            or os.getenv("HTTPS_PROXY")
            or os.getenv("HTTP_PROXY")
            or None
        )

        # Created client per provider
        self.client = None
        self._init_provider()

    # -------- init helpers --------
    def _init_provider(self):
        try:
            if self.provider == "openai":
                # OpenAI Python SDK v1.x
                from openai import OpenAI
                http_client = None
                if self._proxy:
                    import httpx
                    http_client = httpx.Client(proxies=self._proxy)

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")

                if http_client is not None:
                    self.client = OpenAI(api_key=api_key, http_client=http_client)
                else:
                    self.client = OpenAI(api_key=api_key)

                self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                logger.info(f"Initialized openai with model {self.model}")

            elif self.provider in ("google", "gemini"):
                import google.generativeai as genai
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found in environment")
                # google-generativeai reads proxies from env automatically
                genai.configure(api_key=api_key)
                self.model = os.getenv("GOOGLE_MODEL", "gemini-pro")
                self.client = genai.GenerativeModel(self.model)
                logger.info(f"Initialized google with model {self.model}")

            elif self.provider == "anthropic":
                from anthropic import Anthropic
                http_client = None
                if self._proxy:
                    import httpx
                    http_client = httpx.Client(proxies=self._proxy)

                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")

                if http_client is not None:
                    self.client = Anthropic(api_key=api_key, http_client=http_client)
                else:
                    self.client = Anthropic(api_key=api_key)

                self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
                logger.info(f"Initialized anthropic with model {self.model}")

            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise

    # -------- public API --------
    def query(self, prompt: str, system: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """
        Send a prompt to the configured provider and return text.
        """
        try:
            if self.provider == "openai":
                # OpenAI Chat Completions API
                msgs = []
                if system:
                    msgs.append({"role": "system", "content": system})
                msgs.append({"role": "user", "content": prompt})

                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": msgs,
                    "temperature": self.temperature,
                }
                if max_tokens is not None:
                    kwargs["max_tokens"] = max_tokens

                resp = self.client.chat.completions.create(**kwargs)
                return (resp.choices[0].message.content or "").strip()

            elif self.provider in ("google", "gemini"):
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                # google-generativeai
                resp = self.client.generate_content(full_prompt)
                # Some responses need .text; fall back to candidates if needed
                text = getattr(resp, "text", None)
                if text:
                    return text.strip()
                if hasattr(resp, "candidates") and resp.candidates:
                    part = getattr(resp.candidates[0], "content", None)
                    if part and getattr(part, "parts", None):
                        return str(part.parts[0].text).strip()
                return ""

            elif self.provider == "anthropic":
                # Anthropic Messages API
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "temperature": self.temperature,
                    "max_tokens": max_tokens or 1024,
                }
                resp = self.client.messages.create(**kwargs)
                # content is a list of blocks; take first text block
                blocks = getattr(resp, "content", []) or []
                if blocks and hasattr(blocks[0], "text"):
                    return (blocks[0].text or "").strip()
                # Fallback stringify
                return str(resp)

            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise

    def get_provider_info(self) -> Dict[str, str]:
        """Return provider information for display"""
        return {
            "provider": self.provider,
            "model": self.model or "",
            "temperature": str(self.temperature),
        }
