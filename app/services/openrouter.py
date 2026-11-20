"""OpenRouter API client with automatic free-model fallback, rate-limiting, and error handling."""
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.utils.logging import logger
from app.utils.validators import mask_secret

class OpenRouterService:
    """Enterprise client for OpenRouter free models with resilient fallback."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        raw_key = (api_key or settings.OPENROUTER_API_KEY or "").strip()
        if "OPENROUTER_API_KEY=" in raw_key:
            raw_key = raw_key.split("OPENROUTER_API_KEY=", 1)[1].strip()
        elif "key=" in raw_key:
            raw_key = raw_key.split("key=", 1)[1].strip()
        cleaned = raw_key.strip("\"' \t\r\n")
        if "sk-" in cleaned:
            cleaned = "sk-" + cleaned.split("sk-", 1)[1]
        self.api_key = cleaned.strip("\"' \t\r\n")
        self.primary_model = (model or settings.OPENROUTER_MODEL or "openrouter/free").strip("\"' ")
        self.fallback_models = settings.FALLBACK_MODELS
        self.base_url = settings.OPENROUTER_BASE_URL
        self.timeout = settings.REQUEST_TIMEOUT
        
        logger.info(
            f"Initialized OpenRouterService with model={self.primary_model}, "
            f"key={mask_secret(self.api_key)}"
        )

    def is_configured(self) -> bool:
        """Checks if a non-empty API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 8)

    def get_available_free_models(self) -> List[Dict[str, Any]]:
        """Queries OpenRouter /api/v1/models to verify active 0-cost free models."""
        url = f"{self.base_url}/models"
        req = urllib.request.Request(url, headers={"User-Agent": "EstateIntel/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("data", [])
                free_list = [
                    m for m in models 
                    if m.get("id", "").endswith(":free") 
                    or (str(m.get("pricing", {}).get("prompt", "1")) == "0" and str(m.get("pricing", {}).get("completion", "1")) == "0")
                ]
                return free_list
        except Exception as e:
            logger.error(f"Failed to query OpenRouter models: {e}")
            return []

    def _call_model_api(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        temperature: float, 
        max_tokens: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Sends chat completion request to OpenRouter. Returns (completion_text, error_message)."""
        if not self.is_configured():
            return None, "OpenRouter API key is not configured. Please set the OPENROUTER_API_KEY environment variable."

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://estateintel-ai.onrender.com",
            "X-Title": "EstateIntel AI Assistant",
            "User-Agent": "EstateIntel/1.0",
        }

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if not choices:
                    return None, f"OpenRouter returned empty choices response from model {model}."
                content = choices[0].get("message", {}).get("content", "")
                return content, None

        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            logger.error(f"OpenRouter HTTP Error {he.code} for model {model}: {err_body}")
            
            if he.code == 401:
                return None, "Invalid OpenRouter API Key. Please verify your credentials."
            elif he.code == 429:
                return None, f"Rate limit reached on free model {model}. OpenRouter free-tier rate limits apply."
            elif he.code in (404, 502, 503):
                return None, f"Model {model} is currently unavailable (Status {he.code})."
            else:
                return None, f"OpenRouter API error ({he.code}): {err_body[:200]}"
                
        except urllib.error.URLError as ue:
            logger.error(f"OpenRouter network timeout/error: {ue.reason}")
            return None, f"Network timeout contacting OpenRouter: {ue.reason}"
        except Exception as ex:
            logger.error(f"Unexpected error in OpenRouter call: {ex}")
            return None, f"Unexpected error communicating with AI provider: {str(ex)}"

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, str, Optional[str]]:
        """Generates grounded response, automatically attempting free-tier fallbacks if needed.
        
        Returns:
            Tuple[answer_text, active_model_used, error_message]
        """
        temp = temperature if temperature is not None else settings.TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.MAX_TOKENS

        # Assemble chat messages
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for turn in history[-6:]:  # Keep recent context window
                messages.append(turn)
        messages.append({"role": "user", "content": user_prompt})

        # Try primary model first
        models_to_try = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        last_error = None

        for idx, candidate_model in enumerate(models_to_try):
            # Ensure we only use verified free models (ending with :free or openrouter/free)
            if not candidate_model.endswith(":free") and candidate_model != "openrouter/free":
                candidate_model = f"{candidate_model}:free"

            logger.info(f"Attempting inference with free model [{idx+1}/{len(models_to_try)}]: {candidate_model}")
            ans, err = self._call_model_api(candidate_model, messages, temp, tokens)
            
            if ans is not None:
                return ans, candidate_model, None
            
            last_error = err
            # If 401 Unauthorized, no need to retry other models with same invalid key
            if "Invalid OpenRouter API Key" in (err or "") or "not configured" in (err or ""):
                break
                
            time.sleep(1.0)  # Brief pause before fallback attempt

        # If all models failed or API key missing
        fallback_msg = (
            f"Unable to generate response from OpenRouter free models. "
            f"Reason: {last_error or 'Provider unavailable'}. "
            f"Please verify your OPENROUTER_API_KEY and network connection."
        )
        return fallback_msg, self.primary_model, last_error
