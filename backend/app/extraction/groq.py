import base64
import json
import time

import httpx
from pydantic import ValidationError

from ..config import CFG
from .base import VisionProvider, VisionRequest, VisionResponse

RETRYABLE_STATUS = ("429", "500", "502", "503", "504")
API_URL = "https://api.groq.com/openai/v1"


class GroqProvider(VisionProvider):
    """Vision extraction through Groq's OpenAI-compatible chat endpoint."""
    name = "groq"

    def __init__(self):
        self.api_key = CFG.groq_api_key
        self.models = [CFG.groq_model] + CFG.groq_fallback_models

    def _call(self, model: str, req: VisionRequest) -> VisionResponse:
        content = []
        for index, raw in enumerate(req.image_bytes):
            content.extend([
                {"type": "text", "text": f"Image index {index}"},
                {"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")
                }},
            ])
        schema = json.dumps(req.schema_model.model_json_schema())
        content.append({
            "type": "text",
            "text": f"{req.prompt_text}\n\nReturn JSON matching this schema:\n{schema}",
        })
        t0 = time.time()
        response = httpx.post(f"{API_URL}/chat/completions", headers={
            "Authorization": f"Bearer {self.api_key}",
        }, timeout=90.0, json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
        })
        response.raise_for_status()
        result = response.json()
        raw_text = result["choices"][0]["message"]["content"]
        parsed = req.schema_model.model_validate_json(raw_text)
        usage = result.get("usage") or {}
        return VisionResponse(
            parsed=parsed, raw_text=raw_text,
            model_id=result.get("model", model),
            prompt_version=req.prompt_version,
            latency_ms=int((time.time() - t0) * 1000),
            tokens=int(usage.get("total_tokens", 0) or 0),
        )

    def analyze(self, req: VisionRequest) -> VisionResponse:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY missing in .env")
        last = None
        for model in self.models:
            for _ in range(2):
                try:
                    return self._call(model, req)
                except ValidationError as error:
                    last = error
                except Exception as error:
                    last = error
                    if not any(status in str(error) for status in RETRYABLE_STATUS):
                        raise
                time.sleep(2)
        raise last